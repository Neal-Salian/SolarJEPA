"""Executable-source inventories reject redirection instead of hiding its bytes.

These fixtures contain synthetic source/configuration only. Symlink targets may
have identical bytes: identity equality must not bypass the source-path policy.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from solar_flare_jepa.experiments import provenance
from test_experiment_provenance import config


ROOT = Path(__file__).resolve().parents[1]


def _git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _commit(root):
    _git(root, 'add', '.')
    _git(root, '-c', 'user.name=P1 source test', '-c',
         'user.email=source-test@example.invalid', 'commit', '-qm', 'source fixture')


def _source_root(tmp_path):
    root = tmp_path.resolve() / 'source'
    for directory in ('src', 'scripts', 'configs/experiments', 'schemas'):
        (root / directory).mkdir(parents=True)
    for name, contents in [('src/module.py', 'value = 42\n'),
                           ('scripts/run.py', 'pass\n'),
                           ('configs/experiments/p1_test.json', '{}\n'),
                           ('pyproject.toml', ''), ('requirements-lock.txt', ''),
                           ('schemas/experiment_result.schema.json', '{}\n')]:
        (root / name).write_text(contents)
    return root


def _repository(tmp_path):
    root = tmp_path.resolve() / 'repository'
    root.mkdir()
    for name in ('src', 'scripts', 'schemas'):
        shutil.copytree(ROOT / name, root / name,
                        ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('pyproject.toml', 'requirements-lock.txt', '.gitignore'):
        shutil.copyfile(ROOT / name, root / name)
    cfg = config()
    cfg['seeds'] = [17]
    cfg['baselines'] = [dict(name='training_mean', parameters={})]
    path = root / 'configs/experiments/p1_test.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(cfg))
    _git(root, 'init', '-q')
    _commit(root)
    return root, path


def _replace_with_link(path, target, *, relative=True):
    path.unlink()
    path.symlink_to(os.path.relpath(target, path.parent) if relative else target)


@pytest.mark.parametrize('kind', [
    'directory-relative-inside', 'directory-absolute-inside',
    'directory-relative-outside', 'directory-absolute-outside',
    'file-relative-inside', 'file-absolute-inside',
    'file-relative-outside', 'file-absolute-outside',
    'nested-directory', 'dangling-directory', 'dangling-file',
    'self-loop-directory', 'self-loop-file', 'two-link-loop',
])
def test_default_discovery_refuses_source_links_without_following_them(tmp_path, kind):
    root = _source_root(tmp_path)
    outside = tmp_path.resolve() / 'outside'
    outside.mkdir()
    if kind.startswith(('directory-', 'file-')) and 'dangling' not in kind:
        target_root = root / 'aux' if kind.endswith('inside') else outside
        target_root.mkdir(exist_ok=True)
        (target_root / 'module.py').write_text('value = 42\n')
        directory = kind.startswith('directory-')
        link = root / 'src' / ('redirect' if directory else 'linked.py')
        target = target_root if directory else target_root / 'module.py'
        link.symlink_to(os.path.relpath(target, link.parent)
                        if '-relative-' in kind else target,
                        target_is_directory=directory)
    elif kind == 'nested-directory':
        (root / 'src/nested').mkdir()
        (root / 'aux').mkdir()
        (root / 'aux/module.py').write_text('value = 42\n')
        (root / 'src/nested/redirect').symlink_to('../../aux', target_is_directory=True)
    elif kind.startswith('dangling-'):
        link = root / 'src' / ('missing.py' if kind.endswith('file') else 'missing')
        link.symlink_to('absent-target', target_is_directory=kind.endswith('directory'))
    elif kind.startswith('self-loop-'):
        link = root / 'src' / ('loop.py' if kind.endswith('file') else 'loop')
        link.symlink_to(link.name, target_is_directory=kind.endswith('directory'))
    else:
        (root / 'src/loop-a').symlink_to('loop-b', target_is_directory=True)
        (root / 'src/loop-b').symlink_to('loop-a', target_is_directory=True)
    with pytest.raises(ValueError):
        provenance.source_fingerprint(root)


@pytest.mark.parametrize('identifier', [
    'src/module.py', 'scripts/run.py', 'configs/experiments/p1_test.json',
    'pyproject.toml', 'requirements-lock.txt',
    'schemas/experiment_result.schema.json',
])
def test_explicit_source_paths_refuse_same_byte_file_symlinks(tmp_path, identifier):
    root = _source_root(tmp_path)
    path = root / identifier
    target = root / 'same-bytes'
    target.write_bytes(path.read_bytes())
    _replace_with_link(path, target)
    with pytest.raises(ValueError):
        provenance.source_fingerprint(root, [identifier])


@pytest.mark.parametrize('identifier', ['src/module.py', 'scripts/run.py'])
def test_explicit_source_paths_refuse_symlink_directory_components(tmp_path, identifier):
    root = _source_root(tmp_path)
    parent = (root / identifier).parent
    target = root / 'redirected-directory'
    parent.rename(target)
    parent.symlink_to(target.name, target_is_directory=True)
    with pytest.raises(ValueError):
        provenance.source_fingerprint(root, [identifier])


@pytest.mark.parametrize('directory', ['src', 'scripts', 'configs/experiments', 'schemas'])
def test_default_inventory_refuses_redirected_source_input_directories(tmp_path, directory):
    root = _source_root(tmp_path)
    path = root / directory
    target = root / 'saved-directory'
    path.rename(target)
    path.symlink_to(os.path.relpath(target, path.parent), target_is_directory=True)
    with pytest.raises(ValueError):
        provenance.source_fingerprint(root)


@pytest.mark.parametrize('entry', ['root', 'ancestor'])
@pytest.mark.parametrize('operation', ['fingerprint', 'verify'])
def test_source_helpers_refuse_symlink_checkout_root_components(tmp_path, entry, operation):
    root = _source_root(tmp_path)
    identities = provenance.source_fingerprint(root, ['src/module.py'])['files']
    alias = tmp_path.resolve() / 'alias'
    if entry == 'root':
        alias.symlink_to(root, target_is_directory=True)
        supplied = alias
    else:
        alias.symlink_to(root.parent, target_is_directory=True)
        supplied = alias / root.name
    with pytest.raises(ValueError):
        if operation == 'fingerprint':
            provenance.source_fingerprint(supplied, ['src/module.py'])
        else:
            provenance.verify_source_identities(supplied, identities)


@pytest.mark.parametrize('replacement', ['file', 'directory'])
def test_verification_refuses_same_byte_symlink_replacement_after_hash(tmp_path, replacement):
    root = _source_root(tmp_path)
    before = provenance.source_fingerprint(root, ['src/module.py'])
    if replacement == 'file':
        target = root / 'saved.py'
        shutil.copyfile(root / 'src/module.py', target)
        _replace_with_link(root / 'src/module.py', target)
    else:
        (root / 'src').rename(root / 'saved-src')
        (root / 'src').symlink_to('saved-src', target_is_directory=True)
    with pytest.raises(ValueError):
        provenance.verify_source_identities(root, before['files'])


@pytest.mark.parametrize('operation', ['fingerprint', 'verify'])
@pytest.mark.parametrize('timing', ['before-read', 'after-read'])
def test_hashing_refuses_file_replaced_by_symlink_during_hash(
        tmp_path, monkeypatch, operation, timing):
    root = _source_root(tmp_path)
    path = root / 'src/module.py'
    target = root / 'saved.py'
    shutil.copyfile(path, target)
    identities = provenance.source_fingerprint(root, ['src/module.py'])['files']
    original = provenance.sha256_file

    def replace_around_read(candidate):
        if timing == 'before-read' and Path(candidate) == path and not path.is_symlink():
            _replace_with_link(path, target)
        digest = original(candidate)
        if timing == 'after-read' and Path(candidate) == path and not path.is_symlink():
            _replace_with_link(path, target)
        return digest

    monkeypatch.setattr(provenance, 'sha256_file', replace_around_read)
    with pytest.raises(ValueError):
        if operation == 'fingerprint':
            provenance.source_fingerprint(root, ['src/module.py'])
        else:
            provenance.verify_source_identities(root, identities)


def test_ordinary_source_inventory_is_portable_deterministic_and_complete(tmp_path):
    root = _source_root(tmp_path)
    clone = tmp_path.resolve() / 'clone'
    shutil.copytree(root, clone)
    first = provenance.source_fingerprint(root)
    second = provenance.source_fingerprint(clone)
    assert first == second
    assert [item['path'] for item in first['files']] == [
        'configs/experiments/p1_test.json', 'pyproject.toml', 'requirements-lock.txt',
        'schemas/experiment_result.schema.json', 'scripts/run.py', 'src/module.py']
    assert str(tmp_path) not in json.dumps(first)
    provenance.verify_source_identities(clone, first['files'])


def test_loaded_project_module_missing_from_checkout_inventory_is_refused(tmp_path, monkeypatch):
    root, _ = _repository(tmp_path)
    path = tmp_path.resolve() / 'unrecorded.py'
    path.write_text('executed_value = 42\n')
    name = 'solar_flare_jepa.experiments.unrecorded_probe'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.executed_value == 42
    monkeypatch.setitem(sys.modules, name, module)
    with pytest.raises(ValueError):
        provenance.code_provenance(root)


@pytest.mark.parametrize('replacement', ['file', 'directory'])
def test_runner_final_recheck_refuses_committed_same_byte_source_redirection(
        tmp_path, monkeypatch, replacement):
    from solar_flare_jepa.experiments import runner
    root, path = _repository(tmp_path)
    original = runner._dataset

    def replace_after_initial_provenance(cfg, worktree):
        dataset = original(cfg, worktree)
        source = root / 'src/solar_flare_jepa/forecasting'
        (root / 'aux').mkdir()
        (root / '.gitignore').write_text((root / '.gitignore').read_text() + '\n/aux/\n')
        if replacement == 'file':
            target = root / 'aux/baselines.py'
            shutil.copyfile(source / 'baselines.py', target)
            _replace_with_link(source / 'baselines.py', target)
        else:
            source.rename(root / 'aux/forecasting')
            source.symlink_to('../../aux/forecasting', target_is_directory=True)
        _commit(root)
        return dataset

    monkeypatch.setattr(runner, '_dataset', replace_after_initial_provenance)
    with pytest.raises(ValueError):
        runner.run_experiment(path, root)
    assert not list((root / 'results/experiments').glob('*/result.json'))


def _cli(root, path, cwd, pythonpath, name):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(pythonpath)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return subprocess.run([sys.executable, '-B', str(root / 'scripts/run_experiment.py'),
                           '--config', str(path), '--root', str(root),
                           '--output-dir', f'results/experiments/{name}'],
                          cwd=cwd, env=env, capture_output=True, text=True, timeout=45)


@pytest.mark.parametrize('layout', ['ordinary', 'package-directory', 'package-file',
                                    'ancestor', 'module-file', 'module-directory'])
def test_fresh_cli_refuses_symlink_execution_package_paths(tmp_path, layout):
    root, path = _repository(tmp_path)
    execution = tmp_path.resolve() / 'execution'
    shutil.copytree(root / 'src', execution)
    package = execution / 'solar_flare_jepa'
    pythonpath = execution
    if layout == 'package-directory':
        package.rename(execution / 'saved-package')
        package.symlink_to('saved-package', target_is_directory=True)
    elif layout == 'package-file':
        shutil.copyfile(package / '__init__.py', execution / 'saved-init.py')
        _replace_with_link(package / '__init__.py', execution / 'saved-init.py')
    elif layout == 'ancestor':
        alias = tmp_path.resolve() / 'execution-alias'
        alias.symlink_to(execution, target_is_directory=True)
        pythonpath = alias
    elif layout == 'module-file':
        target = execution / 'saved-baselines.py'
        shutil.copyfile(package / 'forecasting/baselines.py', target)
        _replace_with_link(package / 'forecasting/baselines.py', target)
    elif layout == 'module-directory':
        (package / 'forecasting').rename(execution / 'saved-forecasting')
        (package / 'forecasting').symlink_to('../saved-forecasting', target_is_directory=True)
    run = _cli(root, path, tmp_path.resolve(), pythonpath, layout)
    if layout == 'ordinary':
        assert run.returncode == 0, run.stderr
        assert (root / f'results/experiments/{layout}/result.json').is_file()
    else:
        assert run.returncode == 2, run.stderr
        assert 'P1 execution refused:' in run.stderr
        assert not (root / f'results/experiments/{layout}').exists()


@pytest.mark.parametrize('replacement', ['file', 'directory'])
def test_runner_final_parity_recheck_refuses_same_byte_execution_package_redirection(
        tmp_path, replacement):
    root, path = _repository(tmp_path)
    execution = tmp_path.resolve() / 'execution'
    shutil.copytree(root / 'src', execution)
    commit = _git(root, 'rev-parse', 'HEAD')
    program = """
from pathlib import Path
import os, sys
from solar_flare_jepa.experiments import runner
original = runner._dataset
execution = Path(sys.argv[3])
def replace_after_initial_provenance(config, root):
    dataset = original(config, root)
    source = execution / 'solar_flare_jepa/forecasting'
    if sys.argv[4] == 'file':
        source = source / 'baselines.py'
        target = execution / 'saved-baselines.py'
        source.rename(target)
        source.symlink_to(os.path.relpath(target, source.parent))
    else:
        target = execution / 'saved-forecasting'
        source.rename(target)
        source.symlink_to(os.path.relpath(target, source.parent), target_is_directory=True)
    return dataset
runner._dataset = replace_after_initial_provenance
try:
    runner.run_experiment(sys.argv[1], sys.argv[2],
                          output_dir='results/experiments/final-parity')
except (ValueError, OSError) as error:
    print('Final source recheck refused: ' + str(error), file=sys.stderr)
    raise SystemExit(2)
"""
    env = os.environ.copy()
    env['PYTHONPATH'] = str(execution)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    run = subprocess.run([sys.executable, '-B', '-c', program, str(path), str(root),
                          str(execution), replacement], cwd=tmp_path.resolve(), env=env,
                         capture_output=True, text=True, timeout=45)
    assert _git(root, 'rev-parse', 'HEAD') == commit
    assert _git(root, 'status', '--porcelain=v1', '--untracked-files=all') == ''
    redirected = execution / 'solar_flare_jepa/forecasting'
    if replacement == 'file':
        redirected = redirected / 'baselines.py'
    assert redirected.is_symlink(), 'Initial provenance must admit the ordinary package control'
    assert run.returncode == 2, run.stderr
    assert 'Final source recheck refused:' in run.stderr
    assert not (root / 'results/experiments/final-parity').exists()


def test_fresh_normal_cli_refuses_old_ignored_forecasting_directory_exploit(tmp_path):
    root, path = _repository(tmp_path)
    (root / 'aux').mkdir()
    (root / '.gitignore').write_text((root / '.gitignore').read_text() + '\n/aux/\n')
    source = root / 'src/solar_flare_jepa/forecasting'
    source.rename(root / 'aux/forecasting')
    source.symlink_to('../../aux/forecasting', target_is_directory=True)
    _commit(root)
    commit = _git(root, 'rev-parse', 'HEAD')
    assert _git(root, 'status', '--porcelain=v1', '--untracked-files=all') == ''
    records = []
    for index in (0, 1):
        if index:
            baseline = root / 'aux/forecasting/baselines.py'
            before = baseline.read_text()
            after = before.replace("_finite(np.array(means), 'training mean')",
                                   "_finite(np.array(means)+1., 'training mean')")
            assert after != before
            baseline.write_text(after)
        run = _cli(root, path, tmp_path.resolve(), root / 'src', f'exploit-{index}')
        records.append(dict(returncode=run.returncode, stderr=run.stderr))
        assert _git(root, 'rev-parse', 'HEAD') == commit
        assert _git(root, 'status', '--porcelain=v1', '--untracked-files=all') == ''
    assert [item['returncode'] for item in records] == [2, 2], records
    assert all('P1 execution refused:' in item['stderr'] for item in records)
    assert not list((root / 'results/experiments').glob('*/result.json'))
