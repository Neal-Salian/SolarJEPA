"""Literal proper-score examples and strict log/mask boundaries."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.evaluation.diagnostics import calibration_diagnostics
from solar_flare_jepa.forecasting.contracts import ForecastPrediction, ForecastTargets
from test_forecasting_contract import context_and_grid, spec


def example(mask=None):
    _, grid = context_and_grid(spec(availability_mode='retrospective_bin_end',
                                    target_reference=(1.,), feature_reference=(1.,)))
    targets = ForecastTargets(np.array([[[1.], [5.]]]),
                              np.ones((1, 2, 1), bool) if mask is None else mask, grid)
    quantiles = np.array([[[[0., 2., 4.]], [[0., 2., 4.]]]])
    prediction = ForecastPrediction(np.full((1, 2, 1), 2.), grid, 'synthetic',
                                    quantiles=quantiles, quantile_levels=(.25, .5, .75))
    return targets, prediction


def test_literal_quantile_reliability_interval_score_and_counts():
    target, prediction = example()
    result = calibration_diagnostics(target, prediction, space='native', intervals=((.25, .75),))
    assert result['counts'] == [[1], [1]]
    np.testing.assert_allclose(result['quantile_reliability'], [[[0., 1., 1.]], [[0., 0., 0.]]])
    # Second origin: (0.25*5 + 0.5*3 + 0.75*1)/3 = 7/6.
    np.testing.assert_allclose(result['mean_pinball'], [[.5], [7/6]])
    interval = result['intervals'][0]
    assert interval['nominal_coverage'] == .5
    assert interval['coverage'] == [[1.], [0.]]
    assert interval['width'] == [[4.], [4.]]
    assert interval['interval_score'] == [[4.], [8.]]
    assert result['aggregate_mean_pinball'] == pytest.approx(5/6)
    assert interval['aggregate_coverage'] == .5
    assert interval['aggregate_interval_score'] == 6.
    json.dumps(result, allow_nan=False)


def test_masked_invalid_log_values_are_inert_and_empty_support_is_null():
    target, prediction = example(np.zeros((1, 2, 1), bool))
    target = replace(target, values=np.zeros((1, 2, 1)))
    result = calibration_diagnostics(target, prediction, space='log10', intervals=((.25, .75),))
    assert result['mean_pinball'] == [[None], [None]]
    assert result['aggregate_mean_pinball'] is None
    assert result['intervals'][0]['aggregate_coverage'] is None
    json.dumps(result, allow_nan=False)


def test_log_metrics_use_dimensioned_native_targets_and_match_existing_scoring():
    from solar_flare_jepa.evaluation.probabilistic import log_scores
    target, prediction = example()
    target = replace(target, values=10. ** target.values)
    prediction = replace(prediction, values=10. ** prediction.values,
                         quantiles=10. ** prediction.quantiles)
    result = calibration_diagnostics(target, prediction, space='log10', intervals=((.25, .75),))
    assert result['aggregate_mean_pinball'] == pytest.approx(5/6)
    assert result['aggregate_mean_pinball'] == log_scores(target, prediction, target.grid.spec)['mean_pinball']
    assert result['intervals'][0]['aggregate_interval_score'] == 6.


@pytest.mark.parametrize('part', ['observation', 'point', 'quantile'])
def test_nonpositive_scored_log_domain_is_rejected(part):
    target, prediction = example()
    prediction = replace(prediction, quantiles=prediction.quantiles + 1.)
    if part == 'observation':
        target = replace(target, values=np.zeros((1, 2, 1)))
    elif part == 'point':
        prediction = replace(prediction, values=np.zeros((1, 2, 1)))
    else:
        prediction = replace(prediction, quantiles=prediction.quantiles - 1.)
    with pytest.raises(ValueError, match='positive|log'):
        calibration_diagnostics(target, prediction, space='log10')


def test_alignment_and_canonical_snapshots_reject_forged_forecasts():
    target, prediction = example()
    with pytest.raises(ValueError, match='align'):
        calibration_diagnostics(target, replace(prediction, grid=replace(prediction.grid,
                                 dataset_fingerprint='different')), space='native')
    object.__setattr__(prediction, 'quantiles', prediction.quantiles[..., ::-1])
    with pytest.raises(ValueError, match='cross'):
        calibration_diagnostics(target, prediction, space='native')


def test_point_only_and_missing_requested_quantiles_do_not_fabricate_intervals():
    target, prediction = example()
    point = replace(prediction, quantiles=None, quantile_levels=())
    with pytest.raises(ValueError, match='quantile'):
        calibration_diagnostics(target, point, space='native')
    with pytest.raises(ValueError, match='quantile'):
        calibration_diagnostics(target, prediction, space='native', intervals=((.05, .95),))


@pytest.mark.parametrize('changes', [dict(space='standardized'),
    dict(intervals=((.25, .5),)), dict(intervals=((.75, .25),)),
    dict(intervals=((.25, .75), (.25, .75)))])
def test_invalid_diagnostic_definition_fails(changes):
    target, prediction = example()
    with pytest.raises(ValueError):
        calibration_diagnostics(target, prediction, **(dict(space='native') | changes))


def test_log_diagnostics_require_explicit_dimensioned_references():
    target, prediction = example()
    prediction = replace(prediction, quantiles=prediction.quantiles + 1.)
    grid = replace(target.grid, spec=replace(target.grid.spec, target_reference=()))
    target, prediction = replace(target, grid=grid), replace(prediction, grid=grid)
    with pytest.raises(ValueError, match='reference'):
        calibration_diagnostics(target, prediction, space='log10')
