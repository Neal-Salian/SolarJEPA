import importlib
import importlib.util
from pathlib import Path
import hashlib

import numpy as np
import pytest

from test_solexs import archive_fixture, product_bytes


def api():
    name='solar_flare_jepa.provisional.experiment'
    assert importlib.util.find_spec(name), 'provisional runner missing'
    return importlib.import_module(name)


def test_config_refuses_physical_labels_bad_splits_and_overlap():
    config=api().load_config(Path(__file__).parents[1]/'configs/experiments/solexs_provisional_v1.json')
    for changes in [{'scientific_label':'SCIENTIFICALLY_VALIDATED'}, {'horizon_samples':0},
                    {'stride_samples':1}, {'train_stop_row':86400}, {'extra':1}]:
        with pytest.raises(ValueError): api().validate_config(dict(config,**changes))


def test_archive_or_expanded_identity_mismatch_refuses_loading(tmp_path):
    record,members=archive_fixture(tmp_path,[('lc','SDD2',product_bytes())])
    selection=dict(path=record['path'],sha256=record['sha256'],bytes=record['bytes'],member=members[0],
                   fits_sha256='0'*64,nominal_date='2024-07-01')
    with pytest.raises(ValueError,match='expanded'):
        api().load_selected_sequence(tmp_path,record,selection)
    selection['sha256']='1'*64
    with pytest.raises(ValueError,match='archive'):
        api().load_selected_sequence(tmp_path,record,selection)


def test_publish_is_exclusive_and_artifact_tampering_is_detected(tmp_path):
    stage=tmp_path/'results/experiments/.stage-test'
    stage.mkdir(parents=True)
    (stage/'report.json').write_text('{"scientific_label":"EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED"}')
    np.savez_compressed(stage/'predictions.npz',scientific_label=np.array('EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED'),values=[1,2])
    dest=tmp_path/'results/experiments/trial'
    api().publish_stage(stage,dest)
    api().verify_outputs(dest)
    other=tmp_path/'results/experiments/.stage-other';other.mkdir()
    with pytest.raises(FileExistsError): api().publish_stage(other,dest)
    assert (dest/'report.json').exists()
    (dest/'predictions.npz').write_bytes(b'bad')
    with pytest.raises(ValueError): api().verify_outputs(dest)


def test_publisher_rejects_outside_results_and_symlink_destinations(tmp_path):
    stage=tmp_path/'stage';stage.mkdir()
    with pytest.raises(ValueError):api().publish_stage(stage,tmp_path/'data/raw/new')
    target=tmp_path/'target';target.mkdir()
    parent=tmp_path/'results/experiments';parent.mkdir(parents=True)
    (parent/'redirect').symlink_to(target,target_is_directory=True)
    with pytest.raises(FileExistsError):api().publish_stage(stage,parent/'redirect')


@pytest.mark.parametrize('changes',[{'context_samples':32},{'horizon_samples':4},{'stride_samples':16},
                                     {'train_stop_row':50000},{'expected_rows':90000}])
def test_frozen_v1_numerical_contract_cannot_silently_change(changes):
    config=api().load_config(Path(__file__).parents[1]/'configs/experiments/solexs_provisional_v1.json')
    with pytest.raises(ValueError): api().validate_config(dict(config,**changes))


@pytest.mark.parametrize('changes',[{'seed':1},{'epochs':2},{'batch_size':64},
                                     {'learning_rate':.01},{'gradient_clip':2.}])
def test_frozen_v1_neural_budget_cannot_silently_change(changes):
    config=api().load_config(Path(__file__).parents[1]/'configs/experiments/solexs_provisional_v1.json')
    config['neural'].update(changes)
    with pytest.raises(ValueError): api().validate_config(config)


def test_runtime_provenance_does_not_require_optional_test_dependency(monkeypatch):
    runner=api(); original=runner.version
    from importlib.metadata import PackageNotFoundError
    def runtime_only(name):
        if name=='pytest': raise PackageNotFoundError(name)
        return original(name)
    monkeypatch.setattr(runner,'version',runtime_only)
    assert callable(getattr(runner,'runtime_versions',None)), 'runtime versions helper missing'
    versions=runner.runtime_versions()
    assert set(versions)=={'numpy','astropy','torch'}
    assert all(versions.values())


def test_config_and_hash_are_derived_from_the_same_bytes(tmp_path):
    runner=api()
    config_path=Path(__file__).parents[1]/'configs/experiments/solexs_provisional_v1.json'
    data=config_path.read_bytes(); target=tmp_path/'config.json';target.write_bytes(data)
    assert callable(getattr(runner,'load_config_snapshot',None)), 'config snapshot helper missing'
    config,digest=runner.load_config_snapshot(target)
    assert config==runner.load_config(config_path)
    assert digest==hashlib.sha256(data).hexdigest()


def test_publication_rejects_symlink_stage_and_redirected_output_verification(tmp_path):
    outside=tmp_path/'outside';outside.mkdir()
    (outside/'report.json').write_text('{}')
    parent=tmp_path/'results/experiments';parent.mkdir(parents=True)
    stage=parent/'.stage-link';stage.symlink_to(outside,target_is_directory=True)
    dest=parent/'trial'
    with pytest.raises(ValueError):api().publish_stage(stage,dest)
    assert not (outside/'artifacts.json').exists() and not dest.exists()
    real=parent/'.stage-real';real.mkdir();(real/'report.json').write_text('{}')
    api().publish_stage(real,dest)
    redirected=parent/'redirect';redirected.symlink_to(dest,target_is_directory=True)
    with pytest.raises(ValueError):api().verify_outputs(redirected)


def test_stage_must_share_publication_parent(tmp_path):
    stage=tmp_path/'outside-stage';stage.mkdir();(stage/'report.json').write_text('{}')
    parent=tmp_path/'results/experiments';parent.mkdir(parents=True)
    with pytest.raises(ValueError):api().publish_stage(stage,parent/'trial')
    assert stage.exists() and not (stage/'artifacts.json').exists()
