"""Hand-checked baseline outputs and causal training/prediction boundaries."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import (
    ForecastSpec, ForecastContext, FutureGrid, ForecastTargets, TrainingSlice,
)

SECOND = 1_000_000_000


def baseline(name, **parameters):
    # Local import lets the initial RED name the missing implementation in a test.
    from solar_flare_jepa.forecasting.baselines import make_baseline
    return make_baseline(name, parameters)


def spec(**changes):
    defaults = dict(cadence_seconds=1, context_steps=3, horizon_steps=2,
                    feature_names=('x',), target_names=('x',),
                    feature_units=('unit',), target_units=('unit',))
    return ForecastSpec(**(defaults | changes))


def context_grid(values, s=None, *, issue=20, issue_step=1, mask=None, identity='dataset'):
    s = s or spec()
    values = np.asarray(values, float).reshape(-1, s.context_steps, len(s.feature_names))
    n = len(values)
    issues = (issue + np.arange(n, dtype=np.int64) * issue_step) * SECOND
    starts = issues[:, None] + np.arange(-s.context_steps, 0, dtype=np.int64) * SECOND
    ends = starts + SECOND
    context = ForecastContext(values, np.ones_like(values, bool) if mask is None else mask,
                              starts, ends, issues, tuple(f'o{i}' for i in issues), s,
                              identity, np.broadcast_to(ends[:, :, None], values.shape))
    future = issues[:, None] + np.arange(s.horizon_steps, dtype=np.int64) * SECOND
    grid = FutureGrid(future, future + SECOND, issues, context.origin_ids, s, identity)
    return context, grid


def training(raw=(1, 2, 3, 4, 5, 6, 7), s=None, *, windows=None, future=None,
             raw_mask=None, raw_times=None, window_mask=None, target_mask=None):
    s = s or spec()
    raw = np.asarray(raw, float).reshape(-1, len(s.target_names))
    raw_features = np.zeros((len(raw), len(s.feature_names)))
    for i, name in enumerate(s.feature_names):
        if name in s.target_names:
            raw_features[:, i] = raw[:, s.target_names.index(name)]
    raw_mask = np.ones_like(raw, bool) if raw_mask is None else raw_mask
    if windows is None:
        windows = raw_features[:s.context_steps].reshape(1, s.context_steps, -1)
    context, grid = context_grid(windows, s, issue=s.context_steps, mask=window_mask)
    if future is None:
        future = raw[s.context_steps:s.context_steps+s.horizon_steps][None]
    future = np.asarray(future, float).reshape(len(context.origin_ids), s.horizon_steps, len(s.target_names))
    times = np.arange(len(raw), dtype=np.int64) if raw_times is None else np.asarray(raw_times, np.int64)
    starts = times * SECOND
    if target_mask is None:
        target_mask = raw_mask[np.searchsorted(starts, grid.starts_ns)]
    targets = ForecastTargets(np.where(target_mask, future, np.nan), target_mask, grid)
    return TrainingSlice(context, targets, starts, starts+SECOND, raw_features,
                         np.ones_like(raw_features, bool), raw, raw_mask,
                         0, max(int(times[-1])+1, s.context_steps+s.horizon_steps+len(context.origin_ids))*SECOND,
                         'split', raw_availability_ns=np.broadcast_to(starts[:, None]+SECOND, raw_features.shape))


def ridge_training(windows, future, s=None, *, window_mask=None, target_mask=None):
    """Independent literal rows with disjoint support, backed by one raw grid.

    Separate context+target blocks avoid fabricating conflicting overlapping
    observations when testing prescribed multi-lead linear maps.
    """
    s = s or spec()
    windows, future = np.asarray(windows, float), np.asarray(future, float)
    wm = np.ones_like(windows, bool) if window_mask is None else window_mask
    tm = np.ones_like(future, bool) if target_mask is None else target_mask
    context, grid = context_grid(np.where(wm, windows, np.nan), s,
        issue=s.context_steps, issue_step=s.context_steps+s.horizon_steps, mask=wm)
    size = len(windows) * (s.context_steps+s.horizon_steps)
    starts = np.arange(size, dtype=np.int64) * SECOND
    features, targets = np.ones((size, len(s.feature_names))), np.ones((size, len(s.target_names)))
    fm, raw_tm = np.ones_like(features, bool), np.ones_like(targets, bool)
    cr, tr = context.starts_ns // SECOND, grid.starts_ns // SECOND
    features[cr], fm[cr] = np.where(wm, windows, np.nan), wm
    targets[tr], raw_tm[tr] = np.where(tm, future, np.nan), tm
    return TrainingSlice(context, ForecastTargets(np.where(tm, future, np.nan), tm, grid),
        starts, starts+SECOND, features, fm, targets, raw_tm, 0, size*SECOND, 'split',
        raw_availability_ns=starts[:, None]+SECOND)


@pytest.mark.parametrize('name,parameters,context,want', [
    ('persistence', {}, [2, 4, 6], [[[6], [6]]]),
    ('training_mean', {}, [2, 4, 6], [[[4], [4]]]),
    ('trailing_mean', {'lookback_steps': 2}, [2, 4, 6], [[[5], [5]]]),
    ('drift', {'lookback_steps': 3}, [2, 4, 6], [[[8], [10]]]),
    # Training follows x_next = 1 + 2*x; forecast 255, then 511.
    ('ar1', {}, [31, 63, 127], [[[255], [511]]]),
])
def test_literal_outputs_for_five_baselines(name, parameters, context, want):
    raw = [1, 3, 7, 15, 31, 63, 127] if name == 'ar1' else [1, 2, 3, 4, 5, 6, 7]
    model = baseline(name, **parameters).fit(training(raw))
    ctx, grid = context_grid(context)
    prediction = model.predict(ctx, grid)
    np.testing.assert_allclose(prediction.values, want, rtol=1e-12)
    assert prediction.grid is grid
    assert prediction.point_interpretation == 'native_point'
    assert prediction.model_id == name
    json.dumps(model.parameters, allow_nan=False)


def test_training_mean_uses_unique_raw_values_not_overlapping_windows():
    raw = [1, 2, 3, 4, 20, 30, 40]
    one = training(raw)
    overlap = training(raw, windows=[[[1], [2], [3]], [[2], [3], [4]]],
                       future=[[[4], [20]], [[20], [30]]])
    ctx, grid = context_grid([90, 100, 110])
    for train in (one, overlap):
        prediction = baseline('training_mean').fit(train).predict(ctx, grid)
        np.testing.assert_allclose(prediction.values, [[[100/7], [100/7]]])


def test_training_mean_respects_per_target_valid_raw_mask():
    train = training([1, 2, 3, 4, 5, 6, 700], raw_mask=np.array([[1], [1], [1], [1], [1], [1], [0]], bool))
    ctx, grid = context_grid([2, 3, 4])
    np.testing.assert_allclose(baseline('training_mean').fit(train).predict(ctx, grid).values, [[[3.5], [3.5]]])


def test_ar_pairs_never_bridge_masked_rows_or_time_gaps():
    # Only (1,3), (3,7), (20,41), (41,83) are adjacent valid pairs.
    train = training([1, 3, 7, 999, 20, 41, 83],
                     raw_times=[0, 1, 2, 3, 5, 6, 7],
                     # Neither contiguous run spans L+H; AR fits raw pairs,
                     # so no fictional supervised window bridges the gap.
                     windows=np.empty((0,3,1)), future=np.empty((0,2,1)),
                     raw_mask=np.array([[1], [1], [1], [0], [1], [1], [1]], bool))
    ctx, grid = context_grid([20, 41, 83])
    np.testing.assert_allclose(baseline('ar1').fit(train).predict(ctx, grid).values, [[[167], [335]]], rtol=1e-12)


def test_direct_ridge_recovers_two_lead_linear_map_with_intercept():
    train = ridge_training(windows=[[[0], [0], [0]], [[0], [0], [1]], [[0], [0], [2]]],
                     future=[[[1], [2]], [[3], [5]], [[5], [8]]])
    ctx, grid = context_grid([100, 100, 4])
    prediction = baseline('direct_ridge', lag_steps=1, alpha=0).fit(train).predict(ctx, grid)
    np.testing.assert_allclose(prediction.values, [[[9], [14]]], atol=1e-12)


def test_ridge_regularizes_slopes_but_not_intercept():
    train = ridge_training(windows=[[[0], [0], [0]], [[0], [0], [1]], [[0], [0], [2]]],
                     future=[[[1], [2]], [[3], [5]], [[5], [8]]])
    ctx, grid = context_grid([0, 0, 4])
    np.testing.assert_allclose(baseline('direct_ridge', lag_steps=1, alpha=2).fit(train).predict(ctx, grid).values,
                               [[[6], [9.5]]], atol=1e-12)


@pytest.mark.parametrize('name,parameters', [('training_mean', {}), ('ar1', {}), ('direct_ridge', {'lag_steps': 1, 'alpha': 1})])
def test_held_out_data_cannot_change_fitted_numbers_or_earlier_predictions(name, parameters):
    # Altered held-out content changes dataset identity, but identical training
    # partitions must still fit identical numeric parameters.
    from solar_flare_jepa.forecasting.contracts import TimeSeriesDataset
    raw = np.array([1, 3, 7, 15, 31, 63, 127, 255, 511], float)[:, None]
    starts = np.arange(9, dtype=np.int64)*SECOND
    data = TimeSeriesDataset('synthetic', 'synthetic_fixture', starts, starts+SECOND,
                             raw, np.ones_like(raw, bool), raw, np.ones_like(raw, bool),
                             ('x',), ('x',), ('unit',), ('unit',), 1, starts[:, None]+SECOND)
    changed_values = raw.copy()
    changed_values[7:] = 1e200
    changed = replace(data, features=changed_values, targets=changed_values)
    train = training(raw[:7])
    models, predictions = [], []
    for identity in (data.fingerprint, changed.fingerprint):
        aligned_training = replace(train, context=replace(train.context, dataset_fingerprint=identity),
                                   targets=replace(train.targets, grid=replace(train.targets.grid, dataset_fingerprint=identity)))
        model = baseline(name, **parameters).fit(aligned_training)
        ctx, grid = context_grid([31, 63, 127], identity=identity)
        predictions.append(model.predict(ctx, grid).values)
        models.append(model)
    first, second = (model.parameters for model in models)
    first.pop('dataset_fingerprint')
    second.pop('dataset_fingerprint')
    assert first == second
    np.testing.assert_array_equal(predictions[0], predictions[1])
    # Returned parameter dictionaries are detached; advancing a later context
    # changes forecast state, without fitting new coefficients.
    before = models[0].parameters
    later, later_grid = context_grid([127, 1e100, 1e101], issue=30, identity=data.fingerprint)
    models[0].predict(later, later_grid)
    assert models[0].parameters == before
    before.clear()
    ctx, grid = context_grid([31, 63, 127], identity=data.fingerprint)
    np.testing.assert_array_equal(models[0].predict(ctx, grid).values, predictions[0])


def test_multitarget_mapping_preserves_target_order_units_and_shape():
    s = spec(feature_names=('y', 'x'), target_names=('x', 'y'),
             feature_units=('yunit', 'xunit'), target_units=('xunit', 'yunit'))
    train = training([[1, 10], [2, 20], [3, 30], [4, 40], [5, 50]], s,
                     windows=[[[10, 1], [20, 2], [30, 3]]])
    ctx, grid = context_grid([[[20, 2], [40, 4], [60, 6]]], s)
    prediction = baseline('persistence').fit(train).predict(ctx, grid)
    np.testing.assert_array_equal(prediction.values, [[[6, 60], [6, 60]]])
    assert prediction.grid.spec.target_units == ('xunit', 'yunit')


@pytest.mark.parametrize('name,parameters', [('persistence', {}), ('trailing_mean', {'lookback_steps': 2}), ('drift', {'lookback_steps': 2}), ('ar1', {})])
@pytest.mark.parametrize('changes', [{'feature_names': ('other',)}, {'feature_units': ('other',)}])
def test_observed_counterparts_must_have_same_name_and_units(name, parameters, changes):
    with pytest.raises(ValueError, match='counterpart|mapping|unit'):
        baseline(name, **parameters).fit(training(s=spec(**changes)))


def test_dimensioned_log_mean_and_drift_inverse_output():
    s = spec(transform='log10', feature_reference=(100,), target_reference=(10,))
    ctx, grid = context_grid([10, 100, 1000], s)
    train = training([10, 100, 1000, 10000, 100000], s)
    mean = baseline('trailing_mean', lookback_steps=2).fit(train).predict(ctx, grid)
    np.testing.assert_allclose(mean.values, [[[10**2.5], [10**2.5]]])
    assert mean.point_interpretation == 'inverse_transformed_point'
    drift = baseline('drift', lookback_steps=3).fit(train).predict(ctx, grid)
    np.testing.assert_allclose(drift.values, [[[10000], [100000]]])


def test_native_domain_violations_and_log_overflow_fail_without_clipping():
    s = spec(target_minimum=(0,))
    ctx, grid = context_grid([3, 2, 1], s)
    with pytest.raises(ValueError, match='domain'):
        baseline('drift', lookback_steps=3).fit(training(s=s)).predict(ctx, grid)
    s = spec(transform='log10', feature_reference=(1,), target_reference=(1,))
    ctx, grid = context_grid([1e-200, 1, 1e200], s)
    with pytest.raises(ValueError, match='overflow|finite'):
        baseline('drift', lookback_steps=3).fit(training(s=s)).predict(ctx, grid)
    ctx, grid = context_grid([1, 2, 0], s)
    with pytest.raises(ValueError, match='positive'):
        baseline('persistence').fit(training(s=s)).predict(ctx, grid)


def test_ar_advances_from_latest_valid_state_and_drift_uses_elapsed_support():
    mask = np.array([[[True], [True], [False]]])
    ctx, grid = context_grid([2, 4, np.nan], mask=mask)
    train = training([1, 3, 7, 15, 31, 63, 127])
    np.testing.assert_allclose(baseline('ar1').fit(train).predict(ctx, grid).values, [[[19], [39]]], rtol=1e-12)
    np.testing.assert_allclose(baseline('drift', lookback_steps=3).fit(train).predict(ctx, grid).values, [[[8], [10]]])


def test_predict_rejects_unfitted_model_mismatched_fitted_identity_and_misalignment():
    ctx, grid = context_grid([1, 2, 3])
    model = baseline('persistence')
    with pytest.raises(ValueError, match='fit'):
        model.predict(ctx, grid)
    model.fit(training())
    other_ctx = replace(ctx, dataset_fingerprint='other')
    with pytest.raises(ValueError, match='identity|dataset'):
        model.predict(other_ctx, replace(grid, dataset_fingerprint='other'))
    altered = replace(ctx.spec, target_units=('other',))
    with pytest.raises(ValueError, match='spec|identity'):
        model.predict(replace(ctx, spec=altered), replace(grid, spec=altered))
    with pytest.raises(ValueError, match='align'):
        model.predict(ctx, replace(grid, origin_ids=('different',)))


@pytest.mark.parametrize('name,parameters', [('persistence', {}), ('trailing_mean', {'lookback_steps': 2}), ('drift', {'lookback_steps': 2}), ('ar1', {}), ('direct_ridge', {'lag_steps': 2, 'alpha': 1})])
def test_insufficient_prediction_support_fails_without_origin_dropping(name, parameters):
    ctx, grid = context_grid([np.nan, np.nan, np.nan], mask=np.zeros((1, 3, 1), bool))
    with pytest.raises(ValueError, match='valid|support|context'):
        baseline(name, **parameters).fit(training()).predict(ctx, grid)


@pytest.mark.parametrize('name,parameters', [
    ('trailing_mean', {'lookback_steps': 0}), ('trailing_mean', {'lookback_steps': True}),
    ('drift', {'lookback_steps': 1}), ('drift', {'lookback_steps': 1.5}),
    ('direct_ridge', {'lag_steps': -1, 'alpha': 1}),
    ('direct_ridge', {'lag_steps': 1, 'alpha': -1}),
    ('direct_ridge', {'lag_steps': 1, 'alpha': float('nan')}),
    ('direct_ridge', {'lag_steps': 1, 'alpha': True}),
    ('persistence', {'unknown': 1}), ('unknown', {}),
])
def test_constructor_parameters_fail_clearly(name, parameters):
    with pytest.raises(ValueError):
        baseline(name, **parameters)


def test_requested_lags_cannot_exceed_declared_context():
    for name, parameters in [('drift', {'lookback_steps': 4}), ('direct_ridge', {'lag_steps': 4, 'alpha': 1})]:
        with pytest.raises(ValueError, match='context|lookback|lag'):
            baseline(name, **parameters).fit(training())


def test_insufficient_training_fit_samples_fail_clearly():
    train = training(raw_mask=np.zeros((7, 1), bool))
    for name in ('training_mean', 'ar1'):
        with pytest.raises(ValueError, match='valid|sample|pair'):
            baseline(name).fit(train)
    train = training(raw_mask=np.zeros((7, 1), bool))
    with pytest.raises(ValueError, match='valid|sample|window'):
        baseline('direct_ridge', lag_steps=1, alpha=1).fit(train)


def test_ridge_fit_uses_only_complete_declared_lags_and_full_targets():
    # The fourth row is not fit: one future target is invalid. Missing old
    # context bins in the first three rows do not affect a one-lag fit.
    windows = [[[np.nan], [np.nan], [0]], [[np.nan], [np.nan], [1]],
               [[np.nan], [np.nan], [2]], [[0], [0], [1e100]]]
    future = [[[1], [2]], [[3], [5]], [[5], [8]], [[1e200], [np.nan]]]
    wm = np.array([[[0], [0], [1]], [[0], [0], [1]], [[0], [0], [1]], [[1], [1], [1]]], bool)
    tm = np.array([[[1], [1]], [[1], [1]], [[1], [1]], [[1], [0]]], bool)
    train = ridge_training(windows=windows, future=future, window_mask=wm, target_mask=tm)
    ctx, grid = context_grid([np.nan, np.nan, 4], mask=np.array([[[0], [0], [1]]], bool))
    model = baseline('direct_ridge', lag_steps=1, alpha=0).fit(train)
    np.testing.assert_allclose(model.predict(ctx, grid).values, [[[9], [14]]], atol=1e-12)
    assert model.parameters['valid_window_count'] == 3


@pytest.mark.parametrize('name,want', [('training_mean', [[[1000], [1000]]]), ('ar1', [[[10000], [100000]]])])
def test_training_fits_are_in_fixed_dimensioned_log_space(name, want):
    s = spec(transform='log10', feature_reference=(100,), target_reference=(10,))
    train = training([10, 100, 1000, 10000, 100000], s)
    ctx, grid = context_grid([10, 100, 1000], s)
    pred = baseline(name).fit(train).predict(ctx, grid)
    np.testing.assert_allclose(pred.values, want, rtol=1e-12)
    assert pred.point_interpretation == 'inverse_transformed_point'


def test_ridge_transforms_features_and_targets_with_their_own_references():
    s = spec(transform='log10', feature_reference=(100,), target_reference=(10,))
    train = ridge_training(s=s,
                     windows=[[[10], [10], [100]], [[10], [10], [1000]], [[10], [10], [10000]]],
                     future=[[[10], [100]], [[100], [10000]], [[1000], [1000000]]])
    ctx, grid = context_grid([10, 10, 100000], s)
    prediction = baseline('direct_ridge', lag_steps=1, alpha=0).fit(train).predict(ctx, grid)
    # log feature = 3; target coordinates = (3, 7), inverse native = (1e4, 1e8).
    np.testing.assert_allclose(prediction.values, [[[10000], [100000000]]], rtol=1e-12)


@pytest.mark.parametrize('name,parameters', [('persistence', {}), ('training_mean', {}), ('trailing_mean', {'lookback_steps': 2}), ('drift', {'lookback_steps': 3}), ('ar1', {}), ('direct_ridge', {'lag_steps': 1, 'alpha': 1})])
def test_constant_series_forecasts_remain_constant(name, parameters):
    ctx, grid = context_grid([5, 5, 5])
    model = baseline(name, **parameters).fit(training([5]*7))
    np.testing.assert_allclose(model.predict(ctx, grid).values, [[[5], [5]]], rtol=1e-12)
