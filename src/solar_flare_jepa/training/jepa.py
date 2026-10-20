"""Small temporal JEPA forecaster with monotone quantile output (optional Torch).

Scope and semantics
-------------------
* Inputs are the existing P1 contracts and the train-fitted ``Normalization``.
  Values are standardized after the declared spec transform (``log10(flux/ref)``
  for GOES XRS); invalid cells are zero in tensors and always accompanied by an
  explicit boolean mask, so a missing cell is distinguishable from an observed
  training-mean value.
* Self-supervised windows come only from the canonical raw training arrays of a
  ``TrainingSlice`` (training partition only). Validation monitors fine-tuning
  and selects checkpoints; no function here accepts a test partition.
* The target (EMA) encoder sees true future features during training only.
  ``TrainedJepa.predict`` uses the context encoder, predictor and head, never the
  target encoder, and never receives future values.
* Quantiles are produced in standardized transformed space and mapped to native
  units by the monotone inverse transform. The median is reported as the point
  value (``inverse_transformed_point`` for log transforms). No calibration or
  scientific forecast skill is asserted by this module.

Package import does not import Torch; every Torch use goes through ``_torch()``.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import math
from pathlib import Path
import time

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, canonical_json, fingerprint_payload,
)
from .core import (_context_grid, _cpu_state, _finite_state, _torch, _weights_fingerprint,
                   tensor_batch, window_snapshot)
from .normalization import Normalization, training_snapshot

VARIANTS = ('jepa_finetune', 'jepa_frozen', 'supervised')
MODEL_IDS = {'jepa_finetune': 'jepa_finetune', 'jepa_frozen': 'jepa_frozen',
             'supervised': 'supervised_transformer'}
MODEL_KIND = 'temporal_jepa_quantile'
SCHEMA_VERSION = 1


# --------------------------------------------------------------------------- config

@dataclass(frozen=True)
class JepaConfig:
    """Explicit, bounded hyperparameters. ``max_train_windows=None`` means no cap."""
    patch_steps: int = 5
    width: int = 64
    depth: int = 3
    heads: int = 4
    predictor_depth: int = 2
    mlp_ratio: int = 4
    head_hidden: int = 256
    dropout: float = 0.0
    ema_start: float = 0.996
    ema_end: float = 1.0
    quantiles: tuple = (0.05, 0.25, 0.5, 0.75, 0.95)
    pretrain_epochs: int = 10
    finetune_epochs: int = 20
    batch_size: int = 256
    lr: float = 1e-3
    weight_decay: float = 1e-4
    gradient_clip: float = 1.0
    patience: int = 3
    seed: int = 17
    max_train_windows: int | None = None
    threads: int = 8
    jepa_weight_during_finetune: float = 0.0
    jepa_loss: str = 'smooth_l1'
    context_block_mask: bool = False
    context_mask_patches: int = 4
    monitor_windows: int = 2048

    def __post_init__(self):
        ints = {'patch_steps': (1, 120), 'width': (8, 512), 'depth': (1, 8), 'heads': (1, 16),
                'predictor_depth': (1, 8), 'mlp_ratio': (1, 8), 'head_hidden': (8, 4096),
                'pretrain_epochs': (0, 500), 'finetune_epochs': (1, 500), 'batch_size': (1, 4096),
                'patience': (1, 500), 'seed': (0, 2**32 - 1), 'threads': (1, 256),
                'context_mask_patches': (1, 256), 'monitor_windows': (1, 65536)}
        for name, (lower, upper) in ints.items():
            value = getattr(self, name)
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError(f'{name} must be a bounded integer in [{lower}, {upper}]')
        cap = self.max_train_windows
        if cap is not None and (type(cap) is not int or not 1 <= cap <= 10**8):
            raise ValueError('max_train_windows must be None or a bounded positive integer')
        if self.width % self.heads:
            raise ValueError('width must be divisible by heads')
        floats = {'dropout': (0., .5, True), 'ema_start': (0., 1., False), 'ema_end': (0., 1., False),
                  'lr': (0., 1., False), 'weight_decay': (0., 1., True),
                  'gradient_clip': (0., 1000., False), 'jepa_weight_during_finetune': (0., 100., True)}
        for name, (lower, upper, closed) in floats.items():
            value = getattr(self, name)
            if (type(value) not in (int, float) or not np.isfinite(value) or value > upper
                    or value < lower or (not closed and value == lower)):
                raise ValueError(f'{name} must be finite within bounds ({lower}, {upper}]')
            object.__setattr__(self, name, float(value))
        if self.ema_end < self.ema_start:
            raise ValueError('ema_end must be at least ema_start')
        if type(self.context_block_mask) is not bool:
            raise ValueError('context_block_mask must be a boolean')
        if self.jepa_loss not in ('smooth_l1', 'mse'):
            raise ValueError('jepa_loss must be smooth_l1 or mse')
        if not isinstance(self.quantiles, (list, tuple)) or not self.quantiles:
            raise ValueError('quantiles require an explicit ordered list')
        levels = tuple(float(x) for x in self.quantiles if type(x) in (int, float))
        if (len(levels) != len(self.quantiles) or not np.isfinite(levels).all() or min(levels) <= 0
                or max(levels) >= 1 or any(a >= b for a, b in zip(levels, levels[1:]))
                or .5 not in levels or len(levels) > 99):
            raise ValueError('quantiles must be strictly increasing in (0,1) and include 0.5')
        object.__setattr__(self, 'quantiles', levels)

    def as_dict(self):
        result = asdict(self)
        result['quantiles'] = list(self.quantiles)
        return result

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())


def _dimensions(spec, config):
    """Patch geometry derived from the forecast spec; never inferred from data."""
    p = config.patch_steps
    if spec.context_steps % p or spec.horizon_steps % p:
        raise ValueError('context_steps and horizon_steps must be divisible by patch_steps')
    if len(spec.feature_names) != len(spec.target_names):
        raise ValueError('JEPA future latents require equal feature/target channel counts')
    context_patches, future_patches = spec.context_steps // p, spec.horizon_steps // p
    if config.context_block_mask and config.context_mask_patches >= context_patches:
        raise ValueError('context_mask_patches must leave at least one visible context patch')
    return context_patches, future_patches


# ----------------------------------------------------------------------- windows

@dataclass(frozen=True, eq=False)
class TrainWindows:
    """Normalized raw training rows plus eligible sliding-window start rows.

    Row arrays are float32 normalized values (0 where invalid) and boolean masks
    over the raw training partition only. Window ``i`` covers rows
    ``starts[i] : starts[i] + context_steps + horizon_steps``; its first
    ``context_steps`` rows are the context and the rest the future/targets.
    """
    spec: ForecastSpec
    row_features: np.ndarray
    row_feature_mask: np.ndarray
    row_targets: np.ndarray
    row_target_mask: np.ndarray
    starts: np.ndarray
    issue_times_ns: np.ndarray

    @property
    def length(self):
        return self.spec.context_steps + self.spec.horizon_steps

    def __len__(self):
        return len(self.starts)

    def take(self, indices):
        """Return (features [B,C+H,F], feature_mask, targets [B,H,K], target_mask)."""
        starts = self.starts[np.asarray(indices, dtype=np.int64)]
        length, context = self.length, self.spec.context_steps
        out = []
        for array in (self.row_features, self.row_feature_mask):
            out.append(np.ascontiguousarray(
                sliding_window_view(array, length, axis=0)[starts].transpose(0, 2, 1)))
        for array in (self.row_targets, self.row_target_mask):
            out.append(np.ascontiguousarray(
                sliding_window_view(array[context:], self.spec.horizon_steps, axis=0)[starts].transpose(0, 2, 1)))
        return tuple(out)

    def subsample(self, maximum):
        """Deterministic evenly spaced chronological subset (no randomness)."""
        if maximum is None or maximum >= len(self):
            return self
        keep = (np.arange(maximum, dtype=np.int64) * len(self)) // maximum
        return replace(self, starts=self.starts[keep], issue_times_ns=self.issue_times_ns[keep])


def training_windows(training_slice, normalization, stride=1):
    """Sliding windows over the canonical raw training rows (no held-out rows).

    A window is eligible only if all ``context+horizon`` rows are consecutive on
    the declared cadence (no gap is bridged), every context feature mask and
    every target mask is true (the ``complete`` policy), and, when raw
    availability is declared, every context cell was available by issue time.
    Future-row feature masks are carried, not required: those rows feed only the
    training-time target encoder.
    """
    return _windows(training_snapshot(training_slice), normalization, stride)


def _windows(training, normalization, stride):
    """``training_windows`` body for an already validated ``TrainingSlice`` snapshot."""
    spec = training.spec
    if not isinstance(normalization, Normalization) or normalization.spec.fingerprint != spec.fingerprint:
        raise ValueError('Training windows require the train-fitted normalization of this spec')
    if type(stride) is not int or stride < 1:
        raise ValueError('stride must be a positive integer')
    context, horizon = spec.context_steps, spec.horizon_steps
    length = context + horizon
    starts_ns = training.raw_starts_ns
    rows = len(starts_ns)
    if rows < length:
        raise ValueError('Raw training partition is shorter than one window')
    consecutive = np.diff(starts_ns) == spec.cadence_ns
    ok = sliding_window_view(consecutive, length - 1).all(axis=-1)
    ok &= sliding_window_view(training.raw_feature_mask.all(axis=1), context).all(axis=-1)[:rows - length + 1]
    ok &= sliding_window_view(training.raw_target_mask.all(axis=1)[context:], horizon).all(axis=-1)
    issues = starts_ns[context:context + rows - length + 1]
    if training.raw_availability_ns is not None:
        latest = training.raw_availability_ns.max(axis=1)
        ok &= sliding_window_view(latest, context).max(axis=-1)[:rows - length + 1] <= issues
    ok &= ((issues - int(starts_ns[0])) // spec.cadence_ns) % stride == 0
    starts = np.flatnonzero(ok).astype(np.int64)
    if not len(starts):
        raise ValueError('No eligible raw training windows')
    features = normalization.normalize(training.raw_features, training.raw_feature_mask, 'feature')
    targets = normalization.normalize(training.raw_targets, training.raw_target_mask, 'target')
    return TrainWindows(spec, features.astype(np.float32), training.raw_feature_mask.copy(),
                        targets.astype(np.float32), training.raw_target_mask.copy(),
                        starts, issues[starts].astype(np.int64))


def window_tensors(window, normalization, *, device='cpu'):
    """All origins of a P1 ``WindowedPartition`` as normalized tensors (validation)."""
    count = len(window.context.origin_ids)
    if not count:
        raise ValueError('No origins in window partition')
    return tensor_batch(window, normalization, list(range(count)), device=device)


# ------------------------------------------------------------------------- model

def build_jepa_model(spec, config):
    """Context encoder, EMA target encoder, latent predictor and quantile head."""
    torch = _torch()
    nn, F = torch.nn, torch.nn.functional
    context_patches, future_patches = _dimensions(spec, config)
    total = context_patches + future_patches
    channels = len(spec.feature_names)
    targets, levels = len(spec.target_names), len(config.quantiles)
    width, p = config.width, config.patch_steps

    def blocks(depth):
        layer = nn.TransformerEncoderLayer(width, config.heads, width * config.mlp_ratio, config.dropout,
                                           activation='gelu', batch_first=True, norm_first=True)
        return nn.TransformerEncoder(layer, depth, enable_nested_tensor=False)

    class PatchEncoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Linear(p * 2 * channels, width)
            self.position = nn.Parameter(torch.zeros(1, total, width))
            nn.init.trunc_normal_(self.position, std=.02)
            self.blocks = blocks(config.depth)
            self.norm = nn.LayerNorm(width)

        def forward(self, patches, positions):
            return self.norm(self.blocks(self.embed(patches) + self.position[:, positions]))

    class Predictor(nn.Module):
        def __init__(self):
            super().__init__()
            self.project = nn.Linear(width, width)
            self.mask_token = nn.Parameter(torch.zeros(1, 1, width))
            self.position = nn.Parameter(torch.zeros(1, total, width))
            nn.init.trunc_normal_(self.mask_token, std=.02)
            nn.init.trunc_normal_(self.position, std=.02)
            self.blocks = blocks(config.predictor_depth)
            self.norm = nn.LayerNorm(width)
            self.out = nn.Linear(width, width)

        def forward(self, latents, visible, wanted):
            queries = self.mask_token.expand(len(latents), len(wanted), -1) + self.position[:, wanted]
            tokens = torch.cat((self.project(latents) + self.position[:, visible], queries), dim=1)
            return self.out(self.norm(self.blocks(tokens)[:, -len(wanted):]))

    class QuantileHead(nn.Module):
        def __init__(self):
            super().__init__()
            size = width * (1 + future_patches)
            self.net = nn.Sequential(nn.LayerNorm(size), nn.Linear(size, config.head_hidden), nn.GELU(),
                                     nn.Linear(config.head_hidden, spec.horizon_steps * targets * levels))

        def forward(self, context_latents, future_latents):
            joined = torch.cat((context_latents.mean(dim=1), future_latents.flatten(1)), dim=1)
            raw = self.net(joined).reshape(len(joined), spec.horizon_steps, targets, levels)
            # Monotone by construction: base plus cumulative positive increments.
            return torch.cat((raw[..., :1], raw[..., :1] + F.softplus(raw[..., 1:]).cumsum(dim=-1)), dim=-1)

    class JepaForecaster(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = PatchEncoder()
            self.target_encoder = deepcopy(self.encoder)
            for parameter in self.target_encoder.parameters():
                parameter.requires_grad_(False)
            self.predictor = Predictor()
            self.head = QuantileHead()
            self.register_buffer('context_positions', torch.arange(context_patches), persistent=False)
            self.register_buffer('future_positions', torch.arange(context_patches, total), persistent=False)
            self.register_buffer('all_positions', torch.arange(total), persistent=False)

        @staticmethod
        def patchify(values, mask):
            joined = torch.cat((values, mask.to(values.dtype)), dim=-1)
            return joined.reshape(len(joined), joined.shape[1] // p, p * 2 * channels)

        def forecast(self, features, feature_mask, *, return_latents=False):
            """Context-only inference path: [B,C,F] -> normalized quantiles [B,H,K,Q]."""
            if (features.shape != feature_mask.shape or feature_mask.dtype != torch.bool
                    or tuple(features.shape[1:]) != (spec.context_steps, channels)):
                raise ValueError('Forecast input must be context-only [B, context_steps, features]')
            latents = self.encoder(self.patchify(features, feature_mask), self.context_positions)
            future = self.predictor(latents, self.context_positions, self.future_positions)
            quantiles = self.head(latents, future)
            return (quantiles, latents, future) if return_latents else quantiles

        def jepa_loss(self, features, feature_mask, *, generator=None, block_mask=False):
            """Training-only latent loss; ``features`` include true future rows."""
            if (features.shape != feature_mask.shape or feature_mask.dtype != torch.bool
                    or tuple(features.shape[1:]) != (spec.context_steps + spec.horizon_steps, channels)):
                raise ValueError('JEPA input must be [B, context_steps + horizon_steps, features]')
            patches = self.patchify(features, feature_mask)
            with torch.no_grad():
                full = self.target_encoder(patches, self.all_positions)
                full = F.layer_norm(full, (width,))
            visible, wanted = self.context_positions, self.future_positions
            if block_mask:
                count = config.context_mask_patches
                first = int(torch.randint(0, context_patches - count + 1, (1,), generator=generator))
                hidden = torch.arange(first, first + count, device=patches.device)
                keep = torch.ones(context_patches, dtype=torch.bool, device=patches.device)
                keep[hidden] = False
                visible = self.context_positions[keep]
                wanted = torch.cat((hidden, self.future_positions))
            latents = self.encoder(patches[:, visible], visible)
            predicted = self.predictor(latents, visible, wanted)
            target = full[:, wanted]
            if config.jepa_loss == 'mse':
                loss = F.mse_loss(predicted, target)
            else:
                loss = F.smooth_l1_loss(predicted, target)
            return loss, full[:, self.future_positions]

        @torch.no_grad()
        def update_target(self, momentum):
            for target, online in zip(self.target_encoder.parameters(), self.encoder.parameters()):
                target.mul_(momentum).add_(online.detach(), alpha=1. - momentum)

    return JepaForecaster()


def pinball_loss(quantiles, targets, mask, levels):
    """Mean pinball loss over valid target cells and all quantile levels."""
    torch = _torch()
    if (quantiles.shape[:-1] != targets.shape or mask.shape != targets.shape or mask.dtype != torch.bool
            or quantiles.shape[-1] != len(levels)):
        raise ValueError('Pinball quantile/target/mask shape differs')
    if not bool(mask.any()):
        raise ValueError('No valid supervision cells in batch')
    tau = torch.as_tensor(levels, dtype=quantiles.dtype, device=quantiles.device)
    error = targets.unsqueeze(-1) - quantiles
    loss = torch.maximum(tau * error, (tau - 1.) * error)[mask]
    value = loss.mean()
    if not bool(torch.isfinite(value)):
        raise ValueError('Nonfinite pinball loss')
    return value


def _latent_stats(latents):
    """Mean per-dimension std across samples and entropy effective rank."""
    torch = _torch()
    latents = latents.detach().double().reshape(-1, latents.shape[-1])
    std = float(latents.std(dim=0, unbiased=False).mean())
    values = torch.linalg.svdvals(latents - latents.mean(dim=0))
    total = float(values.sum())
    if total <= 0:
        return std, 0.
    share = values / total
    share = share[share > 0]
    return std, float(torch.exp(-(share * share.log()).sum()))


def _parameter_counts(model):
    def count(module, trainable_only=False):
        return int(sum(p.numel() for p in module.parameters() if p.requires_grad or not trainable_only))
    return dict(encoder=count(model.encoder), target_encoder_ema=count(model.target_encoder),
                predictor=count(model.predictor), head=count(model.head),
                trainable_total=count(model.encoder) + count(model.predictor) + count(model.head))


def _setup(config):
    import random
    torch = _torch()
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.set_num_threads(config.threads)
    torch.use_deterministic_algorithms(True)


def _check_step(loss, parameters, config, optimizer):
    torch = _torch()
    if not bool(torch.isfinite(loss)):
        raise ValueError('Nonfinite training loss')
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(parameters, config.gradient_clip, error_if_nonfinite=True)
    if not bool(torch.isfinite(norm)):
        raise ValueError('Nonfinite gradient norm')
    optimizer.step()


def _monitor(model, windows, config, *, with_target):
    """Collapse diagnostics on a fixed, evenly spaced chronological train subset."""
    torch = _torch()
    subset = windows.subsample(config.monitor_windows)
    stats = {}
    was_training = model.training
    model.eval()
    context_latents, target_latents = [], []
    with torch.no_grad():
        for start in range(0, len(subset), config.batch_size):
            idx = np.arange(start, min(start + config.batch_size, len(subset)))
            features, mask, _, _ = subset.take(idx)
            features, mask = torch.from_numpy(features), torch.from_numpy(mask)
            context = features[:, :windows.spec.context_steps]
            cmask = mask[:, :windows.spec.context_steps]
            context_latents.append(model.encoder(model.patchify(context, cmask), model.context_positions).mean(dim=1))
            if with_target:
                full = model.target_encoder(model.patchify(features, mask), model.all_positions)
                full = torch.nn.functional.layer_norm(full, (full.shape[-1],))
                target_latents.append(full[:, model.future_positions].reshape(-1, full.shape[-1]))
    stats['context_latent_std'], stats['context_effective_rank'] = _latent_stats(torch.cat(context_latents))
    if with_target:
        stats['target_latent_std'], stats['target_effective_rank'] = _latent_stats(torch.cat(target_latents))
    model.train(was_training)
    return stats


# --------------------------------------------------------------------- training

def _seeded_model(spec, config):
    _setup(config)
    return build_jepa_model(spec, config)


def pretrain_jepa(train_windows, config, *, model=None):
    """JEPA latent loss only, on training windows, with a linear EMA momentum schedule.

    Returns ``(model, history)``. The target encoder receives no gradient.
    """
    torch = _torch()
    if not isinstance(train_windows, TrainWindows) or not len(train_windows):
        raise ValueError('pretrain_jepa requires nonempty TrainWindows')
    config = JepaConfig(**config.as_dict())
    model = _seeded_model(train_windows.spec, config) if model is None else model
    _setup(config)
    parameters = list(model.encoder.parameters()) + list(model.predictor.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=config.lr, weight_decay=config.weight_decay)
    rng = np.random.default_rng([config.seed, 0])
    generator = torch.Generator().manual_seed(config.seed + 2)
    per_epoch = math.ceil(len(train_windows) / config.batch_size)
    total, steps, history = per_epoch * config.pretrain_epochs, 0, []
    for epoch in range(1, config.pretrain_epochs + 1):
        began, loss_sum, count = time.perf_counter(), 0., 0
        model.train()
        order = rng.permutation(len(train_windows))
        momentum = config.ema_start
        for start in range(0, len(order), config.batch_size):
            features, mask, _, _ = train_windows.take(order[start:start + config.batch_size])
            optimizer.zero_grad(set_to_none=True)
            loss, _ = model.jepa_loss(torch.from_numpy(features), torch.from_numpy(mask),
                                      generator=generator, block_mask=config.context_block_mask)
            _check_step(loss, parameters, config, optimizer)
            steps += 1
            momentum = config.ema_start + (config.ema_end - config.ema_start) * steps / total
            model.update_target(momentum)
            loss_sum += float(loss.detach()) * len(features)
            count += len(features)
        entry = dict(phase='pretrain', epoch=epoch, train_jepa_loss=loss_sum / count, steps=steps,
                     ema_momentum=momentum, wall_seconds=time.perf_counter() - began)
        entry.update(_monitor(model, train_windows, config, with_target=True))
        history.append(entry)
    _finite_state(model.state_dict())
    return model, history


def _validate_inputs(training, validation):
    if validation.as_dict().get('partition', {}).get('name') != 'validation':
        raise ValueError('Checkpoint monitoring requires the validation partition')
    if (validation.context.dataset_fingerprint != training.context.dataset_fingerprint
            or validation.context.spec.fingerprint != training.spec.fingerprint):
        raise ValueError('Validation training dataset/spec identity differs')
    if (validation.context.starts_ns < training.partition_end_ns).any():
        raise ValueError('Validation context overlaps raw training partition')


def _validation_pinball(model, batch, config):
    torch = _torch()
    model.eval()
    total, cells = 0., 0
    with torch.no_grad():
        for start in range(0, len(batch.features), config.batch_size):
            stop = start + config.batch_size
            quantiles = model.forecast(batch.features[start:stop], batch.feature_mask[start:stop])
            mask = batch.target_mask[start:stop]
            if not bool(mask.any()):
                continue
            count = int(mask.sum()) * len(config.quantiles)
            total += float(pinball_loss(quantiles, batch.targets[start:stop], mask, config.quantiles)) * count
            cells += count
    if not cells or not np.isfinite(total):
        raise ValueError('Validation has no valid finite target support')
    return total / cells


def fit_forecaster(training_slice, validation_window, config=None, variant='jepa_finetune', seed=None):
    """Train one variant; select the checkpoint by validation pinball only.

    ``jepa_finetune``: JEPA pretraining, then all weights fine-tuned with pinball
    (+ optional JEPA term). ``jepa_frozen``: JEPA pretraining, then only the head
    is trained. ``supervised``: identical architecture and initialization seed,
    no pretraining, pinball only. Ties keep the earliest epoch; training stops
    after ``patience`` epochs without validation improvement.
    """
    torch = _torch()
    if variant not in VARIANTS:
        raise ValueError(f'variant must be one of {VARIANTS}')
    config = JepaConfig() if config is None else JepaConfig(**config.as_dict())
    if seed is not None:
        config = replace(config, seed=seed)
    if variant != 'supervised' and config.pretrain_epochs < 1:
        raise ValueError('JEPA variants require at least one pretraining epoch')
    began = time.perf_counter()
    training = training_snapshot(training_slice)
    validation = window_snapshot(validation_window)
    _validate_inputs(training, validation)
    normalization = Normalization.fit(training)
    all_windows = _windows(training, normalization, 1)
    windows = all_windows.subsample(config.max_train_windows)
    val_batch = window_tensors(validation, normalization)

    if variant == 'supervised':
        model, pre_history = _seeded_model(training.spec, config), []
    else:
        model, pre_history = pretrain_jepa(windows, config)
    pretrained = dict(encoder=_weights_fingerprint(_cpu_state(model.encoder.state_dict())),
                      predictor=_weights_fingerprint(_cpu_state(model.predictor.state_dict())))
    _setup(config)
    frozen = variant == 'jepa_frozen'
    jepa_weight = config.jepa_weight_during_finetune if variant == 'jepa_finetune' else 0.
    modules = [model.head] if frozen else [model.encoder, model.predictor, model.head]
    parameters = [p for module in modules for p in module.parameters()]
    if frozen:
        for module in (model.encoder, model.predictor):
            for parameter in module.parameters():
                parameter.requires_grad_(False)
    optimizer = torch.optim.AdamW(parameters, lr=config.lr, weight_decay=config.weight_decay)
    rng = np.random.default_rng([config.seed, 1])
    context = training.spec.context_steps
    history, steps, best_loss, best_epoch, best_state, stale = [], 0, float('inf'), None, None, 0
    for epoch in range(1, config.finetune_epochs + 1):
        start_time = time.perf_counter()
        model.train()
        if frozen:
            model.encoder.eval()
            model.predictor.eval()
        loss_sum, count = 0., 0
        order = rng.permutation(len(windows))
        for start in range(0, len(order), config.batch_size):
            features, mask, targets, target_mask = (torch.from_numpy(x) for x in
                                                    windows.take(order[start:start + config.batch_size]))
            optimizer.zero_grad(set_to_none=True)
            quantiles = model.forecast(features[:, :context], mask[:, :context])
            loss = pinball_loss(quantiles, targets, target_mask, config.quantiles)
            total_loss = loss
            if jepa_weight > 0:
                latent, _ = model.jepa_loss(features, mask)
                total_loss = loss + jepa_weight * latent
            _check_step(total_loss, parameters, config, optimizer)
            if jepa_weight > 0:
                model.update_target(config.ema_end)
            steps += 1
            loss_sum += float(loss.detach()) * len(features)
            count += len(features)
        validation_loss = _validation_pinball(model, val_batch, config)
        entry = dict(phase='finetune', epoch=epoch, train_pinball=loss_sum / count,
                     validation_pinball=validation_loss, steps=steps,
                     wall_seconds=time.perf_counter() - start_time)
        entry.update(_monitor(model, windows, config, with_target=variant != 'supervised'))
        history.append(entry)
        if validation_loss < best_loss:
            best_loss, best_epoch, best_state, stale = validation_loss, epoch, _cpu_state(model.state_dict()), 0
        else:
            stale += 1
            if stale >= config.patience:
                break
    model.load_state_dict(best_state, strict=True)
    _finite_state(model.state_dict())
    for parameter in list(model.encoder.parameters()) + list(model.predictor.parameters()):
        parameter.requires_grad_(True)
    record = dict(model_id=MODEL_IDS[variant], model_kind=MODEL_KIND, variant=variant,
        scientific_status='EXPERIMENTAL_UNVALIDATED', config=config.as_dict(), seed=config.seed,
        spec_fingerprint=training.spec.fingerprint, normalization_fingerprint=normalization.fingerprint,
        training_fingerprint=training.fingerprint,
        training_dataset_fingerprint=training.context.dataset_fingerprint,
        validation_origin_count=len(validation.context.origin_ids),
        train_windows=dict(eligible=len(all_windows), used=len(windows), stride=1,
                           policy='complete_consecutive_raw_training_rows',
                           subsample='evenly_spaced_chronological' if len(windows) < len(all_windows) else 'none'),
        parameters=_parameter_counts(model), effective_jepa_weight=jepa_weight,
        pretrain_history=pre_history, finetune_history=history, finetune_steps=steps,
        pre_finetune_weights=pretrained,
        selection=dict(partition='validation', metric='mean_pinball_normalized', epoch=best_epoch,
                       loss=best_loss, tie_policy='earliest_epoch', patience=config.patience),
        torch_version=str(torch.__version__), torch_threads=config.threads,
        wall_seconds=time.perf_counter() - began)
    canonical_json(record)
    return TrainedJepa(model, normalization, config, variant, record)


# -------------------------------------------------------------------- inference

class TrainedJepa:
    """Selected model plus train-fitted normalization; context-only prediction."""

    def __init__(self, model, normalization, config, variant, record):
        if variant not in VARIANTS:
            raise ValueError('Unknown JEPA variant')
        self._model = model.to('cpu').eval()
        self.normalization = normalization
        self.config = config
        self.variant = variant
        self._record = deepcopy(record)

    @property
    def model_id(self):
        return MODEL_IDS[self.variant]

    @property
    def record(self):
        return deepcopy(self._record)

    @property
    def parameter_count(self):
        return _parameter_counts(self._model)['trainable_total']

    def predict_normalized(self, features, feature_mask):
        """Normalized quantiles [B,H,K,Q] from normalized context tensors only."""
        torch = _torch()
        self._model.eval()
        with torch.inference_mode():
            return self._model.forecast(features, feature_mask)

    def predict(self, context, future_grid):
        torch = _torch()
        context, future_grid = _context_grid(context, future_grid)
        spec = context.spec
        if spec.fingerprint != self.normalization.spec.fingerprint:
            raise ValueError('Prediction spec identity differs from the trained normalization/spec identity')
        shape = (spec.horizon_steps, len(spec.target_names), len(self.config.quantiles))
        output = []
        self._model.eval()
        with torch.inference_mode():
            for start in range(0, len(context.origin_ids), self.config.batch_size):
                stop = min(start + self.config.batch_size, len(context.origin_ids))
                values = self.normalization.normalize(context.values[start:stop], context.mask[start:stop], 'feature')
                features = torch.tensor(values, dtype=torch.float32)
                mask = torch.tensor(context.mask[start:stop].copy(), dtype=torch.bool)
                if not bool(torch.isfinite(features).all()):
                    raise ValueError('Nonfinite prediction tensor')
                predicted = self._model.forecast(features, mask)
                if tuple(predicted.shape) != (stop - start,) + shape or not bool(torch.isfinite(predicted).all()):
                    raise ValueError('Nonfinite or malformed model output')
                output.append(predicted.cpu().numpy().astype(float))
        normalized = np.concatenate(output) if output else np.empty((0,) + shape)
        # inverse_targets expects channels last: [N,H,Q,K] -> native -> [N,H,K,Q].
        native = self.normalization.inverse_targets(normalized.transpose(0, 1, 3, 2)).transpose(0, 1, 3, 2)
        if not np.isfinite(native).all() or (np.diff(native, axis=-1) < 0).any():
            raise ValueError('Nonfinite or crossing native quantiles')
        median = self.config.quantiles.index(.5)
        return ForecastPrediction(native[..., median], future_grid, self.model_id,
                                  quantile_levels=self.config.quantiles, quantiles=native,
                                  point_interpretation='inverse_transformed_point' if spec.transform == 'log10' else 'native_point')

    def save(self, path):
        torch = _torch()
        path = Path(path)
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
        state = _cpu_state(self._model.state_dict())
        payload = dict(schema_version=SCHEMA_VERSION, model_kind=MODEL_KIND, variant=self.variant,
                       model_id=self.model_id, config_json=canonical_json(self.config.as_dict()),
                       normalization_json=canonical_json(self.normalization.as_dict()),
                       record_json=canonical_json(self._record), model_state=state,
                       weights_fingerprint=_weights_fingerprint(state), torch_version=str(torch.__version__))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            torch.save(payload, stream)

    @classmethod
    def load(cls, path):
        import json
        torch = _torch()
        try:
            payload = torch.load(Path(path), map_location='cpu', weights_only=True)
        except Exception as error:
            raise ValueError('Checkpoint could not be loaded with safe weights-only deserialization') from error
        required = {'schema_version', 'model_kind', 'variant', 'model_id', 'config_json', 'normalization_json',
                    'record_json', 'model_state', 'weights_fingerprint', 'torch_version'}
        if not isinstance(payload, dict) or set(payload) != required:
            raise ValueError('Malformed JEPA checkpoint payload')
        if (payload['schema_version'] != SCHEMA_VERSION or payload['model_kind'] != MODEL_KIND
                or payload['variant'] not in VARIANTS or payload['model_id'] != MODEL_IDS[payload['variant']]):
            raise ValueError('Unsupported JEPA checkpoint version/kind/variant')
        config = JepaConfig(**json.loads(payload['config_json']))
        normalization = Normalization.from_dict(json.loads(payload['normalization_json']))
        record = json.loads(payload['record_json'])
        if (record.get('config') != config.as_dict() or record.get('variant') != payload['variant']
                or record.get('normalization_fingerprint') != normalization.fingerprint
                or record.get('spec_fingerprint') != normalization.spec.fingerprint):
            raise ValueError('JEPA checkpoint internal identity differs')
        state = payload['model_state']
        if _weights_fingerprint(state) != payload['weights_fingerprint']:
            raise ValueError('JEPA checkpoint weight identity differs')
        model = build_jepa_model(normalization.spec, config)
        try:
            model.load_state_dict(state, strict=True)
        except (RuntimeError, KeyError) as error:
            raise ValueError('Incompatible JEPA checkpoint state') from error
        return cls(model, normalization, config, payload['variant'], record)


load_jepa = TrainedJepa.load
