"""Offline readiness derives facts from verified bytes; it cannot unlock science."""
import hashlib
import importlib
import json
from pathlib import Path
import zipfile

import pytest

from test_solexs import archive_fixture, product_bytes


def api():
    return importlib.import_module('solar_flare_jepa.data.solexs_integration')


def pin(root, path):
    data = (root/path).read_bytes()
    return dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


GATES = [('E1', 'BLOCKED_EXTERNAL_EVIDENCE'), ('E2', 'BLOCKED_EXTERNAL_EVIDENCE'),
         ('E3', 'BLOCKED_EXTERNAL_EVIDENCE'), ('E4', 'PARTIALLY_VERIFIED'),
         ('E5', 'PARTIALLY_VERIFIED'), ('E6', 'BLOCKED_EXTERNAL_EVIDENCE')]


def inputs(root):
    record, _ = archive_fixture(root, [('lc', 'SDD2', product_bytes()),
                                     ('pi', 'SDD2', product_bytes('pi')),
                                     ('gti', 'SDD2', product_bytes('gti')),
                                     ('gti', 'SDD1', product_bytes('gti', 'SDD1'))])
    phase = root/'phase.json'
    phase.write_text(json.dumps(dict(schema_version=1, gate='BLOCKED_FOR_PHASE_E',
        forecast_training_allowed=False, physical_analysis_allowed=False,
        gates=[dict(id=i, status=s) for i, s in GATES])))
    source = root/'source.txt'; source.write_text('Artificial documentary evidence, not mission authority')
    sources = root/'sources.json'; sources.write_text(json.dumps(dict(sources=[pin(root, 'source.txt')])))
    config = dict(schema_version=1, representation='native',
        inventory=pin(root, 'data/manifests/aditya_inventory.json'),
        phase_e=pin(root, 'phase.json'), source_manifests=[pin(root, 'sources.json')],
        archives=[record['path']], chunk_rows=2, expected_native_step=1)
    p = root/'integration.json';p.write_text(json.dumps(config))
    return p, config, record


def test_real_loader_audit_is_deterministic_portable_and_keeps_all_gates_closed(tmp_path):
    path, _, record = inputs(tmp_path)
    report = api().audit_native_inputs(path, tmp_path)
    assert report == api().audit_native_inputs(path, tmp_path)
    assert report['readiness']['jepa_training_allowed'] is False
    assert report['readiness']['physical_analysis_allowed'] is False
    assert report['readiness']['verdict'] == 'NATIVE_INTERFACE_READY_SCIENCE_BLOCKED'
    assert [(g['id'], g['status']) for g in report['readiness']['gates']] == GATES
    assert str(tmp_path) not in json.dumps(report)
    assert report['inputs']['verified_documentary_sources'][0]['path'] == 'source.txt'
    archive = report['archives'][0]
    assert archive['archive_sha256'] == record['sha256']
    lc = next(p for p in archive['prepared_products'] if p['kind'] == 'lc')
    assert lc['rows'] == 3
    assert lc['numerical_quality']['counts']['nan'] == 1
    assert lc['numerical_quality']['row_flags']['break_before'] == 1
    assert lc['gti']['closed_points'] == 3
    assert lc['gti']['half_open_points'] == 2
    assert lc['gti_provenance']['member'].endswith('SDD2_L1.gti.gz')
    assert archive['native_integrity']['zip_integrity'] == 'verified'


@pytest.mark.parametrize('change', ['gate_hash', 'source_bytes', 'archive_bytes', 'inventory_bytes'])
def test_changed_inputs_never_produce_a_report(tmp_path, change):
    path, _, record = inputs(tmp_path)
    target = dict(gate_hash='phase.json', source_bytes='source.txt',
                  archive_bytes=record['path'], inventory_bytes='data/manifests/aditya_inventory.json')[change]
    with (tmp_path/target).open('ab') as f:
        f.write(b' ')
    with pytest.raises(ValueError):
        api().audit_native_inputs(path, tmp_path)


@pytest.mark.parametrize('change', ['duplicate_gate', 'unknown_gate', 'gate_schema', 'pass_gate',
                                   'training_true', 'unknown_config', 'bool_schema', 'bad_chunk'])
def test_forged_or_unsupported_gate_and_config_cannot_grant_clearance(tmp_path, change):
    path, config, _ = inputs(tmp_path)
    gate = json.loads((tmp_path/'phase.json').read_text())
    if change == 'duplicate_gate': gate['gates'].append(gate['gates'][0])
    if change == 'unknown_gate': gate['gates'][0]['id'] = 'E9'
    if change == 'gate_schema': gate['schema_version'] = 2
    if change == 'pass_gate': gate['gates'][0]['status'] = 'PASS'
    if change == 'training_true': gate['forecast_training_allowed'] = True
    if change == 'unknown_config': config['grant_clearance'] = True
    if change == 'bool_schema': config['schema_version'] = True
    if change == 'bad_chunk': config['chunk_rows'] = 8193
    (tmp_path/'phase.json').write_text(json.dumps(gate))
    config['phase_e'] = pin(tmp_path, 'phase.json')
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):
        api().audit_native_inputs(path, tmp_path)


def test_duplicate_config_fields_fail_before_science_access(tmp_path):
    path, _, _ = inputs(tmp_path)
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match='duplicate'):
        api().audit_native_inputs(path, tmp_path)


def test_evidence_source_symlink_cannot_escape_the_data_root(tmp_path):
    path, _, _ = inputs(tmp_path)
    original = tmp_path/'source.txt';data = original.read_bytes();original.unlink()
    outside = tmp_path.parent/(tmp_path.name+'-outside');outside.write_bytes(data)
    original.symlink_to(outside)
    with pytest.raises(ValueError):
        api().audit_native_inputs(path, tmp_path)


def test_inventory_consumption_uses_the_pinned_snapshot_not_a_second_read(tmp_path, monkeypatch):
    path, _, record = inputs(tmp_path)
    inventory_path = tmp_path/'data/manifests/aditya_inventory.json'
    original_read = Path.read_text
    alternate = json.loads(original_read(inventory_path))
    alternate['files'] = []
    # Simulate a disagreeing second pathname read at the IO boundary. The pinned
    # bytes on disk remain the original inventory throughout the audit.
    def disagreeing_read(p, *args, **kwargs):
        if p == inventory_path:
            return json.dumps(alternate)
        return original_read(p, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', disagreeing_read)
    report = api().audit_native_inputs(path, tmp_path)
    assert report['archives'][0]['archive_sha256'] == record['sha256']


def test_audit_refuses_ambiguous_detector_gti_instead_of_silently_selecting_one(tmp_path):
    from solar_flare_jepa.data.storage import register_archives
    path, config, record = inputs(tmp_path)
    with zipfile.ZipFile(tmp_path/record['path'], 'a') as archive:
        member = next(p for p in archive.namelist() if p.endswith('SDD2_L1.gti.gz'))
        archive.writestr('ANOTHER/'+member, archive.read(member))
    # This is a newly constructed artificial archive, not an immutable input.
    (tmp_path/'data/manifests/aditya_inventory.json').unlink()
    register_archives(tmp_path, [record['path']])
    config['inventory'] = pin(tmp_path, 'data/manifests/aditya_inventory.json')
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='ambiguous|Ambiguous'):
        api().audit_native_inputs(path, tmp_path)
