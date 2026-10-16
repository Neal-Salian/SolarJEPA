"""Serial production pilot orchestration, gated separately from implementation.

Importing or asking for metadata does not load science inputs or construct a
model. Execution requires an external approval and an absent reserved directory.
There is no resume/retry entry point, test release or arbitrary report publisher.
"""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from solar_flare_jepa.forecasting.contracts import canonical_json
from .config import read_finite_json
from .v2_pilot_protocol import (DESIGN_FINGERPRINT, EXPERIMENT_ID, evaluation_identity,
                                load_protocol, validate_execution)
from .v2_resource_controls import (ProcessJob, ProcessSupervisor, ResourceLimits,
                                   ResourceMonitoringUnavailable, _processes)
from .provenance import _rename_no_replace
from .v2_runner import JobSpec, RunConfig, _json_copy, _verify_sealed, write_artifact_once


class StorageUnavailable(RuntimeError):
    """The reserved output filesystem is below the frozen free-space floor."""


def check_storage(path, minimum_free_bytes):
    path = Path(path)
    while not path.exists():
        path = path.parent
    free = shutil.disk_usage(path).free
    if free < minimum_free_bytes:
        raise StorageUnavailable(f'Output storage free {free} bytes is below required {minimum_free_bytes}')
    return dict(path=str(path), free_bytes=free, minimum_free_bytes=minimum_free_bytes)


class PilotSupervisor(ProcessSupervisor):
    """Reuse process supervision with a mandatory gate before every attempt."""
    def __init__(self, *args, minimum_free_bytes, **kwargs):
        self.minimum_free_bytes = minimum_free_bytes
        super().__init__(*args, **kwargs)
        if self.limits.max_retries != 0:
            raise ValueError('Protocol v1 permits zero automatic retries')

    @staticmethod
    def _terminate(process):
        """Hard-stop and reap even if the pilot alarm interrupts the TERM grace.

        Keep the historically pinned generic supervisor unchanged. Propagate
        interruptions after cleanup so its ledger remains conservatively
        incomplete; they never permit another worker or completed publication.
        """
        def signal_group(value):
            try:
                os.killpg(process.pid, value)
            except ProcessLookupError:
                pass
            except PermissionError:
                if any(row['group'] == process.pid and not row['state'].startswith('Z')
                       for row in _processes()):
                    raise ResourceMonitoringUnavailable('Cannot terminate a live worker process group')
        try:
            signal_group(signal.SIGTERM)
            try:
                process.wait(timeout=.2)
            except subprocess.TimeoutExpired:
                pass
        finally:
            # SIGALRM/KeyboardInterrupt during wait must not skip SIGKILL.
            try:
                signal_group(signal.SIGKILL)
            finally:
                process.wait(timeout=1)

    def _run_pending(self):
        for job in self.jobs:
            if self._ledger['jobs'][job.job_id]['status'] != 'pending':
                raise RuntimeError('Pilot never resumes completed or failed attempts')
            self._charge()
            if self._ledger['consumed_wall_seconds'] >= self.limits.total_wall_seconds:
                self._ledger['stop_reason'] = 'TOTAL_WALL_BUDGET'
                return
            try:
                check_storage(self.directory, self.minimum_free_bytes)
            except (StorageUnavailable, OSError) as error:
                self._ledger.update(stop_reason='OUTPUT_STORAGE_UNAVAILABLE', storage_error=str(error))
                self._save()
                return
            self._attempt(job)
            if self._ledger['stop_reason'] is not None:
                return
            if self._ledger['jobs'][job.job_id]['status'] != 'succeeded':
                self._ledger['stop_reason'] = 'JOB_FAILED'
                return


def process_plan(root, approval_file, supervisor_directory, design):
    resources = design['resources']
    limits = ResourceLimits(max_rss_bytes=resources['max_rss_bytes'],
        total_wall_seconds=resources['total_wall_seconds'], threads=resources['threads'],
        max_retries=resources['max_retries'], poll_interval_seconds=resources['poll_interval_seconds'])
    jobs = [ProcessJob(job['job_id'], (sys.executable, '-c',
        'from solar_flare_jepa.experiments.v2_pilot_worker import main; raise SystemExit(main())', '--root', str(Path(root).resolve()),
        '--approval', str(Path(approval_file).absolute()), '--job-id', job['job_id'],
        '--supervisor-directory', str(supervisor_directory)), job['timeout_seconds']) for job in design['jobs']]
    return jobs, limits


@contextmanager
def _deadline(seconds):
    """Include preparation/finalization in the Unix pilot wall-clock deadline."""
    if seconds <= 0:
        raise TimeoutError('Total pilot wall budget exhausted')
    def expired(signum, frame):
        raise TimeoutError('Total pilot wall budget exhausted during driver finalization')
    previous = signal.getsignal(signal.SIGALRM)
    timer = signal.getitimer(signal.ITIMER_REAL)
    if timer[0] > 0:
        raise RuntimeError('Pilot cannot share an existing process alarm')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _load_sealed(supervisor, design):
    supervisor._validate_ledger()
    payloads, paths = {}, {}
    for job in design['jobs']:
        entry = supervisor._ledger['jobs'][job['job_id']]
        if entry['status'] != 'succeeded':
            raise ValueError('Complete reporting requires all20 successful processes')
        path = supervisor.directory / entry['artifact_path']
        _verify_sealed(path, entry['artifacts'], job['job_id'])
        paths[job['job_id']] = path
        if job['development_run'] is not None:
            payload = read_finite_json(path / 'result.json')
            if set(payload) != {'model_record', 'evaluation_record'}:
                raise ValueError('Selected worker result has unrecognized report fields')
            payloads[job['job_id']] = payload
    return payloads, paths


def _guarded_runs(context, output, payloads, paths):
    from solar_flare_jepa.data.goes_v2_development import load_development
    from .v2_evaluation_safety import DevelopmentRun
    from .v2_pilot_protocol import validate_data_identity
    bundle = load_development(context['approval']['data_root'])
    validate_data_identity(context, bundle)
    identity = evaluation_identity(context, bundle)
    runs = {}
    for cohort in ('primary', 'alternate_loss'):
        descriptors = [j for j in context['design']['jobs'] if j['development_run'] == cohort]
        specs = [JobSpec(j['arm'], j['seed'], dict(model_config=j['model_config'],
                                                 descriptor_job_id=j['job_id'])) for j in descriptors]
        plan = RunConfig(experiment_id=EXPERIMENT_ID,
            config=dict(execution_mode='DEVELOPMENT_ONLY', evaluation_identity=identity,
                        design_fingerprint=DESIGN_FINGERPRINT, cohort=cohort),
            dataset_fingerprint=bundle.dataset.fingerprint,
            split_identities=bundle.evidence['split_fingerprints'], test_identity='NO_TEST_PARTITION_PERMITTED',
            jobs=specs, approval_status='APPROVED')
        provenance = dict(code_fingerprint=context['runtime']['source_fingerprint'],
            source_files=context['runtime']['source_files'], runtime=context['runtime'],
            execution_binding_fingerprint=context['binding_fingerprint'])
        run = DevelopmentRun(output, cohort, plan, training=bundle.training, validation=bundle.validation,
                             embargo_ns=context['design']['data']['embargo_ns'], provenance=provenance)
        def import_result(job, directory):
            job_id = job['parameters']['descriptor_job_id']
            for name in ('selected.pt', 'result.json', 'binding.json'):
                shutil.copyfile(paths[job_id] / name, directory / name)
            return payloads[job_id]
        run.validate().fit(import_result)
        run.select(lambda entries: dict(selected_job_ids=[j['job_id'] for j in entries],
            criterion='Every fixed planned model selected only on exposed validation; no winner filtering'))
        run.lock()
        runs[cohort] = run
    return runs


def _failure_record(output, supervisor, error, elapsed):
    snapshot = None if supervisor is None else _json_copy(supervisor._ledger)
    record = dict(schema_version=1, status='INCOMPLETE', analysis_status='ENGINEERING_FAILURE_ONLY',
        inference_status='INFERENCE_UNAVAILABLE', inference_reason='NO_VALIDATED_REPLACEMENT',
        model_comparison_published=False, automatic_resume_permitted=False,
        error=dict(type=type(error).__name__, message=str(error)), elapsed_seconds=elapsed,
        supervisor=snapshot)
    write_artifact_once(output / 'pilot_failure.json', (canonical_json(record) + '\n').encode())
    return record


def run_pilot(root, approval_file):
    """Run one explicitly approved pilot, preserving every terminal/pending job."""
    began = time.monotonic()
    context = validate_execution(root, approval_file)
    output = Path(context['approval']['output_root'])
    if output.exists() or output.is_symlink():
        raise FileExistsError('Pilot output already exists; automatic resume is prohibited')
    if not isinstance(approval_file, (str, Path)):
        raise PermissionError('Production driver requires an external execution approval file')
    resources = context['design']['resources']
    check_storage(output, resources['minimum_free_output_bytes'])
    output.mkdir(parents=False, exist_ok=False)
    supervisor, staging, final = None, None, None
    publication_attempted = False
    try:
        with _deadline(resources['total_wall_seconds'] - (time.monotonic() - began)):
            jobs, limits = process_plan(root, approval_file, output / 'supervisor', context['design'])
            supervisor = PilotSupervisor(output / 'supervisor', jobs,
                code_fingerprint=context['runtime']['source_fingerprint'],
                config_fingerprint=context['binding_fingerprint'], limits=limits,
                minimum_free_bytes=resources['minimum_free_output_bytes'])
            preparation = time.monotonic() - began
            supervisor._ledger['consumed_wall_seconds'] = preparation
            supervisor._save()
            ledger = supervisor.run()
            supervision = time.monotonic() - began - preparation
            if ledger['stop_reason'] is not None or any(j['status'] != 'succeeded' for j in ledger['jobs'].values()):
                raise RuntimeError(f"Pilot incomplete: {ledger['stop_reason']}")
            # Revalidate executing source/approval after workers and before any comparison.
            if validate_execution(root, approval_file)['binding_fingerprint'] != context['binding_fingerprint']:
                raise ValueError('Execution binding changed during pilot')
            payloads, paths = _load_sealed(supervisor, context['design'])
            staging = output / '.publication-staging'
            staging.mkdir(exist_ok=False)
            runs = _guarded_runs(context, staging, payloads, paths)
            from .v2_pilot_reporting import build_report
            elapsed = time.monotonic() - began
            accounting = dict(schema_version=1, status='COMPLETE', supervisor=ledger, runtime=context['runtime'],
                design_fingerprint=DESIGN_FINGERPRINT, binding_fingerprint=context['binding_fingerprint'],
                wall_seconds=dict(preparation=preparation, supervision=supervision,
                                  finalization=elapsed - preparation - supervision, total=elapsed),
                development_locks={name: run.snapshot()['lock']['fingerprint'] for name, run in runs.items()})
            report = build_report(context['design'], payloads, accounting=accounting)
            for run in runs.values():
                run.publish_development({'pilot_report.json': report})
            # Charge final loading, validation, guards, report generation and both publications.
            final_elapsed = time.monotonic() - began
            supervisor._ledger['consumed_wall_seconds'] = final_elapsed
            supervisor._save()
            final = dict(schema_version=1, status='COMPLETE', total_wall_seconds=final_elapsed,
                budget_seconds=resources['total_wall_seconds'],
                measurement_scope='Monotonic start through sealed publication and final accounting checkpoint',
                report_accounting_scope='Snapshot before report generation; final accounting includes publication',
                supervisor_plan_fingerprint=supervisor.plan_fingerprint,
                development_locks=accounting['development_locks'], test_released=False)
            write_artifact_once(staging / 'pilot_accounting.json', (canonical_json(final) + '\n').encode())
            if time.monotonic() - began >= resources['total_wall_seconds']:
                raise TimeoutError('Total pilot wall budget exhausted before publication')
            # Both guarded runs and their completion record become visible together.
            publication_attempted = True
            _rename_no_replace(staging, output / 'publication')
            return final
    except BaseException as error:
        # A signal may arrive just after the atomic rename succeeds. Withdraw
        # only this driver's exact bundle; never touch a preexisting destination.
        published = output / 'publication'
        if (publication_attempted and staging is not None and not staging.exists()
                and published.is_dir() and not published.is_symlink()
                and read_finite_json(published / 'pilot_accounting.json') == final):
            from .provenance import _rename_no_replace as withdraw_no_replace
            withdraw_no_replace(published, staging)
        if supervisor is not None:
            supervisor._ledger['consumed_wall_seconds'] = max(
                supervisor._ledger['consumed_wall_seconds'], time.monotonic() - began)
            if supervisor._ledger.get('stop_reason') is None:
                supervisor._ledger['stop_reason'] = 'DRIVER_FINALIZATION_FAILED'
            supervisor._save()
        _failure_record(output, supervisor, error, time.monotonic() - began)
        raise


def metadata(root):
    protocol = load_protocol(root)
    return dict(schema_version=1, mode='METADATA_ONLY', design_fingerprint=DESIGN_FINGERPRINT,
        total_processes=len(protocol['design']['jobs']), selected_models=18,
        execution_authorized=False, model_fit_executed=False, science_inputs_opened=False,
        inference_status='INFERENCE_UNAVAILABLE', inference_reason='NO_VALIDATED_REPLACEMENT',
        required_execution_gates=['G3_NAMED_HOST_DATA_OUTPUT_RUNTIME_RESERVATION', 'G4_SEPARATE_BOUNDED_PILOT_APPROVAL'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--execute', action='store_true', help='Requires separate explicit external execution approval')
    parser.add_argument('--approval', type=Path)
    args = parser.parse_args(argv)
    if args.approval is not None and not args.execute:
        parser.error('--approval is only accepted with explicit --execute')
    try:
        result = run_pilot(args.root, args.approval) if args.execute else metadata(args.root)
    except (PermissionError, ValueError, OSError, RuntimeError) as error:
        print(canonical_json(dict(status='BLOCKED', error_type=type(error).__name__, error=str(error))), file=sys.stderr)
        return 2
    print(canonical_json(result))
    return 0
