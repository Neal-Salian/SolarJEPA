"""Versioned V2 forecast losses: literal arithmetic, channel weights, gradients, V1 parity."""
import importlib

import numpy as np
import pytest

torch = pytest.importorskip('torch')

LEVELS = (0.05, 0.5, 0.95)


def losses():
    return importlib.import_module('solar_flare_jepa.training.losses')


def _rho(error, levels=LEVELS):
    tau = np.asarray(levels)
    return np.maximum(tau * error[..., None], (tau - 1) * error[..., None])


def test_registry_is_explicit_and_unknown_versions_fail():
    module = losses()
    assert module.LOSS_VERSIONS == ('normalized_pinball_v1', 'dex_pinball_equal_channel_v2')
    with pytest.raises(ValueError, match='Unknown forecast loss'):
        module.check_loss_version('dex_pinball')
    with pytest.raises(ValueError, match='Unknown forecast loss'):
        module.channel_weights('pinball', (1., 2.))


def test_channel_weights_are_unit_for_v1_and_train_std_for_dex():
    module = losses()
    assert module.channel_weights('normalized_pinball_v1', (0.3, 0.5)) == (1., 1.)
    assert module.channel_weights('dex_pinball_equal_channel_v2', (0.3, 0.5)) == (0.3, 0.5)
    for bad in ((0.3, 0.), (0.3, float('nan')), (), (0.3, -1.)):
        with pytest.raises(ValueError):
            module.channel_weights('dex_pinball_equal_channel_v2', bad)


def test_literal_arithmetic_for_both_versions():
    module = losses()
    # Two origins, one lead, two channels; predicted quantiles in normalized units.
    quantiles = torch.tensor([[[[-1., 0., 1.], [0., 0., 0.]]],
                              [[[0., 1., 2.], [-2., -1., 0.]]]], dtype=torch.float64)
    targets = torch.tensor([[[0.5, 1.0]], [[0.0, -1.0]]], dtype=torch.float64)
    mask = torch.ones_like(targets, dtype=torch.bool)
    error = targets.numpy()[..., None] - quantiles.numpy()
    tau = np.asarray(LEVELS)
    rho = np.maximum(tau * error, (tau - 1) * error)
    v1 = rho.mean()
    scale = (0.25, 2.0)
    per_channel = rho.mean(axis=(0, 1, 3))
    dex = float(np.mean(np.asarray(scale) * per_channel))
    assert float(module.forecast_loss('normalized_pinball_v1', quantiles, targets, mask, LEVELS, scale)) == pytest.approx(v1, abs=1e-15)
    assert float(module.forecast_loss('dex_pinball_equal_channel_v2', quantiles, targets, mask, LEVELS, scale)) == pytest.approx(dex, abs=1e-15)
    # Hand check of one cell: target 0.5, quantile -1 at tau .05 -> .05 * 1.5.
    assert rho[0, 0, 0, 0] == pytest.approx(0.075)


def test_v1_version_is_exactly_the_v1_training_loss():
    module = losses()
    jepa = importlib.import_module('solar_flare_jepa.training.jepa')
    rng = np.random.default_rng(0)
    quantiles = torch.tensor(np.sort(rng.normal(size=(7, 4, 2, 3)), axis=-1), dtype=torch.float32)
    targets = torch.tensor(rng.normal(size=(7, 4, 2)), dtype=torch.float32)
    mask = torch.tensor(rng.random((7, 4, 2)) > .2)
    expected = jepa.pinball_loss(quantiles, targets, mask, LEVELS)
    actual = module.forecast_loss('normalized_pinball_v1', quantiles, targets, mask, LEVELS, (3., 4.))
    assert torch.equal(actual, expected)


def test_dex_loss_masks_per_channel_before_channel_averaging():
    module = losses()
    quantiles = torch.zeros((3, 1, 2, 3), dtype=torch.float64)
    targets = torch.tensor([[[1., 2.]], [[3., 4.]], [[5., 6.]]], dtype=torch.float64)
    mask = torch.tensor([[[True, True]], [[True, False]], [[True, False]]])
    rho = _rho(targets.numpy())
    a = rho[:, 0, 0].mean()
    b = rho[0, 0, 1].mean()
    value = module.forecast_loss('dex_pinball_equal_channel_v2', quantiles, targets, mask, LEVELS, (1., 1.))
    assert float(value) == pytest.approx((a + b) / 2, abs=1e-14)
    empty = mask.clone()
    empty[..., 1] = False
    with pytest.raises(ValueError, match='every channel'):
        module.forecast_loss('dex_pinball_equal_channel_v2', quantiles, targets, empty, LEVELS, (1., 1.))


def test_dex_gradient_ratio_equals_train_std_ratio():
    module = losses()
    quantiles = torch.zeros((4, 3, 2, 3), dtype=torch.float64, requires_grad=True)
    targets = torch.ones((4, 3, 2), dtype=torch.float64)  # identical normalized errors in both channels
    mask = torch.ones_like(targets, dtype=torch.bool)
    module.forecast_loss('dex_pinball_equal_channel_v2', quantiles, targets, mask, LEVELS, (0.2, 0.7)).backward()
    grad = quantiles.grad
    ratio = grad[..., 1, :] / grad[..., 0, :]
    assert torch.allclose(ratio, torch.full_like(ratio, 0.7 / 0.2))
    quantiles.grad = None
    module.forecast_loss('normalized_pinball_v1', quantiles, targets, mask, LEVELS, (0.2, 0.7)).backward()
    assert torch.equal(quantiles.grad[..., 1, :], quantiles.grad[..., 0, :])


def test_invalid_inputs_are_rejected():
    module = losses()
    q = torch.zeros((2, 1, 2, 3))
    t = torch.zeros((2, 1, 2))
    m = torch.ones((2, 1, 2), dtype=torch.bool)
    with pytest.raises(ValueError):
        module.forecast_loss('dex_pinball_equal_channel_v2', q[..., :2], t, m, LEVELS, (1., 1.))
    with pytest.raises(ValueError):
        module.forecast_loss('dex_pinball_equal_channel_v2', q, t, m.int(), LEVELS, (1., 1.))
    with pytest.raises(ValueError):
        module.forecast_loss('dex_pinball_equal_channel_v2', q, t, m, LEVELS, (1.,))
    with pytest.raises(ValueError):
        module.forecast_loss('dex_pinball_equal_channel_v2', q, t, torch.zeros_like(m), LEVELS, (1., 1.))
    nan = q.clone()
    nan[0, 0, 0, 0] = float('nan')
    with pytest.raises(ValueError, match='Nonfinite'):
        module.forecast_loss('dex_pinball_equal_channel_v2', nan, t, m, LEVELS, (1., 1.))


def test_accumulator_matches_one_shot_loss_over_uneven_batches():
    module = losses()
    rng = np.random.default_rng(4)
    q = torch.tensor(np.sort(rng.normal(size=(11, 5, 2, 3)), axis=-1))
    t = torch.tensor(rng.normal(size=(11, 5, 2)))
    m = torch.tensor(rng.random((11, 5, 2)) > .1)
    for version in module.LOSS_VERSIONS:
        accumulator = module.MetricAccumulator(version, LEVELS, (0.3, 0.9))
        for start in range(0, 11, 4):
            accumulator.add(q[start:start + 4], t[start:start + 4], m[start:start + 4])
        expected = float(module.forecast_loss(version, q, t, m, LEVELS, (0.3, 0.9)))
        assert accumulator.value() == pytest.approx(expected, rel=1e-12)
    with pytest.raises(ValueError, match='no valid'):
        module.MetricAccumulator('dex_pinball_equal_channel_v2', LEVELS, (1., 1.)).value()


def test_dex_metric_equals_log_space_mean_pinball_on_complete_support():
    """Normalized quantiles mapped to native flux score identically under log_scores."""
    module = losses()
    from test_jepa import fixture
    from solar_flare_jepa.evaluation.probabilistic import log_scores
    from solar_flare_jepa.forecasting.contracts import ForecastPrediction
    from solar_flare_jepa.training.normalization import Normalization
    windows = fixture()
    normalization = Normalization.fit(windows['train'].training_slice)
    valid = windows['validation']
    targets = normalization.normalize(valid.targets.values, valid.targets.mask, 'target')
    rng = np.random.default_rng(9)
    quantiles = np.sort(targets[..., None] + rng.normal(scale=.7, size=targets.shape + (5,)), axis=-1)
    levels = (0.05, 0.25, 0.5, 0.75, 0.95)
    native = normalization.inverse_targets(quantiles.transpose(0, 1, 3, 2)).transpose(0, 1, 3, 2)
    prediction = ForecastPrediction(native[..., 2], valid.targets.grid, 'synthetic', quantile_levels=levels,
                                    quantiles=native, point_interpretation='inverse_transformed_point')
    expected = log_scores(valid.targets, prediction, valid.context.spec)['mean_pinball']
    assert valid.targets.mask.all()
    value = module.forecast_loss('dex_pinball_equal_channel_v2', torch.tensor(quantiles), torch.tensor(targets),
                                 torch.tensor(valid.targets.mask), levels, normalization.target_scale)
    assert float(value) == pytest.approx(expected, rel=1e-10)
