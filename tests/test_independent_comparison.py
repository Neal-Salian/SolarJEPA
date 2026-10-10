"""Synthetic effects and shared crossed draws, never scientific outcomes."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.evaluation.comparison import LossPanel, paired_comparison

DAY = 86_400_000_000_000
HOUR = DAY // 24


def panel(losses=((2., 2., 2., 2.), (4., 4., 4., 4.)), **changes):
    args = dict(seed_ids=(11, 22), origin_ids=('a', 'b', 'c', 'd'),
                issue_times_ns=np.arange(4, dtype=np.int64) * DAY + HOUR,
                losses=np.asarray(losses), support_fingerprint='support',
                metric='mean_pinball/v1', unit='dex',
                calendar_start_ns=0, calendar_end_ns=4 * DAY)
    args.update(changes)
    return LossPanel(**args)


def compare(a, b, **changes):
    args = dict(block_days=2, replicates=101, rng_seed=7, confidence=.95)
    args.update(changes)
    return paired_comparison(a, b, **args)


def test_paired_effect_and_seed_uncertainty_are_not_origin_iid():
    a, b = panel(), panel(((3.,) * 4, (6.,) * 4))
    result = compare({'fold': a}, {'fold': b})
    assert result['mean_difference'] == -1.5
    assert result['relative_reduction'] == pytest.approx(1 / 3)
    assert result['per_seed_difference'] == [-1., -2.]
    assert result['seed_difference_sd'] == pytest.approx(2 ** -.5)
    assert result['seed_win_fraction'] == 1.
    assert result['leave_one_seed_out_difference'] == [-2., -1.]
    assert result['difference_interval'] == [-2., -1.]
    assert result == compare({'fold': a}, {'fold': b})
    json.dumps(result, allow_nan=False)


def test_seed_draw_is_shared_across_fixed_folds_and_folds_are_equally_weighted():
    a1 = panel(((10.,) * 4, (0.,) * 4))
    b1 = panel(((0.,) * 4, (10.,) * 4))
    later = dict(calendar_start_ns=4 * DAY, calendar_end_ns=8 * DAY,
                 issue_times_ns=np.arange(4, 8, dtype=np.int64) * DAY + HOUR)
    a2 = panel(((0.,) * 4, (10.,) * 4), **later)
    b2 = panel(((10.,) * 4, (0.,) * 4), **later)
    result = compare({'first': a1, 'second': a2}, {'second': b2, 'first': b1})
    assert result['mean_difference'] == 0.
    assert result['difference_interval'] == [0., 0.]
    short_a = panel(((4.,), (4.,)), origin_ids=('a',),
                    issue_times_ns=np.array([4 * DAY + HOUR], np.int64),
                    calendar_start_ns=4 * DAY, calendar_end_ns=8 * DAY)
    short_b = replace(short_a, losses=np.zeros((2, 1)))
    result = compare({'long': a1, 'short': short_a}, {'long': b1, 'short': short_b})
    assert result['mean_difference'] == 2.  # equal folds, not 4/5 origin weight


def test_unequal_calendar_counts_use_loss_sums_and_counts():
    times = np.array([HOUR, 2 * HOUR, 3 * HOUR, DAY + HOUR], np.int64)
    a = panel(((0., 0., 0., 9.),) * 2, issue_times_ns=times, calendar_end_ns=2 * DAY)
    b = replace(a, losses=np.zeros((2, 4)))
    result = compare({'f': a}, {'f': b}, block_days=1)
    assert result['mean_difference'] == 2.25  # not the unweighted day mean 4.5
    assert result['relative_reduction'] is None
    assert result['relative_interval'] is None
    assert result['relative_interval_reason'] == 'nonpositive_reference'


def test_empty_calendar_days_remain_and_empty_draw_invalidates_interval():
    a = panel(((2.,), (4.,)), origin_ids=('only',),
              issue_times_ns=np.array([HOUR], np.int64), calendar_end_ns=3 * DAY)
    b = replace(a, losses=np.ones((2, 1)))
    result = compare({'f': a}, {'f': b}, block_days=1)
    assert result['mean_difference'] == 2.
    assert result['difference_interval'] is None
    assert result['interval_reason'] == 'empty_resampled_fold'
    assert result['empty_replicates'] > 0
    assert result['folds']['f']['calendar_days'] == 3
    assert result['folds']['f']['observed_days'] == 1


@pytest.mark.parametrize('change', [
    dict(seed_ids=(22, 11)), dict(origin_ids=('d', 'c', 'b', 'a')),
    dict(issue_times_ns=np.arange(4, dtype=np.int64) * DAY + 2 * HOUR),
    dict(support_fingerprint='different'), dict(metric='mae/v1'), dict(unit='W/m2'),
    dict(calendar_end_ns=5 * DAY),
])
def test_pairing_rejects_different_cohorts_targets_times_or_metrics(change):
    with pytest.raises(ValueError, match='align|pair'):
        compare({'f': panel()}, {'f': panel(**change)})


@pytest.mark.parametrize('change', [
    dict(seed_ids=(11, 11)), dict(seed_ids=(True, 22)),
    dict(origin_ids=('a', 'b', 'c', 'c')),
    dict(issue_times_ns=np.array([HOUR, HOUR, DAY + HOUR, 2 * DAY + HOUR])),
    dict(issue_times_ns=np.array([HOUR, DAY + HOUR, 2 * DAY + HOUR, 4 * DAY])),
    dict(issue_times_ns=np.arange(4, dtype=float) * DAY),
    dict(losses=np.full((2, 4), np.nan)), dict(losses=np.full((2, 4), -1.)),
    dict(losses=np.ones((4, 2))), dict(losses=np.ones((2, 4), bool)),
    dict(calendar_start_ns=HOUR), dict(calendar_end_ns=0),
])
def test_panel_rejects_invalid_or_silently_droppable_support(change):
    with pytest.raises(ValueError):
        panel(**change)


@pytest.mark.parametrize('change', [dict(block_days=0), dict(block_days=True),
    dict(block_days=5), dict(replicates=0), dict(replicates=True),
    dict(rng_seed=True), dict(confidence=1.), dict(confidence=float('nan'))])
def test_resampling_configuration_is_explicit_and_strict(change):
    with pytest.raises(ValueError):
        compare({'f': panel()}, {'f': panel()}, **change)


def test_missing_fold_or_seed_is_not_a_successful_pair():
    with pytest.raises(ValueError):
        compare({'f': panel()}, {'g': panel()})
    with pytest.raises(ValueError):
        compare({'f': panel(seed_ids=(11,), losses=np.ones((1, 4)))}, {'f': panel()})


def test_panel_owns_buffers_and_revalidates_forged_copies():
    raw = np.ones((2, 4))
    a = panel(losses=raw)
    raw[:] = 123
    assert a.losses[0, 0] == 1
    with pytest.raises(ValueError):
        a.losses.setflags(write=True)
    object.__setattr__(a, 'losses', np.full((2, 4), np.nan))
    with pytest.raises(ValueError):
        compare({'f': a}, {'f': panel()})


def test_finite_extreme_losses_cannot_publish_infinite_effects():
    with pytest.raises(ValueError, match='finite|arithmetic'):
        compare({'f': panel(losses=np.full((2, 4), 1e308))}, {'f': panel()})


def test_calendar_indices_do_not_wrap_across_int64_span():
    start, end = -100_000 * DAY, 100_000 * DAY
    times = np.array([-50_000 * DAY, 0, 50_000 * DAY, 99_999 * DAY], np.int64)
    a = panel(calendar_start_ns=start, calendar_end_ns=end, issue_times_ns=times)
    result = compare({'f': a}, {'f': a}, block_days=100_000, replicates=2)
    assert result['mean_difference'] == 0
    assert result['folds']['f']['observed_days'] == 4


def test_overlapping_fold_calendars_cannot_be_resampled_as_independent_paths():
    with pytest.raises(ValueError, match='overlap'):
        compare({'f': panel(), 'duplicated_path': panel()},
                {'f': panel(), 'duplicated_path': panel()})


def test_nonconstant_seeds_share_the_same_calendar_block_draw(monkeypatch):
    class LiteralDraws:
        def __init__(self):
            self.draws = iter(([0, 1], [0, 0], [0, 1], [2, 2]))

        def integers(self, low, high, size):
            result = np.array(next(self.draws))
            assert result.shape == (size,)
            return result

    # With seed cohort [0,1], each common-day pair averages exactly 15.
    # Independent day vectors for the two opposing seed paths would not.
    monkeypatch.setattr(np.random, 'default_rng', lambda seed: LiteralDraws())
    a = panel(((0., 10., 20., 30.), (30., 20., 10., 0.)))
    b = replace(a, losses=np.ones((2, 4)))
    result = compare({'f': a}, {'f': b}, replicates=2)
    assert result['difference_interval'] == [14., 14.]
