"""Release replay must cover every saved neural forecast without fitting."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_v1_reference.py"


def test_full_reference_replay_covers_all_nine_checkpoints_and_native_support():
    assert SCRIPT.exists(), "Full V1 reference verifier is missing"
    bundle = ROOT / "results/experiments/v1-full-20261009"
    manifest = json.loads((ROOT / "data/manifests/goes_v1_202408.json").read_text())
    required = [ROOT / row["path"] for row in manifest["files"]]
    required += [bundle / name for name in ("summary.json", "test_predictions.npz")]
    required += [bundle / f"{variant}_seed{seed}.pt"
                 for variant in ("jepa_finetune", "jepa_frozen", "supervised")
                 for seed in (17, 29, 43)]
    missing = [path for path in required if not path.exists()]
    if missing:
        pytest.skip(f"Original ignored V1 bundle incomplete ({len(missing)} missing paths); "
                    "restore it for release verification. check_stable_baseline treats missing assets as blockers.")
    run = subprocess.run([sys.executable, str(SCRIPT), "--root", str(ROOT)],
                         cwd=ROOT.parent, capture_output=True, text=True, timeout=180)
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads(run.stdout)
    assert report["status"] == "PASS"
    assert report["origins"] == 1436
    assert report["native_files"] == 31
    assert report["native_rows"] == 44640
    assert report["raw_context_exact"] and report["raw_context_masks_exact"]
    assert report["raw_targets_exact"] and report["raw_target_masks_exact"]
    assert report["all_temporal_support_exact"]
    assert report["offline_network_blocked"] and not report["fit_performed"]
    assert report["rtol"] == 1e-6 and report["atol"] == 1e-15
    assert set(report["models"]) == {
        f"{variant}_seed{seed}"
        for variant in ("jepa_finetune", "jepa_frozen", "supervised")
        for seed in (17, 29, 43)
    }
    for model in report["models"].values():
        assert model["point_shape"] == [1436, 30, 2]
        assert model["quantile_shape"] == [1436, 30, 2, 5]
        assert model["point_within_tolerance"] and model["quantiles_within_tolerance"]
        assert model["checkpoint_unchanged"]
        assert model["normalization_fingerprint"] == (
            "848623009ce048a14e32c50b7c70d9c9728cdd77391f10115ec1c8fd46d039a9")


def test_missing_reference_bundle_fails_closed_with_structured_error(tmp_path):
    assert SCRIPT.exists(), "Full V1 reference verifier is missing"
    run = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path)],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode != 0
    report = json.loads(run.stdout)
    assert report["status"] == "FAIL" and report["error"]
