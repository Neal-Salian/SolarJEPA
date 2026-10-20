"""Plotly presentation builders; all scientific inputs come from dashboard.data."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLORS = {"xrsa": "#41D5E6", "xrsb": "#7A9FFF"}
BACKGROUND = "#0B1220"


def _style(figure: go.Figure, *, height: int = 380) -> go.Figure:
    figure.update_layout(
        template="plotly_dark", paper_bgcolor=BACKGROUND, plot_bgcolor=BACKGROUND,
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", size=13,
                  color="#CAD5E5"), height=height,
        margin=dict(l=18, r=20, t=36, b=24),
        legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#17243A", font_color="#F2F7FF"),
        hovermode="x unified", dragmode="zoom",
    )
    figure.update_xaxes(showgrid=False, zeroline=False, linecolor="#29354A",
                        title_font=dict(size=12), tickfont=dict(size=11))
    figure.update_yaxes(gridcolor="#1C293C", zeroline=False,
                        title_font=dict(size=12), tickfont=dict(size=11))
    return figure


def flux_figure(frame: pd.DataFrame, title: str, *, max_points: int = 2400) -> go.Figure:
    """Original-timestamp min/max envelope, with explicit gaps and physical units."""
    from solar_flare_jepa.dashboard.data import envelope

    if frame.empty or not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("Chart requires timestamped observations")
    figure = go.Figure()
    for channel in ("xrsa", "xrsb"):
        series = frame[channel + "_flux"]
        values = series.to_numpy(dtype=float)
        if np.isinf(values).any() or (values[np.isfinite(values)] <= 0).any():
            raise ValueError("Log-scale chart requires positive finite flux or missing observations")
        if not np.isfinite(values).any():
            raise ValueError("No valid positive observations in selected interval")
        displayed = envelope(series, max_points=max_points)
        figure.add_trace(go.Scatter(
            x=displayed.index.to_pydatetime(), y=displayed.to_numpy(), mode="lines",
            name="XRS-" + channel[-1].upper(), connectgaps=False,
            line=dict(color=COLORS[channel], width=1.3),
            hovertemplate="%{x|%d %b %Y %H:%M} UTC<br>%{y:.3e} W/m²<extra>%{fullData.name}</extra>",
        ))
    _style(figure, height=410)
    figure.update_xaxes(title_text="Observation time · UTC", tickformat="%d %b")
    figure.update_yaxes(title_text="Solar X-ray flux · W/m²", type="log", exponentformat="power")
    figure.update_layout(meta=dict(title=title, downsampling="original extrema; explicit NaN gaps"))
    return figure


def histogram_figure(payload: dict) -> go.Figure:
    """Render exact precomputed log10-bin counts without statistical recomputation."""
    figure = go.Figure()
    for channel in ("xrsa", "xrsb"):
        counts = np.asarray(payload[channel]["counts"])
        edges = np.asarray(payload[channel]["edges"], dtype=float)
        if (counts.ndim != 1 or edges.ndim != 1 or len(edges) != len(counts) + 1
                or len(counts) == 0 or not np.isfinite(edges).all()
                or not np.isfinite(counts).all() or (counts < 0).any()
                or (np.diff(edges) <= 0).any()):
            raise ValueError("Invalid verified histogram bins")
        figure.add_trace(go.Bar(
            x=(edges[:-1] + edges[1:]) / 2, y=counts, width=np.diff(edges),
            customdata=np.column_stack((edges[:-1],edges[1:])),
            name="XRS-" + channel[-1].upper(), marker_color=COLORS[channel], opacity=.7,
            hovertemplate="log₁₀ bin edges: %{customdata[0]:.8f}, %{customdata[1]:.8f}<br>Valid observations: %{y:,}<extra>%{fullData.name}</extra>",
        ))
    _style(figure)
    figure.update_layout(barmode="overlay", hovermode="closest")
    figure.update_xaxes(title_text="log₁₀(flux / [1 W/m²])")
    figure.update_yaxes(title_text="Valid observation count")
    return figure


def dependence_figure(acf: list, pacf: list, channel: str, transform: str) -> go.Figure:
    """Saved correlation coefficients only; no estimation or confidence intervals."""
    figure = make_subplots(rows=1, cols=2, subplot_titles=("Autocorrelation · ACF", "Partial autocorrelation · PACF"),
                           horizontal_spacing=.12)
    for column, values in enumerate((acf, pacf), start=1):
        values = np.asarray(values, dtype=float)
        if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
            raise ValueError("Invalid saved correlation coefficients")
        figure.add_trace(go.Bar(x=np.arange(1,len(values)), y=values[1:],
                               marker_color=COLORS["xrsa" if column == 1 else "xrsb"],
                               showlegend=False, name="ACF" if column == 1 else "PACF",
                               hovertemplate="Lag: %{x} min<br>Coefficient: %{y:.4f}<extra></extra>"),
                         row=1, col=column)
        figure.update_xaxes(title_text="Lag · minutes", row=1, col=column)
        figure.update_yaxes(title_text="Correlation", row=1, col=column, range=[-1.05, 1.05])
    _style(figure, height=365)
    figure.update_layout(hovermode="closest", meta=dict(channel=channel, transform=transform))
    figure.update_annotations(font=dict(size=13, color="#D9E4F5"))
    return figure


def model_figure(frame: pd.DataFrame) -> go.Figure:
    """Comparable archived log-space MAE; model identity labels supplied by loader."""
    if frame.empty or frame["label"].duplicated().any():
        raise ValueError("Missing or ambiguous model comparisons")
    values = frame["log_mae"].to_numpy(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Invalid model MAE")
    ordered = frame.sort_values("log_mae", ascending=False)
    figure = go.Figure(go.Bar(
        x=ordered["log_mae"].to_list(), y=ordered["label"].to_list(), orientation="h",
        marker_color=["#41D5E6" if model.startswith("jepa") else "#7599CF"
                      for model in ordered["model_id"]],
        text=[f"{value:.4f}" for value in ordered["log_mae"]], textposition="outside",
        cliponaxis=False, hovertemplate="%{y}<br>Log-space MAE: %{x:.6f} dex<extra></extra>",
    ))
    _style(figure, height=355)
    figure.update_layout(hovermode="closest", showlegend=False, margin=dict(l=12, r=70, t=14, b=24))
    figure.update_xaxes(title_text="Mean absolute error in log₁₀ flux · dex", range=[0, max(values) * 1.22])
    figure.update_yaxes(title_text=None, showgrid=False, automargin=True)
    return figure
