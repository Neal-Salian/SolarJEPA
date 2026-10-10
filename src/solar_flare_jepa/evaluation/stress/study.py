"""Bounded Monte Carlo operating characteristics for the unchanged M1 method."""
from statistics import NormalDist
import math

import numpy as np

from ..comparison import paired_comparison
from .reference import rate_summary, reference_bootstrap
from .synthetic import generate_panels, oracle_variance, stream_seed


def _covered(lo, value, hi):
    # Stored loss subtraction and analytic latent truth can differ by roundoff,
    # especially for mathematically degenerate conditional intervals.
    tolerance = 1e-12*max(1., abs(value))
    return lo-tolerance <= value <= hi+tolerance


def run_case(cfg, *, block_days, replications, bootstrap_replicates, confidence, master_seed,
             attribution=False):
    if type(replications) is not int or not 2 <= replications <= 1000:
        raise ValueError('Replication count must be 2..1000')
    if type(bootstrap_replicates) is not int or not 2 <= bootstrap_replicates <= 5000:
        raise ValueError('Bootstrap count must be 2..5000')
    counts = dict(coverage=0, available_intervals=0, negative_exclusion=0, positive_exclusion=0,
                  negative_estimate=0, oracle_coverage=0)
    estimates, widths = [], []
    attributable = {mode: dict(covered=0, available=0, widths=[]) for mode in ('seed_only', 'time_only')}
    variance = oracle_variance(cfg)
    truth = float(np.mean(cfg.effects))
    for r in range(replications):
        data_seed = stream_seed(f'{cfg.name}:replication:{r}', master_seed)
        boot_seed = stream_seed(f'{cfg.name}:bootstrap:{r}', master_seed)
        a, b, targets = generate_panels(cfg, data_seed)
        args = dict(block_days=block_days, replicates=bootstrap_replicates, rng_seed=boot_seed, confidence=confidence)
        result = paired_comparison(a, b, **args)
        estimate, interval = result['mean_difference'], result['difference_interval']
        estimates.append(estimate)
        counts['negative_estimate'] += int(estimate < 0)
        if interval is not None:
            counts['available_intervals'] += 1
            counts['coverage'] += int(_covered(interval[0], truth, interval[1]))
            counts['negative_exclusion'] += int(interval[1] < 0)
            counts['positive_exclusion'] += int(interval[0] > 0)
            widths.append(interval[1]-interval[0])
        if variance is not None:
            half = NormalDist().inv_cdf((1+confidence)/2)*math.sqrt(variance)
            counts['oracle_coverage'] += int(_covered(estimate-half, truth, estimate+half))
        if attribution:
            for mode, item in attributable.items():
                out = reference_bootstrap(a, b, **args, mode=mode)
                if out['interval'] is not None:
                    lo, hi = out['interval']
                    item['available'] += 1
                    item['covered'] += int(_covered(lo, targets[mode], hi))
                    item['widths'].append(hi-lo)
    available = counts['available_intervals']
    estimates = np.asarray(estimates)
    out = dict(scenario=cfg.as_dict(), block_days=block_days, replications=replications,
               bootstrap_replicates=bootstrap_replicates, confidence=confidence, master_seed=master_seed,
               truth=truth, coverage_numerical_tolerance=1e-12, estimate_mean=float(estimates.mean()), bias=float(estimates.mean()-truth),
               bias_mcse=float(estimates.std(ddof=1)/math.sqrt(replications)),
               rmse=float(np.sqrt(np.mean((estimates-truth)**2))), estimator_sd=float(estimates.std(ddof=1)),
               oracle_sd=None if variance is None else math.sqrt(variance),
               mean_ci_width=None if not widths else float(np.mean(widths)),
               width_mcse=None if len(widths) < 2 else float(np.std(widths, ddof=1)/math.sqrt(len(widths))),
               **{key: rate_summary(value, replications) for key, value in counts.items()},
               conditional_coverage=rate_summary(counts['coverage'], available),
               ci_exclusion=rate_summary(counts['negative_exclusion']+counts['positive_exclusion'], replications))
    if variance is None:
        out['oracle_coverage'] = rate_summary(0, 0)
    out['attribution'] = {mode: dict(coverage=rate_summary(item['covered'], replications),
                                   available=rate_summary(item['available'], replications),
                                   conditional_coverage=rate_summary(item['covered'], item['available']),
                                   mean_ci_width=float(np.mean(item['widths'])) if item['widths'] else None)
                          for mode, item in attributable.items()} if attribution else {}
    return out
