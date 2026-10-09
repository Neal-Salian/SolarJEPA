"""Markdown tables and static figures from a completed v1 output directory."""
import json
from pathlib import Path

import numpy as np

BLUE, ORANGE, AQUA, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, MUTED, GRID, SURFACE = '#0b0b0b', '#898781', '#e4e3df', '#fcfcfb'
JEPA_FAMILIES = ('jepa_finetune', 'jepa_frozen', 'supervised')


def _fmt(value, digits=4):
    return '—' if value is None or (isinstance(value, float) and not np.isfinite(value)) else f'{value:.{digits}f}'


def _aggregate(scores):
    """Collapse JEPA seeds to mean ± sd; other models pass through."""
    rows, seeds = {}, {}
    for model_id, entry in scores.items():
        if entry['family'] in JEPA_FAMILIES:
            seeds.setdefault(entry['family'], []).append(entry)
        else:
            rows[model_id] = dict(entry=entry, n=1)
    for family, entries in seeds.items():
        rows[family] = dict(entries=entries, n=len(entries), entry=entries[0])
    return rows


def _metric(row, path):
    def get(entry):
        value = entry
        for key in path:
            value = None if value is None else value.get(key)
        return value
    if 'entries' not in row:
        return get(row['entry']), None
    values = [v for v in (get(e) for e in row['entries']) if v is not None]
    if not values:
        return None, None
    return float(np.mean(values)), (float(np.std(values, ddof=1)) if len(values) > 1 else None)


def _cell(row, path, digits=4):
    mean, sd = _metric(row, path)
    return _fmt(mean, digits) + ('' if sd is None else f' ± {_fmt(sd, digits)}')


def _table(scores, persistence_id='persistence'):
    rows = _aggregate(scores)
    base = scores[persistence_id]['log']['log_mae']
    order = sorted(rows, key=lambda k: (_metric(rows[k], ('log', 'mean_pinball'))[0] is None,
                                        _metric(rows[k], ('log', 'mean_pinball'))[0] or 0,
                                        _metric(rows[k], ('log', 'log_mae'))[0]))
    lines = ['| Model | Family | Seeds | Log MAE (dex) | Skill vs persistence | Mean pinball (dex) | 50% cov. | 90% cov. | 90% width (dex) | Native MAE (W/m2) |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for key in order:
        row = rows[key]
        mae, _ = _metric(row, ('log', 'log_mae'))
        lines.append('| ' + ' | '.join([
            key, row['entry']['family'], str(row['n']), _cell(row, ('log', 'log_mae')),
            _fmt(1 - mae / base, 3), _cell(row, ('log', 'mean_pinball')),
            _cell(row, ('log', 'coverage_central_50'), 3), _cell(row, ('log', 'coverage_central_90'), 3),
            _cell(row, ('log', 'width_central_90'), 3),
            _fmt(_metric(row, ('native', 'aggregate', 'mae', 'value'))[0], 10)]) + ' |')
    return '\n'.join(lines)


def _strata_table(scores):
    rows = _aggregate(scores)
    names = ['all', 'quiet_below_c', 'rising_x2', 'flaring_m_plus']
    counts = {n: scores[next(iter(scores))]['strata'][n]['origins'] for n in names}
    header = '| Model | ' + ' | '.join(f'{n} (n={counts[n]}) log MAE / pinball' for n in names) + ' |'
    lines = [header, '|---|' + '---:|' * len(names)]
    for key, row in sorted(rows.items(), key=lambda kv: _metric(kv[1], ('strata', 'all', 'log_mae'))[0]):
        cells = []
        for n in names:
            mae = _metric(row, ('strata', n, 'log_mae'))[0]
            pin = _metric(row, ('strata', n, 'mean_pinball'))[0]
            cells.append(f'{_fmt(mae)} / {_fmt(pin)}')
        lines.append(f'| {key} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=INK, labelsize=9)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _pick(scores, validation):
    """Representative models for figures: chosen by validation, never test."""
    def best(prefixes):
        candidates = [k for k in scores if scores[k]['family'] in prefixes and k in validation
                      and 'mean_pinball' in validation[k]['log']]
        return min(candidates, key=lambda k: validation[k]['log']['mean_pinball'], default=None)
    return dict(jepa=best(('jepa_finetune', 'jepa_frozen')), garch=best(('volatility',)),
                arima=best(('arima', 'sarima')), empirical=best(('persistence_empirical',)))


def write_report(destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    destination = Path(destination)
    summary = json.loads((destination / 'summary.json').read_text())
    arrays = np.load(destination / 'test_predictions.npz', allow_pickle=False)
    test, validation = summary['scores']['test'], summary['scores']['validation']
    picks = _pick(test, validation)
    figures = []

    # Log MAE by lead for representative models (one axis, <= 4 series).
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    _style(ax)
    series = [('persistence', 'Persistence', YELLOW), (picks['arima'], 'ARIMA (val-selected)', AQUA),
              (picks['garch'], 'GARCH family (val-best)', ORANGE), (picks['jepa'], 'JEPA (val-best)', BLUE)]
    for model_id, label, color in series:
        if model_id is None:
            continue
        values = test[model_id]['log']['by_lead']['log_mae']
        leads = np.arange(1, len(values) + 1)
        ax.plot(leads, values, color=color, linewidth=2, label=f'{label}: {model_id}')
        ax.annotate(label.split(' ')[0], (leads[-1], values[-1]), xytext=(4, 0), textcoords='offset points',
                    va='center', fontsize=8, color=INK)
    ax.set_xlabel('Lead time (minutes)', color=INK)
    ax.set_ylabel('Log MAE of median (dex)', color=INK)
    ax.set_title('Test (Aug 2024): error growth with lead time', color=INK, fontsize=11, loc='left')
    ax.legend(frameon=False, fontsize=8, loc='upper left')
    fig.tight_layout()
    fig.savefig(destination / 'fig_lead_log_mae.png', facecolor=SURFACE)
    plt.close(fig)
    figures.append('fig_lead_log_mae.png')

    # Fan charts on the test origin with the largest XRS-B rise (small multiples).
    model_ids = list(arrays['model_ids'])
    targets, mask = arrays['targets'], arrays['target_mask']
    context, cmask = arrays['context'], arrays['context_mask']
    b = 1
    last = np.array([context[n, np.flatnonzero(cmask[n, :, b])[-1], b] for n in range(len(context))])
    future = np.where(mask[..., b], targets[..., b], np.nan)
    ratio = np.nanmax(future, axis=1) / last
    origin = int(np.nanargmax(ratio))
    panels = [(picks['jepa'], 'JEPA', BLUE), (picks['garch'], 'GARCH family', ORANGE), (picks['arima'], 'ARIMA', AQUA)]
    panels = [p for p in panels if p[0] is not None and f'quantiles_{model_ids.index(p[0])}' in arrays]
    if panels:
        fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 3.6), dpi=150, sharey=True)
        axes = np.atleast_1d(axes)
        t_ctx = np.arange(-context.shape[1] + 1, 1)
        t_fut = np.arange(1, targets.shape[1] + 1)
        for ax, (model_id, label, color) in zip(axes, panels):
            _style(ax)
            q = arrays[f'quantiles_{model_ids.index(model_id)}'][origin, :, b, :]
            ax.fill_between(t_fut, q[:, 0], q[:, -1], color=color, alpha=0.18, linewidth=0, label='90% interval')
            ax.fill_between(t_fut, q[:, 1], q[:, -2], color=color, alpha=0.35, linewidth=0, label='50% interval')
            ax.plot(t_fut, q[:, len(q[0]) // 2], color=color, linewidth=2, label='Median')
            ax.plot(t_ctx, np.where(cmask[origin, :, b], context[origin, :, b], np.nan), color=INK, linewidth=1.2,
                    label='Observed context')
            ax.plot(t_fut, future[origin], color=INK, linewidth=1.2, linestyle='--', label='Observed future')
            ax.axvline(0, color=MUTED, linewidth=0.8)
            ax.set_yscale('log')
            ax.set_title(f'{label}: {model_id}', color=INK, fontsize=9, loc='left')
            ax.set_xlabel('Minutes from issue time', color=INK)
        axes[0].set_ylabel('XRS-B flux (W/m²)', color=INK)
        axes[0].legend(frameon=False, fontsize=7, loc='upper left')
        fig.suptitle(f'Largest test rise: origin {arrays["origin_ids"][origin]} (×{ratio[origin]:.1f} in 30 min)',
                     color=INK, fontsize=10, x=0.01, ha='left')
        fig.tight_layout()
        fig.savefig(destination / 'fig_fan_largest_rise.png', facecolor=SURFACE)
        plt.close(fig)
        figures.append('fig_fan_largest_rise.png')

    # Empirical vs nominal interval coverage, two small multiples, one series each.
    rows = {k: v for k, v in test.items() if 'coverage_central_90' in v['log']}
    if rows:
        order = sorted(rows, key=lambda k: rows[k]['log']['coverage_central_90'])
        fig, axes = plt.subplots(1, 2, figsize=(9, 0.32 * len(order) + 1.2), dpi=150, sharey=True)
        for ax, (key, nominal) in zip(axes, (('coverage_central_50', 0.5), ('coverage_central_90', 0.9))):
            _style(ax)
            values = [rows[k]['log'][key] for k in order]
            ax.barh(range(len(order)), values, color=BLUE, height=0.6)
            ax.axvline(nominal, color=INK, linewidth=1, linestyle='--')
            ax.set_xlim(0, 1)
            ax.set_title(f'{int(nominal * 100)}% interval: empirical coverage (dashed = nominal)',
                         color=INK, fontsize=9, loc='left')
        axes[0].set_yticks(range(len(order)), order, fontsize=7)
        fig.tight_layout()
        fig.savefig(destination / 'fig_coverage.png', facecolor=SURFACE)
        plt.close(fig)
        figures.append('fig_coverage.png')

    comparisons = [c for c in summary['comparisons'] if c['metric'] == 'mean_pinball'
                   and (c['model'] in (picks['jepa'],) or test.get(c['model'], {}).get('family') in JEPA_FAMILIES)]
    lines = [f"# v1 results: {destination.name}", '',
             f"Mode: {'DEV (relaxed provenance)' if summary['dev_mode'] else 'STRICT'}"
             f"{', QUICK' if summary['quick'] else ''}. Git: `{summary['provenance']['git_commit']}`. "
             f"Dataset fingerprint `{summary['dataset']['fingerprint']}`.", '',
             '## Train-only diagnostics (log10 one-minute differences)', '', '```json',
             json.dumps(summary.get('diagnostics'), indent=1), '```', '',
             '## Test (2024-08, untouched until all selections were frozen)', '', _table(test), '',
             '## Validation (selection partition)', '', _table(validation), '',
             '## Test strata (retrospective annotations from observed targets)', '', _strata_table(test), '',
             '## Paired daily-block bootstrap on test (mean pinball, dex; negative favours the model)', '',
             '| Model | Reference | Mean difference | 95% CI | Bootstrap fraction model better |', '|---|---|---:|---:|---:|']
    for c in comparisons:
        lines.append(f"| {c['model']} | {c['reference']} | {_fmt(c['mean_difference'], 5)} | "
                     f"[{_fmt(c['ci95'][0], 5)}, {_fmt(c['ci95'][1], 5)}] | {_fmt(c['prob_a_better'], 3)} |")
    lines += ['', '## Model failures (reported, never converted into origin dropping)', '']
    lines += [f"- {f['model']}: {f['stage']} {f['error_type']}: {f['reason']}" for f in summary.get('failures', [])] or ['- none']
    lines += ['', '## Selections (validation only)', '', '```json', json.dumps(summary['selections'], indent=1), '```',
              '', '## Limitations', ''] + [f'- {x}' for x in summary['limitations']] + \
             ['', '## Figures', ''] + [f'![{f}]({f})' for f in figures]
    (destination / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return destination / 'summary.md'
