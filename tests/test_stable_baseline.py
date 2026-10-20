"""Release preflight rejects missing, altered and incompatible local inputs."""
from importlib import util
from importlib.metadata import version
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_stable_baseline.py"


def checker():
    assert SCRIPT.is_file(), "Stable release preflight is missing"
    spec = util.spec_from_file_location("stable_preflight", SCRIPT)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dependency_check_reports_exact_installed_mismatch(tmp_path):
    check = checker()
    lock = tmp_path / "lock.txt"
    lock.write_text("numpy==0.0.0\n")
    report = check.check_dependencies(lock)
    assert report["numpy"]["installed"] == version("numpy")
    assert report["numpy"]["expected"] == "0.0.0"
    assert report["numpy"]["ok"] is False


def test_dependency_lock_resolves_includes_and_rejects_conflicts(tmp_path):
    check = checker()
    (tmp_path / "base.txt").write_text("numpy==2.2.6\n")
    lock = tmp_path / "lock.txt"
    lock.write_text("-r base.txt\npandas==2.3.3\n")
    assert check.lock_versions(lock) == {"numpy": "2.2.6", "pandas": "2.3.3"}
    lock.write_text("-r base.txt\nnumpy==0.0.0\n")
    with pytest.raises(ValueError, match="Conflicting"):
        check.lock_versions(lock)
    lock.write_text("numpy>=1\n")
    with pytest.raises(ValueError, match="Exact"):
        check.lock_versions(lock)


def test_artifact_check_rejects_missing_changed_and_escaping_paths(tmp_path):
    check = checker()
    (tmp_path / "artifact").write_bytes(b"original")
    digest = hashlib.sha256(b"original").hexdigest()
    assert check.verify_file(tmp_path, {"path": "artifact", "sha256": digest})["ok"]
    changed = check.verify_file(tmp_path, {"path": "artifact", "sha256": "0" * 64})
    assert not changed["ok"] and "SHA-256" in changed["error"]
    missing = check.verify_file(tmp_path, {"path": "missing", "sha256": digest})
    assert not missing["ok"] and "missing" in missing["error"]
    escape = check.verify_file(tmp_path, {"path": "../outside", "sha256": digest})
    assert not escape["ok"] and "escapes" in escape["error"]


def test_full_release_preflight_checks_exact_inputs_without_scientific_execution():
    check = checker()
    artifacts, _ = check.check_artifacts(ROOT, references=True)
    invalid = [row for row in artifacts if not row["ok"] and "missing" not in row["error"]]
    assert not invalid, invalid
    missing = [row["path"] for row in artifacts if not row["ok"]]
    if missing:
        pytest.skip("Original ignored release artifacts are unavailable: " + ", ".join(missing))
    code = r'''import importlib.abc, runpy, sys
class NoScience(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("torch", "netCDF4", "xarray", "solar_flare_jepa.training", "solar_flare_jepa.experiments")):
            raise AssertionError("Preflight imported scientific execution: " + fullname)
sys.meta_path.insert(0, NoScience())
def offline(event, args):
    if event.startswith("socket.connect") or event == "socket.getaddrinfo":
        raise AssertionError("Preflight attempted networking")
sys.addaudithook(offline)
sys.argv = [sys.argv[1], "--references"]
runpy.run_path(sys.argv[0], run_name="__main__")
'''
    run = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT)], cwd=ROOT.parent,
                         capture_output=True, text=True, timeout=60,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads(run.stdout)
    assert report["status"] == "PASS"
    assert report["native_files"] == 123
    assert report["references"] is True
    assert all(row["ok"] for row in report["dependencies"].values())
    assert any(row["path"].endswith("test_predictions.npz") for row in report["artifacts"])
    assert any(row["path"].endswith("diagnostics.json") for row in report["artifacts"])
    assert len([row for row in report["artifacts"] if row["path"].endswith(".pt")]) == 9


def test_missing_checkout_reports_nonzero_json(tmp_path):
    assert SCRIPT.exists(), "Stable release preflight is missing"
    run = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(tmp_path)],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 1
    report = json.loads(run.stdout)
    assert report["status"] == "FAIL" and report["errors"]


def test_normal_installed_package_includes_dashboard_contract_resources(tmp_path):
    code = ("from importlib.resources import files; "
            "p=files('solar_flare_jepa.dashboard'); "
            "assert p.joinpath('registry.json').is_file(); "
            "assert p.joinpath('prediction_registry.json').is_file()")
    run = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path,
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr


def test_reference_mode_detects_missing_and_changed_nonprimary_checkpoint(tmp_path):
    check = checker()
    for relative in check.CONTRACTS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    relative = "results/experiments/v1-full-20261009/jepa_frozen_seed29.pt"
    rows, _ = check.check_artifacts(tmp_path, references=True)
    missing = next((row for row in rows if row["path"] == relative), None)
    assert missing is not None, "Reference checkpoint is not checked"
    assert not missing["ok"] and "missing" in missing["error"]
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"changed checkpoint bytes")
    rows, _ = check.check_artifacts(tmp_path, references=True)
    changed = next(row for row in rows if row["path"] == relative)
    assert not changed["ok"] and "SHA-256 mismatch" in changed["error"]
