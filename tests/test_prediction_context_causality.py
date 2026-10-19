"""Issue-time validation at prediction, including reconstructed public inputs."""
from copy import copy, deepcopy
from dataclasses import fields, replace
import pickle

import numpy as np
import pytest

from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastSpec, FutureGrid, TimeSeriesDataset,
)
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows

NS = 1_000_000_000
MODELS = [
    ('persistence', {}, [10., 11.]),
    ('training_mean', {}, [4.5, 4.5]),
    ('trailing_mean', {'lookback_steps': 2}, [9.5, 10.5]),
    ('drift', {'lookback_steps': 2}, [11., 12.]),
    ('ar1', {}, [11., 12.]),
    ('direct_ridge', {'lag_steps': 2, 'alpha': .1},
     [10.984330484330483, 11.981481481481483]),
]
ROUTES = ('shallow', 'deepcopy', 'pickle', 'subclass', 'subclass_replace',
          'new', 'direct')


class UncheckedContext(ForecastContext):
    def __post_init__(self):
        pass


def declared(value, contract):
    return {field.name: getattr(value, field.name) for field in fields(contract)}


def fixture():
    """One-second ramp: raw train 1..8, test issues 10/11, future 11/12."""
    starts = np.arange(12, dtype=np.int64) * NS
    values = np.arange(1., 13.)[:, None]
    mask = np.ones(values.shape, bool)
    dataset = TimeSeriesDataset('prediction_fixture', 'synthetic_fixture',
        starts, starts + NS, values, mask, values, mask,
        ('x',), ('x',), ('u',), ('u',), 1, starts[:, None] + NS)
    spec = ForecastSpec(1, 2, 1, ('x',), ('x',), ('u',), ('u',))
    train = build_partition_windows(dataset, spec, TemporalPartition('train', 0, 8 * NS))
    test = build_partition_windows(dataset, spec, TemporalPartition('test', 8 * NS, 12 * NS))
    return train.training_slice, test


def reconstructed(context, route):
    if route == 'shallow':
        return copy(context)
    if route == 'deepcopy':
        return deepcopy(context)
    if route == 'pickle':
        return pickle.loads(pickle.dumps(context))
    if route == 'subclass':
        return UncheckedContext(**declared(context, ForecastContext))
    if route == 'subclass_replace':
        return replace(UncheckedContext(**declared(context, ForecastContext)))
    if route == 'new':
        instance = object.__new__(ForecastContext)
        vars(instance).update(declared(context, ForecastContext))
        return instance
    return context  # Explicit dictionary mutation is possible even when frozen.


def future_context(test, route):
    context = reconstructed(test.context, route)
    values = context.values.copy()
    values[:, -1, :] = test.targets.values[:, 0, :]
    changes = dict(values=values, starts_ns=context.starts_ns + NS,
                   ends_ns=context.ends_ns + NS,
                   availability_ns=context.availability_ns + NS)
    if route == 'subclass_replace':
        return replace(context, **changes)  # Calls the subtype's unchecked hook.
    vars(context).update(changes)
    return context


@pytest.mark.parametrize('name,parameters,want', MODELS)
@pytest.mark.parametrize('route', ROUTES)
def test_every_prediction_rejects_reconstructed_future_context(name, parameters, want, route):
    train, test = fixture()
    model = make_baseline(name, parameters).fit(train)
    before = model.parameters
    context = future_context(test, route)
    assert (context.ends_ns[:, -1] > context.issue_times_ns).all()
    assert (context.availability_ns[:, -1, 0] > context.issue_times_ns).all()
    # Removing common semantic validation would admit post-issue observations.
    with pytest.raises(ValueError):
        model.predict(context, test.targets.grid)
    assert model.parameters == before


@pytest.mark.parametrize('name,parameters,want', MODELS)
@pytest.mark.parametrize('mutation', [
    'late_availability', 'before_bin_availability', 'missing_availability',
    'off_grid_start', 'extended_end', 'numeric_mask', 'duplicate_origins',
    'reordered_issues',
])
def test_prediction_validates_actual_content_not_python_type(name, parameters, want, mutation):
    train, test = fixture()
    model = make_baseline(name, parameters).fit(train)
    context = deepcopy(test.context)
    if mutation == 'late_availability':
        context.availability_ns[:, -1, 0] = context.issue_times_ns + NS
        context.values[:, -1, :] = test.targets.values[:, 0, :]
    elif mutation == 'before_bin_availability':
        context.availability_ns[:, -1, 0] = context.ends_ns[:, -1] - 1
    elif mutation == 'missing_availability':
        vars(context)['availability_ns'] = None
    elif mutation == 'off_grid_start':
        context.starts_ns[:, 0] -= NS
    elif mutation == 'extended_end':
        context.ends_ns[:, -1] += NS
    elif mutation == 'numeric_mask':
        vars(context)['mask'] = context.mask.astype(np.int64)
    elif mutation == 'duplicate_origins':
        vars(context)['origin_ids'] = [context.origin_ids[0]] * 2
        grid = deepcopy(test.targets.grid)
        vars(grid)['origin_ids'] = [context.origin_ids[0]] * 2
    else:
        context.issue_times_ns[:] = context.issue_times_ns[::-1]
        grid = deepcopy(test.targets.grid)
        grid.issue_times_ns[:] = context.issue_times_ns
    grid = grid if mutation in ('duplicate_origins', 'reordered_issues') else test.targets.grid
    with pytest.raises(ValueError):
        model.predict(context, grid)


@pytest.mark.parametrize('name,parameters,want', MODELS)
@pytest.mark.parametrize('mutation', ['off_grid_start', 'not_future', 'float_times'])
def test_every_prediction_revalidates_future_grid(name, parameters, want, mutation):
    train, test = fixture()
    model = make_baseline(name, parameters).fit(train)
    grid = deepcopy(test.targets.grid)
    if mutation == 'off_grid_start':
        grid.starts_ns[:] += NS
    elif mutation == 'not_future':
        grid.ends_ns[:] = grid.issue_times_ns[:, None]
    else:
        vars(grid)['starts_ns'] = grid.starts_ns.astype(float)
    with pytest.raises(ValueError):
        model.predict(test.context, grid)


@pytest.mark.parametrize('name,parameters,want', MODELS)
@pytest.mark.parametrize('route', ['canonical', 'shallow', 'deepcopy', 'pickle', 'replace', 'subclass'])
def test_valid_prediction_reconstructions_preserve_literal_outputs(name, parameters, want, route):
    train, test = fixture()
    model = make_baseline(name, parameters).fit(train)
    before = model.parameters
    context = replace(test.context) if route == 'replace' else (
        test.context if route == 'canonical' else reconstructed(test.context, route))
    prediction = model.predict(context, test.targets.grid)
    np.testing.assert_allclose(prediction.values[:, 0, 0], want, rtol=1e-12)
    assert model.parameters == before


@pytest.mark.parametrize('name,parameters,want', MODELS)
def test_returned_grid_is_immutable_and_detached_from_deserialized_input(name, parameters, want):
    train, test = fixture()
    grid = pickle.loads(pickle.dumps(test.targets.grid))
    prediction = make_baseline(name, parameters).fit(train).predict(test.context, grid)
    grid.starts_ns[:] += NS
    grid.ends_ns[:] += NS
    np.testing.assert_array_equal(prediction.grid.starts_ns[:, 0], [10 * NS, 11 * NS])
    np.testing.assert_array_equal(prediction.grid.ends_ns[:, 0], [11 * NS, 12 * NS])
    with pytest.raises(ValueError):
        prediction.grid.starts_ns.setflags(write=True)


@pytest.mark.parametrize('name,parameters,want', MODELS)
def test_subclass_fingerprint_cannot_conceal_different_declared_units(name, parameters, want):
    train, test = fixture()
    identity = train.spec.fingerprint

    class CachedIdentitySpec(ForecastSpec):
        @property
        def fingerprint(self):
            return identity

    spec = CachedIdentitySpec(**(declared(train.spec, ForecastSpec) |
                                 {'target_units': ('different_unit',)}))
    context = replace(test.context, spec=spec)
    grid = replace(test.targets.grid, spec=spec)
    with pytest.raises(ValueError):
        make_baseline(name, parameters).fit(train).predict(context, grid)


@pytest.mark.parametrize('name,parameters,want', MODELS)
def test_declared_valid_spec_is_canonicalized_without_executing_subtype_hooks(name, parameters, want):
    train, test = fixture()

    class BrokenHooksSpec(ForecastSpec):
        @property
        def fingerprint(self):
            raise AssertionError('Subtype fingerprint is not canonical semantics')

        def as_dict(self):
            raise AssertionError('Subtype serializer is not canonical semantics')

    spec = BrokenHooksSpec(**declared(train.spec, ForecastSpec))
    context, grid = replace(test.context, spec=spec), replace(test.targets.grid, spec=spec)
    prediction = make_baseline(name, parameters).fit(train).predict(context, grid)
    np.testing.assert_allclose(prediction.values[:, 0, 0], want, rtol=1e-12)
    assert type(prediction.grid.spec) is ForecastSpec


def test_nested_cadence_override_cannot_turn_future_values_into_completed_bins():
    train, test = fixture()

    class ZeroCadenceSpec(ForecastSpec):
        @property
        def cadence_ns(self):
            return 0

    spec = ZeroCadenceSpec(**declared(train.spec, ForecastSpec))
    coordinates = np.broadcast_to(test.context.issue_times_ns[:, None], (2, 2))
    values = np.repeat(test.targets.values, 2, axis=1)
    context = ForecastContext(values, np.ones_like(values, bool), coordinates,
        coordinates, test.context.issue_times_ns, test.context.origin_ids,
        spec, test.context.dataset_fingerprint, coordinates[:, :, None])
    with pytest.raises(ValueError):
        make_baseline('persistence', {}).fit(train).predict(context, test.targets.grid)


def test_prediction_snapshot_excludes_subclass_realized_target_state():
    train, test = fixture()

    class ExtendedGrid(FutureGrid):
        pass

    grid = ExtendedGrid(**declared(test.targets.grid, FutureGrid))
    vars(grid)['values'] = test.targets.values
    prediction = make_baseline('persistence', {}).fit(train).predict(test.context, grid)
    assert type(prediction.grid) is FutureGrid
    assert not hasattr(prediction.grid, 'values')
    assert not hasattr(prediction.grid, 'targets')
    assert all(field.name not in ('values', 'targets', 'mask') for field in fields(FutureGrid))


def test_late_masked_cells_are_ineligible_without_clipping_or_filling():
    train, test = fixture()
    mask, values, available = test.context.mask.copy(), test.context.values.copy(), test.context.availability_ns.copy()
    mask[:, -1, 0] = False
    values[:, -1, 0] = 1e100
    available[:, -1, 0] = test.context.issue_times_ns + NS
    context = replace(test.context, mask=mask, values=values, availability_ns=available)
    prediction = make_baseline('persistence', {}).fit(train).predict(context, test.targets.grid)
    np.testing.assert_array_equal(prediction.values[:, 0, 0], [9., 10.])
    np.testing.assert_array_equal(context.values[:, -1, 0], [1e100, 1e100])


def test_model_consumes_a_detached_context_snapshot(monkeypatch):
    train, test = fixture()
    context = deepcopy(test.context)
    model = make_baseline('persistence', {}).fit(train)
    actual_predict = model._predict

    def mutate_caller_then_predict(snapshot, grid):
        # Real prediction must use the snapshot captured before caller mutation.
        context.values[:, -1, 0] = 999.
        context.ends_ns[:, -1] += NS
        return actual_predict(snapshot, grid)

    monkeypatch.setattr(model, '_predict', mutate_caller_then_predict)
    prediction = model.predict(context, test.targets.grid)
    np.testing.assert_array_equal(prediction.values[:, 0, 0], [10., 11.])


class RetrospectiveLike(str):
    def __eq__(self, other):
        return other == 'retrospective_bin_end'

    __hash__ = str.__hash__


class AlwaysUnequal(str):
    def __eq__(self, other):
        return False

    __hash__ = str.__hash__


class LogLike(str):
    def __eq__(self, other):
        return other == 'log10'

    __hash__ = str.__hash__


@pytest.mark.parametrize('name,parameters,want', MODELS)
def test_string_enum_hook_cannot_hide_unknown_operational_delivery(name, parameters, want):
    train, test = fixture()
    spec = ForecastSpec(**(declared(train.spec, ForecastSpec) |
                           {'availability_mode': RetrospectiveLike('operational')}))
    context, grid = copy(test.context), copy(test.targets.grid)
    vars(context).update(spec=spec, availability_ns=None)
    vars(grid)['spec'] = spec
    with pytest.raises(ValueError):
        make_baseline(name, parameters).fit(train).predict(context, grid)


@pytest.mark.parametrize('name,parameters,want', MODELS)
def test_string_equality_hook_cannot_hide_duplicate_origins(name, parameters, want):
    train, test = fixture()
    context, grid = copy(test.context), copy(test.targets.grid)
    ids = (AlwaysUnequal('same'), AlwaysUnequal('same'))
    vars(context)['origin_ids'] = vars(grid)['origin_ids'] = ids
    with pytest.raises(ValueError):
        make_baseline(name, parameters).fit(train).predict(context, grid)


@pytest.mark.parametrize('name,parameters,want', MODELS)
def test_nested_transform_hook_cannot_change_fitting_data_under_same_identity(name, parameters, want):
    train, _ = fixture()
    plain = replace(train.spec, feature_reference=(1.,), target_reference=(1.,))
    hooked = ForecastSpec(**(declared(plain, ForecastSpec) |
                             {'transform': LogLike('identity')}))
    variants = [replace(train, context=replace(train.context, spec=spec),
                targets=replace(train.targets, grid=replace(train.targets.grid, spec=spec)))
                for spec in (plain, hooked)]
    models = [make_baseline(name, parameters).fit(t) for t in variants]
    # Same recorded primitive semantics must result in the same numerical fit.
    assert variants[0].fingerprint == variants[1].fingerprint
    assert models[0].parameters == models[1].parameters
    assert type(variants[1].spec.transform) is str


def test_nested_string_conversion_hook_cannot_rewrite_declared_units():
    train, test = fixture()

    class MisleadingString(str):
        def __str__(self):
            return 'different_unit'

    spec = replace(train.spec, target_units=(MisleadingString('u'),))
    prediction = make_baseline('persistence', {}).fit(train).predict(
        replace(test.context, spec=spec), replace(test.targets.grid, spec=spec))
    assert prediction.grid.spec.target_units == ('u',)
    assert type(prediction.grid.spec.target_units[0]) is str
