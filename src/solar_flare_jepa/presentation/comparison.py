"""Independent arithmetic replay of immutable V1 saved predictions; no fitting."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.evaluation.probabilistic import block_bootstrap
from solar_flare_jepa.experiments.config import load_config

LEVELS = np.array([.05, .25, .5, .75, .95])
SEEDS = (17, 29, 43)
FAMILIES = ('supervised', 'jepa_frozen', 'jepa_finetune')
V1_RUN = 'results/experiments/v1-full-20261009'


def independent_scores(targets, mask, point, quantiles=None):
    """Equal-cell dex scores, independently expressed from the saved native arrays."""
    y, p, m = np.asarray(targets, float), np.asarray(point, float), np.asarray(mask, bool)
    if y.ndim != 3 or y.shape != p.shape or m.shape != y.shape:
        raise ValueError('Target, mask and point shape mismatch')
    if not m.any() or not m.any(axis=(1, 2)).all():
        raise ValueError('Each origin requires scored cells')
    if not np.isfinite(y[m]).all() or not np.isfinite(p[m]).all() or (y[m] <= 0).any() or (p[m] <= 0).any():
        raise ValueError('Scored observations and predictions must be finite and positive')
    ly, lp = np.log10(np.where(m, y, 1.)), np.log10(np.where(m, p, 1.))
    error = lp - ly
    def avg(a, axis=None):
        total, count = np.where(m, a, 0.).sum(axis=axis), m.sum(axis=axis)
        return np.divide(total, count, out=np.full_like(total, np.nan, dtype=float), where=count > 0)
    out = dict(log_mae=float(avg(abs(error))), log_rmse=float(np.sqrt(avg(error**2))),
               bias=float(avg(error)), scored_cells=int(m.sum()), origins=len(y),
               by_target={ch + '_flux': dict(log_mae=float(abs(error[..., k])[m[..., k]].mean()))
                          for k, ch in enumerate(('xrsa', 'xrsb')) if k < y.shape[2]},
               by_lead=dict(log_mae=avg(abs(error), axis=(0, 2)).tolist()))
    losses = dict(log_mae=avg(abs(error), axis=(1, 2)))
    if quantiles is not None:
        q = np.asarray(quantiles, float)
        if q.shape != (*y.shape, len(LEVELS)):
            raise ValueError('Quantile shape mismatch')
        if not np.isfinite(q[m]).all() or (q[m] <= 0).any():
            raise ValueError('Scored quantiles must be finite and positive')
        if (np.diff(q[m], axis=-1) < 0).any():
            raise ValueError('Quantiles must be ordered')
        lq = np.log10(np.where(m[..., None], q, 1.))
        residual = ly[..., None] - lq
        # rho_tau(u) = u*(tau - I[u<0]); different expression from production scorer.
        rho = residual * (LEVELS - (residual < 0))
        cell = rho.mean(axis=-1)
        out['mean_pinball'] = float(avg(cell))
        out['pinball_by_level'] = {str(t): float(avg(rho[..., j])) for j, t in enumerate(LEVELS)}
        out['by_lead']['mean_pinball'] = avg(cell, axis=(0, 2)).tolist()
        losses['mean_pinball'] = avg(cell, axis=(1, 2))
        for label, a, b in (('central_50', 1, 3), ('central_90', 0, 4)):
            inside = (ly >= lq[..., a]) & (ly <= lq[..., b])
            out['coverage_' + label] = float(avg(inside))
            out['width_' + label] = float(avg(lq[..., b] - lq[..., a]))
            out['by_lead']['coverage_' + label] = avg(inside, axis=(0, 2)).tolist()
            out['coverage_by_target_' + label] = {
                ch: float(inside[..., k][m[..., k]].mean()) for k, ch in enumerate(('xrsa', 'xrsb'))
                if k < y.shape[2]}
    return out, losses


def mean_seed_scores(rows, family):
    """Arithmetic mean of seed metrics, never a forecast ensemble."""
    ids = [f'{family}_seed{s}' for s in SEEDS]
    if any(k not in rows for k in ids):
        raise ValueError('Missing required seed for family comparison')
    def mean(values):
        if isinstance(values[0], dict):
            return {k: mean([v[k] for v in values]) for k in values[0]}
        a = np.asarray(values, float).mean(axis=0)
        return a.tolist() if a.ndim else float(a)
    return mean([rows[k] for k in ids])


def verify_bundle(root, frame=None):
    """Fail closed on score/support disagreement; optionally verify native alignment."""
    root = Path(root).resolve(); run = root / V1_RUN
    summary = json.loads((run / 'summary.json').read_text())
    origins = json.loads((run / 'per_origin.json').read_text())['test']
    if summary['dev_mode'] or summary['quick'] or summary['status'] != 'complete':
        raise ValueError('Expected completed strict full V1 run')
    # The runner saves resolved ForecastSpec fields and canonical UTC spellings.
    if summary['config'] != load_config(root / 'configs/experiments/v1_goes_2024.json'):
        raise ValueError('V1 configuration mismatch')
    if summary['models_config'] != json.loads((root / 'configs/experiments/v1_models.json').read_text()):
        raise ValueError('V1 model configuration mismatch')
    rows, per_origin, discrepancies, checks = {}, {}, [], 0
    def check(actual, expected):
        nonlocal checks
        a, b = np.asarray(actual), np.asarray(expected)
        if a.shape != b.shape:
            raise ValueError('Artifact shape mismatch')
        np.testing.assert_allclose(a, b, rtol=0, atol=2e-12)
        discrepancies.append(float(np.max(np.abs(a - b)))); checks += 1
    with np.load(run / 'test_predictions.npz', allow_pickle=False) as z:
        ids = list(z['model_ids']); y, mask = z['targets'], z['target_mask']
        if (len(ids) != len(set(ids)) or set(ids) != set(summary['scores']['test'])
                or set(ids) != set(origins['losses'])):
            raise ValueError('Model support mismatch')
        if list(z['origin_ids']) != origins['origin_ids']:
            raise ValueError('Origin support mismatch')
        if not mask.all():
            raise ValueError('Expected V1 complete-case target support')
        np.testing.assert_array_equal(z['issue_times_ns'], origins['issue_times_ns'])
        if frame is not None:
            for field, key, offsets in (('targets', 'flux', np.arange(30)),
                                        ('context', 'flux', np.arange(-120, 0))):
                times = z['issue_times_ns'][:, None] + offsets * 60_000_000_000
                index = frame.index.get_indexer(pd.to_datetime(times.ravel(), utc=True))
                if (index < 0).any():
                    raise ValueError('Saved forecast support absent from native frame')
                native = frame[['xrsa_' + key, 'xrsb_' + key]].to_numpy(float)[index].reshape(z[field].shape)
                np.testing.assert_array_equal(native, z[field])
                np.testing.assert_array_equal(np.isfinite(native), z['target_mask' if field == 'targets' else 'context_mask'])
        for i, model in enumerate(ids):
            q = z[f'quantiles_{i}'] if f'quantiles_{i}' in z else None
            s, loss = independent_scores(y, mask, z[f'point_{i}'], q)
            if q is not None:
                np.testing.assert_array_equal(z[f'point_{i}'], q[..., 2])
            saved = summary['scores']['test'][model]['log']
            for metric, value in s.items():
                if metric.startswith('coverage_by_target_'):
                    continue  # Additional disaggregation, absent from original summary.
                if isinstance(value, dict):
                    for key, v in value.items():
                        if isinstance(v, dict):
                            for subkey, subvalue in v.items():
                                check(subvalue, saved[metric][key][subkey])
                        else:
                            check(v, saved[metric][key])
                else:
                    check(value, saved[metric])
            for metric, values in loss.items():
                check(values, origins['losses'][model][metric])
            rows[model], per_origin[model] = s, loss
    grouped = {k: v for k, v in rows.items() if not any(k.startswith(f + '_seed') for f in FAMILIES)}
    grouped.update({family: mean_seed_scores(rows, family) for family in FAMILIES})
    blocks = np.asarray(origins['issue_times_ns'], np.int64) // (86_400 * 10**9)
    paired = []
    for seeds, label in ((SEEDS, 'all_three'), ((17, 29), 'omit_seed43'),
                         ((17,), 'seed17'), ((29,), 'seed29'), ((43,), 'seed43')):
        a = np.mean([per_origin[f'jepa_finetune_seed{s}']['mean_pinball'] for s in seeds], axis=0)
        b = np.mean([per_origin[f'supervised_seed{s}']['mean_pinball'] for s in seeds], axis=0)
        paired.append(dict(contrast=label, **block_bootstrap(a, b, blocks, replicates=2000, seed=17)))
    for family in ('jepa_finetune', 'jepa_frozen'):
        a = np.mean([per_origin[f'{family}_seed{s}']['mean_pinball'] for s in SEEDS], axis=0)
        for reference in ('supervised', 'ar1-gjr-garch(1,1)-t', 'arima(2,1,0)', 'persistence_empirical'):
            b = (np.mean([per_origin[f'supervised_seed{s}']['mean_pinball'] for s in SEEDS], axis=0)
                 if reference == 'supervised' else per_origin[reference]['mean_pinball'])
            paired.append(dict(contrast=family + '_minus_' + reference,
                               **block_bootstrap(a, b, blocks, replicates=2000, seed=17)))
    evidence = dict(source_run=V1_RUN, executed_commit=summary['provenance']['git_commit'],
        sources=[dict(path=f'{V1_RUN}/{name}', sha256=sha256_file(run / name), bytes=(run / name).stat().st_size)
                 for name in ('summary.json', 'per_origin.json', 'test_predictions.npz')],
        model_count=len(rows), origins=len(origins['origin_ids']), scored_cells=int(mask.sum()),
        numerical_checks=checks, max_absolute_discrepancy=max(discrepancies),
        native_alignment_verified=frame is not None, seed_aggregation='arithmetic mean of fitted-seed losses, not ensemble forecasts',
        paired_daily_bootstrap=paired, per_model=rows, grouped=grouped)
    return summary, evidence
