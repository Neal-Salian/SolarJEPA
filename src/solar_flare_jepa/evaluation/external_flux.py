"""External-only flux scoring using unchanged P1 contracts, without fitting.

P1 evaluate_trajectory deliberately binds its TrainingSlice to the evaluation
source. This adapter omits train-scaled MASE instead of impersonating that source
or manufacturing an external training slice. Nonfinite/partial forecasts fail;
only observation quality masks define scored support.
"""
import numpy as np

from ..forecasting.contracts import (ForecastTargets, fingerprint_payload, logical_array,
                                     validate_alignment)
from .trajectory import _forecast_snapshot, prediction_snapshot


def _cell(value, count, reason=None):
    if value is not None and not np.isfinite(value):
        raise ValueError('Nonfinite evaluation result')
    return dict(value=None if value is None else float(value), count=int(count), reason=reason)


def _losses(signed, mask, reference):
    count = int(mask.sum())
    if not count:
        empty = _cell(None, 0, 'empty_mask')
        return {name: dict(empty) for name in ('mae','rmse','persistence_mae_skill','persistence_mse_skill')}
    mae = float(np.abs(signed[mask]).mean())
    mse = float(np.square(signed[mask]).mean())
    if mse == 0 and np.any(signed[mask] != 0):
        raise ValueError('Nonzero squared reduction underflow; evaluation failed')
    result = dict(mae=_cell(mae, count), rmse=_cell(np.sqrt(mse), count))
    for name, loss, reduction in (('mae', mae, np.abs), ('mse', mse, np.square)):
        ref_loss = None if reference is None else float(reduction(reference[mask]).mean())
        if name == 'mse' and ref_loss == 0 and np.any(reference[mask] != 0):
            raise ValueError('Nonzero reference squared reduction underflow; evaluation failed')
        reason = ('persistence_not_supplied' if ref_loss is None else
                  'zero_persistence_loss' if ref_loss == 0 else None)
        result[f'persistence_{name}_skill'] = _cell(
            None if reason else 1-loss/ref_loss, count, reason)
    return result


def evaluate_external_flux(targets, prediction, persistence=None):
    """MAE/RMSE, per-channel/lead skill, coverage and paired origin losses.

    All cells are equally weighted; RMSE is sqrt(mean squared error), never
    mean lead RMSE. Both model and reference must predict the full fixed grid.
    The caller supplies independently generated persistence on that same grid;
    this function neither trains nor executes any forecasting model.
    """
    if not isinstance(targets, ForecastTargets):
        raise ValueError('Expected ForecastTargets')
    targets = _forecast_snapshot(targets, ForecastTargets)
    prediction = prediction_snapshot(prediction)
    persistence = None if persistence is None else prediction_snapshot(persistence)
    validate_alignment(targets.grid, prediction.grid)
    if persistence is not None:
        validate_alignment(targets.grid, persistence.grid)
    mask = targets.mask
    observed = np.where(mask, targets.values, 0.)
    grid = targets.grid
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        try:
            signed = np.where(mask, prediction.values-observed, 0.)
            reference = None if persistence is None else np.where(mask, persistence.values-observed, 0.)
            by_target = {}
            by_lead = {}
            for k, name in enumerate(grid.spec.target_names):
                by_target[name] = _losses(signed[:,:,k], mask[:,:,k], None if reference is None else reference[:,:,k])
                by_lead[name] = [dict(lead_step=h+1, lead_end_seconds=(h+1)*grid.spec.cadence_seconds,
                    **_losses(signed[:,h,k], mask[:,h,k], None if reference is None else reference[:,h,k]))
                    for h in range(grid.spec.horizon_steps)]
            if len(set(grid.spec.target_units)) == 1:
                aggregate = _losses(signed, mask, reference)
            else:
                aggregate = {name:_cell(None, int(mask.sum()), 'incompatible_target_units')
                             for name in ('mae','rmse','persistence_mae_skill','persistence_mse_skill')}
            absolute, squared = np.abs(signed), np.square(signed)
            if ((absolute > 0) & (squared == 0) & mask).any():
                raise ValueError('Nonzero squared loss underflow; evaluation failed')
            ref_absolute = None if reference is None else np.abs(reference)
            ref_squared = None if reference is None else np.square(reference)
            if reference is not None and ((ref_absolute > 0) & (ref_squared == 0) & mask).any():
                raise ValueError('Nonzero reference squared loss underflow; evaluation failed')
        except FloatingPointError as exc:
            raise ValueError('Nonfinite evaluation loss; model evaluation failed') from exc
    def selected(values, m):
        return np.where(m, values, None).tolist()
    per_origin = [dict(origin_id=origin, issue_time_ns=int(grid.issue_times_ns[i]),
        valid_mask=mask[i].tolist(), absolute_error=selected(absolute[i],mask[i]),
        squared_error=selected(squared[i],mask[i]),
        persistence_absolute_error=None if reference is None else selected(ref_absolute[i],mask[i]),
        persistence_squared_error=None if reference is None else selected(ref_squared[i],mask[i]))
        for i,origin in enumerate(grid.origin_ids)]
    identity = fingerprint_payload(dict(adapter='external_flux_v1',
        dataset_fingerprint=grid.dataset_fingerprint, spec=grid.spec.as_dict(),
        origin_ids=grid.origin_ids, issue_times_ns=logical_array(grid.issue_times_ns),
        starts_ns=logical_array(grid.starts_ns), ends_ns=logical_array(grid.ends_ns),
        targets=logical_array(targets.values), mask=logical_array(mask),
        prediction=logical_array(prediction.values), model_id=prediction.model_id,
        point_interpretation=prediction.point_interpretation,
        persistence=None if persistence is None else dict(model_id=persistence.model_id,
            values=logical_array(persistence.values), point_interpretation=persistence.point_interpretation)))
    return dict(schema_version=1, adapter='external_flux_v1', space='native', fit_performed=False,
        model_id=prediction.model_id, dataset_fingerprint=grid.dataset_fingerprint,
        spec_fingerprint=grid.spec.fingerprint, evaluation_input_fingerprint=identity,
        target_names=list(grid.spec.target_names), target_units=list(grid.spec.target_units),
        origin_ids=list(grid.origin_ids), by_target=by_target, by_target_lead=by_lead,
        aggregate=aggregate, per_origin=per_origin,
        coverage=dict(valid_count=int(mask.sum()), total_count=int(mask.size),
            prediction_count=int(prediction.values.size), scored_count=int(mask.sum()),
            fraction=float(mask.mean()) if mask.size else None,
            prediction_fraction=1. if mask.size else None),
        reduction=dict(mask='fixed observation mask; nonfinite/partial predictions fail',
            weighting='equal valid cells', rmse='sqrt(mean(squared_error))',
            persistence_mae_skill='1 - MAE_model / MAE_persistence on identical valid cells',
            persistence_mse_skill='1 - MSE_model / MSE_persistence on identical valid cells'),
        mase=dict(value=None, reason='not_defined_without_independently_bound_frozen_training_scales'))
