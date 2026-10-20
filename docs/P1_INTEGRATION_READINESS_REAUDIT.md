# P1 integration-readiness re-audit — failed checkpoint

Date: 2026-10-04, Asia/Kolkata. Audit only; no implementation corrections.

**Decision: NOT_READY_FOR_INTEGRATION.**

**R1 — HIGH, blocking:** the common prediction boundary accepts contexts whose
intervals and actual availability extend beyond the issue time. Ordinary
deepcopy/pickle reconstruction and a sibling ForecastContext subclass bypass the
constructor guards. On an artificial fixture, Persistence changes from [10,11]
to the realized future targets [11,12], with the legitimate prediction grid,
training fingerprint and fitted parameter record unchanged. The primary auditor
independently reproduced the copied/pickled routes using the installed package;
a fresh reviewer independently reproduced those routes and the subclass route.

The original F1 training-window/raw-support defect is closed in the inspected
fitting implementation and executed regressions. This does not close R1, which
is a separate prediction-time causal-boundary failure. All six prediction APIs
accepted the malformed context in the primary reproduction; training mean's
numeric output stayed constant because it does not use context values.

Fresh primary tests passed: **53 TrainingSlice regression cases, 294 P1 targeted
cases, and 460 complete-suite cases**. Both broader suites retained the existing
NumPy/netCDF warning. The merge-tree simulation is clean, protected refs are
unchanged, and all 109 preservation hashes match. These checks do not override
the observed HIGH failure.

The new defect triggered the user's instruction to document it and stop. Fresh
real synthetic/GOES acceptance pairs were **not executed**. Completed fixture
tests, corruption controls, installation checks and preservation checks are
identified below; prior acceptance reports are not promoted into fresh evidence.
This report remains local and uncommitted because a HIGH finding was found.

## 1. Exact revisions and Git topology

| Checkpoint | Exact SHA |
|---|---|
| Audited candidate; current feature HEAD | 0f587d96d09583e3f7d15ce5b3d40145264e1ab6 |
| Local main and freshly fetched origin/main | 1a4991da4dda9676caeb1d7e35a03408528c3188 |
| Local/remote frozen research checkpoint | 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe |
| Previous failed-audit candidate | 11b72bb0c714cf71edf1e5ccb390d38444bbb8c8 |
| Preserve original failed audit | 6868a258c512129b580169a94d7ec475b9cea1f5 |
| First consistency/identity remediation | b5ae4c653a4268a7ff4b78a3b6d07d6c07350233 |
| Canonical fitting/subclass remediation | 8ba57aa58242facf7614e805695fe9e71406ea3c |
| Remediation documentation checkpoint | 0f587d96d09583e3f7d15ce5b3d40145264e1ab6 |

OBSERVED: `git fetch origin` completed. Local feature and remote feature are both
the audited candidate, with upstream divergence **0 / 0**. Origin is
`https://github.com/Neal-Salian/SolarJEPA.git`. Research and main match their
specified local/remote SHAs. The merge base of main/candidate is exactly main;
research is an ancestor of candidate. No refs were reset, rebased, deleted,
merged, or pushed by this re-audit.

The complete `main..candidate` history has 15 commits: frozen research; approved
plan; contracts; chronological windows; six baselines; evaluation; provenance;
origin ordering; raw-support/metadata guards; bounded experiment runner;
implementation report; and the four remediation commits above. Actual history
and per-commit file changes were inspected. No unaccounted side ancestry or
dependency changes appeared.

Initial tracked working tree/index were clean. The only initial untracked path
was `.agents/skills/paperclip/SKILL.md`. Its SHA-256 was and remains
`4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`.
It was neither edited nor staged. The sole intended additional untracked path
at completion is this report.

The original failed report remains byte-identical, SHA-256
`74eda048a70f80bde4ecdff2d443271aa66e6878573f5b94dd9a8089e196cba2`.
The remediation report remains byte-identical, SHA-256
`fbf6f50088f362c9a719b640bcba1f15140d5f28a4e7586bde2c0a2f02894bbe`.
Neither historical report was rewritten.

## 2. Complete diff and file inventory

OBSERVED: `git diff main...candidate` contains **35 additions and 2 modified
files**, 37 paths, 7,404 insertions and 37 deletions. Relative to frozen research
805f1c3, there are 32 additions and two modified files. The remediation range
11b72bb..candidate touches 15 distinct paths. Different bases explain the older
29-addition implementation inventory; that number is not the current main diff.

```text
M README.md
A configs/experiments/p1_goes_reference.json
A configs/experiments/p1_synthetic.json
A docs/P1_IMPLEMENTATION_REPORT.md
A docs/P1_INTEGRATION_READINESS_AUDIT.md
A docs/P1_LITERATURE_RECONNAISSANCE.md
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
A tests/test_event_metrics.py
A tests/test_experiment_provenance.py
A tests/test_experiment_reference.py
A tests/test_experiment_runner.py
A tests/test_forecasting_contract.py
A tests/test_forecasting_splits.py
A tests/test_forecasting_windows.py
A tests/test_training_slice_consistency.py
A tests/test_trajectory_metrics.py
```

The full diff is retained locally as
`/private/tmp/solarjepa-p1-reaudit-20261004/candidate-complete.diff`. Source,
configs, schema, tests, CLI, package metadata, inherited scientific files and
historical docs were inspected; documentation was supporting context only.
README/status changes update milestone reporting; frozen research proposal
wording remains historical, not an assertion that current implementation is
absent. No dependency/install metadata changes exist in the main diff.

Actual index/history inspection found no scientific ZIP/FITS/NetCDF/Parquet/
array/checkpoint files or generated results committed. Only the pre-existing
raw/interim/processed/results `.gitkeep` placeholders are tracked in those bulk
locations. `.gitignore`, packaging, dependency pins, existing scientific configs,
manifests, data readers and AGENTS.md are unchanged. Actual raw ZIP, Parquet and
experiment-output paths matched ignore rules using `git check-ignore -v`.

The Paperclip pointer is excluded from package discovery, runtime source
fingerprints and scientific input construction. Its path is recorded as
untracked provenance; none of the P1 loaders or tests uses it as scientific
input. It can affect an agent's available tooling but no observed package,
installation, numerical output or scientific identity. It remains uncommitted.

## 3. Fresh original F1–F9 dispositions

These are this audit's dispositions, not copied acceptance decisions. No open
issue is silently fixed or represented as owner-approved. MEDIUM/LOW means a
bounded outstanding issue under the stated evidence; it does not certify every
consumer or future numerical domain.

| ID | Original severity | Fresh disposition | Current evidence and impact |
|---|---|---|---|
| F1 | HIGH | RESOLVED | Canonical raw/window joins at contracts.py:544–561, exact base constructors at :470–488 and baselines.py:63–64. Fresh 53-case module and 177-case independent review reject inconsistent values/masks/availability and fitting subclasses. Coherent changes get different effective identities. |
| F2 | MEDIUM | BLOCKING in conjunction with R1 | Fresh deepcopy/pickle restores writable ForecastContext buffers; malformed temporal/availability arrays are consumed by predict. The original writability defect remains, and its demonstrated causal consequence is R1 HIGH. Fitting copies are guarded; prediction copies are not. |
| F3 | MEDIUM | STILL_OPEN_NONBLOCKING | Fresh dangling/external-directory/index symlinks pass artifact verification; indexed byte corruption and extra regular files reject. Completeness/containment guarantee remains incomplete, without evidence of indexed hash mismatches passing or output replacement. |
| F4 | MEDIUM | STILL_OPEN_NONBLOCKING | Real scratch Git emits quoted untracked `é.py`; clean-source gate accepts while including its bytes in the source hash. ASCII control rejects. Candidate itself contains no such untracked source. Track/clean guarantee is incomplete, not omitted-content hashing. |
| F5 | MEDIUM | STILL_OPEN_NONBLOCKING | Fresh code comparison confirms unchanged `signed**2` float64 RMSE/MSE path and no underflow refusal. Squaring 1e-170 cannot represent 1e-340 in float64; false-zero consequence is mathematically inferred from current code. Original execution is historical evidence; a new tiny-loss runtime probe was not launched after R1. Ordinary-range metric tests passed. |
| F6 | LOW | STILL_OPEN_NONBLOCKING | Fresh duplicate metadata keys collapse to the last value and share the resulting canonical dataset identity with that unambiguous last-value object. Generated ordinary adapter metadata has no duplicates. No authenticated semantics claimed. |
| F7 | LOW | STILL_OPEN_NONBLOCKING | Primary installed probe: fitted TrailingMean(2) first prediction 1.5 becomes 2 after explicit `lookback_steps=1`, while recorded lookback remains 2 and parameters stay unchanged. Requires caller mutation; runner does none. |
| F8 | LOW | STILL_OPEN_NONBLOCKING | Fresh exponent overflow parses as infinity; oversized alpha/weight raise TypeError/OverflowError and CLI tracebacks without output. Boolean artifact schema version accepts; null index entries raise TypeError. Ordinary malformed/common finite config controls pass. |
| F9 | LOW | STILL_OPEN_NONBLOCKING | Fresh source comparison confirms unchanged division-before-log and power-before-reference inversion. Extreme reference 1e300 and native 1e-100 cause avoidable intermediate underflow; explicit failure is inferred from those unchanged operations. New extreme-range runtime probe was not launched after R1. No fabricated successful prediction; current fixed reference defaults avoid this example. |

F3/F4/F6/F8 have 17 freshly recorded reproduction/control outcomes in the
provenance review. F5/F9 are explicitly static/math dispositions with incomplete
fresh runtime retesting. Their original reports alone are not treated as proof
that current executions passed. Their scope/range dispositions need reconsidering
if the public numerical/API claims or data domain change.

## 4. Original HIGH and fitting subclass remediation

OBSERVED historical code diff: 11b72bb validates raw and supervised tensors
separately, but never joins their cells. DirectRidge consumes window values/masks
while other models use raw support. b5ae4c6 adds exact joins, canonical raw
availability and an effective training fingerprint. Its use of dynamically
dispatched dataclass reconstruction could still invoke overridden subtype hooks.
8ba57aa replaces those paths with exact base constructors and base declared fields.
The two older revisions were inspected through Git; they were not executed by
changing the shared checkout or claimed as newly reproduced historical runs.

Current TrainingSlice canonically rebuilds ForecastSpec, ForecastContext,
FutureGrid and ForecastTargets. It retains chronology, coordinate/bounds, full
dependency tick coverage, lookback and maturity checks. Context masks equal
indexed raw eligibility plus issue-time availability, target masks equal indexed
raw target masks, true values exactly equal the canonical raw values, and false
window cells contain NaNs. Operational raw availability is mandatory; genuinely
unknown retrospective availability stays unknown. There is no clipping,
imputation, inconsistent-row repair, or identity recomputation to hide corruption.

All six baselines inherit `_Baseline.fit`, which constructs the exact base
TrainingSlice before `_fit` and records the fingerprint from that same snapshot.
DirectRidge selects complete declared feature lags and all horizon target cells
from it, then applies the canonical recorded spec transform. Native training
information, raw masks/availability, spec, ordered origins/issues and bounds
determine both fitting data and computed identity. Future-only dataset/split
labels are deliberately outside the effective training fingerprint.

Fresh tests exercise contradictory context/target values, mask upgrades and
downgrades, hidden finite false-window payloads, overlapping-coordinate
contradictions, forged/dropped availability, delayed delivery, joint raw/window
mutations, copied corrupt training, no-op TrainingSlice/context/grid/target
subclasses, and overridden spec transforms. Value and mask mutations of copied
training are rejected by every baseline. Jointly consistent changed raw/windows
fit under different effective training fingerprints. The runner regression
independently reconstructs training identity and seed-tagged semantic IDs.

No same-effective-training-fingerprint/different-data fitting counterexample was
observed in the executed cases. This is bounded evidence, not a claim about
arbitrary malicious Python getters, monkeypatching, hash collisions or concurrent
in-process object tampering. Independent instrumentation of every `_fit` argument
and further historical isolated execution were curtailed by R1.

## 5. R1 — new HIGH prediction leakage, unchanged fitting identity

Locations: `forecasting/baselines.py:102–114`, especially :105–112;
`forecasting/contracts.py:377–386`; guards bypassed at :332–352.

OBSERVED root cause: predict checks `isinstance`, dataset/spec labels, origin
IDs and issue alignment, then consumes supplied context directly. Alignment
compares future interval coordinates only when both operands are FutureGrid.
It does not rerun context interval/availability validators. Writable copied
arrays and a no-op sibling constructor can therefore introduce future support
which the canonical context constructor would reject.

Primary installed reproduction uses an artificial one-second series 1..12,
train [0s,8s), test [8s,12s), two context bins and one forecast bin. Legitimate
test issues are 10s and 11s. Advancing copied context coordinates/delivery by
one cadence puts final intervals' ends/delivery at 11s/12s, after issue. Filling
the last context cell with the first realized target gives:

| Baseline | Legitimate output | Malformed future-context output | Parameter record |
|---|---|---|---|
| Persistence | [10,11] | [11,12], exactly realized targets | unchanged |
| Unique-training mean | [4.5,4.5] | [4.5,4.5], invalid context still accepted | unchanged |
| Trailing mean(2) | [9.5,10.5] | [10,11] | unchanged |
| Drift(2) | [11,12] | [11,12], invalid context still accepted | unchanged |
| Fixed AR(1) | [11,12] | [11,12], invalid context still accepted | unchanged |
| Direct ridge(2,.1) | [10.984330484330483,11.981481481481483] | [11.482905982905983,12.48005698005698] | unchanged |

The Persistence absolute error changes from 1 at each origin to 0. Drift/AR1
already predict this artificial ramp perfectly; no improved score is claimed
for them. Ridge changes numerical output, with no claim it improves here.
All six accept temporally invalid prediction support. Training data are unchanged,
so their identical training fingerprint is correct; R1 is not a new fitting-hash
collision or evidence that the training remediation silently failed.

This is an internally observable contradiction, not inferred external science
semantics. It needs no arbitrary object-level field mutation: ordinary writable
NumPy assignments after ordinary copy/pickle suffice. A sibling subclass also
accepts these fields. Canonical reconstruction of the same fields rejects with
`Context must contain only completed past bins on the declared grid`.

Self-contained reproduction, using the matching installed package from outside
the checkout; all inputs are artificial:

```python
from copy import deepcopy
from dataclasses import fields
import pickle
import numpy as np
from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastSpec, TimeSeriesDataset,
)
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.forecasting.baselines import Persistence

ns = 1_000_000_000
starts = np.arange(12, dtype=np.int64) * ns
values = np.arange(1., 13.)[:, None]
mask = np.ones_like(values, dtype=bool)
data = TimeSeriesDataset('artificial_probe', 'synthetic_fixture',
    starts, starts + ns, values, mask, values, mask,
    ('x',), ('x',), ('u',), ('u',), 1, starts[:, None] + ns)
spec = ForecastSpec(1, 2, 1, ('x',), ('x',), ('u',), ('u',))
train = build_partition_windows(data, spec,
    TemporalPartition('train', 0, 8 * ns)).training_slice
test = build_partition_windows(data, spec,
    TemporalPartition('test', 8 * ns, 12 * ns))
model = Persistence().fit(train)
before = model.parameters
assert model.predict(test.context, test.targets.grid).values[:, 0, 0].tolist() == [10., 11.]
for context in (deepcopy(test.context),
                pickle.loads(pickle.dumps(test.context))):
    context.starts_ns[:] += ns
    context.ends_ns[:] += ns
    context.availability_ns[:] += ns
    context.values[:, -1, :] = test.targets.values[:, 0, :]
    assert (context.ends_ns[:, -1] > context.issue_times_ns).all()
    prediction = model.predict(context, test.targets.grid)  # INVALIDLY ACCEPTED
    assert np.array_equal(prediction.values, test.targets.values)
    assert model.parameters == before
    try:
        ForecastContext(**{f.name: getattr(context, f.name)
                           for f in fields(ForecastContext)})
    except ValueError:
        pass  # Required rejection exists at construction, but predict skips it.
    else:
        raise AssertionError('Canonical constructor unexpectedly accepted')
```

INFERRED corrective requirement, not implemented: the prediction consumption
boundary must establish canonical context/grid/spec shape, masks, coordinates
and availability before using input. A fitting-only defense does not secure
prediction. Future intervals must fail before prediction; silently relabeling
coordinates would not restore causality. No repair was attempted in this audit.

The fresh reviewer's additional sibling variant used a ForecastContext subtype
with `def __post_init__(self): pass`, supplied the same shifted future coordinates,
delivery and target-valued final cell, and called the fitted Persistence with the
unchanged legitimate grid. It also returned the exact realized targets. This
does not require copying: prediction's `isinstance` accepts the subtype while
construction never ran canonical validators. The executed variant and canonical
negative control are retained in prediction_probe.py and the reviewer report.

## 6. Full P1 requirements and leakage evidence

| Requirement | Actual implementation | Fresh verification / limit |
|---|---|---|
| Native units, explicit names/references/domain | contracts ForecastSpec/TimeSeriesDataset; exact name/unit selection in windows | Contract/baseline/window tests pass; F9 extreme transform range open. |
| Immutable arrays, masks and metadata | bytes-backed arrays, frozen dataclasses, canonical JSON; detached manifests/parameters | Original constructors resist writes; F2 copies and R1 prediction invalidate the universal guarantee. |
| Actual availability and target-free future grids | ForecastContext/FutureGrid; operational/retrospective spec; windows dependency maximum availability | Ordinary construction/delayed-cell tests pass; FutureGrid has no realized values; R1 shows target-free signature alone is insufficient. |
| Origin/order/metadata/training support validation | `_origins`, contracts TrainingSlice, splitting/window constructors | Duplicate/reordered/gapped/outside-bound/missing-mask controls pass in executed suites; F6/F8 bounded parsing edges open. |
| Raw-first chronological split and complete dependency support | chronological_partitions; partition-local lookup; lookback/maturity and supplied-group closure | Splitting/windows tests pass, including no shared partition support and missing dependency intervals. No new scientific event semantics invented. |
| Retained/excluded origins and common masks | WindowedPartition manifest; complete/masked eligibility; raw masks independent of window stride | Executed manifests/count/support controls pass; no model-specific origin dropping. |
| Train-only fitting | common canonical fit snapshot; mean/AR raw support; Ridge supervised raw-backed cells | F1 regressions pass for all six; huge future feature/target changes preserve effective fit and earlier predictions on valid builder paths. |
| Predict before realized-target evaluation | runner builds prediction outputs with context/grid; evaluator later sees targets | Valid runner path has no realized target prediction argument. R1 permits realized future data inside invalid context. HIGH failure. |
| Six deterministic baseline formulas | baselines.py, fixed transforms, unique raw samples/adjacent AR pairs | Fresh literal-output and baseline mathematics tests pass. Root artificial six-model numerical probe also executes independently. |
| Trajectory/event formulas and undefined denominators | evaluation/trajectory.py and events.py | Complete targeted suite passes; fresh formula review completed; broader independent metric-oracle execution curtailed after R1. |
| Strict config, failure/provenance/result records | experiments config/runner/provenance, schema and CLI | Producer training-ID/structured failure/ordinary malformed-input tests pass. F3/F4/F6/F8 limit unconditional robustness claims. |
| Read-only pinned GOES adapter | reference.py rehashes source/preparation/Parquet and regenerates ALL prepared content | Artificial adapter tests pass; real six-file identities and all historical sidecars hash unchanged. No fresh real acceptance run claimed. |

Operational delivery is checked against entire feature dependency availability;
retrospective bin completion remains distinct from unknown delivery latency.
Raw feature eligibility is by partition end, then context eligibility by issue.
Target eligibility does not acquire feature-only lookback. Raw maturity support,
supplied group purging and conservative cascading group closure remain visible
and tested. An externally declared group/scientific hash is not an authenticity
certificate. No observed correct-builder future/split contamination was found.

Incomplete new attacks after the stop include independent historical execution,
all-contract serialization permutations, prediction-grid/spec overrides,
availability-only variants, concurrent mutable-input races, and additional
same-fingerprint construction mechanisms. No claim that all were exhausted.

## 7. Mathematical review

Actual baseline and evaluator formulas were read independently by the fresh
mathematics reviewer and primary auditor, with ordinary-range tests executed.
The primary six-model artificial probe also permits direct hand checking:
train raw targets 1..8 give mean 36/8=4.5; last test values 9,10 give persistence
10 and trailing mean 9.5; one-cadence drift gives 11; adjacent raw pairs satisfy
AR1 intercept 1/coefficient 1 and give 11. The second origin analogously gives
11,10.5,12,12. Canonical fitting windows for Ridge(2,.1) have X rows [1,2] through
[6,7] and Y=3..8, so means are [3.5,4.5] and 5.5, centered column sum of squares
17.5. Each symmetric ridge coefficient is 17.5/(35+.1)=175/351; intercept is
5.5−8(175/351). Test X=[9,10] gives 5.5+11(175/351)=10.984330484330483;
[10,11] gives 5.5+13(175/351)=11.981481481481483, matching the independent run.
The intercept is unpenalized; augmentation avoids forming squared-condition
normal equations. Alpha-zero minimum-norm and complete-mask behaviors remain
covered by executed existing tests.

Trajectory source applies common target masks in native units:
MAE=mean(abs(error)); RMSE=sqrt(mean(error²)); persistence-relative skill
1−model loss/reference loss for MAE and MSE; MASE divides by unique adjacent
valid raw-training absolute differences, without bridging gaps. Correlation is
diagnostic Pearson with empty/insufficient/constant reasons. Supplied quantile
pinball is max(q·(y−prediction),(q−1)·(y−prediction)); no quantiles are invented.
Lead/target weighted pooling and native training scales are covered by the
executed metric tests. F5 tiny squared-loss underflow remains an explicit limit.

The fresh mathematics reviewer independently worked a manual weighted example:
observed [[1,3,5],[2,4,6]], model [[0,5,2],[5,2,7]], zero persistence and lead
weights [1,2,0]. Positive-weight denominator is 6, absolute-error sum 12 and
squared-error sum 26, giving MAE=2 and RMSE=sqrt(13/3). Raw training [1,3,7,9]
gives scale 8/3, MASE=3/4. Persistence losses 17/6 and 55/6 give MAE skill 5/17
and MSE skill 29/55. Diagnostic Pearson over all six valid cells is
23/sqrt(2345); positive-weight loss count is four, correlation count six.
Quantiles y−2 at q=.2 and y+3 at q=.8 have pinball .4 and .6. These arithmetic
oracles were compared to the actual source formulas manually; their separate
execution was curtailed at the stop and is not claimed as a new runtime check.

Event source uses supplied valid AND mature masks; decisions and probabilities
are distinct. With TP=a, FP=b, FN=c, TN=d:

| Metric | Reviewed formula |
|---|---|
| Precision | a/(a+b) |
| Recall / POD | a/(a+c) |
| FAR | b/(a+b) |
| FPR | b/(b+d) |
| F1 | 2a/(2a+b+c) |
| TSS | a/(a+c)−b/(b+d) = (ad−bc)/((a+c)(b+d)) |
| HSS2 | 2(ad−bc)/((a+c)(c+d)+(a+b)(b+d)) |
| Brier | mean((probability−outcome)²) |

For hand counts (a,b,c,d)=(2,1,1,2), these give precision/POD/F1=2/3,
FAR/FPR=1/3 and TSS/HSS2=1/3. This is manual algebra against the current source,
not an additional executed confusion-table oracle. Empty masks produce null
with empty_mask; zero denominators produce null with zero_denominator; absent
decisions/probabilities have explicit reasons. No threshold, real flare label,
event-level matching, uncertainty or scientific skill is inferred.

The fresh mathematics review's separate literal/256-table/metric probe was
prepared but not executed before the R1 stop. No new exhaustive hand-oracle
runtime claim is made; ordinary tests are not described as an independent
external metric certification.

## 8. Provenance, publication and reproducibility

OBSERVED fresh source/package fingerprint:
`d7063a2cbfb126dd3593f77c24bb026458ff8eb7251f3bd3f1e2411f06389d51`.
It binds 35 source/config/package/schema files, not documentation or the
untracked Paperclip pointer. Installed provenance reports actual candidate
0f587d9, correct feature branch, tracked_dirty=false and only Paperclip untracked.
All 22 installed Python modules match checkout bytes and are classified as
installed_distribution; checkout/src is absent from the outside-checkout
interpreter's sys.path.

The effective training fingerprint binds canonical raw values/masks/times/
availability, declared spec, partition and retained origins/issues. Actual
runner tests reconstruct it independently, match fitted model records and
recompute seed semantic IDs from config/dataset/split/source/training+seed.
Different coherent value/mask fitting data change training identity; changes to
future-only data preserve effective training identity and numeric fit. The
global dataset/split identities can appropriately change. R1 does not refute
these fitting checks; it refutes causal validation of later prediction input.

Fresh scoped tests exercised deterministic synthetic fixture reruns, semantic
IDs versus distinct execution IDs, stable predictions/metrics/parameters/splits,
portable relative identities, and relocated artificial GOES preparation without
rewriting legacy sidecars. Runtime package/Python/platform are separate
provenance; seeds 17/29/43 are deterministic model tags, not stochastic fitting.
Final source/Git rechecks and ordinary source mutation/package mismatch controls
pass. F4 prevents claiming an unconditional tracked-input gate.

Fresh publication tests exercised exclusive no-replacement destination checks,
finite JSON staging, cleanup on failure and simultaneous thread writers with
one winner/one FileExistsError. macOS uses RENAME_EXCL; Linux/Windows code paths
were read, not executed in this environment. No cross-process stress,
parent-symlink race or power-loss durability claim. Indexed byte corruption and
extra regular files were freshly rejected; F3/F8 show the remaining structural
verification gaps. The SHA-256 index is an integrity check, not authentication
against an actor replacing both data and index.

Reproducibility levels for this re-audit:

| Level | Fresh evidence |
|---|---|
| Deterministic fixture reruns | Executed in targeted runner/provenance tests. |
| Semantic experiment IDs | Independently rebuilt/matched in executed producer test. |
| Selected byte-identical fixture artifacts | Executed rerun tests; scope limited to the artifact names those tests compare. |
| Full real synthetic/GOES acceptance pairs, eight stable JSON files each | NOT EXECUTED in this re-audit after R1; previous reports not reused as evidence. |
| Same-environment installed behavior | Outside-checkout imports/help/provenance and R1 installed reproduction executed. |
| Fresh independent dependency environment | NOT ESTABLISHED. Fresh project wheel was built, but dependencies are the existing environment. |
| Cross-platform/BLAS byte reproducibility | NOT ESTABLISHED. |

Execution timestamps/IDs/output/index-dependent bytes are not expected to match
whole directories. No whole-directory or rebuilt-wheel byte identity claim.

## 9. Fresh primary verification and actual counts

Executed in the candidate checkout:

```sh
.venv/bin/python -m pytest -q tests/test_training_slice_consistency.py
.venv/bin/python -m pytest -q tests/test_training_slice_consistency.py tests/test_forecasting_contract.py tests/test_forecasting_splits.py tests/test_forecasting_windows.py tests/test_baselines.py tests/test_trajectory_metrics.py tests/test_event_metrics.py tests/test_experiment_provenance.py tests/test_experiment_reference.py tests/test_experiment_runner.py
.venv/bin/python -m pytest -q
```

| Primary command | Observed outcome |
|---|---|
| New TrainingSlice module | 53 passed in 0.23s |
| Complete P1 targeted suite | 294 passed, 1 warning in 5.13s |
| Complete repository suite | 460 passed, 1 warning in 39.69s |
| Independent contracts reviewer scoped tests | 177 passed in 0.29s |
| Independent mathematics reviewer scoped tests | 110 passed in 0.18s |
| Independent provenance reviewer scoped tests | 58 passed, 2 installed checks deselected, 1 warning in 3.12s |
| Primary installed prediction-leakage probe | Exit 0 asserting invalid acceptance for deepcopy/pickle and all six baselines; negative constructor controls reject. |
| Independent prediction-leakage probe | Exit 0 asserting invalid acceptance via deepcopy/pickle/subclass; negative constructor control rejects. |
| Original F3/F4/F6/F8 reproduction | Exit 0 recording 17 failing/positive control outcomes; no repairs. |
| Primary F7 stale-parameter reproduction | 1.5→2, unchanged stored lookback 2, live lookback 1. |

The new module contributes 53 parametrized cases; actual remediation diff adds
one producer training-ID test in test_experiment_runner.py, accounting for the
claimed **54 new cases**. No new repository tests were added by this audit.
Counts from independent scopes overlap the primary suite and are not summed.

Both primary broader suites retained:

```text
tests/test_experiment_reference.py::test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability
<frozen importlib._bootstrap>:488: RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility. Expected 16 from C header, got 96 from PyObject
```

No warning filter was added. The warning is observed dependency behavior, not
proof of corrupted scientific source bytes. The fresh mathematics reviewer
result and stop-limited scope are recorded in the independent-review section.

## 10. Installation, CLI and acceptance status

OBSERVED outside checkout, with PYTHONPATH removed and bytecode disabled:

```sh
cd /private/tmp
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --help
```

Help exited 0. Ordinary package/forecasting/evaluation/runner imports and strict
code_provenance succeeded from that directory, resolving the package to
`.venv/lib/python3.13/site-packages`, not checkout/src. Current installed/source
parity was verified for all 22 modules. The CLI is a repository wrapper importing
the installed package; pyproject defines no installed console entry point. No
console-command packaging guarantee is claimed.

A fresh project wheel build was started before the finding. Initial sandbox
build dependency DNS failure was retried with approved escalation and completed:

```sh
.venv/bin/python -m pip wheel --no-deps . --wheel-dir /private/tmp/solarjepa-p1-reaudit-20261004/wheel
```

Wheel: solar_flare_jepa-0.1.0-py3-none-any.whl, 61,487 bytes, SHA-256
`459c46b86451bc49d9b1f2a6e73da172fb0a7f07d48872edaae20a0c7608fa04`.
Its 22 Python files exactly match current source; metadata/dependencies match
unchanged package declarations; no entry_points.txt exists. The wheel was not
installed into a fresh environment after the HIGH stop. Downloading setuptools
for build isolation was tool dependency verification, not science acquisition.
The pip sandbox cache warning and DNS failure are retained as environment limits.

Fresh bounded real synthetic/GOES acceptance pairs and their nine indexed output
files/eight stable artifact comparisons were not launched after R1. Real input
hash checks, artificial GOES adapter tests, producer fixture reruns, and scratch
corruption rejection were completed; those are not substituted for real
acceptance. Thus the previous acceptance claims remain historical reference,
not independently confirmed full acceptance claims for this checkpoint.

## 11. Preserved scientific state and gates

OBSERVED: the existing historical snapshot
`/private/tmp/solarjepa-p1-start-identities.json` contains exactly 109 path/hash
entries. Its own SHA-256 is
`3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193`.
Fresh content comparison gives **109 matched / 0 changed / 0 missing**:
one .agents, six configs, 70 data, 32 results. The selection includes incidental
placeholders/.DS_Store; it is not 109 separate scientific certificates or an
exhaustive historical-file inventory. Fresh comparisons are evidence; the
historical snapshot supplies the expected bytes.

Git independently shows 69 inherited main paths; only README and PROJECT_STATUS
are modified. A separately selected 43-path scientific/config/package/gate/
SoLEXS-test scope matched main blobs, candidate blobs and actual working bytes.
Its path list is retained in scientific-preservation.json. This selection differs
from the old reviewer's 48-path scope; no claim those scope counts are identical.
All inherited scientific manifests/readers/configs/gate docs and package metadata
are unchanged in the complete Git diff. Frozen P1 research/design documents are
unchanged from 805f1c3.

Read-only actual verification:

- Three avg1m and three flsum files pass verified_manifest_paths against
  configs/data/noaa_sample.json; total 1,002,585 bytes.
- Preserved Parquet SHA-256:
  `cc197f8186e0ec15b8ababd5a8c5549349d10fd15112cf4320ca4f23c114c068`.
- Installed `scripts/register_aditya.py --verify` verifies two registered
  SoLEXS archives, without registration, extraction or writes.
- Actual D.1 evidence and requirements gates are BLOCKED_FOR_PHASE_E; actual
  Phase E requirements gate is BLOCKED. Calibration application and product
  clock conversion approvals remain false.

Required unresolved gates still include version-applicable SoLEXS timing,
LC bin semantics, continuous GTI/exposure policy, approved correction state,
compatible HK/parameters if required, PI/response channel-energy mapping/gain,
date/software calibration compatibility, and scientifically defined alignment
and real events. Native SoLEXS code retains its no-UTC/no-GTI/no-calibration
interpretation and warning boundaries. P1 dataset role validation excludes
SoLEXS; runner marks Phase E blocked and real events/ARCH-GARCH/neural training
deferred. There is no new authoritative evidence or basis to weaken those gates.

DOCUMENTED historical instrument assertions remain attributed in unchanged
manifests. OBSERVED here is byte continuity and executable refusal/role/gate
behavior. INFERRED is preservation of the prior scientific checkpoint; UNKNOWN
remains mission semantics not resolved by new evidence. GOES tests do not make
SoLEXS ready. July 2 remains missing_from_obtained_collection, without inference
of mission-wide absence, filling, or a scientific negative label. Full real
FITS/PI/calibration diagnostics were not rerun; no new science was acquired.

## 12. Fresh integration simulation

Executed without changing any protected ref/index/worktree:

```sh
git merge-base main HEAD
git merge-base --is-ancestor 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe 0f587d96d09583e3f7d15ce5b3d40145264e1ab6
git merge-tree --write-tree 1a4991da4dda9676caeb1d7e35a03408528c3188 0f587d96d09583e3f7d15ce5b3d40145264e1ab6
git rev-parse HEAD^{tree}
git diff --check main...HEAD
```

Object-only merge-tree returned
`7d795f428bad79986a26708b268a31ca38d69b41`, exactly candidate's tree; no conflicts.
Main is the merge base, so integration is topologically a fast-forward retaining
research/remediation history. Initial sandbox object-write refusal was retried
with permission; only temporary merge objects were allowed, no branch movement.
Whitespace checks pass. No dependency changes or scientific/config changes are
introduced; packaging discovery includes the new core modules in the verified
wheel. Full tests retain existing behavior within the observed 460-case suite.

Clean integration mechanics do not approve the known causality failure. The
candidate must not be integrated under this audit result.

## 13. Independent reviews and workflow effects

Three fresh bounded reviewers were spawned with isolated task context and
read-only checkout instructions, without inheriting remediation conclusions:

| Reviewer attention | Actual evidence |
|---|---|
| A: TrainingSlice/contracts/leakage/subclasses | Current and historical code diffs, 177 scoped tests, copied/pickled/sibling prediction attack and rejecting canonical controls. Found R1. |
| B/C: baselines/mathematics/evaluation | Actual baseline/metric source and tests, focused metric/baseline suite; independent literal probe prepared but not launched at stop. |
| D: config/provenance/fingerprints/reproducibility | Actual code/schema/CLI/tests, 58 scoped passes and 17 fresh F3/F4/F6/F8/control outcomes. |
| Primary E/F: Git/integration and scientific preservation | Fresh fetch/refs/history/complete diff, raw/index/ignore checks, source/wheel/installed checks, 109 hash comparisons, 43 scoped blob comparisons, six NOAA inputs, SoLEXS read-only inventory and gate manifests, object-only merge simulation. |

The primary independently reproduced R1 with installed modules, all-six
prediction acceptance and negative constructor controls; it did not merely
accept a reviewer summary. No subagent was allowed to fix source, trust docs as
ground truth, acquire data, move shared refs or spawn another reviewer. Checks
left unexecuted at the stop are explicit rather than silently counted as passed.

Superpowers using-superpowers, requesting-code-review/template and
dispatching-parallel-agents established scoped independent review with actual
SHAs, no shared edits and explicit declined checks. Systematic debugging used
trace-through-input-consumption, ordinary copy/pickle reconstruction, a sibling
constructor variant, installed repeat and canonical rejection controls to
establish why a passing suite missed R1. Implementation/fix steps were withheld
under audit-only scope. Verification-before-completion required fresh counts,
ref/hash verification and package parity before claims; the readiness verdict
changed on executable evidence despite passing tests and prior remediation.

## 14. Warnings, limitations and discrepancies

R1 is the one new HIGH finding. No separate BLOCKER-level Git/data-loss condition
was observed. F2's prediction consequence is blocking through R1; F3–F9 are not
erased, repaired or unconditionally accepted. Medium/low dispositions are bounded
by current controlled P1 workflows, not future science/API readiness.

The remediation's 294/460 counts and 54 new cases are corroborated by fresh tests
and diff evidence. Its 109 identities are independently matched. Installed/source
parity is corroborated; prior real acceptance pairs and eight-artifact byte
identity are not claimed freshly rerun. Its statement of no BLOCKER/HIGH in a
fitting-focused closure review remains a historical scoped result, and does not
establish prediction safety. R1 is new evidence requiring another correction.

Remaining limits: no independent fresh dependency environment or cross-platform
reproduction; no real scientific skill/event validation; no exhaustive Python
extension/tampering proof; no complete containment/clean-track guarantee because
of F3/F4; bounded numeric/metadata/type edges remain; existing ABI warning
retained; real acceptance and additional adversarial families curtailed by stop.
No unsupported scientific clock/calibration/event semantics were inferred.

## 15. Local evidence and publication state

Primary evidence: `/private/tmp/solarjepa-p1-reaudit-20261004/` contains
initial-state.json, candidate-complete.diff, candidate-inventory.txt,
targeted-tests.log, full-tests.log, primary-prediction-leakage.json,
f7-current.json, scientific-preservation.json, installed-provenance.json,
fresh-wheel-verification.json and the wheel.

Independent evidence:

- `/private/tmp/solarjepa-p1-reaudit-contracts/REPORT.md` and prediction_probe.py.
- `/private/tmp/solarjepa-p1-reaudit-provenance/report.md`, original_findings.py,
  original-findings.json/.log and the two malformed CLI stderr logs.
- `/private/tmp/solarjepa-p1-reaudit-math/` focused log and prepared, unexecuted probe.
  Its report.md records 110 scoped passes, manual oracles and declined probes.

These scratch paths are local evidence, not durable published artifacts. The
decisive reproduction and numerical observations are therefore embedded here.
No report-only commit or push is permitted under the user's HIGH-found condition.
Audited implementation and resulting branch HEAD both remain 0f587d96; main and
research refs remain pinned. This report and Paperclip are untracked; tracked
source/tests/config/scientific files remain unchanged.

## 16. Eventual human integration procedure — currently gated

There is **no recommended integration of 0f587d96 under this rejected audit**.
Stop for human review of R1. Corrective work needs authorization, followed by
another fresh integration-readiness audit. Preserve both feature/research
milestone branches and meaningful commits. No commands below were executed.

After a future passing audit, a human must set P1_REVIEWED_SHA to that exact
reviewed candidate (including any verified documentation-only audit commit),
never silently to a moving branch or this rejected revision. Stop if main or
research differs from the expected baseline; do not reset or rebase around it.

```sh
cd /Users/nealsalian/Desktop/SolarJEPA
git fetch origin
P1_REVIEWED_SHA=REPLACE_WITH_FUTURE_PASSING_AUDIT_40_CHARACTER_SHA
test "${#P1_REVIEWED_SHA}" -eq 40 || exit 1
test "$P1_REVIEWED_SHA" != 0f587d96d09583e3f7d15ce5b3d40145264e1ab6 || exit 1
test "$(git rev-parse main)" = 1a4991da4dda9676caeb1d7e35a03408528c3188 || exit 1
test "$(git rev-parse origin/main)" = 1a4991da4dda9676caeb1d7e35a03408528c3188 || exit 1
test "$(git rev-parse research/experiment-evaluation-foundation)" = 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe || exit 1
test "$(git rev-parse origin/research/experiment-evaluation-foundation)" = 805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe || exit 1
test "$(git rev-parse feat/p1-experiment-evaluation-foundation)" = "$P1_REVIEWED_SHA" || exit 1
test "$(git rev-parse origin/feat/p1-experiment-evaluation-foundation)" = "$P1_REVIEWED_SHA" || exit 1
git diff --exit-code || exit 1
git diff --cached --exit-code || exit 1
git status --short --untracked-files=all
# Stop on unexpected paths; never add .agents or ignored scientific/results files.
git diff --check main..."$P1_REVIEWED_SHA" || exit 1
git merge-base --is-ancestor main "$P1_REVIEWED_SHA" || exit 1
git merge-tree --write-tree main "$P1_REVIEWED_SHA" || exit 1
# ONLY after explicit human authorization for this exact merge:
git switch main
git merge --ff-only "$P1_REVIEWED_SHA"
test "$(git rev-parse main)" = "$P1_REVIEWED_SHA" || exit 1
git diff --check
git status --short --branch
```

If protection requires a user-managed PR, use that route, preserve commit history,
avoid squash/rebase and leave milestone branches intact. Any agent push to main
requires separate explicit authorization; merge approval is not push approval.

```sh
# ONLY after separate explicit authorization to push main:
git push origin main
git fetch origin
test "$(git rev-parse origin/main)" = "$P1_REVIEWED_SHA" || exit 1
git branch -avv
```

Current stop: R1 HIGH is unresolved; no fixes, integration, main push, feature
report commit/push, branch deletion, Phase E, SolarJEPA training, ARCH/GARCH or
scientific acquisition was performed. Await explicit human review.
