"""Synthetic binary decisions test arithmetic, not forecast performance."""
import json

import numpy as np
import pytest


SECOND = 1_000_000_000
DAY = 86400 * SECOND


def scores(*args, **kwargs):
    from solar_flare_jepa.events.scoring import binary_scores
    return binary_scores(*args, **kwargs)


def intervals(*args, **kwargs):
    from solar_flare_jepa.events.scoring import block_intervals
    return block_intervals(*args, **kwargs)


def test_contingency_metrics_use_only_valid_decisions_and_distinguish_far_from_fpr():
    truth = np.array([True] * 5 + [False] * 5 + [True])
    prediction = np.array([True, True, False, False, False, True,
                           False, False, False, False, False])
    valid = np.array([True] * 10 + [False])
    result = scores(truth, prediction, valid)
    assert result['counts'] == dict(total=11, valid=10, excluded=1, tp=2, fp=1, fn=3, tn=4)
    assert result['metrics'] == pytest.approx(dict(
        prevalence=.5, precision=2/3, recall=.4, far=1/3, fpr=.2,
        csi=1/3, tss=.2, hss=.2, balanced_accuracy=.6))
    assert result['undefined_reasons'] == {}
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('truth,prediction,expected', [
    ([], [], dict(prevalence=None, precision=None, recall=None, far=None,
                 fpr=None, csi=None, tss=None, hss=None, balanced_accuracy=None)),
    ([False, False], [False, False], dict(prevalence=0., precision=None, recall=None,
        far=None, fpr=0., csi=None, tss=None, hss=None, balanced_accuracy=None)),
    ([True, True], [True, True], dict(prevalence=1., precision=1., recall=1.,
        far=0., fpr=None, csi=1., tss=None, hss=None, balanced_accuracy=None)),
])
def test_zero_denominators_are_explicit_without_nan(truth, prediction, expected):
    result = scores(np.array(truth, dtype=bool), np.array(prediction, dtype=bool))
    assert result['metrics'] == expected
    assert set(result['undefined_reasons']) == {k for k, v in expected.items() if v is None}
    assert set(result['undefined_reasons'].values()) <= {'zero_denominator'}
    json.dumps(result, allow_nan=False)


def test_all_excluded_decisions_leave_counts_but_no_defined_metrics():
    result = scores([True, False], [True, True], [False, False])
    assert result['counts'] == dict(total=2, valid=0, excluded=2, tp=0, fp=0, fn=0, tn=0)
    assert all(value is None for value in result['metrics'].values())


@pytest.mark.parametrize('truth,prediction,valid', [
    ([1, 0], [True, False], None),
    ([True, False], [1., 0.], None),
    ([True], [True], [1]),
    ([[True]], [[False]], None),
    ([True], [True, False], None),
    ([True], [False], [True, False]),
    (np.array([True], dtype=object), [True], None),
    ([], [], None),
])
def test_binary_inputs_reject_coercion_dimensions_and_unequal_lengths(truth, prediction, valid):
    with pytest.raises(ValueError):
        scores(truth, prediction, valid)


def test_block_intervals_are_descriptive_deterministic_and_retain_excluded_blocks():
    # Day 0 has one TP, day 1 one TN, day 2 one excluded position. The
    # seed-17 draw of 12 three-block replicates includes two positive-only,
    # two negative-only and one entirely excluded replicate.
    args = (np.array([0, DAY, 2 * DAY], dtype=np.int64),
            [True, False, True], [True, False, False], [True, True, False])
    result = intervals(*args, replicates=12, seed=17)
    assert result == intervals(*args, replicates=12, seed=17)
    assert result['status'] == 'defined'
    assert result['blocks'] == dict(total=3, informative=2)
    assert result['executed_replicates'] == 12
    assert result['observed']['counts']['excluded'] == 1
    undefined = dict(prevalence=1, precision=3, recall=3, far=3, fpr=3,
                     csi=3, tss=5, hss=5, balanced_accuracy=5)
    assert {name: item['undefined_replicates'] for name, item in result['metrics'].items()} == undefined
    for name in ('precision', 'recall', 'csi', 'tss', 'hss', 'balanced_accuracy'):
        assert result['metrics'][name]['lower'] == 1.
        assert result['metrics'][name]['upper'] == 1.
    assert result['metrics']['far']['lower'] == 0.
    assert result['metrics']['fpr']['upper'] == 0.
    assert result['interval_kind'] == 'descriptive_utc_block_percentile'
    assert result['percentiles'] == [2.5, 97.5]
    assert result['block_seconds'] == 86400
    assert result['minimum_block_seconds'] == 9000
    json.dumps(result, allow_nan=False)


def test_blocks_are_utc_epoch_aligned_and_half_open_at_midnight():
    result = intervals(np.array([DAY - 1, DAY], dtype=np.int64),
                       [True, False], [True, False], replicates=8)
    assert result['blocks'] == dict(total=2, informative=2)
    assert result['status'] == 'defined'


def test_two_records_in_one_informative_block_do_not_establish_intervals():
    result = intervals(np.array([0, 60 * SECOND, DAY], dtype=np.int64),
                       [True, False, False], [True, True, False], [True, True, False],
                       replicates=12)
    assert result['status'] == 'undefined'
    assert result['reason'] == 'fewer_than_two_informative_blocks'
    assert result['blocks'] == dict(total=2, informative=1)
    assert result['executed_replicates'] == 0
    assert result['requested_replicates'] == 12
    assert all(item['lower'] is None and item['upper'] is None
               for item in result['metrics'].values())


def test_empty_time_series_returns_explicit_undefined_intervals():
    result = intervals(np.array([], dtype=np.int64), np.array([], dtype=bool),
                       np.array([], dtype=bool), replicates=4)
    assert result['reason'] == 'fewer_than_two_informative_blocks'
    assert result['blocks'] == dict(total=0, informative=0)


def test_metric_undefined_in_every_replicate_has_no_interval():
    result = intervals(np.array([0, DAY], dtype=np.int64), [True, True],
                       [True, True], replicates=12)
    assert result['metrics']['fpr'] == dict(lower=None, upper=None,
        defined_replicates=0, undefined_replicates=12, reason='no_defined_replicates')


@pytest.mark.parametrize('times', [
    [0., float(DAY)], [False, True], [[0, DAY]], [0, 0], [DAY, 0],
    np.array([0, 2**63], dtype=np.uint64),
])
def test_intervals_require_unique_chronological_int64_nanosecond_coordinates(times):
    with pytest.raises(ValueError):
        intervals(times, [True, False], [True, False])


@pytest.mark.parametrize('kwargs', [
    dict(block_seconds=8999), dict(block_seconds=True), dict(block_seconds=86400.),
    dict(minimum_block_seconds=0), dict(minimum_block_seconds=False),
    dict(block_seconds=9000, minimum_block_seconds=9001),
    dict(replicates=0), dict(replicates=True), dict(seed=True), dict(seed=-1),
])
def test_intervals_validate_declared_dependence_bound_and_reproducible_sampling(kwargs):
    with pytest.raises(ValueError):
        intervals(np.array([0, DAY], dtype=np.int64), [True, False], [True, False], **kwargs)


def test_intervals_validate_coordinates_and_masks_before_exclusion():
    with pytest.raises(ValueError):
        intervals(np.array([0, DAY], dtype=np.int64), [True, False], [True, False], [0, 0])
    with pytest.raises(ValueError):
        intervals(np.array([0, DAY], dtype=np.int64), [True], [True])
