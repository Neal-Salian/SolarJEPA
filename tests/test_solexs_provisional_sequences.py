"""Artificial native samples test numerical policies, never physical calibration."""
import importlib
import importlib.util

import numpy as np
import pytest

from solar_flare_jepa.data.solexs import NativeColumns


def api():
    name = 'solar_flare_jepa.provisional.sequences'
    assert importlib.util.find_spec(name), 'sample-index adapter is missing'
    return importlib.import_module(name)


def native(values, coordinates=None, **changes):
    values = np.asarray(values, float)
    args = dict(columns={'TIME': np.arange(len(values), dtype=float) if coordinates is None
                         else np.asarray(coordinates, float), 'COUNTS': values},
                units={'TIME': None, 'COUNTS': None}, time_metadata={'TIMEUNIT': 's'},
                provenance={'archive': 'data/raw/pilot.zip', 'archive_sha256': 'a'*64,
                            'member': 'SDD2/sample.lc.gz', 'member_gzip_sha256': 'b'*64,
                            'fits_sha256': 'c'*64, 'kind': 'lc',
                            'detector': {'value': 'SDD2', 'evidence': 'OBSERVED', 'source': 'FILTER'}},
                warnings=('TIME_REFERENCE_CONFLICT',))
    args.update(changes)
    return NativeColumns(**args)


def test_source_preserves_missing_values_provenance_and_unknown_units():
    s = api().sequence_from_native(native([1, np.nan, 3]))
    np.testing.assert_array_equal(s.values, [1, np.nan, 3])
    np.testing.assert_array_equal(s.observed, [True, False, True])
    assert s.source['provenance']['fits_sha256'] == 'c'*64
    assert s.source['native_unit'] == 'UNKNOWN_UNENCODED_NATIVE_VALUE'
    assert s.source['calibration_applied'] is False
    assert s.source['scientific_label'] == 'EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED'
    with pytest.raises(ValueError):
        s.values.setflags(write=True)


@pytest.mark.parametrize('coordinates', [[0,1,1,3], [0,2,1,3], [0,1,np.nan,3]])
def test_ambiguous_order_aborts_without_sorting(coordinates):
    with pytest.raises(ValueError):
        api().sequence_from_native(native([1,2,3,4], coordinates))


@pytest.mark.parametrize('values', [[np.nan]*4, [1,np.inf,2], [1,-np.inf,2]])
def test_no_finite_support_or_infinite_observation_aborts(values):
    with pytest.raises(ValueError):
        api().sequence_from_native(native(values))


def test_missing_and_coordinate_gap_windows_are_excluded_without_filling():
    s = api().sequence_from_native(native([1,2,3,np.nan,5,6,7,8,9,10]))
    w = api().make_windows(s, 0,10,context=2,horizon=2,stride=2)
    np.testing.assert_array_equal(w.origins, [6,8])
    np.testing.assert_array_equal(w.x[:,:,0], [[5,6],[7,8]])
    np.testing.assert_array_equal(w.y[:,:,0], [[7,8],[9,10]])
    assert w.summary['missing_rows'] == 1
    assert w.summary['excluded_origins'] == 2
    g = api().sequence_from_native(native(np.arange(8),[0,1,2,3,10,11,12,13]))
    gw = api().make_windows(g,0,8,context=2,horizon=2,stride=2)
    np.testing.assert_array_equal(gw.origins,[2,6])
    assert gw.summary['excluded_discontinuity'] == 1


def test_windows_do_not_cross_split_or_future_target_boundary():
    s = api().sequence_from_native(native(np.arange(16)))
    train = api().make_windows(s,0,8,context=2,horizon=2,stride=2)
    val = api().make_windows(s,8,16,context=2,horizon=2,stride=2)
    np.testing.assert_array_equal(train.origins,[2,4,6])
    np.testing.assert_array_equal(val.origins,[10,12,14])
    assert train.y.max() == 7 and val.x.min() == 8
    repeat = api().make_windows(s,0,8,context=2,horizon=2,stride=2)
    assert repeat.fingerprint == train.fingerprint
    changed = api().sequence_from_native(native(np.r_[np.arange(8),np.arange(8)+1000]))
    other = api().make_windows(changed,0,8,context=2,horizon=2,stride=2)
    np.testing.assert_array_equal(train.x,other.x)
    np.testing.assert_array_equal(train.y,other.y)


def test_normalization_unique_raw_train_only_and_constant_scale():
    s = api().sequence_from_native(native([1,2,3,np.nan,10000,20000]))
    n = api().fit_normalization(s,0,4)
    assert n['mean'] == 2 and n['count'] == 3
    assert n['scale'] == pytest.approx(np.sqrt(2/3))
    assert api().fit_normalization(api().sequence_from_native(native([7,7,9])),0,2)['scale'] == 1


@pytest.mark.parametrize('boundaries', [(-1,8),(0,9),(4,4),(5,3)])
def test_invalid_partition_boundaries_fail(boundaries):
    s=api().sequence_from_native(native(range(8)))
    with pytest.raises(ValueError):
        api().make_windows(s,*boundaries,context=2,horizon=2,stride=1)


def test_wrong_detector_or_physical_relabeling_fails():
    n=native([1,2,3,4])
    n.provenance['detector']['value']='SDD1'
    with pytest.raises(ValueError): api().sequence_from_native(n)
    with pytest.raises(ValueError):
        api().sequence_from_native(native([1,2],units={'TIME':None,'COUNTS':'W/m2'}))
    with pytest.raises(ValueError):
        api().sequence_from_native(native([1,2],columns={'TIME':np.arange(2),'COUNTS':np.ones(2),'QUALITY':np.ones(2)}))


def test_valid_finite_zero_and_negative_are_numerical_values():
    s=api().sequence_from_native(native([-1,0,2,3]))
    w=api().make_windows(s,0,4,context=2,horizon=2,stride=1)
    np.testing.assert_array_equal(w.x[:,:,0],[[-1,0]])
