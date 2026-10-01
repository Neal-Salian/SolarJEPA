"""Artificial metadata fixtures test contracts, not scientific performance."""
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from solar_flare_jepa.data.goes import read_goes, backward_log_derivative
from solar_flare_jepa.data.inspect import inspect_file


def write_fixture(path, times=(0, 60, 120, 180), flux=(1e-6, 1e-5, -1, 1e-4), flags=(0, 4, 0, 0)):
    ds = xr.Dataset(coords={'time': ('time', np.array(times, dtype=float))})
    ds.time.attrs = dict(units='seconds since 2000-01-01 12:00:00 UTC',
                         long_name='Record start time. Neglects leap seconds since 2000-01-01.')
    for ch in ['xrsa', 'xrsb']:
        ds[ch+'_flux'] = ('time', np.array(flux))
        ds[ch+'_flux'].attrs = dict(units='W/m2', valid_min=1e-9, valid_max=0.2)
        ds[ch+'_flag'] = ('time', np.array(flags, dtype='u1'))
        ds[ch+'_flag'].attrs = dict(flag_meanings='good_data eclipse bad_data interpolated',
                                     flag_masks=[3,1,2,4], flag_values=[0,1,2,4])
        ds[ch+'_num'] = ('time', np.full(len(times), 60))
    ds['electron_correction_flag'] = ('time', np.zeros(len(times), dtype='u2'))
    ds['electron_correction_flag'].attrs = dict(
        flag_meanings='e_correction_valid e_correction_invalid e_correction_interp e_correction_decay xrsa_significant xrsb_significant xrsa1_significant xrsa2_significant xrsb1_significant xrsb2_significant',
        flag_masks=[1,1,6,6,8,16,32,64,128,256], flag_values=[0,1,2,4,8,16,32,64,128,256])
    ds.to_netcdf(path)


def test_cf_clock_bin_end_quality_and_source_retention(tmp_path):
    p = tmp_path/'fixture.nc'
    write_fixture(p)
    df = read_goes([p])
    assert df.index[0] == pd.Timestamp('2000-01-01T12:00:00Z')
    assert df.time_end.iloc[0] == pd.Timestamp('2000-01-01T12:01:00Z')
    assert df.xrsb_valid.tolist() == [True, False, False, True]
    assert df.xrsb_flux.isna().tolist() == [False, True, True, False]
    assert df.xrsb_flux_raw.iloc[1] == 1e-5
    assert df.source_file.iloc[0] == 'fixture.nc'


@pytest.mark.parametrize('times', [(0,0,60,120), (60,0,120,180)])
def test_rejects_duplicate_and_unsorted_times(tmp_path, times):
    p = tmp_path/'fixture.nc'
    write_fixture(p, times=times)
    with pytest.raises(ValueError, match='time'):
        read_goes([p])


def test_rejects_overlapping_files(tmp_path):
    p = tmp_path/'fixture.nc'
    write_fixture(p)
    with pytest.raises(ValueError, match='time'):
        read_goes([p,p])


@pytest.mark.parametrize('defect', ['unit','flag','epoch'])
def test_unknown_schema_fails_closed(tmp_path, defect):
    p = tmp_path/'fixture.nc'
    write_fixture(p)
    with xr.open_dataset(p, decode_times=False) as src:
        ds = src.load()
    if defect == 'unit':
        ds.xrsb_flux.attrs['units'] = 'counts'
    elif defect == 'flag':
        ds = ds.drop_vars('xrsb_flag')
    else:
        ds.time.attrs['units'] = 'seconds since 1970-01-01'
    ds.to_netcdf(p)
    with pytest.raises(ValueError):
        read_goes([p])


def test_derivative_never_bridges_gaps_or_uses_future():
    ix = pd.to_datetime(['2024-07-01T00:00Z','2024-07-01T00:01Z','2024-07-01T00:05Z','2024-07-01T00:06Z'])
    s = pd.Series([1e-6, 1e-5, 1e-4, np.nan], index=ix)
    d = backward_log_derivative(s)
    assert d.isna().tolist() == [True, False, True, True]
    assert d.iloc[1] == pytest.approx(1/60)
    s.iloc[-1] = 1.0
    pd.testing.assert_series_equal(backward_log_derivative(s).iloc[:3], d.iloc[:3])


def test_inspection_preserves_schema_without_calibration_claim(tmp_path):
    p = tmp_path/'fixture.nc'
    write_fixture(p)
    info = inspect_file(p)
    assert info['variables']['xrsb_flux']['shape'] == [4]
    assert info['variables']['xrsb_flux']['attrs']['units'] == 'W/m2'
    assert info['status'] == 'metadata_only_not_science_validation'


def test_empty_input_rejected():
    with pytest.raises(ValueError):
        read_goes([])


def test_electron_flags_are_channel_specific(tmp_path):
    p = tmp_path/'fixture.nc'
    write_fixture(p, flux=(1e-6,1e-6,1e-6,1e-6), flags=(0,0,0,0))
    with xr.open_dataset(p, decode_times=False) as src:
        ds = src.load()
    ds.electron_correction_flag.values[:] = [40,16,3,0]
    ds.to_netcdf(p)
    df = read_goes([p])
    assert df.xrsa_valid.tolist() == [False,True,False,True]
    assert df.xrsb_valid.tolist() == [True,False,False,True]
