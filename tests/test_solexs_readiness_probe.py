"""Artificial arrays/responses test diagnostic boundaries, not mission policy."""
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from astropy.io import fits

from solar_flare_jepa.data.storage import ROLE
from test_solexs import archive_fixture, product_bytes


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/probe_solexs_readiness.py'


def probe():
    assert SCRIPT.is_file(), 'The reproducible native readiness probe is missing'
    spec = importlib.util.spec_from_file_location('readiness_probe', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_rows(times=(100., 101., 102.)):
    return {
        'TSTART': np.array(times),
        'CHANNEL': np.tile([0, 1, 2, 3, 4], (3, 1)),
        'COUNTS': np.array([[9., 2., 3., 1., 8.], [np.nan]*5,
                            [8., 4., 5., 0., 7.]]),
        'TELAPSE': np.ones(3), 'EXPOSURE': np.ones(3),
    }


def test_slice_diagnostic_keeps_the_tools_exclusive_upper_endpoint():
    # An off-by-one change must distinguish tools' [1:3] from control [1:4].
    bounds = np.array([[1., 1.5], [2.1, 2.5], [3., 21.],
                       [21., 21.9], [22., 22.1]])
    assert probe().candidate_slice(bounds) == (1, 3)


@pytest.mark.parametrize('bounds', [
    np.array([[3., 2.]]), np.array([[np.nan, 3.]]),
    np.array([1., 2.]), np.array([[23., 24.]]),
])
def test_invalid_or_empty_candidate_band_is_refused(bounds):
    with pytest.raises(ValueError):
        probe().candidate_slice(bounds)


def test_native_comparison_preserves_missingness_and_distinguishes_upper_control():
    rows = native_rows()
    lc = {'TIME': np.array([100., 101., 102.]), 'COUNTS': np.array([6., np.nan, 9.])}
    before = rows['COUNTS'].copy()
    result = probe().compare_native_rows(lc, iter([rows]), (1, 3), np.arange(1, 6))
    assert result['finite_compared_rows'] == 2
    assert result['tool_slice'] == {'equal_rows': 1, 'maximum_absolute_difference': 1.0}
    assert result['inclusive_upper_control'] == {'equal_rows': 2, 'maximum_absolute_difference': 0.0}
    assert result['pi_nan_rows'] == 1
    assert result['pi_nan_mask_equals_lc'] is True
    assert result['pi_channel_labels_equal_rmf'] is False
    assert result['pi_channel_first_last'] == [0, 4]
    assert result['mapping_validated'] is False
    np.testing.assert_array_equal(rows['COUNTS'], before)


def test_response_label_match_does_not_approve_calibration():
    lc = {'TIME': np.array([100., 101., 102.]), 'COUNTS': np.array([6., np.nan, 9.])}
    result = probe().compare_native_rows(lc, iter([native_rows()]), (1, 3), np.arange(5))
    assert result['pi_channel_labels_equal_rmf'] is True
    assert result['mapping_validated'] is False


@pytest.mark.parametrize('rows', [native_rows((100., 102., 103.)),
                                 {k:v[:2] for k,v in native_rows().items()}])
def test_positional_comparison_refuses_different_native_coordinates_or_lengths(rows):
    lc = {'TIME': np.array([100., 101., 102.]), 'COUNTS': np.array([6., np.nan, 9.])}
    with pytest.raises(ValueError, match='coordinates|length'):
        probe().compare_native_rows(lc, iter([rows]), (1, 3), np.arange(5))


def test_chunk_boundary_does_not_change_comparison():
    rows = native_rows()
    chunks = [{k:v[:1] for k,v in rows.items()}, {k:v[1:] for k,v in rows.items()}]
    lc = {'TIME': np.array([100., 101., 102.]), 'COUNTS': np.array([6., np.nan, 9.])}
    result = probe().compare_native_rows(lc, iter(chunks), (1, 3), np.arange(5))
    assert result['rows'] == 3
    assert result['inclusive_upper_control']['equal_rows'] == 2
    assert result['all_channel_sum']['maximum_absolute_difference'] == 17.0


def test_integer_native_coordinate_is_not_rounded_to_match_a_float_coordinate():
    rows = {k:v[:1] for k,v in native_rows().items()}
    rows['TSTART'] = np.array([2**53 + 1], dtype=np.int64)
    lc = {'TIME': np.array([float(2**53)]), 'COUNTS': np.array([6.])}
    with pytest.raises(ValueError, match='coordinates'):
        probe().compare_native_rows(lc, iter([rows]), (1, 3), np.arange(5))


def test_integer_counts_are_refused_before_an_overflowing_sum():
    rows = {k:v[:1] for k,v in native_rows().items()}
    rows['COUNTS'] = np.array([[2**62]*5], dtype=np.int64)
    lc = {'TIME': np.array([100.]), 'COUNTS': np.array([1.])}
    with pytest.raises(ValueError, match='floating COUNTS'):
        probe().compare_native_rows(lc, iter([rows]), (1, 3), np.arange(5))


def response_fixture(root, area_unit='keV'):
    low, high = [1., 2.], [2., 3.]
    ebounds = fits.BinTableHDU.from_columns([
        fits.Column(name='CHANNEL', format='K', array=[1, 2]),
        fits.Column(name='E_MIN', format='E', unit='keV', array=low),
        fits.Column(name='E_MAX', format='E', unit='keV', array=high)], name='EBOUNDS')
    matrix = fits.BinTableHDU.from_columns([
        fits.Column(name='ENERG_LO', format='E', unit='keV', array=low),
        fits.Column(name='ENERG_HI', format='E', unit='keV', array=high),
        fits.Column(name='F_CHAN', format='I', array=[1, 1]),
        fits.Column(name='N_CHAN', format='I', array=[2, 2]),
        fits.Column(name='MATRIX', format='2D', array=[[.8, .2], [.1, .9]])], name='MATRIX')
    area = fits.BinTableHDU.from_columns([
        fits.Column(name='ENERG_LO', format='E', unit=area_unit, array=low),
        fits.Column(name='ENERG_HI', format='E', unit=area_unit, array=high),
        fits.Column(name='SPECRESP', format='E', unit='cm2', array=[1., 2.])], name='SPECRESP')
    paths = {'rmf':root/'candidate.rmf', 'arf':root/'candidate.arf', 'arf_pi':root/'pi.arf'}
    fits.HDUList([fits.PrimaryHDU(), ebounds, matrix]).writeto(paths['rmf'])
    fits.HDUList([fits.PrimaryHDU(), area]).writeto(paths['arf'])
    fits.HDUList([fits.PrimaryHDU(), area.copy()]).writeto(paths['arf_pi'])
    return paths


def test_response_probe_reports_units_grids_and_channel_labels_without_approval(tmp_path):
    summary, channels = probe().inspect_candidate_response(response_fixture(tmp_path))
    assert summary['response_channel_first_last'] == [1, 2]
    assert summary['matrix_shape'] == [2, 2]
    assert summary['arf_incident_grid_comparison'] == 'EXACT_VALUES_AND_ENCODED_UNITS'
    assert summary['arf_pi_channel_grid_comparison'] == 'EXACT_VALUES_AND_ENCODED_UNITS'
    assert summary['accepted_for_application'] is False
    assert summary['hdus']['arf']['SPECRESP']['units']['SPECRESP'] == 'cm2'
    np.testing.assert_array_equal(channels, [1, 2])


def test_response_probe_refuses_to_call_equal_numbers_equal_energies_with_different_units(tmp_path):
    summary, _ = probe().inspect_candidate_response(response_fixture(tmp_path, area_unit='MeV'))
    assert summary['arf_incident_grid_comparison'] == 'NOT_COMPARABLE_ENCODED_UNITS'
    assert summary['arf_pi_channel_grid_comparison'] == 'NOT_COMPARABLE_ENCODED_UNITS'


def test_response_input_size_is_bounded_before_fits_access(tmp_path):
    paths = response_fixture(tmp_path)
    with pytest.raises(ValueError, match='byte limit'):
        probe().inspect_candidate_response(paths, max_bytes=1024)


def probe_fixture(root):
    record, _ = archive_fixture(root, [(k, 'SDD2', product_bytes(k)) for k in ('gti', 'lc', 'pi')])
    paths = response_fixture(root)
    bounds = root/'bounds.dat'
    bounds.write_text('2.1 2.5\n3 4\n5 6\n')
    paths['bounds'] = bounds
    manifest_dir = root/'data/manifests'
    manifest_dir.mkdir(parents=True, exist_ok=True)
    previous = manifest_dir/'prior.json'
    previous.write_text(json.dumps({'sources':[]}))
    sources = dict(previous_manifest='data/manifests/prior.json',
                   inputs={k:str(p.relative_to(root)) for k,p in paths.items()},
                   sources=[dict(path=str(p.relative_to(root)), bytes=p.stat().st_size,
                                 sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                            for p in paths.values()])
    (manifest_dir/'sources.json').write_text(json.dumps(sources))
    inventory = dict(schema_version=1, dataset_role=ROLE, files=[record], missing_coverage=[])
    (manifest_dir/'inventory.json').write_text(json.dumps(inventory))
    (root/'config.json').write_text(json.dumps(dict(
        inventory_path='data/manifests/inventory.json', archives=[record['path']])))
    return record, sources


def test_verified_inputs_refuses_changed_source_identity(tmp_path):
    _, sources = probe_fixture(tmp_path)
    (tmp_path/'bounds.dat').write_text('2.2 2.5\n3 4\n5 6\n')
    with pytest.raises(ValueError, match='identity'):
        probe().verified_inputs(tmp_path, sources)


def test_verified_inputs_rejects_oversized_file_before_hashing_or_loading(tmp_path):
    _, sources = probe_fixture(tmp_path)
    with (tmp_path/'bounds.dat').open('wb') as stream:
        stream.truncate(17 * 1024**2)
    record = next(s for s in sources['sources'] if s['path'] == 'bounds.dat')
    record.update(bytes=17 * 1024**2,
                  sha256=hashlib.sha256((tmp_path/'bounds.dat').read_bytes()).hexdigest())
    with pytest.raises(ValueError, match='byte limit'):
        probe().verified_inputs(tmp_path, sources)


def test_native_archive_probe_is_portable_and_preserves_clock_conflict_and_raw_bytes(tmp_path):
    record, sources = probe_fixture(tmp_path)
    before = (tmp_path/record['path']).read_bytes()
    inputs = probe().verified_inputs(tmp_path, sources)
    report = probe().build_probe(tmp_path, [record], inputs)
    archive = report['archives'][0]
    assert archive['comparison']['pi_channel_labels_equal_rmf'] is False
    assert archive['comparison']['pi_nan_rows'] == 1
    assert archive['clocks']['lc']['RATE']['MJDREFF'] == 0.22916666651
    assert archive['clocks']['lc']['RATE']['TIMEPIXR'] is None
    assert archive['clocks']['gti']['GTI']['EXPOSURE'] is None
    assert archive['clocks']['pi']['SPECTRUM']['DTCORR'] is None
    assert report['policies']['absolute_utc_conversion'] == 'UNKNOWN_NOT_APPLIED'
    assert str(tmp_path) not in json.dumps(report)
    assert (tmp_path/record['path']).read_bytes() == before
    assert not list((tmp_path/'.cache').rglob('*.fits'))


def test_probe_cli_emits_deterministic_metadata_from_a_relocated_root(tmp_path):
    probe_fixture(tmp_path)
    command = [sys.executable, str(SCRIPT), '--root', str(tmp_path),
               '--config', 'config.json', '--sources', 'data/manifests/sources.json']
    first = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    assert first.stdout.strip(), 'The CLI did not emit a diagnostic report'
    second = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True)
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout
    assert json.loads(first.stdout)['candidate_calibration']['accepted_for_application'] is False
    assert str(tmp_path) not in first.stdout
