"""Independent references and synthetic truth; no scientific observations."""
from dataclasses import replace
import math

import numpy as np
import pytest

from solar_flare_jepa.evaluation.comparison import paired_comparison
from solar_flare_jepa.evaluation.stress.synthetic import Scenario, generate_panels, oracle_variance
from solar_flare_jepa.evaluation.stress.reference import reference_bootstrap, rate_summary
from solar_flare_jepa.evaluation.stress.study import run_case


def test_paired_effect_survives_large_shared_loss_offset():
    scenario = Scenario('large', seeds=2, days=(4,), sigma_seed=0., sigma_time=0., sigma_cell=0.)
    a, b, _ = generate_panels(scenario, 4)
    b['f0'] = replace(b['f0'], losses=np.full((2, 4), 1e16))
    a['f0'] = replace(a['f0'], losses=b['f0'].losses + np.array([[2., 0., 2., 0.]] * 2))
    result = paired_comparison(a, b, block_days=4, replicates=9, rng_seed=7, confidence=.95)
    assert result['mean_difference'] == 1.
    assert result['per_seed_difference'] == [1., 1.]
    assert result['folds']['f0']['mean_difference'] == 1.
    assert result['difference_interval'] == [1., 1.]
    assert result['relative_reduction'] == -1e-16
    assert result['relative_interval'] == [-1e-16, -1e-16]


@pytest.mark.parametrize('days,counts,block', [((7,), (1,), 1), ((7, 5), (1, 3, 0), 3), ((4, 4), (1,), 4)])
def test_direct_origin_bootstrap_matches_m1_with_shared_draws(days, counts, block):
    cfg = Scenario('reference', seeds=3, days=days, delta=tuple(.1 for _ in days), counts=counts)
    a, b, _ = generate_panels(cfg, 123)
    actual = paired_comparison(a, b, block_days=block, replicates=101, rng_seed=8, confidence=.95)
    ref = reference_bootstrap(a, b, block_days=block, replicates=101, rng_seed=8, confidence=.95)
    np.testing.assert_allclose(actual['difference_interval'], ref['interval'], rtol=1e-12, atol=1e-12)
    assert actual['mean_difference'] == pytest.approx(ref['estimate'], abs=1e-12)


def test_missing_days_invalidate_both_independent_and_m1_intervals():
    cfg = Scenario('sparse', days=(5,), counts=(1, 0, 0, 0, 0))
    a, b, _ = generate_panels(cfg, 8)
    args = dict(block_days=1, replicates=99, rng_seed=3, confidence=.95)
    actual, ref = paired_comparison(a, b, **args), reference_bootstrap(a, b, **args)
    assert actual['difference_interval'] is ref['interval'] is None
    assert actual['empty_replicates'] == ref['empty_replicates'] > 0


def test_additive_gaussian_oracle_variance_and_correlated_seeds():
    cfg = Scenario('oracle', seeds=4, days=(10, 20), delta=(0., 0.),
                   sigma_seed=2., sigma_time=3., sigma_cell=4.)
    # shared seed effect, independent fold paths and cell noise
    expected = 4/4 + 9/4*(1/10+1/20) + 16/(4*4)*(1/10+1/20)
    assert oracle_variance(cfg) == pytest.approx(expected)
    assert oracle_variance(replace(cfg, seed_correlation=.5)) == pytest.approx(expected + 1.5)
    rho_cfg = Scenario('rho', seeds=4, days=(3,), sigma_seed=0., sigma_time=1., sigma_cell=0., rho=.5)
    assert oracle_variance(rho_cfg) == pytest.approx((3 + 2*(2*.5 + .25))/9)


def test_synthetic_determinism_truth_equal_fold_weight_and_global_rng_isolation():
    cfg = Scenario('truth', seeds=3, days=(3, 9), delta=(-1., 1.),
                   sigma_seed=0., sigma_time=0., sigma_cell=0.)
    np.random.seed(8)
    before = np.random.get_state()
    a, b, truth = generate_panels(cfg, 7)
    a2, _, truth2 = generate_panels(cfg, 7)
    after = np.random.get_state()
    assert np.array_equal(before[1], after[1]) and before[2:] == after[2:]
    assert truth == truth2 and truth['joint'] == 0.
    for name in a:
        assert np.array_equal(a[name].losses, a2[name].losses)
        assert (a[name].losses >= 0).all() and (b[name].losses >= 0).all()
    result = paired_comparison(a, b, block_days=1, replicates=9, rng_seed=1, confidence=.95)
    assert result['mean_difference'] == 0.
    assert result['folds']['f0']['mean_difference'] == -1.
    assert result['folds']['f1']['mean_difference'] == 1.


def test_conditional_targets_and_resampling_distinguish_uncertainty():
    cfg = Scenario('conditional', seeds=4, days=(9,), sigma_cell=0.)
    a, b, truth = generate_panels(cfg, 1)
    for mode in ('joint', 'seed_only', 'time_only'):
        out = reference_bootstrap(a, b, block_days=1, replicates=31, rng_seed=2, confidence=.95, mode=mode)
        assert math.isfinite(truth[mode]) and out['interval'] is not None
    assert truth['joint'] == 0.
    assert truth['seed_only'] != truth['time_only']


def test_rate_summary_zero_success_has_nonzero_monte_carlo_interval():
    out = rate_summary(0, 20)
    assert out['rate'] == out['mcse'] == 0.
    assert out['wilson95'][1] > 0.
    assert rate_summary(0, 0)['rate'] is None
    with pytest.raises(ValueError):
        rate_summary(2, 1)


def test_small_study_repeats_exactly_and_reports_all_denominators():
    cfg = Scenario('small', seeds=3, days=(6,))
    args = dict(block_days=1, replications=4, bootstrap_replicates=19, confidence=.95, master_seed=3)
    a, b = run_case(cfg, **args), run_case(cfg, **args)
    assert a == b
    assert a['coverage']['denominator'] == 4
    assert a['available_intervals']['denominator'] == 4
    assert a['conditional_coverage']['denominator'] <= 4
    assert a['oracle_coverage']['denominator'] == 4
    assert a['negative_estimate']['denominator'] == 4


@pytest.mark.parametrize('changes', [dict(seeds=True), dict(days=(0,)), dict(rho=1.),
    dict(delta=(0., 1.)), dict(counts=(0,)), dict(sigma_seed=-1.), dict(distribution='cauchy')])
def test_scenarios_reject_undefined_or_unbounded_inputs(changes):
    with pytest.raises(ValueError):
        Scenario('invalid', **changes)
