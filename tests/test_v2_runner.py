"""V2 staged runner: stage ordering, test-release gate, locks, resume, hooks, resources.

Synthetic, model-free fixtures only: trivial fit/predict callables write small
JSON/npy artifacts. No scientific data, no torch, no real test partition.
"""
import json
import os
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.experiments import v2_runner as v2
from solar_flare_jepa.experiments.provenance import verify_artifacts
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload

DATASET = 'd' * 64
SPLITS = {'train': 'a' * 64, 'validation': 'b' * 64}
TEST = 'c' * 64


def jobs(order=1):
    items = [v2.JobSpec('jepa_finetune', 1, {'epochs': 2}), v2.JobSpec('supervised', 1, {'epochs': 2}),
             v2.JobSpec('jepa_finetune', 2, {'epochs': 2})]
    return tuple(items[::order])


def plan(**changes):
    values = dict(experiment_id='v2-synthetic', config={'lr': 0.01, 'schedule': [1, 2]},
                  dataset_fingerprint=DATASET, split_identities=dict(SPLITS), test_identity=TEST,
                  jobs=jobs())
    values.update(changes)
    return v2.RunConfig(**values)


def make(tmp_path, run_config=None, **options):
    if run_config is None:  # a release-enabled run also needs an approved plan
        run_config = plan(approval_status='APPROVED') if options.get('allow_test_release') else plan()
    return v2.StagedRun(tmp_path, 'run1', run_config, **options)


def test_release_requires_an_approved_plan_even_when_enabled(tmp_path):
    run = make(tmp_path, run_config=plan(), allow_test_release=True)
    run.validate()
    run.fit(Counter())
    run.select(select_best)
    run.lock()
    with pytest.raises(v2.ReleaseRejected, match='run plan approval_status'):
        run.release_test(authorization(run), TEST, predict)
    assert run.stage == 'D_LOCKED' and ledger(run)['release'] is None


def ledger(run):
    path = run.run_dir / 'ledger.json'
    text = path.read_text()
    parsed = json.loads(text)
    assert text == canonical_json(parsed) + '\n'
    return parsed


class Counter:
    def __init__(self, fail_arm=None, interrupt_job=None):
        self.calls, self.fail_arm, self.interrupt_job = [], fail_arm, interrupt_job

    def __call__(self, job, job_dir):
        self.calls.append(job['job_id'])
        v2.write_artifact_once(job_dir / 'weights.json', canonical_json({'seed': job['seed']}).encode())
        with (job_dir / 'state.npy').open('xb') as stream:
            np.save(stream, np.arange(3) * job['seed'])
        if job['job_id'] == self.interrupt_job:
            raise KeyboardInterrupt('simulated crash mid-job')
        if job['arm'] == self.fail_arm:
            raise FloatingPointError('synthetic divergence')
        return {'validation_loss': 1.0 / job['seed'] + (0.5 if job['arm'] == 'supervised' else 0.)}


def select_best(records):
    succeeded = [r for r in records if r['status'] == 'succeeded']
    best = min(succeeded, key=lambda r: (r['record']['validation_loss'], r['job_id']))
    return {'selected_job_ids': [best['job_id']], 'criterion': 'validation_loss'}


def predict(job, job_dir, output_dir):
    weights = json.loads((job_dir / 'weights.json').read_text())
    v2.write_artifact_once(output_dir / 'forecast.json', canonical_json({'seed': weights['seed']}).encode())
    return {'origins': 7}


def authorization(run, **changes):
    values = dict(approval_status='APPROVED', config_fingerprint=run.plan.config_fingerprint,
                  lock_fingerprint=run.lock_fingerprint, authorized_by='synthetic-custodian',
                  reference='test-only')
    values.update(changes)
    return v2.TestReleaseAuthorization(**values)


def locked(tmp_path, **options):
    run = make(tmp_path, **options)
    run.validate()
    run.fit(Counter())
    run.select(select_best)
    run.lock()
    return run


def test_happy_path_a_to_f_with_canonical_ledger_after_each_step(tmp_path):
    run = make(tmp_path, allow_test_release=True)
    assert run.stage == 'CREATED' and run.run_dir == tmp_path / 'results' / 'v2_runs' / 'run1'
    ledger(run)
    run.validate(lambda identities: {'checked': sorted(identities['split_identities'])})
    assert ledger(run)['stage'] == 'A_VALIDATED'
    fit = Counter()
    run.fit(fit)
    state = ledger(run)
    assert state['stage'] == 'B_FITTED' and len(fit.calls) == 3
    assert all(j['status'] == 'succeeded' for j in state['jobs'].values())
    for job_id, job in state['jobs'].items():
        assert {a['path'] for a in job['artifacts']['files']} == {'weights.json', 'state.npy'}
        assert job['wall_seconds'] >= 0
        verify_artifacts(run.run_dir / 'jobs' / job_id)
    assert [r['job_id'] for r in state['resources']] == fit.calls
    assert state['resources'][0]['process_high_water_mark']['bytes'] > 0
    run.select(select_best)
    best = v2.JobSpec('jepa_finetune', 2, {'epochs': 2}).job_id
    assert ledger(run)['selection']['record']['selected_job_ids'] == [best]
    assert ledger(run)['stage'] == 'C_SELECTED'
    run.lock()
    state = ledger(run)
    assert state['stage'] == 'D_LOCKED' and state['lock']['fingerprint'] == run.lock_fingerprint
    assert run.lock_fingerprint == fingerprint_payload(state['lock']['manifest'])
    assert json.loads((run.run_dir / 'lock.json').read_text()) == state['lock']['manifest']
    predicted = []
    run.release_test(authorization(run), TEST, lambda *a: predicted.append(a[0]['job_id']) or predict(*a))
    state = ledger(run)
    assert state['stage'] == 'E_TEST_RELEASED' and sorted(predicted) == sorted(state['jobs'])
    assert state['release']['test_identity'] == TEST
    assert all(r['status'] == 'succeeded' for r in state['release']['jobs'].values())
    destination = run.publish(contents={'summary.json': {'note': 'synthetic'}})
    state = ledger(run)
    assert state['stage'] == 'F_PUBLISHED' and destination == run.run_dir / 'publication'
    manifest = verify_artifacts(destination)
    assert {f['path'] for f in manifest['files']} == {'summary.json', 'run_ledger.json', 'lock_manifest.json'}
    assert [t['to'] for t in state['transitions']] == list(v2.STAGES[1:])
    assert all(t['utc'].endswith('+00:00') for t in state['transitions'])
    assert state['safeguards'] == {'technically_enforced': list(v2.TECHNICALLY_ENFORCED),
                                   'procedural_only': list(v2.PROCEDURAL_ONLY)}


def test_every_out_of_order_call_raises_invalid_transition(tmp_path):
    run = make(tmp_path, allow_test_release=True)
    for call in (lambda: run.fit(Counter()), lambda: run.select(select_best), run.lock,
                 lambda: run.release_test(None, TEST, predict), lambda: run.publish(contents={'a.json': 1})):
        with pytest.raises(v2.InvalidTransition):
            call()
    run.validate()
    with pytest.raises(v2.InvalidTransition):
        run.validate()
    for call in (lambda: run.select(select_best), run.lock, lambda: run.publish(contents={'a.json': 1})):
        with pytest.raises(v2.InvalidTransition):
            call()
    run.fit(Counter())
    for call in (lambda: run.fit(Counter()), run.lock, lambda: run.release_test(None, TEST, predict)):
        with pytest.raises(v2.InvalidTransition):
            call()
    run.select(select_best)
    run.lock()
    for call in (lambda: run.fit(Counter()), lambda: run.select(select_best), run.lock, run.validate,
                 lambda: run.publish(contents={'a.json': 1})):
        with pytest.raises(v2.InvalidTransition):
            call()
    assert ledger(run)['stage'] == 'D_LOCKED'


def test_release_is_disabled_by_default_even_when_authorized(tmp_path):
    run = locked(tmp_path, run_config=plan(approval_status='APPROVED'))
    calls = []
    with pytest.raises(v2.ReleaseRejected, match='disabled'):
        run.release_test(authorization(run), TEST, lambda *a: calls.append(a))
    assert calls == [] and run.stage == 'D_LOCKED'
    state = ledger(run)
    assert state['release'] is None and state['release_rejections'][-1]['reason'].startswith('test release disabled')
    # A rejected attempt does not consume the single shot.
    enabled = v2.StagedRun(tmp_path, 'run1', plan(approval_status='APPROVED'), allow_test_release=True)
    enabled.release_test(authorization(enabled), TEST, predict)
    assert enabled.stage == 'E_TEST_RELEASED'


@pytest.mark.parametrize('change', [dict(approval_status='PROPOSED_REQUIRES_APPROVAL'),
                                    dict(approval_status='approved'),
                                    dict(config_fingerprint='0' * 64), dict(lock_fingerprint='0' * 64)])
def test_release_rejected_for_unapproved_or_mismatched_authorization(tmp_path, change):
    run = locked(tmp_path, allow_test_release=True)
    calls = []
    with pytest.raises(v2.ReleaseRejected):
        run.release_test(authorization(run, **change), TEST, lambda *a: calls.append(a))
    assert calls == [] and run.stage == 'D_LOCKED' and ledger(run)['release'] is None
    run.release_test(authorization(run), TEST, predict)
    assert run.stage == 'E_TEST_RELEASED'


def test_release_rejects_non_authorization_objects_and_wrong_test_identity(tmp_path):
    run = locked(tmp_path, allow_test_release=True)
    calls = []
    imitation = dict(approval_status='APPROVED', config_fingerprint=run.plan.config_fingerprint,
                     lock_fingerprint=run.lock_fingerprint)
    with pytest.raises(v2.ReleaseRejected):
        run.release_test(imitation, TEST, lambda *a: calls.append(a))
    with pytest.raises(v2.ReleaseRejected, match='test identity'):
        run.release_test(authorization(run), 'e' * 64, lambda *a: calls.append(a))
    assert calls == [] and len(ledger(run)['release_rejections']) == 2


def test_release_rejects_artifact_tampered_after_lock(tmp_path):
    run = locked(tmp_path, allow_test_release=True)
    job_id = sorted(ledger(run)['jobs'])[0]
    target = run.run_dir / 'jobs' / job_id / 'weights.json'
    os.chmod(target, 0o644)
    target.write_text('{"seed":99}')
    calls = []
    with pytest.raises(v2.ArtifactIntegrityError):
        run.release_test(authorization(run), TEST, lambda *a: calls.append(a))
    assert calls == [] and run.stage == 'D_LOCKED' and ledger(run)['release'] is None


def test_release_detects_added_file_and_tampered_lock_file(tmp_path):
    run = locked(tmp_path, allow_test_release=True)
    job_id = sorted(ledger(run)['jobs'])[0]
    (run.run_dir / 'jobs' / job_id / 'extra.json').write_text('{}')
    with pytest.raises(v2.ArtifactIntegrityError):
        run.release_test(authorization(run), TEST, predict)
    (run.run_dir / 'jobs' / job_id / 'extra.json').unlink()
    lock = run.run_dir / 'lock.json'
    os.chmod(lock, 0o644)
    lock.write_text(lock.read_text().replace('"schema_version":1', '"schema_version":2'))
    with pytest.raises(v2.ArtifactIntegrityError):
        run.release_test(authorization(run), TEST, predict)


def test_release_is_single_shot_including_after_a_crash(tmp_path):
    run = locked(tmp_path, allow_test_release=True)
    run.release_test(authorization(run), TEST, predict)
    with pytest.raises(v2.InvalidTransition):
        run.release_test(authorization(run), TEST, predict)
    other = tmp_path / 'other'
    crashed = locked(other, allow_test_release=True)

    def crash(*_):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        crashed.release_test(authorization(crashed), TEST, crash)
    resumed = v2.StagedRun(other, 'run1', plan(approval_status='APPROVED'), allow_test_release=True)
    assert resumed.stage == 'D_LOCKED' and ledger(resumed)['release']['started_utc']
    with pytest.raises(v2.InvalidTransition, match='single-shot'):
        resumed.release_test(authorization(resumed), TEST, predict)


def test_prediction_failures_are_recorded_not_dropped(tmp_path):
    run = locked(tmp_path, allow_test_release=True)

    def flaky(job, job_dir, output_dir):
        if job['arm'] == 'supervised':
            raise ValueError('synthetic prediction failure')
        return predict(job, job_dir, output_dir)
    run.release_test(authorization(run), TEST, flaky)
    release = ledger(run)['release']
    statuses = {ledger(run)['jobs'][k]['spec']['arm']: v['status'] for k, v in release['jobs'].items()}
    assert statuses == {'jepa_finetune': 'succeeded', 'supervised': 'failed'}
    assert any(f['stage'] == 'E_TEST_RELEASED' and f['error_type'] == 'ValueError'
               for f in ledger(run)['failures'])


def test_failed_jobs_are_recorded_and_visible_to_selection(tmp_path):
    run = make(tmp_path)
    run.validate()
    run.fit(Counter(fail_arm='supervised'))
    state = ledger(run)
    failed = [k for k, j in state['jobs'].items() if j['status'] == 'failed']
    assert len(failed) == 1 and state['stage'] == 'B_FITTED'
    failure = [f for f in state['failures'] if f['job_id'] == failed[0]][0]
    assert failure == dict(failure, stage='B_FITTED', error_type='FloatingPointError',
                           message='synthetic divergence')
    seen = []

    def selector(records):
        seen.extend(records)
        with pytest.raises(TypeError):
            records[0]['status'] = 'mutated'
        return select_best(records)
    run.select(selector)
    assert sorted(r['job_id'] for r in seen) == sorted(state['jobs'])
    assert [r['failure']['error_type'] for r in seen if r['status'] == 'failed'] == ['FloatingPointError']
    assert all('test' not in key for r in seen for key in r)
    run.lock()
    assert failed[0] not in {j['job_id'] for j in ledger(run)['lock']['manifest']['jobs']}


def test_selection_must_name_succeeded_jobs(tmp_path):
    run = make(tmp_path)
    run.validate()
    run.fit(Counter(fail_arm='supervised'))
    failed = [k for k, j in ledger(run)['jobs'].items() if j['status'] == 'failed']
    with pytest.raises(ValueError):
        run.select(lambda records: {'selected_job_ids': failed})
    with pytest.raises(ValueError):
        run.select(lambda records: {'selected_job_ids': []})
    assert run.stage == 'B_FITTED'


@pytest.mark.parametrize('change', [dict(config={'lr': 0.02, 'schedule': [1, 2]}),
                                    dict(dataset_fingerprint='f' * 64),
                                    dict(split_identities={'train': 'a' * 64, 'validation': 'f' * 64}),
                                    dict(test_identity='f' * 64),
                                    dict(jobs=jobs()[:2]),
                                    dict(approval_status='APPROVED')])
def test_resume_with_changed_identity_is_rejected(tmp_path, change):
    run = make(tmp_path)
    run.validate()
    with pytest.raises(v2.IdentityMismatch):
        make(tmp_path, plan(**change))
    assert make(tmp_path).stage == 'A_VALIDATED'


def test_resume_skips_succeeded_and_quarantines_interrupted_job(tmp_path):
    run = make(tmp_path)
    run.validate()
    order = [j.job_id for j in run.plan.jobs]
    first = Counter(interrupt_job=order[1])
    with pytest.raises(KeyboardInterrupt):
        run.fit(first)
    assert first.calls == order[:2]
    state = ledger(run)
    assert state['jobs'][order[0]]['status'] == 'succeeded'
    assert state['jobs'][order[1]]['status'] == 'pending' and state['stage'] == 'A_VALIDATED'
    resumed = make(tmp_path)
    second = Counter()
    resumed.fit(second)
    assert second.calls == order[1:]
    state = ledger(resumed)
    assert state['stage'] == 'B_FITTED'
    quarantine = state['quarantines']
    assert len(quarantine) == 1 and quarantine[0]['job_id'] == order[1]
    moved = resumed.run_dir / quarantine[0]['path']
    assert (moved / 'weights.json').is_file() and moved.parent.name == 'quarantine'
    assert [a['outcome'] for a in state['jobs'][order[1]]['attempts']] == ['interrupted', 'succeeded']
    verify_artifacts(resumed.run_dir / 'jobs' / order[1])


def test_resume_refuses_when_succeeded_artifact_changed(tmp_path):
    run = make(tmp_path)
    run.validate()
    order = [j.job_id for j in run.plan.jobs]
    with pytest.raises(KeyboardInterrupt):
        run.fit(Counter(interrupt_job=order[1]))
    target = run.run_dir / 'jobs' / order[0] / 'state.npy'
    os.chmod(target, 0o644)
    target.write_bytes(b'tampered')
    calls = Counter()
    with pytest.raises(v2.ArtifactIntegrityError):
        make(tmp_path).fit(calls)
    assert calls.calls == []


def test_job_ids_and_names_are_deterministic_and_order_independent(tmp_path):
    forward, backward = plan(), plan(jobs=jobs(-1))
    assert forward.fingerprint == backward.fingerprint
    assert [j.job_id for j in forward.jobs] == [j.job_id for j in backward.jobs]
    spec = v2.JobSpec('supervised', 1, {'epochs': 2})
    assert spec.job_id == 'supervised-s1-' + fingerprint_payload(
        {'arm': 'supervised', 'seed': 1, 'parameters': {'epochs': 2}})[:12]
    assert v2.JobSpec('supervised', 1, {'epochs': 3}).job_id != spec.job_id
    one, two = make(tmp_path / 'a'), make(tmp_path / 'b', backward)
    for run in (one, two):
        run.validate()
        run.fit(Counter())
    assert sorted(p.name for p in (one.run_dir / 'jobs').iterdir()) == \
        sorted(p.name for p in (two.run_dir / 'jobs').iterdir())
    with pytest.raises(ValueError, match='duplicate'):
        plan(jobs=(spec, v2.JobSpec('supervised', 1, {'epochs': 2})))


def test_publication_refuses_existing_destination(tmp_path):
    run = locked(tmp_path, allow_test_release=True)
    run.release_test(authorization(run), TEST, predict)
    (run.run_dir / 'publication').mkdir()
    with pytest.raises(FileExistsError):
        run.publish(contents={'summary.json': {'a': 1}})
    assert run.stage == 'E_TEST_RELEASED'
    assert not any(p.name.startswith('.stage-') for p in run.run_dir.iterdir())
    with pytest.raises(ValueError):
        run.publish(contents={'artifacts.json': {}})
    with pytest.raises(ValueError):
        run.publish(contents={'../escape.json': {}})


def test_publish_fn_receives_snapshot(tmp_path):
    run = locked(tmp_path, allow_test_release=True)
    run.release_test(authorization(run), TEST, predict)
    destination = run.publish(lambda snapshot: {'release.json': {'jobs': sorted(snapshot['release']['jobs'])}})
    assert json.loads((destination / 'release.json').read_text())['jobs'] == sorted(ledger(run)['jobs'])


def test_failing_or_raising_hook_blocks_transition_and_is_recorded(tmp_path):
    run = make(tmp_path)
    snapshots = []

    def failing(snapshot):
        snapshots.append(snapshot)
        with pytest.raises(TypeError):
            snapshot['stage'] = 'F_PUBLISHED'
        return {'hook_id': 'neal.split_check', 'version': '0.1', 'passed': False, 'details': {'why': 'synthetic'}}
    run.register_hook('A_VALIDATED', failing)
    with pytest.raises(v2.ValidationHookFailed):
        run.validate()
    state = ledger(run)
    assert state['stage'] == 'CREATED'
    assert state['hooks'][-1]['result']['passed'] is False and state['hooks'][-1]['stage'] == 'A_VALIDATED'
    assert snapshots[0]['proposed_transition']['to'] == 'A_VALIDATED'

    def raising(snapshot):
        raise RuntimeError('validator crashed')
    other = make(tmp_path / 'x')
    other.register_hook('A_VALIDATED', raising)
    with pytest.raises(v2.ValidationHookFailed):
        other.validate()
    assert ledger(other)['hooks'][-1]['result']['passed'] is False
    with pytest.raises(ValueError):
        run.register_hook('CREATED', failing)
    passing = make(tmp_path / 'y')
    passing.register_hook('A_VALIDATED', lambda s: {'hook_id': 'ok', 'version': '1', 'passed': True, 'details': {}})
    passing.register_hook('B_FITTED', lambda s: {'hook_id': 'bad', 'version': '1', 'passed': 'yes', 'details': {}})
    passing.validate()
    with pytest.raises(v2.ValidationHookFailed):
        passing.fit(Counter())
    assert ledger(passing)['stage'] == 'A_VALIDATED'


def test_rss_ceiling_stops_further_jobs_with_recorded_failure(tmp_path):
    run = make(tmp_path, max_rss_bytes=1)
    run.validate()
    fit = Counter()
    run.fit(fit)
    state = ledger(run)
    assert len(fit.calls) == 1 and state['stage'] == 'A_VALIDATED'
    assert [j['status'] for j in state['jobs'].values()].count('pending') == 2
    resource = [f for f in state['failures'] if f['error_type'] == 'ResourceCeilingExceeded']
    assert len(resource) == 1 and resource[0]['stage'] == 'B_FITTED' and resource[0]['job_id'] is None
    with pytest.raises(v2.InvalidTransition):
        run.select(select_best)
    resumed = make(tmp_path)
    more = Counter()
    resumed.fit(more)
    assert len(more.calls) == 2 and resumed.stage == 'B_FITTED'


def test_validation_refuses_empty_jobs_and_records_check_failure(tmp_path):
    with pytest.raises(ValueError, match='job'):
        make(tmp_path, plan(jobs=())).validate()
    run = make(tmp_path / 'x')

    def check(identities):
        assert 'test_identity' not in identities
        raise ValueError('split overlap')
    with pytest.raises(ValueError, match='split overlap'):
        run.validate(check)
    state = ledger(run)
    assert state['stage'] == 'CREATED' and state['failures'][-1]['stage'] == 'A_VALIDATED'


def test_plan_is_immutable_and_rejects_test_like_split_declarations():
    config = {'lr': 0.01}
    run_config = plan(config=config)
    config['lr'] = 1.0
    copy = run_config.config
    copy['lr'] = 2.0
    assert run_config.config == {'lr': 0.01}
    assert run_config.config_fingerprint == fingerprint_payload({'lr': 0.01})
    with pytest.raises(AttributeError):
        run_config.test_identity = 'x'
    assert run_config.approval_status == 'PROPOSED_REQUIRES_APPROVAL'
    with pytest.raises(ValueError):
        plan(split_identities={'train': 'a', 'validation': 'b', 'test': 'c'})
    with pytest.raises(ValueError):
        plan(split_identities={'train': 'a'})
    with pytest.raises(ValueError):
        plan(test_identity=SPLITS['train'])
    with pytest.raises(ValueError):
        plan(config={'x': float('nan')})


def test_fit_record_must_be_finite_json(tmp_path):
    run = make(tmp_path)
    run.validate()
    run.fit(lambda job, job_dir: {'loss': float('nan')})
    state = ledger(run)
    assert all(j['status'] == 'failed' for j in state['jobs'].values())
    assert {f['error_type'] for f in state['failures']} == {'ValueError'}


def test_unknown_run_directory_without_ledger_is_refused(tmp_path):
    (tmp_path / 'results' / 'v2_runs' / 'run1').mkdir(parents=True)
    with pytest.raises(FileExistsError):
        make(tmp_path)
    with pytest.raises(ValueError):
        v2.StagedRun(tmp_path, '../escape', plan())


def test_process_high_water_mark_is_normalized_and_labeled():
    record = v2.process_high_water_mark()
    assert record['label'] == 'process_high_water_mark' and record['bytes'] > 1_000_000
    assert record['raw_unit'] in ('bytes', 'kilobytes')


def test_same_test_identity_cannot_be_released_by_a_second_run(tmp_path):
    first = locked(tmp_path, allow_test_release=True)
    first.release_test(authorization(first), TEST, predict)
    second = v2.StagedRun(tmp_path, 'run2', plan(approval_status='APPROVED'), allow_test_release=True)
    second.validate()
    second.fit(Counter())
    second.select(select_best)
    second.lock()
    calls = []
    with pytest.raises(v2.ReleaseRejected, match='already released'):
        second.release_test(authorization(second), TEST, lambda *a: calls.append(a))
    assert calls == [] and second.stage == 'D_LOCKED'


def test_resume_with_different_provenance_is_rejected(tmp_path):
    run = make(tmp_path, provenance={'code': 'abc'})
    run.validate()
    for changed in ({'code': 'different'}, None):
        with pytest.raises(v2.IdentityMismatch, match='provenance'):
            make(tmp_path, provenance=changed)
    assert make(tmp_path, provenance={'code': 'abc'}).stage == 'A_VALIDATED'
