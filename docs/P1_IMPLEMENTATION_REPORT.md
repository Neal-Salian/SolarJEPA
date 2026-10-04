# P1 implementation checkpoint

**Later checkpoint, 2026-10-04:** this historical report describes the original
implementation. The [independent integration audit](P1_INTEGRATION_READINESS_AUDIT.md)
returned NOT_READY_FOR_INTEGRATION at `11b72bb` because public TrainingSlice
windows could contradict raw support. The [focused remediation](P1_TRAININGSLICE_REMEDIATION.md)
at final code commit `8ba57aa58242facf7614e805695fe9e71406ea3c` validates canonical
values, masks and dependency availability, revalidates every baseline's fitting
snapshot, and records computed training fingerprints. Verification is now
294 targeted / 460 full tests, with the existing dependency warning preserved.
The original results and conclusions below remain historical evidence; a fresh
integration-readiness audit is required. Phase E remains blocked.

Recorded: **2026-10-04, Asia/Kolkata**. **Technically ready for user review**
within the approved infrastructure scope. **Phase E: BLOCKED_FOR_PHASE_E.**
No integration, next phase, acquisition, SoLEXS interpretation or neural training
was performed. These checks establish software mechanics and provenance;
predictive skill, operational readiness, superiority and novelty are not established.

## Verified Git state and scope

| Item | Observed identity |
|---|---|
| Starting/current main and origin/main | `1a4991da4dda9676caeb1d7e35a03408528c3188` |
| Frozen research checkpoint, local and remote | `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe` |
| Implementation branch | `feat/p1-experiment-evaluation-foundation` |
| Upstream | `origin/feat/p1-experiment-evaluation-foundation` |
| Implementation base | `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe` |
| Verified implementation/code commit | `2162465510926c4bd0d41c6ee2d8b569a0907d7b` |
| Final documentation revision | Commit containing this report; final SHA is provided in the user checkpoint and `git log` |

Initial independent inspection confirmed the requested branch topology, clean
tracked tree and absent P1 implementation. Baseline execution had **166 passing
tests**. Source, tests, CLI/configuration, six pinned GOES files, processed frame,
scientific manifests, two SoLEXS archives and existing reports were inspected.
The three research documents remain unchanged. The implementation branch was
published with upstream tracking before implementation. All subsequent commits
and pushes went only to that branch. No shared history was rewritten.

| Commit | Coherent unit |
|---|---|
| `c218969` | Implementation decomposition and verified design rulings |
| `8154954` | Immutable forecasting contracts, constructor review fixes |
| `a41904a` | Raw-first temporal partitions/windows and leakage tests |
| `fcb928e` | Six deterministic point baselines and train-only fitting tests |
| `d84d401` | Separate trajectory and supplied-event evaluators |
| `8c0c0a0` | Strict configuration, fixtures, fingerprints and exclusive recording |
| `ddcdb6d` | Explicit ordered origin collections |
| `c83b537` | Complete training support and strict metadata, regression fixtures |
| `2162465` | Bounded runner, CLI, configs/schema and verified GOES adapter |

The final documentation commit updates this report, README and the current
tracker. Scientific manifests, raw/interim/processed data, older proposal
configs, dependency files and existing data source modules were not changed.

## Architecture and behavior actually implemented

`forecasting/contracts.py` defines immutable native-unit datasets, explicit
`ForecastSpec`, contexts, value-free `FutureGrid`, targets, finite point/quantile
predictions and train-only `TrainingSlice`. Coordinates, identities, channel
order/units, masks, transforms, availability and shapes are validated. Arrays
are copied into immutable storage. Operational contexts require actual known
availability; an earliest bin-end bound cannot be relabelled as delivery time.
Log transforms use declared dimensional references and return accurately
labelled inverse-transformed points. Quantiles require actual ordered levels
and finite noncrossing values.

`splitting.py` validates explicit chronological train/validation/(calibration)/test
half-open bounds. `windows.py` selects raw partition support before constructing
supervised windows. Context, additional causal feature lookback, target horizon,
label maturity, cadence coverage and supplied group closure must all remain
inside the partition. Missing cadence is excluded; there is no resampling or
imputation. Complete/masked policies are explicit. Actual retained/excluded
origins, reasons, support intervals and raw masks enter split identity.

Unique raw training observations are independent of overlapping windows/stride.
Public `TrainingSlice` construction also rejects lookback/maturity that crosses
bounds or bridges raw gaps, for windows and true raw cells. Baseline fit receives
only this slice; prediction receives contexts and a future grid without realized
targets. Direct ridge centers its features/targets on training only. Validation
and test contexts advance forecast state without refitting parameters.

| Baseline | Implemented fixed definition |
|---|---|
| Persistence | Latest valid observed counterpart repeated across leads |
| Training-period mean | Per-target mean over valid unique raw training observations |
| Trailing mean | Valid context-only observations in an explicit fixed trailing support |
| Drift | First-to-last valid support slope extrapolated by elapsed time |
| AR(1) | Fixed least-squares intercept/coefficient from adjacent valid raw training pairs; no gap bridging |
| Direct ridge | Fixed recent feature lags to all future leads/targets; training centering, unpenalized intercept, fixed alpha |

The training-period mean is not asserted to be established solar climatology.
Insufficient support, nonfinite output and declared-domain violations are
failures. Predictions are not clipped and origins are not dropped per model.
**ARCH/GARCH is not fitted**; it is recorded as
`deferred_pending_residual_diagnostics`, for later secondary conditional-variance
comparison with an appropriate same-mean constant-variance control.

`evaluation/trajectory.py` provides MAE/RMSE by lead/target, correctly pooled
losses, MAE- and MSE-based persistence-relative skill, MASE from valid adjacent
unique training pairs, diagnostic Pearson correlation and pinball loss for
supplied quantiles. Native units, weights, coverage/counts, common masks,
origin IDs and per-origin losses are retained. Mixed units prohibit raw pooling
across targets. Undefined/empty/zero-scale/constant/insufficient cases use
`value: null` and an explicit reason; invalid prediction shapes/values fail.

`evaluation/events.py` is independent supplied-label scoring: TP/FP/FN/TN,
precision, recall/POD, FAR, FPR, F1, TSS, HSS2 and probability Brier loss.
The scoring mask is valid AND mature. FAR and FPR remain distinct. Probability-only
input does not invent a decision threshold. Tests use artificial labels; the
runner constructs no real event definition.

`experiments/` provides finite resolved configuration, deterministic local fixture
RNG, dataset/config/split/source SHA-256 identities, Git/environment/package
provenance and indexed exclusive atomic JSON publication. Scientific identities
use portable relative identifiers/logical content. Code inspection compares
actual loaded modules and unused package files with checkout hashes without
executing unused optional scientific readers. Full clean-state/source enumeration,
commit and branch are checked again before publication. No environment-variable
or credential dump is collected.

`runner.py` admits only artificial fixtures or the existing pinned GOES reference.
It records common coordinates/targets/masks, fitted parameters, predictions,
metrics and structured fit/predict/evaluate failures. A persistence skill
reference is explicitly recorded if persistence is absent from the declared list.
Model seeds `[17,29,43]` tag identities; deterministic baselines consume no RNG
and do not need seed averaging. Fixture RNG is separately named. A fresh execution
ID/timestamps distinguish reruns from stable semantic experiment IDs.
Configuration/source/data contract violations reject publication; model failures
produce explicit failure records rather than biased score exclusions.

`reference.py` reuses existing verified-manifest paths, `read_goes` and containment
utilities. It checks pinned raw bytes/hashes, preparation/sidecar policies and
source association, processed Parquet hash, and exact reread equality. Legacy
absolute sidecar strings are associated by filename/hash/size without being
dereferenced or rewritten. Portable scientific identity omits those prefixes
and serialization-specific sidecar/Parquet hashes. It exposes native XRS-B masks,
bin start/end and earliest availability bounds, with actual latency **UNKNOWN**.

`scripts/run_experiment.py` is a thin installed-package CLI. Results live only
under a new ignored `results/experiments/<execution>` directory. Publication
refuses unsafe paths and replacement, including concurrent writers. Staged
finite JSON files are fsynced, indexed and verified before OS-level exclusive
directory rename. Failure cleanup removes only that execution's stage. A
reusable result schema is tracked outside ignored results.

## Meaningful design adjustments

- Separate read-only `experiments/reference.py` and its dedicated tests from the
  runner so scientific identity/policy checks can be independently reviewed.
  This is the only extra functional module beyond the proposed inventory.
- Establish an explicit target-value-free `FutureGrid`, plus strict public
  training-support guards. These make the proposed fit/predict and partition
  guarantees enforceable at API boundaries.
- Generic supplied-group support uses conservative overlap closure. Extra
  exclusions are recorded; no solar group semantics are derived.
- Raw target eligibility has its own maturity support and does not acquire
  feature-only derivative dependencies. Valid raw fitting data are not reduced
  to the window union.
- Preserve the historical GOES sidecar unchanged and normalize its source
  association. Bin end remains an earliest retrospective bound.
- Use exclusive atomic publication rather than replacement. Inspect unused
  code files without importing optional SoLEXS dependencies.

These rulings were checked against the approved design and actual repository;
they add no scientific assumptions, new fitting dependency or future model layer.

## Exact file inventory relative to the research checkpoint

Modified: `README.md`, `docs/PROJECT_STATUS.md`.

Added:

```text
docs/P1_IMPLEMENTATION_REPORT.md
docs/superpowers/plans/2026-10-03-p1-experiment-evaluation-foundation.md
configs/experiments/p1_synthetic.json
configs/experiments/p1_goes_reference.json
schemas/experiment_result.schema.json
scripts/run_experiment.py
src/solar_flare_jepa/forecasting/__init__.py
src/solar_flare_jepa/forecasting/contracts.py
src/solar_flare_jepa/forecasting/splitting.py
src/solar_flare_jepa/forecasting/windows.py
src/solar_flare_jepa/forecasting/baselines.py
src/solar_flare_jepa/evaluation/__init__.py
src/solar_flare_jepa/evaluation/trajectory.py
src/solar_flare_jepa/evaluation/events.py
src/solar_flare_jepa/experiments/__init__.py
src/solar_flare_jepa/experiments/config.py
src/solar_flare_jepa/experiments/fixtures.py
src/solar_flare_jepa/experiments/provenance.py
src/solar_flare_jepa/experiments/reference.py
src/solar_flare_jepa/experiments/runner.py
tests/test_forecasting_contract.py
tests/test_forecasting_splits.py
tests/test_forecasting_windows.py
tests/test_baselines.py
tests/test_trajectory_metrics.py
tests/test_event_metrics.py
tests/test_experiment_provenance.py
tests/test_experiment_reference.py
tests/test_experiment_runner.py
```

## Primary verification actually executed

| Check | Observed result |
|---|---|
| Starting full suite | 166 passed, 1 existing warning |
| All nine new test modules | **240 passed**, 1 warning, 8.62 s |
| Complete repository suite | **406 passed**, 1 warning, 38.06 s |
| Installed imports/CLI outside checkout, without PYTHONPATH | Passed; 22 execution-package modules match checkout, all located in installed distribution |
| Synthetic and existing-GOES CLI runs, each repeated | Four complete executions, zero model failures; 54 model/partition scores per execution |
| Rerun identities | Same three semantic experiment IDs per mode; distinct execution IDs |
| Rerun artifacts | Eight stable JSON artifacts byte-identical per mode; all four SHA-256 indexes verified |
| Portability/corruption | Relocation, data/mask/unit/policy/config/split/source/artifact corruption tests passed |
| Publication | Existing-directory refusal, real two-writer race, staged failure cleanup and unsafe paths passed |
| Data/scientific identity audit | All 109 pre-existing snapshot entries unchanged; six GOES files and both SoLEXS ZIPs reverified |
| Git/ignore scope | Diff/check/status/index/history inspected; data/results/scratch ignored; no prohibited data or .agents files committed |
| Fresh final reviews | Scientific/leakage and code/reproducibility **PASS** after independently rechecking fixes |

Targeted command:

```bash
.venv/bin/python -m pytest -q tests/test_forecasting_contract.py tests/test_forecasting_splits.py tests/test_forecasting_windows.py tests/test_baselines.py tests/test_trajectory_metrics.py tests/test_event_metrics.py tests/test_experiment_provenance.py tests/test_experiment_reference.py tests/test_experiment_runner.py
.venv/bin/python -m pytest -q
```

Tests cover future perturbation, exact split cuts, unavailable values, window/
feature/maturity/group support, gap bridging, train-only fitted means/AR/ridge
centering, literal baseline forecasts, hand-calculated continuous and binary
metrics, masks/missingness, zero/undefined denominators, mismatched shapes/IDs,
tiny-scale correlation, quantiles, finite serialization, corrupted fingerprints,
relocation, deterministic reruns, model-domain failure recording, unsafe/atomic
publication, changed source/metadata/branch during execution, installed CLI and
synthetic execution without optional Aditya imports. The whole-chain adversarial
test changes all post-training-cut features to `1e100` and targets to `-1e100`;
earlier numeric fits and predictions of all six baselines remain identical.
Dataset fingerprints correctly change when held-out content changes.

The installed package was rebuilt with `.venv/bin/python -m pip install --no-deps .`
after source changes. An initial `--no-build-isolation` attempt failed because
setuptools was absent from the runtime venv; the declared isolated build succeeded.
No project dependency/lock changes were made. Earlier worker broad tests executed
during missing evaluator/runner or stale installation phases had named transient
failures. They were investigated; final primary verification above supersedes
them, without weakening tests or hiding failures.

Acceptance CLI commands ran from `/private/tmp` with `PYTHONPATH` removed:

```bash
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --config configs/experiments/p1_synthetic.json --root /Users/nealsalian/Desktop/SolarJEPA --output-dir results/experiments/p1_acceptance_synthetic_a
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --config configs/experiments/p1_goes_reference.json --root /Users/nealsalian/Desktop/SolarJEPA --output-dir results/experiments/p1_acceptance_goes_a
```

Both were repeated with suffix `_b`. Absolute shell locations above describe
this execution environment; they are not portable scientific identity inputs.
Ignored acceptance artifacts remain available at those repository-relative result
directories. Dataset, failures, metrics, parameters, predictions, provenance,
resolved configuration and split manifests are byte-identical between each pair.
`result.json` and its containing index differ as intended for execution metadata.

| Mode | Retained train / validation / test origins | Valid native targets |
|---|---|---|
| Artificial two-channel fixture | 112 / 52 / 52 | 240 per target |
| Existing GOES XRS-B, 6 h context / 1 h horizon / 10 min stride | 103 / 62 / 103 | 4,318 of 4,320 rows |

The GOES smoke uses explicit daily July 1/2/3 2024 partitions, complete quality
support and a dimensioned log baseline track scored in native W/m2. Operational
delivery is unknown. All models share the recorded eligible origins. These are
small mechanics smokes, not task/horizon selection or a benchmark conclusion.

Verified source fingerprint (35 source/config/schema/build files):
`5a701dd279d15dd7f73f2b629785d932af704ed81235a5c9ad2df1d10c0e288c`.

| Identity | Synthetic | GOES reference |
|---|---|---|
| Config | `fb94b363e63991a41bafea280efe0a1de198426baae6442d0fbd69d0b6499f9c` | `9bab0a7cec48880cc503d2b4603f786b09dbf3b9c914a541101465d9197723ae` |
| Dataset | `78858423dd4f8770bb2aa8dc5bac1f709fc6335ce3e4f551403f7e5c8281fd68` | `6968f0a40290951acba2d73af362f1ced6cfee6304b68aba82416246cd6562b6` |
| Split | `7f3359ec2af5ab738ae69dc89ffee80793134d74e4811a24b350defa5b7a5b23` | `31c5655b6667274bd41aad03d160995d9aa5af8702b89eba9f4991230aa9f133` |

Runtime recorded Python 3.13.3/macOS 26.3 arm64, NumPy 2.2.6, pandas 2.3.3,
xarray 2026.7.0, netCDF4 1.7.2 and pyarrow 25.0.1. The existing warning remains:
`numpy.ndarray size changed ... Expected 16 from C header, got 96 from PyObject`.
Its first occurrence is now the new artificial GOES adapter test; the starting
suite emitted the same warning at the existing GOES dependency boundary.
It was not suppressed. Independent clean-environment reproduction and native
Linux/Windows publication are unverified; numerical-library bitwise portability
is not promised. Native exclusive rename was exercised on this macOS host.
File fsync/atomic visibility is implemented; full power-loss durability is not claimed.

## Review findings, skills and bounded delegation

Superpowers skills deliberately used: using-superpowers, brainstorming to
revalidate the already approved design, writing-plans, using-git-worktrees
inspection, subagent-driven-development, dispatching-parallel-agents, TDD,
systematic-debugging, receiving/requesting-code-review,
verification-before-completion and finishing-a-development-branch. The user’s
explicit branch/base, independent parallel work and final stop instructions
overrode generic serial-worker/worktree/integration menus. Disjoint writers and
primary-only Git operations were used. The primary established contracts first,
inspected actual worker diffs/source/tests, integrated them and independently
ran the targeted/full/runtime/identity checks.

| Subagent | Bounded contribution |
|---|---|
| p1_design_review | Challenged proposed boundaries, raw fitting support, availability, identity/publication and package parity |
| p1_contract_review | Constructor/metadata/overflow/transform/quantile contract review and re-review |
| p1_windows | Split/window implementation and adversarial support tests |
| p1_leakage_review | Independent cuts, lookback/maturity/group/availability and perturbation review |
| p1_baselines | Six baseline implementations and known-output/train-only tests |
| p1_baseline_review | Independent mathematical/API baseline verification |
| p1_metrics | Trajectory/event implementations and hand-calculated/undefined tests |
| p1_metric_review | Independent weights, tiny-scale correlation and confusion-table verification |
| p1_provenance_review | Artifact/config/portable-path/publication review and two fix re-reviews |
| p1_reference_adapter | Read-only verified GOES adapter and 26 corruption/relocation tests |
| p1_final_scientific_review | Fresh full-support API/leakage/scientific review, repeated adversarial probes and 90 builder combinations |
| p1_final_repro_review | Fresh provenance/config/CLI/reference/publication review and mutation probes |

Important findings were reproduced in failing tests before correction:

- Initial contract review: NaN bounds bypass, mutable/non-JSON scalar metadata,
  identity-transform width, int64 wrap and quantile-domain consistency.
- Provenance review: nested unindexed `artifacts.json` escaped file-set checking,
  string/map channel coercion, portable Windows drive/stream handling and
  overflowing weight sum.
- Primary integration: unused SoLEXS import made synthetic execution depend on
  optional astropy; ambiguous/unordered origin collections were accepted.
- Fresh scientific review: external training slices bypassed lookback/maturity
  bounds and raw dependency coverage. Fix re-review found a residual window
  coverage gap; an additional two failing tests and guard closed it. Four earlier
  unit fixtures had fictional raw support; coordinates were corrected and all
  original behavioral assertions retained. Final independent review rejected all
  five adversarial probes and preserved 330 valid origins over 90 builder cases.
- Fresh reproducibility review: source additions/tracked metadata edits/branch
  changes during execution escaped final provenance checking; three regressions
  now reject publication. Empty metadata containers and unhashable seed/model
  names also now fail with clear ValueError.

Final reviews passed with no material unresolved finding in their scope.
Service usage limits interrupted a scientific re-review; it was resumed after
availability returned, and its final PASS followed actual independent probes.
Ignored local SDD notes preserve initial findings and later re-review evidence;
this report preserves the scientifically relevant conclusions in Git.

## Immutable scientific state and deliberately deferred work

The initial 109-file SHA-256 snapshot covered existing data/config/results and
the Paperclip pointer. Recomparison found **zero changed or missing entries**.
Existing GOES avg1m and flsum manifest verification passed for three files each.
Parquet identity remains
`cc197f8186e0ec15b8ababd5a8c5549349d10fd15112cf4320ca4f23c114c068`;
its sidecar and pinned manifest/config are unchanged. Both registered SoLEXS
archives passed native inventory verification:

- July 1: 6,036,792 bytes,
  `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4`.
- July 3: 6,216,112 bytes,
  `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf`.

The D.1 gate manifest still says `BLOCKED_FOR_PHASE_E`; the historical Phase E
requirements file still says `BLOCKED`. C/D/D.1 reports, native diagnostics,
official tools/CALDB provenance and raw/interim products are unchanged. Full
scientific FITS/calibration diagnostics were not rerun for this infrastructure
milestone; preserving identities does not resolve their existing unknowns.

`.agents/skills/paperclip/SKILL.md` remains unchanged, untracked and uncommitted
(SHA-256 `4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`).
No evidence of repository Git intent emerged, and the user explicitly requested
local preservation. Paperclip was not invoked for implementation; the approved
literature artifact remains the research evidence, separate from code evidence.

Authoritative SoLEXS TIME/MJD/date precedence, UTC/clock correction, LC/PI bin
semantics, GTI/exposure interpretation, HK/correction compatibility, PI/response
mapping and calibration/alignment remain **UNKNOWN/PENDING**. No chronological
reinterpretation, correction, real event definition, cross-instrument alignment,
historical acquisition, final real-data dataset or SolarJEPA training was performed.
Future SoLEXS compatibility requires an approved validated adapter/contract;
it cannot enter through the current runner's dataset modes.

Deferred: ARCH/GARCH diagnostics/fits, learned/JEPA models, probabilistic baseline
fits/calibration, event construction/alarm matching, confidence intervals and
paired block uncertainty, scientific benchmark selection, independent environment
reproduction, GPU/operational validation and novelty assessment (**UNKNOWN**).
Float64 representability limits still apply, including tiny squared-loss
underflow; metric undefined cases are explicit rather than substituted scores.

Post-documentation Git verification is reported in the user checkpoint. The
verified code checkpoint had a clean tracked tree on the synchronized
implementation branch, with sole untracked
`.agents/skills/paperclip/SKILL.md` (short status `?? .agents/`). Raw science,
results and SDD scratch paths match actual ignore rules. Main/research refs and
historical checkpoint documents are preserved. **Stop here for user review;
explicit approval is required before integration into main.**
