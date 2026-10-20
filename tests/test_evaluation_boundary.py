"""Revalidate public evaluation inputs; every observation is synthetic.

Copied/pickled frozen dataclasses can own writable arrays. Evaluation must
validate detached declarations again rather than trusting constructor history.
"""
from copy import copy, deepcopy
from dataclasses import fields, replace
import importlib
import json
import pickle

import numpy as np
import pytest

from solar_flare_jepa.evaluation import evaluate_events, evaluate_trajectory
from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
    TrainingSlice,
)

SECOND = 1_000_000_000


def fixture():
    spec = ForecastSpec(1, 1, 2, ('x',), ('x',), ('unit',), ('unit',),
                        eligibility_policy='masked', target_minimum=(0.,))
    issues = np.array([20, 21], dtype=np.int64) * SECOND
    starts = issues[:, None] + np.array([0, 1], dtype=np.int64) * SECOND
    grid = FutureGrid(starts, starts + SECOND, issues, ('o0', 'o1'), spec, 'synthetic')
    values = np.array([[[10.], [20.]], [[30.], [40.]]])
    targets = ForecastTargets(values, np.ones_like(values, bool), grid)
    prediction = ForecastPrediction(values - 8., grid, 'toy')
    persistence = ForecastPrediction(values - 4., grid, 'persistence')
    train_issues = np.array([1, 2], dtype=np.int64) * SECOND
    raw_starts = np.arange(4, dtype=np.int64) * SECOND
    raw = np.array([[1.], [4.], [8.], [13.]])
    context = ForecastContext(raw[:2, None, :], np.ones((2, 1, 1), bool),
        raw_starts[:2, None], raw_starts[:2, None] + SECOND,
        train_issues, ('t0', 't1'), spec, 'synthetic',
        (raw_starts[:2, None, None] + SECOND))
    train_starts = train_issues[:, None] + np.array([0, 1], dtype=np.int64) * SECOND
    train_grid = FutureGrid(train_starts, train_starts + SECOND, train_issues,
                            ('t0', 't1'), spec, 'synthetic')
    train_targets = ForecastTargets(np.array([[[4.], [8.]], [[8.], [13.]]]),
                                   np.ones((2, 2, 1), bool), train_grid)
    training = TrainingSlice(context, train_targets, raw_starts, raw_starts + SECOND,
        raw, np.ones_like(raw, bool), raw, np.ones_like(raw, bool),
        0, 4 * SECOND, 'split', raw_availability_ns=raw_starts[:, None] + SECOND)
    return targets, prediction, training, persistence


def test_nonempty_training_hand_calculated_scale_mase_and_reference_skill():
    result = evaluate_trajectory(*fixture())
    assert result['training_scales']['x'] == {'value': 4., 'reason': None, 'count': 3}
    cell = result['by_target']['x']
    assert cell['mae']['value'] == 8.
    assert cell['rmse']['value'] == 8.
    assert cell['mase']['value'] == 2.
    assert cell['persistence_mae_skill']['value'] == -1.
    assert cell['persistence_mse_skill']['value'] == -3.
    assert result['coverage']['valid_count'] == result['coverage']['total_count'] == 4
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('changed', ['targets', 'prediction', 'reference', 'training', 'weights'])
def test_evaluation_identity_records_actual_canonical_inputs(changed):
    targets, prediction, training, persistence = fixture()
    control = evaluate_trajectory(targets, prediction, training, persistence)
    weights = None
    if changed == 'targets':
        targets = replace(targets, values=targets.values + 1.)
    elif changed == 'prediction':
        prediction = replace(prediction, values=prediction.values + 1.)
    elif changed == 'reference':
        persistence = replace(persistence, values=persistence.values + 1.)
    elif changed == 'training':
        training = replace(training, raw_targets=training.raw_targets * 2.,
                           targets=replace(training.targets, values=training.targets.values * 2.))
    else:
        weights = [1., 2.]
    actual = evaluate_trajectory(targets, prediction, training, persistence, lead_weights=weights)
    assert actual['training_fingerprint'] == training.fingerprint
    assert actual['evaluation_input_fingerprint'] != control['evaluation_input_fingerprint']
    if changed == 'training':
        assert actual['training_fingerprint'] != control['training_fingerprint']
        assert actual['training_split_fingerprint'] == control['training_split_fingerprint']
        assert actual['by_target']['x']['mase']['value'] == 1.


@pytest.mark.parametrize('changed', ['probabilities', 'masks', 'horizon'])
def test_event_identity_records_effective_outcomes_and_coverage(changed):
    arguments = dict(outcomes=[0., 1.], valid_mask=[True, True], mature_mask=[True, True],
                     origin_ids=('o0', 'o1'), event_definition='synthetic_binary',
                     horizon_seconds=60, decisions=[0., 1.], probabilities=[.2, .8])
    control = evaluate_events(**arguments)
    if changed == 'probabilities':
        arguments['probabilities'] = [.1, .9]
    elif changed == 'masks':
        arguments['mature_mask'] = [True, False]
    else:
        arguments['horizon_seconds'] = 120
    actual = evaluate_events(**arguments)
    assert actual['evaluation_input_fingerprint'] != control['evaluation_input_fingerprint']


def test_target_mask_is_captured_once_before_validation_and_consumption():
    targets, prediction, training, persistence = fixture()
    expected = evaluate_trajectory(targets, prediction, training, persistence)

    class MaskOwner:
        calls = 0

        def __array__(self, dtype=None, copy=None):
            self.calls += 1
            result = np.ones((2, 2, 1), bool) if self.calls == 1 else np.zeros((2, 2, 1), int)
            return np.asarray(result, dtype=dtype)

    owner = MaskOwner()
    targets = copy(targets)
    object.__setattr__(targets, 'mask', owner)
    actual = evaluate_trajectory(targets, prediction, training, persistence)
    assert owner.calls == 1
    assert actual == expected


@pytest.mark.parametrize('field', ['stride_steps', 'feature_lookback_steps', 'label_maturity_steps'])
def test_integer_constraints_check_normalized_content_before_subtype_comparisons(field):
    class NegativeInteger(int):
        def __lt__(self, other):
            return False

    with pytest.raises(ValueError):
        ForecastSpec(1, 1, 2, ('x',), ('x',), ('unit',), ('unit',), **{field: NegativeInteger(-1)})


def test_extreme_positive_lead_weights_retain_masked_common_coverage():
    targets, prediction, training, persistence = fixture()
    mask = np.zeros(targets.mask.shape, bool)
    mask[:, 0] = True
    targets = replace(targets, mask=mask)
    result = evaluate_trajectory(targets, prediction, training, persistence,
                                 lead_weights=[1e-300, 1e300])
    assert result['coverage']['valid_count'] == result['coverage']['scored_count'] == 2
    assert result['by_target']['x']['mae'] == dict(value=8., count=2, reason=None)
    assert result['aggregate']['mae'] == dict(value=8., count=2, reason=None)


def test_extreme_positive_target_weights_retain_masked_common_coverage():
    from test_trajectory_metrics import fixture as two_target_fixture
    mask = np.zeros((2, 2, 2), bool)
    mask[:, :, 0] = True
    inputs = two_target_fixture(values=np.ones(mask.shape) * 10., predictions=np.ones(mask.shape) * 8.,
                                mask=mask, units=('unit', 'unit'))
    result = evaluate_trajectory(*inputs, target_weights=[1e-300, 1e300])
    assert result['coverage']['valid_count'] == result['coverage']['scored_count'] == 4
    assert result['aggregate']['mae'] == dict(value=2., count=4, reason=None)


@pytest.mark.parametrize('ownership', ['copy', 'deepcopy', 'pickle', 'new'])
def test_reconstructed_training_with_changed_raw_values_is_rejected(ownership):
    targets, prediction, training, persistence = fixture()
    if ownership == 'copy':
        training = copy(training)
    elif ownership == 'deepcopy':
        training = deepcopy(training)
    elif ownership == 'pickle':
        training = pickle.loads(pickle.dumps(training))
    else:
        original = training
        training = TrainingSlice.__new__(TrainingSlice)
        for field in fields(TrainingSlice):
            object.__setattr__(training, field.name, getattr(original, field.name))
    # This contradicts actual training windows; accepting it changes MASE 2 -> .008.
    object.__setattr__(training, 'raw_targets', np.array([[0.], [1000.], [2000.], [3000.]]))
    with pytest.raises(ValueError):
        evaluate_trajectory(targets, prediction, training, persistence)


@pytest.mark.parametrize('member', ['prediction', 'persistence'])
def test_prediction_shapes_cannot_broadcast_across_common_origins(member):
    targets, prediction, training, persistence = deepcopy(fixture())
    selected = prediction if member == 'prediction' else persistence
    selected.values.resize((1, 1, 1), refcheck=False)
    # Reference [6] would broadcast against all four targets and turn negative
    # skill positive while reporting unchanged 4/4 coverage.
    with pytest.raises(ValueError):
        evaluate_trajectory(targets, prediction, training, persistence)


@pytest.mark.parametrize('damage', [
    'target_mask_type', 'target_mask_shape', 'target_nonfinite',
    'shared_future_coordinates', 'shared_origin_identity',
    'training_context_availability', 'training_raw_availability',
    'training_target_mask', 'training_raw_mask', 'training_raw_coordinates',
    'training_partition_bounds', 'prediction_domain', 'persistence_domain',
    'shared_spec_reference', 'shared_spec_category',
])
def test_malformed_nested_state_is_rejected_without_correction(damage):
    targets, prediction, training, persistence = deepcopy(fixture())
    if damage == 'target_mask_type':
        object.__setattr__(targets, 'mask', targets.mask.astype(int))
    elif damage == 'target_mask_shape':
        object.__setattr__(targets, 'mask', np.ones((1, 1, 1), bool))
    elif damage == 'target_nonfinite':
        targets.values[0, 0, 0] = np.nan
    elif damage == 'shared_future_coordinates':
        targets.grid.starts_ns[0, 0] -= SECOND
    elif damage == 'shared_origin_identity':
        object.__setattr__(targets.grid, 'origin_ids', ('same', 'same'))
    elif damage == 'training_context_availability':
        training.context.availability_ns[0, 0, 0] = 2 * SECOND
    elif damage == 'training_raw_availability':
        training.raw_availability_ns[0, 0] = 5 * SECOND
    elif damage == 'training_target_mask':
        training.targets.mask[0, 0, 0] = False
    elif damage == 'training_raw_mask':
        training.raw_target_mask[1, 0] = False
    elif damage == 'training_raw_coordinates':
        training.raw_starts_ns[1] += 1
    elif damage == 'training_partition_bounds':
        object.__setattr__(training, 'partition_end_ns', 3 * SECOND)
    elif damage == 'prediction_domain':
        prediction.values[0, 0, 0] = -1.
    elif damage == 'persistence_domain':
        persistence.values[0, 0, 0] = -1.
    elif damage == 'shared_spec_reference':
        for spec in (targets.grid.spec, training.context.spec, training.targets.grid.spec):
            object.__setattr__(spec, 'target_reference', (-1.,))
    else:
        for spec in (targets.grid.spec, training.context.spec, training.targets.grid.spec):
            object.__setattr__(spec, 'availability_mode', 'unrecognized')
    with pytest.raises(ValueError):
        evaluate_trajectory(targets, prediction, training, persistence)


@pytest.mark.parametrize('damage', ['shape', 'crossing', 'levels', 'domain', 'missing'])
def test_quantile_state_is_revalidated_at_evaluation_boundary(damage):
    targets, prediction, training, persistence = fixture()
    quantiles = np.stack((targets.values - 2., targets.values + 2.), axis=-1)
    prediction = deepcopy(replace(prediction, quantile_levels=(.25, .75), quantiles=quantiles))
    if damage == 'shape':
        prediction.quantiles.resize((1, 1, 1, 2), refcheck=False)
    elif damage == 'crossing':
        prediction.quantiles[..., 0] = prediction.quantiles[..., 1] + 1.
    elif damage == 'levels':
        object.__setattr__(prediction, 'quantile_levels', (.75, .25))
    elif damage == 'domain':
        prediction.quantiles[0, 0, 0, 0] = -1.
    else:
        object.__setattr__(prediction, 'quantiles', None)
    with pytest.raises(ValueError):
        evaluate_trajectory(targets, prediction, training, persistence)


class LyingCategory(str):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    def __deepcopy__(self, memo):
        return 'native_point'


def test_categorical_equality_and_copy_hooks_cannot_supply_prediction_semantics():
    targets, prediction, training, persistence = fixture()
    prediction = copy(prediction)
    object.__setattr__(prediction, 'point_interpretation', LyingCategory('invented_semantics'))
    with pytest.raises(ValueError):
        evaluate_trajectory(targets, prediction, training, persistence)


class UntrustedSpec(ForecastSpec):
    @property
    def fingerprint(self):
        return 'forged-spec'

    def __deepcopy__(self, memo):
        raise AssertionError('Evaluation must read declarations, not dispatch deepcopy')


def test_spec_subclass_fingerprint_hook_does_not_replace_declared_identity():
    targets, prediction, training, persistence = fixture()
    baseline = evaluate_trajectory(targets, prediction, training, persistence)
    spec = UntrustedSpec(**{field.name: getattr(targets.grid.spec, field.name)
                           for field in fields(ForecastSpec)})
    object.__setattr__(targets.grid, 'spec', spec)
    object.__setattr__(training.context, 'spec', spec)
    object.__setattr__(training.targets.grid, 'spec', spec)
    result = evaluate_trajectory(targets, prediction, training, persistence)
    assert result['spec_fingerprint'] == baseline['spec_fingerprint']
    assert result['aggregate'] == baseline['aggregate']


class ArithmeticOwner(np.ndarray):
    def __sub__(self, other):
        return np.zeros(np.broadcast_shapes(self.shape, np.shape(other)))

    def __deepcopy__(self, memo):
        return np.zeros(self.shape)


def test_prediction_owner_arithmetic_and_deepcopy_hooks_do_not_change_errors():
    targets, prediction, training, persistence = fixture()
    expected = evaluate_trajectory(targets, prediction, training, persistence)
    prediction = copy(prediction)
    object.__setattr__(prediction, 'values', np.array(prediction.values).view(ArithmeticOwner))
    result = evaluate_trajectory(targets, prediction, training, persistence)
    assert result == expected


def test_training_scale_consumes_validated_detached_base_contracts(monkeypatch):
    module = importlib.import_module('solar_flare_jepa.evaluation.trajectory')
    targets, prediction, training, persistence = deepcopy(fixture())
    original = module._training_scales
    captured = []

    def observe(snapshot):
        captured.append(snapshot)
        return original(snapshot)

    monkeypatch.setattr(module, '_training_scales', observe)
    result = module.evaluate_trajectory(targets, prediction, training, persistence)
    assert result['by_target']['x']['mase']['value'] == 2.
    assert len(captured) == 1
    snapshot = captured[0]
    assert snapshot is not training
    assert type(snapshot) is TrainingSlice
    assert type(snapshot.context) is ForecastContext
    assert type(snapshot.targets) is ForecastTargets
    assert type(snapshot.spec) is ForecastSpec
    assert snapshot.fingerprint == training.fingerprint
    for owner, name in ((snapshot, 'raw_targets'), (snapshot.context, 'values'),
                        (snapshot.targets, 'values')):
        original_owner = training if owner is snapshot else (
            training.context if owner is snapshot.context else training.targets)
        assert not np.shares_memory(getattr(owner, name), getattr(original_owner, name))
        with pytest.raises(ValueError):
            getattr(owner, name).setflags(write=True)


def test_metrics_and_metadata_use_same_snapshots_after_caller_mutation(monkeypatch):
    module = importlib.import_module('solar_flare_jepa.evaluation.trajectory')
    targets, prediction, training, persistence = deepcopy(fixture())
    expected = module.evaluate_trajectory(targets, prediction, training, persistence)
    original = module._weights
    mutated = False

    def mutate_after_capture(value, size, name):
        nonlocal mutated
        if not mutated:
            mutated = True
            targets.values[:] += 100.
            targets.mask[:] = False
            prediction.values[:] += 200.
            persistence.values[:] += 300.
            training.raw_targets[:] *= 10.
            object.__setattr__(training, 'split_fingerprint', 'changed-by-caller')
            object.__setattr__(prediction, 'model_id', 'changed-by-caller')
        return original(value, size, name)

    monkeypatch.setattr(module, '_weights', mutate_after_capture)
    actual = module.evaluate_trajectory(targets, prediction, training, persistence)
    assert mutated
    assert actual == expected


def test_event_masks_are_owned_before_later_numeric_input_hooks_run():
    valid = np.ones(2, bool)
    mature = np.ones(2, bool)

    class OutcomesOwner:
        def __array__(self, dtype=None, copy=None):
            valid[:] = False
            mature[:] = False
            return np.array([0., 1.], dtype=dtype)

    result = evaluate_events(OutcomesOwner(), valid, mature, ('o0', 'o1'),
        'synthetic_binary', 60, decisions=[0., 1.], probabilities=[.2, .8])
    assert result['coverage'] == dict(total_count=2, valid_count=2, mature_count=2,
                                      scored_count=2, fraction=1.)
    assert all(row['valid'] and row['mature'] and row['scored'] for row in result['per_origin'])
    assert result['metrics']['brier']['value'] == pytest.approx(.04)


@pytest.mark.parametrize('ownership', ['copy', 'deepcopy', 'pickle'])
def test_valid_copies_and_serialized_reconstruction_preserve_finite_mathematics(ownership):
    original = fixture()
    expected = evaluate_trajectory(*original)
    reconstructed = tuple(copy(x) for x in original) if ownership == 'copy' else (
        deepcopy(original) if ownership == 'deepcopy' else pickle.loads(pickle.dumps(original)))
    assert evaluate_trajectory(*reconstructed) == expected


def test_masked_nan_empty_and_zero_scale_keep_explicit_null_reasons():
    targets, prediction, training, persistence = fixture()
    targets = replace(targets, values=np.full(targets.values.shape, np.nan),
                      mask=np.zeros(targets.mask.shape, bool))
    result = evaluate_trajectory(targets, prediction, training, persistence)
    assert result['by_target']['x']['mase'] == dict(value=None, reason='empty_mask', count=0)
    assert result['coverage']['valid_count'] == 0
    json.dumps(result, allow_nan=False)
    targets, prediction, training, persistence = fixture()
    constant = replace(training, raw_targets=np.ones(training.raw_targets.shape),
        targets=replace(training.targets, values=np.ones(training.targets.values.shape)))
    result = evaluate_trajectory(targets, prediction, constant, persistence)
    assert result['by_target']['x']['mase'] == dict(value=None, reason='zero_training_scale', count=4)
    json.dumps(result, allow_nan=False)


def test_target_free_forecasts_remain_independent_of_evaluation_targets():
    from solar_flare_jepa.forecasting.baselines import Persistence
    targets, prediction, training, persistence = fixture()
    model = Persistence().fit(training)
    first = model.predict(training.context, training.targets.grid).values.copy()
    held_out = deepcopy(targets)
    held_out.values[:] = 1e100
    second = model.predict(training.context, training.targets.grid).values
    np.testing.assert_array_equal(first, second)


def test_runner_records_malformed_prediction_before_scoring_or_publication(tmp_path, monkeypatch):
    """Real runner/scorer/publication; fixed provenance avoids fixture Git calls."""
    from test_experiment_provenance import config
    from solar_flare_jepa.experiments.provenance import verify_artifacts
    module = importlib.import_module('solar_flare_jepa.experiments.runner')
    cfg = config()
    cfg['baselines'].append(dict(name='training_mean', parameters={}))
    cfg['seeds'] = [17]
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps(cfg))
    provenance = dict(git_commit='bounded-fixture', git_branch='bounded-fixture',
                      source=dict(fingerprint='bounded-source', files=[]))
    monkeypatch.setattr(module, 'code_provenance', lambda root: deepcopy(provenance))
    monkeypatch.setattr(module, 'verify_source_identities', lambda root, files: None)
    make = module.make_baseline

    def malformed_model(name, parameters):
        model = make(name, parameters)
        if name == 'training_mean':
            predict = model.predict

            def malformed_prediction(context, grid):
                result = deepcopy(predict(context, grid))
                result.values.resize((1, 1, 2), refcheck=False)
                return result

            model.predict = malformed_prediction
        return model

    monkeypatch.setattr(module, 'make_baseline', malformed_model)
    output = module.run_experiment(config_path, tmp_path)
    verify_artifacts(output)
    result = json.loads((output / 'result.json').read_text())
    failures = json.loads((output / 'failures.json').read_text())
    metrics = json.loads((output / 'metrics.json').read_text())
    assert result['status'] == 'complete_with_model_failures'
    assert result['successful_model_partition_scores'] == 3
    assert result['failure_count'] == 3
    assert len(failures) == 3
    assert all(f['model'] == 'training_mean' and f['stage'] == 'predict' and
               f['error_type'] == 'ValueError' and f['attempted_origin_ids'] and
               f['common_target_valid_count'] > 0 for f in failures)
    assert all(record['status'] == 'failed' and record['metrics'] is None
               for record in metrics if record['model'] == 'training_mean')
    assert all(record['status'] == 'scored'
               for record in metrics if record['model'] == 'persistence')
