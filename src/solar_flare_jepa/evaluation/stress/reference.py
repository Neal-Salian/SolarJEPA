"""Independent direct-origin resampling and Monte Carlo binomial uncertainty."""
from statistics import NormalDist
import math

import numpy as np

from ..comparison import DAY_NS


def rate_summary(successes, total):
    if type(successes) is not int or type(total) is not int or not 0 <= successes <= total:
        raise ValueError('Integer binomial counts required')
    if not total:
        return dict(numerator=successes, denominator=total, rate=None, mcse=None, wilson95=None)
    p = successes/total
    z = NormalDist().inv_cdf(.975)
    denominator = 1+z*z/total
    center = (p+z*z/(2*total))/denominator
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return dict(numerator=successes, denominator=total, rate=p, mcse=math.sqrt(p*(1-p)/total),
                wilson95=[max(0., center-half), min(1., center+half)])


def reference_bootstrap(a, b, *, block_days, replicates, rng_seed, confidence, mode='joint'):
    """Resample actual origin indices, independently of M1 daily sum code.

    Reference inputs must be paired valid LossPanels. Equal folds and common
    seed draws are deliberate. Empty required draws invalidate the whole CI.
    Seed-only fixes observed days; time-only fixes the supplied seeds.
    """
    if mode not in ('joint', 'seed_only', 'time_only'):
        raise ValueError('Unknown resampling mode')
    if not a or set(a) != set(b) or type(block_days) is not int or block_days < 1:
        raise ValueError('Paired folds and positive block length required')
    if type(replicates) is not int or replicates < 2 or not 0 < confidence < 1:
        raise ValueError('Invalid reference resampling settings')
    names = sorted(a)
    seeds = a[names[0]].seed_ids
    inputs = []
    for name in names:
        left, right = a[name], b[name]
        if (left.seed_ids != seeds or right.seed_ids != seeds or left.origin_ids != right.origin_ids
                or not np.array_equal(left.issue_times_ns, right.issue_times_ns)
                or any(getattr(left, k) != getattr(right, k) for k in ('metric', 'unit', 'support_fingerprint',
                     'calendar_start_ns', 'calendar_end_ns'))):
            raise ValueError('Reference panels must be paired')
        days = (left.calendar_end_ns-left.calendar_start_ns)//DAY_NS
        if block_days > days:
            raise ValueError('Block too long')
        day = np.array([(int(t)-left.calendar_start_ns)//DAY_NS for t in left.issue_times_ns], np.int64)
        inputs.append((left.losses-right.losses, [np.flatnonzero(day == t) for t in range(days)]))
    estimate = float(np.mean([d.mean() for d, _ in inputs]))
    rng = np.random.default_rng(rng_seed)
    draws, empty = [], 0
    for _ in range(replicates):
        selected_seeds = rng.integers(0, len(seeds), len(seeds)) if mode != 'time_only' else np.arange(len(seeds))
        values = []
        for difference, origins in inputs:
            days = len(origins)
            if mode == 'seed_only':
                selected_origins = np.arange(difference.shape[1])
            else:
                starts = rng.integers(0, days, math.ceil(days/block_days))
                selected_days = [(int(start)+offset)%days for start in starts for offset in range(block_days)][:days]
                selected_origins = np.concatenate([origins[t] for t in selected_days])
            if not len(selected_origins):
                values.append(None)
            else:
                values.append(float(difference[np.ix_(selected_seeds, selected_origins)].mean()))
        if any(x is None for x in values):
            empty += 1
        else:
            draws.append(float(np.mean(values)))
    interval = None if empty else np.quantile(draws, [(1-confidence)/2, (1+confidence)/2]).tolist()
    return dict(estimate=estimate, interval=interval, empty_replicates=empty, draws=draws)
