# Frozen V1 external adapters: implementation and verification

Date: 2026-10-14. **Verdict: READY for the approved bounded retrospective
scope.** Implementation and verification cover frozen prediction of the
previously inspected January 2025 science archive. Full experiment execution
is not authorized and no January model
predictions or new performance results have been generated.

The initial readiness audit at `9ae2283` remains a historical record. The
[evaluation protocol](PHASE1_GOES_EVALUATION_PROTOCOL.md) and
[implementation plan](superpowers/plans/2026-10-13-goes-external-model-evaluation.md)
define the unchanged cohort, support, scoring and execution boundary.

## Scientific scope and preserved limitations

The user explicitly approved implementation of the missing adapters while
accepting the bounded retrospective scope. This resolves plan Task 0; it does
not approve the full experiment. All nine saved V1 checkpoints, original
normalization, historical selections, pinned product `v2-2-1` and original QC
remain fixed. No model training, preprocessing fit, external calibration or
January-based selection belongs to the adapter path.

The [processing/exposure supplement](PHASE1_GOES_PROCESSING_LIMITATIONS.md)
records the fresh investigation. **OBSERVED:** recorded January acquisition
and preparation preceded the recorded strict V1 run. **UNKNOWN:** influence
on historical human decisions or private/unrecorded runs. Freezing the cohort
now does not create historical blindness. **DOCUMENTED:** upstream spike
selection, calibration and electron corrections involve processing dependencies.
**UNKNOWN:** exact pinned per-value/LUT dependence and historical delivery.
These limits remain attached to the approved retrospective claim; no causal
operational or untouched-confirmatory claim is made.

## Verification record

### Implemented boundaries

- `experiments/external_inputs.py` consumes the exact bytes pinned by the
  historical audit ledger. It verifies the complete nine-checkpoint cohort,
  original normalization and model records, full May–August V1 support, accepted
  January preparation, QC/exclusions and context/future grids. Returned arrays
  are immutable; publication reverification binds the actual live consumption
  state, including checkpoint snapshots, instead of trusting declared digests.
- `forecasting/frozen.py` restores all 13 saved classical fits without fitting,
  using existing prediction equations. It retains the historical training
  identity and separately binds the external dataset. Original baseline and
  `TrainedJepa` APIs remain unchanged.
- `evaluation/external_model.py` scores native W/m² and dimensioned log10 dex
  errors, equal-weight pinball, channel/lead diagnostics, reliability, inclusive
  interval coverage/width and interval scores. It preserves median versus
  inverse-transformed point semantics; point-only baselines receive no invented
  quantiles. RMSE is the square root of pooled squared error. Input fingerprints
  bind targets, masks, full grids, points, quantiles, levels and persistence.
- The cohort summary requires all nine exact variant/seed pairs and all 13
  classical scores in the production path. It pairs identical observations and
  grids, retains the full 1,488-position calendar axis and reasons, and rejects
  missing arms or model-failure losses. Primary fine-tuned/supervised and
  secondary frozen/supervised contrasts retain all seed effects, relative
  reductions, win fractions and leave-one-seed-out means. Classical fits are
  explicitly replicated across seeds. Seed diagnostics average scores; each
  RMSE is reconstructed from pooled MSE, with no forecast ensemble.
- `experiments/external_evaluation.py` and
  `scripts/evaluate_external_models.py` separate preflight from execution.
  Default preflight authenticates metadata/bytes without predictor construction.
  Future execution requires `--execute` and a nonempty `--approval-reference`;
  that reference records a caller assertion and does not authenticate human
  permission. The runner uses unchanged checkpoint loading/prediction through
  authenticated private temporary copies, retains CPU/batch/thread settings,
  and restores global torch settings. It rechecks inputs, source, protocol,
  runtimes, predictions and scores before atomic no-replacement publication.
  Full native inputs, masks, coordinates, forecasts, losses and identities are
  published only beneath ignored `results/experiments`.

The paired calendar utility/tests are also an exact selective port of
`f309921`, source SHA-256
`b8f28bfa92f1a4048d936dcde0ae34807caa41d308734f4058bc5ebd82bd0abf`.
All 1/3/7-day UTC-epoch settings, B2000/RNG17, nominal 95% and 9,000-second
minimum support remain fixed. Empty/partial blocks and undefined draws retain
their counts. Only dex pinball and MAE receive these descriptive summaries;
there are no p-values, significance claims or joint seed/population intervals.
`NO_VALIDATED_REPLACEMENT` remains explicit. Insufficient informative blocks
raise; the runner cannot select a favorable duration.

The native scoring kernel and its tests were copied byte-for-byte from
external-validation revision `f309921d776cf2deb632a886e8426e42bac1a050`;
marginal diagnostics and tests were copied byte-for-byte from V2 M4B revision
`2e3f87111ab7c3a881064aaad9dbd6d6298c69cd`. No broader V2 implementation was
ported. Kernel SHA-256 identities are respectively
`9bad67db288382c0a53e66d2d45ba1763c42a6011bc518332749f51e39dc648b` and
`5aaa921163a73b9917f4db94bf8d03ad9acbc695881fcb88c167dcc7ef67681c`.

### Focused evidence so far

Input-binding tests: **48 passed**, including altered consumption state,
re-enabled array writes and container/array subclass callbacks. Two independent
fix reviews resolved the consumption-state findings; the final scoped review
found no remaining issue. Metadata-only load/reverification authenticated nine
checkpoint states and 13 saved fits; it invoked no January predictor.

Frozen classical tests: **57 passed** with the opt-in immutable historical V1
artifacts, including 13 first-two-origin replays; combined baseline/statistical
regression: **160 passed**. Twelve native point arrays and all seven quantile
arrays were bitwise equal. Ridge's maximum difference was
`1.7763568394002505e-15` dex against a predeclared `atol=5e-14`, `rtol=0` bound;
this is approximate equality. Synthetic external grids exercised separate
dataset binding and no-fit sentinels.

Scoring and inherited metric checks: **168 passed**, using synthetic arrays.
Hand-computed pinball/interval arithmetic, mask changes, quantile identities,
pooled-MSE RMSE and preserved scoring contracts were tested. Independent Task 2
and Task 3 reviews each returned approved spec/quality verdicts without findings.
These counts overlap and must not be added into a unique-suite total.

Pairing/uncertainty/scoring checks: **95 passed**, including unequal observation
counts, exhaustive calendar support, exact quantile availability, relative-zero
cases and callback/mask-type rejection. Independent Task 4 review found no
issues. Synthetic runner checks: **19 passed**, including genuine synthetic
execution of all 22 arms, changed-input/source/lock aborts, no-fit sentinels and
actual `[256,1]` batching on 257 invented origins for all nine checkpoints.

Normal noneditable installation used `pip install --no-deps --no-build-isolation
--ignore-installed .`; `pip check` found no broken requirements. Normal CLI help
and actual metadata-only January preflight succeeded at `66c2bb4`, verifying
1,488 candidates, 1,007 retained origins (60,420 observed target cells), nine
checkpoints and 13 fits with `inference_performed=false`. Its planned execution
destination was not created. Normal installed bounded August replay reproduced
all nine points/five-quantile arrays bitwise on the first 256 of 1,436 origins,
preserving original batch256/CPU4threads. This does not qualify every original
origin or independently reproduce training.

The first whole suite at `66c2bb4` passed **1,416 tests** in 148.70 seconds,
including opt-in historical classical replay. One inherited netCDF import
warning reported a NumPy ndarray binary-size mismatch. The inherited suite
contains fitting on explicitly invented software fixtures; no scientific V1
fit, normalization refit or real January predictor was run.

Independent Task 5 review nevertheless reproduced an import-state defect:
loading the previously lazy calendar utility changed complete executable
provenance and would abort fresh-process publication despite unchanged source
bytes. A separate normal installed process reproduced the sole changed
`imported_source` field without inference. The synthetic provenance double had
missed this. Commit `55bccb3` loads the calendar dependency before initial
provenance capture and retains both strict flags and complete equality checks.
A fresh-process clean-Git regression failed before the fix and passed after;
the runner suite then passed **20 tests**. Independent scoped review marked the
finding addressed without new issues. A fresh normal installed process at
`55bccb3` also confirmed complete before/after provenance equality, with no
inference. The revised whole suite at `55bccb3` passed **1,417 tests** with the
same one inherited warning in 144.83 seconds, including all 13 opt-in historical
classical checks. A second actual preflight passed after the fix. These checks
establish infrastructure readiness, not January skill or external uncertainty
coverage.

Fresh baseline contract/scoring checks: 251 passed in 4.27 seconds, using
`tests/test_v1_foundation.py`, `tests/test_prediction_context_causality.py` and
`tests/test_evaluation_boundary.py`. Independent task reviews approved input
binding, classical restoration, scoring, pairing and the fixed runner. Whole
branch review and publication checks are recorded below after completion.

A local `main` ref read timed out during read-only verification. A fresh fetch
at task entry verified local/remote main equality; direct remote queries later
confirmed main `1a4991da4dda9676caeb1d7e35a03408528c3188`, V1
`644648f7d555fcbcb3eed4495d37fecffdd1863a` and the research branch's recorded
starting commit. No repair, rewrite or mutation of that ref was attempted.
Feature-branch status and explicit-SHA operations remained available. On October
14 the same bounded read succeeded: local `main`, `origin/main` and the direct
remote main query all returned the preserved hash above. The transient read
failure resolved without repository repair.

A fresh midpoint stream-hash check reproduced **259/259** preserved files
(265,951,467 bytes), including original datasets, checkpoints, acceptance
artifacts and preexisting untracked files. All 12 other worktree status strings
matched the task-entry snapshot. The same 54 branch/remote-tracking refs were
compared; only this research branch advanced. Codex auxiliary capture refs are
outside the initial branch-ref snapshot. The final post-test stream-hash check
again reproduced all 259 files and all 12 other worktree status records. No
protected or unrelated branch moved. No prohibited scientific payload appeared
in the tracked index or new feature history; actual checkpoint, raw NetCDF and
audit-output paths remain ignored. Final publication checks are recorded below
after completion.

## Current readiness evidence and remaining boundaries

| Requirement | Observed evidence |
| --- | --- |
| Immutable cohort and original preprocessing | Nine checkpoint byte/weight/record identities and identical training normalization are bound to the unchanged historical ledger; no fitting path is called. |
| External compatibility | Exact two-channel native/dex spec, 120-minute context, 30-minute horizon, original QC and preparation D fingerprints; distinct January dataset identity. |
| Temporal isolation | Full May–August V1 envelopes remain disjoint from January; context/future coordinates and availability are canonical. Upstream processing causality remains unknown. |
| Common support | 1,488 candidates, 481 original exclusions, 1,007 retained origins and 60,420 observed target cells; all 22 arms share this support or publication aborts. |
| Calendar support | Observation-only inspection found 31/11/6 informative UTC-epoch blocks for 1/3/7-day settings. No losses or predictions were used for this check; these counts do not establish independence. |
| Reproducibility | Normal installed source matches checkout; strict fresh-process provenance is stable after the fix; no development bypass. Current runtime and all three lock identities are recorded separately from historical declarations. |
| Nontraining verification | Full 1,417-test regression, bounded original-August replay, real no-inference preflight and independent task reviews. Inherited synthetic fitting tests do not retrain scientific models. |
| Execution boundary | Full January model predictions/metrics remain NOT_RUN/NOT_COMPUTED. The next action requires separate explicit human approval. |

Final executable source fingerprint at `55bccb3`:
`ed43551c1771f5a9154046cd416ca37f32b6e604c57fc97adb3f5bfcae681de5`.
Scientific protocol fingerprint:
`9492ce5aab184ee0c35a0d05c16016d3209c62e92eb16f7d373cd680e3051417`.
Config byte identity: 7,141 bytes, SHA-256
`2285ecd6858ca8c8500f300204c009ceb1d900d1808625be39119447bffb3caa`.
The original readiness ledger remains byte-identical and records the earlier
PARTIALLY_READY gate; it has not been rewritten to imply these later facts were
known then. The earlier audit/protocol link to this dated follow-up.

Current imported versions are torch2.6.0, NumPy2.2.6, pandas2.3.3,
SciPy1.18.1, statsmodels0.14.5 and arch7.2.0. Each checkpoint declares torch2.6.0.
The original summary does not establish historical scipy/statsmodels/arch
versions; current versions and bounded numerical replay do not invent that
history. Original V1 lacked a contemporaneous artifact manifest; the retained
audit pins identify the bytes observed later. Full original-origin replay and
independent optimization reproduction have not been performed.

No technical blocker remains for attempting the approved bounded retrospective
experiment. Historical blindness, actual operational delivery, exact upstream
code/LUT/per-value causality and training-population uncertainty remain
unestablished. They preclude broader operational or untouched-confirmatory
claims; they are disclosed limits of the explicitly approved retrospective
scope. Statistical simulation uncertainty remains unestimated; the existing
1,000-draw/seed0 recipe is preserved. One month/satellite and QC-conditioned
retention limit interpretation.

## Exact next action

Obtain separate approval to run the unchanged frozen configuration once into a
fresh ignored directory, preserving all 22 arms and the disclosed retrospective
scope. At the current storage layout, safe preflight is:

```sh
.venv/bin/python scripts/evaluate_external_models.py \
  --root "$PWD" \
  --config configs/evaluation/goes_v1_external_january2025.json \
  --v1-dir /Users/nealsalian/Desktop/SolarJEPA/results/experiments/v1-full-20261009 \
  --preparation-dir /Users/nealsalian/.codex/worktrees/goes-external-validation/SolarJEPA/results/experiments/goes-external-january2025-acceptance-d \
  --output-dir results/experiments/goes-v1-external-january2025-approved-run
```

Only after that separate approval, add `--execute --approval-reference '<actual
approval reference>'`. The supplied reference is traceability, not permission
proof. Storage roots are runtime locators and may be relocated only with all
pinned bytes/source contracts intact. Abort on any failed arm, input/source
change or occupied destination. Independently recompute scores/support from
published forecasts before reporting any new model-performance result, as plan
Task 6 requires. No PR, merge or protected-branch action is part of this phase.

## Whole-branch review and publication

Pending final read-only review and final branch-only publication verification.
