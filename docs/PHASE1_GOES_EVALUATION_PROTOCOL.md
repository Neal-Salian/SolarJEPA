# Phase 1: frozen V1 models on external GOES observations

Date: 2026-10-13. Status: **PROTOCOL_ONLY / PARTIALLY_READY**. This document
predeclares a retrospective external replication; it records no external model
scores. It does not approve execution of the full experiment.

## Scope and approval boundary

Use the existing nine V1 checkpoints and recorded classical fitted parameters
without training, refitting, normalization fitting, checkpoint selection,
hyperparameter search or external-data calibration. The standing user request
already authorizes necessary inference/evaluation infrastructure **if readiness
is established**; it does not require a second generic planning approval. Full
external model execution always requires the user's later explicit approval.
No event, flare-onset probability, operational warning, SoLEXS, V2 training or
confirmatory significance claim belongs to this experiment.

**OBSERVED:** the V1 specification and prepared external specification share
fingerprint `094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94`:
60-second record-start bins, 120 context steps, 30 future steps, stride 30,
ordered XRS-A/XRS-B channels in W/m2, log10 transform with reference 1 W/m2,
complete eligibility and retrospective bin-end availability. This establishes
contract compatibility, subject to verified source identities and scientific
quality rules; missing adapter code alone is not scientific incompatibility.

**OBSERVED:** external preparation reports native preprocessing causality and
actual operational delivery as **UNKNOWN**. Reprocessed archive metadata can
list adjacent-day inputs. These limitations prohibit operational-causal claims;
they must remain visible in retrospective results and cannot be repaired by
model-level context-only inference.

## Exposure and temporal separation

V1 fits use 2024-05-01 through 2024-07-22 UTC; validation ends 2024-08-01;
the historical test ends 2024-09-01. External support is January 2025, half-open
`[2025-01-01T00:00:00Z, 2025-02-01T00:00:00Z)`. Verify full context/lookback,
target and maturity envelopes against **all** original train/validation/test
support. The existing external loader's frozen-July overlap check alone is
insufficient for this complete V1 separation check.

**OBSERVED:** V2's exposure ledger identifies external acquisition at
`28e222ba042b32c84dad49a446f0849c677af4b9` and external documentation at
`bd128295c8529e064473e483751ca747de2f57a5`; it explicitly says January 2025 is
not a fresh-test default. The preparation and catalog were previously inspected.
**UNKNOWN:** private/teammate runs, unrecorded access and full inspection history.
Call this a temporally disjoint external replication, never an untouched, blind
or confirmatory holdout. Freeze the existing V1 selections before January
inference; do not choose a checkpoint or reference using January outcomes.

## Immutable input and model cohort

Bind a new small input manifest to original V1 `summary.json`, all nine `.pt`
files, `test_predictions.npz`, `per_origin.json`, original configuration bytes,
data manifests, historical source identity, runtime lockfiles and the chosen
external preparation's `artifacts.json` and member bytes. Use byte sizes and
SHA-256 hashes. Preserve original artifacts. Record current inference source
and installed modules separately from historical training source; a new
inference commit is not evidence of historical training provenance.

Preserve pinned external product `v2-2-1`. The session's official-source check
identified later product `v2-2-2`; that is a provenance/version limitation to
report, not permission to repin or replace immutable observations.

V1 local artifact locator is configurable; the observed collection is
`results/experiments/v1-full-20261009/` in the primary checkout. The observed
external preparation is `results/experiments/goes-external-january2025-acceptance-d/`
in the external-validation worktree. Do not bake either checkout's absolute
path into tracked scientific identities. The selected preparation reports
1,488 candidate origins, 1,007 retained, 481 excluded and 60,420 scored cells;
these are observed artifact declarations to reverify, not success criteria to
force a later loader to match after an input identity changes.

| Role | Frozen cohort |
|---|---|
| Primary contrast | `jepa_finetune_seed17/29/43` versus `supervised_seed17/29/43`, matched by seed |
| Secondary descriptive arm | `jepa_frozen_seed17/29/43` |
| Point references | `persistence`, `training_mean`, `trailing_mean` (30), `drift` (30), `ar1`, `direct_ridge` (lag 10, alpha 0.1) |
| Probabilistic references | `persistence_empirical`; saved validation-selected `arima(2,1,0)`; `ar1-constant-normal`, `ar1-arch(1)-normal`, `ar1-garch(1,1)-normal`, `ar1-garch(1,1)-t`, `ar1-gjr-garch(1,1)-t` |

All named classical references are conditional on exact fitted-state replay
and compatibility checks. Preserve recorded convergence warnings, flags and
near-unit persistence; they are limitations of the frozen implementation.
Do not invent a retrospective fit-acceptance policy, replace a flagged fit,
rerun optimization or silently remove a model. A replay or numeric failure is
a reported blocking result for that arm; no model-specific origin dropping is
allowed. Historical reference selection remains fixed: ARIMA(2,1,0), with GJR
Student-t as the historical strongest GARCH/GJR reference, and empirical
persistence. No January reference selection is performed.

Saved classical records contain the required coefficients, increment table,
ARIMA parameters and volatility mean/scale/variance parameters, but no public
no-refit loader exists. Restore these records without `.fit`. The volatility
simulation recipe remains 1,000 simulations and `sim_seed=0`, with the existing
issue-time/channel RNG derivation. This is one fixed simulated forecast,
not three independent classical training seeds; retain simulation uncertainty
as an unestimated limitation. Repeated seed labels must be marked replicated.

V1 checkpoints retain training, normalizer, spec and seed declarations and
internal weight hashes. Their loader does not authenticate a caller-selected
external training history or bind a validation-support fingerprint; verify
records against the frozen run summary and original support independently.
Selection used training-standardized log pinball, not final equal-channel dex
pinball. Preserve that historical distinction; no reselection or retraining.

**OBSERVED (session checkpoint/state audit):** all nine checkpoints safe-load
and match saved records, training normalization and raw training statistics.
The first 256 historical test origins replay bitwise for all nine with the
saved batch size 256. A batch-size-2 probe changed outputs by up to
`4.107e-7` dex; preserve configured batching, CPU execution and dependency
identities. This is bounded same-host replay, not a full external run or
cross-host bitwise guarantee. Thirteen archived classical test arms replay on
the first two historical origins without fitting: twelve are bitwise equal;
direct ridge differs by up to `1.776e-15` dex. Record this numerical exception
and its comparison method explicitly rather than calling every replay bitwise.

## Forecast support and metrics

Keep the preparation's exact retained origin IDs/order, issue times, future
bin starts/ends, native targets and observation masks. Channel order is
`xrsa_flux`, `xrsb_flux`; lead steps 1..30 end at 60..1,800 seconds. All models
must predict the full fixed retained grid. Nonfinite, missing or crossing
forecasts fail; observed QC alone determines exclusions. Never fill a
point-only comparator with fabricated quantiles.

For observed native flux `F` and reference `r=1 W/m2`, define
`y=log10(F/r)` in dex. For quantile `q`, pinball is
`max(q*(y-yhat_q), (q-1)*(y-yhat_q))`. Quantile levels are exactly
`[0.05, 0.25, 0.50, 0.75, 0.95]`. For quantile arms, the point is the saved
native median. Deterministic controls retain their saved inverse-transformed
point interpretation; no distribution or physical conditional mean is inferred.

| Output | Predeclared reduction and interpretation |
|---|---|
| Primary loss | Equal mean over five quantiles, 30 leads and two channels per origin; equal retained-origin mean, then equal mean over the three saved seeds |
| Pinball diagnostics | Per quantile, channel, lead and channel-by-lead in dex; native pinball in W/m2 is secondary |
| Point losses | MAE and RMSE in dex and W/m2; aggregate, per channel, per lead and channel-by-lead |
| Marginal calibration | Inclusive central 50% `[q.25,q.75]` and 90% `[q.05,q.95]` coverage, width and interval score; quantile reliability `mean(y<=yhat_q)` |
| Coverage detail | Target/prediction counts and exclusions; every coverage metric by channel and lead, with aggregate equal valid-cell pooling |
| Effects | Paired `loss_J-loss_S` and `1-mean(loss_J)/mean(loss_S)`; negative difference favors JEPA; zero reference loss makes relative reduction unavailable |

For central interval endpoints `L,U` and observation `z`, use
`IS_alpha=(U-L)+(2/alpha)*max(L-z,0)+(2/alpha)*max(z-U,0)` with `alpha=0.5`
for the 50% interval and `alpha=0.1` for the 90% interval. Evaluate widths and
interval scores separately in dex and native W/m2, transforming both endpoints
and observation into the chosen space before arithmetic. Coverage and reliability
are dimensionless and invariant to the monotone log transform; do not duplicate
them as independent evidence. Pool all these diagnostics over the fixed observed
cells, with the declared channel/lead breakdown. This matches the existing V2
`calibration_diagnostics` formula without invoking its model/validation adapter.

All channel/lead weights are one. Reduce losses on identical observed cells
before comparing models. Compute RMSE as the square root of pooled squared
error, including across seeds; do not average lead RMSE, origin RMSE or seed
RMSE. Retain per-seed scores separately. Seed averages are averages of losses
and diagnostics, not an ensemble of predicted quantiles. There is no MASE
without an independently bound frozen training scale. Five quantiles do not
define exact CRPS, trajectory coverage, event probability or joint calibration.

## Pairing, missingness and descriptive uncertainty

The primary estimand conditions on these three selected checkpoints, this
training recipe, these observation-quality rules and this January period.
It does not estimate a new-seed or new-period population. Report all matched
seed differences, sample seed-difference SD, seed win fraction and all three
leave-one-seed-out means as descriptive sensitivity. Missing/failed planned
seeds invalidate the full primary cohort; never silently average the survivors.

Reconstruct the full regular 30-minute candidate axis from the frozen window
manifest, including excluded origins. Reindex retained per-origin losses onto
that axis; both arms receive NaN at exactly the same observation-excluded
positions. Store reasons and counts. Never compress separated valid origins
into an apparently regular series or treat model failure as missing observation.

For primary dex pinball and secondary dex MAE, first average the matched
three seed losses per retained origin, then use shared paired draws over
nonoverlapping **UTC-epoch** calendar blocks of 1, 3 and 7 days. Use 2,000
replicates, RNG seed 17 and nominal 95% percentile summaries for each block
duration. Minimum support is 9,000 seconds (120+30 one-minute steps); this
lower bound does not prove independence. Retain partial edge and empty-pair
blocks; pool selected paired loss sums/counts rather than block means. Record
undefined-replicate counts and the utility's conditioning on defined draws.
No seed resampling occurs. Native/dex RMSE, interval coverage and widths have
point summaries only; this protocol does not attach linear-loss bootstrap
intervals to nonlinear RMSE differences.

These are explicitly **descriptive fixed-checkpoint calendar sensitivities**.
V2 M2 found severe dependence/small-seed undercoverage; V2 M3's outcome is
`NO_VALIDATED_REPLACEMENT`. No method passed the full frozen reliability screen.
Do not call the intervals validated confidence guarantees, interpret zero
exclusion as significance, report p-values, use bootstrap sign fractions as
p-values, or infer future-period/solar-cycle generalization. Report all three
block settings without selecting the most favorable one. Operational delivery,
archive preprocessing causality, correlated solar activity, one satellite,
one month, QC-dependent retention and historical exposure remain limitations.

## Reusable APIs and remaining implementation

At V1 base `644648f`, reuse `training/jepa.py:TrainedJepa.load/predict`, canonical
forecast contracts, prediction snapshots, and source/artifact publication
utilities. Do not run `experiments/v1.py:run_v1`, which fits, trains and selects.
`forecasting/baselines.py:_Baseline.predict` and
`evaluation/trajectory.py:evaluate_trajectory` deliberately reject a new dataset
identity; retain these safeguards. An explicit external adapter must preserve
original training identity and bind the distinct external input identity.

External-validation ref `f309921` provides
`data/external_validation.py:build_external_windows` and
`evaluation/external_flux.py:evaluate_external_flux` without fitting or MASE,
plus `evaluation/uncertainty.py:paired_block_bootstrap` with full-axis checks.
Native external scoring does not yet cover quantile scoring/calibration.
V1 `log_scores` lacks channel RMSE/pinball/coverage and channel-by-lead detail.
Extend thin evaluation wrappers with these outputs; preserve existing APIs.

V2 provides reusable `evaluation/records.py:EvaluationRecord`,
`evaluation/diagnostics.py:calibration_diagnostics`, and strict pairing concepts
in `evaluation/comparison.py:loss_panel_from_records` and
`experiments/v2_descriptive.py:descriptive_comparison`. Its
`experiments/v2_evaluation_adapters.py:build_evaluation_record` accepts selected
V2 models on validation support only; it cannot adapt V1 external evaluation.
`validate_fitting_artifacts` also binds the original dataset identity. Do not
weaken these APIs or import the V2 training/release workflow to solve this task.

Readiness requires verified immutable inputs/cohort, unchanged compatible
scientific definitions, recorded exposure/limitations, no-refit state replay,
an external identity boundary, complete metric/pairing tests and matching normal
installed execution. Current status is partially ready until those checks and
missing adapters are resolved. Implementation-only checks use synthetic and
historical replay support; January model inference remains outside them.
While the overall verdict remains PARTIALLY_READY, the implementation plan's
non-code scope/authorization gate must be resolved before any adapter code is
written. This protocol does not grant an exception to the user's conditional
infrastructure authorization.

## Implementation follow-up — 2026-10-14

The original PROTOCOL_ONLY/PARTIALLY_READY status above records the October 13
planning state. The user approved bounded retrospective implementation; the
[verified adapter report](PHASE1_GOES_ADAPTER_IMPLEMENTATION.md) now records
**READY** for that scope. The declared cohort, original normalization, product/QC
pins, primary/secondary estimands, weights and uncertainty settings are unchanged.
Default `scripts/evaluate_external_models.py` execution is metadata-only
preflight. Full inference requires separate approval and an explicit caller
reference; the code records that assertion without authenticating it. Task 6
remains pending. Prior exposure, delivery and upstream processing unknowns,
fixed-checkpoint uncertainty and simulation limits remain attached to all future
results. No operational-causal or untouched-confirmatory claim is established.

## Approved execution record — 2026-10-15

The user subsequently approved one bounded retrospective experiment. Task 6
executed the exact pinned configuration once with all 22 frozen arms on identical
QC support. The [scientific report](PHASE1_GOES_EXTERNAL_EVALUATION.md) and
[execution manifest](../data/manifests/phase1_goes_external_execution.json)
record completed execution and independent output verification. None of the
declared losses, weights, normalization, checkpoints, seeds, product/QC pins,
calendar settings or inferential boundaries changed. Historical NOT_RUN and
approval-pending statements above remain dated planning records. No further
model run, calibration, model selection, retraining, operational claim or
protected-branch integration is authorized by this execution.
