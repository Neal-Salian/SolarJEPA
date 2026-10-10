"""V2 comparators: small causal TCN and full-context quantile-linear models."""
import importlib
import json

import numpy as np
import pytest

torch = pytest.importorskip('torch')

from test_jepa import fixture, tiny  # noqa: E402
from solar_flare_jepa.forecasting.contracts import ForecastSpec  # noqa: E402

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)


def comparators():
    return importlib.import_module('solar_flare_jepa.training.comparators')


def controlled():
    return importlib.import_module('solar_flare_jepa.training.controlled')


def tcn_config(**changes):
    values = dict(width=8, kernel_size=3, dilations=(1, 2), dropout=0.0, seed=5, threads=1, batch_size=16,
                  lr=1e-3, weight_decay=1e-4, gradient_clip=1.0, quantiles=LEVELS, max_train_windows=None)
    values.update(changes)
    return comparators().TcnConfig(**values)


def comparator_schedule(**changes):
    values = dict(downstream_epochs=3, early_stopping_patience=None, train_loss='dex_pinball_equal_channel_v2',
                  selection_metric='dex_pinball_equal_channel_v2', diagnostic_metrics=('normalized_pinball_v1',))
    values.update(changes)
    return comparators().ComparatorSchedule(**values)


def linear_config(**changes):
    values = dict(lambdas=(0.0, 0.01, 1.0), lr=0.01, batch_size=16, epochs=3, seed=5, threads=1,
                  gradient_clip=None, quantiles=LEVELS, max_train_windows=None,
                  train_loss='dex_pinball_equal_channel_v2', selection_metric='dex_pinball_equal_channel_v2')
    values.update(changes)
    return comparators().QuantileLinearConfig(**values)


def fit_tcn(windows=None, config=None, schedule=None):
    windows = fixture() if windows is None else windows
    return comparators().fit_tcn(windows['train'].training_slice, windows['validation'],
                                 config or tcn_config(), schedule or comparator_schedule())


def fit_linear(windows=None, config=None):
    windows = fixture() if windows is None else windows
    return comparators().fit_quantile_linear(windows['train'].training_slice, windows['validation'],
                                             config or linear_config())


@pytest.fixture(scope='module')
def fitted():
    windows = fixture()
    return fit_tcn(windows), fit_linear(windows), windows


def protocol_spec():
    return ForecastSpec(60, 120, 30, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'), ('W/m2', 'W/m2'),
                        transform='log10', feature_reference=(1., 1.), target_reference=(1., 1.))


# ---------------------------------------------------------------------------- TCN


def test_tcn_configuration_is_explicit_and_validated():
    module = comparators()
    with pytest.raises(TypeError):
        module.TcnConfig(width=8)
    for change in (dict(width=0), dict(kernel_size=1), dict(dilations=()), dict(dilations=(1, 0)),
                   dict(dropout=0.9), dict(quantiles=(0.1, 0.9)), dict(lr=0.), dict(seed=-1),
                   dict(gradient_clip=0.), dict(dilations=[1, True])):
        with pytest.raises(ValueError):
            tcn_config(**change)
    for change in (dict(downstream_epochs=0), dict(train_loss='mse'), dict(early_stopping_patience=0),
                   dict(diagnostic_metrics=('dex_pinball_equal_channel_v2',))):
        with pytest.raises(ValueError):
            comparator_schedule(**change)


def test_tcn_arithmetic_for_proposed_configuration():
    """Protocol arithmetic check only: these values are PROPOSED, not approved defaults."""
    module = comparators()
    config = tcn_config(width=32, dilations=(1, 2, 4, 8, 16, 32))
    model = module.build_tcn(protocol_spec(), config)
    assert sum(p.numel() for p in model.parameters()) == 44_620
    assert module.receptive_field(config) == 253


def test_tcn_convolutions_are_causal_within_the_context():
    module = comparators()
    spec = protocol_spec()
    torch.manual_seed(0)
    model = module.build_tcn(spec, tcn_config(width=8, dilations=(1, 2, 4))).eval()
    x = torch.randn(2, 120, 2)
    mask = torch.ones_like(x, dtype=torch.bool)
    with torch.no_grad():
        states = model.states(x, mask)
        later = x.clone()
        later[:, 80:] += 5.
        changed = model.states(later, mask)
    assert torch.equal(states[..., :80], changed[..., :80])
    assert not torch.equal(states[..., 80:], changed[..., 80:])


def test_tcn_shapes_order_budget_and_pairing(fitted):
    tcn, _, windows = fitted
    test = windows['test']
    prediction = tcn.predict(test.context, test.targets.grid)
    assert prediction.quantiles.shape == (len(test.context.origin_ids), 5, 2, 5)
    assert (np.diff(prediction.quantiles, axis=-1) >= 0).all() and prediction.model_id == 'v2_tcn_quantile'
    record = tcn.record
    phase = record['budget']['phases'][0]
    per = -(-record['train_windows']['used'] // 16)
    assert phase['epochs_executed'] == 3 and phase['optimizer_steps'] == 3 * per
    assert phase['parameter_updates']['tcn']['min'] == phase['parameter_updates']['head']['max'] == 3 * per
    assert record['parameters']['trainable_total'] == sum(p.numel() for p in tcn.model.parameters())
    # Same seed and window subset as the JEPA arms -> identical downstream window order.
    jepa = controlled().fit_controlled(
        windows['train'].training_slice, windows['validation'],
        controlled().ControlledConfig(tiny(), controlled().TrainingSchedule(
            arm='supervised', pretrain_epochs=0, warmup_epochs=0, downstream_epochs=3,
            early_stopping_patience=None, train_loss='dex_pinball_equal_channel_v2',
            selection_metric='dex_pinball_equal_channel_v2')))
    assert jepa.record['train_windows'] == record['train_windows']
    assert jepa.record['pairing']['downstream_order'] == record['pairing']['downstream_order']
    values = [e['metrics']['dex_pinball_equal_channel_v2'] for e in record['history']]
    assert record['selection']['epoch'] == int(np.argmin(values)) + 1


def test_tcn_rejects_invalid_inputs(fitted):
    tcn, _, windows = fitted
    with pytest.raises(ValueError):
        tcn.model.forecast(torch.zeros(2, 9, 2), torch.ones(2, 9, 2, dtype=torch.bool))
    with pytest.raises(ValueError):
        tcn.model.forecast(torch.zeros(2, 10, 2), torch.ones(2, 10, 2))
    with pytest.raises(ValueError):
        tcn.predict(windows['test'].targets.grid, windows['test'].context)


def test_tcn_determinism_heldout_invariance_and_reload(fitted, tmp_path):
    tcn, _, windows = fitted
    again = fit_tcn(fixture(test_multiplier=1e3))
    a, b = tcn.model.state_dict(), again.model.state_dict()
    assert all(torch.equal(a[k], b[k]) for k in a)
    tcn.save(tmp_path / 'tcn.pt')
    loaded = controlled().load_forecaster(tmp_path / 'tcn.pt')
    grid = windows['test'].targets.grid
    assert loaded.record == tcn.record
    assert np.array_equal(loaded.predict(windows['test'].context, grid).quantiles,
                          tcn.predict(windows['test'].context, grid).quantiles)
    other = fit_tcn(config=tcn_config(seed=6))
    assert other.record['pairing']['initial_state'] != tcn.record['pairing']['initial_state']


# ----------------------------------------------------------------- quantile linear


def test_linear_configuration_is_explicit_and_validated():
    module = comparators()
    with pytest.raises(TypeError):
        module.QuantileLinearConfig(lambdas=(0.,))
    for change in (dict(lambdas=()), dict(lambdas=(0.1, 0.1)), dict(lambdas=(-1.,)), dict(epochs=0),
                   dict(lr=-1.), dict(train_loss='l2'), dict(lambdas=(float('nan'),))):
        with pytest.raises(ValueError):
            linear_config(**change)


def test_linear_starts_at_zero_and_has_full_context_inputs():
    module = comparators()
    spec = protocol_spec()
    model = module.build_quantile_linear(spec, linear_config())
    assert model.linear.in_features == 120 * 2 and model.linear.out_features == 30 * 2 * 5
    assert not model.linear.weight.any() and not model.linear.bias.any()


def test_lambda_selection_prefers_smallest_lambda_on_ties():
    module = comparators()
    assert module._select_lambda({0.0: 0.4, 0.01: 0.3, 1.0: 0.3}) == 0.01
    assert module._select_lambda({1.0: 0.2, 0.1: 0.2}) == 0.1
    with pytest.raises(ValueError):
        module._select_lambda({0.1: float('nan')})


def test_linear_fit_records_every_lambda_with_identical_shuffle_streams(fitted):
    _, linear, _ = fitted
    record = linear.record
    candidates = record['lambda_candidates']
    assert [c['lambda'] for c in candidates] == [0.0, 0.01, 1.0]
    assert len({c['shuffle_order'] for c in candidates}) == 1
    values = {c['lambda']: c['validation_metric'] for c in candidates}
    assert record['selection']['lambda'] == comparators()._select_lambda(values)
    assert all(0. <= c['validation_raw_crossing_fraction'] <= 1. for c in candidates)
    per = -(-record['train_windows']['used'] // 16)
    assert all(c['optimizer_steps'] == 3 * per for c in candidates)
    assert record['budget']['totals']['optimizer_steps'] == 3 * 3 * per
    norms = [c['mean_squared_coefficient'] for c in candidates]
    assert norms[-1] < norms[0]


def test_linear_prediction_is_rearranged_ordered_and_reports_crossings(fitted, tmp_path):
    _, linear, windows = fitted
    test = windows['test']
    prediction = linear.predict(test.context, test.targets.grid)
    assert (np.diff(prediction.quantiles, axis=-1) >= 0).all() and prediction.model_id == 'v2_quantile_linear'
    assert 0. <= linear.last_crossing_fraction <= 1.
    linear.save(tmp_path / 'linear.pt')
    loaded = controlled().load_forecaster(tmp_path / 'linear.pt')
    assert np.array_equal(loaded.predict(test.context, test.targets.grid).quantiles, prediction.quantiles)
    assert json.loads(json.dumps(loaded.record)) == linear.record


def test_linear_rejects_incomplete_context_and_is_deterministic(fitted):
    _, linear, windows = fitted
    mask = torch.ones(2, 10, 2, dtype=torch.bool)
    mask[0, 3, 1] = False
    with pytest.raises(ValueError, match='complete context'):
        linear.model.forecast(torch.zeros(2, 10, 2), mask)
    again = fit_linear(fixture(test_multiplier=1e3))
    assert torch.equal(again.model.linear.weight, linear.model.linear.weight)
