"""Offline research dashboard with verified historical and saved-model inference."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st

from solar_flare_jepa.dashboard import data, time_series
from solar_flare_jepa.dashboard.charts import (
    dependence_figure, flux_figure, histogram_figure, model_figure,
)

st.set_page_config(page_title="SolarJEPA · Solar X-Ray Research", page_icon="☀", layout="wide")
st.markdown("""
<style>
.stApp { background: #080F1D; }
.block-container { max-width: 1260px; padding-top: 2.5rem; padding-bottom: 3rem; }
h1 { letter-spacing: -0.045em; font-weight: 650 !important; padding-bottom: .1rem !important; }
h2, h3 { letter-spacing: -.02em; }
[data-testid="stSidebar"] { background: #0E192A; border-right: 1px solid #1D2A3D; }
[data-testid="stMetric"] { border-top: 1px solid #25344B; padding-top: 1rem; }
[data-testid="stMetricLabel"] { color: #91A4BF; }
[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 550; }
[data-testid="stCaptionContainer"] { color: #94A7C1; line-height: 1.6; }
[data-testid="stExpander"] { border-color: #25344B; }
[data-testid="stImage"] img { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

PAGES = ("Overview", "Data Explorer", "Time-Series Analysis", "Model Results", "Solar Flux Prediction")
with st.sidebar:
    st.markdown("### SolarJEPA")
    st.caption("SOLAR X-RAY RESEARCH")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("RETROSPECTIVE INFERENCE" if page == "Solar Flux Prediction" else "INTERACTIVE OBSERVATIONS")
    st.markdown("**GOES-16 · XRS**")
    if page == "Solar Flux Prediction":
        st.caption("01–31 August 2024 · UTC\n\nHistorical held-out observations · seed 17")
    else:
        st.caption("01 May – 30 June 2024 · UTC\n\nOne-minute science observations")
    st.divider()
    st.caption("Stable Baseline v0.1 · historical research\n\nLocal evidence · offline operation")
    st.caption("Archived V2 status is context only. V2 pilot, V3 research, live inference and SoLEXS functionality are excluded.")

st.title("SolarJEPA")
st.markdown("<p style='color:#8FA9CA;font-size:1.1rem;margin-top:-.3rem'>Solar X-Ray Time-Series Research</p>",
            unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=2)
def _observations(root: str, registry: dict, source_token: tuple) -> pd.DataFrame:
    return data.load_observations(Path(root), registry)


@st.cache_data(show_spinner=False, max_entries=2)
def _histogram(frame: pd.DataFrame) -> dict:
    return data.histogram(frame)


@st.cache_data(show_spinner=False, max_entries=2)
def _flux_chart(frame: pd.DataFrame, title: str, source_token: tuple):
    return flux_figure(frame, title)


@st.cache_data(show_spinner=False, max_entries=2)
def _summary(frame: pd.DataFrame, source_token: tuple) -> dict:
    return data.dataset_summary(frame)


def observation_token(registry: dict) -> tuple:
    """Invalidate cached data if an explicitly pinned local source changes."""
    data.verify_sources(ROOT, registry, "overview_flux")
    paths = []
    for dataset in registry["datasets"]:
        manifest = ROOT / dataset["manifest"]
        paths.append(manifest)
        content = data.read_json(manifest)
        month = "05" if "202405" in dataset["manifest"] else "06"
        prefix = f"data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/{month}/"
        for row in content["files"]:
            relative = row["path"]
            path = ROOT / relative
            if (not relative.startswith(prefix) or not path.resolve().is_relative_to(ROOT)
                    or ".." in Path(relative).parts):
                raise data.DashboardUnavailable("Unapproved native observation path")
            paths.append(path)
    return tuple((str(path.relative_to(ROOT)), path.stat().st_size,
                  path.stat().st_mtime_ns, path.stat().st_ctime_ns) for path in paths)


def provenance(registry: dict, *entry_ids: str) -> None:
    with st.expander("Scientific source and provenance", expanded=False):
        for entry_id in entry_ids:
            entry = registry["visualizations"][entry_id]
            st.markdown("**" + entry_id.replace("_", " ").capitalize() + "**")
            files = [registry["sources"][key]["path"] for key in entry["sources"]]
            st.caption("Source files: " + "; ".join(files))
            st.json(entry, expanded=False)


def unavailable(error: Exception) -> None:
    st.error("Verified result unavailable")
    st.caption(str(error))


def plot(figure, key: str) -> None:
    st.plotly_chart(figure, use_container_width=True, theme=None,
                    config={"displayModeBar": False, "responsive": True}, key=key)


def period(summary: dict) -> str:
    start = pd.Timestamp(summary["start_utc"])
    end = pd.Timestamp(summary["end_exclusive_utc"]) - pd.Timedelta(minutes=1)
    return f"{start:%d %b %Y %H:%M} – {end:%d %b %Y %H:%M} UTC"


def overview(registry: dict) -> None:
    st.write("Investigating how quality-controlled solar X-ray observations support short-horizon "
             "forecasting, with a focus on representation learning and honest evaluation.")
    token = observation_token(registry)
    frame = _observations(str(ROOT), registry, token)
    data.verify_sources(ROOT, registry, "dataset_summary")
    summary = _summary(frame, token)
    instrument, observations, cadence = st.columns(3)
    instrument.metric("Instrument", "GOES-16 XRS")
    observations.metric("Observed minute records", f"{summary['observed_rows']:,}")
    cadence.metric("Sampling cadence", f"{summary['cadence_seconds']} s")
    st.caption("Dataset scope: " + period(summary) + ". Counts include observed records before channel quality rejection.")
    st.subheader("GOES Solar X-Ray Flux Over Time")
    plot(_flux_chart(frame, "GOES Solar X-Ray Flux Over Time", token), "overview_flux")
    st.caption("XRS-A and XRS-B irradiance in W/m², on a logarithmic axis. Rejected observations remain gaps. "
               "The display retains original local extrema and timestamps; no interpolation or averaging.")
    st.caption("Source: data/manifests/goes_v1_202405.json and goes_v1_202406.json · " + period(summary))
    provenance(registry, "overview_flux", "dataset_summary")
    st.subheader("From observations to evaluation")
    st.markdown("**GOES observations → quality control → time-series preparation → forecasting models → evaluation**")
    data.verify_sources(ROOT, registry, "research_status")
    st.write("The presentation combines verified GOES exploratory analysis and archived V1 evaluation. "
             "V2 infrastructure is implemented; a V2 real-data pilot has not been authorized.")
    provenance(registry, "research_status")


def explorer(registry: dict) -> None:
    st.subheader("Data Explorer")
    st.write("Explore the two solar X-ray channels over the verified May–June observation scope.")
    data.verify_sources(ROOT, registry, "channel_flux")
    token = observation_token(registry)
    frame = _observations(str(ROOT), registry, token)
    summary = _summary(frame, token)
    st.markdown("#### XRS-A and XRS-B comparison")
    plot(_flux_chart(frame, "XRS-A and XRS-B comparison", token), "channel_flux")
    st.caption("Different X-ray bands respond to the same changing solar activity. Channel-specific quality masks "
               "retain missing values. The min/max display envelope preserves rare peaks.")
    st.caption(period(summary) + f" · Valid minutes: XRS-A {summary['xrsa_valid_rows']:,}; "
               f"XRS-B {summary['xrsb_valid_rows']:,}. Source: the two May–June V1 GOES manifests.")
    provenance(registry, "channel_flux")
    st.markdown("#### Flux distribution")
    data.verify_sources(ROOT, registry, "flux_histogram")
    plot(histogram_figure(_histogram(frame)), "flux_histogram")
    st.caption("Dashboard visualization: all positive, finite, quality-valid May–June flux values transformed to "
               "log₁₀(flux / [1 W/m²]); 70 equal-width bins per channel. Counts are minute observations, not independent flares.")
    st.caption("This display uses the EDA's log transformation and bin count on the smaller dashboard scope. "
               "It is not the original May–August histogram.")
    provenance(registry, "flux_histogram")
    time_series.render_explorer(ROOT)


def stationarity_table(rows: list[dict], channel: str) -> pd.DataFrame:
    displayed = []
    for row in rows:
        if row["channel"] != channel:
            continue
        adf_p = row["adf_p_value"]
        adf_display = "Approximation floor (returned 0)" if adf_p == 0 else f"{adf_p:.3g}"
        relation = row["kpss_p_relation"]
        kp_display = f"{relation} {row['kpss_p_value']:.3g}"
        adf_conclusion = "Reject unit root" if adf_p < .05 else "Unit root not rejected"
        kp_reject = relation == "<" or (relation == "=" and row["kpss_p_value"] < .05)
        kp_conclusion = "Reject level stationarity" if kp_reject else "Level stationarity not rejected"
        displayed.append({
            "Transform": {"raw_scaled": "Raw / segment mean", "log_level": "Log₁₀ level",
                          "log_difference": "First log₁₀ difference"}[row["transform"]],
            "ADF statistic": round(row["adf_statistic"], 4), "ADF p (approx.)": adf_display,
            "KPSS statistic": round(row["kpss_statistic"], 4), "KPSS p": kp_display,
            "At 5%": adf_conclusion + "; " + kp_conclusion,
        })
    if not displayed:
        raise data.DashboardUnavailable("No verified stationarity evidence for selected channel")
    return pd.DataFrame(displayed)


def analysis(registry: dict) -> None:
    st.subheader("Time-Series Analysis")
    st.write("Archived diagnostics preserve their original intervals, transformations and estimation methods.")
    st.markdown("#### Rolling statistics · original analysis")
    try:
        sources = data.verify_sources(ROOT, registry, "rolling_statistics")
        image = next(path for path in sources if path.name == "eda_rolling_statistics.png")
        st.image(str(image), width="stretch")
        st.caption("Original EDA interval: 01 May 2024 00:00 – 01 September 2024 00:00 UTC (end exclusive). "
                   "Trailing six-hour mean and sample variance of log₁₀ flux. "
                   "Each window requires 360 consecutive valid minute bins; a rejected minute invalidates that window. "
                   "Units: mean in dex; variance in dex².")
        st.caption("The archived plot reports variance. Verified rolling standard-deviation output is unavailable.")
        provenance(registry, "rolling_statistics")
    except (OSError, ValueError, KeyError, TypeError, StopIteration, RuntimeError) as error:
        unavailable(error)
    st.markdown("#### Autocorrelation and partial autocorrelation")
    diagnostics = data.load_diagnostics(ROOT, registry)
    channel_column, transform_column = st.columns(2)
    channel_label = channel_column.selectbox("Channel", ("XRS-A", "XRS-B"))
    transform_label = transform_column.selectbox("Transformation", ("Log₁₀ level", "First log₁₀ difference"))
    channel = "xrsa" if channel_label == "XRS-A" else "xrsb"
    transform = "log_level" if transform_label == "Log₁₀ level" else "log_difference"
    data.verify_sources(ROOT, registry, "pacf")
    saved = diagnostics["dependence"][channel]
    plot(dependence_figure(saved["acf"][transform], saved["pacf"][transform], channel_label, transform_label),
         "dependence")
    st.caption("Original contiguous training segment: 11 June 2024 16:38 – 18 June 2024 17:47 UTC (end exclusive), "
               "10,149 minute bins. First differences begin at 16:39. ACF: FFT, unadjusted covariance, maximum lag 120 min. "
               "PACF: Yule–Walker MLE (ywm), maximum lag 60 min. No significance bands are asserted.")
    provenance(registry, "acf", "pacf")
    st.markdown("#### Stationarity · limited to this segment")
    st.caption("ADF null: a unit root. KPSS null: level stationarity. Both include a constant; ADF uses fixed 30 lags, "
               "KPSS uses automatic bandwidth. P-values are approximations; inequality signs preserve lookup-table bounds.")
    st.dataframe(stationarity_table(diagnostics["stationarity"], channel), hide_index=True,
                 width="stretch", height=150)
    st.caption("Exact support for raw/scaled and log levels: 11 June 16:38 – 18 June 17:47 UTC, end exclusive. "
               "First log differences: 11 June 16:39 – 18 June 17:47 UTC, end exclusive. "
               "These local tests do not establish global stationarity or validated forecasting inference.")
    provenance(registry, "stationarity")
    time_series.render_analysis(ROOT, channel)


def models(registry: dict) -> None:
    st.subheader("Model Results")
    st.write("A descriptive comparison from the archived V1 evaluation, with identical scored support.")
    comparison = data.load_model_comparison(ROOT, registry)
    contract = comparison.attrs["contract"]
    st.markdown("#### Model comparison · log-space MAE")
    plot(model_figure(comparison), "model_comparison")
    st.caption("Lower is better. Mean absolute error of log₁₀ flux, in dex, over both XRS-A and XRS-B and leads "
               "1–30 minutes. Identical support: 1,436 origins and 86,160 scored channel–lead cells. "
               "The three neural model bars are arithmetic means of losses from seeds 17, 29 and 43; they are not ensembles.")
    st.caption("Experiment: " + contract["experiment_id"] + " · Evaluation period: 01–31 August 2024 UTC. "
               "Source: docs/presentation/model_evidence.json and model_metrics.csv. Only archived aggregates are opened.")
    st.caption("Bar differences are descriptive. Statistical significance and V2 forecasting accuracy remain unvalidated.")
    with st.expander("Exact displayed metrics", expanded=False):
        st.dataframe(comparison[["model_id", "label", "log_mae"]], hide_index=True, width="stretch",
                     column_config={"log_mae": st.column_config.NumberColumn("Log-space MAE (dex)", format="%.8f")})
    provenance(registry, "model_comparison")
    st.markdown("#### Research status")
    data.verify_sources(ROOT, registry, "research_status")
    status = data.read_json(ROOT / "docs/presentation/dashboard_status.json")
    for item in status["items"]:
        st.markdown("- " + item["label"])
    st.caption("Status snapshot: " + status["snapshot_utc"] + ". Infrastructure checks are not forecasting accuracy evidence. "
               "A matched timestamp-level prediction display is omitted from the archived V1 comparison.")
    provenance(registry, "research_status")
    time_series.render_models(ROOT)


try:
    if page == "Solar Flux Prediction":
        from solar_flare_jepa.dashboard.prediction_page import render
        render(ROOT)
    else:
        registry = data.load_registry(ROOT)
        {"Overview": overview, "Data Explorer": explorer,
         "Time-Series Analysis": analysis, "Model Results": models}[page](registry)
except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
    unavailable(error)
