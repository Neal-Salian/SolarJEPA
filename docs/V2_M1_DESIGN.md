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

One resampled seed vector is shared across all fixed folds/arms. Each fold draws
circular contiguous calendar-day blocks with one day vector shared across
seeds/arms. Keep zero-count days, weight selected sums by selected counts,
average folds equally and never resample fold identities. Caller must supply
block length, replicates, RNG seed and confidence explicitly. A required empty
replicate makes intervals unavailable without dropping/redrawing it. This is
a configurable kernel, not approval of V2.1 defaults or proof of coverage.

`calibration_diagnostics` returns per-lead/channel counts, quantile reliability,
pinball and symmetric central interval coverage/width/proper interval score in
explicit native or log10 units. Empty support uses JSON null, never invented
zero loss. Verify arithmetic against literal examples and metric consistency.
Robustness summaries are seed/fold/influence diagnostics; scientific strata
and formal nonsmooth calibration inference need separate protocol decisions.

## Acceptance and limits

Test-first implementation, targeted then full suite, normal installed import
outside checkout, deterministic synthetic integration and independent code and
scientific reviews. Preserve all existing tests. Report warnings/failures as
observed. Check full diff, whitespace, branch/upstream and ignore/index/history
before publication. No PR or merge. Acceptance certifies infrastructure behavior
on tested synthetic inputs, not independent candidate status, statistical power,
nominal CI coverage, operational forecast causality or research superiority.
