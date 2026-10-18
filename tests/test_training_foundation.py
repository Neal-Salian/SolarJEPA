"""Bounded optimizer, train-only raw normalization and safe checkpoint boundaries."""
from copy import deepcopy
from dataclasses import replace
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.evaluation import evaluate_trajectory

NS = 1_000_000_000


def api():
    return importlib.import_module('solar_flare_jepa.training')


def fixture(stride=2, missing=True, future_multiplier=1.):
    ticks = np.arange(48, dtype=np.int64)
    values = np.column_stack((10. ** (-7 + ticks / 10.), 10. ** (-6 + ticks / 20.)))
    values[24:] *= future_multiplier
    fm, tm = np.ones_like(values, bool), np.ones_like(values, bool)
    if missing:
        fm[2, 0], tm[6, 1] = False, False
    data = TimeSeriesDataset('training_fixture', 'synthetic_fixture', ticks * NS,
        (ticks + 1) * NS, values, fm, values, tm, ('a', 'b'), ('a', 'b'),
        ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), 1,
        availability_policy='bin_end_earliest')
    spec = ForecastSpec(1, 3, 2, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'),
        ('W/m2', 'W/m2'), stride_steps=stride, transform='log10',
        feature_reference=(1., 1.), target_reference=(1., 1.),
        availability_mode='retrospective_bin_end', eligibility_policy='masked')
    windows = {name: build_partition_windows(data, spec, TemporalPartition(name, start * NS, end * NS))
               for name, start, end in [('train', 0, 24), ('validation', 24, 36), ('test', 36, 48)]}
    return data, windows


def fitted(**changes):
    module = api()
    _, windows = fixture()
    cfg = module.TrainingConfig(epochs=2, batch_size=2, max_train_batches=2,
                               max_validation_batches=2, max_eval_origins=4, **changes)
    model = module.fit_smoke(windows['train'].training_slice, windows['validation'],
                            config=cfg, source_identity='source-fixture', split_identity='all-splits-fixture')
    return module, model, windows


def test_normalization_fits_unique_raw_support_independent_of_window_stride_and_holdout():
    module = api()
    _, dense = fixture(stride=2)
    _, sparse = fixture(stride=4, future_multiplier=1e50)
    one, two = [module.Normalization.fit(w['train'].training_slice) for w in (dense, sparse)]
    for field in ('feature_mean', 'feature_scale', 'target_mean', 'target_scale', 'feature_counts', 'target_counts'):
        assert getattr(one, field) == getattr(two, field)
    # Log values for channel a are -7 + i/10, with raw tick 2 explicitly invalid.
    assert one.feature_counts == (23, 24)
    assert one.target_counts == (24, 23)
    assert one.feature_mean[0] == pytest.approx((-7 * 24 + sum(range(24)) / 10. - (-6.8)) / 23)
    assert one.target_mean[0] == pytest.approx(-5.85)


def test_tensor_masks_preserve_raw_nan_and_fill_only_normalized_tensor_cells():
    module = api()
    _, windows = fixture()
    train = windows['train'].training_slice
    normalization = module.Normalization.fit(train)
    batch = module.tensor_batch(windows['train'], normalization, [0, 1], device='cpu')
    assert tuple(batch.features.shape) == (2, 3, 2)
    assert tuple(batch.targets.shape) == (2, 2, 2)
    assert batch.feature_mask.dtype == batch.target_mask.dtype
    assert not bool(batch.feature_mask[0, 1, 0])
    assert float(batch.features[0, 1, 0]) == 0.
    assert np.isnan(train.context.values[0, 1, 0])
    assert np.isnan(train.raw_features[2, 0])
    np.testing.assert_array_equal(batch.target_mask.cpu().numpy(), windows['train'].targets.mask[:2])


def test_optimizer_updates_weights_and_only_validation_selects_best_checkpoint():
    _, model, _ = fitted()
    record = model.record
    assert record['optimizer_steps'] == 4
    assert record['initial_weights_fingerprint'] != record['final_training_weights_fingerprint']
    assert record['selection']['partition'] == 'validation'
    assert record['selection']['epoch'] in (1, 2)
    assert record['selection']['loss'] == min(x['validation_loss'] for x in record['history'])
    assert record['coverage']['train']['selected_count'] == 4
    assert record['coverage']['validation']['selected_count'] == 4
    assert record['coverage']['train']['eligible_count'] > 4


def test_checkpoint_reload_is_bitwise_deterministic_and_scores_native_units(tmp_path):
    module, model, windows = fitted()
    path = tmp_path / 'best.pt'
    model.save_checkpoint(path)
    restored = module.load_checkpoint(path, expected_identities=model.identities, device='cpu')
    before = model.predict(windows['test'].context, windows['test'].targets.grid)
    after = restored.predict(windows['test'].context, windows['test'].targets.grid)
    np.testing.assert_array_equal(before.values, after.values)
    assert before.values.shape == (4, 2, 2)
    assert (before.values > 0).all()
    assert before.model_id == 'TRAINING_INFRASTRUCTURE_SMOKE_TEST'
    assert before.point_interpretation == 'inverse_transformed_point'
    score = evaluate_trajectory(windows['test'].targets, after, windows['train'].training_slice)
    assert score['target_units'] == ['W/m2', 'W/m2']
    assert score['coverage']['valid_count'] == 16
    assert restored.record == model.record
    assert restored.optimizer_state
    with pytest.raises(FileExistsError):
        model.save_checkpoint(path)


@pytest.mark.parametrize('key', ['spec', 'dataset', 'source', 'split', 'training', 'normalization', 'training_config'])
def test_checkpoint_rejects_each_changed_identity(tmp_path, key):
    module, model, _ = fitted()
    path = tmp_path / 'best.pt'
    model.save_checkpoint(path)
    wrong = dict(model.identities, **{key: 'changed'})
    with pytest.raises(ValueError, match='identity|identities'):
        module.load_checkpoint(path, expected_identities=wrong)


def test_checkpoint_rejects_nonfinite_weights(tmp_path):
    import torch
    module, model, _ = fitted()
    path = tmp_path / 'best.pt'
    model.save_checkpoint(path)
    payload = torch.load(path, weights_only=True)
    next(iter(payload['model_state'].values())).fill_(float('nan'))
    torch.save(payload, path)
    with pytest.raises(ValueError, match='[Nn]onfinite|weight'):
        module.load_checkpoint(path, expected_identities=model.identities)


@pytest.mark.parametrize('change', ['scientific_status', 'phase_e', 'test_selection',
                                  'empty_history', 'selection_loss', 'optimizer_steps'])
def test_checkpoint_rejects_inconsistent_scientific_and_monitoring_record(tmp_path, change):
    import torch
    module, model, _ = fitted()
    path = tmp_path/'best.pt'
    model.save_checkpoint(path)
    payload = torch.load(path, weights_only=True)
    record = payload['training_record']
    if change == 'scientific_status':
        record['scientific_status'] = 'SCIENTIFICALLY_VALIDATED'
    elif change == 'phase_e':
        record['phase_e'] = 'CLEARED_FOR_PHASE_E'
    elif change == 'test_selection':
        record['selection']['partition'] = 'test'
    elif change == 'empty_history':
        record['history'] = []
    elif change == 'selection_loss':
        record['selection']['loss'] += 1.
    else:
        record['optimizer_steps'] += 1
    torch.save(payload, path)
    with pytest.raises(ValueError, match='record|monitor|status|history|selection|steps'):
        module.load_checkpoint(path, expected_identities=model.identities)


def test_predictions_consume_causal_context_and_grid_without_future_labels():
    _, model, windows = fitted()
    window = windows['validation']
    one = model.predict(window.context, window.targets.grid)
    altered = replace(window.targets, values=window.targets.values * 1e50)
    two = model.predict(window.context, altered.grid)
    np.testing.assert_array_equal(one.values, two.values)
    # A false cell can carry arbitrary payload in a context; its tensor is zero
    # and its explicit false mask is retained. It cannot become an observation.
    train = windows['train']
    values = train.context.values.copy()
    values[~train.context.mask] = 1e100
    hidden = replace(train.context, values=values)
    np.testing.assert_array_equal(model.predict(train.context, train.targets.grid).values,
                                  model.predict(hidden, train.targets.grid).values)
    with pytest.raises(ValueError, match='identity'):
        model.predict(replace(window.context, dataset_fingerprint='wrong'), window.targets.grid)


def test_training_revalidates_copied_raw_window_consistency():
    module = api()
    _, windows = fixture()
    corrupt = deepcopy(windows['train'].training_slice)
    corrupt.context.values[0, 0, 0] *= 100
    with pytest.raises(ValueError, match='canonical|raw|consistent'):
        module.fit_smoke(corrupt, windows['validation'], config=module.TrainingConfig(),
                         source_identity='source', split_identity='split')


def test_nonpositive_valid_log_inputs_and_nonfinite_loss_are_rejected():
    module = api()
    _, windows = fixture()
    validation = windows['validation']
    values = validation.targets.values.copy()
    values[0, 0, 0] = 0.
    bad = replace(validation, targets=replace(validation.targets, values=values))
    with pytest.raises(ValueError, match='positive|log'):
        module.fit_smoke(windows['train'].training_slice, bad, config=module.TrainingConfig(),
                         source_identity='source', split_identity='split')
    import torch
    with pytest.raises(ValueError, match='[Nn]onfinite'):
        module.masked_mse(torch.tensor([float('inf')]), torch.tensor([0.]), torch.tensor([True]))
    with pytest.raises(ValueError, match='supervision|valid'):
        module.masked_mse(torch.tensor([0.]), torch.tensor([0.]), torch.tensor([False]))


def test_cpu_is_default_and_other_devices_require_explicit_supported_capability():
    module = api()
    assert str(module.resolve_device('cpu')) == 'cpu'
    with pytest.raises(ValueError, match='device|CPU|cpu|MPS'):
        module.resolve_device('cuda')
    import torch
    if not torch.backends.mps.is_available():
        with pytest.raises(ValueError, match='MPS|mps'):
            module.resolve_device('mps')


@pytest.mark.parametrize('change', [{'epochs': 0}, {'batch_size': True}, {'learning_rate': float('inf')},
                                  {'max_train_batches': 0}, {'seed': -1}, {'gradient_clip': 0}])
def test_training_configuration_rejects_unbounded_or_nonfinite_values(change):
    with pytest.raises(ValueError):
        api().TrainingConfig(**change)


def test_runner_publishes_verified_checkpoint_and_reproducible_bounded_native_scores(tmp_path):
    from test_experiment_runner import repository
    from solar_flare_jepa.experiments.provenance import verify_artifacts
    module = importlib.import_module('solar_flare_jepa.training.runner')
    root, path = repository(tmp_path)
    config = root / 'configs' / 'training' / 'smoke.json'
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(dict(seed=17, epochs=2, batch_size=2, max_train_batches=2,
        max_validation_batches=2, max_eval_origins=4, learning_rate=.001, gradient_clip=1.)))
    from test_experiment_runner import commit
    commit(root)
    one = module.run_training_smoke(path, root, training_config_path=config,
                                   output_dir='results/experiments/train-a')
    two = module.run_training_smoke(path, root, training_config_path=config,
                                   output_dir='results/experiments/train-b')
    verify_artifacts(one)
    result = json.loads((one / 'result.json').read_text())
    assert result['status'] == 'complete'
    assert result['model_id'] == 'TRAINING_INFRASTRUCTURE_SMOKE_TEST'
    assert result['reload_verification']['bitwise_equal'] is True
    assert result['coverage']['test']['selected_count'] == 4
    assert result['coverage']['test']['omitted_count'] > 0
    for filename in ('predictions.json', 'metrics.json', 'training_record.json', 'normalization.json'):
        assert (one / filename).read_bytes() == (two / filename).read_bytes()
    with pytest.raises(FileExistsError):
        module.run_training_smoke(path, root, training_config_path=config,
                                  output_dir='results/experiments/train-a')


def test_mps_request_fails_when_capability_is_unavailable(monkeypatch):
    import torch
    monkeypatch.setattr(torch.backends.mps, 'is_available', lambda: False)
    with pytest.raises(ValueError, match='MPS'):
        api().resolve_device('mps')


def test_monitoring_cannot_use_the_test_partition():
    module = api()
    _, windows = fixture()
    with pytest.raises(ValueError, match='validation'):
        module.fit_smoke(windows['train'].training_slice, windows['test'],
                         source_identity='source', split_identity='split')


def test_checkpoint_rejects_modified_normalization_record(tmp_path):
    import torch
    module, model, _ = fitted()
    path = tmp_path / 'best.pt'
    model.save_checkpoint(path)
    payload = torch.load(path, weights_only=True)
    payload['normalization']['feature_mean'][0] += 1
    torch.save(payload, path)
    with pytest.raises(ValueError, match='identity'):
        module.load_checkpoint(path, expected_identities=model.identities)
