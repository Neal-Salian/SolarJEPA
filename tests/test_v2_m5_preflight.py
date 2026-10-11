"""M5 planning cannot authorize fitting, test release, or inference."""
from copy import deepcopy
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def api():
    return importlib.import_module('solar_flare_jepa.experiments.v2_m5_preflight')


def forbid_model_imports(monkeypatch):
    import builtins
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name in ('solar_flare_jepa.training.controlled', 'solar_flare_jepa.training.jepa',
                    'solar_flare_jepa.training.comparators'):
            raise AssertionError('Preflight tried to import a model implementation')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)


def test_plan_has_two_seed_linear_paths_and_all_controlled_arms():
    plan = api().build_plan(ROOT)
    assert plan['estimated_job_count'] == 20
    assert plan['quantile_linear_candidate_fits'] == 14
    assert len([j for j in plan['jobs'] if j['kind'] == 'quantile_linear']) == 2
    for seed in plan['seeds']:
        assert {j['arm'] for j in plan['jobs'] if j['seed'] == seed and j['cohort'] == 'primary'} == {
            'jepa_finetune', 'supervised', 'supervised_extra_updates', 'jepa_frozen', 'random_frozen'}
    assert plan == api().build_plan(ROOT)


def test_register_covers_every_required_decision_and_has_no_approvals():
    plan = api().build_plan(ROOT)
    register = api().load_approval_register(ROOT, plan['configuration_fingerprint'])
    assert len(register['decisions']) == 17
    assert all(d['status'] != 'APPROVED' for d in register['decisions'])
    assert api().check_approvals(register, plan['configuration_fingerprint']) == sorted(
        d['identifier'] for d in register['decisions'])


@pytest.mark.parametrize('mutation', ['fingerprint', 'omission', 'duplicate', 'approval', 'policy'])
def test_invalid_or_invented_approval_records_rejected(mutation):
    plan = api().build_plan(ROOT)
    reg = deepcopy(api().load_approval_register(ROOT, plan['configuration_fingerprint']))
    if mutation == 'fingerprint':
        reg['decisions'][0]['configuration_fingerprint'] = '0' * 64
    elif mutation == 'omission':
        reg['decisions'].pop()
    elif mutation == 'duplicate':
        reg['decisions'][0] = reg['decisions'][1]
    elif mutation == 'approval':
        reg['decisions'][0]['status'] = 'APPROVED'
    else:
        reg['decisions'][0]['proposed_policy'] = 'invented change'
    with pytest.raises(ValueError):
        api().check_approvals(reg, plan['configuration_fingerprint'])


def test_missing_files_report_failure_without_any_model_import(tmp_path, monkeypatch):
    # The real loader must detect missing files before normalization/windowing.
    import shutil
    for relative in ('configs', 'data/manifests'):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    forbid_model_imports(monkeypatch)
    evidence = api().inspect_data(tmp_path)
    assert evidence['status'] == 'DATA_NOT_READY'
    assert evidence['missing_files'] == 92
    assert evidence['dataset_fingerprint'] is None
    assert evidence['test_windows_built'] is False


def test_missing_manifest_is_a_data_readiness_failure(tmp_path):
    evidence = api().inspect_data(tmp_path)
    assert evidence['status'] == 'DATA_NOT_READY'
    assert evidence['dataset_fingerprint'] is None
    assert evidence['reason']


def test_metadata_dry_run_is_blocked_deterministic_and_no_optimizer(monkeypatch):
    forbid_model_imports(monkeypatch)
    first = api().preflight(ROOT, verify_data=False)
    assert first == api().preflight(ROOT, verify_data=False)
    assert first['execution_readiness'] == 'PILOT_NOT_AUTHORIZED'
    assert first['data_readiness']['status'] == 'NOT_CHECKED'
    assert len(first['outstanding_approvals']) == 17
    assert first['statistical_reporting'] == ['DESCRIPTIVE_ONLY', 'INFERENCE_UNAVAILABLE']
    assert first['test_release_permitted'] is False
    assert first['training_executed'] is False


def test_amendment_requires_unchanged_original_proposal(tmp_path):
    import json
    import shutil
    shutil.copytree(ROOT / 'configs', tmp_path / 'configs')
    proposal = tmp_path / 'configs/v2_proposed/feasibility_pilot_proposal.json'
    changed = json.loads(proposal.read_text())
    changed['approved'] = True
    proposal.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='proposal'):
        api().build_plan(tmp_path)


def test_metadata_preflight_publishes_immutable_evidence(tmp_path):
    from solar_flare_jepa.experiments.provenance import atomic_record, verify_artifacts
    record = api().preflight(ROOT, verify_data=False)
    target = 'results/experiments/m5-preflight'
    output = atomic_record(tmp_path, target, {'preflight.json': record})
    assert verify_artifacts(output)['files'][0]['path'] == 'preflight.json'
    with pytest.raises(FileExistsError):
        atomic_record(tmp_path, target, {'preflight.json': record})


@pytest.mark.parametrize('mutation', ['boolean_schema', 'null_decision', 'invalid_status'])
def test_malformed_register_is_consistently_rejected(mutation):
    plan = api().build_plan(ROOT)
    reg = deepcopy(api().load_approval_register(ROOT, plan['configuration_fingerprint']))
    if mutation == 'boolean_schema':
        reg['schema_version'] = True
    elif mutation == 'null_decision':
        reg['decisions'][0] = None
    else:
        reg['decisions'][0]['status'] = []
    with pytest.raises(ValueError):
        api().check_approvals(reg, plan['configuration_fingerprint'])


def test_source_change_during_data_check_blocks_result(monkeypatch):
    from solar_flare_jepa.experiments import provenance
    original = provenance.code_provenance
    changed = False
    def observed(*args, **kwargs):
        result = original(*args, **kwargs)
        if changed:
            result['source']['fingerprint'] = '0' * 64
        return result
    def data(*args):
        nonlocal changed
        changed = True
        return {'status': 'DATA_NOT_READY'}
    monkeypatch.setattr(provenance, 'code_provenance', observed)
    monkeypatch.setattr(api(), 'inspect_data', data)
    with pytest.raises(ValueError, match='changed'):
        api().preflight(ROOT)
