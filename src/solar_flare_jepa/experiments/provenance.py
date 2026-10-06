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
import stat
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


def _source_path(value):
    """Check lexical components before resolving; source redirection is refused."""
    path = Path(value).absolute()
    prefix = Path(path.anchor)
    for component in path.parts[1:]:
        prefix = prefix / component
        if prefix.is_symlink():
            raise ValueError(f'Reproducibility source must not redirect through symlinks: {prefix}')
    return path.resolve()


def _source_files(directory):
    directory = _source_path(directory)
    def failed(error):
        raise ValueError(f'Cannot inspect reproducibility source: {error}') from error
    for parent, directories, files in os.walk(directory, followlinks=False, onerror=failed):
        # Directory links (including dangling/loop links) must be inspected even
        # though an ordinary Python glob would omit their executable contents.
        for name in directories + files:
            _source_path(Path(parent) / name)
        for name in files:
            yield Path(parent) / name


def _source_identity(path):
    path = _source_path(path)
    try:
        before = path.stat()
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f'Reproducibility source must be a regular file: {path}')
        digest = sha256_file(path)
        _source_path(path)
        after = path.stat()
    except OSError as error:
        raise ValueError(f'Cannot hash reproducibility source: {path}') from error
    attributes = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    if any(getattr(before, name) != getattr(after, name) for name in attributes):
        raise ValueError(f'Reproducibility source changed during hashing: {path}')
    return dict(bytes=after.st_size, sha256=digest)


def verify_source_identities(root, identities):
    root = _source_path(root)
    for item in identities:
        path = root / str(_relative(item['path']))
        repository_relative_path(path,root)
        if _source_identity(path) != {key: item[key] for key in ('bytes', 'sha256')}:
            raise ValueError(f'Source identity mismatch: {item["path"]}')


def source_fingerprint(root, paths=None):
    root = _source_path(root)
    if paths is None:
        paths = [p.relative_to(root).as_posix() for base in ('src','scripts')
                 for p in _source_files(root/base) if p.suffix == '.py']
        paths += [p.relative_to(root).as_posix() for p in _source_files(root/'configs'/'experiments')
                  if p.parent == root/'configs'/'experiments' and p.match('p1_*.json')]
        # Check the schema tree too, although only the P1 result schema is hashed.
        list(_source_files(root/'schemas'))
        paths += ['pyproject.toml','requirements-lock.txt','schemas/experiment_result.schema.json']
    files = []
    for identifier in sorted(set(paths)):
        path = root/str(_relative(identifier))
        repository_relative_path(path,root)
        if not path.is_file():
            raise ValueError(f'Missing reproducibility source: {identifier}')
        files.append(dict(path=identifier,**_source_identity(path)))
    return dict(files=files,fingerprint=fingerprint_payload(files))


def code_provenance(root, *, require_clean=True, require_installed_match=True):
    root = _source_path(root)
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
    package_root = _source_path(package.__file__).parent
    list(_source_files(package_root))
    try:
        installed_root = Path(distribution('solar-flare-jepa').locate_file('solar_flare_jepa')).resolve()
    except PackageNotFoundError:
        installed_root = None
    recorded_modules = set()
    for item in source['files']:
        if item['path'].startswith('src/solar_flare_jepa/') and item['path'].endswith('.py'):
            relative = item['path'][4:-3].replace('/','.')
            name = relative[:-9] if relative.endswith('.__init__') else relative
            recorded_modules.add(name)
            # Inspect unused module files without executing optional scientific
            # readers. Already loaded modules must match their actual location.
            module = sys.modules.get(name)
            actual = (_source_path(module.__file__) if module is not None else
                      package_root/item['path'].removeprefix('src/solar_flare_jepa/'))
            if not actual.is_file():
                raise ValueError(f'Execution-package source identity mismatch: missing {name}')
            digest = _source_identity(actual)['sha256']
            matches = digest == item['sha256']
            if require_installed_match and not matches:
                raise ValueError(f'Imported/checkout source identity mismatch: {name}')
            location = ('checkout' if actual.is_relative_to(root/'src'/'solar_flare_jepa') else
                        'installed_distribution' if installed_root is not None
                        and actual.is_relative_to(installed_root) else 'external_matching_source')
            imported.append(dict(module=name,sha256=digest,checkout_match=matches,location=location,
                inspection='loaded_module_file' if module is not None else 'package_file_not_imported'))
    unexpected = {name for name, module in sys.modules.copy().items() if module is not None
                  and (name == 'solar_flare_jepa' or name.startswith('solar_flare_jepa.'))} - recorded_modules
    if unexpected:
        raise ValueError(f'Loaded project modules are absent from source inventory: {sorted(unexpected)}')
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
