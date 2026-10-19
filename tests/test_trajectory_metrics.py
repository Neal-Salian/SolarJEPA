"""Hand-derived evaluator checks; all observations here are synthetic."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
    TrainingSlice,
)

SECOND = 1_000_000_000


def evaluate(*args, **kwargs):
    from solar_flare_jepa.evaluation import evaluate_trajectory
    return evaluate_trajectory(*args, **kwargs)


def fixture(values=None, mask=None, predictions=None, raw=None, raw_mask=None,
            raw_starts=None, units=('unit',), **spec_changes):
    values = np.asarray(values if values is not None else [[[2.], [4.]], [[6.], [8.]]])
    n, h, k = values.shape
    names = tuple(f'x{i}' for i in range(k))
    spec = ForecastSpec(1, 1, h, names, names, units, units,
                        eligibility_policy='masked', **spec_changes)
    issues = np.arange(20, 20+n, dtype=np.int64) * SECOND
    starts = issues[:, None] + np.arange(h, dtype=np.int64)[None] * SECOND
    grid = FutureGrid(starts, starts+SECOND, issues,
                      tuple(f'o{i}' for i in range(n)), spec, 'synthetic-dataset')
    targets = ForecastTargets(values, np.ones_like(values, bool) if mask is None else mask, grid)
    predictions = np.asarray(predictions if predictions is not None
                             else [[[1.], [1.]], [[5.], [3.]]])
    prediction = ForecastPrediction(predictions, grid, 'toy')
    # MASE needs unique raw training pairs, not invented supervised observations.
    train_issues = np.empty(0, np.int64)
    context = ForecastContext(np.empty((0,1,k)), np.empty((0,1,k), bool),
                              np.empty((0,1), np.int64), np.empty((0,1), np.int64),
                              train_issues, (), spec, 'synthetic-dataset',
                              np.empty((0,1,k), np.int64))
    train_starts = train_issues[:,None]+np.arange(h,dtype=np.int64)[None]*SECOND
    train_grid = FutureGrid(train_starts, train_starts+SECOND, train_issues,
                            (), spec, 'synthetic-dataset')
    train_targets = ForecastTargets(np.empty((0,h,k)), np.empty((0,h,k), bool), train_grid)
    raw = np.asarray(raw if raw is not None else np.tile([[0.],[2.],[6.],[8.]], (1,k)))
    raw_starts = np.asarray(raw_starts if raw_starts is not None
                            else np.arange(len(raw))*SECOND, np.int64)
    training = TrainingSlice(context, train_targets, raw_starts, raw_starts+SECOND,
                             raw, np.ones_like(raw,bool), raw,
                             np.ones_like(raw,bool) if raw_mask is None else raw_mask,
                             0, max(int(raw_starts[-1]+SECOND), (h+1)*SECOND), 'split',
                             raw_availability_ns=np.broadcast_to(raw_starts[:,None]+SECOND, raw.shape))
    return targets, prediction, training


def value(cell):
    assert cell['reason'] is None
    return cell['value']


def test_hand_calculated_lead_pooled_errors_mase_skills_and_origin_losses():
    targets, prediction, training = fixture()
    persistence = ForecastPrediction(np.zeros((2,2,1)), targets.grid, 'persistence')
    result = evaluate(targets, prediction, training, persistence)
    lead = result['by_target_lead']['x0']
    assert value(lead[0]['mae']) == 1.
    assert value(lead[1]['mae']) == 4.
    assert value(lead[1]['rmse']) == pytest.approx(4.123105625617661)
    pooled = result['by_target']['x0']
    # Errors [-1,-3,-1,-5]: MAE=10/4, RMSE=sqrt(36/4), not mean lead RMSE.
    assert value(pooled['mae']) == 2.5
    assert value(pooled['rmse']) == 3.
    assert value(pooled['mase']) == .9375  # train differences 2,4,2 -> scale 8/3
    assert value(pooled['persistence_mae_skill']) == .5  # reference MAE=5
    assert value(pooled['persistence_mse_skill']) == .7  # reference MSE=30
    assert result['training_scales']['x0']['count'] == 3
    assert result['origin_ids'] == ['o0', 'o1']
    assert result['per_origin'][1]['signed_error'] == [[-1.], [-5.]]
    assert result['per_origin'][1]['squared_error'] == [[1.], [25.]]
    assert result['coverage']['valid_count'] == 4
    assert result['units']['x0']['rmse'] == 'unit'
    json.dumps(result, allow_nan=False)


def test_weighted_pool_accumulates_losses_before_square_root():
    result = evaluate(*fixture(), lead_weights=[1., 3.], target_weights=[2.])
    pooled = result['by_target']['x0']
    # Weighted squared loss=(1+27+1+75)/(1+3+1+3)=13.
    assert value(pooled['rmse']) == pytest.approx(3.605551275463989)
    assert value(pooled['mae']) == 3.25
    assert result['weights']['lead'] == [1., 3.]
    assert result['weights']['target'] == [2.]
    assert pooled['rmse']['count'] == 4


def test_common_mask_is_preserved_and_nonfinite_predictions_are_failures():
    mask = np.array([[[True],[False]], [[True],[True]]])
    targets, prediction, training = fixture(values=[[[2.],[np.nan]],[[6.],[8.]]], mask=mask)
    result = evaluate(targets, prediction, training)
    assert value(result['by_target']['x0']['mae']) == pytest.approx(7/3)
    assert result['by_target_lead']['x0'][1]['mae']['count'] == 1
    assert result['per_origin'][0]['signed_error'] == [[-1.], [None]]
    assert result['coverage']['valid_count'] == 3
    assert result['coverage']['total_count'] == 4
    with pytest.raises(ValueError, match='finite'):
        ForecastPrediction(np.array([[[np.nan],[1.]], [[5.],[3.]]]), targets.grid, 'failed')


def test_training_scale_uses_only_valid_adjacent_unique_observations_without_gaps():
    # Raw pairs remain exactly 0->2 and 100->104, independent of windows.
    args = fixture(raw=[[0.],[2.],[999.],[100.],[104.],[999.],[106.]],
                   raw_mask=np.array([[True],[True],[False],[True],[True],[False],[True]]),
                   raw_starts=np.array([0,1,2,4,5,6,7])*SECOND)
    result = evaluate(*args)
    # Only 0->2 and 100->104 count, not gap 2->100 or masked neighbors.
    assert value(result['training_scales']['x0']) == 3.
    assert result['training_scales']['x0']['count'] == 2
    assert value(result['by_target']['x0']['mase']) == pytest.approx(5/6)


@pytest.mark.parametrize('raw,raw_mask,reason', [
    ([[1.],[1.],[1.],[1.]], None, 'zero_training_scale'),
    ([[1.],[2.],[3.],[4.]], np.array([[True],[False],[True],[False]]),
     'insufficient_adjacent_training_pairs'),
])
def test_undefined_mase_has_reason_without_nonfinite_output(raw,raw_mask,reason):
    result = evaluate(*fixture(raw=raw, raw_mask=raw_mask))
    cell = result['by_target']['x0']['mase']
    assert cell['value'] is None
    assert cell['reason'] == reason
    assert cell['count'] == 4
    json.dumps(result, allow_nan=False)


def test_empty_mask_constant_and_single_pair_correlation_and_zero_reference_loss():
    targets, pred, train = fixture(mask=np.zeros((2,2,1),bool))
    empty = evaluate(targets,pred,train)['by_target']['x0']
    assert empty['rmse'] == {'value': None, 'reason': 'empty_mask', 'count': 0}
    targets,pred,train = fixture(predictions=np.ones((2,2,1)))
    result = evaluate(targets,pred,train,ForecastPrediction(targets.values,targets.grid,'perfect'))
    assert result['by_target']['x0']['pearson']['reason'] == 'constant_input'
    assert result['by_target']['x0']['persistence_mae_skill']['reason'] == 'zero_persistence_loss'
    assert result['by_target']['x0']['persistence_mse_skill']['value'] is None
    mask = np.array([[[True],[False]],[[False],[False]]])
    result = evaluate(*fixture(mask=mask))
    assert result['by_target']['x0']['pearson']['reason'] == 'insufficient_pairs'


def test_pearson_is_diagnostic_and_uses_matched_pairs():
    result = evaluate(*fixture(predictions=[[[4.],[8.]], [[12.],[16.]]]))
    assert value(result['by_target']['x0']['pearson']) == pytest.approx(1.)
    assert result['reduction']['pearson'] == 'unweighted_common_mask_diagnostic'


def test_nonconstant_tiny_values_are_not_misreported_as_constant_correlation():
    result=evaluate(*fixture(values=[[[1e-300],[2e-300]],[[3e-300],[4e-300]]],
                             predictions=[[[2e-300],[4e-300]],[[6e-300],[8e-300]]]))
    assert value(result['by_target']['x0']['pearson']) == pytest.approx(1.)


def test_quantile_pinball_uses_supplied_quantiles_and_records_per_origin_loss():
    targets,pred,train = fixture()
    q = np.concatenate((targets.values[...,None]-2,targets.values[...,None]+1),axis=-1)
    pred = replace(pred,quantile_levels=(.25,.75),quantiles=q)
    result = evaluate(targets,pred,train)
    # Positive residual 2 at q=.25 -> .5; negative residual -1 at q=.75 -> .25.
    pinball = result['by_target']['x0']['pinball']
    assert value(pinball[0]) == .5
    assert value(pinball[1]) == .25
    assert result['quantile_levels'] == [.25,.75]
    assert result['per_origin'][0]['pinball_loss'] == [[[.5,.25]], [[.5,.25]]]
    no_quantiles = evaluate(targets,fixture()[1],train)
    assert no_quantiles['quantile_levels'] == []
    assert no_quantiles['by_target']['x0']['pinball'] is None


@pytest.mark.parametrize('change', ['dataset','origin','coordinates','unit','target','transform'])
def test_identity_coordinate_unit_order_and_transform_mismatch_rejected(change):
    targets,pred,train = fixture()
    grid = pred.grid
    if change == 'dataset':
        grid = replace(grid,dataset_fingerprint='another')
    elif change == 'origin':
        grid = replace(grid,origin_ids=('other0','other1'))
    elif change == 'coordinates':
        grid = replace(grid,issue_times_ns=grid.issue_times_ns+SECOND,
                       starts_ns=grid.starts_ns+SECOND,ends_ns=grid.ends_ns+SECOND)
    elif change == 'unit':
        grid = replace(grid,spec=replace(grid.spec,target_units=('wrong',)))
    elif change == 'target':
        grid = replace(grid,spec=replace(grid.spec,target_names=('wrong',)))
    else:
        grid = replace(grid,spec=replace(grid.spec,transform='log10',
                                         target_reference=(1.,),feature_reference=(1.,)))
    with pytest.raises(ValueError,match='align'):
        evaluate(targets,replace(pred,grid=grid),train)


def test_persistence_and_training_alignment_are_checked_independently():
    targets,pred,train=fixture()
    bad=replace(pred,grid=replace(pred.grid,dataset_fingerprint='other'))
    with pytest.raises(ValueError,match='align'):
        evaluate(targets,pred,train,bad)
    bad_train=replace(train,context=replace(train.context,dataset_fingerprint='other'),
                      targets=replace(train.targets,grid=replace(train.targets.grid,dataset_fingerprint='other')))
    with pytest.raises(ValueError,match='align'):
        evaluate(targets,pred,bad_train)


def test_no_raw_aggregate_mixes_incommensurate_units():
    args=fixture(values=[[[2.,20.],[4.,40.]],[[6.,60.],[8.,80.]]],
                 predictions=np.zeros((2,2,2)),units=('unit_a','unit_b'))
    result=evaluate(*args,target_weights=[1.,2.])
    assert value(result['by_target']['x0']['mae']) == 5.
    assert value(result['by_target']['x1']['mae']) == 50.
    assert result['aggregate']['mae']['value'] is None
    assert result['aggregate']['mae']['reason'] == 'incompatible_target_units'
    compatible=fixture(values=[[[2.,20.],[4.,40.]],[[6.,60.],[8.,80.]]],
                       predictions=np.zeros((2,2,2)),units=('unit','unit'))
    pooled=evaluate(*compatible,target_weights=[1.,2.])
    assert value(pooled['aggregate']['mae']) == pytest.approx(35.)
    assert value(pooled['aggregate']['rmse']) == pytest.approx(44.83302354291979)


@pytest.mark.parametrize('weights', [[-1.,1.],[0.,0.],[np.nan,1.],[np.inf,1.],[1.],[[1.,1.]]])
def test_invalid_aggregation_weights_rejected(weights):
    with pytest.raises(ValueError,match='weight'):
        evaluate(*fixture(),lead_weights=weights)


def test_zero_weight_excludes_lead_only_from_weighted_reductions():
    result=evaluate(*fixture(),lead_weights=[1.,0.])
    assert value(result['by_target']['x0']['mae']) == 1.
    assert result['by_target']['x0']['mae']['count'] == 2
    assert result['coverage']['valid_count'] == 4
    assert result['by_target_lead']['x0'][1]['mae']['count'] == 2


def test_log_fitted_predictions_are_scored_in_declared_native_units():
    targets,pred,train=fixture(transform='log10',feature_reference=(10.,),target_reference=(10.,))
    result=evaluate(targets,replace(pred,point_interpretation='inverse_transformed_point'),train)
    assert value(result['by_target']['x0']['mae']) == 2.5
    assert result['space'] == 'native'
    assert result['model_transform'] == 'log10'
    assert result['point_interpretation'] == 'inverse_transformed_point'
