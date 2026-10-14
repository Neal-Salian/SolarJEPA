"""Synthetic arithmetic and complete-input identity checks; no model execution."""
from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
)

LEVELS = (.05, .25, .5, .75, .95)


def example(observed=100., points=None, quantiles=None, mask=None):
    values = np.asarray(observed, float)
    if values.ndim == 0:
        values = values.reshape(1, 1, 1)
    n, h, k = values.shape
    names = tuple(f'x{i}' for i in range(k))
    spec = ForecastSpec(60, 1, h, names, names, ('W/m2',)*k, ('W/m2',)*k,
                        transform='log10', feature_reference=(1.,)*k,
                        target_reference=(1.,)*k, eligibility_policy='masked')
    issues = (np.arange(n, dtype=np.int64)+1)*3600*10**9
    starts = issues[:, None]+np.arange(h, dtype=np.int64)[None]*60*10**9
    grid = FutureGrid(starts, starts+60*10**9, issues,
                      tuple(f'o{i}' for i in range(n)), spec, 'synthetic-external')
    targets = ForecastTargets(values, np.ones_like(values, bool) if mask is None else mask, grid)
    if quantiles is None and points is None:
        quantiles = np.broadcast_to([1., 10., 100., 1000., 10000.], values.shape+(5,))
    points = np.asarray(points if points is not None else quantiles[..., 2], float)
    return targets, ForecastPrediction(points, grid, 'synthetic-model',
        LEVELS if quantiles is not None else (), quantiles)


def score(*args, **kwargs):
    from solar_flare_jepa.evaluation.external_model import score_external_prediction
    return score_external_prediction(*args, **kwargs)


def test_hand_computed_dex_and_native_pinball():
    result = score(*example())
    assert result['dex']['aggregate']['mean_pinball']['value'] == pytest.approx(.14)
    assert result['native']['aggregate']['mean_pinball']['value'] == pytest.approx(149.49)
    assert result['dex']['aggregate']['pinball_by_quantile'] == pytest.approx([.1, .25, 0., .25, .1])
    assert result['native']['aggregate']['pinball_by_quantile'] == pytest.approx([4.95, 22.5, 0., 225., 495.])
    assert result['dex']['aggregate']['quantile_reliability'] == [0., 0., 1., 1., 1.]
    assert result['per_origin'][0]['dex_mean_pinball'] == pytest.approx(.14)
    assert result['per_origin'][0]['native_mean_pinball'] == pytest.approx(149.49)
    json.dumps(result, allow_nan=False)


def test_rmse_pools_squared_error():
    native = score(*example([[[1.], [1.]]], points=[[[2.], [4.]]]))
    assert native['native']['aggregate']['mae']['value'] == 2.
    assert native['native']['aggregate']['mse']['value'] == 5.
    assert native['native']['aggregate']['rmse']['value'] == pytest.approx(np.sqrt(5))
    dex = score(*example([[[1.], [1.]]], points=[[[10.], [1000.]]]))
    assert dex['dex']['aggregate']['mse']['value'] == 5.
    assert dex['dex']['aggregate']['rmse']['value'] == pytest.approx(np.sqrt(5))
    assert dex['per_origin'][0]['dex_mse'] == 5.


def test_channel_lead_coverage_and_width():
    # Each channel/lead has different coverage; pooling must use observed counts.
    observed = np.array([[[1., 10.], [100., 10000.]], [[10., 100.], [1000., 100000.]]])
    mask = np.ones_like(observed, bool)
    mask[1, 1, 1] = False
    result = score(*example(observed, mask=mask))
    assert result['coverage']['valid_count'] == 7
    assert result['coverage']['excluded_count'] == 1
    assert result['coverage']['valid_by_target_lead'] == {'x0': [2, 2], 'x1': [2, 1]}
    central50 = result['dex']['aggregate']['intervals']['central_50']
    assert central50['coverage'] == pytest.approx(5/7)
    assert central50['width'] == 2.
    assert result['dex']['by_target']['x0']['intervals']['central_50']['coverage'] == .75
    assert result['dex']['by_lead'][1]['intervals']['central_50']['coverage'] == pytest.approx(2/3)
    assert result['dex']['by_target_lead']['x1'][1]['intervals']['central_50']['coverage'] == 0.
    assert result['native']['aggregate']['intervals']['central_90']['coverage'] == 1.
    assert result['native']['aggregate']['intervals']['central_90']['width'] == pytest.approx(9999.)


def test_interval_score_has_declared_alpha_and_space():
    target, prediction = example(4., quantiles=np.array([[[[1., 1., 2., 3., 3.]]]]))
    result = score(target, prediction)
    for label, alpha, expected in [('central_50', .5, 6.), ('central_90', .1, 22.)]:
        interval = result['native']['aggregate']['intervals'][label]
        assert interval['alpha'] == alpha
        assert interval['space'] == 'native'
        assert interval['interval_score'] == expected
        dex = result['dex']['aggregate']['intervals'][label]
        assert dex['space'] == 'dex'
        assert dex['interval_score'] == pytest.approx(np.log10(3)+(2/alpha)*np.log10(4/3))
    # Endpoints are inclusive, including observations exactly on either boundary.
    for observed in (1., 3.):
        result = score(*example(observed, quantiles=prediction.quantiles))
        assert result['dex']['aggregate']['intervals']['central_50']['coverage'] == 1.


def test_quantile_change_changes_score_identity():
    target, prediction = example()
    original = score(target, prediction)
    changed = prediction.quantiles.copy()
    changed[..., 0] = 2.
    updated = score(target, replace(prediction, quantiles=changed))
    assert original['evaluation_input_fingerprint'] != updated['evaluation_input_fingerprint']
    assert original['support_fingerprint'] == updated['support_fingerprint']
    assert original == score(target, prediction)


def test_point_only_reference_has_no_quantiles():
    target, prediction = example(points=[[[10.]]])
    reference = replace(prediction, model_id='persistence', values=np.array([[[1.]]]))
    result = score(target, prediction, persistence=reference)
    assert result['quantile_levels'] == []
    assert result['native']['aggregate']['mean_pinball'] is None
    assert result['dex']['aggregate']['intervals'] is None
    assert result['per_origin'][0]['dex_mean_pinball'] is None
    assert result['dex']['aggregate']['persistence_mae_skill']['value'] == .5
    assert result['dex']['aggregate']['persistence_mse_skill']['value'] == .75
    assert result['mase']['value'] is None


@pytest.mark.parametrize('field,bad', [('values', np.array([[[np.nan]]])),
                                     ('values', np.empty((0, 1, 1))),
                                     ('quantiles', np.array([[[[1., 10., 100., 1000., np.inf]]]])),
                                     ('quantiles', np.array([[[[1., 10., 100., 9., 10000.]]]]))])
def test_partial_or_nonfinite_prediction_fails(field, bad):
    target, prediction = example(mask=np.zeros((1, 1, 1), bool))
    altered = deepcopy(prediction)
    object.__setattr__(altered, field, bad)
    with pytest.raises(ValueError):
        score(target, altered)


@pytest.mark.parametrize('reference', [False, True])
def test_mismatched_support_rejected(reference):
    target, prediction = example()
    other = replace(prediction, grid=replace(prediction.grid, dataset_fingerprint='different'))
    with pytest.raises(ValueError, match='align'):
        score(target, prediction, persistence=other) if reference else score(target, other)


def test_nonmedian_points_and_nonprotocol_levels_fail():
    target, prediction = example()
    with pytest.raises(ValueError, match='median'):
        score(target, replace(prediction, values=prediction.values+1.))
    with pytest.raises(ValueError, match='quantile levels'):
        score(target, replace(prediction, quantile_levels=(.1, .25, .5, .75, .9)))


def test_exact_support_and_masked_payload_identity():
    target, prediction = example([[[100.], [100.]]], mask=np.array([[[True], [False]]]))
    original = score(target, prediction)
    changed = replace(target, values=np.array([[[100.], [999.]]]))
    assert score(changed, prediction)['support_fingerprint'] == original['support_fingerprint']
    assert score(changed, prediction)['evaluation_input_fingerprint'] == original['evaluation_input_fingerprint']
    assert original['origin_ids'] == ['o0']
    assert original['observation_mask'] == [[[True], [False]]]
    assert original['issue_times_ns'] == [3600*10**9]
    assert original['starts_ns'] == [[3600*10**9, 3660*10**9]]
    assert original['ends_ns'] == [[3660*10**9, 3720*10**9]]
    assert original['per_origin'][0]['valid_count'] == 1


def test_empty_masks_are_json_null_and_full_predictions_required():
    target, prediction = example(mask=np.zeros((1, 1, 1), bool))
    result = score(target, prediction)
    assert result['dex']['aggregate']['mae']['value'] is None
    assert result['dex']['aggregate']['mean_pinball']['value'] is None
    assert result['dex']['aggregate']['intervals']['central_50']['coverage'] is None
    assert result['per_origin'][0]['dex_mae'] is None
    json.dumps(result, allow_nan=False)


def test_existing_log_scores_remain_compatible():
    from solar_flare_jepa.evaluation.probabilistic import log_scores
    target, prediction = example()
    previous = log_scores(target, prediction, target.grid.spec)
    result = score(target, prediction)
    assert result['dex']['aggregate']['mean_pinball']['value'] == pytest.approx(previous['mean_pinball'])
    assert result['dex']['aggregate']['mae']['value'] == previous['log_mae']
    assert result['dex']['aggregate']['rmse']['value'] == previous['log_rmse']


def test_score_content_mutation_rejected_before_pairing():
    from solar_flare_jepa.evaluation.external_model import validate_external_score
    result = score(*example())
    detached = validate_external_score(result)
    assert detached == result
    detached['per_origin'][0]['dex_mae'] = 99.
    assert result['per_origin'][0]['dex_mae'] == 0.
    with pytest.raises(ValueError, match='content fingerprint'):
        validate_external_score(detached)
    for field in ('observation_mask', 'issue_times_ns'):
        changed = deepcopy(result)
        changed[field] = []
        with pytest.raises(ValueError, match='content fingerprint'):
            validate_external_score(changed)


def test_channel_lead_point_and_quantile_losses_use_observation_counts():
    observed = np.array([[[1., 10.], [100., 10000.]], [[10., 100.], [1000., 100000.]]])
    mask = np.ones_like(observed, bool)
    mask[1, 1, 1] = False
    result = score(*example(observed, mask=mask))
    # Dex absolute errors: [[2,1],[0,2]], [[1,0],[1,masked]].
    assert result['dex']['aggregate']['mae']['value'] == 1.
    assert result['dex']['aggregate']['mse']['value'] == pytest.approx(11/7)
    assert result['dex']['by_target']['x0']['rmse']['value'] == pytest.approx(np.sqrt(1.5))
    assert result['dex']['by_lead'][1]['mse']['value'] == pytest.approx(5/3)
    assert result['dex']['by_target_lead']['x1'][1]['rmse']['value'] == 2.
    assert result['dex']['by_target_lead']['x1'][1]['mean_pinball']['value'] == pytest.approx(.54)
    assert result['dex']['by_target_lead']['x1'][1]['pinball_by_quantile'] == pytest.approx([.2, .75, 1., .75, 0.])
    assert result['dex']['by_target_lead']['x1'][1]['quantile_reliability'] == [0., 0., 0., 0., 1.]
    assert result['per_origin'][0]['dex_mae'] == 1.25
    assert result['per_origin'][1]['dex_mae'] == pytest.approx(2/3)


@pytest.mark.parametrize('field', ['values', 'quantiles'])
def test_positive_full_grid_required_even_if_observation_excluded(field):
    target, prediction = example(mask=np.zeros((1, 1, 1), bool))
    changes = np.zeros_like(getattr(prediction, field))
    if field == 'quantiles':
        changes = prediction.quantiles.copy()
        changes[..., 0] = 0.
    with pytest.raises(ValueError, match='positive'):
        score(target, replace(prediction, **{field: changes}))


def test_target_grid_subclass_hooks_do_not_spoof_alignment_or_hashes():
    class PretendEqual(str):
        def __eq__(self, other):
            return True

    target, prediction = example()
    altered = deepcopy(prediction)
    object.__setattr__(altered.grid, 'dataset_fingerprint', PretendEqual('different'))
    with pytest.raises(ValueError, match='align'):
        score(target, altered)


def test_score_validator_ignores_container_hooks():
    from solar_flare_jepa.evaluation.external_model import validate_external_score

    class DictHook(dict):
        def items(self):
            raise AssertionError('caller hook invoked')

    result = score(*example())
    assert validate_external_score(DictHook(result)) == result


def test_original_external_native_scores_remain_compatible():
    from solar_flare_jepa.evaluation.external_flux import evaluate_external_flux
    target, prediction = example([[[1.], [1.]]], points=[[[2.], [4.]]])
    previous = evaluate_external_flux(target, prediction)
    current = score(target, prediction)
    for name in ('mae', 'rmse', 'persistence_mae_skill', 'persistence_mse_skill'):
        assert current['native']['aggregate'][name] == previous['aggregate'][name]


def test_complete_coverage_counts_and_squared_loss_units():
    target, prediction = example([[[100.], [100.]]], mask=np.array([[[True], [False]]]))
    result = score(target, prediction)
    assert result['coverage']['by_target']['x0'] == dict(valid_count=1, total_count=2,
        prediction_count=2, excluded_count=1)
    assert result['coverage']['by_lead'][1] == dict(lead_step=2, valid_count=0,
        total_count=1, prediction_count=1, excluded_count=1)
    assert result['coverage']['by_target_lead']['x0'][0] == dict(lead_step=1, valid_count=1,
        total_count=1, prediction_count=1, excluded_count=0)
    assert result['native']['units']['mse'] == '(W/m2)^2'
    assert result['dex']['units']['mse'] == 'dex^2'
    assert result['native']['units']['coverage'] == 'dimensionless'


def test_finite_extreme_loss_fails_without_origin_dropping():
    target, prediction = example(points=[[[1e308]]])
    with pytest.raises(ValueError, match='Nonfinite'):
        score(target, prediction)


def test_mutated_target_masks_are_revalidated():
    target, prediction = example()
    target = deepcopy(target)
    object.__setattr__(target, 'mask', np.ones((1, 2, 1), bool))
    with pytest.raises(ValueError):
        score(target, prediction)


def test_score_validator_uses_actual_base_payload_despite_spoofed_containers():
    from solar_flare_jepa.evaluation.external_model import validate_external_score
    result = score(*example())

    class DictSpoof(dict):
        def items(self):
            return result.items()

        def __getitem__(self, key):
            return result[key]

        def get(self, key, default=None):
            return result.get(key, default)

    altered = deepcopy(result)
    altered['per_origin'][0]['dex_mae'] = 99.
    with pytest.raises(ValueError, match='content fingerprint'):
        validate_external_score(DictSpoof(altered))

    class ListSpoof(list):
        def __iter__(self):
            return iter(result['per_origin'])

        def __getitem__(self, index):
            return result['per_origin'][index]

    altered = deepcopy(result)
    altered['per_origin'][0]['dex_mae'] = 99.
    altered['per_origin'] = ListSpoof(altered['per_origin'])
    with pytest.raises(ValueError, match='content fingerprint'):
        validate_external_score(altered)

    class StringSpoof(str):
        def __eq__(self, other):
            return True

        def __str__(self):
            return result['score_content_fingerprint']

    altered = deepcopy(result)
    altered['score_content_fingerprint'] = StringSpoof('incorrect')
    with pytest.raises(ValueError, match='content fingerprint'):
        validate_external_score(altered)
