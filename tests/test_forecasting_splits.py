"""Adversarial temporal-boundary validation with no scientific date inference."""
import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import TimeSeriesDataset


def dataset():
    starts = np.arange(12, dtype=np.int64) * 1_000_000_000
    return TimeSeriesDataset(
        name='split_fixture', role='synthetic_fixture', starts_ns=starts,
        ends_ns=starts + 1_000_000_000, features=np.ones((12, 1)),
        feature_mask=np.ones((12, 1), bool), targets=np.ones((12, 1)),
        target_mask=np.ones((12, 1), bool), feature_names=('x',),
        target_names=('x',), feature_units=('fixture_unit',),
        target_units=('fixture_unit',), cadence_seconds=1,
        availability_policy='bin_end_earliest')


def test_explicit_partitions_accept_touching_half_open_bounds_and_gaps():
    from solar_flare_jepa.forecasting.splitting import chronological_partitions
    parts = chronological_partitions(dataset(), [
        {'name': 'train', 'start_ns': 0, 'end_ns': 4_000_000_000},
        {'name': 'validation', 'start_ns': 4_000_000_000, 'end_ns': 7_000_000_000},
        {'name': 'calibration', 'start_ns': 8_000_000_000, 'end_ns': 9_000_000_000},
        {'name': 'test', 'start_ns': 9_000_000_000, 'end_ns': 12_000_000_000}])
    assert tuple(p.name for p in parts) == ('train', 'validation', 'calibration', 'test')
    assert parts[0].as_dict() == {'name': 'train', 'start_ns': 0, 'end_ns': 4_000_000_000}


@pytest.mark.parametrize('bounds', [
    [('train', 0, 5), ('validation', 4, 7), ('test', 7, 12)],
    [('validation', 0, 4), ('train', 4, 7), ('test', 7, 12)],
    [('train', 0, 4), ('test', 4, 12)],
    [('train', 0, 4), ('validation', 4, 7), ('validation', 7, 12)],
    [('train', -1, 4), ('validation', 4, 7), ('test', 7, 12)],
    [('train', 0, 4), ('validation', 4, 7), ('test', 7, 13)],
])
def test_reject_ambiguous_partition_order_overlap_roles_and_outside_dataset(bounds):
    from solar_flare_jepa.forecasting.splitting import TemporalPartition, chronological_partitions
    with pytest.raises(ValueError):
        chronological_partitions(dataset(), [
            TemporalPartition(n, s * 1_000_000_000, e * 1_000_000_000)
            for n, s, e in bounds])


def test_reject_non_grid_cut_and_unknown_dict_fields():
    from solar_flare_jepa.forecasting.splitting import chronological_partitions
    base = [dict(name='train', start_ns=0, end_ns=4_000_000_000),
            dict(name='validation', start_ns=4_000_000_000, end_ns=7_000_000_000),
            dict(name='test', start_ns=7_000_000_000, end_ns=12_000_000_000)]
    base[0]['end_ns'] += 1
    with pytest.raises(ValueError):
        chronological_partitions(dataset(), base)
    base[0]['end_ns'] -= 1
    base[0]['fraction'] = .3
    with pytest.raises(ValueError):
        chronological_partitions(dataset(), base)


@pytest.mark.parametrize('start,end', [(0, 0), (4, 3), (True, 4), (0., 4), (0, 2**63)])
def test_partition_rejects_invalid_integer_bounds(start, end):
    from solar_flare_jepa.forecasting.splitting import TemporalPartition
    with pytest.raises(ValueError):
        TemporalPartition('train', start, end)


def test_group_requires_declared_interval_and_maturity_at_or_after_end():
    from solar_flare_jepa.forecasting.splitting import EventGroup
    assert EventGroup('supplied', 1, 3, 3).as_dict() == {
        'group_id': 'supplied', 'start_ns': 1, 'end_ns': 3, 'maturity_ns': 3}
    for args in [('', 1, 3, 3), ('g', 3, 1, 4), ('g', 1, 3, 2), ('g', 1, 3, 3.)]:
        with pytest.raises(ValueError):
            EventGroup(*args)
