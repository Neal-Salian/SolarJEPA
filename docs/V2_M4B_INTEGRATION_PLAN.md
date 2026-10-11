# SolarJEPA V2 M4B integration implementation plan

**Goal:** integrate controlled models with canonical evaluation records and paired
descriptive reporting, using synthetic development data only.

**Authority:** the user's M4B assignment specifies and authorizes implementation,
independent audits, synthetic verification, a dedicated branch and publication.
It authorizes no pilot, protocol approval, PR, protected-branch integration or
test release. This plan executes that specification continuously.

**Architecture:** thin adapters in `experiments/` consume existing training,
forecasting, evaluation and provenance contracts. Historical evaluation kernels
remain unchanged. A development runner installs mandatory fitting guards,
forbids test release, and publishes descriptive artifacts at D_LOCKED without
advancing the historical A–F state machine.

## Verified Git audit (OBSERVED, 2026-10-11)

| Ref | Verified SHA | Ancestry |
|---|---|---|
| main / origin/main | 1a4991da4dda9676caeb1d7e35a03408528c3188 | unchanged protected baseline |
| v1 / origin/v1 | 644648f7d555fcbcb3eed4495d37fecffdd1863a | common integration ancestor |
| controlled | 1826400ca9cacd6020f6a5d4bc9ca9b2b2b3eda0 | ancestor of M4A |
| M4A | ac3428f910b36b7f10cc0fbb0740ce6de62df5a7 | M4B starting HEAD |
| M0/M1 | fd7203bf9a2e1e3dd78d9750a948b823ab100d36 | ancestor of M2 |
| M2 | 94cae59398e52a65074ec66c73ad94bd47ca8867 | evaluation integration target |
| M3.1 | 5e88f3a7109296c9475378b77be0257a4f9363ab | descendant of M2; research kept separate |

Fetched before work. M4A and evaluation changed-path sets are disjoint; read-only
merge-tree reports no conflicts. Integrate M2 by a merge into
`feat/v2-model-evaluation-integration` only, retaining its provenance/reliability
harness. Do not merge M3.1 experimental inference methods: its production
records/comparison/diagnostics/splitting are identical to M2. Preserve its report,
plan and aggregate evidence byte-for-byte with source-ref attribution. M3
reproduction scripts remain on that source branch.

The original presentation checkout has untracked `.agents/` and
`docs/P1_FINAL_INTEGRATION_REAUDIT.md`; both are preserved. Work uses the managed
`v2-m4b-integration` worktree, created from M4A and published with upstream before
milestone edits. No main/v1 checkout or write is needed.

## Dependency map

```text
controlled / comparators / classical forecasters
  -> ForecastPrediction + model record + train-only Normalization
  -> v2_interfaces.evaluation_identity_fields
  -> v2_evaluation_adapters -> EvaluationIdentity / EvaluationRecord
  -> loss_panel_from_records -> calibration_diagnostics -> LossPanel
  -> v2_descriptive -> paired fixed-fold / per-seed descriptive summaries

TrainingSlice + Normalization + validation context/targets
  -> validate_fitting_artifacts -> v2_evaluation_safety hooks
  -> DevelopmentRun -> StagedRun lock and immutable publication primitives
```

## Global constraints

- No real-data training, downloads, January 2025 access or confirmatory evaluation.
- No changes to manifests, temporal definitions, proposed budgets or M1 defaults.
- M3.1 verdict remains `NO_VALIDATED_REPLACEMENT`; inference is unavailable.
- Only `DESCRIPTIVE_ONLY` and `INFERENCE_UNAVAILABLE` integrated status values.
- Missing target cells remain masked/null; primary panels reject partial support.
- No invented classical fit thresholds; A8 remains an explicit unavailable policy.
- Separate optimizer steps, examples, support, exposure and wall/RSS measurements.
- D07 convention and D09 embargo are development interface choices/caller inputs,
  not scientific approval of the proposed experiment.

## Adapter decisions and file responsibilities

| Adapter | Implementation decision |
|---|---|
| A1 | `v2_evaluation_adapters.build_evaluation_record`: validation-only; validate model, selection, normalization, spec, dataset, quantiles and exact support. Classical forecasts can use canonical records with explicit identities. |
| A2 | `split_identity(train, validation, declared_test_identity, fold_id=...)`: versioned seed-free hash of declarations, never test arrays. |
| A3 | `v2_evaluation_safety.StudyLock`: declared complete fold mapping, write-once study lock, E release hooks recheck all fold locks. |
| A4 | `calendar_bounds(validation)`: outward whole-UTC-day envelope of half-open partition bounds, verify every origin is inside original bounds. |
| A5 | `replicate_deterministic_record`: require explicit deterministic attestation; source identity and source seed retained in metadata. Quantile-linear is fitted per seed here. |
| A6 | `subset_records`: exact caller-declared ordered seed vector, no automatic favorable selection. |
| A7 | `register_fitting_guard` and `DevelopmentRun`: per-job actual training/normalization/evaluation/plan checks at B/C/D; complete planned job matrix required. |
| A8 | Explicit `INFERENCE_UNAVAILABLE`/policy-unavailable metadata; existing versioned acceptance wrapper preserved. No production policy is justified. |
| A9 | `descriptive_budget_table`: actual per-job phase/step/example/time/RSS records and matched J/B wall ratio, no acceptance threshold. |
| A10 | `check_comparator_cohort`: bind neural/linear training, normalization, window subset and validation support to controlled reference. |

## Tasks and executable verification

- [x] **1. Baselines and scoped integration.** Run full suite on exact M4A before
  merge; merge audited M2; reinstall the isolated non-editable package; run merged
  regression. Record actual counts independently of historical reports.
- [x] **2. Record adapters (coordinator).** Write failing adapter tests, then
  implement A1/A2/A4/A5/A6/A8/A9 in `experiments/v2_evaluation_adapters.py`.
  Strengthen training validation identity only if a content-mutation regression
  reproduces the origin-only identity gap. Test exact JSON round-trip for five
  arms/TCN/linear, schema/seed invariance, units/horizons/channel/quantile mismatch,
  deterministic replication attestation, masked support and calendar boundaries.
- [x] **3. Safety adapters (isolated implementer).** Own only
  `experiments/v2_evaluation_safety.py` and its tests. TDD A3/A7/A10, mandatory
  development restrictions, complete planned jobs, temporal overlap/embargo,
  changed normalizer, resume provenance, all-fold lock and immutable publication.
- [x] **4. Descriptive adapter (isolated implementer).** Own only
  `experiments/v2_descriptive.py` and tests. TDD reuse of canonical panels,
  cross-model provenance checks, stable paired differences, equal fixed-fold
  weighting, seed subsets, no CI/bootstrap/p-value or experimental imports.
- [x] **5. Synthetic end-to-end (coordinator).** Generate a bounded two-channel
  series with missing cells/gap and only train/validation windows; fit all five
  arms plus TCN and quantile-linear over two seeds and a classical baseline;
  verify reload, pairing, validation-only selection, metrics, provenance and
  no-replace development publication. Poison all test-release entry points.
- [x] **6. Independent review and final publication.** Fresh read-only review
  covers scientific identities, leakage, fairness, inference, provenance,
  immutability and V1 compatibility. Reproduce/fix confirmed findings with TDD.
  Run full suite after final source edits/reinstallation, normal imports,
  `git diff --check`, ignore/index/history audit and protected-ref checks; commit
  focused changes and push only M4B. Create no PR.

## Required handoff tests

T1 record round-trip; T2 seed-cohort panel and fitting-fingerprint rejection;
T3 three-way dex metric agreement at 1e-12 (float64, complete support);
T4 temporal/normalization/embargo guards; T5 all-fold lock;
T6 calendar endpoints; T7 declared deterministic replication;
T8 exact secondary seed subset; T9 comparator validation identity;
T10 synthetic D_LOCKED no-test guarantee; T11 full/V1 regression.
The reconciliation document will map each to exact test names and results.

## Review focus and audit discrepancies

1. Cross-arm matching must compare experiment/code/data/split/training/
   normalization/protocol, although historical pairing only verifies panel support.
2. Historical controlled validation identity binds origins/times, not values/masks;
   exact validation selection support must survive content changes.
3. Supplied records alone do not establish planned arm/seed completeness.
4. Quantile-linear uses seed-specific Adam minibatch order: zero initialization
   does not justify deterministic replication.
5. Historical pilot proposal says the loader reads every manifest while forbidding
   test access. Preserve that proposal; the M4B synthetic route constructs only
   development windows, and M5 requires a development-only loader decision.
6. Hooks are process-local; development wrapper must re-register them on resume.

## Execution ledger

Audit: three independent read-only agents completed Git, model and evaluation
investigations. Source/tests/configuration/manifests and M4A/M3.1 documents were
inspected; no raw dataset was opened. Historical August manifest language is
pre-exposure history, not current untouched-holdout eligibility.

Execution: audited M2 merge `6712ede91a804344db865ef0bd93ea64d7329bf1`;
M4A baseline **1,310 passed**, post-merge baseline **1,477 passed**, final full
regression **1,583 passed** with the same pre-existing NumPy warning. Final
targeted adapter/descriptive/safety/end-to-end checks: **106 passed**.
Two independent final reviewers verified fixes for scientific identity,
execution-mode, publication metadata and post-lock payload consistency findings.
Detailed results and dispositions are in
[the integration report](V2_M4B_INTEGRATION_REPORT.md).
Publication audit at `c028c3aa8e59173e7272ada1c59ef0b914a1241b` confirmed a
clean milestone worktree, exact origin/upstream equality, strict clean installed
provenance, unchanged protected/M4A refs and no prohibited data paths. This
documentation closure records that observed audit; its final branch tip is
reported in Git and the final user-facing response.
