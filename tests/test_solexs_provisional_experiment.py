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
