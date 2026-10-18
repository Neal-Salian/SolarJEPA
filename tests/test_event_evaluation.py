"""Synthetic prospective split safeguards; no historical split certification."""
from copy import deepcopy
import importlib

import numpy as np
import pytest

S = 1_000_000_000


def origin(ident='a', context=10, issue=20, horizon=30, maturity=30, **changes):
    row = dict(origin_id=ident, context_start_ns=context*S, issue_ns=issue*S,
               horizon_end_ns=horizon*S, maturity_ns=maturity*S,
               feature_available_ns=issue*S)
    row.update(changes)
    return row


def event(ident='e', start=15, end=25):
    return dict(event_id=ident, support_start_ns=start*S,
                support_end_ns=None if end is None else end*S)


def partitions():
    return [dict(name='train', start_ns=0, end_ns=100*S),
            dict(name='test', start_ns=100*S, end_ns=200*S)]


def catalog(records=(), **changes):
    result = dict(records=list(records), selection_complete=True,
                  selection_basis='Synthetic declared catalog selection, not physical completeness',
                  coverage_start_ns=0, coverage_end_ns=200*S)
    result.update(changes)
    return result


def audit(origins=None, events=None, parts=None, embargo_seconds=0):
    # A missing implementation fails a real API test rather than collection.
    module = importlib.import_module('solar_flare_jepa.events.evaluation')
    return module.audit_chronological_split(
        [origin()] if origins is None else origins,
        catalog([event()]) if events is None else events,
        partitions() if parts is None else parts, embargo_seconds=embargo_seconds)


def by_origin(result):
    return {row['origin_id']: row for row in result['origin_audit']}


def test_retains_supported_origins_and_scopes_certification_to_declared_selection():
    result = audit()
    assert result['retained_origin_ids'] == {'train': ['a'], 'test': []}
    assert result['purged'] == {}
    assert result['certified'] is True
    assert result['certification_scope'] == 'selected_catalog_event_disjoint_support_only'
    assert result['physical_event_completeness'] == 'UNKNOWN'
    assert len(result['audit_fingerprint']) == 64


def test_undeclared_or_incomplete_catalog_never_certifies_even_empty_groups():
    for events in ([], [event()], catalog([], selection_complete=False)):
        result = audit(events=events)
        assert result['certified'] is False
        assert 'catalog_selection_completeness_not_declared' in result['certification_reasons']
        assert result['retained_origin_ids']['train'] == ['a']
    assert audit(events=catalog([]))['certified'] is True


def test_half_open_adjacent_partitions_and_event_endpoints():
    origins = [origin('left', 80, 90, 100, 100), origin('right', 100, 100, 110, 110)]
    result = audit(origins, catalog([event('l', 80, 100), event('r', 100, 110)]))
    assert result['retained_origin_ids'] == {'train': ['left'], 'test': ['right']}
    assert len(result['event_groups']) == 2
    assert by_origin(result)['left']['event_group_ids'] != by_origin(result)['right']['event_group_ids']


def test_context_and_maturity_crossing_partition_are_purged():
    rows = [origin('context', 99, 105, 110, 110),
            origin('maturity', 80, 90, 95, 101), origin('outside', 210, 220, 230, 230)]
    result = audit(rows, catalog([]))
    assert result['retained_origin_ids'] == {'train': [], 'test': []}
    assert 'support_crosses_partition' in result['purged']['context']
    assert 'support_crosses_partition' in result['purged']['maturity']
    assert result['purged']['outside'] == ['issue_outside_partitions']
    assert result['certified'] is False


def test_events_overlap_context_and_maturity_not_only_forecast_horizon():
    result = audit([origin('a', 10, 20, 25, 40)],
                   catalog([event('context', 12, 18), event('maturity', 35, 39),
                            event('outside', 40, 45)]))
    associated = by_origin(result)['a']['event_group_ids']
    assignments = result['event_group_assignments']
    assert associated == sorted([assignments['context'], assignments['maturity']])
    assert assignments['outside'] not in associated


def test_transitively_overlapping_events_are_one_deterministic_group():
    events = [event('a', 70, 90), event('b', 85, 110), event('c', 105, 130)]
    rows = [origin('a', 60, 65, 75, 75), origin('b', 120, 125, 135, 135)]
    result = audit(rows, catalog(events))
    assert len(result['event_groups']) == 1
    group = result['event_groups'][0]
    assert group['event_ids'] == ['a', 'b', 'c']
    assert group['support_start_ns'] == 70*S
    assert group['support_end_ns'] == 130*S
    assert group['origin_ids'] == ['a', 'b']
    assert group['origin_partitions'] == ['train', 'test']
    assert all('shared_event_group' in result['purged'][ident] for ident in ('a', 'b'))
    assert all('event_group_crosses_partition' in result['purged'][ident] for ident in ('a', 'b'))
    assert audit(list(reversed(rows)), catalog(list(reversed(events)))) == result


def test_event_group_crossing_partition_purges_even_without_opposite_origin():
    result = audit([origin('a', 80, 85, 95, 95)], catalog([event('e', 90, 120)]))
    assert result['purged']['a'] == ['event_group_crosses_partition']


def test_shared_event_context_is_detected_even_when_crossing_origin_already_purged():
    result = audit([origin('left', 80, 90, 95, 95), origin('right', 85, 105, 115, 115)],
                   catalog([event('same', 88, 92)]))
    assert 'shared_event_group' in result['purged']['left']
    assert 'shared_event_group' in result['purged']['right']
    assert 'support_crosses_partition' in result['purged']['right']


def test_explicit_embargo_uses_full_context_and_right_exclusive_boundary():
    rows = [origin('before', 109, 120, 130, 130),
            origin('edge', 110, 120, 130, 130)]
    result = audit(rows, catalog([]), embargo_seconds=10)
    assert result['retained_origin_ids']['test'] == ['edge']
    assert result['purged']['before'] == ['chronological_embargo']
    assert result['embargo_intervals'] == [dict(partition='test', start_ns=100*S, end_ns=110*S)]
    gap = partitions(); gap[1]['start_ns'] = 115*S
    assert audit([rows[1]], catalog([]), gap, embargo_seconds=10)['purged']['edge'] == ['support_crosses_partition']
    assert audit([origin('safe', 115, 120, 130, 130)], catalog([]), gap,
                 embargo_seconds=10)['purged'] == {}


def test_catalog_declared_coverage_must_contain_full_window_support():
    result = audit([origin(maturity=40)], catalog([], coverage_end_ns=35*S))
    assert result['purged']['a'] == ['catalog_selection_coverage']


def test_canonical_provenance_tracks_support_declarations_and_never_mutates_inputs():
    rows, events, parts = [origin()], catalog([event()]), partitions()
    original = deepcopy((rows, events, parts))
    first = audit(rows, events, parts)
    assert (rows, events, parts) == original
    events['records'][0]['support_end_ns'] += 1
    second = audit(rows, events, parts)
    assert first['audit_fingerprint'] != second['audit_fingerprint']
    assert first['event_group_fingerprint'] != second['event_group_fingerprint']
    events['selection_basis'] += ' amended'
    assert audit(rows, events, parts)['audit_fingerprint'] != second['audit_fingerprint']


@pytest.mark.parametrize('value', [True, np.bool_(False), 1.5, float('nan'), float('inf'),
                                  '10', None, -(2**63)-1, 2**63])
@pytest.mark.parametrize('field', ['context_start_ns', 'issue_ns', 'horizon_end_ns',
                                  'maturity_ns', 'feature_available_ns'])
def test_origin_coordinates_reject_coercion_nonfinite_and_int64_overflow(field, value):
    with pytest.raises(ValueError):
        audit([origin(**{field: value})])


@pytest.mark.parametrize('field,value', [('context_start_ns', 21*S), ('horizon_end_ns', 20*S),
                                        ('maturity_ns', 19*S), ('feature_available_ns', 21*S)])
def test_origin_support_order_and_noncausal_availability_are_rejected(field, value):
    with pytest.raises(ValueError):
        audit([origin(**{field: value})])


@pytest.mark.parametrize('value', [None, True, np.bool_(False), 1.5, float('nan'),
                                  float('inf'), 2**63, -(2**63)-1])
@pytest.mark.parametrize('field', ['support_start_ns', 'support_end_ns'])
def test_unknown_invalid_event_support_rejects_audit(field, value):
    row = event(); row[field] = value
    with pytest.raises(ValueError):
        audit(events=catalog([row]))


@pytest.mark.parametrize('records', [[event(end=15)], [event(end=14)], [event(), event()]])
def test_empty_reversed_or_duplicate_event_support_is_rejected(records):
    with pytest.raises(ValueError):
        audit(events=catalog(records))


@pytest.mark.parametrize('value', [True, np.bool_(False), -1, 0.5, float('nan'),
                                  float('inf'), '0', None, 2**63])
def test_embargo_must_be_exact_nonnegative_int64_nanosecond_duration(value):
    with pytest.raises(ValueError):
        audit(embargo_seconds=value)


@pytest.mark.parametrize('field,value', [('start_ns', True), ('end_ns', 1.5),
                                        ('start_ns', float('nan')), ('end_ns', 2**63)])
def test_partition_coordinates_reject_coercion(field, value):
    parts = partitions(); parts[0][field] = value
    with pytest.raises(ValueError):
        audit(parts=parts)


@pytest.mark.parametrize('parts', [[], list(reversed(partitions())),
                                  [dict(name='p', start_ns=0, end_ns=0)],
                                  [dict(name='p', start_ns=0, end_ns=2), dict(name='q', start_ns=1, end_ns=3)],
                                  [dict(name='p', start_ns=0, end_ns=1), dict(name='p', start_ns=1, end_ns=2)]])
def test_partitions_require_unique_names_and_chronological_nonempty_nonoverlap(parts):
    with pytest.raises(ValueError):
        audit(parts=parts)


def test_duplicate_origins_missing_fields_and_generator_inputs_rejected():
    with pytest.raises(ValueError): audit([origin(), origin()])
    for argument, field in [('origins', 'issue_ns'), ('events', 'support_end_ns'), ('parts', 'end_ns')]:
        rows = {'origins': [origin()], 'events': [event()], 'parts': partitions()}
        del rows[argument][0][field]
        with pytest.raises(ValueError): audit(**{argument: rows[argument]})
    with pytest.raises(ValueError): audit(origins=iter([origin()]))
    with pytest.raises(ValueError): audit(events=iter([event()]))


@pytest.mark.parametrize('changes', [dict(selection_complete=1), dict(selection_basis=''),
                                    dict(coverage_start_ns=200*S), dict(coverage_end_ns=None)])
def test_catalog_declaration_is_explicit_and_validated(changes):
    with pytest.raises(ValueError): audit(events=catalog([], **changes))


def test_empty_origins_cannot_vacuously_certify_a_split():
    result = audit([], catalog([]))
    assert result['certified'] is False
    assert 'no_retained_origins' in result['certification_reasons']


@pytest.mark.parametrize('events,purged', [([event('early', 105, 120)], True),
                                          ([event('boundary', 110, 120)], False),
                                          ([event('early', 105, 112), event('later', 111, 120)], True)])
def test_event_group_support_cannot_reenter_after_starting_in_declared_embargo(events, purged):
    result = audit([origin('later', 115, 120, 130, 130)], catalog(events), embargo_seconds=10)
    if purged:
        assert result['purged']['later'] == ['event_group_chronological_embargo']
    else:
        assert result['retained_origin_ids']['test'] == ['later']


def test_label_maturity_cannot_precede_forecast_horizon_even_after_issue():
    with pytest.raises(ValueError):
        audit([origin(horizon=30, maturity=29)])


@pytest.mark.parametrize('records,coverage', [
    ([event('early', 5, 20)], dict(coverage_start_ns=10*S)),
    ([event('late', 15, 40)], dict(coverage_end_ns=35*S)),
    ([event('near', 15, 20), event('extension', 19, 40)], dict(coverage_end_ns=35*S)),
])
def test_event_group_support_must_fit_declared_catalog_coverage(records, coverage):
    result = audit([origin()], catalog(records, **coverage))
    assert result['purged']['a'] == ['event_group_catalog_selection_coverage']
    assert result['certified'] is False
