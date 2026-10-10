"""V2 controlled training arms for the temporal JEPA forecaster (optional Torch).

This module composes, and never changes, the V1 implementation in
``training.jepa``: the same model builder, JEPA pretraining loop, train-only
normalization, deterministic window subset, validation monitoring and seeding.

Arms (all share the architecture, initial weights, training-window subset and
downstream window order for one seed):

* ``jepa_finetune``: JEPA pretraining, then every trainable module fine-tuned.
* ``supervised``: no pretraining; the matched supervised control.
* ``supervised_extra_updates``: supervised warmup over the exact JEPA SSL window
  order and step count, optimizer reset, then the same downstream schedule. It
  matches encoder/predictor update opportunities, not FLOPs or the objective
  (its head also trains during warmup).
* ``jepa_frozen``: JEPA pretraining, then only the forecast head is trained.
* ``random_frozen``: the same seed's random encoder/predictor, head only.

Every budget is supplied explicitly by ``TrainingSchedule``; this module holds no
approved seed counts, epochs or losses. Checkpoints are selected on validation
among downstream epochs only (earliest minimum). Optimizer-step and per-module
parameter-update counts are recorded per phase; downstream and warmup counts are
read from AdamW state, SSL counts follow the V1 optimizer definition
(encoder and predictor every step). No scientific skill is asserted here.
"""
from dataclasses import asdict, dataclass, replace
import hashlib
import importlib
import json
from pathlib import Path
import platform
import resource
import sys
import time

import numpy as np

from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, canonical_json, fingerprint_payload, logical_array,
)
from .core import _context_grid, _cpu_state, _finite_state, _torch, _weights_fingerprint, window_snapshot
from .jepa import (JepaConfig, _check_step, _monitor, _parameter_counts, _seeded_model, _setup,
                   _validate_inputs, _validation_pinball, _windows, build_jepa_model, pretrain_jepa,
                   window_tensors)
from .losses import MetricAccumulator, check_loss_version, forecast_loss
from .normalization import Normalization, training_snapshot

ARMS = ('jepa_finetune', 'supervised', 'supervised_extra_updates', 'jepa_frozen', 'random_frozen')
SSL_ARMS = ('jepa_finetune', 'jepa_frozen')
FROZEN_ARMS = ('jepa_frozen', 'random_frozen')
MODEL_KIND = 'temporal_jepa_quantile_controlled'
SCHEMA_VERSION = 1
MODULES = ('encoder', 'target_encoder', 'predictor', 'head')
# JepaConfig fields owned by TrainingSchedule in V2; their JepaConfig values are ignored.
_SCHEDULE_FIELDS = ('pretrain_epochs', 'finetune_epochs', 'patience', 'jepa_weight_during_finetune')
RNG_STREAMS = dict(
    initialization='training.jepa._setup(seed) then build_jepa_model: random/numpy/torch seeded with seed',
    pretrain_order='numpy.random.default_rng([seed, 0]) permutation per SSL epoch (training.jepa.pretrain_jepa)',
    pretrain_context_mask='torch.Generator().manual_seed(seed + 2) (training.jepa.pretrain_jepa)',
    warmup_order='numpy.random.default_rng([seed, 0]) permutation per warmup epoch (same stream as SSL)',
    downstream_order='numpy.random.default_rng([seed, 1]) permutation per downstream epoch, torch reseeded first')


def _bounded(value, name, minimum, maximum=500):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


@dataclass(frozen=True)
class TrainingSchedule:
    """Explicit V2 phase budgets and objectives; deliberately without defaults."""
    arm: str
    pretrain_epochs: int
    warmup_epochs: int
    downstream_epochs: int
    early_stopping_patience: int | None
    train_loss: str
    selection_metric: str
    diagnostic_metrics: tuple = ()

    def __post_init__(self):
        if self.arm not in ARMS:
            raise ValueError(f'arm must be one of {ARMS}')
        _bounded(self.pretrain_epochs, 'pretrain_epochs', 0)
        _bounded(self.warmup_epochs, 'warmup_epochs', 0)
        _bounded(self.downstream_epochs, 'downstream_epochs', 1)
        if (self.pretrain_epochs > 0) != (self.arm in SSL_ARMS):
            raise ValueError('JEPA arms require pretraining epochs; other arms must have none')
        if (self.warmup_epochs > 0) != (self.arm == 'supervised_extra_updates'):
            raise ValueError('Only supervised_extra_updates has (and requires) supervised warmup epochs')
        if self.early_stopping_patience is not None:
            _bounded(self.early_stopping_patience, 'early_stopping_patience', 1)
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


def v1_compatible_schedule(variant, config):
    """The V1 ``fit_forecaster`` schedule (normalized pinball, early stopping) for one variant."""
    if variant not in ('jepa_finetune', 'jepa_frozen', 'supervised'):
        raise ValueError('V1 compatibility exists only for the three V1 variants')
    return TrainingSchedule(arm=variant, pretrain_epochs=config.pretrain_epochs if variant in SSL_ARMS else 0,
                            warmup_epochs=0, downstream_epochs=config.finetune_epochs,
                            early_stopping_patience=config.patience, train_loss='normalized_pinball_v1',
                            selection_metric='normalized_pinball_v1', diagnostic_metrics=())


@dataclass(frozen=True)
class ControlledConfig:
    """Architecture/optimizer settings (``JepaConfig``) plus an explicit schedule."""
    architecture: JepaConfig
    schedule: TrainingSchedule

    def __post_init__(self):
        if not isinstance(self.architecture, JepaConfig) or not isinstance(self.schedule, TrainingSchedule):
            raise ValueError('ControlledConfig requires a JepaConfig and a TrainingSchedule')
        architecture = JepaConfig(**self.architecture.as_dict())
        schedule = TrainingSchedule(**self.schedule.as_dict())
        if architecture.jepa_weight_during_finetune != 0:
            raise ValueError('An auxiliary JEPA loss during fine-tuning is outside the V2 controlled scope')
        object.__setattr__(self, 'schedule', schedule)
        object.__setattr__(self, 'architecture', replace(
            architecture, pretrain_epochs=schedule.pretrain_epochs, finetune_epochs=schedule.downstream_epochs,
            patience=schedule.early_stopping_patience or 1, jepa_weight_during_finetune=0.))

    @property
    def jepa_config(self):
        """Effective V1 config used by the reused V1 functions."""
        return self.architecture

    @property
    def seed(self):
        return self.architecture.seed

    def as_dict(self):
        architecture = {k: v for k, v in self.architecture.as_dict().items() if k not in _SCHEDULE_FIELDS}
        return dict(schema_version=SCHEMA_VERSION, architecture=architecture, schedule=self.schedule.as_dict())

    @classmethod
    def from_dict(cls, record):
        if (not isinstance(record, dict) or set(record) != {'schema_version', 'architecture', 'schedule'}
                or record['schema_version'] != SCHEMA_VERSION):
            raise ValueError('Malformed controlled configuration record')
        schedule = TrainingSchedule(**record['schedule'])
        return cls(JepaConfig(**record['architecture'], pretrain_epochs=schedule.pretrain_epochs,
                              finetune_epochs=schedule.downstream_epochs), schedule)

    @property
    def run_fingerprint(self):
        return fingerprint_payload(self.as_dict())

    @property
    def recipe_fingerprint(self):
        """Identity of everything except the seed (one recipe, many paired seeds)."""
        record = self.as_dict()
        record['architecture'].pop('seed')
        return fingerprint_payload(record)


# ------------------------------------------------------------------ small helpers


def _state_fingerprint(module):
    return _weights_fingerprint(_cpu_state(module.state_dict()))


def _module_fingerprints(model):
    return {name: _state_fingerprint(getattr(model, name)) for name in MODULES}


def _orders(seed, stream, count, epochs):
    """Planned per-epoch permutations; sequential draws equal V1's per-epoch calls."""
    rng = np.random.default_rng([seed, stream])
    return [rng.permutation(count) for _ in range(epochs)]


def _orders_fingerprint(orders):
    joined = np.concatenate(orders).astype('<i8') if orders else np.empty(0, '<i8')
    return fingerprint_payload(dict(epochs=len(orders), sha256=hashlib.sha256(joined.tobytes()).hexdigest()))


def _select_epoch(values):
    """1-based earliest epoch with the minimum value; ties keep the earliest."""
    values = np.asarray(values, float)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError('Checkpoint selection requires finite validation values')
    return int(np.argmin(values)) + 1


def _should_stop(values, patience):
    return patience is not None and len(values) - _select_epoch(values) >= patience


def _optimizer_updates(optimizer, modules):
    """Per-module min/max update count of each tensor, read from optimizer state."""
    result = {}
    for name, module in modules.items():
        counts = []
        for parameter in module.parameters():
            step = optimizer.state.get(parameter, {}).get('step', 0) if optimizer is not None else 0
            counts.append(int(step.item() if hasattr(step, 'item') else step))
        result[name] = dict(min=min(counts), max=max(counts), tensors=len(counts), source='optimizer_state')
    return result


def _peak_rss_bytes():
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == 'darwin' else peak * 1024)


def _environment(threads):
    torch = _torch()
    return dict(torch_version=str(torch.__version__), torch_threads=threads,
                deterministic_algorithms=bool(torch.are_deterministic_algorithms_enabled()),
                python=sys.version.split()[0], platform=platform.platform(),
                process_peak_rss_bytes=_peak_rss_bytes(),
                rss_scope='process high-water mark since start, not per job')


def _window_record(all_windows, windows, cap):
    return dict(eligible=len(all_windows), used=len(windows), stride=1, cap=cap,
                policy='complete_consecutive_raw_training_rows',
                subsample='evenly_spaced_chronological' if len(windows) < len(all_windows) else 'none',
                fingerprint=fingerprint_payload(dict(starts=logical_array(windows.starts),
                                                     issue_times_ns=logical_array(windows.issue_times_ns))))


def _validation_identity(validation):
    return dict(origin_count=len(validation.context.origin_ids),
                origin_fingerprint=fingerprint_payload(dict(
                    origin_ids=list(validation.context.origin_ids),
                    issue_times_ns=logical_array(validation.context.issue_times_ns))))


def _validation_metric(model, batch, settings, version, normalization):
    if version == 'normalized_pinball_v1':
        return _validation_pinball(model, batch, settings)
    torch = _torch()
    model.eval()
    accumulator = MetricAccumulator(version, settings.quantiles, normalization.target_scale)
    with torch.no_grad():
        for start in range(0, len(batch.features), settings.batch_size):
            stop = start + settings.batch_size
            if bool(batch.target_mask[start:stop].any()):
                accumulator.add(model.forecast(batch.features[start:stop], batch.feature_mask[start:stop]),
                                batch.targets[start:stop], batch.target_mask[start:stop])
    return accumulator.value()


def _train_epoch(model, order, windows, parameters, optimizer, frozen, loss_version, settings, normalization):
    """One pass over ``order``; returns (mean training loss, optimizer steps)."""
    torch = _torch()
    model.train()
    for module in frozen:
        module.eval()
    context = windows.spec.context_steps
    loss_sum, count, steps = 0., 0, 0
    for start in range(0, len(order), settings.batch_size):
        features, mask, targets, target_mask = (torch.from_numpy(x) for x in
                                                windows.take(order[start:start + settings.batch_size]))
        optimizer.zero_grad(set_to_none=True)
        quantiles = model.forecast(features[:, :context], mask[:, :context])
        loss = forecast_loss(loss_version, quantiles, targets, target_mask, settings.quantiles,
                             normalization.target_scale)
        _check_step(loss, parameters, settings, optimizer)
        steps += 1
        loss_sum += float(loss.detach()) * len(features)
        count += len(features)
    return loss_sum / count, steps


def train_downstream(model, *, trainable, frozen, windows, validation_batch, schedule, settings,
                     normalization, monitor=None, modules=None):
    """Shared downstream phase: reset AdamW, fixed or patience schedule, validation selection.

    ``settings`` supplies seed, batch_size, lr, weight_decay, gradient_clip and
    quantiles. The caller seeds Torch first. Selection uses only downstream epochs.
    """
    torch = _torch()
    for module in frozen:
        for parameter in module.parameters():
            parameter.requires_grad_(False)
    parameters = [p for module in trainable for p in module.parameters()]
    optimizer = torch.optim.AdamW(parameters, lr=settings.lr, weight_decay=settings.weight_decay)
    orders = _orders(settings.seed, 1, len(windows), schedule.downstream_epochs)
    wanted = (schedule.selection_metric,) + schedule.diagnostic_metrics
    history, values, best_state, steps, began = [], [], None, 0, time.perf_counter()
    for epoch, order in enumerate(orders, 1):
        start = time.perf_counter()
        loss, count = _train_epoch(model, order, windows, parameters, optimizer, frozen, schedule.train_loss,
                                   settings, normalization)
        steps += count
        metrics = {name: _validation_metric(model, validation_batch, settings, name, normalization)
                   for name in wanted}
        entry = dict(phase='downstream', epoch=epoch, train_loss=loss, train_loss_version=schedule.train_loss,
                     metrics=metrics, steps=steps, wall_seconds=time.perf_counter() - start)
        if monitor is not None:
            entry.update(monitor(model))
        history.append(entry)
        values.append(metrics[schedule.selection_metric])
        if _select_epoch(values) == epoch:
            best_state = _cpu_state(model.state_dict())
        if _should_stop(values, schedule.early_stopping_patience):
            break
    model.load_state_dict(best_state, strict=True)
    _finite_state(model.state_dict())
    for module in frozen:
        for parameter in module.parameters():
            parameter.requires_grad_(True)
    executed = len(history)
    phase = dict(phase='downstream', epochs_planned=schedule.downstream_epochs, epochs_executed=executed,
                 optimizer_steps=steps, examples_seen=executed * len(windows), optimizer='AdamW',
                 optimizer_reset=True, lr=settings.lr, weight_decay=settings.weight_decay,
                 parameter_updates=_optimizer_updates(optimizer, modules or {}),
                 wall_seconds=time.perf_counter() - began)
    selection = dict(partition='validation', metric=schedule.selection_metric, value=min(values),
                     epoch=_select_epoch(values), eligible_phase='downstream', tie_policy='earliest_epoch',
                     early_stopping_patience=schedule.early_stopping_patience,
                     stopped_early=executed < schedule.downstream_epochs,
                     epochs_executed=executed, epochs_planned=schedule.downstream_epochs)
    return dict(history=history, phase=phase, selection=selection, order=_orders_fingerprint(orders))


# ------------------------------------------------------------------ pretraining


def _prepare(training_slice, validation_window, config, *, require_validation=True):
    if validation_window is None and require_validation:
        raise ValueError('Checkpoint/lambda selection requires a validation partition; none was supplied')
    training = training_snapshot(training_slice)
    validation = window_snapshot(validation_window) if validation_window is not None else None
    if validation is not None:
        _validate_inputs(training, validation)
    normalization = Normalization.fit(training)
    all_windows = _windows(training, normalization, 1)
    windows = all_windows.subsample(config.max_train_windows)
    return training, validation, normalization, windows, _window_record(all_windows, windows,
                                                                        config.max_train_windows)


def _pretraining_identity(training, normalization, window_record, config):
    return dict(schema_version=SCHEMA_VERSION, architecture=config.as_dict()['architecture'],
                pretrain_epochs=config.schedule.pretrain_epochs, spec_fingerprint=training.spec.fingerprint,
                normalization_fingerprint=normalization.fingerprint, training_fingerprint=training.fingerprint,
                train_windows=window_record)


@dataclass(frozen=True, eq=False)
class PretrainingArtifact:
    """Immutable post-SSL model state shared by JEPA arms of one seed."""
    state: dict
    record: dict

    def __post_init__(self):
        keys = {'schema_version', 'identity', 'history', 'budget', 'fingerprints', 'pairing', 'state_fingerprint'}
        if not isinstance(self.record, dict) or set(self.record) != keys:
            raise ValueError('Malformed pretraining artifact record')
        record = json.loads(canonical_json(self.record))
        if record['schema_version'] != SCHEMA_VERSION or _weights_fingerprint(self.state) != record['state_fingerprint']:
            raise ValueError('Pretraining artifact weight identity differs')
        object.__setattr__(self, 'record', record)
        object.__setattr__(self, 'state', _cpu_state(self.state))

    @property
    def fingerprint(self):
        return fingerprint_payload(self.record)

    def save(self, path):
        torch = _torch()
        path = Path(path)
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(schema_version=SCHEMA_VERSION, kind='v2_jepa_pretraining',
                       record_json=canonical_json(self.record), state=self.state)
        with path.open('xb') as stream:
            torch.save(payload, stream)

    @classmethod
    def load(cls, path):
        torch = _torch()
        try:
            payload = torch.load(Path(path), map_location='cpu', weights_only=True)
        except Exception as error:
            raise ValueError('Pretraining artifact could not be loaded with weights-only deserialization') from error
        if (not isinstance(payload, dict) or set(payload) != {'schema_version', 'kind', 'record_json', 'state'}
                or payload['schema_version'] != SCHEMA_VERSION or payload['kind'] != 'v2_jepa_pretraining'):
            raise ValueError('Malformed pretraining artifact payload')
        return cls(payload['state'], json.loads(payload['record_json']))


def _pretrain(training, normalization, windows, window_record, config):
    began = time.perf_counter()
    effective = config.jepa_config
    model = _seeded_model(training.spec, effective)
    initial_state, initial = _state_fingerprint(model), _module_fingerprints(model)
    model, history = pretrain_jepa(windows, effective, model=model)
    steps = history[-1]['steps']
    derived = dict(source='v1_ssl_optimizer_definition')
    updates = {name: dict(min=count, max=count, tensors=sum(1 for _ in getattr(model, name).parameters()), **derived)
               for name, count in (('encoder', steps), ('predictor', steps), ('head', 0), ('target_encoder', 0))}
    state = _cpu_state(model.state_dict())
    budget = dict(phase='pretrain', epochs_planned=effective.pretrain_epochs, epochs_executed=len(history),
                  optimizer_steps=steps, examples_seen=len(history) * len(windows), optimizer='AdamW',
                  optimizer_reset=True, lr=effective.lr, weight_decay=effective.weight_decay,
                  parameter_updates=updates, ema_target_updates=steps,
                  wall_seconds=time.perf_counter() - began)
    record = dict(schema_version=SCHEMA_VERSION,
                  identity=_pretraining_identity(training, normalization, window_record, config),
                  history=history, budget=budget,
                  fingerprints=dict(initial=initial, after_pretrain=_module_fingerprints(model)),
                  pairing=dict(initial_state=initial_state,
                               pretrain_order=_orders_fingerprint(_orders(effective.seed, 0, len(windows),
                                                                          effective.pretrain_epochs))),
                  state_fingerprint=_weights_fingerprint(state))
    return PretrainingArtifact(state, record)


def pretrain_controlled(training_slice, config):
    """Run one seed's JEPA pretraining once, for reuse by fine-tuned and frozen arms."""
    if not isinstance(config, ControlledConfig) or config.schedule.arm not in SSL_ARMS:
        raise ValueError('Pretraining requires a ControlledConfig of a JEPA arm')
    training, _, normalization, windows, window_record = _prepare(training_slice, None, config.jepa_config,
                                                                  require_validation=False)
    return _pretrain(training, normalization, windows, window_record, config)


def _supervised_warmup(model, windows, schedule, settings, normalization, monitor):
    torch = _torch()
    began = time.perf_counter()
    _setup(settings)
    modules = {name: getattr(model, name) for name in MODULES}
    parameters = [p for name in ('encoder', 'predictor', 'head') for p in modules[name].parameters()]
    optimizer = torch.optim.AdamW(parameters, lr=settings.lr, weight_decay=settings.weight_decay)
    orders = _orders(settings.seed, 0, len(windows), schedule.warmup_epochs)
    history, steps = [], 0
    for epoch, order in enumerate(orders, 1):
        start = time.perf_counter()
        loss, count = _train_epoch(model, order, windows, parameters, optimizer, [], schedule.train_loss,
                                   settings, normalization)
        steps += count
        entry = dict(phase='supervised_warmup', epoch=epoch, train_loss=loss, train_loss_version=schedule.train_loss,
                     steps=steps, wall_seconds=time.perf_counter() - start)
        entry.update(monitor(model))
        history.append(entry)
    phase = dict(phase='supervised_warmup', epochs_planned=schedule.warmup_epochs, epochs_executed=len(history),
                 optimizer_steps=steps, examples_seen=len(history) * len(windows), optimizer='AdamW',
                 optimizer_reset=True, lr=settings.lr, weight_decay=settings.weight_decay,
                 parameter_updates=_optimizer_updates(optimizer, modules), wall_seconds=time.perf_counter() - began)
    return history, phase, _orders_fingerprint(orders)


# -------------------------------------------------------------------- training


def fit_controlled(training_slice, validation_window, config, *, pretraining=None):
    """Train one controlled arm and select its checkpoint on validation only.

    ``pretraining`` optionally supplies a ``PretrainingArtifact`` for a JEPA arm;
    its identity must match this configuration and training support exactly.
    Reuse is bitwise equivalent to recomputation. No test partition is accepted.
    """
    if not isinstance(config, ControlledConfig):
        raise ValueError('fit_controlled requires a ControlledConfig')
    schedule, effective = config.schedule, config.jepa_config
    arm = schedule.arm
    if pretraining is not None and arm not in SSL_ARMS:
        raise ValueError(f'Arm {arm} does not use a pretraining artifact')
    began = time.perf_counter()
    training, validation, normalization, windows, window_record = _prepare(training_slice, validation_window,
                                                                            effective)
    validation_batch = window_tensors(validation, normalization)
    preparation = time.perf_counter() - began
    started = time.perf_counter()
    history, phases, fingerprints = [], [], {}
    pairing = dict(pretrain_order=None, warmup_order=None)
    pretraining_record, ssl_seconds, ema_updates = None, 0., 0
    monitor = lambda model: _monitor(model, windows, effective, with_target=arm in SSL_ARMS)
    if arm in SSL_ARMS:
        identity = _pretraining_identity(training, normalization, window_record, config)
        reused = pretraining is not None
        if reused and (not isinstance(pretraining, PretrainingArtifact)
                       or json.loads(canonical_json(identity)) != pretraining.record['identity']):
            raise ValueError('Pretraining artifact identity differs from this configuration/training support')
        if not reused:
            pretraining = _pretrain(training, normalization, windows, window_record, config)
        record = pretraining.record
        if reused:
            # The seeded initial state is recomputed; post-SSL weights must equal the recorded modules.
            seeded = _seeded_model(training.spec, effective)
            if (_state_fingerprint(seeded) != record['pairing']['initial_state']
                    or _module_fingerprints(seeded) != record['fingerprints']['initial']):
                raise ValueError('Pretraining artifact identity differs: initial state is not this seed\'s')
        model = build_jepa_model(training.spec, effective)
        model.load_state_dict(_cpu_state(pretraining.state), strict=True)
        if _module_fingerprints(model) != record['fingerprints']['after_pretrain']:
            raise ValueError('Pretraining artifact identity differs: weights do not match recorded modules')
        history.extend(record['history'])
        phases.append(record['budget'])
        fingerprints.update(record['fingerprints'])
        pairing.update(initial_state=record['pairing']['initial_state'],
                       pretrain_order=record['pairing']['pretrain_order'])
        ssl_seconds, ema_updates = record['budget']['wall_seconds'], record['budget']['ema_target_updates']
        pretraining_record = dict(reused=reused, artifact_fingerprint=pretraining.fingerprint,
                                  wall_seconds=ssl_seconds)
    else:
        model = _seeded_model(training.spec, effective)
        pairing['initial_state'] = _state_fingerprint(model)
        fingerprints['initial'] = _module_fingerprints(model)
        if arm == 'supervised_extra_updates':
            warm_history, phase, pairing['warmup_order'] = _supervised_warmup(
                model, windows, schedule, effective, normalization, monitor)
            history.extend(warm_history)
            phases.append(phase)
            fingerprints['after_warmup'] = _module_fingerprints(model)
    _setup(effective)
    frozen = arm in FROZEN_ARMS
    result = train_downstream(
        model, trainable=[model.head] if frozen else [model.encoder, model.predictor, model.head],
        frozen=[model.encoder, model.predictor] if frozen else [], windows=windows,
        validation_batch=validation_batch, schedule=schedule, settings=effective, normalization=normalization,
        monitor=monitor, modules={name: getattr(model, name) for name in MODULES})
    history.extend(result['history'])
    phases.append(result['phase'])
    fingerprints['selected'] = _module_fingerprints(model)
    pairing['downstream_order'] = result['order']
    totals = dict(optimizer_steps=sum(p['optimizer_steps'] for p in phases),
                  examples_seen=sum(p['examples_seen'] for p in phases),
                  parameter_updates={name: sum(p['parameter_updates'][name]['max'] for p in phases)
                                     for name in MODULES},
                  ema_target_updates=ema_updates)
    training_seconds = time.perf_counter() - started
    record = dict(
        schema_version=SCHEMA_VERSION, model_id=f'v2_{arm}', model_kind=MODEL_KIND, arm=arm,
        scientific_status='EXPERIMENTAL_UNVALIDATED', config=config.as_dict(),
        recipe_fingerprint=config.recipe_fingerprint, run_fingerprint=config.run_fingerprint, seed=config.seed,
        spec_fingerprint=training.spec.fingerprint, normalization_fingerprint=normalization.fingerprint,
        training_fingerprint=training.fingerprint, training_dataset_fingerprint=training.context.dataset_fingerprint,
        train_windows=window_record,
        validation=_validation_identity(validation),
        rng_streams=RNG_STREAMS, pairing=pairing, fingerprints=fingerprints, pretraining=pretraining_record,
        history=history, budget=dict(phases=phases, totals=totals), selection=result['selection'],
        parameters=_parameter_counts(model), environment=_environment(effective.threads),
        wall_seconds=dict(preparation=preparation, this_call_training=training_seconds,
                          attributed_training=training_seconds + (ssl_seconds if pretraining_record
                                                                  and pretraining_record['reused'] else 0.),
                          scope='SSL/warmup/downstream incl. monitoring and validation selection; '
                                'excludes data preparation and final inference; attributed_training '
                                'includes reused SSL time, so do not sum it across arms sharing one artifact'))
    return QuantileForecaster(model, normalization, record, quantiles=effective.quantiles,
                              batch_size=effective.batch_size)


def check_paired_cohort(records):
    """Verify that controlled-arm records of each seed form a valid paired cohort.

    Arms of one seed must share initial state, window subset, training support,
    normalization, validation (selection) support, downstream order and
    downstream schedule; every arm's
    architecture must be identical up to the seed. The extra-update control must
    replay the JEPA SSL order and step count, and frozen JEPA must reuse the
    fine-tuned arm's SSL artifact. Returns a summary; raises ValueError listing
    every violation. Schedules are configured independently, so this is the
    enforcement point for budget matching.
    """
    records = [json.loads(canonical_json(r)) for r in records]
    if not records or any(r.get('model_kind') != MODEL_KIND for r in records):
        raise ValueError('A nonempty list of controlled-arm records is required')
    problems, seeds = [], {}
    architectures = {canonical_json({k: v for k, v in r['config']['architecture'].items() if k != 'seed'})
                     for r in records}
    if len(architectures) != 1:
        problems.append('architectures differ beyond the seed')
    downstream = {canonical_json({k: r['config']['schedule'][k] for k in (
        'downstream_epochs', 'early_stopping_patience', 'train_loss', 'selection_metric')}) for r in records}
    if len(downstream) != 1:
        problems.append('downstream schedules or objectives differ')
    for record in records:
        seeds.setdefault(record['seed'], {}).setdefault(record['arm'], []).append(record)
    for seed, arms in sorted(seeds.items()):
        if any(len(v) != 1 for v in arms.values()):
            problems.append(f'seed {seed}: duplicate arm records')
        members = [v[0] for v in arms.values()]
        for key in ('training_fingerprint', 'normalization_fingerprint', 'train_windows', 'validation'):
            if len({canonical_json(m[key]) for m in members}) != 1:
                problems.append(f'seed {seed}: {key} differs')
        for key in ('initial_state', 'downstream_order'):
            if len({m['pairing'][key] for m in members}) != 1:
                problems.append(f'seed {seed}: {key} differs')
        jepa, extra, frozen = (arms.get(a, [None])[0] for a in ('jepa_finetune', 'supervised_extra_updates',
                                                                 'jepa_frozen'))
        steps = lambda r, phase: sum(p['optimizer_steps'] for p in r['budget']['phases'] if p['phase'] == phase)
        if jepa and extra and (extra['pairing']['warmup_order'] != jepa['pairing']['pretrain_order']
                               or steps(extra, 'supervised_warmup') != steps(jepa, 'pretrain')):
            problems.append(f'seed {seed}: extra-update warmup does not replay the JEPA SSL order/steps')
        if jepa and frozen and (jepa['pretraining']['artifact_fingerprint']
                                != frozen['pretraining']['artifact_fingerprint']):
            problems.append(f'seed {seed}: frozen JEPA does not reuse the fine-tuned arm\'s SSL artifact')
    if problems:
        raise ValueError('Paired cohort check failed: ' + '; '.join(problems))
    return dict(seeds=sorted(seeds), arms=sorted({r['arm'] for r in records}), records=len(records))


# ------------------------------------------------------------- shared inference


class QuantileForecaster:
    """Selected V2 model plus train-fitted normalization; context-only prediction.

    ``rearrange`` sorts the predicted quantiles per cell before the inverse
    transform (used only by models without monotone construction); the raw
    crossing fraction of the latest prediction is kept on ``last_crossing_fraction``.
    """

    def __init__(self, model, normalization, record, *, quantiles, batch_size, rearrange=False):
        if record.get('model_kind') not in _BUILDERS:
            raise ValueError('Unknown V2 model kind')
        self.model = model.to('cpu').eval()
        self.normalization = normalization
        self.quantiles = tuple(float(x) for x in quantiles)
        self.batch_size = batch_size
        self.rearrange = rearrange
        self.last_crossing_fraction = None
        self._record = json.loads(canonical_json(record))

    @property
    def record(self):
        return json.loads(canonical_json(self._record))

    @property
    def model_id(self):
        return self._record['model_id']

    def predict(self, context, future_grid):
        torch = _torch()
        context, future_grid = _context_grid(context, future_grid)
        spec = context.spec
        if spec.fingerprint != self.normalization.spec.fingerprint:
            raise ValueError('Prediction spec identity differs from the trained normalization/spec identity')
        shape = (spec.horizon_steps, len(spec.target_names), len(self.quantiles))
        output, crossings, cells = [], 0, 0
        self.model.eval()
        with torch.inference_mode():
            for start in range(0, len(context.origin_ids), self.batch_size):
                stop = min(start + self.batch_size, len(context.origin_ids))
                values = self.normalization.normalize(context.values[start:stop], context.mask[start:stop], 'feature')
                features = torch.tensor(values, dtype=torch.float32)
                mask = torch.tensor(context.mask[start:stop].copy(), dtype=torch.bool)
                if not bool(torch.isfinite(features).all()):
                    raise ValueError('Nonfinite prediction tensor')
                predicted = self.model.forecast(features, mask)
                if tuple(predicted.shape) != (stop - start,) + shape or not bool(torch.isfinite(predicted).all()):
                    raise ValueError('Nonfinite or malformed model output')
                predicted = predicted.cpu().numpy().astype(float)
                crossings += int((np.diff(predicted, axis=-1) < 0).any(axis=-1).sum())
                cells += int(np.prod(predicted.shape[:-1]))
                output.append(np.sort(predicted, axis=-1) if self.rearrange else predicted)
        self.last_crossing_fraction = crossings / cells if cells else None
        normalized = np.concatenate(output) if output else np.empty((0,) + shape)
        native = self.normalization.inverse_targets(normalized.transpose(0, 1, 3, 2)).transpose(0, 1, 3, 2)
        if not np.isfinite(native).all() or (np.diff(native, axis=-1) < 0).any():
            raise ValueError('Nonfinite or crossing native quantiles')
        median = self.quantiles.index(.5)
        return ForecastPrediction(native[..., median], future_grid, self.model_id, quantile_levels=self.quantiles,
                                  quantiles=native, point_interpretation='inverse_transformed_point'
                                  if spec.transform == 'log10' else 'native_point')

    def save(self, path):
        torch = _torch()
        path = Path(path)
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
        state = _cpu_state(self.model.state_dict())
        payload = dict(schema_version=SCHEMA_VERSION, model_kind=self._record['model_kind'],
                       model_id=self.model_id, record_json=canonical_json(self._record),
                       normalization_json=canonical_json(self.normalization.as_dict()), model_state=state,
                       weights_fingerprint=_weights_fingerprint(state), torch_version=str(torch.__version__))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            torch.save(payload, stream)


def _jepa_builder(spec, record):
    config = ControlledConfig.from_dict(record['config'])
    if (record.get('arm') != config.schedule.arm or record.get('model_id') != f'v2_{config.schedule.arm}'
            or record.get('run_fingerprint') != config.run_fingerprint):
        raise ValueError('Controlled JEPA checkpoint arm/configuration identity differs')
    return build_jepa_model(spec, config.jepa_config), dict(quantiles=config.architecture.quantiles,
                                                           batch_size=config.architecture.batch_size)


_BUILDERS = {MODEL_KIND: _jepa_builder}


def register_builder(kind, builder):
    """Register ``builder(spec, record) -> (module, predictor kwargs)`` for checkpoint loading."""
    if kind in _BUILDERS and _BUILDERS[kind] is not builder:
        raise ValueError(f'Model kind {kind!r} is already registered')
    _BUILDERS[kind] = builder


def load_forecaster(path):
    """Safe weights-only load of any registered V2 forecaster with identity checks."""
    torch = _torch()
    importlib.import_module('solar_flare_jepa.training.comparators')  # registers comparator kinds
    try:
        payload = torch.load(Path(path), map_location='cpu', weights_only=True)
    except Exception as error:
        raise ValueError('Checkpoint could not be loaded with safe weights-only deserialization') from error
    required = {'schema_version', 'model_kind', 'model_id', 'record_json', 'normalization_json', 'model_state',
                'weights_fingerprint', 'torch_version'}
    if not isinstance(payload, dict) or set(payload) != required or payload['schema_version'] != SCHEMA_VERSION:
        raise ValueError('Malformed V2 checkpoint payload')
    if payload['model_kind'] not in _BUILDERS:
        raise ValueError('Unsupported V2 model kind')
    record = json.loads(payload['record_json'])
    normalization = Normalization.from_dict(json.loads(payload['normalization_json']))
    if (record.get('model_kind') != payload['model_kind'] or record.get('model_id') != payload['model_id']
            or record.get('normalization_fingerprint') != normalization.fingerprint
            or record.get('spec_fingerprint') != normalization.spec.fingerprint):
        raise ValueError('V2 checkpoint internal identity differs')
    state = payload['model_state']
    if _weights_fingerprint(state) != payload['weights_fingerprint']:
        raise ValueError('V2 checkpoint weight identity differs')
    model, options = _BUILDERS[payload['model_kind']](normalization.spec, record)
    try:
        model.load_state_dict(state, strict=True)
    except (RuntimeError, KeyError) as error:
        raise ValueError('Incompatible V2 checkpoint state') from error
    _verify_selected_weights(model, record)
    return QuantileForecaster(model, normalization, record, **options)


def _verify_selected_weights(model, record):
    """Bind loaded weights to the record so one arm's record cannot carry another's weights."""
    selected = record.get('fingerprints', {}).get('selected')
    if selected is not None:
        actual = {name: _state_fingerprint(getattr(model, name)) for name in selected}
    elif 'lambda_candidates' in record:
        chosen = [c for c in record['lambda_candidates'] if c['lambda'] == record['selection']['lambda']]
        selected, actual = [c['weights_fingerprint'] for c in chosen], [_state_fingerprint(model)]
    else:
        raise ValueError('V2 checkpoint record has no selected-weight identity')
    if actual != selected:
        raise ValueError('V2 checkpoint weights differ from the record\'s selected weights')
