"""Paired descriptive summaries of canonical development evaluation records.

The M3.1 outcome is NO_VALIDATED_REPLACEMENT. This adapter computes no sampling
interval, bootstrap, p-value or significance decision. Supplied fixed periods
and run identities remain declarations, rather than evidence of independence.
"""
from collections.abc import Mapping
import math

import numpy as np

from solar_flare_jepa.evaluation.comparison import DAY_NS, loss_panel_from_records
from solar_flare_jepa.evaluation.records import EvaluationRecord
from solar_flare_jepa.forecasting.contracts import _canonical_fields, canonical_json


_COMMON_IDENTITIES = (
    'experiment_id', 'code_fingerprint', 'data_provenance_fingerprint',
    'split_fingerprint', 'training_fingerprint', 'normalization_fingerprint',
    'protocol_fingerprint', 'selection_partition',
)
_GLOBAL_IDENTITIES = ('experiment_id', 'code_fingerprint', 'protocol_fingerprint')
_REASON = 'NO_VALIDATED_REPLACEMENT'


def _records(cohort):
    if not isinstance(cohort, (tuple, list)) or not cohort:
        raise ValueError('Each fold requires a nonempty ordered EvaluationRecord cohort')
    snapshots = []
    for record in cohort:
        if not isinstance(record, EvaluationRecord):
            raise ValueError('Expected canonical EvaluationRecords')
        snapshots.append(EvaluationRecord(**_canonical_fields(record, EvaluationRecord)))
    return snapshots


def _mean(values):
    return math.fsum(float(value) for value in values) / len(values)


def _sample_sd(values):
    if len(values) < 2:
        return None
    scale = max(abs(value) for value in values)
    if scale == 0:
        return 0.
    scaled = [value / scale for value in values]
    center = _mean(scaled)
    return scale * math.sqrt(math.fsum((value - center) ** 2 for value in scaled) / (len(values) - 1))


def descriptive_comparison(folds_a, folds_b, *, calendars):
    """Equal-fixed-fold, equal-seed loss effect A−B on complete common support.

    Each fold maps to an ordered cohort of ``EvaluationRecord`` objects.
    ``calendars`` must name exactly those folds and supply explicit half-open
    whole-UTC-day bounds ``(start_ns, end_ns)``; no time scale or calendar bounds
    are inferred. The canonical M1 adapter defines equal-cell dex pinball and
    rejects point-only or partial-target forecasts. Model/configuration identities
    may differ across arms, while common fitting/provenance identities must match.

    One seed is supported descriptively, with unavailable SD and leave-one-out
    effects. No planned-run completeness, statistical independence, nominal
    coverage or future-period representativeness is established by this function.
    """
    if (not isinstance(folds_a, Mapping) or not isinstance(folds_b, Mapping)
            or not folds_a or set(folds_a) != set(folds_b)):
        raise ValueError('Nonempty named paired folds must align')
    if any(type(name) is not str or not name.strip() for name in folds_a):
        raise ValueError('Explicit nonempty fold names required')
    if not isinstance(calendars, Mapping) or set(calendars) != set(folds_a):
        raise ValueError('Explicit calendar declarations must match every fold exactly')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            return _summarize(folds_a, folds_b, calendars)
    except (FloatingPointError, OverflowError) as error:
        raise ValueError('Nonfinite descriptive comparison arithmetic') from error


def _summarize(folds_a, folds_b, calendars):
    folds, fold_a, fold_b, fold_differences = {}, [], [], []
    record_fingerprints, model_ids = {}, {}
    seed_ids = metric = unit = global_identity = model_recipes = None
    bounds = []
    for name in sorted(folds_a):
        calendar = calendars[name]
        if not isinstance(calendar, (tuple, list)) or len(calendar) != 2:
            raise ValueError('Each calendar requires explicit start and end bounds')
        left_records, right_records = _records(folds_a[name]), _records(folds_b[name])
        left = loss_panel_from_records(left_records, calendar_start_ns=calendar[0], calendar_end_ns=calendar[1])
        right = loss_panel_from_records(right_records, calendar_start_ns=calendar[0], calendar_end_ns=calendar[1])
        if (left.seed_ids != right.seed_ids
                or any(getattr(left, key) != getattr(right, key) for key in (
                    'origin_ids', 'support_fingerprint', 'metric', 'unit'))
                or not np.array_equal(left.issue_times_ns, right.issue_times_ns)):
            raise ValueError('Paired seeds, exact target support, times and metric identities must align')
        left_identity, right_identity = left_records[0].identity, right_records[0].identity
        if any(getattr(left_identity, key) != getattr(right_identity, key) for key in _COMMON_IDENTITIES):
            raise ValueError('Paired common fitting and provenance identities must align')
        declared_global = tuple(getattr(left_identity, key) for key in _GLOBAL_IDENTITIES)
        declared_recipes = tuple((records[0].identity.model_version, records[0].identity.config_fingerprint,
            records[0].prediction.model_id, records[0].prediction.point_interpretation)
            for records in (left_records, right_records))
        if seed_ids is None:
            seed_ids, metric, unit, global_identity = left.seed_ids, left.metric, left.unit, declared_global
            model_recipes = declared_recipes
        elif (left.seed_ids != seed_ids or left.metric != metric or left.unit != unit
              or declared_global != global_identity):
            raise ValueError('All folds require one ordered seed cohort, metric, experiment, code and protocol')
        if declared_recipes != model_recipes:
            raise ValueError('Each comparison model and recipe must remain identical across fixed folds')
        bounds.append((left.calendar_start_ns, left.calendar_end_ns))
        # Pair before reduction. Subtracting two rounded model means can erase
        # a representable small effect shared with a much larger loss offset.
        differences = left.losses - right.losses
        means_a = [_mean(row) for row in left.losses]
        means_b = [_mean(row) for row in right.losses]
        means_d = [_mean(row) for row in differences]
        fold_a.append(means_a)
        fold_b.append(means_b)
        fold_differences.append(means_d)
        observed_days = len({(int(issue) - left.calendar_start_ns) // DAY_NS for issue in left.issue_times_ns})
        folds[name] = dict(mean_a=_mean(means_a), mean_b=_mean(means_b), mean_difference=_mean(means_d),
            per_seed_difference=means_d, origins=len(left.origin_ids),
            calendar_start_ns=left.calendar_start_ns, calendar_end_ns=left.calendar_end_ns,
            calendar_days=(left.calendar_end_ns - left.calendar_start_ns) // DAY_NS,
            observed_days=observed_days, support_fingerprint=left.support_fingerprint)
        record_fingerprints[name] = dict(a=[record.fingerprint for record in left_records],
                                         b=[record.fingerprint for record in right_records])
        model_ids[name] = dict(a=left_records[0].prediction.model_id, b=right_records[0].prediction.model_id)
    bounds.sort()
    if any(left[1] > right[0] for left, right in zip(bounds, bounds[1:])):
        raise ValueError('Fixed fold calendars must not overlap')
    seed_a = [_mean(column) for column in zip(*fold_a)]
    seed_b = [_mean(column) for column in zip(*fold_b)]
    seed_differences = [_mean(column) for column in zip(*fold_differences)]
    mean_a, mean_b, difference = _mean(seed_a), _mean(seed_b), _mean(seed_differences)
    result = dict(schema_version=1, status='DESCRIPTIVE_ONLY', inference_status='INFERENCE_UNAVAILABLE',
        inference_reason=_REASON, estimand='equal_fixed_fold_mean_origin_loss',
        metric=metric, unit=unit, seed_ids=list(seed_ids), model_ids=model_ids,
        mean_a=mean_a, mean_b=mean_b, mean_difference=difference,
        relative_reduction=-difference / mean_b if mean_b > 0 else None,
        relative_reduction_reason=None if mean_b > 0 else 'nonpositive_reference',
        per_seed_difference=seed_differences, seed_difference_sd=_sample_sd(seed_differences),
        seed_win_fraction=sum(value < 0 for value in seed_differences) / len(seed_differences),
        leave_one_seed_out_difference=[_mean(seed_differences[:index] + seed_differences[index + 1:])
            if len(seed_differences) > 1 else None for index in range(len(seed_differences))],
        folds=folds, record_fingerprints=record_fingerprints,
        difference_interval=None, relative_interval=None, standard_error=None,
        p_value=None, significance=None, bootstrap_negative_fraction=None,
        interval_reason=_REASON, relative_interval_reason=_REASON,
        interpretation='Descriptive fixed-period effects only; no statistical significance, '
                       'joint seed/calendar inference or future-period generalization.')
    # Check the complete publication boundary, including overflow in relative
    # reduction or dispersion. NaN/Infinity must never become result metadata.
    canonical_json(result)
    return result
