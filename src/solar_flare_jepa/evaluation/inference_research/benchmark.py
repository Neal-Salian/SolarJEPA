"""Frozen-design paired benchmarking; conditional and joint targets stay separate."""
from collections import Counter
from dataclasses import fields, replace
import hashlib
import itertools
import json
import math
import time

import numpy as np

from ...forecasting.contracts import canonical_json
from ..comparison import paired_comparison
from ..stress.reference import rate_summary
from ..stress.synthetic import Scenario, stream_seed
from .contracts import Design, MethodConfig, RunState
from .methods import infer
from .reference import hac_matrix_variance, stationary_exact_variance
from .synthetic import generate_case


def validate_config(raw:dict)->dict:
    required={'schema_version','stage','master_seed','replications','bootstrap_replicates','confidence','m1_block_days',
              'max_runtime_seconds','max_resampling_draws','methods','cases','gate'}
    if type(raw) is not dict or set(raw)!=required:
        raise ValueError('Malformed M3 study configuration')
    config=json.loads(canonical_json(raw))
    if type(config['schema_version']) is not int or config['schema_version']!=1 or config['stage'] not in ('development','evaluation'):
        raise ValueError('Unknown M3 schema/stage')
    for name,low,high in (('master_seed',0,2**63-1),('replications',2,1000),('bootstrap_replicates',99,1999),
                         ('m1_block_days',1,90),('max_runtime_seconds',1,900),('max_resampling_draws',1,8_000_000)):
        if type(config[name]) is not int or not low<=config[name]<=high: raise ValueError('Invalid bounded '+name)
    if type(config['confidence']) not in (float,int) or not .95<=config['confidence']<1:
        raise ValueError('Explicit confidence >= .95 and < 1 required')
    gate=config['gate']
    if type(gate) is not dict or set(gate)!={'coverage_wilson_lower_min','coverage_wilson_upper_max','null_type1_wilson_upper_max','availability_min'}:
        raise ValueError('Explicit gate thresholds required')
    if any(type(v) not in (float,int) or not 0<v<=1 for v in gate.values()) or gate['coverage_wilson_lower_min']>=gate['coverage_wilson_upper_max']:
        raise ValueError('Invalid gate threshold')
    methods=config['methods']
    if type(methods) is not list or not 1<=len(methods)<=8: raise ValueError('Bounded explicit methods required')
    labels=[]
    for m in methods:
        if type(m) is not dict or set(m)!={'label','method','estimand','sampling_unit','lag_days','mean_block_days'} or type(m['label']) is not str or not m['label'] or m['label']=='m1_joint':
            raise ValueError('Malformed method definition')
        mc=_method_config(m,config,0)
        expected='seed_conditional' if mc.method=='seed_t' else 'calendar_conditional'
        unit='paired_training_run' if expected=='seed_conditional' else 'calendar_day'
        if m['estimand']!=expected or m['sampling_unit']!=unit: raise ValueError('Method estimand/unit mismatch')
        labels.append(m['label'])
    if len(labels)!=len(set(labels)): raise ValueError('Duplicate method labels')
    if type(config['cases']) is not list or not 1<=len(config['cases'])<=24: raise ValueError('Bounded explicit cases required')
    names=[]
    for row in config['cases']:
        if type(row) is not dict or set(row)!={'scenario','law','overlap_days','assumptions'} or type(row['scenario']) is not dict:
            raise ValueError('Malformed synthetic case')
        if set(row['scenario'])!={f.name for f in fields(Scenario)}: raise ValueError('All scenario parameters must be explicit')
        cfg=Scenario(**row['scenario']);names.append(cfg.name)
        if config['m1_block_days']>min(cfg.days): raise ValueError('M1 block exceeds fixed calendar')
        if row['law']=='m2':
            if row['overlap_days'] is not None: raise ValueError('M2 law takes no overlap override')
        elif row['law']=='overlap_ma':
            if type(row['overlap_days']) is not int or not 2<=row['overlap_days']<=min(cfg.days) or cfg.distribution!='normal' or cfg.rho!=0 or cfg.heteroskedastic:
                raise ValueError('Unsupported overlap design')
        else: raise ValueError('Unknown DGP')
        expected=dict(independent_seeds=cfg.seed_correlation==0,seed_score_law='gaussian' if cfg.distribution=='normal' else 'normal_scale_mixture',
                      calendar_dependence='heteroskedastic_weak' if cfg.heteroskedastic else 'stationary_weak',
                      finite_variance=cfg.distribution!='t1.5',independent_folds=True)
        if row['assumptions']!=expected: raise ValueError('Synthetic law and assumption declarations conflict')
    if len(names)!=len(set(names)): raise ValueError('Duplicate synthetic case name')
    draws=len(config['cases'])*config['replications']*config['bootstrap_replicates']*(1+sum(m['method']=='stationary_basic' for m in methods))
    if draws>config['max_resampling_draws']: raise ValueError('Total resampling budget exceeded')
    return config


def _method_config(method,config,seed):
    return MethodConfig(method['method'],config['confidence'],seed,method['lag_days'],method['mean_block_days'],
                        config['bootstrap_replicates'] if method['method']=='stationary_basic' else 0)


def _design(case,method,a):
    assumptions=case['assumptions']
    seeds=next(iter(a.values())).seed_ids
    return Design(estimand=method['estimand'],sampling_unit=method['sampling_unit'],**(assumptions|{
        'calendar_dependence':'fixed' if method['estimand']=='seed_conditional' else assumptions['calendar_dependence']}),
        finite_mean=True,planned_seed_ids=seeds,missing_runs='reject',  # all declared M2/M3 laws have a mean
        run_states=tuple(RunState(f,m,s,'ok') for f in sorted(a) for m in ('a','b') for s in seeds))


def null_status(case,estimand):
    cfg=Scenario(**case['scenario'])
    if estimand=='seed_conditional' and cfg.sigma_time!=0: return 'varying'
    if estimand=='calendar_conditional' and cfg.sigma_seed!=0: return 'varying'
    if estimand not in ('seed_conditional','calendar_conditional','joint'): raise ValueError('Unknown estimand')
    delta=float(np.mean(cfg.effects))
    return 'null' if abs(delta)<=1e-12 else 'positive_alternative' if delta>0 else 'negative_alternative'


def gate_eligible(case,method):
    cfg=Scenario(**case['scenario'])
    if method['method']=='seed_t':
        return cfg.distribution=='normal' and cfg.seed_correlation==0 and (cfg.sigma_seed>0 or cfg.sigma_cell>0)
    if cfg.distribution=='t1.5' or len(set(cfg.counts))!=1 or cfg.counts[0]==0 or (cfg.sigma_time==0 and cfg.sigma_cell==0): return False
    if method['method']=='stationary_basic':
        return not cfg.heteroskedastic and min(cfg.days)>=max(8,4*method['mean_block_days'])
    return min(cfg.days)>=max(8,4*(method['lag_days']+1))


def _input_hash(a,b):
    digest=hashlib.sha256()
    for name in sorted(a):
        digest.update(name.encode())
        for panel in (a[name],b[name]):
            digest.update(canonical_json([panel.seed_ids,panel.origin_ids,panel.support_fingerprint,panel.metric,panel.unit,
                                          panel.calendar_start_ns,panel.calendar_end_ns]).encode())
            digest.update(panel.issue_times_ns.astype('<i8').tobytes())
            digest.update(panel.losses.astype('<f8').tobytes())
    return digest.digest()


def _summarize(item,replications,finite_variance):
    count=item['count'];available=count['available'];covered=count['covered'];status=item['null_status']
    errors=np.array(item['errors']); widths=item['widths']
    zero_exclusion=count['negative_exclusion']+count['positive_exclusion']
    out=dict(estimand=item['estimand'],null_status=status,gate_eligible=item['gate_eligible'],
        coverage=rate_summary(covered,replications),available_coverage=rate_summary(covered,available),
        availability=rate_summary(available,replications),failure_rate=rate_summary(replications-available,replications),
        true_parameter_exclusion_available=rate_summary(available-covered,available),
        zero_exclusion=rate_summary(zero_exclusion,replications),
        zero_null_type1=rate_summary(zero_exclusion,replications) if status=='null' and available else None,
        directional_power=rate_summary(count['positive_exclusion'] if status=='positive_alternative' else count['negative_exclusion'],replications)
            if status in ('positive_alternative','negative_alternative') and available else None,
        opposite_direction_exclusion=rate_summary(count['negative_exclusion'] if status=='positive_alternative' else count['positive_exclusion'],replications)
            if status in ('positive_alternative','negative_alternative') and available else None,
        failure_reasons=dict(sorted(item['reasons'].items())),
        estimate_mean=float(np.mean(item['estimates'])),truth_mean=float(np.mean(item['truths'])),bias=float(errors.mean()),
        bias_mcse=float(errors.std(ddof=1)/math.sqrt(replications)) if finite_variance else None,
        empirical_rmse=float(np.sqrt(np.mean(errors**2))),finite_estimator_variance=finite_variance,
        mean_ci_width=float(np.mean(widths)) if widths else None,
        width_mcse=float(np.std(widths,ddof=1)/math.sqrt(len(widths))) if len(widths)>1 and finite_variance else None)
    return out


def _gate(row,thresholds):
    if not row['gate_eligible']:return 'NOT_ELIGIBLE'
    bounds=row['coverage']['wilson95']
    passed=(row['availability']['rate']>=thresholds['availability_min'] and bounds[0]>=thresholds['coverage_wilson_lower_min']
            and bounds[1]<=thresholds['coverage_wilson_upper_max'])
    if row['zero_null_type1'] is not None:
        passed &= row['zero_null_type1']['wilson95'][1]<=thresholds['null_type1_wilson_upper_max']
    return 'PASS' if passed else 'FAILED_SCREEN'


def reference_checks():
    x=np.array([-1.,0.,2.]);means=[];weights=[];p=.5
    for path in itertools.product(range(3),repeat=3):
        probability=1/3
        for previous,current in zip(path,path[1:]):probability*=p/3+(1-p)*(current==(previous+1)%3)
        means.append(float(x[list(path)].mean()));weights.append(probability)
    exact=math.fsum(w*(m-x.mean())**2 for w,m in zip(weights,means))
    error=abs(exact-stationary_exact_variance(x,2))
    if error>1e-12: raise AssertionError('Independent stationary reference mismatch')
    return dict(stationary_markov_paths=27,maximum_absolute_error=error,
                hac_toeplitz_fixture_variance=hac_matrix_variance([-2,1,0,4,-1,3,2,-3],1),
                interpretation='Independent exact arithmetic references; not a coverage theorem')


def adversarial_checks(config):
    """Deterministic run-failure probes, separate from Monte Carlo coverage."""
    case=config['cases'][0]
    a,b,_=generate_case(case,stream_seed('m3:run-ledger-probes',config['master_seed']))
    reduced=lambda mapping:{k:replace(p,seed_ids=p.seed_ids[:-1],losses=p.losses[:-1]) for k,p in mapping.items()}
    checks=[]
    for method in config['methods']:
        original=_design(case,method,a)
        for violation in ('one_model_missing','both_models_missing','failed_fitting_record'):
            left,right,design=a,b,original
            if violation=='one_model_missing':left=reduced(a)
            elif violation=='both_models_missing':left,right=reduced(a),reduced(b)
            else:
                states=list(original.run_states);states[0]=replace(states[0],status='failed')
                design=replace(original,run_states=tuple(states))
            try:
                infer(left,right,design=design,config=_method_config(method,config,0))
            except ValueError as error:
                checks.append(dict(method=method['label'],violation=violation,rejected=True,reason=str(error)))
            else:
                raise AssertionError('Missing/failed planned runs were not rejected')
    return checks


def run_benchmark(raw:dict,*,progress=None):
    config=validate_config(raw);started=time.monotonic();case_results=[];timings=Counter()
    for index,case in enumerate(config['cases']):
        cfg=Scenario(**case['scenario']);items={};data_digest=hashlib.sha256()
        specifications=config['methods']+[dict(label='m1_joint',method='m1',estimand='joint')]
        for m in specifications:
            items[m['label']]=dict(estimand=m['estimand'],null_status=null_status(case,m['estimand']),
                gate_eligible=False if m['method']=='m1' else gate_eligible(case,m),count=Counter(),reasons=Counter(),
                errors=[],estimates=[],truths=[],widths=[],covered_vector=[])
        for replication in range(config['replications']):
            if time.monotonic()-started>config['max_runtime_seconds']: raise TimeoutError('M3 incomplete study exceeds runtime budget')
            label=f"m3:{config['stage']}:{cfg.name}:{replication}"
            a,b,truth=generate_case(case,stream_seed(label+':dataset',config['master_seed']))
            data_digest.update(_input_hash(a,b));rng_seed=stream_seed(label+':bootstrap',config['master_seed'])
            for m in specifications:
                item=items[m['label']];begin=time.perf_counter()
                if m['method']=='m1':
                    output=paired_comparison(a,b,block_days=config['m1_block_days'],replicates=config['bootstrap_replicates'],rng_seed=rng_seed,confidence=config['confidence'])
                    estimate=output['mean_difference'];interval=output['difference_interval'];reason=output['interval_reason']
                else:
                    result=infer(a,b,design=_design(case,m,a),config=_method_config(m,config,rng_seed))
                    estimate=result.estimate;interval=result.interval;reason=result.reason
                timings[m['label']]+=time.perf_counter()-begin
                target=truth[m['estimand']];item['errors'].append(estimate-target);item['estimates'].append(estimate);item['truths'].append(target)
                covered=False
                if interval is None:item['reasons'][reason or 'unavailable']+=1
                else:
                    lo,hi=interval;tol=1e-12*max(1.,abs(target));covered=lo-tol<=target<=hi+tol
                    item['count']['available']+=1;item['count']['covered']+=int(covered)
                    item['count']['negative_exclusion']+=int(hi < -1e-12)
                    item['count']['positive_exclusion']+=int(lo > 1e-12)
                    item['widths'].append(hi-lo)
                item['covered_vector'].append(int(covered))
        rows={label:_summarize(item,config['replications'],cfg.distribution!='t1.5') for label,item in items.items()}
        for row in rows.values():row['screen']=_gate(row,config['gate'])
        paired=[]
        for left,right in itertools.combinations(items,2):
            if items[left]['estimand']!=items[right]['estimand']:continue
            difference=np.array(items[left]['covered_vector'])-np.array(items[right]['covered_vector'])
            paired.append(dict(left=left,right=right,estimand=items[left]['estimand'],
                coverage_rate_difference=float(difference.mean()),paired_mcse=float(difference.std(ddof=1)/math.sqrt(len(difference))),
                discordant=int(np.count_nonzero(difference)),replications=len(difference)))
        case_results.append(dict(case=case,replications=config['replications'],bootstrap_replicates=config['bootstrap_replicates'],
            common_dataset_digest=data_digest.hexdigest(),methods=rows,paired_coverage_comparisons=paired))
        if progress is not None:progress(index+1,len(config['cases']),cfg.name)
    if time.monotonic()-started>config['max_runtime_seconds']:raise TimeoutError('M3 incomplete study exceeds runtime budget')
    selection={m['label']:dict(eligible=sum(c['methods'][m['label']]['gate_eligible'] for c in case_results),
                              failed_cases=[c['case']['scenario']['name'] for c in case_results if c['methods'][m['label']]['screen']=='FAILED_SCREEN']) for m in config['methods']}
    for value in selection.values():value['passes_bounded_screen']=value['eligible']>0 and not value['failed_cases']
    scientific=dict(schema_version=1,synthetic_only=True,stage=config['stage'],config=config,cases=case_results,
        selection=selection,references=reference_checks(),run_failure_checks=adversarial_checks(config),
        primary_joint_replacement='NO_VALIDATED_REPLACEMENT',
        interpretation='Different conditional estimands; screens are bounded synthetic evidence, not solar confirmation')
    return scientific,dict(method_seconds=dict(timings),runtime_seconds=time.monotonic()-started)
