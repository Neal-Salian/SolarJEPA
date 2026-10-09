"""V1 artifacts must retain the actual flat provenance contract."""
import json

import numpy as np

from solar_flare_jepa.experiments import v1
from solar_flare_jepa.experiments.v1_report import write_report
from solar_flare_jepa.forecasting.contracts import TimeSeriesDataset


def test_v1_summary_and_report_preserve_commit_and_environment(monkeypatch, tmp_path):
    """Dropping flat code_provenance fields loses the run's reproducible identity."""
    root = tmp_path.resolve()
    names = ("xrsa_flux", "xrsb_flux")
    cadence = 60 * 10**9
    start = 1_704_067_200 * 10**9  # 2024-01-01T00:00:00Z
    ticks = np.arange(6 * 1440, dtype=np.int64)
    starts = start + ticks * cadence
    # Invented positive channels for software verification, never solar observations.
    rng = np.random.default_rng(7)
    values = 10.0 ** np.column_stack((
        -7 + .1 * np.sin(ticks / 13) + .01 * rng.standard_normal(len(ticks)),
        -6 + .1 * np.cos(ticks / 19) + .01 * rng.standard_normal(len(ticks)),
    ))
    mask = np.ones_like(values, dtype=bool)
    dataset = TimeSeriesDataset(
        "v1_provenance_fixture", "synthetic_fixture", starts, starts + cadence,
        values, mask, values, mask, names, names, ("W/m2",) * 2, ("W/m2",) * 2,
        60, availability_policy="bin_end_earliest",
        metadata_json='{"interpretation":"invented_software_fixture"}',
    )
    config = {
        "schema_version": 1,
        "dataset": {"kind": "goes_historical_multi", "manifests": [
            "data/manifests/fixture_a.json", "data/manifests/fixture_b.json",
        ]},
        "forecast": {
            "cadence_seconds": 60, "context_steps": 4, "horizon_steps": 2,
            "stride_steps": 60, "feature_names": names, "target_names": names,
            "feature_units": ("W/m2",) * 2, "target_units": ("W/m2",) * 2,
            "availability_mode": "retrospective_bin_end", "eligibility_policy": "complete",
            "transform": "log10", "feature_reference": (1., 1.),
            "target_reference": (1., 1.), "target_minimum": (0., 0.),
        },
        "splits": [
            {"name": "train", "start_utc": "2024-01-01T00:00:00Z", "end_utc": "2024-01-03T00:00:00Z"},
            {"name": "validation", "start_utc": "2024-01-03T00:00:00Z", "end_utc": "2024-01-05T00:00:00Z"},
            {"name": "test", "start_utc": "2024-01-05T00:00:00Z", "end_utc": "2024-01-07T00:00:00Z"},
        ],
        "baselines": [{"name": "persistence", "parameters": {}}],
        "metrics": {"lead_weights": [1, 1], "target_weights": [1, 1]},
        "seeds": [17],
    }
    models = {"statistical": [{"name": "persistence_empirical", "parameters": {},
                               "family": "persistence_empirical"}]}
    config_path, models_path = root / "config.json", root / "models.json"
    config_path.write_text(json.dumps(config))
    models_path.write_text(json.dumps(models))
    # Complete shape returned by code_provenance, with deterministic boundary values.
    provenance = {
        "git_commit": "0123456789abcdef0123456789abcdef01234567", "git_branch": "v1",
        "tracked_dirty": False, "untracked_configuration_paths": [],
        "source": {"files": [], "fingerprint": "a" * 64}, "imported_source": [],
        "packages": {"solar-flare-jepa": "0.1.0", "numpy": "2.2.6", "pandas": "2.2.3",
                     "xarray": "2025.1.2", "netCDF4": "1.7.2", "pyarrow": "19.0.1"},
        "python": "3.13.11 (synthetic test runtime)", "platform": "macOS-test-arm64",
    }
    monkeypatch.setattr(v1, "_dataset", lambda config, root: dataset)
    monkeypatch.setattr(v1, "code_provenance", lambda *args, **kwargs: provenance)

    destination = v1.run_v1(config_path, models_path, root,
                            output_dir="results/experiments/provenance-regression")
    report = write_report(destination).read_text()
    summary = json.loads((destination / "summary.json").read_text())

    assert summary["provenance"].get("git_commit") == "0123456789abcdef0123456789abcdef01234567"
    assert summary["provenance"]["git_branch"] == "v1"
    assert summary["provenance"]["python"] == "3.13.11 (synthetic test runtime)"
    assert summary["provenance"]["platform"] == "macOS-test-arm64"
    assert summary["provenance"]["packages"] == {
        "solar-flare-jepa": "0.1.0", "numpy": "2.2.6", "pandas": "2.2.3",
        "xarray": "2025.1.2", "netCDF4": "1.7.2", "pyarrow": "19.0.1",
    }
    assert "Git: `0123456789abcdef0123456789abcdef01234567`" in report
    assert "Git: `None`" not in report
