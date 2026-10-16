"""Numerical native SoLEXS diagnostics; no mission quality or exposure policy.

Missingness, anomalous values, coordinate continuity and GTI point membership
are separate observations. None supplies scientific validity or a filter.
"""
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from .solexs import NativeColumns, _compare, _difference


def frozen_array(values):
    """Own detached immutable bytes, retaining native dtype, shape and endian."""
    values = np.asarray(values)
    if values.dtype.kind not in 'biuf':
        raise ValueError('Expected fixed numeric native arrays')
    return np.frombuffer(values.tobytes(), dtype=values.dtype).reshape(values.shape)


def _numeric(values, dimensions, name):
    values = np.asarray(values)
    if values.dtype.kind not in 'iuf' or values.ndim != dimensions:
        raise ValueError(f'Invalid native {name} dimensions or dtype')
    return values


def _coordinates(native):
    if not isinstance(native, NativeColumns) or native.provenance.get('kind') not in ('lc', 'pi'):
        raise ValueError('Expected native LC or PI values')
    name = 'TIME' if native.provenance['kind'] == 'lc' else 'TSTART'
    if name not in native.columns:
        raise ValueError('Missing native time coordinate')
    return _numeric(native.columns[name], 1, name)


@dataclass(frozen=True)
class NumericalQuality:
    entry_finite: np.ndarray
    entry_nan: np.ndarray
    entry_positive_infinity: np.ndarray
    entry_negative_infinity: np.ndarray
    rows: object

    def summary(self):
        return dict(evidence='OBSERVED', scientific_quality='UNKNOWN_NOT_APPLIED',
                    filter_applied=False, rows=len(self.rows['finite_coordinate']),
                    counts=dict(values=self.entry_finite.size,
                                finite=int(self.entry_finite.sum()), nan=int(self.entry_nan.sum()),
                                positive_infinity=int(self.entry_positive_infinity.sum()),
                                negative_infinity=int(self.entry_negative_infinity.sum())),
                    row_flags={name: int(mask.sum()) for name, mask in self.rows.items()},
                    continuity='Exact requested step in native numeric coordinates; no time unit implied')


def validate_native_step(expected_step):
    """Validate the numerical continuity request even for an empty product."""
    if (isinstance(expected_step, (bool, np.bool_))
            or not isinstance(expected_step, (int, float, np.integer, np.floating))
            or not np.isfinite(expected_step) or expected_step <= 0):
        raise ValueError('Expected a positive finite numerical coordinate step')


def numerical_quality(native, *, expected_step, previous_coordinate=None):
    """Derive masks from values; never accept an externally supplied valid mask.

    `expected_step` is a numerical continuity criterion, not seconds or an
    instrument cadence. A first row starts a run unless a preceding coordinate
    is explicitly supplied by the same-product streaming interface.
    """
    validate_native_step(expected_step)
    time = _coordinates(native)
    if 'COUNTS' not in native.columns:
        raise ValueError('Missing native COUNTS')
    counts = _numeric(native.columns['COUNTS'], 1 if native.provenance['kind'] == 'lc' else 2, 'COUNTS')
    if len(counts) != len(time) or counts.ndim == 2 and counts.shape[1] == 0:
        raise ValueError('Native row counts/vector width differ')
    finite = np.isfinite(counts)
    entries = counts.reshape(len(time), -1) if len(time) else counts.reshape(0, 1 if counts.ndim == 1 else counts.shape[1])
    finite_rows = finite.reshape(entries.shape)
    breaks = np.ones(len(time), dtype=bool)
    with np.errstate(over='ignore', invalid='ignore'):
        if len(time) > 1:
            breaks[1:] = ~(np.isfinite(time[1:]) & np.isfinite(time[:-1])
                           & (_difference(time[1:], time[:-1]) == expected_step))
        if len(time) and previous_coordinate is not None:
            previous = _numeric(np.asarray([previous_coordinate]), 1, 'previous coordinate')
            breaks[0] = not bool(np.isfinite(time[0]) and np.isfinite(previous[0])
                                 and (_difference(time[:1], previous) == expected_step)[0])
    rows = dict(finite_coordinate=np.isfinite(time), break_before=breaks,
                all_counts_finite=finite_rows.all(axis=1), any_count_finite=finite_rows.any(axis=1),
                any_negative=(finite_rows & (entries < 0)).any(axis=1),
                any_zero=(finite_rows & (entries == 0)).any(axis=1))
    # Integer arrays must not be cast to float for the diagnostic.
    noninteger = np.zeros(entries.shape, dtype=bool)
    if counts.dtype.kind == 'f':
        noninteger[finite_rows] = entries[finite_rows] != np.floor(entries[finite_rows])
    rows['any_noninteger'] = noninteger.any(axis=1)
    if native.provenance['kind'] == 'pi':
        for name in ('EXPOSURE', 'TELAPSE'):
            if name not in native.columns:
                raise ValueError(f'Missing native {name}')
            values = _numeric(native.columns[name], 1, name)
            if len(values) != len(time):
                raise ValueError('Exposure/elapsed row counts differ')
            rows['positive_finite_' + name.lower()] = np.isfinite(values) & (values > 0)
    return NumericalQuality(*(frozen_array(a) for a in
        (finite, np.isnan(counts), np.isposinf(counts), np.isneginf(counts))),
        MappingProxyType({name: frozen_array(a) for name, a in rows.items()}))


@dataclass(frozen=True)
class GTIDiagnostics:
    closed: np.ndarray
    half_open: np.ndarray

    def summary(self):
        return dict(evidence='OBSERVED', comparison='Native numeric point-membership hypotheses only',
                    closed_points=int(self.closed.sum()), half_open_points=int(self.half_open.sum()),
                    endpoint_disagreements=int((self.closed != self.half_open).sum()),
                    clock_compatibility='UNKNOWN', endpoint_policy='UNKNOWN_NOT_APPLIED',
                    continuous_exposure=None, filter_applied=False)


def require_same_source(science_provenance, gti_provenance):
    """Compare the source/detector labels without erasing association evidence."""
    for key in ('archive', 'archive_sha256'):
        if not science_provenance.get(key) or science_provenance[key] != gti_provenance.get(key):
            raise ValueError('GTI source/detector differs from science product')
    detector = science_provenance.get('detector', {}).get('value')
    if detector not in ('SDD1', 'SDD2') or detector != gti_provenance.get('detector', {}).get('value'):
        raise ValueError('GTI detector differs from science product')


def gti_diagnostics(native, gti):
    """Compare [START,STOP] and [START,STOP), without applying either policy.

    Source and detector agreement is necessary for this numerical diagnostic;
    it does not establish the absent GTI clock/unit/exposure contract.
    """
    time = _coordinates(native)
    if not isinstance(gti, NativeColumns) or gti.provenance.get('kind') != 'gti':
        raise ValueError('Expected a native GTI product')
    require_same_source(native.provenance, gti.provenance)
    if not {'START', 'STOP'} <= set(gti.columns):
        raise ValueError('Missing GTI endpoints')
    start, stop = [_numeric(gti.columns[key], 1, key) for key in ('START', 'STOP')]
    if (len(start) != len(stop) or len(start) > 4096
            or not (np.isfinite(start).all() and np.isfinite(stop).all())
            or not _compare(np.greater_equal, stop, start).all()
            or not _compare(np.greater_equal, start[1:], stop[:-1]).all()):
        raise ValueError('Invalid, overlapping, unordered or excessive GTI intervals; no repair applied')
    closed, half_open = np.zeros(len(time), dtype=bool), np.zeros(len(time), dtype=bool)
    for a, b in zip(start, stop):
        lower = np.isfinite(time) & _compare(np.greater_equal, time, a)
        closed |= lower & _compare(np.less_equal, time, b)
        half_open |= lower & _compare(np.less, time, b)
    return GTIDiagnostics(frozen_array(closed), frozen_array(half_open))
