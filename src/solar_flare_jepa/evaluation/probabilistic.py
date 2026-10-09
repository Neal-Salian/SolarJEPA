"""Log-space point/quantile scores and paired block-bootstrap comparisons.

GOES flux spans orders of magnitude, so native W/m2 losses are dominated by a
few flare peaks. These scores use y = log10(F / reference) ("dex") on exactly
the supplied valid target cells. Five quantiles do not define a full predictive
distribution: mean pinball is reported as a quantile score, not as exact CRPS.
Interval coverage is pointwise per target cell, not trajectory coverage.
"""
import numpy as np

from solar_flare_jepa.forecasting.contracts import ForecastPrediction, ForecastTargets, validate_alignment


def _log(values, reference):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.log10(np.asarray(values, float) / np.asarray(reference, float))


def _interval(levels, low, high):
    levels = list(levels)
    if low in levels and high in levels:
        return levels.index(low), levels.index(high)
    return None


def _masked_mean(values, mask, axis=None):
    count = mask.sum(axis=axis)
    total = np.where(mask, values, 0.).sum(axis=axis)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(count > 0, total / np.maximum(count, 1), np.nan)


def log_scores(targets, prediction, spec):
    """Return aggregate, per-lead and per-origin log-space scores.

    Per-origin values average that origin's valid cells and support paired,
    origin-aligned comparisons; origins are overlapping-context samples.
    """
    if not isinstance(targets, ForecastTargets) or not isinstance(prediction, ForecastPrediction):
        raise TypeError('Expected ForecastTargets and ForecastPrediction')
    validate_alignment(targets.grid, prediction.grid)
    reference = np.asarray(spec.target_reference, float)
    mask = np.asarray(targets.mask, bool)
    observed = np.where(mask, _log(np.where(mask, targets.values, 1.), reference), 0.)
    point = _log(prediction.values, reference)
    if not np.isfinite(point[mask]).all():
        raise ValueError('Nonpositive or nonfinite point forecast on a scored cell')
    error = np.where(mask, point - observed, 0.)
    result = dict(space='log10(F / reference)', unit='dex', scored_cells=int(mask.sum()),
                  origins=len(targets.grid.origin_ids),
                  log_mae=float(_masked_mean(np.abs(error), mask)),
                  log_rmse=float(np.sqrt(_masked_mean(error**2, mask))),
                  bias=float(_masked_mean(error, mask)),
                  by_target={name: dict(log_mae=float(_masked_mean(np.abs(error[..., k]), mask[..., k])))
                             for k, name in enumerate(spec.target_names)},
                  by_lead=dict(log_mae=_masked_mean(np.abs(error), mask, axis=(0, 2)).tolist()))
    per_origin = dict(log_mae=_masked_mean(np.abs(error), mask, axis=(1, 2)))
    if prediction.quantiles is not None:
        levels = np.asarray(prediction.quantile_levels, float)
        quantiles = _log(prediction.quantiles, reference[None, None, :, None])
        if not np.isfinite(quantiles[mask]).all():
            raise ValueError('Nonpositive or nonfinite quantile forecast on a scored cell')
        residual = observed[..., None] - quantiles
        pinball = np.maximum(levels * residual, (levels - 1) * residual)
        cell_pinball = np.where(mask, pinball.mean(axis=-1), 0.)
        result.update(mean_pinball=float(_masked_mean(cell_pinball, mask)),
                      pinball_by_level={str(q): float(_masked_mean(pinball[..., i], mask))
                                        for i, q in enumerate(levels)})
        result['by_lead']['mean_pinball'] = _masked_mean(cell_pinball, mask, axis=(0, 2)).tolist()
        per_origin['mean_pinball'] = _masked_mean(cell_pinball, mask, axis=(1, 2))
        for label, (low, high) in dict(central_50=(0.25, 0.75), central_90=(0.05, 0.95)).items():
            pair = _interval(levels, low, high)
            if pair is None:
                continue
            lo, hi = quantiles[..., pair[0]], quantiles[..., pair[1]]
            inside = (observed >= lo) & (observed <= hi)
            result[f'coverage_{label}'] = float(_masked_mean(inside.astype(float), mask))
            result[f'width_{label}'] = float(_masked_mean(hi - lo, mask))
            result['by_lead'][f'coverage_{label}'] = _masked_mean(inside.astype(float), mask, axis=(0, 2)).tolist()
    result['per_origin'] = {key: value.tolist() for key, value in per_origin.items()}
    return result


def block_bootstrap(loss_a, loss_b, blocks, *, replicates=2000, seed=0):
    """Paired difference mean(loss_a - loss_b) with a block-resampled 95% CI.

    `blocks` assigns each origin to a contiguous block (e.g. UTC day); whole
    blocks are resampled with replacement so within-block dependence among
    overlapping origins is retained. Negative differences favour model A.
    """
    a, b, blocks = (np.asarray(x) for x in (loss_a, loss_b, blocks))
    valid = np.isfinite(a) & np.isfinite(b)
    a, b, blocks = a[valid], b[valid], blocks[valid]
    labels = np.unique(blocks)
    if len(labels) < 2:
        raise ValueError('Block bootstrap requires at least two blocks')
    sums = np.array([(a[blocks == g] - b[blocks == g]).sum() for g in labels])
    counts = np.array([(blocks == g).sum() for g in labels])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(labels), size=(replicates, len(labels)))
    stats = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    low, high = np.percentile(stats, [2.5, 97.5])
    return dict(mean_difference=float((a - b).mean()), ci95=[float(low), float(high)],
                prob_a_better=float((stats < 0).mean()), blocks=int(len(labels)),
                origins=int(valid.sum()), replicates=replicates, seed=seed)
