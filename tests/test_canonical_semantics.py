"""N1 regressions: declared, validated, hashed and consumed semantics agree."""
from copy import copy, deepcopy
from types import MappingProxyType
from dataclasses import fields, replace
from enum import Enum, IntEnum, StrEnum
import json
from pathlib import Path
import pickle

import numpy as np
import pytest

from solar_flare_jepa.evaluation.events import evaluate_events
from solar_flare_jepa.experiments.config import config_fingerprint, validate_config
from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, FutureGrid, TimeSeriesDataset,
)
from solar_flare_jepa.forecasting.splitting import EventGroup, TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows

NS = 1_000_000_000
MODELS = [
    ('persistence', {}), ('training_mean', {}),
    ('trailing_mean', {'lookback_steps': 2}), ('drift', {'lookback_steps': 2}),
    ('ar1', {}), ('direct_ridge', {'lag_steps': 1, 'alpha': .1}),
]
ROUTES = ('copy', 'deepcopy', 'pickle', 'subclass', 'new')


class NumericCategory(int):
    def __new__(cls, value=0, meaning='identity'):
        instance = int.__new__(cls, value)
        instance.meaning = meaning
        return instance

    def __eq__(self, other):
        return other == self.meaning if isinstance(other, str) else int.__eq__(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = int.__hash__


class NativeEnum(IntEnum):
    VALUE = 0

    def __eq__(self, other):
        return other == 'identity' if isinstance(other, str) else int.__eq__(self, other)

    __hash__ = int.__hash__


class LogEnum(IntEnum):
    VALUE = 0

    def __eq__(self, other):
        return other == 'log10' if isinstance(other, str) else int.__eq__(self, other)

    __hash__ = int.__hash__


class ObjectCategory:
    def __init__(self, meaning):
        self.value = meaning
        self.name = meaning.upper()

    def __eq__(self, other):
        return other == self.value


class PlainEnum(Enum):
    VALUE = 'identity'


class StringCategory(str):
    def __new__(cls, value, meaning=None):
        instance = str.__new__(cls, value)
        instance.state = {'meaning': value if meaning is None else meaning,
                          'nested': [dict(items={'original'}, array=np.array([1.]))]}
        return instance

    def __eq__(self, other):
        return other == self.state['meaning']

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.state['meaning'])

    def __str__(self):
        return self.state['meaning']


class IdentityString(StrEnum):
    VALUE = 'identity'


class SelfCopyDict(dict):
    def __deepcopy__(self, memo):
        return self


class NumericFieldKey(int):
    """A JSON number whose mapping lookup impersonates a declared field."""
    def __new__(cls, meaning):
        instance = int.__new__(cls, 0)
        instance.meaning = meaning
        return instance

    def __eq__(self, other):
        return other == self.meaning if isinstance(other, str) else self is other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.meaning)

    def __lt__(self, other):
        return False if isinstance(other, str) else int.__lt__(self, other)

    def __gt__(self, other):
        return True if isinstance(other, str) else int.__gt__(self, other)


class NumericPath(NumericCategory):
    def __fspath__(self):
        return self.actual_path


class UncheckedSpec(ForecastSpec):
    def __post_init__(self):
        pass


def declarations(value, contract):
    return {field.name: getattr(value, field.name) for field in fields(contract)}


def fixture():
    starts = np.arange(12, dtype=np.int64) * NS
    values = np.array([2.,3.,5.,7.,11.,13.,17.,19.,23.,29.,31.,37.])[:, None]
    mask = np.ones_like(values, bool)
    data = TimeSeriesDataset('primes', 'synthetic_fixture', starts, starts + NS,
        values, mask, values, mask, ('x',), ('x',), ('u',), ('u',), 1,
        starts[:, None] + NS)
    spec = ForecastSpec(1, 2, 1, ('x',), ('x',), ('u',), ('u',),
                        feature_reference=(1.,), target_reference=(1.,))
    train = build_partition_windows(data, spec, TemporalPartition('train', 0, 8*NS))
    test = build_partition_windows(data, spec, TemporalPartition('test', 8*NS, 12*NS))
    return data, train.training_slice, test


def unchecked_spec(spec, route, field, category):
    if route == 'copy':
        changed = copy(spec)
    elif route == 'deepcopy':
        changed = deepcopy(spec)
    elif route == 'pickle':
        changed = pickle.loads(pickle.dumps(spec))
    elif route == 'subclass':
        changed = UncheckedSpec(**declarations(spec, ForecastSpec))
    else:
        changed = object.__new__(ForecastSpec)
        vars(changed).update(declarations(spec, ForecastSpec))
    vars(changed)[field] = category
    return changed


def unchecked_training(train, spec):
    changed = copy(train)
    context, targets, grid = copy(train.context), copy(train.targets), copy(train.targets.grid)
    vars(context)['spec'] = vars(grid)['spec'] = spec
    vars(targets)['grid'] = grid
    vars(changed).update(context=context, targets=targets)
    return changed


@pytest.mark.parametrize('field,meaning', [
    ('transform', 'identity'), ('availability_mode', 'operational'),
    ('eligibility_policy', 'complete'),
])
@pytest.mark.parametrize('kind', ['numeric', 'object', 'integer', 'boolean', 'unknown_string'])
def test_spec_rejects_noncanonical_categories_before_equality(field, meaning, kind):
    _, train, _ = fixture()
    value = {'numeric': NumericCategory(0, meaning), 'object': ObjectCategory(meaning),
             'integer': 0, 'boolean': True,
             'unknown_string': StringCategory('UNSUPPORTED', meaning)}[kind]
    with pytest.raises(ValueError):
        replace(train.spec, **{field: value})


@pytest.mark.parametrize('category', [NativeEnum.VALUE, LogEnum.VALUE, PlainEnum.VALUE])
def test_enum_objects_are_not_guessed_from_value_or_name(category):
    _, train, _ = fixture()
    with pytest.raises(ValueError):
        replace(train.spec, transform=category)


@pytest.mark.parametrize('name,parameters', MODELS)
@pytest.mark.parametrize('route', ROUTES)
def test_every_fit_rejects_numeric_semantics_before_model_consumption(name, parameters, route, monkeypatch):
    _, train, _ = fixture()
    spec = unchecked_spec(train.spec, route, 'transform', NumericCategory(0, 'log10'))
    corrupt = unchecked_training(train, spec)
    model = make_baseline(name, parameters)
    consumed = []
    actual = model._fit

    def observe(snapshot):
        consumed.append(snapshot)
        return actual(snapshot)

    monkeypatch.setattr(model, '_fit', observe)
    with pytest.raises(ValueError):
        model.fit(corrupt)
    assert not consumed


@pytest.mark.parametrize('name,parameters', MODELS)
@pytest.mark.parametrize('route', ROUTES)
def test_every_prediction_rejects_numeric_availability_before_consumption(name, parameters, route, monkeypatch):
    _, train, test = fixture()
    spec = unchecked_spec(train.spec, route, 'availability_mode',
                          NumericCategory(0, 'retrospective_bin_end'))
    context, grid = copy(test.context), copy(test.targets.grid)
    vars(context).update(spec=spec, availability_ns=None)
    vars(grid)['spec'] = spec
    operational = unchecked_spec(train.spec, route, 'availability_mode',
                                  NumericCategory(0, 'operational'))
    model = make_baseline(name, parameters)
    consumed = []
    actual = model._predict

    def observe(snapshot, future):
        consumed.append(snapshot)
        return actual(snapshot, future)

    monkeypatch.setattr(model, '_predict', observe)
    with pytest.raises(ValueError):
        model.fit(unchecked_training(train, operational))
        model.predict(context, grid)
    assert not consumed


@pytest.mark.parametrize('name,parameters', [('training_mean', {}),
                                          ('direct_ridge', {'lag_steps': 1, 'alpha': .1})])
def test_same_numeric_value_cannot_select_different_fitting_semantics(name, parameters):
    _, train, _ = fixture()
    for category in (NativeEnum.VALUE, LogEnum.VALUE):
        spec = unchecked_spec(train.spec, 'new', 'transform', category)
        with pytest.raises(ValueError):
            make_baseline(name, parameters).fit(unchecked_training(train, spec))


@pytest.mark.parametrize('name,parameters', MODELS)
def test_legitimate_string_forms_share_actual_fit_semantics_and_identity(name, parameters):
    _, train, test = fixture()
    expected = make_baseline(name, parameters).fit(train)
    for token in (np.str_('identity'), IdentityString.VALUE, StringCategory('identity', 'log10')):
        spec = replace(train.spec, transform=token)
        changed = replace(train, context=replace(train.context, spec=spec),
                          targets=replace(train.targets, grid=replace(train.targets.grid, spec=spec)))
        model = make_baseline(name, parameters).fit(changed)
        assert type(spec.transform) is str
        assert spec.fingerprint == train.spec.fingerprint
        assert changed.fingerprint == train.fingerprint
        assert model.parameters == expected.parameters
        np.testing.assert_array_equal(model.predict(test.context, test.targets.grid).values,
                                      expected.predict(test.context, test.targets.grid).values)


@pytest.mark.parametrize('field,meaning', [
    ('transform', 'identity'), ('availability_mode', 'operational'),
    ('eligibility_policy', 'complete'),
])
def test_snapshot_discards_mutable_string_subtype_state(field, meaning):
    _, train, _ = fixture()
    token = StringCategory(meaning)
    spec = replace(train.spec, **{field: token})
    before = spec.fingerprint
    token.state['meaning'] = 'UNSUPPORTED'
    token.state['nested'][0]['items'].add('changed')
    token.state['nested'][0]['array'][0] = 999.
    token.state['nested'].append(['changed'])
    assert type(getattr(spec, field)) is str
    assert getattr(spec, field) == meaning
    assert spec.fingerprint == before


@pytest.mark.parametrize('name,parameters', MODELS)
def test_caller_metadata_mutation_after_prediction_capture_cannot_change_behavior(name, parameters, monkeypatch):
    _, train, test = fixture()
    token = StringCategory('identity')
    spec = replace(train.spec, transform=token)
    changed = replace(train, context=replace(train.context, spec=spec),
                      targets=replace(train.targets, grid=replace(train.targets.grid, spec=spec)))
    model = make_baseline(name, parameters).fit(changed)
    context = replace(test.context, spec=spec)
    grid = replace(test.targets.grid, spec=spec)
    before = model.predict(context, grid).values
    record = model.parameters
    actual = model._predict

    def mutate_caller(snapshot, future):
        assert type(snapshot.spec.transform) is str
        assert snapshot.spec.transform is not token
        token.state['meaning'] = 'log10'
        token.state['nested'][0]['array'][0] = -999.
        return actual(snapshot, future)

    monkeypatch.setattr(model, '_predict', mutate_caller)
    np.testing.assert_array_equal(model.predict(context, grid).values, before)
    assert model.parameters == record
    assert type(spec.transform) is str


@pytest.mark.parametrize('field,meaning', [('role', 'synthetic_fixture'),
                                          ('availability_policy', 'explicit')])
def test_dataset_categories_require_declared_string_semantics(field, meaning):
    data, _, _ = fixture()
    with pytest.raises(ValueError):
        replace(data, **{field: NumericCategory(0, meaning)})
    with pytest.raises(ValueError):
        replace(data, **{field: StringCategory('UNKNOWN', meaning)})


def test_partition_prediction_and_training_categories_reject_numeric_aliases():
    _, train, test = fixture()
    with pytest.raises(ValueError):
        TemporalPartition(NumericCategory(0, 'train'), 0, 8*NS)
    with pytest.raises(ValueError):
        replace(train, partition_name=NumericCategory(0, 'train'))
    with pytest.raises(ValueError):
        ForecastPrediction(np.ones_like(test.targets.values), test.targets.grid, 'toy',
                           point_interpretation=NumericCategory(0, 'native_point'))


@pytest.mark.parametrize('field', ['name', 'time_policy', 'quality_policy'])
def test_dataset_descriptive_labels_are_detached_plain_strings(field):
    data, _, _ = fixture()
    token = StringCategory(getattr(data, field))
    changed = replace(data, **{field: token})
    before = changed.fingerprint
    token.state['meaning'] = 'changed'
    assert type(getattr(changed, field)) is str
    assert changed.fingerprint == before


def test_names_units_and_origins_use_declared_text_before_uniqueness():
    _, train, test = fixture()
    for field in ('feature_names', 'target_names'):
        prefix = field.split('_')[0]
        changes = {field: (StringCategory('same', 'first'), StringCategory('same', 'second')),
                   prefix + '_units': ('u', 'u'), prefix + '_reference': (1., 1.)}
        if prefix == 'target':
            changes['target_minimum'] = (None, None)
        with pytest.raises(ValueError):
            replace(train.spec, **changes)
    with pytest.raises(ValueError):
        replace(test.context, origin_ids=(StringCategory('same', 'first'),
                                        StringCategory('same', 'second')))
    spec = replace(train.spec, feature_units=[StringCategory('u', 'different')],
                   target_units=[StringCategory('u', 'different')])
    assert type(spec.feature_units[0]) is str
    assert type(spec.target_units[0]) is str
    assert spec.fingerprint == train.spec.fingerprint


def test_identity_group_and_prediction_labels_do_not_retain_subtypes():
    _, train, test = fixture()
    group = EventGroup(StringCategory('group'), 0, NS, NS)
    context = replace(test.context, dataset_fingerprint=StringCategory(test.context.dataset_fingerprint))
    changed = replace(train, split_fingerprint=StringCategory(train.split_fingerprint))
    prediction = ForecastPrediction(np.ones_like(test.targets.values), test.targets.grid, StringCategory('toy'))
    assert type(group.group_id) is str
    assert type(context.dataset_fingerprint) is str
    assert type(changed.split_fingerprint) is str
    assert type(prediction.model_id) is str


def test_event_labels_and_origin_uniqueness_use_plain_strings():
    token = StringCategory('explicit_test_definition')
    report = evaluate_events([0.,1.], [True,True], [True,True],
                             [StringCategory('a'), StringCategory('b')], token, 1, decisions=[0.,1.])
    token.state['meaning'] = 'changed'
    assert type(report['event_definition']) is str
    assert all(type(x) is str for x in report['origin_ids'])
    with pytest.raises(ValueError):
        evaluate_events([0.,1.], [True,True], [True,True],
                        [StringCategory('same', 'first'), StringCategory('same', 'second')],
                        'explicit', 1, decisions=[0.,1.])


def config():
    return json.loads(Path('configs/experiments/p1_synthetic.json').read_text())


@pytest.mark.parametrize('location,meaning', [('dataset', 'synthetic_fixture'),
                                            ('split', 'train'), ('model', 'persistence')])
@pytest.mark.parametrize('kind', ['numeric', 'unknown_string'])
def test_config_categories_cannot_disagree_with_serialized_semantics(location, meaning, kind):
    cfg = config()
    token = NumericCategory(0, meaning) if kind == 'numeric' else StringCategory('UNKNOWN', meaning)
    if location == 'dataset':
        cfg['dataset']['kind'] = token
    elif location == 'split':
        cfg['splits'][0]['name'] = token
    else:
        cfg['baselines'][0]['name'] = token
    with pytest.raises(ValueError):
        validate_config(cfg)


@pytest.mark.parametrize('name,parameters', MODELS)
def test_factory_never_looks_up_a_subtype_equality_alias(name, parameters):
    with pytest.raises(ValueError):
        make_baseline(StringCategory('UNKNOWN', name), parameters)
    assert make_baseline(StringCategory(name, 'UNKNOWN'), parameters).name == name


def test_config_snapshot_detaches_nested_containers_even_if_deepcopy_returns_caller():
    raw = config()
    raw['dataset'] = SelfCopyDict(raw['dataset'])
    raw['forecast']['feature_names'] = [StringCategory(x) for x in raw['forecast']['feature_names']]
    caller = SelfCopyDict(raw)
    encoded = json.dumps(caller)
    resolved = validate_config(caller)
    before = config_fingerprint(resolved)
    assert resolved is not caller
    assert resolved['dataset'] is not caller['dataset']
    assert json.dumps(caller) == encoded
    caller['dataset']['fixture_seed'] += 1
    caller['seeds'].append(999)
    caller['forecast']['feature_names'][0].state['meaning'] = 'changed'
    caller['metrics']['lead_weights'][0] = 99.
    assert config_fingerprint(resolved) == before
    assert type(resolved['forecast']['feature_names'][0]) is str


def test_config_equivalent_string_serializations_have_same_detached_identity():
    cfg = config()
    expected = config_fingerprint(cfg)
    cfg['dataset']['kind'] = StringCategory('synthetic_fixture', 'goes_reference')
    cfg['baselines'][0]['name'] = StringCategory('persistence', 'UNKNOWN')
    cfg['splits'][0]['name'] = StringCategory('train', 'UNKNOWN')
    assert config_fingerprint(cfg) == expected


@pytest.mark.parametrize('field', ['seeds', 'splits', 'baselines'])
def test_canonicalization_does_not_weaken_explicit_config_container_validation(field):
    cfg = config()
    cfg[field] = tuple(cfg[field])
    with pytest.raises(ValueError):
        validate_config(cfg)


@pytest.mark.parametrize('representation', ['text', 'bytes', 'bytearray'])
def test_supported_json_metadata_is_owned_and_nested_views_are_detached(representation):
    data, _, _ = fixture()
    original = {'nested': {'values': [1, {'labels': ['a']}]}}
    encoded = json.dumps(original)
    payload = {'text': encoded, 'bytes': encoded.encode(), 'bytearray': bytearray(encoded.encode())}[representation]
    changed = replace(data, metadata_json=payload)
    before = changed.fingerprint
    original['nested']['values'][1]['labels'].append('changed')
    if representation == 'bytearray':
        payload[:] = b'{}'
    view = changed.semantic_content()
    view['metadata']['nested']['values'][0] = 999
    assert type(changed.metadata_json) is str
    assert changed.fingerprint == before


@pytest.mark.parametrize('unsupported', [dict(nested=[]), ['x'], {'x'}, np.array([1.])])
def test_raw_python_metadata_containers_are_not_silently_coerced(unsupported):
    data, _, _ = fixture()
    with pytest.raises((ValueError, TypeError)):
        replace(data, metadata_json=unsupported)


def test_valid_transform_and_availability_semantics_have_different_effective_ids():
    _, train, test = fixture()
    log_spec = replace(train.spec, transform='log10')
    log_train = replace(train, context=replace(train.context, spec=log_spec),
                        targets=replace(train.targets, grid=replace(train.targets.grid, spec=log_spec)))
    assert log_train.fingerprint != train.fingerprint
    retro = replace(train.spec, availability_mode='retrospective_bin_end')
    assert retro.fingerprint != train.spec.fingerprint
    unknown = replace(test.context, spec=retro, availability_ns=None)
    for name, parameters in MODELS:
        with pytest.raises(ValueError):
            make_baseline(name, parameters).fit(train).predict(unknown, replace(test.targets.grid, spec=retro))
    means = [make_baseline('training_mean', {}).fit(t) for t in (train, log_train)]
    assert means[0].parameters['mean'] != means[1].parameters['mean']
    assert means[0].parameters['training_fingerprint'] != means[1].parameters['training_fingerprint']


@pytest.mark.parametrize('location', ['dataset', 'metrics'])
@pytest.mark.parametrize('swapped', [False, True])
@pytest.mark.parametrize('route', ['original', 'copy', 'deepcopy', 'pickle'])
def test_numeric_field_aliases_cannot_change_consumed_config_under_same_json(location, swapped, route):
    cfg = config()
    if location == 'dataset':
        for name in ('rows', 'fixture_seed'):
            del cfg['dataset'][name]
        first, second = ('fixture_seed', 'rows') if swapped else ('rows', 'fixture_seed')
        cfg['dataset'][NumericFieldKey(first)] = 1200
        cfg['dataset'][NumericFieldKey(second)] = 2400
    else:
        cfg['forecast']['horizon_steps'] = 2
        first, second = ('target_weights', 'lead_weights') if swapped else ('lead_weights', 'target_weights')
        cfg['metrics'] = {NumericFieldKey(first): [1, 0], NumericFieldKey(second): [0, 1]}
    cfg = {'original': lambda x: x, 'copy': copy, 'deepcopy': deepcopy,
           'pickle': lambda x: pickle.loads(pickle.dumps(x))}[route](cfg)
    with pytest.raises(ValueError):
        validate_config(cfg)
    with pytest.raises(ValueError):
        config_fingerprint(cfg)


@pytest.mark.parametrize('field', ['manifest', 'prepared_config', 'sidecar'])
@pytest.mark.parametrize('representation', ['numeric_path', 'object'])
def test_pinned_goes_paths_require_actual_strings_before_equality_or_path_use(field, representation):
    cfg = json.loads(Path('configs/experiments/p1_goes_reference.json').read_text())
    expected = cfg['dataset'][field]
    token = NumericPath(0, expected) if representation == 'numeric_path' else ObjectCategory(expected)
    token.actual_path = 'configs/another_file.json'
    cfg['dataset'][field] = token
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_config_mapping_keys_normalize_string_content_before_field_lookup():
    cfg = config()
    cfg['metrics'] = {StringCategory('lead_weights', 'target_weights'): cfg['metrics']['lead_weights'],
                      StringCategory('target_weights', 'lead_weights'): cfg['metrics']['target_weights']}
    resolved = validate_config(cfg)
    assert all(type(key) is str for key in resolved['metrics'])
    assert config_fingerprint(resolved) == config_fingerprint(config())


def test_duplicate_primitive_config_keys_are_rejected_before_fingerprinting():
    cfg = config()
    cfg['metrics'] = {StringCategory('lead_weights', 'lead_weights'): [1] * 5,
                      StringCategory('lead_weights', 'target_weights'): [1] * 2}
    with pytest.raises(ValueError):
        validate_config(cfg)


@pytest.mark.parametrize('route', ['original', 'copy', 'deepcopy', 'pickle'])
def test_factory_parameter_keys_cannot_redirect_constructor_binding(route):
    raw = {StringCategory('lag_steps', 'alpha'): 1,
           StringCategory('alpha', 'lag_steps'): 2}
    raw = {'original': lambda x: x, 'copy': copy, 'deepcopy': deepcopy,
           'pickle': lambda x: pickle.loads(pickle.dumps(x))}[route](raw)
    model = make_baseline('direct_ridge', raw)
    assert model.lag_steps == 1
    assert model.alpha == 2.
    _, train, test = fixture()
    model.fit(train)
    canonical = make_baseline('direct_ridge', {'lag_steps': 1, 'alpha': 2}).fit(train)
    assert model.parameters == canonical.parameters
    np.testing.assert_array_equal(model.predict(test.context, test.targets.grid).values,
                                  canonical.predict(test.context, test.targets.grid).values)


@pytest.mark.parametrize('name,field', [('trailing_mean', 'lookback_steps'),
                                       ('drift', 'lookback_steps'), ('direct_ridge', 'lag_steps')])
@pytest.mark.parametrize('route', ['original', 'copy', 'deepcopy', 'pickle'])
def test_factory_unknown_primitive_parameter_name_is_not_a_valid_equality_alias(name, field, route):
    raw = {StringCategory('UNKNOWN', field): 2}
    raw = {'original': lambda x: x, 'copy': copy, 'deepcopy': deepcopy,
           'pickle': lambda x: pickle.loads(pickle.dumps(x))}[route](raw)
    with pytest.raises(ValueError):
        make_baseline(name, raw)


@pytest.mark.parametrize('name,parameters', MODELS)
def test_factory_retains_supported_readonly_mapping_parameters(name, parameters):
    _, train, test = fixture()
    model = make_baseline(name, MappingProxyType(parameters)).fit(train)
    canonical = make_baseline(name, parameters).fit(train)
    assert model.parameters == canonical.parameters
    np.testing.assert_array_equal(model.predict(test.context, test.targets.grid).values,
                                  canonical.predict(test.context, test.targets.grid).values)
