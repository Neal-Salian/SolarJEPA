"""Descriptive reference-data EDA. No fitting, forecasting or training labels."""
import numpy as np
import pandas as pd
from .goes import backward_log_derivative


def _counts(series):
    return {str(k):int(v) for k,v in series.value_counts(dropna=False).items()}


def summarize(frame: pd.DataFrame) -> dict:
    if frame.empty or frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError('EDA requires nonempty, sorted unique timestamps')
    dt = frame.index.to_series().diff().dt.total_seconds().dropna()
    grid = pd.date_range(frame.index.min(), frame.index.max(), freq='60s')
    report = dict(dataset_role='external_reference_validation_not_aditya', rows=len(frame),
        time_start=str(frame.index.min()), time_end_exclusive=str(frame.time_end.max()),
        cadence_seconds_counts=_counts(dt), absent_grid_rows=len(grid.difference(frame.index)),
        largest_time_step_seconds=float(dt.max()) if len(dt) else None,
        electron_correction_flag_counts=_counts(frame.electron_correction_flag), channels={})
    for ch in ['xrsa','xrsb']:
        flux = frame[ch+'_flux']
        derivative = backward_log_derivative(flux)
        raw = frame[ch+'_flux_raw']
        # Include absent rows in longest unavailable run, never interpolate.
        missing = flux.reindex(grid).isna()
        groups = (missing != missing.shift()).cumsum()
        longest = int(missing.groupby(groups).sum().max())
        report['channels'][ch] = dict(valid_rows=int(flux.notna().sum()),
            invalid_present_rows=int(flux.isna().sum()),
            raw_nonfinite_rows=int((~np.isfinite(raw)).sum()),
            raw_nonpositive_rows=int((raw <= 0).sum()),
            longest_unavailable_minutes=longest,
            status_flag_counts=_counts(frame[ch+'_flag']),
            exposure_count_min=float(frame[ch+'_num'].min()),
            exposure_count_max=float(frame[ch+'_num'].max()),
            minimum_flux_w_m2=float(flux.min()), maximum_flux_w_m2=float(flux.max()),
            flux_quantiles={str(q):float(v) for q,v in flux.quantile([0.01,0.5,0.95,0.99]).items()},
            log10_flux_quantiles={str(q):float(v) for q,v in np.log10(flux).quantile([0.01,0.5,0.95,0.99]).items()},
            derivative_valid_pairs=int(derivative.notna().sum()),
            derivative_quantiles_per_second={str(q):float(v) for q,v in derivative.quantile([0.01,0.5,0.99]).items()})
    good = frame[['xrsa_flux','xrsb_flux']].dropna()
    report['same_instrument_xrsa_xrsb_log_correlation'] = float(np.log10(good).corr().iloc[0,1]) if len(good)>1 else None
    report['aditya_cross_instrument_alignment'] = 'unavailable: no SoLEXS or ASPEX files'
    report['threshold_minutes_not_event_counts'] = {
        'xrsb_ge_M1':int((frame.xrsb_flux >= 1e-5).sum()),
        'xrsb_ge_X1':int((frame.xrsb_flux >= 1e-4).sum())}
    return report


def summarize_events(records: pd.DataFrame) -> dict:
    if records.empty:
        return {'state_records':0, 'status':'no_catalogue_supplied'}
    required = {'EVENT_START','EVENT_PEAK','EVENT_END'}
    groups = records.groupby('flare_id').status.agg(set)
    incomplete = [int(i) for i,states in groups.items() if not required.issubset(states)]
    peaks = records[records.status == 'EVENT_PEAK'].drop_duplicates('flare_id')
    return dict(state_records=len(records), distinct_event_ids=int(len(groups)),
        events_with_start_peak_end=len(groups)-len(incomplete), incomplete_event_ids=incomplete,
        status_counts=_counts(records.status),
        peak_classes=_counts(peaks.flare_class.str[0]),
        peak_examples=peaks[['flare_id','time','flare_class','xrsb_flux']].sort_values(
            'xrsb_flux', ascending=False).head(5).to_dict('records'),
        note='Catalogue state grouping for EDA only; no onset targets or label maturity implemented')


def plot_reference(frame, events, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), constrained_layout=True)
    for ch,color in [('xrsa','#246da8'), ('xrsb','#d65b28')]:
        axes[0].plot(frame.index, frame[ch+'_flux'], label=ch.upper(), lw=0.7, color=color)
        axes[1].plot(frame.index, frame[ch+'_log10_flux'], label=ch.upper(), lw=0.7, color=color)
        axes[2].plot(frame.index, frame[ch+'_dlog10_dt'], lw=0.5, color=color)
    axes[0].set(ylabel='Flux (W m$^{-2}$)', title='GOES-16 reference sample — not Aditya-L1')
    axes[1].set(ylabel='log10(F / 1 W m$^{-2}$)')
    axes[2].set(ylabel='Backward d log10(F)/dt (s$^{-1}$)', xlabel='UTC (bin start)')
    axes[0].legend()
    fig.savefig(output/'time_series.png', dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for ch in ['xrsa','xrsb']:
        axes[0,0].hist(frame[ch+'_flux'].dropna(), bins=60, histtype='step', label=ch.upper())
        axes[0,1].hist(frame[ch+'_log10_flux'].dropna(), bins=60, histtype='step', label=ch.upper())
        axes[1,0].hist(frame[ch+'_dlog10_dt'].dropna(), bins=60, histtype='step', label=ch.upper())
        missing = frame[ch+'_flux'].isna().resample('6h').mean()
        axes[1,1].plot(missing.index, missing.values, marker='o', label=ch.upper())
    axes[0,0].set(xlabel='Flux (W m$^{-2}$)', ylabel='Present valid samples')
    axes[0,1].set(xlabel='log10(F / 1 W m$^{-2}$)')
    axes[1,0].set(xlabel='Backward log-flux derivative (s$^{-1}$)', ylabel='Valid adjacent pairs')
    axes[1,1].set(xlabel='UTC', ylabel='Invalid fraction of present rows', ylim=(-0.02,1.02))
    axes[0,0].legend()
    fig.suptitle('Descriptive distributions and quality — no imputation')
    fig.savefig(output/'distributions_quality.png', dpi=150)
    plt.close(fig)

    dt = frame.index.to_series().diff().dt.total_seconds().dropna()
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    counts = dt.value_counts().sort_index()
    ax.bar([str(v) for v in counts.index], counts.values, color='#246da8')
    ax.set(xlabel='Elapsed seconds between records', ylabel='Count', title='Observed sampling cadence')
    fig.savefig(output/'cadence.png', dpi=150)
    plt.close(fig)

    if not events.empty and (events.status == 'EVENT_PEAK').any():
        peak = events[events.status == 'EVENT_PEAK'].sort_values('xrsb_flux').iloc[-1]
        t = peak.time
        sub = frame.loc[t-pd.Timedelta('1h'):t+pd.Timedelta('2h')]
        fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
        ax.plot(sub.index, sub.xrsb_flux, color='#d65b28', label='XRS-B observed')
        group = events[events.flare_id == peak.flare_id]
        for row in group.itertuples():
            if row.status in ['EVENT_START','EVENT_PEAK','EVENT_END']:
                ax.axvline(row.time, ls='--', alpha=0.6, label=row.status)
        ax.set(ylabel='Flux (W m$^{-2}$)', xlabel='UTC',
               title=f'Catalogue example {peak.flare_class} — selected largest sample peak, not a forecast')
        ax.legend(fontsize=8)
        fig.savefig(output/'event_example.png', dpi=150)
        plt.close(fig)
