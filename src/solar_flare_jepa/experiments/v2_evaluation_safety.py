"""Development fitting guards and complete-study locks for canonical V2 records.

These checks establish consistency of supplied artifacts and declarations. They
cannot authenticate past data access or the caller's code/protocol attestations.
DevelopmentRun always disables test release and publishes descriptive artifacts
at D_LOCKED. StudyLock is separate, generic infrastructure: it grants no release
approval and preserves every existing StagedRun authorization gate.
"""
from collections.abc import Mapping
from copy import copy
import json
import os

from solar_flare_jepa.evaluation.records import (
    EvaluationIdentity, EvaluationRecord, support_fingerprint, validate_fitting_artifacts,
)
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from solar_flare_jepa.training.controlled import (
    ARMS, MODEL_KIND, ControlledConfig, _validation_identity, _window_record, _windows, check_paired_cohort,
)
from solar_flare_jepa.training.core import window_snapshot
from solar_flare_jepa.training.normalization import Normalization, training_snapshot
from .provenance import _relative, _source_path
from .v2_interfaces import evaluation_identity_fields
from .v2_runner import (
    ArtifactIntegrityError, IdentityMismatch, ReleaseRejected,
    STAGES, StagedRun, _json_copy, _name, write_artifact_once,
)

_IDENTITY_DECLARATIONS = ('experiment_id', 'code_fingerprint', 'data_provenance_fingerprint',
                          'split_fingerprint', 'protocol_fingerprint')
_SUPPORT_KEYS = ('training_fingerprint', 'normalization_fingerprint', 'train_windows', 'validation')
_DEVELOPMENT_FILES = {'artifacts.json', 'run_ledger.json', 'lock_manifest.json', 'development_status.json'}


def check_comparator_cohort(records):
    """Bind controlled and comparator records to identical fitting/selection support.

    This checks supplied support identities, not completeness of an experimental
    plan. The mandatory fitting guard separately checks every planned arm/seed.
    """
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError('A nonempty cohort of model records is required')
    records = [_json_copy(record) for record in records]
    if any(not isinstance(record, dict) or any(key not in record for key in _SUPPORT_KEYS)
           for record in records):
        raise ValueError('Cohort records require complete fitting and validation identities')
    for key in _SUPPORT_KEYS:
        if len({canonical_json(record[key]) for record in records}) != 1:
            raise ValueError(f'Comparator cohort {key} differs')
    return dict(records=len(records), support_keys=list(_SUPPORT_KEYS))


def _declared_inputs(plan, provenance, training, validation, embargo_ns):
    if plan.config.get('execution_mode', 'DEVELOPMENT_ONLY') != 'DEVELOPMENT_ONLY':
        raise ValueError('M4B fitting guards require execution_mode DEVELOPMENT_ONLY')
    declarations = plan.config.get('evaluation_identity')
    if not isinstance(declarations, dict) or set(declarations) != set(_IDENTITY_DECLARATIONS):
        raise ValueError('Plan config requires the complete evaluation_identity declarations')
    if declarations['experiment_id'] != plan.experiment_id:
        raise ValueError('Evaluation experiment identity differs from the run plan')
    if (not isinstance(provenance, Mapping) or not provenance
            or provenance.get('code_fingerprint') != declarations['code_fingerprint']):
        raise ValueError('Code provenance differs from the plan evaluation declaration')
    if plan.dataset_fingerprint != training.context.dataset_fingerprint:
        raise ValueError('Plan dataset identity differs from actual training artifacts')
    if (plan.split_identities.get('train') != training.split_fingerprint
            or plan.split_identities.get('validation') != validation.split_fingerprint):
        raise ValueError('Plan split identities differ from actual train/validation artifacts')
    if validation.as_dict().get('partition', {}).get('name') != 'validation':
        raise ValueError('Fitting guard requires the validation partition')
    matrix = [(job.arm, job.seed) for job in plan.jobs]
    if not matrix or len(set(matrix)) != len(matrix):
        raise ValueError('Planned arm/seed matrix must be nonempty and contain no duplicates')
    supported = set(ARMS) | {'tcn', 'quantile_linear'}
    if any(arm not in supported for arm, _ in matrix):
        raise ValueError('Fitting guard accepts controlled arms, tcn and quantile_linear jobs')
    normalization = Normalization.fit(training)
    # Eagerly refuse invalid temporal declarations; the same call runs per job.
    validate_fitting_artifacts(training, normalization, validation.context, validation.targets,
                               embargo_ns=embargo_ns)
    return declarations, normalization


def _model_configuration(record, job):
    """Validate the actual recipe, run, seed, kind and model-id declarations."""
    kind, config = record.get('model_kind'), record.get('config')
    if kind == MODEL_KIND:
        parsed = ControlledConfig.from_dict(config)
        arm, seed = parsed.schedule.arm, parsed.seed
        expected_id = f'v2_{arm}'
        if record.get('arm') != arm:
            raise ValueError('Model record arm differs from its configuration')
        recipe, run_identity = parsed.recipe_fingerprint, parsed.run_fingerprint
    else:
        from solar_flare_jepa.training.comparators import (
            ComparatorSchedule, LINEAR_KIND, TCN_KIND, QuantileLinearConfig, TcnConfig,
        )
        if kind == TCN_KIND and isinstance(config, dict) and set(config) == {'tcn', 'schedule'}:
            parsed = TcnConfig(**config['tcn'])
            ComparatorSchedule(**config['schedule'])
            arm, expected_id = 'tcn', 'v2_tcn_quantile'
        elif kind == LINEAR_KIND and isinstance(config, dict) and set(config) == {'linear'}:
            parsed = QuantileLinearConfig(**config['linear'])
            arm, expected_id = 'quantile_linear', 'v2_quantile_linear'
        else:
            raise ValueError('Unsupported or malformed V2 model configuration')
        seed = parsed.seed
        run_identity = fingerprint_payload(config)
        recipe = fingerprint_payload({key: {name: value for name, value in part.items() if name != 'seed'}
                                      for key, part in config.items()})
    if ((arm, seed) != (job['arm'], job['seed']) or record.get('seed') != seed
            or record.get('model_id') != expected_id
            or record.get('recipe_fingerprint') != recipe or record.get('run_fingerprint') != run_identity):
        raise ValueError('Model kind/arm/seed/configuration identity differs from its planned job')
    declared = job['parameters'].get('model_config')
    if declared is not None and canonical_json(declared) != canonical_json(config):
        raise ValueError('Emitted model configuration differs from the planned job configuration')
    return parsed.architecture.max_train_windows if kind == MODEL_KIND else parsed.max_train_windows


def _check_jobs(snapshot, plan, training, validation, embargo_ns):
    declarations, normalization = _declared_inputs(plan, snapshot.get('provenance'), training, validation,
                                                    embargo_ns)
    planned = {job.job_id: job.as_dict() for job in plan.jobs}
    jobs = snapshot['jobs']
    if set(jobs) != set(planned):
        raise ValueError('Actual jobs differ from the complete planned arm/seed matrix')
    transition = snapshot.get('proposed_transition', {})
    selection = transition.get('record') if transition.get('to') == 'C_SELECTED' else snapshot.get('selection')
    if selection is not None:
        selected = selection.get('record', {}).get('selected_job_ids', ())
        if len(selected) != len(planned) or set(selected) != set(planned):
            raise ValueError('Selection must retain the complete planned arm/seed matrix')
    all_windows = _windows(training, normalization, 1)
    models, evaluations = [], []
    for job_id, specification in planned.items():
        entry = jobs[job_id]
        if canonical_json(_json_copy(entry['spec'])) != canonical_json(specification):
            raise ValueError('Stored job specification differs from the run plan')
        if entry['status'] != 'succeeded':
            raise ValueError('Complete planned arm/seed matrix requires every job to succeed')
        payload = _json_copy(entry['record'])
        if not isinstance(payload, dict) or set(payload) != {'model_record', 'evaluation_record'}:
            raise ValueError('Each fit job requires full model_record and canonical evaluation_record')
        record = payload['model_record']
        if not isinstance(record, dict):
            raise ValueError('A full model record is required')
        cap = _model_configuration(record, specification)
        expected = dict(training_fingerprint=training.fingerprint,
                        normalization_fingerprint=normalization.fingerprint,
                        training_dataset_fingerprint=training.context.dataset_fingerprint,
                        spec_fingerprint=training.spec.fingerprint,
                        train_windows=_window_record(all_windows, all_windows.subsample(cap), cap),
                        validation=_validation_identity(validation))
        for key, value in expected.items():
            if record.get(key) != value:
                raise ValueError(f'Model {key} differs from actual fitting/validation artifacts')
        evaluation = EvaluationRecord.from_dict(payload['evaluation_record'])
        identity = EvaluationIdentity(**evaluation_identity_fields(record, **declarations))
        if evaluation.identity.as_dict() != identity.as_dict():
            raise ValueError('Canonical evaluation identity differs from the model/run plan')
        if (evaluation.prediction.model_id != record['model_id']
                or evaluation.support_fingerprint != support_fingerprint(validation.targets)):
            raise ValueError('Canonical evaluation model or validation support differs')
        kind = record['model_kind']
        options = record['config']['architecture'] if kind == MODEL_KIND else record['config'][
            'tcn' if kind == 'tcn_quantile' else 'linear']
        if tuple(options['quantiles']) != evaluation.prediction.quantile_levels:
            raise ValueError('Canonical evaluation quantile levels differ from model configuration')
        validate_fitting_artifacts(training, normalization, validation.context, evaluation.targets,
                                   identity=identity, embargo_ns=embargo_ns)
        models.append(record)
        evaluations.append(evaluation.fingerprint)
    check_comparator_cohort(models)
    controlled = [record for record in models if record['model_kind'] == MODEL_KIND]
    if controlled:
        check_paired_cohort(controlled)
    return dict(job_count=len(models), planned_matrix=[list(pair) for pair in sorted(
        (job.arm, job.seed) for job in plan.jobs)], evaluation_fingerprints=evaluations,
        job_payload_fingerprints={job_id: fingerprint_payload(_json_copy(jobs[job_id]['record']))
                                  for job_id in sorted(jobs)},
        embargo_ns=embargo_ns, status='VALIDATED_DECLARED_FITTING_ARTIFACTS')


def register_fitting_guard(run, training, validation, *, embargo_ns):
    """Install actual-artifact and complete-job checks before B_FITTED/C_SELECTED/D_LOCKED.

    Job callbacks must return exactly ``model_record`` and ``evaluation_record``.
    The plan holds complete caller declarations in ``config['evaluation_identity']``;
    optional job ``parameters['model_config']`` binds each exact emitted recipe.
    Hooks are process-local: callers resuming raw StagedRun must reinstall them.
    DevelopmentRun does this automatically and additionally disables test release.
    """
    if not isinstance(run, StagedRun):
        raise TypeError('Fitting guards require a StagedRun')
    training, validation = training_snapshot(training), window_snapshot(validation)
    _declared_inputs(run.plan, run.snapshot().get('provenance'), training, validation, embargo_ns)
    def guard(snapshot):
        details = _check_jobs(snapshot, run.plan, training, validation, embargo_ns)
        return dict(hook_id='v2-actual-fitting-and-complete-jobs', version='1', passed=True, details=details)
    for stage in ('B_FITTED', 'C_SELECTED', 'D_LOCKED'):
        run.register_hook(stage, guard)
    return run


class DevelopmentRun(StagedRun):
    """Always descriptive, mandatory-guard development run with no release mode."""

    def __init__(self, root, run_name, plan, *, training, validation, embargo_ns, provenance,
                 max_rss_bytes=None):
        self._development_training = training_snapshot(training)
        self._development_validation = window_snapshot(validation)
        self._development_embargo_ns = embargo_ns
        _declared_inputs(plan, provenance, self._development_training, self._development_validation, embargo_ns)
        super().__init__(root, run_name, plan, allow_test_release=False,
                         max_rss_bytes=max_rss_bytes, provenance=provenance)
        register_fitting_guard(self, self._development_training, self._development_validation,
                               embargo_ns=embargo_ns)
        if self.stage == 'D_LOCKED':
            self._verify_lock()

    def _verify_lock(self):
        """Recheck artifacts and D-recorded payloads, including accounting.

        The hook ledger detects accidental drift; it is not authenticated
        against a user deliberately rewriting both the payload and its seal.
        """
        super()._verify_lock()
        seals = [entry['result'].get('details', {}).get('job_payload_fingerprints')
                 for entry in self._ledger['hooks']
                 if entry['stage'] == 'D_LOCKED'
                 and entry['result'].get('hook_id') == 'v2-actual-fitting-and-complete-jobs'
                 and entry['result'].get('passed') is True]
        current = {job_id: fingerprint_payload(entry['record'])
                   for job_id, entry in sorted(self._ledger['jobs'].items())}
        if not seals or any(seal != current for seal in seals):
            raise ArtifactIntegrityError('Development job payload differs from its D_LOCKED fingerprint seal')

    def release_test(self, authorization, test_identity, predict_fn):
        raise ReleaseRejected('DevelopmentRun never releases test data')

    def publish_development(self, contents):
        """Publish once at D_LOCKED, preserving the historical runner stage."""
        self._require('D_LOCKED', 'publish_development')
        _check_jobs(self.snapshot(), self.plan, self._development_training,
                    self._development_validation, self._development_embargo_ns)
        self._verify_lock()
        if not isinstance(contents, Mapping) or not contents:
            raise ValueError('Development contents must be a nonempty mapping of relative JSON paths')
        payload = {}
        for name, value in contents.items():
            path = str(_relative(name))
            if path in _DEVELOPMENT_FILES or not path.endswith('.json'):
                raise ValueError('Development publication paths must be nonreserved relative JSON files')
            payload[path] = _json_copy(value)
        payload['run_ledger.json'] = _json_copy(self.snapshot())
        payload['lock_manifest.json'] = _json_copy(self.snapshot()['lock']['manifest'])
        payload['development_status.json'] = dict(
            schema_version=1, analysis_status='DESCRIPTIVE_ONLY', inference_status='INFERENCE_UNAVAILABLE',
            execution_mode='DEVELOPMENT_ONLY',
            m3_verdict='NO_VALIDATED_REPLACEMENT',
            inference_reason='No validated replacement inference method is available',
            classical_acceptance_status='POLICY_UNAVAILABLE',
            approval_status=self.plan.approval_status, test_released=False,
            limitations='Supplied-artifact consistency; caller provenance is not authenticated')
        destination = self.run_dir / 'development_publication'
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(str(destination))
        self._publish_atomic(destination, payload)
        for path in destination.rglob('*'):
            if path.is_file():
                os.chmod(path, 0o444)
        return destination


class StudyLock:
    """Write-once complete fold mapping and generic E_TEST_RELEASED guard.

    It supplies no authorization. Construction registers guards on every supplied
    run, including resumed runs. Each release re-reads every persisted fold ledger
    and lock, verifies sealed artifacts and the immutable complete-study manifest.
    """

    def __init__(self, root, study_id, runs):
        self.root = _source_path(root)
        self.study_id = _name(study_id, 'study id')
        if not isinstance(runs, Mapping) or not runs:
            raise ValueError('StudyLock requires a complete nonempty fold mapping')
        self.runs = dict(runs)
        for fold, run in self.runs.items():
            _name(fold, 'fold id')
            if not isinstance(run, StagedRun) or run.root != self.root:
                raise ValueError('Every fold run must use the same declared results root')
        if len({run.run_dir for run in self.runs.values()}) != len(self.runs):
            raise ValueError('Every fold must name a distinct run')
        parent = self.root / 'results' / 'v2_studies'
        _source_path(parent)
        parent.mkdir(parents=True, exist_ok=True)
        self.directory = parent / self.study_id
        _source_path(self.directory)
        self.directory.mkdir(exist_ok=True)
        self.path = self.directory / 'lock.json'
        if self.path.exists() or self.path.is_symlink():
            self._verify_manifest()
        for run in self.runs.values():
            run.register_hook('E_TEST_RELEASED', self._release_guard)

    def _manifest(self):
        folds = []
        for fold, run in sorted(self.runs.items()):
            # Re-open the persisted state, rather than trusting a stale object.
            ledger_path = run.run_dir / 'ledger.json'
            ledger = json.loads(ledger_path.read_text())
            if ledger.get('plan_fingerprint') != run.plan.fingerprint:
                raise IdentityMismatch('Fold run plan differs from its persisted ledger')
            stage = ledger.get('stage')
            if stage not in STAGES or STAGES.index(stage) < STAGES.index('D_LOCKED'):
                raise ValueError('Every declared fold must reach D_LOCKED before study lock or release')
            if ledger.get('provenance') != _json_copy(run.snapshot().get('provenance')):
                raise IdentityMismatch('Fold run provenance differs from its persisted ledger')
            live = copy(run)
            live._ledger = ledger
            live._check_resume()
            live._verify_lock()
            folds.append(dict(fold_id=fold, run_name=run.run_name,
                              plan_fingerprint=run.plan.fingerprint,
                              config_fingerprint=run.plan.config_fingerprint,
                              lock_fingerprint=ledger['lock']['fingerprint'],
                              test_identity=run.plan.test_identity))
        return dict(schema_version=1, kind='solarjepa_v2_complete_study_lock',
                    study_id=self.study_id, folds=folds)

    def _verify_manifest(self):
        if self.path.is_symlink() or not self.path.is_file():
            raise ArtifactIntegrityError('Complete study lock has not been written')
        try:
            recorded = json.loads(self.path.read_text())
        except (ValueError, OSError) as error:
            raise ArtifactIntegrityError('Study lock is unreadable') from error
        manifest = self._manifest()
        expected = dict(manifest=manifest, fingerprint=fingerprint_payload(manifest))
        if recorded != expected:
            raise IdentityMismatch('Immutable complete-study fold mapping or lock identities differ')
        return expected

    def lock(self):
        manifest = self._manifest()
        record = dict(manifest=manifest, fingerprint=fingerprint_payload(manifest))
        if self.path.exists() or self.path.is_symlink():
            return self._verify_manifest()
        write_artifact_once(self.path, (canonical_json(record) + '\n').encode('utf-8'))
        os.chmod(self.path, 0o444)
        return record

    def _release_guard(self, snapshot):
        record = self._verify_manifest()
        return dict(hook_id='v2-complete-study-lock', version='1', passed=True,
                    details=dict(study_id=self.study_id, study_lock_fingerprint=record['fingerprint'],
                                 fold_count=len(self.runs)))
