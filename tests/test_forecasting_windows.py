"""Literal grid/support cases catch future leakage, cadence bridges and purging."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset

NS = 1_000_000_000


def dataset(n=20, *, omitted=(), availability=True):
    ticks = np.array([i for i in range(n) if i not in omitted], dtype=np.int64)
    starts = ticks * NS
    features = np.column_stack((ticks + 1., ticks + 101.))
    targets = np.column_stack((ticks + 10., ticks + 110.))
    return TimeSeriesDataset(
        name='causal_fixture', role='synthetic_fixture', starts_ns=starts,
        ends_ns=starts + NS, features=features, feature_mask=np.ones(features.shape, bool),
        targets=targets, target_mask=np.ones(targets.shape, bool),
        feature_names=('a', 'b'), target_names=('a', 'b'),
        feature_units=('ua', 'ub'), target_units=('ua', 'ub'), cadence_seconds=1,
        availability_ns=np.broadcast_to((starts + NS)[:, None], features.shape) if availability else None,
        availability_policy='explicit' if availability else 'bin_end_earliest')


def spec(**kwargs):
    return replace(ForecastSpec(1, 2, 2, ('a',), ('a',), ('ua',), ('ua',)), **kwargs)


def build(data=None, task=None, *, start=0, end=10, name='train', groups=()):
    from solar_flare_jepa.forecasting.splitting import TemporalPartition
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    return build_partition_windows(dataset() if data is None else data,
                                   spec() if task is None else task,
                                   TemporalPartition(name, start * NS, end * NS), groups)


def test_exact_cut_endpoint_and_full_support_are_recorded():
    result = build(task=spec(feature_lookback_steps=1, label_maturity_steps=1), end=8)
    assert result.context.issue_times_ns.tolist() == [3 * NS, 4 * NS, 5 * NS]
    assert result.targets.grid.ends_ns[-1, -1] == 7 * NS
    assert result.support_manifest[-1]['end_ns'] == 8 * NS
    assert result.support_manifest[0]['start_ns'] == 0
    reasons = {x['issue_time_ns']: x['reasons'] for x in result.excluded_origins}
    assert 'support_before_partition' in reasons[2 * NS]
    assert 'support_after_partition' in reasons[6 * NS]
    record = result.as_dict()
    json.dumps(record, allow_nan=False)
    assert record['retained_origins'] == list(result.context.origin_ids)
    assert result.training_slice.split_fingerprint == result.split_fingerprint


def test_post_cut_perturbation_cannot_change_earlier_context_or_raw_fitting_values():
    original = dataset()
    f, t = original.features.copy(), original.targets.copy()
    f[10:] = 1e150
    t[10:] = -1e150
    changed = replace(original, features=f, targets=t)
    left, perturbed = build(original), build(changed)
    for attr in ('values', 'mask', 'starts_ns', 'ends_ns'):
        np.testing.assert_array_equal(getattr(left.context, attr), getattr(perturbed.context, attr))
    for attr in ('raw_features', 'raw_targets', 'raw_feature_mask', 'raw_target_mask'):
        np.testing.assert_array_equal(getattr(left.training_slice, attr), getattr(perturbed.training_slice, attr))
    assert left.context.origin_ids == perturbed.context.origin_ids
    assert left.training_slice.raw_starts_ns.tolist() == [i * NS for i in range(10)]


def test_raw_training_partition_is_unique_and_independent_of_stride_and_overlap():
    dense, sparse = build(), build(task=spec(stride_steps=4))
    assert sparse.context.issue_times_ns.tolist() == [4 * NS, 8 * NS]
    np.testing.assert_array_equal(dense.training_slice.raw_features, sparse.training_slice.raw_features)
    assert sparse.training_slice.raw_targets[:, 0].tolist() == list(range(10, 20))
    assert len(sparse.training_slice.raw_starts_ns) == 10


def test_partitions_have_no_shared_raw_or_dependency_support_and_keep_global_stride():
    left = build(task=spec(stride_steps=3))
    right = build(task=spec(stride_steps=3), start=10, end=20, name='validation')
    assert left.context.issue_times_ns.tolist() == [3 * NS, 6 * NS]
    assert right.context.issue_times_ns.tolist() == [12 * NS, 15 * NS, 18 * NS]
    assert right.training_slice is None
    assert max(x['end_ns'] for x in left.support_manifest) <= min(x['start_ns'] for x in right.support_manifest)
    assert set(left.context.origin_ids).isdisjoint(right.context.origin_ids)


def test_missing_cadence_excludes_context_lookback_target_and_maturity_gaps():
    result = build(dataset(omitted=(4,)), spec(feature_lookback_steps=1, label_maturity_steps=1), end=12)
    assert result.context.issue_times_ns.tolist() == [8 * NS, 9 * NS]
    assert any('missing_cadence' in x['reasons'] for x in result.excluded_origins)
    raw = result.training_slice
    assert raw.raw_starts_ns.tolist() == [i * NS for i in (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11)]
    assert raw.raw_feature_mask[:, 0].tolist() == [False, True, True, True, False, True, True, True, True, True, True]


def test_invalid_feature_lookback_masks_raw_dependents_and_excludes_complete_windows():
    data = dataset()
    masks = data.feature_mask.copy()
    masks[3, 0] = False
    result = build(replace(data, feature_mask=masks), spec(feature_lookback_steps=1))
    assert result.training_slice.raw_feature_mask[:, 0].tolist() == [False, True, True, False, False, True, True, True, True, True]
    # An independent target has no derivative dependency merely because a
    # feature does: mean/AR/MASE can still use all independently valid targets.
    assert result.training_slice.raw_target_mask[:, 0].tolist() == [True] * 10
    assert result.training_slice.raw_targets[:, 0].tolist() == list(range(10, 20))
    assert result.context.issue_times_ns.tolist() == [3 * NS, 7 * NS, 8 * NS]


def test_masked_policy_preserves_missing_cells_without_imputation():
    data = dataset()
    values, masks = data.targets.copy(), data.target_mask.copy()
    values[4, 0], masks[4, 0] = np.nan, False
    data = replace(data, targets=values, target_mask=masks)
    complete = build(data)
    masked = build(data, spec(eligibility_policy='masked'))
    assert 4 * NS not in complete.context.issue_times_ns
    row = list(masked.context.issue_times_ns).index(4 * NS)
    assert not masked.targets.mask[row, 0, 0]
    assert np.isnan(masked.targets.values[row, 0, 0])
    assert masked.context.issue_times_ns.tolist() == [i * NS for i in range(2, 9)]


def test_operational_delayed_features_are_not_exposed_at_issue_time():
    data = dataset()
    availability = data.availability_ns.copy()
    availability[3, 0] = 6 * NS
    data = replace(data, availability_ns=availability)
    result = build(data)
    assert result.context.issue_times_ns.tolist() == [2 * NS, 3 * NS, 6 * NS, 7 * NS, 8 * NS]
    assert any('unavailable_features' in x['reasons'] for x in result.excluded_origins)
    masked = build(data, spec(eligibility_policy='masked'))
    row = list(masked.context.issue_times_ns).index(4 * NS)
    assert not masked.context.mask[row, -1, 0]
    assert np.isnan(masked.context.values[row, -1, 0])


def test_operational_unknown_availability_rejected_and_retrospective_does_not_invent_it():
    with pytest.raises(ValueError, match='availability'):
        build(dataset(availability=False))
    result = build(dataset(availability=False), spec(availability_mode='retrospective_bin_end'))
    assert result.context.availability_ns is None
    assert result.context.issue_times_ns.tolist() == [i * NS for i in range(2, 9)]


def test_earliest_bin_end_bounds_are_not_actual_operational_availability():
    with pytest.raises(ValueError, match='availability'):
        replace(dataset(), availability_policy='bin_end_earliest')


def test_supplied_straddling_group_purges_support_and_raw_features_targets():
    from solar_flare_jepa.forecasting.splitting import EventGroup
    group = EventGroup('supplied_cross_cut', 8 * NS, 12 * NS, 13 * NS)
    train = build(groups=(group,))
    validation = build(start=10, end=20, name='validation', groups=(group,))
    assert train.context.issue_times_ns.tolist() == [i * NS for i in range(2, 7)]
    assert train.training_slice.raw_target_mask[:, 0].tolist() == [True] * 8 + [False] * 2
    assert train.training_slice.raw_feature_mask[:, 0].tolist() == [True] * 8 + [False] * 2
    assert validation.context.issue_times_ns[0] == 14 * NS
    assert any('event_group_not_contained' in x['reasons'] for x in train.excluded_origins)


def test_group_maturity_equality_admitted_and_later_maturity_purged():
    from solar_flare_jepa.forecasting.splitting import EventGroup
    contained = EventGroup('supplied', 4 * NS, 5 * NS, 10 * NS)
    mature = build(groups=(contained,))
    assert mature.context.issue_times_ns.tolist() == [i * NS for i in range(2, 9)]
    assert mature.support_manifest[1]['end_ns'] == 10 * NS
    immature = build(groups=(replace(contained, maturity_ns=10 * NS + 1),))
    assert immature.context.issue_times_ns.tolist() == [2 * NS, 7 * NS, 8 * NS]
    assert not immature.training_slice.raw_target_mask[4, 0]


def test_raw_training_masks_maturity_and_availability_past_partition_end():
    data = dataset()
    availability = data.availability_ns.copy()
    availability[4, 0] = 11 * NS
    result = build(replace(data, availability_ns=availability), spec(label_maturity_steps=2))
    assert not result.training_slice.raw_feature_mask[4, 0]
    assert result.training_slice.raw_target_mask[:, 0].tolist() == [True] * 8 + [False] * 2


def test_selected_channels_map_by_name_and_enforce_units_and_cadence():
    task = spec(feature_names=('b', 'a'), feature_units=('ub', 'ua'),
                target_names=('b',), target_units=('ub',))
    result = build(task=task)
    assert result.context.values[0].tolist() == [[101., 1.], [102., 2.]]
    assert result.targets.values[0, :, 0].tolist() == [112., 113.]
    for bad in [spec(feature_names=('missing',)), spec(feature_units=('wrong',)), spec(cadence_seconds=2)]:
        with pytest.raises(ValueError):
            build(task=bad)


def test_empty_window_result_has_valid_shapes_and_full_raw_training_partition():
    result = build(end=2)
    assert result.context.values.shape == (0, 2, 1)
    assert result.targets.values.shape == (0, 2, 1)
    assert result.retained_origins == ()
    assert len(result.excluded_origins) == 2
    assert result.training_slice.raw_starts_ns.tolist() == [0, NS]
    outside_data = build(start=2, end=3, name='validation')
    assert outside_data.training_slice is None


def test_boundary_group_input_and_manifest_fingerprint_are_validated():
    from solar_flare_jepa.forecasting.splitting import EventGroup, TemporalPartition
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    with pytest.raises(ValueError):
        build_partition_windows(dataset(), spec(), TemporalPartition('train', 0, NS + 1))
    with pytest.raises(ValueError):
        build(groups=(EventGroup('g', 1, 2, 2), EventGroup('g', 3, 4, 4)))
    assert build().split_fingerprint != build(task=spec(stride_steps=2)).split_fingerprint


def test_cadence_gap_partition_retains_empty_unique_raw_training_arrays():
    result = build(dataset(omitted=(1, 2, 3)), start=1, end=4)
    assert result.context.values.shape == (0, 2, 1)
    assert result.training_slice.raw_features.shape == (0, 1)
    assert result.training_slice.raw_targets.shape == (0, 1)
    assert result.as_dict()['raw_starts_ns'] == []


def test_lookback_dependencies_require_their_actual_availability():
    data = dataset()
    available = data.availability_ns.copy()
    available[1, 0] = 6 * NS
    result = build(replace(data, availability_ns=available), spec(feature_lookback_steps=2))
    assert result.context.issue_times_ns.tolist() == [6 * NS, 7 * NS, 8 * NS]
    assert result.context.availability_ns[0, 0, 0] == 5 * NS
    # The early partition fit deadline accepts that observation at t=10.
    assert result.training_slice.raw_feature_mask[3, 0]


def test_raw_fit_does_not_depend_on_any_retained_window():
    data = dataset()
    masks = data.target_mask.copy()
    masks[::2] = False
    result = build(replace(data, target_mask=masks))
    assert result.retained_origins == ()
    assert result.training_slice.raw_starts_ns.tolist() == [i * NS for i in range(10)]
    assert result.training_slice.raw_feature_mask[:, 0].all()
    assert result.training_slice.raw_target_mask[:, 0].tolist() == [False, True] * 5
    assert result.training_slice.raw_targets[1::2, 0].tolist() == [11., 13., 15., 17., 19.]


def test_manifest_is_detached_and_supplied_group_order_does_not_change_identity():
    from solar_flare_jepa.forecasting.splitting import EventGroup
    groups = (EventGroup('earlier', NS, 2 * NS, 2 * NS),
              EventGroup('later', 7 * NS, 8 * NS, 8 * NS))
    first = build(groups=groups)
    second = build(groups=tuple(reversed(groups)))
    assert first.split_fingerprint == second.split_fingerprint
    changed_manifest = first.manifest()
    changed_manifest['support_manifest'][0]['end_ns'] = -123
    assert first.split_fingerprint == second.split_fingerprint
    assert first.support_manifest[0]['end_ns'] == 4 * NS


def test_supplied_group_maturity_connects_a_straddling_group_and_purges_cluster():
    from solar_flare_jepa.forecasting.splitting import EventGroup
    # Origin t=2 originally depends on [0,4). The first group extends that
    # support to t=8; the second supplied group then extends it across the cut.
    groups = (EventGroup('initial', 3 * NS, 4 * NS, 8 * NS),
              EventGroup('connected_cross_cut', 7 * NS, 12 * NS, 13 * NS))
    result = build(groups=groups)
    record = next(r for r in result.excluded_origins if r['issue_time_ns'] == 2 * NS)
    assert record['event_group_ids'] == ['initial', 'connected_cross_cut']
    assert record['start_ns'] == 0
    assert record['end_ns'] == 13 * NS
    assert 'event_group_not_contained' in record['reasons']
    assert not result.training_slice.raw_feature_mask[3, 0]
    assert not result.training_slice.raw_target_mask[3, 0]
