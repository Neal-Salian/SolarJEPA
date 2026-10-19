# SolarJEPA Stable Baseline v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Integrate and verify the existing retrospective GOES/V1 five-page dashboard as Stable Baseline v0.1 without changing scientific outputs.

**Architecture:** Retain the exact P1/P2/V1 and dashboard/prediction lineage, then compose the sibling time-series presentation extension. Scientific loading, inference, saved-parameter replay and plots stay in their existing reusable modules; Streamlit provides routing and presentation.

**Tech Stack:** Python >=3.11, NumPy/pandas/xarray/netCDF4, PyTorch 2.6.0 CPU, statsmodels/arch, Streamlit 1.50.0, Plotly 6.3.1, pytest.

**Spec:** User request “Prepare SolarJEPA Stable Baseline v0.1 through a controlled integration process”; verified source/branch/dependency decisions in [integration audit](../../STABLE_BASELINE_V0_1_AUDIT.md).

## Global Constraints

- Do not modify or delete existing branches, worktrees, datasets, checkpoints, or experiments.
- Do not retrain models or execute the V2 pilot.
- Do not automatically merge all branches or include unrelated research.
- Do not modify `main` or create a PR.
- Commit and push verified integration work only to the new integration feature branch.
- Preserve original model outputs, normalization, scientific provenance, and checkpoint compatibility.
- Stop before any merge into `main` and request explicit approval; merging and pushing to main require separate action-specific authorization.
- User explicitly authorized audit, planning, implementation, testing and independent subagent review without an intermediate plan approval pause.

## Review Focus

- A user opens all five pages offline: routing, chart counts and controls work with no network or real-data fitting.
- A user selects altered/missing checkpoint/data/evidence: fail closed with a visible explanation and no fallback prediction.
- A user selects an August issue time: context ends before issue, lead 1 begins at issue, masks and all 30 bins preserve native units/timestamps.
- A fresh process opens presentation pages: no torch/training/prediction import or August raw/checkpoint/NPZ access; richer time-series evidence loads locally.
- A fresh checkout lacks ignored artifacts or installs the wrong dependency family: setup/preflight identifies precise missing/mismatched inputs and does not retrain/rebuild scientific outputs.

---

### Task 1: Establish the isolated reviewed integration tree

**Files:**
- Create: `docs/STABLE_BASELINE_V0_1_AUDIT.md` and this plan.
- Integrate: exact source/docs/tests at `a4951516dc2094ceb246b016700d1483a808212b`.
- Integrate: `5618bc4042d4a88b019504768772880cc15d2fcd` and `abe4b79d2fe7549552b0a1f467be1cd949b652a7`.
- Modify: `streamlit_app.py`, `tests/test_dashboard_ui.py`, `tests/test_flux_prediction_ui.py` only as needed for presentation composition.

**Interfaces:**
- Consumes: clean `main=origin/main=1a4991da4dda9676caeb1d7e35a03408528c3188`, isolated `codex/stable-baseline-v0.1` published with upstream.
- Produces: `streamlit_app.py` routes Overview, Data Explorer, Time-Series Analysis, Model Results and Solar Flux Prediction; existing `time_series.render_explorer(root)`, `render_analysis(root, channel)` and `render_models(root)` remain intact.

- [x] Verify branch, origin base, worktree status and unexpected changes; preserve all other worktrees and untracked paths named in the audit.
- [x] Integrate prediction tip and only the two selected time-series commits, preserving original lineage and scientific source bytes.
- [x] Compose app hooks with the fifth-page route and conditional August sidebar. Preserve `_NATIVE_IO_LOCK` and lazy prediction-page import.
- [x] Update offline presentation regression chart expectations to `[1,4,2,2]`; preserve native-files=61 and every import/file/network guard in `run_legacy_boundary`.
- [x] Compare all pinned registry/source/config/manifests against their source branches; require byte identity. Run `git diff --check`.
- [x] Record a focused Conventional Commit only after the owning tests and independent reviews pass, or keep this task staged for the final verified integration commit.

### Task 2: Make setup and artifact verification reproducible

**Files:**
- Create: stable setup/launch guide, stable dependency lock/check tooling and tests where useful.
- Modify: `README.md`, `pyproject.toml` only where required to expose verified stable setup.
- Preserve: `requirements-dashboard-lock.txt`, `requirements-dashboard-prediction-lock.txt`, V1/core locks and scientific identities.

**Interfaces:**
- Consumes: existing immutable prediction registry, four GOES manifest paths, time-series identity and payload path.
- Produces: documented single stable environment install command and dependency/artifact check command, with explicit missing/mismatched asset errors and no acquisition/fitting.

- [x] Build the stable dependency environment from the dashboard-prediction lock; do not overlay the incompatible V1 lock. Add only compatible inherited core-test dependencies (Astropy/cdflib) if needed in a separate stable lock.
- [x] Run a fresh install where feasible, normal `pip install --no-deps .`, `pip check`, package/model/dashboard imports and recorded runtime versions. Reinstall after source edits when source ownership checks require it.
- [x] Copy only exact manifest/registry-required ignored GOES/V1/time-series artifacts into the isolated checkout. Verify source and destination hashes, leave originals untouched and verify actual copied destinations are ignored.
- [x] Write setup instructions covering Python/platform scope, locked installation, exact artifact restoration, data/checkpoint identity validation, loopback launch from checkout root and five-page scopes. Explain that missing originals require restoration and cannot be replaced by retraining.
- [x] Exercise missing/altered artifact and dependency detection through existing tests plus any new stable-preflight test; document platform and binary warnings.

### Task 3: Verify the combined runtime and original numerical outputs

**Files:**
- Test: existing `tests/test_dashboard*.py`, `tests/test_flux_prediction*.py`, `tests/test_time_series*.py`, and relevant core/GOES/V1 tests.
- Run: `scripts/verify_presentation.py`, `scripts/verify_dashboard.py`, `scripts/verify_flux_prediction.py`.
- Create: fresh results/release-readiness documentation; keep raw execution logs under ignored results if needed.

**Interfaces:**
- Consumes: installed combined tree and restored exact artifacts from Task 2.
- Produces: actual executed test results, pinned saved-score reconciliation, original seed17 forecast replay and five-page offline validation evidence.

- [x] Run four read-only acquisition checks with the stable environment:

```bash
.venv/bin/python scripts/acquire_goes_history.py --manifest data/manifests/goes_v1_202405.json --verify
.venv/bin/python scripts/acquire_goes_history.py --manifest data/manifests/goes_v1_202406.json --verify
.venv/bin/python scripts/acquire_goes_history.py --manifest data/manifests/goes_p2_july2024.json --verify
.venv/bin/python scripts/acquire_goes_history.py --manifest data/manifests/goes_v1_202408.json --verify
```

Expected: all 123 pinned files match bytes/hashes; no download or writes. The existing CLI uses `--manifest` in verify mode; `--config` alone does not change its default July verification selection.

- [x] Run the dashboard/prediction/time-series integration suite:

```bash
.venv/bin/python -m pytest -q tests/test_dashboard.py tests/test_dashboard_ui.py tests/test_flux_prediction.py tests/test_flux_prediction_replay.py tests/test_flux_prediction_ui.py tests/test_time_series_presentation.py tests/test_time_series_ui.py
```

Expected: all selected tests pass; five routes work offline, saved-parameter button succeeds, altered inputs fail closed, presentation-page boundary guards remain enforced.

- [x] Run original source/score/data reconciliation and seed17 numerical replay:

```bash
.venv/bin/python scripts/verify_presentation.py
.venv/bin/python scripts/verify_dashboard.py
.venv/bin/python scripts/verify_flux_prediction.py --root "$PWD"
```

Expected: PASS; 52 original presentation identities, 123 raw files, original 422 score checks, 61 dashboard-native files; exact raw context/masks/target support and saved actuals. Both JEPA and supervised point/quantile outputs match saved seed17 arrays at `2024-08-01T02:00:00Z` with `rtol=1e-6`, `atol=1e-15`. Report the actual measured maximum differences, not only tolerance. Test another exact benchmark origin if feasible without changing reference artifacts; nonbenchmark replay origin must fail rather than choose a neighbor.

- [x] Run relevant core regression tests covering GOES/QC, windows, canonical contracts, causality, provenance, deterministic/statistical baselines and checkpoint compatibility. Do not run real-data training entry points. If the user's no-retraining constraint excludes synthetic fit tests too, use an explicit nontraining selection and document every omitted training-only test instead of claiming a full suite.
- [x] Start `.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501` from root and check loopback health. Record AppTest evidence for all routes and controls; do not equate health alone with page correctness.

### Task 4: Independent review, release verdict and feature-branch publication

**Files:**
- Create: scientific/technical review evidence and release-readiness report.
- Modify: baseline setup/status documentation only where current fresh evidence requires it; preserve historical reports.

**Interfaces:**
- Consumes: final combined source tree, actual fresh test/preflight/replay outputs and exact diff/history.
- Produces: honest release verdict, blockers/limitations, final integration commit and feature-branch upstream equality, exact remaining main merge requirements.

- [x] Assign independent scientific and technical subagents to inspect the final tree, source identity preservation, scientific claims, normalization/context/target semantics, dependency consistency, artifact isolation, offline pages, tests and scope exclusions.
- [x] Resolve material findings within authorized integration scope; reproduce first where practical, then rerun affected checks. Do not silently change the scientific algorithm, reference arrays, normalization, calibration or metrics.
- [x] Record supported historical use and unknown operational/SoLEXS/inferential capabilities. State V2 pilot, V3, live inference and blocked SoLEXS exclusions explicitly. Distinguish fresh results from handoff history and report all unresolved blockers.
- [x] Run final `git diff --check`, status, history, staged path/type and prohibited-data inspection; run `git check-ignore -v` on actual ignored raw/checkpoint/payload paths. Verify original branches/worktrees/main still retain their prior identities and tracked work.
- [x] Commit with focused Conventional Commit messages and push only `codex/stable-baseline-v0.1`; verify upstream equals the delivered commit. Do not create a PR.
- [x] Deliver branch/commit, audit/dependency map, exact tests/replay results, launch instructions and release verdict. Stop before main integration and ask for explicit merge approval. State that any push to main requires separately explicit authorization and a final main/origin recheck.

## Completion evidence

Final frozen-source suite: 1,301 passed, one disclosed warning (138.41s).
All-nine V1 replay and 422 saved-score checks match originals; preflight
verifies 123 native files and nine checkpoints. Both independent reviews PASS.
The release report records the earlier invalidated concurrent-edit run and all
limitations. Main merge/push remain explicitly unapproved.
