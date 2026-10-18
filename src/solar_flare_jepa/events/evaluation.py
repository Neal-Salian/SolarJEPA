"""Prospective split auditing, independent of frozen historical evaluators."""
from collections.abc import Mapping
import hashlib
import json

from .labels import integer


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def _records(rows, identity, coordinates, name):
    if not isinstance(rows, (list, tuple)):
        raise ValueError(f'{name} requires an explicit list or tuple')
    result, seen = [], set()
    required = {identity, *coordinates}
    for row in rows:
        if not isinstance(row, Mapping) or not required.issubset(row):
            raise ValueError(f'{name} missing required record fields')
        ident = row[identity]
        if not isinstance(ident, str) or not ident.strip():
            raise ValueError(f'{name} requires a nonempty {identity}')
        if ident in seen:
            raise ValueError(f'Duplicate {name} {identity}')
        seen.add(ident)
        result.append({identity: ident,
                       **{key: integer(row[key], f'{name}.{key}') for key in coordinates}})
    return result


def audit_chronological_split(origins, events, partitions, *, embargo_seconds):
    """Purge prospective chronological windows using explicit catalog support.

    All records are mappings; collections must be lists or tuples. Coordinates
    are exact signed int64 UTC nanoseconds, never bools or rounded floats.

    ``origins`` records require unique nonempty string ``origin_id`` and fields
    ``context_start_ns <= issue_ns < horizon_end_ns``, ``maturity_ns >= horizon_end_ns``
    and ``feature_available_ns <= issue_ns``. Maturity is the caller-declared
    exclusive label-support bound, as in ``label_events``; the full half-open
    window is ``[context_start_ns, max(horizon_end_ns, maturity_ns))``. Availability
    is the latest availability of every predictor used. Unknown support or
    noncausal predictors raise ValueError rather than inventing a safe window.

    ``events`` records require unique string ``event_id``, ``support_start_ns``
    and ``support_end_ns`` with start < end. Unknown/None ends raise ValueError.
    These are physical/dependence support declarations, not necessarily onset
    and peak times. All events overlapping any part of a window count, including
    events confined to its context or label-maturity extension. Overlapping event
    intervals form transitive components; touching half-open intervals do not.

    A bare event collection provides candidate provenance but cannot certify.
    To declare selected-catalog coverage, pass an envelope mapping with fields
    ``records``, exact bool ``selection_complete``, nonempty ``selection_basis``
    (caller provenance), and ordered int64 ``coverage_start_ns/coverage_end_ns``.
    A true declaration includes explicit negative coverage when records is empty.
    It is a caller assertion about that selection, never independently verified
    physical event completeness. Every retained window and its associated full
    event-group support must fit that coverage.

    ``partitions`` records require unique string ``name`` and ordered nonempty
    half-open ``start_ns/end_ns``. Partitions must be chronological/nonoverlapping
    in supplied order; adjacent partitions are valid. Assign each origin by issue
    time, then purge full support outside its partition. Purge every origin
    touching an event group that is not contained in that partition, or touching
    a group associated with origins in multiple partitions (including origins
    already purged). These conservative purges avoid choosing a favored split.

    ``embargo_seconds`` is an explicit nonnegative integer number of seconds.
    For each later partition, exclude window or associated event-group support
    intersecting the half-open interval
    ``[previous_partition.end_ns, previous_partition.end_ns + embargo_ns)``.
    Existing interpartition gaps count toward the embargo. Its right endpoint is
    permitted. Event-group embargo has its own purge reason, so an ongoing event
    cannot reenter through a later window. No implicit embargo or uncertainty
    padding is inferred; this does not establish active-region independence.

    Return deterministic per-partition retained IDs, purged IDs/reasons, complete
    per-origin audit and event-group membership/support/provenance fingerprints.
    ``certified`` requires a declared complete selection and at least one retained
    origin; its scope is only selected-catalog event-disjoint support. Physical
    event completeness always remains UNKNOWN. This does not certify observation
    quality, forecast validity, development exposure, or any existing V1/V2 split.
    Inputs are neither modified nor populated with inferred scientific values.
    """
    embargo_ns = integer(integer(embargo_seconds, 'embargo_seconds', 0)*10**9,
                         'embargo_nanoseconds', 0)
    origin_rows = _records(origins, 'origin_id', (
        'context_start_ns', 'issue_ns', 'horizon_end_ns', 'maturity_ns',
        'feature_available_ns'), 'origins')
    for row in origin_rows:
        if not (row['context_start_ns'] <= row['issue_ns'] < row['horizon_end_ns']
                and row['maturity_ns'] >= row['horizon_end_ns']):
            raise ValueError('Origin support must be chronologically ordered and nonempty')
        if row['feature_available_ns'] > row['issue_ns']:
            raise ValueError('Origin feature availability must be causal at issue time')
    origin_rows.sort(key=lambda row: (row['issue_ns'], row['origin_id']))

    declaration = None
    if isinstance(events, Mapping):
        required = {'records', 'selection_complete', 'selection_basis',
                    'coverage_start_ns', 'coverage_end_ns'}
        if not required.issubset(events):
            raise ValueError('Catalog declaration missing required fields')
        if type(events['selection_complete']) is not bool:
            raise ValueError('Catalog selection_complete must be an explicit bool')
        if not isinstance(events['selection_basis'], str) or not events['selection_basis'].strip():
            raise ValueError('Catalog selection_basis requires explicit provenance')
        declaration = {key: events[key] for key in ('selection_complete', 'selection_basis')}
        for key in ('coverage_start_ns', 'coverage_end_ns'):
            declaration[key] = integer(events[key], key)
        if declaration['coverage_start_ns'] >= declaration['coverage_end_ns']:
            raise ValueError('Catalog coverage must be ordered and nonempty')
        events = events['records']
    event_rows = _records(events, 'event_id', ('support_start_ns', 'support_end_ns'), 'events')
    for row in event_rows:
        if row['support_start_ns'] >= row['support_end_ns']:
            raise ValueError('Event support must be ordered and nonempty')
    event_rows.sort(key=lambda row: (row['support_start_ns'], row['support_end_ns'], row['event_id']))

    partition_rows = _records(partitions, 'name', ('start_ns', 'end_ns'), 'partitions')
    if not partition_rows:
        raise ValueError('At least one partition required')
    for index, row in enumerate(partition_rows):
        if row['start_ns'] >= row['end_ns']:
            raise ValueError('Partition support must be ordered and nonempty')
        if index and row['start_ns'] < partition_rows[index-1]['end_ns']:
            raise ValueError('Partitions must be chronological and nonoverlapping')
    embargo_intervals = []
    if embargo_ns:
        for previous, row in zip(partition_rows, partition_rows[1:]):
            end = integer(previous['end_ns']+embargo_ns, 'embargo end')
            embargo_intervals.append(dict(partition=row['name'], start_ns=previous['end_ns'], end_ns=end))

    # An interval sweep constructs connected components, including transitive
    # overlaps, without relying on caller group labels or event ordering.
    components = []
    component_end = None
    for row in event_rows:
        if component_end is None or row['support_start_ns'] >= component_end:
            components.append([])
            component_end = row['support_end_ns']
        else:
            component_end = max(component_end, row['support_end_ns'])
        components[-1].append(row)
    groups, assignments = [], {}
    for component in components:
        members = sorted(component, key=lambda row: row['event_id'])
        group_id = _fingerprint(members)
        group = dict(group_id=group_id, event_ids=[row['event_id'] for row in members],
                     support_start_ns=min(row['support_start_ns'] for row in members),
                     support_end_ns=max(row['support_end_ns'] for row in members),
                     origin_ids=[], origin_partitions=[])
        groups.append(group)
        assignments.update({row['event_id']: group_id for row in members})

    origin_audit = []
    for row in origin_rows:
        start = row['context_start_ns']
        end = max(row['horizon_end_ns'], row['maturity_ns'])
        partition = next((part for part in partition_rows
                          if part['start_ns'] <= row['issue_ns'] < part['end_ns']), None)
        associated = [group for group in groups
                      if start < group['support_end_ns'] and group['support_start_ns'] < end]
        for group in associated:
            group['origin_ids'].append(row['origin_id'])
            if partition is not None and partition['name'] not in group['origin_partitions']:
                group['origin_partitions'].append(partition['name'])
        reasons = []
        if partition is None:
            reasons.append('issue_outside_partitions')
        else:
            if start < partition['start_ns'] or end > partition['end_ns']:
                reasons.append('support_crosses_partition')
            for interval in embargo_intervals:
                if interval['partition'] == partition['name']:
                    if start < interval['end_ns'] and interval['start_ns'] < end:
                        reasons.append('chronological_embargo')
                    if any(group['support_start_ns'] < interval['end_ns']
                           and interval['start_ns'] < group['support_end_ns'] for group in associated):
                        reasons.append('event_group_chronological_embargo')
            if declaration is not None and (start < declaration['coverage_start_ns']
                                           or end > declaration['coverage_end_ns']):
                reasons.append('catalog_selection_coverage')
            if declaration is not None and any(
                    group['support_start_ns'] < declaration['coverage_start_ns']
                    or group['support_end_ns'] > declaration['coverage_end_ns'] for group in associated):
                reasons.append('event_group_catalog_selection_coverage')
            if any(group['support_start_ns'] < partition['start_ns']
                   or group['support_end_ns'] > partition['end_ns'] for group in associated):
                reasons.append('event_group_crosses_partition')
        origin_audit.append(dict(origin_id=row['origin_id'],
                                 partition=partition['name'] if partition else None,
                                 support_start_ns=start, support_end_ns=end,
                                 event_group_ids=sorted(group['group_id'] for group in associated),
                                 reasons=reasons))
    for group in groups:
        group['origin_ids'].sort()
        # Partition ordering reflects chronology, independently of origin IDs.
        group['origin_partitions'] = [row['name'] for row in partition_rows
                                      if row['name'] in group['origin_partitions']]
    shared = {group['group_id'] for group in groups if len(group['origin_partitions']) > 1}
    retained = {row['name']: [] for row in partition_rows}
    purged = {}
    for row in origin_audit:
        if shared.intersection(row['event_group_ids']):
            row['reasons'].append('shared_event_group')
        row['retained'] = not row['reasons']
        if row['retained']:
            retained[row['partition']].append(row['origin_id'])
        else:
            purged[row['origin_id']] = list(row['reasons'])
    certification_reasons = []
    if declaration is None or not declaration['selection_complete']:
        certification_reasons.append('catalog_selection_completeness_not_declared')
    if not any(retained.values()):
        certification_reasons.append('no_retained_origins')
    provenance = dict(policy='prospective_chronological_event_support_v1', origins=origin_rows,
                      events=event_rows, partitions=partition_rows, embargo_seconds=int(embargo_seconds),
                      catalog_selection=declaration)
    return dict(certified=not certification_reasons,
                certification_scope='selected_catalog_event_disjoint_support_only',
                certification_reasons=certification_reasons,
                physical_event_completeness='UNKNOWN', catalog_selection=declaration,
                retained_origin_ids=retained, purged=purged, origin_audit=origin_audit,
                event_groups=groups, event_group_assignments=dict(sorted(assignments.items())),
                embargo_intervals=embargo_intervals,
                event_group_fingerprint=_fingerprint(groups),
                audit_fingerprint=_fingerprint(provenance))
