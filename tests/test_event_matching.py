"""Synthetic explicit alarms test event matching without physical onset claims."""
import itertools
import json

import numpy as np
import pytest


SECOND = 1_000_000_000


def match(alarms, events, **kwargs):
    from solar_flare_jepa.events.matching import match_events
    return match_events(alarms, events, decision_policy_id='synthetic_v1', **kwargs)


def alarm(name, issue, end):
    return dict(alarm_id=name, issue_ns=issue * SECOND, window_end_ns=end * SECOND)


def event(name, start):
    return dict(event_id=name, start_ns=start * SECOND)


def test_matching_maximizes_hits_before_earliest_issue_and_onset_preferences():
    result = match([alarm('first', 0, 300), alarm('second', 30, 150)],
                   [event('early', 100), event('late', 200)])
    assert [(row['alarm_id'], row['event_id']) for row in result['matches']] == [
        ('first', 'late'), ('second', 'early')]
    assert result['counts'] == dict(alarms=2, events=2, hits=2, false_alarms=0, misses=0)
    assert result['metrics']['recall']['value'] == 1.
    assert result['metrics']['csi']['value'] == 1.
    assert 'tn' not in result['counts']
    assert 'tss' not in result['metrics'] and 'hss' not in result['metrics']


def test_competing_alarms_and_onsets_are_lexically_tied_independent_of_input_order():
    alarms = [alarm('b', 0, 300), alarm('a', 0, 300), alarm('c', 5, 300)]
    events = [event('z', 100), event('y', 100)]
    expected = match(alarms, events)
    for aa, ee in itertools.product(itertools.permutations(alarms), itertools.permutations(events)):
        assert match(list(aa), list(ee)) == expected
    assert [(row['alarm_id'], row['event_id']) for row in expected['matches']] == [
        ('a', 'y'), ('b', 'z')]
    assert expected['unmatched_alarm_ids'] == ['c']
    assert expected['metrics']['precision']['value'] == pytest.approx(2/3)
    assert expected['metrics']['far']['value'] == pytest.approx(1/3)
    assert expected['metrics']['csi']['value'] == pytest.approx(2/3)


def test_default_minimum_lead_includes_60_seconds_but_excludes_window_end():
    result = match([alarm('a', 100, 300)],
                   [event('zero', 100), event('short', 159), event('boundary', 160), event('end', 300)])
    assert result['matches'][0]['event_id'] == 'boundary'
    assert result['matches'][0]['lead_seconds'] == 60.
    assert result['matches'][0]['advance_warning'] is True
    assert result['minimum_lead_seconds'] == 60
    assert result['unmatched_event_ids'] == ['zero', 'short', 'end']


def test_zero_minimum_lead_preserves_historical_half_open_semantics_without_advance_warning():
    result = match([alarm('a', 10, 20)],
                   [event('past', 9), event('now', 10), event('end', 20)],
                   minimum_lead_seconds=0)
    assert result['matches'][0]['event_id'] == 'now'
    assert result['matches'][0]['lead_seconds'] == 0.
    assert result['matches'][0]['advance_warning'] is False
    assert result['unmatched_event_ids'] == ['past', 'end']
    assert result['timing_precision_seconds'] == 60
    assert result['lead_time_caveat']
    assert result['reduction']['true_negatives'] == 'NOT_DEFINED_FOR_EVENT_ALARM_LISTS'
    json.dumps(result, allow_nan=False)


def test_minimum_lead_is_part_of_input_identity_even_if_no_matches_change():
    zero = match([], [], minimum_lead_seconds=0)
    minute = match([], [])
    assert zero['input_fingerprint'] != minute['input_fingerprint']
    assert len(zero['input_fingerprint']) == 64


@pytest.mark.parametrize('alarms,events,undefined', [
    ([], [], ('recall', 'precision', 'far', 'csi')),
    ([alarm('a', 0, 300)], [], ('recall',)),
    ([], [event('e', 100)], ('precision', 'far')),
])
def test_empty_event_or_alarm_lists_report_zero_denominators(alarms, events, undefined):
    result = match(alarms, events)
    for name in undefined:
        assert result['metrics'][name]['value'] is None
        assert result['metrics'][name]['reason'] == 'zero_denominator'
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('alarms,events', [
    ([alarm('a', 0, 300), alarm('a', 1, 300)], []),
    ([], [event('a', 100), event('a', 200)]),
    ([alarm('a', 100, 100)], []),
    ([dict(alarm_id='a', issue_ns=0., window_end_ns=SECOND)], []),
    ([dict(alarm_id='a', issue_ns=False, window_end_ns=SECOND)], []),
    ([], [dict(event_id='a', start_ns=1.5)]),
    ([], [dict(event_id='a', start_ns=2**63)]),
    ([], [dict(event_id=' ', start_ns=SECOND)]),
    ([], [dict(event_id='a', start_ns=SECOND, peak_ns=2*SECOND)]),
    ({}, []),
])
def test_invalid_identity_and_coordinates_are_not_coerced(alarms, events):
    with pytest.raises(ValueError):
        match(alarms, events)


@pytest.mark.parametrize('kwargs', [
    dict(minimum_lead_seconds=True), dict(minimum_lead_seconds=-1),
    dict(minimum_lead_seconds=60.), dict(timing_precision_seconds=True),
    dict(timing_precision_seconds=0), dict(matching_policy='nearest'),
])
def test_matching_rejects_undeclared_or_invalid_policy(kwargs):
    with pytest.raises(ValueError):
        match([], [], **kwargs)


def test_nonempty_explicit_decision_policy_is_required_and_numpy_integer_times_work():
    from solar_flare_jepa.events.matching import match_events
    with pytest.raises(ValueError):
        match_events([], [], decision_policy_id='')
    result = match([dict(alarm_id='a', issue_ns=np.int64(0), window_end_ns=np.int64(100*SECOND))],
                   [dict(event_id='e', start_ns=np.int64(60*SECOND))])
    assert result['matches'][0]['lead_seconds'] == 60.


def test_cardinality_and_lexical_assignment_agree_with_exhaustive_independent_oracle():
    # Small exhaustive assignment, using a 1-second lead to cover transformed
    # interval starts independently of the optimized interval/point algorithm.
    intervals = [(start, end) for start in range(4) for end in range(start+1, 5)]
    events = [event('e0', 0), event('e1', 1), event('e2', 2), event('e3', 3)]
    for left, right in itertools.product(intervals, repeat=2):
        alarms = [alarm('a', *left), alarm('b', *right)]
        ordered = sorted(alarms, key=lambda row: (row['issue_ns'], row['alarm_id']))
        feasible = []
        for choices in itertools.product(range(5), repeat=2):
            selected = [index for index in choices if index < 4]
            if len(set(selected)) != len(selected):
                continue
            if all(index == 4 or row['issue_ns'] + SECOND <= events[index]['start_ns'] < row['window_end_ns']
                   for row, index in zip(ordered, choices)):
                feasible.append((-len(selected), choices))
        _, best = min(feasible)
        expected = [(row['alarm_id'], events[index]['event_id'])
                    for row, index in zip(ordered, best) if index < 4]
        result = match(alarms, events, minimum_lead_seconds=1)
        assert [(row['alarm_id'], row['event_id']) for row in result['matches']] == expected
