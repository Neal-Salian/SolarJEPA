"""Artificial native arrays test numerical diagnostics, never mission quality."""
import importlib

import numpy as np
import pytest

from solar_flare_jepa.data.solexs import NativeColumns


def api():
    return importlib.import_module('solar_flare_jepa.data.solexs_quality')


def native(coordinates, counts, *, kind='lc', detector='SDD2', **extra):
    columns = {'TIME' if kind == 'lc' else 'TSTART': np.asarray(coordinates),
               'COUNTS': np.asarray(counts)} | {k: np.asarray(v) for k, v in extra.items()}
    return NativeColumns(columns, {k: None for k in columns}, {},
        dict(kind=kind, archive='source.zip', archive_sha256='a'*64,
             member='source.lc.gz', member_gzip_sha256='b'*64, fits_sha256='c'*64,
             detector=dict(value=detector, evidence='OBSERVED', source='FILTER')),
        ('UTC_CONVERSION_NOT_APPLIED',))


def test_masks_keep_missingness_and_anomalies_distinct_from_scientific_quality():
    q = api().numerical_quality(native([0, 1, 2, 3, 4, 5], [0, -2, .5, np.nan, np.inf, -np.inf]),
                                expected_step=1)
    np.testing.assert_array_equal(q.entry_finite, [1, 1, 1, 0, 0, 0])
    np.testing.assert_array_equal(q.entry_nan, [0, 0, 0, 1, 0, 0])
    np.testing.assert_array_equal(q.entry_positive_infinity, [0, 0, 0, 0, 1, 0])
    np.testing.assert_array_equal(q.entry_negative_infinity, [0, 0, 0, 0, 0, 1])
    np.testing.assert_array_equal(q.rows['any_negative'], [0, 1, 0, 0, 0, 0])
    np.testing.assert_array_equal(q.rows['any_noninteger'], [0, 0, 1, 0, 0, 0])
    assert q.summary()['scientific_quality'] == 'UNKNOWN_NOT_APPLIED'
    assert q.summary()['filter_applied'] is False
    with pytest.raises(ValueError):
        q.entry_finite.setflags(write=True)


def test_continuity_is_exact_and_includes_chunk_boundary():
    q = api().numerical_quality(native(np.array([2**63-3, 2**63-2, 2**63-1], dtype=np.int64),
                                      np.array([2**53+1, 0, -2], dtype=np.int64)),
                                expected_step=1, previous_coordinate=2**63-4)
    np.testing.assert_array_equal(q.rows['break_before'], [0, 0, 0])
    q = api().numerical_quality(native([4., 5., 5., 4., np.nan, 7., 9.], np.ones(7)), expected_step=1)
    np.testing.assert_array_equal(q.rows['break_before'], [1, 0, 1, 1, 1, 1, 1])


def test_partial_spectrum_and_exposure_diagnostics_preserve_row_support():
    q = api().numerical_quality(native([0, 1, 2], [[1., np.nan], [np.nan, np.nan], [0., -1.]],
        kind='pi', CHANNEL=[[0, 1]]*3, EXPOSURE=[1., 1., 0.], TELAPSE=[1., np.inf, -1.]), expected_step=1)
    np.testing.assert_array_equal(q.rows['all_counts_finite'], [0, 0, 1])
    np.testing.assert_array_equal(q.rows['any_count_finite'], [1, 0, 1])
    np.testing.assert_array_equal(q.rows['positive_finite_exposure'], [1, 1, 0])
    np.testing.assert_array_equal(q.rows['positive_finite_telapse'], [1, 0, 0])
    assert q.summary()['rows'] == 3
    assert q.summary()['counts']['nan'] == 3


@pytest.mark.parametrize('step', [0, -1, True, np.nan, np.inf, '1'])
def test_invalid_coordinate_step_is_rejected(step):
    with pytest.raises(ValueError):
        api().numerical_quality(native([0, 1], [1, 2]), expected_step=step)


@pytest.mark.parametrize('coordinates,counts', [([[0, 1]], [1, 2]), ([0, 1], [1]),
                                                ([0, 1], [[1], [2]])])
def test_ambiguous_shapes_are_rejected(coordinates, counts):
    with pytest.raises(ValueError):
        api().numerical_quality(native(coordinates, counts), expected_step=1)


def gti(starts, stops, detector='SDD2'):
    n = native([], [], detector=detector)
    return NativeColumns(dict(START=np.asarray(starts), STOP=np.asarray(stops)),
                         dict(START=None, STOP=None), {}, dict(n.provenance, kind='gti', member='gti.gz'), ())


def test_gti_endpoints_are_two_hypotheses_without_filter_or_exposure():
    n = native([0, 1, 2, 3], [7., np.nan, 9., 10.])
    d = api().gti_diagnostics(n, gti([0, 3], [1, 3]))
    np.testing.assert_array_equal(d.closed, [1, 1, 0, 1])
    np.testing.assert_array_equal(d.half_open, [1, 0, 0, 0])
    assert d.summary()['continuous_exposure'] is None
    assert d.summary()['filter_applied'] is False
    assert d.summary()['clock_compatibility'] == 'UNKNOWN'
    assert api().gti_diagnostics(n, gti([], [])).summary()['closed_points'] == 0


@pytest.mark.parametrize('starts,stops', [([2], [1]), ([0, 1], [2, 3]), ([2, 0], [3, 1]),
                                        ([np.nan], [1]), ([0], [])])
def test_invalid_gti_is_not_repaired(starts, stops):
    with pytest.raises(ValueError):
        api().gti_diagnostics(native([0, 1], [2, 3]), gti(starts, stops))


def test_gti_source_and_detector_must_match_even_for_numerical_comparison():
    n = native([0], [1])
    with pytest.raises(ValueError):
        api().gti_diagnostics(n, gti([0], [1], 'SDD1'))
    other = gti([0], [1])
    other.provenance['archive_sha256'] = 'd'*64
    with pytest.raises(ValueError):
        api().gti_diagnostics(n, other)


def test_gti_detector_evidence_can_differ_without_changing_the_detector_label():
    n, intervals = native([0, 1], [2, 3]), gti([0], [1])
    intervals.provenance['detector'] = dict(value='SDD2', evidence='INFERRED', source='member_name')
    assert api().gti_diagnostics(n, intervals).summary()['closed_points'] == 2
