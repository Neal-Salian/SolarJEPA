# SolarJEPA V2 M4B integration handoff (from M4A)

Audience: the developer (or Codex agent) who integrates the V2 model side with the
statistical evaluation infrastructure in **M4B**. Read with
[training protocol](V2_TRAINING_PROTOCOL.md), [baseline audit](V2_BASELINE_AUDIT.md),
[compute feasibility](V2_COMPUTE_FEASIBILITY.md) and the earlier
[shared interface contract](V2_SHARED_INTERFACE_CONTRACT.md).

Date: 2026-10-10. Source branch `feat/v2-training-protocol-feasibility`, based on
`feat/v2-controlled-model-development` @ `1826400`. Nothing here is approved.
M4A performed no confirmatory training, no real-data training, no data acquisition and no test release.

## 1. Branch and dependency map (OBSERVED by read-only git)

```
main 1a4991d ─▶ v1 644648f ─┬─▶ 1826400 feat/v2-controlled-model-development (model side)
                            │      └─▶ feat/v2-training-protocol-feasibility (M4A, this branch)
                            └─▶ 90571df research/v2-independent-validation (protocol docs only)
                                   └─▶ … ─▶ fd7203b feat/v2-m0-m1-validation-foundation (records, temporal checks, paired bootstrap)
                                              └─▶ … ─▶ 94cae59 research/v2-m2-statistical-validation
                                                         = research/v2-m3-inference-remediation (no unique commit yet)
```

- The model side and the evaluation side change **disjoint files**. A read-only `git merge-tree` of
  M4A-base against `94cae59` reported no conflicts (INFERRED: the textual merge is clean). The evaluation side's
  only shared-core edit is `forecasting/splitting.py` (+10 lines, `embargo_ns`), which the model side does not touch.
- M2 (`94cae59`) adds two things over `fd7203b`: a `max_calendar_cells` guard, and a paired-difference summation fix in
  `evaluation/comparison.py`. **Integrate against `94cae59` or later, not `fd7203b`.**
- **M3.1 has published nothing** (its branch equals the M2 tip). Do not cherry-pick unpublished work. Do not assume a method.
- The name "M3" collides with the execution plan's "M3 = approved bounded acquisition". The branch name refers to
  inference remediation.

## 2. What the model side provides (OBSERVED at this branch)

| Capability | API | Notes |
|---|---|---|
| Five controlled arms | `training.controlled.fit_controlled(train_slice, validation_window, ControlledConfig, pretraining=None)` | Explicit `TrainingSchedule`. Validation is now required (M4A) |
| Shared SSL | `pretrain_controlled`, `PretrainingArtifact.save/load` | Identity-checked reuse |
| Comparators | `training.comparators.fit_tcn`, `fit_quantile_linear` | Same windows, normalization and selection data |
| Paired-cohort check | `check_paired_cohort(records)` | Now also enforces identical validation support (M4A). Controlled arms only |
| Prediction | `QuantileForecaster.predict(context, future_grid) → ForecastPrediction` | Native W/m², `[O,H,K,Q]`, noncrossing, `inverse_transformed_point` |
| Checkpoints | `QuantileForecaster.save`, `load_forecaster` | Weights-only, bound to selected fingerprints |
| Losses | `training.losses` (`normalized_pinball_v1`, `dex_pinball_equal_channel_v2`, `check_levels`) | Level validation added (M4A) |
| Identity adapter | `experiments.v2_interfaces.evaluation_identity_fields(record, *, experiment_id, code_fingerprint, data_provenance_fingerprint, split_fingerprint, protocol_fingerprint)` | Returns kwargs for `EvaluationIdentity`. `config_fingerprint` = seed-free recipe |
| Budget summary | `training_budget_summary(record)` | Steps/examples/wall/RSS. No consumer exists yet |
| Staged runner | `experiments.v2_runner.StagedRun` (A→F), `TestReleaseAuthorization` | Test release off by default. Single run = single test identity |
| Benchmark harness | `scripts/benchmark_v2_feasibility.py` | Re-measure on the execution host |
| Proposals | `configs/v2_proposed/*.json` | PROPOSED, unapproved, pinned by `tests/test_v2_m4a_proposals.py` |

## 3. What the evaluation side provides (OBSERVED at `fd7203b`/`94cae59`; do not reimplement)

- `evaluation.records`:
  - `EvaluationIdentity` fields: experiment_id, model_version, seed, code/config/data_provenance/split/training/normalization/protocol fingerprints, `selection_partition='validation'`, schema_version 1.
  - `EvaluationRecord(identity, targets, prediction)` as strict JSON, with `support_fingerprint`.
  - `validate_fitting_artifacts(training, normalization, context, targets, *, identity=None, embargo_ns=0)`.
- `forecasting.splitting.chronological_partitions(..., embargo_ns=0)`.
- `evaluation.comparison`:
  - `loss_panel_from_records` (seed cohort, complete masks only, per-origin dex pinball).
  - `LossPanel` (whole-UTC-day calendar).
  - `paired_comparison(folds_a, folds_b, *, block_days, replicates, rng_seed, confidence, max_calendar_cells)`. It reports intervals, per-seed and per-fold differences and leave-one-seed-out, with **no accept/reject decision**.
- `evaluation.diagnostics.calibration_diagnostics` (reliability, coverage, interval score; no PIT).
- **Not present anywhere:**
  - test-release custodian code
  - a production classical fit-acceptance oracle
  - per-fold, attribution, M+, H2-binomial, 7-slot multiplicity and simultaneous-band endpoints
  - any consumer for the H5 cost endpoint

## 4. Field-level compatibility and required adapters

| Model emitter | Evaluation consumer | Status | M4B action |
|---|---|---|---|
| `ForecastPrediction` | `EvaluationRecord.prediction` | Direct (same P1 class) | — |
| quantile levels, `point_interpretation`, `model_id` | panel equality checks | Direct if every arm uses identical levels | Assert in the adapter |
| `seed`, `recipe_fingerprint`, `training_fingerprint`, `normalization_fingerprint` | `EvaluationIdentity` | Direct via `evaluation_identity_fields` | Integration test: seed-invariance across a cohort |
| `split_fingerprint` | `EvaluationIdentity.split_fingerprint` | **Ambiguous** | **A2**: define one seed-invariant value. Recommended: hash of (train split fingerprint, validation split fingerprint, declared test identity string), never the test windows themselves. Needs joint agreement (D07) |
| Prediction + validation targets | `EvaluationRecord` | **Adapter needed** | **A1**: `build_evaluation_record(forecaster, windowed_partition, identity_kwargs)`. Use validation partitions in M4B. The test partition goes only through `StagedRun.release_test` |
| Fold name | dict key in `paired_comparison` | **Missing** | **A3**: one `StagedRun` per fold, plus a study-level lock: release only after every fold run is `D_LOCKED` (protocol requires locking all folds first). Implement as a release hook, not by editing the runner's state machine |
| Calendar bounds | `LossPanel.calendar_start_ns/end_ns` | **Missing** | **A4**: derive whole UTC days from the partition bounds, and assert every issue time is inside |
| Deterministic models (linear, classical) — one record | `LossPanel` needs ≥2 seeds and identical seed vectors | **Adapter needed** | **A5**: repeat the deterministic forecast under the cohort's seed labels, as M1 docs prescribe. Record that it is a replication |
| Secondary arms (first 5 seeds) vs J/S (20) | identical seed vectors | **Adapter needed** | **A6**: subset J/S to the first 5 seeds for secondary comparisons |
| Runner fitting checks | `validate_fitting_artifacts(..., embargo_ns)` | **Not wired** | **A7**: register a `StagedRun` hook at `B_FITTED`/`C_SELECTED` that calls it per job. Embargo value pending D09 |
| `FitAcceptancePolicy` protocol (model side) | none | Missing | **A8**: the evaluation owner implements the policy from protocol §5 thresholds. The model side supplies wrappers only. Out of M4A/M4B model scope unless assigned |
| `training_budget_summary` | H5 cost endpoint | No consumer | **A9**: a descriptive table (median J/B wall ratio). Inference on it is not defined |
| TCN/linear records | `check_paired_cohort` | Not covered | **A10**: a cohort-identity assertion comparing `training_fingerprint`, `normalization_fingerprint`, `train_windows`, `validation` with the J/S cohort |

Rules for all adapters:

- Keep them thin.
- Put them in a new module, e.g. `experiments/v2_evaluation_adapters.py`. Do not edit `evaluation/*`.
- Do not duplicate bootstrap, pinball or calibration code.
- Never hard-code `block_days`, `replicates`, `confidence`, margins or thresholds. These are caller arguments pending D12/D13 and M3.1.

## 5. Dependencies on M3.1 and conditional outcomes

| M3.1 outcome | M4B consequence |
|---|---|
| Approves a method/settings for `paired_comparison` (or a successor) | Wire the approved function and parameters through A3–A6. Model side unchanged (predictions are method-agnostic) |
| Changes the evaluation API (new panel/endpoint types) | Re-target A1/A4–A6 only. Records and identities remain the contract |
| Requires dependence diagnostics on development losses | The pilot's validation `EvaluationRecord`s are the input. M4B must make them producible (A1) |
| **Verdict: inference remains unreliable** | M4B still delivers records, panels and descriptive per-seed/per-fold differences, which `paired_comparison` already reports. **No interval-based acceptance is wired.** M5 is blocked, or is re-scoped by a protocol amendment to descriptive reporting |

Do not implement provisional thresholds, the 1% margin, 7-slot multiplicity or block-length choices in M4B.
Interval outputs must not be labelled reliable nominal 95% evidence (M2 report §16 recommendation).

## 6. Required integration tests

1. **Record round-trip.** For every model kind (5 arms, TCN, linear), validation `ForecastPrediction` → A1 → `EvaluationRecord` → JSON → equality.
2. **Cohort panel.** J and S over ≥2 seeds → `loss_panel_from_records` accepts. Altering any seed's training/normalization fingerprint is rejected.
3. **Metric agreement.** On complete support, model-side `MetricAccumulator('dex_pinball_equal_channel_v2')`, V1 `log_scores` dex pinball and evaluation-side `calibration_diagnostics(space='log10')` pinball agree to 1e-12 for the same predictions. This guards the three implementations noted in [baseline audit §4](V2_BASELINE_AUDIT.md#4-losses-traininglossespy-v1-trainingjepapypinball_loss).
4. **Temporal guard.** The A7 hook rejects a training slice that overlaps validation, or a normalization refit on other data, with and without `embargo_ns`.
5. **Fold lock.** Release is refused while any fold run is below `D_LOCKED` (A3).
6. **Calendar.** A4 produces whole-day bounds containing every issue time. Off-by-one at partition ends is rejected.
7. **Deterministic replication.** A5 records are identical across seed labels and flagged as replicated.
8. **Secondary subset.** A6 yields identical seed vectors for frozen/TCN vs J.
9. **Comparator cohort.** A10 rejects a TCN record with different validation support.
10. **No-test guarantee.** End-to-end synthetic run through `D_LOCKED` never constructs or reads test targets outside `release_test`.
11. **Regression.** Full suite passes, including the V1 bitwise-parity tests.

## 7. Safe integration sequence (M4B)

1. Obtain authorization for M4B and for merging the evaluation branch into the M4B branch. This is a merge **into the new branch only**, never into `main`/`v1` or teammates' branches.
2. Create `feat/v2-m4b-evaluation-integration` from the M4A tip. Publish it with upstream tracking.
3. Merge `origin/research/v2-m2-statistical-validation` (≥ `94cae59`) into it. Run the full suite and record counts.
4. Implement A1, A2 (after D07 agreement), A4, A5, A6 and A10 with TDD. Then implement A7 and A3 as runner hooks.
5. Add integration tests §6. Run the full suite, a synthetic end-to-end run to `D_LOCKED`, and an independent review.
6. Stop. Request approvals (§9) and data re-acquisition before any pilot.
7. Pilot (separate authorization): execute `configs/v2_proposed/feasibility_pilot_proposal.json` once approved. It stops at `D_LOCKED`.
8. When M3.1 publishes: merge it into the integration branch, re-target adapters if the API changed, and re-run §6.

## 8. Verification evidence (M4A)

| Check | Result |
|---|---|
| Baseline full suite at `1826400` | 1290 passed, 1 warning (pre-existing NumPy RuntimeWarning), 65.2 s |
| New tests: losses (7 parametrized), controlled (2), comparators (1), proposals (8) | Written first. The 10 behavioural regressions failed before their fixes |
| Final full suite | **1308 passed**, 1 warning (same pre-existing warning) |
| Environment gotcha | The repository `.venv` holds a **non-editable** install. `test_installed_synthetic_run_does_not_require_optional_aditya_imports` fails closed ("Imported/checkout source identity mismatch") after any `src/` edit until the package is reinstalled. Observed here: 1307 passed + 1 failed before reinstall, 1308 after. The venv has no `pip`. Use `uv pip install --python .venv/bin/python --no-deps --no-build-isolation --offline .` |
| Benchmark harness | 3 CPU runs + 1 MPS microbench, no failures ([compute §2](V2_COMPUTE_FEASIBILITY.md#2-method)) |
| Independent final review | See §10 |

## 9. Outstanding decisions (none approved)

Register IDs refer to `docs/V2_M0_RESOLUTION.md`.

| Decision | ID | Needed before |
|---|---|---|
| Seeds, budgets, fixed schedule, training loss, λ grid, TCN, retry policy | D10 | Pilot |
| RSS ceiling, timeouts, threads, pilot wall budget | D11 | Pilot |
| Shared schema and `split_fingerprint` convention | D07 | M4B adapters A1/A2 |
| August handling in the pilot; data re-acquisition on the execution host | D02/D18 | Pilot |
| Embargo | D09 | A7 configuration; M5 |
| Estimands, margin, multiplicity; inference method and block length | D12/D13, M3.1 | M5 |
| Exposure attestations, candidate calendar, custodian, test release | D03/D04/D05/D18 | M5 |
| Classical acceptance policy owner and thresholds | D10/A8 | Pilot classical arm, M5 |

**Conditions before M5 (confirmatory):**

- M3.1 verdict published and acted on
- all decisions above approved and frozen with config/code/data/seed hashes
- pilot executed and reviewed, with the measured J/B cost ratio and RSS
- adapters and integration tests merged on the integration branch
- custodian appointed and attestations recorded
- fresh fold data acquired under the approved access process

## 10. Independent review

A separate reviewer with no write access to the repository audited the M4A diff for:

- temporal leakage, training fairness and reproducibility
- checkpoint provenance, baseline and quantile-loss correctness
- resource safety, test-set isolation and statistical-interface assumptions
- V1 compatibility

Findings and dispositions: [§10.1](#101-review-findings).

### 10.1 Review findings

_Filled in after the review; see the commit history for the review-fix commit if any._
