"""Export compact, verified presentation values, never scientific arrays.

Run with the installed presentation-completion environment and --source-root
pointing at the pinned analysis checkout. Original scientific products are read
only. Charts have a separate reproducible builder.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from solar_flare_jepa.presentation.time_series import load_evidence, replay_deployment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.source_root.resolve()
    evidence = load_evidence(root)
    _, replay = replay_deployment(evidence)
    expected = {
        "xrsa": ((1, 1, 0), -12311.066, -12299.136, 0.218835, 0.256635),
        "xrsb": ((2, 1, 0), -20686.728, -20668.832, 0.094347, 0.109055),
    }
    for ch, (order, aic, bic, mae, rmse) in expected.items():
        selected = evidence["classical"]["selected"][ch]
        actual = (tuple(selected["order"]), round(selected["aic"], 3),
                  round(selected["bic"], 3), round(replay[ch]["log_mae"], 6),
                  round(replay[ch]["log_rmse"], 6))
        assert actual == (order, aic, bic, mae, rmse), (ch, actual)
    stationarity_path = root / "docs/presentation/stationarity.csv"
    with stationarity_path.open() as stream:
        stationarity = list(csv.DictReader(stream))
    payload = root / "results/presentation_time_series/diagnostics.json"
    out = {
        "schema_version": 1,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "payload_sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
        "dataset": evidence["dataset"],
        "statistics": evidence["eda"]["statistics"],
        "scatter_correlation": evidence["eda"]["scatter"]["full_sample_correlation"],
        "stationarity": stationarity,
        "diagnostic_block": {
            key: evidence["decomposition"][key]
            for key in ("start_utc", "end_exclusive_utc", "rows", "daily_acf")
        },
        "training": evidence["classical"]["training"],
        "candidates": [{key: row[key] for key in
                        ("channel", "family", "order", "aic", "bic")}
                       for row in evidence["classical"]["candidates"]],
        "selected": {ch: {key: row[key] for key in ("order", "aic", "bic")}
                     for ch, row in evidence["classical"]["selected"].items()},
        "deployment": {key: evidence["deployment"][key]
                       for key in ("issue_utc", "context_steps", "horizon_steps", "metrics")},
        "metric_scope": "One retrospective complete-case held-out 30-minute example, not overall forecasting skill",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "verified_metrics": replay,
                      "source_commit": out["source_commit"]}))


if __name__ == "__main__":
    main()
