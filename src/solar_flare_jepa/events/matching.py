"""One-to-one matching of explicitly supplied alarms and catalog onset times.

Extracted from the historical evaluation matcher: maximum cardinality precedes
lexical issue/onset preferences. Event/ alarm lists cannot define true negatives.
"""
import hashlib
import heapq
import json

import numpy as np


MATCHING_POLICY = 'maximum_cardinality_earliest_issue_then_onset_v1'


def _integer(value, name, *, minimum=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{name} must be an integer')
    result = int(value)
    if minimum is not None and result < minimum:
        raise ValueError(f'{name} must be at least {minimum}')
    return result


def _identity(value, name):
    if type(value) is not str or not value.strip():
        raise ValueError(f'Explicit nonempty {name} is required')
    return value


def _records(records, kind):
    if type(records) not in (list, tuple):
        raise ValueError('Records require an explicit ordered list or tuple')
    keys = {'alarm_id', 'issue_ns', 'window_end_ns'} if kind == 'alarm' else {'event_id', 'start_ns'}
    result, seen = [], set()
    for row in records:
        if type(row) is not dict or set(row) != keys:
            raise ValueError(f'{kind} record requires exact {sorted(keys)} fields')
        item = {kind+'_id': _identity(row[kind+'_id'], kind+' identity')}
        if item[kind+'_id'] in seen:
            raise ValueError(f'Duplicate {kind} identity')
        seen.add(item[kind+'_id'])
        for key in keys - {kind+'_id'}:
            item[key] = _integer(row[key], key)
            if not np.iinfo(np.int64).min <= item[key] <= np.iinfo(np.int64).max:
                raise ValueError('UTC nanosecond coordinate outside int64 range')
        if kind == 'alarm' and item['window_end_ns'] <= item['issue_ns']:
            raise ValueError('Alarm validity interval must be nonempty and future')
        result.append(item)
    if kind == 'alarm':
        return sorted(result, key=lambda x: (x['issue_ns'], x['alarm_id']))
    return sorted(result, key=lambda x: (x['start_ns'], x['event_id']))


def _cardinality(alarms, events, minimum_lead_ns):
    """Maximum interval/point cardinality by earliest expiring active interval."""
    active, position, count = [], 0, 0
    for event in events:
        start = event['start_ns']
        while position < len(alarms) and alarms[position]['issue_ns'] + minimum_lead_ns <= start:
            alarm = alarms[position]
            heapq.heappush(active, (alarm['window_end_ns'], alarm['alarm_id']))
            position += 1
        while active and active[0][0] <= start:
            heapq.heappop(active)
        if active:
            heapq.heappop(active)
            count += 1
    return count


def match_events(alarms, events, *, decision_policy_id,
                 matching_policy=MATCHING_POLICY, timing_precision_seconds=60,
                 minimum_lead_seconds=60):
    """Match explicit alarms in ``[issue, window_end)`` subject to minimum lead.

    Cardinality is maximized first. Among all such matchings, earlier-issued
    alarms (then alarm ID) receive the earliest feasible onset (then event ID),
    provided that choice preserves maximum cardinality. Input ordering cannot
    alter matches or their identity. The default explicitly requires 60 seconds
    of nominal lead. Set ``minimum_lead_seconds=0`` for historical zero-lead
    matching: zero lead is a match, explicitly not advance warning.
    ``timing_precision_seconds`` describes catalog coordinate precision, not
    onset uncertainty. No timestamps or decisions are derived from flux here.
    """
    decision_policy_id = _identity(decision_policy_id, 'decision_policy_id')
    if type(matching_policy) is not str or matching_policy != MATCHING_POLICY:
        raise ValueError('Unsupported predeclared matching policy')
    precision = _integer(timing_precision_seconds, 'timing_precision_seconds', minimum=1)
    minimum_lead_seconds = _integer(minimum_lead_seconds, 'minimum_lead_seconds', minimum=0)
    minimum_lead_ns = minimum_lead_seconds * 1_000_000_000
    alarms, events = _records(alarms, 'alarm'), _records(events, 'event')
    payload = dict(schema_version=1, alarms=alarms, events=events,
        decision_policy_id=decision_policy_id, matching_policy=matching_policy,
        timing_precision_seconds=precision, minimum_lead_seconds=minimum_lead_seconds)
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False, allow_nan=False)
    fingerprint = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    remaining, matches = list(events), []
    needed = _cardinality(alarms, remaining, minimum_lead_ns)
    unmatched = []
    for index, alarm in enumerate(alarms):
        chosen = None
        if needed:
            for j, event in enumerate(remaining):
                if alarm['issue_ns'] + minimum_lead_ns <= event['start_ns'] < alarm['window_end_ns']:
                    rest = remaining[:j] + remaining[j+1:]
                    if 1 + _cardinality(alarms[index+1:], rest, minimum_lead_ns) >= needed:
                        chosen = j
                        break
        if chosen is None:
            unmatched.append(alarm['alarm_id'])
            continue
        event = remaining.pop(chosen)
        lead = (event['start_ns'] - alarm['issue_ns']) / 1_000_000_000
        matches.append(dict(alarm_id=alarm['alarm_id'], event_id=event['event_id'],
            issue_ns=alarm['issue_ns'], window_end_ns=alarm['window_end_ns'],
            start_ns=event['start_ns'], lead_seconds=lead, advance_warning=lead > 0))
        needed -= 1
    hits, false_alarms, misses = len(matches), len(unmatched), len(remaining)

    def ratio(numerator, denominator):
        return dict(value=numerator/denominator if denominator else None,
                    reason=None if denominator else 'zero_denominator', count=denominator)

    return dict(schema_version=1, decision_policy_id=decision_policy_id,
        matching_policy=matching_policy, input_fingerprint=fingerprint,
        timing_precision_seconds=precision, minimum_lead_seconds=minimum_lead_seconds,
        lead_time_caveat='Nominal catalog timestamp minus issuance; supplied catalog precision, detection delay and revisions do not establish exact physical onset or operational warning.',
        matches=matches, unmatched_alarm_ids=unmatched,
        unmatched_event_ids=[event['event_id'] for event in remaining],
        counts=dict(alarms=len(alarms), events=len(events), hits=hits,
                    false_alarms=false_alarms, misses=misses),
        metrics=dict(pod=ratio(hits, hits+misses), recall=ratio(hits, hits+misses),
            precision=ratio(hits, hits+false_alarms), far=ratio(false_alarms, hits+false_alarms),
            csi=ratio(hits, hits+misses+false_alarms), f1=ratio(2*hits, 2*hits+false_alarms+misses)),
        reduction=dict(candidate='issue_ns <= start_ns < window_end_ns and lead_seconds >= minimum_lead_seconds',
            matching='maximum cardinality; lexicographic issue/alarm_id then onset/event_id',
            true_negatives='NOT_DEFINED_FOR_EVENT_ALARM_LISTS'))
