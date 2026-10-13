#!/usr/bin/env python3
"""Render the presentation's scientific figures from verified local evidence.

This script reads the source checkout and scientific files without modifying them.
Run with the evidence checkout's Python environment, for example::

    /path/to/source/.venv/bin/python scripts/presentation/build_charts.py \
        --source-root /path/to/source

PNG figures and a provenance manifest are the only generated outputs. Native
measurements and hydrated diagnostic arrays are never copied into the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import numpy as np
import pandas as pd


BACKGROUND = "#080F1D"
FOREGROUND = "#F1F5FB"
MUTED = "#9AACCA"
GRID = "#26354C"
COLORS = {"xrsa": "#FFAB49", "xrsb": "#4CD9E8"}
CHANNELS = ("xrsa", "xrsb")
LOG_UNITS = "log₁₀(F / (1 W m⁻²))"
REPO = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 16,
        "axes.facecolor": BACKGROUND,
        "figure.facecolor": BACKGROUND,
        "savefig.facecolor": BACKGROUND,
        "text.color": FOREGROUND,
        "axes.labelcolor": FOREGROUND,
        "axes.edgecolor": MUTED,
        "axes.titleweight": "bold",
        "axes.titlesize": 18,
        "axes.labelsize": 16,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 15,
        "ytick.labelsize": 15,
        "legend.labelcolor": FOREGROUND,
        "legend.fontsize": 15,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "grid.alpha": 0.85,
        "lines.linewidth": 1.1,
        "path.simplify": False,
        "axes.unicode_minus": True,
    })


def dates(ax, scope: str, bottom: bool = True) -> None:
    if scope == "months":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz="UTC"))
        label = "UTC · 2024"
    elif scope == "days":
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("Jun %d", tz="UTC"))
        label = "UTC · June 2024"
    else:
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=(0, 30)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
        label = "UTC · 01 August 2024"
    ax.tick_params(axis="x", labelbottom=bottom)
    if bottom:
        ax.set_xlabel(label)


def scientific(ax) -> None:
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((0, 0))
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.get_offset_text().set_size(14)
    ax.yaxis.set_major_locator(MaxNLocator(4))


def channel_title(ax, channel: str, extra: str = "") -> None:
    ax.set_title(channel.upper() + extra, color=COLORS[channel], loc="left", pad=9)


def valid_series(frame: pd.DataFrame, channel: str) -> pd.Series:
    values = frame[channel + "_flux"].astype(float)
    mask = frame.observed & frame[channel + "_valid"] & np.isfinite(values) & (values > 0)
    return values.where(mask)


def build(source_root: Path, output_dir: Path, expected_commit: str, dpi: int) -> dict:
    source_root = source_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_commit = git(source_root, "rev-parse", "HEAD")
    if expected_commit and not source_commit.startswith(expected_commit):
        raise ValueError(f"Unexpected source commit: {source_commit}")
    sys.path.insert(0, str(source_root / "src"))
    from solar_flare_jepa.presentation.time_series import load_evidence, replay_deployment
    from solar_flare_jepa.presentation.eda import load_v1_frame, longest_complete_block

    evidence = load_evidence(source_root)  # Strict report, source and payload identities.
    report_path = source_root / "docs/presentation/time_series_evidence.json"
    identity_path = source_root / "docs/presentation/time_series_identity.json"
    eda_path = source_root / "docs/presentation/eda_evidence.json"
    report = json.loads(report_path.read_text())
    identity = json.loads(identity_path.read_text())
    eda = json.loads(eda_path.read_text())
    frame, native = load_v1_frame(source_root)  # All 123 original source-file hashes.
    dataset = evidence["dataset"]
    assert len(frame) == dataset["rows"] == 177120
    assert native["source_files"] == dataset["source_files"] == 123
    assert native["source_bytes"] == dataset["source_bytes"]
    assert native["manifests"] == dataset["manifests"] == eda["manifests"]
    assert native["native_contract"]["platform"] == eda["native_contract"]["platform"]
    assert native["native_contract"]["instrument"] == eda["native_contract"]["instrument"]
    assert str(frame.index[0]) == str(pd.Timestamp(dataset["start_utc"]))
    assert frame.index[-1] + pd.Timedelta(minutes=1) == pd.Timestamp(dataset["end_exclusive_utc"])
    series = {ch: valid_series(frame, ch) for ch in CHANNELS}
    statistics = evidence["eda"]["statistics"]
    for ch in CHANNELS:
        stored = next(row for row in statistics if row["channel"] == ch and row["transform"] == "raw")
        assert int(series[ch].notna().sum()) == stored["count"]
        assert int((frame.observed & series[ch].isna()).sum()) == stored["rejected_present_bins"]
        np.testing.assert_allclose(series[ch].dropna().mean(), stored["mean"], rtol=1e-12)

    training = dataset["splits"][0]
    block = longest_complete_block(frame, training["start_utc"], training["end_utc"])
    assert len(block) == eda["diagnostic_block"]["rows"] == 10149
    assert block.index[0] == pd.Timestamp(eda["diagnostic_block"]["start_utc"])
    assert block.index[-1] + pd.Timedelta(minutes=1) == pd.Timestamp(eda["diagnostic_block"]["end_exclusive_utc"])
    assert all(valid_series(block, ch).notna().all() for ch in CHANNELS)
    _, replay_metrics = replay_deployment(evidence)
    style()

    source_files = [{"path": entry["path"], "sha256": entry["sha256"]}
                    for entry in identity["sources"]]
    source_files.extend({"path": path.relative_to(source_root).as_posix(), "sha256": sha256(path)}
                        for path in (report_path, identity_path))
    payload = dict(report["payload"])
    charts = []

    def save(fig, name: str, title: str, caption: str, units: str, display_policy: str,
             observations: dict, relevant_files: tuple[str, ...] = ()) -> None:
        target = output_dir / f"chart_{name}.png"
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        canvas_width, canvas_height = fig.canvas.get_width_height()
        # Matplotlib retains nominal tick labels outside the displayed view;
        # those are not drawn and must not be mistaken for clipped labels.
        outside_ticks = set()
        for ax in fig.axes:
            for axis in (ax.xaxis, ax.yaxis):
                low, high = sorted(axis.get_view_interval())
                for tick in [*axis.get_major_ticks(), *axis.get_minor_ticks()]:
                    if not low <= tick.get_loc() <= high:
                        outside_ticks.update((tick.label1, tick.label2))
        for label in fig.findobj(matplotlib.text.Text):
            if label not in outside_ticks and label.get_visible() and label.get_text():
                box = label.get_window_extent(renderer)
                if box.x0 < -.5 or box.y0 < -.5 or box.x1 > canvas_width + .5 or box.y1 > canvas_height + .5:
                    raise ValueError(f"Clipped text in {name}: {label.get_text()!r}")
        fig.savefig(target, dpi=dpi, bbox_inches=None, pad_inches=0)
        width, height = fig.get_size_inches()
        plt.close(fig)
        charts.append(dict(
            path=target.name, title=title, caption=caption, units=units,
            display_policy=display_policy, observations=observations,
            source_commit=source_commit,
            source_files=[entry for entry in source_files if not relevant_files or entry["path"] in relevant_files],
            payload=payload, output_sha256=sha256(target),
            width_pixels=round(width * dpi), height_pixels=round(height * dpi), dpi=dpi,
        ))

    # All minute rows are plotted. NaNs intentionally break the line at rejection.
    for name, log in (("raw", False), ("log", True)):
        fig, axes = plt.subplots(2, 1, figsize=(13.2, 5.25), sharex=True)
        fig.subplots_adjust(left=.105, right=.95, bottom=.14, top=.93, hspace=.24)
        for i, ch in enumerate(CHANNELS):
            ax = axes[i]
            ax.plot(frame.index, series[ch], color=COLORS[ch], linewidth=.65)
            ax.text(.015, .80, ch.upper(), transform=ax.transAxes, color=COLORS[ch],
                    fontsize=18, weight="bold")
            ax.set_ylabel("Flux (W m⁻²)")
            if log:
                ax.set_yscale("log")
            else:
                scientific(ax)
                ax.set_ylim(bottom=0)
            ax.set_xlim(frame.index[0], pd.Timestamp(dataset["end_exclusive_utc"]))
            dates(ax, "months", bottom=i == 1)
        save(fig, name, "Native X-ray flux" if not log else "Flux on a logarithmic axis",
             f"{native['native_contract']['platform']} {native['native_contract']['instrument']}, 01 May–31 August 2024; channel-specific QC masks are preserved as gaps.",
             "W m⁻²; logarithmic y-axis" if log else "W m⁻²; linear y-axis",
             "All 177,120 UTC minute grid rows; rejected observations become NaN line breaks; no interpolation or averaging.",
             {"grid_rows": len(frame), "xrsa_valid": int(series["xrsa"].notna().sum()),
              "xrsb_valid": int(series["xrsb"].notna().sum()), "absent_bins": dataset["absent_bins"]})

    scatter = evidence["eda"]["scatter"]
    fig, ax = plt.subplots(figsize=(13.2, 5.2))
    fig.subplots_adjust(left=.10, right=.98, bottom=.19, top=.96)
    ax.scatter(scatter["xrsa"], scatter["xrsb"], s=13, color=COLORS["xrsb"],
               alpha=.48, edgecolors="none")
    ax.set_xlabel("XRSA · " + LOG_UNITS)
    ax.set_ylabel("XRSB · " + LOG_UNITS)
    ax.text(.025, .91, f"Full-sample Pearson r = {scatter['full_sample_correlation']:.4f}",
            transform=ax.transAxes, fontsize=18, weight="bold")
    ax.text(.025, .82, f"{scatter['total_pairs']:,} joint-valid pairs · {scatter['display_pairs']:,} displayed",
            transform=ax.transAxes, fontsize=16, color=MUTED)
    save(fig, "scatter", "The channels move together in log space",
         "Correlation uses all 172,646 jointly valid pairs; the plot displays the saved chronological subset.",
         LOG_UNITS + " on both axes", scatter["display"],
         {"total_pairs": scatter["total_pairs"], "display_pairs": scatter["display_pairs"],
          "full_sample_correlation": scatter["full_sample_correlation"]})

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2))
    fig.subplots_adjust(left=.085, right=.985, bottom=.19, top=.88, wspace=.23)
    histogram_counts = {}
    for ax, ch in zip(axes, CHANNELS):
        values = np.log10(series[ch].dropna().to_numpy(float))
        counts, edges, _ = ax.hist(values, bins=60, color=COLORS[ch], alpha=.88,
                                    edgecolor=BACKGROUND, linewidth=.4)
        assert int(counts.sum()) == len(values)
        histogram_counts[ch] = {"rows": len(values), "bins": len(counts),
                                "lower_edge": float(edges[0]), "upper_edge": float(edges[-1])}
        channel_title(ax, ch, f" · n = {len(values):,}")
        ax.set_xlabel(LOG_UNITS)
        ax.set_ylabel("Minute observations")
        ax.yaxis.set_major_locator(MaxNLocator(5))
    save(fig, "histogram", "Flux distributions after the log transform",
         "Each histogram uses every channel-valid observation in May–August; equal-width bins are computed in log10 flux.",
         "x: " + LOG_UNITS + "; y: minute-observation count",
         "All channel-valid values; 60 equal-width log10 bins per channel; no subsampling.", histogram_counts)

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2))
    fig.subplots_adjust(left=.075, right=.985, bottom=.19, top=.88, wspace=.23)
    for ax, ch in zip(axes, CHANNELS):
        qq = evidence["eda"]["qq"][ch]
        x = np.asarray(qq["theoretical"])
        y = np.asarray(qq["observed"])
        ax.plot(x, qq["intercept"] + qq["slope"] * x, color=MUTED, linewidth=1.6,
                linestyle="--", label="Fitted Normal reference")
        ax.scatter(x, y, s=14, color=COLORS[ch], edgecolors="none", zorder=3, label="Observed quantiles")
        channel_title(ax, ch)
        ax.set_xlabel("Normal theoretical quantile")
        ax.set_ylabel(LOG_UNITS)
        ax.legend(loc="upper left", fontsize=13)
    save(fig, "qq", "Normal Q–Q plots of log flux",
         "Saved order-statistic ranks reveal departures from the fitted Normal reference, especially in the upper tail.",
         "x: standard-Normal quantile; y: " + LOG_UNITS,
         "301 saved evenly spaced order-statistic ranks per channel; fitted reference uses every valid channel value.",
         {ch: {"full_rows": evidence["eda"]["qq"][ch]["rows"],
                "display_points": len(evidence["eda"]["qq"][ch]["observed"]),
                "reference_slope": evidence["eda"]["qq"][ch]["slope"],
                "reference_intercept": evidence["eda"]["qq"][ch]["intercept"]} for ch in CHANNELS})

    fig, axes = plt.subplots(2, 3, figsize=(13.2, 5.5), sharex=True)
    fig.subplots_adjust(left=.09, right=.985, bottom=.16, top=.89, hspace=.27, wspace=.30)
    for row, ch in enumerate(CHANNELS):
        raw = block[ch + "_flux"].to_numpy(float)
        logged = np.log10(raw)
        transforms = ((block.index, raw), (block.index, logged), (block.index[1:], np.diff(logged)))
        for col, (time, values) in enumerate(transforms):
            ax = axes[row, col]
            ax.plot(time, values, color=COLORS[ch], linewidth=.85)
            if col == 0:
                scientific(ax)
                ax.set_ylabel(ch.upper() + " · W m⁻²")
            else:
                ax.set_ylabel("log₁₀ F" if col == 1 else "Δ log₁₀ F")
                ax.yaxis.set_major_locator(MaxNLocator(4))
            if row == 0:
                ax.set_title(("Native flux", "Log₁₀ flux", "First log difference")[col], loc="left", fontsize=17)
            ax.set_xlim(block.index[0], block.index[-1])
            dates(ax, "days", bottom=row == 1)
            ax.tick_params(axis="x", labelsize=14)
    save(fig, "transform", "A transformation does not remove changing activity",
         "The same complete training block is shown before and after log10 and one-minute differencing; no points are filled.",
         "Native: W m⁻²; log: " + LOG_UNITS + "; difference: one-minute Δlog10 F",
         "All 10,149 native minute observations per channel; 10,148 first differences aligned to the later timestamp.",
         {"block": eda["diagnostic_block"], "native_and_log_rows": len(block), "difference_rows": len(block) - 1})

    decomposition = evidence["decomposition"]
    display = decomposition["display"]
    times = pd.DatetimeIndex(display["time_utc"])
    fig, axes = plt.subplots(4, 2, figsize=(13.2, 6.35), sharex=True)
    fig.subplots_adjust(left=.12, right=.985, bottom=.12, top=.91, hspace=.17, wspace=.23)
    component_names = ("observed", "trend", "seasonal", "residual")
    component_labels = ("Observed", "Trend", "Assumed daily", "Residual")
    for col, ch in enumerate(CHANNELS):
        for row, component in enumerate(component_names):
            ax = axes[row, col]
            ax.plot(times, display[ch][component], color=COLORS[ch], linewidth=.9)
            ax.set_ylabel(component_labels[row], fontsize=15)
            ax.yaxis.set_major_locator(MaxNLocator(3))
            ax.tick_params(axis="y", labelsize=14)
            ax.set_xlim(times[0], times[-1])
            if row == 0:
                channel_title(ax, ch, " · log₁₀ flux")
            if row == 2:
                ax.text(.015, .78, "Imposed period: 1,440 min", transform=ax.transAxes,
                        fontsize=13, color=MUTED)
            dates(ax, "days", bottom=row == 3)
    save(fig, "stl", "STL at an imposed daily period",
         "Robust STL of log10 flux on the 10,149-minute complete June block. The 1,440-minute period is assumed; stable seasonality is not established.",
         "All components are additive in " + LOG_UNITS,
         "1,100 saved deterministic display positions from the full fitted block; no observed-data interpolation. Trend/low-pass LOESS jumps are recorded in source evidence.",
         {"full_rows": decomposition["rows"], "display_rows": len(times),
          "period_minutes": decomposition["period_minutes"], "settings": decomposition["settings"],
          "reconstruction_max_error": decomposition["reconstruction_max_error"],
          "limitations": decomposition["limitations"]})

    for diagnostic, max_lag in (("acf", 120), ("pacf", 60)):
        fig, axes = plt.subplots(2, 2, figsize=(13.2, 5.4), sharex=True)
        fig.subplots_adjust(left=.075, right=.985, bottom=.15, top=.89, hspace=.27, wspace=.20)
        for col, ch in enumerate(CHANNELS):
            for row, transform in enumerate(("log_level", "log_difference")):
                ax = axes[row, col]
                values = np.asarray(eda["dependence"][ch][diagnostic][transform], dtype=float)
                assert len(values) == max_lag + 1
                lags = np.arange(len(values))
                ax.vlines(lags, 0, values, color=COLORS[ch], linewidth=1.2)
                ax.scatter(lags, values, s=9, color=COLORS[ch], edgecolors="none")
                ax.axhline(0, color=MUTED, linewidth=.9)
                ax.set_ylim((-.22, 1.07) if diagnostic == "acf" else (-1.05, 1.05))
                ax.set_xlim(-1, max_lag + 1)
                ax.set_ylabel("Log level" if row == 0 else "Δ log₁₀ flux")
                if row == 0:
                    channel_title(ax, ch)
                if row == 1:
                    ax.set_xlabel("Lag (minutes)")
                ax.xaxis.set_major_locator(MaxNLocator(5, integer=True))
                ax.yaxis.set_major_locator(MaxNLocator(4))
        save(fig, diagnostic, diagnostic.upper() + ": log levels and first differences",
             f"Saved {diagnostic.upper()} diagnostics on the complete June training block; lag zero is included. No inferential confidence bands are added.",
             "Dimensionless correlation; lag in minutes",
             f"All saved {diagnostic.upper()} values, lags 0–{max_lag}, for both channels and both transforms; no refitting.",
             {"block": eda["diagnostic_block"], "lags": [0, max_lag],
              "method": "FFT ACF; adjusted=False" if diagnostic == "acf" else "Yule–Walker PACF; method=ywm"},
             relevant_files=("docs/presentation/eda_evidence.json", "src/solar_flare_jepa/presentation/eda.py",
                             "docs/presentation/time_series_evidence.json", "docs/presentation/time_series_identity.json"))

    deployment = evidence["deployment"]
    issue = pd.Timestamp(deployment["issue_utc"])
    context, actual, forecast = (deployment[key] for key in ("context", "actual", "forecast"))
    context_time = pd.DatetimeIndex(context["time_utc"])
    actual_time = pd.DatetimeIndex(actual["time_utc"])
    forecast_time = pd.DatetimeIndex(forecast["time_utc"])
    assert len(context_time) == 120 and len(actual_time) == len(forecast_time) == 30
    assert actual_time.equals(forecast_time) and actual_time[0] == issue
    assert context_time[-1] + pd.Timedelta(minutes=1) == issue
    fig, axes = plt.subplots(2, 1, figsize=(13.2, 5.3), sharex=True)
    fig.subplots_adjust(left=.10, right=.96, bottom=.15, top=.96, hspace=.19)
    for row, ch in enumerate(CHANNELS):
        ax = axes[row]
        flux = np.r_[context[ch + "_flux"], actual[ch + "_flux"]]
        observed_time = context_time.append(actual_time)
        selected = evidence["classical"]["selected"][ch]
        order = ",".join(map(str, selected["order"]))
        ax.axvspan(issue, actual_time[-1] + pd.Timedelta(minutes=1), color=GRID, alpha=.45)
        ax.plot(observed_time, np.log10(flux), color=COLORS[ch], linewidth=1.6,
                label="Actual · 120-min context + 30-min target")
        ax.plot(forecast_time, np.log10(forecast[ch + "_flux"]), color=FOREGROUND, linewidth=2.0,
                linestyle="--", label=f"Saved ARIMA({order}) forecast")
        ax.axvline(issue, color=MUTED, linewidth=1.1, linestyle=":")
        ax.set_ylabel(ch.upper() + " · log₁₀ F")
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.set_xlim(context_time[0], actual_time[-1] + pd.Timedelta(minutes=1))
        ax.legend(loc="upper left", fontsize=13, ncol=2)
        if row == 0:
            ax.text(.805, .77, "Issue · 02:00 UTC", transform=ax.transAxes,
                    fontsize=14, color=MUTED)
        dates(ax, "minutes", bottom=row == 1)
    save(fig, "forecast", "One held-out forecast replay",
         "Issue time: 01 August 2024, 02:00 UTC. Saved forecasts are compared with 30 actual target minutes after 120 context minutes. This single example does not estimate average skill.",
         LOG_UNITS,
         "Only stored 120-minute context, 30-minute actual target and 30-minute saved forecast, displayed after log10 transformation; timestamp alignment and saved-parameter replay verified; no extrapolated plotting points or intervals.",
         {"issue_utc": deployment["issue_utc"], "context_rows": len(context_time),
          "actual_rows": len(actual_time), "forecast_rows": len(forecast_time),
          "verified_replay_metrics": replay_metrics, "interpretation": deployment["interpretation"]})

    manifest = dict(
        schema_version=1,
        evidence_status="OBSERVED: strict evidence identity checks, native-file verification and saved-parameter forecast replay passed.",
        producer="scripts/presentation/build_charts.py", producer_sha256=sha256(Path(__file__)),
        source_commit=source_commit, source_files=source_files, payload=payload,
        native_source_files=native["source_files"], native_source_bytes=native["source_bytes"],
        native_manifests=native["manifests"],
        environment={name: importlib.metadata.version(name) for name in ("numpy", "pandas", "matplotlib", "scipy", "statsmodels")},
        rendering={"background": BACKGROUND, "foreground": FOREGROUND, "muted": MUTED,
                   "channel_colors": COLORS, "canvas_policy": "Fixed figure sizes; no tight bounding-box crop", "dpi": dpi},
        charts=charts,
    )
    (output_dir / "chart_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="Pinned evidence checkout with its ignored native files/payload")
    parser.add_argument("--output-dir", type=Path, default=REPO / "presentations/assets")
    parser.add_argument("--expected-source-commit", default="abe4b79", help="Required source HEAD prefix; pass an empty string to use strict file identities without a Git pin")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    if args.dpi < 100:
        parser.error("Use at least 100 dpi for readable slide assets")
    manifest = build(args.source_root, args.output_dir, args.expected_source_commit, args.dpi)
    print(json.dumps({"charts": len(manifest["charts"]), "output_dir": str(args.output_dir.resolve()),
                      "source_commit": manifest["source_commit"], "payload_sha256": manifest["payload"]["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
