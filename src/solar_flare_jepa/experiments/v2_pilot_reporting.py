"""Strict Protocol v1 publication from complete, canonical development records.

This module never fits a model, reads scientific files, or computes sampling
inference. The caller must first lock both DevelopmentRuns; supplied locks and
runtime identities remain declarations, not authentication of training history.
"""
import json
import math

import numpy as np

from solar_flare_jepa.evaluation.diagnostics import calibration_diagnostics
from solar_flare_jepa.evaluation.records import EvaluationRecord
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .v2_descriptive import descriptive_comparison
from .v2_evaluation_safety import _model_configuration, check_comparator_cohort
from .v2_interfaces import evaluation_identity_fields

DESIGN_FINGERPRINT = 'ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624'
HEADER = ('DEVELOPMENT FEASIBILITY ONLY — EXPOSED MAY–JULY2024 — '
          'POST-SELECTION VALIDATION — ONE FOLD/TWO SEEDS — '
          'DESCRIPTIVE_ONLY — INFERENCE_UNAVAILABLE — NO_VALIDATED_REPLACEMENT')
_REPORT_KEYS = {'schema_version', 'header', 'status', 'inference_status', 'inference_reason',
                'design_fingerprint', 'design', 'payloads', 'accounting', 'models',
                'comparisons', 'compute_cost'}
_MODEL_REQUIRED = {'schema_version', 'model_id', 'model_kind', 'scientific_status', 'config',
    'run_fingerprint', 'recipe_fingerprint', 'seed', 'spec_fingerprint',
    'normalization_fingerprint', 'training_fingerprint', 'training_dataset_fingerprint',
    'train_windows', 'validation', 'selection', 'budget', 'environment', 'wall_seconds'}
_MODULES = {'encoder','target_encoder','predictor','head'}
_MONITOR = {'context_latent_std','context_effective_rank'}
_TARGET_MONITOR = {'target_latent_std','target_effective_rank'}
_LOCK_FILES = {'requirements-lock.txt','requirements-training-lock.txt','requirements-v1-lock.txt','pyproject.toml'}



def _schema(value, keys, label):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(f'Malformed {label} schema')


def _snapshot(value):
    try:
        return json.loads(canonical_json(value))
    except (TypeError, OverflowError) as error:
        raise ValueError('Report inputs must be finite JSON') from error


def _flat_schema(value, keys, label):
    """An exact object whose fields contain scalars, never extensible metadata."""
    _schema(value,keys,label)
    if any(type(item) not in (str,int,float,bool,type(None)) for item in value.values()):
        raise ValueError(f'{label} fields must be scalar values')


def _string_map(value, label):
    # Package names are a dynamic domain map; versions cannot carry nested JSON.
    if type(value) is not dict or any(type(k) is not str or not k
            or type(v) is not str or not v for k,v in value.items()):
        raise ValueError(f'{label} requires string names and string values')


def _file_entries(value, label):
    if type(value) is not list:
        raise ValueError(f'{label} requires an ordered file manifest')
    paths = set()
    for entry in value:
        _flat_schema(entry,{'path','bytes','sha256'},label)
        path,digest = entry['path'],entry['sha256']
        if (type(path) is not str or not path or path.startswith('/')
                or any(part in ('','..','.') for part in path.split('/')) or path in paths
                or type(entry['bytes']) is not int or entry['bytes'] < 0
                or type(digest) is not str or len(digest) != 64
                or any(char not in '0123456789abcdef' for char in digest)):
            raise ValueError(f'Malformed {label} identity')
        paths.add(path)


def _model_metadata(model,job):
    """Close every nested model-record object using the existing trainer schemas.

    No result map accepts arbitrary extension keys. Configurations are separately
    checked by the original typed parsers and exact frozen job configuration.
    """
    controlled = job['kind'] == 'neural_downstream'
    linear = job['kind'] == 'quantile_linear'
    extras = ({'arm','rng_streams','pairing','fingerprints','pretraining','history','parameters'}
              if controlled else {'rng_streams','lambda_candidates','parameters'} if linear
              else {'rng_streams','pairing','fingerprints','history','parameters'})
    _schema(model,_MODEL_REQUIRED | extras,'model metadata')
    for key in _MODEL_REQUIRED - {'config','train_windows','validation','selection','budget','environment','wall_seconds'}:
        if type(model[key]) not in (str,int,float,bool,type(None)):
            raise ValueError('Model identity fields must be scalar values')
    _flat_schema(model['train_windows'],{'eligible','used','stride','cap','policy','subsample','fingerprint'},'training subset')
    _flat_schema(model['validation'],{'origin_count','origin_fingerprint','split_fingerprint',
        'spec_fingerprint','dataset_fingerprint','content_fingerprint'},'validation provenance')
    _flat_schema(model['environment'],{'torch_version','torch_threads','deterministic_algorithms',
        'python','platform','process_peak_rss_bytes','rss_scope'},'model environment')
    wall_keys = {'preparation','this_call_training','scope'} | ({'attributed_training'} if controlled else set())
    _flat_schema(model['wall_seconds'],wall_keys,'model wall timing')
    _flat_schema(model['parameters'],({'encoder','target_encoder_ema','predictor','head','trainable_total'}
        if controlled else {'trainable_total'} if linear else
        {'trainable_total','receptive_field_bins','context_steps'}),'model parameters')
    selection_keys = ({'partition','metric','value','lambda','tie_policy','epoch_selection','quantile_order'}
        if linear else {'partition','metric','value','epoch','eligible_phase','tie_policy',
            'early_stopping_patience','stopped_early','epochs_executed','epochs_planned'})
    _flat_schema(model['selection'],selection_keys,'model selection')
    rng_keys = ({'initialization','pretrain_order','pretrain_context_mask','warmup_order','downstream_order'}
        if controlled else {'shuffle','initialization'} if linear else {'initialization','downstream_order'})
    _flat_schema(model['rng_streams'],rng_keys,'model random streams')
    _schema(model['budget'],{'phases','totals'},'model budget')
    totals_keys = ({'optimizer_steps','selected_fit_steps'} if linear else
        {'optimizer_steps','examples_seen','parameter_updates'} | ({'ema_target_updates'} if controlled else set()))
    totals = model['budget']['totals']
    _schema(totals,totals_keys,'budget totals')
    _flat_schema({k:v for k,v in totals.items() if k!='parameter_updates'},totals_keys-{'parameter_updates'},'scalar budget totals')
    if not linear:
        _flat_schema(totals['parameter_updates'],_MODULES if controlled else {'tcn','head'},'total module updates')
    phases = model['budget']['phases']
    if type(phases) is not list or any(type(phase) is not dict for phase in phases):
        raise ValueError('Budget phases require an ordered list')
    expected_phases = (['lambda_grid'] if linear else
        (['pretrain'] if controlled and job['dependencies'] else
         ['supervised_warmup'] if job['arm']=='supervised_extra_updates' else []) + ['downstream'])
    if [phase.get('phase') for phase in phases] != expected_phases:
        raise ValueError('Every actual planned training phase must be retained')
    common_phase = {'phase','epochs_planned','epochs_executed','optimizer_steps','examples_seen',
        'optimizer','optimizer_reset','lr','weight_decay','parameter_updates','wall_seconds'}
    for phase in phases:
        if linear:
            _flat_schema(phase,{'phase','fits','epochs_per_fit','optimizer_steps','optimizer','lr'},'linear budget phase')
        else:
            phase_keys = common_phase | ({'ema_target_updates'} if phase['phase']=='pretrain' else set())
            _schema(phase,phase_keys,'neural budget phase')
            _flat_schema({k:v for k,v in phase.items() if k!='parameter_updates'},phase_keys-{'parameter_updates'},'scalar phase budget')
            _schema(phase['parameter_updates'],_MODULES if controlled else {'tcn','head'},'phase modules')
            for updates in phase['parameter_updates'].values():
                _flat_schema(updates,{'min','max','tensors','source'},'module optimizer updates')
    if not linear:
        _flat_schema(model['pairing'],{'initial_state','pretrain_order','warmup_order','downstream_order'}
            if controlled else {'initial_state','downstream_order'},'model pairing')
        stage_keys = {'initial','selected'} | ({'after_pretrain'} if job['dependencies'] else
            {'after_warmup'} if job['arm']=='supervised_extra_updates' else set())
        _schema(model['fingerprints'],stage_keys,'module fingerprint stages')
        for stage in model['fingerprints'].values():
            _flat_schema(stage,_MODULES if controlled else {'blocks','head'},'module fingerprints')
        if controlled:
            if job['dependencies']:
                _flat_schema(model['pretraining'],{'reused','artifact_fingerprint','wall_seconds'},'reused SSL')
            elif model['pretraining'] is not None:
                raise ValueError('An arm without SSL cannot carry pretraining metadata')
        history = model['history']
        if type(history) is not list or any(type(row) is not dict for row in history):
            raise ValueError('Neural histories require an ordered list')
        expected_epochs = [(phase,epoch) for phase in expected_phases
            for epoch in range(1,(15 if phase=='downstream' else 8)+1)]
        if [(row.get('phase'),row.get('epoch')) for row in history] != expected_epochs:
            raise ValueError('Every planned neural epoch must appear once in order')
        for row in history:
            phase = row.get('phase')
            monitor = (_MONITOR | (_TARGET_MONITOR if job['dependencies'] else set())) if controlled else set()
            if phase == 'pretrain':
                _flat_schema(row,{'phase','epoch','train_jepa_loss','steps','ema_momentum','wall_seconds'}
                    | _MONITOR | _TARGET_MONITOR,'SSL history')
            elif phase == 'supervised_warmup':
                _flat_schema(row,{'phase','epoch','train_loss','train_loss_version','steps','wall_seconds'}
                    | _MONITOR,'warmup history')
            elif phase == 'downstream':
                keys = {'phase','epoch','train_loss','train_loss_version','metrics','steps','wall_seconds'} | monitor
                _schema(row,keys,'downstream history')
                _flat_schema({k:v for k,v in row.items() if k!='metrics'},keys-{'metrics'},'scalar downstream history')
                schedule = job['model_config']['schedule']
                _flat_schema(row['metrics'],set(schedule['diagnostic_metrics']) | {schedule['selection_metric']},'epoch metrics')
            else:
                raise ValueError('Unexpected training history phase')



def _nonnegative(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{label} must be finite and nonnegative')


def _accounting(design, accounting):
    _schema(accounting, {'schema_version','status','supervisor','runtime','design_fingerprint',
        'binding_fingerprint','wall_seconds','development_locks'}, 'pilot accounting')
    if type(accounting['binding_fingerprint']) is not str or not accounting['binding_fingerprint']:
        raise ValueError('Execution binding identity must be explicit')
    if (accounting['schema_version'] != 1 or accounting['status'] != 'COMPLETE'
            or accounting['design_fingerprint'] != DESIGN_FINGERPRINT):
        raise ValueError('Complete accounting must bind Protocol v1')
    _schema(accounting['development_locks'], {'primary','alternate_loss'}, 'development locks')
    if any(type(value) is not str or not value for value in accounting['development_locks'].values()):
        raise ValueError('Both development locks must be present')
    runtime = accounting['runtime']
    _schema(runtime, {'git_commit','git_branch','source_fingerprint','source_files','environment',
        'host','host_fingerprint','fingerprint'}, 'runtime')
    _schema(runtime['environment'], {'python','executable','packages','lock_files'}, 'environment')
    _flat_schema({k:v for k,v in runtime.items() if k not in ('source_files','environment','host')},
        {'git_commit','git_branch','source_fingerprint','host_fingerprint','fingerprint'},'runtime identities')
    _file_entries(runtime['source_files'],'source file')
    environment = runtime['environment']
    if type(environment['python']) is not str or type(environment['executable']) is not str:
        raise ValueError('Python environment identities must be strings')
    _string_map(environment['packages'],'package versions')
    _schema(environment['lock_files'],_LOCK_FILES,'dependency lock files')
    _string_map(environment['lock_files'],'dependency lock hashes')
    _flat_schema(runtime['host'], {'hostname','platform','machine','processor','logical_cpus',
        'physical_memory_bytes'}, 'host')
    timing = accounting['wall_seconds']
    _schema(timing, {'preparation','supervision','finalization','total'}, 'wall timing')
    for key,value in timing.items():
        _nonnegative(value, key)
    if timing['total'] > design['resources']['total_wall_seconds']:
        raise ValueError('Total pilot wall budget exceeded')
    if timing['total'] + 1e-6 < sum(timing[key] for key in ('preparation','supervision','finalization')):
        raise ValueError('Pilot timing omits charged phases')
    ledger = accounting['supervisor']
    _schema(ledger, {'schema_version','plan','plan_fingerprint','execution_order',
        'consumed_wall_seconds','stop_reason','jobs','attempts'}, 'supervisor ledger')
    if type(ledger['schema_version']) is not int or ledger['schema_version'] != 1:
        raise ValueError('Unsupported supervisor ledger schema')
    plan = ledger['plan']
    _schema(plan,{'schema_version','code_fingerprint','config_fingerprint','resources','jobs'},'supervisor plan')
    _flat_schema({k:v for k,v in plan.items() if k not in ('resources','jobs')},
        {'schema_version','code_fingerprint','config_fingerprint'},'supervisor identities')
    _flat_schema(plan['resources'],{'max_rss_bytes','total_wall_seconds','threads','max_retries','poll_interval_seconds'},'resource limits')
    resource_keys = ('max_rss_bytes','total_wall_seconds','threads','max_retries','poll_interval_seconds')
    if plan['resources'] != {key:design['resources'][key] for key in resource_keys}:
        raise ValueError('Supervised limits must equal frozen resource policy')
    if type(plan['jobs']) is not list:
        raise ValueError('Supervisor process declarations require an ordered list')
    process_specs = {}
    for process in plan['jobs']:
        _schema(process,{'job_id','command','timeout_seconds'},'process declaration')
        if (type(process['command']) is not list or not process['command']
                or any(type(arg) is not str or not arg for arg in process['command'])
                or type(process['job_id']) is not str or process['job_id'] in process_specs):
            raise ValueError('Process arguments require exact scalar argv strings')
        _nonnegative(process['timeout_seconds'],'process timeout')
        process_specs[process['job_id']] = process
    if ledger['plan_fingerprint'] != fingerprint_payload(plan):
        raise ValueError('Supervisor plan fingerprint differs from its content')
    jobs = {job['job_id']: job for job in design['jobs']}
    if (list(process_specs) != list(jobs)
            or any(process_specs[key]['timeout_seconds'] != job['timeout_seconds'] for key,job in jobs.items())):
        raise ValueError('Every exact process declaration must be retained')
    if (ledger['execution_order'] != list(jobs) or set(ledger['jobs']) != set(jobs)
            or ledger['stop_reason'] is not None or len(ledger['attempts']) != 20):
        raise ValueError('Complete reporting requires the exact 20-job matrix')
    _nonnegative(ledger['consumed_wall_seconds'], 'consumed wall seconds')
    if ledger['consumed_wall_seconds'] > timing['preparation'] + timing['supervision'] + 1e-6:
        raise ValueError('Pilot accounting understates supervision time')
    attempts = {}
    for attempt in ledger['attempts']:
        _flat_schema(attempt, {'job_id','job_fingerprint','number','status','path','pid','started_utc','checkpoint_utc',
            'wall_seconds','peak_sampled_rss_bytes','returncode','failure_kind','error',
            'finished_utc'}, 'job attempt')
        job_id = attempt['job_id']
        if (job_id not in jobs or job_id in attempts or type(attempt['number']) is not int
                or attempt['number'] != 1 or attempt['status'] != 'succeeded'
                or attempt['failure_kind'] is not None or attempt['error'] is not None
                or attempt['returncode'] != 0):
            raise ValueError('Every planned process must succeed once with zero retries')
        _nonnegative(attempt['wall_seconds'], 'process wall time')
        if (attempt['wall_seconds'] > jobs[job_id]['timeout_seconds']
                or type(attempt['peak_sampled_rss_bytes']) is not int
                or not 0 <= attempt['peak_sampled_rss_bytes'] <= design['resources']['max_rss_bytes']):
            raise ValueError('Job resource ceiling exceeded')
        _schema(ledger['jobs'][job_id], {'status','artifact_path','artifacts'}, 'supervised job')
        entry = ledger['jobs'][job_id]
        if type(entry['artifact_path']) is not str or not entry['artifact_path']:
            raise ValueError('Successful job artifact path must be explicit')
        _schema(entry['artifacts'],{'files','manifest_sha256'},'sealed artifacts')
        _file_entries(entry['artifacts']['files'],'artifact file')
        if type(entry['artifacts']['manifest_sha256']) is not str:
            raise ValueError('Artifact manifest identity must be a scalar string')
        if attempt['job_fingerprint'] != fingerprint_payload(process_specs[job_id]):
            raise ValueError('Attempt process identity differs from its frozen declaration')
        if ledger['jobs'][job_id]['status'] != 'succeeded':
            raise ValueError('Failed or pending jobs cannot become a complete comparison')
        attempts[job_id] = attempt
    return attempts


def _model_payload(job, payload, design):
    _schema(payload, {'model_record','evaluation_record'}, 'selected-model payload')
    model = payload['model_record']
    _model_metadata(model,job)
    if model['schema_version'] != 1 or model['scientific_status'] != 'EXPERIMENTAL_UNVALIDATED':
        raise ValueError('Pilot models must remain experimental and unvalidated')
    planned = dict(job, parameters={'model_config':job['model_config']})
    _model_configuration(model, planned)
    _schema(model['budget'], {'phases','totals'}, 'model budget')
    if type(model['budget']['phases']) is not list or type(model['budget']['totals']) is not dict:
        raise ValueError('Complete recorded model budgets required')
    selection = model['selection']
    if selection.get('partition') != 'validation':
        raise ValueError('Only validation selections may be reported')
    if job['kind'] == 'quantile_linear':
        candidates = model.get('lambda_candidates')
        if (type(candidates) is not list or any(type(item) is not dict for item in candidates)
                or [item.get('lambda') for item in candidates]
                != design['training']['quantile_linear']['lambdas']):
            raise ValueError('Every frozen linear lambda must be retained')
        for candidate in candidates:
            _flat_schema(candidate, {'lambda','validation_metric','validation_raw_crossing_fraction',
                'optimizer_steps','final_epoch_train_objective','mean_squared_coefficient',
                'shuffle_order','weights_fingerprint','wall_seconds'}, 'linear candidate')
        best = min(candidates, key=lambda item: (item['validation_metric'],item['lambda']))
        if selection.get('lambda') != best['lambda'] or selection.get('value') != best['validation_metric']:
            raise ValueError('Linear selection must keep exact minimum and smallest-lambda ties')
    else:
        history = model.get('history')
        if type(history) is not list or any(type(row) is not dict for row in history):
            raise ValueError('Complete neural curves required')
        downstream = [row for row in history if row.get('phase') == 'downstream']
        metric = job['model_config']['schedule']['selection_metric']
        if ([row.get('epoch') for row in downstream] != list(range(1,16))
                or selection.get('metric') != metric or selection.get('epochs_executed') != 15
                or selection.get('early_stopping_patience') is not None
                or selection.get('stopped_early') is not False):
            raise ValueError('All 15 downstream epochs and fixed selection must be retained')
        values = [row['metrics'][metric] for row in downstream]
        if selection.get('epoch') != values.index(min(values)) + 1 or selection.get('value') != min(values):
            raise ValueError('Neural selection must be the exact earliest minimum')
    evaluation = EvaluationRecord.from_dict(payload['evaluation_record'])
    identity = evaluation.identity
    declarations = {key:getattr(identity,key) for key in ('experiment_id','code_fingerprint',
        'data_provenance_fingerprint','split_fingerprint','protocol_fingerprint')}
    if (identity.as_dict() != evaluation_identity_fields(model, **declarations)
            or identity.protocol_fingerprint != DESIGN_FINGERPRINT
            or evaluation.prediction.model_id != model['model_id']
            or canonical_json(evaluation.targets.grid.spec.as_dict()) != canonical_json(design['data']['forecast'])
            or tuple(evaluation.prediction.quantile_levels) != tuple(design['training']['quantiles'])
            or not evaluation.targets.mask.all() or not len(evaluation.targets.values)):
        raise ValueError('Canonical evaluation must bind the planned model, task and complete support')
    grid = evaluation.targets.grid
    bounds = [int(np.datetime64(value.rstrip('Z'),'ns').astype(np.int64))
              for value in design['data']['splits_utc_half_open']['validation']]
    if (min(int(value) for value in grid.issue_times_ns)
            - grid.spec.context_steps * grid.spec.cadence_ns < bounds[0]
            or max(int(value) for value in grid.ends_ns.flat) > bounds[1]):
        raise ValueError('Full validation contexts and targets must be partition-local')
    if not np.array_equal(evaluation.prediction.values,
                          evaluation.prediction.quantiles[...,evaluation.prediction.quantile_levels.index(.5)]):
        raise ValueError('Saved point forecast must equal the saved median quantile')
    return evaluation


def _point_metrics(record, space):
    observed, point = record.targets.values, record.prediction.values
    if space == 'log10':
        observed = np.log10(observed)
        point = np.log10(point)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        signed = point - observed
        absolute, squared = np.abs(signed), signed**2
        def cell(a, s):
            mse = float(np.mean(s))
            return dict(mae=float(np.mean(a)), mse=mse, rmse=math.sqrt(mse), count=int(a.size))
        return dict(aggregate=cell(absolute,squared), by_channel={name:cell(absolute[:,:,index],squared[:,:,index])
            for index,name in enumerate(record.targets.grid.spec.target_names)},
            by_lead_channel={name:[cell(absolute[:,lead,index],squared[:,lead,index])
                for lead in range(record.targets.grid.spec.horizon_steps)]
                for index,name in enumerate(record.targets.grid.spec.target_names)})


def _linear_work(model):
    if 'lambda_candidates' not in model:
        return None
    config = model['config']['linear']
    used = model['train_windows']['used']
    if type(used) is not int or used <= 0:
        raise ValueError('Linear work accounting requires the actual used training-window count')
    candidates = model['lambda_candidates']
    for candidate in candidates:
        if type(candidate['optimizer_steps']) is not int or candidate['optimizer_steps'] < 0:
            raise ValueError('Linear optimizer counts must be recorded nonnegative integers')
    steps = sum(candidate['optimizer_steps'] for candidate in candidates)
    phase = model['budget']['phases'][0]
    if (phase['epochs_per_fit'] != config['epochs'] or phase['fits'] != len(candidates)
            or phase['optimizer_steps'] != steps or model['budget']['totals']['optimizer_steps'] != steps):
        raise ValueError('Linear candidate work differs from complete fixed-schedule totals')
    examples = config['epochs'] * used
    return dict(evidence='DERIVED_FROM_COMPLETE_FIXED_SCHEDULE_AND_RECORDED_OPTIMIZER_STEPS',
        training_windows_used=used,epochs_per_candidate=config['epochs'],
        candidates=[dict(**{'lambda':candidate['lambda']},examples_seen=examples,
            optimizer_steps=candidate['optimizer_steps'],module_optimizer_updates=dict(
                weight=candidate['optimizer_steps'],bias=candidate['optimizer_steps'])) for candidate in candidates],
        total_examples_seen=examples*len(candidates),total_optimizer_steps=steps,
        module_optimizer_updates=dict(weight=steps,bias=steps),
        scope='Examples are derived from the complete fixed epoch schedule and used training support. '
              'Weight/bias update opportunities are derived from recorded optimizer steps and the fixed Adam recipe; '
              'they are not separately observed parameter-state counters.')


def _diagnostics(record, model):
    native = calibration_diagnostics(record.targets, record.prediction, space='native',
                                     intervals=((.05,.95),(.25,.75)))
    dex = calibration_diagnostics(record.targets, record.prediction, space='log10',
                                  intervals=((.05,.95),(.25,.75)))
    quantiles = record.prediction.quantiles
    collapsed = {str(int(round((high-low)*100))):int(np.count_nonzero(
        quantiles[...,record.prediction.quantile_levels.index(high)]
        == quantiles[...,record.prediction.quantile_levels.index(low)]))
        for low,high in ((.05,.95),(.25,.75))}
    candidates = model.get('lambda_candidates')
    return dict(diagnostics=dict(native=native,log10=dex),derived_linear_work=_linear_work(model),
        channel_mean_dex_pinball={name:float(np.mean(np.asarray(dex['mean_pinball'])[:,index]))
            for index,name in enumerate(record.targets.grid.spec.target_names)},
        point_metrics={space:_point_metrics(record,space) for space in ('native','log10')},
        collapsed_predictive_interval_cells=collapsed,
        raw_crossings=None if candidates is None else [dict(**{'lambda':item['lambda']},
            validation_raw_crossing_fraction=item['validation_raw_crossing_fraction']) for item in candidates],
        boundary_selected=None if candidates is None else model['selection']['lambda'] == max(item['lambda'] for item in candidates))


def _build(design, payloads, accounting):
    if fingerprint_payload(design) != DESIGN_FINGERPRINT:
        raise ValueError('Protocol defaults changed; renewed ratification is required')
    jobs = {job['job_id']:job for job in design['jobs'] if job['development_run'] is not None}
    if type(payloads) is not dict or set(payloads) != set(jobs):
        raise ValueError('Reporting requires exactly all 18 selected models, excluding shared SSL jobs')
    attempts = _accounting(design,accounting)
    records, models, cohorts = {}, {}, {}
    for job_id,job in jobs.items():
        record = _model_payload(job,payloads[job_id],design)
        records[job_id] = record
        cohorts.setdefault((job['development_run'],job['arm']),[]).append(record)
        model = payloads[job_id]['model_record']
        models[job_id] = dict(job_id=job_id,arm=job['arm'],seed=job['seed'],
            cohort=job['development_run'],evaluation_fingerprint=record.fingerprint,
            support_fingerprint=record.support_fingerprint,model_record_fingerprint=fingerprint_payload(model),
            model_record=model,**_diagnostics(record,model))
    check_comparator_cohort([payload['model_record'] for payload in payloads.values()])
    if len({record.support_fingerprint for record in records.values()}) != 1:
        raise ValueError('Every model requires the identical observed support')
    for cohort in cohorts.values():
        if [record.identity.seed for record in cohort] != design['seeds']:
            raise ValueError('Every recipe requires the exact ordered two-seed cohort')
    fold = design['evaluation']['folds'][0]
    bounds = [int(np.datetime64(value.rstrip('Z'),'ns').astype(np.int64))
              for value in design['data']['splits_utc_half_open']['validation']]
    def compare(left,right):
        return descriptive_comparison({fold:cohorts[left]},{fold:cohorts[right]},calendars={fold:bounds})
    comparisons = {f"primary:{contrast['a']}-{contrast['b']}":compare(
        ('primary',contrast['a']),('primary',contrast['b'])) for contrast in design['evaluation']['contrasts']}
    comparisons['alternate_loss:jepa_finetune-supervised'] = compare(
        ('alternate_loss','jepa_finetune'),('alternate_loss','supervised'))
    for arm in design['objectives']['alternate_arms']:
        comparisons[f'loss_recipe:{arm}:dex-normalized'] = compare(('primary',arm),('alternate_loss',arm))
    shared = [job for job in design['jobs'] if job['development_run'] is None]
    costs = {job_id:attempt['wall_seconds'] for job_id,attempt in attempts.items()}
    compute = dict(actual_process_count=20, actual_ssl_process_count=2,
        actual_process_wall_seconds=math.fsum(costs.values()),
        actual_ssl_process_wall_seconds=math.fsum(costs[job['job_id']] for job in shared),
        pilot_elapsed_seconds=accounting['wall_seconds']['total'],
        standalone_recipe_process_wall_seconds={job_id:costs[job_id]+math.fsum(costs[dep] for dep in job['dependencies'])
            for job_id,job in jobs.items()},
        cost_scope='Process wall times count shared SSL once; attributed recipe views duplicate SSL and must not be summed. '
            'Pilot elapsed includes charged preparation/supervision/finalization through report generation snapshot; '
            'final post-publication accounting is persisted separately.',
        matching_claim=design['compute_reporting']['claim'])
    return dict(schema_version=1,header=HEADER,status='DESCRIPTIVE_ONLY',
        inference_status='INFERENCE_UNAVAILABLE',inference_reason='NO_VALIDATED_REPLACEMENT',
        design_fingerprint=DESIGN_FINGERPRINT,design=design,payloads=payloads,accounting=accounting,
        models=models,comparisons=comparisons,compute_cost=compute)


def build_report(design, payloads, *, accounting):
    """Derive the complete fixed pilot report; arbitrary report JSON is refused.

    Inputs are only canonical model/evaluation records for all 18 selected jobs,
    with all 20 successful first-attempt process records in accounting. SSL jobs
    belong to the supervisor and are never passed as DevelopmentRun models.
    """
    design,payloads,accounting = (_snapshot(value) for value in (design,payloads,accounting))
    try:
        report = _build(design,payloads,accounting)
        canonical_json(report)
        return report
    except (KeyError,TypeError,IndexError,FloatingPointError,OverflowError) as error:
        raise ValueError('Malformed or nonfinite complete pilot report inputs') from error


def validate_report(report):
    """Recompute a serialized report and reject extra keys, aliases or tampering.

    This checks report semantics and declared artifact identities. The driver
    separately authenticates sealed files and fitting guards before publication.
    """
    report = _snapshot(report)
    _schema(report,_REPORT_KEYS,'pilot report')
    expected = build_report(report['design'],report['payloads'],accounting=report['accounting'])
    if canonical_json(report) != canonical_json(expected):
        raise ValueError('Report schema or derived descriptive content differs from canonical records')
    return report
