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
from types import CodeType


# Preserve history across reload: old from-import references may still execute.
if '_captures' not in globals():
    _captures = {}
    _changed = set()


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


def _capture(name, filename, source, code):
    identity = dict(path=str(Path(filename).absolute()),
                    sha256=hashlib.sha256(source).hexdigest())
    if name in _captures and _captures[name] != identity:
        _changed.add(name)
    _captures.setdefault(name, identity)


def _bootstrap_capture(name, filename, executing_code):
    source = Path(filename).read_bytes()
    expected = compile(source, filename, 'exec', dont_inherit=True, optimize=sys.flags.optimize)
    if _code_content(executing_code) != _code_content(expected):
        _changed.add(name)
    _capture(name, filename, source, executing_code)


class _CapturedSourceLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        filename = self.get_filename(fullname)
        source = self.get_data(filename)
        code = compile(source, filename, 'exec', dont_inherit=True, optimize=sys.flags.optimize)
        _capture(fullname, filename, source, code)
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
    if not any(isinstance(finder, _ProjectSourceFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, _ProjectSourceFinder())


def verify_loaded_source(name, filename, digest):
    identity = dict(path=str(Path(filename).absolute()), sha256=digest)
    if name in _changed or _captures.get(name) != identity:
        raise ValueError(f'Executed/recorded project source mismatch: {name}; use a fresh interpreter')
    return digest


# These two bootstrap modules precede the finder. Compare their executing module
# code to source too, so a stale bootstrap cache cannot attest today's bytes.
_bootstrap_capture(__name__, __file__, sys._getframe().f_code)
