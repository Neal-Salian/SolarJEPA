"""Artificial NetCDF and isolated filesystem tests; not observational validation."""
from pathlib import Path
from dataclasses import replace
import json
import numpy as np
import pandas as pd
import pytest
from test_p2_foundation import native_file
from test_goes_acquisition import Response
from solar_flare_jepa.data import goes_acquisition as acquisition
from solar_flare_jepa.forecasting.contracts import ForecastSpec

ROOT=Path(__file__).resolve().parents[1]


def history(tmp_path,monkeypatch,day='2025-01-01'):
    c=json.loads((ROOT/'configs/data/goes_external_january2025.json').read_text())
    c['selected_interval']={'start':day,'end_exclusive':(pd.Timestamp(day)+pd.Timedelta(days=1)).date().isoformat(),'basis':'synthetic test selection'}
    date=pd.Timestamp(day)
    name=f'sci_xrsf-l2-avg1m_g16_d{date:%Y%m%d}_v2-2-1.nc'
    entry={'nominal_date':day,'url':f'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/{date:%Y/%m}/{name}',
        'path':f'data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/{date:%Y/%m}/{name}','max_bytes':1048576}
    c['files']=[entry];c['max_total_bytes']=1048576
    (tmp_path/'configs/data').mkdir(parents=True)
    config=tmp_path/'configs/data/external.json';config.write_text(json.dumps(c))
    sample=tmp_path/name
    offset=(pd.Timestamp(day,tz='UTC')-pd.Timestamp('2000-01-01T12:00:00Z')).total_seconds()
    native_file(sample,times=tuple(offset+x for x in (0,60,180,240)))
    payload=sample.read_bytes()
    monkeypatch.setattr(acquisition,'open_history_url',lambda url,timeout:Response(payload))
    inventory=acquisition.acquire_history(config,tmp_path)
    (tmp_path/'data/manifests/goes_p2_july2024.json').write_bytes((ROOT/'data/manifests/goes_p2_july2024.json').read_bytes())
    return tmp_path/c['manifest_path'],inventory


def load(*args,**kwargs):
    from solar_flare_jepa.data.external_validation import load_external_dataset
    return load_external_dataset(*args,**kwargs)


def test_external_native_identity_and_quality_are_preserved_without_fit(tmp_path,monkeypatch):
    manifest,inventory=history(tmp_path,monkeypatch)
    dataset,report=load(manifest,tmp_path)
    assert dataset.name=='external-goes16-january2025-science-avg1m-v2-2-1'
    assert dataset.availability_ns is None
    assert dataset.feature_mask[:5,1].tolist()==[True,False,False,True,True]
    assert np.isnan(dataset.features[2]).all()
    assert report['observed_rows']==4
    assert report['missing_bins']==1436
    metadata=json.loads(dataset.metadata_json)
    assert metadata['evaluation_only'] is True
    assert metadata['preprocessing']['fit_performed'] is False
    assert metadata['sources'][0]['sha256']==inventory['files'][0]['sha256']
    assert str(tmp_path) not in dataset.metadata_json
    assert metadata['frozen_benchmark']['sha256']=='581a3c4b8cfba6b9b21ed1fdb0b2277e728e9bf329a8da1ddcc0bd49c3cc4b3d'
    assert load(manifest,tmp_path)[0].fingerprint==dataset.fingerprint


def test_overlap_with_frozen_july_benchmark_fails_before_evaluation(tmp_path,monkeypatch):
    manifest,_=history(tmp_path,monkeypatch,day='2024-07-31')
    with pytest.raises(ValueError,match='overlap'):
        load(manifest,tmp_path)


def test_changed_frozen_identity_cannot_redefine_exclusion_period(tmp_path,monkeypatch):
    manifest,_=history(tmp_path,monkeypatch)
    frozen=tmp_path/'data/manifests/goes_p2_july2024.json'
    value=json.loads(frozen.read_text());value['selected_interval']['start']='2024-07-02'
    frozen.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='Frozen'):
        load(manifest,tmp_path)


def test_external_loader_rechecks_raw_hash_not_just_cached_table(tmp_path,monkeypatch):
    manifest,inventory=history(tmp_path,monkeypatch)
    load(manifest,tmp_path)
    raw=tmp_path/inventory['files'][0]['path'];raw.write_bytes(raw.read_bytes()+b'changed')
    with pytest.raises(ValueError):load(manifest,tmp_path)


def test_external_windows_are_test_only_and_causal_with_deterministic_exclusions(tmp_path,monkeypatch):
    from solar_flare_jepa.data.external_validation import build_external_windows
    manifest,_=history(tmp_path,monkeypatch)
    dataset,_=load(manifest,tmp_path)
    spec=ForecastSpec(60,1,1,dataset.feature_names,dataset.target_names,dataset.feature_units,dataset.target_units,
        availability_mode='retrospective_bin_end')
    windows=build_external_windows(dataset,spec)
    assert windows.training_slice is None
    assert windows.context.issue_times_ns.tolist()==[pd.Timestamp('2025-01-01T00:04:00Z').value]
    assert (windows.context.ends_ns<=windows.context.issue_times_ns[:,None]).all()
    assert (windows.targets.grid.starts_ns>=windows.context.issue_times_ns[:,None]).all()
    assert windows.manifest()==build_external_windows(dataset,spec).manifest()
    assert len(windows.excluded_origins)==1439
    with pytest.raises(ValueError):
        build_external_windows(replace(dataset,metadata_json='{}'),spec)


def test_external_manifest_path_escape_rejected(tmp_path,monkeypatch):
    manifest,_=history(tmp_path,monkeypatch)
    with pytest.raises(ValueError):load('../external.json',tmp_path)


def test_frozen_snapshot_digest_is_the_identity_used_for_exclusion(tmp_path,monkeypatch):
    from solar_flare_jepa.data import external_validation as external
    manifest,_=history(tmp_path,monkeypatch,day='2024-07-31')
    frozen=tmp_path/external.FROZEN_MANIFEST
    original=external._json_snapshot
    def replaced_snapshot(path,root):
        if Path(path)==frozen:
            value=json.loads(frozen.read_text())
            value['selected_interval']={'start':'2024-08-01','end_exclusive':'2024-09-01'}
            frozen.write_text(json.dumps(value))
        return original(path,root)
    monkeypatch.setattr(external,'_json_snapshot',replaced_snapshot)
    with pytest.raises(ValueError,match='Frozen'):
        load(manifest,tmp_path)
