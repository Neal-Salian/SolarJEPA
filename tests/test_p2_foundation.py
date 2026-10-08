"""Offline native fixtures prove P2 policies, not solar forecasting skill."""
import importlib
import importlib.util
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from solar_flare_jepa.experiments.config import validate_config
from solar_flare_jepa.forecasting.contracts import ForecastSpec
from solar_flare_jepa.forecasting.splitting import chronological_partitions
from solar_flare_jepa.forecasting.windows import build_partition_windows
from test_goes import write_fixture


def foundation():
    name = 'solar_flare_jepa.data.foundation'
    assert importlib.util.find_spec(name) is not None, 'P2 historical foundation is not implemented'
    return importlib.import_module(name)


def native_file(path, times=(0, 60, 180, 240), defect=None):
    write_fixture(path, times=times, flux=(1e-6, 1e-5, 1e-4, 1e-3), flags=(0, 4, 0, 0))
    with xr.open_dataset(path, decode_times=False) as original:
        ds = original.load()
    ds.attrs.update(platform='g16', instrument='GOES R Series Extreme Ultraviolet Sensor and X-ray Irradiance Sensors (EXIS)')
    if defect == 'platform':
        ds.attrs['platform'] = 'GOES-18'
    if defect == 'instrument':
        ds.attrs['instrument'] = 'SoLEXS'
    if defect == 'unit':
        ds.xrsb_flux.attrs['units'] = 'counts'
    if defect == 'nonfinite':
        ds.xrsb_flux.values[2] = np.inf
    if defect == 'fractional_quality':
        ds['electron_correction_flag'] = ds.electron_correction_flag.astype(float)
        ds.electron_correction_flag.values[2] = 0.5
    ds.to_netcdf(path)


def test_absent_bins_are_nan_with_false_masks_and_reported(tmp_path):
    path = tmp_path/'fixture.nc'
    native_file(path)
    frame, report = foundation().validate_goes_files([path], start_utc='2000-01-01T12:00:00Z',
        end_utc='2000-01-01T12:05:00Z', platform='GOES-16')
    assert len(frame) == 5
    assert frame.observed.tolist() == [True, True, False, True, True]
    assert frame.xrsb_valid.tolist() == [True, False, False, True, True]
    assert np.isnan(frame.xrsb_flux.iloc[2])
    assert np.isnan(frame.xrsb_flux_raw.iloc[2])
    assert report['missing_bins'] == 1
    assert report['observed_rows'] == 4
    assert report['missing_intervals'][0]['start_utc'] == '2000-01-01T12:02:00+00:00'
    assert report['channels']['xrsb']['quality_rejected_bins'] == 1
    assert report['event_labels']['status'] == 'NOT_DEFINED'


@pytest.mark.parametrize('defect', ['platform', 'instrument', 'unit', 'fractional_quality'])
def test_unsupported_native_identity_and_semantics_rejected(tmp_path, defect):
    path = tmp_path/'fixture.nc'
    native_file(path, defect=defect)
    with pytest.raises(ValueError):
        foundation().validate_goes_files([path], start_utc='2000-01-01T12:00:00Z',
            end_utc='2000-01-01T12:05:00Z', platform='GOES-16')


@pytest.mark.parametrize('times', [(60, 0, 180, 240), (0, 60, 60, 240), (0, 60, 170, 240)])
def test_disorder_duplicates_and_nonuniform_native_cadence_rejected(tmp_path, times):
    path = tmp_path/'fixture.nc'
    native_file(path, times=times)
    with pytest.raises(ValueError):
        foundation().validate_goes_files([path], start_utc='2000-01-01T12:00:00Z',
            end_utc='2000-01-01T12:05:00Z', platform='GOES-16')


def test_nonfinite_flux_masked_and_counted_without_imputation(tmp_path):
    path = tmp_path/'fixture.nc'
    native_file(path, defect='nonfinite')
    frame, report = foundation().validate_goes_files([path], start_utc='2000-01-01T12:00:00Z',
        end_utc='2000-01-01T12:05:00Z', platform='GOES-16')
    assert np.isnan(frame.xrsb_flux.iloc[3])
    assert not frame.xrsb_valid.iloc[3]
    assert report['channels']['xrsb']['nonfinite_raw_bins'] == 1


def historical_config():
    return json.loads((__import__('pathlib').Path(__file__).resolve().parents[1] /
        'configs/experiments/p1_goes_reference.json').read_text())


def test_historical_config_retains_source_identity_and_both_channels():
    cfg = historical_config()
    cfg['dataset'] = dict(kind='goes_historical', manifest='data/manifests/goes_p2_july2024.json')
    cfg['forecast'].update(feature_names=['xrsa_flux', 'xrsb_flux'],
        target_names=['xrsa_flux', 'xrsb_flux'], feature_units=['W/m2', 'W/m2'],
        target_units=['W/m2', 'W/m2'], feature_reference=[1.0, 1.0],
        target_reference=[1.0, 1.0], target_minimum=[0.0, 0.0])
    cfg['metrics']['target_weights'] = [1, 1]
    result = validate_config(cfg)
    assert result['dataset']['kind'] == 'goes_historical'
    assert result['forecast']['target_names'] == ['xrsa_flux', 'xrsb_flux']
    cfg['forecast']['target_units'][0] = 'counts'
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_sources_cannot_mix_convert_or_bypass_native_science_gate():
    cls = foundation().SourceIdentity
    goes = cls(mission='NOAA GOES-R', platform='GOES-16', instrument='EXIS/XRS',
        channels=('xrsa_flux', 'xrsb_flux'), native_units=('W/m2', 'W/m2'),
        time_basis='NOAA documented UTC neglecting leap seconds', sampling='60 s record-start bins',
        measurement_type='irradiance', quality_status='native_flags_applied',
        preprocessing='none', validation_status='OBSERVED_NATIVE',
        target_definition='future primary-channel flux bins')
    native = cls(mission='ISRO Aditya-L1', platform='Aditya-L1', instrument='SoLEXS',
        channels=('SDD2 native light curve',), native_units=('native FITS column units',),
        time_basis='native TIME; absolute UTC UNKNOWN', sampling='native rows; bin semantics UNKNOWN',
        measurement_type='detector-space light curve', quality_status='UNKNOWN',
        preprocessing='none', validation_status='OBSERVED_NATIVE', target_definition='NONE')
    goes.require_training_clearance()
    with pytest.raises(ValueError, match='BLOCKED_FOR_PHASE_E'):
        native.require_training_clearance()
    with pytest.raises(ValueError, match='incompatible|Incompatible'):
        goes.assert_compatible(native)
    with pytest.raises(ValueError):
        native.convert_units('W/m2')
    assert native.as_dict()['platform'] == 'Aditya-L1'


def test_historical_windows_use_p1_partition_support_and_no_future_overlap():
    module = foundation()
    from solar_flare_jepa.forecasting.contracts import TimeSeriesDataset
    starts = np.arange(60, dtype=np.int64)*60_000_000_000
    vals = np.full((60, 2), 1e-6)
    masks = np.ones_like(vals, dtype=bool)
    data = TimeSeriesDataset('offline_goes', 'goes_historical', starts, starts+60_000_000_000,
        vals, masks, vals, masks, ('xrsa_flux', 'xrsb_flux'), ('xrsa_flux', 'xrsb_flux'),
        ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), 60, availability_policy='bin_end_earliest')
    spec = ForecastSpec(60, 4, 2, data.feature_names, data.target_names,
        data.feature_units, data.target_units, stride_steps=2, availability_mode='retrospective_bin_end')
    parts = chronological_partitions(data, [dict(name=name, start_ns=i*20*spec.cadence_ns,
        end_ns=(i+1)*20*spec.cadence_ns) for i,name in enumerate(['train', 'validation', 'test'])])
    windows = [build_partition_windows(data, spec, p) for p in parts]
    for window, part in zip(windows, parts):
        assert (window.context.ends_ns <= window.context.issue_times_ns[:, None]).all()
        assert (window.targets.grid.ends_ns <= part.end_ns).all()
        assert (window.context.starts_ns >= part.start_ns).all()
    assert windows[0].targets.grid.ends_ns.max() <= windows[1].targets.grid.starts_ns.min()
    assert windows[1].targets.grid.ends_ns.max() <= windows[2].targets.grid.starts_ns.min()
    assert windows[0].training_slice.raw_targets.shape == (20, 2)


def offline_history(tmp_path, monkeypatch):
    """HTTP boundary supplies a real-format artificial native NetCDF file."""
    from test_goes_acquisition import config, Response
    from solar_flare_jepa.data import goes_acquisition as acquisition
    source = tmp_path/'native.nc'
    offset = (pd.Timestamp('2024-07-01T00:00:00Z')-pd.Timestamp('2000-01-01T12:00:00Z')).total_seconds()
    native_file(source, times=tuple(offset+x for x in (0, 60, 180, 240)))
    path, selection = config(tmp_path, days=1)
    selection['max_total_bytes'] = 1048576
    selection['files'][0]['max_bytes'] = 1048576
    path.write_text(json.dumps(selection))
    payload = source.read_bytes()
    monkeypatch.setattr(acquisition, 'open_history_url', lambda url, timeout: Response(payload))
    inventory = acquisition.acquire_history(path, tmp_path)
    cfg = historical_config()
    cfg['dataset'] = dict(kind='goes_historical', manifest=selection['manifest_path'])
    return cfg, inventory


def test_pinned_historical_adapter_preserves_identity_nan_and_provenance(tmp_path, monkeypatch):
    cfg, inventory = offline_history(tmp_path, monkeypatch)
    dataset = foundation().goes_training(cfg, tmp_path)
    assert len(dataset.starts_ns) == 1440
    assert dataset.feature_mask[:5, 1].tolist() == [True, False, False, True, True]
    assert np.isnan(dataset.features[2]).all()
    assert dataset.availability_ns is None
    metadata = json.loads(dataset.metadata_json)
    assert metadata['source_identity']['platform'] == 'GOES-16'
    assert metadata['source_identity']['native_units'] == ['W/m2', 'W/m2']
    assert metadata['sources'][0]['sha256'] == inventory['files'][0]['sha256']
    assert metadata['raw_validation']['missing_bins'] == 1436
    assert str(tmp_path) not in dataset.metadata_json


def test_adapter_rechecks_raw_identity_and_refuses_corruption(tmp_path, monkeypatch):
    cfg, inventory = offline_history(tmp_path, monkeypatch)
    foundation().goes_training(cfg, tmp_path)
    raw = tmp_path/inventory['files'][0]['path']
    raw.write_bytes(raw.read_bytes()+b'corruption')
    with pytest.raises(ValueError):
        foundation().goes_training(cfg, tmp_path)


@pytest.mark.parametrize('manifest', ['/tmp/outside.json', '../other.json',
                                     'data/manifests/../other.json', 'data//manifests/a.json'])
def test_historical_config_rejects_nonportable_manifest(manifest):
    cfg = historical_config()
    cfg['dataset'] = dict(kind='goes_historical', manifest=manifest)
    with pytest.raises(ValueError):
        validate_config(cfg)
