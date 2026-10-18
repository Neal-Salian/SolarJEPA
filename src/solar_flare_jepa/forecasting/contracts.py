"""Immutable interval contracts. Nanoseconds are coordinates, never inferred clocks.

Intervals are half-open. Values are in declared native units; transforms are
fixed, dimensioned operations applied by a forecaster, never fitted here.
"""
from dataclasses import asdict, dataclass, fields
import hashlib
import json

import numpy as np


def canonical_json(value) -> str:
    """Finite, order-independent JSON used by semantic identities and records."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False)


def fingerprint_payload(value) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def _canonical_strings(value):
    """Detach ordered/container declarations using base string/container content.

    Preserve numerical and collection types for their existing strict validators.
    No arbitrary object's equality, string conversion or deepcopy hook supplies
    categorical semantics. Nested contracts/arrays have their own constructors.
    """
    if isinstance(value, str):
        return str.__str__(value)
    if isinstance(value, tuple):
        return tuple(_canonical_strings(part) for part in tuple.__iter__(value))
    if isinstance(value, list):
        return [_canonical_strings(part) for part in list.__iter__(value)]
    if isinstance(value, dict):
        result = {}
        for key, part in dict.items(value):
            if not isinstance(key, str):
                raise ValueError('Canonical mapping keys require explicit strings')
            key = str.__str__(key)
            if key in result:
                raise ValueError('Duplicate canonical mapping keys')
            result[key] = _canonical_strings(part)
        return result
    return value


def _canonical_fields(value, contract):
    """Read base declarations; constructors validate every captured field."""
    return {field.name: _canonical_strings(getattr(value, field.name)) for field in fields(contract)}


def _string(value, label):
    """Accept genuine string representations, retaining only primitive content."""
    if not isinstance(value, str):
        raise ValueError(f'{label} requires an explicit string')
    value = str.__str__(value)
    if not value:
        raise ValueError(f'{label} requires a nonempty string')
    return value


def _category(value, choices, label):
    value = _string(value, label)
    if value not in choices:
        raise ValueError(f'Unsupported {label}')
    return value


def logical_array(value):
    """JSON content with explicit nulls for masked NaNs, never nonfinite JSON."""
    array = np.asarray(value)
    if array.dtype.kind == 'f':
        if np.isinf(array).any():
            raise ValueError('Infinite logical array content')
        return np.where(np.isnan(array), None, array).tolist()
    return array.tolist()


def _immutable(value, dtype, *, ndim=None):
    array = np.asarray(value, dtype=dtype)
    if ndim is not None and array.ndim != ndim:
        raise ValueError(f'Expected {ndim} dimensions, received {array.shape}')
    # A bytes owner prevents callers from re-enabling writes with setflags.
    return np.frombuffer(array.tobytes(order='C'), dtype=array.dtype).reshape(array.shape)


def _times(value, *, ndim):
    raw = np.asarray(value)
    if raw.dtype.kind not in 'iu' or raw.dtype.kind == 'b':
        raise ValueError('Time coordinates must be integer nanoseconds')
    if raw.size and (int(raw.min()) < np.iinfo(np.int64).min
                     or int(raw.max()) > np.iinfo(np.int64).max):
        raise ValueError('Time coordinate outside int64 range')
    return _immutable(raw, np.int64, ndim=ndim)


def _values_mask(values, mask, shape):
    values = _immutable(values, np.float64)
    mask = np.asarray(mask)
    if mask.dtype.kind != 'b':
        raise ValueError('Masks must be boolean')
    mask = _immutable(mask, bool)
    if values.shape != shape or mask.shape != shape:
        raise ValueError(f'Values/mask must have shape {shape}')
    if np.isinf(values).any() or not np.isfinite(values[mask]).all():
        raise ValueError('Valid values must be finite; masked NaNs are allowed')
    return values, mask


def _names(value, *, unique=True):
    if not isinstance(value, (list, tuple)):
        raise ValueError('Names/units require an explicit ordered list or tuple')
    values = tuple(_string(x, 'Names/units') for x in value)
    if not values or any(not x.strip() for x in values):
        raise ValueError('Names/units must be nonempty strings')
    if unique and len(set(values)) != len(values):
        raise ValueError('Names must be unique')
    return values


def _integer(value, *, positive=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError('Sample lengths and bounds must be integers')
    value = int.__int__(value) if isinstance(value, int) else int(value)
    if value < (1 if positive else 0):
        raise ValueError('Invalid sample length')
    return value


def _time_scalar(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError('Time bounds must be integer nanoseconds')
    value = int(value)
    if not np.iinfo(np.int64).min <= value <= np.iinfo(np.int64).max:
        raise ValueError('Time bound outside int64 range')
    return value


def _number(value):
    array = np.asarray(value)
    if array.ndim != 0 or array.dtype.kind not in 'fiu':
        raise ValueError('Numeric metadata must contain genuine scalars')
    value = float(array)
    if not np.isfinite(value):
        raise ValueError('Numeric metadata must be finite')
    return value


def _coordinate_grid(issues, offsets):
    # Python integer arithmetic cannot wrap a future interval into the past.
    offsets = tuple(offsets)
    rows = [[_time_scalar(int(issue) + int(offset)) for offset in offsets] for issue in issues]
    return np.asarray(rows, dtype=np.int64).reshape(len(issues), len(offsets))


def _shift_times(times, offset):
    return _coordinate_grid(times.reshape(-1), (offset,)).reshape(times.shape)


def _identity(value):
    return _string(value, 'Identity')


@dataclass(frozen=True)
class ForecastSpec:
    cadence_seconds: int
    context_steps: int
    horizon_steps: int
    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]
    feature_units: tuple[str, ...]
    target_units: tuple[str, ...]
    stride_steps: int = 1
    feature_lookback_steps: int = 0
    label_maturity_steps: int = 0
    availability_mode: str = 'operational'
    eligibility_policy: str = 'complete'
    transform: str = 'identity'
    feature_reference: tuple[float, ...] = ()
    target_reference: tuple[float, ...] = ()
    target_minimum: tuple[float | None, ...] = ()

    def __post_init__(self):
        for name, choices, label in (
                ('availability_mode', ('operational', 'retrospective_bin_end'), 'availability mode'),
                ('eligibility_policy', ('complete', 'masked'), 'eligibility policy'),
                ('transform', ('identity', 'log10'), 'transform')):
            object.__setattr__(self, name, _category(getattr(self, name), choices, label))
        for name in ('cadence_seconds', 'context_steps', 'horizon_steps', 'stride_steps'):
            object.__setattr__(self, name, _integer(getattr(self, name), positive=True))
        for name in ('feature_lookback_steps', 'label_maturity_steps'):
            object.__setattr__(self, name, _integer(getattr(self, name)))
        for steps in (1, self.context_steps + self.feature_lookback_steps,
                      self.horizon_steps + self.label_maturity_steps):
            _time_scalar(steps * self.cadence_ns)
        for name in ('feature_names', 'target_names', 'feature_units', 'target_units'):
            object.__setattr__(self, name, _names(getattr(self, name), unique=name.endswith('names')))
        if (len(self.feature_names) != len(self.feature_units)
                or len(self.target_names) != len(self.target_units)):
            raise ValueError('Name/unit lengths differ')
        for name, count in [('feature_reference', len(self.feature_names)),
                            ('target_reference', len(self.target_names))]:
            if not isinstance(getattr(self, name), (list, tuple)):
                raise ValueError('Reference scales require an explicit ordered list or tuple')
            refs = tuple(_number(x) for x in getattr(self, name))
            if self.transform == 'log10' and len(refs) != count:
                raise ValueError('Log transforms require explicit dimensional references')
            if refs and (len(refs) != count or not np.isfinite(refs).all()
                         or min(refs) <= 0):
                raise ValueError('References must be finite, positive and dimensioned')
            object.__setattr__(self, name, tuple(float(x) for x in refs))
        if not isinstance(self.target_minimum, (list, tuple)):
            raise ValueError('Target minima require an explicit ordered list or tuple')
        minima = tuple(None if x is None else _number(x) for x in self.target_minimum) or (None,) * len(self.target_names)
        if len(minima) != len(self.target_names) or any(
                x is not None and not np.isfinite(x) for x in minima):
            raise ValueError('Invalid target domain minimum')
        object.__setattr__(self, 'target_minimum', minima)

    @property
    def cadence_ns(self):
        return self.cadence_seconds * 1_000_000_000

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())

    def as_dict(self):
        return asdict(self)

    def _transform(self, values, refs, count):
        values = np.asarray(values, dtype=float)
        if values.ndim < 1 or values.shape[-1] != count:
            raise ValueError('Transform channel dimension mismatch')
        if not np.isfinite(values).all():
            raise ValueError('Transform values must be finite')
        if self.transform == 'identity':
            return values.copy()
        if values.shape[-1] != len(refs) or (values <= 0).any():
            raise ValueError('Log transform requires positive values and matching references')
        with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
            result = np.log10(values / np.asarray(refs))
        if not np.isfinite(result).all():
            raise ValueError('Nonfinite log transform')
        return result

    def transform_features(self, values):
        return self._transform(values, self.feature_reference, len(self.feature_names))

    def transform_targets(self, values):
        return self._transform(values, self.target_reference, len(self.target_names))

    def inverse_targets(self, values):
        values = np.asarray(values, dtype=float)
        if values.ndim < 1 or values.shape[-1] != len(self.target_names):
            raise ValueError('Inverse target dimension mismatch')
        if not np.isfinite(values).all():
            raise ValueError('Inverse values must be finite')
        if self.transform == 'identity':
            return values.copy()
        if values.shape[-1] != len(self.target_reference):
            raise ValueError('Inverse target dimension mismatch')
        with np.errstate(over='ignore', under='ignore', invalid='ignore'):
            result = np.power(10., values) * np.asarray(self.target_reference)
        if not np.isfinite(result).all() or (result <= 0).any():
            raise ValueError('Inverse transform overflow or nonfinite/domain result')
        return result


@dataclass(frozen=True, eq=False)
class TimeSeriesDataset:
    name: str
    role: str
    starts_ns: np.ndarray
    ends_ns: np.ndarray
    features: np.ndarray
    feature_mask: np.ndarray
    targets: np.ndarray
    target_mask: np.ndarray
    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]
    feature_units: tuple[str, ...]
    target_units: tuple[str, ...]
    cadence_seconds: int
    availability_ns: np.ndarray | None = None
    availability_policy: str = 'explicit'
    time_policy: str = 'explicit_UTC_half_open_intervals'
    quality_policy: str = 'declared_valid_mask_no_imputation'
    metadata_json: str = '{}'

    def __post_init__(self):
        object.__setattr__(self, 'name', _identity(self.name))
        object.__setattr__(self, 'role', _category(self.role, ('synthetic_fixture', 'goes_reference', 'goes_historical'),
                                                'scientific dataset role; SoLEXS remains gated'))
        object.__setattr__(self, 'availability_policy',
                           _category(self.availability_policy, ('explicit', 'bin_end_earliest'),
                                     'availability policy'))
        object.__setattr__(self, 'cadence_seconds', _integer(self.cadence_seconds, positive=True))
        for name in ('feature_names', 'target_names', 'feature_units', 'target_units'):
            object.__setattr__(self, name, _names(getattr(self, name), unique=name.endswith('names')))
        if (len(self.feature_names) != len(self.feature_units)
                or len(self.target_names) != len(self.target_units)):
            raise ValueError('Dataset names/units differ')
        starts, ends = _times(self.starts_ns, ndim=1), _times(self.ends_ns, ndim=1)
        cadence = self.cadence_seconds * 1_000_000_000
        if (not len(starts) or starts.shape != ends.shape or (ends <= starts).any()
                or any(int(e)-int(s) != cadence for s,e in zip(starts,ends))
                or any(int(b)-int(a) < cadence or (int(b)-int(a)) % cadence != 0
                       for a,b in zip(starts,starts[1:]))):
            raise ValueError('Expected unique ordered cadence-aligned intervals')
        object.__setattr__(self, 'starts_ns', starts)
        object.__setattr__(self, 'ends_ns', ends)
        for values_name, mask_name, count in [('features', 'feature_mask', len(self.feature_names)),
                                             ('targets', 'target_mask', len(self.target_names))]:
            values, mask = _values_mask(getattr(self, values_name), getattr(self, mask_name),
                                        (len(starts), count))
            object.__setattr__(self, values_name, values)
            object.__setattr__(self, mask_name, mask)
        if self.availability_ns is None:
            if self.availability_policy == 'explicit':
                raise ValueError('Explicit availability cannot be unknown')
        else:
            if self.availability_policy != 'explicit':
                raise ValueError('Earliest availability bounds cannot stand for actual delivery times')
            available = _times(self.availability_ns, ndim=2)
            if (available.shape != self.features.shape
                    or (available[self.feature_mask] < np.broadcast_to(ends[:, None], available.shape)[self.feature_mask]).any()):
                raise ValueError('Invalid actual availability before bin completion')
            object.__setattr__(self, 'availability_ns', available)
        object.__setattr__(self, 'time_policy', _identity(self.time_policy))
        object.__setattr__(self, 'quality_policy', _identity(self.quality_policy))
        metadata = json.loads(self.metadata_json)
        if not isinstance(metadata, dict):
            raise ValueError('Dataset metadata must be an object')
        object.__setattr__(self, 'metadata_json', canonical_json(metadata))

    @property
    def fingerprint(self):
        return fingerprint_payload(self.semantic_content())

    def semantic_content(self):
        return dict(name=self.name, role=self.role, cadence_seconds=self.cadence_seconds,
                    feature_names=self.feature_names, target_names=self.target_names,
                    feature_units=self.feature_units, target_units=self.target_units,
                    time_policy=self.time_policy, quality_policy=self.quality_policy,
                    availability_policy=self.availability_policy, metadata=json.loads(self.metadata_json),
                    **{name: logical_array(getattr(self, name)) for name in
                       ('starts_ns', 'ends_ns', 'features', 'feature_mask', 'targets', 'target_mask')},
                    availability_ns=None if self.availability_ns is None else logical_array(self.availability_ns))


def _origins(obj):
    issues = _times(obj.issue_times_ns, ndim=1)
    if not isinstance(obj.origin_ids, (list, tuple)):
        raise ValueError('Origins require an explicit ordered list or tuple')
    ids = tuple(_string(x, 'Origin identity') for x in obj.origin_ids)
    if (len(ids) != len(issues) or len(set(ids)) != len(ids)
            or any(not x.strip() for x in ids)
            or any(int(a) >= int(b) for a,b in zip(issues,issues[1:]))):
        raise ValueError('Origins must be ordered, unique and explicitly identified')
    object.__setattr__(obj, 'dataset_fingerprint', _identity(obj.dataset_fingerprint))
    object.__setattr__(obj, 'issue_times_ns', issues)
    object.__setattr__(obj, 'origin_ids', ids)
    return len(issues)


@dataclass(frozen=True, eq=False)
class ForecastContext:
    values: np.ndarray
    mask: np.ndarray
    starts_ns: np.ndarray
    ends_ns: np.ndarray
    issue_times_ns: np.ndarray
    origin_ids: tuple[str, ...]
    spec: ForecastSpec
    dataset_fingerprint: str
    availability_ns: np.ndarray | None = None

    def __post_init__(self):
        n = _origins(self)
        values, mask = _values_mask(self.values, self.mask, (n, self.spec.context_steps, len(self.spec.feature_names)))
        starts, ends = _times(self.starts_ns, ndim=2), _times(self.ends_ns, ndim=2)
        expected = _coordinate_grid(self.issue_times_ns,
                                    (-i*self.spec.cadence_ns for i in range(self.spec.context_steps,0,-1)))
        if (starts.shape != expected.shape or not np.array_equal(starts, expected)
                or not np.array_equal(ends, _shift_times(expected, self.spec.cadence_ns))):
            raise ValueError('Context must contain only completed past bins on the declared grid')
        for name, value in [('values', values), ('mask', mask), ('starts_ns', starts), ('ends_ns', ends)]:
            object.__setattr__(self, name, value)
        if self.availability_ns is None:
            if self.spec.availability_mode == 'operational':
                raise ValueError('Operational contexts require known actual availability')
        else:
            available = _times(self.availability_ns, ndim=3)
            if (available.shape != values.shape
                    or (available[mask] > np.broadcast_to(self.issue_times_ns[:, None, None], values.shape)[mask]).any()
                    or (available[mask] < np.broadcast_to(ends[:, :, None], values.shape)[mask]).any()):
                raise ValueError('Context availability violates the issue-time boundary')
            object.__setattr__(self, 'availability_ns', available)


@dataclass(frozen=True, eq=False)
class FutureGrid:
    starts_ns: np.ndarray
    ends_ns: np.ndarray
    issue_times_ns: np.ndarray
    origin_ids: tuple[str, ...]
    spec: ForecastSpec
    dataset_fingerprint: str

    def __post_init__(self):
        _origins(self)
        starts, ends = _times(self.starts_ns, ndim=2), _times(self.ends_ns, ndim=2)
        expected = _coordinate_grid(self.issue_times_ns,
                                    (i*self.spec.cadence_ns for i in range(self.spec.horizon_steps)))
        if (starts.shape != expected.shape or not np.array_equal(starts, expected)
                or not np.array_equal(ends, _shift_times(expected, self.spec.cadence_ns))
                or (ends <= self.issue_times_ns[:, None]).any()):
            raise ValueError('Future targets must start at issue time and end later')
        object.__setattr__(self, 'starts_ns', starts)
        object.__setattr__(self, 'ends_ns', ends)


def validate_alignment(left, right):
    """Check meaning and coordinates, including ordered origin and target identity."""
    if (left.dataset_fingerprint != right.dataset_fingerprint
            or left.spec.fingerprint != right.spec.fingerprint
            or left.origin_ids != right.origin_ids
            or not np.array_equal(left.issue_times_ns, right.issue_times_ns)):
        raise ValueError('Forecast objects do not align in identity/spec/origins')
    if isinstance(left, FutureGrid) and isinstance(right, FutureGrid):
        if not np.array_equal(left.starts_ns, right.starts_ns) or not np.array_equal(left.ends_ns, right.ends_ns):
            raise ValueError('Future intervals do not align')


@dataclass(frozen=True, eq=False)
class ForecastTargets:
    values: np.ndarray
    mask: np.ndarray
    grid: FutureGrid

    def __post_init__(self):
        shape = (len(self.grid.origin_ids), self.grid.spec.horizon_steps, len(self.grid.spec.target_names))
        values, mask = _values_mask(self.values, self.mask, shape)
        object.__setattr__(self, 'values', values)
        object.__setattr__(self, 'mask', mask)


@dataclass(frozen=True, eq=False)
class ForecastPrediction:
    values: np.ndarray
    grid: FutureGrid
    model_id: str
    quantile_levels: tuple[float, ...] = ()
    quantiles: np.ndarray | None = None
    point_interpretation: str = 'native_point'

    def __post_init__(self):
        object.__setattr__(self, 'model_id', _identity(self.model_id))
        object.__setattr__(self, 'point_interpretation',
                           _category(self.point_interpretation,
                                     ('native_point', 'inverse_transformed_point'), 'point interpretation'))
        shape = (len(self.grid.origin_ids), self.grid.spec.horizon_steps, len(self.grid.spec.target_names))
        values = _immutable(self.values, np.float64)
        if values.shape != shape:
            raise ValueError(f'Prediction must have shape {shape}')
        if not np.isfinite(values).all():
            raise ValueError('Prediction values must be finite')
        for k, minimum in enumerate(self.grid.spec.target_minimum):
            if minimum is not None and (values[:, :, k] < minimum).any():
                raise ValueError('Prediction violates declared target domain')
        object.__setattr__(self, 'values', values)
        levels = tuple(_number(x) for x in self.quantile_levels)
        if self.quantiles is None:
            if levels:
                raise ValueError('Quantile levels require quantile predictions')
        else:
            if (not levels or not np.isfinite(levels).all() or min(levels) <= 0
                    or max(levels) >= 1 or any(a >= b for a, b in zip(levels, levels[1:]))):
                raise ValueError('Quantile levels must be strictly ordered within (0,1)')
            quantiles = _immutable(self.quantiles, np.float64)
            if quantiles.shape != shape + (len(levels),) or not np.isfinite(quantiles).all():
                raise ValueError('Quantile shape/finite contract violated')
            if (np.diff(quantiles, axis=-1) < 0).any():
                raise ValueError('Quantile crossing is not permitted')
            for k, minimum in enumerate(self.grid.spec.target_minimum):
                if minimum is not None and (quantiles[:, :, k, :] < minimum).any():
                    raise ValueError('Quantile prediction violates declared target domain')
            object.__setattr__(self, 'quantiles', quantiles)
        object.__setattr__(self, 'quantile_levels', levels)


@dataclass(frozen=True, eq=False)
class TrainingSlice:
    """Canonical raw train support with exactly validated derived windows.

    Raw feature masks are dependency eligibility by partition end, and optional
    raw availability is actual availability of that entire dependency. Context
    eligibility applies the earlier issue deadline to this canonical support.
    Declared dataset/split labels are separate from the computed fitting identity.
    """
    context: ForecastContext
    targets: ForecastTargets
    raw_starts_ns: np.ndarray
    raw_ends_ns: np.ndarray
    raw_features: np.ndarray
    raw_feature_mask: np.ndarray
    raw_targets: np.ndarray
    raw_target_mask: np.ndarray
    partition_start_ns: int
    partition_end_ns: int
    split_fingerprint: str
    partition_name: str = 'train'
    raw_availability_ns: np.ndarray | None = None

    def __post_init__(self):
        object.__setattr__(self, 'partition_name',
                           _category(self.partition_name, ('train',), 'training partition name'))
        if not isinstance(self.context, ForecastContext) or not isinstance(self.targets, ForecastTargets):
            raise ValueError('Training windows require ForecastContext and ForecastTargets')
        if (not isinstance(self.context.spec, ForecastSpec)
                or not isinstance(self.targets.grid, FutureGrid)
                or not isinstance(self.targets.grid.spec, ForecastSpec)):
            raise ValueError('Training windows require explicit forecast specs and a future grid')
        # Use canonical constructors, not dynamically dispatched subclass hooks.
        # Copied buffers and declarative specs receive the same fixed semantics
        # and validators as builder output; no window values are corrected.
        context = _canonical_fields(self.context, ForecastContext)
        context['spec'] = ForecastSpec(**_canonical_fields(self.context.spec, ForecastSpec))
        grid = _canonical_fields(self.targets.grid, FutureGrid)
        grid['spec'] = ForecastSpec(**_canonical_fields(self.targets.grid.spec, ForecastSpec))
        object.__setattr__(self, 'context', ForecastContext(**context))
        object.__setattr__(self, 'targets', ForecastTargets(self.targets.values, self.targets.mask,
                                                          FutureGrid(**grid)))
        validate_alignment(self.context, self.targets.grid)
        object.__setattr__(self, 'split_fingerprint', _identity(self.split_fingerprint))
        object.__setattr__(self, 'partition_start_ns', _time_scalar(self.partition_start_ns))
        object.__setattr__(self, 'partition_end_ns', _time_scalar(self.partition_end_ns))
        if self.partition_start_ns >= self.partition_end_ns:
            raise ValueError('Invalid training bounds')
        starts, ends = _times(self.raw_starts_ns, ndim=1), _times(self.raw_ends_ns, ndim=1)
        spec = self.context.spec
        if (starts.shape != ends.shape or any(int(b)-int(a) < spec.cadence_ns
                or (int(b)-int(a)) % spec.cadence_ns for a,b in zip(starts,starts[1:]))
                or any(int(e)-int(s) != spec.cadence_ns for s,e in zip(starts,ends))
                or (starts < self.partition_start_ns).any() or (ends > self.partition_end_ns).any()
                or (self.context.starts_ns < self.partition_start_ns).any()
                or (self.targets.grid.ends_ns > self.partition_end_ns).any()):
            raise ValueError('Training support must be unique and within its raw partition')
        if (any(int(row[0])-spec.feature_lookback_steps*spec.cadence_ns < self.partition_start_ns
                for row in self.context.starts_ns)
                or any(int(row[-1])+spec.label_maturity_steps*spec.cadence_ns > self.partition_end_ns
                       for row in self.targets.grid.ends_ns)):
            raise ValueError('Full training window support exceeds its raw partition')
        object.__setattr__(self, 'raw_starts_ns', starts)
        object.__setattr__(self, 'raw_ends_ns', ends)
        observed = set(map(int, starts))
        for context_start, target_end in zip(self.context.starts_ns[:,0], self.targets.grid.ends_ns[:,-1]):
            start = int(context_start)-spec.feature_lookback_steps*spec.cadence_ns
            end = int(target_end)+spec.label_maturity_steps*spec.cadence_ns
            if any(tick not in observed for tick in range(start, end, spec.cadence_ns)):
                raise ValueError('Full training window support bridges a raw cadence gap')
        for vn, mn, count in [('raw_features', 'raw_feature_mask', len(spec.feature_names)),
                              ('raw_targets', 'raw_target_mask', len(spec.target_names))]:
            values, mask = _values_mask(getattr(self, vn), getattr(self, mn), (len(starts), count))
            for row in np.flatnonzero(mask.any(axis=1)):
                start, end = int(starts[row]), int(ends[row])
                if vn == 'raw_features':
                    start -= spec.feature_lookback_steps*spec.cadence_ns
                else:
                    end += spec.label_maturity_steps*spec.cadence_ns
                if (start < self.partition_start_ns or end > self.partition_end_ns
                        or any(tick not in observed for tick in range(start, end, spec.cadence_ns))):
                    raise ValueError('Valid raw training support exceeds bounds or bridges a cadence gap')
            object.__setattr__(self, vn, values)
            object.__setattr__(self, mn, mask)

        available = self.raw_availability_ns
        if available is None:
            if spec.availability_mode == 'operational' or self.context.availability_ns is not None:
                raise ValueError('Canonical raw training availability is required')
        else:
            available = _times(available, ndim=2)
            if (available.shape != self.raw_features.shape
                    or (available[self.raw_feature_mask] < np.broadcast_to(ends[:, None], available.shape)[self.raw_feature_mask]).any()
                    or (available[self.raw_feature_mask] > self.partition_end_ns).any()):
                raise ValueError('Raw training availability contradicts eligible support')
            object.__setattr__(self, 'raw_availability_ns', available)

        # The coverage checks above guarantee these coordinates exist exactly.
        context_rows = np.searchsorted(starts, self.context.starts_ns)
        target_rows = np.searchsorted(starts, self.targets.grid.starts_ns)
        context_mask = self.raw_feature_mask[context_rows]
        if available is not None:
            context_available = available[context_rows]
            if (self.context.availability_ns is None
                    or not np.array_equal(self.context.availability_ns, context_available)):
                raise ValueError('Context availability contradicts canonical raw training support')
            context_mask = context_mask & (context_available <= self.context.issue_times_ns[:, None, None])
        for window, raw_values, rows, mask in (
                (self.context, self.raw_features, context_rows, context_mask),
                (self.targets, self.raw_targets, target_rows, self.raw_target_mask[target_rows])):
            if not np.array_equal(window.mask, mask):
                raise ValueError('Training window mask contradicts canonical raw training support')
            expected = np.where(mask, raw_values[rows], np.nan)
            if not np.array_equal(window.values, expected, equal_nan=True):
                raise ValueError('Training window values contradict canonical raw training support')

    @property
    def spec(self):
        return self.context.spec

    @property
    def fingerprint(self):
        """Observed effective training content, independent of declared labels.

        Windows are determined by validated canonical support and retained
        origins. Full-dataset/split labels are excluded so future-only changes
        do not change the identity of identical effective fitting information.
        """
        return fingerprint_payload(dict(schema_version=1, spec_fingerprint=self.spec.fingerprint,
            partition_name=self.partition_name, partition_start_ns=self.partition_start_ns,
            partition_end_ns=self.partition_end_ns, origin_ids=self.context.origin_ids,
            issue_times_ns=logical_array(self.context.issue_times_ns),
            **{name: logical_array(getattr(self, name)) for name in
               ('raw_starts_ns', 'raw_ends_ns', 'raw_features', 'raw_feature_mask',
                'raw_targets', 'raw_target_mask')},
            raw_availability_ns=None if self.raw_availability_ns is None
                else logical_array(self.raw_availability_ns)))
