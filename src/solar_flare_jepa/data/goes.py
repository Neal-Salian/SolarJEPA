"""Conservative GOES-R science L2 one-minute adapter, not an Aditya adapter."""
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

TIME_UNITS = 'seconds since 2000-01-01 12:00:00 UTC'


def _times(ds):
    if 'time' not in ds or ds.time.attrs.get('units') != TIME_UNITS:
        raise ValueError('Unrecognized time convention; consult product documentation')
    values = np.asarray(ds.time.values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or (values == -9999).any():
        raise ValueError('Invalid time values')
    # Product's documented leap-second-neglecting UTC convention; not TT/J2000.
    return pd.DatetimeIndex(pd.Timestamp('2000-01-01T12:00:00Z') + pd.to_timedelta(values, unit='s'))


def backward_log_derivative(flux: pd.Series, cadence_seconds=60) -> pd.Series:
    if cadence_seconds <= 0:
        raise ValueError('cadence_seconds must be positive')
    elapsed = flux.index.to_series().diff().dt.total_seconds()
    log_flux = np.log10(flux.where(flux > 0))
    return (log_flux.diff() / elapsed).where(elapsed == cadence_seconds)


def read_goes(paths: list[Path]) -> pd.DataFrame:
    if not paths:
        raise ValueError('No GOES flux files supplied')
    frames = []
    for path in paths:
        with xr.open_dataset(path, decode_times=False, engine='netcdf4') as ds:
            times = _times(ds)
            if not len(times) or not times.is_monotonic_increasing or times.has_duplicates:
                raise ValueError('time must be nonempty, sorted and unique within each flux file')
            if ds.time.attrs.get('long_name', '').split('.')[0] != 'Record start time':
                raise ValueError('Time is not documented as bin start')
            frame = pd.DataFrame(index=times)
            frame.index.name = 'time_start'
            frame['time_end'] = times + pd.Timedelta(seconds=60)
            if 'time_coverage_start' in ds.attrs:
                if times[0] != pd.Timestamp(ds.attrs['time_coverage_start']):
                    raise ValueError('time start differs from file coverage metadata')
            if 'time_coverage_end' in ds.attrs:
                if frame.time_end.iloc[-1] != pd.Timestamp(ds.attrs['time_coverage_end']):
                    raise ValueError('time end differs from file coverage metadata')
            if 'electron_correction_flag' not in ds:
                raise ValueError('Missing electron correction quality flags')
            eflag = ds.electron_correction_flag.values
            if (list(ds.electron_correction_flag.attrs.get('flag_masks', [])) != [1,1,6,6,8,16,32,64,128,256]
                    or list(ds.electron_correction_flag.attrs.get('flag_values', [])) != [0,1,2,4,8,16,32,64,128,256]):
                raise ValueError('Unknown electron correction flag schema')
            finite_eflag = np.isfinite(eflag) & (eflag >= 0) & (eflag <= 511)
            ebits = np.where(finite_eflag, eflag, 65535).astype('uint16')
            frame['electron_correction_flag'] = eflag
            for ch in ['xrsa', 'xrsb']:
                required = [ch+'_flux', ch+'_flag', ch+'_num']
                if any(k not in ds for k in required):
                    raise ValueError(f'Missing required flux/quality fields for {ch}')
                var, flag = ds[ch+'_flux'], ds[ch+'_flag']
                if var.dims != ('time',) or var.attrs.get('units') != 'W/m2':
                    raise ValueError('Expected scalar time-series irradiance in W/m2')
                if (flag.attrs.get('flag_meanings') != 'good_data eclipse bad_data interpolated'
                        or list(flag.attrs.get('flag_values', [])) != [0,1,2,4]
                        or list(flag.attrs.get('flag_masks', [])) != [3,1,2,4]):
                    raise ValueError('Unknown status flag schema; review this product version')
                values, flags, count = var.values, flag.values, ds[ch+'_num'].values
                # Invalid/interpolated/decaying correction plus significant contamination
                # for THIS primary channel. A-only contamination must not mask B.
                electron_good = finite_eflag & ((ebits & (7 | (8 if ch == 'xrsa' else 16))) == 0)
                valid = (np.isfinite(values) & (values > 0) & (flags == 0) & electron_good
                         & (count > 0) & (count <= 60))
                if 'valid_min' in var.attrs:
                    valid &= values >= var.attrs['valid_min']
                if 'valid_max' in var.attrs:
                    valid &= values <= var.attrs['valid_max']
                frame[ch+'_flux_raw'] = values
                frame[ch+'_flag'] = flags
                frame[ch+'_num'] = count
                frame[ch+'_valid'] = valid
                frame[ch+'_flux'] = np.where(valid, values, np.nan)
            for name in ['au_factor', 'xrs_primary_chan', 'yaw_flip_flag']:
                if name in ds and ds[name].dims == ('time',):
                    frame[name] = ds[name].values
            frame['source_file'] = Path(path).name
            frames.append(frame)
    result = pd.concat(frames).sort_index()
    if result.index.has_duplicates:
        raise ValueError('Duplicate time across files; choose one product version')
    intervals = result.index.to_series().diff().dt.total_seconds().dropna()
    if ((intervals < 60) | (intervals % 60 != 0)).any():
        raise ValueError('Unexpected time cadence for one-minute data')
    for ch in ['xrsa','xrsb']:
        result[ch+'_log10_flux'] = np.log10(result[ch+'_flux'])
        result[ch+'_dlog10_dt'] = backward_log_derivative(result[ch+'_flux'])
    return result


def read_event_records(paths: list[Path]) -> pd.DataFrame:
    """Return catalogue states, not training labels; duplicate event times are legal."""
    frames = []
    for path in paths:
        with xr.open_dataset(path, decode_times=False, engine='netcdf4') as ds:
            names = ['status','flare_id','flare_class','xrsb_flux']
            if any(k not in ds for k in names):
                raise ValueError('Missing event state schema')
            frame = pd.DataFrame({k:ds[k].values for k in names})
            frame['time'] = _times(ds)
            for name in ['status','flare_class']:
                frame[name] = frame[name].map(lambda v: v.decode() if isinstance(v,bytes) else str(v))
            frame['source_file'] = Path(path).name
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
