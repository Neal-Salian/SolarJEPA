"""v1 multi-month GOES selection and log-space probabilistic scoring; synthetic only."""
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from solar_flare_jepa.evaluation.probabilistic import block_bootstrap, log_scores
from solar_flare_jepa.experiments.config import validate_config
from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
)

ROOT = Path(__file__).resolve().parents[1]
SECOND = 1_000_000_000


def v1_config():
    return json.loads((ROOT / 'configs/experiments/v1_goes_2024.json').read_text())


def test_v1_config_declares_contiguous_untouched_test_month():
    cfg = validate_config(v1_config())
    assert cfg['dataset']['kind'] == 'goes_historical_multi'
    assert [s['name'] for s in cfg['splits']] == ['train', 'validation', 'test']
    assert cfg['splits'][2]['start_utc'].startswith('2024-08-01')
    assert cfg['splits'][2]['end_utc'].startswith('2024-09-01')


@pytest.mark.parametrize('manifests', [
    ['data/manifests/goes_p2_july2024.json'],
    ['data/manifests/goes_p2_july2024.json', 'data/manifests/goes_p2_july2024.json'],
    ['data/manifests/goes_p2_july2024.json', '../outside.json'],
    ['data/manifests/goes_p2_july2024.json', 'data\\manifests\\x.json'],
    'data/manifests/goes_p2_july2024.json',
])
def test_multi_manifest_requires_unique_portable_selections(manifests):
    cfg = v1_config()
    cfg['dataset']['manifests'] = manifests
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_multi_manifest_rejects_unknown_dataset_keys():
    cfg = v1_config()
    cfg['dataset']['manifest'] = 'data/manifests/goes_p2_july2024.json'
    with pytest.raises(ValueError):
        validate_config(cfg)


def _frame(start, minutes):
    index = pd.date_range(start, periods=minutes, freq='min', tz='UTC', name='time_start')
    frame = pd.DataFrame(dict(xrsa_flux=1e-7, xrsb_flux=1e-6, xrsa_valid=True, xrsb_valid=True), index=index)
    frame['time_end'] = index + pd.Timedelta(minutes=1)
    frame['observed'] = True
    return frame


def _patch_selections(monkeypatch, frames):
    from solar_flare_jepa.data import foundation
    lookup = {f'data/manifests/m{i}.json': frame for i, frame in enumerate(frames)}

    def fake(relative, root):
        manifest = root / relative
        inventory = dict(dataset_id=Path(relative).stem, platform='GOES-16')
        return manifest, inventory, [], lookup[relative], dict(status='synthetic')
    monkeypatch.setattr(foundation, '_pinned_frame', fake)
    monkeypatch.setattr(foundation, 'sha256_file', lambda path: '0' * 64)
    cfg = v1_config()
    cfg['dataset']['manifests'] = list(lookup)
    return foundation, cfg


def test_multi_manifest_concatenates_only_exactly_contiguous_selections(monkeypatch, tmp_path):
    foundation, cfg = _patch_selections(monkeypatch, [_frame('2024-05-01', 60), _frame('2024-05-01 01:00', 30)])
    dataset = foundation.goes_training(cfg, tmp_path)
    assert len(dataset.starts_ns) == 90
    assert (np.diff(dataset.starts_ns) == 60 * SECOND).all()
    assert dataset.name == 'm0+m1'


@pytest.mark.parametrize('second_start', ['2024-05-01 01:01', '2024-05-01 00:59'])
def test_multi_manifest_refuses_gaps_and_overlaps(monkeypatch, tmp_path, second_start):
    foundation, cfg = _patch_selections(monkeypatch, [_frame('2024-05-01', 60), _frame(second_start, 30)])
    with pytest.raises(ValueError, match='contiguous'):
        foundation.goes_training(cfg, tmp_path)


def _scored(targets, point, quantiles=None, mask=None):
    targets = np.asarray(targets, float)
    n, h, k = targets.shape
    names = tuple(f'x{i}' for i in range(k))
    spec = ForecastSpec(60, 1, h, names, names, ('W/m2',) * k, ('W/m2',) * k, eligibility_policy='masked',
                        transform='log10', feature_reference=(1.,) * k, target_reference=(1.,) * k,
                        target_minimum=(0.,) * k)
    issues = np.arange(n, dtype=np.int64) * 86_400 * SECOND
    starts = issues[:, None] + np.arange(h, dtype=np.int64)[None] * 60 * SECOND
    grid = FutureGrid(starts, starts + 60 * SECOND, issues, tuple(f'o{i}' for i in range(n)), spec, 'synthetic')
    target = ForecastTargets(targets, np.ones_like(targets, bool) if mask is None else mask, grid)
    levels = () if quantiles is None else (0.05, 0.25, 0.5, 0.75, 0.95)
    prediction = ForecastPrediction(np.asarray(point, float), grid, 'toy', levels, quantiles,
                                    'inverse_transformed_point')
    return log_scores(target, prediction, spec)


def test_log_scores_use_dex_and_only_valid_cells():
    targets = np.array([[[1e-6], [1e-5]], [[1e-7], [1e-3]]])
    point = np.array([[[1e-6], [1e-6]], [[1e-6], [1e-6]]])
    mask = np.array([[[True], [True]], [[True], [False]]])
    scores = _scored(targets, point, mask=mask)
    assert scores['scored_cells'] == 3
    assert scores['log_mae'] == pytest.approx((0 + 1 + 1) / 3)
    assert scores['by_lead']['log_mae'] == pytest.approx([0.5, 1.0])
    assert scores['per_origin']['log_mae'] == pytest.approx([0.5, 1.0])


def test_log_pinball_coverage_and_width_are_hand_checkable():
    targets = np.array([[[1e-6]], [[1e-4]]])
    offsets = np.array([-1., -0.5, 0., 0.5, 1.])
    quantiles = 10.0**(-6 + offsets)[None, None, None, :].repeat(2, axis=0)
    point = quantiles[..., 2]
    scores = _scored(targets, point, quantiles)
    levels = np.array([0.05, 0.25, 0.5, 0.75, 0.95])
    first = np.maximum(levels * (0 - offsets), (levels - 1) * (0 - offsets)).mean()
    second = np.maximum(levels * (2 - offsets), (levels - 1) * (2 - offsets)).mean()
    assert scores['mean_pinball'] == pytest.approx((first + second) / 2)
    assert scores['coverage_central_90'] == pytest.approx(0.5)
    assert scores['coverage_central_50'] == pytest.approx(0.5)
    assert scores['width_central_90'] == pytest.approx(2.0)
    assert scores['width_central_50'] == pytest.approx(1.0)


def test_block_bootstrap_is_paired_seeded_and_requires_blocks():
    rng = np.random.default_rng(0)
    a = rng.normal(size=200)
    blocks = np.repeat(np.arange(10), 20)
    same = block_bootstrap(a, a, blocks)
    assert same['mean_difference'] == 0 and same['ci95'] == [0.0, 0.0]
    better = block_bootstrap(a - 1, a, blocks, seed=3)
    assert better['ci95'][1] < 0 and better['prob_a_better'] == 1.0
    assert block_bootstrap(a, a + 0.1, blocks, seed=3) == block_bootstrap(a, a + 0.1, blocks, seed=3)
    with pytest.raises(ValueError):
        block_bootstrap(a, a, np.zeros(200))
