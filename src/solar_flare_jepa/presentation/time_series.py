"""Bounded academic diagnostics; generated scientific arrays stay outside Git.

The tracked report pins a local ignored payload and every scientific source file.
No network, fitting, or native-data access occurs when loading the report.
"""
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np
import pandas as pd

from solar_flare_jepa.data.download import sha256_file
from .eda import CHANNELS, V1_CONFIG, load_v1_frame, longest_complete_block, _check_block

REPORT = 'docs/presentation/time_series_evidence.json'
IDENTITY = 'docs/presentation/time_series_identity.json'
PAYLOAD = 'results/presentation_time_series/diagnostics.json'
SOURCES = (
    V1_CONFIG, 'data/manifests/goes_v1_202405.json', 'data/manifests/goes_v1_202406.json',
    'data/manifests/goes_p2_july2024.json', 'data/manifests/goes_v1_202408.json',
    'src/solar_flare_jepa/presentation/time_series.py',
    'src/solar_flare_jepa/presentation/classical.py', 'src/solar_flare_jepa/presentation/eda.py',
    'src/solar_flare_jepa/data/download.py', 'src/solar_flare_jepa/data/goes.py',
    'src/solar_flare_jepa/data/eda.py', 'src/solar_flare_jepa/data/storage.py',
    'configs/data/v1_goes_202405.json', 'configs/data/v1_goes_202406.json',
    'configs/data/p2_goes_july2024.json', 'configs/data/v1_goes_202408.json',
    'src/solar_flare_jepa/data/goes_acquisition.py', 'src/solar_flare_jepa/data/foundation.py',
    'src/solar_flare_jepa/forecasting/statistical.py',
    'src/solar_flare_jepa/forecasting/baselines.py',
    'src/solar_flare_jepa/forecasting/contracts.py',
    'src/solar_flare_jepa/forecasting/windows.py', 'src/solar_flare_jepa/forecasting/splitting.py',
    'docs/presentation/eda_evidence.json', 'requirements-dashboard-lock.txt',
    'scripts/build_time_series_presentation.py',
)


def _frame_check(frame):
    if not isinstance(frame, pd.DataFrame) or not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError('Expected a DataFrame with an aware UTC minute grid')
    if (frame.empty
            or frame.index.tz is None or frame.index.hasnans
            or frame.index.has_duplicates or not frame.index.is_monotonic_increasing):
        raise ValueError('Expected nonempty ordered contiguous UTC minute grid')
    if any(t.utcoffset() != pd.Timedelta(0) for t in (frame.index[0], frame.index[-1])):
        raise ValueError('Expected UTC timestamps with zero offset')
    frame = frame.copy(deep=False)
    frame.index = frame.index.tz_convert('UTC').as_unit('ns')
    if ((frame.index.asi8 % 60_000_000_000 != 0).any()
            or (np.diff(frame.index.asi8) != 60_000_000_000).any()):
        raise ValueError('Expected nonempty ordered contiguous UTC minute grid')
    required = {'observed', 'xrsa_valid', 'xrsb_valid', 'xrsa_flux', 'xrsb_flux'}
    if not required.issubset(frame):
        raise ValueError('Missing channel or observation masks')
    for key in ('observed', 'xrsa_valid', 'xrsb_valid'):
        if frame[key].dtype != bool:
            raise ValueError('Observation and channel masks must be boolean')
    return frame


def _valid(frame, channel):
    s = frame[channel + '_flux'].astype(float)
    return s.where(frame.observed & frame[channel + '_valid'] & np.isfinite(s) & (s > 0))


def _positions(rows, maximum):
    return np.unique(np.linspace(0, rows-1, min(rows, maximum), dtype=int))


def eda_diagnostics(frame):
    """Full-sample statistics/Normal Q–Q; deterministic display thinning only."""
    from scipy.stats import probplot
    frame = _frame_check(frame)
    rows, qq, valid = [], {}, {}
    for ch in CHANNELS:
        s = _valid(frame, ch)
        valid[ch] = s
        x = s.dropna().to_numpy(float)
        if len(x) < 3:
            raise ValueError('EDA requires at least three valid observations per channel')
        raw = frame.get(ch + '_flux_raw', frame[ch + '_flux']).astype(float)
        for transform, values, units in [('raw', x, 'W/m2'),
                ('log10', np.log10(x), 'log10(F / (1 W/m2))')]:
            q25, median, q75 = np.quantile(values, [.25, .5, .75])
            rows.append(dict(channel=ch, transform=transform, units=units, count=len(values),
                mean=float(np.mean(values)), median=float(median), std=float(np.std(values, ddof=1)),
                min=float(np.min(values)), q25=float(q25), q75=float(q75), max=float(np.max(values)),
                absent_bins=int((~frame.observed).sum()),
                rejected_present_bins=int((frame.observed & s.isna()).sum()),
                nonfinite_raw_bins=int((frame.observed & ~np.isfinite(raw)).sum())))
        (theoretical, observed), (slope, intercept, r) = probplot(np.log10(x), dist='norm', fit=True)
        positions = _positions(len(x), 301)
        qq[ch] = dict(theoretical=theoretical[positions].tolist(), observed=observed[positions].tolist(),
            slope=float(slope), intercept=float(intercept), r=float(r), rows=len(x),
            reference='Normal theoretical quantiles; fitted least-squares reference line',
            display='301 evenly spaced order-statistic ranks; all valid values used in line fit')
    paired = pd.DataFrame(valid).dropna()
    positions = _positions(len(paired), 2500)
    if len(paired) < 3:
        raise ValueError('Scatter requires jointly valid paired observations')
    logged = np.log10(paired)
    return dict(statistics=rows, qq=qq,
        scatter=dict(xrsa=logged.xrsa.iloc[positions].tolist(), xrsb=logged.xrsb.iloc[positions].tolist(),
            total_pairs=len(paired), display_pairs=len(positions),
            full_sample_correlation=float(logged.corr().iloc[0, 1]),
            display='deterministic evenly spaced chronological joint-valid observations; no averaging'),
        missing_policy='Absent bins and rejected present bins remain missing; no interpolation. '
                       'Nonfinite raw counts are a subset of rejected present bins, not additive.')


def seasonal_diagnostic(block, period_minutes=1440):
    """STL at an imposed exploratory period, never a detected physical cycle."""
    from statsmodels.tsa.seasonal import STL
    from statsmodels.tsa.stattools import acf
    block = _frame_check(block)
    _check_block(block)
    if (isinstance(period_minutes, bool) or not isinstance(period_minutes, int)
            or period_minutes < 2 or len(block) < 4*period_minutes):
        raise ValueError('Exploratory STL requires integer period and at least four cycles')
    if not all(_valid(block, ch).notna().all() for ch in CHANNELS):
        raise ValueError('STL segment must be jointly quality valid; never fill gaps')
    positions = _positions(len(block), 1100)
    settings = dict(period=period_minutes, seasonal=7, robust=True, seasonal_jump=1,
                    trend_jump=max(1, period_minutes//10), low_pass_jump=max(1, period_minutes//10))
    display = dict(time_utc=[t.isoformat() for t in block.index[positions]])
    error, daily_acf = 0., {}
    for ch in CHANNELS:
        x = np.log10(block[ch + '_flux'].to_numpy(float))
        fitted = STL(x, **settings).fit()
        reconstruction = fitted.trend + fitted.seasonal + fitted.resid
        error = max(error, float(np.max(abs(x-reconstruction))))
        display[ch] = {name: values[positions].tolist() for name, values in
            dict(observed=x, trend=fitted.trend, seasonal=fitted.seasonal, residual=fitted.resid).items()}
        daily_acf[ch] = float(acf(np.diff(x), nlags=period_minutes, fft=True, adjusted=False)[period_minutes])
    return dict(method='robust STL on log10 flux', period_minutes=period_minutes, settings=settings,
        start_utc=block.index[0].isoformat(),
        end_exclusive_utc=(block.index[-1]+pd.Timedelta(minutes=1)).isoformat(), rows=len(block),
        display=display, daily_acf=daily_acf, reconstruction_max_error=error,
        period_basis='Prespecified daily-cycle diagnostic (1440 minutes), not an inferred solar period.',
        limitations='STL imposes the period; its seasonal component does not prove seasonality. '
                    'One training segment, about seven daily cycles; flares and changing variance limit interpretation. '
                    'Trend/low-pass jumps use linear interpolation between LOESS fits for bounded computation; '
                    'observed data and missing values are never interpolated.',
        seasonal_conclusion='Reliable stable seasonality is not established; no seasonal model is selected.')


def _read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate evidence field')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite evidence')))


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def _local(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or p.as_posix() != relative:
        raise ValueError('Noncanonical evidence path')
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError('Evidence path escapes repository')
    return target


def load_evidence(root):
    """Verify report/code/payload hashes, then hydrate the ignored scientific arrays."""
    root = Path(root).resolve()
    try:
        identity = _read(_local(root, IDENTITY))
        if identity['schema_version'] != 1 or identity['report']['path'] != REPORT:
            raise ValueError('Unsupported time-series evidence identity')
        if sha256_file(_local(root, REPORT)) != identity['report']['sha256']:
            raise ValueError('Time-series report identity mismatch')
        sources = identity['sources']
        if len(sources) != len(SOURCES) or {s['path'] for s in sources} != set(SOURCES):
            raise ValueError('Incomplete time-series source identity set')
        for source in sources:
            if sha256_file(_local(root, source['path'])) != source['sha256']:
                raise ValueError('Stale time-series source: '+source['path'])
        report = _read(_local(root, REPORT))
        if report['payload']['path'] != PAYLOAD:
            raise ValueError('Unapproved scientific payload path')
        if sha256_file(_local(root, PAYLOAD)) != report['payload']['sha256']:
            raise ValueError('Scientific payload identity mismatch')
        payload = _read(_local(root, PAYLOAD))
        if payload['schema_version'] != 1 or payload['dataset'] != report['dataset']:
            raise ValueError('Scientific payload/report mismatch')
        return payload
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ValueError('Verified time-series evidence unavailable: '+str(exc)+
            '. Restore pinned local data and run scripts/build_time_series_presentation.py.') from exc


def replay_deployment(evidence):
    """Fresh saved-parameter inference checked against the verified stored replay."""
    from .classical import infer
    deployment = evidence['deployment']
    def frame(table):
        return pd.DataFrame({ch+'_flux':table[ch+'_flux'] for ch in CHANNELS},
                            index=pd.DatetimeIndex(table['time_utc']))
    context, actual, stored = (frame(deployment[k]) for k in ('context', 'actual', 'forecast'))
    predicted = infer(evidence['classical']['selected'], context, deployment['issue_utc'])
    if not predicted.index.equals(actual.index) or not predicted.index.equals(stored.index):
        raise ValueError('Forecast and actual timestamp alignment mismatch')
    if not np.allclose(predicted.to_numpy(), stored.to_numpy(), rtol=1e-8, atol=0):
        raise ValueError('Saved-model replay differs from pinned predictions')
    metrics = {}
    for ch in CHANNELS:
        error = np.log10(predicted[ch+'_flux'])-np.log10(actual[ch+'_flux'])
        metrics[ch] = dict(log_mae=float(np.mean(abs(error))), log_rmse=float(np.sqrt(np.mean(error**2))))
        for name, value in metrics[ch].items():
            if not np.isclose(value, deployment['metrics'][ch][name], rtol=1e-8, atol=1e-12):
                raise ValueError('Replay metric mismatch')
    return predicted, metrics


def build_evidence(root):
    """Offline bounded build from the four verified manifests; no neural execution."""
    from .classical import build_classical
    root = Path(root).resolve()
    frame, native = load_v1_frame(root)
    config = _read(root / V1_CONFIG)
    train, test = config['splits'][0], config['splits'][-1]
    block = longest_complete_block(frame, train['start_utc'], train['end_utc'])
    test_frame = frame.loc[(frame.index>=pd.Timestamp(test['start_utc'])) &
                           (frame.index<pd.Timestamp(test['end_utc']))].copy()
    classical = build_classical(block, test_frame)
    dataset = dict(source_files=native['source_files'], source_bytes=native['source_bytes'], rows=len(frame),
        start_utc=frame.index[0].isoformat(), end_exclusive_utc=(frame.index[-1]+pd.Timedelta(minutes=1)).isoformat(),
        absent_bins=int((~frame.observed).sum()), manifests=native['manifests'], splits=config['splits'],
        quality_policy='strict status zero and channel-specific electron bits; no imputation',
        time_policy='UTC minute bin starts; retrospective bin-end availability; actual delivery unknown',
        units='W/m2', channels=list(CHANNELS))
    payload = dict(schema_version=1, dataset=dataset, eda=eda_diagnostics(frame),
                   decomposition=seasonal_diagnostic(block), **classical)
    replay_deployment(payload)
    _write(root / PAYLOAD, payload)
    report = dict(schema_version=1, dataset=dataset, statistics=payload['eda']['statistics'],
        decomposition={k:v for k,v in payload['decomposition'].items() if k!='display'},
        classical=payload['classical'],
        deployment={k:v for k,v in payload['deployment'].items() if k not in ('context','actual','forecast')},
        payload=dict(path=PAYLOAD,sha256=sha256_file(root/PAYLOAD)),
        environment={name:version(name) for name in ('numpy','pandas','scipy','statsmodels','streamlit')},
        evidence_status='OBSERVED offline native verification and bounded presentation calculations; '
                        'not a rerun or replacement of archived V1 neural experiments')
    _write(root / REPORT, report)
    _write(root / IDENTITY, dict(schema_version=1, report=dict(path=REPORT,sha256=sha256_file(root/REPORT)),
        sources=[dict(path=p,sha256=sha256_file(root/p)) for p in SOURCES]))
    return report
