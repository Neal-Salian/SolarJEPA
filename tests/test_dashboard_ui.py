"""Presentation contracts: native UI, scientific labels, and fail-closed charts."""
from importlib import import_module
from pathlib import Path
import socket

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "streamlit_app.py"


def chart_builders():
    return import_module("solar_flare_jepa.dashboard.charts")


def test_flux_chart_preserves_missing_observations_and_physical_units():
    charts = chart_builders()
    index = pd.date_range("2024-05-01", periods=5, freq="min", tz="UTC")
    frame = pd.DataFrame({"xrsa_flux": [1e-8, 2e-8, np.nan, 4e-8, 2e-8],
                          "xrsb_flux": [1e-6, 2e-6, np.nan, 4e-6, 2e-6]}, index=index)
    figure = charts.flux_figure(frame, "GOES Solar X-Ray Flux Over Time")
    assert figure.layout.yaxis.type == "log"
    assert "W/m²" in figure.layout.yaxis.title.text
    assert "UTC" in figure.layout.xaxis.title.text
    assert [trace.name for trace in figure.data] == ["XRS-A", "XRS-B"]
    assert all(trace.connectgaps is False for trace in figure.data)
    assert np.isnan(figure.data[0].y[2])
    assert list(figure.data[0].x) == list(index.to_pydatetime())


def test_flux_chart_retains_an_isolated_peak_under_render_budget():
    charts = chart_builders()
    index = pd.date_range("2024-05-01", periods=10_000, freq="min", tz="UTC")
    flux = np.full(10_000, 1e-8)
    flux[4321] = 9e-4
    frame = pd.DataFrame({"xrsa_flux": flux, "xrsb_flux": flux * 2}, index=index)
    figure = charts.flux_figure(frame, "Flux", max_points=300)
    for trace in figure.data:
        assert len(trace.y) <= 300
        peak = int(np.argmax(trace.y))
        assert pd.Timestamp(trace.x[peak]) == index[4321]
    assert max(figure.data[0].y) == 9e-4


def test_flux_chart_refuses_nonpositive_finite_values():
    charts = chart_builders()
    index = pd.date_range("2024-05-01", periods=2, freq="min", tz="UTC")
    frame = pd.DataFrame({"xrsa_flux": [0, 1e-8], "xrsb_flux": [1e-6, 1e-6]}, index=index)
    with pytest.raises(ValueError, match="positive"):
        charts.flux_figure(frame, "Flux")


def test_histogram_chart_uses_supplied_counts_without_rebinning():
    charts = chart_builders()
    figure = charts.histogram_figure({
        "xrsa": {"counts": [2, 7], "edges": [-9.0, -8.5, -8.0]},
        "xrsb": {"counts": [1, 8], "edges": [-7.0, -6.5, -6.0]},
    })
    assert [list(trace.y) for trace in figure.data] == [[2, 7], [1, 8]]
    assert list(figure.data[0].x) == [-8.75, -8.25]
    assert list(figure.data[0].width) == [0.5, 0.5]
    assert "log₁₀" in figure.layout.xaxis.title.text
    assert "count" in figure.layout.yaxis.title.text.lower()


def test_dependence_chart_displays_saved_values_and_minute_lags():
    charts = chart_builders()
    figure = charts.dependence_figure([1.0, 0.8, 0.4], [1.0, 0.7], "XRS-B", "log difference")
    assert list(figure.data[0].y) == [0.8, 0.4]
    assert list(figure.data[1].y) == [0.7]
    assert list(figure.data[0].x) == [1, 2]
    assert "minutes" in figure.layout.xaxis.title.text
    assert "minutes" in figure.layout.xaxis2.title.text


def test_model_chart_displays_log_mae_values_and_dex_units():
    charts = chart_builders()
    frame = pd.DataFrame({"model_id": ["a", "b"], "label": ["Persistence", "ARIMA"],
                          "log_mae": [0.17, 0.13]})
    figure = charts.model_figure(frame)
    assert figure.data[0].orientation == "h"
    assert sorted(figure.data[0].x) == [0.13, 0.17]
    assert "dex" in figure.layout.xaxis.title.text
    assert set(figure.data[0].y) == {"Persistence", "ARIMA"}


@pytest.fixture
def offline(monkeypatch):
    def reject_network(*args, **kwargs):
        raise AssertionError("Dashboard attempted network access")
    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket.socket, "connect", reject_network)


def test_all_four_pages_render_native_artifacts_offline(offline):
    assert APP.exists(), "Streamlit entry point is required"
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert app.title[0].value == "SolarJEPA"
    assert len(app.metric) == 3
    assert len(app.get("plotly_chart")) == 1
    for page, chart_count in [("Data Explorer", 4), ("Time-Series Analysis", 2), ("Model Results", 2)]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        assert len(app.get("plotly_chart")) == chart_count, page
        assert not app.error, page
    assert any("dex" in caption.value for caption in app.caption)


def test_missing_evidence_is_explicit_and_never_plotted(monkeypatch):
    assert APP.exists(), "Streamlit entry point is required"
    data = import_module("solar_flare_jepa.dashboard.data")
    def unavailable(*args, **kwargs):
        raise data.DashboardUnavailable("Required registry source is missing")
    monkeypatch.setattr(data, "load_registry", unavailable)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert any("Verified result unavailable" in message.value for message in app.error)
    assert len(app.get("plotly_chart")) == 0
    assert len(app.metric) == 0


def test_overview_with_unverified_status_omits_milestone_claims(monkeypatch):
    data = import_module("solar_flare_jepa.dashboard.data")
    original = data.verify_sources
    def verify(root, registry, entry_id):
        if entry_id == "research_status":
            raise data.DashboardUnavailable("Status snapshot identity mismatch")
        return original(root, registry, entry_id)
    monkeypatch.setattr(data, "verify_sources", verify)
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert any("Verified result unavailable" in message.value for message in app.error)
    assert not any("V2 infrastructure is implemented" in item.value for item in app.markdown)


def test_rerun_reuses_bounded_plotting_transformation(monkeypatch):
    import streamlit as st
    data=import_module('solar_flare_jepa.dashboard.data')
    original=data.envelope; calls=[]
    def envelope(*args,**kwargs):
        calls.append(1); return original(*args,**kwargs)
    monkeypatch.setattr(data,'envelope',envelope); st.cache_data.clear()
    app=AppTest.from_file(str(APP),default_timeout=60).run()
    first=len(calls); assert first==2
    app.run()
    assert not app.error and not app.exception
    assert len(calls)==first
