# P1 experiment/evaluation foundation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development with task-scoped TDD and review. Steps use checkbox syntax for tracking.

**Goal:** Implement the approved, model-independent P1 mechanics on synthetic data and the pinned GOES reference, without advancing the SoLEXS scientific gate.

**Architecture:** Immutable NumPy contracts carry intervals, availability, masks, identities and units. Raw chronological partitions precede causal windows; six point baselines use training-only information. Separate evaluators and a bounded runner record semantic identities and atomic execution artifacts.

**Tech stack:** Python >=3.11, existing NumPy/pandas dependencies, standard library, pytest. No new model-fitting dependencies.

**Spec:** `docs/P1_PROPOSED_DESIGN.md`, approved by the user's 2026-10-03 implementation instruction. This plan records execution decisions; the frozen proposal remains unchanged.

## Global constraints

- Implementation base: `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe`; branch/upstream: `feat/p1-experiment-evaluation-foundation` / `origin/feat/p1-experiment-evaluation-foundation`.
- Preserve main `1a4991da4dda9676caeb1d7e35a03408528c3188` and research checkpoint `805f1c3`; no integration or history rewriting.
- **Phase E remains BLOCKED_FOR_PHASE_E.** No SoLEXS interpretation/calibration/alignment, real event definitions, data acquisition, neural training or ARCH/GARCH fitting.
- Only explicit synthetic fixtures and the existing pinned GOES XRS-B reference are runner inputs. Outputs say `foundation_smoke_not_scientific_skill`.
- Raw support is partitioned before windows. Full context, extra feature lookback, targets and supplied label maturity must fit one partition.
- Train fitting uses only unique eligible raw training observations or training windows. Target masks are common across methods; invalid predictions are failures, not exclusions.
- Preserve existing scientific data/configs/manifests/reports and `.agents/skills/paperclip/SKILL.md`; no raw scientific data or `.agents` commits.
- User explicitly chose bounded parallel subagent work with primary integration and independent verification. File ownership is disjoint; only primary stages/commits/pushes. No worker subdelegation.
- Execute the approved scope without another planning approval gate; the next required user checkpoint is after verified implementation, before integration.

## Review focus and smallest design clarifications

1. Frozen dataclasses do not freeze arrays: copy into read-only byte-backed arrays; test external mutation and write-flag escalation.
2. Half-open containment admits support ending exactly at a cut. Label maturity equality is admissible; supplied groups crossing a cut purge intersecting support and raw fit observations.
3. Mean/AR/MASE use the full unique raw training partition, independent of overlap/stride, with masks excluding invalid feature dependencies and straddling groups.
4. Finite prediction contracts cannot carry overflow failures: runner records structured model failures with attempted origins and common target counts outside valid predictions.
5. Existing GOES sidecar has historical absolute paths, and the storage inventory writer permits replacement: normalize logical source identifiers using pinned manifests and implement a separate no-replacement publisher, including concurrent-writer tests.

These clarify the approved design rather than expand scientific scope. Actual imported module hashes must match checkout before a reproducible installed runner executes.

## Shared interface decisions

- `ForecastSpec`: cadence/context/horizon/stride in positive integer samples; extra feature lookback and label maturity in nonnegative samples; ordered names/units; explicit fixed identity/log10 transform with dimensional references; complete or masked eligibility; operational or retrospective-bin-end availability mode.
- `TimeSeriesDataset`: immutable `[T,C]` feature and `[T,K]` target arrays/masks; int64 nanosecond interval coordinates; optional actual per-feature availability; declared units, role and policies. Valid cells are finite; masked missing cells are represented canonically.
- `ForecastContext`: immutable `[N,L,C]` values/masks, `[N,L]` intervals, optional `[N,L,C]` availability, issue times/origin IDs, spec and dataset identity.
- `FutureGrid`: immutable target-value-free `[N,H]` intervals, issue times/origin IDs, spec and dataset identity. `ForecastTargets` and `ForecastPrediction` contain this grid plus `[N,H,K]` values; predictions optionally contain ordered, noncrossing `[N,H,K,Q]` quantiles.
- `TrainingSlice`: train-only context/targets plus unique raw intervals/features/targets/masks, train bounds and split fingerprint. Non-training role is rejected.
- `TemporalPartition(name,start_ns,end_ns)` and `EventGroup(group_id,start_ns,end_ns,maturity_ns)` live in splitting; `chronological_partitions(dataset,boundaries)` validates ordered explicit train/validation/(calibration)/test boundaries.
- `build_partition_windows(dataset,spec,partition,event_groups=()) -> WindowedPartition` returns context/targets, retained/excluded origins with reasons, support manifest, and `training_slice` only for train.
- Baselines expose `fit(training_slice)`, `predict(context,future_grid) -> ForecastPrediction`, and JSON-compatible `parameters`; fitting requires nonempty training support.
- Evaluators expose `evaluate_trajectory(targets,prediction,training,persistence=None,lead_weights=None,target_weights=None)` and `evaluate_events(...)`; JSON-compatible metric cells have `value`, `reason`, `count`.
- Runner exposes `run_experiment(config_path,root,output_dir=None)` and CLI `scripts/run_experiment.py --config ... --root ... [--output-dir ...]`. Output is confined to `results/experiments/` under the selected root.

## Task 1: Shared contracts (primary, prerequisite)

**Files:** create `forecasting/__init__.py`, `forecasting/contracts.py`, `tests/test_forecasting_contract.py`.

**Interfaces:** produces the immutable data/spec/context/grid/target/prediction/training types above, explicit fixed transform helpers and coordinate/alignment validation. Logical content fingerprints are exposed by validated immutable contracts; experiment provenance adds source/config/split/code identities.

- [ ] Write tests for shape/order/unit/interval mismatch, NaN on valid cells, unavailable context, operational unknown availability, external array mutation, quantile order/crossing, log references/inversion/overflow and train-only role.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_forecasting_contract.py`; observe missing-feature failure.
- [ ] Implement contracts and strict finite/canonical identities; no forecasting algorithms.
- [ ] Run targeted tests and inspect diff; independent task review before dependent integration.
- [ ] Commit `feat(forecasting): define immutable forecasting contracts`.

## Task 2: Chronological support/windows (agent A, after Task 1)

**Files:** create `forecasting/splitting.py`, `forecasting/windows.py`, `tests/test_forecasting_splits.py`, `tests/test_forecasting_windows.py`.

**Consumes:** Task 1 contracts. **Produces:** partition/group/window interfaces above, exact support/exclusion records and unique eligible training slice.

- [ ] Write adversarial tests: drastic post-cut value perturbation leaves earlier context/raw fit arrays unchanged; cut endpoints; added derivative lookback; delayed availability; masked targets; missing cadence; supplied group straddling/maturity; no support shared across partitions; empty partitions.
- [ ] Run tests RED before implementation.
- [ ] Implement raw partition validation before window construction; no resampling/imputation/transforms fitted on full data. Candidate origins use a fixed dataset-grid stride, not values.
- [ ] Run scoped tests GREEN; produce report with exact commands and results.
- [ ] Primary reviews, verifies and commits `feat(forecasting): construct leakage-safe chronological windows`.

## Task 3: Six deterministic baselines (agent B, after Task 1; parallel with 2/4)

**Files:** create `forecasting/baselines.py`, `tests/test_baselines.py`.

**Consumes:** Task 1 TrainingSlice/context/FutureGrid. **Produces:** `Persistence`, `TrainingMean`, `TrailingMean(lookback_steps)`, `Drift(lookback_steps)`, `AR1`, `DirectRidge(lag_steps,alpha)` and `make_baseline(name,parameters)`.

- [ ] Test literal constant/ramp/AR outputs, unique train mean independent of window overlap, AR pairs do not bridge gaps, direct-ridge toy recovery, train-only frozen fits under huge validation/test perturbation, unsupported feature-target mapping and log/domain failures.
- [ ] Run baseline tests RED; implement NumPy fitting with intercepts and fixed parameters, no tuning/refit/clipping.
- [ ] Run scoped tests GREEN, self-review and report; primary independently verifies.
- [ ] Commit `feat(forecasting): add deterministic training-only baselines`.

## Task 4: Separate trajectory/event metrics (agent C, after Task 1; parallel with 2/3)

**Files:** create `evaluation/__init__.py`, `evaluation/trajectory.py`, `evaluation/events.py`, `tests/test_trajectory_metrics.py`, `tests/test_event_metrics.py`.

**Consumes:** Task 1 contracts; event inputs are explicitly supplied synthetic labels, mature/valid mask, ordered IDs and event definition/horizon. **Produces:** JSON-compatible metrics, counts, units, aggregation weights and per-origin errors.

- [ ] Test hand-derived MAE/RMSE/MASE/skill/correlation/pinball; common masks and bad predictions; zero scales/constant/empty/insufficient samples; incompatible units/coordinates and aggregation.
- [ ] Test TP/FP/FN/TN, precision/POD/FAR/FPR/F1/TSS/HSS2, probability-only Brier with no invented threshold, missing/immature labels, invalid probabilities and all undefined denominators.
- [ ] Run RED; implement correct pooling and explicit null/reason/count; run GREEN and report.
- [ ] Primary verifies and commits `feat(evaluation): separate trajectory and supplied-event metrics`.

## Task 5: Config, fixtures, provenance and atomic recording (primary, parallel with 2/3/4)

**Files:** create `experiments/__init__.py`, `experiments/config.py`, `experiments/provenance.py`, `experiments/fixtures.py`, `tests/test_experiment_provenance.py`.

**Consumes:** Task 1 contracts; raw dataset/source and split manifests. **Produces:** strict resolved config, deterministic fixture, canonical SHA-256 identities, Git/source/import environment evidence, artifact verification, no-replacement atomic publisher.

- [ ] Test duplicate/unknown/nonfinite config fields, canonical ordering, data/mask/unit/policy/split/code corruption, relocation identity, RNG independence, existing empty destination, concurrent same-ID publication and injected prepublication failure.
- [ ] Run RED; implement local RNG streams, finite canonical JSON, source/manifest checks and portable identities. No environment dump or absolute paths in semantic identity.
- [ ] Publisher stages only beneath the safe output parent, validates artifact hashes then atomically publishes without replacement; cleanup never touches existing results/science data.
- [ ] Run scoped tests GREEN; independent review and focused commit.

## Task 6: Bounded runner, configs, schema and CLI (primary, after 2/3/4/5)

**Files:** create `experiments/runner.py`, `scripts/run_experiment.py`, `configs/experiments/p1_synthetic.json`, `configs/experiments/p1_goes_reference.json`, `schemas/experiment_result.schema.json`, `tests/test_experiment_runner.py`; modify `pyproject.toml` only if needed for installed CLI.

- [ ] Write runner/CLI tests before implementation: deterministic semantic reruns, distinct execution IDs, structured failed baselines, persisted actual origins/common target coverage, unsupported SoLEXS input, unsafe output paths, dirty tracked source/import mismatch, corruption and outside-checkout imports.
- [ ] Synthetic config uses explicit resolved times, seeds `[17,29,43]`, all six baselines and multiple targets. GOES config uses pinned XRS-B only, 6-hour context, 1-hour horizon, 10-minute stride and retrospective bin-end metadata; no event-label derivation.
- [ ] Reuse `read_goes`, verified manifest paths and sidecar hashes; preserve historical absolute paths while deriving portable identifiers from pinned config. No download path.
- [ ] Store resolved config/dataset/split/code/environment/parameters/predictions/errors/metrics/exclusions/failures and artifact hashes; record `deferred_pending_residual_diagnostics` for ARCH/GARCH.
- [ ] Run scoped tests GREEN; reinstall package without dependencies; verify normal installed code parity and CLI smoke.
- [ ] Commit `feat(experiments): run and record bounded reproducible foundation smokes`.

## Task 7: Independent integrated review and final evidence

**Files:** add `docs/P1_IMPLEMENTATION_REPORT.md`; update current README/status only. Preserve frozen design and historical reports.

- [ ] Fresh whole-branch code-quality and scientific leakage/reproducibility reviews; reproduce findings, fix via focused regression tests, record meaningful deviations.
- [ ] Primary runs all eight new test files, existing regression tests and complete repository suite; inspect scientific invariants beyond green output.
- [ ] Reinstall and run normal imports/CLI outside checkout, deterministic synthetic reruns and opt-in pinned GOES smoke; report mechanics only.
- [ ] Compare starting identity snapshot for all existing science files/manifests/configs/results and Paperclip pointer; inspect ignore rules, index/history, diff/status, refs/upstreams.
- [ ] Commit final verification/report, push only implementation branch, verify origin refs. Stop for user review; no integration or next phase.

## Execution record

Initial state independently verified before branch creation. Fresh baseline command `.venv/bin/python -m pytest -q`: **166 passed, one existing NumPy ndarray ABI RuntimeWarning, 35.90s**. GOES regenerated table equals pinned Parquet (4,320 rows; XRS-A 2,267 / XRS-B 4,318 valid); source identities and SoLEXS inventory pass. A read-only identity snapshot of 109 pre-existing data/config/result/skill files is retained outside Git for final comparison.

Read-only independent design review found the five Review Focus clarifications above. No material scope expansion is required. Work proceeds on the user-specified implementation branch in the existing checkout with disjoint file ownership; no concurrent Git mutations by subagents and no additional worktree needed.
