"""The future integration boundary preserves data and refuses scientific promotion."""
import importlib
import io
import json

import numpy as np
import pytest
from astropy.io import fits

from test_solexs import archive_fixture, product_bytes
from test_solexs_quality import native


def api():
    return importlib.import_module('solar_flare_jepa.data.solexs_interface')


def test_snapshot_preserves_large_integer_values_dtype_and_detaches_all_metadata():
    n = native(np.array([2**63-2, 2**63-1], dtype=np.int64),
               np.array([2**53+1, 2**53+3], dtype='>i8'))
    n.time_metadata['MJDREFI'] = 40587
    b = api().prepare_native_batch(n, expected_step=1)
    assert b.columns['COUNTS'].dtype == np.dtype('>i8')
    assert b.columns['COUNTS'].tolist() == [9007199254740993, 9007199254740995]
    before = b.fingerprint
    n.columns['COUNTS'][0] = 0
    n.units['COUNTS'] = 'invented'
    n.provenance['detector']['value'] = 'SDD1'
    n.time_metadata['MJDREFI'] = 0
    assert b.units['COUNTS'] is None
    assert b.provenance['detector']['value'] == 'SDD2'
    assert b.time_metadata['MJDREFI'] == 40587
    b.provenance['detector']['value'] = 'SDD1'
    assert b.fingerprint == before
    with pytest.raises(ValueError):
        b.columns['COUNTS'].setflags(write=True)
    with pytest.raises(TypeError):
        b.columns['COUNTS'] = np.zeros(2)


@pytest.mark.parametrize('representation', ['utc', 'count_rate', 'calibrated_flux', 'goes_aligned', 'jepa'])
def test_unsupported_interpretations_never_return_a_batch(representation):
    with pytest.raises(ValueError):
        api().prepare_native_batch(native([0, 1], [2, 3]), expected_step=1,
                                   representation=representation)


def test_finite_data_never_clear_scientific_or_jepa_training_gates():
    b = api().prepare_native_batch(native([0, 1], [2, 3]), expected_step=1)
    assert b.quality.entry_finite.all()
    with pytest.raises(ValueError, match='BLOCKED'):
        b.require_jepa_ready()
    m = b.summary()['semantics']
    assert m['upstream_correction_state'] == 'UNKNOWN'
    assert m['local_transformations']['calibration'] is False
    assert m['local_transformations']['unit_conversion'] is False
    assert m['validated_utc'] is None
    assert m['scientific_quality'] == 'UNKNOWN_NOT_APPLIED'


@pytest.mark.parametrize('chunk_rows', [1, 2, 3])
def test_verified_stream_preserves_rows_masks_and_continuity_at_chunk_boundaries(tmp_path, chunk_rows):
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', product_bytes('pi'))])
    batches = list(api().iter_native_batches(tmp_path, record, members[0], chunk_rows=chunk_rows))
    assert [b.row_start for b in batches] == list(range(0, 3, chunk_rows))
    counts = np.concatenate([b.columns['COUNTS'] for b in batches])
    np.testing.assert_equal(counts, [[1, 2, 3], [np.nan]*3, [2.5, 0, -1]])
    np.testing.assert_array_equal(np.concatenate([b.quality.rows['break_before'] for b in batches]), [1, 0, 0])
    assert all(b.provenance['archive_sha256'] == record['sha256'] for b in batches)
    assert all(b.provenance['zip_member_crc_verified'] for b in batches)
    assert all(b.units['COUNTS'] is None for b in batches)
    assert not list((tmp_path/'.cache').rglob('*.fits'))


def test_explicit_gti_diagnostics_preserve_separate_detector_evidence(tmp_path):
    # Match the real GTI's absent FILTER, unlike the general fixture default.
    stream = io.BytesIO()
    with fits.open(io.BytesIO(product_bytes('gti'))) as hdus:
        del hdus['GTI'].header['FILTER']
        hdus.writeto(stream, checksum=True)
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes()),
                                               ('gti', 'SDD2', stream.getvalue())])
    b = next(api().iter_native_batches(tmp_path, record, members[0], gti_member=members[1]))
    assert b.gti.summary()['closed_points'] == 3
    assert b.gti.summary()['half_open_points'] == 2
    assert b.gti_provenance['detector']['evidence'] == 'INFERRED'
    assert b.provenance['detector']['evidence'] == 'OBSERVED'
    assert b.quality.entry_nan.tolist() == [False, True, False]
    assert b.summary()['gti']['filter_applied'] is False


def test_gti_of_another_detector_is_not_selected_automatically(tmp_path):
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes()),
                                               ('gti', 'SDD1', product_bytes('gti', 'SDD1'))])
    with pytest.raises(ValueError, match='detector'):
        list(api().iter_native_batches(tmp_path, record, members[0], gti_member=members[1]))


def test_metadata_summary_is_portable_and_original_warnings_survive(tmp_path):
    record, members = archive_fixture(tmp_path)
    b = next(api().iter_native_batches(tmp_path, record, members[0]))
    summary = b.summary()
    assert str(tmp_path) not in json.dumps(summary)
    assert 'TIME_REFERENCE_CONFLICT' in summary['warnings']
    assert summary['columns']['COUNTS']['unit'] is None
    assert summary['provenance']['member'] == members[0]
    assert summary['row_start'] == 0


@pytest.mark.parametrize('chunk_rows', [0, True, 8193])
def test_stream_limits_are_enforced_before_access(tmp_path, chunk_rows):
    with pytest.raises(ValueError):
        list(api().iter_native_batches(tmp_path, {}, 'absent', chunk_rows=chunk_rows))


def test_fingerprint_binds_derived_continuity_and_gti_diagnostics():
    from test_solexs_quality import gti
    n = native([4, 5], [2, 3])
    first = api().prepare_native_batch(n, expected_step=1, previous_coordinate=3)
    broken = api().prepare_native_batch(n, expected_step=1, previous_coordinate=0)
    assert first.fingerprint != broken.fingerprint
    closed = api().prepare_native_batch(n, expected_step=1, gti=gti([4], [5]))
    empty = api().prepare_native_batch(n, expected_step=1, gti=gti([0], [1]))
    assert closed.fingerprint != empty.fingerprint


@pytest.mark.parametrize('change', ['missing_channel', 'missing_spec_num', 'channel_shape',
                                   'fractional_channel', 'fractional_spec_num', 'vector_spec_num'])
def test_direct_pi_snapshot_enforces_loader_equivalent_identifier_structure(change):
    n = native([0, 1], [[1, 2], [3, 4]], kind='pi', EXPOSURE=[1, 1], TELAPSE=[1, 1],
               CHANNEL=[[0, 1], [0, 1]], SPEC_NUM=[1, 2])
    if change == 'missing_channel': del n.columns['CHANNEL']; del n.units['CHANNEL']
    if change == 'missing_spec_num': del n.columns['SPEC_NUM']; del n.units['SPEC_NUM']
    if change == 'channel_shape': n.columns['CHANNEL'] = np.array([[0, 1, 2]]*2)
    if change == 'fractional_channel': n.columns['CHANNEL'] = np.array([[.5, 1.5]]*2)
    if change == 'fractional_spec_num': n.columns['SPEC_NUM'] = np.array([.5, 1.5])
    if change == 'vector_spec_num': n.columns['SPEC_NUM'] = np.array([[1], [2]])
    with pytest.raises(ValueError):
        api().prepare_native_batch(n, expected_step=1)


@pytest.mark.parametrize('kind', ['lc', 'pi'])
def test_empty_science_still_validates_requested_step_and_detector(tmp_path, kind):
    stream = io.BytesIO()
    with fits.open(io.BytesIO(product_bytes(kind))) as hdus:
        hdus[1].data = hdus[1].data[:0]
        hdus.writeto(stream, checksum=True)
    record, members = archive_fixture(tmp_path, [(kind, 'SDD2', stream.getvalue()),
                                               ('gti', 'SDD1', product_bytes('gti', 'SDD1'))])
    assert list(api().iter_native_batches(tmp_path, record, members[0])) == []
    with pytest.raises(ValueError, match='step'):
        list(api().iter_native_batches(tmp_path, record, members[0], expected_step=-1))
    with pytest.raises(ValueError, match='detector'):
        list(api().iter_native_batches(tmp_path, record, members[0], gti_member=members[1]))
