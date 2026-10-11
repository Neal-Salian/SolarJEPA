"""Synthetic records exercise the descriptive boundary without training or inference."""
from dataclasses import replace
import importlib
import json
import math

import numpy as np
import pytest

from solar_flare_jepa.evaluation.comparison import DAY_NS
from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord
from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
)

NS = 1_000_000_000


def api():
    try:
        return importlib.import_module('solar_flare_jepa.experiments.v2_descriptive')
    except ModuleNotFoundError as error:
        if error.name == 'solar_flare_jepa.experiments.v2_descriptive':
            pytest.fail('The M4B descriptive comparison adapter is not implemented')
        raise


def records(losses, *, model='a', seeds=(3, 5), day=0, **identity_changes):
    """A median at 10**(2*loss) against y=1 has dex pinball exactly loss."""
    losses = np.asarray(losses, float)
    n = losses.shape[1]
    spec = ForecastSpec(1, 1, 1, ('x',), ('x',), ('u',), ('u',),
        availability_mode='retrospective_bin_end', transform='log10',
        feature_reference=(1.,), target_reference=(1.,))
    issues = day * DAY_NS + np.arange(n, dtype=np.int64) * NS + NS
    starts = issues[:, None]
    grid = FutureGrid(starts, starts + NS, issues,
        tuple(f'f{day}-o{i}' for i in range(n)), spec, f'data-{day}')
    targets = ForecastTargets(np.ones((n, 1, 1)), np.ones((n, 1, 1), bool), grid)
    cohort = []
    for seed, values in zip(seeds, losses):
        declarations = dict(experiment_id='synthetic', model_version=f'{model}-v2', seed=seed,
            code_fingerprint='code', config_fingerprint=f'{model}-recipe',
            data_provenance_fingerprint=f'data-{day}', split_fingerprint=f'split-{day}',
            training_fingerprint=f'train-{day}', normalization_fingerprint=f'norm-{day}',
            protocol_fingerprint='proposed-development')
        declarations.update(identity_changes)
        point = np.power(10., 2 * values)[:, None, None]
        prediction = ForecastPrediction(point, grid, model, (.5,), point[..., None])
        cohort.append(EvaluationRecord(EvaluationIdentity(**declarations), targets, prediction))
    return cohort


def example():
    a = dict(alpha=records([[1., 1.], [3., 3.]]),
             beta=records([[2.] * 6, [6.] * 6], day=10))
    b = dict(alpha=records([[2., 2.], [4., 4.]], model='b'),
             beta=records([[6.] * 6, [8.] * 6], model='b', day=10))
    calendars = dict(alpha=(0, 2 * DAY_NS), beta=(10 * DAY_NS, 12 * DAY_NS))
    return a, b, calendars


def compare(a=None, b=None, calendars=None):
    aa, bb, bounds = example()
    return api().descriptive_comparison(aa if a is None else a, bb if b is None else b,
                                       calendars=bounds if calendars is None else calendars)


def test_equal_fixed_fold_weighting_and_seed_summaries_have_no_inference():
    result = compare()
    assert result['status'] == 'DESCRIPTIVE_ONLY'
    assert result['inference_status'] == 'INFERENCE_UNAVAILABLE'
    assert result['inference_reason'] == 'NO_VALIDATED_REPLACEMENT'
    assert result['seed_ids'] == [3, 5]
    assert result['mean_a'] == pytest.approx(3.)
    assert result['mean_b'] == pytest.approx(5.)
    assert result['mean_difference'] == pytest.approx(-2.)
    assert result['relative_reduction'] == pytest.approx(.4)
    assert result['per_seed_difference'] == pytest.approx([-2.5, -1.5])
    assert result['seed_difference_sd'] == pytest.approx(math.sqrt(.5))
    assert result['seed_win_fraction'] == 1.
    assert result['leave_one_seed_out_difference'] == pytest.approx([-1.5, -2.5])
    assert result['folds']['alpha']['mean_difference'] == pytest.approx(-1.)
    assert result['folds']['beta']['mean_difference'] == pytest.approx(-3.)
    assert result['folds']['beta']['origins'] == 6
    for key in ('difference_interval', 'relative_interval', 'p_value', 'significance'):
        assert result[key] is None
    json.dumps(result, allow_nan=False)


def test_single_seed_is_descriptive_and_has_no_dispersion_or_leave_one_out_estimate():
    a = {'f': records([[1., 1.]], seeds=(7,))}
    b = {'f': records([[2., 2.]], model='b', seeds=(7,))}
    result = compare(a, b, {'f': (0, 2 * DAY_NS)})
    assert result['mean_difference'] == pytest.approx(-1.)
    assert result['seed_difference_sd'] is None
    assert result['leave_one_seed_out_difference'] == [None]
    assert result['inference_status'] == 'INFERENCE_UNAVAILABLE'


@pytest.mark.parametrize('field', [
    'experiment_id', 'code_fingerprint', 'data_provenance_fingerprint',
    'split_fingerprint', 'training_fingerprint', 'normalization_fingerprint',
    'protocol_fingerprint',
])
def test_cross_arm_common_provenance_mismatch_is_rejected(field):
    a, b, calendars = example()
    b['alpha'] = [replace(r, identity=replace(r.identity, **{field: 'changed'})) for r in b['alpha']]
    with pytest.raises(ValueError):
        compare(a, b, calendars)


@pytest.mark.parametrize('field', ['experiment_id', 'code_fingerprint', 'protocol_fingerprint'])
def test_global_experiment_code_and_protocol_mismatch_between_folds_is_rejected(field):
    a, b, calendars = example()
    for mapping in (a, b):
        mapping['beta'] = [replace(r, identity=replace(r.identity, **{field: 'changed'}))
                           for r in mapping['beta']]
    with pytest.raises(ValueError):
        compare(a, b, calendars)


@pytest.mark.parametrize('side', ['a', 'b'])
@pytest.mark.parametrize('field', ['model_version', 'config_fingerprint', 'model_id', 'point_interpretation'])
def test_each_model_recipe_is_stable_across_fixed_folds(side, field):
    a, b, calendars = example()
    mapping = a if side == 'a' else b
    if field in ('model_version', 'config_fingerprint'):
        mapping['beta'] = [replace(r, identity=replace(r.identity, **{field: 'other-recipe'}))
                           for r in mapping['beta']]
    else:
        value = 'other-model' if field == 'model_id' else 'inverse_transformed_point'
        mapping['beta'] = [replace(r, prediction=replace(r.prediction, **{field: value}))
                           for r in mapping['beta']]
    with pytest.raises(ValueError, match='model|recipe'):
        compare(a, b, calendars)


@pytest.mark.parametrize('where', ['paired_arm', 'another_fold'])
def test_reversed_seed_order_is_rejected(where):
    a, b, calendars = example()
    if where == 'paired_arm':
        b['alpha'] = list(reversed(b['alpha']))
    else:
        a['beta'] = list(reversed(a['beta']))
        b['beta'] = list(reversed(b['beta']))
    with pytest.raises(ValueError):
        compare(a, b, calendars)


def test_changed_target_values_cannot_pair_under_equal_metadata():
    a, b, calendars = example()
    b['alpha'] = [replace(r, targets=replace(r.targets, values=r.targets.values * 2)) for r in b['alpha']]
    with pytest.raises(ValueError):
        compare(a, b, calendars)


@pytest.mark.parametrize('damage', ['partial_targets', 'point_only'])
def test_missing_primary_target_or_quantile_support_is_rejected_without_imputation(damage):
    a, b, calendars = example()
    changed = []
    for record in a['alpha']:
        if damage == 'partial_targets':
            mask = record.targets.mask.copy()
            mask[0] = False
            record = replace(record, targets=replace(record.targets, mask=mask))
        else:
            record = replace(record, prediction=replace(record.prediction,
                quantiles=None, quantile_levels=()))
        changed.append(record)
    a['alpha'] = changed
    with pytest.raises(ValueError):
        compare(a, b, calendars)


@pytest.mark.parametrize('damage', ['missing_fold', 'extra_calendar', 'missing_calendar', 'overlap', 'origin_outside'])
def test_fold_and_explicit_calendar_identity_guards(damage):
    a, b, calendars = example()
    if damage == 'missing_fold':
        b.pop('beta')
    elif damage == 'extra_calendar':
        calendars['extra'] = (20 * DAY_NS, 22 * DAY_NS)
    elif damage == 'missing_calendar':
        calendars.pop('beta')
    elif damage == 'overlap':
        calendars['alpha'] = (0, 11 * DAY_NS)
    else:
        calendars['alpha'] = (DAY_NS, 2 * DAY_NS)
    with pytest.raises(ValueError):
        compare(a, b, calendars)


@pytest.mark.parametrize('a,b,calendars', [({}, {}, {}), ([], [], {}), ({'f': []}, {'f': []}, {'f': (0, DAY_NS)})])
def test_empty_or_nonmapping_cohorts_do_not_publish(a, b, calendars):
    with pytest.raises(ValueError):
        compare(a, b, calendars)


def test_difference_is_reduced_after_pairing_before_model_means_cancel():
    a = records([[100., 100.], [100., 100.]])
    b = records([[100., 100.], [100., 100.]], model='b')
    prediction = a[0].prediction
    point = prediction.values.copy()
    point[0, 0, 0] = 10. ** np.nextafter(200., np.inf)
    a[0] = replace(a[0], prediction=replace(prediction, values=point, quantiles=point[..., None]))
    result = compare({'f': a}, {'f': b}, {'f': (0, 2 * DAY_NS)})
    # One cell's log10 increases by one ULP at 200. Its .5 pinball contribution
    # is averaged across two origins and two seeds: 2**-45 / 8 = 2**-48.
    assert result['mean_difference'] == 2. ** -48
    assert result['mean_a'] - result['mean_b'] == 0.


def test_zero_reference_loss_leaves_relative_reduction_unavailable():
    a = {'f': records([[1., 1.], [2., 2.]])}
    b = {'f': records([[0., 0.], [0., 0.]], model='b')}
    result = compare(a, b, {'f': (0, 2 * DAY_NS)})
    assert result['mean_difference'] == pytest.approx(1.5)
    assert result['relative_reduction'] is None
    assert result['relative_reduction_reason'] == 'nonpositive_reference'


def test_historical_bootstrap_and_rng_are_never_called(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Descriptive reporting attempted statistical inference')
    module = importlib.import_module('solar_flare_jepa.evaluation.comparison')
    monkeypatch.setattr(module, 'paired_comparison', forbidden)
    monkeypatch.setattr(np.random, 'default_rng', forbidden)
    result = compare()
    assert result['mean_difference'] == pytest.approx(-2.)
    assert result['difference_interval'] is None


def test_inference_parameters_are_not_an_opt_in_escape_hatch():
    a, b, calendars = example()
    with pytest.raises(TypeError):
        api().descriptive_comparison(a, b, calendars=calendars, inference=True)
