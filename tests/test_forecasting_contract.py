"""Contracts reject inputs that could silently change a forecast's meaning."""
from dataclasses import replace

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import (
    ForecastSpec, TimeSeriesDataset, ForecastContext, FutureGrid,
    ForecastTargets, ForecastPrediction, TrainingSlice, validate_alignment,
)

MINUTE = 60_000_000_000


def spec(**kwargs):
    return ForecastSpec(cadence_seconds=60, context_steps=2, horizon_steps=2,
                        feature_names=('x',), target_names=('x',),
                        feature_units=('unit',), target_units=('unit',), **kwargs)


def dataset():
    starts = np.arange(6, dtype=np.int64) * MINUTE
    values = np.arange(1., 7.)[:, None]
    return TimeSeriesDataset('toy', 'synthetic_fixture', starts, starts + MINUTE,
                            values, np.ones_like(values, dtype=bool), values,
                            np.ones_like(values, dtype=bool), ('x',), ('x',),
                            ('unit',), ('unit',), 60, starts[:, None] + MINUTE)


def context_and_grid(s=None):
    s = s or spec()
    context = ForecastContext(np.array([[[1.], [2.]]]), np.ones((1, 2, 1), bool),
                              np.array([[0, MINUTE]], np.int64),
                              np.array([[MINUTE, 2*MINUTE]], np.int64),
                              np.array([2*MINUTE], np.int64), ('o2',), s, 'dataset',
                              np.array([[[MINUTE], [2*MINUTE]]], np.int64))
    grid = FutureGrid(np.array([[2*MINUTE, 3*MINUTE]], np.int64),
                      np.array([[3*MINUTE, 4*MINUTE]], np.int64),
                      context.issue_times_ns, context.origin_ids, s, 'dataset')
    return context, grid


def test_input_mutation_and_write_flag_cannot_change_dataset_identity():
    data = dataset()
    fingerprint = data.fingerprint
    with pytest.raises(ValueError):
        data.features[0, 0] = 999
    with pytest.raises(ValueError):
        data.starts_ns.setflags(write=True)
    original = np.array([[5.], [6.]])
    ctx, _ = context_and_grid()
    changed = replace(ctx, values=original[None])
    original[:] = 999
    np.testing.assert_array_equal(changed.values, [[[5.], [6.]]])
    assert data.fingerprint == fingerprint


@pytest.mark.parametrize('changes', [
    {'context_steps': 0}, {'horizon_steps': 1.5}, {'stride_steps': True},
    {'feature_lookback_steps': -1}, {'target_units': ()},
    {'feature_names': ('x', 'x')}, {'availability_mode': 'invented'},
])
def test_spec_rejects_ambiguous_or_unsupported_definitions(changes):
    with pytest.raises(ValueError):
        replace(spec(), **changes)


def test_valid_missing_values_fail_but_explicit_masked_nan_is_preserved():
    data = dataset()
    values = np.array(data.features)
    values[1, 0] = np.nan
    with pytest.raises(ValueError, match='finite'):
        replace(data, features=values)
    mask = np.array(data.feature_mask)
    mask[1, 0] = False
    masked = replace(data, features=values, feature_mask=mask)
    assert np.isnan(masked.features[1, 0])
    assert masked.fingerprint != data.fingerprint


def test_dataset_rejects_undeclared_role_irregular_grid_and_false_availability():
    data = dataset()
    with pytest.raises(ValueError):
        replace(data, role='native_solexs')
    with pytest.raises(ValueError):
        replace(data, starts_ns=np.array([0, 1, 2, 3, 4, 5], np.int64))
    with pytest.raises(ValueError, match='availability'):
        replace(data, availability_ns=np.zeros((6, 1), np.int64))


def test_operational_unknown_availability_rejected_retrospective_explicit():
    ctx, grid = context_and_grid()
    with pytest.raises(ValueError, match='availability'):
        replace(ctx, availability_ns=None)
    retrospective = replace(ctx, spec=spec(availability_mode='retrospective_bin_end'),
                            availability_ns=None)
    assert retrospective.availability_ns is None
    with pytest.raises(ValueError, match='availability'):
        replace(ctx, availability_ns=np.array([[[MINUTE], [3*MINUTE]]]))


def test_context_cannot_include_first_target_bin_and_future_grid_has_no_values():
    ctx, grid = context_and_grid()
    with pytest.raises(ValueError):
        replace(ctx, starts_ns=ctx.starts_ns + MINUTE, ends_ns=ctx.ends_ns + MINUTE)
    assert not hasattr(grid, 'values')
    with pytest.raises(ValueError):
        replace(grid, starts_ns=grid.starts_ns-MINUTE, ends_ns=grid.ends_ns-MINUTE)


def test_alignment_checks_identity_order_times_units_and_spec():
    ctx, grid = context_and_grid()
    validate_alignment(ctx, grid)
    with pytest.raises(ValueError, match='align'):
        validate_alignment(ctx, replace(grid, dataset_fingerprint='other'))
    with pytest.raises(ValueError, match='align'):
        validate_alignment(ctx, replace(grid, origin_ids=('other',)))
    with pytest.raises(ValueError, match='align'):
        validate_alignment(ctx, replace(grid, spec=replace(grid.spec, target_units=('other',))))


def test_prediction_requires_finite_correct_shapes_and_ordered_quantiles():
    _, grid = context_and_grid()
    with pytest.raises(ValueError):
        ForecastPrediction(np.ones((1, 2)), grid, 'toy')
    with pytest.raises(ValueError, match='finite'):
        ForecastPrediction(np.array([[[1.], [np.inf]]]), grid, 'toy')
    with pytest.raises(ValueError):
        ForecastPrediction(np.ones((1, 2, 1)), grid, 'toy', quantile_levels=(.9, .1),
                           quantiles=np.ones((1, 2, 1, 2)))
    with pytest.raises(ValueError, match='cross'):
        ForecastPrediction(np.ones((1, 2, 1)), grid, 'toy', quantile_levels=(.1, .9),
                           quantiles=np.array([[[[2., 1.]], [[2., 1.]]]]))
    pred = ForecastPrediction(np.ones((1, 2, 1)), grid, 'toy', quantile_levels=(.1, .9),
                              quantiles=np.array([[[[0., 2.]], [[0., 2.]]]]))
    assert pred.quantiles.shape == (1, 2, 1, 2)


def test_log_transform_requires_positive_values_and_dimensioned_references():
    s = spec(transform='log10', feature_reference=(10.,), target_reference=(10.,))
    np.testing.assert_allclose(s.transform_features(np.array([[10.], [100.]])), [[0.], [1.]])
    np.testing.assert_allclose(s.inverse_targets(np.array([[0.], [1.]])), [[10.], [100.]])
    with pytest.raises(ValueError):
        s.transform_targets(np.array([[0.]]))
    with pytest.raises(ValueError):
        spec(transform='log10')
    with pytest.raises(ValueError, match='finite|overflow'):
        s.inverse_targets(np.array([[9999.]]))


def test_training_slice_rejects_nontraining_role_and_outside_raw_support():
    ctx, grid = context_and_grid()
    data = dataset()
    targets = ForecastTargets(np.array([[[3.], [4.]]]), np.ones((1, 2, 1), bool), grid)
    kwargs = dict(context=ctx, targets=targets, raw_starts_ns=data.starts_ns[:4],
                  raw_ends_ns=data.ends_ns[:4], raw_features=data.features[:4],
                  raw_feature_mask=data.feature_mask[:4], raw_targets=data.targets[:4],
                  raw_target_mask=data.target_mask[:4], partition_start_ns=0,
                  partition_end_ns=4*MINUTE, split_fingerprint='split')
    train = TrainingSlice(**kwargs)
    assert len(train.raw_targets) == 4
    with pytest.raises(ValueError, match='train'):
        TrainingSlice(**kwargs, partition_name='validation')
    with pytest.raises(ValueError):
        TrainingSlice(**{**kwargs, 'partition_end_ns': 3*MINUTE})


@pytest.mark.parametrize('bound', [float('nan'), float('inf'), True, 4.5])
def test_malformed_training_bounds_cannot_bypass_containment(bound):
    ctx, grid = context_and_grid()
    data = dataset()
    targets = ForecastTargets(np.array([[[3.], [4.]]]), np.ones((1, 2, 1), bool), grid)
    with pytest.raises(ValueError):
        TrainingSlice(ctx, targets, data.starts_ns, data.ends_ns, data.features,
                      data.feature_mask, data.targets, data.target_mask, 0, bound, 'split')


def test_scalar_metadata_is_normalized_and_external_mutation_cannot_change_it():
    minimum = np.array(0.)
    s = spec(target_minimum=(minimum,))
    identity = s.fingerprint
    minimum[...] = 100
    assert s.target_minimum == (0.,)
    assert s.fingerprint == identity
    assert isinstance(spec(target_minimum=(np.float32(0),)).fingerprint, str)
    _, grid = context_and_grid()
    q = np.array(.1)
    pred = ForecastPrediction(np.ones((1, 2, 1)), grid, 'toy', (q, .9),
                              np.array([[[[0., 2.]], [[0., 2.]]]]))
    q[...] = .8
    assert pred.quantile_levels == (.1, .9)
    with pytest.raises(ValueError):
        spec(target_minimum=(np.array([0.]),))


def test_identity_transforms_validate_target_and_feature_widths():
    with pytest.raises(ValueError):
        spec().transform_targets(np.ones((2, 2)))
    with pytest.raises(ValueError):
        spec().transform_features(np.ones((2, 2)))
    with pytest.raises(ValueError):
        spec().inverse_targets(np.ones((2, 2)))


def test_extreme_context_arithmetic_cannot_wrap_future_bins_into_the_past():
    s = replace(spec(availability_mode='retrospective_bin_end'), context_steps=1)
    issue = np.iinfo(np.int64).min + 1
    wrapped_start = np.array([issue], np.int64) - MINUTE
    with pytest.raises(ValueError):
        ForecastContext(np.ones((1,1,1)), np.ones((1,1,1), bool), wrapped_start[None],
                        np.array([[issue]], np.int64), np.array([issue], np.int64),
                        ('extreme',), s, 'dataset')


def test_quantile_predictions_obey_the_declared_target_domain():
    _, grid = context_and_grid(spec(target_minimum=(0.,)))
    with pytest.raises(ValueError, match='domain'):
        ForecastPrediction(np.ones((1,2,1)), grid, 'toy', (.1,.9),
                           np.array([[[[-1.,2.]], [[-1.,2.]]]]))


def test_earliest_availability_bound_cannot_be_labeled_actual_delivery():
    with pytest.raises(ValueError, match='availability'):
        replace(dataset(), availability_policy='bin_end_earliest')
