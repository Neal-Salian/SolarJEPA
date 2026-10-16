"""Metadata and authorization boundaries; no scientific inputs or optimizers."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIGEST = 'ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624'


def api():
    return importlib.import_module('solar_flare_jepa.experiments.v2_pilot_protocol')


def approval_for(root, runtime, output):
    history = api().load_protocol(ROOT)['design']['data']['normalization']
    identity = dict(dataset_fingerprint=history['historical_expected_dataset_fingerprint'],
        forecast_fingerprint='094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94', split_fingerprint=history['historical_expected_split_fingerprint'],
        split_fingerprints=dict(train='e79a5074c3323f771a8cc40c3dde7a1c8f61747f5ed90f827c450fbb9b6f0c9d', validation='707588906ec567b711d60f53fcd7ec81934755a3cb3df24d9df6837e67a68677'),
        training_fingerprint=history['historical_expected_training_fingerprint'],
        normalization_fingerprint=history['historical_expected_fingerprint'],
        train_windows=dict(eligible=20001,used=20000,stride=1,cap=20000,policy='complete_consecutive_raw_training_rows',subsample='evenly_spaced_chronological',fingerprint='a'*64), validation_content_fingerprint='b' * 64)
    return dict(data_identity=identity, schema_version=1, kind='solarjepa_v2_pilot_execution_approval', approval_status='APPROVED',
        authorized_by='synthetic owner', approved_utc='2026-10-16T00:00:00Z',
        protocol_id='solarjepa.phase2.v2.development.v1', design_fingerprint=DIGEST,
        execution_authorized=True, data_fitting_authorized=True, test_release_authorized=False,
        scope='EXPOSED_DEVELOPMENT_FEASIBILITY_ONLY', source_root=str(root), data_root=str(root),
        output_root=str(output), runtime_fingerprint=runtime['fingerprint'],
        configuration_fingerprint=api().configuration_fingerprint(api().load_protocol(ROOT)['design']),
        host_reservation=dict(reserved=True, host_fingerprint=runtime['host_fingerprint'], rationale='synthetic test only'))


def test_protocol_exact_design_and_twenty_job_graph():
    protocol = api().load_protocol(ROOT)
    assert protocol['design_fingerprint'] == DIGEST
    jobs = protocol['design']['jobs']
    assert len(jobs) == 20 and len({j['job_id'] for j in jobs}) == 20
    assert sum(j['development_run'] == 'primary' for j in jobs) == 14
    assert sum(j['development_run'] == 'alternate_loss' for j in jobs) == 4
    assert protocol['design']['resources']['max_retries'] == 0


def test_protocol_design_drift_fails_before_source_access(tmp_path):
    target = tmp_path / 'docs/protocols/phase2_v2_development_v1.json'
    target.parent.mkdir(parents=True)
    protocol = json.loads((ROOT / 'docs/protocols/phase2_v2_development_v1.json').read_text())
    protocol['design']['resources']['max_retries'] = 1
    target.write_text(json.dumps(protocol))
    with pytest.raises(ValueError, match='fingerprint|design'):
        api().load_protocol(tmp_path)


def test_missing_approval_fails_before_runtime_or_output(monkeypatch, tmp_path):
    monkeypatch.setattr(api(), 'runtime_identity', lambda root: pytest.fail('runtime touched'))
    with pytest.raises(PermissionError, match='approval'):
        api().validate_execution(ROOT, None)
    assert list(tmp_path.iterdir()) == []


def test_broad_approval_fails_before_runtime(monkeypatch):
    monkeypatch.setattr(api(), 'runtime_identity', lambda root: pytest.fail('runtime touched'))
    with pytest.raises(PermissionError):
        api().validate_execution(ROOT, {'execution_authorized': True})


def test_matching_external_binding_and_stale_runtime(monkeypatch, tmp_path):
    runtime = dict(fingerprint='runtime', host_fingerprint='host', source_fingerprint='source')
    monkeypatch.setattr(api(), 'runtime_identity', lambda root: runtime)
    approval = approval_for(ROOT, runtime, tmp_path / 'new-output')
    context = api().validate_execution(ROOT, approval)
    assert context['runtime'] == runtime and context['design']['seeds'] == [1261866429, 1291916211]
    approval['runtime_fingerprint'] = 'stale'
    with pytest.raises(PermissionError, match='runtime'):
        api().validate_execution(ROOT, approval)
    assert not (tmp_path / 'new-output').exists()


@pytest.mark.parametrize('field,value', [('test_release_authorized', True), ('data_fitting_authorized', False),
    ('design_fingerprint', 'fake'), ('extra_execution_override', True)])
def test_approval_never_broadens_or_invents_authorization(monkeypatch, tmp_path, field, value):
    runtime = dict(fingerprint='runtime', host_fingerprint='host', source_fingerprint='source')
    monkeypatch.setattr(api(), 'runtime_identity', lambda root: runtime)
    approval = approval_for(ROOT, runtime, tmp_path / 'new-output')
    approval[field] = value
    with pytest.raises(PermissionError):
        api().validate_execution(ROOT, approval)


def test_approval_requires_fixed_input_identity(monkeypatch, tmp_path):
    runtime = dict(fingerprint='runtime', host_fingerprint='host', source_fingerprint='source')
    monkeypatch.setattr(api(), 'runtime_identity', lambda root: runtime)
    approval = approval_for(ROOT, runtime, tmp_path / 'new-output')
    approval.pop('data_identity', None)
    with pytest.raises(PermissionError, match='fields|data identity'):
        api().validate_execution(ROOT, approval)


@pytest.mark.parametrize('damage', ['invalid_validation_hash', 'invalid_split_hashes', 'incomplete_subset'])
def test_declared_data_identity_must_be_complete_and_consistent(monkeypatch, tmp_path, damage):
    runtime = dict(fingerprint='runtime', host_fingerprint='host', source_fingerprint='source')
    monkeypatch.setattr(api(), 'runtime_identity', lambda root: runtime)
    approval = approval_for(ROOT, runtime, tmp_path / 'new-output')
    identity = approval['data_identity']
    if damage == 'invalid_validation_hash':
        identity['validation_content_fingerprint'] = 'z' * 64
    elif damage == 'invalid_split_hashes':
        identity['split_fingerprints'] = dict(train='a'*64, validation='b'*64)
    else:
        identity['train_windows'] = {}
    with pytest.raises(PermissionError, match='identity|support'):
        api().validate_execution(ROOT, approval)
