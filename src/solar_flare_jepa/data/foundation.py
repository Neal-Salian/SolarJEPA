"""Source-specific historical data foundation; native SoLEXS remains gated."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
import xarray as xr

from .download import sha256_file
from .goes import _times, read_goes
from .storage import repository_relative_path
from solar_flare_jepa.forecasting.contracts import TimeSeriesDataset, canonical_json


GOES_INSTRUMENT = 'GOES R Series Extreme Ultraviolet Sensor and X-ray Irradiance Sensors (EXIS)'
GOES_TIME = ('GOES documented UTC convention neglecting leap seconds; index=bin start, '
             'available at time_end at earliest; operational latency unknown')
GOES_QUALITY = 'strict_status_zero_and_channel_specific_electron_bits'


@dataclass(frozen=True)
class SourceIdentity:
    """Common metadata contract, without a common numeric scale or clock."""
    mission: str
    platform: str
    instrument: str
    channels: tuple[str, ...]
    native_units: tuple[str, ...]
    time_basis: str
    sampling: str
    measurement_type: str
    quality_status: str
    preprocessing: str
    validation_status: str
    target_definition: str

    def __post_init__(self):
        for name in ('mission', 'platform', 'instrument', 'time_basis', 'sampling',
                     'measurement_type', 'quality_status', 'preprocessing',
                     'validation_status', 'target_definition'):
            if type(getattr(self, name)) is not str or not getattr(self, name).strip():
                raise ValueError(f'Explicit {name} is required; use UNKNOWN when unresolved')
        for name in ('channels', 'native_units'):
            values = tuple(getattr(self, name))
            if not values or any(type(x) is not str or not x.strip() for x in values):
                raise ValueError('Explicit channel/unit identities are required')
            object.__setattr__(self, name, values)
        if len(self.channels) != len(self.native_units) or len(set(self.channels)) != len(self.channels):
            raise ValueError('Channel/unit identity mismatch')
        if self.validation_status not in ('OBSERVED_NATIVE', 'EXPERIMENTAL_UNCALIBRATED',
                                          'SCIENTIFICALLY_VALIDATED'):
            raise ValueError('Unknown scientific validation status')
        if self.instrument == 'SoLEXS' and self.validation_status == 'SCIENTIFICALLY_VALIDATED':
            raise ValueError('SoLEXS remains BLOCKED_FOR_PHASE_E')

    def as_dict(self):
        return asdict(self)

    def require_training_clearance(self):
        if (self.mission != 'NOAA GOES-R' or self.platform != 'GOES-16'
                or self.instrument != 'EXIS/XRS' or self.measurement_type != 'irradiance'
                or any(x != 'W/m2' for x in self.native_units)
                or any(x not in ('xrsa_flux', 'xrsb_flux') for x in self.channels)):
            raise ValueError('Unsupported training identity; SoLEXS remains BLOCKED_FOR_PHASE_E')

    def assert_compatible(self, other):
        if type(other) is not SourceIdentity or self != other:
            raise ValueError('Incompatible source identities; no cross-instrument conversion established')

    def convert_units(self, unit):
        if any(value != unit for value in self.native_units):
            raise ValueError('Unsupported unit conversion; calibration/response evidence required')
        return self


def _missing_intervals(index, observed):
    absent = np.flatnonzero(~observed)
    groups = np.split(absent, np.flatnonzero(np.diff(absent) != 1)+1) if len(absent) else []
    return [dict(start_utc=index[g[0]].isoformat(),
                 end_utc=(index[g[-1]]+pd.Timedelta(minutes=1)).isoformat(), bins=len(g))
            for g in groups]


def validate_goes_files(paths, *, start_utc, end_utc, platform='GOES-16'):
    """Validate native files, then represent absent bins explicitly on a grid.

    No native timestamp is moved and no observation is filled. `observed=False`
    identifies grid bins absent in the selected files. P1 windows apply the
    quality masks and exclude/retain incomplete origins according to their spec.
    """
    from solar_flare_jepa.experiments.config import utc_ns
    start, end = [pd.Timestamp(utc_ns(x), tz='UTC') for x in (start_utc, end_utc)]
    if platform != 'GOES-16' or start >= end or start.value % 60_000_000_000 or end.value % 60_000_000_000:
        raise ValueError('Expected GOES-16 and ordered minute-aligned UTC interval')
    if not paths:
        raise ValueError('No observed GOES files supplied')
    previous = None
    for path in paths:
        with xr.open_dataset(path, decode_times=False, engine='netcdf4') as ds:
            if ds.attrs.get('platform') != 'g16' or ds.attrs.get('instrument') != GOES_INSTRUMENT:
                raise ValueError('Native GOES platform/instrument identity mismatch')
            if ds.attrs.get('id') != Path(path).name:
                raise ValueError('Native product id differs from pinned filename/version/date')
            times = _times(ds)
            if (not len(times) or not times.is_monotonic_increasing or times.has_duplicates
                    or previous is not None and times[0] <= previous):
                raise ValueError('Native time/files must be nonempty, chronologically ordered and unique')
            previous = times[-1]
            if ((times.asi8-start.value) % 60_000_000_000 != 0).any():
                raise ValueError('Native timestamps are off the selected minute cadence grid')
            if times[0] < start or times[-1]+pd.Timedelta(minutes=1) > end:
                raise ValueError('Native observations outside selected interval')
            name = Path(path).name
            if name.startswith('sci_xrsf-l2-avg1m_'):
                match = re.fullmatch(r'sci_xrsf-l2-avg1m_g16_d(\d{8})_v2-2-1\.nc', name)
                if match is None:
                    raise ValueError('Unsupported native product filename/version')
                nominal_day = pd.Timestamp(match[1], tz='UTC')
                if times[0] < nominal_day or times[-1]+pd.Timedelta(minutes=1) > nominal_day+pd.Timedelta(days=1):
                    raise ValueError('Native time coverage contradicts the nominal source day')
            for name in ('electron_correction_flag', 'xrsa_flag', 'xrsb_flag', 'xrsa_num', 'xrsb_num'):
                if name not in ds or ds[name].dims != ('time',):
                    raise ValueError('Missing scalar native quality/count field')
                values = np.asarray(ds[name].values)
                finite = np.isfinite(values)
                if (values[finite] != np.floor(values[finite])).any():
                    raise ValueError('Noninteger native quality/count field')
    native = read_goes(list(paths))
    index = pd.date_range(start, end, freq='min', inclusive='left', name='time_start')
    observed = index.isin(native.index)
    if int(observed.sum()) != len(native):
        raise ValueError('Native observation conservation failed; reindex would discard measurements')
    frame = native.reindex(index)
    frame['time_end'] = index+pd.Timedelta(minutes=1)
    frame['observed'] = observed
    channels = {}
    for ch in ('xrsa', 'xrsb'):
        frame[ch+'_valid'] = frame[ch+'_valid'].eq(True)
        raw = native[ch+'_flux_raw'].to_numpy(float)
        channels[ch] = dict(units='W/m2', valid_bins=int(native[ch+'_valid'].sum()),
            quality_rejected_bins=int((~native[ch+'_valid']).sum()),
            nonfinite_raw_bins=int((~np.isfinite(raw)).sum()),
            nonpositive_raw_bins=int((np.isfinite(raw) & (raw <= 0)).sum()),
            status_flag_counts={str(k): int(v) for k,v in native[ch+'_flag'].value_counts(dropna=False).items()},
            electron_quality_policy=GOES_QUALITY)
    report = dict(status='VALIDATED_NATIVE_GOES_CONTRACT', evidence='OBSERVED',
        platform=platform, instrument='EXIS/XRS', start_utc=start.isoformat(), end_utc=end.isoformat(),
        observed_start_utc=native.index[0].isoformat(), observed_end_utc=native.time_end.iloc[-1].isoformat(),
        observed_rows=len(native), grid_rows=len(frame), missing_bins=int((~observed).sum()),
        missing_intervals=_missing_intervals(index, observed), cadence_seconds=60,
        chronological_order='PASS', duplicate_timestamps=0, nonuniform_cadence='none except reported absent bins',
        channels=channels, imputation='none', normalization='none', availability='retrospective_bin_end',
        actual_operational_delivery='UNKNOWN', event_labels=dict(status='NOT_DEFINED',
            reason='Continuous native flux task; no flare catalogue-to-label rule has been established'),
        primary_detector_selector_counts=({str(k): int(v) for k,v in native.xrs_primary_chan.value_counts().items()}
            if 'xrs_primary_chan' in native else 'UNKNOWN'))
    return frame, report


def _pinned_frame(relative, root):
    """Verify one pinned bounded selection and validate its native files."""
    from solar_flare_jepa.experiments.config import read_finite_json
    from .goes_acquisition import verify_history
    manifest = root/repository_relative_path(relative, root)
    inventory = read_finite_json(manifest)
    paths = verify_history(manifest, root)
    interval = inventory['selected_interval']
    start = pd.Timestamp(interval['start'], tz='UTC').isoformat()
    end = pd.Timestamp(interval['end_exclusive'], tz='UTC').isoformat()
    frame, report = validate_goes_files(paths, start_utc=start, end_utc=end, platform=inventory['platform'])
    return manifest, inventory, paths, frame, report


def goes_training(config, root):
    """Rebuild from pinned raw identities; never trust a prepared cache alone.

    `goes_historical_multi` concatenates several independently pinned
    selections only when their declared intervals are exactly contiguous, so
    the combined grid has no silently bridged time.
    """
    from solar_flare_jepa.experiments.config import validate_config
    cfg = validate_config(config)
    kind = cfg['dataset']['kind']
    if kind not in ('goes_historical', 'goes_historical_multi'):
        raise ValueError('Historical adapter requires goes_historical')
    root = Path(root).resolve()
    selections = [_pinned_frame(value, root) for value in
                  ([cfg['dataset']['manifest']] if kind == 'goes_historical' else cfg['dataset']['manifests'])]
    return _goes_dataset(selections, root, kind)


def _goes_dataset(selections, root, kind):
    """Assemble already verified selections without inventing a test partition.

    Shared by the unchanged V1 loader and the separately pinned V2 development
    loader. Native validation and manifest access remain the callers' concerns;
    this preserves the historical dataset's exact semantic identity construction.
    """
    for (_, _, _, left, _), (_, _, _, right, _) in zip(selections, selections[1:]):
        if left['time_end'].iloc[-1] != right.index[0]:
            raise ValueError('Multi-manifest GOES selections must be chronologically contiguous')
    if len({s[1]['platform'] for s in selections}) != 1:
        raise ValueError('Multi-manifest GOES selections must share one platform')
    if kind == 'goes_historical':
        manifest, inventory, paths, frame, report = selections[0]
        dataset_id, manifest_sha256 = inventory['dataset_id'], sha256_file(manifest)
    else:
        frame = pd.concat([s[3] for s in selections])
        paths = [p for s in selections for p in s[2]]
        report = [s[4] for s in selections]
        dataset_id = '+'.join(s[1]['dataset_id'] for s in selections)
        manifest_sha256 = [dict(path=repository_relative_path(s[0], root), sha256=sha256_file(s[0]))
                           for s in selections]
    channels = ('xrsa_flux', 'xrsb_flux')
    identity = SourceIdentity('NOAA GOES-R', 'GOES-16', 'EXIS/XRS', channels, ('W/m2', 'W/m2'),
        GOES_TIME, '60 s record-start half-open bins', 'irradiance', GOES_QUALITY, 'none',
        'OBSERVED_NATIVE', 'future electron-corrected primary XRS-A and XRS-B flux bins')
    identity.require_training_clearance()
    sources = [dict(path=repository_relative_path(p, root), sha256=sha256_file(p), bytes=p.stat().st_size)
               for p in paths]
    metadata = dict(adapter='p2_goes16_native_flux_v1', source_identity=identity.as_dict(),
        sources=sources, manifest_sha256=manifest_sha256, raw_validation=report,
        channel_bands_nm={'xrsa_flux': [0.05, 0.4], 'xrsb_flux': [0.1, 0.8]},
        detector_selection='primary composite; native per-bin xrs_primary_chan retained in preparation',
        scientific_role='GOES retrospective flux forecasting; not Aditya-L1',
        operational_latency='UNKNOWN', imputation='none', normalization='none', phase_e='BLOCKED_FOR_PHASE_E')
    values = frame[list(channels)].to_numpy(float)
    mask = frame[['xrsa_valid', 'xrsb_valid']].to_numpy(bool)
    return TimeSeriesDataset(dataset_id, 'goes_historical', frame.index.asi8,
        pd.DatetimeIndex(frame.time_end).asi8, values, mask, values, mask, channels, channels,
        ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), 60, availability_policy='bin_end_earliest',
        time_policy=GOES_TIME, quality_policy=GOES_QUALITY, metadata_json=canonical_json(metadata))


def prepare_foundation(config_path, root, output_dir):
    """Materialize regenerable native table plus split/window reports, exclusively."""
    from solar_flare_jepa.experiments.config import load_config, utc_ns
    from solar_flare_jepa.experiments.provenance import atomic_record, code_provenance, verify_source_identities
    from solar_flare_jepa.forecasting.contracts import ForecastSpec
    from solar_flare_jepa.forecasting.splitting import chronological_partitions
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    root = Path(root).resolve()
    cfg_path = Path(config_path)
    if not cfg_path.is_absolute():
        cfg_path = root/cfg_path
    cfg = load_config(cfg_path)
    provenance = code_provenance(root)
    dataset = goes_training(cfg, root)
    metadata = json.loads(dataset.metadata_json)
    inventory = json.loads((root/cfg['dataset']['manifest']).read_text())
    from .goes_acquisition import verify_history
    frame, report = validate_goes_files(verify_history(root/cfg['dataset']['manifest'], root),
        start_utc=pd.Timestamp(inventory['selected_interval']['start'], tz='UTC').isoformat(),
        end_utc=pd.Timestamp(inventory['selected_interval']['end_exclusive'], tz='UTC').isoformat())
    spec = ForecastSpec(**cfg['forecast'])
    partitions = chronological_partitions(dataset, [dict(name=p['name'], start_ns=utc_ns(p['start_utc']),
        end_ns=utc_ns(p['end_utc'])) for p in cfg['splits']])
    windows = {p.name: build_partition_windows(dataset, spec, p) for p in partitions}
    summary = dict(schema_version=1, dataset_fingerprint=dataset.fingerprint, identity=metadata['source_identity'],
        validation=report, forecast=spec.as_dict(), splits=[dict(**p.as_dict(),
            raw_bins=int(((dataset.starts_ns >= p.start_ns) & (dataset.ends_ns <= p.end_ns)).sum()),
            valid_forecast_origins=len(windows[p.name].retained_origins),
            excluded_forecast_origins=len(windows[p.name].excluded_origins)) for p in partitions],
        training_fingerprint=windows['train'].training_slice.fingerprint,
        target_transform='log10(F / (1 W/m2)); model outputs inverted to W/m2',
        scaler_policy='only unique raw training observations; neural checkpoint records fitted statistics',
        baseline_selection='fixed before held-out evaluation', status='GOES_FOUNDATION_PREPARED')
    # Reuse P1's finite-JSON-only immutable publisher without weakening its
    # artifact protections. NaNs remain represented by null plus false masks.
    contents = {'dataset.json': dataset.semantic_content(), 'summary.json': summary,
        'native_diagnostics.json': json.loads(frame.reset_index().to_json(orient='split', date_format='iso')),
        'split_manifest.json': dict(partitions=[w.manifest() for w in windows.values()]),
        'provenance.json': provenance, 'resolved_config.json': cfg}
    verify_source_identities(root, provenance['source']['files'])
    atomic_record(root, output_dir, contents)
    return summary
