"""Causal windows constructed only after partitioning the raw temporal axis.

Values stay in declared native units. There is no resampling, imputation,
transformation fitting, inferred availability or scientific event derivation.
"""
from dataclasses import dataclass
import json

import numpy as np

from .contracts import (ForecastContext, ForecastSpec, ForecastTargets, FutureGrid,
                        TimeSeriesDataset, TrainingSlice, canonical_json,
                        fingerprint_payload, _time_scalar)
from .splitting import EventGroup, TemporalPartition, validate_partition


@dataclass(frozen=True)
class WindowedPartition:
    context: ForecastContext
    targets: ForecastTargets
    training_slice: TrainingSlice | None
    _manifest_json: str

    @property
    def retained_origins(self):
        return self.context.origin_ids

    @property
    def excluded_origins(self):
        return tuple(self.as_dict()['excluded_origins'])

    @property
    def support_manifest(self):
        return tuple(self.as_dict()['support_manifest'])

    @property
    def split_fingerprint(self):
        return fingerprint_payload(self.as_dict())

    def as_dict(self):
        """A detached finite JSON-compatible retained/excluded/support manifest."""
        return json.loads(self._manifest_json)

    def manifest(self):
        return self.as_dict()


def _columns(selected_names, selected_units, names, units, kind):
    indices = []
    for name, unit in zip(selected_names, selected_units):
        if name not in names:
            raise ValueError(f'Unknown {kind} name: {name}')
        index = names.index(name)
        if units[index] != unit:
            raise ValueError(f'{kind} unit mismatch for {name}')
        indices.append(index)
    return indices


def _group_support(start, end, partition, groups):
    """Expand intersecting supplied group support, including cascading overlap."""
    associated = []
    bad = False
    changed = True
    while changed:
        changed = False
        for group in groups:
            if group.group_id in associated or not (start < group.end_ns and group.start_ns < end):
                continue
            associated.append(group.group_id)
            if (group.start_ns < partition.start_ns or group.end_ns > partition.end_ns
                    or group.maturity_ns > partition.end_ns):
                bad = True
            start, end = min(start, group.start_ns), max(end, group.maturity_ns)
            changed = True
    return start, end, associated, bad


def build_partition_windows(dataset: TimeSeriesDataset, spec: ForecastSpec,
                            partition: TemporalPartition, event_groups=()) -> WindowedPartition:
    """Build causal windows and (train only) full unique raw fitting arrays.

    Origins are dataset-origin + integer multiples of stride * cadence inside
    [partition.start, partition.end), even when an origin bin is missing.
    Each candidate requires contiguous observed bins throughout context,
    additional feature lookback, targets and label-maturity support. Full
    support must fit inside the partition, including intersecting supplied
    group intervals/maturity. Group support expands conservatively until no
    new supplied group interval intersects the expanded envelope. This generic
    closure can cause extra recorded exclusions; it derives no real events.
    End equality is admitted.

    Selected channels map by exact names and units, in spec order. ``complete``
    excludes any invalid/unavailable selected context or target cell. ``masked``
    retains such windows with false masks and NaNs, without filling values;
    cadence gaps and out-of-partition support still exclude whole windows.
    Operational context masks additionally require actual availability of every
    causal feature dependency by issue time. Retrospective mode uses completed
    bins without synthesizing latency; supplied actual availability remains
    enforced when present.

    Raw train arrays contain every observed bin wholly within the raw partition,
    once, independent of retained windows and stride. Feature masks require
    contiguous valid causal lookback and availability by partition end. Target
    masks require their independently valid target and complete maturity support
    within bounds; they do not acquire feature-only derivative dependencies.
    Supplied groups purged by bounds/maturity mask dependent raw cells too.
    Invalid values are hidden as NaNs; original dataset masks/values remain
    unchanged.
    """
    validate_partition(dataset, partition)
    if dataset.cadence_seconds != spec.cadence_seconds:
        raise ValueError('Dataset/spec cadence mismatch')
    if spec.availability_mode == 'operational' and (
            dataset.availability_ns is None or dataset.availability_policy != 'explicit'):
        raise ValueError('Operational windows require known actual availability')
    features = _columns(spec.feature_names, spec.feature_units,
                        dataset.feature_names, dataset.feature_units, 'feature')
    targets = _columns(spec.target_names, spec.target_units,
                       dataset.target_names, dataset.target_units, 'target')
    groups = tuple(event_groups)
    if (any(not isinstance(g, EventGroup) for g in groups)
            or len({g.group_id for g in groups}) != len(groups)):
        raise ValueError('Event groups require unique explicit EventGroup identities')
    # Canonical sorting makes caller ordering immaterial to support/identity.
    groups = tuple(sorted(groups, key=lambda g: (g.start_ns, g.end_ns, g.group_id)))
    cadence = spec.cadence_ns
    raw_rows = np.flatnonzero((dataset.starts_ns >= partition.start_ns)
                              & (dataset.ends_ns <= partition.end_ns))
    # No lookup for an observation outside the raw partition is created.
    lookup = {int(dataset.starts_ns[i]): i for i in raw_rows}

    def interval_rows(start, end):
        rows = [lookup.get(tick) for tick in range(start, end, cadence)]
        return None if any(row is None for row in rows) else rows

    def feature_eligibility(row, deadline):
        start = int(dataset.starts_ns[row]) - spec.feature_lookback_steps * cadence
        end = int(dataset.ends_ns[row])
        dep = interval_rows(start, end)
        mask = np.zeros(len(features), bool)
        available = None
        support_start, support_end, _, bad_group = _group_support(start, end, partition, groups)
        if dep is not None and support_start >= partition.start_ns and support_end <= partition.end_ns and not bad_group:
            mask = dataset.feature_mask[np.ix_(dep, features)].all(axis=0)
            if dataset.availability_ns is not None:
                available = dataset.availability_ns[np.ix_(dep, features)].max(axis=0)
                mask &= available <= deadline
        # Invalid entries' availability is inert because their mask is false.
        if available is None and dataset.availability_ns is not None:
            available = dataset.availability_ns[row, features]
        return mask, available

    def target_eligibility(row):
        start = int(dataset.starts_ns[row])
        end = int(dataset.ends_ns[row]) + spec.label_maturity_steps * cadence
        dep = interval_rows(start, end)
        support_start, support_end, _, bad_group = _group_support(start, end, partition, groups)
        if dep is None or support_start < partition.start_ns or support_end > partition.end_ns or bad_group:
            return np.zeros(len(targets), bool)
        return dataset.target_mask[row, targets].copy()

    raw_fmask = np.array([feature_eligibility(i, partition.end_ns)[0] for i in raw_rows], bool).reshape(-1, len(features))
    raw_tmask = np.array([target_eligibility(i) for i in raw_rows], bool).reshape(-1, len(targets))
    raw_fvalues = np.where(raw_fmask, dataset.features[np.ix_(raw_rows, features)], np.nan)
    raw_tvalues = np.where(raw_tmask, dataset.targets[np.ix_(raw_rows, targets)], np.nan)

    retained, excluded, supports, issues = [], [], [], []
    cvalues, cmasks, cstarts, cends, cavail = [], [], [], [], []
    tvalues, tmasks, tstarts, tends = [], [], [], []
    grid_origin = int(dataset.starts_ns[0])
    step = spec.stride_steps * cadence
    first = grid_origin + ((partition.start_ns - grid_origin + step - 1) // step) * step
    for issue in range(first, partition.end_ns, step):
        origin_id = f'origin:{issue}'
        base_start = issue - (spec.context_steps + spec.feature_lookback_steps) * cadence
        target_end = issue + spec.horizon_steps * cadence
        base_end = target_end + spec.label_maturity_steps * cadence
        # Coordinates are Python integers until checked, so overflow cannot wrap.
        _time_scalar(base_start)
        _time_scalar(base_end)
        support_start, support_end, associated, bad_group = _group_support(base_start, base_end, partition, groups)
        support = dict(origin_id=origin_id, issue_time_ns=issue, start_ns=support_start,
                       end_ns=support_end, context_start_ns=issue - spec.context_steps * cadence,
                       context_end_ns=issue, feature_lookback_start_ns=base_start,
                       target_start_ns=issue, target_end_ns=target_end,
                       label_maturity_ns=base_end, event_group_ids=associated)
        reasons = []
        if support_start < partition.start_ns:
            reasons.append('support_before_partition')
        if support_end > partition.end_ns:
            reasons.append('support_after_partition')
        if bad_group:
            reasons.append('event_group_not_contained')
        # Group times may be off the sample grid; coverage is checked for the
        # declared cadence dependency, not fabricated group observations.
        if not reasons and interval_rows(base_start, base_end) is None:
            reasons.append('missing_cadence')
        if reasons:
            excluded.append(dict(**support, reasons=reasons))
            continue
        cr = interval_rows(issue - spec.context_steps * cadence, issue)
        tr = interval_rows(issue, target_end)
        feature_masks, available = zip(*(feature_eligibility(i, issue) for i in cr))
        cmask = np.asarray(feature_masks, bool)
        tmask = np.asarray([target_eligibility(i) for i in tr], bool)
        if spec.eligibility_policy == 'complete':
            if not cmask.all():
                if dataset.availability_ns is not None and (np.asarray(available) > issue).any():
                    reasons.append('unavailable_features')
                if not dataset.feature_mask[np.ix_(interval_rows(base_start, issue), features)].all():
                    reasons.append('invalid_features')
            if not tmask.all():
                reasons.append('invalid_targets')
        if reasons:
            excluded.append(dict(**support, reasons=reasons))
            continue
        retained.append(origin_id)
        issues.append(issue)
        supports.append(support)
        cvalues.append(np.where(cmask, dataset.features[np.ix_(cr, features)], np.nan))
        cmasks.append(cmask)
        cstarts.append(dataset.starts_ns[cr])
        cends.append(dataset.ends_ns[cr])
        if dataset.availability_ns is not None:
            cavail.append(available)
        tvalues.append(np.where(tmask, dataset.targets[np.ix_(tr, targets)], np.nan))
        tmasks.append(tmask)
        tstarts.append(dataset.starts_ns[tr])
        tends.append(dataset.ends_ns[tr])

    count = len(issues)
    dataset_id = dataset.fingerprint
    context = ForecastContext(
        np.asarray(cvalues, float).reshape(count, spec.context_steps, len(features)),
        np.asarray(cmasks, bool).reshape(count, spec.context_steps, len(features)),
        np.asarray(cstarts, np.int64).reshape(count, spec.context_steps),
        np.asarray(cends, np.int64).reshape(count, spec.context_steps),
        np.asarray(issues, np.int64), tuple(retained), spec, dataset_id,
        None if dataset.availability_ns is None else np.asarray(cavail, np.int64).reshape(count, spec.context_steps, len(features)))
    grid = FutureGrid(np.asarray(tstarts, np.int64).reshape(count, spec.horizon_steps),
                      np.asarray(tends, np.int64).reshape(count, spec.horizon_steps),
                      np.asarray(issues, np.int64), tuple(retained), spec, dataset_id)
    forecast_targets = ForecastTargets(
        np.asarray(tvalues, float).reshape(count, spec.horizon_steps, len(targets)),
        np.asarray(tmasks, bool).reshape(count, spec.horizon_steps, len(targets)), grid)
    manifest = dict(schema_version=1, partition=partition.as_dict(), dataset_fingerprint=dataset_id,
                    spec=spec.as_dict(), spec_fingerprint=spec.fingerprint,
                    origin_policy='dataset_origin_stride_grid_partition_issue_half_open',
                    raw_eligibility_policy=dict(
                        observations='full_unique_partition_independent_of_windows_and_stride',
                        features='valid_selected_channel_and_contiguous_causal_lookback_available_by_partition_end',
                        targets='independently_valid_target_with_contiguous_maturity_support_no_feature_only_dependencies',
                        supplied_groups='purge_dependent_cells_if_group_closure_interval_or_maturity_crosses_partition',
                        invalid_values='masked_nan_no_imputation'),
                    group_support_policy='closure_of_group_intervals_intersecting_expanded_dependency_envelope',
                    event_groups=[g.as_dict() for g in groups], retained_origins=retained,
                    excluded_origins=excluded, support_manifest=supports,
                    raw_starts_ns=dataset.starts_ns[raw_rows].tolist(),
                    raw_ends_ns=dataset.ends_ns[raw_rows].tolist(),
                    raw_feature_mask=raw_fmask.tolist(), raw_target_mask=raw_tmask.tolist())
    manifest_json = canonical_json(manifest)
    training = None
    if partition.name == 'train':
        training = TrainingSlice(context, forecast_targets, dataset.starts_ns[raw_rows],
                                 dataset.ends_ns[raw_rows], raw_fvalues, raw_fmask,
                                 raw_tvalues, raw_tmask, partition.start_ns, partition.end_ns,
                                 fingerprint_payload(manifest))
    return WindowedPartition(context, forecast_targets, training, manifest_json)
