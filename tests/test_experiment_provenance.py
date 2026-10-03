"""Portable identities and publication fail closed on corruption/replacement."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from solar_flare_jepa.experiments.config import load_config, validate_config, config_fingerprint
from solar_flare_jepa.experiments.fixtures import synthetic_fixture
from solar_flare_jepa.experiments.provenance import (
    dataset_fingerprint, split_fingerprint, source_fingerprint,
    verify_source_identities, atomic_record, verify_artifacts,
)


def config():
    return dict(schema_version=1, dataset=dict(kind='synthetic_fixture', rows=90,
                start_utc='2024-01-01T00:00:00Z', fixture_seed=17),
                forecast=dict(cadence_seconds=60, context_steps=3, horizon_steps=2,
                stride_steps=1, feature_names=['x', 'y'], target_names=['x', 'y'],
                feature_units=['synthetic_unit', 'synthetic_unit'],
                target_units=['synthetic_unit', 'synthetic_unit']),
                splits=[dict(name=name, start_utc=start, end_utc=end) for name,start,end in [
                    ('train','2024-01-01T00:00:00Z','2024-01-01T00:40:00Z'),
                    ('validation','2024-01-01T00:40:00Z','2024-01-01T01:00:00Z'),
                    ('test','2024-01-01T01:00:00Z','2024-01-01T01:30:00Z')]],
                baselines=[dict(name='persistence', parameters={})],
                metrics=dict(lead_weights=[1,1], target_weights=[1,1]), seeds=[17,29,43])


def test_config_canonical_order_duplicate_unknown_nonfinite_and_unsafe_modes(tmp_path):
    cfg = config()
    resolved = validate_config(cfg)
    assert config_fingerprint(resolved) == config_fingerprint(dict(reversed(list(resolved.items()))))
    path = tmp_path/'config.json'
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match='duplicate'):
        load_config(path)
    for bad in [{**cfg, 'typo':1}, {**cfg, 'seeds':[True]},
                {**cfg, 'dataset':{'kind':'solexs'}},
                {**cfg, 'metrics':{'lead_weights':[float('nan'),1], 'target_weights':[1,1]}}]:
        with pytest.raises(ValueError):
            validate_config(bad)


def test_fixture_is_local_rng_deterministic_and_content_changes_identity():
    np.random.seed(567)
    state = np.random.get_state()
    first = synthetic_fixture(config())
    second = synthetic_fixture(config())
    np.testing.assert_array_equal(first.features, second.features)
    assert dataset_fingerprint(first) == dataset_fingerprint(second)
    after = np.random.get_state()
    np.testing.assert_array_equal(state[1], after[1])
    values = np.array(first.features)
    values[-1,0] += 10
    assert dataset_fingerprint(replace(first,features=values)) != dataset_fingerprint(first)
    mask = np.array(first.feature_mask)
    mask[0,0] = False
    assert dataset_fingerprint(replace(first,feature_mask=mask)) != dataset_fingerprint(first)
    assert dataset_fingerprint(replace(first,quality_policy='another_declared_policy')) != dataset_fingerprint(first)
    assert dataset_fingerprint(replace(first,feature_units=('changed','synthetic_unit'))) != dataset_fingerprint(first)


def test_split_fingerprint_hashes_actual_origins_exclusions_and_support():
    manifest = {'boundaries':[0,40,60,90], 'origins':['a','b'],
                'excluded':[{'origin':'c','reason':'support'}], 'lookback':1}
    before = split_fingerprint(manifest)
    for key, value in [('origins',['a','d']), ('lookback',2), ('boundaries',[0,41,60,90]),
                       ('excluded',[{'origin':'c','reason':'quality'}])]:
        assert split_fingerprint({**manifest,key:value}) != before


def test_source_identity_is_portable_but_detects_byte_corruption(tmp_path):
    a,b=tmp_path/'a',tmp_path/'b'
    (a/'src').mkdir(parents=True)
    (a/'src'/'module.py').write_text('value = 42\n')
    shutil.copytree(a,b)
    one=source_fingerprint(a,['src/module.py'])
    two=source_fingerprint(b,['src/module.py'])
    assert one == two
    assert str(tmp_path) not in json.dumps(one)
    verify_source_identities(b,one['files'])
    (b/'src'/'module.py').write_text('value = 43\n')
    with pytest.raises(ValueError,match='identity'):
        verify_source_identities(b,one['files'])
    assert source_fingerprint(b,['src/module.py'])['fingerprint'] != one['fingerprint']


def test_atomic_record_existing_empty_destination_is_never_replaced(tmp_path):
    root=tmp_path/'repo'
    destination=root/'results'/'experiments'/'existing'
    destination.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        atomic_record(root,destination,{'result.json':{'ok':True}})
    assert list(destination.iterdir()) == []


def test_atomic_record_corruption_and_unsafe_paths(tmp_path):
    root=tmp_path/'repo'
    root.mkdir()
    destination=root/'results'/'experiments'/'one'
    atomic_record(root,destination,{'result.json':{'ok':True},'nested/values.json':[1,2]})
    verify_artifacts(destination)
    (destination/'nested'/'values.json').write_text('[1,3]\n')
    with pytest.raises(ValueError,match='identity'):
        verify_artifacts(destination)
    for path in [root/'data'/'raw'/'bad',tmp_path/'outside',root/'results'/'experiments']:
        with pytest.raises(ValueError):
            atomic_record(root,path,{'result.json':{'ok':True}})
    with pytest.raises(ValueError):
        atomic_record(root,root/'results'/'experiments'/'two',{'../escape.json':{}})


def test_failed_staging_preserves_existing_science_and_leaves_no_published_run(tmp_path):
    root=tmp_path/'repo'
    science=root/'data'/'raw'/'original.txt'
    science.parent.mkdir(parents=True)
    science.write_text('immutable')
    destination=root/'results'/'experiments'/'failed'
    with pytest.raises(ValueError):
        atomic_record(root,destination,{'result.json':{'invalid':float('nan')}})
    assert not destination.exists()
    assert science.read_text() == 'immutable'
    assert not list((root/'results'/'experiments').glob('.stage-*'))


def test_concurrent_same_execution_id_has_exactly_one_complete_winner(tmp_path):
    root=tmp_path/'repo'
    root.mkdir()
    destination=root/'results'/'experiments'/'one'
    def publish(number):
        try:
            atomic_record(root,destination,{'result.json':{'number':number}})
            return 'won'
        except FileExistsError:
            return 'lost'
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(publish,[1,2]))
    assert sorted(outcomes) == ['lost','won']
    verify_artifacts(destination)
    assert json.loads((destination/'result.json').read_text())['number'] in [1,2]


def test_config_rejects_string_channel_lists():
    cfg = config()
    cfg['forecast']['feature_names'] = 'xy'
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_config_rejects_mapping_in_place_of_ordered_channel_list():
    cfg = config()
    cfg['forecast']['feature_names'] = {'x':'ignored','y':'ignored'}
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_config_rejects_overflowing_weight_sum():
    cfg = config()
    cfg['metrics']['lead_weights'] = [1e308,1e308]
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_unindexed_nested_artifact_index_is_corruption(tmp_path):
    root=tmp_path/'repo'
    root.mkdir()
    destination=root/'results'/'experiments'/'one'
    atomic_record(root,destination,{'result.json':{'ok':True}})
    extra=destination/'extra'/'artifacts.json'
    extra.parent.mkdir()
    extra.write_text('{}\n')
    with pytest.raises(ValueError,match='identity'):
        verify_artifacts(destination)


@pytest.mark.parametrize('identifier',['C:/outside/result.json','C:result.json','nested/file:stream.json'])
def test_portable_artifact_paths_reject_windows_drives_and_streams(tmp_path,identifier):
    root=tmp_path/'repo'
    root.mkdir()
    with pytest.raises(ValueError):
        atomic_record(root,root/'results'/'experiments'/'one',{identifier:{}})
