"""Offline native diagnostics; artificial observations never imply mission validity."""
import hashlib
from dataclasses import fields
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_solexs import ARCHIVE, archive_fixture, product_bytes


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/explore_solexs.py'


def exploration():
    assert importlib.util.find_spec('solar_flare_jepa.data.solexs_exploration'), 'Native exploration API missing'
    return importlib.import_module('solar_flare_jepa.data.solexs_exploration')


def inputs(root, *, limits=None):
    record, _ = archive_fixture(root, [
        ('gti', 'SDD1', product_bytes('gti', 'SDD1')),
        ('gti', 'SDD2', product_bytes('gti')),
        ('lc', 'SDD2', product_bytes('lc')),
        ('pi', 'SDD2', product_bytes('pi')),
    ])
    gate_path = root / 'data/manifests/gate.json'
    gate_path.write_text(json.dumps(dict(gate='BLOCKED_FOR_PHASE_E',
                                        minimum_remaining_evidence=['Unresolved mission clock policy'])))
    config = dict(schema_version=1, inventory_path='data/manifests/aditya_inventory.json',
                  gate_path='data/manifests/gate.json',
                  gate_sha256=hashlib.sha256(gate_path.read_bytes()).hexdigest(),
                  archives=[record['path']], limits=limits or dict(max_plot_points=2, max_plot_spectra=2))
    path = root / 'exploration.json'
    path.write_text(json.dumps(config))
    return record, path


def test_native_output_retains_detector_evidence_units_and_clock_conflict(tmp_path):
    record, config = inputs(tmp_path)
    before = (tmp_path / ARCHIVE).read_bytes()
    report = exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/first')
    assert report['status'] == 'OBSERVED_NATIVE'
    assert report['gate']['status'] == 'BLOCKED_FOR_PHASE_E'
    identities = report['source_identities']
    lc = next(i for i in identities if i['product_kind'] == 'lc')
    assert lc['detector'] == dict(value='SDD2', evidence='OBSERVED', source='FILTER')
    assert lc['native_units'] == ['UNKNOWN', 'UNKNOWN']
    assert lc['column_units'] == dict(TIME=None, COUNTS=None)
    assert lc['native_details']['time_basis']['metadata']['MJDREFF'] == 0.22916666651
    assert lc['native_details']['time_basis']['converted_utc'] is None
    assert lc['provenance']['archive_sha256'] == record['sha256']
    assert 'TIME_REFERENCE_CONFLICT' in lc['native_details']['time_basis']['warnings']
    assert lc['validation_status'] == 'OBSERVED_NATIVE'
    assert lc['native_details']['quality']['scientific_qc'] == 'UNKNOWN_NOT_APPLIED'
    sdd1 = next(d for d in report['detectors'] if d['value'] == 'SDD1')
    assert sdd1['product_kinds'] == ['gti']
    assert sdd1['native_sequence_available'] is False
    assert sdd1['absence_reason'] == 'UNKNOWN'
    assert sdd1['association_evidence'] == ['INFERRED']
    assert report['archives'][0]['zip_integrity'] == 'verified'
    assert report['archives'][0]['products'][0]['rows'] == 0
    assert (tmp_path / ARCHIVE).read_bytes() == before
    assert not list((tmp_path / '.cache').rglob('*.fits'))


def test_common_identity_constructs_and_refuses_training_with_native_details_intact(tmp_path):
    from solar_flare_jepa.data.foundation import SourceIdentity
    _, config = inputs(tmp_path)
    report = exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/common')
    for source in report['source_identities']:
        common = SourceIdentity(**{field.name: source[field.name] for field in fields(SourceIdentity)})
        with pytest.raises(ValueError, match='BLOCKED_FOR_PHASE_E'):
            common.require_training_clearance()
        assert source['detector'] and source['provenance']['member']
        assert source['native_details']['time_basis']['converted_utc'] is None


@pytest.mark.parametrize('representation', ['utc', 'calibrated_flux', 'goes_aligned', 'count_rate'])
def test_unsupported_semantic_conversion_is_refused(representation):
    with pytest.raises(ValueError, match='native|conversion'):
        exploration().validate_request(representation=representation)


def test_sequence_training_is_refused_even_for_native_counts():
    with pytest.raises(ValueError, match='BLOCKED_FOR_PHASE_E'):
        exploration().validate_request(train=True)


def test_every_candidate_task_is_blocked_with_explicit_scientific_dependencies(tmp_path):
    _, config = inputs(tmp_path)
    report = exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/tasks')
    assert report['training']['executed'] is False
    assert report['training']['metrics'] is None
    assert report['housekeeping']['present_in_selected_archives'] is False
    assert report['calibration']['applied'] is False
    for task in report['candidate_tasks']:
        assert task['training_allowed'] is False
        assert task['gate_disposition'] == 'BLOCKED_FOR_PHASE_E'
        assert task['measured_quantity'] and task['target_definition']
        assert task['timing'] and task['quality'] and task['assumptions']
        assert task['evaluation'] and task['required_evidence']
    pi = next(t for t in report['candidate_tasks'] if t['id'] == 'native_pi_forecast')
    assert 'CHANNEL' in pi['measured_quantity']
    assert pi['status'] == 'EXPERIMENTAL_UNCALIBRATED'


def test_plot_selection_is_bounded_and_artifacts_have_portable_verified_identities(tmp_path):
    _, config = inputs(tmp_path)
    report = exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/bounded')
    assert len(report['plots']) == 2
    for plot in report['plots']:
        assert plot['status'] == 'EXPERIMENTAL_UNCALIBRATED'
        assert 'UTC' in plot['axis_semantics']['timing']
        assert plot['displayed_rows'] <= 2
        path = tmp_path / plot['path']
        assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == plot['sha256']
    assert str(tmp_path) not in json.dumps(report)
    saved = json.loads((tmp_path/'results/p2_solexs/bounded/report.json').read_text())
    assert saved == report
    assert report['provenance']['config']['path'] == 'exploration.json'
    runtime = report['provenance']['runtime_sources']['solar_flare_jepa.data.solexs_exploration']
    assert runtime['sha256'] == hashlib.sha256(Path(exploration().__file__).read_bytes()).hexdigest()


def test_existing_output_directory_is_never_overwritten(tmp_path):
    _, config = inputs(tmp_path)
    destination = tmp_path / 'results/p2_solexs/existing'
    destination.mkdir(parents=True)
    sentinel = destination / 'report.json'
    sentinel.write_text('preserve me')
    with pytest.raises(FileExistsError):
        exploration().explore_solexs(config, tmp_path, destination)
    assert sentinel.read_text() == 'preserve me'


@pytest.mark.parametrize('output', ['data/raw/new', 'results/elsewhere/new', '../escape'])
def test_output_is_confined_to_unique_p2_results_directory(tmp_path, output):
    _, config = inputs(tmp_path)
    with pytest.raises(ValueError, match='root|p2_solexs'):
        exploration().explore_solexs(config, tmp_path, output)


def test_output_symlink_cannot_escape_storage_root(tmp_path):
    _, config = inputs(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + '-external')
    outside.mkdir()
    (tmp_path/'results').mkdir()
    (tmp_path/'results/p2_solexs').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='root'):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/escape')
    assert not list(outside.iterdir())


def test_changed_gate_identity_fails_closed_before_output(tmp_path):
    _, config = inputs(tmp_path)
    (tmp_path/'data/manifests/gate.json').write_text(json.dumps(dict(gate='ALLOWED')))
    with pytest.raises(ValueError, match='gate|identity'):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/bad-gate')
    assert not (tmp_path/'results/p2_solexs/bad-gate').exists()


def test_unexpected_gate_state_is_rejected_even_when_new_hash_is_supplied(tmp_path):
    _, config = inputs(tmp_path)
    gate = tmp_path/'data/manifests/gate.json'
    gate.write_text(json.dumps(dict(gate='ALLOWED')))
    values = json.loads(config.read_text())
    values['gate_sha256'] = hashlib.sha256(gate.read_bytes()).hexdigest()
    config.write_text(json.dumps(values))
    with pytest.raises(ValueError, match='Unexpected scientific gate'):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/allowed')
    assert not (tmp_path/'results/p2_solexs/allowed').exists()


def test_failed_bounded_plot_removes_only_new_output_and_keeps_source(tmp_path):
    _, config = inputs(tmp_path, limits=dict(max_plot_channels=2))
    before = (tmp_path/ARCHIVE).read_bytes()
    with pytest.raises(ValueError, match='channel-count limit'):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/channels')
    assert not (tmp_path/'results/p2_solexs/channels').exists()
    assert (tmp_path/ARCHIVE).read_bytes() == before


def test_corrupt_registered_archive_is_rejected_without_publishing_output(tmp_path):
    _, config = inputs(tmp_path)
    archive = tmp_path / ARCHIVE
    archive.write_bytes(archive.read_bytes()[:-10])
    with pytest.raises(ValueError):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/corrupt')
    assert not (tmp_path/'results/p2_solexs/corrupt').exists()


@pytest.mark.parametrize('limits', [dict(max_plot_points=0), dict(max_plot_spectra=True),
                                  dict(chunk_rows=0), dict(max_archives=0)])
def test_invalid_bounds_are_rejected_before_creating_outputs(tmp_path, limits):
    _, config = inputs(tmp_path, limits=limits)
    with pytest.raises(ValueError, match='positive integer'):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/limits')


def test_archive_count_cap_is_enforced_before_native_access(tmp_path):
    _, config = inputs(tmp_path, limits=dict(max_archives=1))
    values = json.loads(config.read_text())
    values['archives'] = [ARCHIVE, 'second.zip']
    config.write_text(json.dumps(values))
    with pytest.raises(ValueError, match='archive.*limit'):
        exploration().explore_solexs(config, tmp_path, 'results/p2_solexs/too-many')


def test_cli_works_from_another_working_directory_and_refuses_second_publication(tmp_path):
    _, config = inputs(tmp_path)
    command = [sys.executable, str(SCRIPT), '--root', str(tmp_path), '--config', config.name,
               '--output', 'results/p2_solexs/cli']
    result = subprocess.run(command, cwd=tmp_path.parent, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary['gate'] == 'BLOCKED_FOR_PHASE_E'
    assert summary['report'] == 'results/p2_solexs/cli/report.json'
    result = subprocess.run(command, cwd=tmp_path.parent, text=True, capture_output=True)
    assert result.returncode != 0
