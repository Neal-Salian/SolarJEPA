"""Known normal/uniform probability diagnostics, with independent score arithmetic."""
from dataclasses import replace
from statistics import NormalDist
import math

import numpy as np

from ...forecasting.contracts import ForecastSpec, FutureGrid, ForecastTargets, ForecastPrediction
from ..diagnostics import calibration_diagnostics
from .synthetic import stream_seed

LEVELS = (.05, .25, .5, .75, .95)


def _objects(values, quantiles):
    n, horizon, channels = values.shape
    spec = ForecastSpec(1, 1, horizon, ('artificial',), ('artificial',), ('unit',), ('unit',),
                        availability_mode='retrospective_bin_end')
    issues = np.arange(n, dtype=np.int64)*3_000_000_000
    starts = issues[:, None]+np.arange(horizon, dtype=np.int64)*1_000_000_000
    grid = FutureGrid(starts, starts+1_000_000_000, issues, tuple(f'o{i}' for i in range(n)), spec, 'synthetic-only')
    targets = ForecastTargets(values, np.ones_like(values, bool), grid)
    prediction = ForecastPrediction(quantiles[..., 2], grid, 'synthetic-quantiles', LEVELS, quantiles)
    return targets, prediction


def _independent_error(values, quantiles, actual):
    # Literal loops: do not use production reduction/score helpers.
    maximum, scaled = 0., 0.
    def check(expected, observed):
        nonlocal maximum, scaled
        error = abs(expected-observed)
        maximum = max(maximum, error)
        scaled = max(scaled, error/max(1., abs(expected)))
    for lead in range(values.shape[1]):
        y = values[:, lead, 0]
        for j, q in enumerate(LEVELS):
            predicted = quantiles[:, lead, 0, j]
            coverage = math.fsum(float(v <= p) for v, p in zip(y, predicted))/len(y)
            pinball = math.fsum(q*(v-p) if v >= p else (1-q)*(p-v) for v, p in zip(y, predicted))/len(y)
            check(coverage, actual['quantile_reliability'][lead][0][j])
            check(pinball, actual['pinball_by_quantile'][lead][0][j])
        for interval in actual['intervals']:
            low = quantiles[:, lead, 0, LEVELS.index(interval['low'])]
            high = quantiles[:, lead, 0, LEVELS.index(interval['high'])]
            alpha = 2*interval['low']
            width = math.fsum(float(h-l) for l, h in zip(low, high))/len(y)
            covered = math.fsum(float(l <= v <= h) for v, l, h in zip(y, low, high))/len(y)
            score = math.fsum(float(h-l)+(2/alpha)*(l-v if v < l else v-h if v > h else 0.)
                        for v, l, h in zip(y, low, high))/len(y)
            check(width, interval['width'][lead][0])
            check(covered, interval['coverage'][lead][0])
            check(score, interval['interval_score'][lead][0])
    return dict(max_absolute_error=maximum, max_scaled_error=scaled)


def calibration_study(*, origins, rng_seed):
    if type(origins) is not int or not 1 <= origins <= 100000:
        raise ValueError('Calibration origins must be 1..100000')
    rng = np.random.default_rng(stream_seed('calibration', rng_seed))
    normal = NormalDist()
    z = np.array([normal.inv_cdf(q) for q in LEVELS])
    # Independent marginal observations; no trajectory-calibration interpretation.
    values = rng.normal(size=(origins, 2, 1))*np.array([1., 2.])[None, :, None]
    variants = [('calibrated', 1., 0.), ('underdispersed', .5, 0.),
                ('overdispersed', 2., 0.), ('biased', 1., .75), ('tail_only', 1., 0.),
                ('horizon_failure', 1., 0.)]
    rows = []
    for name, scale, bias in variants:
        standardized = scale*z+bias
        if name == 'tail_only':
            standardized[[0, -1]] = .5*z[[0, -1]]
        lead_q = np.stack([standardized, standardized*2])[:, None, :]
        if name == 'horizon_failure':
            lead_q[1, 0] = (.5*z+.75)*2
        q = np.broadcast_to(lead_q, values.shape+(len(LEVELS),))
        targets, prediction = _objects(values, q)
        actual = calibration_diagnostics(targets, prediction, space='native')
        analytic = [[[normal.cdf(float(x/s)) for x in lead_q[h, 0]]]
                    for h, s in enumerate((1., 2.))]
        actual.pop('per_origin_mean_pinball')
        rows.append(dict(name=name, origins=origins, analytic_quantile_reliability=analytic,
                         diagnostics=actual, arithmetic=_independent_error(values, q, actual)))
    # Pre-issue synthetic regime: unconditional U uniform, conditional supports differ.
    rare = rng.random(origins) < .1
    u = rng.random((origins, 2, 1))
    u = np.where(rare[:, None, None], .9+.1*u, .9*u)
    q = np.broadcast_to(1+np.array(LEVELS), u.shape+(len(LEVELS),))
    targets, prediction = _objects(1+u, q)
    overall = calibration_diagnostics(targets, prediction, space='native')
    overall.pop('per_origin_mean_pinball')
    strata = {}
    for name, selected in (('rare', rare), ('common', ~rare)):
        strata[name] = calibration_diagnostics(replace(targets, mask=np.broadcast_to(selected[:, None, None], u.shape)),
                                               prediction, space='native')
        strata[name].pop('per_origin_mean_pinball')
    crossing = q.copy()
    crossing[..., 1] = crossing[..., 3]+1
    try:
        replace(prediction, quantiles=crossing)
    except ValueError:
        rejected = True
    else:
        rejected = False
    return dict(normal=rows, rare_uniform_regime=dict(overall=overall, **strata,
                rare_origins=int(rare.sum()), common_origins=int((~rare).sum()),
                analytic_overall90=.9, analytic_rare90=.5, analytic_common90=.85/.9),
                crossing_rejected=rejected)
