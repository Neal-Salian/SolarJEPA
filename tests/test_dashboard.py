"""Dashboard safeguards. Artificial observations exist only in isolated tests."""
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from solar_flare_jepa.dashboard.data import (
    DashboardUnavailable, load_registry, verify_sources, load_observations,
    filter_interval, dataset_summary, envelope, histogram, load_model_comparison,
    load_diagnostics, validate_comparison,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture_frame():
    ix = pd.date_range('2024-05-01', periods=12, freq='min', tz='UTC')
    return pd.DataFrame({'xrsa_flux': np.arange(1.,13), 'xrsb_flux': np.arange(2.,14),
                         'observed': True, 'xrsa_valid': True, 'xrsb_valid': True}, index=ix)


def test_registry_requires_scientific_fields_and_rejects_traversal(tmp_path):
    r = load_registry(ROOT)
    for entry in r['visualizations'].values():
        assert all(k in entry for k in ['sources','dataset_identity','date_range','transformation',
            'quality_mask_policy','units','metric_definition','experiment_identity','source_commit'])
    bad = copy.deepcopy(r); bad['sources']['eda']['path'] = '../outside.json'
    (tmp_path/'src/solar_flare_jepa/dashboard').mkdir(parents=True)
    (tmp_path/'src/solar_flare_jepa/dashboard/registry.json').write_text(json.dumps(bad))
    with pytest.raises(DashboardUnavailable): load_registry(tmp_path)


def test_missing_or_corrupt_artifact_never_returns_fallback(tmp_path):
    r = load_registry(ROOT)
    with pytest.raises(DashboardUnavailable): verify_sources(tmp_path, r, 'acf')
    p = tmp_path / r['sources']['eda']['path']; p.parent.mkdir(parents=True); p.write_text('{}')
    with pytest.raises(DashboardUnavailable): verify_sources(tmp_path, r, 'acf')
    with pytest.raises(DashboardUnavailable): load_observations(tmp_path, r)


def test_half_open_filter_rejects_unsupported_periods_and_empty_ranges():
    f=fixture_frame()
    result=filter_interval(f, f.index[2], f.index[5])
    assert result.index.equals(f.index[2:5])
    for a,b in [('2024-04-30','2024-05-01'),('2024-08-01','2024-08-02'),
                ('2024-05-01','2024-05-01'),('2024-05-01T00:00:30Z','2024-05-01T00:03Z')]:
        with pytest.raises(DashboardUnavailable): filter_interval(f,a,b)


def test_summary_counts_observations_not_channels_or_grid_rows():
    f=fixture_frame(); f.loc[f.index[3],['observed','xrsa_valid','xrsb_valid']]=False
    f.loc[f.index[3],['xrsa_flux','xrsb_flux']]=np.nan
    s=dataset_summary(f)
    assert s['rows']==12 and s['observed_rows']==11 and s['cadence_seconds']==60


def test_histogram_uses_quality_masks_positive_finite_values_and_exact_70_bins():
    f=fixture_frame(); f.loc[f.index[:3],'xrsa_flux']=[0.,np.inf,100.]
    f.loc[f.index[2],'xrsa_valid']=False
    h=histogram(f)['xrsa']; expected=np.histogram(np.log10(np.arange(4.,13)),bins=70)
    np.testing.assert_array_equal(h['counts'],expected[0]); np.testing.assert_array_equal(h['edges'],expected[1])
    assert h['counts'].sum()==9
    f.loc[:,'xrsa_valid']=False
    with pytest.raises(DashboardUnavailable): histogram(f)


def test_envelope_preserves_original_extrema_timestamps_and_gap_breaks():
    ix=pd.date_range('2024-05-01',periods=10000,freq='min',tz='UTC')
    y=pd.Series(1.,index=ix); y.iloc[1234]=1e8; y.iloc[3333]=1e-9; y.iloc[6000:6005]=np.nan
    d=envelope(y,max_points=200)
    assert len(d)<=200 and d.loc[ix[1234]]==1e8 and d.loc[ix[3333]]==1e-9
    assert d.isna().any() and d.index.is_monotonic_increasing
    assert set(d.index).issubset(set(ix))
    for t,v in d.dropna().items(): assert v==y.loc[t]
    with pytest.raises(DashboardUnavailable): envelope(pd.Series([np.nan]*10,index=ix[:10]))


def test_comparison_refuses_incompatible_support_or_metrics():
    r=load_registry(ROOT); evidence=load_diagnostics(ROOT,r)
    assert evidence['diagnostic_block']['rows']==10149
    rows=load_model_comparison(ROOT,r)
    assert len(rows)==5 and rows.attrs['contract']['scored_cells']==86160
    bad=copy.deepcopy(json.loads((ROOT/'docs/presentation/model_evidence.json').read_text()))
    bad['per_model']['persistence_empirical']['origins']-=1
    with pytest.raises(DashboardUnavailable): validate_comparison(bad,r['comparison_contract'])
    bad=copy.deepcopy(r['comparison_contract']); bad['horizon_steps']=31
    with pytest.raises(DashboardUnavailable): validate_comparison(json.loads((ROOT/'docs/presentation/model_evidence.json').read_text()),bad)


def test_production_works_offline_without_training_or_test_release(monkeypatch):
    import socket, builtins, io, sys, xarray
    def denied(*args,**kwargs): raise AssertionError('Network forbidden')
    monkeypatch.setattr(socket.socket,'connect',denied)
    opened=[]; original=builtins.open
    def guarded(file,*args,**kwargs):
        name=str(file); opened.append(name)
        assert not any(x in name for x in ['2024/08/','test_predictions','results/experiments','test_release'])
        return original(file,*args,**kwargs)
    monkeypatch.setattr(builtins,'open',guarded)
    original_io=io.open
    def guarded_io(file,*args,**kwargs):
        name=str(file); opened.append(name)
        assert not any(x in name for x in ['2024/08/','test_predictions','results/experiments','test_release'])
        return original_io(file,*args,**kwargs)
    monkeypatch.setattr(io,'open',guarded_io)
    allowed=set()
    for name in ['goes_v1_202405.json','goes_v1_202406.json']:
        allowed.update((ROOT/row['path']).resolve() for row in json.loads((ROOT/'data/manifests'/name).read_text())['files'])
    original_dataset=xarray.open_dataset
    native_opened=[]
    def guarded_dataset(file,*args,**kwargs):
        assert Path(file).resolve() in allowed
        native_opened.append(Path(file).resolve())
        return original_dataset(file,*args,**kwargs)
    monkeypatch.setattr(xarray,'open_dataset',guarded_dataset)
    r=load_registry(ROOT); f=load_observations(ROOT,r)
    assert len(f)==87840 and f.index.max()<pd.Timestamp('2024-07-01',tz='UTC')
    assert dataset_summary(f)['observed_rows']==87840
    load_diagnostics(ROOT,r); load_model_comparison(ROOT,r)
    assert not any(n.startswith('solar_flare_jepa.training') for n in sys.modules)
    assert not any('test_predictions' in n for n in opened)
    assert set(native_opened)==allowed


def test_missing_comparison_contract_fails_closed(tmp_path):
    r=load_registry(ROOT); del r['comparison_contract']
    p=tmp_path/'src/solar_flare_jepa/dashboard/registry.json'; p.parent.mkdir(parents=True)
    p.write_text(json.dumps(r))
    with pytest.raises(DashboardUnavailable): load_registry(tmp_path)


def test_status_snapshot_does_not_claim_historical_blob_identity():
    r=load_registry(ROOT)
    assert r['sources']['status']['commit'] is None
    assert r['visualizations']['research_status']['source_commit'] is None
    assert 'historical Git blob equality' not in r['visualizations']['research_status']['verification_evidence']


@pytest.mark.parametrize('defect',['dependencies','missing_entry','units','date_range','source_alias'])
def test_corrupt_visualization_contract_cannot_disable_source_verification(tmp_path,defect):
    r=copy.deepcopy(load_registry(ROOT))
    if defect=='dependencies': r['visualizations']['model_comparison']['sources']=['status']
    elif defect=='missing_entry': del r['visualizations']['model_comparison']
    elif defect=='units': r['visualizations']['model_comparison']['units']={}
    elif defect=='date_range': r['visualizations']['model_comparison']['date_range']=None
    else: r['sources']['models']=copy.deepcopy(r['sources']['status'])
    p=tmp_path/'src/solar_flare_jepa/dashboard/registry.json'; p.parent.mkdir(parents=True)
    p.write_text(json.dumps(r))
    with pytest.raises(DashboardUnavailable): load_registry(tmp_path)
