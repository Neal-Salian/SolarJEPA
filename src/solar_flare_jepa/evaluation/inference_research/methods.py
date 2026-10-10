"""Restricted conditional methods with explicit failure, no fallback or dropping."""
from collections.abc import Mapping
from dataclasses import fields
from statistics import NormalDist
import math

import numpy as np

from ..comparison import DAY_NS, LossPanel
from ..stress.synthetic import stream_seed
from .contracts import Design, InferenceResult, MethodConfig, integer

MAX_CELLS=1_000_000


def _paired(a, b, design):
    if not isinstance(a,Mapping) or not isinstance(b,Mapping) or not a or set(a)!=set(b):
        raise ValueError('Named paired folds must align')
    if any(type(k) is not str or not k.strip() for k in a):
        raise ValueError('Nonempty fold names required')
    snapshots=[]; calendars=[]; expected=set()
    first=None; total_cells=0
    for name in sorted(a):
        pair=[]
        for model, mapping in (('a',a),('b',b)):
            p=mapping[name]
            if not isinstance(p,LossPanel): raise ValueError('Expected LossPanel')
            p=LossPanel(**{f.name:getattr(p,f.name) for f in fields(LossPanel)})
            if p.seed_ids != design.planned_seed_ids:
                raise ValueError('Actual runs do not match planned ordered seed cohort')
            expected.update((name,model,s) for s in design.planned_seed_ids)
            pair.append(p)
        left,right=pair
        if first is None: first=left
        if (left.metric!=first.metric or left.unit!=first.unit or
            any(getattr(left,k)!=getattr(right,k) for k in ('origin_ids','support_fingerprint','metric','unit','calendar_start_ns','calendar_end_ns')) or
            not np.array_equal(left.issue_times_ns,right.issue_times_ns)):
            raise ValueError('Paired support, times and metric identities must align')
        days=(left.calendar_end_ns-left.calendar_start_ns)//DAY_NS
        total_cells+=len(left.seed_ids)*days
        if total_cells>MAX_CELLS: raise ValueError('Calendar cell budget exceeded')
        calendars.append((left.calendar_start_ns,left.calendar_end_ns))
        snapshots.append((name,left,right,days))
    calendars.sort()
    if any(l[1]>r[0] for l,r in zip(calendars,calendars[1:])):
        raise ValueError('Fixed fold calendars overlap')
    states=[(x.fold,x.model,x.seed) for x in design.run_states]
    if len(states)!=len(set(states)) or set(states)!=expected or any(x.status!='ok' for x in design.run_states):
        raise ValueError('Complete successful planned run ledger required')
    differences=[(name,left.losses-right.losses,left,days) for name,left,right,days in snapshots]
    scale=max(float(np.max(np.abs(d))) for _,d,_,_ in differences)
    scale=scale or 1.
    return [(name,d/scale,p,days) for name,d,p,days in differences],scale


def stationary_indices(*,days:int,replicates:int,mean_block_days:int,rng_seed:int)->np.ndarray:
    """Shared per-step uniforms couple block settings without variable RNG use."""
    for value,minimum,label in ((days,1,'Days'),(replicates,2,'Replicates'),(mean_block_days,1,'Block'),(rng_seed,0,'Seed')):
        integer(value,minimum,label)
    if days*replicates>MAX_CELLS:
        raise ValueError('Bootstrap index cell budget exceeded')
    rng=np.random.default_rng(rng_seed)
    out=np.empty((replicates,days),np.int64)
    out[:,0]=rng.integers(0,days,size=replicates)
    for t in range(1,days):
        restart=rng.random(replicates)<1/mean_block_days
        fresh=rng.integers(0,days,size=replicates)
        out[:,t]=np.where(restart,fresh,(out[:,t-1]+1)%days)
    return out


def infer(a, b, *, design:Design, config:MethodConfig)->InferenceResult:
    if type(design) is not Design or type(config) is not MethodConfig:
        raise ValueError('Typed explicit research design and method required')
    expected='seed_conditional' if config.method=='seed_t' else 'calendar_conditional'
    if design.estimand!=expected:
        raise ValueError('Method cannot silently substitute a different estimand')
    try:
        with np.errstate(over='raise',invalid='raise',divide='raise'):
            return _infer(a,b,design,config)
    except (FloatingPointError,OverflowError) as error:
        raise ValueError('Nonfinite experimental inference arithmetic') from error


def _infer(a,b,design,config):
    inputs,scale=_paired(a,b,design)
    seed_means=np.mean([d.mean(axis=1) for _,d,_,_ in inputs],axis=0)
    center=float(seed_means.mean()); estimate=center*scale
    details=dict(confidence=config.confidence,configuration={f.name:getattr(config,f.name) for f in fields(config)},
                 fold_effects={name:float(d.mean()*scale) for name,d,_,_ in inputs},
                 planned_seeds=list(design.planned_seed_ids),assumptions_are_caller_declarations=True)
    def result(interval=None,se=None,reason=None):
        numbers=[estimate]+([] if interval is None else list(interval))+([] if se is None else [se])
        if not all(math.isfinite(x) for x in numbers): raise ValueError('Nonfinite inference result')
        if interval is not None and (interval[0]>=interval[1] or se is None or se<=0):
            interval=None;se=None;reason='INSUFFICIENT_NUMERICAL_RESOLUTION'
        return InferenceResult(config.method,design.estimand,design.sampling_unit,estimate,interval,se,reason,details)
    def unavailable(reason): return result(reason=reason)
    if not design.finite_mean: return unavailable('unsupported_undefined_mean_estimand')
    if config.method=='seed_t':
        if not design.independent_seeds: return unavailable('unsupported_seed_dependence')
        if design.calendar_dependence!='fixed' or design.seed_score_law=='unknown':
            return unavailable('unsupported_seed_score_law_or_conditioning')
        if len(seed_means)<2 or np.ptp(seed_means)==0:
            return unavailable('INSUFFICIENT_INDEPENDENT_INFORMATION')
        se=float(seed_means.std(ddof=1)/math.sqrt(len(seed_means)))
        if se<=0: return unavailable('INSUFFICIENT_INDEPENDENT_INFORMATION')
        from scipy.stats import t
        critical=float(t.ppf((1+config.confidence)/2,len(seed_means)-1))
        details.update(degrees_of_freedom=len(seed_means)-1,
            guarantee='exact_iid_gaussian' if design.seed_score_law=='gaussian' else 'conservative_independent_normal_scale_mixture')
        return result(((center-critical*se)*scale,(center+critical*se)*scale),se*scale)
    if not design.independent_folds: return unavailable('unsupported_fold_dependence')
    if not design.finite_variance: return unavailable('unsupported_calendar_moments')
    if design.calendar_dependence not in ('stationary_weak','heteroskedastic_weak'):
        return unavailable('unsupported_calendar_dependence')
    if config.method=='stationary_basic' and design.calendar_dependence!='stationary_weak':
        return unavailable('unsupported_stationarity')
    daily=[]
    for name,d,p,days in inputs:
        indices=np.array([(int(x)-p.calendar_start_ns)//DAY_NS for x in p.issue_times_ns],np.int64)
        counts=np.bincount(indices,minlength=days)
        if not (counts>0).all() or not (counts==counts[0]).all():
            return unavailable('unsupported_daily_support')
        minimum=max(8,4*(config.lag_days+1)) if config.method=='hac' else max(8,4*config.mean_block_days)
        if days<minimum: return unavailable('INSUFFICIENT_INDEPENDENT_INFORMATION')
        scores=np.bincount(indices,weights=d.mean(axis=0),minlength=days)/counts
        daily.append((name,scores))
    if all(np.ptp(x)==0 for _,x in daily):
        return unavailable('INSUFFICIENT_INDEPENDENT_INFORMATION')
    if config.method=='hac':
        variances=[]
        for _,x in daily:
            n=len(x); e=x-x.mean()
            if np.ptp(x)==0:
                variances.append(0.)
                continue
            value=float(e@e)
            for k in range(1,config.lag_days+1):
                value+=2*(1-k/(config.lag_days+1))*float(e[k:]@e[:-k])
            if value<0: return unavailable('negative_variance_estimate')
            variances.append(value/(n*(n-1)))  # explicit n/(n-1) correction
        variance=math.fsum(variances)/len(daily)**2
        if variance<=0: return unavailable('INSUFFICIENT_INDEPENDENT_INFORMATION')
        se=math.sqrt(variance); critical=NormalDist().inv_cdf((1+config.confidence)/2)
        details.update(lag_days=config.lag_days,finite_sample_correction='T/(T-1)',
                       guarantee='requires_suitable_bandwidth_sequence_not_guaranteed_by_fixed_lag')
        return result(((center-critical*se)*scale,(center+critical*se)*scale),se*scale)
    draws=np.zeros(config.replicates); fold_seeds={}
    for name,x in daily:
        seed=stream_seed('m3:stationary:'+name,config.rng_seed);fold_seeds[name]=seed
        selected=stationary_indices(days=len(x),replicates=config.replicates,mean_block_days=config.mean_block_days,rng_seed=seed)
        draws+=x[selected].mean(axis=1)/len(daily)
    if float(draws.std())<=0: return unavailable('INSUFFICIENT_INDEPENDENT_INFORMATION')
    low,high=np.quantile(draws,[(1-config.confidence)/2,(1+config.confidence)/2],method='linear')
    details.update(fold_rng_seeds=fold_seeds,interval_type='basic_linear_quantiles',
                   guarantee='requires_suitable_block_length_sequence_not_guaranteed_by_fixed_length')
    return result(((2*center-float(high))*scale,(2*center-float(low))*scale),float(draws.std(ddof=1))*scale)
