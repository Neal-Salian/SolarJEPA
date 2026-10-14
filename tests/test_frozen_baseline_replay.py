"""No-refit restoration, exact prediction identities, and opt-in historical replay.

SOLAR_JEPA_V1_REPLAY_DIR points at immutable local V1 artifacts. Default unit
fixtures below are invented deterministic records, not scientific observations.
Ridge replay tolerance is predeclared as 5e-14 dex, rtol=0: bounded floating
arithmetic/batching differences are not described as bitwise equality.
"""
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastContext, ForecastSpec, FutureGrid
from solar_flare_jepa.forecasting.statistical import QUANTILE_LEVELS

SPEC = ForecastSpec(1, 6, 2, ('x',), ('x',), ('unit',), ('unit',),
                    availability_mode='retrospective_bin_end')
POLICY = 'latest_valid_observed_bin; elapsed_cadence_to_future'
NAMES = ('persistence', 'training_mean', 'trailing_mean', 'drift', 'ar1', 'direct_ridge',
         'persistence_empirical', 'arima(2,1,0)', 'ar1-constant-normal',
         'ar1-arch(1)-normal', 'ar1-garch(1,1)-normal', 'ar1-garch(1,1)-t',
         'ar1-gjr-garch(1,1)-t')


def restore(record, spec=SPEC, identity='external'):
    from solar_flare_jepa.forecasting.frozen import load_frozen_baseline
    return load_frozen_baseline(record, spec, expected_training_fingerprint='training',
                                external_dataset_fingerprint=identity)


def record(name, spec=SPEC):
    r = dict(name=name, training_fingerprint='training', dataset_fingerprint='original',
             split_fingerprint='split', spec_fingerprint=spec.fingerprint,
             transform=spec.transform, feature_reference=list(spec.feature_reference),
             target_reference=list(spec.target_reference))
    k, h = len(spec.target_names), spec.horizon_steps
    if name != 'training_mean' and name != 'direct_ridge':
        r['state_policy'] = POLICY
    if name == 'training_mean':
        r.update(mean=[3.] * k, valid_sample_counts=[20] * k)
    elif name in ('trailing_mean', 'drift'):
        r['lookback_steps'] = 2
    elif name == 'ar1':
        r.update(intercept=[1.] * k, coefficient=[.5] * k, valid_pair_counts=[20] * k)
    elif name == 'direct_ridge':
        r.update(lag_steps=2, alpha=.1, coefficient=[[1.] * (h*k)] * (2*len(spec.feature_names)),
                 intercept=[0.] * (h*k), valid_window_count=20)
    elif name == 'persistence_empirical':
        r.update(quantile_levels=list(QUANTILE_LEVELS),
                 increment_quantiles=[[[-2., -1., 0., 1., 2.]] * k] * (spec.context_steps+h),
                 valid_pair_counts=[[20]*k] * (spec.context_steps+h),
                 lead_policy='leads 1..context_steps+horizon_steps from latest valid bin')
    elif name == 'arima(2,1,0)':
        r.update(order=[2,1,0], seasonal_order=[0,0,0,0], fit_last_steps=None,
                 maxiter=200, trend='n', params=[[.5,-.1,.01]]*k,
                 param_names=[['ar.L1','ar.L2','sigma2']]*k, aic=[1.]*k,
                 loglikelihood=[1.]*k, converged=[False]*k, fit_grid_steps=[20]*k,
                 valid_observation_counts=[20]*k, fit_warnings=[['fixture warning']]*k)
    elif name.startswith('ar1-'):
        vol = 'gjr' if 'gjr' in name else 'garch' if 'garch' in name else 'arch' if 'arch' in name else 'constant'
        dist = 't' if name.endswith('-t') else 'normal'
        names, params = {'constant':(['sigma2'],[.01]), 'arch':(['omega','alpha[1]'],[.01,.2]),
                         'garch':(['omega','alpha[1]','beta[1]'],[.01,.2,.80001]),
                         'gjr':(['omega','alpha[1]','gamma[1]','beta[1]'],[.01,.3,-.1,.5])}[vol]
        if dist == 't':
            names, params = names+['nu'], params+[5.]
        persistence = {'constant':0., 'arch':.2, 'garch':1.00001, 'gjr':.75}[vol]
        r.update(vol=vol, dist=dist, simulations=1000, sim_seed=0,
                 mean=[dict(const=.1,phi=.5)]*k, scale=[2.]*k, params=[params]*k,
                 param_names=[names]*k, persistence=[persistence]*k,
                 convergence_flag=[8]*k, loglikelihood=[1.]*k, valid_pair_counts=[20]*k,
                 fit_warnings=[['fixture warning']]*k, starts=[[]]*k,
                 estimator='two-stage: OLS AR(1) mean, then zero-mean variance MLE on residuals',
                 pair_policy='consecutive valid differences; residuals concatenated across gaps')
    return r


def context_grid(spec=SPEC, identity='external', values=None):
    values = np.asarray(values if values is not None else np.arange(1.,7.)[None,:,None], float)
    issues = np.arange(20,20+len(values),dtype=np.int64)*spec.cadence_ns
    starts = issues[:,None]+np.arange(-spec.context_steps,0,dtype=np.int64)*spec.cadence_ns
    ctx = ForecastContext(values,np.ones_like(values,bool),starts,starts+spec.cadence_ns,
                          issues,tuple(f'o{i}' for i in range(len(values))),spec,identity,
                          np.broadcast_to((starts+spec.cadence_ns)[:,:,None],values.shape))
    future = issues[:,None]+np.arange(spec.horizon_steps,dtype=np.int64)*spec.cadence_ns
    return ctx, FutureGrid(future,future+spec.cadence_ns,issues,ctx.origin_ids,spec,identity)


@pytest.mark.parametrize('name,want', [('persistence',[6.,6.]), ('training_mean',[3.,3.]),
    ('trailing_mean',[5.5,5.5]), ('drift',[7.,8.]), ('ar1',[4.,3.]), ('direct_ridge',[11.,11.])])
def test_frozen_point_equations(name,want):
    prediction = restore(record(name)).predict(*context_grid())
    np.testing.assert_array_equal(prediction.values[0,:,0],want)
    assert prediction.quantiles is None


@pytest.mark.parametrize('name', NAMES[6:])
def test_probabilistic_restore_preserves_state_and_recipe(name):
    original = record(name)
    model = restore(original)
    prediction = model.predict(*context_grid())
    assert prediction.quantiles.shape == (1,2,1,5)
    np.testing.assert_array_equal(prediction.values,prediction.quantiles[...,2])
    assert model.parameters == original
    assert model.training_fingerprint == 'training'
    assert model.dataset_fingerprint == 'original'
    assert model.external_dataset_fingerprint == 'external'
    # A detached public record cannot change later forecast equations.
    original['name'] = 'changed'
    model.parameters['name'] = 'changed'
    replay = model.predict(*context_grid())
    np.testing.assert_array_equal(replay.quantiles,prediction.quantiles)


def test_frozen_restore_never_calls_fit_or_optimizer(monkeypatch):
    from solar_flare_jepa.forecasting.baselines import _Baseline
    from solar_flare_jepa.forecasting.statistical import Volatility
    from solar_flare_jepa.training import jepa
    from statsmodels.tsa.statespace.mlemodel import MLEModel
    from arch.univariate.base import ARCHModel
    import scipy.optimize
    def forbidden(*args,**kwargs):
        raise AssertionError('No fitting or optimization is allowed')
    for obj,attribute in [(_Baseline,'fit'),(Volatility,'_multistart'),
                          (jepa,'fit_forecaster'),(MLEModel,'fit'),(ARCHModel,'fit'),
                          (scipy.optimize,'minimize'),(np.linalg,'lstsq')]:
        monkeypatch.setattr(obj,attribute,forbidden)
    for name in NAMES:
        output = restore(record(name)).predict(*context_grid())
        assert output.values.shape == (1,2,1)


def test_external_identity_is_distinct_and_preserved():
    r = record('ar1')
    model = restore(r)
    output = model.predict(*context_grid())
    assert output.grid.dataset_fingerprint == 'external'
    assert model.parameters == r
    assert model.training_fingerprint == r['training_fingerprint']
    with pytest.raises(ValueError):
        model.predict(*context_grid(identity='original'))
    with pytest.raises(ValueError):
        restore(dict(r,training_fingerprint='substituted'))
    with pytest.raises(ValueError):
        model.predict(*context_grid(spec=replace(SPEC,transform='log10',feature_reference=(1.,),target_reference=(1.,))))
    ctx,grid = context_grid()
    with pytest.raises(ValueError):
        model.predict(ctx,replace(grid,origin_ids=('wrong',)))
    # Underlying original guard still requires its training dataset.
    with pytest.raises(ValueError):
        model._model.predict(ctx,grid)


@pytest.mark.parametrize('name,changes', [
    ('unknown',{}), ('ar1',{'coefficient':[.2,.3]}), ('ar1',{'intercept':[float('nan')]}),
    ('training_mean',{'mean':[float('inf')]}), ('direct_ridge',{'coefficient':[[1.]]}),
    ('persistence_empirical',{'increment_quantiles':[[[0.]*5]]}),
    ('persistence_empirical',{'quantile_levels':[.1,.2,.5,.8,.9]}),
    ('persistence_empirical',{'increment_quantiles':[[[2.,1.,0.,-1.,-2.]]]*8}),
    ('arima(2,1,0)',{'param_names':[['ar.L2','ar.L1','sigma2']]}),
    ('arima(2,1,0)',{'params':[[.2,.1]]}),
    ('arima(2,1,0)',{'trend':'c'}),
    ('ar1-garch(1,1)-t',{'param_names':[['omega','beta[1]','alpha[1]','nu']]}),
    ('ar1-garch(1,1)-t',{'scale':[0.]}),
    ('ar1-garch(1,1)-t',{'mean':[dict(const=0.,phi=float('nan'))]}),
    ('persistence',{'target_reference':[2.]}), ('persistence',{'transform':'log10'}),
    ('trailing_mean',{'lookback_steps':20}), ('ar1-constant-normal',{'simulations':200}),
    ('ar1-constant-normal',{'sim_seed':7}), ('persistence',{'split_fingerprint':''}),
])
def test_restore_rejects_malformed_state(name,changes):
    with pytest.raises(ValueError):
        restore(record(name)|changes)


def test_log_references_are_applied_without_fitting_normalization():
    s = replace(SPEC,transform='log10',feature_reference=(2.,),target_reference=(2.,))
    m = restore(record('training_mean',s),s)
    np.testing.assert_array_equal(m.predict(*context_grid(s)).values,[[[2000.],[2000.]]])


def test_revalidates_tampered_exact_inputs_and_consumes_detached_snapshots():
    ctx,grid = context_grid()
    object.__setattr__(grid,'starts_ns',grid.starts_ns+SPEC.cadence_ns)
    with pytest.raises(ValueError):
        restore(record('persistence')).predict(ctx,grid)


@pytest.mark.parametrize('name',NAMES)
def test_saved_classical_state_replays_historical_predictions(name):
    root = os.environ.get('SOLAR_JEPA_V1_REPLAY_DIR')
    if root is None:
        pytest.skip('Opt-in immutable historical V1 artifact replay')
    from solar_flare_jepa.forecasting.frozen import load_frozen_baseline
    p = Path(root)
    summary = json.loads((p/'summary.json').read_text())
    s = ForecastSpec(**summary['config']['forecast'])
    r = summary['fits'][name]['parameters']
    model = load_frozen_baseline(r,s,expected_training_fingerprint=r['training_fingerprint'],
                                 external_dataset_fingerprint=r['dataset_fingerprint'])
    with np.load(p/'test_predictions.npz',allow_pickle=False) as arrays:
        n=2
        values,mask = arrays['context'][:n],arrays['context_mask'][:n]
        issues = arrays['issue_times_ns'][:n]
        origins = tuple(arrays['origin_ids'][:n].tolist())
        starts = issues[:,None]+np.arange(-s.context_steps,0,dtype=np.int64)*s.cadence_ns
        ctx = ForecastContext(values,mask,starts,starts+s.cadence_ns,issues,origins,s,r['dataset_fingerprint'],
                              np.broadcast_to((starts+s.cadence_ns)[:,:,None],values.shape))
        future = issues[:,None]+np.arange(s.horizon_steps,dtype=np.int64)*s.cadence_ns
        grid = FutureGrid(future,future+s.cadence_ns,issues,origins,s,r['dataset_fingerprint'])
        result = model.predict(ctx,grid)
        index = arrays['model_ids'].tolist().index(name)
        if name == 'direct_ridge':
            np.testing.assert_allclose(s.transform_targets(result.values),
                                       s.transform_targets(arrays[f'point_{index}'][:n]),atol=5e-14,rtol=0)
        else:
            np.testing.assert_array_equal(result.values,arrays[f'point_{index}'][:n])
        if result.quantiles is not None:
            np.testing.assert_array_equal(result.quantiles,arrays[f'quantiles_{index}'][:n])


def test_empirical_saved_table_is_used_without_fabricating_missing_support():
    model = restore(record('persistence_empirical'))
    result = model.predict(*context_grid())
    np.testing.assert_array_equal(result.quantiles[0,:,0],[[4.,5.,6.,7.,8.]]*2)
    r = record('persistence_empirical')
    r['increment_quantiles'] = [deepcopy(row) for row in r['increment_quantiles']]
    r['valid_pair_counts'] = [deepcopy(row) for row in r['valid_pair_counts']]
    r['increment_quantiles'][6][0] = [None]*5
    r['valid_pair_counts'][6][0] = 0
    model = restore(r)
    ctx,grid = context_grid()
    model.predict(ctx,grid)  # Fresh context uses supported leads 1 and 2.
    mask = np.zeros_like(ctx.mask)
    mask[:,0] = True
    ctx = replace(ctx,mask=mask,values=np.where(mask,ctx.values,np.nan))
    with pytest.raises(ValueError):
        model.predict(ctx,grid)  # Lead 7 has no recorded increment support.


@pytest.mark.parametrize('name,key', [('training_mean','mean'), ('ar1','coefficient'),
                                    ('direct_ridge','coefficient'), ('arima(2,1,0)','params'),
                                    ('ar1-garch(1,1)-t','params')])
def test_restore_requires_fitted_state_fields(name,key):
    r = record(name)
    del r[key]
    with pytest.raises(ValueError):
        restore(r)


def test_tampered_nested_specs_fail_as_invalid_prediction_inputs():
    model = restore(record('persistence'))
    ctx,grid = context_grid()
    object.__setattr__(ctx,'spec',None)
    with pytest.raises(ValueError):
        model.predict(ctx,grid)
    ctx,grid = context_grid()
    object.__setattr__(grid,'spec',None)
    with pytest.raises(ValueError):
        model.predict(ctx,grid)
