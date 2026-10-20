"""Gap-preserving descriptive analysis of the four pinned V1 GOES selections."""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.data.eda import summarize
from solar_flare_jepa.data.foundation import validate_goes_files
from solar_flare_jepa.data.goes_acquisition import verify_history

V1_CONFIG = 'configs/experiments/v1_goes_2024.json'
CHANNELS = ('xrsa', 'xrsb')


def load_v1_frame(root):
    """Hash-verify exactly V1's explicit manifests, never discover other datasets."""
    root = Path(root).resolve()
    config = json.loads((root / V1_CONFIG).read_text())
    paths, manifests = [], []
    for relative in config['dataset']['manifests']:
        manifest = root / relative
        selected = verify_history(manifest, root)
        paths.extend(selected)
        manifests.append(dict(path=relative, sha256=sha256_file(manifest), files=len(selected),
                              bytes=sum(p.stat().st_size for p in selected)))
    frame, quality = validate_goes_files(paths, start_utc=config['splits'][0]['start_utc'],
                                        end_utc=config['splits'][-1]['end_utc'])
    # Promote before logarithms: native float32 values remain exactly represented.
    for ch in CHANNELS:
        frame[ch + '_flux'] = frame[ch + '_flux'].astype(float)
    descriptive = summarize(frame)
    # Historical EDA uses "exposure_count"; native metadata says averaged measurements.
    for row in descriptive['channels'].values():
        row['averaged_measurements_min'] = row.pop('exposure_count_min')
        row['averaged_measurements_max'] = row.pop('exposure_count_max')
    evidence = dict(config_path=V1_CONFIG, config_sha256=sha256_file(root / V1_CONFIG),
                    manifests=manifests, source_files=len(paths),
                    source_bytes=sum(p.stat().st_size for p in paths),
                    native_contract=quality, descriptive=descriptive)
    return frame, evidence


def longest_complete_block(frame, start, end):
    """Earliest longest positive, finite two-channel minute run in [start,end)."""
    def utc(value):
        t = pd.Timestamp(value)
        return t.tz_localize('UTC') if t.tzinfo is None else t.tz_convert('UTC')
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError('Expected sorted unique timestamps')
    selected = frame.loc[(frame.index >= utc(start)) & (frame.index < utc(end))]
    values = selected[['xrsa_flux', 'xrsb_flux']].to_numpy(float)
    good = np.isfinite(values).all(axis=1) & (values > 0).all(axis=1)
    runs, first = [], None
    for i, valid in enumerate(good):
        consecutive = i == 0 or selected.index[i].value - selected.index[i - 1].value == 60_000_000_000
        if first is not None and (not valid or not consecutive):
            runs.append((first, i)); first = None
        if valid and first is None:
            first = i
    if first is not None:
        runs.append((first, len(selected)))
    if not runs:
        raise ValueError('No complete contiguous training block')
    a, b = max(runs, key=lambda r: r[1] - r[0])
    return selected.iloc[a:b].copy()


def _check_block(block):
    if (len(block) < 200 or block.index.has_duplicates
            or not (np.diff(block.index.asi8) == 60_000_000_000).all()):
        raise ValueError('Diagnostics require at least 200 contiguous minute rows')
    values = block[['xrsa_flux', 'xrsb_flux']].to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Diagnostics require finite positive complete observations')


def stationarity_analysis(block):
    """ADF fixed lags and complementary level-KPSS, never concatenate across gaps."""
    from statsmodels.tsa.stattools import adfuller, kpss
    _check_block(block)
    rows = []
    for ch in CHANNELS:
        raw = block[ch + '_flux'].to_numpy(float)
        log = np.log10(raw)
        series = dict(raw_scaled=raw / raw.mean(), log_level=log, log_difference=np.diff(log))
        for name, values in series.items():
            adf = adfuller(values, maxlag=30, regression='c', autolag=None)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                kp = kpss(values, regression='c', nlags='auto')
            relation = '<' if kp[1] == .01 else '>' if kp[1] == .1 else '='
            sensitivity = {}
            for lag in (10, 60):
                a = adfuller(values, maxlag=lag, regression='c', autolag=None)
                sensitivity[str(lag)] = dict(statistic=float(a[0]), p_value=float(a[1]), nobs=int(a[3]))
            rows.append(dict(channel=ch, transform=name, input_rows=len(values),
                start_utc=(block.index[1] if name == 'log_difference' else block.index[0]).isoformat(),
                end_exclusive_utc=(block.index[-1] + pd.Timedelta(minutes=1)).isoformat(),
                adf_statistic=float(adf[0]), adf_p_value=float(adf[1]), adf_lags=int(adf[2]),
                adf_p_interpretation=('lower_approximation_cutoff_returned_zero' if adf[1] == 0
                                      else 'MacKinnon_approximation'),
                adf_nobs=int(adf[3]), adf_regression='c', adf_autolag=None, adf_critical=adf[4],
                adf_lag_sensitivity=sensitivity, kpss_statistic=float(kp[0]), kpss_p_value=float(kp[1]),
                kpss_p_relation=relation, kpss_lags=int(kp[2]), kpss_regression='c',
                kpss_critical=kp[3], warnings=[str(w.message).strip() for w in caught]))
    return rows


def dependence_analysis(block):
    """Descriptive correlations/spectrum of one fully observed training segment."""
    from statsmodels.tsa.stattools import acf, pacf
    from scipy.signal import periodogram
    _check_block(block)
    result = {}
    for ch in CHANNELS:
        log = np.log10(block[ch + '_flux'].to_numpy(float))
        diff = np.diff(log)
        longest_lag = min(4320, len(diff) - 1)
        acfs = {name: acf(x, nlags=longest_lag, fft=True, adjusted=False)
                for name, x in dict(log_level=log, log_difference=diff,
                                    squared_log_difference=diff**2).items()}
        frequency, power = periodogram(diff, fs=1., detrend='constant')
        keep = (frequency > 0) & (frequency >= 2 / len(diff)) & (frequency <= 1 / 60)
        indices = np.flatnonzero(keep)
        peaks = indices[np.argsort(power[indices])[-5:][::-1]]
        result[ch] = dict(rows=len(log),
            acf={name: a[:121].tolist() for name, a in acfs.items()},
            pacf={name: pacf(x, nlags=60, method='ywm').tolist()
                  for name, x in dict(log_level=log, log_difference=diff).items()},
            selected_lags={name: {str(lag): dict(acf=float(a[lag]), pairs=len(diff) - lag)
                                  for lag in (60, 120, 1440, 2880, 4320) if lag < len(a)}
                           for name, a in acfs.items() if name != 'log_level'},
            exploratory_periodogram_peaks=[dict(period_minutes=float(1 / frequency[i]),
                                                 power=float(power[i])) for i in peaks])
    return result
