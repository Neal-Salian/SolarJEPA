"""Sample-index numerical contracts. These never grant physical training clearance."""
from dataclasses import dataclass
import hashlib
import json
import re

import numpy as np

from solar_flare_jepa.data.solexs import NativeColumns
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload

LABEL = 'EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED'
UNIT = 'UNKNOWN_UNENCODED_NATIVE_VALUE'
BUILDER_VERSION = 'solexs-recorded-sequence-v1'


def _array(values, dtype):
    a = np.asarray(values, dtype=dtype)
    return np.frombuffer(a.tobytes(), dtype=a.dtype).reshape(a.shape)


def array_hash(values):
    a = np.asarray(values)
    return fingerprint_payload(dict(shape=list(a.shape), dtype=str(a.dtype),
                                    sha256=hashlib.sha256(a.tobytes()).hexdigest()))


@dataclass(frozen=True)
class NativeSequence:
    coordinates: np.ndarray
    values: np.ndarray
    observed: np.ndarray
    source_json: str

    @property
    def source(self):
        return json.loads(self.source_json)

    @property
    def fingerprint(self):
        return fingerprint_payload(dict(source=self.source, coordinates=array_hash(self.coordinates),
                                        values=array_hash(self.values), observed=array_hash(self.observed)))


def sequence_from_native(native):
    """Preserve original row order, numerical values/missingness and exact provenance.

    Current pilot contract intentionally rejects any changed column/unit layout:
    new quality fields or encoded physical semantics need explicit design review.
    """
    if not isinstance(native, NativeColumns) or set(native.columns) != {'TIME', 'COUNTS'}:
        raise ValueError('Expected exactly native LC TIME/COUNTS; quality policy requires review')
    p = native.provenance
    if (p.get('kind') != 'lc' or p.get('detector', {}).get('value') != 'SDD2'
            or p.get('detector', {}).get('evidence') != 'OBSERVED'):
        raise ValueError('Requires observed SDD2 LC identity')
    for key in ('archive_sha256', 'member_gzip_sha256', 'fits_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', p.get(key, '')):
            raise ValueError('Missing full source identity')
    if not p.get('archive') or not p.get('member'):
        raise ValueError('Missing product provenance')
    if native.units != {'TIME': None, 'COUNTS': None}:
        raise ValueError('Pilot has unencoded column units; changed units require review')
    t, v = (_array(native.columns[k], np.float64) for k in ('TIME', 'COUNTS'))
    if (t.ndim != 1 or t.shape != v.shape or len(t) < 2 or len(t) > 1_000_000
            or not np.isfinite(t).all() or not (np.diff(t) > 0).all()):
        raise ValueError('Ambiguous native sequence order/shape; sorting and deduplication forbidden')
    if np.isinf(v).any() or not np.isfinite(v).any():
        raise ValueError('Infinite values or no finite numerical support')
    source = dict(builder_version=BUILDER_VERSION, scientific_label=LABEL,
                  native_unit=UNIT, target='SDD2 LC RATE.COUNTS recorded numerical values',
                  provenance=p, time_metadata=native.time_metadata, warnings=list(native.warnings),
                  time_basis='native row index; UTC and completed-bin availability UNKNOWN',
                  quality='finite numerical usability only; scientific QC UNKNOWN_NOT_APPLIED',
                  calibration_applied=False, exposure_interpretation='UNKNOWN_NOT_APPLIED',
                  gti_filter_applied=False, gap_filling=False, physical_forecasting_clearance=False)
    return NativeSequence(t, v, _array(np.isfinite(v), bool), canonical_json(source))


def _bounds(sequence, start, stop):
    if (type(start) is not int or type(stop) is not int
            or not 0 <= start < stop <= len(sequence.values)):
        raise ValueError('Invalid half-open raw row partition')


@dataclass(frozen=True)
class SequenceWindows:
    x: np.ndarray
    y: np.ndarray
    x_mask: np.ndarray
    y_mask: np.ndarray
    origins: np.ndarray
    source_fingerprint: str
    summary_json: str

    @property
    def summary(self):
        return json.loads(self.summary_json)

    @property
    def fingerprint(self):
        return fingerprint_payload(dict(summary=self.summary, source=self.source_fingerprint,
                                        x=array_hash(self.x), y=array_hash(self.y),
                                        x_mask=array_hash(self.x_mask), y_mask=array_hash(self.y_mask),
                                        origins=array_hash(self.origins)))


def make_windows(sequence, start, stop, *, context, horizon, stride):
    """Fixed split-start lattice; whole context+target must be one finite run.

    Native coordinate transitions must equal one NUMERICAL unit. No seconds or
    live exposure is implied. Target origin is the first future raw row index.
    """
    _bounds(sequence, start, stop)
    if any(type(a) is not int or not 1 <= a <= 4096 for a in (context, horizon, stride)):
        raise ValueError('Window lengths must be bounded positive sample counts')
    origins = np.arange(start+context, stop-horizon+1, stride, dtype=np.int64)
    missing = np.r_[0, np.cumsum(~sequence.observed)]
    gaps = np.r_[0, np.cumsum(np.diff(sequence.coordinates) != 1)]
    left, right = origins-context, origins+horizon
    has_missing = missing[right] != missing[left]
    has_gap = gaps[right-1] != gaps[left]
    retained = origins[~(has_missing | has_gap)]
    if len(retained) == 0:
        raise ValueError('No eligible complete numerical sequence windows')
    xi = retained[:, None] + np.arange(-context, 0)
    yi = retained[:, None] + np.arange(horizon)
    x, y = sequence.values[xi, None], sequence.values[yi, None]
    summary = dict(scientific_label=LABEL, unit=UNIT, raw_start=start, raw_stop=stop,
                   context_samples=context, horizon_samples=horizon, stride_samples=stride,
                   lattice='raw_split_start_plus_context_then_fixed_stride', expected_native_step=1,
                   candidate_origins=len(origins), retained_origins=len(retained),
                   excluded_origins=int((has_missing | has_gap).sum()),
                   excluded_missing=int(has_missing.sum()),
                   excluded_discontinuity=int((has_gap & ~has_missing).sum()),
                   missing_rows=int((~sequence.observed[start:stop]).sum()),
                   observed_rows=int(sequence.observed[start:stop].sum()),
                   coordinate_discontinuities=int(np.count_nonzero(np.diff(sequence.coordinates[start:stop]) != 1)),
                   first_target_row=int(retained[0]), last_target_row=int(retained[-1]+horizon-1),
                   target_cells=int(y.size), padding=False, interpolation=False)
    return SequenceWindows(_array(x, float), _array(y, float), _array(np.isfinite(x), bool),
                           _array(np.isfinite(y), bool), _array(retained, np.int64),
                           sequence.fingerprint, canonical_json(summary))


def fit_normalization(sequence, start, stop):
    """Population moments from unique raw TRAIN rows, never window frequencies."""
    _bounds(sequence, start, stop)
    raw = sequence.values[start:stop]
    valid = raw[np.isfinite(raw)]
    if not len(valid):
        raise ValueError('No valid training normalization rows')
    mean, scale = float(valid.mean()), float(valid.std(ddof=0))
    scale = scale or 1.0
    if not np.isfinite(mean) or not np.isfinite(scale):
        raise ValueError('Normalization overflow')
    return dict(scientific_label=LABEL, unit=UNIT, policy='unique_finite_raw_train_rows_only',
                transform='identity', mean=mean, scale=scale, count=len(valid),
                raw_start=start, raw_stop=stop, support_hash=array_hash(raw))
