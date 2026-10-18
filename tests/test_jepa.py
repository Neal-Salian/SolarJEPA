"""Temporal JEPA quantile forecaster: windows, causality, masks, EMA, selection, reload."""
from dataclasses import replace
import importlib
import inspect
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows

NS = 1_000_000_000
CONTEXT, HORIZON = 10, 5
GAP_TICK, BAD_FEATURE_TICK, BAD_TARGET_TICK = 50, 30, 80


def jepa():
    return importlib.import_module('solar_flare_jepa.training.jepa')


def fixture(heldout_multiplier=1., test_multiplier=1.):
    """Artificial positive two-channel series with a cadence gap and invalid cells."""
    ticks = np.array([t for t in range(200) if t != GAP_TICK], dtype=np.int64)
    rng = np.random.default_rng(3)
    logs = np.column_stack((-6 + .5 * np.sin(ticks / 7.) + .05 * rng.standard_normal(len(ticks)),
                            -5.5 + .4 * np.cos(ticks / 11.) + .05 * rng.standard_normal(len(ticks))))
    values = 10. ** logs
    values[ticks >= 120] *= heldout_multiplier
    values[ticks >= 160] *= test_multiplier
    fm, tm = np.ones_like(values, bool), np.ones_like(values, bool)
    fm[ticks == BAD_FEATURE_TICK, 0] = False
    tm[ticks == BAD_TARGET_TICK, 1] = False
    data = TimeSeriesDataset('jepa_fixture', 'synthetic_fixture', ticks * NS, (ticks + 1) * NS,
                             values, fm, values, tm, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'),
                             ('W/m2', 'W/m2'), 1, availability_policy='bin_end_earliest')
    spec = ForecastSpec(1, CONTEXT, HORIZON, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'), ('W/m2', 'W/m2'),
                        stride_steps=1, transform='log10', feature_reference=(1., 1.),
                        target_reference=(1., 1.), target_minimum=(0., 0.),
                        availability_mode='retrospective_bin_end', eligibility_policy='complete')
    return {name: build_partition_windows(data, spec, TemporalPartition(name, a * NS, b * NS))
            for name, a, b in [('train', 0, 120), ('validation', 120, 160), ('test', 160, 200)]}


def tiny(**changes):
    values = dict(patch_steps=5, width=16, depth=1, heads=2, predictor_depth=1, mlp_ratio=2,
                  head_hidden=32, pretrain_epochs=2, finetune_epochs=3, batch_size=16, threads=1,
                  patience=2, monitor_windows=64, seed=5)
    values.update(changes)
    return jepa().JepaConfig(**values)


def fit(windows=None, variant='jepa_finetune', **changes):
    windows = fixture() if windows is None else windows
    model = jepa().fit_forecaster(windows['train'].training_slice, windows['validation'],
                                  tiny(**changes), variant)
    return model, windows


@pytest.fixture(scope='module')
def fitted():
    return fit()


def spec_model(**changes):
    windows = fixture()
    return jepa().build_jepa_model(windows['train'].training_slice.spec, tiny(**changes)), windows


def test_package_import_does_not_import_torch():
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    code = 'import sys, solar_flare_jepa.training.jepa; assert "torch" not in sys.modules'
    subprocess.run([sys.executable, '-c', code], check=True, env=env)


def test_training_windows_equal_p1_complete_windows_and_never_span_gaps():
    module = jepa()
    windows = fixture()
    train = windows['train'].training_slice
    normalization = module.Normalization.fit(train)
    result = module.training_windows(train, normalization, stride=1)
    np.testing.assert_array_equal(result.issue_times_ns, train.context.issue_times_ns)
    features, mask, targets, target_mask = result.take(np.arange(len(result)))
    assert features.shape == (len(result), CONTEXT + HORIZON, 2) and features.dtype == np.float32
    assert targets.shape == (len(result), HORIZON, 2) and target_mask.all() and mask[:, :CONTEXT].all()
    expected = normalization.normalize(train.context.values, train.context.mask, 'feature')
    np.testing.assert_allclose(features[:, :CONTEXT], expected.astype(np.float32))
    expected = normalization.normalize(train.targets.values, train.targets.mask, 'target')
    np.testing.assert_allclose(targets, expected.astype(np.float32))
    starts = train.raw_starts_ns
    length = CONTEXT + HORIZON
    spans = starts[result.starts + length - 1] - starts[result.starts]
    assert (spans == (length - 1) * NS).all()
    for first in result.starts:
        covered = set(range(int(starts[first]) // NS, int(starts[first]) // NS + length))
        assert GAP_TICK not in covered
        assert BAD_FEATURE_TICK not in set(range(int(starts[first]) // NS, int(starts[first]) // NS + CONTEXT))
        assert BAD_TARGET_TICK not in set(range(int(starts[first]) // NS + CONTEXT, int(starts[first]) // NS + length))
    assert int(starts[result.starts[-1] + length - 1]) + NS <= train.partition_end_ns
    strided = module.training_windows(train, normalization, stride=3)
    assert set(strided.issue_times_ns) <= set(result.issue_times_ns)
    assert (((strided.issue_times_ns - starts[0]) // NS) % 3 == 0).all()
    capped = result.subsample(7)
    assert len(capped) == 7 and (np.diff(capped.starts) > 0).all()


def test_training_windows_use_only_training_rows():
    module = jepa()
    arrays = []
    for multiplier in (1., 1e30):
        train = fixture(heldout_multiplier=multiplier)['train'].training_slice
        result = module.training_windows(train, module.Normalization.fit(train))
        arrays.append(result.take(np.arange(len(result))))
    for one, two in zip(*arrays):
        np.testing.assert_array_equal(one, two)


def test_target_encoder_receives_no_gradient_and_is_ema_updated():
    import torch
    model, windows = spec_model()
    torch.manual_seed(0)
    x = torch.randn(4, CONTEXT + HORIZON, 2)
    mask = torch.ones_like(x, dtype=torch.bool)
    loss, _ = model.jepa_loss(x, mask)
    loss.backward()
    assert all(p.grad is None and not p.requires_grad for p in model.target_encoder.parameters())
    assert all(p.grad is not None for p in model.encoder.parameters())
    optimizer = torch.optim.SGD(model.encoder.parameters(), lr=1.)
    optimizer.step()
    before = [p.detach().clone() for p in model.target_encoder.parameters()]
    online = [p.detach().clone() for p in model.encoder.parameters()]
    assert any(not torch.equal(a, b) for a, b in zip(before, online))
    model.update_target(.75)
    for old, new, current in zip(before, online, model.target_encoder.parameters()):
        torch.testing.assert_close(current, .75 * old + .25 * new)


def test_forecast_is_context_only_and_mask_distinguishes_missing_from_training_mean():
    import torch
    model, _ = spec_model()
    model.eval()
    zeros = torch.zeros(1, CONTEXT, 2)
    observed = torch.ones(1, CONTEXT, 2, dtype=torch.bool)
    missing = observed.clone()
    missing[0, 3, 0] = False
    with torch.no_grad():
        assert not torch.equal(model.forecast(zeros, observed), model.forecast(zeros, missing))
        with pytest.raises(ValueError, match='context'):
            model.forecast(torch.zeros(1, CONTEXT + HORIZON, 2), torch.ones(1, CONTEXT + HORIZON, 2, dtype=torch.bool))


def test_prediction_shapes_monotone_quantiles_and_native_units(fitted):
    from solar_flare_jepa.evaluation import evaluate_trajectory
    model, windows = fitted
    window = windows['test']
    prediction = model.predict(window.context, window.targets.grid)
    n = len(window.context.origin_ids)
    assert prediction.quantiles.shape == (n, HORIZON, 2, 5)
    assert prediction.values.shape == (n, HORIZON, 2)
    assert prediction.quantile_levels == (.05, .25, .5, .75, .95)
    assert (np.diff(prediction.quantiles, axis=-1) >= 0).all() and (prediction.quantiles > 0).all()
    np.testing.assert_array_equal(prediction.values, prediction.quantiles[..., 2])
    assert prediction.model_id == 'jepa_finetune'
    assert prediction.point_interpretation == 'inverse_transformed_point'
    score = evaluate_trajectory(window.targets, prediction, windows['train'].training_slice)
    assert score['target_units'] == ['W/m2', 'W/m2']


def test_prediction_is_causal_and_never_uses_target_encoder(fitted):
    import torch
    model, windows = fitted
    assert list(inspect.signature(model.predict).parameters) == ['context', 'future_grid']
    window = windows['validation']
    one = model.predict(window.context, window.targets.grid)
    altered = replace(window.targets, values=window.targets.values * 1e30)
    np.testing.assert_array_equal(one.quantiles, model.predict(window.context, altered.grid).quantiles)
    values = window.context.values.copy()
    mask = window.context.mask.copy()
    mask[0, 0, 0] = False
    values[0, 0, 0] = np.nan
    masked = replace(window.context, values=values, mask=mask)
    payload = values.copy()
    payload[~mask] = 1e100
    np.testing.assert_array_equal(model.predict(masked, window.targets.grid).quantiles,
                                  model.predict(replace(masked, values=payload), window.targets.grid).quantiles)
    saved = [p.detach().clone() for p in model._model.target_encoder.parameters()]
    with torch.no_grad():
        for parameter in model._model.target_encoder.parameters():
            parameter.fill_(float('nan'))
    try:
        np.testing.assert_array_equal(one.quantiles, model.predict(window.context, window.targets.grid).quantiles)
    finally:
        with torch.no_grad():
            for parameter, value in zip(model._model.target_encoder.parameters(), saved):
                parameter.copy_(value)


def test_selection_uses_validation_only_and_earliest_best_epoch(fitted):
    model, windows = fitted
    record = model.record
    history = record['finetune_history']
    losses = [entry['validation_pinball'] for entry in history]
    assert record['selection']['partition'] == 'validation'
    assert record['selection']['epoch'] == history[int(np.argmin(losses))]['epoch']
    assert record['selection']['loss'] == min(losses)
    assert len(record['pretrain_history']) == 2
    for entry in record['pretrain_history']:
        assert entry['target_latent_std'] > 0 and entry['target_effective_rank'] > 1
    assert record['parameters']['trainable_total'] == model.parameter_count
    assert record['train_windows']['eligible'] == len(windows['train'].context.origin_ids)
    assert 'test' not in inspect.signature(jepa().fit_forecaster).parameters
    with pytest.raises(ValueError, match='validation'):
        jepa().fit_forecaster(windows['train'].training_slice, windows['test'], tiny(), 'supervised')


def test_held_out_test_values_cannot_change_training(fitted):
    model, windows = fitted
    changed, changed_windows = fit(fixture(test_multiplier=1e20))
    validation, other = windows['validation'], changed_windows['validation']
    np.testing.assert_array_equal(model.predict(validation.context, validation.targets.grid).quantiles,
                                  changed.predict(other.context, other.targets.grid).quantiles)


def test_seeded_training_is_deterministic_and_seed_sensitive(fitted):
    model, windows = fitted
    window = windows['test']
    again, _ = fit(windows)
    np.testing.assert_array_equal(model.predict(window.context, window.targets.grid).quantiles,
                                  again.predict(window.context, window.targets.grid).quantiles)
    other = jepa().fit_forecaster(windows['train'].training_slice, windows['validation'], tiny(),
                                  'jepa_finetune', seed=6)
    assert other.config.seed == 6
    assert not np.array_equal(model.predict(window.context, window.targets.grid).quantiles,
                              other.predict(window.context, window.targets.grid).quantiles)


def test_save_load_round_trip_is_bitwise_identical(fitted, tmp_path):
    model, windows = fitted
    path = tmp_path / 'jepa.pt'
    model.save(path)
    restored = jepa().TrainedJepa.load(path)
    window = windows['test']
    before = model.predict(window.context, window.targets.grid)
    after = restored.predict(window.context, window.targets.grid)
    np.testing.assert_array_equal(before.quantiles, after.quantiles)
    assert restored.record == model.record and restored.model_id == model.model_id
    with pytest.raises(FileExistsError):
        model.save(path)
    import torch
    payload = torch.load(path, weights_only=True)
    next(iter(payload['model_state'].values())).add_(1.)
    torch.save(payload, path)
    with pytest.raises(ValueError, match='weight'):
        jepa().TrainedJepa.load(path)


def test_frozen_variant_keeps_pretrained_encoder_and_supervised_has_no_pretraining():
    from solar_flare_jepa.training.core import _cpu_state, _weights_fingerprint
    windows = fixture()
    frozen, _ = fit(windows, 'jepa_frozen')
    record = frozen.record
    assert frozen.model_id == 'jepa_frozen'
    assert _weights_fingerprint(_cpu_state(frozen._model.encoder.state_dict())) == record['pre_finetune_weights']['encoder']
    assert _weights_fingerprint(_cpu_state(frozen._model.predictor.state_dict())) == record['pre_finetune_weights']['predictor']
    supervised, _ = fit(windows, 'supervised')
    assert supervised.model_id == 'supervised_transformer'
    assert supervised.record['pretrain_history'] == []
    assert supervised.parameter_count == frozen.parameter_count
    window = windows['test']
    assert supervised.predict(window.context, window.targets.grid).model_id == 'supervised_transformer'


def test_block_masking_and_joint_latent_finetuning_run():
    model, windows = fit(context_block_mask=True, context_mask_patches=1, jepa_weight_during_finetune=.5,
                         max_train_windows=20)
    record = model.record
    assert record['effective_jepa_weight'] == .5
    assert record['train_windows']['used'] == 20
    assert all(np.isfinite(e['train_jepa_loss']) for e in record['pretrain_history'])


@pytest.mark.parametrize('change', [{'width': 15}, {'quantiles': (.1, .9)}, {'quantiles': (.5, .25)},
                                    {'batch_size': 0}, {'lr': float('nan')}, {'ema_start': 1., 'ema_end': .99},
                                    {'max_train_windows': 0}, {'threads': True}, {'jepa_loss': 'l2'}])
def test_config_rejects_unbounded_values(change):
    with pytest.raises(ValueError):
        tiny(**change)


def test_patch_geometry_must_divide_context_and_horizon():
    windows = fixture()
    with pytest.raises(ValueError, match='divisible'):
        jepa().build_jepa_model(windows['train'].training_slice.spec, tiny(patch_steps=3))
