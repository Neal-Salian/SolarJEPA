"""Frozen input boundary: authenticate first, preserve canonical support, never fit."""
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastSpec, canonical_json, fingerprint_payload
from solar_flare_jepa.training.jepa import JepaConfig, MODEL_IDS, build_jepa_model
from solar_flare_jepa.training.normalization import Normalization
from solar_flare_jepa.training.core import _weights_fingerprint


ROOT = Path(__file__).resolve().parents[1]
START = 1735689600000000000
END = 1738368000000000000
MINUTE = 60_000_000_000


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + '\n')


def identity(path, name=None):
    payload = path.read_bytes()
    result = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    return result if name is None else dict(path=name, **result)


def seal(fixture):
    """Re-pin intentional semantic changes; corruption tests deliberately skip this."""
    v1, prep, protocol = fixture
    index = dict(schema_version=1, files=[identity(p, p.name) for p in sorted(prep.iterdir())
                                         if p.name != 'artifacts.json'])
    write_json(prep/'artifacts.json', index)
    ledger_path = Path(protocol['code_root'])/protocol['readiness_ledger']['path']
    ledger = json.loads(ledger_path.read_text())
    ledger['checkpoint_audit']['artifacts'] = {p.name: identity(p) for p in v1.iterdir()}
    ledger['dataset_audit']['acceptance']['d']['artifacts'] = [
        dict(name=p.name, **identity(p)) for p in sorted(prep.iterdir())]
    write_json(ledger_path, ledger)
    protocol['readiness_ledger'] = identity(ledger_path, protocol['readiness_ledger']['path'])


@pytest.fixture
def frozen_fixture(tmp_path, monkeypatch):
    import torch
    # Removing hash, support, cohort or metadata checks must break these tests.
    protocol = json.loads((ROOT/'configs/evaluation/goes_v1_external_january2025.json').read_text())
    code = tmp_path/'code'
    protocol['code_root'] = str(code)
    for directory in ('scripts', 'configs/experiments'):
        (code/directory).mkdir(parents=True, exist_ok=True)
    for name in ('src/example.py', 'pyproject.toml', 'requirements-lock.txt',
                 'schemas/experiment_result.schema.json'):
        path = code/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}\n' if name.endswith('.json') else '# synthetic fixture source\n')
    vroot, proot = tmp_path/'v1', tmp_path/'external'
    v1, prep = vroot/'results/experiments/original', proot/'results/experiments/prepared'
    v1.mkdir(parents=True)
    prep.mkdir(parents=True)
    spec = ForecastSpec(**protocol['forecast'])
    norm = Normalization(spec, (-7., -5.), (1., 1.), (-7., -5.), (1., 1.),
                         (100, 100), (100, 100), 'synthetic-raw-support')
    config = JepaConfig(width=8, depth=1, heads=1, predictor_depth=1, head_hidden=8,
                        batch_size=256, threads=1)
    base_config = config.as_dict()
    base_config.pop('seed')
    split_manifest = [dict(partition=dict(name=x['name'], start_ns=int(__import__('pandas').Timestamp(x['start_utc']).value),
                        end_ns=int(__import__('pandas').Timestamp(x['end_utc']).value))) for x in protocol['v1_support']]
    summary = dict(status='complete', quick=False, failures=[],
        config=dict(forecast=protocol['forecast'], splits=protocol['v1_support'],
                    dataset=dict(kind='goes_historical_multi', manifests=['data/manifests/train.json'])),
        dataset=dict(fingerprint='synthetic-v1-dataset', starts_ns=1714521600000000000,
                     ends_ns=1725148800000000000, metadata=dict(manifest_sha256=[])),
        split_manifest=split_manifest, fits={}, models_config=dict(jepa=dict(
            config=base_config, seeds=[17, 29, 43], variants=['jepa_finetune','jepa_frozen','supervised'])),
        selections=dict(arima=dict(selected='arima(2,1,0)')),
        provenance=dict(git_commit='historical-synthetic-commit', source=dict(files=[], fingerprint='historical-source')))
    for planned in protocol['checkpoint_cohort']:
        cfg = dict(config.as_dict(), seed=planned['seed'])
        record = dict(config=cfg, variant=planned['variant'], seed=planned['seed'],
            model_id=MODEL_IDS[planned['variant']], model_kind='temporal_jepa_quantile',
            training_fingerprint='synthetic-training', training_dataset_fingerprint='synthetic-v1-dataset',
            normalization_fingerprint=norm.fingerprint, spec_fingerprint=spec.fingerprint)
        state = build_jepa_model(spec, JepaConfig(**cfg)).state_dict()
        payload = dict(schema_version=1, model_kind='temporal_jepa_quantile', variant=planned['variant'],
            model_id=record['model_id'], config_json=canonical_json(cfg), record_json=canonical_json(record),
            normalization_json=canonical_json(norm.as_dict()), model_state=state,
            weights_fingerprint=_weights_fingerprint(state), torch_version=str(torch.__version__))
        torch.save(payload, v1/planned['path'])
        summary['fits'][planned['model']] = dict(record=record)
    for name in protocol['classical_models']:
        summary['fits'][name] = dict(parameters=dict(name=name, spec_fingerprint=spec.fingerprint,
            dataset_fingerprint='synthetic-v1-dataset', training_fingerprint='synthetic-training',
            split_fingerprint='synthetic-train-split', transform='log10',
            feature_reference=[1.,1.], target_reference=[1.,1.]))
    write_json(v1/'summary.json', summary)
    write_json(v1/'per_origin.json', {})
    np.savez(v1/'test_predictions.npz', synthetic=np.ones((1,)))
    protocol['historical_input_files'] = []
    for name, value in [('configs/experiments/v1_goes_2024.json', summary['config']),
                        ('configs/experiments/v1_models.json', summary['models_config']),
                        ('data/manifests/train.json', {'synthetic': True})]:
        write_json(vroot/name, value)
        protocol['historical_input_files'].append(identity(vroot/name, name))
    protocol['preparation_input_files'] = []
    issues = np.array([START+120*MINUTE, START+150*MINUTE, START+210*MINUTE], dtype=np.int64)
    ids = [f'origin:{x}' for x in issues]
    starts = issues[:,None] + np.arange(-120,0)[None,:]*MINUTE
    future = issues[:,None] + np.arange(30)[None,:]*MINUTE
    common = dict(spec=protocol['forecast'], dataset_fingerprint='synthetic-external-dataset',
                  issue_times_ns=issues.tolist(), origin_ids=ids)
    context = dict(**common, starts_ns=starts.tolist(), ends_ns=(starts+MINUTE).tolist(),
        values=np.full((3,120,2),1e-6).tolist(), mask=np.ones((3,120,2),bool).tolist(), availability_ns=None)
    grid = dict(**common, starts_ns=future.tolist(), ends_ns=(future+MINUTE).tolist())
    targets = dict(grid=grid, values=np.full((3,30,2),2e-6).tolist(), mask=np.ones((3,30,2),bool).tolist())
    support = [dict(origin_id=i, issue_time_ns=int(t), start_ns=int(t-120*MINUTE),
        end_ns=int(t+30*MINUTE), feature_lookback_start_ns=int(t-120*MINUTE),
        context_start_ns=int(t-120*MINUTE), context_end_ns=int(t), target_start_ns=int(t),
        target_end_ns=int(t+30*MINUTE), label_maturity_ns=int(t+30*MINUTE), event_group_ids=[])
        for i,t in zip(ids,issues)]
    excluded = [dict(origin_id=f'origin:{t}', issue_time_ns=t, reasons=['invalid_features'])
                for t in range(START,END,30*MINUTE) if t not in issues]
    window = dict(spec=protocol['forecast'], spec_fingerprint=spec.fingerprint,
        dataset_fingerprint=common['dataset_fingerprint'], partition=dict(name='test',start_ns=START,end_ns=END),
        origin_policy='dataset_origin_stride_grid_partition_issue_half_open',
        retained_origins=ids, support_manifest=support, excluded_origins=excluded,
        raw_starts_ns=[START], raw_ends_ns=[START+MINUTE])
    prep_summary = dict(fit_performed=False, forecast=protocol['forecast'], spec_fingerprint=spec.fingerprint,
        dataset_fingerprint=common['dataset_fingerprint'], split_fingerprint=fingerprint_payload(window),
        retained_origins=3, excluded_origins=1485, valid_target_cells=180,
        operational_benchmark_status='BLOCKED_EXTERNAL_EVIDENCE')
    for name,value in [('contexts.json',context),('future_grid.json',grid),('targets.json',targets),
                       ('window_manifest.json',window),('summary.json',prep_summary),
                       ('dataset_manifest.json',dict(actual_operational_delivery='UNKNOWN',
                        native_preprocessing_causality='UNKNOWN',preprocessing=dict(fit_performed=False),
                        sources=[])),('resolved_config.json',dict(forecast=protocol['forecast']))]:
        write_json(prep/name,value)
    ledger = dict(schema_version=1, checkpoint_audit=dict(artifacts={},checks=dict(
        normalization=dict(record=norm.as_dict()), reconstruction=dict(training_fingerprint='synthetic-training'))),
        dataset_audit=dict(acceptance=dict(d=dict(artifacts=[]))))
    write_json(code/protocol['readiness_ledger']['path'],ledger)
    fixture = v1,prep,protocol
    seal(fixture)
    # Fail immediately if a validation path starts predicting or fitting.
    def forbidden(*args,**kwargs):
        raise AssertionError('Frozen input verification must never invoke model inference or fitting')
    monkeypatch.setattr('solar_flare_jepa.training.jepa.TrainedJepa.predict', forbidden)
    monkeypatch.setattr('solar_flare_jepa.training.jepa.TrainedJepa.predict_normalized', forbidden)
    monkeypatch.setattr(Normalization, 'fit', forbidden)
    return fixture


def load(fixture):
    module = importlib.import_module('solar_flare_jepa.experiments.external_inputs')
    return module.load_frozen_inputs(*fixture)


def test_retained_grid_matches_candidate_manifest(frozen_fixture):
    result = load(frozen_fixture)
    assert len(result['candidate_issue_times_ns']) == 1488
    assert result['candidate_issue_times_ns'][0] == START
    assert result['candidate_issue_times_ns'][-1] == END-30*MINUTE
    assert result['context'].origin_ids == tuple(f'origin:{START+t*MINUTE}' for t in (120,150,210))
    np.testing.assert_array_equal(result['retained_candidate_indices'], [4,5,7])
    assert len(result['candidate_exclusions']) == 1485
    assert len(result['checkpoint_records']) == 9
    assert list(result['classical_fit_records']) == frozen_fixture[2]['classical_models']
    assert not result['context'].values.flags.writeable


@pytest.mark.parametrize('member', ['contexts.json','artifacts.json'])
def test_tampered_member_rejected_before_predict(frozen_fixture, member):
    path=frozen_fixture[1]/member
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='identity'):
        load(frozen_fixture)


@pytest.mark.parametrize('change', ['missing','duplicate'])
def test_missing_or_duplicate_planned_seed_rejected(frozen_fixture,change):
    path=frozen_fixture[0]/'summary.json'
    summary=json.loads(path.read_text())
    if change=='missing':
        del summary['fits']['supervised_seed43']
    else:
        summary['fits']['supervised_seed43']['record']['seed']=29
    write_json(path,summary)
    seal(frozen_fixture)
    with pytest.raises(ValueError,match='cohort|seed|record'):
        load(frozen_fixture)


@pytest.mark.parametrize('change', ['channel','spec'])
def test_spec_and_channel_order_mismatch_rejected(frozen_fixture,change):
    path=frozen_fixture[1]/'contexts.json'
    context=json.loads(path.read_text())
    if change=='channel':
        context['spec']['feature_names'].reverse()
    else:
        context['spec']['stride_steps']=1
    write_json(path,context)
    seal(frozen_fixture)
    with pytest.raises(ValueError,match='spec|align'):
        load(frozen_fixture)


@pytest.mark.parametrize('partition', ['train','validation','test'])
def test_full_v1_support_overlap_rejected(frozen_fixture,partition):
    path=frozen_fixture[0]/'summary.json'
    summary=json.loads(path.read_text())
    row=next(x for x in summary['split_manifest'] if x['partition']['name']==partition)
    row['partition']['end_ns']=END
    write_json(path,summary)
    seal(frozen_fixture)
    with pytest.raises(ValueError,match='support|overlap'):
        load(frozen_fixture)


def test_missing_candidate_rejected(frozen_fixture):
    path=frozen_fixture[1]/'window_manifest.json'
    window=json.loads(path.read_text());window['excluded_origins'].pop()
    write_json(path,window)
    summary_path=frozen_fixture[1]/'summary.json'
    summary=json.loads(summary_path.read_text());summary['split_fingerprint']=fingerprint_payload(window)
    write_json(summary_path,summary)
    seal(frozen_fixture)
    with pytest.raises(ValueError,match='candidate|count'):
        load(frozen_fixture)


def test_symlink_locator_rejected(frozen_fixture,tmp_path):
    link=tmp_path/'redirect';link.symlink_to(frozen_fixture[0],target_is_directory=True)
    with pytest.raises(ValueError,match='symlink|redirect'):
        load((link,*frozen_fixture[1:]))


def test_runtime_locator_is_separate_from_scientific_identity(frozen_fixture,tmp_path):
    import shutil
    first=load(frozen_fixture)
    protocol=deepcopy(frozen_fixture[2]);new_code=tmp_path/'code-copy'
    shutil.copytree(protocol['code_root'],new_code);protocol['code_root']=str(new_code)
    second=load((*frozen_fixture[:2],protocol))
    assert first['input_identities']==second['input_identities']
    assert first['protocol_fingerprint']==second['protocol_fingerprint']
    assert first['historical_source']['git_commit']=='historical-synthetic-commit'
    assert first['current_source']!=first['historical_source']
    assert str(tmp_path) not in canonical_json(first['input_identities'])


@pytest.mark.parametrize('text', ['{"a":NaN}', '{"a":1,"a":2}', '{"a":1e999}'])
def test_strict_snapshot_json_rejected(frozen_fixture,text):
    (frozen_fixture[1]/'dataset_manifest.json').write_text(text)
    seal(frozen_fixture)
    with pytest.raises(ValueError):
        load(frozen_fixture)


def test_reverification_rejects_later_input_mutation(frozen_fixture):
    frozen=load(frozen_fixture)
    path=frozen_fixture[0]/'test_predictions.npz';path.write_bytes(path.read_bytes()+b'tamper')
    module=importlib.import_module('solar_flare_jepa.experiments.external_inputs')
    with pytest.raises(ValueError,match='identity'):
        module.reverify_frozen_inputs(frozen,*frozen_fixture)


@pytest.mark.parametrize('field,value', [
    ('metrics', dict(primary_loss='native_pinball', secondary_paired_loss='log10_dex_mae',
                     quantile_weights=[1]*5, lead_weights=[1]*30, channel_weights=[1,1],
                     rmse_reduction='sqrt_pooled_squared_error')),
    ('full_external_execution','already_approved'),
    ('exposure', dict(acquisition_commit='28e222ba042b32c84dad49a446f0849c677af4b9',
                     documentation_commit='bd128295c8529e064473e483751ca747de2f57a5',
                     prior_january_inspection='OBSERVED', unrecorded_access='KNOWN_NONE',
                     confirmatory_status='AVAILABLE')),
])
def test_changed_scientific_protocol_rejected(frozen_fixture,field,value):
    protocol=deepcopy(frozen_fixture[2]);protocol[field]=value
    with pytest.raises(ValueError,match='protocol|scope|exposure|metric'):
        load((*frozen_fixture[:2],protocol))


def test_consumes_authenticated_snapshot_and_rechecks_at_publication(frozen_fixture,monkeypatch):
    module=importlib.import_module('solar_flare_jepa.experiments.external_inputs')
    verify=module.verify_artifacts
    def mutate_after_verification(directory):
        result=verify(directory)
        path=directory/'contexts.json'
        context=json.loads(path.read_text());context['values'][0][0][0]=9e-6
        write_json(path,context)
        return result
    monkeypatch.setattr(module,'verify_artifacts',mutate_after_verification)
    frozen=load(frozen_fixture)
    assert frozen['context'].values[0,0,0]==1e-6
    with pytest.raises(ValueError,match='identity'):
        module.reverify_frozen_inputs(frozen,*frozen_fixture)


def test_member_symlink_rejected_even_when_target_bytes_match(frozen_fixture,tmp_path):
    path=frozen_fixture[1]/'contexts.json';target=tmp_path/'contexts-copy.json'
    target.write_bytes(path.read_bytes());path.unlink();path.symlink_to(target)
    with pytest.raises(ValueError,match='symlink|redirect'):
        load(frozen_fixture)


def test_path_traversal_locator_rejected(frozen_fixture):
    v1,prep,protocol=frozen_fixture
    with pytest.raises(ValueError,match='traversal'):
        load((v1/'..'/v1.name,prep,protocol))


def test_checkpoint_internal_weight_mismatch_rejected(frozen_fixture):
    import torch
    path=frozen_fixture[0]/'supervised_seed43.pt'
    payload=torch.load(path,weights_only=True,map_location='cpu')
    payload['weights_fingerprint']='wrong-internal-state-identity'
    torch.save(payload,path);seal(frozen_fixture)
    with pytest.raises(ValueError,match='weight identity'):
        load(frozen_fixture)


def test_checkpoint_nonfinite_json_rejected(frozen_fixture):
    import torch
    path=frozen_fixture[0]/'supervised_seed43.pt'
    payload=torch.load(path,weights_only=True,map_location='cpu')
    payload['record_json']='{"loss":1e999}'
    torch.save(payload,path);seal(frozen_fixture)
    with pytest.raises(ValueError,match='finite JSON'):
        load(frozen_fixture)
