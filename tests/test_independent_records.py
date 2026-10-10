"""Strict independent evaluation records, using artificial observations only."""
from copy import deepcopy
from dataclasses import replace
import importlib
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
)

NS = 1_000_000_000


def api():
    return importlib.import_module('solar_flare_jepa.evaluation.records')


def identity(**changes):
    fields = dict(experiment_id='artificial', model_version='toy-v1', seed=17,
        code_fingerprint='code', config_fingerprint='config',
        data_provenance_fingerprint='provenance', split_fingerprint='splits',
        training_fingerprint='training', normalization_fingerprint='normalization',
        protocol_fingerprint='protocol')
    fields.update(changes)
    return api().EvaluationIdentity(**fields)


def fixture():
    spec = ForecastSpec(1, 2, 2, ('x',), ('x',), ('artificial',), ('artificial',),
                        availability_mode='retrospective_bin_end', eligibility_policy='masked')
    issues = np.array([10, 12], np.int64) * NS
    starts = issues[:, None] + np.array([0, 1], np.int64) * NS
    grid = FutureGrid(starts, starts + NS, issues, ('o10', 'o12'), spec, 'dataset')
    observed = np.array([[[2.], [np.nan]], [[4.], [5.]]])
    targets = ForecastTargets(observed, np.isfinite(observed), grid)
    point = np.array([[[1.], [2.]], [[3.], [4.]]])
    prediction = ForecastPrediction(point, grid, 'toy', (.25, .75),
                                    np.stack((point, point + 2), axis=-1))
    return targets, prediction


def test_record_roundtrip_preserves_values_masks_quantiles_and_identity():
    targets, prediction = fixture()
    record = api().EvaluationRecord(identity(), targets, prediction)
    payload = record.as_dict()
    assert payload['targets']['values'][0][1][0] is None
    encoded = record.to_json()
    json.loads(encoded, parse_constant=lambda value: pytest.fail(value))
    restored = api().EvaluationRecord.from_json(encoded)
    assert restored.fingerprint == record.fingerprint
    assert restored.support_fingerprint == api().support_fingerprint(targets)
    np.testing.assert_array_equal(restored.targets.values, targets.values)
    np.testing.assert_array_equal(restored.prediction.quantiles, prediction.quantiles)
    assert not restored.targets.values.flags.writeable
    assert restored.identity.selection_partition == 'validation'


@pytest.mark.parametrize('probabilistic', [False, True])
def test_empty_record_roundtrip_restores_declared_shapes_and_integer_coordinates(probabilistic):
    targets, prediction = fixture()
    grid = replace(targets.grid, starts_ns=targets.grid.starts_ns[:0],
        ends_ns=targets.grid.ends_ns[:0], issue_times_ns=targets.grid.issue_times_ns[:0],
        origin_ids=())
    targets = replace(targets, values=targets.values[:0], mask=targets.mask[:0], grid=grid)
    prediction = replace(prediction, values=prediction.values[:0], grid=grid,
        quantile_levels=prediction.quantile_levels if probabilistic else (),
        quantiles=prediction.quantiles[:0] if probabilistic else None)
    record = api().EvaluationRecord(identity(), targets, prediction)
    restored = api().EvaluationRecord.from_json(record.to_json())
    assert restored.fingerprint == record.fingerprint
    assert restored.targets.values.shape == (0, 2, 1)
    assert restored.targets.mask.dtype == bool
    assert restored.targets.grid.starts_ns.shape == (0, 2)
    assert restored.targets.grid.starts_ns.dtype == np.int64
    assert restored.targets.grid.issue_times_ns.dtype == np.int64
    if probabilistic:
        assert restored.prediction.quantiles.shape == (0, 2, 1, 2)
    else:
        assert restored.prediction.quantiles is None


@pytest.mark.parametrize('changes', [dict(seed=True), dict(seed=-1), dict(seed=1.5),
    dict(seed=2**32), dict(model_version=''), dict(code_fingerprint=' '),
    dict(schema_version=True), dict(schema_version=2),
    dict(selection_partition='train'), dict(selection_partition='test'),
    dict(selection_partition='calibration')])
def test_identity_rejects_ambiguous_metadata_or_nonvalidation_selection(changes):
    with pytest.raises(ValueError):
        identity(**changes)


@pytest.mark.parametrize('part', ['value', 'mask', 'time', 'unit', 'dataset'])
def test_support_identity_changes_when_observed_support_changes(part):
    targets, _ = fixture()
    original = api().support_fingerprint(targets)
    if part == 'value':
        targets = replace(targets, values=targets.values + 1)
    elif part == 'mask':
        mask = targets.mask.copy()
        mask[1, 1] = False
        targets = replace(targets, mask=mask)
    elif part == 'dataset':
        targets = replace(targets, grid=replace(targets.grid, dataset_fingerprint='other'))
    elif part == 'unit':
        grid = replace(targets.grid, spec=replace(targets.grid.spec, target_units=('other',)))
        targets = replace(targets, grid=grid)
    else:
        grid = replace(targets.grid, starts_ns=targets.grid.starts_ns + NS,
            ends_ns=targets.grid.ends_ns + NS, issue_times_ns=targets.grid.issue_times_ns + NS)
        targets = replace(targets, grid=grid)
    assert api().support_fingerprint(targets) != original


def test_support_identity_ignores_unscored_payload_and_model_values():
    targets, prediction = fixture()
    hidden = targets.values.copy()
    hidden[~targets.mask] = 900
    one = api().EvaluationRecord(identity(), targets, prediction)
    two = api().EvaluationRecord(identity(), replace(targets, values=hidden),
                                 replace(prediction, values=prediction.values + 1))
    assert one.support_fingerprint == two.support_fingerprint
    assert one.fingerprint != two.fingerprint
    assert two.as_dict()['targets']['values'][0][1][0] is None


def test_record_rejects_misaligned_prediction_and_revalidates_copied_state():
    targets, prediction = fixture()
    with pytest.raises(ValueError):
        api().EvaluationRecord(identity(), targets,
            replace(prediction, grid=replace(prediction.grid, dataset_fingerprint='other')))
    copied = deepcopy(prediction)
    object.__setattr__(copied, 'quantiles', copied.quantiles[..., ::-1])
    with pytest.raises(ValueError):
        api().EvaluationRecord(identity(), targets, copied)
    record = api().EvaluationRecord(identity(), targets, prediction)
    object.__setattr__(record.prediction, 'values', np.ones((1, 1, 1)))
    with pytest.raises(ValueError):
        record.to_json()


@pytest.mark.parametrize('damage', ['unknown', 'version', 'support', 'valid_null',
    'masked_number', 'mask_integer', 'grid_unknown', 'identity_unknown', 'prediction_nan'])
def test_record_loader_rejects_schema_and_content_corruption(damage):
    targets, prediction = fixture()
    payload = api().EvaluationRecord(identity(), targets, prediction).as_dict()
    if damage == 'unknown':
        payload['extra'] = 'unexpected'
    elif damage == 'version':
        payload['schema_version'] = True
    elif damage == 'support':
        payload['support_fingerprint'] = 'forged'
    elif damage == 'valid_null':
        payload['targets']['values'][0][0][0] = None
    elif damage == 'masked_number':
        payload['targets']['values'][0][1][0] = 99.
    elif damage == 'mask_integer':
        payload['targets']['mask'][0][0][0] = 1
    elif damage == 'grid_unknown':
        payload['grid']['extra'] = 'unexpected'
    elif damage == 'identity_unknown':
        payload['identity']['extra'] = 'unexpected'
    else:
        payload['prediction']['values'][0][0][0] = float('nan')
    with pytest.raises(ValueError):
        api().EvaluationRecord.from_dict(payload)


@pytest.mark.parametrize('content', ['{"schema_version":1,"schema_version":1}',
                                   '{"x":NaN}', '{"x":Infinity}'])
def test_json_loader_rejects_duplicate_keys_and_nonfinite_literals(content):
    with pytest.raises(ValueError):
        api().EvaluationRecord.from_json(content)


@pytest.mark.parametrize('part', ['targets', 'points', 'quantiles'])
@pytest.mark.parametrize('value', ['2.0', True, False, None])
def test_loader_rejects_coercible_nonnumeric_json_cells(part, value):
    targets, prediction = fixture()
    payload = api().EvaluationRecord(identity(), targets, prediction).as_dict()
    if part == 'targets':
        payload['targets']['values'][0][0][0] = value
    elif part == 'points':
        payload['prediction']['values'][0][0][0] = value
    else:
        payload['prediction']['quantiles'][0][0][0][0] = value
    with pytest.raises(ValueError):
        api().EvaluationRecord.from_dict(payload)


def test_subclass_hooks_cannot_replace_record_spec_or_identity_semantics():
    targets, prediction = fixture()
    class FakeSpec(ForecastSpec):
        @property
        def fingerprint(self):
            return targets.grid.spec.fingerprint
    forged = FakeSpec(**replace(targets.grid.spec, target_units=('other',)).as_dict())
    copied = deepcopy(prediction)
    object.__setattr__(copied.grid, 'spec', forged)
    with pytest.raises(ValueError):
        api().EvaluationRecord(identity(), targets, copied)
    class FakeIdentity(api().EvaluationIdentity):
        def as_dict(self):
            return {'selection_partition': 'validation'}
    forged_identity = FakeIdentity(**identity().as_dict())
    object.__setattr__(forged_identity, 'selection_partition', 'test')
    with pytest.raises(ValueError):
        api().EvaluationRecord(forged_identity, targets, prediction)
