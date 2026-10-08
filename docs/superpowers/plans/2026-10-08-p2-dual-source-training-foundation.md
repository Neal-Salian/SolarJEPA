# P2 Dual-Source Training Foundation Implementation Plan

> Execution: bounded independent workers for acquisition, native diagnostics and training; primary owns integration, commits and verification. The user's explicit P2 implementation instruction is the design and execution authorization.

**Goal:** Deliver a reproducible GOES historical training path, safe real SoLEXS exploration and a tested lightweight model-training interface for Claude Code.

**Architecture:** Reuse P1 immutable time-series, chronological partition, window, baseline and evaluation contracts. Add source-specific historical acquisition and dataset adapters; retain SoLEXS in native instrument space behind the existing Phase E gate. A small optional PyTorch pipeline consumes P1 windows and returns physical-unit ForecastPrediction objects.

**Tech stack:** Existing Python/NumPy/pandas/xarray/astropy/matplotlib; optional PyTorch, CPU default.

**Authoritative requirements:** The user's P2 specification and AGENTS.md. Parent is unmerged P1 `595371190177de4638962aafa327f611b2045b90`; P1 remains NOT_READY_FOR_INTEGRATION.

## Constraints and design decisions

- Only `feat/p2-dual-source-training-foundation` changes and pushes; main, P1 and frozen research refs remain untouched.
- Preserve the untracked P1 final audit, Paperclip tooling and all existing data/results by hashes.
- Complete July 2024 GOES-16 NCEI science one-minute files, selected by calendar/overlap before observing results. Bounded sequential downloads, immutable paths, retries, checksums, resume ledger and no silent overwrite.
- Forecast two native GOES flux channels, units W/m2, context 120 minutes, horizon 30 minutes, stride 30 minutes. Train July 1–22, validation July 22–27, test July 27–August 1, half-open UTC. Fixed hyperparameters; seed 17. No test selection/tuning.
- GOES availability is retrospective completed-bin availability; operational delivery latency UNKNOWN. No operational forecast claim. Keep raw missingness and native quality masks, no interpolation.
- No new flare event labels in P2. Native historical catalogue states may be described separately; continuous flux evaluation cannot establish event classification skill.
- SoLEXS gate remains BLOCKED_FOR_PHASE_E. No UTC conversion, calibrated irradiance, cross-source alignment, count/flux conversion or SoLEXS training without established semantics and gate permission.
- New model is TRAINING_INFRASTRUCTURE_SMOKE_TEST, never SolarJEPA. CPU, bounded batches/epochs; optional explicit MPS; no large pretrained downloads.

## Review focus

1. Resumed raw files must match ledger identities, including corrupt/truncated streams and version/date mismatch.
2. Missing bins, invalid flags, time disorder, wrong platform and wrong units must fail or remain explicitly masked; no sorting-away defects.
3. All training statistics must use unique raw training support; future targets and validation/test data cannot influence fit.
4. Native detector/time identities and unresolved gates must survive every SoLEXS output and conversion attempt.
5. Checkpoints must bind spec/source/data/split/training/normalization identities; nonfinite training and incompatible reload fail.

## Task 1: Verify and preserve starting state

- [x] Read repository policy, source/interfaces, manifests, refs and local audit.
- [x] Fetch and verify main/P1/research refs and P1 checkpoint ancestry.
- [x] Create exact requested P2 branch from verified P1 HEAD and publish upstream before implementation.
- [ ] Record existing file identities; run fresh full P1 suite and recheck reference GOES data.

## Task 2: Historical NOAA acquisition

Owner: acquisition worker. Files: new `data/goes_acquisition.py`, `scripts/acquire_goes_history.py`, `tests/test_goes_acquisition.py`, `configs/data/p2_goes_july2024.json`, `data/manifests/goes_p2_july2024.json`.

Interface: `acquire_history(config_path, root) -> dict` and `verify_history(manifest_path, root) -> list[Path]` (flux files only). Manifest records portable paths, official URLs, sizes, hashes, selected interval and satellite/product/version.

- [ ] Write offline tests for bounded acquisition, retries/failure, immutable resume, path safety and integrity; observe RED.
- [ ] Implement minimum acquisition; run GREEN. Browse official NOAA source/product documentation.
- [ ] Acquire/verify the fixed month within caps and record actual inventory.

## Task 3: GOES validation and P1 integration

Owner: primary. Files: new `data/foundation.py`, `scripts/prepare_goes_training.py`, `tests/test_p2_foundation.py`; narrow additions to `experiments/config.py`, `experiments/runner.py`, `forecasting/contracts.py`; new experiment config.

Interfaces: `goes_training(config, root) -> TimeSeriesDataset`; `prepare_foundation(config_path, root, output_dir) -> dict`. Preserve native identity metadata, complete measured-bin grids with explicit absent masks, raw quality report and P1 split/window manifests.

- [ ] Write failing tests for historical adapter, mask/missingness, platform/units/order and no incompatible source conversion/mixing.
- [ ] Add `goes_historical` config/role preserving original reference protections; reuse native read_goes quality policy.
- [ ] Verify target support inside splits and train-only normalization; record raw rows, valid origins and exclusions.
- [ ] Execute all six fixed P1 baselines and verify indexed artifacts, causality, coverage and failures.

## Task 4: Native SoLEXS exploration

Owner: native worker. Files: new `data/solexs_exploration.py`, CLI, dedicated tests, diagnostic config and readiness document. Do not modify old loader/gate/manifests.

- [ ] Read existing loader/scientific evidence; verify archives with existing APIs.
- [ ] Write and observe failing tests for detector identity, blocked conversion/task, bounded native diagnostics and provenance.
- [ ] Implement native summaries and plots using existing loaders. Label OBSERVED_NATIVE or EXPERIMENTAL_UNCALIBRATED; never SCIENTIFICALLY_VALIDATED.
- [ ] Run real inspection; report each candidate sequence task and gate disposition.

## Task 5: Lightweight training foundation

Owner: training worker. Files: new `training/` package, `scripts/train_smoke.py`, `tests/test_training_foundation.py`; primary adds optional dependency metadata.

Interfaces: P1 WindowedPartition/TrainingSlice inputs; train-only unique-raw log/standard normalization; explicit input/target masks; model output `[batch,horizon,targets]`; P1 prediction/evaluation adapter; checkpoint reload and inference.

- [ ] Inspect existing package/environment; write deterministic tests and observe RED.
- [ ] Implement bounded CPU loops, optional MPS selection, seeds, validation-only checkpoint selection, optimizer and numerical guards.
- [ ] Verify checkpoint identities, deterministic reload and evaluator integration; run actual GOES smoke after primary prepares windows.

## Task 6: Independent review, verification and handoff

- [ ] Commit scoped tested implementation and push P2 throughout; install package normally after source changes.
- [ ] Run P2, native loaders, historical F1/R1/N1/N2/N3, full suite, actual NOAA validation/baselines, native inspection and smoke/reload.
- [ ] Independent scientific/leakage/code review; reproduce and fix important findings with tests.
- [ ] Write `docs/P2_DUAL_SOURCE_FOUNDATION.md`, `docs/P2_CLAUDE_CODE_HANDOFF.md` and future model contract; distinguish IMPLEMENTED/VERIFIED/PLANNED/BLOCKED.
- [ ] Inspect diffs/index/history/ignore policy, preservation identities and all protected refs; push final P2 and confirm sync. Stop for human review.
