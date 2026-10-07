"""Executing source must match provenance in persistent and cached interpreters."""
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _git(root, *arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments], text=True).strip()


def _commit(root, message):
    _git(root, 'add', '.')
    _git(root, '-c', 'user.name=P1 provenance fixture',
         '-c', 'user.email=p1@example.invalid', 'commit', '-qm', message)
    return _git(root, 'rev-parse', 'HEAD')


def _repository(tmp_path):
    root = tmp_path / 'repository'
    root.mkdir()
    for directory in ('src', 'scripts', 'schemas'):
        shutil.copytree(ROOT / directory, root / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('pyproject.toml', 'requirements-lock.txt', '.gitignore'):
        shutil.copyfile(ROOT / name, root / name)
    config = dict(schema_version=1,
        dataset=dict(kind='synthetic_fixture', rows=36,
                     start_utc='2024-01-01T00:00:00Z', fixture_seed=17),
        forecast=dict(cadence_seconds=60, context_steps=2, horizon_steps=1,
                      feature_names=['x'], target_names=['x'],
                      feature_units=['synthetic_unit'], target_units=['synthetic_unit']),
        splits=[dict(name=name, start_utc=start, end_utc=end)
                for name, start, end in (
                    ('train', '2024-01-01T00:00:00Z', '2024-01-01T00:12:00Z'),
                    ('validation', '2024-01-01T00:12:00Z', '2024-01-01T00:24:00Z'),
                    ('test', '2024-01-01T00:24:00Z', '2024-01-01T00:36:00Z'))],
        baselines=[dict(name='persistence', parameters={})],
        metrics=dict(lead_weights=[1], target_weights=[1]), seeds=[17])
    path = root / 'configs' / 'experiments' / 'p1_test.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(config))
    _git(root, 'init', '-q')
    return root


def _environment(root):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(root / 'src')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def _cli(root, name):
    process = subprocess.run([sys.executable, '-B', str(root / 'scripts/run_experiment.py'),
        '--config', 'configs/experiments/p1_test.json', '--root', str(root),
        '--output-dir', f'results/experiments/{name}'], cwd=root,
        env=_environment(root), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    return root / 'results' / 'experiments' / name


def _json(directory, filename):
    return json.loads((directory / filename).read_text())


@pytest.mark.parametrize('evict_module', [False, True])
def test_persistent_api_refuses_old_loaded_source_after_clean_checkout(tmp_path, evict_module):
    root = _repository(tmp_path)
    baseline = root / 'src/solar_flare_jepa/forecasting/baselines.py'
    canonical = baseline.read_text()
    statement = 'output[n, :, k] = values[-1]\n'
    assert canonical.count(statement) == 1
    baseline.write_text(canonical.replace(statement, statement.rstrip() + ' + 1.\n', 1))
    old = _commit(root, 'old persistence implementation')
    baseline.write_text(canonical)
    current = _commit(root, 'canonical persistence implementation')
    fresh = _cli(root, 'fresh')
    _git(root, 'checkout', '-q', old)
    program = """
import json,pathlib,subprocess,sys
from solar_flare_jepa.experiments.runner import run_experiment
root=pathlib.Path(sys.argv[1]); current=sys.argv[2]
subprocess.run(['git','-C',str(root),'checkout','-q',current],check=True)
if sys.argv[3]=='evict':
    sys.modules.pop('solar_flare_jepa.forecasting.baselines')
assert not subprocess.check_output(['git','-C',str(root),'status','--porcelain',
                                   '--untracked-files=no'],text=True)
destination=root/'results/experiments/stale'
try:
    output=run_experiment('configs/experiments/p1_test.json',root,output_dir=destination)
except ValueError as error:
    print(json.dumps(dict(rejected=True,error=str(error),published=destination.exists())))
else:
    result=json.loads((output/'result.json').read_text())
    predictions=json.loads((output/'predictions.json').read_text())
    provenance=json.loads((output/'provenance.json').read_text())
    print(json.dumps(dict(rejected=False,published=True,result=result,
        first_prediction=predictions[0]['values'][0][0][0],
        all_checkout_match=all(x['checkout_match'] for x in provenance['imported_source']))))
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root), current,
                              'evict' if evict_module else 'retain'],
                             cwd=root, env=_environment(root), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    observed = json.loads(process.stdout)
    # Include the actual semantic collision in the red failure, rather than
    # mistaking a process error or an ordinary dirty-tree refusal for proof.
    if not observed['rejected']:
        control = _json(fresh, 'result.json')
        observed['same_fingerprints_as_fresh'] = observed['result']['fingerprints'] == control['fingerprints']
        observed['same_experiment_ids_as_fresh'] = observed['result']['experiment_ids'] == control['experiment_ids']
        observed['fresh_first_prediction'] = _json(fresh, 'predictions.json')[0]['values'][0][0][0]
    assert observed['rejected'], observed
    assert not observed['published']
    assert not list((root / 'results/experiments').glob('.stage-*'))


def test_unchanged_source_supports_repeated_persistent_api_and_fresh_cli(tmp_path):
    root = _repository(tmp_path)
    _commit(root, 'canonical source')
    program = """
import pathlib,sys
from solar_flare_jepa.experiments.runner import run_experiment
root=pathlib.Path(sys.argv[1])
for name in ('api-one','api-two'):
    run_experiment('configs/experiments/p1_test.json',root,
                   output_dir=root/'results/experiments'/name)
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root)], cwd=root,
                             env=_environment(root), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    directories = [root / 'results/experiments' / name for name in ('api-one', 'api-two')]
    directories.append(_cli(root, 'fresh'))
    results = [_json(directory, 'result.json') for directory in directories]
    assert all(result['status'] == 'complete' for result in results)
    assert all(result['experiment_ids'] == results[0]['experiment_ids'] for result in results)
    predictions = [_json(directory, 'predictions.json') for directory in directories]
    assert predictions[0] == predictions[1] == predictions[2]


def test_timestamp_valid_old_bytecode_cannot_change_fresh_cli_computation(tmp_path):
    root = _repository(tmp_path)
    _commit(root, 'canonical source')
    control = _cli(root, 'control')
    baseline = root / 'src/solar_flare_jepa/forecasting/baselines.py'
    canonical = baseline.read_bytes()
    old = canonical.replace(b'output[n, :, k] = values[-1]',
                            b'output[n, :, k] = values[+0]', 1)
    assert old != canonical and len(old) == len(canonical)
    # CPython timestamp caches identify source by integer mtime and byte count.
    # A same-size edit/checkout within one timestamp quantum can therefore
    # leave an old cache valid. Control that quantum explicitly and boundedly.
    timestamp = 1_600_000_000
    baseline.write_bytes(old)
    os.utime(baseline, (timestamp, timestamp))
    cache = Path(py_compile.compile(str(baseline), doraise=True,
                                  invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP))
    baseline.write_bytes(canonical)
    os.utime(baseline, (timestamp, timestamp))
    assert cache.is_file()
    assert not _git(root, 'status', '--porcelain', '--untracked-files=no')
    output = _cli(root, 'cached')
    result, expected = [_json(directory, 'result.json') for directory in (output, control)]
    assert result['fingerprints'] == expected['fingerprints']
    assert result['experiment_ids'] == expected['experiment_ids']
    assert _json(output, 'predictions.json') == _json(control, 'predictions.json')
    assert _json(output, 'metrics.json') == _json(control, 'metrics.json')


def test_alternate_loader_cannot_reuse_an_earlier_module_source_capture(tmp_path):
    root = _repository(tmp_path)
    _commit(root, 'canonical source')
    control = _cli(root, 'control')
    program = """
import importlib.util,json,pathlib,sys
from solar_flare_jepa.forecasting import baselines
root=pathlib.Path(sys.argv[1]); source=root/'src/solar_flare_jepa/forecasting/baselines.py'
canonical=source.read_text(); statement='output[n, :, k] = values[-1]\\n'
source.write_text(canonical.replace(statement,statement.rstrip()+' + 1.\\n',1))
name=baselines.__name__
spec=importlib.util.spec_from_file_location(name,source)
alternate=importlib.util.module_from_spec(spec)
sys.modules[name]=alternate
try:
    spec.loader.exec_module(alternate)
finally:
    source.write_text(canonical)
from solar_flare_jepa.experiments.runner import run_experiment
destination=root/'results/experiments/alternate'
try:
    output=run_experiment('configs/experiments/p1_test.json',root,output_dir=destination)
except ValueError as error:
    print(json.dumps(dict(rejected=True,error=str(error),published=destination.exists())))
else:
    result=json.loads((output/'result.json').read_text())
    values=json.loads((output/'predictions.json').read_text())
    print(json.dumps(dict(rejected=False,published=True,result=result,
                         first_prediction=values[0]['values'][0][0][0])))
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root)], cwd=root,
                             env=_environment(root), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    observed = json.loads(process.stdout)
    if not observed['rejected']:
        expected = _json(control, 'result.json')
        observed['same_fingerprints'] = expected['fingerprints'] == observed['result']['fingerprints']
        observed['same_experiment_ids'] = expected['experiment_ids'] == observed['result']['experiment_ids']
        observed['control_prediction'] = _json(control, 'predictions.json')[0]['values'][0][0][0]
    assert observed['rejected'], observed
    assert not observed['published']


@pytest.mark.parametrize('loader_path', ['existing-module', 'new-module', 'load-module', 'external-source'])
def test_alternate_loader_cannot_attest_stale_bytecode_as_canonical_source(tmp_path, loader_path):
    root = _repository(tmp_path)
    _commit(root, 'canonical source')
    program = """
import importlib.machinery,importlib.util,json,os,pathlib,py_compile,sys
from solar_flare_jepa.forecasting import baselines
from solar_flare_jepa.experiments.runner import run_experiment
root=pathlib.Path(sys.argv[1]); mode=sys.argv[2]
source=root/'src/solar_flare_jepa/forecasting/baselines.py'
canonical=source.read_bytes()
stale=canonical.replace(b'output[n, :, k] = values[-1]',b'output[n, :, k] = values[+0]',1)
assert stale!=canonical and len(stale)==len(canonical)
stamp=1_600_000_000
source.write_bytes(stale);os.utime(source,(stamp,stamp))
py_compile.compile(str(source),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
source.write_bytes(canonical);os.utime(source,(stamp,stamp))
name=baselines.__name__
if mode=='external-source':
    clone=root.parent/'alternate-baselines.py'
    clone.write_bytes(canonical.replace(b'output[n, :, k] = values[-1]',
                                       b'output[n, :, k] = values[-1] + 1.',1))
    importlib.machinery.SourceFileLoader(name,str(clone)).exec_module(baselines)
elif mode=='existing-module':
    importlib.machinery.SourceFileLoader(name,str(source)).exec_module(baselines)
elif mode=='load-module':
    importlib.machinery.SourceFileLoader(name,str(source)).load_module()
else:
    spec=importlib.util.spec_from_file_location(name,source)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
destination=root/'results/experiments/alternate-cache'
try:
    run_experiment('configs/experiments/p1_test.json',root,output_dir=destination)
except ValueError as error:
    print(json.dumps(dict(rejected=True,error=str(error),published=destination.exists())))
else:
    print(json.dumps(dict(rejected=False,published=True)))
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root), loader_path],
                             cwd=root, env=_environment(root), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    observed = json.loads(process.stdout)
    assert observed['rejected'], observed
    assert not observed['published']


@pytest.mark.parametrize('canonical_reimport', [False, True])
@pytest.mark.parametrize('package_preimport', [False, True])
@pytest.mark.parametrize('cache_module', [False, True])
def test_first_alternate_execution_cannot_disappear_before_source_attestation(
        tmp_path, canonical_reimport, package_preimport, cache_module):
    root = _repository(tmp_path)
    _commit(root, 'canonical source')
    source = (root / 'src/solar_flare_jepa/experiments/runner.py').read_text()
    statement = "model = make_baseline(name, definition['parameters'])"
    assert source.count(statement) == 1
    alternate = root.parent / 'first-alternate-runner.py'
    alternate.write_text(source.replace(statement, "model = make_baseline('training_mean', {})"))
    program = """
import importlib,importlib.util,json,pathlib,sys
if sys.argv[4]=='preimport':
    import solar_flare_jepa.experiments
root=pathlib.Path(sys.argv[1]); path=pathlib.Path(sys.argv[2])
name='solar_flare_jepa.experiments.runner'
assert name not in sys.modules
spec=importlib.util.spec_from_file_location(name,path)
module=importlib.util.module_from_spec(spec)
if sys.argv[5]=='cache':
    sys.modules[name]=module
spec.loader.exec_module(module)
retained=module.run_experiment
sys.modules.pop(name,None)
if sys.argv[3]=='reimport':
    canonical=importlib.import_module(name)
    assert canonical.run_experiment is not retained
destination=root/'results/experiments/retained-first'
try:
    retained('configs/experiments/p1_test.json',root,output_dir=destination)
except ValueError as error:
    print(json.dumps(dict(rejected=True,error=str(error),published=destination.exists())))
else:
    print(json.dumps(dict(rejected=False,published=True)))
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root), str(alternate),
                              'reimport' if canonical_reimport else 'evict',
                              'preimport' if package_preimport else 'bootstrap',
                              'cache' if cache_module else 'uncached'],
                             cwd=root, env=_environment(root), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    observed = json.loads(process.stdout)
    assert observed['rejected'], observed
    assert 'Executed/recorded project source mismatch' in observed['error']
    assert not observed['published']
