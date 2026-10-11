# V2 M4B interface reconciliation

Date: 2026-10-11 (Asia/Kolkata). Milestone branch:
`feat/v2-model-evaluation-integration`.

**Status: development integration, DESCRIPTIVE_ONLY;
INFERENCE_UNAVAILABLE.** The model/evaluation interfaces are connected on
synthetic train/validation inputs. This document does not approve the scientific
protocol, a real-data pilot, acquisition, test access or integration into protected
branches. A8 remains **POLICY_UNAVAILABLE**.

Read with the [M4B implementation plan](V2_M4B_INTEGRATION_PLAN.md),
[M4B integration report](V2_M4B_INTEGRATION_REPORT.md),
[M5 handoff](V2_M4B_M5_HANDOFF.md) and historical
[M4A handoff](V2_M4_INTEGRATION_HANDOFF.md). **OBSERVED** below means verified
source or execution; **DOCUMENTED** means a cited historical statement;
**INFERRED** means a consequence of those contracts; **UNKNOWN** is not established.
The integration report is the execution ledger for final test counts, independent
review and publication checks; this document maps contracts to their tests.

## Integrated source boundary

The starting model/M4A commit is
`ac3428f910b36b7f10cc0fbb0740ce6de62df5a7`. The evaluation implementation is
integrated from M2
`94cae59398e52a65074ec66c73ad94bd47ca8867`, retaining its canonical records,
fitting validator, loss-panel extraction, diagnostics, numerical fixes and
synthetic reliability harness. The adapters reuse these kernels; they do not
implement another pinball score, calibration calculation or resampler.

The M3.1 publication at
`5e88f3a7109296c9475378b77be0257a4f9363ab` is later evidence than the M4A
handoff's historical statement that M3 had no publication. Its report, research
plan, aggregate evidence and figure are preserved byte-for-byte with that source
attribution. Its experimental methods are **not integrated**. Reproducing M3.1
requires its source branch and recorded frozen executable commit; the copied
report alone is not an executable reproduction package. Its verdict remains
`NO_VALIDATED_REPLACEMENT`.

## A1–A10 source-to-target contracts

All paths in this table are under `src/solar_flare_jepa/`.

| Adapter | Source contract → target contract | Current status and limits |
|---|---|---|
| **A1** | Selected `QuantileForecaster` + validation `WindowedPartition` + explicit identity declarations → `experiments.v2_evaluation_adapters.build_evaluation_record` → canonical `evaluation.records.EvaluationRecord` | **IMPLEMENTED, validation only.** Supports five controlled arms, TCN and quantile-linear. Revalidates predictor options, selected weights, configuration, spec, dataset, normalization and exact validation-selection identity before prediction. Rejects any partition not named `validation`. Classical persistence uses the canonical constructor with explicit identities in the synthetic test; it does not pass through this V2 model-record adapter. |
| **A2** | Train split fingerprint + validation split fingerprint + declared test identity string + fold id → `split_identity` → `EvaluationIdentity.split_fingerprint` | **IMPLEMENTED for development.** Schema 1, convention `M4B_DEVELOPMENT_SPLIT_V1`, seed-free canonical hash. Explicit nonempty, distinct train/validation/test strings required. No test window or target is accepted. Scientific adoption remains D07. |
| **A3** | Complete named fold → distinct `StagedRun` mapping under one results root → `experiments.v2_evaluation_safety.StudyLock` → write-once study manifest and `E_TEST_RELEASED` hooks | **IMPLEMENTED generic infrastructure.** Every fold must be at least `D_LOCKED`; persisted plans, provenance, locks and sealed artifacts are re-read on lock/release. Changed/incomplete mappings fail. No release approval is supplied. `DevelopmentRun` cannot release tests even with a study lock. |
| **A4** | Validation partition's declared half-open integer UTC bounds and issue times → `calendar_bounds` → whole-day `LossPanel` envelope | **IMPLEMENTED.** Floors start and ceils end outward using exact integer arithmetic; verifies every origin belongs to the original `[start,end)` bounds. Includes empty calendar days. Does not infer calendar length from retained samples. |
| **A5** | One canonical forecast + explicit deterministic attestation + source execution id + ordered seed labels → `replicate_deterministic_record` → replicated canonical records and provenance metadata | **IMPLEMENTED with caller attestation.** Retains source seed, full source identity, record fingerprint and execution id; sets `replicated=True`, `independent_seed_runs=False`. Seed labels are not independent fits. **Quantile-linear is fitted per seed**, because minibatch order depends on seed; zero initialization does not justify replication. |
| **A6** | Ordered primary canonical cohort + caller-declared secondary seed vector → `subset_records` → exact ordered prefix | **IMPLEMENTED.** Refuses reordered, duplicated, missing or non-prefix selections. It supplies no automatic favorable-seed selection and embeds no proposed 20/5-seed values. |
| **A7** | Actual `TrainingSlice`, train-only `Normalization`, validation context/targets, run plan/provenance and explicit `embargo_ns` → `register_fitting_guard` / `DevelopmentRun` → hooks at `B_FITTED`, `C_SELECTED`, `D_LOCKED` | **IMPLEMENTED and mandatory in development wrapper.** Recomputes fitting identities and window subset, invokes `validate_fitting_artifacts` per job, binds model/evaluation records to plan, and retains every planned successful arm/seed at selection. D hooks record full job-payload fingerprints; the development wrapper rechecks them on locked resume/publication. Hooks are reinstalled on `DevelopmentRun` resume. Raw `StagedRun` callers must reinstall their hooks. No approved embargo value is inferred. |
| **A8** | Existing `forecasting.acceptance` `FitCandidate`, `AcceptanceDecision`, `FitAcceptancePolicy`, `AcceptedARIMA`/`AcceptedVolatility` → a production acceptance oracle | **POLICY_UNAVAILABLE.** Versioned wrappers/test doubles exist; no approved oracle, stationarity/convergence threshold, forecast-variance rule or retry policy is invented. Persistence exercises canonical classical forecasts without asserting accepted ARIMA/volatility fits. This is an explicit unresolved scientific policy, not a completed oracle. |
| **A9** | Actual model `budget`, `wall_seconds`, environment RSS and fitting identities → `training_budget_summary` / `descriptive_budget_table` → per-job table and matched J/B wall ratios | **IMPLEMENTED, descriptive.** Reports phases, steps, examples, selected window support, measured training time and process peak RSS; matches J/B fitting support. Median ratio has no acceptance threshold (`acceptance=None`). Shared attributed SSL time must not be added across arms; steps are not FLOPs and RSS is a high-water mark. H5 inference is unavailable. |
| **A10** | Controlled/TCN/linear model records → `check_comparator_cohort` → matching training, normalization, train-window and validation identities | **IMPLEMENTED.** Checks all supplied records, including exact validation-content identity. The guard separately verifies complete planned jobs and actual artifacts; cohort equality alone does not prove plan completeness or honest history. Capacity, objectives and compute differ across families. |

## Scientific and identity compatibility

**OBSERVED:** prediction, target and grid objects are the existing P1 contracts.
No parallel forecast schema was introduced. `ForecastPrediction` is in native
target units and carries `[origin,horizon,target]` point values and
`[origin,horizon,target,quantile]` quantiles. V2 log10 models use the
inverse-transformed median point interpretation. Native channel names/order,
units, forecast spec, horizon coordinates, issue times, origin ids and dataset
identity travel with `FutureGrid`; `EvaluationRecord` revalidates exact alignment.
Strictly ordered quantile levels and noncrossing native quantiles are retained.
The integration does not relabel these values as normalized units or dex.

`evaluation_identity_fields` retains
`INTERFACE_VERSION='solarjepa-v2-model-interface-1'` and returns the schema-1
`EvaluationIdentity` field set. It remains a plain mapping for existing callers;
A1 constructs the canonical object. The mapping is:

| Evaluation identity | Emitter / meaning |
|---|---|
| `model_version` | `model_kind:model_id:recipe_fingerprint` |
| `seed` | Explicit uint32 model seed |
| `config_fingerprint` | Seed-free `recipe_fingerprint`; `run_fingerprint` remains seed-specific in the model record |
| `training_fingerprint` | Actual `TrainingSlice.fingerprint` |
| `normalization_fingerprint` | Train-only `Normalization.fingerprint` |
| `selection_partition` / `schema_version` | `validation` / `1` |
| `experiment_id`, `code_fingerprint`, `data_provenance_fingerprint`, `split_fingerprint`, `protocol_fingerprint` | Explicit caller declarations; the guard checks their consistency with the supplied run/artifacts but cannot authenticate them |

Within one model panel, all identity fields except seed must match; exact target
support, model id, point interpretation and quantile levels must also match.
Across paired arms, model/recipe identities may differ while experiment, code,
data provenance, split, training, normalization, protocol and selection partition
must agree. Across fixed folds, the ordered seed vector, metric, experiment, code
and protocol agree; each arm retains one model/recipe identity. Data/split/training
identities can differ by fold. Fixed-fold calendars may not overlap.

The strengthened V2 `_validation_identity` binds origin count/ids/times, split,
spec and dataset plus content: observed context/target values and masks, context
and target bin bounds, and declared feature availability. Changing scored values
or availability at unchanged origins therefore changes selection identity.
Unscored values are canonicalized to NaN/null, preserving missingness without
promoting arbitrary masked payload to observations. This closes the old
origin-only selection identity gap.

**Compatibility limit:** historical V2 checkpoints may remain loadable under
their existing schema, but their old origin-only `validation` records lack the
new content identity. They cannot establish M4B exact selection support and are
rejected by A1/mandatory fitting checks when compared with current artifacts.
Their provenance is not silently upgraded. V1 prediction, training defaults,
configuration and checkpoint schema are unchanged; its bitwise parity check is
part of T11.

At `D_LOCKED`, the successful fitting hook records a fingerprint for the **full
model/evaluation job payload**, including predictions and accounting metadata.
`DevelopmentRun._verify_lock` compares current payloads with every successful D
seal and retains the runner's artifact/lock checks. Locked resume and development
publication reject changed live/persisted predictions, changed accounting and
missing D seals. This detects ordinary post-lock drift; the ledger and its seals
are not authenticated against a same-user actor rewriting both.

## Metric and descriptive-output contract

`loss_panel_from_records` delegates to existing
`calibration_diagnostics(space='log10', intervals=())`. On **complete common
support**, equal-cell dex pinball agrees with model-side
`MetricAccumulator('dex_pinball_equal_channel_v2')` and V1 `log_scores`.
The canonical metric identity hashes the full spec and quantile levels, so equal
textual metric names cannot hide different units/reference scales, horizons,
channels or quantile cohorts. Primary panel extraction rejects point-only or
partial-target support; it performs no imputation or favorable support dropping.
Canonical records themselves preserve masked cells for diagnostics.

T3's `1e-12` assertion compares the three formulas on the **same float64
predictions/targets with complete support**. It does not promise that a stored
float32 training-selection value equals a reconstructed native score to that
precision. The separate actual-checkpoint test uses `rel=2e-5, abs=2e-7` for the
float32 standardization/inverse-transform arithmetic. These are numerical
regression tolerances, not scientific margins or model-acceptance thresholds.

`descriptive_comparison` pairs losses before reduction, then averages origins
within each fixed fold, folds equally within seed, and seeds equally. Its
estimand label is `equal_fixed_fold_mean_origin_loss`; the signed effect is
**A minus B**, so a negative value favors A on supplied periods. It reports
per-fold/per-seed effects, sample seed-effect SD, win fraction and leave-one-seed-out
effects. Relative reduction is unavailable for a nonpositive reference mean.
Single-seed output is descriptive, with SD and leave-one-out effects unavailable.

All integrated descriptive outputs state `DESCRIPTIVE_ONLY` and
`INFERENCE_UNAVAILABLE`, citing `NO_VALIDATED_REPLACEMENT`. Difference/relative
intervals, standard error, p-value, significance and bootstrap sign fraction are
null. The adapter accepts no inference settings and calls no bootstrap or M3
experimental method. Seed SD and win fraction do not certify independent runs,
nominal coverage, significance, future-period generalization or JEPA value.

## M4A required tests: exact traceability

The following maps all eleven requirements from historical
[M4A handoff §6](V2_M4_INTEGRATION_HANDOFF.md#6-required-integration-tests).
Names are executable test functions, with parametrization providing additional
cases. Final executed results and counts belong to the
[integration report](V2_M4B_INTEGRATION_REPORT.md); source presence alone is not a
passing-test claim.

| Requirement | Exact test names and files | Contract exercised |
|---|---|---|
| **T1 record round-trip** | `tests/test_v2_evaluation_adapters.py::test_record_round_trip_all_model_kinds`; `tests/test_v2_m4b_end_to_end.py::test_synthetic_two_fold_all_models_descriptive_publication_without_test_access` | All five controlled arms, TCN and linear; canonical JSON equality, seed-free recipe identity, channel/quantile/horizon shapes; selected checkpoint reload equality. |
| **T2 seed-cohort panel / fitting fingerprints** | `tests/test_v2_evaluation_adapters.py::test_primary_two_seed_panels_reject_one_seed_fitting_identity_change`; `tests/test_v2_descriptive.py::test_cross_arm_common_provenance_mismatch_is_rejected`; `tests/test_v2_evaluation_safety.py::test_guard_rejects_changed_actual_model_fingerprints` | J/S two-seed canonical cohorts accepted directly by the panel builder; changing one seed's training or normalization fingerprint fails; actual per-job fitting identities and cross-arm provenance are checked. |
| **T3 three-way dex agreement** | `tests/test_v2_evaluation_adapters.py::test_three_way_float64_metric_agreement`; `tests/test_v2_evaluation_adapters.py::test_actual_float32_checkpoint_metric_matches_native_with_declared_numeric_tolerance` | Shared complete-support float64 formulas at `1e-12`; distinct declared float32 checkpoint tolerance. |
| **T4 temporal / normalization / embargo guard** | `tests/test_v2_evaluation_safety.py::test_guard_rejects_temporal_overlap_and_explicit_embargo`; `tests/test_v2_evaluation_safety.py::test_guard_rejects_changed_actual_model_fingerprints`; `tests/test_v2_evaluation_safety.py::test_guard_binds_actual_data_splits_and_code_provenance` | Training overlap, nonzero explicit embargo, changed normalizer/training/spec/window/validation identity, plan/data/provenance mismatches. |
| **T5 all-fold lock** | `tests/test_v2_evaluation_safety.py::test_study_lock_refuses_release_until_every_declared_fold_is_locked`; `tests/test_v2_evaluation_safety.py::test_study_release_rechecks_other_fold_lock_before_consuming_release`; `tests/test_v2_evaluation_safety.py::test_study_resume_rejects_changed_complete_fold_mapping`; `tests/test_v2_evaluation_safety.py::test_study_resume_reinstalls_release_hooks_and_rejects_changed_study_manifest` | Full declared fold mapping, persisted lock/artifact recheck, fail before consuming release, hooks on resume. Test release here is a synthetic generic-run infrastructure probe, not real-data release. |
| **T6 calendar endpoints** | `tests/test_v2_evaluation_adapters.py::test_calendar_uses_half_open_partition_bounds_and_checks_actual_origins`; `tests/test_v2_descriptive.py::test_fold_and_explicit_calendar_identity_guards` | Whole-day envelope, half-open end exclusion, exact calendars/nonoverlapping fixed folds. |
| **T7 deterministic replication** | `tests/test_v2_evaluation_adapters.py::test_deterministic_replication_requires_attestation_and_preserves_source_identity`; `tests/test_v2_m4b_end_to_end.py::test_synthetic_two_fold_all_models_descriptive_publication_without_test_access` | Explicit attestation, identical forecasts under seed labels, retained source provenance; persistence demonstration, no linear replication claim. |
| **T8 secondary seed subset** | `tests/test_v2_evaluation_adapters.py::test_seed_invariant_split_identity_and_exact_prefix_subset`; `tests/test_v2_descriptive.py::test_reversed_seed_order_is_rejected`; `tests/test_v2_m4b_end_to_end.py::test_synthetic_two_fold_all_models_descriptive_publication_without_test_access` | Exact ordered prefix, seed-invariant split/recipe, no arbitrary reordering or replacement. |
| **T9 comparator validation identity** | `tests/test_v2_evaluation_safety.py::test_comparator_cohort_rejects_changed_validation_selection_support`; `tests/test_v2_evaluation_safety.py::test_guard_recomputes_training_windows_instead_of_trusting_a_common_label`; `tests/test_v2_m4b_end_to_end.py::test_synthetic_two_fold_all_models_descriptive_publication_without_test_access` | Changed TCN-like validation content rejected, actual common train-window subset recomputed, real fitted TCN/linear included. |
| **T10 D_LOCKED no-test guarantee** | `tests/test_v2_m4b_end_to_end.py::test_synthetic_two_fold_all_models_descriptive_publication_without_test_access`; `tests/test_v2_evaluation_safety.py::test_guard_accepts_complete_actual_jobs_and_development_stays_locked`; `tests/test_v2_evaluation_safety.py::test_development_rejects_release_enablement_and_confirmatory_mode`; `tests/test_v2_evaluation_safety.py::test_development_rejects_non_development_execution_mode_in_plan`; `tests/test_v2_evaluation_safety.py::test_development_publication_is_forced_descriptive_and_cannot_be_replaced` | Only train/validation window constructors, poisoned release/bootstrap entry points, no release record, mandatory guarded development wrapper, rejected nondevelopment modes and no-replace descriptive publication at D_LOCKED. |
| **T11 full/V1 regression** | Full `python -m pytest -q`; `tests/test_v2_controlled.py::test_v1_compatibility_mode_reproduces_v1_fit_forecaster_bitwise`; `tests/test_training_foundation.py::test_checkpoint_reload_is_bitwise_deterministic_and_scores_native_units` | Whole integrated regression plus V1 bitwise parity/native-unit checkpoint behavior. Actual baseline, post-merge and final counts are reported separately. |

Additional named checks cover `test_selection_identity_changes_when_values_masks_change_at_same_origins`,
`test_selection_identity_preserves_declared_feature_availability`,
`test_record_refuses_mutated_selected_predictor`,
`test_masked_record_canonicalizes_unscored_values_and_panel_refuses_partial_support`,
`test_guard_rejects_incomplete_planned_seed_matrix`,
`test_guard_rejects_selectively_dropped_planned_seed_at_selection`,
`test_resumed_development_cannot_bypass_guard_with_a_changed_job_record`,
`test_development_publication_rechecks_model_records_after_lock`,
`test_development_refuses_post_lock_payload_drift`,
`test_each_model_recipe_is_stable_across_fixed_folds`,
`test_difference_is_reduced_after_pairing_before_model_means_cancel`,
`test_historical_bootstrap_and_rng_are_never_called`,
`test_inference_parameters_are_not_an_opt_in_escape_hatch`,
`test_budget_table_preserves_measured_cost_without_acceptance_threshold` and
`test_classical_policy_and_inference_remain_explicitly_unavailable` in the
corresponding adapter/safety/descriptive files above.

## Demonstrated execution and remaining limits

The synthetic end-to-end test uses two nonoverlapping fixed calendars, two seeds,
five controlled arms plus TCN and independently fitted quantile-linear: 28 guarded
model jobs per execution. It constructs a two-channel 1-second software fixture
with a missing bin and masked cells, a 10-bin context and five-bin horizon. These
are deliberate software-test settings, not GOES cadence or an approved study
recipe. It saves/reloads selected checkpoints, pairs full-support retained
validation windows, reports measured budgets, publishes immutable descriptive
artifacts at `D_LOCKED`, and repeats the entire execution. Canonical evaluation
record fingerprints and the scientific descriptive report agree across repeats;
wall time/RSS are measurements and are not claimed equal. Classical persistence
is separately constructed with explicit canonical identity and deterministic
replication metadata; it is outside the controlled/TCN/linear fit-job guard.

**OBSERVED scope:** these checks establish supplied-artifact consistency on
synthetic development inputs. **UNKNOWN:** real GOES operability/performance,
real loss dependence, independent seed generation, operational availability,
cross-platform bitwise reproducibility and confirmatory inference. A caller under
the same user account can read files outside the runner, supply dishonest
provenance/approval strings, alter permissions or use another results root.
Write-once artifacts, hashes, resume checks and one-root release registry do not
provide signed custody, access control or universal prevention of repeated test
access. The M5 handoff keeps these procedural limits and unresolved approvals
visible.
