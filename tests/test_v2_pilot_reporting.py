"""Synthetic canonical records test publication without model fitting or files."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord
from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid, fingerprint_payload,
)
from solar_flare_jepa.experiments.v2_interfaces import evaluation_identity_fields

ROOT = Path(__file__).resolve().parents[1]
DIGEST = 'ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624'


def api():
    try:
        return importlib.import_module('solar_flare_jepa.experiments.v2_pilot_reporting')
    except ModuleNotFoundError as error:
        if error.name == 'solar_flare_jepa.experiments.v2_pilot_reporting':
            pytest.fail('Production pilot report boundary is missing')
        raise


def _synthetic_model_metadata(record,job):
    """Handcrafted full trainer-output schemas; no model is built or executed."""
    controlled = job['kind']=='neural_downstream'
    linear = job['kind']=='quantile_linear'
    modules = ('encoder','target_encoder','predictor','head') if controlled else ('tcn','head')
    record.update(train_windows=dict(eligible=2,used=2,stride=1,cap=20000,
        policy='complete_consecutive_raw_training_rows',subsample='none',fingerprint='synthetic-window'),
        validation=dict(origin_count=2,origin_fingerprint='synthetic-origin',split_fingerprint='synthetic-split',
            spec_fingerprint=record['spec_fingerprint'],dataset_fingerprint='synthetic-data',content_fingerprint='synthetic-content'),
        environment=dict(torch_version='2.6.0',torch_threads=4,deterministic_algorithms=True,
            python='3.13.3',platform='synthetic',process_peak_rss_bytes=100,rss_scope='synthetic'),
        parameters=dict(trainable_total=100),
        wall_seconds=dict(preparation=1.,this_call_training=2.,scope='synthetic no-fit metadata'))
    if linear:
        record['rng_streams'] = dict(shuffle='synthetic',initialization='zeros')
        record['selection'].update(tie_policy='smallest_lambda',epoch_selection='none_final_epoch_kept',quantile_order='sorted')
        record['budget'] = dict(phases=[dict(phase='lambda_grid',fits=7,epochs_per_fit=100,
            optimizer_steps=700,optimizer='Adam',lr=.01)],totals=dict(optimizer_steps=700,selected_fit_steps=100))
        return
    record['rng_streams'] = dict(initialization='synthetic',downstream_order='synthetic')
    record['pairing'] = dict(initial_state=f"synthetic-initial-{job['seed']}",downstream_order='synthetic-downstream')
    phase_names = (['pretrain'] if job['dependencies'] else
        ['supervised_warmup'] if job['arm']=='supervised_extra_updates' else []) + ['downstream']
    phases,history = [],[]
    for phase in phase_names:
        epochs = 15 if phase=='downstream' else 8
        if phase=='pretrain': active = {'encoder','predictor'}
        elif phase=='downstream' and job['arm'] in ('jepa_frozen','random_frozen'): active = {'head'}
        else: active = set(modules)-{'target_encoder'}
        updates = {name:dict(min=epochs if name in active else 0,max=epochs if name in active else 0,
            tensors=1,source='synthetic') for name in modules}
        budget = dict(phase=phase,epochs_planned=epochs,epochs_executed=epochs,optimizer_steps=epochs,
            examples_seen=epochs*2,optimizer='AdamW',optimizer_reset=True,lr=.001,
            weight_decay=.0001,parameter_updates=updates,wall_seconds=float(epochs))
        if phase=='pretrain': budget['ema_target_updates'] = epochs
        phases.append(budget)
        for epoch in range(1,epochs+1):
            row = dict(phase=phase,epoch=epoch,steps=epoch,wall_seconds=1.)
            if controlled:
                row.update(context_latent_std=1.,context_effective_rank=1.)
                if job['dependencies']: row.update(target_latent_std=1.,target_effective_rank=1.)
            if phase=='pretrain': row.update(train_jepa_loss=.1,ema_momentum=1.)
            else:
                metric=job['model_config']['schedule']['selection_metric']
                row.update(train_loss=.1,train_loss_version=metric)
                if phase=='downstream': row['metrics']={name:.1 for name in
                    [metric]+job['model_config']['schedule']['diagnostic_metrics']}
            history.append(row)
    totals = dict(optimizer_steps=sum(p['optimizer_steps'] for p in phases),
        examples_seen=sum(p['examples_seen'] for p in phases),
        parameter_updates={name:sum(p['parameter_updates'][name]['max'] for p in phases) for name in modules})
    record.update(history=history,budget=dict(phases=phases,totals=totals))
    stage_names = ['initial'] + (['after_pretrain'] if job['dependencies'] else
        ['after_warmup'] if job['arm']=='supervised_extra_updates' else []) + ['selected']
    record['fingerprints'] = {stage:{name:f'synthetic-{stage}-{name}-{job["seed"]}'
        for name in (modules if controlled else ('blocks','head'))} for stage in stage_names}
    if controlled:
        record['rng_streams'].update(pretrain_order='synthetic',pretrain_context_mask='synthetic',warmup_order='synthetic')
        record['pairing'].update(pretrain_order='synthetic-shared-order' if job['dependencies'] else None,
            warmup_order='synthetic-shared-order' if job['arm']=='supervised_extra_updates' else None)
        record['pretraining'] = (dict(reused=True,artifact_fingerprint=f"synthetic-ssl-{job['seed']}",wall_seconds=8.)
            if job['dependencies'] else None)
        totals['ema_target_updates'] = 8 if job['dependencies'] else 0
        record['parameters'].update(encoder=20,target_encoder_ema=20,predictor=20,head=60)
        record['wall_seconds']['attributed_training'] = 10. if job['dependencies'] else 2.
    else:
        record['parameters'].update(receptive_field_bins=253,context_steps=120)


def fixture():
    design = json.loads((ROOT / 'docs/protocols/phase2_v2_development_v1.json').read_text())['design']
    spec = ForecastSpec(**design['data']['forecast'])
    begin = int(np.datetime64('2024-07-22T02:00:00', 'ns').astype(np.int64))
    issues = np.array([begin, begin + 1800 * 10**9], dtype=np.int64)
    starts = issues[:, None] + np.arange(30, dtype=np.int64)[None] * 60 * 10**9
    grid = FutureGrid(starts, starts + 60 * 10**9, issues, ('synthetic-1', 'synthetic-2'), spec, 'synthetic-data')
    targets = ForecastTargets(np.ones((2, 30, 2)), np.ones((2, 30, 2), bool), grid)
    payloads = {}
    for job in design['jobs']:
        if job['development_run'] is None:
            continue
        config = deepcopy(job['model_config'])
        seedfree = deepcopy(config)
        for part in seedfree.values():
            if isinstance(part, dict):
                part.pop('seed', None)
        kind = {'neural_downstream': 'controlled_quantile_jepa', 'tcn': 'tcn_quantile',
                'quantile_linear': 'quantile_linear'}[job['kind']]
        if job['kind'] == 'neural_downstream':
            from solar_flare_jepa.training.controlled import MODEL_KIND
            kind = MODEL_KIND
        model_id = {'tcn': 'v2_tcn_quantile', 'quantile_linear': 'v2_quantile_linear'}.get(job['arm'], 'v2_' + job['arm'])
        record = dict(schema_version=1, model_id=model_id, model_kind=kind,
            scientific_status='EXPERIMENTAL_UNVALIDATED', config=config,
            run_fingerprint=fingerprint_payload(config), recipe_fingerprint=fingerprint_payload(seedfree),
            seed=job['seed'], spec_fingerprint=spec.fingerprint,
            normalization_fingerprint='synthetic-normalization', training_fingerprint='synthetic-training',
            training_dataset_fingerprint='synthetic-data', train_windows={'fingerprint': 'synthetic-window'},
            validation={'fingerprint': 'synthetic-validation'},
            selection={'partition': 'validation', 'metric': 'dex_pinball_equal_channel_v2', 'value': 0.1},
            budget={'phases': [], 'totals': {'optimizer_steps': 15}},
            environment={'torch_threads': 4}, wall_seconds={'preparation': 1., 'this_call_training': 2.})
        if job['kind'] == 'neural_downstream':
            record['arm'] = job['arm']
        if job['kind'] == 'quantile_linear':
            record['lambda_candidates'] = [{'lambda': value, 'validation_metric': 0.1,
                'validation_raw_crossing_fraction': 0., 'optimizer_steps': 100,
                'final_epoch_train_objective': 0.1, 'mean_squared_coefficient': 0.,
                'shuffle_order': 'synthetic-order', 'weights_fingerprint': 'synthetic-weights',
                'wall_seconds': 1.} for value in config['linear']['lambdas']]
            record['selection']['lambda'] = 0.
        else:
            metric = config['schedule']['selection_metric']
            record['selection'].update(metric=metric, epoch=1, eligible_phase='downstream',
                tie_policy='earliest_epoch', early_stopping_patience=None, stopped_early=False,
                epochs_executed=15, epochs_planned=15)
            record['history'] = [dict(phase='downstream', epoch=epoch, train_loss=0.1,
                train_loss_version=metric, metrics={metric: 0.1}, steps=epoch, wall_seconds=1.)
                for epoch in range(1,16)]
        _synthetic_model_metadata(record,job)
        quantiles = np.broadcast_to(np.array([.1, .5, 1., 4., 10.]), (2, 30, 2, 5)).copy()
        quantiles[1,:,:,2] = 3.
        point = quantiles[:,:,:,2]
        pred = ForecastPrediction(point, grid, model_id, tuple(spec_value for spec_value in design['training']['quantiles']), quantiles)
        identity = EvaluationIdentity(**evaluation_identity_fields(record, experiment_id='synthetic',
            code_fingerprint='synthetic-code', data_provenance_fingerprint='synthetic-provenance',
            split_fingerprint='synthetic-split', protocol_fingerprint=DIGEST))
        payloads[job['job_id']] = dict(model_record=record,
            evaluation_record=EvaluationRecord(identity, targets, pred).as_dict())
    supervisor_plan = dict(schema_version=1,code_fingerprint='synthetic-code',config_fingerprint='synthetic-config',
        resources=dict(max_rss_bytes=2147483648,total_wall_seconds=7200,threads=4,max_retries=0,poll_interval_seconds=.05),
        jobs=[dict(job_id=j['job_id'],command=['synthetic-command'],timeout_seconds=j['timeout_seconds']) for j in design['jobs']])
    supervisor = dict(schema_version=1, plan=supervisor_plan, plan_fingerprint=fingerprint_payload(supervisor_plan),
        execution_order=[j['job_id'] for j in design['jobs']], consumed_wall_seconds=20.,
        stop_reason=None, jobs={j['job_id']: dict(status='succeeded',artifact_path='synthetic',artifacts=dict(files=[],manifest_sha256='a'*64))
            for j in design['jobs']}, attempts=[dict(job_id=j['job_id'], number=1, status='succeeded',
                job_fingerprint=fingerprint_payload(dict(job_id=j['job_id'],command=['synthetic-command'],timeout_seconds=j['timeout_seconds'])), path='synthetic', pid=1, started_utc='synthetic', checkpoint_utc='synthetic',
                wall_seconds=1., peak_sampled_rss_bytes=100, returncode=0, failure_kind=None,
                error=None, finished_utc='synthetic') for j in design['jobs']])
    runtime = dict(git_commit='synthetic', git_branch='synthetic', source_fingerprint='synthetic',
        source_files=[], environment=dict(python='synthetic',executable='synthetic',packages={},
            lock_files={name:'a'*64 for name in ('requirements-lock.txt','requirements-training-lock.txt','requirements-v1-lock.txt','pyproject.toml')}),
        host=dict(hostname='synthetic',platform='synthetic',machine='synthetic',processor='synthetic',
            logical_cpus=4,physical_memory_bytes=8589934592),host_fingerprint='synthetic',fingerprint='synthetic')
    accounting = dict(schema_version=1,status='COMPLETE',supervisor=supervisor,runtime=runtime,
        design_fingerprint=DIGEST,binding_fingerprint='synthetic-binding',
        wall_seconds=dict(preparation=1.,supervision=20.,finalization=1.,total=22.),
        development_locks=dict(primary='synthetic-primary',alternate_loss='synthetic-alternate'))
    return design, payloads, accounting


def build():
    design, payloads, accounting = fixture()
    return api().build_report(design,payloads,accounting=accounting)


def test_complete_report_retains_ten_comparisons_and_no_sampling_inference():
    report = build()
    assert report['status'] == 'DESCRIPTIVE_ONLY'
    assert len(report['comparisons']) == 10
    assert len(report['models']) == 18
    assert report['header'].endswith('NO_VALIDATED_REPLACEMENT')
    assert report['comparisons']['primary:jepa_finetune-supervised']['seed_ids'] == [1261866429,1291916211]
    for comparison in report['comparisons'].values():
        for field in ('difference_interval','relative_interval','standard_error','p_value','significance','bootstrap_negative_fraction'):
            assert comparison[field] is None
        for field in ('inference_reason','interval_reason','relative_interval_reason'):
            assert comparison[field] == 'NO_VALIDATED_REPLACEMENT'
    assert api().validate_report(json.loads(json.dumps(report,allow_nan=False))) == report


def test_diagnostics_keep_cell_reliability_native_intervals_and_pooled_rmse():
    report = build()
    model = report['models']['01-1261866429-primary-jepa_finetune']
    native = model['diagnostics']['native']
    assert np.shape(native['pinball_by_quantile']) == (30,2,5)
    assert np.shape(native['quantile_reliability']) == (30,2,5)
    assert native['counts'] == [[2,2]] * 30
    central = next(value for value in native['intervals'] if value['low'] == .25)
    assert central['aggregate_coverage'] == 1.
    assert central['aggregate_width'] == 3.5
    assert central['aggregate_interval_score'] == 3.5
    assert model['point_metrics']['native']['aggregate']['mse'] == 2.
    assert model['point_metrics']['native']['aggregate']['rmse'] == pytest.approx(np.sqrt(2.))
    assert model['point_metrics']['log10']['aggregate']['rmse'] == pytest.approx(np.log10(3.)/np.sqrt(2.))
    assert set(model['channel_mean_dex_pinball']) == {'xrsa_flux','xrsb_flux'}
    assert report['compute_cost']['actual_ssl_process_count'] == 2
    assert report['compute_cost']['actual_process_wall_seconds'] == 20.
    assert report['compute_cost']['actual_ssl_process_wall_seconds'] == 2.
    assert len(report['compute_cost']['standalone_recipe_process_wall_seconds']) == 18
    assert report['compute_cost']['standalone_recipe_process_wall_seconds']['01-1261866429-primary-jepa_finetune'] == 2.


@pytest.mark.parametrize('damage',['missing_model','extra_ssl','missing_attempt','retry','failed','seed','support','protocol','config'])
def test_complete_report_refuses_shrunk_changed_or_incomplete_cohorts(damage):
    design,payloads,accounting = fixture()
    first = next(iter(payloads))
    if damage == 'missing_model': payloads.pop(first)
    elif damage == 'extra_ssl': payloads[design['jobs'][0]['job_id']] = payloads[first]
    elif damage == 'missing_attempt': accounting['supervisor']['attempts'].pop()
    elif damage == 'retry': accounting['supervisor']['attempts'][0]['number'] = 2
    elif damage == 'failed': accounting['supervisor']['jobs'][first]['status'] = 'failed'
    elif damage == 'seed': payloads[first]['evaluation_record']['identity']['seed'] = 1
    elif damage == 'support': payloads[first]['evaluation_record']['targets']['values'][0][0][0] = 2.
    elif damage == 'protocol': payloads[first]['evaluation_record']['identity']['protocol_fingerprint'] = 'other'
    else: payloads[first]['model_record']['config']['architecture']['width'] = 64
    with pytest.raises(ValueError): api().build_report(design,payloads,accounting=accounting)


@pytest.mark.parametrize('location,key,value',[
    ('top','confidence_interval',[0.,1.]),('comparison','credible_interval',[0.,1.]),
    ('comparison','p_value',.1),('comparison','interval_reason','accepted'),
    ('model','arbitrary_note','better'),('diagnostic','pvalue',.2),('accounting','power',.9)])
def test_round_trip_validation_rejects_extra_fields_aliases_and_tampering(location,key,value):
    report = build()
    target = {'top':report,'comparison':next(iter(report['comparisons'].values())),
        'model':next(iter(report['models'].values())),
        'diagnostic':next(iter(report['models'].values()))['diagnostics']['native'],
        'accounting':report['accounting']}[location]
    target[key] = value
    with pytest.raises(ValueError): api().validate_report(report)


def test_real_supervisor_ledger_is_accepted_with_preparation_charged(tmp_path):
    """Catch production ledger-field and cumulative preparation-accounting drift."""
    import sys
    import time
    from solar_flare_jepa.experiments.v2_resource_controls import ProcessJob, ProcessSupervisor, ResourceLimits
    design,payloads,accounting = fixture()
    jobs = [ProcessJob(job['job_id'], (sys.executable,'-c',
        'from pathlib import Path; Path("synthetic.txt").write_text("synthetic only")'),
        timeout_seconds=job['timeout_seconds']) for job in design['jobs']]
    supervisor = ProcessSupervisor(tmp_path/'supervisor',jobs,
        code_fingerprint='synthetic-code', config_fingerprint='synthetic-config',
        limits=ResourceLimits(max_rss_bytes=2147483648,total_wall_seconds=7200,
            threads=4,max_retries=0,poll_interval_seconds=.05))
    supervisor._ledger['consumed_wall_seconds'] = 1.
    supervisor._save()
    began = time.monotonic()
    ledger = supervisor.run()
    elapsed = time.monotonic()-began
    assert len(ledger['attempts']) == 20
    assert all(job['status']=='succeeded' for job in ledger['jobs'].values())
    accounting.update(supervisor=ledger,wall_seconds=dict(preparation=1.,supervision=elapsed,
        finalization=1.,total=2.+elapsed))
    assert len(api().build_report(design,payloads,accounting=accounting)['models']) == 18


@pytest.mark.parametrize('damage',['median','target_end','extra_model_field','inference_alias'])
def test_canonical_input_content_cannot_broaden_publication(damage):
    from dataclasses import replace
    design,payloads,accounting = fixture()
    if damage in ('extra_model_field','inference_alias'):
        model = next(iter(payloads.values()))['model_record']
        if damage == 'extra_model_field': model['arbitrary_result'] = 'better'
        else: model['history'][0]['credible_interval'] = [0.,1.]
    else:
        for payload in payloads.values():
            record = EvaluationRecord.from_dict(payload['evaluation_record'])
            if damage == 'median':
                record = replace(record,prediction=replace(record.prediction,values=record.prediction.values*1.1))
            else:
                grid = record.targets.grid
                new_issues = grid.issue_times_ns + (int(np.datetime64('2024-08-01','ns').astype(np.int64)) - int(grid.ends_ns[-1,-1]) + 60*10**9)
                shift = new_issues[0]-grid.issue_times_ns[0]
                new_grid = replace(grid,issue_times_ns=new_issues,starts_ns=grid.starts_ns+shift,ends_ns=grid.ends_ns+shift)
                record = replace(record,targets=replace(record.targets,grid=new_grid),prediction=replace(record.prediction,grid=new_grid))
            payload['evaluation_record'] = record.as_dict()
    with pytest.raises(ValueError): api().build_report(design,payloads,accounting=accounting)


@pytest.mark.parametrize('where', ['history','selection','budget','totals','environment',
    'train_windows','validation','wall_seconds','runtime_environment','runtime_host',
    'source_files','packages','lock_files','supervisor_plan'])
@pytest.mark.parametrize('key', ['unexpected_payload','sampling_ci95'])
def test_nested_metadata_is_a_closed_schema_not_an_inference_alias_blacklist(where,key):
    """Any unrecognized nested field must fail even when its name is new."""
    design,payloads,accounting = fixture()
    model = next(iter(payloads.values()))['model_record']
    targets = dict(history=model['history'][0],selection=model['selection'],budget=model['budget'],
        totals=model['budget']['totals'],environment=model['environment'],
        train_windows=model['train_windows'],validation=model['validation'],wall_seconds=model['wall_seconds'],
        runtime_environment=accounting['runtime']['environment'],runtime_host=accounting['runtime']['host'],
        source_files=accounting['runtime']['source_files'],packages=accounting['runtime']['environment']['packages'],
        lock_files=accounting['runtime']['environment']['lock_files'],supervisor_plan=accounting['supervisor']['plan'])
    if where=='source_files': targets[where].append(dict(path='synthetic.py',bytes=0,sha256='a'*64,**{key:[-1.,1.]}))
    else: targets[where][key] = [-1.,1.]
    with pytest.raises(ValueError): api().build_report(design,payloads,accounting=accounting)


def test_existing_scalar_fields_cannot_smuggle_nested_results():
    design,payloads,accounting = fixture()
    accounting['supervisor']['schema_version'] = {'sampling_ci95': [-1.,1.]}
    with pytest.raises(ValueError): api().build_report(design,payloads,accounting=accounting)


@pytest.mark.parametrize('where',['linear_candidate','module_update','fingerprint','pretraining',
    'pairing','random_stream','phase','artifact_file','process_command'])
def test_remaining_nested_metadata_roles_reject_unknown_or_container_values(where):
    design,payloads,accounting = fixture()
    controlled = payloads['01-1261866429-primary-jepa_finetune']['model_record']
    linear = payloads['07-1261866429-baseline-quantile_linear']['model_record']
    node = {'linear_candidate':linear['lambda_candidates'][0],
        'module_update':controlled['budget']['phases'][0]['parameter_updates']['encoder'],
        'fingerprint':controlled['fingerprints']['initial'],'pretraining':controlled['pretraining'],
        'pairing':controlled['pairing'],'random_stream':controlled['rng_streams'],
        'phase':controlled['budget']['phases'][0]}.get(where)
    if node is not None: node['sampling_ci95'] = [-1.,1.]
    elif where=='artifact_file':
        accounting['supervisor']['jobs'][next(iter(payloads))]['artifacts']['files'].append(
            dict(path='synthetic.json',bytes=0,sha256='a'*64,sampling_ci95=[-1.,1.]))
    else: accounting['supervisor']['plan']['jobs'][0]['command'].append({'sampling_ci95':[-1.,1.]})
    with pytest.raises(ValueError): api().build_report(design,payloads,accounting=accounting)


def test_linear_work_discloses_derived_examples_and_weight_bias_updates():
    report = build()
    work = report['models']['07-1261866429-baseline-quantile_linear']['derived_linear_work']
    assert work['evidence'] == 'DERIVED_FROM_COMPLETE_FIXED_SCHEDULE_AND_RECORDED_OPTIMIZER_STEPS'
    assert work['total_examples_seen'] == 1400
    assert work['total_optimizer_steps'] == 700
    assert work['module_optimizer_updates'] == {'weight':700,'bias':700}
    assert [candidate['examples_seen'] for candidate in work['candidates']] == [200]*7
    assert all(candidate['module_optimizer_updates']=={'weight':100,'bias':100} for candidate in work['candidates'])
