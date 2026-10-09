"""Synthetic UTC bins test catalog alignment; these are not observational validation."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastSpec, FutureGrid, TimeSeriesDataset

MINUTE = 60_000_000_000


def data(*, omitted=(), bad=(), n=12):
    ticks = np.array([i for i in range(n) if i not in omitted], dtype=np.int64)
    values = np.column_stack((np.ones(len(ticks)) * 1e-6, np.ones(len(ticks)) * 1e-5))
    mask = np.ones(values.shape, dtype=bool)
    for tick in bad:
        mask[ticks == tick, 1] = False
    return TimeSeriesDataset('synthetic_alignment', 'synthetic_fixture', ticks * MINUTE,
        (ticks + 1) * MINUTE, values, mask, values, mask,
        ('xrsa_flux', 'xrsb_flux'), ('xrsa_flux', 'xrsb_flux'),
        ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), 60, availability_policy='bin_end_earliest',
        metadata_json='{"source_identity":{"platform":"GOES-16","instrument":"EXIS/XRS"}}')


def grid(dataset, *, issues=(2, 5, 8), horizon=3):
    task = ForecastSpec(60, 2, horizon, ('xrsb_flux',), ('xrsb_flux',), ('W/m2',), ('W/m2',),
                        availability_mode='retrospective_bin_end')
    issued = np.asarray(issues, dtype=np.int64) * MINUTE
    starts = issued[:, None] + np.arange(horizon, dtype=np.int64)[None, :] * MINUTE
    return FutureGrid(starts, starts + MINUTE, issued,
                      tuple(f'origin:{int(x)}' for x in issued), task, dataset.fingerprint)


def event(event_id='e1', *, start=2, peak=3, end=4, flare_class='M1.0', source='GOES-16',
          saturated=False, flags=(), offset_ns=0, catalog_id='catalog', catalog_sha256='a' * 64):
    from solar_flare_jepa.data.flare_catalog import FlareEvent
    return FlareEvent(catalog_id=catalog_id, catalog_sha256=catalog_sha256, event_id=event_id,
        start_ns=start * MINUTE + offset_ns, peak_ns=peak * MINUTE + offset_ns,
        end_ns=None if end is None else end * MINUTE + offset_ns, flare_class=flare_class,
        peak_flux=1e-5, source=source, sequential_number=1, peak_saturated=saturated,
        original_row=1, flags=tuple(flags))


def align(events, dataset):
    from solar_flare_jepa.evaluation.flare_alignment import align_events
    return align_events(events, dataset)


def labels(events, dataset, future=None, **kwargs):
    from solar_flare_jepa.evaluation.flare_alignment import label_onsets
    if not events and 'catalog_provenance' not in kwargs:
        kwargs['catalog_provenance'] = ({'catalog_id': 'catalog', 'sha256': 'a' * 64},)
    return label_onsets(events, dataset, grid(dataset) if future is None else future,
                        catalog_interval=kwargs.pop('catalog_interval', (0, 20 * MINUTE)), **kwargs)


def test_empty_catalog_alignment_contains_no_invented_events():
    assert align((), data()) == []


def test_alignment_retains_original_timestamps_and_catalog_dataset_provenance():
    dataset = data()
    row = align((event(offset_ns=30_000_000_000),), dataset)[0]
    assert row['start_ns'] == 150_000_000_000
    assert row['peak_ns'] == 210_000_000_000
    assert row['end_ns'] == 270_000_000_000
    assert row['catalog_id'] == 'catalog'
    assert row['catalog_sha256'] == 'a' * 64
    assert row['event_id'] == 'e1'
    assert row['dataset_fingerprint'] == dataset.fingerprint
    assert row['timestamp_precision_seconds'] == 60
    assert 'off_minute_catalog_time' in row['ambiguity_flags']
    json.dumps(row, allow_nan=False)


def test_boundary_spanning_events_are_retained_by_known_event_extent():
    rows = align((event('before', start=-4, peak=-3, end=-2),
                  event('span', start=-2, peak=1, end=3),
                  event('after', start=12, peak=13, end=14),
                  event('right', start=11, peak=13, end=14)), data())
    assert [row['event_id'] for row in rows] == ['span', 'right']
    assert 'event_support_before_dataset' in rows[0]['ambiguity_flags']
    assert 'event_support_after_dataset' in rows[1]['ambiguity_flags']


def test_unknown_end_is_retained_without_filling_or_claiming_known_continuation():
    rows = align((event('unknown', end=None), event('old', start=-5, peak=-4, end=None)), data())
    assert len(rows) == 1
    assert rows[0]['end_ns'] is None
    assert rows[0]['known_support_end_ns'] == 4 * MINUTE
    assert 'unknown_end' in rows[0]['ambiguity_flags']


def test_alignment_reports_quality_and_raw_cadence_gaps_for_full_known_event():
    row = align((event(start=2, peak=3, end=6),), data(omitted=(4,), bad=(5,)))[0]
    assert 'event_support_missing_cadence' in row['ambiguity_flags']
    assert 'event_support_invalid_xrsb' in row['ambiguity_flags']
    assert row['event_support']['invalid_xrsb_bins'] == 1


def test_known_event_overlaps_are_diagnostic_and_input_order_is_irrelevant():
    a, b = event('a', start=2, peak=3, end=5), event('b', start=4, peak=5, end=6)
    left, right = align((a, b), data()), align((b, a), data())
    assert left == right
    assert left[0]['overlapping_event_ids'] == ['b']
    assert left[1]['overlapping_event_ids'] == ['a']


def test_source_disagreement_saturation_and_native_flags_are_preserved():
    row = align((event(source='GOES-18', saturated=True, flags=('peak_saturated',)),), data())[0]
    assert row['source'] == 'GOES-18'
    assert row['peak_saturated'] is True
    assert 'source_mismatch' in row['ambiguity_flags']
    assert 'peak_saturated' in row['ambiguity_flags']
    assert row['catalog_flags'] == ['peak_saturated']


def test_duplicate_catalog_event_identity_fails_closed():
    with pytest.raises(ValueError, match='Duplicate'):
        align((event(), event()), data())


def test_alignment_does_not_modify_or_add_event_information_to_dataset():
    dataset = data()
    before = dataset.semantic_content()
    align((event(),), dataset)
    labels((event(),), dataset)
    assert dataset.semantic_content() == before
    assert dataset.feature_names == ('xrsa_flux', 'xrsb_flux')


def test_onsets_use_inclusive_issue_and_exclusive_horizon_end():
    dataset = data()
    result = labels((event('left', start=2, peak=3, end=4),
                     event('right', start=5, peak=6, end=7)), dataset)
    assert result['outcomes'] == [True, True, False]
    assert result['origin_provenance'][0]['event_ids'] == ['left']
    assert result['origin_provenance'][1]['event_ids'] == ['right']
    assert result['origin_provenance'][2]['event_ids'] == []
    assert result['valid_mask'] == [True, True, True]


def test_ongoing_event_is_not_new_onset_but_additional_overlapping_start_counts():
    dataset = data()
    ongoing = event('ongoing', start=1, peak=4, end=7)
    assert labels((ongoing,), dataset)['outcomes'][0] is False
    result = labels((ongoing, event('new', start=3, peak=5, end=6)), dataset)
    assert result['outcomes'][0] is True
    assert result['origin_provenance'][0]['event_ids'] == ['new']


@pytest.mark.parametrize(('flare_class', 'expected'), [('C9.9', False), ('M1.0', True),
                                                     ('M1.1', True), ('X1.0', True)])
def test_class_threshold_uses_catalog_class_not_untruncated_peak_flux(flare_class, expected):
    dataset = data()
    e = replace(event(flare_class=flare_class), peak_flux=1e-4)
    result = labels((e,), dataset)
    assert result['outcomes'][0] is expected


def test_unknown_end_does_not_invalidate_known_onset_and_peak_label():
    dataset = data()
    result = labels((event(end=None),), dataset)
    assert result['outcomes'][0] is True
    assert result['valid_mask'][0] is True
    assert 'unknown_end' in result['origin_provenance'][0]['ambiguity_flags']


def test_class_maturity_includes_full_peak_bin_and_negative_window_end():
    dataset = data()
    result = labels((event(peak=6, end=7),), dataset)
    assert result['maturity_ns'] == [7 * MINUTE, 8 * MINUTE, 11 * MINUTE]
    assert result['mature_mask'] == [True, True, True]
    assert result['definition']['classification'] == 'retrospective_catalog_peak_class'


def test_matching_event_peak_beyond_dataset_is_positive_but_immature_and_invalid():
    dataset = data()
    result = labels((event(start=8, peak=13, end=None),), dataset)
    assert result['outcomes'][2] is True
    assert result['valid_mask'][2] is False
    assert result['mature_mask'][2] is False
    assert result['maturity_ns'][2] == 14 * MINUTE
    assert 'class_peak_after_dataset' in result['origin_provenance'][2]['reasons']


@pytest.mark.parametrize(('kwargs', 'reason'), [({'bad': (3,)}, 'horizon_invalid_xrsb'),
                                               ({'omitted': (3,)}, 'horizon_missing_cadence')])
def test_horizon_quality_and_cadence_mask_both_positive_and_zero_event_windows(kwargs, reason):
    dataset = data(**kwargs)
    for events in ((), (event(),)):
        result = labels(events, dataset)
        assert result['valid_mask'][0] is False
        assert reason in result['origin_provenance'][0]['reasons']
    assert labels((event(),), dataset)['outcomes'][0] is True


def test_peak_bin_quality_outside_horizon_invalidates_retrospective_positive():
    dataset = data(bad=(6,))
    result = labels((event(peak=6, end=8),), dataset)
    assert result['outcomes'][0] is True
    assert result['valid_mask'][0] is False
    assert 'event_start_to_peak_invalid_xrsb' in result['origin_provenance'][0]['reasons']


@pytest.mark.parametrize(('kwargs', 'reason'), [({'saturated': True}, 'peak_saturated'),
                                               ({'source': 'GOES-18'}, 'source_mismatch')])
def test_uncertain_positive_is_retained_but_never_scored_as_valid(kwargs, reason):
    dataset = data()
    result = labels((event(**kwargs),), dataset)
    assert result['outcomes'][0] is True
    assert result['valid_mask'][0] is False
    assert reason in result['origin_provenance'][0]['reasons']


def test_empty_catalog_means_no_cataloged_start_and_does_not_prove_physical_absence():
    dataset = data()
    result = labels((), dataset)
    assert result['outcomes'] == [False, False, False]
    assert result['catalog_completeness'] == 'UNKNOWN'
    assert result['label_status'] == 'CANDIDATE_CATALOG_ONSET_LABELS'
    assert result['definition']['physical_event_absence'] == 'UNKNOWN'
    json.dumps(result, allow_nan=False)


def test_catalog_interval_is_selection_coverage_and_outside_horizons_are_invalid():
    dataset = data()
    result = labels((), dataset, catalog_interval=(3 * MINUTE, 10 * MINUTE))
    assert result['valid_mask'] == [False, True, False]
    assert 'outside_catalog_interval' in result['origin_provenance'][0]['reasons']
    assert result['catalog_completeness'] == 'UNKNOWN'


def test_definition_and_dataset_identity_are_deterministic_and_threshold_sensitive():
    dataset = data()
    e = event()
    a, b = labels((e,), dataset), labels((e,), dataset)
    assert a == b
    assert a['dataset_fingerprint'] == dataset.fingerprint
    assert a['definition_id'] != labels((e,), dataset, minimum_class='C1.0')['definition_id']


@pytest.mark.parametrize('minimum', ['M0', 'M-1', 'bogus', 1e-5, 'Mnan'])
def test_invalid_class_threshold_fails_closed(minimum):
    with pytest.raises(ValueError):
        labels((), data(), minimum_class=minimum)


@pytest.mark.parametrize('interval', [(0, 0), (True, 20 * MINUTE), (0.0, 20 * MINUTE),
                                     (0, 2 ** 64), [0, 20 * MINUTE]])
def test_invalid_catalog_interval_fails_closed(interval):
    with pytest.raises(ValueError):
        labels((), data(), catalog_interval=interval)


def test_grid_identity_mismatch_fails_closed():
    dataset = data()
    future = replace(grid(dataset), dataset_fingerprint='another_dataset')
    with pytest.raises(ValueError, match='identity'):
        labels((), dataset, future)


def test_grid_unit_mismatch_fails_closed():
    dataset = data()
    future = grid(dataset)
    wrong = replace(future.spec, target_units=('counts',))
    with pytest.raises(ValueError, match='unit'):
        labels((), dataset, replace(future, spec=wrong))


def test_grid_cadence_mismatch_fails_closed():
    dataset = data()
    task = replace(grid(dataset).spec, cadence_seconds=30)
    starts = np.array([[2 * MINUTE, 2 * MINUTE + MINUTE // 2, 3 * MINUTE]], dtype=np.int64)
    future = FutureGrid(starts, starts + MINUTE // 2, np.array([2 * MINUTE]),
                        ('different',), task, dataset.fingerprint)
    with pytest.raises(ValueError, match='cadence'):
        labels((), dataset, future)


def test_tampered_grid_coordinates_are_resnapshotted_and_rejected():
    dataset = data()
    future = grid(dataset)
    object.__setattr__(future, 'starts_ns', future.starts_ns - MINUTE)
    with pytest.raises(ValueError):
        labels((), dataset, future)


def test_tampered_dataset_intervals_are_resnapshotted_and_rejected():
    dataset = data()
    object.__setattr__(dataset, 'ends_ns', dataset.ends_ns + MINUTE)
    with pytest.raises(ValueError):
        align((), dataset)


def test_tampered_event_order_is_resnapshotted_and_rejected():
    e = event()
    object.__setattr__(e, 'peak_ns', MINUTE)
    with pytest.raises(ValueError):
        align((e,), data())


def test_dataset_missing_xrsb_or_wrong_units_cannot_generate_labels():
    dataset = data()
    with pytest.raises(ValueError, match='xrsb'):
        align((), replace(dataset, target_names=('a', 'b')))
    with pytest.raises(ValueError, match='unit'):
        align((), replace(dataset, target_units=('W/m2', 'counts')))


def test_empty_catalog_requires_explicit_catalog_provenance():
    from solar_flare_jepa.evaluation.flare_alignment import label_onsets
    dataset = data()
    with pytest.raises(ValueError, match='catalog.*identity'):
        label_onsets((), dataset, grid(dataset), catalog_interval=(0, 20 * MINUTE))


def test_zero_event_labels_retain_explicit_source_catalog_identity():
    dataset = data()
    result = labels((), dataset, catalog_provenance=({'catalog_id': 'quiet_catalog', 'sha256': 'b' * 64},))
    assert result['catalog_identities'] == [{'catalog_id': 'quiet_catalog', 'catalog_sha256': 'b' * 64}]
    assert result['outcomes'] == [False, False, False]


def test_supplied_catalog_identity_must_match_event_bytes():
    dataset = data()
    with pytest.raises(ValueError, match='catalog.*identity'):
        labels((event(),), dataset, catalog_provenance=({'catalog_id': 'catalog', 'sha256': 'b' * 64},))


@pytest.mark.parametrize('provenance', [(), [], ({'catalog_id': 'catalog', 'sha256': 'bad'},),
    ({'catalog_id': 'catalog', 'sha256': 'a' * 64, 'extra': 1},),
    ({'catalog_id': 'catalog', 'sha256': 'a' * 64}, {'catalog_id': 'catalog', 'sha256': 'a' * 64})])
def test_malformed_or_duplicate_catalog_provenance_is_rejected(provenance):
    dataset = data()
    with pytest.raises(ValueError):
        labels((), dataset, catalog_provenance=provenance)


@pytest.mark.parametrize(('kwargs', 'reason'), [({'saturated': True}, 'peak_saturated'),
                                               ({'source': 'GOES-18'}, 'source_mismatch')])
def test_uncertain_subthreshold_onset_cannot_certify_a_valid_negative(kwargs, reason):
    dataset = data()
    result = labels((event(flare_class='C9.9', **kwargs),), dataset)
    assert result['outcomes'][0] is False
    assert result['valid_mask'][0] is False
    assert result['origin_provenance'][0]['candidate_event_ids'] == ['e1']
    assert reason in result['origin_provenance'][0]['reasons']


def test_bad_dataset_source_declaration_fails_closed_as_value_error():
    dataset = replace(data(), metadata_json='{"source_identity":"GOES-16"}')
    with pytest.raises(ValueError):
        align((), dataset)


def test_subthreshold_peak_after_dataset_cannot_certify_a_mature_negative():
    dataset = data()
    result = labels((event(start=8, peak=13, end=None, flare_class='C9.9'),), dataset)
    assert result['outcomes'][2] is False
    assert result['valid_mask'][2] is False
    assert result['mature_mask'][2] is False
    assert result['maturity_ns'][2] == 14 * MINUTE
    assert 'class_peak_after_dataset' in result['origin_provenance'][2]['reasons']


def test_subthreshold_peak_quality_outside_horizon_cannot_certify_negative():
    dataset = data(bad=(6,))
    result = labels((event(peak=6, end=7, flare_class='C9.9'),), dataset)
    assert result['outcomes'][0] is False
    assert result['valid_mask'][0] is False
    assert 'event_start_to_peak_invalid_xrsb' in result['origin_provenance'][0]['reasons']


def test_positive_label_maturity_never_precedes_fixed_horizon_end():
    dataset = data()
    result = labels((event(peak=3, end=4),), dataset)
    assert result['outcomes'][0] is True
    assert result['maturity_ns'][0] == 5 * MINUTE


def test_positive_with_other_unmatured_subthreshold_start_remains_immature():
    dataset = data()
    result = labels((event('mature', start=8, peak=9, end=10),
                     event('late', start=9, peak=13, end=None, flare_class='C9.9')), dataset)
    assert result['outcomes'][2] is True
    assert result['valid_mask'][2] is False
    assert result['mature_mask'][2] is False
    assert result['maturity_ns'][2] == 14 * MINUTE
