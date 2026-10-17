"""Synthetic cancellation/recovery probes; no science, models or approvals."""
import json
import os
from pathlib import Path
import signal
import select
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]


def wait_for(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.01)
    raise AssertionError('Synthetic handshake did not complete')


def group_live(pid):
    from solar_flare_jepa.experiments.v2_resource_controls import _processes
    return any(r['group'] == pid and not r['state'].startswith('Z') for r in _processes())


def stop_group(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    wait_for(lambda: not group_live(pid))


def launch_supervisor(tmp_path, *, spawn_signal=False, deadline=False):
    worker = ("import os,signal,time;from pathlib import Path;"
              "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
              "Path('ready').write_text(str(os.getpid()));time.sleep(60)")
    script = '''
import json,os,signal,subprocess,sys,time
from pathlib import Path
from solar_flare_jepa.experiments import v2_pilot as p
from solar_flare_jepa.experiments.v2_resource_controls import ProcessJob,ResourceLimits
base=Path(sys.argv[1]);worker=sys.argv[2]
jobs=[ProcessJob('00-worker',(sys.executable,'-c',worker),30),
      ProcessJob('01-pending',(sys.executable,'-c',"raise AssertionError('must not launch')"),2)]
runner=p.PilotSupervisor(base/'supervisor',jobs,code_fingerprint='synthetic',
 config_fingerprint='synthetic',limits=ResourceLimits(256*1024**2,40,1,0,.01),minimum_free_bytes=1)
sample=runner._sample_rss
def ready(pid):
 if (base/'supervisor/attempts/00-worker-1/artifacts/ready').exists():
  (base/'ready').write_text(str(pid))
 return sample(pid)
runner._sample_rss=ready
if sys.argv[3]=='spawn':
 original=subprocess.Popen
 def popen(*a,**kw):
  process=original(*a,**kw)
  if kw.get('start_new_session'):
   (base/'spawned').write_text(str(process.pid))
   os.kill(os.getpid(),signal.SIGTERM)
  return process
 subprocess.Popen=popen
try:
 if sys.argv[3]=='deadline':
  with p._deadline(.5): runner.run()
 else: runner.run()
except BaseException as error:
 (base/'error.json').write_text(json.dumps(dict(type=type(error).__name__,message=str(error))))
'''
    mode = 'spawn' if spawn_signal else 'deadline' if deadline else 'ordinary'
    process = subprocess.Popen([sys.executable, '-c', script, str(tmp_path), worker, mode],
                               env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process


@pytest.mark.parametrize('signum', [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])
def test_supervisor_only_signal_stops_owned_group_and_never_starts_next(tmp_path, signum):
    process = launch_supervisor(tmp_path)
    pid = None
    try:
        pid = int(wait_for(lambda: (tmp_path / 'ready').read_text() if (tmp_path / 'ready').exists() else None))
        os.kill(process.pid, signum)
        out, err = process.communicate(timeout=8)
        assert not group_live(pid), f'supervisor exited {process.returncode}, worker group survived: {err}'
        ledger = json.loads((tmp_path / 'supervisor/supervisor.json').read_text())
        assert len(ledger['attempts']) == 1
        assert ledger['attempts'][0]['status'] == 'failed'
        assert ledger['jobs']['01-pending']['status'] == 'pending'
        assert (tmp_path / 'error.json').exists()
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=8)
        if pid is not None:
            stop_group(pid)


def test_signal_between_spawn_and_assignment_cannot_orphan_worker(tmp_path):
    process = launch_supervisor(tmp_path, spawn_signal=True)
    pid = None
    try:
        pid = int(wait_for(lambda: (tmp_path / 'spawned').read_text() if (tmp_path / 'spawned').exists() else None))
        out, err = process.communicate(timeout=8)
        assert not group_live(pid), f'spawn gap leaked process: {err}'
        state = json.loads((tmp_path / 'supervisor/supervisor.json').read_text())
        assert len(state['attempts']) == 1
        assert state['attempts'][0]['pid'] == pid
        assert state['jobs']['01-pending']['status'] == 'pending'
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=8)
        if pid is not None:
            stop_group(pid)


def test_twenty_synthetic_pilot_attempts_pass_actual_closed_report_schema(tmp_path):
    """Ownership sidecars must not contaminate scientific report schemas."""
    from test_v2_pilot_reporting import fixture
    from solar_flare_jepa.experiments.v2_pilot import PilotSupervisor
    from solar_flare_jepa.experiments.v2_pilot_reporting import build_report
    from solar_flare_jepa.experiments.v2_resource_controls import ProcessJob, ResourceLimits
    design, payloads, accounting = fixture()
    jobs = [ProcessJob(job['job_id'], (sys.executable, '-c',
        "from pathlib import Path;Path('synthetic.txt').write_text('synthetic')"), job['timeout_seconds'])
        for job in design['jobs']]
    runner = PilotSupervisor(tmp_path / 'supervisor', jobs, minimum_free_bytes=1,
        code_fingerprint='synthetic-code', config_fingerprint='synthetic-config',
        limits=ResourceLimits(2147483648, 7200, 4, 0, .05))
    runner._ledger['consumed_wall_seconds'] = 1.
    runner._save()
    began = time.monotonic()
    ledger = runner.run()
    elapsed = time.monotonic() - began
    accounting.update(supervisor=ledger, wall_seconds=dict(preparation=1., supervision=elapsed,
        finalization=1., total=2. + elapsed))
    assert len(build_report(design, payloads, accounting=accounting)['models']) == 18
    assert len(ledger['attempts']) == 20
    assert all(a['status'] == 'succeeded' for a in ledger['attempts'])
    with pytest.raises(ValueError, match='resum'):
        runner.run()


def test_confirmed_exit_during_identity_inspection_is_not_a_live_mismatch(monkeypatch):
    from solar_flare_jepa.experiments import v2_pilot_lifecycle as lifecycle
    token = 'a' * 64
    read_fd, write_fd = os.pipe()
    child = subprocess.Popen([sys.executable, '-c',
        'import os,signal,sys;os.write(int(sys.argv[1]),b"ready");signal.pause()', str(write_fd)],
        pass_fds=(write_fd,), start_new_session=True,
        env=dict(os.environ, **{lifecycle.OWNER_ENV: token}))
    os.close(write_fd)
    original = lifecycle._metadata
    observations = []
    def exit_after_token_read(pid):
        if observations:
            child.kill()
            child.wait(timeout=3)
        value = original(pid)
        observations.append(value)
        return value
    try:
        assert select.select([read_fd], [], [], 3)[0]
        assert os.read(read_fd, 5) == b'ready'
        monkeypatch.setattr(lifecycle, '_metadata', exit_after_token_read)
        assert lifecycle.read_process_identity(child.pid, token) is None
        assert observations[0] is not None and observations[1] is None
    finally:
        os.close(read_fd)
        if child.poll() is None:
            child.kill()
        child.wait(timeout=3)


def test_live_identity_error_remains_terminal_even_if_worker_then_exits(monkeypatch, tmp_path):
    from solar_flare_jepa.experiments import v2_pilot as pilot
    from solar_flare_jepa.experiments.v2_resource_controls import (
        ProcessJob, ResourceLimits, SupervisionIntegrityError,
    )
    spawned = []
    original = subprocess.Popen
    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        spawned.append(process)
        return process
    def mismatch_then_exit(pid, token):
        assert spawned[0].pid == pid
        spawned[0].wait(timeout=3)
        raise SupervisionIntegrityError('observed live identity mismatch')
    monkeypatch.setattr(subprocess, 'Popen', capture)
    monkeypatch.setattr(pilot, 'read_process_identity', mismatch_then_exit)
    jobs = [ProcessJob('00-fast', (sys.executable, '-c', 'pass'), 3),
            ProcessJob('01-pending', (sys.executable, '-c', 'pass'), 3)]
    runner = pilot.PilotSupervisor(tmp_path / 'supervisor', jobs, minimum_free_bytes=1,
        code_fingerprint='synthetic', config_fingerprint='synthetic',
        limits=ResourceLimits(1024**3, 10, 1, 0))
    with pytest.raises(SupervisionIntegrityError, match='observed live identity mismatch'):
        runner.run()
    assert runner._ledger['jobs']['00-fast']['status'] == 'failed'
    assert runner._ledger['jobs']['01-pending']['status'] == 'pending'
    assert len(runner._ledger['attempts']) == 1
