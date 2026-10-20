"""Scientific presentation boundaries for the added time-series views."""
from copy import deepcopy
from importlib import import_module, util
import json
from pathlib import Path
import socket

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def charts():
    name = "solar_flare_jepa.dashboard.time_series"
    assert util.find_spec(name) is not None, "Time-series presentation charts are required"
    return import_module(name)


def test_scatter_displays_paired_log_values_and_channel_units():
    figure = charts().scatter_figure({"xrsa": [-8.0, -7.0], "xrsb": [-6.0, -5.0],
                                      "total_pairs": 20, "display_pairs": 2})
    assert list(figure.data[0].x) == [-8.0, -7.0]
    assert list(figure.data[0].y) == [-6.0, -5.0]
    assert "XRS-A" in figure.layout.xaxis.title.text
    assert "XRS-B" in figure.layout.yaxis.title.text
    assert "log₁₀" in figure.layout.xaxis.title.text


def test_qq_displays_saved_normal_quantiles_and_channel_specific_reference():
    payload = {"xrsa": {"theoretical": [-1., 0., 1.], "observed": [-9., -8., -6.],
                         "slope": 1.5, "intercept": -8., "r": .9, "rows": 30},
               "xrsb": {"theoretical": [-1., 0., 1.], "observed": [-7., -6., -4.],
                         "slope": 2., "intercept": -6., "r": .8, "rows": 30}}
    figure = charts().qq_figure(payload)
    assert list(figure.data[0].y) == [-9., -8., -6.]
    assert list(figure.data[1].y) == [-9.5, -8., -6.5]
    assert list(figure.data[2].y) == [-7., -6., -4.]
    assert "Normal" in figure.layout.xaxis.title.text
    assert "log₁₀" in figure.layout.yaxis.title.text


def test_stl_displays_all_four_saved_components_with_original_utc_times():
    times = ["2024-06-11T16:38:00Z", "2024-06-11T16:40:00Z"]
    payload = {"period_minutes": 1440, "display": {"time_utc": times,
               "xrsa": {"observed": [-8., -7.], "trend": [-8., -8.],
                         "seasonal": [0., .2], "residual": [0., .8]}}}
    figure = charts().decomposition_figure(payload, "xrsa")
    assert [trace.name for trace in figure.data] == ["Observed", "Trend", "Seasonal component", "Residual"]
    assert list(figure.data[2].y) == [0., .2]
    assert pd.Timestamp(figure.data[0].x[1]) == pd.Timestamp(times[1])
    assert "UTC" in figure.layout.xaxis4.title.text
    assert "dex" in figure.layout.yaxis.title.text
    assert figure.layout.meta["assumed_period_minutes"] == 1440


def deployment():
    return {"issue_utc": "2024-08-01T00:02:00Z", "context_steps": 2, "horizon_steps": 2,
            "context": {"time_utc": ["2024-08-01T00:00:00Z", "2024-08-01T00:01:00Z"],
                        "xrsa_flux": [1e-8, 2e-8], "xrsb_flux": [1e-6, 2e-6]},
            "actual": {"time_utc": ["2024-08-01T00:02:00Z", "2024-08-01T00:03:00Z"],
                       "xrsa_flux": [3e-8, 4e-8], "xrsb_flux": [3e-6, 4e-6]},
            "forecast": {"time_utc": ["2024-08-01T00:02:00Z", "2024-08-01T00:03:00Z"],
                         "xrsa_flux": [2.5e-8, 3.5e-8], "xrsb_flux": [2.5e-6, 3.5e-6]}}


def test_forecast_overlay_preserves_target_bin_starts_and_native_flux():
    figure = charts().deployment_figure(deployment())
    assert len(figure.data) == 6
    assert list(figure.data[2].y) == [2.5e-8, 3.5e-8]
    assert pd.Timestamp(figure.data[2].x[0]) == pd.Timestamp("2024-08-01T00:02:00Z")
    assert figure.layout.yaxis.type == "log"
    assert "W/m²" in figure.layout.yaxis.title.text
    assert "bin start" in figure.layout.xaxis2.title.text
    assert all(trace.connectgaps is False for trace in figure.data)


def test_forecast_overlay_refuses_bad_physical_values_and_misaligned_times():
    payload = deployment()
    payload["forecast"]["xrsa_flux"][0] = 0.
    with pytest.raises(ValueError, match="positive"):
        charts().deployment_figure(payload)
    payload = deployment()
    payload["forecast"]["time_utc"][0] = "2024-08-01T00:01:00Z"
    with pytest.raises(ValueError, match="align"):
        charts().deployment_figure(payload)


def test_new_views_and_saved_parameter_inference_work_without_fitting_or_network(monkeypatch):
    charts()
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    def denied(*args, **kwargs):
        raise AssertionError("Rendering and saved-parameter inference must not fit or use the network")
    monkeypatch.setattr(ARIMA, "fit", denied)
    monkeypatch.setattr(SARIMAX, "fit", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    for page, count in [("Data Explorer", 4), ("Time-Series Analysis", 2), ("Model Results", 2)]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        assert not app.error, page
        assert len(app.get("plotly_chart")) == count, page
        if page == "Time-Series Analysis":
            app.selectbox[0].set_value("XRS-B").run()
            app.selectbox[1].set_value("First log₁₀ difference").run()
            assert not app.exception and not app.error
            plotted = json.loads(app.get("plotly_chart")[1].proto.spec)
            assert plotted["layout"]["meta"]["channel"] == "xrsb"
    assert any("BIC" in item.value for item in app.markdown)
    assert any("target-bin" in item.value for item in app.caption)
    app.button(key="saved_model_inference").click().run()
    assert not app.exception and not app.error
    assert any("inference verified" in item.value.lower() for item in app.success)
    assert len(app.get("plotly_chart")) == 2


def test_unavailable_new_evidence_preserves_existing_explorer_charts(monkeypatch):
    charts()
    evidence = import_module("solar_flare_jepa.presentation.time_series")
    def unavailable(*args, **kwargs):
        raise ValueError("Verified time-series evidence unavailable: Scientific payload identity mismatch. "
                         "Restore pinned local data and run scripts/build_time_series_presentation.py.")
    monkeypatch.setattr(evidence, "load_evidence", unavailable)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("Data Explorer").run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    assert any("Verified result unavailable" in item.value for item in app.error)
    assert any("identity mismatch" in item.value for item in app.caption)
    recovery = " ".join(item.value for item in app.caption)
    assert "build_time_series_presentation.py" not in recovery
    assert "Restore the original pinned payload and sources" in recovery
    assert "docs/STABLE_BASELINE_V0_1_RUN.md" in recovery


def test_failed_candidate_remains_visible_in_likelihood_and_forecast_tables(monkeypatch):
    evidence_module = import_module("solar_flare_jepa.presentation.time_series")
    evidence = deepcopy(evidence_module.load_evidence(ROOT))
    failed = {"channel": "xrsa", "family": "Failed test candidate", "order": [9, 1, 9],
              "comparison_group": None, "aic": None, "bic": None,
              "fit_status": "failed", "log_mae": None, "log_rmse": None}
    evidence["classical"]["candidates"].append(failed)
    monkeypatch.setattr(evidence_module, "load_evidence", lambda root: evidence)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("Model Results").run()
    assert not app.exception and not app.error
    matching = [table.value for table in app.dataframe
                if "Family" in table.value and "Failed test candidate" in table.value["Family"].tolist()]
    assert len(matching) == 2, "Failed fits must remain visible in IC and forecast tables"


def test_inference_mismatch_is_explicit_without_a_success_or_new_forecast(monkeypatch):
    evidence_module = import_module("solar_flare_jepa.presentation.time_series")
    def mismatch(evidence):
        raise ValueError("Saved-model replay prediction mismatch")
    monkeypatch.setattr(evidence_module, "replay_deployment", mismatch)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("Model Results").run()
    app.button(key="saved_model_inference").click().run()
    assert not app.exception and not app.success
    assert any("Verified result unavailable" in item.value for item in app.error)
    assert any("prediction mismatch" in item.value for item in app.caption)
    assert len(app.get("plotly_chart")) == 1, "Archived comparison should remain; failed replay should not plot"
