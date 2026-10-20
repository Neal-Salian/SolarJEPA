# SolarJEPA P1 final integration-readiness audit

Date: 2026-10-04 (Asia/Kolkata). **AUDIT ONLY.**

**Readiness: NOT_READY_FOR_INTEGRATION.**

**Blocking finding F1 (HIGH):** the public TrainingSlice constructor accepts
training windows whose true masks or values contradict its own raw training
arrays. Direct ridge fits those windows under the unchanged dataset/spec/split
identities. This violates the reusable training-support contract. Correcting
this finding and auditing the resulting new candidate requires a separate
authorized change; no finding was fixed here.

The builder-generated synthetic/GOES path passed the executed leakage controls.
The targeted suite passed **240 tests** and the complete suite passed **406 tests**,
each with **one existing dependency warning**. Four installed-package experiment
reruns completed, their stable artifacts reproduced byte for byte, and all
109 preserved snapshot identities matched. Integration is technically a clean
fast-forward, but these positive results do not close F1.

No merge, push, rebase, squash, history rewrite, branch deletion, scientific-input
modification, acquisition, Phase E work, SolarJEPA training, or ARCH/GARCH fit was
performed. The audit report is left **untracked and uncommitted** on the existing
candidate branch; audited HEAD remains unchanged.

## 1. Exact audited identities and Git topology

| Item | Freshly observed identity |
|---|---|
| Candidate HEAD, local branch and origin upstream | 11b72bb0c714cf71edf1e5ccb390d38444bbb8c8 |
| Candidate branch | feat/p1-experiment-evaluation-foundation |
| Upstream | origin/feat/p1-experiment-evaluation-foundation |
| Protected local main and origin/main | 1a4991da4dda9676caeb1d7e35a03408528c3188 |
| Frozen research branch and origin research branch | 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe |
| Research branch | research/experiment-evaluation-foundation |
| Candidate tree | 1542fa1e4cb6502acf5f10e6fa1d91c09f9cd4f0 |
| Implementation/code checkpoint before final documentation | 2162465510926c4bd0d41c6ee2d8b569a0907d7b |

A fresh `git fetch origin` completed successfully. Main, candidate, and research
local/upstream comparisons each returned **0 ahead / 0 behind**. The merge base
of main and candidate is exactly protected main. Both main and the frozen research
checkpoint are ancestors of candidate. Candidate is 11 linear commits ahead of
main: the research commit plus ten implementation/documentation commits.

```text
1a4991d main = origin/main
  -> 805f1c3 research checkpoint = preserved local/origin research branch
  -> c218969 implementation plan
  -> 8154954 immutable contracts
  -> a41904a chronological splits/windows
  -> fcb928e six point baselines
  -> d84d401 trajectory/event evaluation
  -> 8c0c0a0 config/provenance/publication
  -> ddcdb6d ordered origin guards
  -> c83b537 additional public support/metadata guards
  -> 2162465 runner/GOES/CLI
  -> 11b72bb final implementation documentation = local/origin candidate
```

No unexpected commit or ancestry change was observed. A single worktree exists,
on the candidate branch. Initial tracked working tree and index were clean.
The initial sole untracked file was .agents/skills/paperclip/SKILL.md. Main was
never checked out or moved during this audit. Remote milestone branches remain
preserved. Fetch and an object-only merge simulation changed no branch refs.

## 2. Audit method and actual Superpowers use

The frozen proposed design supplied the requirements. README, tracker, research
notes, implementation report, and previous worker reports were supporting or
historical context. Actual source, tests, configs, schema, CLI, packaging,
Git history/diffs, manifests, loaded module paths, scientific file hashes, and
newly generated output artifacts supplied implementation evidence.

| Workflow/skill actually read and used | Effect on this audit |
|---|---|
| Superpowers using-superpowers and Codex reference | Established skill/tool use before exploration; kept the explicit audit-only scope above generic implementation workflows. |
| requesting-code-review and its reviewer template | Dispatched focused, independent, read-only reviewers with exact base/HEAD, requirements, severity expectations, and source/test scope. Review findings were reproduced rather than accepted from a summary. |
| dispatching-parallel-agents | Divided independent domains without shared writers. No subagent could modify repository files or Git refs. |
| systematic-debugging | Traced accepted contradictions from constructor checks into ridge row selection; traced Git quoting, filesystem enumeration, and float64 square underflow. Used working controls and small reproductions. Stopped before any fix, as required by the audit instruction. |
| verification-before-completion | Executed fresh targeted/full suites, installed and wheel checks, reruns, identity comparisons, simulation, and final Git/diff checks before concluding. Recorded failed adversarial expectations and unverified limits. |

Independent roles:

| Reviewer | Actual evidence reviewed |
|---|---|
| contracts_leakage_audit | Full forecasting contracts/splits/windows/baseline boundaries, four corresponding test files, actual changes, 96 builder configurations, future perturbations, malformed public objects. |
| mathematics_audit | Baselines and both evaluators, tests, independent rational/hand calculations, numeric-range probes, installed/source byte comparisons. |
| reproducibility_audit | Config/fixtures/provenance/runner/schema/CLI/tests, temporary Git/source copies, corruption, relocation, failures, multi-process publication. |
| scientific_scope_audit | GOES adapter and existing data readers, actual source/config/manifest diffs, preserved SoLEXS gates and scientific assumptions. |
| Primary auditor | Git/integration safety, complete inventory, packaging, full suites, real pinned inputs, paired installed smokes, snapshot preservation, and independent reproductions of the material findings. |

Scientific/reproducibility review was performed through these code/manifests/hash
checks; no separate available skill was misrepresented as a scientific certification.
**DOCUMENTED** denotes an authoritative definition or an explicitly attributed
documented requirement; **OBSERVED** denotes file/execution evidence;
**INFERRED** denotes an implication of that evidence; **UNKNOWN** remains
unestablished. No new scientific semantics were inferred.

## 3. Complete diff and file inventory

`git diff --name-status main...feat/p1-experiment-evaluation-foundation`
has **32 added files and 2 modified files**, 34 paths total. No deletion,
rename, binary scientific product, dependency change, or packaging-metadata
change appears in that diff.

The **29 added / 2 modified** claim is correct **relative to the research
checkpoint**, as the implementation report explicitly labels its inventory.
Main integration additionally includes the three frozen research documents.
This is a reference-base clarification, not three unexpected implementation files.

Modified:

- README.md
- docs/PROJECT_STATUS.md

Added:

```text
configs/experiments/p1_goes_reference.json
configs/experiments/p1_synthetic.json
docs/P1_IMPLEMENTATION_REPORT.md
docs/P1_LITERATURE_RECONNAISSANCE.md
docs/P1_PROPOSED_DESIGN.md
docs/P1_REPOSITORY_AUDIT.md
docs/superpowers/plans/2026-10-03-p1-experiment-evaluation-foundation.md
schemas/experiment_result.schema.json
scripts/run_experiment.py
src/solar_flare_jepa/evaluation/__init__.py
src/solar_flare_jepa/evaluation/events.py
src/solar_flare_jepa/evaluation/trajectory.py
src/solar_flare_jepa/experiments/__init__.py
src/solar_flare_jepa/experiments/config.py
src/solar_flare_jepa/experiments/fixtures.py
src/solar_flare_jepa/experiments/provenance.py
src/solar_flare_jepa/experiments/reference.py
src/solar_flare_jepa/experiments/runner.py
src/solar_flare_jepa/forecasting/__init__.py
src/solar_flare_jepa/forecasting/baselines.py
src/solar_flare_jepa/forecasting/contracts.py
src/solar_flare_jepa/forecasting/splitting.py
src/solar_flare_jepa/forecasting/windows.py
tests/test_baselines.py
tests/test_event_metrics.py
tests/test_experiment_provenance.py
tests/test_experiment_reference.py
tests/test_experiment_runner.py
tests/test_forecasting_contract.py
tests/test_forecasting_splits.py
tests/test_forecasting_windows.py
tests/test_trajectory_metrics.py
```

All inherited source/data-reader code, manifests, scientific configs, proposal
configs, historical reports, AGENTS.md, .gitignore, pyproject.toml, and
requirements-lock.txt have unchanged Git blobs. Per-commit changed-path history
was inspected, not only the final tree. Index/history inspection found no raw
data, model weights, generated experiment artifacts, or .agents files committed.
Raw/interim/processed/results tracked paths contain only their .gitkeep files.

Actual `git check-ignore -v` checks matched the raw NOAA files, both scientific
archive paths, processed Parquet, new experiment result paths, local venv/build
outputs, and SDD scratch. No forced staging was used.

### Untracked Paperclip pointer

.agents/skills/paperclip/SKILL.md contains Markdown instructions for the local
Paperclip skill. Its SHA-256 is unchanged:
4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424.

**OBSERVED:** setuptools discovers packages only under src; pytest's source
injection is src; no package code, test, config, or CLI imports this Markdown.
The wheel contains no .agents content. Its presence does not alter package
behavior, installation, model arithmetic, scientific inputs, or semantic
config/dataset/split/source identities.

**OBSERVED reproducibility effect:** code_provenance records the path in its
untracked_configuration_paths field and permits it because it is outside the
source/config/schema/script prefixes. Presence/absence therefore can change
provenance.json bytes and its artifact hash on another checkout. It does not
change the semantic experiment IDs. It can guide a local agent if the skill is
invoked; that is a workflow effect, not package execution.

**INFERRED integration effect:** being untracked and absent from the candidate
tree, it is not introduced into main by integration. It must remain uncommitted.
Paperclip was not invoked for this audit.

## 4. Requirement -> implementation -> executed test traceability

Source references below are relative to src/solar_flare_jepa; tests are relative
to tests. All nine new test modules were freshly executed together by the primary.
PASS means the stated bounded evidence passed; it does not erase listed gaps.

| P1 requirement | Actual implementation | Executed test evidence | Result |
|---|---|---|---|
| Immutable native arrays/coordinates and detached metadata | forecasting/contracts.py:33, :255; windows.py:40 | test_forecasting_contract.py:43, :178; test_forecasting_windows.py:246 | Original objects PASS; copy/pickle gap F2 |
| Declared names/units, shapes, cadence, references and domain | contracts.py:51, :136, :185, :411 | test_forecasting_contract.py:63, :68, :139, :196, :215 | PASS ordinary ranges; F9 range limit |
| Explicit boolean masks and finite true cells | contracts.py:51; windows.py:163, :221 | test_forecasting_contract.py:68; test_forecasting_windows.py:110 | PASS per-array; cross-array gap F1 |
| Actual availability versus earliest bin-end bound | contracts.py:270, :343; windows.py:114, :137 | test_forecasting_contract.py:81, :91, :222; test_forecasting_windows.py:124, :138, :146, :223 | PASS; operational unknowns rejected |
| Context ends by issue; future starts at issue; no realized-target grid | contracts.py:335, :355; baselines.py:96 | test_forecasting_contract.py:102, :205; test_baselines.py:221 | PASS |
| Ordered unique origins and identity/unit/time alignment | contracts.py:305, :377 | test_forecasting_contract.py:111, :228; test_event_metrics.py:27; test_baselines.py:170 | PASS |
| Train role, raw bounds, full lookback/maturity/tick coverage | contracts.py:460 | test_forecasting_contract.py:151, :169, :236, :251, :262, :277 | Bounds/gaps PASS; internally contradictory true cells F1 |
| Finite/JSON/scalar metadata validation | contracts.py:91, :285; experiments/config.py:64 | test_forecasting_contract.py:178; test_experiment_provenance.py:34, :164, :172 | Usual cases PASS; F6/F8 |
| Raw-first ordered chronological partitions | forecasting/splitting.py:49, :62; runner.py:86 | test_forecasting_splits.py:20, :39, :47, :62 | PASS |
| Causal windows with contained context/lookback/horizon/maturity | windows.py:128, :174 | test_forecasting_windows.py:40, :78, :88, :174 | PASS on builder path |
| Record retained/excluded origins, complete support and reasons | windows.py:183, :247 | test_forecasting_windows.py:40, :205, :246; test_experiment_provenance.py:68 | PASS builder manifests |
| Missing cadence and dependency validity/availability | windows.py:133, :137, :154 | test_forecasting_windows.py:88, :97, :124, :223 | PASS builder path |
| Supplied group straddling, maturity and conservative closure | splitting.py:30; windows.py:60 | test_forecasting_windows.py:151, :163, :259 | PASS; no real labels derived |
| No future/split contamination; unique raw train support | windows.py:128, :163; baselines.py:56 | test_forecasting_windows.py:55, :70, :78, :234; test_experiment_runner.py:68 | PASS generated inputs; F1 public boundary |
| Persistence | baselines.py:124 | test_baselines.py:75, :170, :238, :312 | Latest valid counterpart; PASS |
| Unique training-period mean | baselines.py:138 | test_baselines.py:87, :98, :291; test_forecasting_windows.py:70 | PASS |
| Trailing mean | baselines.py:158 | test_baselines.py:75, :188, :238, :258 | PASS fixed caller state; F7 |
| Drift | baselines.py:180 | test_baselines.py:75, :199, :213, :238 | PASS elapsed-time/manual checks |
| Fixed AR(1) | baselines.py:201 | test_baselines.py:75, :104, :133, :213, :291 | PASS adjacent-pair/intercept/recursive checks |
| Direct ridge | baselines.py:246 | test_baselines.py:116, :124, :133, :274, :300 | Mathematics PASS; inconsistent input acceptance F1 |
| MAE, RMSE, lead/target and weighted pooling | evaluation/trajectory.py:34, :89, :169 | test_trajectory_metrics.py:60, :84, :210, :231 | Ordinary range PASS; F5 |
| Matched persistence-relative MAE/MSE skill | trajectory.py:62, :101 | test_trajectory_metrics.py:60, :135, :199 | PASS ordinary range; F5 underflow diagnosis |
| Train-only MASE scale, adjacent valid unique samples | trajectory.py:72 | test_trajectory_metrics.py:108, :126 | PASS |
| Pearson correlation and empty/constant/insufficient reasons | trajectory.py:43 | test_trajectory_metrics.py:135, :149, :155 | PASS, including tiny nonconstant values |
| Pinball for actual ordered noncrossing quantiles | trajectory.py:160; contracts.py:425 | test_trajectory_metrics.py:161; test_forecasting_contract.py:122, :215 | PASS |
| Common target mask, counts, losses, units and model failures | trajectory.py:144, :195 | test_trajectory_metrics.py:95, :178, :210, :226 | PASS |
| Confusion counts, precision, recall/POD, FAR, FPR, F1, TSS, HSS2 | evaluation/events.py:65 | test_event_metrics.py:32, :82 | PASS; independent 625-table oracle |
| Brier; supplied labels/definition; valid AND mature mask | events.py:24, :55, :80 | test_event_metrics.py:32, :54, :62, :110, :121 | PASS; no invented threshold |
| Undefined event denominators/empty masks | events.py:71 | test_event_metrics.py:82, :92 | PASS explicit null/reason |
| Strict resolved finite config, supported modes and parameters | experiments/config.py:12, :64 | test_experiment_provenance.py:34, :148, :155, :164, :172, :182; test_experiment_runner.py:138 | Usual cases PASS; F8 |
| Deterministic local fixture RNG and separately named fixture seed | experiments/fixtures.py:17; runner.py:194 | test_experiment_provenance.py:49 | PASS; no global RNG changes in independent probe |
| Config/dataset/split/source fingerprints | contracts.py:294; config.py:155; provenance.py:49; runner.py:92 | test_experiment_provenance.py:49, :68, :77 | PASS; actual artifact content checked |
| Actual Git/package/loaded-source provenance and final recheck | provenance.py:65; runner.py:177 | test_experiment_runner.py:123, :149 | Intended cases PASS; quoted-path gap F4 |
| Structured fit/predict/evaluate failures on common origins | runner.py:57, :118, :142, :171 | test_experiment_runner.py:97; independent empty-training experiment | PASS; 18 explicit failures retained in independent probe |
| Exclusive staged/atomic recording, safe paths, cleanup, races | provenance.py:117, :134, :179 | test_experiment_provenance.py:93, :118, :131, :202 | PASS on macOS, including independent four-process race |
| Corruption detection and complete artifact file set | provenance.py:157 | test_experiment_provenance.py:102, :189 | Indexed regular files PASS; symlink/type gaps F3/F8 |
| Portable source/artifact/reference identities and relocation | provenance.py:30; reference.py:47, :81 | test_experiment_provenance.py:77; test_experiment_reference.py:84 | Local relocation PASS; limits in section 8 |
| Reusable tracked result schema | schemas/experiment_result.schema.json | Actual schema/result inspection and artifact-name pattern checks | Inspected; formal Draft 2020-12 validator not run |
| Thin CLI, normal imports outside checkout | scripts/run_experiment.py; pyproject.toml package discovery | test_cli.py:20, :31; test_experiment_runner.py:169, :182 | PASS; fresh wheel/copied wrapper also exercised |
| Pinned read-only GOES preparation identity/policy/reread checks | experiments/reference.py:19 | all 26 test_experiment_reference.py cases; actual paired GOES runs | PASS |
| No scientific-gate weakening or prohibited model/input mode | config.py:75, :124; runner.py:21, :201; unchanged scientific manifests | test_experiment_runner.py:138; actual Git/blob/hash comparisons | PASS; Phase E blocked |

The independent contract reviewer additionally enumerated **96 configurations /
288 partitions**, retaining 989 origins and excluding 931. Every retained
context/lookback/target/maturity support used existing ticks, fit its partition,
and shared no support with another partition. Enumeration covered lengths,
horizons, stride, lookback, maturity, and complete versus gapped grids; it was
not an exhaustive enumeration of every availability/group combination.

## 5. Findings, severity and reproductions

Severity policy: BLOCKER means a critical integration/data-state failure; HIGH
means a substantive required contract violation that must be corrected before
integration; MEDIUM means a bounded correctness/robustness gap requiring an owner
decision; LOW means a limited edge/API issue; INFORMATIONAL records evidence or
scope limits. **F1 is the concrete integration blocker.** No separate BLOCKER-level
finding was observed. All findings below remain unfixed.

| ID | Severity | Finding | Integration consequence |
|---|---|---|---|
| F1 | HIGH | TrainingSlice does not reconcile window true masks/values with raw training support | Must correct and independently re-audit |
| F2 | MEDIUM | Deepcopy/pickle restores writable arrays in an immutable contract type | Decide supported copy/serialization contract and address or explicitly limit it |
| F3 | MEDIUM | Artifact verifier accepts unindexed symlinks and an external index symlink | Complete contained-tree guarantee is not established |
| F4 | MEDIUM | Git-quoted untracked source paths bypass the clean-source prefix gate | Clean tracked-source guarantee is incomplete |
| F5 | MEDIUM | Tiny nonzero errors can silently become RMSE zero | Numerical correctness limit; default smokes unaffected in observed runs |
| F6 | LOW | Duplicate dataset-metadata JSON keys silently collapse | Ambiguous caller metadata; generated adapter metadata has no duplicates |
| F7 | LOW | Explicit post-fit lookback assignment changes prediction with a stale parameter record | Caller mutation caveat; runner does not mutate it |
| F8 | LOW | Numeric/finite-JSON/artifact-index type edge validation is incomplete | Controlled refusal/helper guarantees need tightening; no malformed experiment published |
| F9 | LOW | Avoidable log/inverse intermediate underflow rejects some finite values | Explicit safe failure, outside observed smoke scale |

### F1: internally contradictory training support

Locations: [contracts.py](../src/solar_flare_jepa/forecasting/contracts.py), lines
460-504, particularly 485-504; [baselines.py](../src/solar_flare_jepa/forecasting/baselines.py),
lines 268-274.

**OBSERVED:** constructor checks coordinate containment and existence of dependency
ticks, then validates raw arrays independently. It never joins window cells to
raw rows by timestamp, checks that window true implies raw true, compares true
values, or reconciles repeated coordinates. Ridge selects rows using window
masks and fits window values, whereas training mean/AR/MASE use raw arrays.

Three independently rerun adversarial cases were accepted:

1. Feature tick 3 invalid; one-bin causal lookback makes raw feature ticks 3/4
   false/NaN. The builder excludes issue 5. A supplied issue-5 context with true
   masks and values 4/5 is accepted with those unchanged raw arrays.
2. Raw target tick 5 false/NaN; supplied future training target tick 5 true/value 6
   is accepted. The builder had excluded that origin.
3. A repeated context coordinate has value 2 in raw data and one window but
   1234 in another window. Construction accepts all three as true cells under the
   same split fingerprint.

The standalone expectation probe exits **1** with three
UNEXPECTEDLY_ACCEPTED cases. A separate primary probe then changed only
window features by +1000 and fit ridge: the raw arrays and split identity stayed
equal, while the fitted intercept changed from approximately **0.5** to
**-1666.1666666666663**.

This is an internally checkable contradiction, not a request to authenticate an
arbitrary caller's scientific hash. An adapter/assembly error can cause ridge and
raw-data baselines to use inconsistent training information while claiming one
dataset/spec/split identity. No such inconsistency was observed in the current
builder-generated runner path.

Self-contained bounded reproduction from the candidate, using the matching
installed package:

```python
from dataclasses import replace
import numpy as np
from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.forecasting.baselines import DirectRidge

ns = 1_000_000_000
starts = np.arange(3, dtype=np.int64) * ns
v = np.array([1., 2., 4.])[:, None]
mask = np.ones_like(v, dtype=bool)
spec = ForecastSpec(1, 1, 1, ('x',), ('x',), ('u',), ('u',))
data = TimeSeriesDataset(
    'audit_fixture', 'synthetic_fixture', starts, starts + ns,
    v, mask, v, mask, ('x',), ('x',), ('u',), ('u',), 1,
    availability_ns=starts[:, None] + ns)
train = build_partition_windows(
    data, spec, TemporalPartition('train', 0, 3 * ns)).training_slice
# Expected rejection: true window values no longer match raw values.
bad = replace(train, context=replace(
    train.context, values=train.context.values + 1000.))
assert np.array_equal(bad.raw_features, train.raw_features)
assert bad.split_fingerprint == train.split_fingerprint
print(DirectRidge(1, .1).fit(train).parameters['intercept'])
print(DirectRidge(1, .1).fit(bad).parameters['intercept'])
# Observed: [~0.5], [~-1666.1666666666663]; no ValueError.
```

Required corrective outcome: true window cells must correspond to true raw cells
with matching values, including overlapping coordinates. Window false masks may
legitimately be stricter than raw masks because of earlier availability deadlines.
Any stricter support/provenance authentication needs explicit trusted evidence,
not merely a caller-supplied fingerprint string. Existing public-slice tests at
test_forecasting_contract.py:236-295 cover bounds/gaps, not these contradictions.
Some isolated baseline mathematics fixtures also construct windows independently
of raw values; they do not establish temporal-contract consistency.

### F2: copy/deserialization immutability

Location: contracts.py:33-38 and constructor call sites.

**OBSERVED by reviewer and primary:** original arrays resist writes and write-flag
escalation. Both deepcopy(dataset) and pickle.loads(pickle.dumps(dataset)) produce
writable feature arrays. Assigning 999 succeeds and changes the copied dataset's
fingerprint; the original remains unchanged. Reconstruction bypasses constructor
storage normalization. Dataset round trips were tested; every contract round trip
was not exhaustively tested. The runner does not copy/pickle these contracts.

### F3: structural artifact corruption

Location: experiments/provenance.py:157-175.

**OBSERVED by reviewer and primary:** verify_artifacts accepts an added dangling
symlink, an added symlink to an external directory, and artifacts.json replaced
by a symlink to an identical external index. Indexed result bytes/hash stayed
unchanged. is_file-only enumeration skips the first two; the index itself has
no symlink/containment check before reading. Indexed regular-file corruption
still rejects. This is a completeness/containment/relocation gap, not evidence
that an indexed checksum mismatch passes or that publication overwrites outputs.

### F4: quoted Git source paths

Location: experiments/provenance.py:72-77.

**OBSERVED by reviewer and primary:** a clean temporary candidate copy plus
untracked src/solar_flare_jepa/é.py makes Git emit a quoted porcelain path.
The parser's line[3:] starts with a quote, bypassing startswith('src/').
code_provenance(require_clean=True) succeeds with tracked_dirty=false.
The file is included in the source hash; the failure is the clean/track gate and
usable path reporting, not an omitted byte hash. Candidate itself has no such
untracked source. Temporary copies used existing Git metadata and changed no
protected refs.

### F5: squared-loss underflow

Location: evaluation/trajectory.py:92, :104, :182, :192.

**OBSERVED by reviewer and primary:** targets 1e-170, model points zero,
reference points 2e-170 yield MAE approximately 1e-170 but RMSE **0 with no
reason**, and persistence_mse_skill null/zero_persistence_loss. Correct RMSE
is 1e-170 and MSE skill is zero. Squaring silently underflows in float64;
underflow is not raised by the evaluator's errstate. Normal-scale controls and
scaled independent arithmetic succeed. Large squared-loss overflow is an explicit
evaluation failure, which is a different behavior.

The implementation report mentions tiny squared-loss underflow as a limitation.
This audit confirms its concrete false-zero consequence; it is not a newly
observed failure at the pinned GOES or default fixture scales.

### F6-F9: bounded input/API issues

- **F6**, contracts.py:285: metadata
  {"source_hash":"first","source_hash":"second"} is accepted and canonicalized to
  {"source_hash":"second"}. Nonfinite/nonobject/malformed metadata otherwise
  rejects. Config duplicate-key rejection works; this gap is dataset metadata.
- **F7**, baselines.py:77, :163, :175: after fitting TrailingMean(2), explicitly
  setting lookback_steps=1 changes first forecasts from 1.5 to 2 while parameters
  still records lookback 2. Ordinary predict does not mutate parameters.
- **F8**, experiments/config.py:25, :56, :136; provenance.py:160-164;
  scripts/run_experiment.py:17: alpha 2**64 causes uncaught TypeError; a
  10**400 metric weight causes OverflowError. Installed CLI exits 1 with traceback
  and creates no output. read_finite_json accepts exponent 1e400 as inf, although
  subsequent validate_config rejects nonfinite configs. Artifact schema_version
  true is accepted as equal to 1; null files/entries raise TypeError. These cases
  were independently rerun. Indexed bytes/hashes remain checked.
- **F9**, contracts.py:196, :218; baselines.py:39: value 1e-100/reference 1e300
  has finite log coordinate -400, but intermediate division underflows to zero
  and is refused. Inversion of -400 similarly underflows before multiplication
  although native 1e-100 is representable. This is an explicit refusal, not an
  invented prediction. Default GOES reference is 1 W/m2.

## 6. Independent mathematics review

All hand/probe values below are artificial arithmetic fixtures, not scientific
skill estimates.

| Baseline | Independently checked mathematics |
|---|---|
| Persistence | Latest valid observed target counterpart repeated at every lead; correct channel names/units/order. Context [2,4,6] gives 6. |
| Training mean | Arithmetic mean over unique valid raw training bins, not duplicated overlapping windows. Raw 1..7 gives 4. |
| Trailing mean | Mean over valid cells in declared causal trailing bins; trailing [4,6] gives 5. |
| Drift | Last value plus first-to-last valid slope times elapsed future time; [2,4,6] gives 8,10. Missing/stale context uses actual interval-end separation. |
| AR(1) | Least squares with intercept on adjacent valid raw pairs; recursive fixed coefficients from latest valid state. Law next=1+2*state after 127 gives 255,511. No gap bridge or held-out refit. |
| Direct ridge | Center X/Y using training means; minimize residual sum of squares plus alpha times squared slopes; intercept unpenalized. X=[0,1,2], Y=(1+2X,2+3X), alpha=2 gives slopes (1,1.5), predictions (6,9.5) at X=4. Multioutput lead/target flattening and feature-shift invariance also checked. |

The independent mathematics reviewer executed **5 multivariate/reordered/stale-state
baseline cases**, **4 multioutput ridge cases**, **80 seeded masked/zero-weight
trajectory cases with exact Fraction oracles**, and **625 confusion tables**
(each count 0..4). The HSS2 oracle used chance-corrected agreement independently
of the implementation's expanded rational expression.

Primary hand trajectory check used observations [1,3,4], points [2,1,4],
reference points [1,1,1], and unique adjacent training values [1,2,4]:

| Metric | Hand result | Observed |
|---|---|---|
| MAE | (1+2+0)/3 = 1 | 1 |
| RMSE | sqrt((1+4+0)/3) | 1.2909944487358056 |
| Persistence MAE skill | 1 - 1/(5/3) = 0.4 | approximately 0.4 |
| Persistence MSE skill | 1 - (5/3)/(13/3) = 8/13 | 0.6153846153846154 |
| MASE | 1 / ((1+2)/2) = 2/3 | 0.6666666666666666 |
| Pearson | centered covariance / norm product = 0.5 | approximately 0.5 |
| Median pinball, supplied q=0.5 points [2,1,4] | 0.5*MAE = 0.5 | 0.5 |

Pooling accumulates weighted absolute/squared losses over common valid,
positive-weight cells and takes the square root afterward. It does not average
lead RMSEs. Different declared target units prohibit raw cross-target pooling.
MASE uses adjacent valid unique training differences. Correlation is an explicitly
unweighted diagnostic; zero aggregate weights do not redefine its target mask.
Empty masks, insufficient pairs, constant inputs, zero training scale, and zero
reference loss have explicit null/reason cells, subject to F5's extreme-range gap.

MAE/RMSE and training-denominator MASE definitions were checked against
[Hyndman and Koehler](https://www.robjhyndman.com/papers/mase.pdf), pp.8 and 12.
The repository's adjacent-valid exclusion across gaps is its declared masked-data
policy. Supplied-quantile pinball agrees with the piecewise definition in
[Steinwart and Christmann](https://arxiv.org/pdf/1102.2101), p.2.

Primary binary hand table: TP=3, FP=1, FN=2, TN=4; valid/mature masks all true.

| Metric | Hand formula/result | Observed |
|---|---|---|
| Precision | TP/(TP+FP) = 3/4 | 0.75 |
| Recall/POD | TP/(TP+FN) = 3/5 | 0.6 |
| FAR | FP/(TP+FP) = 1/4 | 0.25 |
| FPR | FP/(FP+TN) = 1/5 | 0.2 |
| F1 | 2TP/(2TP+FP+FN) = 2/3 | 0.6666666666666666 |
| TSS | 3/5 - 1/5 = 0.4 | 0.4 |
| HSS2 | 2*(3*4-1*2)/((3+2)*(2+4)+(3+1)*(1+4)) = 0.4 | 0.4 |
| Brier | squared probability-error sum 2.37 / 10 | approximately 0.237 |

The probability vector was [.9,.8,.7,.2,.1,.8,.3,.2,.1,0], with the first five
outcomes positive. HSS2/TSS formulas were checked against
[Bloomfield et al.](https://arxiv.org/pdf/1202.5995), equations 1-2. Binary Brier
was checked against [NOAA/NCEP MMAB 261](https://polar.ncep.noaa.gov/mmab/papers/tn261/mmab261.pdf),
equation 1.

Undefined denominators remain undefined. Probability-only input does not invent
a decision threshold/confusion table. All-negative/all-positive, empty,
invalid/immature, constant/single-pair and no-training-scale cases were covered
by executed tests and independent probes. No formula error was found in the
ordinary-range cases.

## 7. Leakage red-team

| Attack | Fresh evidence and outcome |
|---|---|
| Drastic future targets/features | Whole-chain test changes post-training-cut features to 1e100 and targets to -1e100; all six earlier numeric fits/predictions invariant. Independent reviewer repeated all-six controls. Content fingerprints appropriately change. |
| Future-target argument at predict | FutureGrid has coordinates/spec/identity but no realized values or masks. Passing ForecastTargets instead rejects. |
| Split boundaries and exact cuts | Raw rows selected before windows; lookup has no outside-partition observation. End-equality admitted; context/lookback/horizon/maturity crossing cuts excluded. |
| Missing context/lookback/target/maturity ticks | Builder exclusions and public-slice tick guards reject tested gaps; no interpolation or bridging. |
| Delayed/unknown availability | Operational unknown availability rejects; delayed feature/dependency cells are masked/excluded by issue deadline. |
| Reordered/duplicate/ambiguous origins | Tests and independent probes reject reversed issue order, duplicate IDs, strings/maps/sets in place of ordered origin collections. |
| Malformed metadata and masks | Usual nonfinite/object/nonboolean/missing-mask cases reject; F6/F8 record remaining parsing/type edges. |
| Incomplete raw support | Missing coordinates/outside bounds reject; F1 demonstrates that existing coordinates with contradictory validity/values still pass the public boundary. |
| Supplied groups across cut/maturity | Builder masks dependent raw cells and excludes affected windows; synthetic closure/group tests pass. |
| Empty/degenerate scores | Explicit undefined reasons; empty-training experiment records failures and attempted held-out origins. F5 is the tiny squared-error exception. |

**FIT:** runner.py:89-115 obtains training from the train builder and passes only
that TrainingSlice to each fit. Mean/AR use unique raw training samples; ridge
uses training windows. There is no adaptive validation/test refit.

**PREDICT:** runner.py:122-134 calls each baseline with context and FutureGrid.
Every model's outputs for that partition are fixed before evaluation begins.

**EVALUATE:** runner.py:160-176 receives realized ForecastTargets afterward.
Prediction validation prevents models from hiding failures through their own
target masks or origin dropping. Model errors are recorded on common coordinates.

**OBSERVED:** no better earlier numeric behavior resulted from changed future
observations on the generated path. **UNKNOWN:** universal correctness for all
possible caller-built objects; F1 directly refutes the complete public boundary.
A bare caller-supplied split fingerprint cannot authenticate arbitrary group
eligibility. That trust limitation is separate from F1's visible contradictions.

## 8. Reproducibility and actual experiment artifacts

The primary ran both configs twice from /private/tmp, with PYTHONPATH removed
and normal installed package imports. Every execution recorded candidate Git
HEAD 11b72bb0c714cf71edf1e5ccb390d38444bbb8c8, 54 attempted/successful
model/partition scores, zero failures, and nine SHA-256-indexed JSON artifacts.

| Mode | Execution | Execution ID |
|---|---|---|
| Synthetic | results/experiments/p1_audit_20261004_synthetic_a | f95915c0820c45d9bc2b13130587b5a8 |
| Synthetic | results/experiments/p1_audit_20261004_synthetic_b | 2bf438dbb3114ac38fb3b918d375ea5b |
| GOES | results/experiments/p1_audit_20261004_goes_a | dad4398aeefc4692b33aec075a820ecb |
| GOES | results/experiments/p1_audit_20261004_goes_b | 0814e22902854436acfbf2dcc47b53e9 |

| Mode | Retained train / validation / test | Excluded train / validation / test | Native valid targets |
|---|---|---|---|
| Synthetic | 112 / 52 / 52 | 8 / 8 / 8 | 240 per target |
| GOES XRS-B | 103 / 62 / 103 | 41 / 82 / 41 | 4,318 of 4,320 rows |

For each pair, the three seed-tag semantic experiment IDs were identical and the
execution IDs differed. These **eight artifacts** were compared directly as bytes
and all matched:

- resolved_config.json
- dataset_manifest.json
- split_manifest.json
- provenance.json
- model_parameters.json
- predictions.json
- metrics.json
- failures.json

result.json differs intentionally for execution ID/times/output; artifacts.json
differs accordingly. All four artifact indexes verified. Seed tags [17,29,43]
do not make deterministic baselines random; fixture RNG has a separately named seed.
No seed-average uncertainty or superiority was inferred.

| Identity | Synthetic | GOES |
|---|---|---|
| Config | fb94b363e63991a41bafea280efe0a1de198426baae6442d0fbd69d0b6499f9c | 9bab0a7cec48880cc503d2b4603f786b09dbf3b9c914a541101465d9197723ae |
| Dataset | 78858423dd4f8770bb2aa8dc5bac1f709fc6335ce3e4f551403f7e5c8281fd68 | 6968f0a40290951acba2d73af362f1ced6cfee6304b68aba82416246cd6562b6 |
| Split | 7f3359ec2af5ab738ae69dc89ffee80793134d74e4811a24b350defa5b7a5b23 | 31c5655b6667274bd41aad03d160995d9aa5af8702b89eba9f4991230aa9f133 |
| Source, 35 files | 5a701dd279d15dd7f73f2b629785d932af704ed81235a5c9ad2df1d10c0e288c | same |

These match the implementation checkpoint fingerprints. Commit identity is
recorded separately from semantic source identity: the documentation-only
11b72bb commit does not change source/config/dataset/split hashes.

Independent temporary-root source replays also produced equal semantic IDs and
seven deterministic artifact byte streams. GOES artificial-fixture relocation
tests preserve scientific identity without rewriting legacy sidecars. A separate
four-process publication race had exactly one complete winner and three
FileExistsError losers, with no staging debris. A valid config with empty train
support produced status=failed, 18 attempts, zero successful scores, 18 explicit
fit failures, preserved validation/test origins, and a valid artifact index.

| Reproducibility level | Supported conclusion |
|---|---|
| Semantic | OBSERVED for repeated synthetic/GOES runs and same-machine temporary-root relocation. |
| Byte for byte | OBSERVED for the eight listed artifacts in each installed pair; summaries/indexes intentionally differ. Seven deterministic source-replay artifacts also matched. |
| Same machine | OBSERVED on the recorded Python/dependency/numerical environment. |
| Fresh project-package installation | OBSERVED through a newly built wheel/new venv, with existing third-party libraries deliberately reused; section 10. |
| Independent clean dependency environment | UNKNOWN; no separate complete dependency-stack reproduction was run. |
| Cross-platform/BLAS/Python/NumPy versions | UNKNOWN; Linux/Windows publication code was read but not executed. |

Provenance includes source bytes, actual loaded/package file hashes, Git commit
and branch, tracked cleanliness, Python/platform and six package versions.
It does not certify all native library/BLAS build details or power-loss durability.
Atomic visibility/no replacement on this macOS host was tested; adversarial
concurrent parent-directory replacement and full crash/power-loss recovery were not.
F3/F4 prevent claiming universal complete-contained-artifact or clean-track guards.

## 9. Fresh targeted and full tests

Primary commands, executed against the unchanged candidate:

```sh
.venv/bin/python -m pytest -q tests/test_forecasting_contract.py tests/test_forecasting_splits.py tests/test_forecasting_windows.py tests/test_baselines.py tests/test_trajectory_metrics.py tests/test_event_metrics.py tests/test_experiment_provenance.py tests/test_experiment_reference.py tests/test_experiment_runner.py
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

| Check | Actual fresh result |
|---|---|
| Nine targeted modules | 240 passed, 1 warning, 4.50 s, exit 0 |
| Complete repository suite | 406 passed, 1 warning, 39.19 s, exit 0 |
| pip check | No broken requirements found, exit 0 |
| Contract review's scoped run | 124 passed, exit 0 |
| Mathematics review's scoped run | 110 passed, exit 0 |
| Reproducibility review's scoped runs | 26 + 26 passed, second run one warning |
| Independent expected-rejection contract probe | Exit 1: three unexpected acceptances, finding F1 |
| Primary ordinary-math/F1/numeric/copy/metadata probes | Exit 0 with explicit defect assertions and ordinary hand-calculation checks |

Scoped reviewer counts overlap the primary suites; they are not additive new
repository tests. Adversarial probe scripts are temporary evidence, not added
tests or implementation fixes.

Unresolved warning, unchanged from the starting suite:

```text
RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject
```

It surfaced at the artificial GOES/reference netCDF4 import boundary. It was
not suppressed. Passing tests do not certify ABI compatibility. Pip also reported
its nonwritable-cache warning in sandbox diagnostics; no dependency repair was
attempted. The dependency lock/declarations remain unchanged.

## 10. Installation, CLI and package/source identity

**OBSERVED:** normal imports from /private/tmp with PYTHONPATH removed resolve
under .venv/lib/python3.13/site-packages, not src. All **22 package Python files**
match checkout SHA-256. The source manifest contains **35** source/config/schema/
build files and its fingerprint is the one in section 8.

Fresh build command:

```sh
.venv/bin/python -m pip wheel --no-deps --no-cache-dir --wheel-dir /private/tmp/solarjepa-p1-audit-20261004/wheels .
```

The first sandbox attempt could not resolve PyPI for the declared setuptools
build dependency. The approved network retry succeeded with isolated build
dependencies. No project runtime/scientific data acquisition or dependency-file
change occurred.

Built wheel: solar_flare_jepa-0.1.0-py3-none-any.whl, **60,201 bytes**,
SHA-256 **5f6e9fc245c4ceff3b3a204986cd56a28c815061be290ce6104932e1a01c510b**.
All 22 wheel Python modules exactly match checkout. No raw data, .agents,
results, weights, or unexpected package file was present.

The wheel was installed with --no-deps --no-index in a **new temporary venv**.
Its project package resolves entirely inside that new venv. A clearly named
p1_audit_borrowed_dependencies.pth in that temporary environment supplies the
existing .venv third-party libraries; it contains no src path and changes no
original environment file. This is explicitly a fresh project-package check,
not an independently clean dependency-stack check.

The thin run_experiment.py wrapper was copied to /private/tmp and exercised
there with PYTHONPATH removed. Help passed. A synthetic run completed with
54 scores/zero failures and candidate Git identity; its index verified, semantic
IDs matched, and all eight stable artifacts matched the earlier installed run.
All 22 provenance file entries were checked as matching installed-distribution
files, and actual __file__/sys.path independently confirmed the new venv location.

The fifth output is
results/experiments/p1_audit_20261004_fresh_wheel_synthetic, execution ID
50fda540127047d29c1d5866c59a05ea.

**INFORMATIONAL packaging limit:** pyproject.toml has no console-script entry point,
and the wheel does not install scripts/run_experiment.py as an executable.
The approved design specifies a repository wrapper using the installed core;
that workflow passed without checkout-source/PYTHONPATH dependence. A wholly
wheel-contained command distribution was not implemented or claimed.

Environment observed: Python 3.13.3, macOS 26.3 arm64; project 0.1.0,
NumPy 2.2.6, pandas 2.3.3, xarray 2026.7.0, netCDF4 1.7.2, pyarrow 25.0.1.
An external-matching source path can sometimes receive an installed_distribution
label through discoverable egg-info metadata. The audit therefore checked actual
loaded __file__ paths and bytes rather than trusting that label alone.

## 11. GOES adapter and scientific-gate preservation

**OBSERVED:** experiments/reference.py reads only the configured pinned manifest,
preparation config, historical sidecar, Parquet, and three avg1m sources.
It reuses verified_manifest_paths, read_goes and containment utilities.
It verifies raw sizes/SHA-256, preparation/sidecar time/unit/quality policies,
source association, processed hash and row count, then compares the complete
fresh read_goes frame exactly with Parquet. No write/download/calibration/label
construction call is present in that adapter. The runner output writes only
new ignored experiment directories.

Legacy absolute sidecar prefixes are not dereferenced. Filename/hash/size
association must be unique; scientific source IDs become repository-relative.
Portable identity deliberately omits sidecar/Parquet serialization-specific
hashes while their actual bytes are checked before use. Both historical
sidecar and Parquet retained their snapshot hashes after all new runs.

**OBSERVED:** the GOES smoke selects native XRS-B W/m2 with the existing strict
channel-specific mask, 60-second bins, 6-hour context, 1-hour horizon and
10-minute stride. Log predictions are labelled inverse-transformed points and
scored in native units. The config is a mechanics reference, not final task
selection or physical conditional-mean evidence.

**DOCUMENTED/OBSERVED distinction:** the existing reader enforces its pinned
product UTC convention, bin-start metadata, units, coverage and flag schema.
P1 reuses these checks without changing scientific semantics. Bin end is an
earliest retrospective availability bound; actual delivery/latency remains
**UNKNOWN**, and operational mode is refused. GOES is external reference
validation, not Aditya data.

Both scientific gate manifests have unchanged Git blobs and local hashes:

- data/manifests/solexs_phase_d1_requirements.json: gate=BLOCKED_FOR_PHASE_E.
- data/manifests/solexs_phase_e_requirements.json: gate=BLOCKED, with unresolved
  version-specific timing/GTI/exposure, correction/HK and response/calibration requirements.

| Existing scientific requirement | Preserved status and evidence |
|---|---|
| SoLEXS TIME/MJD/date precedence and UTC/clock correction | UNKNOWN/PENDING; no P1 reinterpretation or conversion; native reader unchanged |
| LC/PI bin semantics and NUMBAND | UNKNOWN/PENDING for scientific application; no inferred rule |
| Continuous GTI endpoints/filtering | UNKNOWN/PENDING; no new application |
| Exposure and correction state | UNKNOWN/PENDING; no invented exposure or deadtime policy |
| Housekeeping compatibility | Unresolved, conditional on mission-approved workflow; no HK substitution |
| PI/channel-response mapping and units | Unresolved applicability/indexing; no counts-to-flux mapping |
| Gain/calibration/tools/CALDB date/pipeline compatibility | Unresolved; filename/version similarity is not approval |
| Cross-payload alignment | Not performed; no inferred timing alignment |
| Scientifically defensible real event definitions | Gated; evaluator accepts supplied labels only and runner constructs none |
| Phase E/historical acquisition/final dataset | Remains blocked; no expanded selection or gap filling |

**OBSERVED:** P1 runner admits only synthetic_fixture or pinned goes_reference.
Its baseline allowlist contains no neural/JEPA/ARCH/GARCH implementation.
Result fields explicitly retain foundation_smoke_not_scientific_skill,
BLOCKED_FOR_PHASE_E, not_constructed_real_event_definitions_gated,
deferred_pending_residual_diagnostics and novelty=UNKNOWN.

No new evidence resolving the existing scientific gates was obtained.
GOES smoke success provides no evidence that SoLEXS is science-ready.
Historical status text is explicitly labelled historical; preserved old reports
were not rewritten to imply later knowledge.

## 12. Preservation of the claimed 109 identities

The prior scratch snapshot exists at
/private/tmp/solarjepa-p1-start-identities.json and contains exactly **109**
path -> SHA-256 entries. Its own SHA-256 is
3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193.

**OBSERVED:** independent comparisons before and after audit executions found
**109 unchanged / 0 changed / 0 missing**.

| Snapshot category | Entries |
|---|---|
| .agents | 1 |
| configs | 6 |
| data | 70 |
| results | 32 |

The selection includes incidental .DS_Store/placeholders as well as scientific
files. The count does not mean 109 independent scientific certificates or every
possible historical file. The snapshot is historical supporting evidence;
the freshly executed content comparisons are observed evidence. Git blob checks
separately establish preservation of every inherited tracked scientific/config/
gate file, and pinned manifests separately establish source identities.

Additional read-only source checks:

- Three avg1m and three flsum NOAA files passed verified_manifest_paths against
  configs/data/noaa_sample.json: six files, total 1,002,585 bytes.
- SoLEXS inventory verification passed for both original archives; no re-registration.
- July 1 archive: 6,036,792 bytes,
  9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4.
- July 3 archive: 6,216,112 bytes,
  b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf.
- Preserved Parquet SHA-256:
  cc197f8186e0ec15b8ababd5a8c5549349d10fd15112cf4320ca4f23c114c068.

Full real FITS/PI/calibration diagnostics were not rerun. Preserved hashes
establish identity continuity, not resolution of scientific unknowns.
The new ignored audit experiment outputs are additional records and do not
replace any historical result directory.

The independent scientific reviewer also compared 48 inherited scoped tracked
paths against main and current worktree bytes, and independently checked 32
unique SoLEXS/evidence identities against unchanged manifest declarations,
including the official Tools-1.1 archive and historical native/readiness outputs.
Those checks agreed without relying on the 109-entry snapshot.

## 13. Integration simulation and discrepancies against the implementation report

Executed:

```sh
git merge-base --is-ancestor main feat/p1-experiment-evaluation-foundation
git merge-base --is-ancestor 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe feat/p1-experiment-evaluation-foundation
git merge-tree --write-tree main feat/p1-experiment-evaluation-foundation
git rev-parse 'feat/p1-experiment-evaluation-foundation^{tree}'
```

Both ancestor commands exit 0. Object-only merge simulation returned
1542fa1e4cb6502acf5f10e6fa1d91c09f9cd4f0, exactly the candidate tree.
There are no conflicts or unexpected ancestry. The first simulation attempt
was blocked by sandbox Git-object writes; an approved retry completed.
No branch ref, index, working tree, or protected main was merged/moved.

**OBSERVED integration contents:** 32 additions/two doc modifications; no
dependency/install-metadata change; full tests retain all 166 pre-existing cases
within the observed 406. A fast-forward would preserve the complete research and
implementation history and can leave both milestone branches intact.
Clean topology/test results do not authorize integration or close F1.

| Implementation report claim | Independent audit comparison |
|---|---|
| 29 added / 2 modified | Correct from frozen research base; main diff is 32 added / 2 modified |
| 240 targeted / 406 full tests | Reproduced exactly; different observed runtimes; existing warning retained |
| Complete public training-support guards | Bounds/tick guards reproduced, but F1 disproves internal raw/window validity/content consistency |
| Immutable forecasting contracts | Original construction passes; F2 ordinary copy/pickle guarantee is incomplete |
| Full clean-state/source checks | Intended dirty/change tests pass; F4 quoted untracked-source bypass remains |
| Complete artifact corruption/file-set checks | Indexed regular-file checks pass; F3 symlink structure and F8 type edges remain |
| Strict finite parsing/clear malformed refusal | Common config cases pass; F6/F8 expose bounded metadata/helper/type handling gaps |
| Correct native metrics with explicit undefined behavior | Ordinary formulas pass; documented tiny-square underflow concretely yields false RMSE zero (F5) |
| Eight byte-identical stable artifacts per mode | Reproduced for each installed pair on this machine |
| Installed imports/CLI/source identity | Reproduced; fresh wheel/copied wrapper strengthens project-package evidence, with explicit dependency-environment and no-console-entry-point limits |
| 109 identities unchanged and gates preserved | Reproduced from available snapshot plus fresh manifest/Git evidence |
| Final reviews had no material unresolved finding | Historical report is preserved; this fresh independent audit finds HIGH F1 and the bounded issues above |

The frozen design/repository audit/literature documents remain byte-identical to
805f1c3. Their historic proposal/no-implementation wording is not a claim about
current code. No historical document was silently corrected during this audit.

## 14. Evidence locations, final checks and eventual integration commands

Local audit logs/evidence reside at
/private/tmp/solarjepa-p1-audit-20261004/:
targeted-tests.log, full-tests.log, installed-provenance.json,
fresh-wheel-provenance.json, rerun-verification.json, identity-comparison.json,
pre-report-git-state.json, candidate-complete.diff, wheel build logs, four CLI logs,
fresh-wheel-synthetic.log, contracts-reproduction.log, symlink-reproduction.log,
quoted-source-reproduction.log, independent-boundary-math-expanded.log,
malformed-input-reproduction.log and malformed-cli-reproduction.log.

Independent full review notes and bounded probes are retained under /private/tmp:
solarjepa-p1-contracts-audit.md, solarjepa-p1-math-audit.md,
solarjepa-p1-repro-audit.md, solarjepa-p1-science-audit.md,
solarjepa-p1-contracts-probes.py, solarjepa-p1-math-probes.py,
solarjepa-p1-symlink-verifier-probe.py,
solarjepa-p1-quoted-untracked-source-probe.py and related scratch scripts.
These local evidence paths are not portable published artifacts; the main
finding's self-contained reproduction is included in section 5.

Primary installed rerun commands (each repeated with suffix b):

```sh
cd /private/tmp
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --config configs/experiments/p1_synthetic.json --root /Users/nealsalian/Desktop/SolarJEPA --output-dir results/experiments/p1_audit_20261004_synthetic_a
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --config configs/experiments/p1_goes_reference.json --root /Users/nealsalian/Desktop/SolarJEPA --output-dir results/experiments/p1_audit_20261004_goes_a
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/register_aditya.py --root /Users/nealsalian/Desktop/SolarJEPA --config configs/data/solexs_storage.json --verify
```

Final audit checks reverified the seven local/origin refs, ancestry, empty tracked
and cached diffs, candidate/main diff whitespace, forbidden index paths, unchanged
source fingerprint, all new result indexes, and all 109 snapshot hashes.
After writing this report, the expected sole additional path is this untracked
report. Neither this report nor the Paperclip pointer is staged.

### Stop point and future human procedure

**Current candidate 11b72bb is NOT_READY_FOR_INTEGRATION because of F1.**
There is no safe approved merge command for this rejected revision. Stop for
the user's explicit decision. Correction work, re-audit, integration, and any
push to main each require the applicable explicit authorization. Medium/low
findings need an owner disposition rather than silently disappearing.

After authorized corrections and a fresh passing readiness audit, a human can
use the following procedure. P1_REVIEWED_SHA must be set to the exact **new**
reviewed candidate; it must not be filled automatically from an unreviewed
moving branch. The placeholder deliberately prevents copying this block into
a present integration:

```sh
cd /Users/nealsalian/Desktop/SolarJEPA
git fetch origin
P1_REVIEWED_SHA=REPLACE_WITH_NEW_INDEPENDENTLY_REVIEWED_40_CHARACTER_SHA
test "$P1_REVIEWED_SHA" != 11b72bb0c714cf71edf1e5ccb390d38444bbb8c8 || exit 1
test "$(git rev-parse main)" = 1a4991da4dda9676caeb1d7e35a03408528c3188 || exit 1
test "$(git rev-parse origin/main)" = 1a4991da4dda9676caeb1d7e35a03408528c3188 || exit 1
test "$(git rev-parse feat/p1-experiment-evaluation-foundation)" = "$P1_REVIEWED_SHA" || exit 1
test "$(git rev-parse origin/feat/p1-experiment-evaluation-foundation)" = "$P1_REVIEWED_SHA" || exit 1
git diff --exit-code || exit 1
git diff --cached --exit-code || exit 1
git status --short --untracked-files=all
git diff --check main...feat/p1-experiment-evaluation-foundation || exit 1
git merge-base --is-ancestor main "$P1_REVIEWED_SHA" || exit 1
git merge-tree --write-tree main "$P1_REVIEWED_SHA" || exit 1
# Stop on any unexpected ref, file, conflict, or failed guard; do not reset work.
# Resolve only the audit report's tracking decision, without adding .agents.
# ONLY after explicit authorization to integrate this reviewed SHA:
git switch main
git merge --ff-only "$P1_REVIEWED_SHA"
test "$(git rev-parse main)" = "$P1_REVIEWED_SHA" || exit 1
git diff --check
git status --short --branch
```

If main has advanced, stop and re-evaluate ancestry/diff/tests against that new
base. Do not replace the pinned guard or rebase silently. A user-managed PR is an
alternative; preserve commits rather than squashing/rebasing, and disable branch
deletion. Repository branch protection may require that route.

**Only after separate explicit approval to push main**, or through a user-managed
PR satisfying protection:

```sh
git push origin main
git fetch origin
test "$(git rev-parse origin/main)" = "$P1_REVIEWED_SHA"
git branch -vv
```

No future procedure above was executed. If the report is later committed, stage
only docs/P1_INTEGRATION_READINESS_AUDIT.md on the candidate branch, use a focused
documentation commit, push only that feature branch, and record its new SHA.
Do not commit .agents, raw science, generated results or scratch; never force-add.
Both research and implementation milestone branches must remain on GitHub.
