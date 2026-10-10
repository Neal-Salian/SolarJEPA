"""V2 staged experiment runner: a model-agnostic, persisted A-F state machine.

Status: infrastructure for a PROPOSED protocol. Nothing here approves the V2
protocol, a test custodian, seeds, budgets or a test release.

Stages, strictly in order::

    CREATED -> A_VALIDATED -> B_FITTED -> C_SELECTED -> D_LOCKED
            -> E_TEST_RELEASED -> F_PUBLISHED

* A ``validate``: records declared dataset/split identities, refuses an empty
  job list, runs an optional train/validation check and registered hooks.
* B ``fit``: runs every pending job through an injected ``fit_fn(job, job_dir)``.
  Exceptions become per-job failure records (never silent drops); a crash
  (``BaseException``) leaves the job pending and its directory is quarantined by
  rename on resume. Succeeded job directories are sealed with an
  ``artifacts.json`` sha256 manifest and re-verified on every resume.
* C ``select``: an injected ``select_fn(records)`` sees fit/validation records
  of every job (failed ones included) and never any test data.
* D ``lock``: config, plan, selection and every succeeded job's artifact
  identities are bound into a write-once ``lock.json`` with a lock fingerprint.
* E ``release_test``: disabled by default. Requires ``allow_test_release=True``
  at construction plus a ``TestReleaseAuthorization`` with approval status
  exactly ``APPROVED`` naming this run's config and lock fingerprints, and the
  declared test identity. Locks are re-verified before and after prediction.
  Release is single-shot: its record is persisted before the first prediction.
* F ``publish``: JSON results are published by verified no-replace atomic rename.

Model-specific work is injected as callables; the runner itself never loads
data. Identities are caller declarations. See ``TECHNICALLY_ENFORCED`` and
``PROCEDURAL_ONLY`` for what this local code can and cannot guarantee.
"""
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile
import time
from types import MappingProxyType

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .config import read_finite_json
from .provenance import _relative, _rename_no_replace, _source_path, verify_artifacts

SCHEMA_VERSION = 1
STAGES = ('CREATED', 'A_VALIDATED', 'B_FITTED', 'C_SELECTED', 'D_LOCKED', 'E_TEST_RELEASED', 'F_PUBLISHED')
PROPOSED = 'PROPOSED_REQUIRES_APPROVAL'
APPROVED = 'APPROVED'
RUNS_DIRECTORY = ('results', 'v2_runs')
LEDGER_NAME = 'ledger.json'
LOCK_NAME = 'lock.json'
PUBLICATION_NAME = 'publication'
_RESERVED_PUBLICATION = ('artifacts.json', 'run_ledger.json', 'lock_manifest.json')
_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*')

TECHNICALLY_ENFORCED = (
    'one test release per declared test identity per results root, claimed by an exclusive-create registry '
    'file before the run-level release record is persisted',
    'resume refuses a provenance declaration that differs from the one recorded when the run was created',
    'stage ordering: every method checks the persisted current stage and raises InvalidTransition otherwise',
    'test release is disabled unless StagedRun is constructed with allow_test_release=True',
    'test release requires the run plan approval_status to be exactly APPROVED',
    'test release requires a TestReleaseAuthorization instance with approval_status exactly APPROVED '
    'naming this run config fingerprint and lock fingerprint',
    'single-shot test release: the release record is persisted before the first prediction, '
    'so any later call, including after a crash, is refused',
    'identity checks: resume refuses a changed config, dataset, split or test identity, job list or '
    'approval status; release refuses a supplied test identity different from the declared one',
    'sha256 artifact verification of sealed job directories on resume, selection, lock and before and '
    'after test release; lock.json must equal the ledger lock manifest',
    'job artifacts, artifact manifests and lock.json are created exclusively and never replaced by the '
    'runner; interrupted job directories are quarantined by rename, never deleted',
    'per-job failure records: no job is silently dropped and selection receives failed jobs',
    'no-replace atomic publication of a verified artifacts.json directory',
    'atomic ledger replacement (same-directory temporary file, fsync, os.replace)',
    'a failing, raising or malformed validation hook blocks its transition and is recorded',
    'optional process peak-RSS ceiling checked between jobs stops further fitting with a recorded failure',
)
RELEASE_REGISTRY = '.test_releases'

PROCEDURAL_ONLY = (
    'the cross-run release registry covers one results root only; another root or a deleted registry '
    'file can release the same test identity again',
    'job records are opaque to the runner: declared dataset/split identities are not compared with '
    'fingerprints inside job records unless a validation hook does so',
    'the runner never receives test data, but users and injected callables can still read test files '
    'outside the runner',
    'the local filesystem has no access control against the same user: ledger, lock.json and artifacts '
    'can be edited; read-only file modes are advisory',
    'dataset, split and test identities are caller declarations; the runner does not recompute them from data',
    'no cryptographic signing: sha256 detects inconsistent changes, not an adversary who also rewrites the ledger',
    'TestReleaseAuthorization is not authenticated: anyone can construct one, and authorized_by is a recorded claim',
    'the plan approval_status is a recorded caller string, not verified against any approval record',
    'fit_fn and predict_fn are trusted not to use test data during fitting and to write only inside '
    'their directory; files written elsewhere are not tracked',
    'no protection against concurrent processes operating on the same run directory',
    'peak RSS is the process-lifetime high-water mark (children excluded), not per job, checked only between jobs',
)


class InvalidTransition(RuntimeError):
    """A stage method was called out of order, or a single-shot step was repeated."""


class ReleaseRejected(PermissionError):
    """The test-release gate refused the request; the single shot is not consumed."""


class IdentityMismatch(ValueError):
    """A resumed run's declared identities differ from its ledger."""


class ArtifactIntegrityError(ValueError):
    """A sealed or locked artifact no longer matches its recorded identity."""


class ValidationHookFailed(RuntimeError):
    """A registered validation hook failed, raised or returned a malformed record."""


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    return value


def _json_copy(value):
    """Detached finite JSON copy; raises ValueError/TypeError for non-JSON content."""
    return json.loads(canonical_json(_thaw(value)))


def _freeze(value):
    """Read-only view of detached JSON: mappings become proxies, lists tuples."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _name(value, kind):
    if not isinstance(value, str) or not _NAME.fullmatch(value):
        raise ValueError(f'{kind} must match {_NAME.pattern}: {value!r}')
    return str.__str__(value)


def _identity(value, kind):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f'{kind} must be a nonempty identity string')
    return str.__str__(value)


def _error(error):
    return dict(error_type=type(error).__name__, message=str(error))


def write_artifact_once(path, data: bytes):
    """Write bytes with exclusive create and fsync; an existing file is never replaced."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def process_high_water_mark():
    """Process-lifetime peak RSS from getrusage, normalized to bytes.

    macOS reports ``ru_maxrss`` in bytes, Linux in kilobytes. This is the
    high-water mark of the whole process (children excluded), not a per-job figure.
    """
    try:
        import resource
    except ImportError:
        return dict(label='process_high_water_mark', bytes=None, raw=None, raw_unit=None,
                    platform=sys.platform, scope='resource module unavailable on this platform')
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    darwin = sys.platform == 'darwin'
    return dict(label='process_high_water_mark', bytes=raw if darwin else raw * 1024, raw=raw,
                raw_unit='bytes' if darwin else 'kilobytes', platform=sys.platform,
                scope='peak resident set size of this process since start; children excluded; not per job')


class JobSpec:
    """Immutable job declaration; ``job_id`` is derived from its canonical spec."""
    __slots__ = ('_spec',)

    def __init__(self, arm, seed, parameters=None):
        _name(arm, 'arm')
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError('seed must be a nonnegative integer')
        parameters = {} if parameters is None else parameters
        if not isinstance(parameters, Mapping):
            raise ValueError('job parameters must be a JSON mapping')
        spec = _json_copy(dict(arm=arm, seed=int(seed), parameters=parameters))
        object.__setattr__(self, '_spec', canonical_json(spec))

    def __setattr__(self, name, value):
        raise AttributeError('JobSpec is immutable')

    @classmethod
    def from_dict(cls, value):
        return cls(value['arm'], value['seed'], value['parameters'])

    def spec(self):
        return json.loads(self._spec)

    arm = property(lambda self: self.spec()['arm'])
    seed = property(lambda self: self.spec()['seed'])
    parameters = property(lambda self: self.spec()['parameters'])

    @property
    def job_id(self):
        spec = self.spec()
        return f"{spec['arm']}-s{spec['seed']}-{fingerprint_payload(spec)[:12]}"

    def as_dict(self):
        return dict(self.spec(), job_id=self.job_id)

    def __eq__(self, other):
        return isinstance(other, JobSpec) and other._spec == self._spec

    def __hash__(self):
        return hash(self._spec)

    def __repr__(self):
        return f'JobSpec({self.job_id})'


class RunConfig:
    """Immutable run plan. Holds only identities of test data, never test data.

    ``split_identities`` must name ``train`` and ``validation`` and no test-like
    partition; ``test_identity`` is the declared test-partition fingerprint (for
    example ``WindowedPartition.split_fingerprint``). ``approval_status`` is a
    caller declaration and defaults to ``PROPOSED_REQUIRES_APPROVAL``.
    """
    __slots__ = ('_payload',)

    def __init__(self, *, experiment_id, config, dataset_fingerprint, split_identities, test_identity,
                 jobs, approval_status=PROPOSED):
        _name(experiment_id, 'experiment_id')
        if not isinstance(config, Mapping):
            raise ValueError('config must be a JSON mapping')
        config = _json_copy(config)
        dataset = _identity(dataset_fingerprint, 'dataset_fingerprint')
        if not isinstance(split_identities, Mapping):
            raise ValueError('split_identities must be a mapping of partition name to identity')
        splits = {_name(k, 'split name'): _identity(v, f'split identity {k}') for k, v in split_identities.items()}
        if not {'train', 'validation'} <= set(splits):
            raise ValueError('split_identities must declare train and validation')
        if any('test' in name.casefold() for name in splits):
            raise ValueError('Test partitions are declared only through test_identity')
        test = _identity(test_identity, 'test_identity')
        if test in set(splits.values()) | {dataset}:
            raise ValueError('test_identity must differ from the dataset and train/validation identities')
        jobs = tuple(jobs)
        if any(not isinstance(job, JobSpec) for job in jobs):
            raise TypeError('jobs must be JobSpec instances')
        ids = [job.job_id for job in jobs]
        if len(set(ids)) != len(ids):
            raise ValueError('duplicate job ids in plan')
        payload = dict(experiment_id=experiment_id, config=config, config_fingerprint=fingerprint_payload(config),
                       dataset_fingerprint=dataset, split_identities=splits, test_identity=test,
                       approval_status=_identity(approval_status, 'approval_status'),
                       jobs=[job.as_dict() for job in sorted(jobs, key=lambda j: j.job_id)])
        object.__setattr__(self, '_payload', canonical_json(payload))

    def __setattr__(self, name, value):
        raise AttributeError('RunConfig is immutable')

    def as_dict(self):
        return json.loads(self._payload)

    experiment_id = property(lambda self: self.as_dict()['experiment_id'])
    config = property(lambda self: self.as_dict()['config'])
    config_fingerprint = property(lambda self: self.as_dict()['config_fingerprint'])
    dataset_fingerprint = property(lambda self: self.as_dict()['dataset_fingerprint'])
    split_identities = property(lambda self: self.as_dict()['split_identities'])
    test_identity = property(lambda self: self.as_dict()['test_identity'])
    approval_status = property(lambda self: self.as_dict()['approval_status'])

    @property
    def jobs(self):
        return tuple(JobSpec.from_dict(job) for job in self.as_dict()['jobs'])

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())


@dataclass(frozen=True)
class TestReleaseAuthorization:
    """Caller-constructed release authorization. NOT authenticated or signed."""
    __test__ = False  # not a pytest test class

    approval_status: str
    config_fingerprint: str
    lock_fingerprint: str
    authorized_by: str
    reference: str = ''

    def __post_init__(self):
        if any(not isinstance(getattr(self, name), str) for name in self.__dataclass_fields__):
            raise TypeError('TestReleaseAuthorization fields must be strings')

    def as_dict(self):
        return _json_copy(asdict(self))


def _seal(directory):
    """Write a write-once sha256 manifest of a job directory; mark files read-only."""
    directory = Path(directory)
    if (directory / 'artifacts.json').exists():
        raise ValueError('artifacts.json is reserved for the runner')
    files = []
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ArtifactIntegrityError(f'Symlinks are not accepted as artifacts: {path.name}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ArtifactIntegrityError(f'Only regular files are accepted as artifacts: {path.name}')
        identifier = str(_relative(path.relative_to(directory).as_posix()))
        files.append(dict(path=identifier, bytes=path.stat().st_size, sha256=sha256_file(path)))
    manifest = dict(schema_version=1, files=files)
    write_artifact_once(directory / 'artifacts.json', (canonical_json(manifest) + '\n').encode('utf-8'))
    verify_artifacts(directory)
    for path in [directory / item['path'] for item in files] + [directory / 'artifacts.json']:
        os.chmod(path, 0o444)
    return dict(files=files, manifest_sha256=sha256_file(directory / 'artifacts.json'))


def _verify_sealed(directory, recorded, label):
    try:
        manifest = verify_artifacts(directory)
        manifest_sha = sha256_file(Path(directory) / 'artifacts.json')
    except (ValueError, OSError) as error:
        raise ArtifactIntegrityError(f'{label}: {error}') from error
    if manifest['files'] != recorded['files'] or manifest_sha != recorded['manifest_sha256']:
        raise ArtifactIntegrityError(f'{label}: artifact manifest differs from the recorded identity')


class StagedRun:
    """Persisted staged run under ``<root>/results/v2_runs/<run_name>``.

    Constructing on an existing run directory resumes from its ledger and
    refuses any change of declared identities. Hooks are not persisted and must
    be registered again in each process.
    """

    def __init__(self, root, run_name, plan, *, allow_test_release=False, max_rss_bytes=None, provenance=None):
        if not isinstance(plan, RunConfig):
            raise TypeError('plan must be a RunConfig')
        _name(run_name, 'run name')
        if max_rss_bytes is not None:
            if isinstance(max_rss_bytes, bool) or not isinstance(max_rss_bytes, int) or max_rss_bytes <= 0:
                raise ValueError('max_rss_bytes must be a positive integer or None')
            if process_high_water_mark()['bytes'] is None:
                raise ValueError('max_rss_bytes cannot be enforced: peak RSS is unavailable on this platform')
        root = _source_path(root)
        parent = root.joinpath(*RUNS_DIRECTORY)
        parent.mkdir(parents=True, exist_ok=True)
        if parent.resolve() != parent:
            raise ValueError('Run parent must not redirect through symlinks')
        self.root, self.run_name, self.plan = root, run_name, plan
        self._provenance = provenance
        self.run_dir = parent / run_name
        self.allow_test_release = allow_test_release is True
        self.max_rss_bytes = max_rss_bytes
        self._hooks = []
        if self.run_dir.is_symlink():
            raise ValueError('Run directory must not be a symlink')
        if (self.run_dir / LEDGER_NAME).is_file():
            self._ledger = read_finite_json(self.run_dir / LEDGER_NAME)
            self._check_resume()
            recorded = self._ledger.get('provenance')
            if recorded != (None if provenance is None else _json_copy(provenance)):
                raise IdentityMismatch('Resume refused: code/runtime provenance differs from the run ledger')
        elif self.run_dir.exists():
            raise FileExistsError(f'Run directory exists without a ledger; refusing unknown state: {self.run_dir}')
        else:
            self.run_dir.mkdir()
            self._ledger = self._new_ledger()
        self._ledger['sessions'].append(dict(
            utc=_utc(), pid=os.getpid(), python=sys.version, platform=platform.platform(),
            allow_test_release=self.allow_test_release, max_rss_bytes=max_rss_bytes,
            provenance=None if provenance is None else _json_copy(provenance)))
        self._save()

    # ----------------------------------------------------------------- ledger
    def _new_ledger(self):
        plan = self.plan.as_dict()
        return dict(
            schema_version=SCHEMA_VERSION, experiment_id=plan['experiment_id'], run_name=self.run_name,
            plan=plan, plan_fingerprint=self.plan.fingerprint, config_fingerprint=plan['config_fingerprint'],
            dataset_fingerprint=plan['dataset_fingerprint'], split_identities=plan['split_identities'],
            test_identity=plan['test_identity'], approval_status=plan['approval_status'],
            stage=STAGES[0], created_utc=_utc(), transitions=[],
            jobs={job['job_id']: dict(spec=job, status='pending', attempts=[], record=None, artifacts=None,
                                      failure=None, wall_seconds=None) for job in plan['jobs']},
            failures=[], quarantines=[], validation=None, fit=None, selection=None, lock=None, release=None,
            release_rejections=[], publication=None, hooks=[], resources=[], sessions=[],
            provenance=None if self._provenance is None else _json_copy(self._provenance),
            safeguards=dict(technically_enforced=list(TECHNICALLY_ENFORCED), procedural_only=list(PROCEDURAL_ONLY)))

    def _check_resume(self):
        ledger = self._ledger
        if not isinstance(ledger, dict) or ledger.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported or invalid run ledger')
        plan = self.plan.as_dict()
        for field in ('experiment_id', 'config_fingerprint', 'dataset_fingerprint', 'split_identities',
                      'test_identity', 'approval_status'):
            if ledger.get(field) != plan[field]:
                raise IdentityMismatch(f'Resume refused: {field} differs from the run ledger')
        if (ledger.get('run_name') != self.run_name or ledger.get('plan_fingerprint') != self.plan.fingerprint
                or fingerprint_payload(ledger.get('plan')) != ledger.get('plan_fingerprint')):
            raise IdentityMismatch('Resume refused: run plan (job list) differs from the run ledger')
        if ledger.get('stage') not in STAGES:
            raise ValueError('Run ledger has an unknown stage')

    def _save(self):
        encoded = (canonical_json(self._ledger) + '\n').encode('utf-8')
        descriptor, temporary = tempfile.mkstemp(prefix='.ledger-', suffix='.tmp', dir=self.run_dir)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.run_dir / LEDGER_NAME)
        except BaseException:
            if os.path.exists(temporary):
                os.unlink(temporary)
            raise
        try:
            directory = os.open(self.run_dir, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass

    @property
    def stage(self):
        return self._ledger['stage']

    @property
    def lock_fingerprint(self):
        lock = self._ledger['lock']
        return None if lock is None else lock['fingerprint']

    def snapshot(self):
        """Detached read-only view of the ledger."""
        return _freeze(_json_copy(self._ledger))

    def _require(self, stage, action):
        if self.stage != stage:
            raise InvalidTransition(f'{action} requires stage {stage}; current stage is {self.stage}')

    def _failure(self, stage, error, job_id=None):
        record = dict(stage=stage, job_id=job_id, utc=_utc(), **_error(error))
        self._ledger['failures'].append(record)
        return record

    # ------------------------------------------------------------------ hooks
    def register_hook(self, stage_name, hook):
        """Register an independent validator run before entering ``stage_name``.

        The hook receives a read-only ledger snapshot with ``proposed_transition``
        and must return ``{'hook_id', 'version', 'passed': bool, 'details'}``.
        """
        if stage_name not in STAGES[1:]:
            raise ValueError(f'Hooks attach to one of {STAGES[1:]}')
        if not callable(hook):
            raise TypeError('hook must be callable')
        self._hooks.append((stage_name, hook))

    def _run_hooks(self, stage, proposed):
        hooks = [hook for name, hook in self._hooks if name == stage]
        if not hooks:
            return
        snapshot = _freeze(_json_copy(dict(self._ledger, proposed_transition=dict(
            from_stage=self.stage, to=stage, record=proposed))))
        failed = []
        for hook in hooks:
            name = getattr(hook, '__qualname__', type(hook).__name__)
            try:
                result = hook(snapshot)
                if not isinstance(result, Mapping) or set(result) != {'hook_id', 'version', 'passed', 'details'}:
                    raise ValueError('hook must return exactly hook_id, version, passed, details')
                if not isinstance(result['passed'], bool) or not isinstance(result['hook_id'], str) \
                        or not result['hook_id'] or not isinstance(result['version'], str):
                    raise ValueError('hook_id/version must be strings and passed a bool')
                result = _json_copy(result)
            except Exception as error:
                result = dict(hook_id=name, version=None, passed=False,
                              details=dict(invalid_or_raised=True, **_error(error)))
            self._ledger['hooks'].append(dict(stage=stage, callable=name, utc=_utc(), result=result))
            if not result['passed']:
                failed.append(result['hook_id'])
        if failed:
            self._save()
            raise ValidationHookFailed(f'Validation hooks blocked {stage}: {failed}')

    def _transition(self, stage):
        if STAGES.index(stage) != STAGES.index(self.stage) + 1:
            raise InvalidTransition(f'Cannot move from {self.stage} to {stage}')
        self._ledger['transitions'].append({'from': self.stage, 'to': stage, 'utc': _utc()})
        self._ledger['stage'] = stage

    def _advance(self, stage, field, record):
        self._run_hooks(stage, record)
        self._ledger[field] = record
        self._transition(stage)
        self._save()

    # ------------------------------------------------------------------ stages
    def validate(self, train_validation_check_fn=None):
        """A: record declared identities, refuse empty jobs, run checks and hooks."""
        self._require('CREATED', 'validate')
        if not self._ledger['jobs']:
            raise ValueError('Refusing to validate a plan with no jobs')
        identities = dict(dataset_fingerprint=self.plan.dataset_fingerprint,
                          split_identities=self.plan.split_identities)
        check = None
        if train_validation_check_fn is not None:
            try:
                check = _json_copy(train_validation_check_fn(_freeze(_json_copy(identities))))
            except Exception as error:
                self._failure('A_VALIDATED', error)
                self._save()
                raise
        self._advance('A_VALIDATED', 'validation',
                      dict(identities=identities, check=check, job_count=len(self._ledger['jobs']), utc=_utc()))
        return self

    def _job_dir(self, job_id):
        return self.run_dir / 'jobs' / job_id

    def _verify_succeeded(self):
        for job_id, entry in sorted(self._ledger['jobs'].items()):
            if entry['status'] == 'succeeded':
                _verify_sealed(self._job_dir(job_id), entry['artifacts'], f'job {job_id}')

    def _quarantine(self, job_id):
        entry = self._ledger['jobs'][job_id]
        open_attempts = [a for a in entry['attempts'] if a['outcome'] is None]
        source = self._job_dir(job_id)
        if not open_attempts and not source.exists():
            return
        number = entry['attempts'][-1]['number'] if entry['attempts'] else 0
        relative = None
        if source.exists() or source.is_symlink():
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            relative = f'quarantine/{job_id}-attempt{number}-{stamp}'
            (self.run_dir / 'quarantine').mkdir(exist_ok=True)
            _rename_no_replace(source, self.run_dir / relative)
        for attempt in open_attempts:
            attempt.update(outcome='interrupted', quarantined_to=relative)
        self._ledger['quarantines'].append(dict(
            job_id=job_id, attempt=number, path=relative, utc=_utc(),
            reason='job directory or attempt without a recorded outcome (interrupted run)'))
        self._save()

    def _run_job(self, job, fit_fn):
        job_id = job['job_id']
        entry = self._ledger['jobs'][job_id]
        attempt = dict(number=len(entry['attempts']) + 1, started_utc=_utc(), outcome=None)
        entry['attempts'].append(attempt)
        self._save()  # a crash from here on leaves the job pending with an open attempt
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(parents=True)
        began = time.perf_counter()
        try:
            record = fit_fn(dict(job), job_dir)
            if not isinstance(record, Mapping):
                raise TypeError('fit_fn must return a JSON mapping record')
            record = _json_copy(record)
            artifacts = _seal(job_dir)
        except Exception as error:
            wall = time.perf_counter() - began
            attempt.update(outcome='failed', finished_utc=_utc())
            entry.update(status='failed', wall_seconds=wall, failure=_error(error))
            self._failure('B_FITTED', error, job_id)
        else:
            wall = time.perf_counter() - began
            attempt.update(outcome='succeeded', finished_utc=_utc())
            entry.update(status='succeeded', record=record, artifacts=artifacts, wall_seconds=wall)
        self._ledger['resources'].append(dict(stage='B_FITTED', job_id=job_id, wall_seconds=wall,
                                              process_high_water_mark=process_high_water_mark(),
                                              max_rss_bytes=self.max_rss_bytes))
        self._save()

    def fit(self, fit_fn):
        """B: run pending jobs via ``fit_fn(job_dict, job_dir) -> dict``; resume-safe."""
        self._require('A_VALIDATED', 'fit')
        if not callable(fit_fn):
            raise TypeError('fit_fn must be callable')
        self._verify_succeeded()
        jobs = self._ledger['jobs']
        for job_id in sorted(jobs):
            if jobs[job_id]['status'] == 'pending':
                self._quarantine(job_id)
        for job_id in sorted(jobs):
            if jobs[job_id]['status'] != 'pending':
                continue
            self._run_job(jobs[job_id]['spec'], fit_fn)
            peak = process_high_water_mark()['bytes']
            remaining = [k for k, v in jobs.items() if v['status'] == 'pending']
            if self.max_rss_bytes is not None and remaining and peak > self.max_rss_bytes:
                self._failure('B_FITTED', RuntimeError(
                    f'process high-water mark {peak} bytes exceeds max_rss_bytes {self.max_rss_bytes}; '
                    f'{len(remaining)} jobs left pending'))
                self._ledger['failures'][-1]['error_type'] = 'ResourceCeilingExceeded'
                self._save()
                return self
        summary = dict(succeeded=sorted(k for k, v in jobs.items() if v['status'] == 'succeeded'),
                       failed=sorted(k for k, v in jobs.items() if v['status'] == 'failed'), utc=_utc())
        self._advance('B_FITTED', 'fit', summary)
        return self

    def select(self, select_fn):
        """C: ``select_fn(records)`` sees every job's fit record or failure; no test data."""
        self._require('B_FITTED', 'select')
        self._verify_succeeded()
        inputs = [dict(job_id=job_id, spec=entry['spec'], status=entry['status'], record=entry['record'],
                       failure=entry['failure'], wall_seconds=entry['wall_seconds'])
                  for job_id, entry in sorted(self._ledger['jobs'].items())]
        try:
            result = select_fn(tuple(_freeze(_json_copy(item)) for item in inputs))
            if not isinstance(result, Mapping):
                raise TypeError('select_fn must return a JSON mapping')
            result = _json_copy(result)
            selected = result.get('selected_job_ids')
            succeeded = {item['job_id'] for item in inputs if item['status'] == 'succeeded'}
            if (not isinstance(selected, list) or not selected or len(set(selected)) != len(selected)
                    or not set(selected) <= succeeded):
                raise ValueError('selected_job_ids must be a nonempty list of distinct succeeded job ids')
        except Exception as error:
            self._failure('C_SELECTED', error)
            self._save()
            raise
        self._advance('C_SELECTED', 'selection', dict(record=result, inputs_fingerprint=fingerprint_payload(inputs),
                                                      utc=_utc()))
        return self

    def lock(self):
        """D: bind config, plan, selection and succeeded artifacts into lock.json."""
        self._require('C_SELECTED', 'lock')
        self._verify_succeeded()
        ledger = self._ledger
        manifest = dict(
            schema_version=1, experiment_id=ledger['experiment_id'], run_name=self.run_name,
            plan_fingerprint=ledger['plan_fingerprint'], config_fingerprint=ledger['config_fingerprint'],
            dataset_fingerprint=ledger['dataset_fingerprint'], split_identities=ledger['split_identities'],
            test_identity=ledger['test_identity'], approval_status=ledger['approval_status'],
            selection_fingerprint=fingerprint_payload(ledger['selection']),
            jobs=[dict(job_id=job_id, spec_fingerprint=fingerprint_payload(entry['spec']), artifacts=entry['artifacts'])
                  for job_id, entry in sorted(ledger['jobs'].items()) if entry['status'] == 'succeeded'])
        record = dict(manifest=manifest, fingerprint=fingerprint_payload(manifest), path=LOCK_NAME, utc=_utc())
        self._run_hooks('D_LOCKED', record)
        encoded = (canonical_json(manifest) + '\n').encode('utf-8')
        path = self.run_dir / LOCK_NAME
        if path.exists() or path.is_symlink():
            # Only an identical lock from an interrupted earlier call is accepted.
            if path.is_symlink() or path.read_bytes() != encoded:
                raise ArtifactIntegrityError('An existing lock.json differs from this lock manifest')
        else:
            write_artifact_once(path, encoded)
            os.chmod(path, 0o444)
        ledger['lock'] = record
        self._transition('D_LOCKED')
        self._save()
        return self

    def _verify_lock(self):
        lock = self._ledger['lock']
        path = self.run_dir / LOCK_NAME
        try:
            content = path.read_bytes() if path.is_file() and not path.is_symlink() else None
        except OSError:
            content = None
        if (content != (canonical_json(lock['manifest']) + '\n').encode('utf-8')
                or fingerprint_payload(lock['manifest']) != lock['fingerprint']):
            raise ArtifactIntegrityError('lock.json differs from the ledger lock record')
        for item in lock['manifest']['jobs']:
            entry = self._ledger['jobs'][item['job_id']]
            if entry['status'] != 'succeeded' or entry['artifacts'] != item['artifacts']:
                raise ArtifactIntegrityError(f'ledger job {item["job_id"]} differs from the lock manifest')
            _verify_sealed(self._job_dir(item['job_id']), item['artifacts'], f'locked job {item["job_id"]}')

    def release_test(self, authorization, test_identity, predict_fn):
        """E: single-shot, gated test release; ``predict_fn(job, locked_dir, output_dir) -> dict``."""
        release = self._ledger['release']
        if release is not None:
            raise InvalidTransition(f'Test release is single-shot; a release started at {release["started_utc"]}')
        self._require('D_LOCKED', 'release_test')

        def reject(reason):
            self._ledger['release_rejections'].append(dict(
                utc=_utc(), reason=reason,
                authorization=authorization.as_dict() if isinstance(authorization, TestReleaseAuthorization)
                else type(authorization).__name__,
                supplied_test_identity=test_identity if isinstance(test_identity, str) else None))
            self._save()
            raise ReleaseRejected(reason)

        if not self.allow_test_release:
            reject('test release disabled: construct StagedRun with allow_test_release=True')
        if self._ledger['approval_status'] != APPROVED:
            reject(f'run plan approval_status is {self._ledger["approval_status"]!r}, not {APPROVED!r}')
        if not isinstance(authorization, TestReleaseAuthorization):
            reject('authorization must be a TestReleaseAuthorization instance')
        if authorization.approval_status != APPROVED:
            reject(f'authorization approval_status is {authorization.approval_status!r}, not {APPROVED!r}')
        if authorization.config_fingerprint != self._ledger['config_fingerprint']:
            reject('authorization names a different config fingerprint')
        if authorization.lock_fingerprint != self.lock_fingerprint:
            reject('authorization names a different lock fingerprint')
        if test_identity != self._ledger['test_identity']:
            reject('supplied test identity differs from the declared test identity')
        if not callable(predict_fn):
            raise TypeError('predict_fn must be callable')
        try:
            self._verify_lock()
        except ArtifactIntegrityError as error:
            self._failure('E_TEST_RELEASED', error)
            self._save()
            raise
        proposed = dict(authorization=authorization.as_dict(), test_identity=test_identity,
                        config_fingerprint=self._ledger['config_fingerprint'],
                        lock_fingerprint=self.lock_fingerprint, started_utc=_utc())
        self._run_hooks('E_TEST_RELEASED', proposed)
        # Cross-run single shot: one release per declared test identity in this results root.
        registry = self.run_dir.parent / RELEASE_REGISTRY
        registry.mkdir(exist_ok=True)
        claim = registry / f'{fingerprint_payload(test_identity)}.json'
        try:
            write_artifact_once(claim, (canonical_json(dict(proposed, run_name=self.run_name)) + '\n').encode())
        except FileExistsError:
            reject('this test identity was already released by a run in this results root')
        release = self._ledger['release'] = dict(proposed, jobs={}, pre_verification='passed',
                                                 post_verification=None, completed_utc=None)
        self._save()  # the single shot is consumed before any prediction runs
        outputs = self.run_dir / 'test_release'
        outputs.mkdir()
        for item in self._ledger['lock']['manifest']['jobs']:
            job_id = item['job_id']
            output_dir = outputs / job_id
            output_dir.mkdir()
            began = time.perf_counter()
            try:
                record = predict_fn(dict(self._ledger['jobs'][job_id]['spec']), self._job_dir(job_id), output_dir)
                if not isinstance(record, Mapping):
                    raise TypeError('predict_fn must return a JSON mapping record')
                result = dict(status='succeeded', record=_json_copy(record), artifacts=_seal(output_dir),
                              failure=None)
            except Exception as error:
                result = dict(status='failed', record=None, artifacts=None, failure=_error(error))
                self._failure('E_TEST_RELEASED', error, job_id)
            result['wall_seconds'] = time.perf_counter() - began
            release['jobs'][job_id] = result
            self._ledger['resources'].append(dict(stage='E_TEST_RELEASED', job_id=job_id,
                                                  wall_seconds=result['wall_seconds'],
                                                  process_high_water_mark=process_high_water_mark(),
                                                  max_rss_bytes=self.max_rss_bytes))
            self._save()
        try:
            self._verify_lock()
        except ArtifactIntegrityError as error:
            release['post_verification'] = 'failed'
            self._failure('E_TEST_RELEASED', error)
            self._save()
            raise
        release.update(post_verification='passed', completed_utc=_utc())
        self._transition('E_TEST_RELEASED')
        self._save()
        return self

    def publish(self, publish_fn=None, *, contents=None):
        """F: publish JSON results (``contents`` or ``publish_fn(snapshot)``) by no-replace rename."""
        self._require('E_TEST_RELEASED', 'publish')
        if (publish_fn is None) == (contents is None):
            raise ValueError('Supply exactly one of publish_fn or contents')
        if publish_fn is not None:
            contents = publish_fn(self.snapshot())
        if not isinstance(contents, Mapping) or not contents:
            raise ValueError('A nonempty mapping of relative .json paths to JSON values is required')
        payload = {}
        for name, value in contents.items():
            identifier = str(_relative(name))
            if identifier in _RESERVED_PUBLICATION or not identifier.endswith('.json'):
                raise ValueError(f'Publication path is reserved or not .json: {identifier}')
            payload[identifier] = _json_copy(value)
        payload['run_ledger.json'] = _json_copy(self._ledger)
        payload['lock_manifest.json'] = self._ledger['lock']['manifest']
        destination = self.run_dir / PUBLICATION_NAME
        self._run_hooks('F_PUBLISHED', dict(files=sorted(payload)))
        try:
            if destination.exists() or destination.is_symlink():
                raise FileExistsError(f'Refusing to replace an existing publication: {destination}')
            manifest = self._publish_atomic(destination, payload)
        except OSError as error:
            self._failure('F_PUBLISHED', error)
            self._save()
            raise
        self._ledger['publication'] = dict(path=PUBLICATION_NAME, files=manifest['files'], utc=_utc(),
                                           artifacts_manifest_sha256=sha256_file(destination / 'artifacts.json'))
        self._transition('F_PUBLISHED')
        self._save()
        return destination

    def _publish_atomic(self, destination, payload):
        """Local analogue of provenance.atomic_record for a run directory destination."""
        stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=self.run_dir))
        try:
            files = []
            for identifier in sorted(payload):
                path = stage / identifier
                encoded = (canonical_json(payload[identifier]) + '\n').encode('utf-8')
                write_artifact_once(path, encoded)
                files.append(dict(path=identifier, bytes=len(encoded), sha256=sha256_file(path)))
            manifest = dict(schema_version=1, files=files)
            write_artifact_once(stage / 'artifacts.json', (canonical_json(manifest) + '\n').encode('utf-8'))
            verify_artifacts(stage)
            _rename_no_replace(stage, destination)
        except BaseException:
            if stage.exists():
                shutil.rmtree(stage)
            raise
        return manifest
