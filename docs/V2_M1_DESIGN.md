# V2 M1 model-independent validation design and interface proposal

Date: 2026-10-10. Scope authorized by the current request after the
[M0 assessment](V2_M0_RESOLUTION.md). Add reusable validation only; no candidate
data access, JEPA experiment, new comparator, V1 artifact alteration or integration.
The earlier execution plan's model schedules/loss/runner work is deferred.

## Chosen architecture

Use P1/P2 immutable `ForecastSpec`, `ForecastContext`, `FutureGrid`,
`ForecastTargets`, `ForecastPrediction`, `TrainingSlice`, window builder and
train-only `Normalization`. Add an explicit minimum-gap option to the existing
chronological split validator. Build additive evaluation modules for versioned
records, fitting checks, calibration and statistical comparison. Preserve V1
scoring, training and configurations exactly. No dependencies or UI added.

Alternatives rejected: a replacement data/model framework would duplicate
validated work; changing V1 scoring/selection would alter historical semantics;
an end-to-end V2 runner would require unresolved model-owner decisions.

## Shared contract proposal

All model families emit P1 `ForecastPrediction` on the same `FutureGrid` and
experimental `ForecastSpec`, in native declared target units, with explicit
point interpretation and ordered noncrossing quantiles. Models consume context
and future coordinates only, never future observations. Adapter agreement is
required for a model with a different internal context/feature schema; do not
weaken P1's full-spec alignment to accommodate it silently.

An `EvaluationRecord` binds canonical target/prediction snapshots to an
`EvaluationIdentity`: schema version, experiment/model version, seed,
code/config/data-provenance/split/training/normalization identities and the
selection partition. Selection may use validation only. The actual model ID is
carried by `ForecastPrediction`. Support identity includes dataset/spec,
ordered origins, issue/future timestamps, observations and validity masks;
different support or targets cannot be silently paired. Provenance identities
are caller declarations, not authentication or proof of unseen training history.

Strict JSON serialization revalidates all schemas and restores masked null
observations as NaN. Bulk forecasts belong under ignored results, never Git.
Records do not load a dataset or discover a holdout. Future stronger baselines,
classical models and frozen/fine-tuned JEPA share this same boundary.

## Temporal and leakage validation

`chronological_partitions(..., embargo_ns=0)` validates explicit minimum gaps
without shifting dates silently. Partition-local window construction retains
its full context/lookback/target/maturity/group bounds, exact cadence and masks.
`validate_fitting_artifacts` recomputes normalization from canonical unique raw
training support, compares full statistics and checks evaluation alignment and
disjoint support. An externally fitted evaluation normalizer with relabeled
metadata is rejected when its values differ. Dishonest feature dependencies or
coincidentally identical external statistics cannot be inferred from arrays.

Tests cover overlap, insufficient embargo, context/horizon crossings, duplicate
and missing timestamps, nonboolean masks, delayed future-derived features,
normalization/evaluation reuse, post-boundary perturbation, serialization and
determinism. Use existing synthetic helpers or local artificial arrays only.
No changes to GOES/SoLEXS scientific readers or upstream quality rules.

## Statistical and diagnostic interfaces

`LossPanel` binds finite nonnegative per-origin losses for an ordered seed
cohort to exact origin times, support, metric/version/unit and complete UTC-day
calendar bounds. `paired_comparison` validates equal named folds, cohorts,
origins/timestamps/support and metric identity, then reports equal-fold paired
effects, relative effect with positive-reference guard, per-seed/per-fold
effects, seed SD, win fraction and leave-one-seed influence. Loss averaging is
not prediction ensembling. Failure/nonfinite loss is rejected, not filtered.

The canonical `loss_panel_from_records` adapter computes equal-cell per-origin
dex pinball from complete-target `EvaluationRecord` cohorts. It binds actual
support and quantile levels, requires one model/experiment/provenance recipe
within each panel, and preserves ordered seed IDs. It rejects partial masks or
point-only forecasts rather than fabricating quantile support. Raw `LossPanel`
is a lower-level trusted-input kernel; equality of caller labels alone does not
authenticate its derivation. Paired metric identity includes quantile levels.

One resampled seed vector is shared across all fixed folds/arms. Each fold draws
circular contiguous calendar-day blocks with one day vector shared across
seeds/arms. Keep zero-count days, weight selected sums by selected counts,
average folds equally and never resample fold identities. Fold calendars must
be disjoint: this kernel does not handle shared temporal paths through separate
day vectors. Caller must supply
block length, replicates, RNG seed and confidence explicitly. A required empty
replicate makes intervals unavailable without dropping/redrawing it. This is
a configurable kernel, not approval of V2.1 defaults or proof of coverage.

`calibration_diagnostics` returns per-lead/channel counts, quantile reliability,
pinball and symmetric central interval coverage/width/proper interval score in
explicit native or log10 units. Empty support uses JSON null, never invented
zero loss. Verify arithmetic against literal examples and metric consistency.
Robustness summaries are seed/fold/influence diagnostics; scientific strata
and formal nonsmooth calibration inference need separate protocol decisions.

## Implemented API map

All paths below are under `src/solar_flare_jepa/`. No import of Torch is needed.

| Module / API | Contract |
|---|---|
| `forecasting.splitting.chronological_partitions(dataset, boundaries, *, embargo_ns=0)` | Minimum raw partition gap, int64 ns; existing zero-gap default preserved |
| `evaluation.records.EvaluationIdentity(...)` | Experiment/model version, uint32 seed, code/config/data/split/training/normalization/protocol identities; schema 1, validation selection only |
| `evaluation.records.EvaluationRecord(identity, targets, prediction)` | Canonical snapshots, `.support_fingerprint`, `.fingerprint`, `.as_dict()`, `.to_json()`, `.from_dict()`, `.from_json()` |
| `evaluation.records.support_fingerprint(targets)` | Hash actual valid observations, masks and complete output grid/spec; invalid payload canonicalized |
| `evaluation.records.validate_fitting_artifacts(training, normalization, evaluation_context, evaluation_targets, *, identity=None, embargo_ns=0)` | Recompute train statistics; verify full declared support separation/alignment and optional fitting identities |
| `evaluation.diagnostics.calibration_diagnostics(targets, prediction, *, space, intervals=None)` | Native/log10 diagnostics with explicit dimensional references for log10; per-lead/channel counts and per-origin losses; absent support null; mixed native-unit aggregates unavailable |
| `evaluation.comparison.LossPanel(...)` | Ordered seed/origin IDs, integer issue times, finite nonnegative losses, support/metric/unit, whole UTC-day calendar bounds |
| `evaluation.comparison.loss_panel_from_records(records, *, calendar_start_ns, calendar_end_ns)` | Canonical complete-support dex-pinball adapter; quantile metric identity |
| `evaluation.comparison.paired_comparison(folds_a, folds_b, *, block_days, replicates, rng_seed, confidence)` | Explicit resampling settings; JSON effect/interval/seed/fold/influence report; no significance decision |

Identity strings are required nonempty declarations; they are not signatures
or automatically verified file hashes. The fitting audit verifies the declared
training/normalizer content, not all metadata such as source acquisition history.
Callers must archive source/config/data provenance separately through P1/P2.
Raw quality flags remain in the source/preprocessing lineage; the evaluation
boundary carries their derived Boolean validity masks and provenance identities.
It does not invent flag meanings or operational availability.

For a deterministic classical reference, repeat its identical fixed forecasts
under the neural model's paired seed labels when constructing a paired panel;
report one fitted reference, not multiple independent classical training runs.
With only one stochastic run, the joint seed-bootstrap API is unavailable.
Calendar-block inference requires documented UTC epoch nanoseconds supplied by
the caller. Integer coordinates alone do not prove a time scale; native SoLEXS
coordinates must never be relabeled as UTC to enter this interface.

Diagnostics retain per-channel native units. Unit-sensitive native aggregates
are unavailable across incompatible units; dimensionless coverage can aggregate.
Only relatively symmetric quantile tail masses receive the symmetric proper
interval score. Logarithmic references are declared, never silently assumed.

## Acceptance and limits

Test-first implementation, targeted then full suite, normal installed import
outside checkout, deterministic synthetic integration and independent code and
scientific reviews. Preserve all existing tests. Report warnings/failures as
observed. Check full diff, whitespace, branch/upstream and ignore/index/history
before publication. No PR or merge. Acceptance certifies infrastructure behavior
on tested synthetic inputs, not independent candidate status, statistical power,
nominal CI coverage, operational forecast causality or research superiority.
