"""Probabilistic classical comparators: quantile contracts, train-only fits, causality."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastSpec, ForecastTargets, FutureGrid, TrainingSlice,
)
from solar_flare_jepa.forecasting.statistical import QUANTILE_LEVELS, make_probabilistic

CADENCE = 60 * 1_000_000_000
L, H = 12, 4
SPEC = ForecastSpec(cadence_seconds=60, context_steps=L, horizon_steps=H,
                    feature_names=('xa', 'xb'), target_names=('xa', 'xb'),
                    feature_units=('W/m2', 'W/m2'), target_units=('W/m2', 'W/m2'),
                    transform='log10', feature_reference=(1., 1.), target_reference=(1., 1.))
CONFIGS = [('persistence_empirical', {}),
           ('arima', {'order': [1, 0, 0]}),
           ('arima', {'order': [1, 1, 1]}),
           ('arima', {'order': [1, 0, 0], 'seasonal_order': [1, 0, 0, 4]}),
           ('volatility', {'vol': 'constant', 'dist': 'normal', 'simulations': 200}),
           ('volatility', {'vol': 'arch', 'dist': 'normal', 'simulations': 200}),
           ('volatility', {'vol': 'garch', 'dist': 't', 'simulations': 200}),
           ('volatility', {'vol': 'gjr', 'dist': 't', 'simulations': 200})]


def flux(n, seed=0, phi=0.7):
    """Positive synthetic 'flux': AR(1) in log10 space around -6, two channels."""
    rng = np.random.default_rng(seed)
    y = np.full((n, 2), -6.)
    for t in range(1, n):
        y[t] = -6 + phi * (y[t - 1] + 6) + rng.normal(0, 0.05, 2) * (1 + (t % 50 < 5))
    return 10 ** y


def training(raw, mask=None, issues=(L, L + 10), identity='dataset'):
    raw = np.asarray(raw, float)
    mask = np.ones_like(raw, bool) if mask is None else mask
    raw = np.where(mask, raw, np.nan)
    starts = np.arange(len(raw), dtype=np.int64) * CADENCE
    issues = np.asarray(issues, np.int64)
    crow = issues[:, None] + np.arange(-L, 0)
    trow = issues[:, None] + np.arange(H)
    cstarts = starts[crow]
    available = np.broadcast_to((cstarts + CADENCE)[:, :, None], crow.shape + (2,))
    context = ForecastContext(raw[crow], mask[crow], cstarts, cstarts + CADENCE, starts[issues],
                              tuple(f't{i}' for i in issues), SPEC, identity, available)
    grid = FutureGrid(starts[trow], starts[trow] + CADENCE, starts[issues], context.origin_ids, SPEC, identity)
    return TrainingSlice(context, ForecastTargets(raw[trow], mask[trow], grid), starts, starts + CADENCE,
                         raw, mask, raw, mask, 0, len(raw) * CADENCE, 'split',
                         raw_availability_ns=np.broadcast_to((starts + CADENCE)[:, None], raw.shape))


def context_grid(windows, issue=10_000, mask=None, identity='dataset'):
    windows = np.asarray(windows, float).reshape(-1, L, 2)
    mask = np.ones_like(windows, bool) if mask is None else mask
    issues = (issue + np.arange(len(windows), dtype=np.int64) * 7) * CADENCE
    starts = issues[:, None] + np.arange(-L, 0, dtype=np.int64) * CADENCE
    context = ForecastContext(np.where(mask, windows, np.nan), mask, starts, starts + CADENCE, issues,
                              tuple(f'o{i}' for i in issues), SPEC, identity,
                              np.broadcast_to((starts + CADENCE)[:, :, None], windows.shape))
    future = issues[:, None] + np.arange(H, dtype=np.int64) * CADENCE
    return context, FutureGrid(future, future + CADENCE, issues, context.origin_ids, SPEC, identity)


RAW = flux(600)
TRAIN = training(RAW)
WINDOWS = np.stack([flux(L, seed=5), flux(L, seed=6)])


@pytest.fixture(scope='module')
def fitted():
    return {(name, json.dumps(p, sort_keys=True)): make_probabilistic(name, p).fit(TRAIN) for name, p in CONFIGS}


def model(fitted, name, parameters):
    return fitted[(name, json.dumps(parameters, sort_keys=True))]


@pytest.mark.parametrize('name,parameters', CONFIGS)
def test_quantile_contract_shapes_ordering_and_median_point(fitted, name, parameters):
    m = model(fitted, name, parameters)
    ctx, grid = context_grid(WINDOWS)
    prediction = m.predict(ctx, grid)
    assert prediction.quantiles.shape == (2, H, 2, len(QUANTILE_LEVELS))
    assert prediction.quantile_levels == QUANTILE_LEVELS
    assert np.isfinite(prediction.quantiles).all() and (prediction.quantiles > 0).all()
    assert (np.diff(prediction.quantiles, axis=-1) >= 0).all()
    np.testing.assert_array_equal(prediction.values, prediction.quantiles[..., QUANTILE_LEVELS.index(0.5)])
    assert prediction.point_interpretation == 'inverse_transformed_point'
    assert prediction.model_id == m.name == m.parameters['name']
    # Predictive spread is nondegenerate for every comparator.
    assert (prediction.quantiles[..., -1] > prediction.quantiles[..., 0]).all()
    json.dumps(m.parameters, allow_nan=False)


def test_model_ids_are_descriptive_and_unique():
    ids = [make_probabilistic(n, p).name for n, p in CONFIGS] + [
        make_probabilistic('arima', {'order': [1, 1, 1], 'seasonal_order': [1, 0, 0, 60], 'fit_last_steps': 20160}).name,
        make_probabilistic('volatility', {'vol': 'garch', 'dist': 't', 'sim_seed': 3}).name]
    assert len(set(ids)) == len(ids)
    assert 'arima(1,1,1)' in ids and 'sarima(1,0,0)(1,0,0,4)' in ids
    assert 'ar1-gjr-garch(1,1)-t-sim200' in ids and 'sarima(1,1,1)(1,0,0,60)-last20160' in ids
    assert make_probabilistic('volatility', {'vol': 'arch'}).name == 'ar1-arch(1)-normal'


@pytest.mark.parametrize('name,parameters', CONFIGS)
def test_predict_refuses_unfitted_model(name, parameters):
    ctx, grid = context_grid(WINDOWS)
    with pytest.raises(ValueError, match='fit'):
        make_probabilistic(name, parameters).predict(ctx, grid)


@pytest.mark.parametrize('name,parameters', CONFIGS)
def test_fit_identity_ignores_held_out_data_and_predictions_are_causal(fitted, name, parameters):
    # A different full-dataset identity (e.g. altered validation/test content)
    # with identical training support must fit identical numbers.
    other = make_probabilistic(name, parameters).fit(training(RAW, identity='altered-held-out'))
    first, second = model(fitted, name, parameters).parameters, other.parameters
    first.pop('dataset_fingerprint'), second.pop('dataset_fingerprint')
    assert first == second
    # Origin 0's forecast cannot see the later origin, whose context overlaps
    # origin 0's future bins; nor does it depend on origin batching.
    m = model(fitted, name, parameters)
    ctx, grid = context_grid(WINDOWS)
    altered = WINDOWS.copy()
    altered[1] *= 1e3
    ctx2, grid2 = context_grid(altered)
    alone_ctx, alone_grid = context_grid(WINDOWS[:1])
    a, b, c = m.predict(ctx, grid), m.predict(ctx2, grid2), m.predict(alone_ctx, alone_grid)
    np.testing.assert_array_equal(a.quantiles[0], b.quantiles[0])
    np.testing.assert_array_equal(a.quantiles[0], c.quantiles[0])


def test_training_values_change_fit_only_through_the_training_slice():
    m1 = make_probabilistic('arima', {'order': [1, 0, 0]}).fit(TRAIN)
    raw = RAW.copy()
    raw[-1] *= 100  # last training row, outside every training window
    m2 = make_probabilistic('arima', {'order': [1, 0, 0]}).fit(training(raw))
    assert m1.parameters['params'] != m2.parameters['params']


@pytest.mark.parametrize('vol', ['garch', 'gjr'])
def test_garch_parameters_satisfy_positivity_constraints(fitted, vol):
    record = model(fitted, 'volatility', {'vol': vol, 'dist': 't', 'simulations': 200}).parameters
    for names, values in zip(record['param_names'], record['params']):
        p = dict(zip(names, values))
        assert p['omega'] > 0 and p['alpha[1]'] >= 0 and p['beta[1]'] >= 0
        assert p['alpha[1]'] + p.get('gamma[1]', 0) >= 0
        assert p['nu'] > 2
    assert all(np.isfinite(record['persistence']))


def test_simulation_is_deterministic_given_seed():
    ctx, grid = context_grid(WINDOWS)
    make = lambda seed: make_probabilistic('volatility', {'vol': 'garch', 'dist': 'normal',
                                                          'simulations': 300, 'sim_seed': seed}).fit(TRAIN)
    one, two, other = make(7).predict(ctx, grid), make(7).predict(ctx, grid), make(8).predict(ctx, grid)
    np.testing.assert_array_equal(one.quantiles, two.quantiles)
    assert not np.array_equal(one.quantiles, other.quantiles)


def test_arima_recovers_ar_coefficient_on_synthetic_ar_process():
    raw = flux(3000, seed=1, phi=0.7)
    m = make_probabilistic('arima', {'order': [1, 0, 0]}).fit(training(raw))
    for names, values in zip(m.parameters['param_names'], m.parameters['params']):
        p = dict(zip(names, values))
        assert abs(p['ar.L1'] - 0.7) < 0.05
    assert all(m.parameters['converged'])
    # fit_last_steps fits on the documented tail of the training grid only.
    tail = make_probabilistic('arima', {'order': [1, 0, 0], 'fit_last_steps': 500}).fit(training(raw))
    assert tail.parameters['fit_grid_steps'] == [500, 500]


def test_persistence_empirical_median_is_last_value_plus_median_increment(fitted):
    m = model(fitted, 'persistence_empirical', {})
    ctx, grid = context_grid(WINDOWS)
    prediction = m.predict(ctx, grid)
    y = np.log10(RAW)
    for h in range(1, H + 1):
        median_increment = np.median(y[h:] - y[:-h], axis=0)
        np.testing.assert_allclose(np.log10(prediction.values[:, h - 1]),
                                   np.log10(WINDOWS[:, -1]) + median_increment, rtol=0, atol=1e-12)


def test_stale_context_uses_elapsed_leads_and_gaps_in_training_are_not_bridged(fitted):
    mask = np.ones((1, L, 2), bool)
    mask[0, -1] = False
    ctx, grid = context_grid(WINDOWS[:1], mask=mask)
    prediction = model(fitted, 'persistence_empirical', {}).predict(ctx, grid)
    y = np.log10(RAW)
    want = np.log10(WINDOWS[0, -2]) + np.median(y[2:] - y[:-2], axis=0)
    np.testing.assert_allclose(np.log10(prediction.values[0, 0]), want, atol=1e-12)
    for name, parameters in CONFIGS[1:]:
        assert np.isfinite(model(fitted, name, parameters).predict(ctx, grid).quantiles).all()
    # Invalid training bins never contribute increments.
    raw_mask = np.ones_like(RAW, bool)
    raw_mask[100:110] = False
    gapped = make_probabilistic('persistence_empirical', {}).fit(training(RAW, raw_mask))
    assert gapped.parameters['valid_pair_counts'][0] == [len(RAW) - 1 - 11] * 2


def test_insufficient_context_support_fails_without_origin_dropping(fitted):
    ctx, grid = context_grid(WINDOWS[:1], mask=np.zeros((1, L, 2), bool))
    for name, parameters in CONFIGS:
        with pytest.raises(ValueError, match='valid|support|context'):
            model(fitted, name, parameters).predict(ctx, grid)


@pytest.mark.parametrize('name,parameters', [
    ('arima', {}), ('arima', {'order': [1, 0]}), ('arima', {'order': [1, -1, 0]}),
    ('arima', {'order': [1, 0, 0], 'seasonal_order': [1, 0, 0, 1]}),
    ('arima', {'order': [1, 0, 0], 'seasonal_order': [0, 0, 0, 60]}),
    ('arima', {'order': [1, 0, 0], 'fit_last_steps': 1.5}),
    ('volatility', {'vol': 'egarch'}), ('volatility', {'vol': 'garch', 'dist': 'skewt'}),
    ('volatility', {'vol': 'garch', 'simulations': True}), ('volatility', {'vol': 'garch', 'sim_seed': -1}),
    ('persistence_empirical', {'unknown': 1}), ('unknown', {}),
])
def test_constructor_parameters_fail_clearly(name, parameters):
    with pytest.raises(ValueError):
        make_probabilistic(name, parameters)


@pytest.mark.parametrize('vol', ['constant', 'arch', 'garch', 'gjr'])
def test_two_stage_mean_is_stationary_and_multistart_keeps_best_likelihood(vol):
    record = make_probabilistic('volatility', {'vol': vol, 'dist': 't', 'simulations': 200}).fit(TRAIN).parameters
    assert 'two-stage' in record['estimator']
    for mean, starts, likelihood in zip(record['mean'], record['starts'], record['loglikelihood']):
        assert abs(mean['phi']) < 1
        finite = [s['loglikelihood'] for s in starts if s.get('loglikelihood') is not None]
        assert starts[0]['start'] is None and finite
        assert likelihood == pytest.approx(max(finite))


def test_shared_mean_makes_variance_models_differ_only_in_distribution():
    means = [make_probabilistic('volatility', {'vol': vol, 'dist': 'normal', 'simulations': 200}).fit(TRAIN).parameters['mean']
             for vol in ('constant', 'garch')]
    assert means[0] == means[1]
