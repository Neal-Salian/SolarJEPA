"""Scientific validation and pipeline smoke of GOES development data on synthetic native fixtures."""
from datetime import date
import importlib

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from solar_flare_jepa.forecasting.contracts import TimeSeriesDataset
from test_goes import write_fixture

NS = 60_000_000_000
EPOCH = pd.Timestamp('2000-01-01T12:00:00Z')
PLAN = dict(interval=(date(2024, 5, 1), date(2024, 9, 1)))


def api():
    return importlib.import_module('solar_flare_jepa.data.goes_development_validation')


def restoration():
    return importlib.import_module('solar_flare_jepa.data.goes_restoration')


def native_day(directory, day='2024-07-01', minutes=None, defect=None):
    """A real-format native daily file with the archive's identity attributes."""
    stamp = pd.Timestamp(day, tz='UTC')
    minutes = list(range(1440)) if minutes is None else minutes
    name = f'sci_xrsf-l2-avg1m_g16_d{stamp:%Y%m%d}_v2-2-1.nc'
    path = directory / name
    offset = (stamp - EPOCH).total_seconds()
    flux = tuple(1e-6 * (1 + (m % 7)) for m in minutes)
    write_fixture(path, times=tuple(offset + 60 * m for m in minutes), flux=flux, flags=tuple(0 for _ in minutes))
    with xr.open_dataset(path, decode_times=False) as original:
        ds = original.load()
    ds.attrs.update(platform='g16', instrument=api().GOES_INSTRUMENT, title='L2 XRS 1 minute average',
                    processing_level='Level 2', time_coverage_resolution='PT1M', naming_authority='gov.nesdis.noaa',
                    id=name, time_coverage_start=f'{stamp:%Y-%m-%d}T00:00:00.000Z',
                    time_coverage_end=f'{stamp + pd.Timedelta(days=1):%Y-%m-%d}T00:00:00.000Z',
                    date_created='2025-12-05T18:40:27.237Z', algorithm='xrs04_avg.py')
    if defect == 'title':
        ds.attrs['title'] = 'L2 XRS 1 second flux'
    if defect == 'level':
        ds.attrs['processing_level'] = 'Level 1b'
    if defect == 'coverage':
        ds.attrs['time_coverage_start'] = '2024-07-02T00:00:00.000Z'
    if defect == 'offset':
        ds.attrs['time_coverage_start'] = f'{stamp:%Y-%m-%d}T00:00:00.000+05:30'
    if defect == 'units':
        ds.xrsa_flux.attrs['units'] = 'counts'
    path.unlink()
    ds.to_netcdf(path)
    if defect == 'version':
        renamed = path.with_name(name.replace('v2-2-1', 'v2-2-0'))
        path.rename(renamed)
        path = renamed
    return path, dict(path=f'x/{path.name}', nominal_date=day)


def test_native_identity_passes_for_the_official_product_and_records_provenance(tmp_path):
    path, row = native_day(tmp_path)
    result = api().native_identity(path, row)
    assert result['passed'] is True and all(result['checks'].values())
    assert result['provenance']['date_created'] == '2025-12-05T18:40:27.237Z'
    assert result['provenance']['git_commit_hash'] is None   # absent attributes stay unknown, never invented


@pytest.mark.parametrize('defect,check', [('title', 'title'), ('level', 'processing_level'),
                                          ('coverage', 'coverage_start_is_nominal_day'),
                                          ('offset', 'coverage_start_is_nominal_day'),
                                          ('units', 'flux_units_w_m2'), ('version', 'filename_version')])
def test_native_identity_flags_wrong_product_level_version_coverage_or_units(tmp_path, defect, check):
    path, row = native_day(tmp_path, defect=defect)
    result = api().native_identity(path, row)
    assert result['passed'] is False and result['checks'][check] is False


def test_missing_timestamps_are_counted_never_filled(tmp_path):
    foundation = importlib.import_module('solar_flare_jepa.data.foundation')
    kept = [m for m in range(1440) if not 100 <= m < 130]
    path, _ = native_day(tmp_path, minutes=kept)
    frame, report = foundation.validate_goes_files([path], start_utc='2024-07-01T00:00:00Z',
                                                   end_utc='2024-07-02T00:00:00Z')
    summary = api().quality_summary(frame)
    assert summary['missing_bins'] == report['missing_bins'] == 30
    assert summary['observed_bins'] == 1410 and summary['observed_bins_per_day']['days_below_1440'] == 1
    assert summary['xrsa']['valid_samples_1_to_59'] == summary['xrsa']['valid_samples_lt_30'] == 0
    assert frame['xrsa_flux'].iloc[100:130].isna().all()   # absent bins stay absent


def test_partial_sample_counts_distinguish_observed_from_valid_bins(tmp_path):
    # Review F1: valid-bin partial-sample counts are computed, not only observed-bin counts.
    foundation = importlib.import_module('solar_flare_jepa.data.foundation')
    path, _ = native_day(tmp_path)
    with xr.open_dataset(path, decode_times=False) as original:
        ds = original.load()
    ds['xrsa_num'].values[:5] = [10, 45, 59, 60, 0]
    ds['xrsa_flag'].values[1] = 2   # bad data: observed partial-sample bin that is not valid
    path.unlink()
    ds.to_netcdf(path)
    frame, _ = foundation.validate_goes_files([path], start_utc='2024-07-01T00:00:00Z',
                                              end_utc='2024-07-02T00:00:00Z')
    a = api().quality_summary(frame)['xrsa']
    assert (a['samples_1_to_59'], a['valid_samples_1_to_59'], a['valid_samples_lt_30']) == (3, 2, 1)
    assert a['samples_zero_or_invalid'] == 1


def test_duplicate_or_off_grid_timestamps_are_rejected(tmp_path):
    foundation = importlib.import_module('solar_flare_jepa.data.foundation')
    path, _ = native_day(tmp_path, minutes=[0, 1, 1, 2])
    with pytest.raises(ValueError):
        foundation.validate_goes_files([path], start_utc='2024-07-01T00:00:00Z', end_utc='2024-07-02T00:00:00Z')


def synthetic_dataset(days=3, start='2024-07-01'):
    begin = pd.Timestamp(start, tz='UTC').value
    starts = begin + NS * np.arange(days * 1440, dtype=np.int64)
    t = np.arange(len(starts))
    values = np.column_stack((1e-7 * (2 + np.sin(t / 50.)), 1e-6 * (2 + np.cos(t / 70.))))
    mask = np.ones_like(values, bool)
    mask[500:510, 0] = False
    names, units = ('xrsa_flux', 'xrsb_flux'), ('W/m2', 'W/m2')
    return TimeSeriesDataset('synthetic', 'synthetic_fixture', starts, starts + NS, values, mask, values, mask.copy(),
                             names, names, units, units, 60, availability_policy='bin_end_earliest')


def config(splits=None):
    forecast = dict(cadence_seconds=60, context_steps=120, horizon_steps=30, stride_steps=30,
                    feature_names=['xrsa_flux', 'xrsb_flux'], target_names=['xrsa_flux', 'xrsb_flux'],
                    feature_units=['W/m2', 'W/m2'], target_units=['W/m2', 'W/m2'],
                    availability_mode='retrospective_bin_end', eligibility_policy='complete', transform='log10',
                    feature_reference=[1., 1.], target_reference=[1., 1.], target_minimum=[0., 0.])
    splits = splits or [dict(name='train', start_utc='2024-07-01T00:00:00Z', end_utc='2024-07-02T12:00:00Z'),
                        dict(name='validation', start_utc='2024-07-02T12:00:00Z', end_utc='2024-07-03T06:00:00Z'),
                        dict(name='test', start_utc='2024-07-03T06:00:00Z', end_utc='2024-07-04T00:00:00Z')]
    return dict(forecast=forecast, splits=splits)


def test_pipeline_smoke_builds_only_development_windows_with_train_only_normalization(monkeypatch):
    pytest.importorskip('torch')
    module = api()
    windows = importlib.import_module('solar_flare_jepa.forecasting.windows')
    built = []
    original = windows.build_partition_windows
    monkeypatch.setattr(windows, 'build_partition_windows',
                        lambda dataset, spec, partition, *a: (built.append(partition.name), original(dataset, spec, partition, *a))[1])
    result = module.pipeline_smoke_from_dataset(synthetic_dataset(), config(), PLAN, max_train_windows=256)
    assert set(built) == {'train', 'validation'} and result['test_windows_built'] is False
    assert result['built_partitions'] == ['train', 'validation']
    for split in result['splits'].values():
        assert split['deterministic'] and split['context_inside'] and split['targets_inside']
        assert split['retained_origins'] > 0
    assert result['validation_starts_after_training']
    assert result['normalization']['equals_independent_train_only'] is True
    assert result['normalization']['differs_from_train_plus_validation'] is True
    assert result['shapes']['validation_context'][1:] == [120, 2] and result['shapes']['validation_targets'][1:] == [30, 2]
    v2 = result['v2_preparation']
    assert v2['normalization_matches'] and v2['train_windows']['used'] == 256
    assert v2['train_window_shape'][1:] == [150, 2] and v2['validation_tensor_shapes']['features'][1:] == [120, 2]


def test_pipeline_smoke_rejects_splits_outside_the_authorized_interval():
    bad = config()['splits']
    bad[-1] = dict(bad[-1], end_utc='2024-09-02T00:00:00Z')
    with pytest.raises(restoration().UnauthorizedSelection):
        api().pipeline_smoke_from_dataset(synthetic_dataset(), config(bad), PLAN)


def test_pipeline_smoke_rejects_configs_requesting_unplanned_manifests(tmp_path):
    import json
    plan = dict(PLAN, manifests=[dict(path='data/manifests/goes_v1_202405.json')])
    path = tmp_path / 'experiment.json'
    path.write_text(json.dumps(dict(dataset=dict(kind='goes_historical_multi',
                                                 manifests=['data/manifests/goes_v1_202405.json',
                                                            'data/manifests/goes_external_january2025.json']))))
    with pytest.raises(restoration().UnauthorizedSelection, match='outside the restoration plan'):
        api().pipeline_smoke(plan, path, tmp_path)
