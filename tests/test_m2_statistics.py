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


def test_coverage_and_null_exclusion_use_the_same_roundoff_convention():
    cfg = Scenario('cancelled', seeds=3, days=(3, 9), delta=(-.4, .4),
                   sigma_seed=0., sigma_time=0., sigma_cell=0.)
    out = run_case(cfg, block_days=1, replications=5, bootstrap_replicates=19, confidence=.95, master_seed=3)
    assert out['coverage']['rate'] == 1.
    assert out['ci_exclusion']['rate'] == 0.
    assert out['null_exclusion_numerical_tolerance'] == 1e-12


def test_infinite_variance_case_does_not_claim_mean_or_width_standard_errors():
    cfg = Scenario('infinite-variance', seeds=3, days=(4,), distribution='t1.5')
    out = run_case(cfg, block_days=1, replications=3, bootstrap_replicates=19, confidence=.95, master_seed=3)
    assert out['bias_mcse'] is None
    assert out['width_mcse'] is None
    assert not out['finite_estimator_variance']
    assert out['coverage']['mcse'] is not None


def test_dense_calendar_allocation_budget_is_checked_before_allocating(monkeypatch):
    cfg = Scenario('bounded', seeds=10, days=(2,))
    a, b, _ = generate_panels(cfg, 2)
    updates = dict(calendar_start_ns=-100000*86400000000000, calendar_end_ns=100000*86400000000000)
    a['f0'], b['f0'] = replace(a['f0'], **updates), replace(b['f0'], **updates)
    original = np.zeros
    def guarded(shape, *args, **kwargs):
        if isinstance(shape, tuple) and math.prod(shape) > 1_000_000:
            raise AssertionError('Attempted dangerous dense calendar allocation')
        return original(shape, *args, **kwargs)
    monkeypatch.setattr(np, 'zeros', guarded)
    with pytest.raises(ValueError, match='calendar.*budget|Calendar.*budget'):
        paired_comparison(a, b, block_days=1, replicates=2, rng_seed=1, confidence=.95)


def test_calendar_memory_budget_is_explicit_and_configurable():
    a, b, _ = generate_panels(Scenario('budget', seeds=3, days=(4,)), 3)
    args = dict(block_days=1, replicates=2, rng_seed=1, confidence=.95)
    with pytest.raises(ValueError):
        paired_comparison(a, b, max_calendar_cells=11, **args)
    with pytest.raises(ValueError):
        paired_comparison(a, b, max_calendar_cells=True, **args)
    assert paired_comparison(a, b, max_calendar_cells=12, **args)['mean_difference'] is not None


def test_synthetic_generator_rejects_effect_lost_in_loss_representation():
    cfg = Scenario('too-small', seeds=3, days=(4,), delta=(1e-20,), sigma_seed=0., sigma_time=0., sigma_cell=0.)
    with pytest.raises(ValueError, match='resolution|represent'):
        generate_panels(cfg, 2)


def test_reference_calendar_arithmetic_does_not_wrap_int64():
    from solar_flare_jepa.evaluation.comparison import LossPanel, DAY_NS
    times = np.array([-50000*DAY_NS, 0, 50000*DAY_NS, 99999*DAY_NS], np.int64)
    a = LossPanel((0, 1), ('a', 'b', 'c', 'd'), times, np.array([[0., 1., 2., 3.]]*2),
                  'support', 'artificial', 'unit', -100000*DAY_NS, 100000*DAY_NS)
    b = replace(a, losses=np.zeros((2, 4)))
    out = reference_bootstrap({'f': a}, {'f': b}, block_days=200000, replicates=2, rng_seed=1, confidence=.95)
    assert out['interval'] == [1.5, 1.5]


def test_seed_dispersion_does_not_underflow_for_representable_tiny_effects():
    a, b, _ = generate_panels(Scenario('tiny-scale', seeds=2, days=(4,)), 1)
    b['f0'] = replace(b['f0'], losses=np.zeros((2, 4)))
    a['f0'] = replace(a['f0'], losses=np.array([[1e-300]*4, [2e-300]*4]))
    out = paired_comparison(a, b, block_days=1, replicates=9, rng_seed=1, confidence=.95)
    assert out['seed_difference_sd']/1e-300 == pytest.approx(2**-.5)
