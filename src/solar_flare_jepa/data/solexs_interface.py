"""Guarded native SoLEXS preparation for future integration, without training.

Only the archive loader verifies external bytes. Preparing an in-memory
NativeColumns snapshot validates structure and derives numerical masks; it
does not authenticate caller-supplied provenance or grant scientific clearance.
"""
from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType

import numpy as np

from .solexs import NativeColumns, iter_spectra, load_gti, load_light_curve, open_solexs_product
from .solexs_quality import (
    frozen_array, gti_diagnostics, numerical_quality, require_same_source, validate_native_step,
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _array_identity(a):
    return dict(dtype=str(a.dtype), shape=list(a.shape), sha256=hashlib.sha256(a.tobytes()).hexdigest())


def require_native_request(representation='native'):
    if type(representation) is not str or representation != 'native':
        raise ValueError('Only native preparation is supported; scientific conversion remains BLOCKED')


@dataclass(frozen=True)
class NativeBatch:
    columns: object
    quality: object
    row_start: int
    metadata_json: str
    gti: object = None

    @property
    def provenance(self):
        return json.loads(self.metadata_json)['provenance']

    @property
    def gti_provenance(self):
        return json.loads(self.metadata_json)['gti_provenance']

    @property
    def units(self):
        return json.loads(self.metadata_json)['units']

    @property
    def time_metadata(self):
        return json.loads(self.metadata_json)['time_metadata']

    @property
    def fingerprint(self):
        identity = dict(metadata=json.loads(self.metadata_json), row_start=self.row_start,
            columns={name: _array_identity(a) for name, a in self.columns.items()},
            numerical_masks={name: _array_identity(getattr(self.quality, name)) for name in
                ('entry_finite', 'entry_nan', 'entry_positive_infinity', 'entry_negative_infinity')},
            row_flags={name: _array_identity(a) for name, a in self.quality.rows.items()},
            gti_masks={name: _array_identity(getattr(self.gti, name)) for name in ('closed', 'half_open')}
                if self.gti is not None else None)
        return hashlib.sha256(_json(identity).encode()).hexdigest()

    def require_jepa_ready(self):
        raise ValueError('SoLEXS scientific JEPA integration/training is BLOCKED: timing, quality, '
                         'exposure, response applicability and target/availability are unresolved')

    def summary(self):
        metadata = json.loads(self.metadata_json)
        return dict(row_start=self.row_start, **metadata,
                    columns={name: dict(dtype=str(a.dtype), shape=list(a.shape),
                                        unit=metadata['units'].get(name))
                             for name, a in self.columns.items()},
                    numerical_quality=self.quality.summary(),
                    gti=self.gti.summary() if self.gti is not None else None,
                    fingerprint=self.fingerprint)


def prepare_native_batch(native, *, expected_step, row_start=0, previous_coordinate=None,
                         gti=None, representation='native'):
    """Detach original arrays and metadata; no cleanup or physical transformation.

    Negative, zero, fractional and missing values remain in their original rows.
    The returned masks describe stored numbers. Upstream energy calibration and
    correction state are distinct from SolarJEPA's local transformations.
    """
    require_native_request(representation)
    if not isinstance(native, NativeColumns) or type(row_start) is not int or row_start < 0:
        raise ValueError('Expected native columns and a nonnegative row origin')
    provenance = native.provenance
    if (provenance.get('kind') not in ('lc', 'pi')
            or provenance.get('detector', {}).get('value') not in ('SDD1', 'SDD2')):
        raise ValueError('Expected separate detector-labelled LC or PI')
    for key in ('archive_sha256', 'member_gzip_sha256', 'fits_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', provenance.get(key, '')):
            raise ValueError('Missing complete native product source identity')
    if not provenance.get('archive') or not provenance.get('member'):
        raise ValueError('Missing native source paths')
    columns = MappingProxyType({name: frozen_array(values) for name, values in native.columns.items()})
    if set(native.units) != set(columns):
        raise ValueError('Native unit/column metadata differ')
    if provenance['kind'] == 'pi':
        required = {'TSTART', 'TELAPSE', 'EXPOSURE', 'SPEC_NUM', 'CHANNEL', 'COUNTS'}
        if not required <= set(columns):
            raise ValueError('Missing required native PI columns')
        channel, identifiers, counts = columns['CHANNEL'], columns['SPEC_NUM'], columns['COUNTS']
        if (channel.ndim != 2 or counts.ndim != 2 or channel.shape != counts.shape
                or channel.dtype.kind not in 'iu' or identifiers.ndim != 1
                or identifiers.dtype.kind not in 'iu'):
            raise ValueError('Invalid native PI channel/counter identifiers or dimensions')
    # Work only from captured arrays, so caller masks and subsequent mutations
    # cannot change the prepared numerical result.
    snapshot = NativeColumns(columns, dict(native.units), dict(native.time_metadata),
                             json.loads(_json(provenance)), tuple(native.warnings))
    quality = numerical_quality(snapshot, expected_step=expected_step,
                                previous_coordinate=previous_coordinate)
    rows = len(quality.rows['finite_coordinate'])
    if any(a.ndim == 0 or len(a) != rows for a in columns.values()):
        raise ValueError('Native column row counts differ')
    diagnostic = gti_diagnostics(snapshot, gti) if gti is not None else None
    metadata = dict(provenance=snapshot.provenance, units=snapshot.units,
        time_metadata=snapshot.time_metadata, warnings=list(snapshot.warnings),
        expected_native_step=expected_step.item() if isinstance(expected_step, np.generic) else expected_step,
        gti_provenance=gti.provenance if gti is not None else None,
        semantics=dict(representation='native_values_and_encoded_metadata',
            validated_utc=None, physical_quantity='NOT_ESTABLISHED_BY_THIS_INTERFACE',
            scientific_quality='UNKNOWN_NOT_APPLIED', upstream_correction_state='UNKNOWN',
            completed_bin_availability='UNKNOWN', continuous_live_exposure=None,
            local_transformations=dict(calibration=False, unit_conversion=False,
                utc_conversion=False, gti_filter=False, gap_filling=False,
                normalization=False, channel_mapping=False),
            jepa_training_allowed=False))
    return NativeBatch(columns, quality, row_start, _json(metadata), diagnostic)


def iter_native_batches(root, record, member, *, chunk_rows=1024, expected_step=1,
                        gti_member=None, representation='native'):
    """Yield bounded, verified, detector-separated native LC/PI snapshots.

    The default step is one numerical coordinate unit, without asserting a
    second or clock. Each product starts its own run; streams are never joined.
    GTI comparisons require explicit member selection. Scratch cleanup belongs
    to the existing loader context, including generator close/failure.
    """
    require_native_request(representation)
    validate_native_step(expected_step)
    if type(chunk_rows) is not int or not 1 <= chunk_rows <= 8192:
        raise ValueError('Native batch chunk_rows must be in 1..8192')
    intervals = None
    if gti_member is not None:
        with open_solexs_product(root, record, gti_member) as product:
            intervals = load_gti(product)
    with open_solexs_product(root, record, member) as product:
        if intervals is not None:
            require_same_source(product.provenance, intervals.provenance)
        if product.kind == 'pi':
            chunks = iter_spectra(product, chunk_rows=chunk_rows)
        elif product.kind == 'lc':
            native = load_light_curve(product)
            chunks = (NativeColumns({name: values[start:start+chunk_rows]
                                     for name, values in native.columns.items()},
                                    native.units, native.time_metadata, native.provenance, native.warnings)
                      for start in range(0, len(native.columns['TIME']), chunk_rows))
        else:
            raise ValueError('Native batches require LC or PI; GTIs are diagnostic inputs')
        previous, offset = None, 0
        for chunk in chunks:
            batch = prepare_native_batch(chunk, expected_step=expected_step, row_start=offset,
                                         previous_coordinate=previous, gti=intervals)
            time = batch.columns['TIME' if product.kind == 'lc' else 'TSTART']
            if len(time):
                previous = time[-1].item()
            offset += len(time)
            yield batch
