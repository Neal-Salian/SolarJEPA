# Frozen GOES External Model Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a no-refit external inference/evaluation path for the existing
V1 cohort and make a separately approved retrospective January replication
reproducible.

**Architecture:** Read verified immutable V1 and external preparation artifacts
through explicit configurable locators. Restore saved model state and keep
historical training identities separate from external forecast support; compose
thin scoring/pairing wrappers around existing canonical contracts. Preserve P1,
V1 and V2 APIs and approval boundaries.

**Tech Stack:** Python, NumPy, existing PyTorch/statsmodels/arch, pytest and the
existing locked normal package environment; no new dependency.

**Spec:** [Phase 1 protocol](../../PHASE1_GOES_EVALUATION_PROTOCOL.md).

## Global Constraints

- Status is **PARTIALLY_READY**; all implementation/execution tasks below are pending.
- The standing request authorizes necessary infrastructure **if readiness is established**; no additional generic planning approval is required.
- Full January model inference/evaluation always needs later explicit user approval.
- Use seeds `[17, 29, 43]`, quantiles `[0.05, 0.25, 0.50, 0.75, 0.95]`, unchanged spec fingerprint `094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94`.
- No training/refitting/reselection/calibration, event claims, V2 training or operational/confirmatory claim.
- Preserve checkpoint batch size 256, CPU execution and pinned external product `v2-2-1`; later product availability does not authorize replacement.
- Primary contrast: matched fine-tuned JEPA versus supervised; frozen JEPA and named compatible classical references are descriptive.
- Seed averages mean losses; RMSE is the square root of pooled squared error.
- Preserve the full regular candidate axis and identical observation exclusions.
- Calendar sensitivities: UTC-epoch 1/3/7-day blocks, 2,000 draws, RNG 17, nominal 95%, minimum support 9,000 seconds; no seed resampling or significance claim.
- January is temporally disjoint but previously exposed, not certified blind.
- Preserve immutable sources and ignored bulk artifacts; branch-only Conventional Commits/pushes, no merge/push to main.

## Review Focus

- Tampered or partially copied artifact bundles must fail before any predictor runs (Task 1).
- An external dataset must never be relabeled with the original training dataset fingerprint (Task 2).
- Missing planned seeds or model failures must never shrink common scored support (Tasks 1 and 4).
- Channel weighting, sparse candidate days and unequal edge blocks must not change reductions silently (Tasks 3 and 4).
- A runtime import mismatch or accidentally invoked optimizer must abort execution (Tasks 2 and 5).

---

## File map

Planned new modules are `experiments/external_inputs.py` (verified artifact
consumption), `forecasting/frozen.py` (saved classical state restoration),
`evaluation/external_model.py` (external scores/pairing), and
`experiments/external_evaluation.py` (explicit orchestration). Add one CLI and
one resolved configuration under existing script/config conventions. Reuse
small external/V2 evaluation kernels only when their dependency closure and
semantics fit; no broad branch merge or V2 runner integration. Source paths
below are relative to `src/solar_flare_jepa/`.

### Task 0: Resolve scientific scope and implementation authorization (no code)

**Files:** Review this plan, the protocol, `docs/PHASE1_GOES_READINESS_AUDIT.md`
and the portable readiness ledger. Change only evidence/decision records.

- [x] **Step 1: Preserve the current verdict PARTIALLY_READY.** Identify the
  missing native-processing/as-issued evidence, prior January exposure and
  unsupported external restore/scoring boundary separately. Use only the phase
  statuses `READY`, `PARTIALLY_READY` and `BLOCKED`; no renamed readiness status
  can bypass the implementation condition.
- [x] **Step 2: Obtain the required scope decision.** If causal operational
  validity is mandatory, obtain authoritative processing/delivery evidence and
  re-audit it. Alternatively, the user can explicitly accept a previously exposed,
  retrospective science-product replication with the recorded limits and
  authorize the specific missing no-refit adapters while the overall verdict
  remains PARTIALLY_READY. This is a material scope/action decision, not a generic
  planning-approval request; the present plan itself supplies no authorization.
- [x] **Step 3: Check authorization before Task 1.** Proceed only with a supported
  READY verdict under the standing conditional instruction, or explicit user
  authorization for the bounded adapter work described above. Otherwise leave
  all code tasks pending. Full experiment execution still requires Task 6's
  separate approval after infrastructure verification and final readiness review.

### Task 1: Freeze verified inputs

**Files:**
- Create: `experiments/external_inputs.py`
- Create: `configs/evaluation/goes_v1_external_january2025.json`
- Test: `tests/test_external_model_inputs.py`
- Update: `docs/PHASE1_GOES_EVALUATION_PROTOCOL.md` only with observed readiness evidence.

**Interfaces:**
- Consumes: V1 summary/checkpoints/NPZ, preparation artifact directory, canonical forecast contracts and `verify_artifacts`.
- Produces: `load_frozen_inputs(v1_dir: Path, preparation_dir: Path, protocol: dict) -> dict`, returning canonical `context`, `targets`, `candidate_issue_times_ns`, `candidate_exclusions`, ordered checkpoint records, classical fit records and detached input identities. It performs no inference or fitting.

- [x] **Step 1: Add failing input tests.** `test_tampered_member_rejected_before_predict`, `test_missing_or_duplicate_planned_seed_rejected`, `test_spec_and_channel_order_mismatch_rejected`, `test_full_v1_support_overlap_rejected`, and `test_retained_grid_matches_candidate_manifest` must exercise exact hashes, nine variant/seed pairs, unchanged spec, full May-Aug envelopes and candidate-axis reconstruction. Assert no model invocation on failure.
- [x] **Step 2: Run** `python -m pytest tests/test_external_model_inputs.py -q`; expect missing-interface failures before implementation.
- [x] **Step 3: Implement the interface.** Parse finite JSON strictly; verify byte identities, manifest members, checkpoint/summary declarations and external separation. Bind historical source and current source separately. Config declares exact model roster, losses/weights, exposure, block settings and no-fitting policy. Keep runtime storage locators out of scientific path identities.
- [x] **Step 4: Run the same tests; expect PASS.** Read-only readiness may verify checkpoint metadata, historical artifacts and preparation bytes, without January predictor execution. Recheck exposure and native archive limitations; retain the supported phase verdict and exact approved claim/scope. Operational/confirmatory status remains unavailable unless independently established; adapter tests do not establish it.
- [x] **Step 5: If input tests pass under Task 0's implementation authorization, commit only Task 1 code/config/tests and evidence docs:** `feat: bind frozen external evaluation inputs`. If scientific incompatibility or missing immutable state remains, stop with evidence and leave later tasks pending; do not repair by training or replacing data.

### Task 2: Restore classical fitted state without refitting

**Files:**
- Create: `forecasting/frozen.py`
- Test: `tests/test_frozen_baseline_replay.py`

**Interfaces:**
- Consumes: `load_frozen_inputs` records, exact original `ForecastSpec` and explicit distinct external dataset fingerprint.
- Produces: `load_frozen_baseline(record: dict, spec: ForecastSpec, *, expected_training_fingerprint: str, external_dataset_fingerprint: str) -> FrozenBaseline`; `FrozenBaseline.predict(context, future_grid) -> ForecastPrediction`. Original training/fit identity stays available unchanged.

- [x] **Step 1: Add failing tests.** `test_saved_classical_state_replays_historical_predictions` covers six point and seven probabilistic saved references; `test_frozen_restore_never_calls_fit_or_optimizer` patches baseline `.fit`, JEPA fitting, statsmodels fitting and arch optimization to raise; `test_external_identity_is_distinct_and_preserved` rejects identity substitution and mismatched spec/grid. Include malformed coefficient/table shapes, nonfinite state and unknown model names.
- [x] **Step 2: Run** `python -m pytest tests/test_frozen_baseline_replay.py -q`; expect missing-loader failure.
- [x] **Step 3: Implement strict restoration.** Hydrate constructor plus fitted coefficient/table/ARIMA/volatility fields from finite saved records; reuse fixed-parameter prediction equations. Do not weaken `_Baseline.predict`, mutate its training fingerprint to external, or call `.fit`. Preserve warnings/flags and the original `simulations=1000`, `sim_seed=0` recipe.
- [x] **Step 4: Run tests; expect PASS.** Compare restored historical points/quantiles to immutable V1 NPZ by model ID. Preserve configured CPU/dependencies and batch size 256. Reproduce the session's bounded evidence: nine neural first-256-origin replays and twelve classical first-two-origin replays are bitwise equal; direct ridge's observed maximum difference is `1.776e-15` dex. Document ridge arithmetic/batching sensitivity and predeclare a justified comparison tolerance before extending replay; do not silently label approximate equality bitwise. Synthetic external-grid tests verify identity handling without January inference.
- [x] **Step 5: Commit:** `feat: restore frozen classical forecasts without fitting`.

### Task 3: Complete external flux/quantile scoring

**Files:**
- Create: `evaluation/external_model.py`
- Test: `tests/test_external_model_metrics.py`

**Interfaces:**
- Consumes: canonical `ForecastTargets`, `ForecastPrediction`, optional aligned persistence and saved quantile levels.
- Produces: `score_external_prediction(targets, prediction, *, persistence=None) -> dict`, including native/dex point and quantile diagnostics, scalar per-origin MAE/MSE/pinball, channel/lead detail and input identity. No TrainingSlice is fabricated.

- [x] **Step 1: Add failing tests.** `test_hand_computed_dex_and_native_pinball`, `test_rmse_pools_squared_error`, `test_channel_lead_coverage_and_width`, `test_interval_score_has_declared_alpha_and_space`, `test_quantile_change_changes_score_identity`, `test_point_only_reference_has_no_quantiles`, `test_partial_or_nonfinite_prediction_fails`, and `test_mismatched_support_rejected` use tiny explicit grids and unequal error magnitudes. For squared errors `[1,9]`, assert RMSE `sqrt(5)`, not `2`; use ordered five-quantile forecasts with known inclusive 50%/90% counts. For `L=1,U=3,z=4`, assert interval scores `6` at alpha0.5 and `22` at alpha0.1, and verify dex/native transforms separately. Changing only a quantile must change the complete score-input fingerprint.
- [x] **Step 2: Run** `python -m pytest tests/test_external_model_metrics.py -q`; expect missing-scoring failure.
- [x] **Step 3: Implement the wrapper.** Reuse external native scoring and strict marginal diagnostic arithmetic, selectively bringing needed kernels into this branch with provenance. Supply missing channel/lead dex RMSE/pinball/coverage outputs; keep `log_scores` and `evaluate_trajectory` backward compatible. Record MASE unavailable, point interpretation, equal weights, full grid and observation-only masks.
- [x] **Step 4: Run metric tests and existing** `tests/test_trajectory_metrics.py tests/test_evaluation_boundary.py`; expect PASS without changes to previous scores/contracts.
- [x] **Step 5: Commit:** `feat: score frozen external flux forecasts`.

### Task 4: Pair the complete cohort and calendar axis

**Files:**
- Modify: `evaluation/external_model.py`
- Test: `tests/test_external_model_pairing.py`

**Interfaces:**
- Consumes: ordered scores from Task 3 and full candidate axis/exclusions from Task 1.
- Produces: `summarize_external_cohort(scores_by_variant_seed: dict, candidate_issue_times_ns, exclusions: dict, *, settings: dict) -> dict`, with complete cohort validation, primary paired seed effects, loss averages, pooled-MSE RMSE, seed leave-one-out and descriptive 1/3/7-day paired calendar sensitivity.

- [x] **Step 1: Add failing tests.** `test_exact_seed_origin_support_pairing`, `test_common_missing_seed_rejected`, `test_seed_mean_is_loss_mean_not_forecast_ensemble`, `test_seed_rmse_uses_pooled_mse`, `test_missing_origins_preserve_full_axis`, `test_utc_epoch_edges_and_empty_blocks`, and `test_bootstrap_metadata_and_repeatability`. Reject reordered/duplicate origins, different masks and attempted model-failure NaNs; verify empty and partial edge blocks retain counts and B2000/RNG17 is deterministic.
- [x] **Step 2: Run** `python -m pytest tests/test_external_model_pairing.py -q`; expect missing-summary failure.
- [x] **Step 3: Implement the interface.** Average three matched per-origin losses, pair before reduction and reindex onto the full 30-minute axis. Reuse `paired_block_bootstrap` semantics with UTC-epoch durations 86,400/259,200/604,800 seconds and minimum 9,000. Bootstrap only dex pinball and dex MAE; preserve undefined draw counts/conditioning. Mark baseline replication and fixed-checkpoint conditioning; return no p-value/significance or joint-seed interval.
- [x] **Step 4: Run tests; expect PASS.** Include all three block settings and all seed leave-one-out means, without selecting favorable output. Record V2's `NO_VALIDATED_REPLACEMENT` caveat in the result schema.
- [x] **Step 5: Commit:** `feat: pair external losses on fixed calendar support`.

### Task 5: Add a guarded runner and verify infrastructure

**Files:**
- Create: `experiments/external_evaluation.py`
- Create: `scripts/evaluate_external_models.py`
- Test: `tests/test_external_model_runner.py`
- Update: protocol readiness/results references only after executed checks.

**Interfaces:**
- Consumes: Tasks 1-4 and `TrainedJepa.load/predict`.
- Produces: `run_external_evaluation(config_path: Path, root: Path, *, v1_dir: Path, preparation_dir: Path, output_dir: Path) -> Path`, publishing immutable result, inputs, provenance, predictions and losses. CLI requires explicit locators and a fresh output directory; it never invokes training or automatic acquisition.

- [x] **Step 1: Add failing runner tests.** `test_synthetic_end_to_end_no_training`, `test_installed_source_mismatch_aborts`, `test_failed_arm_aborts_common_comparison`, `test_output_is_no_replace_and_inputs_unchanged`, `test_preflight_does_not_infer`, and `test_saved_checkpoint_batching_is_preserved` use fixtures/mocks only. Assert original nine checkpoint record identities remain unchanged, batch size remains 256, no fit/optimizer calls, and results contain the approval scope/retrospective limitations.
- [x] **Step 2: Run** `python -m pytest tests/test_external_model_runner.py -q`; expect missing-runner failure.
- [x] **Step 3: Implement orchestration.** Separate preflight from prediction. Reverify inputs/source at publication; include all lockfile hashes and full relevant dependency versions, historical versus inference provenance, exact per-seed checkpoint hashes and external preparation fingerprint. Use no-replacement publication under ignored `results/`.
- [x] **Step 4: Run targeted tests, normal installed import, CLI `--help`/preflight and the full regression suite.** Use the pinned environment and a matching normal installation. Preflight may consume January observation/preparation bytes but must not invoke any January predictor. Inspect `git diff --check`, final diff/status, ignored output/data paths and index for prohibited bulk artifacts. Obtain independent review of no-fitting, identity, metric and scope boundaries.
- [x] **Step 5: Commit/push milestone infrastructure to its existing research branch only:** `feat: add frozen external evaluation runner`. Report only executed checks, remaining scientific limitations and that full experiment execution still awaits explicit approval.

### Task 6: Separately approved full external replication

**Files:**
- New ignored immutable `results/experiments/<explicit-new-id>/` bundle.
- Future small tracked report/config/input-hash manifest only; no raw arrays/checkpoints.

**Interfaces:**
- Consumes: verified runner, frozen protocol/input identities and **later explicit user approval for full external evaluation**.
- Produces: all prespecified model/seed scores and paired descriptive results, including unfavorable outcomes and limitations.

- [x] **Step 1: Obtain action-specific approval and preserve its scope.** This is the required experiment gate, not a generic planning gate. Do not execute this task based on infrastructure readiness alone.
- [x] **Step 2: Run the exact frozen config once into a fresh ignored destination.** No fitting, tuning, seed/reference replacement, calibration or full experiment retries selected for favorable output.
- [x] **Step 3: Independently recompute scores/support from published forecasts, verify original input hashes and all planned arms/seeds, then report primary/secondary findings and failures.** Review figures/tables if produced; retain exposure, retrospective-causality, fixed-cohort and V2 reliability caveats. Main integration and any other milestone remain separately authorized actions.

## Execution follow-up — 2026-10-14

The planning-time PARTIALLY_READY status is preserved above. The user expressly
approved bounded retrospective implementation, fulfilling Task 0. Tasks 1–5
are implemented and reviewed, including a fresh-process provenance fix; see
[the verification/readiness report](../../PHASE1_GOES_ADAPTER_IMPLEMENTATION.md).
Full regression: 1,417 passed with one inherited import warning. Current status
is READY for the approved bounded retrospective scope. Feature-only publication
is checked before the completion response. Task 6 has not begun and requires
separate explicit approval; no January model prediction or metric was generated.
The original immutable readiness ledger and historical reports remain preserved.

## Task 6 completion — 2026-10-15

The user explicitly approved one bounded retrospective experiment. The exact
pinned runner/configuration executed once from commit `26479e0`, exited zero and
published the immutable fresh `goes-v1-external-january2025-approved-run` bundle.
All nine original checkpoint states/normalization and 13 classical fitted records
were preserved; all 22 arms shared 1,007 origins and 60,420 cells. Independent
native/QC and full saved-output metric/pair/calendar audits passed. Fresh focused
verification: 458 tests passed. No source/configuration change, fitting, model
selection, guard bypass, second inference or protected-branch integration
occurred. [The scientific report](../../PHASE1_GOES_EXTERNAL_EVALUATION.md) and
[execution manifest](../../../data/manifests/phase1_goes_external_execution.json)
retain outcome hashes, unfavorable findings, uncertainty and scientific limits.
The previous October 14 Task 6-pending paragraph is historical. Further model
runs or milestones need their own authorization. Final report review and
feature-only publication are verified before the completion response.
