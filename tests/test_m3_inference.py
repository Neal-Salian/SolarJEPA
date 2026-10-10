"""Independent literal and adversarial checks of experimental inference."""
from dataclasses import replace
import itertools
import math

import numpy as np
import pytest

from solar_flare_jepa.evaluation.comparison import DAY_NS, LossPanel
from solar_flare_jepa.evaluation.inference_research.contracts import Design, MethodConfig, RunState
from solar_flare_jepa.evaluation.inference_research.methods import infer, stationary_indices
from solar_flare_jepa.evaluation.inference_research.reference import hac_matrix_variance, stationary_exact_variance


def panels(difference, counts=None):
    d = np.asarray(difference, float)
    days = d.shape[1]
    counts = np.ones(days, int) if counts is None else np.array(counts)
    origins = np.repeat(np.arange(days), counts)
    d = d[:, origins]
    base = 10+np.abs(d)
    times = np.array([t*DAY_NS+(j+1)*100 for t,c in enumerate(counts) for j in range(c)], np.int64)
    fields = dict(seed_ids=tuple(range(len(d))), origin_ids=tuple(map(str, range(len(origins)))),
                  issue_times_ns=times, support_fingerprint='fixture',metric='artificial',unit='loss',
                  calendar_start_ns=0,calendar_end_ns=days*DAY_NS)
    return {'f':LossPanel(losses=base+d,**fields)}, {'f':LossPanel(losses=base,**fields)}


def design(a, mode='seed_conditional', **changes):
    seeds = next(iter(a.values())).seed_ids
    args = dict(estimand=mode, sampling_unit='paired_training_run' if mode=='seed_conditional' else 'calendar_day',
                independent_seeds=True,seed_score_law='gaussian',calendar_dependence='fixed' if mode=='seed_conditional' else 'stationary_weak',
                finite_mean=True,finite_variance=True,independent_folds=True,planned_seed_ids=seeds,missing_runs='reject',
                run_states=tuple(RunState(f,m,s,'ok') for f in sorted(a) for m in ('a','b') for s in seeds))
    args.update(changes)
    return Design(**args)


def settings(method='seed_t', **changes):
    args = dict(method=method,confidence=.95,rng_seed=7,lag_days=None,mean_block_days=None,
                replicates=0 if method!='stationary_basic' else 399)
    if method=='hac': args['lag_days']=1
    if method=='stationary_basic': args['mean_block_days']=3
    args.update(changes)
    return MethodConfig(**args)


def test_literal_seed_t_df_two_and_pairing():
    a,b=panels([[1]*8,[2]*8,[3]*8])
    result=infer(a,b,design=design(a),config=settings())
    # df=2: F(t)=1/2+t/(2*sqrt(t*t+2)); exact inverse at .975.
    half=4.302652729749464/math.sqrt(3)
    assert result.estimate == 2
    assert result.standard_error == pytest.approx(1/math.sqrt(3))
    assert result.interval == pytest.approx((2-half,2+half),abs=1e-12)
    assert result.details['degrees_of_freedom']==2


def test_hac_matches_independent_toeplitz_quadratic_form():
    x=np.array([-2,1,0,4,-1,3,2,-3.])
    a,b=panels([x,x])
    result=infer(a,b,design=design(a,'calendar_conditional'),config=settings('hac'))
    e=x-x.mean()
    kernel=np.eye(8)+.5*np.eye(8,k=1)+.5*np.eye(8,k=-1)
    expected=float(e@kernel@e)/(8*7)
    assert result.standard_error**2 == pytest.approx(expected,abs=1e-12)
    assert hac_matrix_variance(x,1) == pytest.approx(expected,abs=1e-12)
    assert result.interval == pytest.approx((.5-1.959963984540054*math.sqrt(expected),.5+1.959963984540054*math.sqrt(expected)))


def test_exact_stationary_variance_from_all_markov_paths():
    x=np.array([-1.,0.,2.]); p=.5
    means=[]; weights=[]
    for path in itertools.product(range(3),repeat=3):
        probability=1/3
        for previous,current in zip(path,path[1:]):
            probability*=p/3+(1-p)*(current==(previous+1)%3)
        means.append(float(x[list(path)].mean()));weights.append(probability)
    assert math.fsum(weights)==pytest.approx(1.)
    variance=math.fsum(w*(m-x.mean())**2 for w,m in zip(weights,means))
    assert stationary_exact_variance(x,2)==pytest.approx(variance,abs=1e-14)


def test_stationary_sampling_matches_exact_variance_and_is_deterministic():
    indices=stationary_indices(days=3,replicates=100000,mean_block_days=2,rng_seed=81)
    assert np.array_equal(indices,stationary_indices(days=3,replicates=100000,mean_block_days=2,rng_seed=81))
    x=np.array([-1.,0.,2.])
    assert np.var(x[indices].mean(axis=1))==pytest.approx(stationary_exact_variance(x,2),rel=.015)


def test_basic_interval_uses_reflection_not_percentile():
    x=np.arange(24.)**2
    a,b=panels([x,x])
    result=infer(a,b,design=design(a,'calendar_conditional'),config=settings('stationary_basic'))
    indices=stationary_indices(days=24,replicates=399,mean_block_days=3,
                               rng_seed=result.details['fold_rng_seeds']['f'])
    lo,hi=np.quantile(x[indices].mean(axis=1),[.025,.975],method='linear')
    assert result.interval==pytest.approx((2*x.mean()-hi,2*x.mean()-lo))
    assert result==infer(a,b,design=design(a,'calendar_conditional'),config=settings('stationary_basic'))


@pytest.mark.parametrize('method',['seed_t','hac','stationary_basic'])
def test_no_point_interval_from_constant_sample(method):
    a,b=panels(np.ones((3,24)))
    mode='seed_conditional' if method=='seed_t' else 'calendar_conditional'
    result=infer(a,b,design=design(a,mode),config=settings(method))
    assert result.interval is None
    assert result.reason=='INSUFFICIENT_INDEPENDENT_INFORMATION'


def test_common_missing_run_is_detected_using_planned_ledger():
    a,b=panels(np.arange(24.).reshape(3,8))
    planned=design(a)
    reduced=lambda mapping:{k:replace(p,seed_ids=p.seed_ids[:-1],losses=p.losses[:-1]) for k,p in mapping.items()}
    with pytest.raises(ValueError,match='planned'):
        infer(reduced(a),reduced(b),design=planned,config=settings())


@pytest.mark.parametrize('status',['failed','missing'])
def test_declared_failed_or_missing_fit_rejects(status):
    a,b=panels(np.arange(24.).reshape(3,8)); declared=design(a)
    states=list(declared.run_states);states[0]=replace(states[0],status=status)
    with pytest.raises(ValueError,match='run'):
        infer(a,b,design=replace(declared,run_states=tuple(states)),config=settings())


@pytest.mark.parametrize('field,value',[('support_fingerprint','other'),('unit','other'),('metric','other')])
def test_mismatched_pair_contract_rejects(field,value):
    a,b=panels(np.arange(24.).reshape(3,8))
    b={'f':replace(b['f'],**{field:value})}
    with pytest.raises(ValueError,match='align'):
        infer(a,b,design=design(a),config=settings())


def test_unequal_daily_counts_supported_only_for_seed_target():
    a,b=panels(np.arange(72.).reshape(3,24),counts=[1,3,0]*8)
    assert infer(a,b,design=design(a),config=settings()).interval is not None
    result=infer(a,b,design=design(a,'calendar_conditional'),config=settings('hac'))
    assert result.reason=='unsupported_daily_support' and result.interval is None


def test_correlated_seed_declaration_cannot_silently_fallback():
    a,b=panels(np.arange(24.).reshape(3,8))
    result=infer(a,b,design=design(a,independent_seeds=False),config=settings())
    assert result.reason=='unsupported_seed_dependence'


@pytest.mark.parametrize('method',['hac','stationary_basic'])
def test_infinite_variance_calendar_inference_is_unavailable(method):
    a,b=panels(np.arange(72.).reshape(3,24))
    result=infer(a,b,design=design(a,'calendar_conditional',finite_variance=False),config=settings(method))
    assert result.reason=='unsupported_calendar_moments'


def test_scale_mixture_seed_law_does_not_require_finite_variance():
    a,b=panels(np.arange(24.).reshape(3,8))
    result=infer(a,b,design=design(a,seed_score_law='normal_scale_mixture',finite_variance=False),config=settings())
    assert result.interval is not None
    assert result.details['guarantee']=='conservative_independent_normal_scale_mixture'


def test_scale_mixture_without_finite_mean_cannot_target_expected_loss():
    a,b=panels(np.arange(24.).reshape(3,8))
    result=infer(a,b,design=design(a,seed_score_law='normal_scale_mixture',finite_mean=False,finite_variance=False),config=settings())
    assert result.interval is None and result.reason=='unsupported_undefined_mean_estimand'


@pytest.mark.parametrize('method',['hac','stationary_basic'])
def test_insufficient_temporal_length_is_explicit(method):
    a,b=panels(np.arange(24.).reshape(3,8))
    config=settings(method,**({'lag_days':3} if method=='hac' else {'mean_block_days':3}))
    result=infer(a,b,design=design(a,'calendar_conditional'),config=config)
    assert result.reason=='INSUFFICIENT_INDEPENDENT_INFORMATION'


def test_stationary_rejects_declared_nonstationary_variance():
    a,b=panels(np.arange(72.).reshape(3,24))
    result=infer(a,b,design=design(a,'calendar_conditional',calendar_dependence='heteroskedastic_weak'),config=settings('stationary_basic'))
    assert result.reason=='unsupported_stationarity'


def test_large_offset_retains_representable_effect():
    a,b=panels([[0]*8,[0]*8,[0]*8])
    b={'f':replace(b['f'],losses=np.full((3,8),1e16))}
    a={'f':replace(a['f'],losses=b['f'].losses+np.array([0,2,4])[:,None])}
    assert infer(a,b,design=design(a),config=settings()).estimate==2


@pytest.mark.parametrize('changes',[{'confidence':float('nan')},{'confidence':True},{'rng_seed':-1},
    {'method':'unknown'},{'replicates':99},{'lag_days':1}])
def test_invalid_method_configuration_rejects(changes):
    with pytest.raises(ValueError): settings(**changes)


def test_resource_guard_precedes_dense_calendar_allocation():
    with pytest.raises(ValueError,match='budget'):
        stationary_indices(days=1000,replicates=1001,mean_block_days=3,rng_seed=2)


def test_identical_nonbinary_seed_means_do_not_gain_roundoff_variance():
    a,b=panels(np.tile([0.,0.,1.]*8,(10,1)))
    result=infer(a,b,design=design(a),config=settings())
    assert result.interval is None
    assert result.reason=='INSUFFICIENT_INDEPENDENT_INFORMATION'


@pytest.mark.parametrize('magnitude',[1e-323,1e16])
def test_interval_cannot_collapse_when_scaling_to_float_precision(magnitude):
    a,b=panels(np.zeros((100,24)))
    values=np.zeros((100,24))+magnitude
    values[0,:]=0. if magnitude<1 else magnitude+2.
    a={'f':replace(a['f'],losses=values)}
    b={'f':replace(b['f'],losses=np.zeros_like(values))}
    result=infer(a,b,design=design(a),config=settings())
    assert result.interval is None
    assert result.reason=='INSUFFICIENT_NUMERICAL_RESOLUTION'
