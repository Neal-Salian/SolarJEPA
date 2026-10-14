"""Guarded runner fixtures are invented arrays and fitted state, never GOES results."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from test_external_model_inputs import frozen_fixture, seal, write_json, identity
from test_frozen_baseline_replay import record as baseline_record
from solar_flare_jepa.forecasting.contracts import ForecastSpec, fingerprint_payload
from solar_flare_jepa.training.jepa import TrainedJepa

ORIGINAL_PREDICT = TrainedJepa.predict
ROOT = Path(__file__).resolve().parents[1]


def runner():
    return importlib.import_module('solar_flare_jepa.experiments.external_evaluation')


@pytest.fixture
def execution_fixture(frozen_fixture, monkeypatch):
    v1, prep, protocol = frozen_fixture
    spec = ForecastSpec(**protocol['forecast'])
    summary = json.loads((v1/'summary.json').read_text())
    for name in protocol['classical_models']:
        fitted = baseline_record(name, spec)
        fitted.update(dataset_fingerprint='synthetic-v1-dataset', training_fingerprint='synthetic-training')
        if name == 'training_mean':
            fitted['mean'] = [-6., -6.]
        if name in ('trailing_mean', 'drift'):
            fitted['lookback_steps'] = 30
        if name == 'direct_ridge':
            fitted.update(lag_steps=10, coefficient=np.zeros((20,60)).tolist(), intercept=[-6.]*60)
        if name == 'persistence_empirical':
            fitted['increment_quantiles'] = np.broadcast_to([-.2,-.1,0.,.1,.2],(150,2,5)).tolist()
        summary['fits'][name]['parameters'] = fitted
    write_json(v1/'summary.json', summary)
    # Three invented origins span several calendar blocks for all1/3/7-day
    # settings; a same-day fixture cannot identify a block sensitivity.
    issues = np.array([1735696800000000000, 1736647200000000000, 1737684000000000000], dtype=np.int64)
    ids = [f'origin:{x}' for x in issues]
    for member in ('contexts.json', 'future_grid.json'):
        document = json.loads((prep/member).read_text())
        shifts = issues-np.asarray(document['issue_times_ns'], dtype=np.int64)
        document.update(issue_times_ns=issues.tolist(), origin_ids=ids)
        for key in ('starts_ns','ends_ns'):
            document[key] = (np.asarray(document[key], dtype=np.int64)+shifts[:,None]).tolist()
        write_json(prep/member,document)
    targets = json.loads((prep/'targets.json').read_text())
    targets['grid'] = json.loads((prep/'future_grid.json').read_text())
    write_json(prep/'targets.json',targets)
    window = json.loads((prep/'window_manifest.json').read_text())
    for row, issue, origin_id in zip(window['support_manifest'], issues, ids):
        shift = int(issue)-row['issue_time_ns']
        for key,value in row.items():
            if key.endswith('_ns'):
                row[key] = value+shift
        row['origin_id'] = origin_id
    window['retained_origins'] = ids
    window['excluded_origins'] = [dict(origin_id=f'origin:{t}', issue_time_ns=t, reasons=['invalid_features'])
        for t in range(1735689600000000000,1738368000000000000,1800000000000) if t not in issues]
    write_json(prep/'window_manifest.json',window)
    prep_summary = json.loads((prep/'summary.json').read_text())
    prep_summary['split_fingerprint'] = fingerprint_payload(window)
    write_json(prep/'summary.json',prep_summary)
    seal(frozen_fixture)
    root = Path(protocol['code_root'])
    cfg = root/'configs/evaluation/protocol.json'
    write_json(cfg, protocol)
    for name in ('requirements-training-lock.txt', 'requirements-v1-lock.txt'):
        (root/name).write_text('# invented runtime lock\n')
    # Synthetic source tree has no Git/installation. Only that boundary is doubled;
    # authenticated input loading, predictors, metrics and publication are real.
    def provenance(root, *, require_clean, require_installed_match):
        assert require_clean is True and require_installed_match is True
        return dict(git_commit='synthetic-inference', source=dict(files=[], fingerprint='synthetic-code'))
    monkeypatch.setattr(TrainedJepa, 'predict', ORIGINAL_PREDICT)
    return dict(v1=v1, prep=prep, protocol=protocol, root=root, config=cfg,
                output=root/'results/experiments/synthetic-execution', provenance=provenance)


def setup(fixture, monkeypatch):
    module = runner()
    monkeypatch.setattr(module, 'code_provenance', fixture['provenance'])
    return module


def run(module, f, **kwargs):
    return module.run_external_evaluation(f['config'], f['root'], v1_dir=f['v1'],
        preparation_dir=f['prep'], output_dir=f['output'], approval_reference='synthetic-test-only', **kwargs)


def test_preflight_does_not_infer(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    def forbidden(*args, **kwargs):
        raise AssertionError('Preflight must not construct or invoke predictors')
    monkeypatch.setattr(TrainedJepa, 'load', forbidden)
    monkeypatch.setattr(module, 'load_frozen_baseline', forbidden)
    result = module.preflight_external_evaluation(f['config'], f['root'],
        v1_dir=f['v1'], preparation_dir=f['prep'], output_dir=f['output'])
    assert result['inference_performed'] is False
    assert result['protocol_file_identity'] == identity(f['config'])
    assert result['historical_runtime']['package_versions']['scipy'] is None
    assert set(result['historical_runtime']['checkpoint_torch_versions']) == {
        x['model'] for x in f['protocol']['checkpoint_cohort']}
    assert result['fit_performed'] is False
    assert len(result['checkpoints']) == 9
    assert len(result['classical_models']) == 13
    assert not f['output'].exists()


def test_installed_source_mismatch_aborts(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    def mismatch(*args, **kwargs):
        raise ValueError('Imported/checkout source identity mismatch')
    monkeypatch.setattr(module, 'code_provenance', mismatch)
    with pytest.raises(ValueError, match='source identity mismatch'):
        run(module, f)
    assert not f['output'].exists()


def test_synthetic_end_to_end_no_training(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    import scipy.optimize
    from solar_flare_jepa.forecasting.baselines import _Baseline
    from solar_flare_jepa.training import jepa
    from statsmodels.tsa.statespace.mlemodel import MLEModel
    from arch.univariate.base import ARCHModel
    def forbidden(*args, **kwargs):
        raise AssertionError('Fitting/optimization forbidden')
    for obj, name in [(_Baseline,'fit'), (jepa,'fit_forecaster'), (MLEModel,'fit'),
                      (ARCHModel,'fit'), (scipy.optimize,'minimize')]:
        monkeypatch.setattr(obj, name, forbidden)
    destination = run(module, f)
    result = json.loads((destination/'summary.json').read_text())
    predictions = json.loads((destination/'predictions.json').read_text())
    inputs = json.loads((destination/'inputs.json').read_text())
    assert inputs['context']['values'][0][0] == [1e-6,1e-6]
    assert inputs['targets']['values'][0][0] == [2e-6,2e-6]
    assert inputs['future_grid']['dataset_fingerprint'] == 'synthetic-external-dataset'
    assert result['fit_performed'] is False
    assert result['execution_approval']['reference'] == 'synthetic-test-only'
    assert result['execution_approval']['authenticated_by_code'] is False
    assert result['scope'] == 'bounded_retrospective_continuous_flux_replication'
    assert 'actual_operational_delivery_UNKNOWN' in result['limitations']
    assert set(predictions) == {p['model'] for p in f['protocol']['checkpoint_cohort']} | set(f['protocol']['classical_models'])
    assert len(predictions) == 22
    assert set(result['cohort']['variants']) == {'jepa_finetune', 'jepa_frozen', 'supervised'}
    assert len(result['cohort']['classical_models']) == 13
    assert set(result['inference_runtime']['packages']) >= {'torch','scipy','statsmodels','arch'}
    assert {x['path'] for x in result['inference_runtime']['lockfiles']} == {
        'requirements-lock.txt','requirements-training-lock.txt','requirements-v1-lock.txt'}
    assert result['historical_source']['git_commit'] == 'historical-synthetic-commit'


def test_failed_arm_aborts_common_comparison(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    original = TrainedJepa.predict
    def fail(self, context, grid):
        if self.variant == 'supervised' and self.config.seed == 43:
            raise ValueError('Invented failed arm')
        return original(self, context, grid)
    monkeypatch.setattr(TrainedJepa, 'predict', fail)
    with pytest.raises(ValueError, match='Invented failed arm'):
        run(module, f)
    assert not f['output'].exists()


def test_output_is_no_replace_and_inputs_unchanged(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    before = {p: p.read_bytes() for base in (f['v1'],f['prep']) for p in base.iterdir()}
    run(module, f)
    saved = (f['output']/'summary.json').read_bytes()
    with pytest.raises(FileExistsError):
        run(module, f)
    assert saved == (f['output']/'summary.json').read_bytes()
    assert all(p.read_bytes() == payload for p,payload in before.items())


def test_saved_checkpoint_batching_is_preserved(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    original = TrainedJepa.predict
    observed = []
    def verify(self, context, grid):
        observed.append(deepcopy(self.record))
        assert self.config.batch_size == 256
        assert self.config.threads == 1
        return original(self, context, grid)
    monkeypatch.setattr(TrainedJepa, 'predict', verify)
    run(module, f)
    summary = json.loads((f['v1']/'summary.json').read_text())
    assert observed == [summary['fits'][p['model']]['record'] for p in f['protocol']['checkpoint_cohort']]


@pytest.mark.parametrize('reference', [None, '', '   '])
def test_execution_requires_explicit_nonempty_reference(execution_fixture, monkeypatch, reference):
    f = execution_fixture
    module = setup(f, monkeypatch)
    with pytest.raises(ValueError, match='approval'):
        module.run_external_evaluation(f['config'], f['root'], v1_dir=f['v1'],
            preparation_dir=f['prep'], output_dir=f['output'], approval_reference=reference)
    assert not f['output'].exists()


def test_changed_consumed_inputs_abort_publication(execution_fixture, monkeypatch):
    f = execution_fixture
    module = setup(f, monkeypatch)
    original = TrainedJepa.predict
    def tamper(self, context, grid):
        value = original(self, context, grid)
        if self.variant == 'supervised' and self.config.seed == 43:
            path = f['prep']/'contexts.json'
            path.write_bytes(path.read_bytes()+b' ')
        return value
    monkeypatch.setattr(TrainedJepa, 'predict', tamper)
    with pytest.raises(ValueError, match='identity'):
        run(module, f)
    assert not f['output'].exists()


def cli():
    spec = importlib.util.spec_from_file_location('external_runner_cli', ROOT/'scripts/evaluate_external_models.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli_args(f):
    return ['--root', str(f['root']), '--config', str(f['config']), '--v1-dir', str(f['v1']),
            '--preparation-dir', str(f['prep']), '--output-dir', str(f['output'])]


def test_cli_defaults_to_preflight(execution_fixture, monkeypatch, capsys):
    f = execution_fixture
    setup(f, monkeypatch)
    def forbidden(*args, **kwargs):
        raise AssertionError('Default CLI must not load predictors')
    monkeypatch.setattr(TrainedJepa, 'load', forbidden)
    cli().main(cli_args(f))
    assert json.loads(capsys.readouterr().out)['inference_performed'] is False
    assert not f['output'].exists()


@pytest.mark.parametrize('extra', [['--execute'], ['--execute','--approval-reference',' '], ['--dev']])
def test_cli_rejects_missing_approval_and_source_bypass(execution_fixture, extra):
    with pytest.raises(SystemExit) as error:
        cli().main(cli_args(execution_fixture)+extra)
    assert error.value.code == 2


@pytest.mark.parametrize('changed', ['protocol','source','runtime_lock'])
def test_changed_execution_provenance_aborts_publication(execution_fixture, monkeypatch, changed):
    f = execution_fixture
    module = setup(f, monkeypatch)
    original = TrainedJepa.predict
    def tamper(self, context, grid):
        prediction = original(self, context, grid)
        if self.variant == 'supervised' and self.config.seed == 43:
            if changed == 'protocol':
                f['config'].write_bytes(f['config'].read_bytes()+b' ')
            elif changed == 'runtime_lock':
                path = f['root']/'requirements-v1-lock.txt'
                path.write_bytes(path.read_bytes()+b' ')
            else:
                monkeypatch.setattr(module, 'code_provenance', lambda *args,**kwargs: dict(
                    git_commit='changed-source', source=dict(files=[], fingerprint='changed-source')))
        return prediction
    monkeypatch.setattr(TrainedJepa, 'predict', tamper)
    with pytest.raises(ValueError, match='changed'):
        run(module, f)
    assert not f['output'].exists()


def test_publication_inputs_preserve_native_values_masks_and_unknowns(execution_fixture, monkeypatch):
    from solar_flare_jepa.forecasting.contracts import ForecastTargets
    f = execution_fixture
    module = setup(f, monkeypatch)
    frozen = module.load_frozen_inputs(f['v1'],f['prep'],f['protocol'])
    values, mask = frozen['targets'].values.copy(), frozen['targets'].mask.copy()
    values[0,0,0], mask[0,0,0] = np.nan, False
    frozen['targets'] = ForecastTargets(values,mask,frozen['targets'].grid)
    published = module._publication_inputs(frozen)
    assert published['context']['values'][0][0] == [1e-6,1e-6]
    assert published['targets']['values'][0][0] == [None,2e-6]
    assert published['targets']['mask'][0][0] == [False,True]
    assert published['future_grid']['dataset_fingerprint'] == 'synthetic-external-dataset'
    assert published['candidate_issue_times_ns'][0] == 1735689600000000000
    assert published['retained_candidate_indices'] == [4,532,1108]


def test_saved_256_batch_size_controls_actual_forecast_calls(execution_fixture, monkeypatch):
    from solar_flare_jepa.forecasting.contracts import ForecastContext, ForecastTargets, FutureGrid
    import torch
    f = execution_fixture
    module = setup(f, monkeypatch)
    frozen = module.load_frozen_inputs(f['v1'],f['prep'],f['protocol'])
    spec = frozen['context'].spec
    issues = 1735696800000000000+np.arange(257,dtype=np.int64)*1800000000000
    ids = tuple(f'invented-batch-origin:{i}' for i in range(257))
    past = issues[:,None]+np.arange(-120,0,dtype=np.int64)[None,:]*60000000000
    future = issues[:,None]+np.arange(30,dtype=np.int64)[None,:]*60000000000
    frozen['context'] = ForecastContext(np.full((257,120,2),1e-6),np.ones((257,120,2),bool),
        past,past+60000000000,issues,ids,spec,'synthetic-external-dataset')
    grid = FutureGrid(future,future+60000000000,issues,ids,spec,'synthetic-external-dataset')
    frozen['targets'] = ForecastTargets(np.full((257,30,2),2e-6),np.ones((257,30,2),bool),grid)
    original_load = TrainedJepa.load
    calls, private_paths = {}, []
    def load(cls,path):
        path = Path(path)
        assert path.is_relative_to(f['root']/'results/experiments')
        private_paths.append(path)
        model = original_load(path)
        key = f'{model.variant}_seed{model.config.seed}'
        original_forecast = model._model.forecast
        def forecast(features, mask):
            assert torch.get_num_threads() == model.config.threads
            assert torch.are_deterministic_algorithms_enabled()
            calls.setdefault(key, []).append(len(features))
            return original_forecast(features,mask)
        monkeypatch.setattr(model._model,'forecast',forecast)
        return model
    monkeypatch.setattr(TrainedJepa,'load',classmethod(load))
    outputs, execution = module._checkpoint_predictions(frozen,f['root'])
    assert len(outputs) == 9
    assert all(batches == [256,1] for batches in calls.values())
    assert all(prediction.values.shape == (257,30,2) for prediction in outputs.values())
    assert all(not path.exists() for path in private_paths)


def test_fresh_runner_dependency_closure_preserves_strict_provenance(tmp_path):
    """Late calendar import must not invalidate a fresh process's source record.

    This clean copied Git fixture exercises both strict guards without mutating
    the repository or relaxing production provenance. Installed qualification is
    a separate coordinator check against the committed normal installation.
    """
    import os
    import shutil
    import subprocess
    import sys
    copied = tmp_path/'clean-source-fixture'
    copied.mkdir()
    for name in ('src','scripts','configs','schemas'):
        shutil.copytree(ROOT/name,copied/name,ignore=shutil.ignore_patterns('__pycache__','*.egg-info'))
    for name in ('pyproject.toml','requirements-lock.txt','.gitignore'):
        shutil.copyfile(ROOT/name,copied/name)
    for command in (['git','init','-q'], ['git','add','src','scripts','configs','schemas',
                     'pyproject.toml','requirements-lock.txt','.gitignore'],
                    ['git','-c','user.name=Synthetic Fixture','-c','user.email=fixture@example.invalid',
                     'commit','-qm','test: synthetic clean source fixture']):
        subprocess.run(command,cwd=copied,check=True,capture_output=True,text=True)
    environment = dict(os.environ,PYTHONPATH=str(copied/'src'),PYTHONDONTWRITEBYTECODE='1')
    program = '''
import importlib
import json
from pathlib import Path
import sys
from solar_flare_jepa.experiments import external_evaluation
from solar_flare_jepa.experiments.provenance import code_provenance

def forbidden(*args, **kwargs):
    raise AssertionError('No model loading, prediction or fitting in provenance regression')
external_evaluation.TrainedJepa.load = forbidden
external_evaluation.TrainedJepa.predict = forbidden
external_evaluation.load_frozen_baseline = forbidden
before = code_provenance(Path.cwd(), require_clean=True, require_installed_match=True)
importlib.import_module('solar_flare_jepa.evaluation.uncertainty')
after = code_provenance(Path.cwd(), require_clean=True, require_installed_match=True)
print(json.dumps({'full_provenance_equal': before == after,
                  'source_fingerprint_equal': before['source'] == after['source'],
                  'changed_fields': [key for key in before if before[key] != after[key]],
                  'inference_performed': False}))
'''
    completed = subprocess.run([sys.executable,'-c',program],cwd=copied,env=environment,
                               capture_output=True,text=True,check=True)
    evidence = json.loads(completed.stdout)
    assert evidence['full_provenance_equal'], evidence
    assert evidence['source_fingerprint_equal']
    assert evidence['inference_performed'] is False
