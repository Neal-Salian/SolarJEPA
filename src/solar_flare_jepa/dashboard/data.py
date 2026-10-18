"""Fail-closed, UI-independent access to bounded observations and published evidence."""
import hashlib
import json
import re
from pathlib import Path
from threading import RLock

import numpy as np
import pandas as pd

# NetCDF open/metadata/read/close can overlap across Streamlit rerun threads.
# Share this lock with the isolated prediction loader for the full native lifetime.
_NATIVE_IO_LOCK = RLock()

REGISTRY_PATH = 'src/solar_flare_jepa/dashboard/registry.json'
DATASETS = {
    'data/manifests/goes_v1_202405.json': 'v1-goes16-202405-science-avg1m-v2-2-1',
    'data/manifests/goes_v1_202406.json': 'v1-goes16-202406-science-avg1m-v2-2-1',
}
ALLOWED_SOURCES = set(DATASETS) | {
    'configs/data/v1_goes_202405.json', 'configs/data/v1_goes_202406.json',
    'configs/experiments/v1_goes_2024.json', 'configs/experiments/v1_models.json',
    'docs/presentation/eda_evidence.json', 'docs/presentation/model_evidence.json',
    'docs/presentation/model_metrics.csv', 'docs/presentation/verification.json',
    'docs/presentation/dashboard_status.json',
    'docs/figures/presentation/eda_rolling_statistics.png',
    'src/solar_flare_jepa/data/goes.py', 'src/solar_flare_jepa/data/foundation.py',
    'src/solar_flare_jepa/data/goes_acquisition.py',
    'src/solar_flare_jepa/presentation/eda.py', 'src/solar_flare_jepa/presentation/figures.py',
}
MODEL_IDS = ('persistence_empirical', 'arima(2,1,0)', 'supervised', 'jepa_frozen', 'jepa_finetune')
# Bind evidence roles to concrete files: editing registry dependencies cannot skip a hash check.
SOURCE_PATHS = dict(zip(
    ('may_manifest','june_manifest','may_config','june_config','v1_config','models_config',
     'eda','models','metrics','historical_verification','rolling','status','goes_adapter',
     'goes_foundation','goes_verification','eda_algorithm','figure_algorithm'),
    ('data/manifests/goes_v1_202405.json','data/manifests/goes_v1_202406.json',
     'configs/data/v1_goes_202405.json','configs/data/v1_goes_202406.json',
     'configs/experiments/v1_goes_2024.json','configs/experiments/v1_models.json',
     'docs/presentation/eda_evidence.json','docs/presentation/model_evidence.json',
     'docs/presentation/model_metrics.csv','docs/presentation/verification.json',
     'docs/figures/presentation/eda_rolling_statistics.png','docs/presentation/dashboard_status.json',
     'src/solar_flare_jepa/data/goes.py','src/solar_flare_jepa/data/foundation.py',
     'src/solar_flare_jepa/data/goes_acquisition.py','src/solar_flare_jepa/presentation/eda.py',
     'src/solar_flare_jepa/presentation/figures.py')))
NATIVE_SOURCES = {'may_manifest','june_manifest','may_config','june_config',
                  'goes_adapter','goes_foundation','goes_verification'}
REQUIRED_SOURCES = {
    'overview_flux': NATIVE_SOURCES, 'channel_flux': NATIVE_SOURCES, 'dataset_summary': NATIVE_SOURCES,
    'flux_histogram': NATIVE_SOURCES | {'figure_algorithm'},
    'rolling_statistics': {'rolling','figure_algorithm'},
    'acf': {'eda','eda_algorithm'}, 'pacf': {'eda','eda_algorithm'},
    'stationarity': {'eda','eda_algorithm','historical_verification'},
    'model_comparison': {'models','metrics','v1_config','models_config','historical_verification'},
    'research_status': {'status'},
}


class DashboardUnavailable(ValueError):
    """Evidence is absent, invalid, or outside the presentation contract."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise DashboardUnavailable('Duplicate JSON field')
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(Path(path).read_text(), object_pairs_hook=_unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(DashboardUnavailable('Nonfinite JSON')))
    except (OSError, ValueError, TypeError) as exc:
        raise DashboardUnavailable('Missing or invalid JSON evidence') from exc


def _path(root, relative):
    root = Path(root).resolve(); p = Path(relative)
    if p.is_absolute() or '..' in p.parts or p.as_posix() != relative:
        raise DashboardUnavailable('Noncanonical source path')
    target = root / p
    if not target.resolve().is_relative_to(root):
        raise DashboardUnavailable('Source escapes repository')
    return target


def _sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def load_registry(root):
    r = read_json(_path(root, REGISTRY_PATH))
    try:
        if r['schema_version'] != 1 or set(d['manifest'] for d in r['datasets']) != set(DATASETS):
            raise DashboardUnavailable('Unsupported dataset selection')
        for d in r['datasets']:
            if d['dataset_id'] != DATASETS[d['manifest']]: raise DashboardUnavailable('Dataset identity mismatch')
        if not isinstance(r['comparison_contract'], dict):
            raise DashboardUnavailable('Missing comparison contract')
        if set(r['sources']) != set(SOURCE_PATHS) or set(r['visualizations']) != set(REQUIRED_SOURCES):
            raise DashboardUnavailable('Incomplete source or visualization registry')
        for key,source in r['sources'].items():
            _path(root, source['path'])
            if source['path'] != SOURCE_PATHS[key] or not re.fullmatch('[0-9a-f]{64}', source['sha256']):
                raise DashboardUnavailable('Unapproved source identity')
            if source['commit'] is None and source['path'] == 'docs/presentation/dashboard_status.json':
                continue  # New audit snapshot: its underlying source commits are recorded per item.
            if not isinstance(source['commit'],str) or not re.fullmatch('[0-9a-f]{40}', source['commit']):
                raise DashboardUnavailable('Missing source commit')
        fields = {'sources','dataset_identity','date_range','transformation','quality_mask_policy',
                  'units','metric_definition','experiment_identity','source_commit'}
        for key,entry in r['visualizations'].items():
            if not fields.issubset(entry) or not entry['sources']:
                raise DashboardUnavailable('Incomplete visualization provenance')
            if any(s not in r['sources'] for s in entry['sources']): raise DashboardUnavailable('Unknown source')
            if set(entry['sources']) != REQUIRED_SOURCES[key]:
                raise DashboardUnavailable('Visualization evidence dependencies mismatch')
            if key != 'research_status':
                for field in ('units','transformation','quality_mask_policy','source_commit'):
                    if not isinstance(entry[field],str) or not entry[field].strip():
                        raise DashboardUnavailable('Invalid scientific provenance metadata')
                if not isinstance(entry['dataset_identity'],list) or not entry['dataset_identity']:
                    raise DashboardUnavailable('Missing visualization dataset identity')
                period=entry['date_range']
                if not isinstance(period,dict) or not {'start_utc','end_exclusive_utc'}.issubset(period):
                    raise DashboardUnavailable('Missing visualization date range')
                if _utc(period['start_utc']) >= _utc(period['end_exclusive_utc']):
                    raise DashboardUnavailable('Invalid visualization interval')
    except (KeyError, TypeError, AttributeError) as exc:
        raise DashboardUnavailable('Invalid provenance registry') from exc
    return r


def verify_sources(root, registry, entry_id):
    try:
        if set(registry['visualizations'][entry_id]['sources']) != REQUIRED_SOURCES[entry_id]:
            raise DashboardUnavailable('Visualization evidence dependencies mismatch')
        paths=[]
        for key in registry['visualizations'][entry_id]['sources']:
            source=registry['sources'][key]; path=_path(root,source['path'])
            if source['path'] != SOURCE_PATHS[key] or _sha(path)!=source['sha256']:
                raise DashboardUnavailable('Source identity mismatch: '+source['path'])
            paths.append(path)
        return paths
    except (OSError, KeyError, TypeError) as exc:
        raise DashboardUnavailable('Required verified artifact is missing or invalid') from exc


def load_observations(root, registry):
    """Open exactly the May/June training selection. No discovery or acquisition."""
    from solar_flare_jepa.data.goes_acquisition import verify_history
    from solar_flare_jepa.data.foundation import validate_goes_files
    try:
        verify_sources(root, registry, 'overview_flux')
        paths=[]
        for relative, identity in DATASETS.items():
            manifest=read_json(_path(root,relative))
            if manifest['dataset_id']!=identity: raise DashboardUnavailable('Dataset identity mismatch')
            # Validate selection before any native file is opened, even with a forged manifest.
            month='05' if '202405' in relative else '06'
            expected_start=f'2024-{month}-01'
            expected_end='2024-06-01' if month=='05' else '2024-07-01'
            if manifest['selected_interval']['start']!=expected_start or manifest['selected_interval']['end_exclusive']!=expected_end:
                raise DashboardUnavailable('Unapproved observation period')
            for row in manifest['files']:
                if not row['path'].startswith(f'data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/{month}/'):
                    raise DashboardUnavailable('Unapproved native file')
                _path(root,row['path'])
            paths.extend(verify_history(_path(root,relative),Path(root).resolve()))
        if len(paths)!=61: raise DashboardUnavailable('Incomplete selected dataset')
        with _NATIVE_IO_LOCK:
            frame,_=validate_goes_files(paths,start_utc='2024-05-01T00:00:00Z',end_utc='2024-07-01T00:00:00Z')
        cols=['xrsa_flux','xrsb_flux','observed','xrsa_valid','xrsb_valid']
        frame=frame[cols].copy()
        for ch in ('xrsa','xrsb'): frame[ch+'_flux']=valid_flux(frame,ch).astype(float)
        return frame
    except DashboardUnavailable: raise
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        raise DashboardUnavailable('GOES selection could not be verified; check the two local manifests and files') from exc


def _utc(value):
    t=pd.Timestamp(value)
    if pd.isna(t): raise DashboardUnavailable('Invalid date')
    return t.tz_localize('UTC') if t.tzinfo is None else t.tz_convert('UTC')


def filter_interval(frame,start,end_exclusive):
    try:
        a,b=_utc(start),_utc(end_exclusive)
        if frame.empty or a>=b or a<frame.index.min() or b>frame.index.max()+pd.Timedelta(minutes=1):
            raise DashboardUnavailable('Date range is outside the verified available observations')
        if a.value%60_000_000_000 or b.value%60_000_000_000:
            raise DashboardUnavailable('Date range must use whole UTC minute bins')
        selected=frame.loc[(frame.index>=a)&(frame.index<b)].copy()
        if selected.empty: raise DashboardUnavailable('Empty selected interval')
        return selected
    except (TypeError, ValueError) as exc:
        if isinstance(exc,DashboardUnavailable): raise
        raise DashboardUnavailable('Unsupported date range') from exc


def valid_flux(frame,ch):
    s=frame[ch+'_flux'].astype(float)
    return s.where(frame[ch+'_valid'] & frame['observed'] & np.isfinite(s) & (s>0))


def dataset_summary(frame):
    if frame.empty or frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise DashboardUnavailable('Invalid observation timestamps')
    if len(frame)>1 and not (np.diff(frame.index.asi8)==60_000_000_000).all():
        raise DashboardUnavailable('Unexpected sampling grid')
    return dict(rows=len(frame),observed_rows=int(frame.observed.sum()),cadence_seconds=60,
        xrsa_valid_rows=int(valid_flux(frame,'xrsa').notna().sum()),
        xrsb_valid_rows=int(valid_flux(frame,'xrsb').notna().sum()),
        start_utc=frame.index[0].isoformat(),
        end_exclusive_utc=(frame.index[-1]+pd.Timedelta(minutes=1)).isoformat())


def envelope(series,max_points=2400):
    """Keep original first/last/min/max per bucket plus every missing-run break.

    Missing runs retain one original NaN separator and both valid edge observations.
    Budget exhaustion fails closed instead of connecting across a missing interval.
    """
    y=series.astype(float).replace([np.inf,-np.inf],np.nan)
    if y.empty or not y.notna().any() or y.index.has_duplicates or not y.index.is_monotonic_increasing:
        raise DashboardUnavailable('No valid chart data')
    if len(y)>1 and not (np.diff(y.index.asi8)==60_000_000_000).all():
        raise DashboardUnavailable('Chart requires explicit minute gap rows')
    if max_points<8: raise DashboardUnavailable('Chart budget is too small')
    if len(y)<=max_points: return y
    missing=y.isna().to_numpy(); boundaries=np.flatnonzero(missing[1:]!=missing[:-1])+1
    mandatory={0,len(y)-1}
    for j in boundaries: mandatory.update((int(j-1),int(j)))
    room=max_points-len(mandatory)
    if room<4: raise DashboardUnavailable('Too many gaps for a faithful bounded chart; select a shorter interval')
    keep=set(mandatory); values=y.to_numpy()
    buckets=max(1,room//4)
    for indices in np.array_split(np.arange(len(y)),buckets):
        good=indices[np.isfinite(values[indices])]
        if len(good): keep.update((int(good[0]),int(good[-1]),int(good[np.argmin(values[good])]),int(good[np.argmax(values[good])])))
    return y.iloc[sorted(keep)]


def histogram(frame):
    result={}
    for ch in ('xrsa','xrsb'):
        values=valid_flux(frame,ch).dropna().to_numpy()
        if not len(values): raise DashboardUnavailable('No valid observations for flux distribution')
        counts,edges=np.histogram(np.log10(values),bins=70)
        result[ch]=dict(counts=counts,edges=edges)
    return result


def load_diagnostics(root,registry):
    verify_sources(root,registry,'acf'); verify_sources(root,registry,'stationarity')
    d=read_json(_path(root,'docs/presentation/eda_evidence.json'))
    try:
        block=d['diagnostic_block']
        if (block['start_utc'],block['end_exclusive_utc'],block['rows']) != (
            '2024-06-11T16:38:00+00:00','2024-06-18T17:47:00+00:00',10149):
            raise DashboardUnavailable('Diagnostic support mismatch')
        for ch in ('xrsa','xrsb'):
            for method,n in [('acf',121),('pacf',61)]:
                for transform in ('log_level','log_difference'):
                    a=np.asarray(d['dependence'][ch][method][transform],float)
                    if a.shape!=(n,) or not np.isfinite(a).all() or (abs(a)>1.000001).any():
                        raise DashboardUnavailable('Invalid stored correlation')
        if len(d['stationarity'])!=6: raise DashboardUnavailable('Incomplete stationarity evidence')
        for row in d['stationarity']:
            if row['adf_lags']!=30 or row['adf_regression']!='c' or row['kpss_regression']!='c':
                raise DashboardUnavailable('Stationarity method mismatch')
            for field in ('adf_statistic','adf_p_value','kpss_statistic','kpss_p_value'):
                if not np.isfinite(row[field]): raise DashboardUnavailable('Invalid stationarity value')
    except (KeyError,TypeError,ValueError) as exc:
        if isinstance(exc,DashboardUnavailable): raise
        raise DashboardUnavailable('Invalid diagnostic evidence') from exc
    return d


def validate_comparison(evidence,contract):
    expected=dict(experiment_id='v1-full-20261009',origins=1436,scored_cells=86160,
        horizon_steps=30,cadence_seconds=60,targets=['xrsa_flux','xrsb_flux'],
        start_utc='2024-08-01T00:00:00Z',end_exclusive_utc='2024-09-01T00:00:00Z',
        metric='log_mae',units='dex',seed_aggregation='arithmetic mean of fitted-seed losses, not ensemble forecasts')
    try:
        if contract!=expected: raise DashboardUnavailable('Incompatible metric comparison contract')
        if evidence['source_run']!='results/experiments/'+contract['experiment_id']:
            raise DashboardUnavailable('Experiment identity mismatch')
        if evidence['origins']!=1436 or evidence['scored_cells']!=86160:
            raise DashboardUnavailable('Incompatible evaluation support')
        if evidence['seed_aggregation']!=expected['seed_aggregation']:
            raise DashboardUnavailable('Incompatible seed aggregation')
        for model in MODEL_IDS:
            members=[f'{model}_seed{s}' for s in (17,29,43)] if model in MODEL_IDS[2:] else [model]
            scores=[]
            for member in members:
                row=evidence['per_model'][member]
                if row['origins']!=1436 or row['scored_cells']!=86160 or len(row['by_lead']['log_mae'])!=30:
                    raise DashboardUnavailable('Incompatible model evaluation support')
                if set(row['by_target'])!=set(expected['targets']): raise DashboardUnavailable('Incompatible target channels')
                value=row['log_mae']
                if not np.isfinite(value) or value<0: raise DashboardUnavailable('Invalid model metric')
                scores.append(value)
            if not np.isclose(np.mean(scores),evidence['grouped'][model]['log_mae'],rtol=0,atol=1e-15):
                raise DashboardUnavailable('Seed metric mismatch')
    except (KeyError,TypeError,ValueError) as exc:
        if isinstance(exc,DashboardUnavailable): raise
        raise DashboardUnavailable('Invalid model comparison evidence') from exc


def load_model_comparison(root,registry):
    verify_sources(root,registry,'model_comparison')
    e=read_json(_path(root,'docs/presentation/model_evidence.json'))
    try:
        contract=registry['comparison_contract']; validate_comparison(e,contract)
        all_rows=pd.read_csv(_path(root,'docs/presentation/model_metrics.csv'),float_precision='round_trip')
        if all_rows.model_id.duplicated().any(): raise DashboardUnavailable('Duplicate model identity')
        table=all_rows.set_index('model_id').loc[list(MODEL_IDS)].reset_index()
        for row in table.itertuples():
            if not np.isclose(row.log_mae,e['grouped'][row.model_id]['log_mae'],rtol=0,atol=1e-15):
                raise DashboardUnavailable('Published metric mismatch')
        table=table[['model_id','label','log_mae']]; table.attrs['contract']=dict(contract)
        return table
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if isinstance(exc,DashboardUnavailable): raise
        raise DashboardUnavailable('Invalid model metric table') from exc
