"""Real synthetic preparation, with only Git/package publication preflight replaced."""
from copy import deepcopy
import hashlib
import json
import pytest
from test_external_validation import history
from test_external_config import fixture
from test_flare_catalog import config as catalog_config, Response
from solar_flare_jepa.data import flare_catalog
from solar_flare_jepa.data import external_validation as external
from solar_flare_jepa.experiments import provenance


def setup(tmp_path,monkeypatch):
    manifest,_=history(tmp_path,monkeypatch)
    stage=tmp_path/'synthetic_catalog'
    staged,spec,bodies=catalog_config(stage)
    catalog_path=tmp_path/'configs/data/flare_catalog_2025.json'
    catalog_path.write_bytes(staged.read_bytes())
    monkeypatch.setattr(flare_catalog,'open_history_url',lambda url,timeout:Response(bodies['metadata' if url.endswith('.json') else 'catalog']))
    flare_catalog.acquire_catalog(catalog_path,tmp_path)
    value=fixture();value['forecast'].update(context_steps=1,horizon_steps=1,stride_steps=1)
    config=tmp_path/'configs/evaluation/external.json';config.parent.mkdir(parents=True)
    config.write_text(json.dumps(value))
    monkeypatch.setattr(provenance,'code_provenance',lambda root:{'source':{'files':[]},'interpretation':'synthetic_preflight_only'})
    return config


def test_preparation_publishes_separate_predictor_inputs_targets_and_labels(tmp_path,monkeypatch):
    config=setup(tmp_path,monkeypatch)
    result=external.prepare_external_validation(config,tmp_path,'results/experiments/prepared')
    assert result['retained_origins']==1
    assert result['fit_performed'] is False and result['model_predictions']=='NOT_RUN'
    assert result['config_sha256']==hashlib.sha256(config.read_bytes()).hexdigest()
    output=tmp_path/'results/experiments/prepared'
    context=json.loads((output/'contexts.json').read_text())
    assert set(context)=={'dataset_fingerprint','spec','origin_ids','issue_times_ns','starts_ns','ends_ns','values','mask','availability_ns'}
    assert context['ends_ns'][0][-1]==context['issue_times_ns'][0]
    assert (output/'onset_labels_M.json').is_file()
    assert not (output/'model_metrics.json').exists()
    with pytest.raises((ValueError,FileExistsError)):
        external.prepare_external_validation(config,tmp_path,'results/experiments/prepared')


@pytest.mark.parametrize('resource',['config','goes_manifest','catalog_manifest','goes_config','catalog_config','raw_goes','raw_catalog'])
def test_consumed_input_changes_are_rejected_before_any_publication(tmp_path,monkeypatch,resource):
    config=setup(tmp_path,monkeypatch)
    cfg=json.loads(config.read_text())
    manifests={name:tmp_path/cfg[name] for name in ('goes_manifest','catalog_manifest')}
    goes=json.loads(manifests['goes_manifest'].read_text());catalog=json.loads(manifests['catalog_manifest'].read_text())
    path={'config':config,**manifests,'goes_config':tmp_path/goes['config_path'],
          'catalog_config':tmp_path/catalog['config_path'],
          'raw_goes':tmp_path/goes['files'][0]['path'],
          'raw_catalog':tmp_path/catalog['resources'][0]['path']}[resource]
    real=external.build_external_windows
    def changed(*args):
        result=real(*args)
        if path.suffix=='.json':
            value=json.loads(path.read_text());value['injected_after_consumption']=True
            path.write_text(json.dumps(value))
        else:path.write_bytes(path.read_bytes()+b'changed')
        return result
    monkeypatch.setattr(external,'build_external_windows',changed)
    with pytest.raises(ValueError):
        external.prepare_external_validation(config,tmp_path,'results/experiments/rejected')
    assert not (tmp_path/'results/experiments/rejected').exists()
