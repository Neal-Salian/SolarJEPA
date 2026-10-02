"""Bounded native SoLEXS access. No UTC, GTI or calibration transformation."""
from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
import gzip
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import tempfile
import warnings
import zipfile

import numpy as np
from astropy.io import fits
from astropy import units as u

from .storage import ROLE, repository_relative_path, verify_inventory
from .inspect import json_value


MEMBER_NAME = re.compile(r'AL1_SOLEXS_([0-9]{8})_(SDD[12])_L1\.(lc|gti|pi)\.gz')
TIME_CARDS = ('TIMEUNIT', 'TIMESYS', 'TIMEREF', 'MJDREF', 'MJDREFI', 'MJDREFF',
              'TIMZERO', 'TIMEZERO', 'TIMEDEL', 'TSTART', 'TSTOP', 'DATE-OBS',
              'DATE-END', 'CLOCKAPP', 'TASSIGN')


@dataclass(frozen=True)
class AccessLimits:
    max_member_bytes: int = 16 * 1024**2
    max_fits_bytes: int = 512 * 1024**2
    max_eager_rows: int = 1_000_000
    max_archive_members: int = 128

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in vars(self).values()):
            raise ValueError('Access limits must be positive integers')


@dataclass
class ScienceProduct:
    """HDU access is valid only inside open_solexs_product's context."""
    kind: str
    detector: dict
    hdus: fits.HDUList
    table_name: str
    provenance: dict
    expanded_bytes: int
    time_metadata: dict
    warnings: tuple
    limits: AccessLimits
    active: bool = True


@dataclass(frozen=True)
class NativeColumns:
    """Copied native arrays survive context closure; encoded units may be null."""
    columns: dict
    units: dict
    time_metadata: dict
    provenance: dict
    warnings: tuple


def _inventory(record):
    return dict(schema_version=1, dataset_role=ROLE, files=[record], missing_coverage=[])


def _layout(hdus, kind, detector):
    if hdus[0].header.get('INSTRUME') != 'SoLEXS':
        raise ValueError('Missing or unsupported instrument metadata')
    if any(h.header.get('INSTRUME', 'SoLEXS') != 'SoLEXS' for h in hdus):
        raise ValueError('Conflicting instrument metadata across FITS HDUs')
    if any(h.header.get('FILTER', detector) != detector for h in hdus):
        raise ValueError('Detector metadata conflicts with member identity')
    name, required = {'lc': ('RATE', ('TIME', 'COUNTS')),
                      'gti': ('GTI', ('START', 'STOP')),
                      'pi': ('SPECTRUM', ('TSTART', 'TELAPSE', 'SPEC_NUM', 'CHANNEL',
                                          'COUNTS', 'EXPOSURE'))}.get(kind, (None, ()))
    if name is None:
        raise ValueError('Unsupported scientific product layout')
    tables = [h for h in hdus if h.name == name]
    if len(tables) != 1 or not isinstance(tables[0], fits.BinTableHDU):
        raise ValueError('Missing or ambiguous scientific table HDU')
    table = tables[0]
    if not set(required).issubset(table.columns.names):
        raise ValueError('Missing required scientific columns')
    for column in required:
        array = table.data[column]
        dimensions = 2 if kind == 'pi' and column in ('CHANNEL', 'COUNTS') else 1
        if array.ndim != dimensions or array.dtype.kind not in 'iuf':
            raise ValueError('Scientific columns must be scalar numeric values')
    if kind == 'pi':
        width = table.header.get('DETCHANS')
        if (type(width) is not int or width <= 0 or table.header.get('CHANTYPE') != 'PI'
                or table.header.get('HDUCLAS4') != 'TYPE:II'):
            raise ValueError('Unsupported Type-II PI metadata')
        if (table.data['CHANNEL'].shape != table.data['COUNTS'].shape
                or table.data['COUNTS'].shape[1] != width
                or table.data['CHANNEL'].dtype.kind not in 'iu'
                or table.data['SPEC_NUM'].dtype.kind not in 'iu'):
            raise ValueError('Incompatible PI vector dimensions/channel identifiers')
    card = table.header.get('FILTER', hdus[0].header.get('FILTER'))
    association = dict(value=detector, evidence='OBSERVED' if card else 'INFERRED',
                       source=('FILTER' if 'FILTER' in table.header else 'PRIMARY.FILTER')
                       if card else 'member_name')
    time = {k: table.header.get(k) for k in TIME_CARDS}
    notices = ['UTC_CONVERSION_NOT_APPLIED', 'GTI_FILTERING_NOT_APPLIED', 'CALIBRATION_NOT_APPLIED']
    if time['MJDREFI'] is None or time['TIMEUNIT'] is None or time['TIMESYS'] is None:
        notices.append('TIME_REFERENCE_MISSING')
    time_column = {'lc': 'TIME', 'gti': 'START', 'pi': 'TSTART'}[kind]
    encoded_unit = table.columns[time_column].unit
    if encoded_unit is not None and time['TIMEUNIT'] is not None:
        try:
            if u.Unit(encoded_unit).to(u.Unit(time['TIMEUNIT'])) != 1:
                notices.append('TIME_COLUMN_UNIT_CONFLICT')
        except (ValueError, u.UnitConversionError):
            notices.append('TIME_COLUMN_UNIT_CONFLICT')
    if (hdus[0].header.get('CREATOR') == 'solexs_pipeline-1.1'
            and time['MJDREFI'] == 40587 and time['MJDREFF'] not in (None, 0)):
        notices.append('TIME_REFERENCE_CONFLICT')
    if kind == 'lc':
        notices.append('LC_BIN_POSITION_UNKNOWN')
    elif kind == 'gti':
        notices.append('GTI_ENDPOINT_EXPOSURE_POLICY_UNKNOWN')
    else:
        notices.extend(['CHANNEL_ENERGY_MAPPING_NOT_APPLIED', 'EXPOSURE_CORRECTION_STATE_UNKNOWN'])
    return name, association, time, tuple(notices)


@contextmanager
def open_solexs_product(root: Path, record: dict, member: str, *, limits=AccessLimits()):
    """Verify a registered ZIP; stage exactly one bounded gzip/FITS member.

    Never uses member names as extraction paths. No persistent cache is published.
    Source identity/listing safety reuse the registration foundation unchanged.
    Callers must not retain HDU/mapped-array views after leaving this context.
    """
    root = Path(root).resolve()
    verify_inventory(_inventory(record), root)
    if record['processing_level'] != 'L1':
        raise ValueError('Only the verified L1 scientific product contract is supported')
    if len(record['archive']['members']) > limits.max_archive_members:
        raise ValueError('Archive member-count limit exceeded')
    declarations = [m for m in record['archive']['members'] if m['path'] == member]
    if len(declarations) != 1 or declarations[0]['is_directory']:
        raise ValueError('Select one registered scientific member')
    declaration = declarations[0]
    if declaration['uncompressed_bytes'] > limits.max_member_bytes:
        raise ValueError('Compressed-member byte limit exceeded')
    name = PurePosixPath(member)
    match = MEMBER_NAME.fullmatch(name.name)
    if match is None:
        raise ValueError('Unsupported SoLEXS scientific member name')
    date, detector, kind = match.groups()
    if name.parent.name != detector or date != record['nominal_observation_date'].replace('-', ''):
        raise ValueError('Scientific member identity conflicts with archive/detector')
    cache = root / repository_relative_path('.cache/aditya/solexs', root)
    cache.mkdir(parents=True, exist_ok=True)
    source = root / record['path']
    with tempfile.TemporaryDirectory(dir=cache, prefix='product-') as temporary:
        target = Path(temporary) / 'inspected.fits'
        digest, expanded = hashlib.sha256(), 0
        try:
            with zipfile.ZipFile(source) as z:
                with z.open(member) as stream:
                    compressed = stream.read(limits.max_member_bytes + 1)
                if len(compressed) > limits.max_member_bytes:
                    raise ValueError('Compressed-member byte limit exceeded')
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as gz, target.open('wb') as dest:
                while block := gz.read(min(1024**2, limits.max_fits_bytes - expanded + 1)):
                    expanded += len(block)
                    if expanded > limits.max_fits_bytes:
                        raise ValueError('FITS expansion byte limit exceeded')
                    digest.update(block)
                    dest.write(block)
        except (gzip.BadGzipFile, EOFError, zipfile.BadZipFile) as exc:
            raise ValueError('Corrupt ZIP/gzip scientific member') from exc
        with warnings.catch_warnings():
            warnings.simplefilter('error', fits.verify.VerifyWarning)
            try:
                hdus = fits.open(target, mode='readonly', memmap=True, lazy_load_hdus=False)
            except (OSError, ValueError) as exc:
                raise ValueError('Malformed FITS scientific payload') from exc
            product = None
            try:
                hdus.verify('exception')
                # A VLA exposes object arrays with mutable nested views and may
                # expand the heap on access. This fixed-width contract rejects
                # them before checksum/data access, including extra HDUs.
                if any(re.match(r'\d*[PQ]', str(c.format)) for h in hdus
                       for c in getattr(h, 'columns', [])):
                    raise ValueError('Variable-length scientific columns are unsupported')
                for hdu in hdus:
                    for key, verify in [('DATASUM', hdu.verify_datasum), ('CHECKSUM', hdu.verify_checksum)]:
                        if key in hdu.header and verify() != 1:
                            raise ValueError(f'FITS {key} verification failed')
                table, association, time, notices = _layout(hdus, kind, detector)
                verify_inventory(_inventory(record), root)
                provenance = dict(archive=record['path'], archive_sha256=record['sha256'],
                                  member=member, member_gzip_sha256=hashlib.sha256(compressed).hexdigest(),
                                  fits_sha256=digest.hexdigest(), zip_member_crc_verified=True,
                                  gzip_integrity_verified=True, kind=kind, detector=association)
                product = ScienceProduct(kind, association, hdus, table, provenance, expanded,
                                         time, notices, limits)
                yield product
            finally:
                if product is not None:
                    product.active = False
                # Release the HDU's cached column bindings before destroying its
                # FITS_rec. Otherwise Astropy preserves them as full table copies
                # (FITS_rec.__del__), defeating bounded chunk access on close.
                # NativeColumns own independent copies; no mapped view escapes.
                for hdu in hdus:
                    if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                        del hdu.columns
                # Astropy closes the backing file and drops loaded mmap views.
                # Reading .data after close would invoke a lazy read on that file.
                hdus.close()


def _table(product, kind):
    if not product.active:
        raise ValueError('Scientific product context is closed')
    if product.kind != kind:
        raise ValueError('Loader does not match scientific product kind')
    return product.hdus[product.table_name]


def _copy_columns(product, table, selection=slice(None)):
    columns = {c.name: np.array(table.data[c.name][selection], copy=True) for c in table.columns}
    for values in columns.values():
        values.setflags(write=False)
    return NativeColumns(columns, {c.name: c.unit for c in table.columns},
                         dict(product.time_metadata), dict(product.provenance), product.warnings)


def _load_eager(product, kind):
    table = _table(product, kind)
    if len(table.data) > product.limits.max_eager_rows:
        raise ValueError('Eager scientific row limit exceeded')
    return _copy_columns(product, table)


def load_light_curve(product: ScienceProduct) -> NativeColumns:
    """Native TIME/COUNTS, without UTC conversion, cleaning or rate/flux conversion."""
    return _load_eager(product, 'lc')


def load_gti(product: ScienceProduct) -> NativeColumns:
    """Native START/STOP, without choosing an endpoint or filtering policy."""
    return _load_eager(product, 'gti')


def iter_spectra(product: ScienceProduct, *, chunk_rows=1024):
    """Yield independent readonly native Type-II chunks, without response mapping.

    Iteration must occur inside the product context. Retained chunks remain valid
    after it closes. Memory grows if the caller collects every chunk in a list.
    """
    if type(chunk_rows) is not int or chunk_rows <= 0:
        raise ValueError('chunk_rows must be a positive integer')
    table = _table(product, 'pi')
    for start in range(0, len(table.data), chunk_rows):
        _table(product, 'pi')  # Also reject resumption after context closure.
        yield _copy_columns(product, table, slice(start, start + chunk_rows))


def _numeric_update(stats, array):
    finite = np.isfinite(array)
    values = array[finite]
    for key, count in dict(values=array.size, finite=values.size, nan=np.isnan(array).sum(),
                           positive_infinity=np.isposinf(array).sum(),
                           negative_infinity=np.isneginf(array).sum(),
                           negative=(values < 0).sum(), zero=(values == 0).sum(),
                           noninteger_finite=(values != np.floor(values)).sum()
                           if array.dtype.kind == 'f' else 0).items():
        stats[key] = stats.get(key, 0) + int(count)
    for key, value, operation in [('min', values.min() if values.size else None, min),
                                  ('max', values.max() if values.size else None, max)]:
        if key not in stats:
            stats[key] = None
        if value is not None:
            value = value.item()
            stats[key] = operation(stats[key], value) if stats[key] is not None else value


def _difference(after, before):
    # FITS integer coordinates include unsigned/16-bit fields. NumPy subtraction
    # in those dtypes wraps, and even int64 can overflow. Python integers keep
    # diagnostic arithmetic exact while leaving returned native arrays intact.
    if after.dtype.kind in 'iu':
        after = after.astype(object)
    if before.dtype.kind in 'iu':
        before = before.astype(object)
    # Mixed floats/integers need exact arithmetic too: Python float subtraction
    # can round an integer above 2**53 into a false zero. Fractions represent the
    # stored floating values exactly, only for these uncommon mixed diagnostics.
    if after.dtype.kind == 'f' and before.dtype.kind == 'O':
        after = _fraction_array(after)
    if before.dtype.kind == 'f' and after.dtype.kind == 'O':
        before = _fraction_array(before)
    return after - before


def _fraction_array(values):
    return np.array([Fraction(float(v)) if np.isfinite(v) else float(v)
                     for v in values.flat], dtype=object).reshape(values.shape)


def _compare(operation, left, right):
    left, right = np.asarray(left), np.asarray(right)
    if left.dtype.kind != right.dtype.kind:
        left, right = left.astype(object), right.astype(object)
    return operation(left, right)


def _number(value):
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else float(value)
    return json_value(value)


def _coordinates_equal(left, right):
    return left.shape == right.shape and bool(_compare(np.equal, left, right).all())


def _time_summary(values):
    """Numeric coordinate diagnostics; 'one' means one native coordinate unit."""
    finite = np.isfinite(values)
    points = values[finite]
    adjacent = finite[:-1] & finite[1:]
    steps = _difference(values[1:][adjacent], values[:-1][adjacent])
    return json_value(dict(
        first_native=values[0] if values.size else None,
        last_native=values[-1] if values.size else None,
        min_native=points.min() if points.size else None,
        max_native=points.max() if points.size else None,
        duplicate_values=points.size - np.unique(points).size,
        nonmonotonic_steps=int((steps < 0).sum()), zero_steps=int((steps == 0).sum()),
        step_min=steps.min() if steps.size else None,
        step_max=steps.max() if steps.size else None,
        positive_steps_not_one=int(((steps > 0) & (steps != 1)).sum()),
        converted_utc=None, epoch_interpretation='UNKNOWN_NOT_APPLIED'))


def _gti_summary(columns):
    start, stop = columns['START'], columns['STOP']
    finite = np.isfinite(start) & np.isfinite(stop)
    valid = finite & _compare(np.greater_equal, stop, start)
    return json_value(dict(
        invalid_intervals=int((finite & _compare(np.less, stop, start)).sum()),
        nonfinite_intervals=int((~finite).sum()),
        adjacent_overlaps=int((valid[:-1] & valid[1:] & _compare(np.less, start[1:], stop[:-1])).sum()),
        unordered_starts=int((_difference(start[1:], start[:-1]) < 0).sum()),
        sum_stop_minus_start_native=_number(_difference(stop[finite], start[finite]).sum()),
        intervals_native=[[json_value(a), json_value(b)] for a, b in zip(start[:64], stop[:64])],
        intervals_truncated=len(start) > 64, endpoint_policy='UNKNOWN_NOT_APPLIED',
        continuous_exposure=None))


def _hdu_inventory(hdus):
    return [dict(
        index=i, name=h.name, type=type(h).__name__,
        header_cards=[[c.keyword, json_value(c.value), c.comment] for c in h.header.cards],
        datasum='verified' if 'DATASUM' in h.header else 'absent',
        checksum='verified' if 'CHECKSUM' in h.header else 'absent',
        columns=[dict(name=c.name, format=c.format, unit=c.unit,
                      shape=list(h.data[c.name].shape), dtype=str(h.data[c.name].dtype))
                 for c in getattr(h, 'columns', [])]) for i, h in enumerate(hdus)]


def _inspect_product(product, chunk_rows, light_curve=None):
    table = _table(product, product.kind)
    if len(table.data) > product.limits.max_eager_rows:
        raise ValueError('Summary time-coordinate row limit exceeded')
    numeric, times, spectral, sums, identifiers = {}, [], None, [], []
    if product.kind == 'pi':
        chunks = iter_spectra(product, chunk_rows=chunk_rows)
        spectral = dict(all_nan_rows=0, partially_nan_rows=0, channel_axis_constant=True,
                        channel_min=None, channel_max=None, exposure_equals_telapse_rows=0,
                        nonpositive_exposure_rows=0, energy_mapping=None)
    else:
        chunks = iter([_load_eager(product, product.kind)])
    first_channel = None
    for chunk in chunks:
        for name, values in chunk.columns.items():
            if values.dtype.kind in 'iuf':
                _numeric_update(numeric.setdefault(name, {}), values)
        if product.kind == 'pi':
            cols = chunk.columns
            times.append(cols['TSTART'])
            identifiers.append(cols['SPEC_NUM'])
            if light_curve is not None:
                counts = cols['COUNTS']
                sums.append((counts.astype(object) if counts.dtype.kind in 'iu' else counts).sum(axis=1))
            nan = np.isnan(cols['COUNTS']).sum(axis=1)
            spectral['all_nan_rows'] += int((nan == cols['COUNTS'].shape[1]).sum())
            spectral['partially_nan_rows'] += int(((nan > 0) & (nan < cols['COUNTS'].shape[1])).sum())
            if len(cols['CHANNEL']):
                if first_channel is None:
                    first_channel = cols['CHANNEL'][0].copy()
                spectral['channel_axis_constant'] &= bool((cols['CHANNEL'] == first_channel).all())
            spectral['exposure_equals_telapse_rows'] += int(_compare(np.equal, cols['EXPOSURE'], cols['TELAPSE']).sum())
            spectral['nonpositive_exposure_rows'] += int((cols['EXPOSURE'] <= 0).sum())
        elif product.kind == 'lc':
            times.append(chunk.columns['TIME'])
        else:
            gti = _gti_summary(chunk.columns)
    if spectral is not None:
        spectral['channel_min'] = numeric.get('CHANNEL', {}).get('min')
        spectral['channel_max'] = numeric.get('CHANNEL', {}).get('max')
        ids = np.concatenate(identifiers) if identifiers else np.array([])
        spectral['spec_num_duplicate_values'] = int(ids.size - np.unique(ids).size)
        if len(table.data) == 0:
            spectral['channel_axis_constant'] = None
    result = dict(kind=product.kind, detector=product.detector, provenance=product.provenance,
                  format='FITS', expanded_bytes=product.expanded_bytes,
                  table_bytes=int(table.header['NAXIS1'] * table.header['NAXIS2']),
                  rows=len(table.data), hdus=_hdu_inventory(product.hdus),
                  time_metadata=product.time_metadata, warnings=list(product.warnings), numeric=numeric)
    if product.kind == 'gti':
        result['gti'] = gti
    else:
        result['time'] = _time_summary(np.concatenate(times) if times else np.array([]))
    if spectral is not None:
        result['spectra'] = spectral
        if light_curve is not None:
            coordinates = np.concatenate(times) if times else np.array([])
            lc = light_curve.columns
            equal = _coordinates_equal(coordinates, lc['TIME'])
            comparison = dict(time_rows_equal=equal, nan_masks_equal=None, equal_sum_rows=None,
                              maximum_absolute_sum_difference=None, compared_finite_rows=None,
                              quantity_equivalence='UNKNOWN', transformations_applied=False)
            if equal:
                totals = np.concatenate(sums) if sums else np.array([])
                # Object totals here contain exact Python integer sums only.
                finite = np.ones(totals.shape, dtype=bool) if totals.dtype.kind == 'O' else np.isfinite(totals)
                missing = np.zeros(totals.shape, dtype=bool) if totals.dtype.kind == 'O' else np.isnan(totals)
                usable = finite & np.isfinite(lc['COUNTS'])
                difference = _difference(totals[usable], lc['COUNTS'][usable])
                comparison.update(nan_masks_equal=bool(np.array_equal(missing, np.isnan(lc['COUNTS']))),
                                  equal_sum_rows=int((difference == 0).sum()),
                                  compared_finite_rows=int(usable.sum()),
                                  maximum_absolute_sum_difference=_number(np.abs(difference).max())
                                  if difference.size else None)
            result['lc_comparison'] = comparison
    return result


def _gti_comparison(light_curve, gti):
    start, stop = gti.columns['START'], gti.columns['STOP']
    result = dict(coordinate_policy='inclusive_point_membership_diagnostic',
                  evidence='OBSERVED', filter_applied=False, continuous_exposure=None,
                  finite_inside=None, finite_outside=None, nan_inside=None, nan_outside=None)
    if len(start) > 64 or not (np.isfinite(start) & np.isfinite(stop)
                              & _compare(np.greater_equal, stop, start)).all():
        return dict(result, status='not_checked_large_or_invalid_interval_list')
    lc = light_curve.columns
    inside = np.zeros(len(lc['TIME']), dtype=bool)
    for a, b in zip(start, stop):
        inside |= _compare(np.greater_equal, lc['TIME'], a) & _compare(np.less_equal, lc['TIME'], b)
    finite, nan = np.isfinite(lc['COUNTS']), np.isnan(lc['COUNTS'])
    return dict(result, status='checked_native_coordinates_only',
                finite_inside=int((finite & inside).sum()), finite_outside=int((finite & ~inside).sum()),
                nan_inside=int((nan & inside).sum()), nan_outside=int((nan & ~inside).sum()))


def inspect_solexs_archive(root: Path, record: dict, *, limits=AccessLimits(), chunk_rows=1024) -> dict:
    """Deterministic, portable native inventory/quality report; no transformations.

    Full ZIP-member CRC, gzip, FITS structure and present FITS checksums are checked.
    Unknown units and conflicting/missing clock metadata are retained. A failed
    scientific member aborts the report, rather than publishing partial success.
    """
    if type(chunk_rows) is not int or chunk_rows <= 0:
        raise ValueError('chunk_rows must be a positive integer')
    root = Path(root).resolve()
    verify_inventory(_inventory(record), root)
    members = record['archive']['members']
    if len(members) > limits.max_archive_members or any(
            m['uncompressed_bytes'] > limits.max_member_bytes for m in members):
        raise ValueError('Archive inspection limit exceeded')
    products, curves, intervals = [], {}, {}
    for member in sorted(members, key=lambda m: m['path']):
        if not member['is_directory']:
            with open_solexs_product(root, record, member['path'], limits=limits) as product:
                detector = product.detector['value']
                summary = _inspect_product(product, chunk_rows, curves.get(detector))
                if product.kind == 'gti':
                    intervals[detector] = load_gti(product)
                elif product.kind == 'lc':
                    curves[detector] = load_light_curve(product)
                    if detector in intervals:
                        summary['gti_comparison'] = _gti_comparison(curves[detector], intervals[detector])
                products.append(summary)
    with zipfile.ZipFile(root / record['path']) as archive:
        for member in members:
            with archive.open(member['path']) as stream:
                if len(stream.read(limits.max_member_bytes + 1)) > limits.max_member_bytes:
                    raise ValueError('ZIP CRC inspection byte limit exceeded')
    verify_inventory(_inventory(record), root)
    return dict(schema_version=1, evidence='OBSERVED',
                evidence_scope='integrity, structure, native values and diagnostics', dataset_role=ROLE,
                archive=record['path'], archive_bytes=record['bytes'], archive_sha256=record['sha256'],
                nominal_observation_date=record['nominal_observation_date'],
                product_version=record['product_version'],
                identity_evidence=dict(archive='OBSERVED', archive_bytes='OBSERVED', archive_sha256='OBSERVED',
                                       nominal_observation_date=record['metadata_evidence']['nominal_observation_date'],
                                       product_version=record['metadata_evidence']['product_version']),
                zip_integrity='verified',
                members=members, products=products)
