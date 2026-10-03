"""Portable identities, actual code provenance, and no-replacement publication."""
import ctypes
import errno
import importlib
from importlib.metadata import distribution, version, PackageNotFoundError
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import platform
import re
import shutil
import subprocess
import sys
import tempfile

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.data.storage import repository_relative_path
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .config import read_finite_json


def dataset_fingerprint(dataset):
    return dataset.fingerprint


def split_fingerprint(manifest):
    return fingerprint_payload(manifest)


def _relative(value):
    if not isinstance(value,str) or '\\' in value or ':' in value or PureWindowsPath(value).drive:
        raise ValueError('Artifact/source identifiers must be portable relative paths')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or not path.parts or str(path) != value:
        raise ValueError('Unsafe relative path')
    return path


def verify_source_identities(root, identities):
    root = Path(root).resolve()
    for item in identities:
        path = root / str(_relative(item['path']))
        repository_relative_path(path,root)
        if (not path.is_file() or path.stat().st_size != item['bytes']
                or sha256_file(path) != item['sha256']):
            raise ValueError(f'Source identity mismatch: {item["path"]}')


def source_fingerprint(root, paths=None):
    root = Path(root).resolve()
    if paths is None:
        paths = [p.relative_to(root).as_posix() for base in ('src','scripts') for p in (root/base).rglob('*.py')]
        paths += [p.relative_to(root).as_posix() for p in (root/'configs'/'experiments').glob('p1_*.json')]
        paths += ['pyproject.toml','requirements-lock.txt','schemas/experiment_result.schema.json']
    files = []
    for identifier in sorted(set(paths)):
        path = root/str(_relative(identifier))
        repository_relative_path(path,root)
        if not path.is_file():
            raise ValueError(f'Missing reproducibility source: {identifier}')
        files.append(dict(path=identifier,bytes=path.stat().st_size,sha256=sha256_file(path)))
    return dict(files=files,fingerprint=fingerprint_payload(files))


def code_provenance(root, *, require_clean=True, require_installed_match=True):
    root = Path(root).resolve()
    def git(*args):
        result = subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,check=True)
        return result.stdout.strip()
    if Path(git('rev-parse','--show-toplevel')).resolve() != root:
        raise ValueError('Experiment root must be the actual Git worktree root')
    status = git('status','--porcelain=v1','--untracked-files=all').splitlines()
    tracked_dirty = bool(git('status','--porcelain=v1','--untracked-files=no'))
    untracked = [line[3:] for line in status if line.startswith('?? ')]
    if require_clean and (tracked_dirty or any(x.startswith(('src/','scripts/','configs/','schemas/')) for x in untracked)):
        raise ValueError('Reproducible execution requires clean tracked source and tracked P1 inputs')
    source = source_fingerprint(root)
    imported = []
    package = importlib.import_module('solar_flare_jepa')
    package_root = Path(package.__file__).resolve().parent
    try:
        installed_root = Path(distribution('solar-flare-jepa').locate_file('solar_flare_jepa')).resolve()
    except PackageNotFoundError:
        installed_root = None
    for item in source['files']:
        if item['path'].startswith('src/solar_flare_jepa/') and item['path'].endswith('.py'):
            relative = item['path'][4:-3].replace('/','.')
            name = relative[:-9] if relative.endswith('.__init__') else relative
            # Inspect unused module files without executing optional scientific
            # readers. Already loaded modules must match their actual location.
            module = sys.modules.get(name)
            actual = (Path(module.__file__).resolve() if module is not None else
                      package_root/item['path'].removeprefix('src/solar_flare_jepa/'))
            if not actual.is_file():
                raise ValueError(f'Execution-package source identity mismatch: missing {name}')
            digest = sha256_file(actual)
            matches = digest == item['sha256']
            if require_installed_match and not matches:
                raise ValueError(f'Imported/checkout source identity mismatch: {name}')
            location = ('checkout' if actual.is_relative_to(root/'src'/'solar_flare_jepa') else
                        'installed_distribution' if installed_root is not None
                        and actual.is_relative_to(installed_root) else 'external_matching_source')
            imported.append(dict(module=name,sha256=digest,checkout_match=matches,location=location,
                inspection='loaded_module_file' if module is not None else 'package_file_not_imported'))
    packages = {}
    for name in ('solar-flare-jepa','numpy','pandas','xarray','netCDF4','pyarrow'):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return dict(git_commit=git('rev-parse','HEAD'),git_branch=git('branch','--show-current'),
                tracked_dirty=tracked_dirty,untracked_configuration_paths=untracked,
                source=source,imported_source=imported,packages=packages,
                python=sys.version,platform=platform.platform())


def _destination(root, destination):
    root = Path(root).resolve()
    destination = Path(destination)
    if not destination.is_absolute():
        destination = root/destination
    safe_parent = root/'results'/'experiments'
    logical = destination.relative_to(root) if destination.is_relative_to(root) else None
    if (logical is None or logical.parts[:2] != ('results','experiments')
            or len(logical.parts) != 3 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',logical.name)):
        raise ValueError('Output must be a single execution directory beneath results/experiments')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(str(destination))
    if safe_parent.resolve() != safe_parent or destination.resolve().parent != safe_parent:
        raise ValueError('Output parent must not redirect through symlinks')
    return destination


def _rename_no_replace(source, destination):
    """OS-level exclusive directory rename, including external/concurrent writers."""
    if os.name == 'nt':
        os.rename(source,destination)  # Windows refuses an existing destination.
        return
    libc = ctypes.CDLL(None,use_errno=True)
    if sys.platform == 'darwin':
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p,ctypes.c_char_p,ctypes.c_uint]
        result = rename(os.fsencode(source),os.fsencode(destination),4)  # RENAME_EXCL
    elif sys.platform.startswith('linux') and hasattr(libc,'renameat2'):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
        result = rename(-100,os.fsencode(source),-100,os.fsencode(destination),1)  # RENAME_NOREPLACE
    else:
        raise OSError('Atomic no-replacement publication is unsupported on this platform')
    if result:
        error = ctypes.get_errno()
        if error in (errno.EEXIST,errno.ENOTEMPTY):
            raise FileExistsError(error,os.strerror(error),str(destination))
        raise OSError(error,os.strerror(error),str(destination))


def verify_artifacts(directory):
    directory = Path(directory)
    manifest = read_finite_json(directory/'artifacts.json')
    if not isinstance(manifest,dict) or set(manifest) != {'schema_version','files'} or manifest['schema_version'] != 1:
        raise ValueError('Invalid artifact identity manifest')
    expected = []
    for item in manifest['files']:
        if set(item) != {'path','bytes','sha256'}:
            raise ValueError('Invalid artifact identity entry')
        identifier = str(_relative(item['path']))
        path = directory/identifier
        if (path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(directory.resolve())
                or path.stat().st_size != item['bytes'] or sha256_file(path) != item['sha256']):
            raise ValueError(f'Artifact identity mismatch: {identifier}')
        expected.append(identifier)
    actual = sorted(p.relative_to(directory).as_posix() for p in directory.rglob('*')
                    if p.is_file() and p.relative_to(directory).as_posix() != 'artifacts.json')
    if sorted(expected) != actual or len(set(expected)) != len(expected):
        raise ValueError('Artifact identity file set mismatch')
    return manifest


def atomic_record(root, destination, contents):
    destination = _destination(root,destination)
    if not isinstance(contents,dict) or not contents:
        raise ValueError('A nonempty artifact mapping is required')
    identifiers = [str(_relative(name)) for name in contents]
    if 'artifacts.json' in identifiers or any(not x.endswith('.json') for x in identifiers):
        raise ValueError('Artifact index is reserved; P1 stores finite JSON artifacts only')
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.stage-',dir=destination.parent))
    try:
        files = []
        for identifier in sorted(identifiers):
            path = stage/identifier
            path.parent.mkdir(parents=True,exist_ok=True)
            encoded = (canonical_json(contents[identifier])+'\n').encode('utf-8')
            with path.open('xb') as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            files.append(dict(path=identifier,bytes=len(encoded),sha256=sha256_file(path)))
        manifest = dict(schema_version=1,files=files)
        with (stage/'artifacts.json').open('xb') as stream:
            stream.write((canonical_json(manifest)+'\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        verify_artifacts(stage)
        _rename_no_replace(stage,destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return destination
