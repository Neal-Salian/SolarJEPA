"""V2 lightweight forecasting comparators on the JEPA input contract (optional Torch).

Both comparators consume the same train-normalized context [B, context, F] and
Boolean mask as the JEPA arms, emit [B, horizon, targets, quantiles] in
standardized transformed space, reuse the same train-only normalization,
deterministic training-window subset and validation partition, and predict
through the shared context-only ``QuantileForecaster``.

* Small causal TCN: residual blocks of two left-padded dilated convolutions,
  GELU after the first convolution and after the residual addition, a 1x1 skip
  projection when channel counts differ, final-time-step affine head with
  monotone quantiles (base plus cumulative Softplus, as in the JEPA head). Inputs
  are the normalized values and masks (2F channels). It is trained with the
  shared downstream loop, so its window order equals the JEPA arms' for a seed.
* Full-context quantile-linear: flattened normalized context values to all
  horizon x target x quantile outputs, zero initialization, Adam, fixed epochs,
  objective = training loss + lambda * mean squared input coefficients (bias
  excluded). Each lambda reuses an identical PCG64(seed) shuffle stream. The
  final epoch is kept (no epoch selection); lambda is chosen on validation after
  sorting quantiles, ties to the smallest lambda. Raw crossing rates are kept.
  It requires complete context support (no mask channels).

Architectures, grids and budgets are explicit configuration, never defaults.
Equal inputs and data do not make capacity, optimization or compute equal.
"""
from dataclasses import asdict, dataclass
import math
import time

import numpy as np

from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .controlled import (QuantileForecaster, SCHEMA_VERSION, _environment, _orders_fingerprint, _prepare,
                         _state_fingerprint, _validation_identity, register_builder, train_downstream)
from .core import _cpu_state, _finite_state, _torch, _weights_fingerprint
from .jepa import _setup, window_tensors
from .losses import MetricAccumulator, check_loss_version, forecast_loss

TCN_KIND, LINEAR_KIND = 'tcn_quantile', 'quantile_linear'


def _int(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


def _float(value, name, lower, upper, closed=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value > upper or value < lower \
            or (not closed and value == lower):
        raise ValueError(f'{name} must be finite within bounds')
    return float(value)


def _levels(value):
    if not isinstance(value, (list, tuple)) or not value or any(type(x) not in (int, float) for x in value):
        raise ValueError('quantiles require an explicit ordered list')
    levels = tuple(float(x) for x in value)
    if (not all(0 < x < 1 for x in levels) or any(a >= b for a, b in zip(levels, levels[1:]))
            or .5 not in levels):
        raise ValueError('quantiles must be strictly increasing in (0,1) and include 0.5')
    return levels


def _common(config):
    _int(config.seed, 'seed', 0, 2**32 - 1)
    _int(config.threads, 'threads', 1, 256)
    _int(config.batch_size, 'batch_size', 1, 4096)
    _float(config.lr, 'lr', 0., 1.)
    cap = config.max_train_windows
    if cap is not None:
        _int(cap, 'max_train_windows', 1, 10**8)
    object.__setattr__(config, 'quantiles', _levels(config.quantiles))


@dataclass(frozen=True)
class ComparatorSchedule:
    """Downstream-only schedule (same semantics as ``TrainingSchedule``)."""
    downstream_epochs: int
    early_stopping_patience: int | None
    train_loss: str
    selection_metric: str
    diagnostic_metrics: tuple = ()

    def __post_init__(self):
        _int(self.downstream_epochs, 'downstream_epochs', 1, 500)
        if self.early_stopping_patience is not None:
            _int(self.early_stopping_patience, 'early_stopping_patience', 1, 500)
        check_loss_version(self.train_loss)
        check_loss_version(self.selection_metric)
        if not isinstance(self.diagnostic_metrics, (list, tuple)):
            raise ValueError('diagnostic_metrics must be an explicit sequence')
        diagnostics = tuple(check_loss_version(x) for x in self.diagnostic_metrics)
        if len(set(diagnostics)) != len(diagnostics) or self.selection_metric in diagnostics:
            raise ValueError('Diagnostic metrics must be unique and exclude the selection metric')
        object.__setattr__(self, 'diagnostic_metrics', diagnostics)

    def as_dict(self):
        result = asdict(self)
        result['diagnostic_metrics'] = list(self.diagnostic_metrics)
        return result


@dataclass(frozen=True)
class TcnConfig:
    width: int
    kernel_size: int
    dilations: tuple
    dropout: float
    seed: int
    threads: int
    batch_size: int
    lr: float
    weight_decay: float
    gradient_clip: float
    quantiles: tuple
    max_train_windows: int | None

    def __post_init__(self):
        _common(self)
        _int(self.width, 'width', 1, 1024)
        _int(self.kernel_size, 'kernel_size', 2, 64)
        if not isinstance(self.dilations, (list, tuple)) or not self.dilations:
            raise ValueError('dilations require an explicit nonempty list')
        object.__setattr__(self, 'dilations', tuple(_int(d, 'dilation', 1, 4096) for d in self.dilations))
        object.__setattr__(self, 'dropout', _float(self.dropout, 'dropout', 0., .5, closed=True))
        object.__setattr__(self, 'weight_decay', _float(self.weight_decay, 'weight_decay', 0., 1., closed=True))
        object.__setattr__(self, 'gradient_clip', _float(self.gradient_clip, 'gradient_clip', 0., 1000.))
        object.__setattr__(self, 'lr', float(self.lr))

    def as_dict(self):
        result = asdict(self)
        result.update(dilations=list(self.dilations), quantiles=list(self.quantiles))
        return result


def receptive_field(config):
    """Bins seen by the final state: 1 + sum over blocks of 2 (k - 1) d."""
    return 1 + sum(2 * (config.kernel_size - 1) * d for d in config.dilations)


def _check_context(features, feature_mask, spec):
    torch = _torch()
    if (features.shape != feature_mask.shape or feature_mask.dtype != torch.bool or features.ndim != 3
            or tuple(features.shape[1:]) != (spec.context_steps, len(spec.feature_names))):
        raise ValueError('Forecast input must be context-only [B, context_steps, features] with a Boolean mask')


def build_tcn(spec, config):
    torch = _torch()
    nn, F = torch.nn, torch.nn.functional
    targets, levels, width, k = len(spec.target_names), len(config.quantiles), config.width, config.kernel_size

    class CausalConv(nn.Module):
        def __init__(self, inputs, dilation):
            super().__init__()
            self.pad = (k - 1) * dilation
            self.conv = nn.Conv1d(inputs, width, k, dilation=dilation)

        def forward(self, x):
            return self.conv(F.pad(x, (self.pad, 0)))

    class Block(nn.Module):
        def __init__(self, inputs, dilation):
            super().__init__()
            self.first, self.second = CausalConv(inputs, dilation), CausalConv(width, dilation)
            self.skip = nn.Conv1d(inputs, width, 1) if inputs != width else nn.Identity()
            self.dropout = nn.Dropout(config.dropout)

        def forward(self, x):
            return F.gelu(self.second(self.dropout(F.gelu(self.first(x)))) + self.skip(x))

    class TemporalConvForecaster(nn.Module):
        def __init__(self):
            super().__init__()
            blocks, inputs = [], 2 * len(spec.feature_names)
            for dilation in config.dilations:
                blocks.append(Block(inputs, dilation))
                inputs = width
            self.blocks = nn.Sequential(*blocks)
            self.head = nn.Linear(width, spec.horizon_steps * targets * levels)

        def states(self, features, feature_mask):
            """Causal hidden states [B, width, context]; state t uses bins <= t only."""
            _check_context(features, feature_mask, spec)
            joined = torch.cat((features, feature_mask.to(features.dtype)), dim=-1)
            return self.blocks(joined.transpose(1, 2))

        def forecast(self, features, feature_mask):
            raw = self.head(self.states(features, feature_mask)[..., -1])
            raw = raw.reshape(len(features), spec.horizon_steps, targets, levels)
            return torch.cat((raw[..., :1], raw[..., :1] + F.softplus(raw[..., 1:]).cumsum(dim=-1)), dim=-1)

    return TemporalConvForecaster()


def _base_record(kind, model_id, config_record, seed, training, normalization, window_record, validation):
    return dict(schema_version=SCHEMA_VERSION, model_id=model_id, model_kind=kind,
                scientific_status='EXPERIMENTAL_UNVALIDATED', config=config_record,
                run_fingerprint=fingerprint_payload(config_record),
                recipe_fingerprint=fingerprint_payload({k: {kk: vv for kk, vv in v.items() if kk != 'seed'}
                                                        for k, v in config_record.items()}),
                seed=seed, spec_fingerprint=training.spec.fingerprint,
                normalization_fingerprint=normalization.fingerprint, training_fingerprint=training.fingerprint,
                training_dataset_fingerprint=training.context.dataset_fingerprint, train_windows=window_record,
                validation=_validation_identity(validation))


def fit_tcn(training_slice, validation_window, config, schedule):
    """Train the causal TCN with the shared downstream loop; select on validation only."""
    if not isinstance(config, TcnConfig) or not isinstance(schedule, ComparatorSchedule):
        raise ValueError('fit_tcn requires a TcnConfig and a ComparatorSchedule')
    began = time.perf_counter()
    training, validation, normalization, windows, window_record = _prepare(training_slice, validation_window, config)
    validation_batch = window_tensors(validation, normalization)
    preparation, started = time.perf_counter() - began, time.perf_counter()
    _setup(config)
    model = build_tcn(training.spec, config)
    initial = dict(blocks=_state_fingerprint(model.blocks), head=_state_fingerprint(model.head))
    initial_state = _state_fingerprint(model)
    _setup(config)
    result = train_downstream(model, trainable=[model], frozen=[], windows=windows,
                              validation_batch=validation_batch, schedule=schedule, settings=config,
                              normalization=normalization, modules=dict(tcn=model.blocks, head=model.head))
    phase = result['phase']
    record = _base_record(TCN_KIND, 'v2_tcn_quantile', dict(tcn=config.as_dict(), schedule=schedule.as_dict()),
                          config.seed, training, normalization, window_record, validation)
    record.update(
        rng_streams=dict(initialization='training.jepa._setup(seed) then build_tcn',
                         downstream_order='numpy.random.default_rng([seed, 1]) permutation per epoch'),
        pairing=dict(initial_state=initial_state, downstream_order=result['order']),
        fingerprints=dict(initial=initial, selected=dict(blocks=_state_fingerprint(model.blocks),
                                                         head=_state_fingerprint(model.head))),
        history=result['history'], selection=result['selection'],
        budget=dict(phases=[phase], totals=dict(
            optimizer_steps=phase['optimizer_steps'], examples_seen=phase['examples_seen'],
            parameter_updates={k: v['max'] for k, v in phase['parameter_updates'].items()})),
        parameters=dict(trainable_total=int(sum(p.numel() for p in model.parameters())),
                        receptive_field_bins=receptive_field(config), context_steps=training.spec.context_steps),
        environment=_environment(config.threads),
        wall_seconds=dict(preparation=preparation, this_call_training=time.perf_counter() - started,
                          scope='downstream epochs incl. validation selection; excludes preparation/inference'))
    return QuantileForecaster(model, normalization, record, quantiles=config.quantiles, batch_size=config.batch_size)


# ------------------------------------------------------------------ quantile linear


@dataclass(frozen=True)
class QuantileLinearConfig:
    lambdas: tuple
    lr: float
    batch_size: int
    epochs: int
    seed: int
    threads: int
    gradient_clip: float | None
    quantiles: tuple
    max_train_windows: int | None
    train_loss: str
    selection_metric: str

    def __post_init__(self):
        _common(self)
        if not isinstance(self.lambdas, (list, tuple)) or not self.lambdas:
            raise ValueError('lambdas require an explicit nonempty list')
        lambdas = tuple(_float(x, 'lambda', 0., 1e6, closed=True) for x in self.lambdas)
        if len(set(lambdas)) != len(lambdas):
            raise ValueError('lambdas must be unique')
        object.__setattr__(self, 'lambdas', tuple(sorted(lambdas)))
        _int(self.epochs, 'epochs', 1, 10_000)
        object.__setattr__(self, 'lr', float(self.lr))
        if self.gradient_clip is not None:
            object.__setattr__(self, 'gradient_clip', _float(self.gradient_clip, 'gradient_clip', 0., 1000.))
        check_loss_version(self.train_loss)
        check_loss_version(self.selection_metric)

    def as_dict(self):
        result = asdict(self)
        result.update(lambdas=list(self.lambdas), quantiles=list(self.quantiles))
        return result


def build_quantile_linear(spec, config):
    torch = _torch()
    nn = torch.nn
    shape = (spec.horizon_steps, len(spec.target_names), len(config.quantiles))

    class QuantileLinear(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(spec.context_steps * len(spec.feature_names), int(np.prod(shape)))
            nn.init.zeros_(self.linear.weight)
            nn.init.zeros_(self.linear.bias)

        def forecast(self, features, feature_mask):
            """Raw (possibly crossing) quantiles; prediction sorts them."""
            _check_context(features, feature_mask, spec)
            if not bool(feature_mask.all()):
                raise ValueError('Quantile-linear comparator requires complete context support')
            return self.linear(features.flatten(1)).reshape((len(features),) + shape)

    return QuantileLinear()


def _select_lambda(values):
    """Lowest validation value; exact ties choose the smallest lambda."""
    items = sorted(values.items())
    if not items or not all(math.isfinite(v) for _, v in items):
        raise ValueError('Lambda selection requires finite validation values')
    best = min(v for _, v in items)
    return next(lam for lam, v in items if v == best)


def _sorted_validation(model, batch, config, normalization):
    torch = _torch()
    model.eval()
    accumulator = MetricAccumulator(config.selection_metric, config.quantiles, normalization.target_scale)
    crossings, cells = 0, 0
    with torch.no_grad():
        for start in range(0, len(batch.features), config.batch_size):
            stop = start + config.batch_size
            if not bool(batch.target_mask[start:stop].any()):
                continue
            raw = model.forecast(batch.features[start:stop], batch.feature_mask[start:stop])
            crossings += int((raw.diff(dim=-1) < 0).any(dim=-1).sum())
            cells += int(np.prod(raw.shape[:-1]))
            accumulator.add(raw.sort(dim=-1).values, batch.targets[start:stop], batch.target_mask[start:stop])
    return accumulator.value(), crossings / cells


def fit_quantile_linear(training_slice, validation_window, config):
    """Fit every lambda for fixed epochs on training windows; choose lambda on validation."""
    torch = _torch()
    if not isinstance(config, QuantileLinearConfig):
        raise ValueError('fit_quantile_linear requires a QuantileLinearConfig')
    began = time.perf_counter()
    training, validation, normalization, windows, window_record = _prepare(training_slice, validation_window, config)
    validation_batch = window_tensors(validation, normalization)
    preparation, started = time.perf_counter() - began, time.perf_counter()
    context = training.spec.context_steps
    candidates, states = [], {}
    for lam in config.lambdas:
        start_time = time.perf_counter()
        _setup(config)
        model = build_quantile_linear(training.spec, config)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
        rng = np.random.Generator(np.random.PCG64(config.seed))
        orders = [rng.permutation(len(windows)) for _ in range(config.epochs)]
        steps, loss_sum, count = 0, 0., 0
        for order in orders:
            model.train()
            loss_sum, count = 0., 0
            for begin in range(0, len(order), config.batch_size):
                features, mask, targets, target_mask = (torch.from_numpy(x) for x in
                                                        windows.take(order[begin:begin + config.batch_size]))
                optimizer.zero_grad(set_to_none=True)
                fit = forecast_loss(config.train_loss, model.forecast(features[:, :context], mask[:, :context]),
                                    targets, target_mask, config.quantiles, normalization.target_scale)
                loss = fit + lam * model.linear.weight.square().mean()
                if not bool(torch.isfinite(loss)):
                    raise ValueError('Nonfinite training loss')
                loss.backward()
                if config.gradient_clip is not None:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip, error_if_nonfinite=True)
                optimizer.step()
                steps += 1
                loss_sum += float(loss.detach()) * len(features)
                count += len(features)
        _finite_state(model.state_dict())
        metric, crossing = _sorted_validation(model, validation_batch, config, normalization)
        states[lam] = _cpu_state(model.state_dict())
        candidates.append({'lambda': lam, 'validation_metric': metric, 'validation_raw_crossing_fraction': crossing,
                           'optimizer_steps': steps, 'final_epoch_train_objective': loss_sum / count,
                           'mean_squared_coefficient': float(model.linear.weight.detach().square().mean()),
                           'shuffle_order': _orders_fingerprint(orders),
                           'weights_fingerprint': _weights_fingerprint(states[lam]),
                           'wall_seconds': time.perf_counter() - start_time})
    selected = _select_lambda({c['lambda']: c['validation_metric'] for c in candidates})
    model = build_quantile_linear(training.spec, config)
    model.load_state_dict(states[selected], strict=True)
    steps = sum(c['optimizer_steps'] for c in candidates)
    record = _base_record(LINEAR_KIND, 'v2_quantile_linear', dict(linear=config.as_dict()), config.seed,
                          training, normalization, window_record, validation)
    record.update(
        rng_streams=dict(shuffle='numpy.random.Generator(PCG64(seed)) reinitialized for every lambda',
                         initialization='zeros'),
        lambda_candidates=candidates,
        selection=dict(partition='validation', metric=config.selection_metric, value=min(
            c['validation_metric'] for c in candidates), **{'lambda': selected},
            tie_policy='smallest_lambda', epoch_selection='none_final_epoch_kept', quantile_order='sorted'),
        budget=dict(phases=[dict(phase='lambda_grid', fits=len(candidates), epochs_per_fit=config.epochs,
                                 optimizer_steps=steps, optimizer='Adam', lr=config.lr)],
                    totals=dict(optimizer_steps=steps, selected_fit_steps=steps // len(candidates))),
        parameters=dict(trainable_total=int(sum(p.numel() for p in model.parameters()))),
        environment=_environment(config.threads),
        wall_seconds=dict(preparation=preparation, this_call_training=time.perf_counter() - started,
                          scope='all lambda fits incl. validation; excludes preparation/inference'))
    return QuantileForecaster(model, normalization, record, quantiles=config.quantiles,
                              batch_size=config.batch_size, rearrange=True)


# ----------------------------------------------------------------- checkpoint load


def _verified(record, config):
    if record.get('run_fingerprint') != fingerprint_payload(config):
        raise ValueError('Comparator checkpoint configuration identity differs')


def _tcn_builder(spec, record):
    _verified(record, record['config'])
    config = TcnConfig(**record['config']['tcn'])
    if canonical_json(config.as_dict()) != canonical_json(record['config']['tcn']):
        raise ValueError('Comparator checkpoint configuration identity differs')
    return build_tcn(spec, config), dict(quantiles=config.quantiles, batch_size=config.batch_size)


def _linear_builder(spec, record):
    _verified(record, record['config'])
    config = QuantileLinearConfig(**record['config']['linear'])
    return build_quantile_linear(spec, config), dict(quantiles=config.quantiles, batch_size=config.batch_size,
                                                     rearrange=True)


register_builder(TCN_KIND, _tcn_builder)
register_builder(LINEAR_KIND, _linear_builder)
