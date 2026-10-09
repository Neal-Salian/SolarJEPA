"""Synthetic interval/point alarms; no physical flux-to-event decision rule."""
import itertools
import json

import numpy as np
import pytest

SECOND = 1_000_000_000


def match(alarms, events, **kwargs):
    from solar_flare_jepa.evaluation.event_matching import match_events
    return match_events(alarms, events, decision_policy_id='synthetic_predeclared_v1', **kwargs)


def alarm(name, issue, end):
    return dict(alarm_id=name, issue_ns=issue*SECOND, window_end_ns=end*SECOND)


def event(name, start):
    return dict(event_id=name, start_ns=start*SECOND)


def test_global_matching_preserves_two_hits_when_nearest_greedy_would_lose_one():
    result = match([alarm('flexible', 0, 30), alarm('restricted', 15, 25)],
                   [event('early', 10), event('late', 20)])
    assert [(x['alarm_id'], x['event_id']) for x in result['matches']] == [
        ('flexible', 'early'), ('restricted', 'late')]
    assert [x['lead_seconds'] for x in result['matches']] == [10., 5.]
    assert result['metrics']['pod']['value'] == 1.
    assert result['metrics']['far']['value'] == 0.
    assert 'tss' not in result['metrics'] and 'hss2' not in result['metrics']


def test_matching_uses_maximum_cardinality_before_earliest_onset_preference():
    # Early issue can match both, later issue only the early onset.
    result = match([alarm('first', 0, 30), alarm('second', 5, 15)],
                   [event('early', 10), event('late', 20)])
    assert [(x['alarm_id'], x['event_id']) for x in result['matches']] == [
        ('first', 'late'), ('second', 'early')]


def test_repeated_alarms_get_one_credit_and_ties_are_order_invariant():
    alarms = [alarm('b', 0, 30), alarm('a', 0, 30), alarm('c', 5, 30)]
    events = [event('z', 10), event('y', 10)]
    expected = None
    for aa, ee in itertools.product(itertools.permutations(alarms), itertools.permutations(events)):
        result = match(list(aa), list(ee))
        if expected is None:
            expected = result
        assert result == expected
    assert [(x['alarm_id'], x['event_id']) for x in expected['matches']] == [('a', 'y'), ('b', 'z')]
    assert expected['unmatched_alarm_ids'] == ['c']
    assert expected['metrics']['precision']['value'] == pytest.approx(2/3)
    assert expected['metrics']['far']['value'] == pytest.approx(1/3)
    assert expected['metrics']['f1']['value'] == pytest.approx(4/5)


def test_half_open_horizon_accepts_zero_lead_but_excludes_end_and_past():
    result = match([alarm('a', 10, 20)], [event('past', 9), event('now', 10), event('end', 20)])
    assert result['matches'][0]['event_id'] == 'now'
    assert result['matches'][0]['lead_seconds'] == 0.
    assert result['matches'][0]['advance_warning'] is False
    assert result['unmatched_event_ids'] == ['past', 'end']
    assert result['timing_precision_seconds'] == 60
    assert result['lead_time_caveat']
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('alarms,events,undefined', [
    ([], [], ('pod', 'precision', 'far', 'recall', 'f1')),
    ([alarm('a', 0, 10)], [], ('pod', 'recall')),
    ([], [event('e', 5)], ('precision', 'far')),
])
def test_zero_events_and_alarms_have_explicit_denominator_reasons(alarms, events, undefined):
    result = match(alarms, events)
    for name in undefined:
        assert result['metrics'][name]['value'] is None
        assert result['metrics'][name]['reason'] == 'zero_denominator'
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('alarms,events', [
    ([alarm('a', 0, 10), alarm('a', 1, 12)], []),
    ([], [event('a', 1), event('a', 2)]),
    ([alarm('a', 10, 10)], []),
    ([{'alarm_id':'a', 'issue_ns':0., 'window_end_ns':SECOND}], []),
    ([{'alarm_id':'a', 'issue_ns':False, 'window_end_ns':SECOND}], []),
    ([], [{'event_id':'a', 'start_ns':1.5}]),
    ([], [{'event_id':'a', 'start_ns':2**63}]),
    ([], [{'event_id':' ', 'start_ns':SECOND}]),
])
def test_bad_identity_and_coordinates_fail_without_float_coercion(alarms, events):
    with pytest.raises(ValueError):
        match(alarms, events)


def test_explicit_decision_policy_and_matching_rule_are_required():
    from solar_flare_jepa.evaluation.event_matching import match_events
    with pytest.raises(ValueError):
        match_events([], [], decision_policy_id='')
    with pytest.raises(ValueError):
        match([], [], matching_policy='post_hoc_nearest')
    with pytest.raises(ValueError):
        match([], [], timing_precision_seconds=True)
    result = match([dict(alarm_id='a',issue_ns=np.int64(0),window_end_ns=np.int64(SECOND))],
                   [dict(event_id='e',start_ns=np.int64(0))])
    assert result['matches'][0]['lead_seconds'] == 0.


def test_interval_matching_agrees_with_exhaustive_assignment_oracle():
    # Exhaustive assignments independently check the optimization objective,
    # including cases where an early alarm must forgo its preferred event.
    intervals = [(start,end) for start in range(4) for end in range(start+1,5)]
    events = [event('e0',0),event('e1',1),event('e2',2),event('e3',3)]
    for left,right in itertools.product(intervals,repeat=2):
        alarms = [alarm('a',*left),alarm('b',*right)]
        ordered = sorted(alarms,key=lambda row:(row['issue_ns'],row['alarm_id']))
        feasible = []
        for choices in itertools.product(range(5),repeat=2):
            selected = [index for index in choices if index < 4]
            if len(set(selected)) != len(selected):
                continue
            if all(index == 4 or row['issue_ns'] <= events[index]['start_ns'] < row['window_end_ns']
                   for row,index in zip(ordered,choices)):
                feasible.append((-len(selected),choices))
        _,best = min(feasible)
        expected = [(row['alarm_id'],events[index]['event_id'])
                    for row,index in zip(ordered,best) if index < 4]
        result = match(alarms,events)
        assert [(row['alarm_id'],row['event_id']) for row in result['matches']] == expected
