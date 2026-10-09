"""Retrospective catalog alignment and separate candidate onset labels.

No threshold crossing is promoted to a flare. Catalog classes use future peak
information for ground truth only. Unknown catalog completeness and unknown
operational availability remain explicit; labels never enter predictor arrays.
"""
from dataclasses import asdict
import json
import re

import numpy as np

from ..data.flare_catalog import FlareEvent, class_threshold
from ..forecasting.contracts import (
    ForecastSpec, FutureGrid, TimeSeriesDataset, _canonical_fields, _integer,
    _number, _time_scalar, fingerprint_payload,
)


MINUTE_NS = 60_000_000_000
ALIGNMENT_POLICY = 'native_UTC_catalog_times_known_state_bins_no_snapping_v1'


def _dataset_snapshot(dataset):
    if not isinstance(dataset, TimeSeriesDataset):
        raise ValueError('Alignment requires a TimeSeriesDataset')
    try:
        result = TimeSeriesDataset(**_canonical_fields(dataset, TimeSeriesDataset))
    except (AttributeError, TypeError) as exc:
        raise ValueError('Malformed dataset declarations') from exc
    if result.cadence_seconds != 60 or (result.starts_ns % MINUTE_NS).any():
        raise ValueError('GOES alignment requires UTC minute cadence')
    if 'xrsb_flux' not in result.target_names:
        raise ValueError('GOES alignment requires target xrsb_flux')
    if result.target_units[result.target_names.index('xrsb_flux')] != 'W/m2':
        raise ValueError('GOES xrsb_flux unit must be W/m2')
    metadata = json.loads(result.metadata_json)
    identity = metadata.get('source_identity')
    if not isinstance(identity, dict) or identity.get('platform') != 'GOES-16':
        raise ValueError('Dataset source identity must explicitly be GOES-16')
    return result


def _events_snapshot(events):
    if not isinstance(events, (tuple, list)):
        raise ValueError('Events require an explicit ordered tuple or list')
    captured, seen, catalogs = [], set(), {}
    for original in events:
        if not isinstance(original, FlareEvent):
            raise ValueError('Events must be explicit FlareEvent records')
        try:
            fields = _canonical_fields(original, FlareEvent)
            for name in ('catalog_id', 'event_id', 'source'):
                if not isinstance(fields[name], str) or not fields[name].strip():
                    raise ValueError(f'Explicit event {name} required')
            if (not isinstance(fields['catalog_sha256'], str)
                    or not re.fullmatch('[0-9a-f]{64}', fields['catalog_sha256'])):
                raise ValueError('Invalid catalog SHA-256 provenance')
            for name in ('start_ns', 'peak_ns', 'end_ns'):
                if name != 'end_ns' or fields[name] is not None:
                    fields[name] = _time_scalar(fields[name])
            if (fields['peak_ns'] < fields['start_ns'] or fields['end_ns'] is not None
                    and fields['end_ns'] < fields['peak_ns']):
                raise ValueError('Event timestamps must be chronologically ordered')
            class_threshold(fields['flare_class'])
            fields['peak_flux'] = _number(fields['peak_flux'])
            if fields['peak_flux'] <= 0:
                raise ValueError('Event peak irradiance must be positive')
            if not re.fullmatch(r'GOES-([1-9]|1[0-9])', fields['source']):
                raise ValueError('Unknown event irradiance source')
            for name in ('sequential_number', 'original_row'):
                fields[name] = _integer(fields[name], positive=True)
            if type(fields['peak_saturated']) is not bool:
                raise ValueError('Peak saturation must be an explicit boolean')
            if (not isinstance(fields['flags'], tuple)
                    or any(not isinstance(flag, str) or not flag.strip() for flag in fields['flags'])):
                raise ValueError('Catalog flags require explicit string tuples')
            fields['flags'] = tuple(sorted(set(fields['flags'])))
            event = FlareEvent(**fields)
        except (AttributeError, TypeError, KeyError) as exc:
            raise ValueError('Malformed event declarations') from exc
        prior_digest = catalogs.setdefault(event.catalog_id, event.catalog_sha256)
        if prior_digest != event.catalog_sha256:
            raise ValueError('One catalog identity cannot name conflicting SHA-256 bytes')
        key = (event.catalog_id, event.event_id)
        if key in seen:
            raise ValueError('Duplicate catalog event identity')
        seen.add(key)
        captured.append(event)
    return tuple(sorted(captured, key=lambda e: (e.start_ns, e.peak_ns, e.catalog_id, e.event_id)))


def _catalog_provenance(events, supplied):
    """Capture declared pinned identities; file verification belongs to acquisition."""
    inferred = {(event.catalog_id, event.catalog_sha256) for event in events}
    if supplied is None:
        if not inferred:
            raise ValueError('Empty events require an explicit catalog source identity')
        return sorted(inferred)
    if not isinstance(supplied, tuple) or not supplied:
        raise ValueError('Explicit catalog provenance requires a nonempty tuple')
    identities = set()
    seen = set()
    for row in supplied:
        if type(row) is not dict or set(row) != {'catalog_id', 'sha256'}:
            raise ValueError('Each catalog provenance identity requires catalog_id and sha256')
        catalog, digest = row['catalog_id'], row['sha256']
        if (type(catalog) is not str or not catalog.strip() or type(digest) is not str
                or not re.fullmatch('[0-9a-f]{64}', digest) or catalog in seen):
            raise ValueError('Malformed or duplicate catalog provenance identity')
        seen.add(catalog)
        identities.add((catalog, digest))
    if inferred and identities != inferred:
        raise ValueError('Supplied catalog provenance identity contradicts event source bytes')
    return sorted(identities)


def _event_ambiguities(event):
    reasons = []
    if event.end_ns is None:
        reasons.append('unknown_end')
    if event.source != 'GOES-16':
        reasons.append('source_mismatch')
    if event.peak_saturated:
        reasons.append('peak_saturated')
    if event.sequential_number > 1:
        reasons.append('sequential_flare')
    if any(value is not None and value % MINUTE_NS for value in
           (event.start_ns, event.peak_ns, event.end_ns)):
        reasons.append('off_minute_catalog_time')
    return reasons


def _support(dataset, start, end):
    """Inspect intersecting bins without moving an observation or event time."""
    first = int(np.searchsorted(dataset.ends_ns, start, side='right'))
    last = int(np.searchsorted(dataset.starts_ns, end, side='left'))
    rows = np.arange(first, last, dtype=np.int64)
    continuous = bool(len(rows) and dataset.starts_ns[first] <= start
                      and dataset.ends_ns[last - 1] >= end
                      and np.array_equal(dataset.ends_ns[first:last - 1],
                                         dataset.starts_ns[first + 1:last]))
    channel = dataset.target_names.index('xrsb_flux')
    return dict(start_ns=start, end_ns=end, observed_bins=len(rows),
        before_dataset=start < int(dataset.starts_ns[0]),
        after_dataset=end > int(dataset.ends_ns[-1]),
        missing_cadence=not continuous,
        invalid_xrsb_bins=int((~dataset.target_mask[rows, channel]).sum()))


def align_events(events, dataset: TimeSeriesDataset) -> list[dict]:
    """Retain events whose known start/peak/end span intersects dataset bins.

    Event state timestamps refer to one-minute means, so known support includes
    the final state's entire bin. An unknown end limits *known* support to the
    peak bin; it never fabricates physical cessation or indefinite continuation.
    Overlap diagnostics describe known shared bin support, not event merging.
    """
    dataset = _dataset_snapshot(dataset)
    events = _events_snapshot(events)
    dataset_id = dataset.fingerprint
    metadata = json.loads(dataset.metadata_json)
    retained = []
    for event in events:
        last_state = event.peak_ns if event.end_ns is None else event.end_ns
        support_end = _time_scalar(last_state + MINUTE_NS)
        if not (event.start_ns < int(dataset.ends_ns[-1])
                and support_end > int(dataset.starts_ns[0])):
            continue
        support = _support(dataset, event.start_ns, support_end)
        ambiguities = _event_ambiguities(event)
        for key, reason in (('before_dataset', 'event_support_before_dataset'),
                            ('after_dataset', 'event_support_after_dataset'),
                            ('missing_cadence', 'event_support_missing_cadence'),
                            ('invalid_xrsb_bins', 'event_support_invalid_xrsb')):
            if support[key]:
                ambiguities.append(reason)
        fields = asdict(event)
        fields.pop('flags')
        retained.append(dict(**fields, catalog_flags=list(event.flags), dataset_name=dataset.name,
            dataset_fingerprint=dataset_id, dataset_provenance=metadata,
            alignment_policy=ALIGNMENT_POLICY, timestamp_precision_seconds=60,
            physical_timing_uncertainty='UNKNOWN',
            known_support_end_ns=support_end, event_support=support,
            ambiguity_flags=sorted(set(ambiguities))))
    for row in retained:
        overlaps = [other for other in retained if other is not row
                    and row['start_ns'] < other['known_support_end_ns']
                    and other['start_ns'] < row['known_support_end_ns']]
        row['overlapping_event_ids'] = [other['event_id'] for other in overlaps]
        row['overlapping_catalog_events'] = [dict(catalog_id=other['catalog_id'],
            catalog_sha256=other['catalog_sha256'], event_id=other['event_id']) for other in overlaps]
    return retained


def _future_snapshot(grid, dataset):
    if not isinstance(grid, FutureGrid):
        raise ValueError('Onset labels require a FutureGrid')
    try:
        fields = _canonical_fields(grid, FutureGrid)
        if not isinstance(fields['spec'], ForecastSpec):
            raise ValueError('Onset labels require an explicit ForecastSpec')
        fields['spec'] = ForecastSpec(**_canonical_fields(fields['spec'], ForecastSpec))
        grid = FutureGrid(**fields)
    except (AttributeError, TypeError) as exc:
        raise ValueError('Malformed future-grid declarations') from exc
    if grid.dataset_fingerprint != dataset.fingerprint:
        raise ValueError('Future-grid dataset identity mismatch')
    if grid.spec.cadence_seconds != dataset.cadence_seconds:
        raise ValueError('Future-grid cadence mismatch')
    if (grid.issue_times_ns % MINUTE_NS).any():
        raise ValueError('Forecast issues must be on the native UTC minute grid')
    for kind in ('feature', 'target'):
        names, units = getattr(dataset, kind + '_names'), getattr(dataset, kind + '_units')
        for name, unit in zip(getattr(grid.spec, kind + '_names'), getattr(grid.spec, kind + '_units')):
            if name not in names:
                raise ValueError(f'Future-grid unknown {kind} name')
            if units[names.index(name)] != unit:
                raise ValueError(f'Future-grid {kind} unit mismatch')
    if 'xrsb_flux' not in grid.spec.target_names:
        raise ValueError('Onset labels require an xrsb_flux forecast target')
    return grid


def label_onsets(events, dataset: TimeSeriesDataset, grid: FutureGrid,
                 minimum_class='M1.0', *, catalog_interval, catalog_provenance=None) -> dict:
    """Return separate catalog-start occurrence labels for [issue, horizon_end).

    Classification is the catalog's retrospective peak class, never reconstructed
    from a model output. Maturity includes horizon end and every candidate
    onset's peak-bin end, because subthreshold classifications also use future
    peak information. Full horizon B quality and every candidate's start-to-peak
    support must be valid. Uncertain positives remain positive but
    receive false validity, with diagnostics. ``catalog_interval`` is a declared
    selection envelope, not evidence of physical-event detection completeness.
    Empty event inputs require separately declared pinned catalog provenance;
    this function validates identities but does not re-open source catalog files.
    """
    dataset = _dataset_snapshot(dataset)
    events = _events_snapshot(events)
    grid = _future_snapshot(grid, dataset)
    catalogs = _catalog_provenance(events, catalog_provenance)
    threshold = class_threshold(minimum_class)
    if not isinstance(catalog_interval, tuple) or len(catalog_interval) != 2:
        raise ValueError('Catalog interval requires an explicit (start_ns, end_ns) tuple')
    catalog_start, catalog_end = (_time_scalar(value) for value in catalog_interval)
    if catalog_end <= catalog_start:
        raise ValueError('Catalog interval must be chronologically ordered')
    definition = dict(version=1, event_quantity='cataloged_flare_start_occurrence',
        occurrence_interval='issue_inclusive_horizon_end_exclusive', minimum_class=minimum_class,
        minimum_peak_irradiance_W_m2=threshold, classification='retrospective_catalog_peak_class',
        classification_maturity='max_horizon_end_and_all_candidate_onset_peak_bin_ends',
        alignment_policy=ALIGNMENT_POLICY, timestamp_precision_seconds=60,
        physical_timing_uncertainty='UNKNOWN',
        quality_policy='complete_xrsb_horizon_and_all_candidate_starts_through_peak_bins',
        source_policy='GOES-16_only_no_cross_spacecraft_substitution',
        saturation_policy='any_saturated_onset_invalid_even_if_reported_below_threshold',
        catalog_interval_meaning='selection_coverage_not_detection_completeness',
        catalog_completeness='UNKNOWN', physical_event_absence='UNKNOWN',
        operational_availability='UNKNOWN', predictor_label_separation='labels_returned_separately')
    outcomes, validity, maturity, mature, provenance = [], [], [], [], []
    for origin, issue, end in zip(grid.origin_ids, grid.issue_times_ns, grid.ends_ns[:, -1]):
        issue, end = int(issue), int(end)
        candidates = [event for event in events if issue <= event.start_ns < end]
        matching = [event for event in candidates if class_threshold(event.flare_class) >= threshold]
        deadline = max([end] + [event.peak_ns + MINUTE_NS for event in candidates])
        deadline = _time_scalar(deadline)
        is_mature = deadline <= int(dataset.ends_ns[-1])
        support = _support(dataset, issue, end)
        reasons, ambiguities, event_support = [], [], []
        if issue < catalog_start or end > catalog_end:
            reasons.append('outside_catalog_interval')
        for key, reason in (('before_dataset', 'horizon_before_dataset'),
                            ('after_dataset', 'horizon_after_dataset'),
                            ('missing_cadence', 'horizon_missing_cadence'),
                            ('invalid_xrsb_bins', 'horizon_invalid_xrsb')):
            if support[key]:
                reasons.append(reason)
        # A clipped subthreshold class or unsupported-spacecraft class cannot
        # certify a negative. Preserve its recorded class without relabeling it.
        for event in candidates:
            flags = _event_ambiguities(event)
            ambiguities.extend(flags)
            reasons.extend(flag for flag in flags if flag in
                           ('source_mismatch', 'peak_saturated', 'off_minute_catalog_time'))
        for event in candidates:
            peak_end = _time_scalar(event.peak_ns + MINUTE_NS)
            peak_support = _support(dataset, event.start_ns, peak_end)
            event_support.append(dict(event_id=event.event_id, catalog_id=event.catalog_id,
                catalog_sha256=event.catalog_sha256, **peak_support))
            if peak_end > int(dataset.ends_ns[-1]):
                reasons.append('class_peak_after_dataset')
            if event.start_ns < catalog_start or peak_end > catalog_end:
                reasons.append('class_support_outside_catalog_interval')
            if peak_support['missing_cadence']:
                reasons.append('event_start_to_peak_missing_cadence')
            if peak_support['invalid_xrsb_bins']:
                reasons.append('event_start_to_peak_invalid_xrsb')
        outcomes.append(bool(matching))
        validity.append(not reasons and is_mature)
        maturity.append(deadline)
        mature.append(is_mature)
        provenance.append(dict(origin_id=origin, issue_time_ns=issue, horizon_end_ns=end,
            event_ids=[event.event_id for event in matching],
            candidate_event_ids=[event.event_id for event in candidates],
            candidate_catalog_events=[dict(catalog_id=event.catalog_id,
                catalog_sha256=event.catalog_sha256, event_id=event.event_id,
                flare_class=event.flare_class, source=event.source,
                peak_saturated=event.peak_saturated) for event in candidates],
            catalog_events=[dict(catalog_id=event.catalog_id, catalog_sha256=event.catalog_sha256,
                event_id=event.event_id, start_ns=event.start_ns, peak_ns=event.peak_ns,
                end_ns=event.end_ns, flare_class=event.flare_class, source=event.source)
                for event in matching], maturity_ns=deadline, horizon_support=support,
            event_support=event_support, reasons=sorted(set(reasons)),
            ambiguity_flags=sorted(set(ambiguities))))
    return dict(schema_version=1, label_status='CANDIDATE_CATALOG_ONSET_LABELS',
        dataset_fingerprint=dataset.fingerprint, dataset_name=dataset.name,
        dataset_provenance=json.loads(dataset.metadata_json), spec_fingerprint=grid.spec.fingerprint,
        definition=definition, definition_id=fingerprint_payload(definition),
        catalog_interval=[catalog_start, catalog_end], catalog_completeness='UNKNOWN',
        catalog_identities=[dict(catalog_id=catalog, catalog_sha256=digest) for catalog, digest in catalogs],
        origin_ids=list(grid.origin_ids), issue_times_ns=grid.issue_times_ns.tolist(),
        outcomes=outcomes, valid_mask=validity, mature_mask=mature, maturity_ns=maturity,
        origin_provenance=provenance)
