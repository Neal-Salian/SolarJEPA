"""Worker boundary checks only: no native decoding, optimizer, fit or evaluation."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def api():
    return importlib.import_module('solar_flare_jepa.experiments.v2_pilot_worker')


def design():
    return json.loads((ROOT / 'docs/protocols/phase2_v2_development_v1.json').read_text())['design']


def test_missing_approval_refuses_before_loader_or_output(tmp_path, monkeypatch):
    worker = api()
    def forbidden(*args, **kwargs):
        raise AssertionError('Scientific work reached without authorization')
    monkeypatch.setattr(worker, '_load_inputs', forbidden)
    monkeypatch.setattr(worker, '_fit', forbidden)
    output = tmp_path / 'must-not-exist'
    with pytest.raises(ValueError):
        worker.execute_job(ROOT, None, design()['jobs'][0], output, tmp_path / 'supervisor')
    assert not output.exists()


@pytest.mark.parametrize('index,kind', [(0, 'ControlledConfig'), (2, 'ControlledConfig'),
                                        (6, 'TcnConfig'), (7, 'QuantileLinearConfig'), (8, 'ControlledConfig')])
def test_exact_typed_job_configurations_preserve_protocol(index, kind):
    job = design()['jobs'][index]
    config, schedule = api().parse_job_config(job)
    assert type(config).__name__ == kind
    if kind == 'ControlledConfig':
        assert config.seed == 1261866429
        assert config.as_dict() == job['model_config']
        assert config.schedule.early_stopping_patience is None
        assert config.architecture.width == 32
        assert config.architecture.context_mask_patches == 4
    elif kind == 'TcnConfig':
        assert config.width == 32
        assert config.dilations == (1, 2, 4, 8, 16, 32)
        assert schedule.downstream_epochs == 15
    else:
        assert config.lambdas == (0., 1., 10., 100., 1000., 10000., 100000.)
        assert config.epochs == 100
        assert config.gradient_clip is None


@pytest.mark.parametrize('mutation', ['digest', 'missing_config', 'missing_field', 'wrong_kind'])
def test_bad_configuration_cannot_fall_back_to_model_defaults(mutation):
    from solar_flare_jepa.forecasting.contracts import fingerprint_payload
    job = deepcopy(design()['jobs'][0])
    if mutation == 'digest':
        job['model_config']['architecture']['width'] = 64
    elif mutation == 'missing_config':
        job.pop('model_config')
    elif mutation == 'missing_field':
        job['model_config']['architecture'].pop('width')
        job['model_config_fingerprint'] = fingerprint_payload(job['model_config'])
    else:
        job['kind'] = 'unknown'
    with pytest.raises(ValueError):
        api().parse_job_config(job)


def test_missing_or_unsealed_ssl_dependency_never_recomputed(tmp_path):
    job = design()['jobs'][1]
    context = dict(approval=dict(output_root=str(tmp_path)), design=design(), protocol=dict(design_fingerprint='frozen'),
                   binding_fingerprint='bound', runtime=dict(source_fingerprint='source'))
    with pytest.raises((ValueError, FileNotFoundError)):
        api().load_dependency(context, job, tmp_path)
    assert list(tmp_path.iterdir()) == []


def supervised(tmp_path, job_index=2):
    """Synthetic supervisor metadata, never a launched process or execution approval."""
    from solar_flare_jepa.forecasting.contracts import fingerprint_payload
    register = json.loads((ROOT / 'docs/protocols/phase2_v2_development_v1.json').read_text())
    context = dict(protocol=register, design=register['design'],
                   approval=dict(output_root=str(tmp_path), data_root=str(tmp_path / 'data')),
                   runtime=dict(source_fingerprint='synthetic-source'), binding_fingerprint='synthetic-bound')
    resources = context['design']['resources']
    limits = {key: resources[key] for key in ('threads', 'max_rss_bytes', 'total_wall_seconds',
                                             'max_retries', 'poll_interval_seconds')}
    jobs = [dict(job_id=j['job_id'], command=['synthetic-unused'], timeout_seconds=j['timeout_seconds'])
            for j in context['design']['jobs']]
    plan = dict(schema_version=1, code_fingerprint='synthetic-source', config_fingerprint='synthetic-bound',
                resources=limits, jobs=jobs)
    job = context['design']['jobs'][job_index]
    supervisor = tmp_path / 'supervisor'
    output = supervisor / f"attempts/{job['job_id']}-1/artifacts"
    output.mkdir(parents=True)
    ledger = dict(plan=plan, plan_fingerprint=fingerprint_payload(plan),
                  execution_order=[j['job_id'] for j in jobs], stop_reason=None,
                  jobs={j['job_id']: dict(status='pending', artifact_path=None, artifacts=None) for j in jobs},
                  attempts=[dict(job_id=job['job_id'], number=1, status='running', pid=None,
                                 path=f"attempts/{job['job_id']}-1", job_fingerprint=fingerprint_payload(jobs[job_index]))])
    (supervisor / 'supervisor.json').write_text(json.dumps(ledger))
    return context, job, supervisor, output, ledger


@pytest.mark.parametrize('drift', ['resources', 'timeout', 'attempt_fingerprint'])
def test_worker_refuses_supervision_drift_before_loader(tmp_path, monkeypatch, drift):
    from solar_flare_jepa.experiments import v2_pilot_protocol
    from solar_flare_jepa.forecasting.contracts import fingerprint_payload
    context, job, supervisor, output, ledger = supervised(tmp_path)
    if drift == 'resources':
        ledger['plan']['resources']['max_retries'] = 1
    elif drift == 'timeout':
        ledger['plan']['jobs'][2]['timeout_seconds'] = 9999
    else:
        ledger['attempts'][0]['job_fingerprint'] = 'wrong'
    ledger['plan_fingerprint'] = fingerprint_payload(ledger['plan'])
    (supervisor / 'supervisor.json').write_text(json.dumps(ledger))
    monkeypatch.setattr(v2_pilot_protocol, 'validate_execution', lambda *a: context)
    monkeypatch.setattr(api(), '_establish_runtime', lambda *a: None)
    def forbidden(*args):
        raise AssertionError('Invalid supervisor reached scientific loader')
    monkeypatch.setattr(api(), '_load_inputs', forbidden)
    with pytest.raises(ValueError):
        api().execute_job(ROOT, {'synthetic': True}, job, output, supervisor)
    assert list(output.iterdir()) == []


def ssl_fixture(tmp_path):
    from solar_flare_jepa.training.controlled import PretrainingArtifact
    from solar_flare_jepa.training.core import _weights_fingerprint
    from solar_flare_jepa.forecasting.contracts import fingerprint_payload
    from solar_flare_jepa.experiments.v2_runner import _seal
    import torch
    context, job, supervisor, _, ledger = supervised(tmp_path, 1)
    dep = context['design']['jobs'][0]
    directory = supervisor / f"attempts/{dep['job_id']}-1/artifacts"
    directory.mkdir(parents=True)
    state = {'synthetic': torch.tensor([1.], dtype=torch.float32)}
    record = dict(schema_version=1, identity={'synthetic': True}, history=[], budget={}, fingerprints={},
                  pairing={}, state_fingerprint=_weights_fingerprint(state))
    artifact = PretrainingArtifact(state, record)
    artifact.save(directory / 'ssl.pt')
    result = dict(pretraining_record=record, artifact_fingerprint=artifact.fingerprint)
    digest = __import__('hashlib').sha256((directory / 'ssl.pt').read_bytes()).hexdigest()
    binding = dict(schema_version=1, job_id=dep['job_id'], design_fingerprint=context['protocol']['design_fingerprint'],
                   binding_fingerprint='synthetic-bound', model_config_fingerprint=dep['model_config_fingerprint'],
                   artifact_name='ssl.pt', artifact_sha256=digest, artifact_fingerprint=artifact.fingerprint)
    (directory / 'binding.json').write_text(json.dumps(binding))
    (directory / 'result.json').write_text(json.dumps(result))
    (directory / 'worker.json').write_text(json.dumps({'synthetic': True}))
    ledger['attempts'].insert(0, dict(job_id=dep['job_id'], number=1, status='succeeded', returncode=0,
                                     job_fingerprint=fingerprint_payload(ledger['plan']['jobs'][0])))
    ledger['jobs'][dep['job_id']] = dict(status='succeeded',
        artifact_path=f"attempts/{dep['job_id']}-1/artifacts", artifacts=_seal(directory))
    (supervisor / 'supervisor.json').write_text(json.dumps(ledger))
    return context, job, supervisor, directory, ledger, artifact


def test_sealed_dependency_loads_weights_only_without_fit(tmp_path):
    context, job, supervisor, _, _, original = ssl_fixture(tmp_path)
    loaded = api().load_dependency(context, job, supervisor)
    assert loaded.record == original.record
    assert loaded.fingerprint == original.fingerprint


@pytest.mark.parametrize('drift', ['binding', 'config', 'weights', 'failed', 'retry'])
def test_ssl_dependency_identity_or_state_drift_is_terminal(tmp_path, drift):
    context, job, supervisor, directory, ledger, _ = ssl_fixture(tmp_path)
    dep = job['dependencies'][0]
    if drift in ('binding', 'config'):
        field = 'binding_fingerprint' if drift == 'binding' else 'model_config_fingerprint'
        binding = json.loads((directory / 'binding.json').read_text())
        binding[field] = 'stale'
        (directory / 'binding.json').chmod(0o644)
        (directory / 'binding.json').write_text(json.dumps(binding))
        # Reseal deliberately: immutable dependency binding must be checked beyond file seals.
        for path in directory.iterdir():
            path.chmod(0o644)
        (directory / 'artifacts.json').unlink()
        from solar_flare_jepa.experiments.v2_runner import _seal
        ledger['jobs'][dep]['artifacts'] = _seal(directory)
    elif drift == 'weights':
        (directory / 'ssl.pt').chmod(0o644)
        (directory / 'ssl.pt').write_bytes(b'changed-weights')
    elif drift == 'failed':
        ledger['jobs'][dep]['status'] = 'failed'
    else:
        ledger['attempts'][0]['number'] = 2
    (supervisor / 'supervisor.json').write_text(json.dumps(ledger))
    with pytest.raises(ValueError):
        api().load_dependency(context, job, supervisor)


def synthetic_bundle(context):
    from types import SimpleNamespace
    from m4b_helpers import development_windows
    from solar_flare_jepa.forecasting.contracts import fingerprint_payload
    from solar_flare_jepa.training.normalization import Normalization
    from solar_flare_jepa.training.jepa import training_windows
    from solar_flare_jepa.training.controlled import _validation_identity, _window_record
    windows = development_windows()
    training = windows['train'].training_slice
    normalization = Normalization.fit(training)
    lazy = training_windows(training, normalization, stride=1)
    split_ids = {name: w.split_fingerprint for name, w in windows.items()}
    evidence = dict(dataset_fingerprint=training.context.dataset_fingerprint,
        forecast_fingerprint=training.spec.fingerprint, split_fingerprint=fingerprint_payload(split_ids),
        split_fingerprints=split_ids, training_fingerprint=training.fingerprint,
        normalization_fingerprint=normalization.fingerprint,
        train_windows=_window_record(lazy, lazy.subsample(20000), 20000),
        test_windows_built=False, test_partition_constructed=False,
        manifest_identities=context['design']['data']['allowed_manifests'])
    context['approval']['data_identity'] = {k: evidence[k] for k in ('dataset_fingerprint', 'forecast_fingerprint',
        'split_fingerprint', 'split_fingerprints', 'training_fingerprint', 'normalization_fingerprint', 'train_windows')}
    context['approval']['data_identity']['validation_content_fingerprint'] = _validation_identity(
        windows['validation'])['content_fingerprint']
    pins = context['design']['data']['normalization']
    for key in ('dataset', 'split', 'training', 'normalization'):
        name = 'historical_expected_fingerprint' if key == 'normalization' else f'historical_expected_{key}_fingerprint'
        pins[name] = evidence[f'{key}_fingerprint']
    return SimpleNamespace(training=training, validation=windows['validation'], normalization=normalization,
        dataset=SimpleNamespace(fingerprint=training.context.dataset_fingerprint), evidence=evidence)


def test_distinct_approved_data_root_used_without_decoding_source_root(tmp_path, monkeypatch):
    from solar_flare_jepa.data import goes_v2_development
    context, _, _, _, _ = supervised(tmp_path)
    bundle = synthetic_bundle(context)
    observed = []
    def fake_loader(root, **kwargs):
        observed.append(root)
        return bundle
    monkeypatch.setattr(goes_v2_development, 'load_development', fake_loader)
    assert api()._load_inputs(ROOT, context) is bundle
    assert observed == [str(tmp_path / 'data')]


def test_approval_validation_content_drift_blocks_input_consumer(tmp_path):
    context, _, _, _, _ = supervised(tmp_path)
    bundle = synthetic_bundle(context)
    context['approval']['data_identity']['validation_content_fingerprint'] = '0' * 64
    with pytest.raises(ValueError):
        api()._check_inputs(bundle, context)


@pytest.mark.parametrize('outcome', ['success', 'parity_drift', 'source_drift', 'config_drift'])
def test_nonfitting_worker_orchestration_requires_exact_reload_and_bindings(tmp_path, monkeypatch, outcome):
    from types import SimpleNamespace
    import numpy as np
    import torch
    from solar_flare_jepa.experiments import v2_pilot_protocol, v2_evaluation_adapters
    from solar_flare_jepa.training import controlled
    from solar_flare_jepa.evaluation.records import EvaluationRecord, EvaluationIdentity
    from solar_flare_jepa.forecasting.contracts import ForecastPrediction
    context, job, supervisor, output, _ = supervised(tmp_path)
    bundle = synthetic_bundle(context)
    validated = []
    def fake_approval(*args):
        validated.append(True)
        result = deepcopy(context)
        if outcome == 'source_drift' and len(validated) > 1:
            result['binding_fingerprint'] = 'changed-source'
        return result
    monkeypatch.setattr(v2_pilot_protocol, 'validate_execution', fake_approval)
    monkeypatch.setattr(api(), '_load_inputs', lambda *a: bundle)
    monkeypatch.setattr(api(), '_establish_runtime', lambda *a: None)
    record = dict(config=deepcopy(job['model_config']), seed=job['seed'], train_windows=bundle.evidence['train_windows'])
    if outcome == 'config_drift':
        record['config']['architecture']['width'] = 64
    selected = SimpleNamespace(record=record, model=SimpleNamespace(state_dict=lambda: {'x': torch.tensor([1.])}))
    selected.save = lambda path: path.write_bytes(b'synthetic-checkpoint-no-trained-weights')
    monkeypatch.setattr(api(), '_fit', lambda *a: selected)
    monkeypatch.setattr(controlled, 'load_forecaster', lambda path: selected)
    evaluated = []
    def fake_adapter(model, window, kwargs):
        evaluated.append(True)
        shape = window.targets.values.shape
        native = np.repeat(window.targets.values[..., None], 5, axis=-1)
        if outcome == 'parity_drift' and len(evaluated) > 1:
            native *= 1.01
        prediction = ForecastPrediction(native[..., 2], window.targets.grid, 'synthetic-no-fit',
            quantile_levels=(.05, .25, .5, .75, .95), quantiles=native)
        identity = EvaluationIdentity(**kwargs, model_version='synthetic-no-fit', seed=job['seed'],
            config_fingerprint=job['model_config_fingerprint'], training_fingerprint=bundle.training.fingerprint,
            normalization_fingerprint=bundle.normalization.fingerprint)
        return EvaluationRecord(identity, window.targets, prediction)
    monkeypatch.setattr(v2_evaluation_adapters, 'build_evaluation_record', fake_adapter)
    if outcome == 'success':
        result = api().execute_job(ROOT, {'synthetic': True}, job, output, supervisor)
        assert set(result) == {'model_record', 'evaluation_record'}
        assert result['model_record'] == record
        assert {p.name for p in output.iterdir()} == {'selected.pt', 'result.json', 'binding.json', 'worker.json'}
        binding = json.loads((output / 'binding.json').read_text())
        assert binding['artifact_name'] == 'selected.pt'
        assert binding['model_config_fingerprint'] == job['model_config_fingerprint']
        assert binding['binding_fingerprint'] == 'synthetic-bound'
        assert json.loads((output / 'worker.json').read_text())['exact_weights_only_reload_parity'] is True
        assert len(validated) == 2
    else:
        with pytest.raises(ValueError):
            api().execute_job(ROOT, {'synthetic': True}, job, output, supervisor)
        assert not (output / 'result.json').exists()
        assert not (output / 'binding.json').exists()
        if outcome == 'config_drift':
            assert not (output / 'selected.pt').exists()


def test_ssl_worker_output_can_be_sealed_and_reused_without_training(tmp_path, monkeypatch):
    import torch
    from solar_flare_jepa.experiments import v2_pilot_protocol
    from solar_flare_jepa.experiments.v2_runner import _seal
    from solar_flare_jepa.training.controlled import PretrainingArtifact, _pretraining_identity
    from solar_flare_jepa.training.core import _weights_fingerprint
    context, job, supervisor, output, ledger = supervised(tmp_path, 0)
    bundle = synthetic_bundle(context)
    config, _ = api().parse_job_config(job)
    state = {'synthetic-float32-weight': torch.tensor([1.], dtype=torch.float32)}
    record = dict(schema_version=1,
        identity=_pretraining_identity(bundle.training, bundle.normalization, bundle.evidence['train_windows'], config),
        history=[], budget={}, fingerprints={}, pairing={}, state_fingerprint=_weights_fingerprint(state))
    artifact = PretrainingArtifact(state, record)
    monkeypatch.setattr(v2_pilot_protocol, 'validate_execution', lambda *a: context)
    monkeypatch.setattr(api(), '_establish_runtime', lambda *a: None)
    monkeypatch.setattr(api(), '_load_inputs', lambda *a: bundle)
    monkeypatch.setattr(api(), '_fit', lambda *a: artifact)
    result = api().execute_job(ROOT, {'synthetic': True}, job, output, supervisor)
    assert result['artifact_fingerprint'] == artifact.fingerprint
    assert {p.name for p in output.iterdir()} == {'ssl.pt', 'result.json', 'binding.json', 'worker.json'}
    ledger['attempts'][0].update(status='succeeded', returncode=0)
    ledger['jobs'][job['job_id']] = dict(status='succeeded',
        artifact_path=str(output.relative_to(supervisor)), artifacts=_seal(output))
    (supervisor / 'supervisor.json').write_text(json.dumps(ledger))
    loaded = api().load_dependency(context, context['design']['jobs'][1], supervisor)
    assert loaded.fingerprint == artifact.fingerprint


@pytest.mark.parametrize('job_index,function', [(0, 'pretrain_controlled'), (2, 'fit_controlled'),
                                               (6, 'fit_tcn'), (7, 'fit_quantile_linear')])
def test_existing_trainer_adapters_receive_explicit_configs_without_fitting(tmp_path, monkeypatch, job_index, function):
    from solar_flare_jepa.training import controlled, comparators
    context, job, _, _, _ = supervised(tmp_path, job_index)
    bundle = synthetic_bundle(context)
    config, schedule = api().parse_job_config(job)
    calls = []
    def no_fit(*args, **kwargs):
        calls.append((args, kwargs))
        return 'synthetic-no-fit'
    monkeypatch.setattr(controlled if job_index in (0, 2) else comparators, function, no_fit)
    assert api()._fit(bundle, job, config, schedule, None) == 'synthetic-no-fit'
    args, kwargs = calls[0]
    assert args[0] is bundle.training
    if job_index == 0:
        assert args[1] is config
    else:
        assert args[1] is bundle.validation
        assert args[2] is config
    if job_index == 2:
        assert kwargs == {'pretraining': None}
    if job_index == 6:
        assert args[3] is schedule


def test_cpu_float32_four_thread_seed_setup_precedes_any_model_construction(tmp_path, monkeypatch):
    import random
    import numpy as np
    import torch
    context, job, _, _, _ = supervised(tmp_path)
    config, _ = api().parse_job_config(job)
    for name in context['design']['resources']['thread_environment']:
        monkeypatch.setenv(name, '4')
    prior = (torch.get_default_dtype(), torch.get_default_device(), torch.get_num_threads(),
             torch.are_deterministic_algorithms_enabled(), torch.random.get_rng_state(),
             np.random.get_state(), random.getstate())
    try:
        api()._establish_runtime(context, config.architecture)
        first = (torch.rand(1).item(), np.random.rand(), random.random())
        api()._establish_runtime(context, config.architecture)
        second = (torch.rand(1).item(), np.random.rand(), random.random())
        assert first == second
        assert torch.tensor(0.).dtype == torch.float32
        assert torch.tensor(0.).device.type == 'cpu'
        assert torch.get_num_threads() == 4
        assert torch.are_deterministic_algorithms_enabled()
        monkeypatch.setenv('OMP_NUM_THREADS', '8')
        with pytest.raises(ValueError):
            api()._establish_runtime(context, config.architecture)
    finally:
        torch.set_default_dtype(prior[0])
        torch.set_default_device(prior[1])
        torch.set_num_threads(prior[2])
        torch.use_deterministic_algorithms(prior[3])
        torch.random.set_rng_state(prior[4])
        np.random.set_state(prior[5])
        random.setstate(prior[6])


def test_float64_artifact_cannot_be_published_as_float32():
    import torch
    with pytest.raises(ValueError):
        api()._assert_state_runtime({'weight': torch.tensor([1.], dtype=torch.float64)})


def test_resealed_float64_ssl_dependency_is_rejected_before_downstream(tmp_path):
    import torch
    from solar_flare_jepa.training.controlled import PretrainingArtifact
    from solar_flare_jepa.training.core import _weights_fingerprint
    from solar_flare_jepa.experiments.v2_runner import _seal
    context, job, supervisor, directory, ledger, original = ssl_fixture(tmp_path)
    for path in directory.iterdir():
        path.chmod(0o644)
    (directory / 'artifacts.json').unlink()
    (directory / 'ssl.pt').unlink()
    state = {'synthetic': torch.tensor([1.], dtype=torch.float64)}
    record = dict(original.record, state_fingerprint=_weights_fingerprint(state))
    artifact = PretrainingArtifact(state, record)
    artifact.save(directory / 'ssl.pt')
    result = dict(pretraining_record=artifact.record, artifact_fingerprint=artifact.fingerprint)
    (directory / 'result.json').write_text(json.dumps(result))
    binding = json.loads((directory / 'binding.json').read_text())
    binding.update(artifact_sha256=__import__('hashlib').sha256((directory / 'ssl.pt').read_bytes()).hexdigest(),
                   artifact_fingerprint=artifact.fingerprint)
    (directory / 'binding.json').write_text(json.dumps(binding))
    ledger['jobs'][job['dependencies'][0]]['artifacts'] = _seal(directory)
    (supervisor / 'supervisor.json').write_text(json.dumps(ledger))
    with pytest.raises(ValueError):
        api().load_dependency(context, job, supervisor)


def test_actual_production_worker_launch_preserves_executed_source_provenance(tmp_path):
    """Real clean temporary checkout + fresh worker help; no fitting authorization.

    An external atexit probe observes the actual imported namespace after the
    production command completes. It does not change project source or checks.
    """
    import os
    import shutil
    import subprocess
    import sys
    from solar_flare_jepa.experiments.v2_pilot import process_plan
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    for relative in ('src', 'scripts', 'configs/experiments', 'schemas'):
        shutil.copytree(ROOT / relative, checkout / relative, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('pyproject.toml', 'requirements-lock.txt', 'requirements-training-lock.txt', 'requirements-v1-lock.txt'):
        shutil.copy2(ROOT / name, checkout / name)
    for command in (['git', 'init', '-q', '-b', 'codex/v2-experimental-validation-readiness'],
                    ['git', 'add', '.'],
                    ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                     'commit', '-qm', 'test fixture source snapshot']):
        subprocess.run(command, cwd=checkout, check=True, capture_output=True)
    probe = tmp_path / 'external-probe'
    probe.mkdir()
    (probe / 'sitecustomize.py').write_text(
        'import atexit\n'
        'def inspect_provenance():\n'
        '    try:\n'
        '        from solar_flare_jepa.experiments.v2_pilot_protocol import runtime_identity\n'
        f'        result = runtime_identity({str(checkout)!r})\n'
        '        print("PROVENANCE_PASS=" + result["source_fingerprint"])\n'
        '    except Exception as error:\n'
        '        print("PROVENANCE_ERROR=" + str(error))\n'
        'atexit.register(inspect_provenance)\n')
    jobs, _ = process_plan(checkout, tmp_path / 'absent-no-approval.json', tmp_path / 'supervisor', design())
    command = [*jobs[0].command, '--help']
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join((str(probe), str(checkout / 'src'))),
                 PYTHONDONTWRITEBYTECODE='1'))
    assert result.returncode == 0, result.stderr
    assert 'PROVENANCE_PASS=' in result.stdout, result.stdout + result.stderr
    assert 'PROVENANCE_ERROR=' not in result.stdout
    assert not (tmp_path / 'supervisor').exists()
    assert not (tmp_path / 'absent-no-approval.json').exists()
