"""Synthetic fitting guards, mandatory development isolation, and all-fold locks."""
from copy import deepcopy
from dataclasses import replace
import importlib
import json

import numpy as np
import pytest

pytest.importorskip('torch')

from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord
from solar_flare_jepa.experiments import v2_runner as runner
from solar_flare_jepa.experiments.v2_interfaces import evaluation_identity_fields
from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset, canonical_json
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.training.controlled import ControlledConfig, TrainingSchedule, fit_controlled
from solar_flare_jepa.training.jepa import JepaConfig

NS = 1_000_000_000
DECLARATIONS = dict(experiment_id='safety-development', code_fingerprint='code',
                    data_provenance_fingerprint='source', split_fingerprint='declared-splits',
                    protocol_fingerprint='development-protocol')
PROVENANCE = dict(code_fingerprint='code', source_kind='synthetic-test')


def safety():
    return importlib.import_module('solar_flare_jepa.experiments.v2_evaluation_safety')


@pytest.fixture(scope='module')
def development():
    ticks = np.arange(80, dtype=np.int64)
    values = 10. ** np.column_stack((-6 + .2 * np.sin(ticks / 5), -5.5 + .3 * np.cos(ticks / 7)))
    mask = np.ones_like(values, bool)
    dataset = TimeSeriesDataset('safety-fixture', 'synthetic_fixture', ticks * NS, (ticks + 1) * NS,
                               values, mask, values, mask, ('a', 'b'), ('a', 'b'),
                               ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), 1,
                               availability_policy='bin_end_earliest')
    spec = ForecastSpec(1, 4, 2, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'), ('W/m2', 'W/m2'),
                        stride_steps=2, transform='log10', feature_reference=(1., 1.),
                        target_reference=(1., 1.), target_minimum=(0., 0.),
                        availability_mode='retrospective_bin_end', eligibility_policy='complete')
    train = build_partition_windows(dataset, spec, TemporalPartition('train', 0, 48 * NS))
    valid = build_partition_windows(dataset, spec, TemporalPartition('validation', 48 * NS, 80 * NS))
    schedule = TrainingSchedule('supervised', 0, 0, 1, None,
                                'dex_pinball_equal_channel_v2', 'dex_pinball_equal_channel_v2')
    models = {}
    for seed in (5, 6):
        architecture = JepaConfig(patch_steps=2, width=8, depth=1, heads=2, predictor_depth=1,
                                  mlp_ratio=2, head_hidden=16, batch_size=8, threads=1,
                                  monitor_windows=8, max_train_windows=16, context_mask_patches=1, seed=seed)
        models[seed] = fit_controlled(train.training_slice, valid, ControlledConfig(architecture, schedule))
    return dict(dataset=dataset, spec=spec, train=train, validation=valid, models=models)


def plan_for(development, *, seeds=(5, 6), **changes):
    arguments = dict(experiment_id=DECLARATIONS['experiment_id'],
                     config=dict(evaluation_identity=DECLARATIONS),
                     dataset_fingerprint=development['dataset'].fingerprint,
                     split_identities=dict(train=development['train'].split_fingerprint,
                                           validation=development['validation'].split_fingerprint),
                     test_identity='opaque-unread-test-identity',
                     jobs=tuple(runner.JobSpec('supervised', seed, dict(model_config=development['models'][seed].record['config']))
                                for seed in seeds))
    arguments.update(changes)
    return runner.RunConfig(**arguments)


def job_record(development, seed):
    model = development['models'][seed]
    valid = development['validation']
    identity = EvaluationIdentity(**evaluation_identity_fields(model.record, **DECLARATIONS))
    record = EvaluationRecord(identity, valid.targets, model.predict(valid.context, valid.targets.grid))
    return dict(model_record=model.record, evaluation_record=record.as_dict())


def make_run(tmp_path, development, name='development', *, plan=None, validation=None, embargo_ns=0):
    return safety().DevelopmentRun(tmp_path, name, plan or plan_for(development),
                                   training=development['train'].training_slice,
                                   validation=validation or development['validation'],
                                   embargo_ns=embargo_ns, provenance=PROVENANCE)


def fit_to_lock(run, development):
    run.validate().fit(lambda job, directory: job_record(development, job['seed']))
    run.select(lambda records: dict(selected_job_ids=[r['job_id'] for r in records]))
    return run.lock()


def test_guard_accepts_complete_actual_jobs_and_development_stays_locked(tmp_path, development):
    run = fit_to_lock(make_run(tmp_path, development), development)
    assert run.stage == 'D_LOCKED'
    assert [entry['result']['passed'] for entry in run.snapshot()['hooks']] == [True, True, True]
    with pytest.raises(runner.ReleaseRejected):
        run.release_test(None, 'opaque-unread-test-identity', None)
    assert run.snapshot()['release'] is None


@pytest.mark.parametrize('key', ['normalization_fingerprint', 'training_fingerprint', 'spec_fingerprint',
                                 'training_dataset_fingerprint'])
def test_guard_rejects_changed_actual_model_fingerprints(tmp_path, development, key):
    run = make_run(tmp_path, development)
    run.validate()
    def changed(job, directory):
        result = job_record(development, job['seed'])
        result['model_record'][key] = 'different'
        return result
    with pytest.raises(runner.ValidationHookFailed):
        run.fit(changed)
    assert run.stage == 'A_VALIDATED'


@pytest.mark.parametrize('change', ['seed', 'arm', 'model_id', 'evaluation_seed', 'evaluation_protocol',
                                   'evaluation_support', 'configuration'])
def test_guard_rejects_plan_record_and_evaluation_mismatch(tmp_path, development, change):
    run = make_run(tmp_path, development)
    run.validate()
    def changed(job, directory):
        result = job_record(development, job['seed'])
        model, evaluation = result['model_record'], result['evaluation_record']
        if change == 'seed':
            model['seed'] = 17
        elif change == 'arm':
            model['arm'] = 'random_frozen'
        elif change == 'model_id':
            model['model_id'] = 'v2_random_frozen'
        elif change == 'evaluation_seed':
            evaluation['identity']['seed'] = 17
        elif change == 'evaluation_protocol':
            evaluation['identity']['protocol_fingerprint'] = 'different'
        elif change == 'configuration':
            model['config']['architecture']['lr'] = .5
        else:
            evaluation['targets']['values'][0][0][0] *= 2
        return result
    with pytest.raises(runner.ValidationHookFailed):
        run.fit(changed)


def test_guard_rejects_incomplete_planned_seed_matrix(tmp_path, development):
    run = make_run(tmp_path, development)
    run.validate()
    def fit(job, directory):
        if job['seed'] == 6:
            raise RuntimeError('explicit synthetic fit failure')
        return job_record(development, job['seed'])
    with pytest.raises(runner.ValidationHookFailed):
        run.fit(fit)
    assert run.stage == 'A_VALIDATED'
    assert sum(j['status'] == 'failed' for j in run.snapshot()['jobs'].values()) == 1


def test_guard_rejects_duplicate_arm_seed_jobs_even_with_different_parameters(tmp_path, development):
    base = plan_for(development)
    jobs = list(base.jobs) + [runner.JobSpec('supervised', 5, {'duplicate': True})]
    plan = plan_for(development, jobs=jobs)
    with pytest.raises(ValueError, match='duplicate|matrix|arm.*seed'):
        make_run(tmp_path, development, plan=plan)


@pytest.mark.parametrize('field', ['dataset', 'train', 'validation', 'provenance'])
def test_guard_binds_actual_data_splits_and_code_provenance(tmp_path, development, field):
    changes = {}
    provenance = PROVENANCE
    if field == 'dataset':
        changes['dataset_fingerprint'] = 'different'
    elif field in ('train', 'validation'):
        changes['split_identities'] = dict(plan_for(development).split_identities, **{field: 'different'})
    else:
        provenance = dict(code_fingerprint='different')
    with pytest.raises(ValueError):
        safety().DevelopmentRun(tmp_path, 'development', plan_for(development, **changes),
                                training=development['train'].training_slice,
                                validation=development['validation'], embargo_ns=0, provenance=provenance)


def test_guard_rejects_temporal_overlap_and_explicit_embargo(tmp_path, development):
    overlap = build_partition_windows(development['dataset'], development['spec'],
                                      TemporalPartition('validation', 40 * NS, 80 * NS))
    plan = plan_for(development, split_identities=dict(train=development['train'].split_fingerprint,
                                                      validation=overlap.split_fingerprint))
    with pytest.raises(ValueError, match='overlap'):
        make_run(tmp_path, development, plan=plan, validation=overlap)
    with pytest.raises(ValueError, match='embargo'):
        make_run(tmp_path, development, name='embargo', embargo_ns=1)


def test_comparator_cohort_rejects_changed_validation_selection_support(development):
    record = development['models'][5].record
    comparator = deepcopy(record)
    comparator.update(model_kind='tcn_quantile', model_id='v2_tcn_quantile')
    summary = safety().check_comparator_cohort([record, comparator])
    assert summary['records'] == 2
    comparator['validation']['content_fingerprint'] = 'different'
    with pytest.raises(ValueError, match='validation'):
        safety().check_comparator_cohort([record, comparator])


def test_development_resume_reinstalls_required_guards(tmp_path, development):
    run = make_run(tmp_path, development)
    run.validate().fit(lambda job, directory: job_record(development, job['seed']))
    resumed = make_run(tmp_path, development)
    resumed.select(lambda records: dict(selected_job_ids=[r['job_id'] for r in records])).lock()
    stages = [entry['stage'] for entry in resumed.snapshot()['hooks']]
    assert stages == ['B_FITTED', 'C_SELECTED', 'D_LOCKED']
    assert resumed.stage == 'D_LOCKED'


def test_resumed_development_cannot_bypass_guard_with_a_changed_job_record(tmp_path, development):
    run = make_run(tmp_path, development)
    run.validate().fit(lambda job, directory: job_record(development, job['seed']))
    path = run.run_dir / 'ledger.json'
    ledger = json.loads(path.read_text())
    next(iter(ledger['jobs'].values()))['record']['model_record']['normalization_fingerprint'] = 'different'
    path.write_text(canonical_json(ledger))
    resumed = make_run(tmp_path, development)
    with pytest.raises(runner.ValidationHookFailed):
        resumed.select(lambda records: dict(selected_job_ids=[r['job_id'] for r in records]))


def test_development_publication_is_forced_descriptive_and_cannot_be_replaced(tmp_path, development):
    run = fit_to_lock(make_run(tmp_path, development), development)
    destination = run.publish_development({'summary.json': {'example': 1}})
    metadata = json.loads((destination / 'development_status.json').read_text())
    assert metadata['analysis_status'] == 'DESCRIPTIVE_ONLY'
    assert metadata['inference_status'] == 'INFERENCE_UNAVAILABLE'
    assert metadata['execution_mode'] == 'DEVELOPMENT_ONLY'
    assert metadata['classical_acceptance_status'] == 'POLICY_UNAVAILABLE'
    assert json.loads((destination / 'run_ledger.json').read_text())['stage'] == 'D_LOCKED'
    assert (destination / 'lock_manifest.json').is_file()
    assert (destination / 'artifacts.json').is_file()
    assert run.stage == 'D_LOCKED'
    with pytest.raises(FileExistsError):
        run.publish_development({'summary.json': {'example': 2}})
    assert json.loads((destination / 'summary.json').read_text()) == {'example': 1}


def test_development_publication_rechecks_guards_and_lock(tmp_path, development):
    run = fit_to_lock(make_run(tmp_path, development), development)
    lock = run.run_dir / 'lock.json'
    lock.chmod(0o644)
    lock.write_text('{}')
    with pytest.raises(runner.ArtifactIntegrityError):
        run.publish_development({'summary.json': {}})
    assert not (run.run_dir / 'development_publication').exists()


@pytest.mark.parametrize('location', ['live', 'persisted'])
@pytest.mark.parametrize('field', ['prediction', 'accounting', 'missing_seal'])
def test_development_refuses_post_lock_payload_drift(tmp_path, development, location, field):
    run = fit_to_lock(make_run(tmp_path, development), development)
    ledger = run._ledger if location == 'live' else json.loads((run.run_dir / 'ledger.json').read_text())
    payload = next(iter(ledger['jobs'].values()))['record']
    if field == 'prediction':
        payload['evaluation_record']['prediction']['values'][0][0][0] *= 2
    elif field == 'accounting':
        payload['model_record']['wall_seconds']['this_call_training'] *= 2
    else:
        ledger['hooks'] = [entry for entry in ledger['hooks'] if entry['stage'] != 'D_LOCKED']
    with pytest.raises(runner.ArtifactIntegrityError, match='payload|fingerprint|seal'):
        if location == 'persisted':
            (run.run_dir / 'ledger.json').write_text(canonical_json(ledger))
            run = make_run(tmp_path, development)
        run.publish_development({'summary.json': {}})
    assert not (run.run_dir / 'development_publication').exists()


def test_development_rejects_release_enablement_and_confirmatory_mode(tmp_path, development):
    kwargs = dict(training=development['train'].training_slice, validation=development['validation'],
                  embargo_ns=0, provenance=PROVENANCE)
    for extra in (dict(allow_test_release=True), dict(mode='confirmatory')):
        with pytest.raises(TypeError):
            safety().DevelopmentRun(tmp_path, 'development', plan_for(development), **kwargs, **extra)


@pytest.mark.parametrize('mode', ['CONFIRMATORY', 'INFERENCE_VALIDATED', 'confirmatory', None])
def test_development_rejects_non_development_execution_mode_in_plan(tmp_path, development, mode):
    plan = plan_for(development, config=dict(evaluation_identity=DECLARATIONS, execution_mode=mode))
    with pytest.raises(ValueError, match='DEVELOPMENT_ONLY'):
        make_run(tmp_path, development, plan=plan)


def plain_run(root, name, test_identity):
    plan = runner.RunConfig(experiment_id='study', config={'synthetic': True}, dataset_fingerprint='dataset',
                            split_identities={'train': 'train', 'validation': 'validation'},
                            test_identity=test_identity, jobs=(runner.JobSpec('toy', 5),),
                            approval_status=runner.APPROVED)
    return runner.StagedRun(root, name, plan, allow_test_release=True)


def lock_plain(run):
    run.validate().fit(lambda job, directory: {'synthetic': True})
    run.select(lambda records: {'selected_job_ids': [r['job_id'] for r in records]}).lock()
    return run


def authorization(run):
    return runner.TestReleaseAuthorization(runner.APPROVED, run.plan.config_fingerprint,
                                            run.lock_fingerprint, 'synthetic-test')


def test_study_lock_refuses_release_until_every_declared_fold_is_locked(tmp_path):
    first = lock_plain(plain_run(tmp_path, 'first', 'test-first'))
    second = plain_run(tmp_path, 'second', 'test-second')
    study = safety().StudyLock(tmp_path, 'all-folds', {'f1': first, 'f2': second})
    with pytest.raises(ValueError, match='locked|D_LOCKED'):
        study.lock()
    with pytest.raises(runner.ValidationHookFailed):
        first.release_test(authorization(first), 'test-first', lambda *args: {'synthetic': True})
    assert not (first.run_dir.parent / runner.RELEASE_REGISTRY).exists()
    lock_plain(second)
    study.lock()
    first.release_test(authorization(first), 'test-first', lambda *args: {'synthetic': True})
    assert first.stage == 'E_TEST_RELEASED'


def test_study_release_rechecks_other_fold_lock_before_consuming_release(tmp_path):
    first = lock_plain(plain_run(tmp_path, 'first', 'test-first'))
    second = lock_plain(plain_run(tmp_path, 'second', 'test-second'))
    safety().StudyLock(tmp_path, 'all-folds', {'f1': first, 'f2': second}).lock()
    lock = second.run_dir / 'lock.json'
    lock.chmod(0o644)
    lock.write_text('{}')
    with pytest.raises(runner.ValidationHookFailed):
        first.release_test(authorization(first), 'test-first', lambda *args: {'synthetic': True})
    assert first.snapshot()['release'] is None
    assert not (first.run_dir.parent / runner.RELEASE_REGISTRY).exists()


def test_study_resume_rejects_changed_complete_fold_mapping(tmp_path):
    first = lock_plain(plain_run(tmp_path, 'first', 'test-first'))
    second = lock_plain(plain_run(tmp_path, 'second', 'test-second'))
    safety().StudyLock(tmp_path, 'all-folds', {'f1': first, 'f2': second}).lock()
    with pytest.raises((ValueError, runner.IdentityMismatch)):
        safety().StudyLock(tmp_path, 'all-folds', {'f1': first})


def test_study_requires_distinct_runs_under_one_results_root(tmp_path):
    first = plain_run(tmp_path, 'first', 'test-first')
    other = plain_run(tmp_path / 'other-root', 'other', 'test-other')
    with pytest.raises(ValueError):
        safety().StudyLock(tmp_path, 'duplicate', {'f1': first, 'f2': first})
    with pytest.raises(ValueError):
        safety().StudyLock(tmp_path, 'different-root', {'f1': first, 'f2': other})


def test_guard_rejects_selectively_dropped_planned_seed_at_selection(tmp_path, development):
    run = make_run(tmp_path, development)
    run.validate().fit(lambda job, directory: job_record(development, job['seed']))
    with pytest.raises(runner.ValidationHookFailed):
        run.select(lambda records: {'selected_job_ids': [records[0]['job_id']]})
    assert run.stage == 'B_FITTED'


def test_guard_recomputes_training_windows_instead_of_trusting_a_common_label(tmp_path, development):
    run = make_run(tmp_path, development)
    run.validate()
    def changed(job, directory):
        result = job_record(development, job['seed'])
        result['model_record']['train_windows']['fingerprint'] = 'same-forged-window-identity'
        return result
    with pytest.raises(runner.ValidationHookFailed):
        run.fit(changed)


def test_development_publication_rechecks_model_records_after_lock(tmp_path, development):
    run = fit_to_lock(make_run(tmp_path, development), development)
    next(iter(run._ledger['jobs'].values()))['record']['model_record']['normalization_fingerprint'] = 'different'
    with pytest.raises(ValueError, match='normalization'):
        run.publish_development({'summary.json': {}})
    assert not (run.run_dir / 'development_publication').exists()


def test_study_resume_reinstalls_release_hooks_and_rejects_changed_study_manifest(tmp_path):
    first = lock_plain(plain_run(tmp_path, 'first', 'test-first'))
    second = lock_plain(plain_run(tmp_path, 'second', 'test-second'))
    study = safety().StudyLock(tmp_path, 'all-folds', {'f1': first, 'f2': second})
    study.lock()
    resumed = plain_run(tmp_path, 'first', 'test-first')
    safety().StudyLock(tmp_path, 'all-folds', {'f1': resumed, 'f2': second})
    study.path.chmod(0o644)
    study.path.write_text('{}')
    with pytest.raises(runner.ValidationHookFailed):
        resumed.release_test(authorization(resumed), 'test-first', lambda *args: {'synthetic': True})
    assert resumed.snapshot()['release'] is None
