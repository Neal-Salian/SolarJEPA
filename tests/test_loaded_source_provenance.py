"""Executing source must match provenance in persistent and cached interpreters."""
import ast
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


def _shifted_runner(source):
    statement = '                    outputs[model_name] = prediction\n'
    assert source.count(statement) == 1
    return source.replace(statement,
        '                    prediction = type(prediction)(\n'
        '                        prediction.values + 1., prediction.grid, prediction.model_id,\n'
        '                        point_interpretation=prediction.point_interpretation,\n'
        '                        quantile_levels=prediction.quantile_levels,\n'
        '                        quantiles=prediction.quantiles)\n' + statement)


@pytest.mark.parametrize('canonical_reimport', [False, True])
@pytest.mark.parametrize('cache_module', [False, True])
def test_worker_loader_starting_before_bootstrap_cannot_escape_history(
        tmp_path, canonical_reimport, cache_module):
    root = _repository(tmp_path)
    _commit(root, 'canonical source')
    control = _cli(root, 'control')
    marker, release = tmp_path / 'started', tmp_path / 'release'
    alternate = tmp_path / 'worker-runner.py'
    prefix = (f'import pathlib,time\n_marker=pathlib.Path({str(marker)!r})\n'
              f'_release=pathlib.Path({str(release)!r})\n'
              '_marker.write_text("started")\n_deadline=time.monotonic()+15\n'
              'while not _release.exists():\n'
              '    if time.monotonic()>_deadline: raise RuntimeError("release timeout")\n'
              '    time.sleep(.01)\n')
    source = (root / 'src/solar_flare_jepa/experiments/runner.py').read_text()
    alternate.write_text(prefix + _shifted_runner(source))
    program = """
import importlib,importlib.util,json,pathlib,sys,threading,time
root,path,marker,release=map(pathlib.Path,sys.argv[1:5])
name='solar_flare_jepa.experiments.runner'
assert 'solar_flare_jepa' not in sys.modules
spec=importlib.util.spec_from_file_location(name,path)
module=importlib.util.module_from_spec(spec)
if sys.argv[6]=='cache': sys.modules[name]=module
errors=[]
def load():
    try: spec.loader.exec_module(module)
    except BaseException as error: errors.append(repr(error))
worker=threading.Thread(target=load);worker.start();deadline=time.monotonic()+15
while not marker.exists():
    assert worker.is_alive(),errors
    if time.monotonic()>deadline: raise RuntimeError('startup timeout')
    time.sleep(.01)
import solar_flare_jepa.experiments
release.write_text('continue');worker.join(15)
assert not worker.is_alive() and not errors,errors
retained=module.run_experiment;sys.modules.pop(name,None)
if sys.argv[5]=='reimport': importlib.import_module(name)
destination=root/'results/experiments/threaded'
try:
    retained('configs/experiments/p1_test.json',root,output_dir=destination)
except ValueError as error:
    observed=dict(rejected=True,error=str(error),published=destination.exists())
else:
    control=root/'results/experiments/control'
    def read(directory,name): return json.loads((directory/name).read_text())
    a,b=read(control,'result.json'),read(destination,'result.json')
    observed=dict(rejected=False,published=True,status=b['status'],
                  same_fingerprints=a['fingerprints']==b['fingerprints'],
                  same_ids=a['experiment_ids']==b['experiment_ids'],
                  same_predictions=read(control,'predictions.json')==read(destination,'predictions.json'))
print(json.dumps(observed))
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root), str(alternate),
                              str(marker), str(release),
                              'reimport' if canonical_reimport else 'evict',
                              'cache' if cache_module else 'uncached'],
                             cwd=root, env=_environment(root), capture_output=True, text=True,
                             timeout=45)
    assert process.returncode == 0, process.stderr
    observed = json.loads(process.stdout)
    assert observed['rejected'], observed
    assert not observed['published']
    assert _json(control, 'result.json')['status'] == 'complete'


@pytest.mark.parametrize('canonical_reimport', [False, True])
@pytest.mark.parametrize('source_path', ['external', 'canonical'])
def test_completed_deferred_import_loader_cannot_hide_retained_code(
        tmp_path, canonical_reimport, source_path):
    root = _repository(tmp_path)
    path = root / 'src/solar_flare_jepa/experiments/runner.py'
    canonical = path.read_text()
    current = _commit(root, 'canonical source')
    _cli(root, 'control')
    tree = ast.parse(_shifted_runner(canonical))
    imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
    names = [alias.asname or alias.name for node in imports for alias in node.names]
    tree.body = [node for node in tree.body if node not in imports]
    tree.body.append(ast.FunctionDef(name='_late_imports', args=ast.arguments(
        posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Global(names=names)] + imports, decorator_list=[]))
    run = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
               and node.name == 'run_experiment')
    run.body.insert(1, ast.Expr(value=ast.Call(func=ast.Name(id='_late_imports', ctx=ast.Load()),
                                            args=[], keywords=[])))
    altered = ast.unparse(ast.fix_missing_locations(tree))
    if source_path == 'canonical':
        path.write_text(altered)
        _commit(root, 'old deferred runner')
    else:
        path = tmp_path / 'deferred-runner.py'
        path.write_text(altered)
    program = """
import importlib,importlib.util,json,pathlib,subprocess,sys
root,path=map(pathlib.Path,sys.argv[1:3]);name='solar_flare_jepa.experiments.runner'
assert 'solar_flare_jepa' not in sys.modules
spec=importlib.util.spec_from_file_location(name,path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert 'solar_flare_jepa' not in sys.modules
retained=module.run_experiment
subprocess.run(['git','-C',str(root),'checkout','-q',sys.argv[3]],check=True)
import solar_flare_jepa.experiments
if sys.argv[4]=='reimport': importlib.import_module(name)
destination=root/'results/experiments/deferred'
try:
    retained('configs/experiments/p1_test.json',root,output_dir=destination)
except ValueError as error:
    observed=dict(rejected=True,error=str(error),published=destination.exists())
else:
    def read(directory,name): return json.loads((directory/name).read_text())
    control=root/'results/experiments/control';a,b=read(control,'result.json'),read(destination,'result.json')
    observed=dict(rejected=False,published=True,status=b['status'],
                  same_fingerprints=a['fingerprints']==b['fingerprints'],
                  same_ids=a['experiment_ids']==b['experiment_ids'],
                  same_predictions=read(control,'predictions.json')==read(destination,'predictions.json'))
print(json.dumps(observed))
"""
    process = subprocess.run([sys.executable, '-B', '-c', program, str(root), str(path), current,
                              'reimport' if canonical_reimport else 'evict'],
                             cwd=root, env=_environment(root), capture_output=True, text=True,
                             timeout=45)
    assert process.returncode == 0, process.stderr
    observed = json.loads(process.stdout)
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
