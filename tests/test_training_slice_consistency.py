"""Adversarial raw/window consistency and effective fitting identity regressions."""
from copy import deepcopy
from dataclasses import replace

import numpy as np
import pytest

from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows

NS = 1_000_000_000
MODELS = [('persistence', {}), ('training_mean', {}),
          ('trailing_mean', {'lookback_steps': 2}), ('drift', {'lookback_steps': 2}),
          ('ar1', {}), ('direct_ridge', {'lag_steps': 1, 'alpha': .1})]


def dataset():
    starts = np.arange(12, dtype=np.int64) * NS
    values = np.arange(1., 13.)[:, None]
    mask = np.ones(values.shape, bool)
    return TimeSeriesDataset('consistency_fixture', 'synthetic_fixture', starts,
        starts + NS, values, mask, values, mask, ('x',), ('x',), ('u',), ('u',),
        1, starts[:, None] + NS)


def training(data=None, **changes):
    spec = ForecastSpec(1, 2, 1, ('x',), ('x',), ('u',), ('u',),
                        eligibility_policy='masked', **changes)
    return build_partition_windows(dataset() if data is None else data, spec,
                                   TemporalPartition('train', 0, 8 * NS)).training_slice


@pytest.mark.parametrize('part', ['context', 'targets'])
def test_window_value_mutation_is_rejected_before_fitting(part):
    train = training()
    window = getattr(train, part)
    values = window.values.copy()
    values[0, 0, 0] += 1000
    inconsistent = replace(window, values=values)
    with pytest.raises(ValueError, match='raw|canonical|consistent'):
        replace(train, **{part: inconsistent})


@pytest.mark.parametrize('part', ['context', 'targets'])
def test_window_mask_downgrade_cannot_drop_valid_raw_support(part):
    train = training()
    window = getattr(train, part)
    values, mask = window.values.copy(), window.mask.copy()
    values[0, 0, 0], mask[0, 0, 0] = np.nan, False
    with pytest.raises(ValueError, match='raw|canonical|consistent'):
        replace(train, **{part: replace(window, values=values, mask=mask)})


@pytest.mark.parametrize('kind,part', [('features', 'context'), ('targets', 'targets')])
def test_window_mask_upgrade_cannot_invent_missing_raw_support(kind, part):
    data = dataset()
    field = 'feature_mask' if kind == 'features' else 'target_mask'
    mask = getattr(data, field).copy()
    mask[2, 0] = False
    train = training(replace(data, **{field: mask}))
    window = getattr(train, part)
    values, mask = window.values.copy(), window.mask.copy()
    index = tuple(np.argwhere(~mask)[0])
    values[index], mask[index] = 999., True
    with pytest.raises(ValueError, match='raw|canonical|consistent'):
        replace(train, **{part: replace(window, values=values, mask=mask)})


@pytest.mark.parametrize('part', ['context', 'targets'])
def test_false_window_cells_cannot_hide_finite_payloads(part):
    data = dataset()
    field = 'feature_mask' if part == 'context' else 'target_mask'
    mask = getattr(data, field).copy()
    mask[2, 0] = False
    train = training(replace(data, **{field: mask}))
    window = getattr(train, part)
    values = window.values.copy()
    values[tuple(np.argwhere(~window.mask)[0])] = 1e100
    with pytest.raises(ValueError, match='raw|canonical|consistent'):
        replace(train, **{part: replace(window, values=values)})


def test_repeated_coordinates_cannot_disagree_with_one_another():
    train = training()
    values = train.context.values.copy()
    # Tick 1 appears at [0,1] and [1,0], and has canonical raw value 2.
    assert values[0, 1, 0] == values[1, 0, 0] == 2.
    values[1, 0, 0] = 1234.
    with pytest.raises(ValueError, match='raw|canonical|consistent'):
        replace(train, context=replace(train.context, values=values))


def test_context_cannot_redeclare_canonical_actual_availability():
    train = training()
    availability = train.context.availability_ns.copy()
    availability[0, 0, 0] += 1  # Still past bin-end and before issue; local validation passes.
    context = replace(train.context, availability_ns=availability)
    with pytest.raises(ValueError, match='availability|canonical|raw'):
        replace(train, context=context)


def test_delayed_cell_cannot_be_exposed_by_redeclaring_its_delivery_time():
    data = dataset()
    availability = data.availability_ns.copy()
    availability[2, 0] = 5 * NS
    train = training(replace(data, availability_ns=availability))
    values, mask = train.context.values.copy(), train.context.mask.copy()
    available = train.context.availability_ns.copy()
    index = tuple(np.argwhere(~mask)[0])
    values[index], mask[index], available[index] = 3., True, 3 * NS
    context = replace(train.context, values=values, mask=mask, availability_ns=available)
    with pytest.raises(ValueError, match='availability|canonical|raw'):
        replace(train, context=context)


@pytest.mark.parametrize('lookback', [0, 1])
def test_canonical_delayed_masks_keep_legitimate_origin_deadlines(lookback):
    data = dataset()
    available = data.availability_ns.copy()
    available[2, 0] = 5 * NS
    train = training(replace(data, availability_ns=available), feature_lookback_steps=lookback)
    assert train.raw_feature_mask[2, 0]  # Available by training partition end.
    row = list(train.context.issue_times_ns).index(3 * NS)
    assert not train.context.mask[row, -1, 0]  # Not available at this issue.
    assert np.isnan(train.context.values[row, -1, 0])
    row = list(train.context.issue_times_ns).index(5 * NS)
    assert train.context.mask[row].all()
    replace(train)  # The valid public construction still succeeds.


@pytest.mark.parametrize('mode', ['operational', 'retrospective_bin_end'])
def test_known_training_availability_cannot_be_dropped(mode):
    train = training(availability_mode=mode)
    with pytest.raises(ValueError, match='availability'):
        replace(train, raw_availability_ns=None)


def test_retrospective_unknown_availability_stays_unknown():
    data = replace(dataset(), availability_ns=None, availability_policy='bin_end_earliest')
    train = training(data, availability_mode='retrospective_bin_end')
    assert train.context.availability_ns is None
    assert getattr(train, 'raw_availability_ns', None) is None
    replace(train)


def test_joint_value_change_has_distinct_effective_ridge_identity():
    one = training()
    two = replace(one, raw_features=one.raw_features + 1000.,
                  context=replace(one.context, values=one.context.values + 1000.))
    assert one.context.dataset_fingerprint == two.context.dataset_fingerprint
    assert one.split_fingerprint == two.split_fingerprint
    models = [make_baseline('direct_ridge', {'lag_steps': 1, 'alpha': .1}).fit(t)
              for t in (one, two)]
    assert models[0].parameters['intercept'] != models[1].parameters['intercept']
    assert models[0].parameters.get('training_fingerprint') != models[1].parameters.get('training_fingerprint')


@pytest.mark.parametrize('kind', ['features', 'targets'])
def test_joint_mask_change_has_distinct_effective_ridge_identity(kind):
    one = training()
    mask_field = 'raw_feature_mask' if kind == 'features' else 'raw_target_mask'
    part = 'context' if kind == 'features' else 'targets'
    raw_mask, raw_values = getattr(one, mask_field).copy(), getattr(one, 'raw_' + kind).copy()
    raw_mask[4, 0], raw_values[4, 0] = False, np.nan
    window = getattr(one, part)
    matches = window.starts_ns == 4 * NS if part == 'context' else window.grid.starts_ns == 4 * NS
    mask, values = window.mask.copy(), window.values.copy()
    mask[matches, :], values[matches, :] = False, np.nan
    two = replace(one, **{mask_field: raw_mask, 'raw_' + kind: raw_values,
                         part: replace(window, values=values, mask=mask)})
    assert one.split_fingerprint == two.split_fingerprint
    models = [make_baseline('direct_ridge', {'lag_steps': 1, 'alpha': .1}).fit(t)
              for t in (one, two)]
    assert models[0].parameters['valid_window_count'] > models[1].parameters['valid_window_count']
    assert models[0].parameters.get('training_fingerprint') != models[1].parameters.get('training_fingerprint')


@pytest.mark.parametrize('name,parameters', MODELS)
@pytest.mark.parametrize('mutation', ['value', 'mask'])
def test_every_fit_revalidates_copied_training_before_consumption(name, parameters, mutation):
    # deepcopy is a real public reconstruction path that restores writable buffers.
    copied = deepcopy(training())
    if mutation == 'value':
        copied.context.values[0, 0, 0] += 1000
    else:
        copied.targets.mask[0, 0, 0] = False
        copied.targets.values[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match='raw|canonical|consistent'):
        make_baseline(name, parameters).fit(copied)


@pytest.mark.parametrize('name,parameters,want', [
    ('persistence', {}, 2.), ('training_mean', {}, 4.5),
    ('trailing_mean', {'lookback_steps': 2}, 1.5),
    ('drift', {'lookback_steps': 2}, 3.), ('ar1', {}, 3.),
    ('direct_ridge', {'lag_steps': 1, 'alpha': 0.}, 3.),
])
def test_canonical_training_preserves_all_six_literal_baseline_outputs(name, parameters, want):
    train = training()
    model = make_baseline(name, parameters).fit(train)
    prediction = model.predict(train.context, train.targets.grid)
    assert prediction.values[0, 0, 0] == pytest.approx(want)


@pytest.mark.parametrize('name,parameters', MODELS)
def test_future_perturbation_preserves_training_identity_fit_and_prediction(name, parameters):
    data = dataset()
    features, targets = data.features.copy(), data.targets.copy()
    features[8:], targets[8:] = 1e100, -1e100
    trains = [training(d) for d in (data, replace(data, features=features, targets=targets))]
    models = [make_baseline(name, parameters).fit(t) for t in trains]
    records = [model.parameters for model in models]
    assert isinstance(records[0].get('training_fingerprint'), str)
    assert records[0]['training_fingerprint'] == records[1]['training_fingerprint']
    for record in records:
        record.pop('dataset_fingerprint')
        record.pop('split_fingerprint')
    assert records[0] == records[1]
    predictions = [model.predict(train.context, train.targets.grid).values
                   for model, train in zip(models, trains)]
    np.testing.assert_array_equal(*predictions)
