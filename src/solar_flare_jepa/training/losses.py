"""Versioned forecast losses and validation metrics for V2 training (optional Torch).

Both versions score quantiles predicted in train-standardized transformed space.

* ``normalized_pinball_v1`` is the unchanged V1 objective: mean pinball over all
  valid standardized cells and levels (``training.jepa.pinball_loss``). With
  complete support it weights channel k by 1 implicitly in standardized units,
  i.e. by ``1 / target_scale[k]`` in dex.
* ``dex_pinball_equal_channel_v2`` multiplies each channel's mean standardized
  pinball by its train-fitted target standard deviation, then averages channels.
  Pinball is positively homogeneous, so ``scale * rho(e) = rho(scale * e)`` and
  for log10 specs this is mean pinball in dex with equal channel weight. Cells are
  averaged within a channel before channels are averaged; with complete support
  this equals the cell-weighted dex pinball of ``evaluation.probabilistic``.

Neither version is a scientific decision: which one trains or selects a V2 model
is a protocol choice recorded by the caller.
"""
import math

import numpy as np

from .core import _torch

LOSS_VERSIONS = ('normalized_pinball_v1', 'dex_pinball_equal_channel_v2')


def check_loss_version(version):
    if version not in LOSS_VERSIONS:
        raise ValueError(f'Unknown forecast loss version {version!r}; expected one of {LOSS_VERSIONS}')
    return version


def channel_weights(version, target_scale):
    """Per-channel multipliers applied to mean standardized pinball."""
    check_loss_version(version)
    scales = tuple(target_scale) if isinstance(target_scale, (list, tuple)) else ()
    if (not scales or any(type(x) not in (int, float) for x in scales)
            or not all(math.isfinite(x) and x > 0 for x in scales)):
        raise ValueError('Target scales must be a nonempty sequence of finite positive numbers')
    return (1.,) * len(scales) if version == 'normalized_pinball_v1' else tuple(float(x) for x in scales)


def check_levels(levels):
    """Quantile levels must be a nonempty, strictly increasing sequence inside (0, 1)."""
    values = tuple(levels) if isinstance(levels, (list, tuple)) else ()
    if (not values or any(type(x) not in (int, float) for x in values)
            or not all(math.isfinite(x) and 0 < x < 1 for x in values)
            or any(b <= a for a, b in zip(values, values[1:]))):
        raise ValueError('Quantile levels must be a nonempty strictly increasing sequence inside (0, 1)')
    return tuple(float(x) for x in values)


def _checked(quantiles, targets, mask, levels, scales):
    torch = _torch()
    check_levels(levels)
    if (quantiles.shape[:-1] != targets.shape or mask.shape != targets.shape or mask.dtype != torch.bool
            or quantiles.shape[-1] != len(levels) or targets.ndim != 3 or targets.shape[-1] != len(scales)):
        raise ValueError('Loss quantile/target/mask/channel shape differs')
    if not bool(mask.any()):
        raise ValueError('No valid supervision cells in batch')


def _cell_pinball(quantiles, targets, levels):
    torch = _torch()
    tau = torch.as_tensor(levels, dtype=quantiles.dtype, device=quantiles.device)
    error = targets.unsqueeze(-1) - quantiles
    return torch.maximum(tau * error, (tau - 1.) * error)


def forecast_loss(version, quantiles, targets, mask, levels, target_scale):
    """Scalar training loss of ``version`` for [B,H,K,Q] quantiles and [B,H,K] targets."""
    torch = _torch()
    weights = channel_weights(version, target_scale)
    _checked(quantiles, targets, mask, levels, weights)
    if version == 'normalized_pinball_v1':
        from .jepa import pinball_loss
        return pinball_loss(quantiles, targets, mask, levels)
    pinball = _cell_pinball(quantiles, targets, levels)
    terms = []
    for k, weight in enumerate(weights):
        selected = pinball[..., k, :][mask[..., k]]
        if not selected.numel():
            raise ValueError('Equal-channel loss requires valid support in every channel')
        terms.append(weight * selected.mean())
    value = torch.stack(terms).mean()
    if not bool(torch.isfinite(value)):
        raise ValueError('Nonfinite pinball loss')
    return value


class MetricAccumulator:
    """Exact full-partition metric from batches: float64 per-channel sums/counts."""

    def __init__(self, version, levels, target_scale):
        self.version = check_loss_version(version)
        self.levels = check_levels(levels)
        self.weights = channel_weights(version, target_scale)
        self.sums = np.zeros(len(self.weights))
        self.counts = np.zeros(len(self.weights), dtype=np.int64)

    def add(self, quantiles, targets, mask):
        torch = _torch()
        _checked(quantiles, targets, mask, self.levels, self.weights)
        pinball = _cell_pinball(quantiles.double(), targets.double(), self.levels)
        for k in range(len(self.weights)):
            selected = pinball[..., k, :][mask[..., k]]
            if not bool(torch.isfinite(selected).all()):
                raise ValueError('Nonfinite pinball metric')
            self.sums[k] += float(selected.sum())
            self.counts[k] += int(selected.numel())

    def value(self):
        if not self.counts.sum() or (self.version != 'normalized_pinball_v1' and (self.counts == 0).any()):
            raise ValueError('Metric has no valid support for a required channel')
        if self.version == 'normalized_pinball_v1':
            return float(self.sums.sum() / self.counts.sum())
        return float(np.mean(np.asarray(self.weights) * self.sums / self.counts))
