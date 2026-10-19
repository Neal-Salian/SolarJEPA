"""Thin renderers for verified time-series evidence and saved-parameter inference."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from .charts import COLORS, _style

CHANNELS = ("xrsa", "xrsb")


def _vector(values) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Missing or nonfinite verified chart values")
    return values


def _times(values) -> pd.DatetimeIndex:
    if not values or any(pd.Timestamp(value).tzinfo is None for value in values):
        raise ValueError("Chart timestamps require explicit UTC offsets")
    index = pd.DatetimeIndex(pd.to_datetime(values, utc=True))
    if index.hasnans or index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError("Chart timestamps must be unique and ordered")
    return index


def scatter_figure(payload: dict) -> go.Figure:
    x, y = _vector(payload["xrsa"]), _vector(payload["xrsb"])
    if x.shape != y.shape:
        raise ValueError("Paired channel scatter requires aligned observations")
    figure = go.Figure(go.Scattergl(
        x=x, y=y, mode="markers", name="Jointly valid minute pairs",
        marker=dict(color=COLORS["xrsa"], size=3, opacity=.3),
        hovertemplate="XRS-A: %{x:.4f} dex<br>XRS-B: %{y:.4f} dex<extra></extra>",
    ))
    _style(figure)
    figure.update_layout(hovermode="closest", showlegend=False)
    figure.update_xaxes(title_text="XRS-A · log₁₀(flux / [1 W/m²])")
    figure.update_yaxes(title_text="XRS-B · log₁₀(flux / [1 W/m²])")
    return figure


def qq_figure(payload: dict) -> go.Figure:
    figure = make_subplots(rows=1, cols=2, subplot_titles=("XRS-A", "XRS-B"), horizontal_spacing=.12)
    for column, channel in enumerate(CHANNELS, 1):
        saved = payload[channel]
        x, y = _vector(saved["theoretical"]), _vector(saved["observed"])
        if x.shape != y.shape:
            raise ValueError("Normal QQ quantiles must be paired")
        reference = float(saved["intercept"]) + float(saved["slope"]) * x
        if not np.isfinite(reference).all():
            raise ValueError("Invalid saved Normal QQ reference")
        figure.add_trace(go.Scatter(x=x, y=y, mode="markers", name="Observed quantiles",
                                   marker=dict(color=COLORS[channel], size=4), showlegend=False), row=1, col=column)
        figure.add_trace(go.Scatter(x=x, y=reference, mode="lines", name="Fitted Normal reference",
                                   line=dict(color="#91A4BF", dash="dash"), showlegend=False), row=1, col=column)
        figure.update_xaxes(title_text="Theoretical standard Normal quantile", row=1, col=column)
        figure.update_yaxes(title_text="Observed log₁₀ flux · dex", row=1, col=column)
    _style(figure, height=390)
    figure.update_layout(hovermode="closest")
    return figure


def decomposition_figure(payload: dict, channel: str) -> go.Figure:
    if channel not in CHANNELS:
        raise ValueError("Unsupported solar X-ray channel")
    titles = ("Observed", "Trend", "Seasonal component", "Residual")
    figure = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=titles, vertical_spacing=.07)
    times = _times(payload["display"]["time_utc"])
    for row, (field, title) in enumerate(zip(("observed", "trend", "seasonal", "residual"), titles), 1):
        values = _vector(payload["display"][channel][field])
        if len(values) != len(times):
            raise ValueError("STL values and timestamps must align")
        figure.add_trace(go.Scatter(x=times.to_pydatetime(), y=values, name=title, mode="lines",
                                   connectgaps=False, line=dict(color=COLORS[channel], width=1.2),
                                   showlegend=False), row=row, col=1)
        figure.update_yaxes(title_text="dex", row=row, col=1)
    _style(figure, height=720)
    figure.update_xaxes(title_text="Original minute-bin start · UTC", row=4, col=1)
    figure.update_layout(meta=dict(channel=channel, assumed_period_minutes=payload["period_minutes"]))
    return figure


def _native_frame(payload) -> pd.DataFrame:
    columns = [channel + "_flux" for channel in CHANNELS]
    if isinstance(payload, pd.DataFrame):
        frame = payload.copy()
        if list(frame.columns) != columns or not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
            raise ValueError("Forecast requires named native channels and UTC timestamps")
        frame.index = frame.index.tz_convert("UTC")
    else:
        frame = pd.DataFrame({column: _vector(payload[column]) for column in columns}, index=_times(payload["time_utc"]))
    values = frame.to_numpy(float)
    if frame.empty or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Native flux overlay requires positive finite observations and predictions")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("Native overlay timestamps must align in increasing order")
    return frame


def deployment_figure(payload: dict, forecast: pd.DataFrame | None = None) -> go.Figure:
    context, actual = _native_frame(payload["context"]), _native_frame(payload["actual"])
    predicted = _native_frame(payload["forecast"] if forecast is None else forecast)
    issue = pd.Timestamp(payload["issue_utc"])
    if (issue.tzinfo is None or not actual.index.equals(predicted.index)
            or actual.index[0] != issue or context.index[-1] >= issue):
        raise ValueError("Forecast, realized targets and issue time must align")
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("XRS-A", "XRS-B"), vertical_spacing=.14)
    for row, channel in enumerate(CHANNELS, 1):
        for frame, name, color, dash in (
            (context, "Observed context", "#91A4BF", "solid"),
            (actual, "Realized future", COLORS[channel], "solid"),
            (predicted, "Saved-model forecast", "#F4BD70", "dash"),
        ):
            figure.add_trace(go.Scatter(x=frame.index.to_pydatetime(), y=frame[channel + "_flux"],
                mode="lines", name=name, legendgroup=name, showlegend=row == 1, connectgaps=False,
                line=dict(color=color, dash=dash, width=1.6),
                hovertemplate="%{x|%d %b %Y %H:%M} UTC<br>%{y:.5e} W/m²<extra>%{fullData.name}</extra>"), row=row, col=1)
        figure.update_yaxes(title_text="Flux · W/m²", type="log", row=row, col=1)
    _style(figure, height=570)
    figure.add_vline(x=issue.isoformat(), line_dash="dot", line_color="#91A4BF")
    figure.update_xaxes(title_text="Minute / target-bin start · UTC", row=2, col=1)
    return figure


def _plot(figure: go.Figure, key: str) -> None:
    st.plotly_chart(figure, use_container_width=True, theme=None,
                   config={"displayModeBar": False, "responsive": True}, key=key)


def _evidence(root: Path) -> dict:
    from solar_flare_jepa.presentation.time_series import load_evidence
    try:
        return load_evidence(root)
    except ValueError as error:
        reason = str(error).removesuffix(
            '. Restore pinned local data and run scripts/build_time_series_presentation.py.')
        raise ValueError(reason + '. Restore the original pinned payload and sources; '
                         'see docs/STABLE_BASELINE_V0_1_RUN.md.') from error


def _provenance(evidence: dict) -> None:
    with st.expander("Time-series report source and methods", expanded=False):
        st.caption("Source: docs/presentation/time_series_evidence.json; its pinned local diagnostic payload is hash-verified before display.")
        st.json({"dataset": evidence["dataset"], "classical_training": evidence["classical"]["training"],
                 "selection": evidence["classical"]["selection"],
                 "decomposition_method": evidence["decomposition"]["method"]}, expanded=False)


def render_explorer(root: Path) -> None:
    evidence = _evidence(root)
    st.markdown("#### Full May–August report · descriptive statistics")
    st.caption("This verified report uses all four May–August selections. It is distinct from the May–June plots above. "
               "Raw statistics use W/m²; log statistics use log₁₀(flux / [1 W/m²]). Each channel uses its own quality-valid mask. "
               "Standard deviation is the sample statistic (ddof=1).")
    st.dataframe(pd.DataFrame(evidence["eda"]["statistics"]).rename(columns={
        "channel": "Channel", "transform": "Transform", "units": "Units", "count": "Valid minutes",
        "mean": "Mean", "median": "Median", "std": "Standard deviation", "min": "Minimum",
        "q25": "25%", "q75": "75%", "max": "Maximum", "absent_bins": "Absent bins",
        "rejected_present_bins": "Rejected present bins", "nonfinite_raw_bins": "Nonfinite raw bins",
    }), hide_index=True, width="stretch", column_config={
        name: st.column_config.NumberColumn(name, format="%.5g")
        for name in ("Mean", "Median", "Standard deviation", "Minimum", "25%", "75%", "Maximum")})
    st.caption(evidence["eda"]["missing_policy"])
    st.markdown("#### Paired channel scatter · full report")
    scatter = evidence["eda"]["scatter"]
    _plot(scatter_figure(scatter), "full_scope_scatter")
    st.caption(f"Jointly quality-valid timestamp pairs: {scatter['total_pairs']:,}; deterministic display subset: "
               f"{scatter['display_pairs']:,}. Pairing is by the same minute, with no interpolation. "
               "Association between channels does not establish causation or forecasting skill.")
    st.markdown("#### Normal QQ plots · log₁₀ flux")
    _plot(qq_figure(evidence["eda"]["qq"]), "full_scope_qq")
    st.caption("Saved ordered log-flux quantiles versus standard Normal quantiles, with fitted reference lines. "
               "Curvature and tail departures diagnose distributional mismatch; serially dependent minute observations "
               "do not justify an independent-sample normality claim. QQ plots do not establish stationarity.")
    _provenance(evidence)


def render_analysis(root: Path, channel: str) -> None:
    st.markdown("#### Reading dependence and model orders")
    st.write("ACF measures correlation with earlier values; PACF measures the additional linear association at a lag "
             "after accounting for intervening lags. For a stationary series, a PACF cutoff can suggest AR order p, "
             "and an ACF cutoff can suggest MA order q. Mixed ARMA processes often have decaying ACF and PACF; "
             "these patterns are guides, not an automatic order-selection rule.")
    st.caption("ARIMA(p,d,q): p autoregressive lags, d ordinary differences, q moving-average error lags. "
               "SARIMA(p,d,q)(P,D,Q)ₛ adds seasonal autoregressive order P, seasonal differencing D, "
               "seasonal moving-average order Q and period s in observation steps. At minute cadence, s=1440 assumes a daily cycle. "
               "Differencing changes the series being modeled; stationarity tests and residual checks still matter.")
    evidence = _evidence(root)
    saved = evidence["decomposition"]
    st.markdown("#### Exploratory STL · contiguous training segment")
    _plot(decomposition_figure(saved, channel), "training_stl")
    st.caption(f"XRS-{channel[-1].upper()} · {saved['start_utc']} to {saved['end_exclusive_utc']} (end exclusive); "
               f"{saved['rows']:,} contiguous valid minute bins. {saved['method']}. "
               f"The period of {saved['period_minutes']:,} minutes is an assumed daily-cycle diagnostic; "
               "the seasonal component is not evidence of physical solar seasonality. "
               "Observed = trend + seasonal + residual in log₁₀ flux; no imputation or concatenation across gaps.")
    st.caption("The plotted components are a bounded display of saved calculations at original timestamps. "
               "STL uses the full selected training segment and is descriptive; its trend is not an issue-time forecast.")
    st.caption("A daily cycle is a prespecified candidate to inspect at minute cadence, not a measured solar period. "
               "ACF of first log₁₀ differences at lag 1,440 min: " + "; ".join(
                   f"XRS-{ch[-1].upper()} {saved['daily_acf'][ch]:.5f}" for ch in CHANNELS) + ". "
               "Reliable stable seasonality is not established in this short segment with changing solar activity.")
    st.caption(saved["limitations"])
    st.caption("SARIMA status: " + evidence["classical"]["sarima_status"] + ". " + evidence["classical"]["sarima_reason"])
    _provenance(evidence)


def render_models(root: Path) -> None:
    evidence = _evidence(root)
    classical, deployment = evidence["classical"], evidence["deployment"]
    st.markdown("#### Classical model identification · separate training demo")
    training = classical["training"]
    st.caption(f"Fit support: {training['start_utc']} to {training['end_exclusive_utc']} (end exclusive), "
               f"{training['rows']:,} consecutive training minutes. This bounded demonstration is separate from the archived V1 benchmark.")
    st.markdown("**AIC/BIC compare training likelihood with a complexity penalty; lower is preferred within a compatible group.**")
    st.caption("Compare only rows within the same channel and comparison group, which holds differencing, trend "
               "and likelihood support compatible. AIC/BIC values from different groups are not a common ranking. "
               "They are training criteria, distinct from out-of-sample forecast errors. "
               "BIC's per-parameter complexity penalty grows with sample size and exceeds AIC's when log(n) > 2.")
    candidates = pd.DataFrame(classical["candidates"])
    for (channel, group), rows in candidates.groupby(["channel", "comparison_group"], sort=False, dropna=False):
        group_label = str(group) if pd.notna(group) else "unavailable (failed fit)"
        with st.expander(f"XRS-{channel[-1].upper()} · likelihood group {group_label}", expanded=False):
            display = rows[["family", "order", "aic", "bic", "fit_status"]].copy()
            display["order"] = display["order"].map(str)
            st.dataframe(display.rename(columns={"family": "Family", "order": "(p,d,q)", "aic": "AIC",
                "bic": "BIC", "fit_status": "Fit status"}), hide_index=True, width="stretch")
    st.caption("Selection: " + classical["selection"] + ". " + "; ".join(
        f"XRS-{channel[-1].upper()} order {tuple(classical['selected'][channel]['order'])}" for channel in CHANNELS))
    st.caption("SARIMA status: " + classical["sarima_status"] + ". " + classical["sarima_reason"])
    st.markdown("**Candidate forecast errors · the same single held-out origin**")
    errors = candidates[["channel", "family", "order", "fit_status", "log_mae", "log_rmse"]].copy()
    errors["order"] = errors["order"].map(str)
    st.dataframe(errors.rename(columns={"channel": "Channel", "family": "Family", "order": "(p,d,q)",
        "fit_status": "Fit status", "log_mae": "Log MAE (dex)", "log_rmse": "Log RMSE (dex)"}),
        hide_index=True, width="stretch", column_config={name: st.column_config.NumberColumn(name, format="%.6f")
            for name in ("Log MAE (dex)", "Log RMSE (dex)")})
    st.caption("These errors are displayed after the training-only BIC choice. They do not select the model. "
               "A missing error denotes an unavailable candidate forecast; a single origin is a demonstration, not a benchmark.")
    st.markdown("#### Saved-model inference · observed and forecast flux")
    st.caption("Preview: the verified saved forecast below was produced by applying training-fitted parameters to past context. "
               "The button executes saved-parameter inference again and checks timestamps, predictions and errors against this preview. "
               "No model fitting occurs while rendering or replaying this page.")
    forecast = None
    metrics = deployment["metrics"]
    if st.button("Run saved-model inference", key="saved_model_inference"):
        from solar_flare_jepa.presentation.time_series import replay_deployment
        forecast, metrics = replay_deployment(evidence)
        st.success("Saved-model inference verified against the pinned forecast and metrics.")
    _plot(deployment_figure(deployment, forecast), "classical_deployment")
    st.caption(f"Issue time: {deployment['issue_utc']}; context: {deployment['context_steps']} completed past minute bins; "
               f"horizon: {deployment['horizon_steps']} target bins. The vertical line is issue time. "
               "Plotted timestamps denote target-bin starts: lead 1 starts at issue time and ends one minute later. "
               "Realized future values are shown for retrospective evaluation and are not passed into inference.")
    st.markdown("**Forecast errors · this single held-out origin, log₁₀ flux in dex**")
    st.dataframe(pd.DataFrame([{"Channel": "XRS-" + channel[-1].upper(), "Log MAE (dex)": metrics[channel]["log_mae"],
        "Log RMSE (dex)": metrics[channel]["log_rmse"]} for channel in CHANNELS]), hide_index=True, width="stretch")
    st.caption("A single origin illustrates deployment and alignment; it does not establish general forecasting skill "
               "or a statistically supported advantage. No prediction interval is claimed for this point-forecast demo.")
    _provenance(evidence)
