"""Generic, opt-in Unix subprocess supervision; no experiment execution policy.

All budgets and code/config identities are supplied by the caller. This module
does not load models/data, approve a protocol, select results or release tests.
``ProcessSupervisor`` runs declared argv commands serially in job-id order, with
one fresh process session per attempt. A job timeout applies to each attempt;
the total wall budget includes every attempt, retry and resumed session.

RSS is the sampled sum of live workers and descendants reported by Unix ``ps``
(KiB), not an OS allocation limit or exact high-water mark. Short peaks between
samples can escape detection. Workers must not daemonize or leave their session;
this is trusted-job infrastructure, not a sandbox. Native-library thread
environment variables are capped at four; a worker can override library settings
at runtime, so no OS thread-count guarantee is made. Termination latency is
bounded by polling/ps latency and a short kill grace period, not a hard deadline.

The ledger is fsynced atomically and successful artifacts are hash-verified and
made read-only. Same-user tampering, external writes, claimed code fingerprints,
hardware changes and credentials are not authenticated. A crashed supervisor
charges the wall interval since its last checkpoint conservatively on recovery
(including downtime, using UTC); a backward clock or a still-live orphan group
blocks resume. Concurrent ``run`` calls are excluded with an advisory file lock.
If termination itself cannot be established, the unresolved running attempt is
persisted and execution raises; it is never quarantined while a worker may live.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .config import read_finite_json
from .provenance import _rename_no_replace
from .v2_runner import ArtifactIntegrityError, _seal, _verify_sealed

_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*')
_THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
               'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS')
_RETRYABLE = {'TIMEOUT', 'RSS_CEILING', 'INFRASTRUCTURE_SIGNAL', 'START_FAILURE', 'INTERRUPTED'}
_FAILURES = _RETRYABLE | {'JOB_EXIT', 'ARTIFACT_INTEGRITY', 'TOTAL_WALL_BUDGET', 'MONITOR_UNAVAILABLE'}
_LEDGER = 'supervisor.json'


class SupervisionIdentityError(ValueError):
    """The resumed declarations differ from the persisted execution plan."""


class SupervisionIntegrityError(ValueError):
    """Ledger state or immutable successful artifacts changed inconsistently."""


class ResourceMonitoringUnavailable(RuntimeError):
    """A supported, parseable process-tree RSS sample cannot be obtained."""


def _positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive')


def _identity(value, name):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f'{name} must be an explicit nonempty identity')
    return value


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _copy(value):
    return json.loads(canonical_json(value))


@dataclass(frozen=True)
class ResourceLimits:
    """Explicit operational budgets, capped at 4 GiB, four threads and one retry."""
    max_rss_bytes: int
    total_wall_seconds: float
    threads: int
    max_retries: int = 1
    poll_interval_seconds: float = 0.05

    def __post_init__(self):
        if type(self.max_rss_bytes) is not int or not 0 < self.max_rss_bytes <= 4 * 1024**3:
            raise ValueError('max_rss_bytes must be an integer in (0, 4 GiB]')
        if type(self.threads) is not int or not 1 <= self.threads <= 4:
            raise ValueError('threads must be an integer in [1, 4]')
        if type(self.max_retries) is not int or not 0 <= self.max_retries <= 1:
            raise ValueError('max_retries must be zero or one')
        _positive(self.total_wall_seconds, 'total_wall_seconds')
        _positive(self.poll_interval_seconds, 'poll_interval_seconds')


@dataclass(frozen=True)
class ProcessJob:
    """Exact shell-free argv declaration; artifacts are written in the worker cwd."""
    job_id: str
    command: tuple
    timeout_seconds: float

    def __post_init__(self):
        if not isinstance(self.job_id, str) or not _NAME.fullmatch(self.job_id):
            raise ValueError('job_id must be a portable single path component')
        if (not isinstance(self.command, (list, tuple)) or not self.command
                or any(not isinstance(arg, str) or not arg or '\0' in arg for arg in self.command)):
            raise ValueError('command must be nonempty argv strings; no shell is used')
        object.__setattr__(self, 'command', tuple(self.command))
        _positive(self.timeout_seconds, 'timeout_seconds')

    @property
    def fingerprint(self):
        return fingerprint_payload(asdict(self))


def _processes():
    if sys.platform not in ('darwin', 'linux'):
        raise ResourceMonitoringUnavailable('Only macOS/Linux ps RSS units are supported')
    try:
        result = subprocess.run(['ps', '-axo', 'pid=,ppid=,pgid=,rss=,stat='],
                                capture_output=True, text=True, timeout=0.5, check=True)
        rows = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            pid, parent, group, rss, state = line.split()
            row = dict(pid=int(pid), parent=int(parent), group=int(group),
                       rss_bytes=int(rss) * 1024, state=state)
            if min(row['pid'], row['parent'], row['group'], row['rss_bytes']) < 0:
                raise ValueError('Negative process statistic')
            rows.append(row)
        if not rows or not any(row['pid'] == os.getpid() for row in rows):
            raise ValueError('ps did not include the supervisor process')
        return rows
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ResourceMonitoringUnavailable(f'Cannot sample process-tree RSS: {error}') from error


class ProcessSupervisor:
    """Persist exact job/resource identities and supervise only explicit commands.

    A nonzero ordinary exit is terminal (including numerical failures). Only
    timeout, RSS breach, SIGTERM/SIGKILL/SIGHUP, spawn failure and interruption permit the
    single identical infrastructure retry. Monitoring failure and total-budget
    exhaustion stop the entire run immediately. Any terminal job failure also
    stops the run with later jobs pending; it never silently drops a job.
    """

    def __init__(self, directory, jobs, *, code_fingerprint, config_fingerprint, limits):
        if not isinstance(limits, ResourceLimits):
            raise TypeError('limits must be ResourceLimits')
        jobs = tuple(jobs)
        if not jobs or any(not isinstance(job, ProcessJob) for job in jobs):
            raise ValueError('jobs must be nonempty ProcessJob declarations')
        if len({job.job_id for job in jobs}) != len(jobs):
            raise ValueError('Duplicate job ids')
        self.jobs = tuple(sorted(jobs, key=lambda job: job.job_id))
        self.limits = limits
        self._wall_checkpoint = None
        self._active_attempt = None
        self.directory = Path(directory).absolute()
        if self.directory.resolve() != self.directory:
            raise ValueError('Supervisor directory must not redirect through a symlink')
        self.plan = dict(schema_version=1,
                         code_fingerprint=_identity(code_fingerprint, 'code_fingerprint'),
                         config_fingerprint=_identity(config_fingerprint, 'config_fingerprint'),
                         resources=asdict(limits), jobs=[asdict(job) for job in self.jobs])
        self.plan = _copy(self.plan)
        self.plan_fingerprint = fingerprint_payload(self.plan)
        self._validate_storage()
        if self.directory.exists() and not (self.directory / _LEDGER).is_file():
            if any(self.directory.iterdir()):
                raise FileExistsError('Refusing unrelated nonempty supervisor directory')
        self.directory.mkdir(parents=True, exist_ok=True)
        if (self.directory / _LEDGER).is_file():
            self._ledger = read_finite_json(self.directory / _LEDGER)
            self._validate_ledger()
        else:
            self._ledger = dict(schema_version=1, plan=self.plan, plan_fingerprint=self.plan_fingerprint,
                execution_order=[job.job_id for job in self.jobs], consumed_wall_seconds=0.0,
                stop_reason=None, attempts=[], jobs={job.job_id: dict(status='pending',
                    artifact_path=None, artifacts=None) for job in self.jobs})
            self._save(create=True)

    def _validate_storage(self):
        if self.directory.resolve() != self.directory:
            raise SupervisionIntegrityError('Supervisor storage redirects through a symlink')
        for name, kind in ((_LEDGER, 'file'), ('.supervisor.lock', 'file'),
                           ('attempts', 'directory'), ('quarantine', 'directory')):
            path = self.directory / name
            if path.is_symlink() or path.resolve() != path:
                raise SupervisionIntegrityError(f'Supervisor {name} storage redirects through a symlink')
            if path.exists() and not (path.is_file() if kind == 'file' else path.is_dir()):
                raise SupervisionIntegrityError(f'Supervisor {name} is not a {kind}')

    def _save(self, *, create=False):
        self._charge()
        descriptor, path = tempfile.mkstemp(prefix='.supervisor-', dir=self.directory)
        try:
            with os.fdopen(descriptor, 'w') as stream:
                stream.write(canonical_json(self._ledger) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            if create:
                _rename_no_replace(Path(path), self.directory / _LEDGER)
            else:
                os.replace(path, self.directory / _LEDGER)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def _validate_ledger(self):
        self._validate_storage()
        state = self._ledger
        if (not isinstance(state, dict) or state.get('schema_version') != 1
                or state.get('plan_fingerprint') != self.plan_fingerprint
                or state.get('plan') != self.plan):
            raise SupervisionIdentityError('Execution code/config/job/resource identity differs')
        if (state.get('execution_order') != [job.job_id for job in self.jobs]
                or set(state.get('jobs', {})) != {job.job_id for job in self.jobs}
                or type(state.get('consumed_wall_seconds')) not in (int, float)
                or not math.isfinite(state['consumed_wall_seconds']) or state['consumed_wall_seconds'] < 0
                or not isinstance(state.get('attempts'), list)):
            raise SupervisionIntegrityError('Malformed supervisor ledger')
        declarations = {job.job_id: job for job in self.jobs}
        for attempt in state['attempts']:
            if (not isinstance(attempt, dict) or attempt.get('job_id') not in declarations
                    or type(attempt.get('number')) is not int or attempt['number'] < 1
                    or attempt.get('status') not in ('running', 'succeeded', 'failed')):
                raise SupervisionIntegrityError('Unknown or malformed attempt')
            name = f"{attempt['job_id']}-{attempt['number']}"
            expected = f"{'quarantine' if attempt['status'] == 'failed' else 'attempts'}/{name}"
            path = self.directory / expected
            if attempt.get('path') != expected or path.resolve() != path or not path.is_dir():
                raise SupervisionIntegrityError('Unsafe, unexpected or missing attempt path')
            if (attempt.get('failure_kind') not in _FAILURES | {None}
                    or (attempt['status'] == 'succeeded' and
                        (attempt.get('failure_kind') is not None or attempt.get('returncode') != 0))
                    or (attempt['status'] == 'failed' and attempt.get('failure_kind') is None)
                    or type(attempt.get('wall_seconds')) not in (int, float)
                    or not math.isfinite(attempt['wall_seconds']) or attempt['wall_seconds'] < 0
                    or type(attempt.get('peak_sampled_rss_bytes')) is not int
                    or attempt['peak_sampled_rss_bytes'] < 0
                    or (attempt.get('pid') is not None and
                        (type(attempt['pid']) is not int or attempt['pid'] <= 0))):
                raise SupervisionIntegrityError('Malformed attempt outcome or accounting')
            try:
                checkpoint = datetime.fromisoformat(attempt['checkpoint_utc'])
                if checkpoint.utcoffset() is None or checkpoint.utcoffset().total_seconds() != 0:
                    raise ValueError('UTC required')
            except (KeyError, TypeError, ValueError) as error:
                raise SupervisionIntegrityError('Invalid attempt wall checkpoint') from error
        if [a['job_id'] for a in state['attempts']] != sorted(a['job_id'] for a in state['attempts']):
            raise SupervisionIntegrityError('Attempt order differs from the deterministic plan')
        for job in self.jobs:
            entry = state['jobs'][job.job_id]
            attempts = [attempt for attempt in state['attempts'] if attempt.get('job_id') == job.job_id]
            if (entry.get('status') not in ('pending', 'succeeded', 'failed')
                    or len(attempts) > self.limits.max_retries + 1
                    or any(attempt.get('number') != number or attempt.get('job_fingerprint') != job.fingerprint
                           for number, attempt in enumerate(attempts, 1))):
                raise SupervisionIntegrityError('Invalid attempt identity or retry count')
            if any(a['status'] != 'failed' or a['failure_kind'] not in _RETRYABLE for a in attempts[:-1]):
                raise SupervisionIntegrityError('A successful or terminal failure was retried')
            if (entry['status'] == 'succeeded' and (not attempts or attempts[-1]['status'] != 'succeeded')
                    or entry['status'] == 'failed' and (not attempts or attempts[-1]['status'] != 'failed')
                    or entry['status'] == 'pending' and attempts and
                        (attempts[-1]['status'] == 'succeeded' or
                         attempts[-1]['status'] == 'failed' and
                         (attempts[-1]['failure_kind'] not in _RETRYABLE or
                          len(attempts) > self.limits.max_retries))):
                raise SupervisionIntegrityError('Job status differs from its terminal attempt')
            if entry['status'] == 'succeeded':
                expected = f'attempts/{job.job_id}-{len(attempts)}/artifacts'
                if not attempts or entry.get('artifact_path') != expected:
                    raise SupervisionIntegrityError('Unexpected successful artifact path')
                try:
                    _verify_sealed(self.directory / expected, entry['artifacts'], job.job_id)
                except (ArtifactIntegrityError, OSError, ValueError, KeyError) as error:
                    raise SupervisionIntegrityError(str(error)) from error

    def _sample_rss(self, process_group):
        rows = _processes()
        members = {row['pid'] for row in rows if row['group'] == process_group}
        while True:
            expanded = members | {row['pid'] for row in rows if row['parent'] in members}
            if expanded == members:
                break
            members = expanded
        return sum(row['rss_bytes'] for row in rows
                   if row['pid'] in members and not row['state'].startswith('Z'))

    def _quarantine(self, attempt):
        source = self.directory / attempt['path']
        destination = self.directory / 'quarantine' / f"{attempt['job_id']}-{attempt['number']}"
        destination.parent.mkdir(exist_ok=True)
        _rename_no_replace(source, destination)
        attempt['path'] = str(destination.relative_to(self.directory))

    def _recover(self, recovered_until):
        for attempt in self._ledger['attempts']:
            if attempt['status'] != 'running':
                continue
            if attempt.get('pid') is None:
                # Popen may have succeeded immediately before a supervisor
                # crash, without its PID reaching the durable ledger. Retrying
                # would risk two simultaneous workers under one budget.
                raise SupervisionIntegrityError('Interrupted worker spawn state is unknown; resume is refused')
            if attempt.get('pid') is not None and self._sample_rss(attempt['pid']) > 0:
                raise SupervisionIntegrityError('Interrupted worker group still lives; resume is refused')
            elapsed = (recovered_until - datetime.fromisoformat(attempt['checkpoint_utc'])).total_seconds()
            if elapsed < 0:
                raise SupervisionIntegrityError('Clock moved backwards; interrupted wall budget is unknown')
            self._ledger['consumed_wall_seconds'] += elapsed
            attempt['wall_seconds'] += elapsed
            attempt.update(status='failed', failure_kind='INTERRUPTED',
                           error='Supervisor exited without a final attempt record', finished_utc=_utc())
            self._quarantine(attempt)
            if attempt['number'] > self.limits.max_retries:
                self._ledger['jobs'][attempt['job_id']]['status'] = 'failed'
                self._ledger['stop_reason'] = 'JOB_FAILED'
            self._save()

    def _charge(self):
        if self._wall_checkpoint is None:
            return
        now = time.monotonic()
        elapsed = now - self._wall_checkpoint
        self._ledger['consumed_wall_seconds'] += elapsed
        if self._active_attempt is not None:
            self._active_attempt['wall_seconds'] += elapsed
            self._active_attempt['checkpoint_utc'] = _utc()
        self._wall_checkpoint = now

    @staticmethod
    def _terminate(process):
        def signal_group(value):
            try:
                os.killpg(process.pid, value)
            except ProcessLookupError:
                pass
            except PermissionError:
                # Darwin can return EPERM for a just-extinguished group. Do
                # not mistake that race for a failure, or ignore live workers.
                if any(row['group'] == process.pid and not row['state'].startswith('Z')
                       for row in _processes()):
                    raise ResourceMonitoringUnavailable('Cannot terminate a live worker process group')
        try:
            signal_group(signal.SIGTERM)
        finally:
            # Always try the hard stop, even when soft termination was denied.
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
            signal_group(signal.SIGKILL)
        process.wait(timeout=1)

    def _attempt(self, job):
        prior = [attempt for attempt in self._ledger['attempts'] if attempt['job_id'] == job.job_id]
        number = len(prior) + 1
        relative = f'attempts/{job.job_id}-{number}'
        directory = self.directory / relative
        directory.mkdir(parents=True, exist_ok=False)
        artifacts = directory / 'artifacts'
        artifacts.mkdir()
        attempt = dict(job_id=job.job_id, number=number, job_fingerprint=job.fingerprint,
                       status='running', path=relative, pid=None, started_utc=_utc(),
                       checkpoint_utc=_utc(), wall_seconds=0.0, peak_sampled_rss_bytes=0,
                       returncode=None, failure_kind=None, error=None)
        self._ledger['attempts'].append(attempt)
        self._active_attempt = attempt
        self._save()
        environment = dict(os.environ, **{name: str(self.limits.threads) for name in _THREAD_ENV})
        process, interrupted = None, None
        began = time.monotonic()

        try:
            with (directory / 'stdout.log').open('xb') as stdout, (directory / 'stderr.log').open('xb') as stderr:
                try:
                    process = subprocess.Popen(job.command, cwd=artifacts, env=environment,
                                               stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                               start_new_session=True)
                except OSError as error:
                    attempt.update(failure_kind='START_FAILURE', error=f'{type(error).__name__}: {error}')
                if process is not None:
                    attempt['pid'] = process.pid
                    self._save()
                    while True:
                        self._charge()
                        if self._ledger['consumed_wall_seconds'] >= self.limits.total_wall_seconds:
                            attempt.update(failure_kind='TOTAL_WALL_BUDGET', error='Cumulative wall budget exhausted')
                            break
                        if time.monotonic() - began >= job.timeout_seconds:
                            attempt.update(failure_kind='TIMEOUT', error='Per-attempt job timeout exceeded')
                            break
                        attempt['peak_sampled_rss_bytes'] = max(attempt['peak_sampled_rss_bytes'],
                                                              self._sample_rss(process.pid))
                        if attempt['peak_sampled_rss_bytes'] > self.limits.max_rss_bytes:
                            attempt.update(failure_kind='RSS_CEILING', error='Sampled process-tree RSS ceiling exceeded')
                            break
                        code = process.poll()
                        if code is not None:
                            attempt['returncode'] = code
                            if code != 0:
                                kind = 'INFRASTRUCTURE_SIGNAL' if -code in (
                                    signal.SIGTERM, signal.SIGKILL, signal.SIGHUP) else 'JOB_EXIT'
                                attempt.update(failure_kind=kind,
                                               error=f'Worker exited with code {code}')
                            elif self._sample_rss(process.pid) > 0:
                                attempt.update(failure_kind='JOB_EXIT', error='Worker left live descendants')
                            break
                        self._save()
                        remaining = min(self.limits.poll_interval_seconds,
                                        job.timeout_seconds - (time.monotonic() - began),
                                        self.limits.total_wall_seconds - self._ledger['consumed_wall_seconds'])
                        if remaining > 0:
                            time.sleep(remaining)
        except ResourceMonitoringUnavailable as error:
            attempt.update(failure_kind='MONITOR_UNAVAILABLE', error=str(error))
        except BaseException as error:
            interrupted = error
            attempt.update(failure_kind='INTERRUPTED', error=f'{type(error).__name__}: {error}')
        finally:
            if process is not None:
                try:
                    self._terminate(process)
                except (OSError, subprocess.SubprocessError, ResourceMonitoringUnavailable) as error:
                    attempt.update(failure_kind='MONITOR_UNAVAILABLE', error=str(error))
                    self._ledger['stop_reason'] = 'MONITOR_UNAVAILABLE'
                    self._save()
                    raise ResourceMonitoringUnavailable(str(error)) from error
                attempt['returncode'] = process.returncode
            self._charge()
        entry = self._ledger['jobs'][job.job_id]
        if attempt['failure_kind'] is None:
            try:
                entry['artifacts'] = _seal(artifacts)
                entry.update(status='succeeded', artifact_path=f'{relative}/artifacts')
            except (ArtifactIntegrityError, OSError, ValueError) as error:
                attempt.update(failure_kind='ARTIFACT_INTEGRITY', error=f'{type(error).__name__}: {error}')
        attempt.update(status='succeeded' if attempt['failure_kind'] is None else 'failed', finished_utc=_utc())
        if attempt['failure_kind'] is not None:
            self._quarantine(attempt)
            if attempt['failure_kind'] not in _RETRYABLE or number > self.limits.max_retries:
                entry['status'] = 'failed'
            if attempt['failure_kind'] in ('TOTAL_WALL_BUDGET', 'MONITOR_UNAVAILABLE'):
                self._ledger['stop_reason'] = attempt['failure_kind']
        self._charge()
        if self._ledger['consumed_wall_seconds'] >= self.limits.total_wall_seconds:
            self._ledger['stop_reason'] = 'TOTAL_WALL_BUDGET'
        self._save()
        self._active_attempt = None
        if interrupted is not None:
            raise interrupted

    def run(self):
        """Run pending declarations; never invoke an undeclared job or exceed retries."""
        began, recovered_until = time.monotonic(), datetime.now(timezone.utc)
        self._validate_storage()
        lock_path = self.directory / '.supervisor.lock'
        with lock_path.open('a+b') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise SupervisionIntegrityError('Another supervisor is already running') from error
            try:
                self._ledger = read_finite_json(self.directory / _LEDGER)
                self._validate_ledger()
                self._recover(recovered_until)
                if (self._ledger['stop_reason'] is None and
                        any(entry['status'] != 'succeeded' for entry in self._ledger['jobs'].values())):
                    self._wall_checkpoint = began
                    self._run_pending()
            finally:
                try:
                    if self._wall_checkpoint is not None:
                        self._charge()
                        if self._ledger['consumed_wall_seconds'] >= self.limits.total_wall_seconds:
                            self._ledger['stop_reason'] = 'TOTAL_WALL_BUDGET'
                        self._save()
                finally:
                    self._wall_checkpoint = None
                    self._active_attempt = None
            return _copy(self._ledger)

    def _run_pending(self):
        for job in self.jobs:
            entry = self._ledger['jobs'][job.job_id]
            while entry['status'] == 'pending':
                self._charge()
                if self._ledger['consumed_wall_seconds'] >= self.limits.total_wall_seconds:
                    self._ledger['stop_reason'] = 'TOTAL_WALL_BUDGET'
                    return
                self._attempt(job)
                if self._ledger['stop_reason'] is not None:
                    return
            if entry['status'] == 'failed':
                self._ledger['stop_reason'] = 'JOB_FAILED'
                return
