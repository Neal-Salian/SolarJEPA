"""Strict paired-seed, fixed-fold calendar-block loss comparisons.

Intervals condition on the supplied periods and training recipe. They require
representative seed runs and adequate weakly dependent calendar blocks; this
kernel verifies arithmetic, not nominal coverage or scientific independence.
"""
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from ..forecasting.contracts import _canonical_fields, _immutable, _time_scalar

DAY_NS = 86_400_000_000_000


def _label(value):
    if type(value) is not str or not value.strip():
        raise ValueError('Nonempty metric, unit and support identities are required')
    return value


def _integer(value, minimum, label):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{label} must be an integer >= {minimum}')
    return value


@dataclass(frozen=True, eq=False)
class LossPanel:
    """Per-origin mean losses, ordered as seed × common origin.

    Each origin must summarize the same lead/channel/quantile support with the
    same weights. ``support_fingerprint`` binds observations/masks/coordinates;
    it is a declaration from the caller, not authenticated provenance. Calendar
    bounds are whole UTC days, including days with no eligible origins.
    """
    seed_ids: tuple[int, ...]
    origin_ids: tuple[str, ...]
    issue_times_ns: np.ndarray
    losses: np.ndarray
    support_fingerprint: str
    metric: str
    unit: str
    calendar_start_ns: int
    calendar_end_ns: int

    def __post_init__(self):
        for name in ('seed_ids', 'origin_ids'):
            raw = getattr(self, name)
            if not isinstance(raw, (tuple, list)) or not raw:
                raise ValueError('Explicit nonempty ordered seed/origin identities required')
            values = tuple(raw)
            if name == 'seed_ids':
                for x in values:
                    _integer(x, 0, 'Seed')
            else:
                for x in values:
                    _label(x)
            if len(set(values)) != len(values):
                raise ValueError('Seed and origin identities must be unique')
            object.__setattr__(self, name, values)
        for name in ('support_fingerprint', 'metric', 'unit'):
            _label(getattr(self, name))
        for name in ('calendar_start_ns', 'calendar_end_ns'):
            object.__setattr__(self, name, _time_scalar(getattr(self, name)))
        if (self.calendar_start_ns >= self.calendar_end_ns
                or self.calendar_start_ns % DAY_NS or self.calendar_end_ns % DAY_NS):
            raise ValueError('Calendar bounds must be increasing whole UTC days')
        times = np.asarray(self.issue_times_ns)
        if (times.dtype.kind not in 'iu' or times.shape != (len(self.origin_ids),)
                or any(int(b) <= int(a) for a, b in zip(times, times[1:]))
                or any(not self.calendar_start_ns <= int(t) < self.calendar_end_ns for t in times)):
            raise ValueError('Origins require unique increasing integer times within the calendar')
        losses = np.asarray(self.losses)
        if (losses.dtype.kind not in 'fiu'
                or losses.shape != (len(self.seed_ids), len(self.origin_ids))
                or not np.isfinite(losses).all() or (losses < 0).any()):
            raise ValueError('Loss panel must contain finite nonnegative seed-by-origin losses')
        object.__setattr__(self, 'issue_times_ns', _immutable(times, np.int64))
        object.__setattr__(self, 'losses', _immutable(losses, np.float64))


def loss_panel_from_records(records, *, calendar_start_ns, calendar_end_ns):
    """Bind complete-support equal-cell dex pinball to canonical seed records.

    Records in one panel must share model/experiment/recipe/provenance and actual
    targets, grid, masks and quantile levels. Between panels, model identities
    may differ, but quantile levels are included in metric identity so pairs
    cannot compare different prediction targets. Point-only and partial-mask
    records require a separately defined metric; this adapter never fills them.
    """
    from .diagnostics import calibration_diagnostics
    from .records import EvaluationRecord
    from ..forecasting.contracts import fingerprint_payload

    if not isinstance(records, (tuple, list)) or not records:
        raise ValueError('An ordered nonempty cohort of EvaluationRecords is required')
    snapshots = []
    for record in records:
        if not isinstance(record, EvaluationRecord):
            raise ValueError('Expected EvaluationRecord')
        snapshots.append(EvaluationRecord(**_canonical_fields(record, EvaluationRecord)))
    first = snapshots[0]
    recipe = first.identity.as_dict()
    recipe.pop('seed')
    support = first.support_fingerprint
    losses, seeds = [], []
    for record in snapshots:
        identity = record.identity.as_dict()
        seeds.append(identity.pop('seed'))
        if (identity != recipe or record.support_fingerprint != support
                or record.prediction.quantile_levels != first.prediction.quantile_levels
                or record.prediction.model_id != first.prediction.model_id
                or record.prediction.point_interpretation != first.prediction.point_interpretation):
            raise ValueError('Seed records must align in actual support, quantiles and recipe')
        if not record.targets.mask.all():
            raise ValueError('Primary dex pinball adapter requires complete common target support')
        score = calibration_diagnostics(record.targets, record.prediction, space='log10', intervals=())
        losses.append(score['per_origin_mean_pinball'])
    metric = fingerprint_payload(dict(name='equal_cell_dex_mean_pinball', schema_version=1,
                                     spec_fingerprint=first.targets.grid.spec.fingerprint,
                                     quantile_levels=list(first.prediction.quantile_levels)))
    return LossPanel(tuple(seeds), first.targets.grid.origin_ids, first.targets.grid.issue_times_ns,
                     np.asarray(losses), support, f'dex_pinball/v1:{metric}', 'dex',
                     calendar_start_ns, calendar_end_ns)


def _panels(value):
    if not isinstance(value, Mapping) or not value:
        raise ValueError('Named fixed folds are required')
    result = {}
    for name, panel in value.items():
        _label(name)
        if not isinstance(panel, LossPanel):
            raise ValueError('Expected LossPanel')
        result[name] = LossPanel(**_canonical_fields(panel, LossPanel))
    return result


def _daily(panel, values=None):
    days = (panel.calendar_end_ns - panel.calendar_start_ns) // DAY_NS
    indices = np.asarray([(int(t) - panel.calendar_start_ns) // DAY_NS
                          for t in panel.issue_times_ns], np.int64)
    sums = np.zeros((len(panel.seed_ids), days), float)
    counts = np.bincount(indices, minlength=days)
    for seed, losses in enumerate(panel.losses if values is None else values):
        np.add.at(sums[seed], indices, losses)
    return sums, counts


def paired_comparison(folds_a, folds_b, *, block_days, replicates, rng_seed, confidence):
    """Equal-fold loss effect A−B; negative favours A, without a test decision.

    A shared seed vector crosses every fixed fold. Each fold's circular block
    draw is shared across all seeds and both models. Calendar days, including
    empty days, are retained. Required zero-support draws invalidate intervals,
    never get silently removed/redrawn. Relative reduction is 1−mean(A)/mean(B),
    not the mean of per-origin ratios. All analysis settings are explicit.
    """
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            return _compare(folds_a, folds_b, block_days=block_days,
                            replicates=replicates, rng_seed=rng_seed, confidence=confidence)
    except (FloatingPointError, OverflowError) as error:
        raise ValueError('Nonfinite comparison arithmetic') from error


def _compare(folds_a, folds_b, *, block_days, replicates, rng_seed, confidence):
    a, b = _panels(folds_a), _panels(folds_b)
    if set(a) != set(b):
        raise ValueError('Paired fold identities must align')
    names = sorted(a)
    calendars = sorted((p.calendar_start_ns, p.calendar_end_ns) for p in a.values())
    if any(left[1] > right[0] for left, right in zip(calendars, calendars[1:])):
        raise ValueError('Fixed fold calendars must not overlap: separate day draws require distinct paths')
    first = a[names[0]]
    seeds = first.seed_ids
    if len(seeds) < 2:
        raise ValueError('Joint seed uncertainty requires at least two paired seeds')
    _integer(block_days, 1, 'Block days')
    _integer(replicates, 2, 'Replicates')
    _integer(rng_seed, 0, 'RNG seed')
    if (type(confidence) not in (int, float) or not np.isfinite(confidence)
            or not 0 < confidence < 1):
        raise ValueError('Confidence must be finite and strictly within (0,1)')
    daily = []
    fold_report, fold_means_a, fold_means_b, fold_differences = {}, [], [], []
    for name in names:
        left, right = a[name], b[name]
        if (left.seed_ids != seeds or right.seed_ids != seeds
                or left.metric != first.metric or left.unit != first.unit
                or any(getattr(left, k) != getattr(right, k) for k in (
                    'origin_ids', 'support_fingerprint', 'metric', 'unit',
                    'calendar_start_ns', 'calendar_end_ns'))
                or not np.array_equal(left.issue_times_ns, right.issue_times_ns)):
            raise ValueError('Paired seeds, targets/support, times and metric identities must align')
        sums_a, counts = _daily(left)
        sums_b, _ = _daily(right)
        # Subtract paired observations before reducing: a small representable
        # effect can disappear when large model means are subtracted later.
        paired_losses = left.losses - right.losses
        sums_difference, _ = _daily(left, paired_losses)
        days = len(counts)
        if days < 2 or block_days > days:
            raise ValueError('At least two calendar days and a block no longer than the fold required')
        means_a, means_b = left.losses.mean(axis=1), right.losses.mean(axis=1)
        fold_means_a.append(means_a)
        fold_means_b.append(means_b)
        paired_means = paired_losses.mean(axis=1)
        fold_differences.append(paired_means)
        daily.append((sums_a, sums_b, sums_difference, counts))
        fold_report[name] = dict(mean_difference=float(paired_means.mean()),
                                 per_seed_difference=paired_means.tolist(),
                                 origins=len(left.origin_ids), calendar_days=days,
                                 observed_days=int((counts > 0).sum()))
    seed_a, seed_b = np.mean(fold_means_a, axis=0), np.mean(fold_means_b, axis=0)
    seed_difference = np.mean(fold_differences, axis=0)
    mean_a, mean_b = float(seed_a.mean()), float(seed_b.mean())
    rng = np.random.default_rng(rng_seed)
    differences, relatives = [], []
    empty, nonpositive = 0, 0
    for _ in range(replicates):
        sampled_seeds = rng.integers(0, len(seeds), size=len(seeds))
        draw_a, draw_b, draw_difference = [], [], []
        for sums_a, sums_b, sums_difference, counts in daily:
            days = len(counts)
            starts = rng.integers(0, days, size=(days + block_days - 1) // block_days)
            selected = ((starts[:, None] + np.arange(block_days)) % days).ravel()[:days]
            denominator = int(counts[selected].sum())
            if denominator == 0:
                draw_a.append(np.nan)
                draw_b.append(np.nan)
                draw_difference.append(np.nan)
            else:
                draw_a.append(float(sums_a[sampled_seeds][:, selected].sum()
                                    / (denominator * len(seeds))))
                draw_b.append(float(sums_b[sampled_seeds][:, selected].sum()
                                    / (denominator * len(seeds))))
                draw_difference.append(float(sums_difference[sampled_seeds][:, selected].sum()
                                             / (denominator * len(seeds))))
        aa, bb = float(np.mean(draw_a)), float(np.mean(draw_b))
        if not np.isfinite(aa + bb):
            empty += 1
            continue  # final interval is unavailable; never condition on these draws
        difference = float(np.mean(draw_difference))
        differences.append(difference)
        if bb <= 0:
            nonpositive += 1
        else:
            relatives.append(float(-np.divide(difference, bb)))
    percentiles = [50 * (1 - confidence), 50 * (1 + confidence)]
    reason = 'empty_resampled_fold' if empty else None
    relative_reason = reason or ('nonpositive_reference' if mean_b <= 0 or nonpositive else None)
    return dict(schema_version=1, estimand='equal_fixed_fold_mean_origin_loss',
                metric=first.metric, unit=first.unit, seed_ids=list(seeds),
                mean_a=mean_a, mean_b=mean_b, mean_difference=float(seed_difference.mean()),
                relative_reduction=None if mean_b <= 0 else float(-np.divide(seed_difference.mean(), mean_b)),
                per_seed_difference=seed_difference.tolist(),
                seed_difference_sd=float(seed_difference.std(ddof=1)),
                seed_win_fraction=float((seed_difference < 0).mean()),
                leave_one_seed_out_difference=[float(np.delete(seed_difference, i).mean())
                                              for i in range(len(seeds))],
                folds=fold_report,
                difference_interval=None if reason else np.percentile(differences, percentiles).tolist(),
                relative_interval=None if relative_reason else np.percentile(relatives, percentiles).tolist(),
                interval_reason=reason, relative_interval_reason=relative_reason,
                empty_replicates=empty, nonpositive_reference_replicates=nonpositive,
                bootstrap_negative_fraction=None if reason else float((np.asarray(differences) < 0).mean()),
                confidence=float(confidence), block_days=block_days,
                replicates=replicates, rng_seed=rng_seed,
                assumptions=['fixed named periods; no period-population inference',
                             'representative independent paired training seeds',
                             'adequate approximately stationary calendar blocks',
                             'conditional on supplied training data and selection recipe'],
                interpretation='Intervals are approximate; bootstrap fractions are descriptive, not p-values.')
