"""Real CPU fitting and checkpoint boundaries for numerical sample sequences."""
from copy import deepcopy
import importlib
import importlib.util

import numpy as np
import pytest


def api():
    # Keep the first RED run a feature assertion, rather than a collection error.
    try:
        module = importlib.util.find_spec('solar_flare_jepa.provisional.neural')
    except ModuleNotFoundError:
        module = None
    assert module is not None, 'The isolated numerical neural adapter is missing'
    return importlib.import_module('solar_flare_jepa.provisional.neural')


def samples():
    x = np.array([[[1.], [2.], [3.]], [[2.], [3.], [4.]],
                  [[3.], [4.], [5.]], [[4.], [5.], [6.]],
                  [[5.], [6.], [7.]]])
    y = np.array([[[4.], [5.]], [[5.], [6.]], [[6.], [7.]],
                  [[7.], [8.]], [[8.], [9.]]])
    return [x, y, np.ones_like(x, bool), np.ones_like(y, bool),
            x + 10., y + 10., np.ones_like(x, bool), np.ones_like(y, bool)]


def fitted(arrays=None, **changes):
    kwargs = dict(mean=4., scale=2., identities={'source': 'source-a', 'training': 'train-a'},
                  config={'seed': 17, 'epochs': 3, 'batch_size': 2,
                          'learning_rate': .001, 'gradient_clip': 1.})
    kwargs.update(changes)
    return api().fit_neural(*(samples() if arrays is None else arrays), **kwargs)


def test_cpu_fit_consumes_all_origins_and_selects_validation_minimum():
    model = fitted()
    prediction = model.predict(samples()[0], samples()[2])
    assert prediction.shape == (5, 2, 1)
    assert np.isfinite(prediction).all()
    assert model.parameter_count == 14  # 3 values + 3 masks -> 2 leads, with bias.
    assert len(model.history) == 3
    best = min(model.history, key=lambda item: item['validation_loss'])
    assert model.selected_epoch == best['epoch']
    assert all(item['train_origins'] == item['validation_origins'] == 5 for item in model.history)
    assert all(item['optimizer_steps'] == 3 for item in model.history)


def test_repeated_cpu_training_and_checkpoint_reload_are_bitwise_equal(tmp_path):
    module = api()
    one, two = fitted(), fitted()
    before = one.predict(samples()[0], samples()[2])
    np.testing.assert_array_equal(before, two.predict(samples()[0], samples()[2]))
    assert one.history == two.history
    path = tmp_path / 'model.pt'
    one.save_checkpoint(path)
    loaded = module.load_checkpoint(path, expected_identities={'source': 'source-a', 'training': 'train-a'})
    np.testing.assert_array_equal(before, loaded.predict(samples()[0], samples()[2]))
    assert loaded.history == one.history
    assert loaded.selected_epoch == one.selected_epoch
    with pytest.raises(FileExistsError):
        one.save_checkpoint(path)


def test_false_feature_and_target_payloads_do_not_change_fitting_or_predictions():
    arrays = samples()
    arrays[2][0, 1, 0] = False
    arrays[3][1, 0, 0] = False
    arrays[6][0, 1, 0] = False
    arrays[7][1, 0, 0] = False
    original = deepcopy(arrays)
    for values, mask in ((arrays[0], arrays[2]), (arrays[1], arrays[3]),
                         (arrays[4], arrays[6]), (arrays[5], arrays[7])):
        values[~mask] = np.nan
    changed = deepcopy(arrays)
    for values, mask in ((changed[0], changed[2]), (changed[1], changed[3]),
                         (changed[4], changed[6]), (changed[5], changed[7])):
        values[~mask] = 1e200
    one, two = fitted(arrays), fitted(changed)
    np.testing.assert_array_equal(one.predict(arrays[0], arrays[2]), two.predict(changed[0], changed[2]))
    assert one.history == two.history
    # The training adapter never fills the caller's scientific arrays in place.
    assert np.isnan(arrays[0][0, 1, 0])
    assert np.array_equal(arrays[2], original[2])


def test_checkpoint_stores_selected_epoch_normalization_and_provisional_scope(tmp_path):
    import torch
    model = fitted()
    path = tmp_path / 'model.pt'
    model.save_checkpoint(path)
    payload = torch.load(path, map_location='cpu', weights_only=True)
    assert payload['normalization'] == {'mean': 4., 'scale': 2.}
    assert payload['context_steps'] == 3 and payload['horizon_steps'] == 2
    assert payload['scientific_label'] == 'EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED'
    assert payload['selected_epoch'] == model.selected_epoch
    assert payload['optimizer_state']['state']
    assert payload['versions']['torch'] == str(torch.__version__)
    # The selected model genuinely differs from its initialized state.
    assert payload['initial_weights_fingerprint'] != payload['weights_fingerprint']


@pytest.mark.parametrize('key', ['source', 'training'])
def test_checkpoint_rejects_changed_external_provenance(tmp_path, key):
    model = fitted()
    path = tmp_path / 'model.pt'
    model.save_checkpoint(path)
    wrong = {'source': 'source-a', 'training': 'train-a', key: 'changed'}
    with pytest.raises(ValueError, match='identit|provenance'):
        api().load_checkpoint(path, expected_identities=wrong)


@pytest.mark.parametrize('change', ['normalization', 'config', 'label', 'weights', 'nonfinite', 'history', 'optimizer'])
def test_checkpoint_rejects_tampered_internal_records(tmp_path, change):
    import torch
    model = fitted()
    path = tmp_path / 'model.pt'
    model.save_checkpoint(path)
    payload = torch.load(path, weights_only=True)
    if change == 'normalization':
        payload['normalization']['mean'] += 1.
    elif change == 'config':
        payload['config']['learning_rate'] *= 2.
    elif change == 'label':
        payload['scientific_label'] = 'SCIENTIFICALLY_VALIDATED'
    elif change == 'history':
        payload['history'][0]['validation_loss'] = -1.
    elif change == 'optimizer':
        next(iter(payload['optimizer_state']['state'].values()))['exp_avg'].fill_(float('inf'))
    else:
        value = next(iter(payload['model_state'].values()))
        value.fill_(float('nan')) if change == 'nonfinite' else value.add_(1.)
    torch.save(payload, path)
    with pytest.raises(ValueError):
        api().load_checkpoint(path, expected_identities={'source': 'source-a', 'training': 'train-a'})


@pytest.mark.parametrize('changes', [{'scale': 0.}, {'scale': float('nan')}, {'mean': float('inf')},
                                    {'scale': True}, {'identities': {}},
                                    {'config': {'seed': 17, 'epochs': 0, 'batch_size': 2,
                                                'learning_rate': .001, 'gradient_clip': 1.}}])
def test_training_rejects_unusable_normalization_provenance_and_configuration(changes):
    with pytest.raises(ValueError):
        fitted(**changes)


@pytest.mark.parametrize('change', ['float_mask', 'wrong_target_shape', 'valid_nan', 'empty',
                                  'no_features', 'no_targets', 'validation_context'])
def test_training_rejects_malformed_arrays_and_empty_supervision(change):
    arrays = samples()
    if change == 'float_mask':
        arrays[2] = arrays[2].astype(float)
    elif change == 'wrong_target_shape':
        arrays[1] = arrays[1][:, :, 0]
    elif change == 'valid_nan':
        arrays[0][0, 0, 0] = np.nan
    elif change == 'empty':
        arrays[:4] = [array[:0] for array in arrays[:4]]
    elif change == 'no_features':
        arrays[2][0] = False
    elif change == 'no_targets':
        arrays[3][0] = False
    else:
        arrays[4] = arrays[4][:, :2]
        arrays[6] = arrays[6][:, :2]
    with pytest.raises(ValueError):
        fitted(arrays)


def test_predict_rejects_changed_shape_and_no_observed_context():
    model = fitted()
    x, _, mask, *_ = samples()
    with pytest.raises(ValueError):
        model.predict(x[:, :2], mask[:, :2])
    with pytest.raises(ValueError):
        model.predict(x, np.zeros_like(mask))
    x[0, 0, 0] = np.inf
    with pytest.raises(ValueError):
        model.predict(x, mask)
