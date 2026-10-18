"""Strict binary-decision scores and descriptive UTC-block resampling.

These functions accept declared decisions and eligibility masks. They do not
derive labels, decision thresholds, probabilities, or independent observations.
"""
import numpy as np


def _boolean_vector(value, name):
    result = np.asarray(value)
    if result.ndim != 1 or result.dtype != np.dtype(bool):
        raise ValueError(f'{name} must be a one-dimensional boolean array; no coercion')
    return result


def _decisions(truth, prediction, valid):
    truth = _boolean_vector(truth, 'truth')
    prediction = _boolean_vector(prediction, 'prediction')
    if truth.shape != prediction.shape:
        raise ValueError('truth and prediction must have equal lengths')
    valid = np.ones(truth.shape, dtype=bool) if valid is None else _boolean_vector(valid, 'valid')
    if valid.shape != truth.shape:
        raise ValueError('valid must have the same length as truth and prediction')
    return truth, prediction, valid


def _from_counts(tp, fp, fn, tn, total):
    tp, fp, fn, tn, total = map(int, (tp, fp, fn, tn, total))
    valid = tp + fp + fn + tn
    metrics, reasons = {}, {}

    def ratio(name, numerator, denominator):
        metrics[name] = numerator / denominator if denominator else None
        if not denominator:
            reasons[name] = 'zero_denominator'

    ratio('prevalence', tp + fn, valid)
    ratio('precision', tp, tp + fp)
    ratio('recall', tp, tp + fn)
    ratio('far', fp, tp + fp)
    ratio('fpr', fp, fp + tn)
    ratio('csi', tp, tp + fp + fn)
    # This common-denominator form also enforces both observed classes.
    ratio('tss', tp * tn - fp * fn, (tp + fn) * (fp + tn))
    ratio('hss', 2 * (tp * tn - fp * fn),
          (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn))
    ratio('balanced_accuracy', tp * (fp + tn) + tn * (tp + fn),
          2 * (tp + fn) * (fp + tn))
    return dict(counts=dict(total=total, valid=valid, excluded=total-valid,
                            tp=tp, fp=fp, fn=fn, tn=tn),
                metrics=metrics, undefined_reasons=reasons)


def binary_scores(truth, prediction, valid=None):
    """Score equally sized 1D boolean decisions on explicitly valid positions.

    Boolean sequences or boolean NumPy arrays are accepted; numeric and object
    arrays are never interpreted as decisions. Empty input requires explicitly
    boolean arrays. Undefined ratios are ``None`` with a denominator reason.
    FAR means FP/(TP+FP); FPR means FP/(FP+TN). HSS is the binary Heidke score.
    """
    truth, prediction, valid = _decisions(truth, prediction, valid)
    return _from_counts(
        np.count_nonzero(valid & truth & prediction),
        np.count_nonzero(valid & ~truth & prediction),
        np.count_nonzero(valid & truth & ~prediction),
        np.count_nonzero(valid & ~truth & ~prediction), len(truth))


def _integer(value, name, *, minimum):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{name} must be an integer')
    result = int(value)
    if result < minimum:
        raise ValueError(f'{name} must be at least {minimum}')
    return result


def _coordinates(value, length):
    # np.asarray([False, 1]) would erase the boolean's invalid coordinate type.
    if isinstance(value, (list, tuple)) and any(
            isinstance(part, (bool, np.bool_)) or not isinstance(part, (int, np.integer))
            for part in value):
        raise ValueError('issue_times_ns must contain integer nanosecond coordinates')
    result = np.asarray(value)
    if result.ndim != 1 or result.dtype.kind not in 'iu':
        raise ValueError('issue_times_ns must be a one-dimensional integer array')
    if len(result) != length:
        raise ValueError('issue_times_ns and decision arrays must have equal lengths')
    if len(result) and (int(result.min()) < np.iinfo(np.int64).min
                        or int(result.max()) > np.iinfo(np.int64).max):
        raise ValueError('issue_times_ns is outside the int64 nanosecond range')
    if np.any(result[1:] <= result[:-1]):
        raise ValueError('issue_times_ns must be unique and strictly chronological')
    return result.astype(np.int64, copy=False)


def block_intervals(issue_times_ns, truth, prediction, valid=None, *,
                    block_seconds=86400, replicates=1000, seed=17,
                    minimum_block_seconds=9000):
    """Return descriptive 2.5/97.5 percentiles from UTC-block resampling.

    Nonoverlapping blocks are aligned to the Unix UTC epoch. Each block with a
    supplied coordinate is retained, including blocks containing only excluded
    decisions. Absent coordinates are not invented. A replicate samples the
    same number of observed blocks with replacement, retaining all positions
    and their validity masks within each selected block.

    At least two blocks containing eligible positions are required to attempt
    intervals. Degenerate replicates are counted separately for every metric;
    percentiles use only defined values. These are descriptive intervals, with
    no asserted IID sampling or nominal frequentist coverage. The caller must
    declare a minimum block length covering its context-plus-horizon dependency
    and any other known dependence. The default bound is 9000 seconds; passing
    this bound does not establish independence of adjacent blocks.
    """
    truth, prediction, valid = _decisions(truth, prediction, valid)
    times = _coordinates(issue_times_ns, len(truth))
    block_seconds = _integer(block_seconds, 'block_seconds', minimum=1)
    minimum_block_seconds = _integer(minimum_block_seconds, 'minimum_block_seconds', minimum=1)
    if block_seconds < minimum_block_seconds:
        raise ValueError('block_seconds must cover the declared minimum_block_seconds dependence bound')
    replicates = _integer(replicates, 'replicates', minimum=1)
    seed = _integer(seed, 'seed', minimum=0)
    observed = binary_scores(truth, prediction, valid)
    block_ns = block_seconds * 1_000_000_000
    # Python arithmetic avoids overflow even for a caller's very long block.
    block_ids = np.array([int(time) // block_ns for time in times], dtype=np.int64)
    _, block_indices = np.unique(block_ids, return_inverse=True)
    n_blocks = int(block_indices.max()) + 1 if len(times) else 0
    # TP, FP, FN, TN and total positions per observed block. Retaining total
    # positions keeps all-excluded blocks in the sampling population.
    rows = np.zeros((n_blocks, 5), dtype=np.int64)
    selectors = (valid & truth & prediction, valid & ~truth & prediction,
                 valid & truth & ~prediction, valid & ~truth & ~prediction,
                 np.ones(len(times), dtype=bool))
    for column, selector in enumerate(selectors):
        np.add.at(rows[:, column], block_indices[selector], 1)
    informative = int(np.count_nonzero(rows[:, :4].sum(axis=1)))
    result = dict(
        status='undefined' if informative < 2 else 'defined',
        reason='fewer_than_two_informative_blocks' if informative < 2 else None,
        interval_kind='descriptive_utc_block_percentile', percentiles=[2.5, 97.5],
        block_alignment='unix_utc_epoch', block_seconds=block_seconds,
        minimum_block_seconds=minimum_block_seconds,
        dependence_caveat='Caller-declared bound must cover context plus horizon and other known dependence; adjacent blocks are not asserted independent.',
        coverage_caveat='Descriptive percentiles conditional on supplied records, validity, labels and decisions; no IID or nominal confidence-coverage claim.',
        requested_replicates=replicates, executed_replicates=0, seed=seed,
        blocks=dict(total=n_blocks, informative=informative), observed=observed,
        metrics={})
    samples = {name: [] for name in observed['metrics']}
    if informative >= 2:
        rng = np.random.default_rng(seed)
        for _ in range(replicates):
            selected = rng.integers(0, n_blocks, size=n_blocks)
            tp, fp, fn, tn, total = rows[selected].sum(axis=0)
            sample = _from_counts(tp, fp, fn, tn, total)
            for name, value in sample['metrics'].items():
                if value is not None:
                    samples[name].append(value)
        result['executed_replicates'] = replicates
    for name, values in samples.items():
        bounds = np.percentile(values, [2.5, 97.5]) if values else (None, None)
        result['metrics'][name] = dict(
            lower=float(bounds[0]) if values else None,
            upper=float(bounds[1]) if values else None,
            defined_replicates=len(values),
            undefined_replicates=result['executed_replicates'] - len(values),
            reason=result['reason'] if informative < 2 else
                   ('no_defined_replicates' if not values else None))
    return result
