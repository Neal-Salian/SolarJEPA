# P1 N2/N3 remediation checkpoint

Date: 2026-10-07. Branch: `feat/p1-experiment-evaluation-foundation`.
Result: **READY_FOR_P1_REAUDIT**. This is a remediation record, not an
integration-readiness approval. A fresh independent audit is required.

## Checkpoints and evidence

| Identity | Exact SHA |
|---|---|
| Feature branch at start | `65369567d2f6cd2aebb4c1f4e7bd608fb393cb03` |
| Implementation before remediation | `edea3df87c0b08fdc08e66fe1df597334270dad8` |
| Verified final implementation | `cde534d67820bc34fbaf83a131667b72edab0016` |
| Final tests and fresh acceptance checkout | `3028ad10f3e6bcac0ce4df93650ae87465083460` |
| Protected local/remote main | `1a4991da4dda9676caeb1d7e35a03408528c3188` |
| Frozen local/remote research checkpoint | `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe` |

The only change between the verified implementation and the acceptance checkout
is test-process isolation. The subsequent commit containing this report changes
documentation only. Resolve its exact SHA with
`git log -1 --format=%H -- docs/P1_N2_N3_REMEDIATION.md`; it cannot contain its own
commit hash. The final delivery separately records that branch HEAD.

The failed [final integration audit](P1_FINAL_INTEGRATION_AUDIT.md) was committed
unchanged first, at `3d4fa36ed475f9eb13aac171ca0b4b6853747877`. Its SHA-256 remains
`99152af34e569a91206c164e6098717d3822f540f09c31ff59f2d5fadfaf5bb4`.
Earlier failed audits and F1/R1/N1 remediation reports remain historical records.

**OBSERVED** below means inspected source, Git, hashes or executed checks.
**INFERRED** conclusions are bounded by those checks. Instrument semantics not
established by scientific evidence remain **UNKNOWN**. Local detailed evidence
is retained under ignored
`results/experiments/p1-n2-n3-verification-20261007/` (called `E` below).
Logs, scratch Git repositories, wheels and acceptance artifacts are not committed.
The checked-in regression tests and this record provide portable reproduction
instructions; availability of the ignored local evidence on another machine is
not claimed.

## Invariants established before implementation

1. Material project source must be represented in executable-source provenance,
   or execution must refuse to publish a scientific result. A Git SHA alone does
   not identify installed, redirected or previously loaded Python code.
2. Evaluation must reconstruct and validate detached canonical targets,
   predictions, training support, persistence references, grids, masks and metric
   options. Those exact captured values must feed calculations, coverage and
   evaluation fingerprints. Constructor history is insufficient.
3. Publication must serialize the same canonical model output that is evaluated,
   with the requested coordinates and model identity. Invalid output must be an
   explicit failure, not an apparently valid forecast under different labels.
4. Previously established canonical categorical semantics, metadata ownership,
   training-support consistency and issue-time causality remain in force.

These invariants guide the supported Python/file-backed execution model. They are
not an interpreter security sandbox or an atomic snapshot of an entire mutable
filesystem; limits are explicit below.

## N2: reproduction and source-provenance repair

### Independently reproduced failure

The pinned starting implementation was copied into an ignored scratch Git
repository. Its `src/solar_flare_jepa/forecasting` directory was replaced by a
relative directory symlink to ignored `aux/forecasting`. A second CLI invocation
changed the target's training-mean computation by adding one. Both invocations
completed with clean tracked Git state and identical configuration, dataset,
split, training and source fingerprints and semantic experiment IDs:

| Observation | First | Changed effective source |
|---|---:|---:|
| Test MAE | 0.7366108960049575 | 0.26614098652884344 |
| Source fingerprint | `78d6eb159a72b15f94bf7996779b0286588a12e3f4729c93810eec42a0d22ec3` | same |
| Experiment fingerprint | `37cfc0d38c205695a26e0bc28546f6a978ae9b6d37eeb8d00f4d3e7614522957` | same |

Scratch Git identity was `8abe4712f5092fdb68a99c9cc4eca4a66b79dd43`, not a real
SolarJEPA branch. Evidence: `E/historical-n2-red.log` and
`E/historical-n2-complete/source_symlink_same_commit.json`.

The original recursive glob omitted Python modules behind directory symlinks.
Parity checks iterated that incomplete inventory, so they omitted the same
modules. Python imports followed the directory link and executed different
bytes. Changes in ignored external target files did not dirty Git. Consequently
neither recorded source identity nor experiment identity described the changed
effective computation. This path was reachable through the ordinary CLI.

### Explicit policy and implementation

Policy A: **refuse symlinked reproducibility source**. This includes file and
directory links, lexical ancestor components, relative/absolute and
inside/outside-checkout links, nested/dangling links and loops. A link is refused
even when its current target has identical bytes. This policy also applies to
the execution package, including unused package modules inspected without
importing optional scientific readers.

`experiments/provenance.py` checks lexical path components before resolution and
walks directories with explicit inspection of link entries. It checks regular
files, hashes bytes, and compares device/inode/size/mtime/ctime before and after
hashing. The source inventory covers project Python source/scripts, P1 configs,
the result schema and package/lock metadata. Installed/checkout parity checks
use actual loaded module locations or actual unused package files. Unexpected
project modules absent from the inventory are refused. Source identities and
Git state are checked again before atomic publication.

The tests cover replacement during discovery/hashing and replacement after
initial provenance, installed source redirection, relocation, clean controls,
and CLI refusal. Filesystem-wide locking and undetectable replace-and-restore
(ABA) races are not claimed to be solved.

### Related N4: loaded source and namespace lifecycle

Independent review generalized N2 beyond paths. Hashing today's `.py` file can
misrepresent an already imported function, a timestamp-valid stale bytecode
cache, an alternate loader, an evicted module retained by a `from` import, or an
older globals dictionary attached to otherwise identical function code.
These were material source/identity disagreements and received additional
bounded failing-test/fix/review cycles, rather than being hidden as limitations.

The new `_executed_source.py`, initialized by the package, captures the source
bytes compiled by project imports. It checks bootstrap code, uses source rather
than timestamp-only bytecode caches, retains execution/loader history, and
refuses unrecorded or changed loaded source. Audit observation covers standard
alternate loader executions; bootstrap checks cached modules and active loader
frames, including other threads. At the provenance boundary, active project
frames must match captured filename/code and the exact current base-module
namespace. A retained older namespace cannot attest itself merely by sharing
code and filename with the current module.

An independent worker-loader reproduction changed a prediction from
`2.061095831704141` to `3.061095831704141` under the same identity in an interim
candidate. A subsequent independent reproduction retained identical function
code/filename but older globals. Both are now rejected before publication.
Completed deferred-import, cached/uncached and worker variants are retained in
the 27 loaded-source regression cases. The final namespace review repeated the
original counterexample unchanged and observed a namespace-ownership refusal.

After the final fix, the original directory-symlink CLI attack was rerun with
two changed-source variants. **Both exit 2**, reporting
`Reproducibility source must not redirect through symlinks`; neither publishes
a result. See `E/post-fix-n2-final.log`. Valid canonical runs still complete.

## N3: reproduction, reachability and evaluation repair

### Independently reproduced numerical discrepancy

The original public evaluator accepted a deep copy with writable inconsistent
raw training targets and a copied persistence reference resized to a broadcastable
shape, without reconstructing their contracts.

The hand-calculated fixture uses raw training targets `[1,4,8,13]`, adjacent
differences `[3,4,5]`, scale 4, targets `[3,7,11,15]` and point predictions all 1.
MAE is 8 and **MASE is 2**. Replacing only copied raw support with
`[0,1000,2000,3000]` made the denominator 1000 and **MASE 0.008**, while training
windows remained contradictory. A valid persistence reference `[0,1,2,3]` has
MAE 7.5 and skill `1 - 8/7.5 = -0.06666666666666665`. A resized `(1,1,1)` zero
reference broadcast to all four cells, producing reference MAE 9 and skill
`1 - 8/9 = +0.11111111111111116`. Both reports retained 4/4 coverage.
Canonical construction rejected the same malformed declarations.

Evidence: `E/historical-n3-red.log`, the preserved audit's Appendix A and new
evaluation regressions. This was constructor-versus-consumption trust, not a
different valid choice of training scale or reference.

| Entry path | Established reachability |
|---|---|
| Public `evaluate_trajectory` API | Yes: direct copied/reconstructed invalid contracts reproduced the discrepancy. |
| Normal unmodified experiment runner | Not established. It constructs its training/windows/reference internally; no ordinary route to the demonstrated malformed state was found. |
| CLI/config-driven normal execution | Not established. JSON config does not carry arbitrary Python contracts; strict configuration and canonical construction remain. |
| Deserialization/reconstruction | Pickle/deepcopy/alternate-object reconstruction supplied to the public API is reachable and tested. There is no P1 artifact-to-pickle evaluation loader. |
| Fault-injected runner/model output | Tested explicitly to verify failure records and publication boundaries; this is a controlled API fixture, not evidence of ordinary CLI exploitation. |

The public API defect required repair even without ordinary runner reachability.

### Shared canonical consumption boundary

`evaluate_trajectory` now reconstructs exact-base `ForecastSpec`, `FutureGrid`,
`ForecastTargets`, `ForecastPrediction` and `TrainingSlice` snapshots. Alignment,
dataset/spec identity, shape, units, domain, masks, availability, raw support and
quantiles are validated before metric reductions. Calculations, coverage and
fingerprints use those captured objects, never the original caller objects.
Malformed inputs are rejected; they are not clipped, dropped or silently fixed.

Metrics include the actual canonical `training_fingerprint` and a new
`evaluation_input_fingerprint` covering targets/masks/grid, point/quantile
predictions, reference, training identity and reduction weights. Event evaluation
captures immutable numeric arrays and boolean masks, canonical origin/event
strings and horizon, and fingerprints exactly the scored semantics. Masked-out
event numeric values are explicitly inert in the identity.

Further boundary tests exposed a twice-converted boolean mask and integer
subtype comparison ordering. Contracts now capture a mask once and check integer
constraints after primitive normalization. Weight reduction normalizes on scored
support and uses log products for pooled positive weights, preventing tiny
positive weights from disappearing before a common mask is applied. These
changes have explicit numerical/ownership regressions.

Final installed-package reproduction retains MASE **2.0**, persistence skill
**-0.06666666666666665** and coverage **4/4** for valid inputs. Contradictory
training raises `Training window values contradict canonical raw training support`;
the malformed reference raises `Prediction must have shape (2, 2, 1)` before
returning metrics. See `E/post-fix-n3-final.json`.

### Related N5: prediction publication versus evaluation

Independent review found that an array subclass could serialize different values
from those used in arithmetic, supplied quantiles could be scored without being
published, and an internally valid prediction on the wrong grid could be
published under requested coordinates before evaluation rejected it.

The runner now captures one canonical prediction, validates requested grid and
model identity, then uses that output for both serialization and evaluation.
Supplied quantile levels/values are recorded. Invalid output becomes an explicit
predict-stage failure with attempted origins/coverage retained. A failed
persistence reference produces explicit null skills with
`persistence_not_supplied`, not a favorable substituted reference.

The independent evaluator review exercised five mismatch kinds across all six
models and a reference-only case: 31 controlled executions, 93 affected outputs,
93 predict-stage failures and 717 passing boundary/coverage assertions.

## All-metric and six-baseline verification

| Metric family | Canonical inputs and verified calculation |
|---|---|
| MAE / RMSE | Target mask, native points and weights; weighted absolute loss / square root after pooled squared loss. Origin-level lead scores use equal origin weights. |
| Persistence skill | Same aligned target mask; `1 - model_loss/reference_loss` for MAE and MSE. Missing reference or zero denominator gives null plus reason. |
| MASE | Unique raw training targets, valid adjacent pairs and contiguous raw intervals; no gap bridging or overlap-window multiplicity. Null for insufficient pairs/zero scale. |
| Correlation | Unweighted matched Pearson diagnostic; null for empty, insufficient or constant inputs. No uncertainty claim. |
| Pinball | Only explicitly supplied, validated quantiles; `max(q*residual,(q-1)*residual)`, using the same target coverage. |
| Event counts / rates | Explicit supplied outcomes/decisions on `valid & mature`; TP/FP/FN/TN, precision, recall/POD, FAR and FPR. No inferred labels or decision threshold. |
| F1 / TSS / HSS2 | Standard confusion-table formulas, with null/reason on undefined denominators. TSS equals POD minus FPR; HSS2 uses `2*(TP*TN-FP*FN)/((TP+FN)*(FN+TN)+(TP+FP)*(FP+TN))`. |
| Brier | Mean squared probability error on the same scored origins; probability-only input does not invent decisions. |

Common attempted origins survive model failures. Nonfinite model outputs are
failures, not exclusions. Target masks and event maturity determine coverage;
model success cannot silently choose an easier subset. Across-target raw loss is
undefined for different declared units. Returned objects are ordinary result
records; mutable caller edits to returned reports are not authenticated artifacts.

The independent numerical review used scalar Python/Decimal oracles, including
16 trajectory cases and 323 event cases (all 256 confusion tables with counts
0..3, 64 mask pairs and three optional-input cases). It recalculated all 54
model/partition records in three controlled publication runs. Its 79,313
assertions are assertions, not that many independent experiments.

No baseline mathematics or fitted algorithm was changed:

| Baseline | Preserved behavior |
|---|---|
| Persistence | Last permitted target observation, repeated across leads. |
| Training mean | Mean over unique valid raw training-period observations. |
| Trailing mean | Mean over the configured causal trailing support. |
| Drift | Extrapolation from permitted context endpoints. |
| Fixed AR(1) | Training-fitted fixed autoregressive coefficient/intercept; causal recursion. |
| Direct ridge | Training-window design/targets from validated raw-consistent support; configured fixed transforms, training-only centering and regularized direct lead fits. |

All six retain the existing shared fit and causal-prediction snapshot boundaries.
The evaluator adds its own consumption boundary. Existing hand-calculated
baseline tests, future-perturbation checks and F1/R1/N1 suites pass. Normal fresh
acceptance exercises all six across train/validation/test and three seeds.

## TDD evidence and verification results

Systematic debugging independently reproduced both reported failures before
production changes. TDD separated failing tests and fixes into commits. Review
findings led to further bounded red/green cycles. Verification-before-completion
required rerunning final tests and installed acceptance rather than relying on
review summaries. Parallel reviewers inspected executable source and ran their
own source, evaluation and whole-chain probes.

Some initial temporary logs disappeared with the temporary environment. The
starting checkpoint was therefore exported again and the accumulated 136 tests
at that stage rerun against it: **118 failed, 18 passed**, with expected semantic
assertion failures (`E/pinned-final-regressions-red.log`). This corroborates,
rather than replaces, the original test-before-fix sequence. The final ten
source-lifecycle cases were introduced later against interim implementations:
worker/deferred cases gave **6 failures / 2 controls passed**, and namespace
ownership gave **1 failure / 1 control passed**. It would be inaccurate to claim
all 146 final tests were run unchanged against the original checkpoint.

| Final suite | Observed result |
|---|---:|
| N2 executable source (`test_executable_source_provenance.py`) | 49 passed |
| N2/N4 loaded source (`test_loaded_source_provenance.py`) | 27 passed |
| N3 evaluation (`test_evaluation_boundary.py`) | 53 passed |
| N3/N5 publication (`test_prediction_publication.py`) | 17 passed |
| New cases total | **146 passed** |
| Existing F1 | **53 passed** |
| Existing R1 | **185 passed** |
| Existing N1 | **179 passed** |
| Complete P1 targeted suite | **805 passed, 1 warning, 37.70 s** |
| Complete repository suite | **971 passed, 1 warning, 72.17 s** |

The source suites independently passed 76/76; evaluation/publication and prior
regressions passed 487/487. The final targeted/full runs include all of them.
Final logs: `E/p1-targeted-isolated-final.log` and
`E/full-suite-isolated-final.log`.

An earlier full run recorded **7 failures / 964 passes**: one new test deliberately
loaded an unrecorded project module in the shared pytest process. Production
correctly retained unsafe execution history; later runner tests were consequently
refused. Commit `3028ad1` moved that adversarial load into a subprocess and checks
refusal both before and after cache eviction. It did not clear or weaken the
production history guard. The failing full log remains preserved, followed by
the fresh 805/971 passing runs. Earlier namespace checks also rejected bad inputs
but eight assertions expected the previous diagnostic prefix; preserving that
prefix resolved the assertion discrepancy without permitting those executions.

The existing warning was retained, not suppressed:

```text
RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject
```

## Fresh acceptance, artifacts and installation

All four runs used the rebuilt installed package from outside the checkout with
`PYTHONPATH` unset, at clean tracked commit `3028ad1`. They used existing local
dependencies and the already pinned GOES sample/Parquet/sidecar, without data
acquisition or sidecar rewriting.

| Output beneath `results/experiments/` | Execution ID | Scores / failures |
|---|---|---:|
| `p1-n2-n3-synthetic-a-20261007` | `de26acc73a884afba2dbdd1df6453e65` | 54 / 0 |
| `p1-n2-n3-synthetic-b-20261007` | `7f331fbe37e8443f9897cbc30b223e7e` | 54 / 0 |
| `p1-n2-n3-goes-a-20261007` | `5ca8599178d14f1eab10c265615ce4f9` | 54 / 0 |
| `p1-n2-n3-goes-b-20261007` | `bfd05efde96243d3aa82690a30d139ea` | 54 / 0 |

Every run has 54 scored/predicted combinations, 18 fitted parameter records,
seeds 17/29/43, train/validation/test partitions, nonempty scored coverage and
matching actual training fingerprints. Each records canonical evaluation input
identities and `BLOCKED_FOR_PHASE_E` / `foundation_smoke_not_scientific_skill`.

Within each pair, semantic IDs and all declared fingerprints match. The following
eight JSON files are byte-identical: `resolved_config`, `dataset_manifest`,
`split_manifest`, `provenance`, `model_parameters`, `predictions`, `metrics`,
`failures` (each with `.json`). `result.json` contains different execution IDs,
timestamps and destinations, so entire output directories/indexes are not
claimed byte-identical. All four nine-file artifact indexes and recorded source
identities verified. Appending a newline to a copied `predictions.json` was
rejected as `Artifact identity mismatch: predictions.json`; originals remained
untouched. Evidence: `E/acceptance-verification.json`.

Final executable-source fingerprint:
`5e15bd463d938f8e1f3115907bff9d438545899c6de40d181b9b19cf5009b0e0`.
The new source-capture helper increases module count from 22 to **23**. All 23
installed module files matched checkout SHA-256 hashes and imported from
`site-packages` outside checkout without `PYTHONPATH`. Actual executed digests
were checked, not only disk parity. The installed-package-backed
`scripts/run_experiment.py --help` and all four CLI runs passed. The wheel has no
new console entry point; the CLI is the repository script using the installed
package. No checkout import dependency was used in these acceptance runs.

Environment: CPython 3.13.3, macOS 26.3 arm64; NumPy 2.2.6, pandas 2.3.3,
xarray 2026.7.0, netCDF4 1.7.2, pyarrow 25.0.1; package 0.1.0. Wheel build used
existing setuptools 78.1.0 with no build isolation/dependency installation.
This establishes deterministic same-environment reruns, selected byte identity
and installed/source parity. **It does not establish fresh-dependency-environment
or cross-platform reproducibility.** A documentation-only Git commit changes
recorded Git provenance and provenance artifact bytes, but does not change the
semantic experiment IDs: those use config, dataset, split, source and training
fingerprints plus seed, not Git SHA. Acceptance is attributed to its actual
execution commit.

## Independent review and whole-chain findings

Three reviewers did not implement the changes they reviewed. They were asked
to seek new discrepancies, not simply rerun the known exploits.

| Reviewer area | Final executable evidence and disposition |
|---|---|
| Effective source / installation | 76 source tests, original alternate/worker/deferred/namespace refusals, ordinary clean checkout API/CLI and isolated local wheel controls. All 23 wheel files match; 18 executed, five inspected without importing optional readers. Changed unused installed source and same-byte source symlinks refuse. No surviving related HIGH in the bounded review. |
| Evaluation / metric semantics | 127 focused tests; 16 trajectory + 323 event oracle cases; 54 records independently recomputed; 31 output-alignment fault injections. N5 publication discrepancy discovered and verified closed. Reviewed evaluation/contracts/runner bytes still match final implementation. |
| End-to-end source/config/fit/predict/score/publication | 315 targeted tests; original retained-namespace counterexample rejected; two additional clean, real-provenance all-six CLI controls each score 18/18 without failures; IDs/prediction/metric bytes match and three artifact indexes verify. N4 namespace discrepancy discovered and verified closed. |

Reports: `E/source-review/NAMESPACE_OWNERSHIP_REVIEW.md`,
`E/evaluation-review/final-review.md`,
`E/chain-review/namespace-ownership-final.md`. Numerical publication fixtures
used explicitly labelled provenance stubs; they are not represented as ordinary
CLI acceptance. Source/whole-chain controls and the primary four acceptance runs
used real provenance.

| Trust boundary | Accepted, validated, captured and consumed state |
|---|---|
| Config → contracts | Strict finite JSON and supported schema categories; canonical spec/parameters before use. Config identity is recorded. |
| Raw data → partitions/windows | Existing pinned/synthetic inputs, chronological raw support and causal dependencies; canonical raw-consistent training identity. |
| Fit → prediction | All six use existing F1/R1/N1 canonical snapshots; prediction grids remain target-free. |
| Prediction → evaluation | Detached output/target/reference/training objects; full grid/spec/model checks; metric inputs and fingerprints agree. |
| Evaluation → publication | Same owned point/quantile values, attempted coverage and explicit failures serialized; malformed output cannot become a valid forecast row. |
| Executable source → provenance | Link policy, actual installed/source bytes, captured import history and active namespace ownership; final recheck before publication. |
| Publication → verification | Existing exclusive atomic destination creation and finite JSON index; concurrency/corruption/relocation regressions retained in the passing suite. |

The review closed N4/N5 examples of the requested general invariant. Finite
adversarial tests cannot establish absence of every possible Python-level attack.

## Scientific-state preservation and remaining limits

**109/109** starting identities were rehashed after fresh acceptance with zero
mismatches. The exact inventory is 70 data files, 32 pre-existing result files,
six non-P1 configuration files (including a pre-existing `.DS_Store`) and one
Paperclip skill file. It excludes new experiment outputs and the two P1 configs;
those configs are separately unchanged in Git and included in source identity.
This is a preservation inventory, not 109 independently validated scientific
claims. Baseline inventory JSON SHA-256:
`3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193`.
Evidence: `E/scientific-identities-final.json`.

Git diff confirms no changes to scientific data/manifests, data adapters,
configuration, schemas, package requirements or lockfile. D.1 requirements and
evidence manifests still say **BLOCKED_FOR_PHASE_E**. SoLEXS timing, bin/GTI/
exposure semantics, HK compatibility, PI/response mapping, calibration/alignment
and scientifically defensible real-event definitions remain unresolved. GOES
acceptance validates infrastructure only. No new data acquisition, SolarJEPA
training, ARCH/GARCH fitting or Phase E work occurred.

Remaining limitations, not suppressed findings:

- **LOW, open:** Git porcelain quotes some non-ASCII untracked config paths.
  Prefix-based tracked-input rejection can miss `configs/experiments/p1_é.json`.
  The file's bytes are nevertheless included in the source fingerprint, so the
  review did not reproduce a hidden computation/identity collision through it.
  This separate tracked-input-policy issue is documented, not silently repaired.
- **Dependency warning:** the existing NumPy/netCDF binary-size warning remains.
  Passing local execution is not an ABI portability guarantee.
- **Execution scope:** standard tested CPython file-backed imports are supported;
  custom module subclasses/lazy frameworks, patched hooks/loaders, arbitrary
  runtime mutation and generated non-file code are not generally attested.
  Conservative refusal can require a fresh interpreter after manual package
  reload/alternate loading or retained old namespaces. Ordinary captured-loader
  reload/reimport controls passed. No general security-sandbox claim is made.
- **TOCTOU:** before/after file checks and final provenance revalidation do not
  provide an atomic whole-filesystem snapshot or protection against all concurrent
  ABA mutations. Dependency versions are recorded, not dependency binary hashes.
- **Numerics and prior limits:** extreme floating-point overflow can still fail
  explicitly; historical F3-F9 qualifications, malformed numeric-subtype edges
  outside the corrected boundaries, caller-mutated fitted hyperparameters and
  broader portability gaps are not claimed newly resolved by this work.
- **Science/reproducibility:** no scientific skill, clean-environment or
  cross-platform claim; no real-event definition or SoLEXS-readiness inference.

No remaining related BLOCKER/HIGH was reproduced in the final bounded reviews.
These limitations must remain visible to the next independent integration audit.

## Reproduction commands

Run source tests from the matching checkout; no data acquisition is needed:

```bash
.venv/bin/python -m pytest -q tests/test_executable_source_provenance.py tests/test_loaded_source_provenance.py
.venv/bin/python -m pytest -q tests/test_evaluation_boundary.py tests/test_prediction_publication.py
.venv/bin/python -m pytest -q tests/test_training_slice_consistency.py tests/test_prediction_context_causality.py tests/test_canonical_semantics.py
.venv/bin/python -m pytest -q tests/test_baselines.py tests/test_canonical_semantics.py tests/test_evaluation_boundary.py tests/test_event_metrics.py tests/test_executable_source_provenance.py tests/test_experiment_provenance.py tests/test_experiment_reference.py tests/test_experiment_runner.py tests/test_forecasting_contract.py tests/test_forecasting_splits.py tests/test_forecasting_windows.py tests/test_loaded_source_provenance.py tests/test_prediction_context_causality.py tests/test_prediction_publication.py tests/test_training_slice_consistency.py tests/test_trajectory_metrics.py
.venv/bin/python -m pytest -q
```

Installation used `python3 -m pip wheel . --no-build-isolation --no-deps` with an
ignored wheel destination, then `.venv/bin/python -m pip install --no-deps
--force-reinstall <wheel>`. Outside checkout, with absolute paths substituted:

```bash
env -u PYTHONPATH <repo>/.venv/bin/python -B <repo>/scripts/run_experiment.py --help
env -u PYTHONPATH <repo>/.venv/bin/python -B <repo>/scripts/run_experiment.py --root <repo> --config <repo>/configs/experiments/p1_synthetic.json --output-dir results/experiments/<new-synthetic-id>
env -u PYTHONPATH <repo>/.venv/bin/python -B <repo>/scripts/run_experiment.py --root <repo> --config <repo>/configs/experiments/p1_goes_reference.json --output-dir results/experiments/<new-goes-id>
```

Repeat each config with a distinct new destination, then use `verify_artifacts`
and `verify_source_identities` from `experiments.provenance`. The local
`E/verify_acceptance.py` records the exact four-run assertions and corruption
check; rerunning that helper needs a new corruption-copy destination. Existing
output directories are deliberately not overwritten.

## Files and commit traceability

Exact changed paths from the starting feature checkpoint through this report:

- `docs/P1_FINAL_INTEGRATION_AUDIT.md` — preserve failed audit, unchanged content.
- `src/solar_flare_jepa/__init__.py`
- `src/solar_flare_jepa/_executed_source.py`
- `src/solar_flare_jepa/evaluation/events.py`
- `src/solar_flare_jepa/evaluation/trajectory.py`
- `src/solar_flare_jepa/experiments/provenance.py`
- `src/solar_flare_jepa/experiments/runner.py`
- `src/solar_flare_jepa/forecasting/contracts.py`
- `tests/test_evaluation_boundary.py`
- `tests/test_executable_source_provenance.py`
- `tests/test_loaded_source_provenance.py`
- `tests/test_prediction_publication.py`
- `docs/P1_N2_N3_REMEDIATION.md`
- `docs/PROJECT_STATUS.md`
- `README.md`

No Paperclip, bulk data, wheel, generated experiment output or other tooling is
staged. The untracked Paperclip SHA-256 remains
`4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`.
Only the feature branch is authorized for publication. Main/research refs remain
at the exact checkpoints above. No integration commands are executed or approved
by this remediation record.

The following commits preserve the failed checkpoint, expected failures,
implementation corrections and test isolation in order. The documentation commit
containing this report follows them without changing executable state.

| Commit | Purpose |
|---|---|
| `3d4fa36ed475f9eb13aac171ca0b4b6853747877` | docs(p1): preserve failed final integration audit |
| `c15941daf15bd6a473ff1afafd281c3deb3e7814` | test(provenance): reproduce executable source escape |
| `4df12a1bdb31c1b8d12c460ac3bb0e146bcf0171` | test(evaluation): reproduce evaluation trust boundary bypass |
| `cc09961b4019a774c1d3882c66cdeabca9cc9856` | test(provenance): reproduce stale loaded source identities |
| `510eff06469f9dab7709ae64730bd4e3d7594b34` | fix(evaluation): consume canonical detached evaluation inputs |
| `193a0f759233a68e67ff9b8b9d02a3a537b43fc0` | fix(provenance): reject redirected executable source |
| `a08650776e39a417060c9f50d8a82b03bbdaf6d6` | fix(provenance): bind project imports to captured source bytes |
| `ff696685f861544629d265da60435f7380a1fcc0` | test(provenance): cover alternate loader source capture bypasses |
| `df88fcace203620207725393f41ea4b638ed2cce` | test(provenance): cover retained and external module executions |
| `d1828683187fe7d7fa9cba3c1822e09d55f4c185` | test(evaluation): cover publication and canonical input discrepancies |
| `d9e1721b26d4a3a694d984baa4ffe2bc4038abab` | test(p1): cover first source execution and output alignment |
| `35bc8ac3592aef48c404c3243f4374997017184c` | test(provenance): cover source execution before bootstrap |
| `64159d6caaa1116d6420392efc01c6be1195dec5` | fix(evaluation): align canonical scoring and published forecasts |
| `6f1064d1f5edd17b331fcd5f16e7e277a3dafb7d` | fix(provenance): retain source execution history across loader paths |
| `db48958a535eca0b67f5b98634be971b68b179cf` | test(provenance): reproduce concurrent and deferred source execution |
| `915f57bf609359925bc294c6106df266ff6cf3c8` | fix(provenance): attest retained execution at the provenance boundary |
| `b5cb280a246a30a6fb3713b5dbdd37412e450061` | test(provenance): reproduce retained namespace identity mismatch |
| `cde534d67820bc34fbaf83a131667b72edab0016` | fix(provenance): require captured project namespace ownership |
| `3028ad10f3e6bcac0ce4df93650ae87465083460` | test(provenance): isolate persistent unsafe execution history |
