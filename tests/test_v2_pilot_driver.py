"""Driver tests never launch a scientific worker."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def api():
    return importlib.import_module('solar_flare_jepa.experiments.v2_pilot')


def test_metadata_default_cli_opens_no_loader_and_writes_nothing(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_v2_goes_pilot.py'), '--root', str(ROOT)],
                            cwd=tmp_path, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))
    assert result.returncode == 0, result.stderr
    metadata = json.loads(result.stdout)
    assert metadata['execution_authorized'] is False
    assert metadata['model_fit_executed'] is False and metadata['total_processes'] == 20
    assert list(tmp_path.iterdir()) == []


def test_execute_denied_before_loader_or_outputs(tmp_path):
    with pytest.raises(PermissionError, match='approval'):
        api().run_pilot(ROOT, None)
    assert list(tmp_path.iterdir()) == []


def test_storage_gate_at_one_gib_boundary(monkeypatch, tmp_path):
    monkeypatch.setattr(api().shutil, 'disk_usage', lambda path: SimpleNamespace(free=1024**3 - 1))
    with pytest.raises(api().StorageUnavailable):
        api().check_storage(tmp_path, 1024**3)
    monkeypatch.setattr(api().shutil, 'disk_usage', lambda path: SimpleNamespace(free=1024**3))
    assert api().check_storage(tmp_path, 1024**3)['free_bytes'] == 1024**3


def test_driver_never_resumes_existing_output(monkeypatch, tmp_path):
    output = tmp_path / 'existing'
    output.mkdir()
    marker = output / 'untouched'
    marker.write_text('preserve')
    monkeypatch.setattr(api(), 'validate_execution', lambda *a: dict(approval=dict(output_root=str(output))))
    with pytest.raises(FileExistsError, match='resume|exists'):
        api().run_pilot(ROOT, '/external/approval.json')
    assert marker.read_text() == 'preserve'


def test_exact_process_commands_and_zero_retry_limits(tmp_path):
    protocol = importlib.import_module('solar_flare_jepa.experiments.v2_pilot_protocol').load_protocol(ROOT)
    jobs, limits = api().process_plan(ROOT, tmp_path / 'approval.json', tmp_path / 'supervisor', protocol['design'])
    assert len(jobs) == 20 and limits.max_retries == 0
    assert limits.max_rss_bytes == 2 * 1024**3 and limits.total_wall_seconds == 7200
    assert all(job.command[0] == sys.executable for job in jobs)
    assert [j.timeout_seconds for j in jobs] == [j['timeout_seconds'] for j in protocol['design']['jobs']]


def test_each_attempt_storage_gate_keeps_all_jobs_pending(monkeypatch, tmp_path):
    resources = importlib.import_module('solar_flare_jepa.experiments.v2_resource_controls')
    job = resources.ProcessJob('synthetic', (sys.executable, '-c', 'raise AssertionError("must not launch")'), 1)
    supervisor = api().PilotSupervisor(tmp_path / 'supervisor', [job], code_fingerprint='code',
        config_fingerprint='config', limits=resources.ResourceLimits(1024**3, 10, 1, 0), minimum_free_bytes=1024**3)
    monkeypatch.setattr(api().shutil, 'disk_usage', lambda path: SimpleNamespace(free=0))
    result = supervisor.run()
    assert result['stop_reason'] == 'OUTPUT_STORAGE_UNAVAILABLE'
    assert result['jobs']['synthetic']['status'] == 'pending'
    assert result['attempts'] == []


def synthetic_driver(monkeypatch, tmp_path, *, first_failure=False):
    resources = importlib.import_module('solar_flare_jepa.experiments.v2_resource_controls')
    protocol = importlib.import_module('solar_flare_jepa.experiments.v2_pilot_protocol').load_protocol(ROOT)
    output = tmp_path / 'pilot'
    context = dict(approval=dict(output_root=str(output)), design=protocol['design'],
        runtime=dict(source_fingerprint='synthetic-code', source_files=[]), binding_fingerprint='synthetic-binding')
    monkeypatch.setattr(api(), 'validate_execution', lambda *a: context)
    real_plan = api().process_plan
    def stub_plan(root, approval, supervisor, design):
        jobs, limits = real_plan(root, approval, supervisor, design)
        commands = []
        for index, job in enumerate(jobs):
            code = ('raise SystemExit(7)' if index == 0 and first_failure else
                    "from pathlib import Path;Path('result.json').write_text('{\"model_record\":{},\"evaluation_record\":{}}')")
            commands.append(resources.ProcessJob(job.job_id, (sys.executable, '-c', code), job.timeout_seconds))
        return commands, limits
    monkeypatch.setattr(api(), 'process_plan', stub_plan)
    publications = []
    class FakeGuardedRun:
        def __init__(self, cohort, run_root):
            self.cohort, self.run_root = cohort, run_root
        def snapshot(self):
            return dict(lock=dict(fingerprint='synthetic-lock-' + self.cohort))
        def publish_development(self, contents):
            publications.append((self.cohort, contents))
            directory = self.run_root / 'results/v2_runs' / self.cohort / 'development_publication'
            directory.mkdir(parents=True)
            (directory / 'pilot_report.json').write_text(json.dumps(contents))
    def guarded(context, output, payloads, paths):
        assert len(payloads) == 18 and len(paths) == 20
        return {name: FakeGuardedRun(name, output) for name in ('primary', 'alternate_loss')}
    monkeypatch.setattr(api(), '_guarded_runs', guarded)
    report_calls = []
    def report(design, payloads, *, accounting):
        assert len(payloads) == 18
        assert all(e['status'] == 'succeeded' for e in accounting['supervisor']['jobs'].values())
        assert len(accounting['supervisor']['attempts']) == 20
        report_calls.append(accounting)
        return dict(synthetic_only=True)
    monkeypatch.setitem(sys.modules, 'solar_flare_jepa.experiments.v2_pilot_reporting', SimpleNamespace(build_report=report))
    return output, publications, report_calls


def test_synthetic_twenty_process_driver_seals_then_guards_and_publishes(monkeypatch, tmp_path):
    output, publications, reports = synthetic_driver(monkeypatch, tmp_path)
    result = api().run_pilot(ROOT, tmp_path / 'external-approval.json')
    assert result['status'] == 'COMPLETE' and result['test_released'] is False
    assert len(publications) == 2 and len(reports) == 1
    ledger = json.loads((output / 'supervisor/supervisor.json').read_text())
    assert len(ledger['attempts']) == 20 and all(a['number'] == 1 for a in ledger['attempts'])
    assert ledger['consumed_wall_seconds'] >= reports[0]['wall_seconds']['total']
    assert (output / 'publication/pilot_accounting.json').is_file()
    assert not (output / 'pilot_failure.json').exists()


def test_synthetic_first_failure_preserves_nineteen_pending_without_retry(monkeypatch, tmp_path):
    output, publications, reports = synthetic_driver(monkeypatch, tmp_path, first_failure=True)
    with pytest.raises(RuntimeError, match='incomplete'):
        api().run_pilot(ROOT, tmp_path / 'external-approval.json')
    ledger = json.loads((output / 'supervisor/supervisor.json').read_text())
    assert len(ledger['attempts']) == 1
    assert sum(e['status'] == 'failed' for e in ledger['jobs'].values()) == 1
    assert sum(e['status'] == 'pending' for e in ledger['jobs'].values()) == 19
    assert not publications and not reports
    assert json.loads((output / 'pilot_failure.json').read_text())['status'] == 'INCOMPLETE'
    assert not (output / 'pilot_accounting.json').exists()


def test_second_publication_failure_exposes_no_complete_bundle(monkeypatch, tmp_path):
    output, publications, reports = synthetic_driver(monkeypatch, tmp_path)
    guarded = api()._guarded_runs
    def fail_second(*args):
        runs = guarded(*args)
        def failure(contents):
            raise OSError('synthetic second publication failure')
        runs['alternate_loss'].publish_development = failure
        return runs
    monkeypatch.setattr(api(), '_guarded_runs', fail_second)
    with pytest.raises(OSError, match='second publication'):
        api().run_pilot(ROOT, tmp_path / 'external-approval.json')
    assert not (output / 'publication').exists()
    assert not (output / 'results/v2_runs').exists()
    assert not (output / 'pilot_accounting.json').exists()
    assert (output / 'pilot_failure.json').is_file()


def test_alarm_after_atomic_rename_withdraws_completed_bundle(monkeypatch, tmp_path):
    output, publications, reports = synthetic_driver(monkeypatch, tmp_path)
    original = api()._rename_no_replace
    def interrupted_rename(source, destination):
        original(source, destination)
        if destination == output / 'publication':
            raise TimeoutError('synthetic alarm after atomic rename')
    monkeypatch.setattr(api(), '_rename_no_replace', interrupted_rename)
    with pytest.raises(TimeoutError, match='after atomic rename'):
        api().run_pilot(ROOT, tmp_path / 'external-approval.json')
    assert not (output / 'publication').exists()
    assert (output / '.publication-staging/pilot_accounting.json').is_file()
    assert json.loads((output / 'pilot_failure.json').read_text())['status'] == 'INCOMPLETE'


def test_publication_collision_preserves_existing_destination(monkeypatch, tmp_path):
    output, publications, reports = synthetic_driver(monkeypatch, tmp_path)
    original = api()._rename_no_replace
    def collision(source, destination):
        if destination == output / 'publication':
            destination.mkdir()
            (destination / 'unrelated.txt').write_text('preserve')
        original(source, destination)
    monkeypatch.setattr(api(), '_rename_no_replace', collision)
    with pytest.raises(FileExistsError):
        api().run_pilot(ROOT, tmp_path / 'external-approval.json')
    assert (output / 'publication/unrelated.txt').read_text() == 'preserve'
    assert not (output / 'publication/pilot_accounting.json').exists()
    assert (output / '.publication-staging/pilot_accounting.json').is_file()


@pytest.mark.parametrize('interruption', ['deadline', 'keyboard'])
def test_cleanup_interruption_still_kills_worker_and_keeps_pilot_incomplete(monkeypatch, tmp_path, interruption):
    """An alarm/interrupt during the TERM grace wait must not skip the hard stop."""
    import signal
    resources = importlib.import_module('solar_flare_jepa.experiments.v2_resource_controls')
    command = ('import signal,time;from pathlib import Path;'
               'signal.signal(signal.SIGTERM,signal.SIG_IGN);'
               'Path("ready").write_text("ready");time.sleep(30)')
    jobs = [resources.ProcessJob('00-stubborn', (sys.executable, '-c', command), 1),
            resources.ProcessJob('01-must-stay-pending', (sys.executable, '-c', 'pass'), 1)]
    runner = api().PilotSupervisor(tmp_path / 'supervisor', jobs, code_fingerprint='synthetic',
        config_fingerprint='synthetic', limits=resources.ResourceLimits(1024**3, 10, 4, 0),
        minimum_free_bytes=1)
    terminate = runner._terminate
    def interrupted_cleanup(process):
        assert (runner.directory / 'attempts/00-stubborn-1/artifacts/ready').is_file()
        if interruption == 'deadline':
            with api()._deadline(.03):
                terminate(process)
        else:
            wait = process.wait
            def interrupt_grace(*args, **kwargs):
                if kwargs.get('timeout') == .2:
                    raise KeyboardInterrupt('synthetic interruption during grace wait')
                return wait(*args, **kwargs)
            monkeypatch.setattr(process, 'wait', interrupt_grace)
            terminate(process)
    monkeypatch.setattr(runner, '_terminate', interrupted_cleanup)
    try:
        expected = TimeoutError if interruption == 'deadline' else KeyboardInterrupt
        with pytest.raises(expected):
            runner.run()
        ledger = json.loads((runner.directory / 'supervisor.json').read_text())
        assert len(ledger['attempts']) == 1
        assert ledger['jobs']['00-stubborn']['status'] != 'succeeded'
        assert ledger['jobs']['01-must-stay-pending']['status'] == 'pending'
        assert runner._sample_rss(ledger['attempts'][0]['pid']) == 0
        assert not (runner.directory / 'publication').exists()
    finally:
        # Keep the regression safe when run against the unfixed implementation.
        for attempt in runner._ledger['attempts']:
            if attempt['pid'] is not None:
                try:
                    os.killpg(attempt['pid'], signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    os.waitpid(attempt['pid'], 0)
                except ChildProcessError:
                    pass
