"""Strict marginal quantile diagnostics on canonical common target support.

Coverage is descriptive pointwise coverage, never trajectory coverage, event
probability or a formal test of calibration. Width and proper interval score
accompany coverage so wide intervals cannot appear good from coverage alone.
"""
import numpy as np

from ..forecasting.contracts import ForecastTargets, validate_alignment
from .trajectory import _forecast_snapshot, prediction_snapshot


def _mean(values, mask, axis=None):
    count = mask.sum(axis=axis)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        result = np.where(mask, values, 0.).sum(axis=axis) / np.maximum(count, 1)
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite diagnostic reduction')
    if np.ndim(result) == 0:
        return None if count == 0 else float(result)
    return np.where(count > 0, result, None).tolist()


def calibration_diagnostics(targets, prediction, *, space, intervals=None):
    """Reliability/pinball by lead/channel and symmetric central interval scores.

    ``space`` is explicitly ``native`` or dimensioned ``log10`` using the
    grid spec's target reference. ``intervals=None`` selects available 50%/90%
    central intervals only; explicitly requested unavailable quantiles fail.
    Invalid cells are inert and empty support is JSON null. No fitted transform
    or held-out calibration adjustment is performed.
    """
    if not isinstance(targets, ForecastTargets):
        raise ValueError('Expected ForecastTargets')
    targets = _forecast_snapshot(targets, ForecastTargets)
    prediction = prediction_snapshot(prediction)
    validate_alignment(targets.grid, prediction.grid)
    if space not in ('native', 'log10'):
        raise ValueError('Diagnostic space must be native or log10')
    if prediction.quantiles is None:
        raise ValueError('Quantile diagnostics require quantile predictions')
    levels = prediction.quantile_levels
    if intervals is None:
        intervals = [pair for pair in ((.05, .95), (.25, .75)) if all(q in levels for q in pair)]
    pairs = []
    for pair in intervals:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError('Each central interval requires two quantiles')
        low, high = pair
        if (type(low) not in (int, float) or type(high) not in (int, float)
                or not 0 < low < .5 < high < 1 or not np.isclose(low + high, 1., rtol=0, atol=1e-12)):
            raise ValueError('Central intervals require symmetric ordered quantiles')
        if low not in levels or high not in levels:
            raise ValueError('Requested interval quantile is unavailable')
        if (low, high) in pairs:
            raise ValueError('Duplicate central interval')
        pairs.append((low, high))
    mask = targets.mask
    observed = np.where(mask, targets.values, 1.)
    quantiles = np.where(mask[..., None], prediction.quantiles, 1.)
    if space == 'log10':
        if len(targets.grid.spec.target_reference) != len(targets.grid.spec.target_names):
            raise ValueError('Log diagnostics require explicit dimensioned target references')
        if ((observed[mask] <= 0).any() or (quantiles[mask] <= 0).any()
                or (prediction.values[mask] <= 0).any()):
            raise ValueError('Log diagnostics require positive scored observations and forecasts')
        reference = np.asarray(targets.grid.spec.target_reference)
        # Subtract logs to avoid overflow of F/reference for finite extremes.
        observed = np.log10(observed) - np.log10(reference)
        quantiles = np.log10(quantiles) - np.log10(reference)[None, None, :, None]
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            residual = observed[..., None] - quantiles
            q = np.asarray(levels)
            pinball = np.maximum(q * residual, (q - 1) * residual)
            reliability = (observed[..., None] <= quantiles).astype(float)
            cell_pinball = pinball.mean(axis=-1)
            result = dict(schema_version=1, space=space,
                          units=list(targets.grid.spec.target_units) if space == 'native'
                          else ['dex'] * len(targets.grid.spec.target_names),
                          target_names=list(targets.grid.spec.target_names),
                          quantile_levels=list(levels), counts=mask.sum(axis=0).tolist(),
                          quantile_reliability=_mean(reliability, np.broadcast_to(mask[..., None], pinball.shape), axis=0),
                          pinball_by_quantile=_mean(pinball, np.broadcast_to(mask[..., None], pinball.shape), axis=0),
                          mean_pinball=_mean(cell_pinball, mask, axis=0),
                          aggregate_mean_pinball=_mean(cell_pinball, mask), intervals=[])
            for low, high in pairs:
                lo, hi = quantiles[..., levels.index(low)], quantiles[..., levels.index(high)]
                alpha = 1 - (high - low)
                width = hi - lo
                score = width + (2 / alpha) * np.maximum(lo - observed, 0.) + (2 / alpha) * np.maximum(observed - hi, 0.)
                inside = ((observed >= lo) & (observed <= hi)).astype(float)
                result['intervals'].append(dict(low=low, high=high, nominal_coverage=high - low,
                    coverage=_mean(inside, mask, axis=0), width=_mean(width, mask, axis=0),
                    interval_score=_mean(score, mask, axis=0),
                    aggregate_coverage=_mean(inside, mask), aggregate_width=_mean(width, mask),
                    aggregate_interval_score=_mean(score, mask)))
    except FloatingPointError as error:
        raise ValueError('Nonfinite diagnostic arithmetic') from error
    return result
