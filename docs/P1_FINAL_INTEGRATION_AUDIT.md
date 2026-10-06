# P1 final fresh integration-readiness re-audit

Date: 2026-10-06, Asia/Kolkata. **Decision: NOT_READY_FOR_INTEGRATION.**

This is a new audit after F1, R1 and N1 remediation. Two new **HIGH** findings
prevent readiness:

- **N2 — incomplete executing-source identity:** an accepted source-directory
  symlink omits forecasting modules from source hashing and package parity.
  Two successful ordinary CLI executions can share the same clean Git commit,
  every declared fingerprint and semantic experiment ID, while fitted means,
  predictions and scores differ.
- **N3 — public evaluation consumes invalid copied contracts:** ordinary
  deepcopied training/reference objects can violate canonical support or shape
  invariants and still produce successful scores. MASE changes from 2.0 to
  0.008; persistence-relative MAE skill changes from negative to positive while
  coverage remains 4/4.

Both findings were independently reproduced by the primary auditor and a fresh
final reviewer. Their conditions and limits are stated below. No BLOCKER-level
finding was established. The original F1/R1/N1 fitting and prediction exploits
remain closed in the independently tested model-boundary scope.

Under the user's HIGH stop rule, complete targeted/full-suite executions, fresh
real acceptance pairs and integration simulation were withheld. No finding was
fixed. This report is local/uncommitted; nothing was pushed or integrated.

## 1. Exact audited checkpoints

| Item | Independently observed SHA |
|---|---|
| Protected main, local and origin | 1a4991da4dda9676caeb1d7e35a03408528c3188 |
| Pre-audit feature HEAD, local and origin | 65369567d2f6cd2aebb4c1f4e7bd608fb393cb03 |
| Audited implementation | edea3df87c0b08fdc08e66fe1df597334270dad8 |
| Frozen research/design branch, local and origin | 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe |
| Original failed F1 candidate | 11b72bb0c714cf71edf1e5ccb390d38444bbb8c8 |
| Failed R1 candidate | 0f587d96d09583e3f7d15ce5b3d40145264e1ab6 |
| Failed N1 candidate | 8fa3877f66264ab2f9309c8f5a3aa7fa225df224 |
| Post-audit feature HEAD | Unchanged: 65369567d2f6cd2aebb4c1f4e7bd608fb393cb03 |
| Post-audit documentation commit | None; prohibited by the HIGH findings |

The active branch is feat/p1-experiment-evaluation-foundation. Remote:
https://github.com/Neal-Salian/SolarJEPA.git. Initial fetch and direct remote-ref
inspection agreed with local refs. Candidate/upstream divergence is **0/0**.
Main is an ancestor of the candidate and is its merge base; the research and
implementation checkpoints are also ancestors. There are 28 linear commits
after protected main. There is no unexpected merge, rewritten ancestry or
candidate/main divergence in the inspected chain.

The implementation-to-feature-HEAD difference contains only README.md,
docs/P1_CANONICAL_SEMANTICS_REMEDIATION.md, docs/P1_IMPLEMENTATION_REPORT.md and
docs/PROJECT_STATUS.md. Source/tests/configuration/package/data trees are
identical between the implementation and pre-audit HEAD.

## 2. Complete main-to-feature inventory and integration safety

The complete main...feature diff was captured and inspected: **43 files,
41 added and 2 modified; 10,881 insertions and 37 deletions**. No deletions or
renames. This replaces the original implementation's historical 29-added/
2-modified inventory; additional audit/remediation evidence and regressions
account for the growth.

| Category | Added | Modified |
|---|---:|---:|
| P1 documentation and saved plan | 11 | 1: PROJECT_STATUS |
| README | 0 | 1 |
| P1 experiment configurations | 2 | 0 |
| Result schema | 1 | 0 |
| Experiment CLI wrapper | 1 | 0 |
| Forecasting/evaluation/experiment package modules | 14 | 0 |
| P1 test modules | 12 | 0 |
| **Total** | **41** | **2** |

Full file inventory:

~~~text
M README.md
A configs/experiments/p1_goes_reference.json
A configs/experiments/p1_synthetic.json
A docs/P1_CANONICAL_SEMANTICS_REMEDIATION.md
A docs/P1_FINAL_INTEGRATION_READINESS_AUDIT.md
A docs/P1_IMPLEMENTATION_REPORT.md
A docs/P1_INTEGRATION_READINESS_AUDIT.md
A docs/P1_INTEGRATION_READINESS_REAUDIT.md
A docs/P1_LITERATURE_RECONNAISSANCE.md
A docs/P1_PREDICTION_CONTEXT_REMEDIATION.md
A docs/P1_PROPOSED_DESIGN.md
A docs/P1_REPOSITORY_AUDIT.md
A docs/P1_TRAININGSLICE_REMEDIATION.md
M docs/PROJECT_STATUS.md
A docs/superpowers/plans/2026-10-03-p1-experiment-evaluation-foundation.md
A schemas/experiment_result.schema.json
A scripts/run_experiment.py
A src/solar_flare_jepa/evaluation/__init__.py
A src/solar_flare_jepa/evaluation/events.py
A src/solar_flare_jepa/evaluation/trajectory.py
A src/solar_flare_jepa/experiments/__init__.py
A src/solar_flare_jepa/experiments/config.py
A src/solar_flare_jepa/experiments/fixtures.py
A src/solar_flare_jepa/experiments/provenance.py
A src/solar_flare_jepa/experiments/reference.py
A src/solar_flare_jepa/experiments/runner.py
A src/solar_flare_jepa/forecasting/__init__.py
A src/solar_flare_jepa/forecasting/baselines.py
A src/solar_flare_jepa/forecasting/contracts.py
A src/solar_flare_jepa/forecasting/splitting.py
A src/solar_flare_jepa/forecasting/windows.py
A tests/test_baselines.py
A tests/test_canonical_semantics.py
A tests/test_event_metrics.py
A tests/test_experiment_provenance.py
A tests/test_experiment_reference.py
A tests/test_experiment_runner.py
A tests/test_forecasting_contract.py
A tests/test_forecasting_splits.py
A tests/test_forecasting_windows.py
A tests/test_prediction_context_causality.py
A tests/test_training_slice_consistency.py
A tests/test_trajectory_metrics.py
~~~

Pyproject/build metadata, requirements-lock.txt, ignore rules, AGENTS.md,
pre-existing scientific configurations, data manifests/readers and scientific
reports are unchanged from main. No torch/statsmodels/ARCH dependency, raw
scientific data, trained model, generated experiment JSON or prohibited binary
was added to the tracked inventory. Actual NOAA NetCDF, SoLEXS ZIP, processed
Parquet, saved GOES summary and experiment-output paths remain ignored.

No source/script symlink exists in the actual candidate. N2 tests the current
runner against an alternative source layout it accepts; it does not claim that
the checked-out candidate already contains that layout.

Initial tracked tree/index were clean. The sole initial untracked file was
.agents/skills/paperclip/SKILL.md. It is absent from the index and its SHA-256
remains 4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424.
It has no package-discovery, runtime, test, installation or scientific-output
role in the inspected P1 code. Its preserved bytes participate only in the
historical preservation inventory. Paperclip was not invoked or committed.

## 3. Actual audit/remediation history

Git records the failed checkpoints and subsequent fixes rather than replacing
the failed reports:

| Stage | Actual commits and executable change |
|---|---|
| Research/design | 805f1c3; then c218969 saved plan |
| Initial P1 | 8154954 through 2162465 add contracts, raw-first windows, six baselines, metrics, provenance/runner; 11b72bb records implementation |
| F1 | 6868a258c512129b580169a94d7ec475b9cea1f5 preserves failed audit; b5ae4c653a4268a7ff4b78a3b6d07d6c07350233 joins windows to raw support; 8ba57aa58242facf7614e805695fe9e71406ea3c reconstructs exact-base contracts at fit; 0f587d9 records remediation |
| R1 | 990d6f3d04ce3028947059b2d8b5da3103f1c991 preserves failed re-audit; 5048d42616c41249b4115f2f2a1cbacde6ce4017 adds failing leakage regressions; 009547932e398edeef1bd2ede2ff3d10bc9e1862 captures causal prediction snapshots; 8fa3877 records remediation |
| N1 | bb044b9376fcae1de3a4bd1a288602baf621ed7c preserves failed final audit; f7f678c/ef45f85 add tests/owned category capture; 59212da/1eebb0c add tests/strict config keys and paths; f11e4e4/7fd9d60 add tests/factory key normalization; edea3df captures dict base content without subtype hooks; 6536956 records remediation |

Every listed historical audit/remediation document, README and status tracker
was inspected as context. Current source, tests, runtime probes and Git objects
were used for conclusions. Historical reports were not edited during this audit.

## 4. Superpowers workflow and independent review

| Skill/workflow actually read and used | Effect on this audit |
|---|---|
| using-superpowers and Codex tool guidance | Chose relevant audit workflows before substantive work; preserved user audit-only and protected-ref restrictions. |
| requesting-code-review and reviewer template | Assigned exact source/SHAs, requirements, severity and executable attack scope to fresh reviewers rather than forwarding remediation conclusions. |
| dispatching-parallel-agents | Three bounded, read-only roles reviewed contracts, mathematics, and provenance independently. Repository edits/Git mutations and extra fan-out were prohibited. |
| systematic-debugging | Traced N2 through enumeration/parity/runner IDs and N3 through copied ownership/shape/scale use; ran canonical and normal-layout controls and independently reproduced both. No repairs. |
| verification-before-completion | Ran fresh focused suites, inspected outputs and hashes, and withheld downstream checks on HIGH. Completion claims are limited to executed evidence. |
| Scientific/reproducibility review | Applied AGENTS scientific-integrity rules to manifests, gate states, pinned identities and adapter source; kept DOCUMENTED, OBSERVED, INFERRED and UNKNOWN distinct. No separate scientific skill was available or claimed. |

Fresh reviewers did not implement F1/R1/N1:

- Boundary reviewer: actual contracts, baselines, splitting/windows, config,
  tests; then a separate final cross-boundary review of N2/N3.
- Mathematics reviewer: actual six baselines, trajectory/events, contract
  inputs and independent literal/Fraction oracles.
- Provenance reviewer: config/fixtures/adapter/runner/schema/provenance,
  artifacts and scratch Git/CLI executions.

The boundary review initially found no HIGH in its fit/predict-only scope.
Its fresh final follow-up independently reproduced and classified **both N2 and
N3 HIGH**. This distinction preserves the scope of the earlier positive review.
Primary reproduction confirmed the same outcomes.

## 5. Fresh dispositions of every historical finding

STILL_OPEN_NONBLOCKING means the defect persists but the current bounded P1
scope does not require its broader guarantee. It does not mean corrected.
Nonblocking judgments below are fresh judgments, not inherited acceptance.

| Finding | Severity | Fresh disposition | Current evidence/decision |
|---|---|---|---|
| F1: raw/window fitting contradiction and unchanged fitting identity | Historical HIGH | **RESOLVED** at fit boundary | 53 regressions pass; all-six mutation and subclass attacks reject before fit; fitted fingerprint and numerical inputs use the same reconstructed TrainingSlice. N3 is a later evaluation consumer, not a reopened Ridge fit route. |
| F2: deepcopy/pickle restores writable arrays | MEDIUM underlying gap; HIGH consequence in N3 | **BLOCKING** through N3 | Eight fresh copy/serialization controls reproduce writable arrays. Fit/predict recapture protects their consumption, but the public evaluator consumes invalid copies and silently changes scores. Standalone universal copy immutability remains unestablished. |
| F3: incomplete artifact-tree/index symlink containment | MEDIUM | **STILL_OPEN_NONBLOCKING** | External directory, dangling and index symlinks pass verification. Indexed-file symlink, corruption and extra regular file reject. Normal private producer writes regular finite JSON; no indexed corruption was accepted. Complete tree containment must not be claimed. |
| F4: Git-quoted untracked paths bypass clean-source prefix gate | MEDIUM | **STILL_OPEN_NONBLOCKING** | Untracked scripts/é.py is quoted and admitted; ordinary ASCII control refuses. Its bytes are nevertheless hashed and quoted path recorded. Real candidate has no such source path; this case alone does not hide executing bytes. N2 independently defeats completeness. |
| F5: squared-error underflow gives false RMSE zero | MEDIUM | **STILL_OPEN_NONBLOCKING** | Fresh 2e-180 errors report RMSE 0 and incorrect zero-reference-loss reason; true RMSE is representable. Literal/rational ordinary cases pass. No affected default-scale P1 fixture/reference result established; universal finite-range correctness is not supported. |
| F6: duplicate dataset metadata JSON keys collapse | LOW | **STILL_OPEN_NONBLOCKING** | Duplicate policy keys fingerprint as their last-value canonical object. Config/sidecar duplicate-key parser refuses; normal adapter metadata is unambiguous. This ambiguity does not produce different consumed canonical model semantics in the fresh control. |
| F7: explicit post-fit estimator-setting mutation | LOW | **STILL_OPEN_NONBLOCKING** | Changing lookback 3 to 1 changes prediction 26 to 50 with old record; changing public name relabels output. Requires explicit estimator mutation; private runner does not perform it and returned parameter records are detached. |
| F8: malformed numeric/JSON/index edge handling | LOW | **STILL_OPEN_NONBLOCKING** | Boolean index version accepts; null entry raises TypeError; huge alpha/weight cause TypeError/OverflowError; 1e400 reader returns infinity. Ordinary config subsequently refuses nonfinite values and producer emits finite integer-versioned records; no malformed successful experiment established from these cases. |
| F9: avoidable dimensional-log intermediate range failures | LOW | **STILL_OPEN_NONBLOCKING** | Native 1e-110/reference 1e290 has finite log -400 and finite inverse, but intermediate ratio/power fails. Explicit refusal rather than fabricated output; ordinary-scale controls pass. |
| R1: future coordinates/availability admitted at predict | Historical HIGH | **RESOLVED** at predict boundary | 185 regressions pass; all-six copy/deepcopy/pickle/reconstruction/subclass variants reject historical future support and late availability; literal causal Persistence stays [10,11]. |
| N1: noncanonical categories, availability and caller aliasing | Historical HIGH | **RESOLVED** in audited canonical fit/predict/config/factory paths | 179 regressions pass; actual text/base-container capture precedes validation, identities and consumption; enum/numeric/custom objects cannot supply closed categories; owned snapshot observations and factory/Mapping probes agree. N2/N3 expose other boundaries. |

The separately documented numeric-subtype edge remains **LOW,
STILL_OPEN_NONBLOCKING**: custom int(3) with __int__ returning 0 can record zero
lookback then fail prediction via IndexError. Primitive JSON config rejects
such subtypes; all-six revalidated zero-context specs reject. It is an actual
validation defect, not a claim of fully strict arbitrary-Python numerical input.
No successful hidden identity/leakage route was demonstrated from it.

## 6. F1 fitting-boundary evidence

Source: contracts.py:516-607 reconstructs exact-base nested context/grid/spec,
validates raw bounds, dependency coverage, availability, exact coordinates and
raw-to-window values/masks. Its effective payload at :621-629 includes spec,
partition bounds/name, retained origins/issues, raw coordinates, features,
targets, masks and raw availability. Declared dataset/split labels are separate.

Baseline.fit at baselines.py:56-92 reconstructs a TrainingSlice before calling
_fit and records that same snapshot's fingerprint. Ridge uses matched window
values/masks only after this join. TrainingMean uses unique raw valid targets.

Fresh attacks changed values, masks, availability, coordinates, support,
categories, metadata and nested owners through copies, deepcopies, pickle,
unchecked subclasses and reconstruction. Reviewer checks include 42 all-six
raw/window attacks, dependency gaps, categorical hooks, coherent identity
changes and after-capture caller mutation sentinels. Captured arrays have
bytes-owned read-only buffers; setflags(write=True) fails. No different effective
fit under an invalidly identical effective training hash was established.

**Executed full existing F1 module: 53 passed in 0.71s.**

## 7. R1 prediction-boundary evidence and actual use

Baseline.predict at :100-127 reconstructs context and grid, independently
reconstructs their exact-base specs, validates alignment and fitted identity,
then passes the reconstructed context/grid themselves into _predict. It does
not validate one object and consume the original caller object.

The future grid contains coordinates/origins/spec/dataset identity; no realized
target values or masks. Supplying ForecastTargets to predict refuses.
ForecastContext enforces fixed past intervals and true-cell availability no
later than issue time. Masks make invalid entries inert; they do not authorize
future true observations.

Fresh reviewer attacks cover 30 all-six future-context and 30 late-availability
cases, coordinate/mask/category/spec manipulation, copies/deepcopy/pickle,
unchecked subclasses, alternate reconstruction, stale/subtype properties and
after-capture caller mutation. Instrumented original _predict logic receives
the detached exact-base state even after caller arrays/metadata are changed.

Literal ramp control: valid Persistence is **[10.0,11.0]** through each route.
Replacing support with the formerly leaking future bins that would yield
**[11.0,12.0]** now raises ValueError across all six baselines. A caller falsely
relabelling future measurements with scientifically false old coordinates is
not detectable from truthful-declaration contracts; no scientific origin of
arbitrary supplied numbers is inferred.

**Executed full existing R1 module: 185 passed in 0.51s.**

## 8. N1 canonical-semantics and ownership review

contracts.py:23-68 captures genuine string content via base string operations;
closed categories refuse non-strings and unknown text. Base tuple/list/dict
content is captured, non-string/duplicate canonical keys refuse, subtype
attributes are discarded. Numerical arrays use copied bytes-owned buffers.
Supported dataset metadata is finite JSON object text/bytes/bytearray, stored
as owned canonical text; decoded views are independent. Arbitrary Python
dict/list/set/array metadata arguments are not supported by that contract.

| Field family | Current representation/rule | Identity/use observations |
|---|---|---|
| Availability mode/policy | Plain strings; operational/retrospective_bin_end and explicit/bin_end_earliest closed sets | Spec/dataset hashes and causal checks consume normalized values; unknown enum-like objects refuse. |
| Eligibility, transform, dataset role, point interpretation | Plain strings in explicit closed vocabularies | Branches and fingerprints agree at constructor and fit/predict capture. |
| Names, units, origin/group/model identities, time/quality policies | Genuine nonempty ordered/plain text; uniqueness where required | Declared strings are fingerprinted and consumed exactly. Units are declarations, not inferred dimensional conversions or a unit ontology. |
| Partition and training role | Closed train/validation/calibration/test; TrainingSlice train only | Normalized before boundaries/manifest/effective fit identity. |
| Config/schema/dataset/model selectors and parameter keys | Owned base containers, genuine text keys, strict fields/types, closed selectors | Numeric key aliases, dict lookup redirects and pinned path .fspath impersonation refuse; factory controls preserve actual kwargs semantics. |
| Masks/status/numerical coordinates | Boolean arrays; integer nanoseconds; producer statuses | No category inference from numeric coincidence; canonical shapes/content are checked. Evaluation recapture gap is N3. |
| Supplied event labels/definitions | Genuine primitive text and ordered unique IDs | No invented real-event semantics; event scorer receives explicit outcomes. |

Semantically equal supported string/StrEnum/numpy-string forms normalize to
plain text; different literal units/policies/transforms remain distinct.
Case/whitespace variants are not guessed into known categories. Enum/IntEnum,
bool/numeric values, custom equality/.value/.name/__str__, container and Mapping
subtypes were attacked. Caller/nested owners, including arrays held only in
subtype attributes, did not survive model capture. No equivalent known N1
material collision was found in the reviewed paths.

**Executed full existing N1 module: 179 passed in 2.34s.** This is bounded
evidence, not an arbitrary-Python sandbox, race or interpreter-tampering proof.
Public evaluation's later consumption remains unprotected as N3 demonstrates.

## 9. Novel HIGH N2: executing source omitted from identity/parity

### Reproduction and observed outputs

The primary independently copied current src/scripts/schema/build inputs into
a scratch Git root, moved forecasting to aux/forecasting and committed an
in-root directory symlink:

~~~text
src/solar_flare_jepa/forecasting -> ../../aux/forecasting
~~~

The scratch .gitignore excludes /aux/. The normal unchanged CLI is run in two
fresh processes using that scratch source. Between runs, only the ignored
target source's TrainingMean calculation is changed from np.array(means) to
np.array(means)+1. This is an adversarial source-identity fixture, not a change
or fix in SolarJEPA's actual implementation.

Both CLI processes exit **0**, publish **complete** results with valid indexed
artifacts, and record:

| Declared item | Both primary runs |
|---|---|
| Scratch Git commit | e5eb93219a983affe28fe44d1d7387243f26ba5b |
| tracked_dirty / untracked paths | false / [] |
| Config hash | 8ebe67003ac4d52b0a897b72ac686edf97a8a827a74c1c18ecfd09fc1ab9402e |
| Dataset hash | 5487ecd66c8f4b9768db1c72d28cf466efbbf14da85a352befa4d62394f1c770 |
| Source hash | 78d6eb159a72b15f94bf7996779b0286588a12e3f4729c93810eec42a0d22ec3 |
| Split hash | 7bed1d53bafe6d3498f812fbc597bfde806fd83020f585db9535a83c83f5d102 |
| Effective training hash | 828d2e8585d98a4be5a52f147a85e92ab3b4d8a92d922901105bdb0df712553c |
| Semantic experiment ID, seed 17 | 37cfc0d38c205695a26e0bc28546f6a978ae9b6d37eeb8d00f4d3e7614522957 |

Actual fitted means are respectively
[2.3008928111843345,3.3394540427636357] and
[3.3008928111843345,4.339454042763636]. Test MAE changes
**0.7366108960049575 -> 0.26614098652884344**. Both source manifests/parity
records omit every forecasting module. Both nine-file artifact indexes verify.

The provenance reviewer and fresh final reviewer reproduced this in their own
scratch Git roots with different fixture commits and the same collision.
Normal candidate enumeration includes the baseline; explicit enumeration of
the symlinked baseline hashes its bytes. An ordinary tracked source edit
causes CLI refusal, exit 2/no output. Thus the problem is specifically omitted
effective source, not general absence of any cleanliness check.

### Root cause and severity

provenance.py:52 enumerates Python files with Path.rglob, which does not descend
directory symlinks in this runtime. The directory link itself is not indexed.
code_provenance :85-104 checks actual loaded/package files only for entries
in that incomplete inventory. Source verification and final runner recheck
repeat the omission. Runner :93-97 derives semantic IDs from the incomplete hash.
Ignored target bytes can change under one clean Git identity.

**HIGH:** successful scientific computations materially differ under identical
claimed executing-code identities. Artifact checksums faithfully record the
different output bytes; they do not recover omitted code provenance. This is
not a SHA-256 collision, hostile class hook, dependency-binary substitution or
process monkeypatch. It is an accepted local Python source layout.

**Limit:** the actual candidate has ordinary nonsymlink source and matching
installed files. The scratch root has its own Git commit. This finding does
not establish that untouched candidate artifacts are already wrong, but it
refutes the runner's accepted-root completeness/parity guarantee. No repair or
unilateral exclusion of the accepted layout was made.

## 10. Novel HIGH N3: scoring bypasses canonical consumption

### Ordinary-copy reproductions

The primary independently executed the minimal current public-API example
included in Appendix A. No custom classes, object.__setattr__, estimator
mutation, new data or constructor patch is needed.

1. Valid training raw targets [1,4,8,13] have adjacent-difference scale 4 and
   held-out MAE 8, so MASE=2. Ordinary copy.deepcopy restores writable arrays.
   Changing only copied raw targets to [0,1000,2000,3000] leaves stored windows
   unchanged. Evaluation accepts contradictory support, uses scale 1000 and
   reports **MASE=0.008**, with unchanged reported training split identity.
   Exact-base TrainingSlice reconstruction refuses that identical object:
   **Training window values contradict canonical raw training support**.
2. Deepcopy a valid persistence reference [0,1,2,3] shaped (2,2,1), then call
   values.resize((1,1,1),refcheck=False). Its old grid still declares four cells.
   Evaluation silently broadcasts the remaining zero to every cell, changing
   persistence MAE skill **-0.06666666666666665 -> +0.11111111111111116**.
   It reports valid_count=total_count=scored_count=4, fraction=1, no reason.
   Canonical ForecastPrediction refuses: **Prediction must have shape (2,2,1)**.

A valid unchanged deepcopy gives an exactly equal complete score report.
Additional reviewer controls show resized/crossing quantiles and below-domain
copied predictions score even when their constructors refuse; copied paired
grids with equally invalid past intervals also evade alignment comparison.
Hostile subclass fingerprint/name hooks are supporting observations only,
not needed for the severity judgment.

### Actual validation/use gap and limits

trajectory.py:132-147 checks isinstance, declared grid/dataset/spec alignment
and prediction finiteness. It does not reconstruct targets/predictions/training
or capture canonical snapshots. _training_scales :72-85 directly reads raw
training arrays, while :158-164 allows reference/quantile broadcasting.
The score report :212 includes the caller's split label but no effective
training fingerprint.

The corrupted training object's computed effective fingerprint changes.
**No cryptographic training-fingerprint collision is claimed here.** The failure
is accepting a canonical-contract contradiction and reporting favorable scores
without refusing or identifying the effective training change. The incomplete
reference turns a negative skill into positive skill despite declared common
full coverage.

**HIGH for the reusable public evaluator:** current ordinary copy/serialization
behavior lets canonical invariants disappear at a successful scientific scoring
boundary. This is a material consequence of F2 beyond standalone writability.
The user's invariant includes evaluation, coverage and provenance, so silently
narrowing P1 to the private runner would change the acceptance scope.

**Limit:** ordinary unmodified strict-JSON runner reachability is **not
established**. It builds canonical windows/training and immediately scores
baseline-returned predictions; it does not perform these mutations. This is
not proof that the six protected fit/predict paths consumed future observations,
or that their ordinary result artifacts have corrupt MASE/skill.

## 11. Six-baseline mathematical review

All six share the validated fit/predict snapshot boundaries described above.
Independent fixtures were built without importing expected-value test helpers.

| Baseline | Formula and independent result |
|---|---|
| Persistence | Latest valid counterpart repeated across leads. Context [6,10,NaN,NaN] with last two masked gives [10,10,10]. |
| Unique training mean | Valid unique raw targets, not overlapping window repetitions. Raw [2,5,11,23,47,95,191,383] gives 757/8=94.625 across leads. |
| Trailing mean | Valid observed counterparts inside fixed lookback. Last three positions of the masked context contain only 10: [10,10,10]. |
| Drift | Endpoint slope per elapsed cadence, extrapolated from last valid bin through future ends; stale context yields [22,26,30]. |
| Fixed AR(1) | OLS intercept/coefficient on adjacent valid unique raw pairs, then recursive elapsed-cadence advancement. Recurrence next=1+2*x and stale state 10 yields [87,175,351], with masked/gapped pair controls. |
| Direct ridge | Centered joint direct multi-lead/target regression, unpenalized intercept and slope ridge via augmented least squares. X=[-2,1,4], responses [3+4x,-1+2x,7-x], x=8: alpha=0 gives [35,15,-1]; alpha=6 with Sxx=18 gives [28,11.5,0.75]. |

Ridge admits only complete lag/full-target training rows after canonical raw
joins, and refuses incomplete prediction lags. Counterpart models require
matching native target/feature names and units. TrainingMean may predict its
fixed mean without complete observed counterpart state after shared context
validation. AR uses adjacent valid pairs, not invented gap bridging.

Transforms use declared dimensioned references. Native inverse-transformed
points are not described as physical conditional means. No ARCH/GARCH or
SolarJEPA training occurred. F7/F9 and numeric-subtype limitations still bound
the public guarantees.

## 12. Metrics, hand calculations and coverage

Independent mathematical review covered 40 exact-Fraction trajectory cases,
240 target/lead metric sets and all 256 confusion tables with TP/FP/FN/TN in
0..3. Ordinary calculations agree within floating arithmetic tolerance.

Trajectory formulas: MAE is pooled weighted absolute error; RMSE is square
root after pooled squared error; persistence skill is 1-model/reference
matched loss; training MASE divides by mean absolute adjacent valid unique
raw target difference; Pearson is an unweighted common-mask diagnostic;
pinball is max(q*(observed-quantile),(q-1)*(observed-quantile)), per supplied q.
Cross-target raw losses are undefined for unequal declared units.

| Event quantity | Verified formula |
|---|---|
| Confusion | Counts on common eligible/mature mask |
| Precision / recall-POD | TP/(TP+FP) / TP/(TP+FN) |
| FAR / FPR | FP/(TP+FP) / FP/(FP+TN) |
| F1 | 2TP/(2TP+FP+FN) |
| TSS | (TP*TN-FP*FN)/((TP+FN)*(FP+TN)) |
| HSS2 | 2(TP*TN-FP*FN)/((TP+FN)*(FN+TN)+(TP+FP)*(FP+TN)) |
| Brier | Mean (probability-outcome)^2 on the same scored mask |

Explicit maturity/missingness fixture scores two of four cells with
(TP,FP,FN,TN)=(0,1,1,0), Brier=13/32=0.40625. Empty masks and zero
denominators produce null/reason cells; probability-only scoring does not
invent binary decisions. Constant/single-pair Pearson, zero reference loss and
missing/zero MASE scale are explicitly undefined.

Normal prediction failure is not a model-specific mask. Runner uses the same
window/origin set across models; fit/predict/evaluate failures retain common
attempted origin IDs and target counts. Zero-weight lead fixture has four valid
cells but two aggregate-scored cells, with separate full lead diagnostics.
Overlapping origins remain explicit; no uncertainty or independence claim.
F5 limits tiny-range RMSE and N3 invalidates public malformed-input scoring.

## 13. Temporal/leakage and requirement traceability

| Requirement | Actual implementation | Fresh test/review evidence |
|---|---|---|
| Explicit native names/units, masks, availability and origins | contracts.py; fixed spec/context/grid constructors | forecasting_contract, F1/R1/N1 modules and independent boundary attacks |
| Raw-first chronological support | splitting.py; runner partitions before windows.py construction | forecasting_splits/windows scoped suite; dependency/boundary controls |
| Context/lookback, horizon/maturity and group support retained/excluded | windows.py: raw partition lookup only; interval_rows checks gaps; full support manifest | Existing window tests plus gap/group/partition attacks |
| Train-only model fitting | TrainingSlice joins and Baseline.fit snapshot | All six fitting probes, future-only changes and 53 F1 regressions |
| Target-free causal prediction | FutureGrid, ForecastContext and Baseline.predict snapshot | All six prediction probes and 185 R1 regressions |
| Effective categorical semantics/ownership | _canonical_strings/_category; strict config/factory capture | 179 N1 cases and fresh nested/container/Mapping checks |
| Six baseline formulas | baselines.py | Literal independent fixtures and scoped baseline tests |
| Trajectory/event mathematics and failure coverage | evaluation modules, runner failure records | 146 math/contract tests and independent rational/event oracles; N3 exception |
| Deterministic declared fixture and semantic inputs | fixtures.py, config.py, contracts' content identities | Runner/provenance/config scoped tests and scratch CLI controls |
| Code/package provenance | provenance.py, final runner recheck | Existing normal parity passes; N2 blocks completeness |
| Exclusive atomic records/indexes | provenance.py:126-210 | Concurrency/relocation/corruption probes; F3/F8 limits |
| Read-only pinned GOES adapter | reference.py | Reference tests in 240-case scoped suite; primary raw/Parquet/hash checks |
| Provided CLI/importability | scripts/run_experiment.py, unchanged pyproject | Actual outside-checkout installed imports/help and 22 hash matches |

Attacks include future target/feature perturbations, issue/split boundaries,
dependency gaps, incomplete/missing support/masks, duplicate/reordered origins,
malformed metadata and support, unavailable observations and reconstructed
contexts. No prohibited declared future support was admitted by fit/predict in
the executed probes. Fitted raw means/AR/ridge are train-only in ordinary
construction. This does not authenticate callers' physical observations or
invent missing detector timing/availability.

## 14. Fingerprints, provenance and publication

For regular canonical inputs, config, dataset, split, source, effective training
and seed determine semantic experiment IDs. Effective training excludes
future-only whole-dataset labels intentionally; declared dataset/split labels
remain independently recorded. Masked payloads or conservative source/config
inventory can cause different identities for the same particular model output:
input identity is not promised to be a minimal equivalence class of all
possible computations. Supported equivalent string/config forms normalize.

Model parameter records contain actual training/spec/source-associated
identities, references and transform. Package provenance includes Git branch/
commit, dirtiness, imported file parity, Python/platform and dependency versions.
N2 demonstrates an incomplete source inventory despite truthful Git recording.
N3 demonstrates direct public scoring's consumption and effective-training
reporting gap. Neither is dismissed as harmless because another label differs.

The strict config rejects unsupported SoLEXS/neural/ARCH modes and ordinary
duplicate keys, nonfinite settings and mismatched forecast declarations.
Dataset JSON duplicate metadata and numeric/index edge cases remain F6/F8.
Schema is a summary schema, not an authentication or complete artifact validator;
effective training hash is optional for historical schema-version compatibility.

Eight bounded concurrent publication attempts produced exactly one winner,
seven FileExistsError losers and no staging leftovers. Existing destination
replacement refuses. Nonfinite stage fails without publication; indexed byte
corruption and extra regular files refuse; regular copied relocation verifies.
Primary independently verified both N2 artifact trees (nine indexed files),
relocated one and reproduced metrics.json corruption refusal.
Artifact hashes verify output bytes, not scientific truth or complete code.
F3 does not support full symlink-tree containment; parent races, power-loss
durability and cross-platform atomic behavior were not established.

## 15. Tests actually executed in this audit

All commands used the existing .venv. Primary focused commands:

~~~sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_training_slice_consistency.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_prediction_context_causality.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_canonical_semantics.py
~~~

| Fresh execution | Actual result |
|---|---|
| Primary F1 module | **53 passed**, 0.71s |
| Primary R1 module | **185 passed**, 0.51s |
| Primary N1 module | **179 passed**, 2.34s |
| Boundary reviewer: baseline/contract/splits/windows | **124 passed**, 0.26s |
| Math reviewer: baseline/trajectory/events/contract | **146 passed**, 0.21s |
| Provenance reviewer: provenance/runner/canonical/reference | **240 passed, 1 warning**, 4.86s |
| Boundary scratch probes | 213 + 66 checks, exit 0 |
| Independent math probes | Six formulas, 40 rational cases/240 target-lead sets, 256 event tables; assertions pass |
| Primary N2/N3 reproductions and final reviewer controls | Exit 0 with defect assertions and canonical-refusal controls |
| Complete P1 targeted suite | **NOT RUN as a complete suite**, stopped on HIGH |
| Complete repository suite | **NOT RUN**, stopped on HIGH |

Focused modules total **417** tests, but scoped reviewer suites overlap them
and each other. Counts are not additive. **659/825** remain historical reported
results, not newly observed full-suite results from this audit. The historical
686/8/6 probes were not reused as current verification.

The existing warning was retained:

~~~text
tests/test_experiment_reference.py::test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability
RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject
~~~

No warning filter or dependency repair was used. Reviewer audit-harness errors
(fixture shape/container lookup) were corrected only in scratch and rerun.
The primary's first scientific check read the EDA summary instead of the
processed sidecar and raised KeyError; the corrected explicit sidecar check
passed. A reviewer first ran scoped pytest with default temp/bytecode settings,
then reran with explicit scratch/cache controls; ordinary ignored caches may
have been created. No tracked/source/scientific mutation resulted.

## 16. Acceptance and reproducibility decisions

Fresh requested synthetic #1/#2 and pinned GOES #1/#2: **NOT RUN**, because
N2/N3 HIGH findings were confirmed first. No new 54-score acceptance count,
zero-failure claim or byte-identical real rerun pair is asserted. The tiny
synthetic scratch N2 CLI runs are adversarial reproductions, not acceptance.

Same-environment ordinary deterministic behavior is supported by scoped runner
tests and prior artifacts only within their demonstrated input/layout limits.
N2 refutes an unrestricted executing-source/semantic-ID reproducibility claim.
Selected-artifact byte identity from remediation is historical, not a fresh
rerun result here. Relocation/corruption/publication checks were freshly run.

Clean independent environment/build reproduction, independent dependency-binary
attestation and cross-platform numerical/recording reproducibility are
**UNKNOWN/not demonstrated**. These future project-wide gaps do not by
themselves require Phase E or prevent bounded P1 integration, but no broad
portability claim is justified.

## 17. Installed package and CLI outside checkout

Primary ran outside checkout in the scratch directory with **PYTHONPATH
removed** and bytecode disabled. All **22 actual package modules imported
from .venv/lib/python3.13/site-packages**; every imported file SHA-256 equals
the corresponding current source file. Checkout source was not substituted.
Recorded normal source fingerprint:
203d0a05d46a75e968ae31e8457b19dc3c7d6c0004b5b1e64616308ca9a6ef9c.
Recorded Git commit is actual 65369567..., with clean tracked state.

~~~sh
cd /private/tmp/solarjepa-p1-final-fresh-audit-20261006
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --help
~~~

CLI help exits **0** and imports the installed runner. Pyproject declares no
console entry point: this is verification of the provided script wrapper and
installed package, not a claim of a separately installed CLI executable.

Runtime: Python 3.13.3, macOS 26.3 arm64; package 0.1.0, NumPy 2.2.6,
pandas 2.3.3, xarray 2026.7.0, netCDF4 1.7.2, pyarrow 25.0.1.
No package was rebuilt/reinstalled or dependency acquired during this audit.
This is same-machine existing-install evidence, not clean-environment proof.

## 18. Independent 109-identity preservation

The original temporary starting-inventory file is unavailable. The primary
therefore reconstructed the claimed path set from actual pre-existing configs,
data/results and Paperclip, excluding the two P1 configs and experiment runs,
then freshly SHA-256-hashed every path. Counts are exactly:

| Category | Count |
|---|---:|
| Paperclip pointer | 1 |
| Pre-existing configurations | 6 |
| Data paths | 70 |
| Pre-existing results | 32 |
| **Total** | **109** |

The reconstructed path-to-SHA mapping serialized as sorted, indent-2 JSON plus
newline has SHA-256 **3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193**,
exactly the historically committed starting-inventory checksum. Thus the
reconstruction recovers identical recorded inventory bytes, not merely the
same count. All **109/109** current file hashes match; zero changed/missing.
This approach and the missing original temporary file are disclosed explicitly.
Placeholders/housekeeping are included; this is not 109 science certifications.

Additional independent preservation evidence:

- **53** selected pre-existing tracked source/test/script/config/manifest/
  packaging/ignore/AGENTS/scientific-report files equal their main Git blobs.
- **55/55** explicit local path/hash pairs recursively obtained from scientific
  manifests match current bytes.
- All six pinned NOAA inputs verify; both original SoLEXS ZIPs pass inventory
  size/hash/listing checks. No archive was extracted, corrected or rewritten.
- Processed Parquet SHA is
  cc197f8186e0ec15b8ababd5a8c5549349d10fd15112cf4320ca4f23c114c068,
  matching the unchanged preparation sidecar.
- Historical audit/report/Paperclip bytes captured at audit start remain
  unchanged; no scientific data appeared in the tracked diff/index.

## 19. Scientific gates and GOES isolation

Observed D.1 gate: **BLOCKED_FOR_PHASE_E**.
Observed historical Phase E gate: **BLOCKED**.
scientific_application_approved remains **false**.

The unchanged minimum remaining evidence requires mission-applicable
pipeline-1.1 absolute clock, LC bin and continuous GTI/exposure policy;
approved correction state/workflow and matching HK/parameters if required;
approved response/channel-energy indexing, gain provenance and date/software
compatibility. Cross-payload alignment, calibration and scientifically
defensible real-event definitions remain unresolved. No new authoritative
reply/evidence or scientific resolution was established.

GOES reference source is read-only and isolated: pinned manifest/preparation/
sidecar/raw/Parquet identities and policy are checked; exact reread comparison
is required by adapter source; channel-specific quality masks, native W/m2 and
unknown actual delivery latency are preserved. Legacy absolute sidecar paths
are association evidence, not dereferenced paths. Artificial-format reference
tests pass; real fresh GOES acceptance was stopped. GOES infrastructure success
does not establish SoLEXS timing, calibration, labels or Phase E readiness.

No new science data, ARCH/GARCH fit, neural training, event-definition inference
or next-phase work occurred.

## 20. Remaining limitations and documentation discrepancies

- F3/F4/F5 remain real MEDIUM open limits; F6-F9 and numeric subtypes remain LOW.
  They do not independently demand future science/training to integrate P1's
  bounded intended infrastructure. Their unsupported broader guarantees are
  explicitly excluded above.
- Copy/serialization immutability is incomplete; its evaluated scientific
  consequence is now blocking N3 rather than merely an accepted caveat.
- NumPy/netCDF ABI warning remains unresolved. Existing executed checks still
  pass, but independent environment health was not established.
- Clean-environment and cross-platform reproducibility remain unverified.
- No caller-data authenticity, arbitrary hostile interpreter, mutable estimator
  tampering, atomic multi-field capture under concurrent mutation, parent race,
  power-loss durability or real operational forecast skill is claimed.
- F1/R1/N1 reports accurately describe scoped fixes and historical verification;
  their reported full suites/acceptance are not new audit observations.
- Source/package provenance claims need the N2 condition stated; current
  ordinary 22-module parity alone does not prove completeness for all accepted
  source layouts.
- Public evaluation/common-coverage claims need the N3 condition stated;
  valid-only constructor tests do not demonstrate consumption-boundary safety.
- README/status still describe the prior READY_FOR_P1_REAUDIT checkpoint;
  they were preserved, not silently rewritten as readiness approval.

## 21. Fresh final independent review and new finding register

The fresh boundary reviewer reviewed actual current provenance/trajectory code,
executed its own independent source-layout CLI fixture and public evaluator
copy reproductions, and ran controls for normal-layout hashing, dirty tracked
refusal, unchanged-copy equality and indexed artifact verification.
It concluded both N2 and N3 are **HIGH** within the exact scopes stated above.
It did not implement any F1/R1/N1 fix and did not repair the new findings.

| New finding | Severity | Integration disposition |
|---|---|---|
| N2 omitted executing source through directory symlink | **HIGH** | **BLOCKING**; same clean commit/all fingerprints/ID, different effective model computation |
| N3 invalid copied contracts accepted by public trajectory evaluation | **HIGH** | **BLOCKING**; silent MASE rescaling and reference broadcasting/skill sign reversal |
| New BLOCKER-level findings | None established | Does not downgrade the two HIGH blockers |
| Additional new MEDIUM/LOW defect | None separately established | Historical F2-F9/numeric limits remain explicitly dispositioned |

This is a bounded adversarial review, not an exhaustive proof against every
possible input. No equivalent old fit/predict bypass was established.

## 22. Integration simulation and proposed eventual procedure

Fresh merge-tree/worktree simulation: **NOT RUN**, under the HIGH stop rule.
Ancestry establishes an available fast-forward topology from the pinned main,
but topology is not a clean integration/readiness verdict. Packaging/scientific
preservation observations are positive within their tested scope; unresolved
N2/N3 prevent recommending integration now.

**No integration procedure is authorized or recommended for this candidate.**
After separately authorized remediation, a fresh independent audit must run
the withheld full suites, fresh synthetic/GOES acceptance pairs, deterministic
artifact checks and non-destructive merge simulation. Only after a READY audit
and explicit action-specific human authorization could the following guarded
procedure apply. The future audited SHA must be inserted; the current blocked
SHA must not be substituted as approved.

~~~sh
git fetch origin
git status --porcelain=v1 --untracked-files=all
# Review the preserved Paperclip pointer and require a clean tracked tree.
# Set APPROVED_FEATURE_SHA to the exact future human-approved audit/docs HEAD.
test "$(git rev-parse main)" = 1a4991da4dda9676caeb1d7e35a03408528c3188
test "$(git rev-parse origin/main)" = 1a4991da4dda9676caeb1d7e35a03408528c3188
test "$(git rev-parse feat/p1-experiment-evaluation-foundation)" = "$APPROVED_FEATURE_SHA"
test "$(git rev-parse origin/feat/p1-experiment-evaluation-foundation)" = "$APPROVED_FEATURE_SHA"
test "$(git rev-parse research/experiment-evaluation-foundation)" = 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe
test "$(git rev-parse origin/research/experiment-evaluation-foundation)" = 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe
git diff --quiet
git diff --cached --quiet
git merge-base --is-ancestor main "$APPROVED_FEATURE_SHA"
# Only after explicit authorization to integrate locally:
git switch main
git merge --ff-only "$APPROVED_FEATURE_SHA"
# Verify the resulting SHA/tree and approved checks.
# A push requires its own explicit authorization; if granted:
git push origin main:main
# Preserve feature/research/milestone branches; do not delete or force-push.
~~~

These commands were **not executed**. A user-managed reviewed PR is also a
possible future integration route; no PR approval, merge or main push was
performed here.

## 23. Evidence location and final preservation

Primary/reviewer scratch evidence:
/private/tmp/solarjepa-p1-final-fresh-audit-20261006.
This contains captured complete-diff.txt, inventory.txt, history.txt,
initial-state.json, focused test logs, independent reviewer reports/probes,
primary evaluation/source-collision logs and artifact trees, installed parity,
reconstructed historical inventory and scientific verification JSON.
Scratch files are supplementary local evidence, not committed scientific data;
the self-contained reproductions below preserve the essential attack steps.

Final Git checks retain the same feature/main/research identities, upstream
0/0, empty tracked diff/index, unchanged historical reports and Paperclip.
The only additional untracked file is this authorized new audit report.
No commits, pushes, main movement or implementation/config/test/data changes
were made. Main/research and all milestone branches remain preserved.

**NOT_READY_FOR_INTEGRATION.** Stop for human review of N2 and N3. No remediation
or integration permission is inferred from this audit.


## Appendix A. N3 standalone evaluator reproduction

Save the following to a temporary .py file and run with the existing matching
.venv/bin/python -B. It constructs synthetic contracts only and writes no
repository files. The assertions prove the defect and canonical-refusal
controls; exit 0 means the defect was reproduced, not that the audit passed.

~~~python
"""Self-contained public-copy evaluator mismatch reproduction; no repository writes."""
import copy,json,numpy as np
from solar_flare_jepa.forecasting.contracts import ForecastSpec,ForecastContext,FutureGrid,ForecastTargets,ForecastPrediction,TrainingSlice,_canonical_fields
from solar_flare_jepa.evaluation import evaluate_trajectory
S=10**9
s=ForecastSpec(1,1,2,('x',),('x',),('u',),('u',))
def grid(issues,ids):
    issues=np.asarray(issues,np.int64)*S;starts=issues[:,None]+np.arange(2,dtype=np.int64)*S
    return FutureGrid(starts,starts+S,issues,ids,s,'dataset')
raw=np.array([[1.],[4.],[8.],[13.]]);starts=np.arange(4,dtype=np.int64)*S
tg=grid([1],('train',))
ctx=ForecastContext(raw[:1][None],np.ones((1,1,1),bool),np.array([[0]],np.int64),np.array([[S]],np.int64),np.array([S],np.int64),('train',),s,'dataset',np.array([[[S]]],np.int64))
tr=TrainingSlice(ctx,ForecastTargets(raw[1:3][None],np.ones((1,2,1),bool),tg),starts,starts+S,raw,np.ones_like(raw,bool),raw,np.ones_like(raw,bool),0,4*S,'same-split',raw_availability_ns=starts[:,None]+S)
g=grid([20,21],('held0','held1'));targets=ForecastTargets(np.array([[[3.],[7.]],[[11.],[15.]]]),np.ones((2,2,1),bool),g);pred=ForecastPrediction(np.ones((2,2,1)),g,'toy')
persistence=ForecastPrediction(np.arange(4.).reshape(2,2,1),g,'persistence')
valid=evaluate_trajectory(targets,pred,tr,persistence)
corrupt=copy.deepcopy(tr);corrupt.raw_targets[:]=np.arange(4)[:,None]*1000
accepted=evaluate_trajectory(targets,pred,corrupt,persistence)
try:TrainingSlice(**_canonical_fields(corrupt,TrainingSlice))
except ValueError as exc:training_control=str(exc)
else:raise AssertionError('canonical training should reject')
bad_reference=copy.deepcopy(persistence);bad_reference.values.resize((1,1,1),refcheck=False)
reference_accepted=evaluate_trajectory(targets,pred,tr,bad_reference)
try:ForecastPrediction(**_canonical_fields(bad_reference,ForecastPrediction))
except ValueError as exc:reference_control=str(exc)
else:raise AssertionError('canonical prediction should reject')
assert valid['by_target']['x']['mase']['value']==2
assert accepted['by_target']['x']['mase']['value']==.008
assert valid['training_split_fingerprint']==accepted['training_split_fingerprint']
assert valid['by_target']['x']['persistence_mae_skill']['value']<0<reference_accepted['by_target']['x']['persistence_mae_skill']['value']
print(json.dumps(dict(valid_mase=valid['by_target']['x']['mase'],corrupt_mase=accepted['by_target']['x']['mase'],valid_scale=valid['training_scales']['x'],corrupt_scale=accepted['training_scales']['x'],same_reported_training_split=valid['training_split_fingerprint'],report_contains_effective_training_fingerprint='training_fingerprint' in accepted,training_control_rejection=training_control,valid_persistence_skill=valid['by_target']['x']['persistence_mae_skill'],broadcast_reference_skill=reference_accepted['by_target']['x']['persistence_mae_skill'],broadcast_reference_shape=list(bad_reference.values.shape),reference_control_rejection=reference_control,accepted_coverage=reference_accepted['coverage']),indent=2,allow_nan=False))
~~~

## Appendix B. N2 ordinary-CLI scratch-source reproduction

This is the exact primary reproduction script. It copies package/scripts/schema
into an isolated scratch Git root and changes only that scratch source. It
does not modify real source, data, Git refs or the index, and never pushes.
For a repeat execution, select a new absent scratch base directory, create that
base first, and adjust the base literal below. The script requires its
symlink-same-commit fixture directory not to exist and uses the actual repository
test configuration helper. Run from the actual checkout with its matching venv.
Both children are fresh CLI processes. Exit 0 confirms the source identity
collision, not integration readiness.

~~~python
from pathlib import Path
import os, subprocess, shutil, json, sys
base=Path('/private/tmp/solarjepa-p1-final-fresh-audit-20261006/primary-provenance')
actual=Path('/Users/nealsalian/Desktop/SolarJEPA')
sys.path.insert(0,str(actual/'tests'))
from test_experiment_provenance import config
root=base/'symlink-same-commit'; root.mkdir()
for name in ('src','scripts','schemas'):shutil.copytree(actual/name,root/name,ignore=shutil.ignore_patterns('__pycache__'))
for name in ('pyproject.toml','requirements-lock.txt','.gitignore'):shutil.copy(actual/name,root/name)
(root/'.gitignore').write_text((root/'.gitignore').read_text()+'\n/aux/\n')
(root/'aux').mkdir();shutil.move(root/'src/solar_flare_jepa/forecasting',root/'aux/forecasting')
(root/'src/solar_flare_jepa/forecasting').symlink_to('../../aux/forecasting',target_is_directory=True)
cfg=config(); cfg['seeds']=[17]; cfg['baselines']=[{'name':'training_mean','parameters':{}}]
c=root/'configs/experiments/p1_test.json'; c.parent.mkdir(parents=True); c.write_text(json.dumps(cfg))
for args in [('init','-q'),('add','.'),('-c','user.name=Scratch reviewer','-c','user.email=scratch@example.invalid','commit','-qm','Scratch source fixture')]:subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)
records=[]
for n in (0,1):
    if n:
        f=root/'aux/forecasting/baselines.py';f.write_text(f.read_text().replace("self._mean = _finite(np.array(means), 'training mean')", "self._mean = _finite(np.array(means)+1., 'training mean')"))
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(root/'src')
    run=subprocess.run([str(actual/'.venv/bin/python'),'-B',str(root/'scripts/run_experiment.py'),'--config',str(c),'--root',str(root),'--output-dir',f'results/experiments/probe{n}'],env=env,cwd=base,capture_output=True,text=True)
    out=root/f'results/experiments/probe{n}';record={'n':n,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
    if out.exists():
        result=json.loads((out/'result.json').read_text()); provenance=json.loads((out/'provenance.json').read_text());params=json.loads((out/'model_parameters.json').read_text());metrics=json.loads((out/'metrics.json').read_text())
        record.update(fingerprints=result['fingerprints'],experiment_ids=result['experiment_ids'],git_commit=result['code_commit'],status=result['status'],tracked_dirty=provenance['tracked_dirty'],untracked=provenance['untracked_configuration_paths'],means=[p['parameters']['mean'] for p in params if p['model']=='training_mean'],test_mae=[m['metrics']['aggregate']['mae']['value'] for m in metrics if m['partition']=='test'])
    records.append(record)
print(json.dumps(records,indent=2));(base/'source_symlink_same_commit.json').write_text(json.dumps(records,indent=2))
assert all(r['returncode']==0 and r['status']=='complete' and not r['tracked_dirty'] and not r['untracked'] for r in records)
assert records[0]['fingerprints']==records[1]['fingerprints']
assert records[0]['experiment_ids']==records[1]['experiment_ids']
assert records[0]['git_commit']==records[1]['git_commit']
assert records[0]['means']!=records[1]['means']
assert records[0]['test_mae']!=records[1]['test_mae']
~~~
