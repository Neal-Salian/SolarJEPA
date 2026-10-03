"""Artificial GOES-format artifacts exercise provenance, never solar skill."""
import importlib
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.data.goes import read_goes
from test_experiment_provenance import config as prototype
from test_goes import write_fixture


ROOT = Path(__file__).resolve().parents[1]
TIME_POLICY = ('GOES documented UTC convention neglecting leap seconds; index=bin start, '
               'available at time_end at earliest; operational latency unknown')


def adapter():
    return importlib.import_module('solar_flare_jepa.experiments.reference').goes_reference


def reference_config():
    cfg = prototype()
    cfg['dataset'] = dict(kind='goes_reference', manifest='configs/data/noaa_sample.json',
                          prepared_config='configs/data/noaa_eda.json',
                          sidecar='data/processed/noaa_reference.metadata.json')
    cfg['forecast'].update(feature_names=['xrsb_flux'], target_names=['xrsb_flux'],
                           feature_units=['W/m2'], target_units=['W/m2'],
                           availability_mode='retrospective_bin_end')
    cfg['metrics']['target_weights'] = [1]
    return cfg


def prepared_reference(tmp_path):
    root = tmp_path / 'reference'
    raw = root / 'data/raw/noaa/fixture.nc'
    raw.parent.mkdir(parents=True)
    write_fixture(raw)
    manifest = root / 'configs/data/noaa_sample.json'
    manifest.parent.mkdir(parents=True)
    entry = dict(path=raw.relative_to(root).as_posix(), bytes=raw.stat().st_size,
                 sha256=sha256_file(raw), max_bytes=1048576,
                 url='https://data.ngdc.noaa.gov/platforms/goes/l2/data/xrsf-l2-avg1m_science/fixture.nc')
    manifest.write_text(json.dumps(dict(files=[entry], max_total_bytes=1048576)))
    preparation = json.loads((ROOT / 'configs/data/noaa_eda.json').read_text())
    (root / 'configs/data/noaa_eda.json').write_text(json.dumps(preparation))
    parquet = root / preparation['processed_path']
    parquet.parent.mkdir(parents=True)
    read_goes([raw]).to_parquet(parquet)
    sidecar = parquet.with_suffix('.metadata.json')
    metadata = dict(config=preparation, role='external_reference_validation_not_aditya', rows=4,
                    manifest_sha256=sha256_file(manifest), processed_sha256=sha256_file(parquet),
                    units={'flux':'W/m2', 'log10_flux':'log10(F / (1 W/m2))', 'dlog10_dt':'s^-1'},
                    time_policy=TIME_POLICY,
                    sources=[dict(path=str(raw.resolve()), sha256=entry['sha256'], bytes=entry['bytes'])])
    sidecar.write_text(json.dumps(metadata))
    return root, raw, parquet, sidecar


def test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability(tmp_path):
    root, _, _, _ = prepared_reference(tmp_path)
    data = adapter()(reference_config(), root)
    assert data.role == 'goes_reference'
    assert data.feature_names == data.target_names == ('xrsb_flux',)
    assert data.feature_units == data.target_units == ('W/m2',)
    assert data.availability_ns is None
    assert data.availability_policy == 'bin_end_earliest'
    np.testing.assert_array_equal(data.feature_mask[:, 0], [True, False, False, True])
    np.testing.assert_array_equal(data.target_mask, data.feature_mask)
    np.testing.assert_array_equal(data.features[:, 0], [1e-6, np.nan, np.nan, 1e-4])
    np.testing.assert_array_equal(data.targets, data.features)
    assert data.starts_ns[0] == 946728000000000000
    np.testing.assert_array_equal(data.ends_ns - data.starts_ns, [60_000_000_000]*4)
    metadata = json.loads(data.metadata_json)
    assert metadata['interpretation'] == 'reference_validation_not_aditya'
    assert metadata['operational_latency'] == 'UNKNOWN'
    assert str(tmp_path) not in json.dumps(data.semantic_content())


def test_legacy_sidecar_relocation_has_same_identity_without_artifact_rewrites(tmp_path):
    root, _, parquet, sidecar = prepared_reference(tmp_path)
    first = adapter()(reference_config(), root)
    before = [parquet.read_bytes(), sidecar.read_bytes()]
    moved = tmp_path / 'moved'
    shutil.move(root, moved)
    second = adapter()(reference_config(), moved)
    assert first.fingerprint == second.fingerprint
    assert before == [(moved / 'data/processed' / p.name).read_bytes() for p in (parquet, sidecar)]


@pytest.mark.parametrize('defect', ['manifest_hash', 'processed_hash', 'source_hash', 'source_bytes',
                                   'source_name', 'missing_source', 'duplicate_source', 'role',
                                   'rows', 'units', 'time_policy', 'config'])
def test_sidecar_conflicts_fail_closed(tmp_path, defect):
    root, _, _, sidecar = prepared_reference(tmp_path)
    metadata = json.loads(sidecar.read_text())
    if defect in ('manifest_hash', 'processed_hash'):
        metadata[defect.replace('_hash', '_sha256')] = '0'*64
    elif defect == 'source_hash':
        metadata['sources'][0]['sha256'] = '0'*64
    elif defect == 'source_bytes':
        metadata['sources'][0]['bytes'] += 1
    elif defect == 'source_name':
        metadata['sources'][0]['path'] = '/historical/root/unrelated.nc'
    elif defect == 'missing_source':
        metadata['sources'] = []
    elif defect == 'duplicate_source':
        metadata['sources'] *= 2
    elif defect == 'role':
        metadata['role'] = 'aditya_training'
    elif defect == 'rows':
        metadata['rows'] += 1
    elif defect == 'units':
        metadata['units']['flux'] = 'counts'
    elif defect == 'time_policy':
        metadata['time_policy'] = 'actual_operational_delivery'
    elif defect == 'config':
        metadata['config']['imputation'] = 'interpolation'
    sidecar.write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        adapter()(reference_config(), root)


def test_processed_hash_rejection_precedes_parquet_decoding(tmp_path, monkeypatch):
    root, _, parquet, _ = prepared_reference(tmp_path)
    parquet.write_bytes(b'not parquet')
    def forbidden_decode(*args, **kwargs):
        raise AssertionError('Corrupt artifacts must fail before decoding')
    monkeypatch.setattr(pd, 'read_parquet', forbidden_decode)
    with pytest.raises(ValueError, match='processed|Parquet|SHA'):
        adapter()(reference_config(), root)


def test_matching_processed_hash_cannot_hide_divergence_from_pinned_raw(tmp_path):
    root, _, parquet, sidecar = prepared_reference(tmp_path)
    frame = pd.read_parquet(parquet)
    frame.loc[frame.index[0], 'xrsb_flux'] = 0.15
    frame.to_parquet(parquet)
    metadata = json.loads(sidecar.read_text())
    metadata['processed_sha256'] = sha256_file(parquet)
    sidecar.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='raw|prepar|GOES'):
        adapter()(reference_config(), root)


@pytest.mark.parametrize('policy,value', [('imputation','linear'), ('normalization','full_series'),
                                         ('cadence_seconds',120), ('quality_policy','all_valid'),
                                         ('dataset_role','aditya_training')])
def test_even_matching_sidecar_cannot_authorize_unsupported_preparation(tmp_path, policy, value):
    root, _, _, sidecar = prepared_reference(tmp_path)
    path = root / 'configs/data/noaa_eda.json'
    preparation = json.loads(path.read_text())
    preparation[policy] = value
    path.write_text(json.dumps(preparation))
    metadata = json.loads(sidecar.read_text())
    metadata['config'] = preparation
    sidecar.write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        adapter()(reference_config(), root)


def test_source_bytes_are_verified_against_manifest(tmp_path):
    root, raw, _, _ = prepared_reference(tmp_path)
    content = bytearray(raw.read_bytes())
    content[-1] ^= 1
    raw.write_bytes(content)
    with pytest.raises(ValueError, match='SHA-256'):
        adapter()(reference_config(), root)


def test_prepared_artifact_cannot_escape_root_through_symlink(tmp_path):
    root, _, parquet, _ = prepared_reference(tmp_path)
    outside = tmp_path / 'outside.parquet'
    shutil.move(parquet, outside)
    parquet.symlink_to(outside)
    with pytest.raises(ValueError, match='root'):
        adapter()(reference_config(), root)


@pytest.mark.parametrize('change', [('availability_mode','operational'),
                                  ('eligibility_policy','masked'), ('feature_lookback_steps',1)])
def test_nonretrospective_or_derived_reference_modes_are_rejected(tmp_path, change):
    root, _, _, _ = prepared_reference(tmp_path)
    cfg = reference_config()
    cfg['forecast'][change[0]] = change[1]
    with pytest.raises(ValueError):
        adapter()(cfg, root)
