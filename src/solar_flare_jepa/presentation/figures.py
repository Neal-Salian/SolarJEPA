"""Deterministic Matplotlib assets, with captions and input lineage per figure."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch

from .comparison import SEEDS, V1_RUN

INK, MUTED = '#152b3c', '#536879'
BLUE, ORANGE, GREEN, PURPLE = '#1976a3', '#cd641b', '#258778', '#8362a9'
LABELS = {
    'persistence_empirical': 'Empirical persistence',
    'arima(2,1,0)': 'ARIMA(2,1,0)',
    'ar1-constant-normal': 'AR(1) + constant variance',
    'ar1-arch(1)-normal': 'AR(1) + ARCH(1), Normal',
    'ar1-garch(1,1)-normal': 'AR(1) + GARCH(1,1), Normal*',
    'ar1-garch(1,1)-t': 'AR(1) + GARCH(1,1), Student-t*',
    'ar1-gjr-garch(1,1)-t': 'AR(1) + GJR-GARCH(1,1), t†',
    'supervised': 'Supervised control (3-seed mean)',
    'jepa_frozen': 'Frozen JEPA (3-seed mean)',
    'jepa_finetune': 'Fine-tuned JEPA (3-seed mean)',
}
ORDER = list(LABELS)
COLORS = {k: (BLUE if k == 'supervised' else PURPLE if k == 'jepa_frozen'
              else GREEN if k == 'jepa_finetune' else ORANGE) for k in ORDER}


def style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
        'axes.titlesize': 15, 'axes.labelsize': 12, 'axes.titleweight': 'bold',
        'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#b7c4cc',
        'axes.facecolor': '#ffffff', 'figure.facecolor': '#ffffff',
        'legend.frameon': False, 'svg.fonttype': 'none', 'svg.hashsalt': 'solarjepa-presentation',
        'savefig.dpi': 220, 'path.simplify': False})


def _dates(ax):
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=7))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.grid(axis='y', color='#dce4e8', lw=.6)


def _save(fig, destination, name, caption, source, entries):
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=True)
    for extension in ('png', 'svg'):
        path = destination / f'{name}.{extension}'
        fig.savefig(path, bbox_inches='tight',
                    metadata={'Date': None} if extension == 'svg' else None)
        if extension == 'svg':
            # Matplotlib emits trailing spaces in multiline path data; keep Git diffs clean.
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    entries.append(dict(stem=name, files=[f'docs/figures/presentation/{name}.{ext}' for ext in ('png', 'svg')],
                        caption=caption, source=source))
    plt.close(fig)


def eda_figures(frame, block, dependence, evidence, destination):
    style(); entries = []
    source = [x['path'] for x in evidence['manifests']]
    channels = [('xrsa', 'XRS-A · 0.05–0.4 nm', BLUE), ('xrsb', 'XRS-B · 0.1–0.8 nm', ORANGE)]
    period = 'GOES-16 · May–August 2024 · one-minute bins'
    fig, axes = plt.subplots(2, 1, figsize=(12, 6.6), sharex=True, layout='constrained')
    for ax, (ch, title, color) in zip(axes, channels):
        raw = frame[ch + '_flux_raw'].astype(float)
        ax.plot(frame.index, raw.where(np.isfinite(raw) & (raw > 0)), color=color, lw=.55, rasterized=True)
        rejected = (~frame[ch + '_valid']) & raw.gt(0) & np.isfinite(raw)
        ax.scatter(frame.index[rejected], raw[rejected], color='#b82d44', s=4, alpha=.7,
                   label='Finite values rejected by V1 QC', rasterized=True)
        ax.set(title=title, ylabel='Irradiance (W m$^{-2}$)', ylim=(0, None)); ax.legend(fontsize=9); _dates(ax)
    axes[-1].set_xlabel('UTC record start'); fig.suptitle(period + ' | native flux before repository QC')
    _save(fig, destination, 'eda_raw_flux',
          'Native electron-corrected primary irradiance before repository QC, on a linear scale. '
          'Red marks finite rejected values; nonfinite values are gaps. These are not raw detector counts.', source, entries)

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.6), sharex=True, layout='constrained')
    for ax, (ch, title, color) in zip(axes, channels):
        ax.plot(frame.index, np.log10(frame[ch + '_flux']), color=color, lw=.55, rasterized=True)
        ax.set(title=title, ylabel='log$_{10}$(F / 1 W m$^{-2}$)'); _dates(ax)
    axes[-1].set_xlabel('UTC record start'); fig.suptitle(period + ' | QC-valid log flux; gaps retained')
    _save(fig, destination, 'eda_log_flux', 'Base-10 log of QC-valid irradiance relative to 1 W m⁻². '
          'Every one-minute observation is supplied to the plot; rejected data remain gaps, without interpolation.', source, entries)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
    for ch, title, color in channels:
        valid = frame[ch + '_flux'].dropna().to_numpy(float)
        axes[0].hist(valid, bins=70, histtype='step', lw=1.7, color=color, label=ch.upper())
        axes[1].hist(np.log10(valid), bins=70, histtype='step', lw=1.7, color=color, label=ch.upper())
    axes[0].set(xlabel='Irradiance (W m$^{-2}$)', ylabel='Valid minute bins', title='Native units: long right tail')
    axes[0].ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
    axes[1].set(xlabel='log$_{10}$(F / 1 W m$^{-2}$)', title='Log transform spreads the range')
    for ax in axes: ax.legend(); ax.grid(axis='y', color='#dce4e8')
    fig.suptitle(period + ' | QC-valid distributions')
    _save(fig, destination, 'eda_distribution', 'Each panel counts valid minute bins, not independent '
          'events. Native-unit and log-space histograms have equal-width bins in their respective spaces.', source, entries)

    fig, axes = plt.subplots(2, 2, figsize=(12, 6.8), sharex=True, layout='constrained')
    for i, (ch, title, color) in enumerate(channels):
        values = np.log10(frame[ch + '_flux'])
        rolling = values.rolling(360, min_periods=360)
        axes[i, 0].plot(frame.index, rolling.mean(), color=color, lw=.75, rasterized=True)
        axes[i, 1].plot(frame.index, rolling.var(ddof=1), color=color, lw=.75, rasterized=True)
        axes[i, 0].set(title=title + ' · trailing mean', ylabel='Mean log flux (dex)')
        axes[i, 1].set(title=title + ' · trailing variance', ylabel='Variance (dex²)', ylim=(0, None))
        for ax in axes[i]: _dates(ax)
    for ax in axes[-1]: ax.set_xlabel('UTC record start')
    fig.suptitle('Six-hour rolling statistics · 360 valid consecutive bins required')
    _save(fig, destination, 'eda_rolling_statistics', 'Trailing six-hour log-flux mean and sample variance '
          '(ddof=1). A missing/rejected minute invalidates that full rolling window. Changing variance alone '
          'does not decide unit-root stationarity.', source, entries)

    block_label = f'{block.index[0]:%d %b %H:%M}–{block.index[-1] + pd.Timedelta(minutes=1):%d %b %H:%M} UTC'
    for method in ('acf', 'pacf'):
        fig, axes = plt.subplots(2, 2, figsize=(12, 6.8), sharex=True, layout='constrained')
        for i, (ch, title, color) in enumerate(channels):
            for j, transform in enumerate(('log_level', 'log_difference')):
                values = dependence[ch][method][transform]
                lags = np.arange(1, len(values))
                axes[i, j].vlines(lags, 0, values[1:], color=color, lw=1.3)
                axes[i, j].axhline(0, color=INK, lw=.7)
                axes[i, j].set(title=title + (' · log levels' if j == 0 else ' · first log differences'),
                               ylabel=method.upper(), ylim=(-1, 1))
                axes[i, j].grid(axis='y', color='#dce4e8')
        for ax in axes[-1]: ax.set_xlabel('Lag (minutes)')
        fig.suptitle(f'{method.upper()} · contiguous training block · {block_label}')
        _save(fig, destination, 'eda_' + method, f'{method.upper()} on the longest jointly valid training '
              'run (10,149 minute bins). Log levels and differences use the same segment. '
              + ('ACF uses FFT with biased covariance normalization.' if method == 'acf' else 'PACF uses Yule–Walker MLE (ywm).')
              + ' No iid significance bands are asserted; neither plot is a stationarity proof.', source, entries)

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.6), sharex=True, layout='constrained')
    for ax, (ch, title, color) in zip(axes, channels):
        daily = np.log10(frame[ch + '_flux']).resample('1D')
        median, low, high = daily.median(), daily.quantile(.25), daily.quantile(.75)
        ax.fill_between(median.index, low, high, color=color, alpha=.2, label='Within-day IQR')
        ax.plot(median.index, median, color=color, label='Daily median', lw=1.6)
        ax.set(title=title, ylabel='Log flux (dex)'); ax.legend(fontsize=10); _dates(ax)
    axes[-1].set_xlabel('UTC day'); fig.suptitle('Daily summaries show changing activity · no daily seasonality assumed')
    _save(fig, destination, 'eda_daily_variability', 'Daily median and 25–75% spread of available QC-valid '
          'log measurements. Days can have different valid counts; see data-quality figure. IQR is '
          'within-day variability, not uncertainty of the median and not evidence of daily seasonality.', source, entries)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.9), layout='constrained')
    for ch, title, color in channels:
        daily = (~frame[ch + '_valid']).resample('1D').mean() * 100
        axes[0].plot(daily.index, daily, color=color, lw=1.4, label=ch.upper())
    axes[0].set(title='Rejected minute bins by UTC day', ylabel='Rejected (%)', ylim=(0, 100), xlabel='UTC day')
    axes[0].legend(); _dates(axes[0])
    counts = evidence['native_contract']['channels']
    categories = ['Absent timestamps', 'Nonfinite native flux', 'All QC-rejected bins']
    for offset, (ch, _, color) in zip((-.18, .18), channels):
        vals = [evidence['native_contract']['missing_bins'], counts[ch]['nonfinite_raw_bins'], counts[ch]['quality_rejected_bins']]
        bars = axes[1].barh(np.arange(3) + offset, vals, height=.32, color=color, label=ch.upper())
        axes[1].bar_label(bars, padding=4, fontsize=10)
    axes[1].set(yticks=np.arange(3), yticklabels=categories, xlabel='Minute bins', xlim=(0, 5600),
                title='Missing records ≠ rejected measurements')
    axes[1].legend(loc='lower right'); axes[1].grid(axis='x', color='#dce4e8')
    fig.suptitle(period + ' | no duplicates; no imputation')
    _save(fig, destination, 'eda_data_quality', 'There are zero absent/duplicate timestamps; nonfinite native '
          'flux is a subset of all rejected bins, so bars are not additive. QC also tests status, '
          'channel-specific electron bits, valid range and averaged-measurement count.', source, entries)
    return entries


def comparison_figures(summary, evidence, destination):
    style(); entries = []; rows = evidence['grouped']
    source = [x['path'] for x in evidence['sources']]
    present = [k for k in ORDER if k in rows and 'mean_pinball' in rows[k]]
    for metric, stem, xlabel in (('mean_pinball', 'comparison_pinball', 'Mean five-quantile pinball loss (dex)'),
                                  ('log_mae', 'comparison_log_mae', 'MAE of log median forecast (dex)')):
        fig, ax = plt.subplots(figsize=(12.5, 6.7), layout='constrained')
        values = [rows[k][metric] for k in present]
        bars = ax.barh(np.arange(len(present)), values, color=[COLORS[k] for k in present], height=.66)
        ax.bar_label(bars, labels=[f'{v:.6f}' for v in values], padding=5, fontsize=10)
        ax.set(yticks=np.arange(len(present)), yticklabels=[LABELS[k] for k in present], xlabel=xlabel,
               xlim=(0, max(values) * 1.19), title='August 2024 · common support · lower is better')
        ax.invert_yaxis(); ax.grid(axis='x', color='#dce4e8'); ax.set_axisbelow(True)
        fig.supxlabel('* XRS-A optimizer flag 8; † GJR near stationarity boundary · seed means are losses, not ensembles', fontsize=10)
        _save(fig, destination, stem, f'{xlabel}; 1,436 origins × 30 leads × two channels. '
              'Neural bars average the three fitted-seed scores. Axes start at zero; no confidence '
              'interval over seed populations is implied. See comparator optimizer qualifications.', source, entries)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.1), layout='constrained')
    picks = ['arima(2,1,0)', 'ar1-gjr-garch(1,1)-t', 'supervised', 'jepa_finetune']
    for ax, metric, ylabel in zip(axes, ('mean_pinball', 'log_mae'), ('Mean pinball (dex)', 'Log MAE (dex)')):
        for k, color in zip(picks, (ORANGE, PURPLE, BLUE, GREEN)):
            ax.plot(np.arange(1, 31), rows[k]['by_lead'][metric], label=LABELS[k].replace(' (3-seed mean)', ''), color=color, lw=2)
        ax.set(xlabel='Lead (minutes to target-bin end)', ylabel=ylabel, ylim=(0, None)); ax.grid(color='#dce4e8')
    axes[0].legend(fontsize=9); fig.suptitle('August 2024 · error grows with forecast horizon')
    _save(fig, destination, 'comparison_lead_errors', 'Equal-channel per-lead losses; neural curves average '
          'three fitted-seed losses. Fine-tuned JEPA has higher pinball than GJR at leads 1–5 despite '
          'lower aggregate loss. Lead 1 predicts the minute bin starting at issue time and ending one minute later.', source, entries)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.7), sharey=True, layout='constrained')
    for ax, label, nominal in zip(axes, ('central_50', 'central_90'), (50, 90)):
        ax.barh(np.arange(len(present)), [100 * rows[k]['coverage_' + label] for k in present],
                color=[COLORS[k] for k in present], height=.66)
        ax.axvline(nominal, color=INK, ls='--', label=f'Nominal {nominal}%')
        ax.set(xlim=(0, 100), xlabel='Achieved cell coverage (%)', title=f'Central {nominal}% interval')
        ax.legend(fontsize=10); ax.grid(axis='x', color='#dce4e8'); ax.set_axisbelow(True)
    axes[0].set_yticks(np.arange(len(present)), [LABELS[k] for k in present]); axes[0].invert_yaxis()
    fig.suptitle('August 2024 · calibration must be read together with interval width')
    _save(fig, destination, 'comparison_coverage', 'Marginal coverage pools channels/leads and averages '
          'neural-seed coverages. It is not simultaneous trajectory coverage. Fine-tuned JEPA pooled '
          '90% coverage (89.72%) hides XRS-A 87.03% versus XRS-B 92.41%; widths are in the comparison table.', source, entries)

    paired = {r['contrast']: r for r in evidence['paired_daily_bootstrap']}
    labels = ['Seed 17', 'Seed 29', 'Seed 43', 'All three seeds', 'Omit seed 43']
    keys = ['seed17', 'seed29', 'seed43', 'all_three', 'omit_seed43']
    fig, ax = plt.subplots(figsize=(11, 5.1), layout='constrained')
    for i, key in enumerate(keys):
        r = paired[key]; mean = r['mean_difference']; low, high = r['ci95']
        ax.errorbar(mean, i, xerr=[[mean-low], [high-mean]], fmt='o', capsize=5,
                    color=GREEN if mean < 0 else ORANGE, markersize=8)
    ax.axvline(0, color=INK, lw=1); ax.axhline(2.5, color='#b7c4cc', lw=.8)
    ax.set(yticks=np.arange(5), yticklabels=labels, xlabel='JEPA − supervised mean pinball (dex)',
           title='Small average gain depends on seed 43 · August 2024')
    ax.invert_yaxis(); ax.grid(axis='x', color='#dce4e8'); ax.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
    fig.supxlabel('Negative favours fine-tuned JEPA · 95% paired daily-block intervals condition on fitted seeds', fontsize=11)
    _save(fig, destination, 'jepa_seed_comparison', 'Paired seed differences and mean-loss contrasts with '
          '2,000 UTC-day bootstrap draws (seed 17; 31 days). Excluding seed 43 reverses the aggregate '
          'direction. This influence diagnostic is exploratory, not a reason to discard seed 43.', source, entries)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
    for seed, color in zip(SEEDS, (BLUE, ORANGE, PURPLE)):
        record = summary['fits'][f'jepa_finetune_seed{seed}']['record']
        history = record['pretrain_history']
        axes[0].plot([x['epoch'] for x in history], [x['train_jepa_loss'] for x in history],
                     marker='o', color=color, label=f'Seed {seed}')
    for family, color in (('supervised', BLUE), ('jepa_finetune', GREEN), ('jepa_frozen', PURPLE)):
        for seed in SEEDS:
            record = summary['fits'][f'{family}_seed{seed}']['record']; h = record['finetune_history']
            axes[1].plot([x['epoch'] for x in h], [x['validation_pinball'] for x in h],
                         color=color, alpha=.7, lw=1.3, label=LABELS[family].split(' (')[0] if seed == 17 else None)
    axes[0].set(title='JEPA pretraining · training data only', xlabel='Pretraining epoch', ylabel='Smooth-L1 latent loss', ylim=(0, None))
    axes[1].set(title='Downstream validation · all fitted seeds', xlabel='Downstream epoch', ylabel='Pinball in standardized log space', ylim=(0, None))
    for ax in axes: ax.legend(fontsize=9); ax.grid(color='#dce4e8')
    fig.suptitle('Saved V1 histories · declining loss does not establish representation utility')
    _save(fig, destination, 'jepa_training_curves', 'Compact rendering of all three pretraining histories '
          'and all nine downstream validation histories. Latent loss and standardized validation '
          'pinball use different units; neither is the held-out dex score.', source, entries)
    return entries


def architecture_figure(destination):
    style(); entries = []
    fig, ax = plt.subplots(figsize=(15, 8)); ax.set(xlim=(0, 15), ylim=(0, 8)); ax.axis('off')
    def box(x, y, w, h, title, detail, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.12',
                                   facecolor=color, edgecolor='#aec1cc', lw=1))
        ax.text(x+w/2, y+h*.68, title, ha='center', va='center', fontsize=13, weight='bold')
        ax.text(x+w/2, y+h*.31, detail, ha='center', va='center', fontsize=11)
    def arrow(a, b, label=''):
        ax.annotate('', xy=b, xytext=a, arrowprops=dict(arrowstyle='->', color=INK, lw=1.6))
        if label: ax.text((a[0]+b[0])/2, (a[1]+b[1])/2+.14, label, ha='center', fontsize=10)
    ax.text(.15, 7.55, 'Temporal JEPA in V1: learn representations, then forecast quantiles', fontsize=19, weight='bold')
    ax.text(.15, 7.1, 'PRETRAINING · training partition only', fontsize=12, color=MUTED, weight='bold')
    box(.2, 5.2, 3, 1.4, 'Training window\n150 minutes', '120 context + 30 future min\n5-min patches; values + masks', '#edf5f9')
    box(4.1, 5.2, 3.1, 1.4, 'Student encoder\n+ predictor', 'Hide 4 context + 6 future\nPredict hidden embeddings', '#e7f2ee')
    box(8.3, 5.2, 2.7, 1.4, 'EMA target encoder', 'All 150 min; no gradients\nEMA .996 → 1', '#f3edf8')
    box(12, 5.2, 2.6, 1.4, 'Latent training loss', 'Smooth-L1 latent loss\nHidden patches only', '#fcf0e5')
    arrow((3.32, 5.9), (3.95, 5.9))
    ax.plot([5.6, 5.6, 13.3], [5.08, 4.88, 4.88], color=INK, lw=1.4)
    arrow((13.3, 4.88), (13.3, 5.08))
    arrow((11.12, 6.2), (11.85, 6.2))
    ax.annotate('', xy=(8.15, 6.05), xytext=(7.35, 6.05),
                arrowprops=dict(arrowstyle='->', color=MUTED, lw=1.3, ls='--'))
    ax.text(7.75, 6.28, 'EMA', ha='center', fontsize=9)
    ax.plot([1.6, 1.6, 9.65, 9.65], [6.72, 6.9, 6.9, 6.72], color=MUTED, lw=1)
    ax.text(.15, 4.55, 'DOWNSTREAM FORECASTING · observed context only at inference', fontsize=12, color=MUTED, weight='bold')
    boxes = [(.2, 2.9, 2.5, 'Observed context', '120 minutes × 2 channels\nTrain-normalized log flux', '#edf5f9'),
             (3.3, 2.9, 2.5, 'Context encoder', '24 patches · width 32\n3 layers · 4 heads', '#e7f2ee'),
             (6.4, 2.9, 2.5, 'Latent predictor', '2 Transformer layers\n6 future mask queries', '#e7f2ee'),
             (9.5, 2.9, 2.3, 'Quantile head', 'Mean context + future\n128 hidden units', '#fcf0e5'),
             (12.4, 2.9, 2.2, 'Direct forecasts', '30 min × 2 channels\n5 ordered quantiles', '#edf5f9')]
    for x, y, w, title, detail, color in boxes: box(x, y, w, 1.35, title, detail, color)
    for a, b in zip(boxes, boxes[1:]): arrow((a[0]+a[2]+.12, 3.57), (b[0]-.15, 3.57))
    ax.plot([4.55, 4.55, 10.65, 10.65], [2.77, 2.45, 2.45, 2.77], color=MUTED, lw=1)
    ax.text(7.6, 2.25, 'Head also receives the mean observed-context embedding', ha='center', fontsize=10)
    ax.text(.3, 1.58, 'Supervised control: same architecture; skip pretraining', color=BLUE, fontsize=13)
    ax.text(.3, 1.12, 'Frozen JEPA: freeze encoder + predictor; train head only', color=PURPLE, fontsize=13)
    ax.text(.3, .66, 'Fine-tuned JEPA: train encoder + predictor + head with pinball loss', color=GREEN, fontsize=13)
    ax.text(10.3, 1.25, 'Quantiles: .05 / .25 / .50 / .75 / .95\nMedian is the point forecast\nTeacher is unused at inference', ha='center', fontsize=11)
    _save(fig, destination, 'jepa_architecture', 'Verified V1 computation graph. EMA updates copy student '
          'encoder parameters into the teacher after pretraining steps. The downstream head uses '
          'softplus cumulative increments for ordered quantiles. Fine-tuning auxiliary JEPA weight is zero. '
          'No physical dynamics constraint, neural autoregressive rollout or joint trajectory sampler is implemented.',
          ['src/solar_flare_jepa/training/jepa.py', 'configs/experiments/v1_models.json'], entries)
    return entries
