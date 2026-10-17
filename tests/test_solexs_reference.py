"""Artificial arrays and TAR/FITS files; no mission science is a test fixture."""
import copy
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import numpy as np
import pytest

from test_solexs import archive_fixture, product_bytes


def reference():
    assert importlib.util.find_spec('solar_flare_jepa.data.solexs_reference'), 'Reference validator missing'
    return importlib.import_module('solar_flare_jepa.data.solexs_reference')


def tar_fixture(tmp_path, name='solexs_tools-1.1/solexs_tools/time_utils.py', payload=b'reviewed'):
    path = tmp_path/'tools.tar.gz'
    with tarfile.open(path, 'w:gz') as archive:
        member = tarfile.TarInfo(name)
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    return path, {name: dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())}


def test_selected_regular_member_read_preserves_original(tmp_path):
    path, pins = tar_fixture(tmp_path)
    before = path.read_bytes()
    assert reference().read_selected_members(path, pins) == {next(iter(pins)): b'reviewed'}
    assert path.read_bytes() == before


@pytest.mark.parametrize('change', ['digest', 'size', 'missing', 'unsafe', 'symlink', 'duplicate', 'oversize'])
def test_selected_members_fail_closed(tmp_path, change):
    path, pins = tar_fixture(tmp_path)
    name = next(iter(pins))
    if change == 'digest':
        pins[name]['sha256'] = '0'*64
    elif change == 'size':
        pins[name]['bytes'] += 1
    elif change == 'missing':
        pins['solexs_tools-1.1/absent'] = pins.pop(name)
    elif change == 'unsafe':
        path, pins = tar_fixture(tmp_path, '../escape')
    elif change in ('symlink', 'duplicate'):
        with tarfile.open(path, 'w:gz') as archive:
            member = tarfile.TarInfo(name)
            if change == 'symlink':
                member.type = tarfile.SYMTYPE
                member.linkname = '/etc/passwd'
                archive.addfile(member)
            else:
                member.size = 8
                for _ in range(2):
                    archive.addfile(member, io.BytesIO(b'reviewed'))
    kwargs = {'max_member_bytes': 4} if change == 'oversize' else {}
    with pytest.raises(ValueError):
        reference().read_selected_members(path, pins, **kwargs)


def test_manifest_parser_rejects_duplicate_and_nonfinite_json(tmp_path):
    for payload in ('{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}'):
        (tmp_path/'manifest.json').write_text(payload)
        with pytest.raises(ValueError):
            reference().load_reference_manifest(tmp_path, 'manifest.json')


@pytest.mark.parametrize('payload', [[], {}, {'schema_version': True}, {'schema_version': 99}])
def test_malformed_reference_contract_is_refused(tmp_path, payload):
    (tmp_path/'manifest.json').write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        reference().load_reference_manifest(tmp_path, 'manifest.json')


def test_manifest_paths_cannot_escape_root(tmp_path):
    with pytest.raises(ValueError):
        reference().load_reference_manifest(tmp_path, '../outside.json')


def artificial_native(tmp_path):
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes()),
        ('pi', 'SDD2', product_bytes('pi')), ('gti', 'SDD2', product_bytes('gti'))])
    return record


def test_native_witness_is_chunk_independent_and_keeps_unknowns(tmp_path):
    record = artificial_native(tmp_path)
    before = (tmp_path/record['path']).read_bytes()
    api = reference()
    first = api.native_witness(tmp_path, record, (0, 1), np.arange(1, 4), [0, 1, 2], chunk_rows=1)
    second = api.native_witness(tmp_path, record, (0, 1), np.arange(1, 4), [0, 1, 2], chunk_rows=2)
    assert first == second
    assert first['comparison']['rows'] == 3
    assert first['comparison']['finite_compared_rows'] == 2
    assert first['comparison']['pi_nan_rows'] == 1
    assert first['comparison']['pi_channel_labels_equal_rmf'] is False
    assert first['comparison']['mapping_validated'] is False
    assert first['units']['lc']['COUNTS'] is None
    assert first['clocks']['lc']['RATE']['MJDREFF'] == 0.22916666651
    assert first['clocks']['pi']['SPECTRUM']['MJDREFI'] is None
    assert first['cases'][1]['lc'] is None
    assert (tmp_path/record['path']).read_bytes() == before


def test_native_expected_mismatch_fails_with_case_locator(tmp_path):
    record = artificial_native(tmp_path)
    observed = reference().native_witness(tmp_path, record, (0, 1), np.arange(1, 4), [0])
    expected = copy.deepcopy(observed)
    expected['comparison']['rows'] = 4
    with pytest.raises(ValueError, match='native.*comparison'):
        reference().assert_expected(observed, expected, 'native')


def test_reference_comparison_requires_all_expected_values_and_finite_types():
    api = reference()
    api.assert_expected({'a': 1, 'extra': 'retained'}, {'a': 1}, 'test')
    for observed, expected in [({'a': True}, {'a': 1}), ({}, {'a': None}), ({'a': 2}, {'a': 1})]:
        with pytest.raises(ValueError):
            api.assert_expected(observed, expected, 'test')


def test_reference_publication_refuses_existing_output_before_work(tmp_path, monkeypatch):
    destination = tmp_path/'results/experiments/existing'
    destination.mkdir(parents=True)
    (destination/'sentinel').write_text('preserved')
    def forbidden(*args, **kwargs):
        pytest.fail('Existing-output refusal must precede audit/replay')
    monkeypatch.setattr(reference(), 'audit_reference', forbidden)
    with pytest.raises(FileExistsError):
        reference().run_reference_validation('missing.json', project_root=tmp_path,
            data_root=tmp_path, output_dir='results/experiments/existing')
    assert (destination/'sentinel').read_text() == 'preserved'


def contract():
    return json.loads((Path(__file__).resolve().parents[1]/'data/manifests/solexs_reference_cases.json').read_text())


@pytest.mark.parametrize('change', ['unknown_archive', 'unreviewed_member', 'empty_expected', 'duplicate_native'])
def test_manifest_cannot_weaken_reviewed_execution_contract(tmp_path, change):
    manifest = contract()
    if change == 'unknown_archive':
        manifest['tools_archive']['sha256'] = '0'*64
    elif change == 'unreviewed_member':
        manifest['members'][next(iter(manifest['members']))]['sha256'] = '0'*64
    elif change == 'empty_expected':
        manifest['tool_expected']['UTC'] = {}
    else:
        manifest['native'].append(manifest['native'][0])
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        reference().load_reference_manifest(tmp_path, 'manifest.json')


def test_replay_boundary_itself_refuses_changed_payload_before_subprocess(monkeypatch):
    payloads = {'solexs_tools-1.1/'+name: b'unreviewed' for name in reference().SELECTED_MEMBERS}
    def forbidden(*args, **kwargs):
        pytest.fail('Unreviewed source reached subprocess')
    monkeypatch.setattr(reference().subprocess, 'run', forbidden)
    with pytest.raises(ValueError, match='reviewed'):
        reference().replay_tools(payloads)


@pytest.mark.parametrize('missing', [False, True])
def test_changed_or_missing_archive_fails_before_replay(tmp_path, monkeypatch, missing):
    manifest = contract()
    manifest['tools_archive']['path'] = 'tools.tar.gz'
    if not missing:
        (tmp_path/'tools.tar.gz').write_bytes(b'changed official source')
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    def forbidden(*args, **kwargs):
        pytest.fail('Unverified input reached replay')
    monkeypatch.setattr(reference(), 'replay_tools', forbidden)
    with pytest.raises(ValueError, match='identity|Cannot hash'):
        reference().audit_reference('manifest.json', tmp_path)


@pytest.mark.parametrize('path,value', [
    (('tool_expected', 'UTC', 'genlc'), None),
    (('tool_expected', 'UTC', 'genspec'), 7),
    (('native',), [None]),
    (('sources',), [None]),
])
def test_nested_malformed_manifest_is_value_error(tmp_path, path, value):
    manifest = contract()
    target = manifest
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        reference().load_reference_manifest(tmp_path, 'manifest.json')


@pytest.mark.parametrize('case', ['native', 'epoch', 'genlc', 'rebin', 'genspec', 'clock', 'case_row'])
def test_empty_reference_witness_cannot_receive_pass(tmp_path, case):
    manifest = contract()
    if case == 'native':
        manifest['native'][0]['expected'] = {}
    elif case == 'clock':
        manifest['native'][0]['expected']['clocks']['lc']['RATE'] = {}
    elif case == 'case_row':
        manifest['native'][0]['expected']['cases'][0] = {}
    elif case == 'epoch':
        manifest['tool_expected']['UTC']['epoch'] = {}
    elif case == 'genlc':
        for label in manifest['tool_expected']['UTC']['genlc']:
            manifest['tool_expected']['UTC']['genlc'][label] = {}
    elif case == 'rebin':
        for label in manifest['tool_expected']['UTC']['rebin']:
            manifest['tool_expected']['UTC']['rebin'][label] = {}
    else:
        for label in manifest['tool_expected']['UTC']['genspec']:
            manifest['tool_expected']['UTC']['genspec'][label] = {}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='witness|reference'):
        reference().load_reference_manifest(tmp_path, 'manifest.json')


@pytest.mark.parametrize('record,value', [
    ('tools_release', []), ('tools_release', None), ('tools_release', {}),
    ('native_release', []), ('native_release', None), ('native_release', {}),
])
def test_malformed_release_record_cannot_receive_pass(tmp_path, record, value):
    manifest = contract()
    manifest[record] = value
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='reference|release'):
        reference().load_reference_manifest(tmp_path, 'manifest.json')


@pytest.mark.parametrize('record,field,value', [
    ('tools_release', 'tools_version', 'unreviewed'),
    ('tools_release', 'caldb_version', '2'),
    ('native_release', 'data_version', '1.2'),
    ('native_release', 'pipeline_version', '1.2'),
    ('tools_release', 'mission_policy_accepted', True),
    ('native_release', 'mission_policy_accepted', True),
    ('native_release', 'release_date', '2025-01-01'),
    ('native_release', 'nominal_selected_dates', ['2024-07-02']),
])
def test_changed_release_identity_or_approval_cannot_receive_pass(tmp_path, record, field, value):
    manifest = contract()
    manifest[record][field] = value
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='reference|release'):
        reference().load_reference_manifest(tmp_path, 'manifest.json')


def test_complete_reviewed_release_and_witness_contract_is_accepted(tmp_path):
    (tmp_path/'manifest.json').write_text(json.dumps(contract()))
    manifest, _ = reference().load_reference_manifest(tmp_path, 'manifest.json')
    assert manifest['tools_release']['tools_version'] == '1.1'
    assert manifest['tools_release']['caldb_version'] == '1'
    assert manifest['native_release']['data_version'] == '1.1'
    assert manifest['native_release']['pipeline_version'] == '1.1'
    assert manifest['tools_release']['mission_policy_accepted'] is False
    assert manifest['native_release']['mission_policy_accepted'] is False
