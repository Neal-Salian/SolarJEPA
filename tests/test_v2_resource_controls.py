"""Synthetic subprocesses only: no model, data or pilot execution."""
import importlib.util
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import signal
import sys
import time

import pytest


def test_resource_supervisor_public_api_exists():
    assert importlib.util.find_spec('solar_flare_jepa.experiments.v2_resource_controls') is not None


@pytest.fixture
def controls():
    name = 'solar_flare_jepa.experiments.v2_resource_controls'
    assert importlib.util.find_spec(name) is not None, 'Resource supervisor is not implemented'
    return __import__(name, fromlist=['ResourceLimits'])


def command(code):
    return (sys.executable, '-c', code)


def limits(controls, **changes):
    values = dict(max_rss_bytes=256 * 1024**2, total_wall_seconds=5.0,
                  threads=4, max_retries=1, poll_interval_seconds=0.02)
    return controls.ResourceLimits(**dict(values, **changes))


def supervisor(controls, tmp_path, jobs, **changes):
    values = dict(code_fingerprint='code-fixture', config_fingerprint='config-fixture',
                  limits=limits(controls))
    return controls.ProcessSupervisor(tmp_path / 'supervision', jobs, **dict(values, **changes))


def test_success_is_ordered_isolated_thread_limited_and_sealed(controls, tmp_path):
    code = ('import json, os, pathlib; '
            'pathlib.Path("result.json").write_text(json.dumps(dict('
            'threads={k:os.environ[k] for k in '
            '["OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",'
            '"NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"]},pid=os.getpid()))); '
            'print("stdout evidence"); print("stderr evidence",file=__import__("sys").stderr)')
    jobs = [controls.ProcessJob('z-job', command(code), timeout_seconds=1),
            controls.ProcessJob('a-job', command(code), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    state = runner.run()
    assert state['execution_order'] == ['a-job', 'z-job']
    assert [a['job_id'] for a in state['attempts']] == state['execution_order']
    assert all(j['status'] == 'succeeded' for j in state['jobs'].values())
    pids = []
    for job in state['jobs'].values():
        directory = runner.directory / job['artifact_path']
        result = json.loads((directory / 'result.json').read_text())
        assert set(result['threads'].values()) == {'4'}
        assert (directory / 'artifacts.json').is_file()
        assert not ((directory / 'result.json').stat().st_mode & 0o222)
        pids.append(result['pid'])
    assert len(set(pids)) == 2 and os.getpid() not in pids
    attempt = state['attempts'][0]
    assert 'stdout evidence' in (runner.directory / attempt['path'] / 'stdout.log').read_text()
    assert 'stderr evidence' in (runner.directory / attempt['path'] / 'stderr.log').read_text()
    assert state['consumed_wall_seconds'] > 0
    resumed = supervisor(controls, tmp_path, reversed(jobs)).run()
    assert resumed == state


@pytest.mark.parametrize('changes', [dict(max_retries=2), dict(max_retries=True),
                                   dict(max_rss_bytes=0), dict(max_rss_bytes=True),
                                   dict(max_rss_bytes=4*1024**3+1),
                                   dict(threads=0), dict(threads=5),
                                   dict(total_wall_seconds=float('inf')),
                                   dict(poll_interval_seconds=0)])
def test_invalid_or_excessive_resource_limits_are_rejected(controls, changes):
    with pytest.raises(ValueError):
        limits(controls, **changes)


@pytest.mark.parametrize('changes', [dict(job_id='../escape'), dict(command=[]),
                                   dict(timeout_seconds=0), dict(timeout_seconds=True)])
def test_job_declarations_are_explicit_and_safe(controls, changes):
    values = dict(job_id='job', command=command('pass'), timeout_seconds=1)
    with pytest.raises((ValueError, TypeError)):
        controls.ProcessJob(**dict(values, **changes))


def test_timeout_stops_process_and_allows_at_most_one_identical_retry(controls, tmp_path):
    job = controls.ProcessJob('sleep', command('import pathlib,time; pathlib.Path("partial").write_text("x"); time.sleep(5)'),
                              timeout_seconds=0.15)
    runner = supervisor(controls, tmp_path, [job])
    started = time.monotonic()
    state = runner.run()
    assert time.monotonic() - started < 3
    assert state['jobs']['sleep']['status'] == 'failed'
    assert [a['failure_kind'] for a in state['attempts']] == ['TIMEOUT', 'TIMEOUT']
    assert len({a['job_fingerprint'] for a in state['attempts']}) == 1
    assert all(a['path'].startswith('quarantine/') for a in state['attempts'])
    assert all((runner.directory / a['path'] / 'artifacts' / 'partial').read_text() == 'x'
               for a in state['attempts'])
    assert len(supervisor(controls, tmp_path, [job]).run()['attempts']) == 2


def test_nonzero_numeric_failure_is_terminal_and_keeps_logs(controls, tmp_path):
    job = controls.ProcessJob('numeric', command('import sys; print("nonfinite loss",file=sys.stderr); sys.exit(2)'),
                              timeout_seconds=1)
    runner = supervisor(controls, tmp_path, [job])
    state = runner.run()
    assert state['jobs']['numeric']['status'] == 'failed'
    assert len(state['attempts']) == 1
    assert state['attempts'][0]['failure_kind'] == 'JOB_EXIT'
    assert 'nonfinite loss' in (runner.directory / state['attempts'][0]['path'] / 'stderr.log').read_text()


def test_total_budget_includes_retry_and_remains_exhausted_on_resume(controls, tmp_path):
    jobs = [controls.ProcessJob('a-sleep', command('import time; time.sleep(5)'), timeout_seconds=0.15),
            controls.ProcessJob('z-never', command('raise AssertionError("must never start")'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs,
                        limits=limits(controls, total_wall_seconds=0.24))
    state = runner.run()
    assert state['stop_reason'] == 'TOTAL_WALL_BUDGET'
    assert state['jobs']['z-never']['status'] == 'pending'
    assert state['attempts'][-1]['failure_kind'] == 'TOTAL_WALL_BUDGET'
    assert state['consumed_wall_seconds'] >= 0.24
    assert supervisor(controls, tmp_path, jobs,
                      limits=limits(controls, total_wall_seconds=0.24)).run() == state


def test_sampled_rss_covers_child_processes(controls, tmp_path):
    child = 'import time; x=bytearray(48*1024**2); time.sleep(5)'
    code = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(5)'
    job = controls.ProcessJob('memory', command(code), timeout_seconds=2)
    state = supervisor(controls, tmp_path, [job],
                       limits=limits(controls, max_rss_bytes=40*1024**2, max_retries=0)).run()
    assert state['attempts'][0]['failure_kind'] == 'RSS_CEILING'
    assert state['attempts'][0]['peak_sampled_rss_bytes'] > 40*1024**2
    assert state['jobs']['memory']['status'] == 'failed'


@pytest.mark.parametrize('field', ['code', 'config', 'resource', 'job'])
def test_resume_refuses_changed_execution_identity(controls, tmp_path, field):
    jobs = [controls.ProcessJob('job', command('pass'), timeout_seconds=1)]
    supervisor(controls, tmp_path, jobs).run()
    changes = {'code': dict(code_fingerprint='other'), 'config': dict(config_fingerprint='other'),
               'resource': dict(limits=limits(controls, total_wall_seconds=6)), 'job': {}}[field]
    if field == 'job':
        jobs = [controls.ProcessJob('job', command('print(1)'), timeout_seconds=1)]
    with pytest.raises(controls.SupervisionIdentityError):
        supervisor(controls, tmp_path, jobs, **changes)


def test_resume_verifies_successful_artifact_bytes(controls, tmp_path):
    jobs = [controls.ProcessJob('job', command('from pathlib import Path; Path("out").write_text("original")'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    state = runner.run()
    output = runner.directory / state['jobs']['job']['artifact_path'] / 'out'
    output.chmod(0o644)
    output.write_text('changed')
    with pytest.raises(controls.SupervisionIntegrityError):
        supervisor(controls, tmp_path, jobs)


def test_refuses_unrelated_directory_and_symlink_artifact(controls, tmp_path):
    directory = tmp_path / 'supervision'
    directory.mkdir()
    unrelated = directory / 'keep'
    unrelated.write_text('user bytes')
    job = controls.ProcessJob('job', command('pass'), timeout_seconds=1)
    with pytest.raises(FileExistsError):
        supervisor(controls, tmp_path, [job])
    assert unrelated.read_text() == 'user bytes'
    other = tmp_path / 'other'
    job = controls.ProcessJob('job', command('from pathlib import Path; Path("link").symlink_to("/etc/hosts")'), timeout_seconds=1)
    state = supervisor(controls, other, [job]).run()
    assert state['jobs']['job']['status'] == 'failed'
    assert state['attempts'][0]['failure_kind'] == 'ARTIFACT_INTEGRITY'
    assert len(state['attempts']) == 1


def test_interruption_is_logged_quarantined_and_resumed_within_retry_limit(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('job', command('import time; time.sleep(.1)'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    original = runner._sample_rss
    def interrupt(_):
        raise KeyboardInterrupt
    monkeypatch.setattr(runner, '_sample_rss', interrupt)
    with pytest.raises(KeyboardInterrupt):
        runner.run()
    state = json.loads((runner.directory / 'supervisor.json').read_text())
    assert state['attempts'][0]['failure_kind'] == 'INTERRUPTED'
    assert state['attempts'][0]['path'].startswith('quarantine/')
    resumed = supervisor(controls, tmp_path, jobs).run()
    assert len(resumed['attempts']) == 2 and resumed['jobs']['job']['status'] == 'succeeded'


def test_rss_backend_failure_stops_without_unmonitored_retry(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('job', command('import time; time.sleep(5)'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    def unavailable(_):
        raise controls.ResourceMonitoringUnavailable('synthetic ps failure')
    monkeypatch.setattr(runner, '_sample_rss', unavailable)
    state = runner.run()
    assert state['stop_reason'] == 'MONITOR_UNAVAILABLE'
    assert len(state['attempts']) == 1
    assert state['attempts'][0]['failure_kind'] == 'MONITOR_UNAVAILABLE'


def test_total_budget_accounts_for_slow_artifact_sealing_before_next_job(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('a-job', command('pass'), timeout_seconds=1),
            controls.ProcessJob('z-job', command('pass'), timeout_seconds=1)]
    original = controls._seal
    called = []
    def slow_seal(directory):
        called.append(directory)
        time.sleep(1.1)
        return original(directory)
    monkeypatch.setattr(controls, '_seal', slow_seal)
    runner = supervisor(controls, tmp_path, jobs, limits=limits(controls, total_wall_seconds=1))
    state = runner.run()
    assert len(called) == 1
    assert state['consumed_wall_seconds'] >= 1.1
    assert state['stop_reason'] == 'TOTAL_WALL_BUDGET'
    assert state['jobs']['z-job']['status'] == 'pending'
    assert len(state['attempts']) == 1


def test_total_budget_accounts_for_active_resume_validation(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('job', command('pass'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs, limits=limits(controls, total_wall_seconds=.1))
    original = runner._validate_ledger
    def slow_validation():
        time.sleep(.15)
        return original()
    monkeypatch.setattr(runner, '_validate_ledger', slow_validation)
    state = runner.run()
    assert state['consumed_wall_seconds'] >= .15
    assert state['stop_reason'] == 'TOTAL_WALL_BUDGET'
    assert state['attempts'] == []


@pytest.mark.parametrize('mutation', ['unknown_job', 'unsafe_path', 'unknown_status', 'false_success'])
def test_resume_rejects_malformed_attempts_before_recovery(controls, tmp_path, mutation):
    jobs = [controls.ProcessJob('job', command('pass'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    state = runner.run()
    attempt = state['attempts'][0]
    if mutation == 'unknown_job':
        attempt['job_id'] = 'undeclared'
    elif mutation == 'unsafe_path':
        attempt['status'] = 'running'
        attempt['path'] = '../../user-directory'
        state['jobs']['job']['status'] = 'pending'
    elif mutation == 'unknown_status':
        attempt['status'] = 'arbitrary'
    elif mutation == 'false_success':
        attempt['status'] = 'failed'
    (runner.directory / 'supervisor.json').write_text(json.dumps(state))
    with pytest.raises(controls.SupervisionIntegrityError):
        supervisor(controls, tmp_path, jobs)


def test_numerical_signal_does_not_receive_infrastructure_retry(controls, tmp_path):
    job = controls.ProcessJob('numerical', command('import os,signal; os.kill(os.getpid(),signal.SIGFPE)'), timeout_seconds=1)
    state = supervisor(controls, tmp_path, [job]).run()
    assert len(state['attempts']) == 1
    assert state['jobs']['numerical']['status'] == 'failed'


def test_same_supervisor_resumes_after_interruption_without_charging_idle_time(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('job', command('pass'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    original = runner._sample_rss
    monkeypatch.setattr(runner, '_sample_rss', lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        runner.run()
    assert runner._wall_checkpoint is None
    monkeypatch.setattr(runner, '_sample_rss', original)
    state = runner.run()
    assert state['jobs']['job']['status'] == 'succeeded'
    assert runner._wall_checkpoint is None


def test_termination_failure_preserves_running_partial_and_refuses_unsafe_resume(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('job', command('import time;time.sleep(5)'), timeout_seconds=.1)]
    runner = supervisor(controls, tmp_path, jobs)
    original = runner._terminate
    def fail_stop(process):
        # Stop the synthetic worker for test hygiene, then simulate an inability
        # to establish termination. The supervisor must preserve unresolved state.
        original(process)
        raise controls.ResourceMonitoringUnavailable('synthetic unresolved termination')
    monkeypatch.setattr(runner, '_terminate', fail_stop)
    with pytest.raises(controls.ResourceMonitoringUnavailable):
        runner.run()
    state = json.loads((runner.directory / 'supervisor.json').read_text())
    assert state['stop_reason'] == 'MONITOR_UNAVAILABLE'
    assert state['attempts'][0]['status'] == 'running'
    assert state['attempts'][0]['error'] == 'synthetic unresolved termination'
    assert (runner.directory / state['attempts'][0]['path']).is_dir()


def test_refuses_symlinked_attempt_storage_before_worker_start(controls, tmp_path):
    jobs = [controls.ProcessJob('job', command('pass'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    outside = tmp_path / 'unrelated'
    outside.mkdir()
    (runner.directory / 'attempts').symlink_to(outside, target_is_directory=True)
    with pytest.raises(controls.SupervisionIntegrityError):
        runner.run()
    assert list(outside.iterdir()) == []


def test_persisted_running_attempt_recovery_charges_downtime_and_keeps_retry_cap(controls, tmp_path, monkeypatch):
    jobs = [controls.ProcessJob('job', command('import time; time.sleep(.02)'), timeout_seconds=1)]
    runner = supervisor(controls, tmp_path, jobs)
    original = runner._terminate
    def unresolved(process):
        original(process)
        raise controls.ResourceMonitoringUnavailable('synthetic crash point')
    monkeypatch.setattr(runner, '_terminate', unresolved)
    with pytest.raises(controls.ResourceMonitoringUnavailable):
        runner.run()
    path = runner.directory / 'supervisor.json'
    state = json.loads(path.read_text())
    state['stop_reason'] = None
    state['attempts'][0].update(failure_kind=None, error=None,
        checkpoint_utc=(datetime.now(timezone.utc)-timedelta(seconds=.2)).isoformat())
    path.write_text(json.dumps(state))
    consumed = state['consumed_wall_seconds']
    resumed = supervisor(controls, tmp_path, jobs).run()
    assert resumed['consumed_wall_seconds'] >= consumed + .2
    assert [a['failure_kind'] for a in resumed['attempts']] == ['INTERRUPTED', None]
    assert resumed['attempts'][0]['path'].startswith('quarantine/')
    assert resumed['jobs']['job']['status'] == 'succeeded'
    assert len(supervisor(controls, tmp_path, jobs).run()['attempts']) == 2


def test_racing_initializers_cannot_replace_another_execution_plan(controls, tmp_path, monkeypatch):
    job = controls.ProcessJob('job', command('pass'), timeout_seconds=1)
    original = controls.ProcessSupervisor._save
    barrier = Barrier(2)
    def synchronized_save(self, *args, **kwargs):
        barrier.wait(timeout=2)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(controls.ProcessSupervisor, '_save', synchronized_save)
    def initialize(identity):
        try:
            return supervisor(controls, tmp_path, [job], code_fingerprint=identity)
        except FileExistsError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(initialize, ['code-a', 'code-b']))
    assert sum(result is not None for result in results) == 1
    winner = next(result for result in results if result is not None)
    state = json.loads((winner.directory / 'supervisor.json').read_text())
    assert state['plan']['code_fingerprint'] == winner.plan['code_fingerprint']


def test_unknown_spawn_state_blocks_resume_instead_of_launching_retry(controls, tmp_path):
    job = controls.ProcessJob('job', command('pass'), timeout_seconds=1)
    runner = supervisor(controls, tmp_path, [job])
    state = runner.run()
    # The supervisor can crash after spawn but before persisting the child PID.
    # A null PID does not prove that no worker survived.
    state['attempts'][0].update(status='running', pid=None, failure_kind=None, error=None)
    state['jobs']['job'].update(status='pending', artifact_path=None, artifacts=None)
    (runner.directory / 'supervisor.json').write_text(json.dumps(state))
    with pytest.raises(controls.SupervisionIntegrityError, match='spawn state'):
        supervisor(controls, tmp_path, [job]).run()
    assert len(json.loads((runner.directory / 'supervisor.json').read_text())['attempts']) == 1
