"""Adversarial pilot lifecycle checks with synthetic processes only.

The subprocess fixtures never load scientific inputs or invoke the scientific
worker. Each fixture owns a fresh session; cleanup targets only those sessions.
"""
import json
import os
from pathlib import Path
import signal
import select
import subprocess
import sys
import threading
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(sys.platform not in ('darwin', 'linux'), reason='Unix process groups')

_WORKER = r'''
import json, os, signal, subprocess, sys
from pathlib import Path
root, mode = Path(sys.argv[1]), sys.argv[2]
def term(signum, frame):
    (root / 'term-observed').touch()
signal.signal(signal.SIGTERM, term)
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
read_fd, write_fd = os.pipe()
child_code = ''' + repr(r'''
import os, signal, sys
signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
os.write(int(sys.argv[1]), str(os.getpid()).encode())
os.close(int(sys.argv[1]))
while True: signal.pause()
''') + r'''
child = subprocess.Popen([sys.executable, '-c', child_code, str(write_fd), str(root)], pass_fds=(write_fd,))
os.close(write_fd)
assert int(os.read(read_fd, 64)) == child.pid
os.close(read_fd)
ready = dict(worker=os.getpid(), child=child.pid, group=os.getpgrp())
(root / 'ready-tmp').write_text(json.dumps(ready))
os.replace(root / 'ready-tmp', root / 'ready.json')
if mode == 'nonzero': raise SystemExit(7)
while True: signal.pause()
'''

_DRIVER = r'''
import json, os, signal, subprocess, sys, time
from pathlib import Path
from solar_flare_jepa.experiments import v2_pilot as pilot
from solar_flare_jepa.experiments.v2_resource_controls import ProcessJob, ResourceLimits, ResourceMonitoringUnavailable
root, worker, mode = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
def prior(signum, frame):
    (root / 'prior-handler-invoked').touch()
previous = {sig: prior for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
for sig, handler in previous.items(): signal.signal(sig, handler)
output = root / 'output'
resources = dict(total_wall_seconds=10, minimum_free_output_bytes=1)
context = dict(approval=dict(output_root=str(output)), design=dict(resources=resources),
               runtime=dict(source_fingerprint='synthetic'), binding_fingerprint='synthetic')
pilot.validate_execution = lambda *args: context
jobs = [ProcessJob('00-owned', (sys.executable, worker, str(root), mode), .5 if mode == 'timeout' else 8),
        ProcessJob('01-unstarted', (sys.executable, '-c', "from pathlib import Path;Path(" + repr(str(root / 'next-job')) + ").touch()"), 1)]
pilot.process_plan = lambda *args: (jobs, ResourceLimits(1024**3, 10, 1, 0, .01))
def no_publication(*args):
    (root / 'publication-attempted').touch()
    raise AssertionError('Synthetic failure must never reach publication')
pilot._load_sealed = no_publication
if mode == 'hard-kill':
    real_killpg = os.killpg
    def pause_hard_stop(group, signum):
        result = real_killpg(group, signum)
        if signum == signal.SIGKILL:
            (root / 'hard-kill-observed').touch()
            end = time.monotonic() + 3
            while not (root / 'hard-kill-release').exists():
                if time.monotonic() >= end: raise AssertionError('hard-kill handshake missing')
                time.sleep(.005)
        return result
    os.killpg = pause_hard_stop
if mode == 'monitor':
    def fail_monitor(self, group):
        end = time.monotonic() + 3
        while not (root / 'ready.json').exists():
            if time.monotonic() >= end: raise AssertionError('worker readiness missing')
            time.sleep(.005)
        raise ResourceMonitoringUnavailable('synthetic monitor loss after descendant readiness')
    pilot.PilotSupervisor._sample_rss = fail_monitor
if mode == 'spawn-race':
    real_spawn = subprocess.Popen
    def interrupt_spawn(*args, **kwargs):
        process = real_spawn(*args, **kwargs)
        if kwargs.get('start_new_session'):
            end = time.monotonic() + 3
            while not (root / 'ready.json').exists():
                if time.monotonic() >= end: raise AssertionError('worker readiness missing')
                time.sleep(.005)
            os.kill(os.getpid(), signal.SIGTERM)
        return process
    subprocess.Popen = interrupt_spawn
if len(sys.argv) > 4 and sys.argv[4] == 'cleanup':
    recovery = {}
    try:
        supervisor = pilot.PilotSupervisor(output / 'supervisor', jobs,
            code_fingerprint='synthetic', config_fingerprint='synthetic',
            limits=ResourceLimits(1024**3, 10, 1, 0, .01), minimum_free_bytes=1)
        if len(sys.argv) > 5 and sys.argv[5] == 'monitor-after-term':
            real_killpg = os.killpg
            term_sent = [False]
            def observe_term(group, signum):
                result = real_killpg(group, signum)
                if signum == signal.SIGTERM:
                    term_sent[0] = True
                return result
            real_group_live = pilot._group_live
            def unavailable_after_term(group):
                if term_sent[0]:
                    raise ResourceMonitoringUnavailable('synthetic orphan grace monitor loss')
                return real_group_live(group)
            os.killpg = observe_term
            pilot._group_live = unavailable_after_term
        supervisor.cleanup_orphan()
        recovery['cleanup_error'] = None
        try:
            supervisor.run()
            recovery['run_refused'] = False
        except BaseException:
            recovery['run_refused'] = True
    except BaseException as error:
        recovery['cleanup_error'] = type(error).__name__
        recovery['message'] = str(error)
    (root / 'recovery-outcome.json').write_text(json.dumps(recovery))
    raise SystemExit(0)
try:
    pilot.run_pilot(root, root / 'synthetic-external-approval.json')
    outcome = dict(error=None)
except BaseException as error:
    outcome = dict(error=type(error).__name__, message=str(error))
outcome['handlers_restored'] = all(signal.getsignal(sig) is handler for sig, handler in previous.items())
(root / 'outcome.json').write_text(json.dumps(outcome))
'''


@pytest.fixture
def unrelated_session():
    """A separate owned group makes collateral-termination assertions safe."""
    read_fd, write_fd = os.pipe()
    code = 'import os,signal,sys;os.write(int(sys.argv[1]), b"ready");signal.pause()'
    process = subprocess.Popen([sys.executable, '-c', code, str(write_fd)],
                               pass_fds=(write_fd,), start_new_session=True)
    os.close(write_fd)
    try:
        assert select.select([read_fd], [], [], 3)[0], 'unrelated session did not become ready'
        assert os.read(read_fd, 5) == b'ready'
        yield process
    finally:
        os.close(read_fd)
        if process.poll() is None:
            process.kill()
        process.wait(timeout=3)


def _until(predicate, description, *, seconds=5):
    """Wait for an explicit fixture event, with a monotonic upper bound."""
    deadline = time.monotonic() + seconds
    pause = threading.Event()
    while True:
        value = predicate()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise AssertionError(f'Timed out waiting for {description}')
        pause.wait(.005)


def _live_group(group):
    result = subprocess.run(['ps', '-axo', 'pid=,pgid=,stat='], capture_output=True,
                            text=True, check=True, timeout=1)
    return [int(pid) for line in result.stdout.splitlines() if line.strip()
            for pid, pgid, state in [line.split()]
            if int(pgid) == group and not state.startswith('Z')]


class _SyntheticPilot:
    def __init__(self, root, mode='signal'):
        self.root = root
        worker, driver = root / 'worker.py', root / 'driver.py'
        worker.write_text(_WORKER)
        driver.write_text(_DRIVER)
        self.stdout = (root / 'driver.stdout').open('wb')
        self.stderr = (root / 'driver.stderr').open('wb')
        self.process = subprocess.Popen([sys.executable, str(driver), str(root), str(worker), mode],
            env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), start_new_session=True,
            stdout=self.stdout, stderr=self.stderr)
        self.owned = None

    def ready(self):
        _until(lambda: (self.root / 'ready.json').is_file(), 'worker and descendant readiness')
        self.owned = json.loads((self.root / 'ready.json').read_text())
        assert self.owned['group'] == self.owned['worker']
        assert self.owned['group'] != os.getpgrp()
        return self.owned

    def finish(self):
        self.process.wait(timeout=6)
        _until(lambda: not _live_group(self.owned['group']), 'owned worker group extinction')
        outcome_path = self.root / 'outcome.json'
        assert outcome_path.is_file(), (self.root / 'driver.stderr').read_text()
        outcome = json.loads(outcome_path.read_text())
        assert outcome['error'] is not None, outcome
        assert outcome['handlers_restored'], outcome
        assert not (self.root / 'prior-handler-invoked').exists()
        ledger = json.loads((self.root / 'output/supervisor/supervisor.json').read_text())
        assert len(ledger['attempts']) == 1
        assert ledger['attempts'][0]['number'] == 1
        assert set(ledger['attempts'][0]) == {'job_id', 'job_fingerprint', 'number', 'status',
            'path', 'pid', 'started_utc', 'checkpoint_utc', 'wall_seconds', 'peak_sampled_rss_bytes',
            'returncode', 'failure_kind', 'error', 'finished_utc'}
        assert 'pilot_started' not in ledger
        assert ledger['jobs']['00-owned']['status'] != 'succeeded'
        assert ledger['jobs']['01-unstarted']['status'] == 'pending'
        assert not (self.root / 'next-job').exists()
        assert not (self.root / 'publication-attempted').exists()
        assert not (self.root / 'output/publication').exists()
        failure = json.loads((self.root / 'output/pilot_failure.json').read_text())
        assert failure['status'] == 'INCOMPLETE'
        assert failure['model_comparison_published'] is False
        assert failure['automatic_resume_permitted'] is False
        return ledger

    def close(self):
        # On a red regression run even an unhandled TERM/HUP must not leak workers.
        if self.owned is None and (self.root / 'ready.json').is_file():
            self.owned = json.loads((self.root / 'ready.json').read_text())
        if self.owned and _live_group(self.owned['group']):
            # The unique temporary-root argument authenticates fixture ownership
            # before emergency cleanup, even if the original leader has exited.
            inspected = subprocess.run(['ps', '-axo', 'pid=,pgid=,command='],
                capture_output=True, text=True, check=True, timeout=1).stdout.splitlines()
            owned_pids = {self.owned['worker'], self.owned['child']}
            verified = any(int(pid) in owned_pids and int(group) == self.owned['group']
                           and str(self.root) in command for line in inspected if line.strip()
                           for pid, group, command in [line.strip().split(None, 2)])
            assert verified, 'Refusing cleanup of an unauthenticated/reused worker group'
            assert self.owned['group'] != os.getpgrp()
            try:
                os.killpg(self.owned['group'], signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=3)
        if self.owned:
            _until(lambda: not _live_group(self.owned['group']), 'fixture cleanup')
        self.stdout.close()
        self.stderr.close()


@pytest.mark.parametrize('signum', [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])
def test_supervisor_only_signal_stops_ready_stubborn_worker_and_child(tmp_path, signum):
    fixture = _SyntheticPilot(tmp_path)
    try:
        owned = fixture.ready()
        assert {owned['worker'], owned['child']} <= set(_live_group(owned['group']))
        os.kill(fixture.process.pid, signum)
        fixture.finish()
    finally:
        fixture.close()


def test_repeated_signals_during_term_grace_cannot_interrupt_hard_stop(tmp_path):
    fixture = _SyntheticPilot(tmp_path)
    try:
        fixture.ready()
        os.kill(fixture.process.pid, signal.SIGTERM)
        _until(lambda: (tmp_path / 'term-observed').exists(), 'worker TERM grace handshake')
        for signum in (signal.SIGINT, signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            os.kill(fixture.process.pid, signum)
        fixture.finish()
    finally:
        fixture.close()


@pytest.mark.parametrize('mode', ['timeout', 'nonzero', 'monitor'])
def test_real_subprocess_failure_kills_descendant_and_stops_without_retry(tmp_path, mode):
    fixture = _SyntheticPilot(tmp_path, mode)
    try:
        fixture.ready()
        fixture.finish()
    finally:
        fixture.close()


def test_signal_between_popen_success_and_return_does_not_lose_worker_ownership(tmp_path):
    fixture = _SyntheticPilot(tmp_path, 'spawn-race')
    try:
        fixture.ready()
        fixture.finish()
    finally:
        fixture.close()


def test_repeated_signals_at_hard_kill_boundary_still_reap_and_finalize(tmp_path):
    fixture = _SyntheticPilot(tmp_path, 'hard-kill')
    try:
        fixture.ready()
        os.kill(fixture.process.pid, signal.SIGTERM)
        _until(lambda: (tmp_path / 'hard-kill-observed').exists(), 'actual hard-kill boundary')
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            os.kill(fixture.process.pid, signum)
        (tmp_path / 'hard-kill-release').touch()
        fixture.finish()
    finally:
        (tmp_path / 'hard-kill-release').touch()
        fixture.close()


def _orphan_ready_group(fixture):
    owned = fixture.ready()
    ledger_path = fixture.root / 'output/supervisor/supervisor.json'
    identity_path = fixture.root / 'output/supervisor/ownership/00-owned-1.json'
    def persisted_identity():
        return json.loads(identity_path.read_text()) if identity_path.is_file() else None
    identity = _until(persisted_identity, 'durable worker ownership identity')
    assert identity['pid'] == owned['worker']
    assert identity['pgid'] == owned['group']
    fixture.process.kill()  # Explicitly exercise the documented uncatchable loss.
    fixture.process.wait(timeout=3)
    assert {owned['worker'], owned['child']} <= set(_live_group(owned['group']))
    return ledger_path


def _recover_fixture(fixture, failure=None):
    extra = [] if failure is None else [failure]
    result = subprocess.run([sys.executable, str(fixture.root / 'driver.py'),
        str(fixture.root), str(fixture.root / 'worker.py'), 'signal', 'cleanup', *extra],
        env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), capture_output=True,
        text=True, timeout=6)
    assert result.returncode == 0, result.stderr
    return json.loads((fixture.root / 'recovery-outcome.json').read_text())


def test_explicit_orphan_cleanup_stops_only_owned_group_and_never_resumes(tmp_path, unrelated_session):
    fixture = _SyntheticPilot(tmp_path)
    try:
        ledger_path = _orphan_ready_group(fixture)
        outcome = _recover_fixture(fixture)
        assert outcome['cleanup_error'] is None, outcome
        assert outcome['run_refused'], outcome
        assert unrelated_session.poll() is None
        _until(lambda: not _live_group(fixture.owned['group']), 'orphan group extinction')
        ledger = json.loads(ledger_path.read_text())
        assert len(ledger['attempts']) == 1
        assert ledger['attempts'][0]['status'] == 'failed'
        assert ledger['jobs']['00-owned']['status'] == 'failed'
        assert ledger['jobs']['01-unstarted']['status'] == 'pending'
        assert ledger['stop_reason'] is not None
        assert not (tmp_path / 'next-job').exists()
        assert not (tmp_path / 'publication-attempted').exists()
        assert not (tmp_path / 'output/publication').exists()
    finally:
        fixture.close()


@pytest.mark.parametrize('mismatch', ['token', 'missing-token', 'null-token', 'birth', 'pgid', 'uid', 'session', 'missing'])
def test_orphan_identity_mismatch_refuses_without_signaling_or_rewriting_evidence(tmp_path, mismatch, unrelated_session):
    fixture = _SyntheticPilot(tmp_path)
    try:
        ledger_path = _orphan_ready_group(fixture)
        identity_path = tmp_path / 'output/supervisor/ownership/00-owned-1.json'
        identity = json.loads(identity_path.read_text())
        if mismatch == 'token':
            identity['token'] = '0' * 64 if identity['token'] != '0' * 64 else '1' * 64
        elif mismatch == 'missing-token':
            del identity['token']
        elif mismatch == 'null-token':
            identity['token'] = None
        elif mismatch == 'birth':
            identity['birth'] = 'unrelated process birth'
        elif mismatch == 'pgid':
            identity['pgid'] = unrelated_session.pid
        elif mismatch in ('uid', 'session'):
            identity[mismatch] += 1
        if mismatch == 'missing':
            identity_path.unlink()
        else:
            identity_path.chmod(0o600)
            identity_path.write_text(json.dumps(identity))
        before = ledger_path.read_bytes()
        identity_before = identity_path.read_bytes() if identity_path.exists() else None
        outcome = _recover_fixture(fixture)
        assert outcome['cleanup_error'] is not None, outcome
        assert unrelated_session.poll() is None
        assert ledger_path.read_bytes() == before
        assert (identity_path.read_bytes() if identity_path.exists() else None) == identity_before
        assert {fixture.owned['worker'], fixture.owned['child']} <= set(_live_group(fixture.owned['group']))
        assert not (tmp_path / 'term-observed').exists()
        assert not (tmp_path / 'next-job').exists()
    finally:
        fixture.close()


def test_orphan_with_missing_leader_but_live_descendant_refuses_ambiguous_cleanup(tmp_path):
    fixture = _SyntheticPilot(tmp_path)
    try:
        ledger_path = _orphan_ready_group(fixture)
        os.kill(fixture.owned['worker'], signal.SIGKILL)
        _until(lambda: fixture.owned['worker'] not in _live_group(fixture.owned['group']),
               'leader death with descendant remaining')
        assert fixture.owned['child'] in _live_group(fixture.owned['group'])
        before = ledger_path.read_bytes()
        outcome = _recover_fixture(fixture)
        assert outcome['cleanup_error'] is not None, outcome
        assert ledger_path.read_bytes() == before
        assert fixture.owned['child'] in _live_group(fixture.owned['group'])
        assert not (tmp_path / 'next-job').exists()
    finally:
        fixture.close()


def test_cleanup_refuses_while_original_supervisor_holds_execution_lock(tmp_path):
    fixture = _SyntheticPilot(tmp_path)
    try:
        fixture.ready()
        outcome = _recover_fixture(fixture)
        assert outcome['cleanup_error'] is not None, outcome
        assert fixture.process.poll() is None
        assert {fixture.owned['worker'], fixture.owned['child']} <= set(_live_group(fixture.owned['group']))
        assert not (tmp_path / 'term-observed').exists()
        os.kill(fixture.process.pid, signal.SIGTERM)
        fixture.finish()
    finally:
        fixture.close()


def test_authenticated_orphan_monitor_loss_cannot_skip_hard_stop(tmp_path, unrelated_session):
    fixture = _SyntheticPilot(tmp_path)
    try:
        ledger_path = _orphan_ready_group(fixture)
        before = ledger_path.read_bytes()
        outcome = _recover_fixture(fixture, 'monitor-after-term')
        assert outcome['cleanup_error'] == 'ResourceMonitoringUnavailable', outcome
        _until(lambda: not _live_group(fixture.owned['group']), 'hard stop despite grace monitor loss')
        assert ledger_path.read_bytes() == before
        assert unrelated_session.poll() is None
        assert not (tmp_path / 'next-job').exists()
        assert not (tmp_path / 'output/publication').exists()
    finally:
        fixture.close()
