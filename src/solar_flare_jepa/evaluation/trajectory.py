"""Native-unit trajectory scoring on the common target mask.

Fitted transforms are model metadata: the contracts carry native targets and
native or inverse-transformed points. This evaluator does not reinterpret
those points as physical conditional means or fabricate quantile forecasts.
"""
import numpy as np

from ..forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid, TrainingSlice,
    _canonical_fields, fingerprint_payload, logical_array, validate_alignment,
)


def _grid_snapshot(grid):
    if not isinstance(grid, FutureGrid):
        raise ValueError('Evaluation requires an explicit future grid')
    declarations = _canonical_fields(grid, FutureGrid)
    if not isinstance(declarations['spec'], ForecastSpec):
        raise ValueError('Evaluation requires an explicit forecast spec')
    declarations['spec'] = ForecastSpec(**_canonical_fields(declarations['spec'], ForecastSpec))
    return FutureGrid(**declarations)


def _forecast_snapshot(value, contract):
    declarations = _canonical_fields(value, contract)
    declarations['grid'] = _grid_snapshot(declarations['grid'])
    return contract(**declarations)


def _prediction_content(prediction):
    if prediction is None:
        return None
    return dict(model_id=prediction.model_id, point_interpretation=prediction.point_interpretation,
                values=logical_array(prediction.values), quantile_levels=prediction.quantile_levels,
                quantiles=None if prediction.quantiles is None else logical_array(prediction.quantiles))


def _cell(value, count, reason=None):
    if value is not None and not np.isfinite(value):
        raise ValueError('Nonfinite evaluation result')
    return {'value': None if value is None else float(value),
            'reason': reason, 'count': int(count)}


def _weights(value, size, name):
    if value is None:
        return np.ones(size, dtype=float)
    raw = np.asarray(value)
    if raw.dtype.kind not in 'fiu' or raw.shape != (size,):
        raise ValueError(f'{name} weights must be a numeric vector of length {size}')
    weights = raw.astype(float)
    if (not np.isfinite(weights).all() or (weights < 0).any()
            or not np.isfinite(weights.sum()) or weights.sum() <= 0):
        raise ValueError(f'{name} weights must be finite, nonnegative, with positive sum')
    return weights


def _mean(values, mask, weights):
    selected = mask & (weights > 0)
    count = int(selected.sum())
    if not count:
        return _cell(None, 0, 'empty_mask')
    w = weights[selected]
    return _cell(np.dot(values[selected], w / w.sum()), count)


def _pearson(observed, predicted, mask):
    count = int(mask.sum())
    if not count:
        return _cell(None, 0, 'empty_mask')
    if count < 2:
        return _cell(None, count, 'insufficient_pairs')
    x, y = observed[mask], predicted[mask]
    # Normalize before centering to avoid overflow in diagnostic sums of squares.
    sx, sy = float(np.max(np.abs(x))), float(np.max(np.abs(y)))
    if sx == 0 or sy == 0:
        return _cell(None, count, 'constant_input')
    x, y = x/sx, y/sy
    x, y = x-x.mean(), y-y.mean()
    nx, ny = np.linalg.norm(x), np.linalg.norm(y)
    if nx == 0 or ny == 0:
        return _cell(None, count, 'constant_input')
    return _cell(np.clip(np.dot(x/nx, y/ny), -1., 1.), count)


def _skill(loss, reference):
    if loss['value'] is None:
        return _cell(None, loss['count'], loss['reason'])
    if reference is None:
        return _cell(None, loss['count'], 'persistence_not_supplied')
    if reference['value'] == 0:
        return _cell(None, loss['count'], 'zero_persistence_loss')
    return _cell(1-loss['value']/reference['value'], loss['count'])


def _training_scales(training):
    raw, valid = training.raw_targets, training.raw_target_mask
    adjacent = np.array([int(a) == int(b) for a,b in
                         zip(training.raw_starts_ns[1:], training.raw_ends_ns[:-1])], bool)
    scales = []
    for k in range(raw.shape[1]):
        pairs = adjacent & valid[:-1,k] & valid[1:,k]
        count = int(pairs.sum())
        if not count:
            scales.append(_cell(None, 0, 'insufficient_adjacent_training_pairs'))
            continue
        differences = np.abs(raw[1:,k][pairs]-raw[:-1,k][pairs])
        scale = float(np.mean(differences))
        scales.append(_cell(scale, count, 'zero_training_scale' if scale == 0 else None))
    return scales


def _metrics(observed, predicted, signed, mask, weights, scale,
             reference_signed=None, quantile_loss=None):
    mae = _mean(np.abs(signed), mask, weights)
    mse = _mean(signed**2, mask, weights)
    rmse = _cell(None if mse['value'] is None else np.sqrt(mse['value']),
                 mse['count'], mse['reason'])
    if mae['value'] is None:
        mase = _cell(None, mae['count'], mae['reason'])
    elif scale['reason'] is not None:
        mase = _cell(None, mae['count'], scale['reason'])
    else:
        mase = _cell(mae['value']/scale['value'], mae['count'])
    ref_mae = ref_mse = None
    if reference_signed is not None:
        ref_mae = _mean(np.abs(reference_signed),mask,weights)
        ref_mse = _mean(reference_signed**2,mask,weights)
    return dict(mae=mae,rmse=rmse,mase=mase,pearson=_pearson(observed,predicted,mask),
                persistence_mae_skill=_skill(mae,ref_mae),
                persistence_mse_skill=_skill(mse,ref_mse),
                pinball=None if quantile_loss is None else
                [_mean(quantile_loss[...,q],mask,weights)
                 for q in range(quantile_loss.shape[-1])])


def _masked_list(values, mask):
    return np.where(mask,values,None).tolist()


def evaluate_trajectory(targets, prediction, training, persistence=None,
                        lead_weights=None, target_weights=None):
    """Evaluate aligned native predictions; return finite JSON-compatible content.

    Lead scores use every valid origin equally. Per-target and across-target
    loss reductions pool cells with lead and (where relevant) target weights,
    renormalized over valid positive-weight cells. RMSE takes the square root
    after pooling squared errors. Pearson is an unweighted diagnostic on the
    same target mask, even when a lead has zero aggregate weight.

    Across-target raw loss is undefined for differing declared units. MASE and
    persistence-relative skill are returned per target rather than combined
    across different training scales or reference losses. Overlapping origins
    are retained as supplied; no independence or uncertainty claim is made.
    """
    if not isinstance(targets,ForecastTargets) or not isinstance(prediction,ForecastPrediction):
        raise TypeError('Expected ForecastTargets and ForecastPrediction')
    if not isinstance(training,TrainingSlice):
        raise TypeError('Expected TrainingSlice')
    if persistence is not None and not isinstance(persistence,ForecastPrediction):
        raise TypeError('Expected ForecastPrediction persistence')
    # Constructor history is not a trust boundary: copies, pickle and subclasses
    # may contain different buffers or declarations. These exact-base snapshots
    # are the only objects used for alignment, metrics, coverage and identities.
    targets = _forecast_snapshot(targets, ForecastTargets)
    prediction = _forecast_snapshot(prediction, ForecastPrediction)
    training = TrainingSlice(**_canonical_fields(training, TrainingSlice))
    persistence = None if persistence is None else _forecast_snapshot(persistence, ForecastPrediction)
    validate_alignment(targets.grid,prediction.grid)
    if (training.spec.fingerprint != targets.grid.spec.fingerprint
            or training.context.dataset_fingerprint != targets.grid.dataset_fingerprint):
        raise ValueError('Training data do not align in dataset/spec/target identity')
    if persistence is not None:
        validate_alignment(targets.grid,persistence.grid)
    for pred in (prediction,persistence):
        if pred is not None and (not np.isfinite(pred.values).all()
                                 or (pred.quantiles is not None and not np.isfinite(pred.quantiles).all())):
            raise ValueError('Nonfinite prediction is a model failure, not an exclusion')
    n,h,k = targets.values.shape
    lead = _weights(lead_weights,h,'lead')
    target = _weights(target_weights,k,'target')
    training_identity = training.fingerprint
    grid = targets.grid
    evaluation_identity = fingerprint_payload(dict(
        schema_version=1, dataset=grid.dataset_fingerprint, spec=grid.spec.as_dict(),
        origin_ids=grid.origin_ids, issue_times_ns=logical_array(grid.issue_times_ns),
        starts_ns=logical_array(grid.starts_ns), ends_ns=logical_array(grid.ends_ns),
        targets=logical_array(targets.values), target_mask=logical_array(targets.mask),
        prediction=_prediction_content(prediction), persistence=_prediction_content(persistence),
        training=training_identity, lead_weights=lead.tolist(), target_weights=target.tolist()))
    # Normalize axes separately before multiplication to avoid weight overflow.
    pooled_weights = np.broadcast_to((lead/lead.sum())[None,:,None]
                                    * (target/target.sum())[None,None,:], (n,h,k))
    mask = targets.mask
    observed = np.where(mask,targets.values,0.)
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            signed = np.where(mask,prediction.values-observed,0.)
            reference = None if persistence is None else np.where(mask,persistence.values-observed,0.)
            pinball = None
            if prediction.quantiles is not None:
                residual = observed[...,None]-prediction.quantiles
                q = np.asarray(prediction.quantile_levels)
                pinball = np.maximum(q*residual,(q-1)*residual)
                pinball = np.where(mask[...,None],pinball,0.)
            scales = _training_scales(training)
            by_target,by_lead = {},{}
            names = targets.grid.spec.target_names
            for t,name in enumerate(names):
                by_target[name] = _metrics(observed[:,:,t],prediction.values[:,:,t],signed[:,:,t],
                    mask[:,:,t],np.broadcast_to((lead/lead.sum())[None],(n,h)),scales[t],
                    None if reference is None else reference[:,:,t],
                    None if pinball is None else pinball[:,:,t,:])
                by_lead[name] = [dict(lead_step=l+1,**_metrics(
                    observed[:,l,t],prediction.values[:,l,t],signed[:,l,t],mask[:,l,t],
                    np.ones(n),scales[t],None if reference is None else reference[:,l,t],
                    None if pinball is None else pinball[:,l,t,:])) for l in range(h)]
            same_units = len(set(targets.grid.spec.target_units)) == 1
            scored_count = int((mask & (pooled_weights > 0)).sum())
            if same_units:
                aggregate_mae = _mean(np.abs(signed),mask,pooled_weights)
                aggregate_mse = _mean(signed**2,mask,pooled_weights)
                aggregate_rmse = _cell(None if aggregate_mse['value'] is None else
                                      np.sqrt(aggregate_mse['value']),aggregate_mse['count'],aggregate_mse['reason'])
                aggregate_pinball = None if pinball is None else [
                    _mean(pinball[...,q],mask,pooled_weights) for q in range(pinball.shape[-1])]
            else:
                aggregate_mae = _cell(None,scored_count,'incompatible_target_units')
                aggregate_rmse = _cell(None,scored_count,'incompatible_target_units')
                aggregate_pinball = None if pinball is None else [
                    _cell(None,scored_count,'incompatible_target_units') for _ in prediction.quantile_levels]
            absolute,squared = np.abs(signed),signed**2
    except FloatingPointError as exc:
        raise ValueError('Nonfinite evaluation loss; evaluation failed') from exc
    per_origin = []
    for i,origin_id in enumerate(targets.grid.origin_ids):
        per_origin.append(dict(origin_id=origin_id,issue_time_ns=int(targets.grid.issue_times_ns[i]),
            valid_mask=mask[i].tolist(),signed_error=_masked_list(signed[i],mask[i]),
            absolute_error=_masked_list(absolute[i],mask[i]),
            squared_error=_masked_list(squared[i],mask[i]),
            persistence_absolute_error=None if reference is None else _masked_list(np.abs(reference[i]),mask[i]),
            persistence_squared_error=None if reference is None else _masked_list(reference[i]**2,mask[i]),
            pinball_loss=None if pinball is None else _masked_list(pinball[i],mask[i,...,None])))
    units = {name: dict(mae=unit,rmse=unit,pinball=unit,training_scale=unit,
                       signed_error=unit,absolute_error=unit,squared_error=f'({unit})^2',
                       mase='dimensionless',persistence_mae_skill='dimensionless',
                       persistence_mse_skill='dimensionless',pearson='dimensionless')
             for name,unit in zip(names,targets.grid.spec.target_units)}
    return dict(schema_version=1,space='native',model_id=prediction.model_id,
        point_interpretation=prediction.point_interpretation,model_transform=targets.grid.spec.transform,
        dataset_fingerprint=targets.grid.dataset_fingerprint,spec_fingerprint=targets.grid.spec.fingerprint,
        training_split_fingerprint=training.split_fingerprint,
        training_fingerprint=training_identity,evaluation_input_fingerprint=evaluation_identity,
        origin_ids=list(targets.grid.origin_ids),target_names=list(names),
        target_units=list(targets.grid.spec.target_units),units=units,
        quantile_levels=list(prediction.quantile_levels),
        weights=dict(lead=lead.tolist(),target=target.tolist()),
        reduction=dict(lead='equal_valid_origins',
            loss='sum(valid_cell_weight * loss) / sum(valid_cell_weight)',
            cell_weight='lead_weight * target_weight; target cancels within each target',
            rmse='sqrt(pooled_weighted_squared_error)',
            persistence_mae_skill='1 - pooled_model_mae / pooled_persistence_mae',
            persistence_mse_skill='1 - pooled_model_mse / pooled_persistence_mse',
            mase='pooled_mae / mean_absolute_adjacent_valid_unique_training_difference',
            pinball='max(q * (observed - quantile), (q - 1) * (observed - quantile)); separate q',
            pearson='unweighted_common_mask_diagnostic'),
        coverage=dict(valid_count=int(mask.sum()),total_count=int(mask.size),
                      scored_count=scored_count,fraction=float(mask.mean()) if mask.size else None,
                      valid_by_target_lead={name:mask[:,:,t].sum(axis=0).tolist() for t,name in enumerate(names)}),
        training_scales=dict(zip(names,scales)),by_target_lead=by_lead,by_target=by_target,
        aggregate=dict(unit=targets.grid.spec.target_units[0] if same_units else None,
                       mae=aggregate_mae,rmse=aggregate_rmse,pinball=aggregate_pinball),
        per_origin=per_origin)
