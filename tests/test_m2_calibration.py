"""Known probability calibration and independent arithmetic."""
import numpy as np
import pytest

from solar_flare_jepa.evaluation.stress.calibration import calibration_study


def test_known_normal_calibration_recovers_probability_and_scores():
    results = calibration_study(origins=20000, rng_seed=23)
    for row in results['normal']:
        n = row['origins']
        expected = np.array(row['analytic_quantile_reliability'])
        actual = np.array(row['diagnostics']['quantile_reliability'])
        tolerance = 5*np.sqrt(expected*(1-expected)/n)+1e-12
        assert np.all(np.abs(actual-expected) <= tolerance)
        assert row['arithmetic']['max_scaled_error'] < 1e-12
    calibrated = results['normal'][0]
    assert calibrated['name'] == 'calibrated'
    assert calibrated['diagnostics']['intervals'][0]['aggregate_coverage'] == pytest.approx(.9, abs=.01)
    rare = results['rare_uniform_regime']
    assert rare['overall']['intervals'][0]['aggregate_coverage'] == pytest.approx(.9, abs=.01)
    assert rare['rare']['intervals'][0]['aggregate_coverage'] == pytest.approx(.5, abs=.05)
    assert rare['common']['intervals'][0]['aggregate_coverage'] == pytest.approx(.85/.9, abs=.01)
    assert results['crossing_rejected']


def test_calibration_study_reproducible_and_single_origin_supported():
    assert calibration_study(origins=100, rng_seed=4) == calibration_study(origins=100, rng_seed=4)
    out = calibration_study(origins=1, rng_seed=5)
    assert out['normal'][0]['diagnostics']['counts'] == [[1], [1]]


@pytest.mark.parametrize('n', [0, True, 1000001])
def test_calibration_budget_is_bounded(n):
    with pytest.raises(ValueError):
        calibration_study(origins=n, rng_seed=1)
