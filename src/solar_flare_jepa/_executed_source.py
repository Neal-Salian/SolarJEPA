"""Bind project imports to captured source, rather than timestamp bytecode caches.

This supports reproducible experiments in ordinary Python interpreters, including
long-lived API sessions. It is not protection against interpreter monkeypatching.
Changing project source after import requires a fresh interpreter for experiments.
"""
import hashlib
import importlib.abc
import importlib.machinery
from pathlib import Path
import sys
from types import CodeType, ModuleType


# Preserve history across reload: old from-import references may still execute.
if '_captures' not in globals():
    _captures = {}
    _changed = set()
    _codes = {}
    _loaders = {}
    _audit_ready = False


def _code_content(code):
    """Compare bootstrap code without equality collisions between scalar types."""
    def constant(value):
        if isinstance(value, CodeType):
            return ('code', _code_content(value))
        if isinstance(value, tuple):
            return ('tuple', tuple(constant(x) for x in value))
        if isinstance(value, frozenset):
            return ('frozenset', tuple(sorted(constant(x) for x in value)))
        return (type(value).__name__, repr(value))
    return tuple(getattr(code, name) for name in (
        'co_argcount', 'co_posonlyargcount', 'co_kwonlyargcount', 'co_nlocals',
        'co_stacksize', 'co_flags', 'co_code', 'co_names', 'co_varnames',
        'co_freevars', 'co_cellvars', 'co_firstlineno', 'co_linetable',
        'co_exceptiontable')) + (tuple(constant(x) for x in code.co_consts),)


def _capture(name, filename, source, code, loader):
    identity = dict(path=str(Path(filename).absolute()),
                    sha256=hashlib.sha256(source).hexdigest())
    if name in _captures and _captures[name] != identity:
        _changed.add(name)
    _captures.setdefault(name, identity)
    _codes.setdefault(name, _code_content(code))
    _loaders[name] = loader


def _bootstrap_capture(name, filename, executing_code):
    source = Path(filename).read_bytes()
    expected = compile(source, filename, 'exec', dont_inherit=True, optimize=sys.flags.optimize)
    if _code_content(executing_code) != _code_content(expected):
        _changed.add(name)
    _capture(name, filename, source, executing_code, sys.modules[name].__loader__)


def _execution_audit(event, arguments):
    global _audit_ready
    if event == 'solar_flare_jepa.source_capture_ready':
        _audit_ready = True
        return
    if event != 'exec' or not isinstance(arguments[0], CodeType):
        return
    code = arguments[0]
    if code.co_name != '<module>':
        return
    filename = str(Path(code.co_filename).absolute())
    for name, identity in _captures.copy().items():
        if identity['path'] == filename and _code_content(code) != _codes[name]:
            _changed.add(name)
    # Standard importlib permits exec_module(existing_module), preserving the
    # existing module's loader metadata. Observe the loader that actually executes
    # its namespace; metadata alone cannot establish ownership of execution.
    frame = sys._getframe(1)
    # Follow only importlib's execution trampoline. Searching arbitrary ancestor
    # frames would misclassify dataclasses' generated <string> code as a second
    # execution of the enclosing project module during its ordinary import.
    while frame is not None and frame.f_code.co_name == '_call_with_frames_removed':
        frame = frame.f_back
    module = (frame.f_locals.get('module') if frame is not None
              and frame.f_code.co_name == 'exec_module' else None)
    if (isinstance(module, ModuleType)
            and (module.__name__ == 'solar_flare_jepa'
                 or module.__name__.startswith('solar_flare_jepa.'))):
        name = module.__name__
        if (name not in _captures or frame.f_locals.get('self') is not _loaders.get(name)
                or filename != _captures[name]['path']):
            _changed.add(name)


class _CapturedSourceLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        filename = self.get_filename(fullname)
        source = self.get_data(filename)
        code = compile(source, filename, 'exec', dont_inherit=True, optimize=sys.flags.optimize)
        _capture(fullname, filename, source, code, self)
        return code


class _ProjectSourceFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith('solar_flare_jepa.'):
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is not None and isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            spec.loader = _CapturedSourceLoader(fullname, spec.origin)
        return spec


def install(package_name, filename, executing_code):
    _bootstrap_capture(package_name, filename, executing_code)
    # A standard loader can start a project module before importing its parent
    # package. Bootstrap then runs in the middle of that unobserved execution.
    # Preserve both cached modules and active uncached loader frames rather than
    # letting their retained functions disappear before a later normal import.
    for name in sys.modules.copy():
        if (name == 'solar_flare_jepa' or name.startswith('solar_flare_jepa.')) and name not in _captures:
            _changed.add(name)
    frame = sys._getframe(1)
    while frame is not None:
        module = frame.f_locals.get('module') if frame.f_code.co_name == 'exec_module' else None
        if (isinstance(module, ModuleType)
                and (module.__name__ == 'solar_flare_jepa'
                     or module.__name__.startswith('solar_flare_jepa.'))
                and module.__name__ not in _captures):
            _changed.add(module.__name__)
        frame = frame.f_back
    if not any(isinstance(finder, _ProjectSourceFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, _ProjectSourceFinder())


def verify_loaded_source(name, filename, digest):
    identity = dict(path=str(Path(filename).absolute()), sha256=digest)
    module = sys.modules.get(name)
    if (not _audit_ready or name in _changed or _captures.get(name) != identity
            or module is None or module.__loader__ is not _loaders.get(name)):
        raise ValueError(f'Executed/recorded project source mismatch: {name}; use a fresh interpreter')
    return digest


def captured_source_names():
    """Include evicted modules: retained from-import references can still run."""
    return tuple(sorted(set(_captures) | _changed))


# These two bootstrap modules precede the finder. Compare their executing module
# code to source too, so a stale bootstrap cache cannot attest today's bytes.
_bootstrap_capture(__name__, __file__, sys._getframe().f_code)
if not _audit_ready:
    sys.addaudithook(_execution_audit)
    sys.audit('solar_flare_jepa.source_capture_ready')
