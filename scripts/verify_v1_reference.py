"""Replay all nine original V1 neural checkpoints against the frozen test archive.

This explicit offline verifier reads the original saved evaluation arrays. It
does not fit models, download observations, recompute accuracy metrics or write
artifacts. JSON is emitted to stdout so callers can preserve a new audit report.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from solar_flare_jepa.dashboard import prediction as p
from solar_flare_jepa.dashboard.data import _path, read_json
from solar_flare_jepa.forecasting.contracts import ForecastContext, ForecastSpec, FutureGrid

RTOL = 1e-6
ATOL = 1e-15  # W/m²; the same negligible absolute floor as the single-origin verifier.
CHECKPOINTS = {
    "jepa_finetune_seed17": "3d18e1067b7eeaf2b64ea572ff48831559f5171b82e765bf56841f2903fdaf48",
    "jepa_finetune_seed29": "e1b97d4cc8587fd9fa9ff02da2cda2165e2bf5b8febb825b4b820af4ddf1540f",
    "jepa_finetune_seed43": "6e36849378836f83847ae275561c65460fe4eb129eb1703302bbead7b342e4d5",
    "jepa_frozen_seed17": "84772e256b7796978ca53154e4e5088b5b38e98f78a903b5cc33e51e76272c54",
    "jepa_frozen_seed29": "1da1e6f474e7cf0e96522e3e391f7f1dc2998974c436e143b2920b488159fe33",
    "jepa_frozen_seed43": "98ba8d6379100b2687b075754c15551d9960c8de175957bb6891fdd01ceaea4a",
    "supervised_seed17": "973f784e2adecd5183bd11bd3f6d47f49c5a8786e603cac82c15e2854858273b",
    "supervised_seed29": "0e77f5fd68a6972ca7f3335733fc873b109527a90e8e7758ab644ad3584c2585",
    "supervised_seed43": "6ef24954846756544957363433c1fe000101154e6c9c814aaedd5c8bc3c3a550",
}


def verify_reference(root):
    began = time.perf_counter()
    root = Path(root).resolve()
    registry = p.load_prediction_registry(root)
    p.verify_artifacts(root, registry, p.SOURCE_KEYS + (
        "replay_archive", "replay_summary", "jepa_checkpoint", "supervised_checkpoint"))
    summary_path = _path(root, registry["artifacts"]["replay_summary"]["path"])
    archive_path = _path(root, registry["artifacts"]["replay_archive"]["path"])
    summary = read_json(summary_path)
    spec = ForecastSpec(**registry["forecast_spec"])
    if (summary["status"] != "complete" or summary["failures"]
            or summary["dataset"]["fingerprint"] != registry["dataset_fingerprint"]
            or ForecastSpec(**summary["config"]["forecast"]).fingerprint != spec.fingerprint
            or summary["provenance"]["git_commit"] != registry["executed_commit"]):
        raise ValueError("Saved V1 experiment lineage differs from the approved contract")
    partitions = [row for row in summary["split_manifest"] if row["partition"]["name"] == "test"]
    if len(partitions) != 1:
        raise ValueError("Missing unique saved test partition")
    partition = partitions[0]
    checkpoints = {name: _path(root, str(summary_path.parent.relative_to(root) / (name + ".pt")))
                   for name in CHECKPOINTS}
    references = {"summary": summary_path, "archive": archive_path, **checkpoints}
    hashes_before = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for name, path in references.items()}
    for name, expected in CHECKPOINTS.items():
        if hashes_before[name] != expected:
            raise ValueError("Original checkpoint identity mismatch: " + name)

    # Verify native observations independently before any checkpoint is loaded.
    frame = p.load_august_observations(root, registry)
    import torch
    from solar_flare_jepa.training.jepa import TrainedJepa
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    models = {}
    with np.load(archive_path, allow_pickle=False) as archive:
        issues = archive["issue_times_ns"]
        ids = tuple(str(value) for value in archive["origin_ids"])
        model_ids = tuple(str(value) for value in archive["model_ids"])
        if (len(ids) != 1436 or list(ids) != partition["retained_origins"]
                or issues.dtype.kind not in "iu" or issues.shape != (1436,)
                or len(np.unique(issues)) != 1436 or (np.diff(issues) <= 0).any()
                or ids != tuple("origin:" + str(int(value)) for value in issues)
                or len(model_ids) != 22 or len(set(model_ids)) != 22
                or not set(CHECKPOINTS).issubset(model_ids)):
            raise ValueError("Saved origin or model inventory differs")
        starts = issues[:, None] + np.arange(-120, 0)[None, :] * p.MINUTE_NS
        future_starts = issues[:, None] + np.arange(30)[None, :] * p.MINUTE_NS
        if (starts.min() < frame.index.asi8[0]
                or future_starts.max() > frame.index.asi8[-1]
                or ((issues - frame.index.asi8[0]) % p.MINUTE_NS).any()):
            raise ValueError("Saved support is outside exact native minute coordinates")
        offsets = (issues - frame.index.asi8[0]) // p.MINUTE_NS
        context_indices = offsets[:, None] + np.arange(-120, 0)[None, :]
        target_indices = offsets[:, None] + np.arange(30)[None, :]
        np.testing.assert_array_equal(frame.index.asi8[context_indices], starts)
        np.testing.assert_array_equal(frame.index.asi8[target_indices], future_starts)
        native = frame[["xrsa_flux", "xrsb_flux"]].to_numpy()
        masks = np.column_stack([frame["observed"] & frame[channel + "_valid"]
                                 for channel in ("xrsa", "xrsb")])
        np.testing.assert_array_equal(native[context_indices], archive["context"])
        np.testing.assert_array_equal(masks[context_indices], archive["context_mask"])
        np.testing.assert_array_equal(native[target_indices], archive["targets"])
        np.testing.assert_array_equal(masks[target_indices], archive["target_mask"])
        supports = partition["support_manifest"]
        if len(supports) != len(ids):
            raise ValueError("Saved temporal support count differs")
        for index, support in enumerate(supports):
            expected = {"origin_id": ids[index], "issue_time_ns": int(issues[index]),
                        "context_start_ns": int(starts[index, 0]),
                        "context_end_ns": int(issues[index]),
                        "target_start_ns": int(issues[index]),
                        "target_end_ns": int(future_starts[index, -1] + p.MINUTE_NS)}
            if any(support[key] != value for key, value in expected.items()):
                raise ValueError("Saved temporal support differs: " + ids[index])
        context = ForecastContext(native[context_indices], masks[context_indices],
            starts, starts + p.MINUTE_NS, issues, ids, spec, registry["dataset_fingerprint"])
        grid = FutureGrid(future_starts, future_starts + p.MINUTE_NS, issues, ids,
                          spec, registry["dataset_fingerprint"])
        for name, checkpoint in checkpoints.items():
            model_began = time.perf_counter()
            model = TrainedJepa.load(checkpoint)
            variant, seed = name.rsplit("_seed", 1)
            if (model.variant != variant or model.record["seed"] != int(seed)
                    or model.record != summary["fits"][name]["record"]
                    or model.config.batch_size != 256 or model.config.threads != 4
                    or model.normalization.fingerprint != registry["normalization_fingerprint"]
                    or model.normalization.spec.fingerprint != registry["spec_fingerprint"]):
                raise ValueError("Checkpoint record, original batch shape or normalization differs: " + name)
            output = model.predict(context, grid)
            index = model_ids.index(name)
            point, quantiles = archive["point_" + str(index)], archive["quantiles_" + str(index)]
            if point.shape != (1436, 30, 2) or quantiles.shape != (1436, 30, 2, 5):
                raise ValueError("Saved forecast shape differs: " + name)
            np.testing.assert_allclose(output.values, point, rtol=RTOL, atol=ATOL)
            np.testing.assert_allclose(output.quantiles, quantiles, rtol=RTOL, atol=ATOL)
            if output.quantile_levels != (.05, .25, .5, .75, .95):
                raise ValueError("Original quantile levels differ: " + name)
            models[name] = {
                "checkpoint_sha256": hashes_before[name], "seed": int(seed), "variant": variant,
                "normalization_fingerprint": model.normalization.fingerprint,
                "point_shape": list(point.shape), "quantile_shape": list(quantiles.shape),
                "point_within_tolerance": True, "quantiles_within_tolerance": True,
                "point_bitwise_exact": bool(np.array_equal(output.values, point)),
                "quantiles_bitwise_exact": bool(np.array_equal(output.quantiles, quantiles)),
                "max_point_absolute_difference": float(np.max(np.abs(output.values - point))),
                "max_quantile_absolute_difference": float(np.max(np.abs(output.quantiles - quantiles))),
                "max_point_relative_difference": float(np.max(np.abs(output.values - point) / np.abs(point))),
                "max_quantile_relative_difference": float(np.max(np.abs(output.quantiles - quantiles) / np.abs(quantiles))),
                "elapsed_seconds": round(time.perf_counter() - model_began, 3),
            }
    for name, path in references.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes_before[name]:
            raise ValueError("Original reference changed during replay: " + name)
        if name in models:
            models[name]["checkpoint_unchanged"] = True
    return {
        "status": "PASS", "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(ROOT), "artifact_root": str(root),
        "experiment_id": registry["experiment_id"], "executed_commit": registry["executed_commit"],
        "dataset_fingerprint": registry["dataset_fingerprint"],
        "spec_fingerprint": registry["spec_fingerprint"],
        "normalization_fingerprint": registry["normalization_fingerprint"],
        "reference_sha256": hashes_before, "origins": 1436, "native_files": 31,
        "native_rows": len(frame), "raw_context_exact": True, "raw_context_masks_exact": True,
        "raw_targets_exact": True, "raw_target_masks_exact": True, "all_temporal_support_exact": True,
        "reference_model_count": 22, "replayed_neural_model_count": 9,
        "classical_forecasts_replayed": False, "models": models,
        "rtol": RTOL, "atol": ATOL,
        "tolerance_reason": "Frozen single-origin replay tolerance; exact equality is reported separately. Original batch256 is retained.",
        "offline_network_blocked": True, "fit_performed": False,
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "machine": platform.machine(), "numpy": np.__version__,
                    "torch": str(torch.__version__), "device": "cpu", "threads": 4, "batch_size": 256},
        "elapsed_seconds": round(time.perf_counter() - began, 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository/storage root containing pinned original V1 artifacts")
    args = parser.parse_args()
    def offline(event, arguments):
        if event.startswith("socket.connect") or event == "socket.getaddrinfo":
            raise RuntimeError("Reference replay forbids network access")
    sys.addaudithook(offline)
    try:
        report = verify_reference(args.root)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError, AssertionError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, allow_nan=False))
        return 1
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
