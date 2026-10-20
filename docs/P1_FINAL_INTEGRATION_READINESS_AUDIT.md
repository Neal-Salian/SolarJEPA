# P1 final fresh integration-readiness audit

Date: 2026-10-05. Repository: SolarJEPA. Audit only, after R1 remediation.

**Decision: NOT_READY_FOR_INTEGRATION.** One new **HIGH** finding, N1, was
independently reproduced by a fresh reviewer and the primary auditor. Numeric
categorical objects survive the canonical snapshots with behavior that their
JSON fingerprints omit. Identical spec/effective-training identities select
different transformations and fitting data; an operational identity also admits
retrospective prediction inputs without actual availability. No repair was made.

The original F1 raw/window inconsistency and the original R1 shifted-future-bin
reproducer are closed in the cases freshly exercised here. Their closure does
not establish the stronger semantic-consumption invariant defeated by N1.

Under the user's HIGH stop rule, fresh full-suite/acceptance pairs and integration
simulation were not launched after the finding. Historical passing counts and
acceptance results are not substituted for fresh verification. This report is
local and **uncommitted**; nothing was pushed. Protected main, the feature HEAD,
and the research milestone remain unchanged.

## 1. Exact identities and Git topology

| Role | Exact identity observed locally and, where applicable, on origin |
|---|---|
| Protected main | `1a4991da4dda9676caeb1d7e35a03408528c3188` |
| Pre-audit feature HEAD | `8fa3877f66264ab2f9309c8f5a3aa7fa225df224` |
| Audited implementation | `009547932e398edeef1bd2ede2ff3d10bc9e1862` |
| Frozen research/design checkpoint | `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe` |
| Previous pre-R1 implementation checkpoint | `0f587d96d09583e3f7d15ce5b3d40145264e1ab6` |
| Previous failed original-audit implementation | `11b72bb0c714cf71edf1e5ccb390d38444bbb8c8` |
| Post-audit documentation commit | **None created**; feature remains `8fa3877f66264ab2f9309c8f5a3aa7fa225df224` |

OBSERVED: `git fetch origin` succeeded. Origin is
`https://github.com/Neal-Salian/SolarJEPA.git`. Local and origin feature match,
with upstream divergence **0/0**. Local/origin main and local/origin
`research/experiment-evaluation-foundation` match the specified identities.
The merge base of main and feature is exactly main. Research, `0f587d9`, and
`0095479` are ancestors of feature HEAD. There are 19 commits in `main..HEAD`.

The relevant actual history, in order, is:

```text
1a4991d protected main
  -> 805f1c3 frozen research/design
  -> c218969 approved P1 implementation plan
  -> 8154954 immutable interval contracts
  -> a41904a chronological partitions/windows
  -> fcb928e six deterministic baselines
  -> d84d401 trajectory/event evaluation
  -> 8c0c0a0 provenance/publication
  -> ddcdb6d origin guards
  -> c83b537 support/metadata guards
  -> 2162465 runner/GOES/CLI
  -> 11b72bb original implementation report
  -> 6868a25 preserved failed original audit
  -> b5ae4c6 raw/window consistency remediation
  -> 8ba57aa canonical fitting validators
  -> 0f587d9 TrainingSlice remediation documentation
  -> 990d6f3 preserved failed R1 re-audit
  -> 5048d42 failing prediction-context regressions
  -> 0095479 canonical prediction snapshots
  -> 8fa3877 R1 remediation/status documentation = local/origin feature
```

`0095479..8fa3877` changes only README and three P1/status documents. Source,
tests, configuration, schema, and package behavior at feature HEAD are therefore
the audited implementation's tree for those paths. No unexpected ancestry,
main modification, branch deletion, rebase, squash, history rewrite, or remote
mutation was observed or performed.

## 2. Method, actual skills, and independent review

Actual source, tests, JSON configuration/schema, runner/CLI, packaging metadata,
Git refs/history/diffs, installed file locations, file hashes, and fresh execution
provided evidence. Historical reports and README were supporting context.

| Workflow actually read and applied | Effect on this audit |
|---|---|
| Superpowers using-superpowers and its Codex tooling reference | Established the relevant workflows and kept the explicit audit-only restrictions above implementation defaults. |
| requesting-code-review and reviewer template | Assigned fresh reviewers exact code/commit targets and explicit adversarial questions; required evidence rather than summaries of remediation. |
| dispatching-parallel-agents | Bounded independent domains, with read-only repository access and scratch-only outputs. No shared implementation writers. |
| systematic-debugging | Traced the new categorical defect through construction, reconstruction, JSON hashing, fit, and predict. Used valid/malformed controls and two independent fixtures. Stopped before a fix phase. |
| verification-before-completion | Required fresh results and actual loaded file identities; prevented historical test counts, acceptance pairs, or an unperformed simulation from becoming success claims. |

Three fresh reviewers did not implement F1 or R1:

| Reviewer | Executable evidence inspected and generated |
|---|---|
| `final_audit_boundaries` | Contracts, partitions/windows, all six fit/predict paths, tests and historical code; 327 scoped tests; 159 labeled checks; original R1 sensitivity; discovered N1. |
| `final_audit_mathematics` | Baselines, both evaluators, actual runner flow, 122 scoped tests, literal/rational/Decimal calculations, 60 trajectory cases, 625 confusion tables, failure/coverage cases. |
| `final_audit_provenance` | Config, fixture/reference adapters, provenance, schema, CLI, source/package metadata, 59 scoped tests, temporary Git roots, identities, corruption, relocation and multi-process publication. |
| Primary auditor | Git/integration safety, historical chain, scientific gates/preserved files, installed parity, 238 F1/R1 regressions, independent N1 reproduction including genuine IntEnum and post-snapshot aliasing. |

Scientific/reproducibility review used the repository's scientific-integrity
rules and actual manifests/code/hashes. No separate unavailable scientific skill
or new instrument validation is claimed. **DOCUMENTED** refers to an attributed
requirement; **OBSERVED** to execution/file evidence; **INFERRED** to its derived
implication; **UNKNOWN** remains unestablished.

## 3. Complete main-to-feature inventory and preserved tooling

OBSERVED: the complete `git diff main...HEAD` has **38 additions and 2 modified
files**, 40 paths, **8,937 insertions and 37 deletions**. No deletion, rename,
dependency/packaging-metadata modification, or binary scientific addition is
present. The entire diff was retained and inspected. The historical 29-addition
inventory was relative to frozen research at the earlier implementation; its
original main diff included three additional research documents. Neither count
describes this remediated 40-path integration tree.

```text
M README.md
A configs/experiments/p1_goes_reference.json
A configs/experiments/p1_synthetic.json
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
```

Git tree/history inspections found no committed scientific ZIP/FITS/NetCDF/
Parquet/NumPy arrays, model checkpoints, or generated experiment outputs.
Existing reader code, dependency lock, pyproject, scientific configuration,
manifests, and validation gates are unchanged. The two experiment configurations
and result schema are intentional P1 additions, not replacements of frozen
scientific configuration.

The only initial untracked file was `.agents/skills/paperclip/SKILL.md`. It remains
untracked and byte-identical, SHA-256
`4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`.
Setuptools discovers packages under `src`; pytest's declared path is `src`;
the CLI imports the package and does not read this Markdown. The installed
module/source parity and unchanged source identity provide no evidence of a
package, numerical, scientific, or installation effect from it. It can appear
in recorded untracked-tooling Git metadata; that is not an effective data input.
It was not invoked, edited, staged, or committed. This new audit report is the
sole intended additional untracked repository file.

## 4. Fresh disposition of every historical finding

These dispositions concern the exact historical mechanisms. They do not imply
universal contract safety or approval of the new HIGH. No new user acceptance
of a remaining limitation is invented.

| Finding | Severity | Fresh disposition | Current executable evidence and bounds |
|---|---|---|---|
| F1: contradictory raw/window fitting support | HIGH, historical | **RESOLVED** for the original numerical join defect | 53-case TrainingSlice module and all-six independent fit attacks reject mismatched values, masks, availability, coordinates, support and subclass validators; coherent numerical changes change effective identity. N1 is a separate semantic identity defect between otherwise numerically consistent slices. |
| F2: writable deep-copy/pickle contract arrays | MEDIUM | **STILL_OPEN_NONBLOCKING** for ordinary array writability alone | Eight fresh copy/serialization checks reproduce writable buffers. All-six model-consumption sentinels prove immutable detached arrays are consumed and caller-array mutation cannot alter them. Do not claim copied objects themselves remain universally immutable. N1 independently blocks nested semantic metadata safety. |
| F3: incomplete artifact tree/symlink verification | MEDIUM | **STILL_OPEN_NONBLOCKING** | Dangling symlink, external directory symlink and external index symlink still pass. Indexed corruption and extra regular files reject; private-stage regular producer, relocation and exclusive winner controls pass. Complete containment cannot be claimed. |
| F4: Git-quoted untracked-source path gate | MEDIUM | **STILL_OPEN_NONBLOCKING** | Scratch untracked `scripts/é.py` is Git-quoted and accepted; ASCII control rejects. Its bytes are nevertheless included in the source hash and its quoted name recorded. No omitted-content collision reproduced; real candidate has no such source file. |
| F5: squared-loss underflow | MEDIUM | **STILL_OPEN_NONBLOCKING** | Fresh errors `1e-170` and `1e-200` produce false RMSE zero and a false zero-reference-loss reason, although RMSE/error ratio are representable. Ordinary literal/rational cases pass. This remains a real extreme-range correctness defect, not an accepted universal metric guarantee. |
| F6: duplicate dataset metadata JSON keys | LOW | **STILL_OPEN_NONBLOCKING** | Duplicate keys collapse to last value and fingerprint as that canonical object. Normal configuration/sidecar parsing rejects duplicates; generated adapter metadata has no duplicate keys. Caller metadata ambiguity remains. |
| F7: explicit caller mutation of fitted settings | LOW | **STILL_OPEN_NONBLOCKING** | Changing a fitted trailing lookback changes predictions while its recorded parameter remains old. Requires explicit mutation of the estimator; normal private runner does not do this. N1 needs no estimator mutation for its principal identity collision. |
| F8: malformed numeric/JSON/index type handling | LOW | **STILL_OPEN_NONBLOCKING** | Oversized alpha/weight produce TypeError/OverflowError and CLI tracebacks with no output; `1e400` parses as infinity; boolean artifact version accepts and null index entries raise TypeError. Some ordinary controls now reject correctly. Normal producer emits finite integer-versioned artifacts. |
| F9: avoidable dimensional-log intermediates | LOW | **STILL_OPEN_NONBLOCKING** | Finite true log coordinates ±400 and finite inverse results are refused after intermediate overflow/underflow. Ordinary dimensional controls pass. Explicit failure, not a fabricated successful forecast. |
| R1: copied/subclassed context exposes future bins | HIGH, historical | **RESOLVED** for the original coordinate/availability route | Five reconstruction routes × six models reject the old future-shifted context. Private loading of `0f587d9` confirms old all-six admission and Persistence `[11,12]`; current valid result is `[10,11]`. N1 is a distinct availability-policy identity hole. |
| N1: non-string category hooks omitted from identity | **HIGH, new** | **BLOCKING** | Exact-base reconstructed specs retain numeric equality hooks. Two fitting transforms share effective identity and produce materially different mean/Ridge fits; all six admit unknown availability under an operational fitted identity; a caller metadata alias also survives snapshot capture. |

F3-F9 were re-executed by fresh independent reviewers, rather than carried forward
because earlier remediation focused on F1/R1. Their severities reflect the
demonstrated mechanisms and bounded normal producer behavior. They remain open.

## 5. N1 HIGH: primitive categorical semantics are not canonical

### Boundary and root cause

`ForecastSpec` annotates `availability_mode`, `eligibility_policy`, and
`transform` as strings but validates them by membership/equality only
(`contracts.py:167-172`). `_canonical_fields` converts actual string subtypes
to their base string representation, recurses through ordered containers, and
otherwise returns the original object (`contracts.py:23-38`). It does not
require categorical fields to become plain permitted strings.

An `int` subclass or genuine `IntEnum` can therefore implement equality against
`'identity'`, `'log10'`, `'operational'`, or `'retrospective_bin_end'` and survive
exact-base `ForecastSpec` reconstruction. `canonical_json` serializes its
underlying integer **0**, whereas validation and model transforms use its
overridden equality semantics. Fingerprinting loses effective meaning. This is
an omitted-semantic-state collision, not a cryptographic SHA-256 collision.

The common fit boundary reconstructs TrainingSlice and uses it for model
fitting and recording (`baselines.py:56-91`). The common prediction boundary
reconstructs context/spec/grid and passes the reconstructed context to `_predict`
(`baselines.py:100-127`). Those are real protections for arrays and the original
F1/R1 exploits. Both reconstruction paths still retain these category objects.

### Independent reviewer reproduction

The reviewer used ordinary public ForecastSpec/TrainingSlice construction and
`fit`/`predict`, with a numeric category carrying a string meaning. No model
monkeypatch, concurrent mutation, subclassed model, or pickle execution was
needed for this identity-collision reproduction. A 12-row geometric fixture
gave identical raw support and retained origins for native/log variants:

| Evidence | Native identity semantics | Log10 semantics |
|---|---|---|
| Serialized transform | `0` | `0` |
| Spec fingerprint | `c97c387f91e1a155fdce4baa8d12dea74cc75c8bea33614911f38c609201e7d5` | Same |
| Effective training fingerprint | `89cdba2e0d1a70addaf608be8a48815061457c51e6b0edad069e6faa02b9cd14` | Same |
| TrainingMean first forecast | `31.875` | `11.31370849898476` |
| DirectRidge first forecast | `4.00135034291604` | `4.433034516116853` |

The primary independently executed that reproduction and observed the same
results, then wrote a separate genuine-IntEnum fixture rather than relying only
on the reviewer's custom numeric class.

### Genuine IntEnum reproduction and effective Ridge fitting data

Primary fixture: native values
`[2,3,5,7,11,13,17,19,23,29,31,37]`, one-second cadence, context length two,
horizon one, train `[0,8s)`, dimensional references one. Publicly constructed
native and log slices pass canonical raw/window validation. Their declared
dataset/split, raw values, masks, availability and coordinates are equal.

Spec identity remains `c97c387f...`; both training identities are
`f319c080554a0c7c91f825b98f043df4e8ce949c81c2a149df9b23c6134a6bf9`.

| Consumed/fitted result | Native IntEnum | Logarithmic IntEnum |
|---|---:|---:|
| TrainingMean fitted transformed mean | 9.625 | 0.8733447318162606 |
| TrainingMean native forecast | 9.625 | 7.470415055041088 |
| Ridge coefficient, lag one / alpha 0.1 | 1.0184078412622521 | 0.6304265516090046 |
| Ridge intercept | 2.4948601482189794 | 0.4666510780152532 |
| Ridge first native forecast | 5.550083672005735 | 5.8538418522175695 |

Both fitted parameter records contain the same spec/training fingerprints and
serialize `transform` as `0`. Ridge actually transforms the fitting window
features and targets differently (`baselines.py:288-305`); this is not merely
a label difference or posthoc evaluation change.

### Availability-policy collision, all six baselines

Genuine Operational and Retrospective IntEnums, both numerically zero, have
identical spec identity
`ee7691222c73f9abce9ab935d8342dc51e615dfe83e1aa7cfc08e702b7017341`.
Each model fits valid known-availability operational training. A retrospective
prediction spec with `availability_ns=None` then passes alignment and fitted
spec identity checks. **Persistence, training mean, trailing mean, drift, AR(1),
and direct Ridge all reach model logic and return finite predictions.**

An observer at `_predict` verified that the consumed object is the reconstructed
exact-base ForecastContext with unknown actual availability; it delegated to
the actual algorithm. The earlier independent reviewer also reproduced this
policy admission with unmodified Persistence and a numeric category.

This does not prove a measured post-issue delivery time for those toy values;
it proves actual delivery is **UNKNOWN** yet accepted under the same fingerprint
as an operational spec that requires known delivery. It is a causality-policy
identity failure, distinct from the old literal future-interval exploit.

### Validation/use separation: retained caller metadata alias

The primary also used a mutable numeric category with underlying zero and a
caller-owned `meaning`. After fitting TrainingMean, prediction snapshot capture
retained `snapshot.spec.transform is caller_token` and
`model._spec.transform is caller_token`. An observer immediately before actual
model consumption changed only `caller_token.meaning` from identity to log10.
It delegated to the original algorithm. Prediction changed from **9.625** to
**4216965034.2858224**. The recorded parameters' JSON and spec fingerprint
remained identical.

This is an instrumented after-capture timing probe, not an assertion that the
ordinary runner automatically mutates metadata or that all concurrent races
were tested. It directly establishes caller alias retention across the claimed
detachment boundary. The principal mean/Ridge and policy-collision evidence
above requires no such observer or mutation.

### Scope, controls, and severity

Twelve ordinary malformed controls (`0`, `0.0`, `True`, `'IDENTITY'` for the
three categorical fields) reject. Valid StrEnum identity normalizes to plain
`str` and preserves legitimate identity. Actual string subtype, units, names,
origin/identity and fitted transform controls pass. The missing adversarial
class is a **non-string numeric object with behavioral category equality**.

Normal JSON configurations cannot encode this custom Python equality behavior;
no pinned CLI acceptance run or real scientific result is claimed exploited.
The public Python contracts and common all-six model boundaries do accept it.
The user's audit explicitly requires primitive/enum-like normalization,
effective identity, and no equivalent consumption-boundary bypass. Identical
effective fitting identity for different transformed data, plus operational
policy admission, makes this **HIGH** within that contract. No repair, silent
normalization, dropped input, or model-specific patch was applied.

## 6. Reproducible N1 public-API control

The following self-contained synthetic control illustrates the principal
identity defect. It does not acquire or modify scientific data. Run with the
audited package/source; successful assertions establish the defect, not safety.

```python
from dataclasses import fields, replace
from enum import IntEnum
import numpy as np
from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows

class Native(IntEnum):
    VALUE = 0
    def __eq__(self, other):
        return other == 'identity' if isinstance(other, str) else int.__eq__(self, other)
    __hash__ = int.__hash__

class Logarithmic(IntEnum):
    VALUE = 0
    def __eq__(self, other):
        return other == 'log10' if isinstance(other, str) else int.__eq__(self, other)
    __hash__ = int.__hash__

ns = 10**9
starts = np.arange(12, dtype=np.int64) * ns
values = np.array([2.,3.,5.,7.,11.,13.,17.,19.,23.,29.,31.,37.])[:, None]
mask = np.ones_like(values, bool)
dataset = TimeSeriesDataset('primary_primes', 'synthetic_fixture', starts,
    starts+ns, values, mask, values, mask, ('x',), ('x',), ('u',), ('u',), 1,
    starts[:, None]+ns)
plain = ForecastSpec(1, 2, 1, ('x',), ('x',), ('u',), ('u',),
    feature_reference=(1.,), target_reference=(1.,))
train = build_partition_windows(dataset, plain,
    TemporalPartition('train', 0, 8*ns)).training_slice
declarations = {f.name: getattr(plain, f.name) for f in fields(ForecastSpec)}
slices = []
for category in (Native.VALUE, Logarithmic.VALUE):
    spec = ForecastSpec(**(declarations | {'transform': category}))
    slices.append(replace(train, context=replace(train.context, spec=spec),
        targets=replace(train.targets, grid=replace(train.targets.grid, spec=spec))))
assert slices[0].spec.fingerprint == slices[1].spec.fingerprint
assert slices[0].fingerprint == slices[1].fingerprint
for name, parameters in [('training_mean', {}),
                         ('direct_ridge', {'lag_steps': 1, 'alpha': .1})]:
    models = [make_baseline(name, parameters).fit(t) for t in slices]
    forecasts = [m.predict(t.context, t.targets.grid).values
                 for m, t in zip(models, slices)]
    assert models[0].parameters['training_fingerprint'] == models[1].parameters['training_fingerprint']
    assert not np.allclose(forecasts[0], forecasts[1])
    print(name, forecasts[0][0,0,0], forecasts[1][0,0,0])
```

The executed primary probe extends this with the all-six policy collision,
ordinary malformed controls, StrEnum control and after-capture alias observation.
Its results and source are retained under the evidence directory in section 20.

## 7. F1 fitting trust boundary and requirement traceability

The common fit path reconstructs a TrainingSlice before `_fit`; its constructor
reconstructs nested exact-base context/spec/targets/grid. Raw support is checked
for partition membership, cadence/uniqueness, dependency coverage, positive
declared bounds and target maturity. Window coordinates join canonical raw rows
with `searchsorted`; masks and values must equal canonical eligible support,
including NaNs in false cells (`contracts.py:486-577`). Actual availability
must match raw support and masks derived at each issue time.

| Requirement | Implementation and actual test/evidence |
|---|---|
| Reject contradictory window feature/target values and masks | Canonical join at `contracts.py:560-577`; executed `test_window_value_mutation_is_rejected_before_fitting`, mask upgrade/downgrade, finite false-payload and repeated-coordinate regressions. |
| Reject availability, coordinates and dependency contradiction | Support/availability checks at :511-569; complete TrainingSlice module and independent malformed raw support/availability/lookback tests. |
| Reject copied/subclassed validator bypass before every fit | Exact-base nested construction at :498-504 and common fit :62; all-six copied and overridden-subclass regressions. |
| Coherent numerical changes get different identity | TrainingSlice effective payload at :591-599; joint value/mask identity tests and independent ordinary runner reconstruction. |
| Canonically derived slices and all six algorithms remain valid | Literal all-six fit/predict regression controls pass. |
| Held-out future perturbation cannot change fit inputs/output | Executed all-six TrainingSlice future-perturbation cases and baseline held-out tests. |

OBSERVED: **53 TrainingSlice regression cases passed** as part of the primary's
238-case F1/R1 run. Independent attacks also cover support, masks, availability,
partition and subclass variants. The original F1 numerical contradiction is
rejected before Ridge row selection. **N1 defeats the stronger effective
semantics/identity claim despite these numerical joins**; no universal fingerprint
correctness conclusion is drawn from the 53 passing cases.

## 8. R1 prediction boundary, copies, and validation/use separation

`ForecastContext` requires exactly the declared completed past grid ending at
issue time. Supplied availability for true cells must be at least bin end and no
later than issue time (`contracts.py:350-369`). FutureGrid holds only future
coordinates/spec/identity/origins, with no realized target values or masks.
Common predict reconstructs both declared specs independently, context and
grid, checks alignment and fitted dataset/spec identity, and calls `_predict`
with those reconstructed variables (`baselines.py:112-124`).

Fresh observer controls prove the actual model logic receives detached exact-base
context/grid arrays rather than merely validating a discarded object. Mutation
of original array buffers after capture does not change these inputs. Returned
grid arrays are detached and immutable. Subclass methods/cached realized-target
fields are excluded from the declared snapshot. Genuine string subtype hooks
are stripped by primitive reconstruction.

Fresh original-exploit sensitivity uses ramp values 1..12:

| Code/route | Observed result |
|---|---|
| Current valid Persistence at the two test origins | `[10,11]` |
| Current shallow copy, deepcopy, pickle, `__new__`, unchecked sibling subclass with shifted future context, all six models | Deterministic rejection; no leaked forecast |
| Read-only historical `0f587d9` package loaded in scratch, same malformed context | All six admit it; Persistence `[11,12]` |

The primary executed **185 prediction-context regressions**, including future
interval/availability, origin/grid/mask/spec mutation, replacement, subclass
overrides, detached use, and target-free grid controls. This module plus the
53 fitting regressions gives the observed 238, without assuming the larger
reported test counts. The historical 186-case increment consists of this module
and an additional runner regression; it is not a fresh standalone 186-test run.

**Remaining separation defect:** N1's non-string categorical fields stay aliased
even when the context and arrays are reconstructed. The old future-coordinate
reproducer is closed; a general claim of fully primitive, detached semantics is
false. The after-capture observation and policy collision in section 5 are the
specific counterexamples.

## 9. Primitive normalization, units, and identities

The fresh boundary review exercised 24 primitive/identity/fit controls: valid
`numpy.str_`, StrEnum, misleading string subtype hooks, integer scalar lengths,
reference scalar values, units, dataset/split identity, and all-six fit records.
The primary additionally exercised 12 plain malformed categorical controls and
a legitimate StrEnum identity equivalence. These ordinary controls pass.

String fields in canonical fit/predict snapshots use base string content;
distinct valid unit/spec labels do not evade the fitted identity comparison in
the exercised controls. Case is significant for category literals; there is no
documented scientific unit alias/case-folding system. Feature/target counterpart
name/unit equality is checked. Physical correctness of caller-declared units is
not authenticated or inferred by this contract.

N1 shows the normalization is incomplete for **non-string behavioral numeric
categories**. Their underlying numeric representation collapses identity while
models execute different semantic comparisons. No claim of arbitrary custom
object canonicalization or all primitive subclass combinations is supported.

## 10. Six-baseline mathematical review

Fresh independent calculations use literal arrays and algebra, not previous
reports or expected values copied from model internals. All ordinary-string
spec controls agree with the implemented definitions:

| Baseline | Independent representative calculation and result |
|---|---|
| Persistence | Last valid counterpart in `[4,7,10]` gives `[10,10]`; masking newest gives `[7,7]`. Feature/target dimensional references may differ; the native target counterpart remains correct. |
| Unique-training-period mean | Unique raw `[2,4,6,8,10,12,14]` gives 8, without repeated-window weighting. Log values 10 through 10^7 average in transformed space and inverse to 10^4. |
| Trailing mean | Last two `[7,10]` give 8.5; masks use valid cells inside declared trailing support. Log counterpart average inverses to a geometric mean. |
| Drift | First/last valid values in `[4,7,10]` imply three units per cadence, yielding `[13,16]`. Missing newest retains actual elapsed times and the same future endpoints. |
| Fixed AR(1) | `[1,5,13,29,61,125,253]` has intercept 3 and coefficient 2, forecasting `[509,1021]`. Invalid/gapped pairs are excluded; a stale valid initial state is advanced to each actual future end. |
| Direct Ridge | Centered X `[-1,1,3]`, Y `[5+2X,-2+3X]`, Sxx=8 and alpha=4 give slopes `[4/3,2]`, intercepts `[17/3,-1]`, forecast X=5 `[37/3,9]`. Alpha zero gives `[15,13]`; a single training sample with regularization gives constant `[7,11]`. |

Implementation is at `baselines.py:141-317`. Ridge uses centered augmented
least squares with a sqrt(alpha) penalty and an unpenalized intercept; it fits
complete fixed-horizon training windows. Mean and AR(1) use unique raw permitted
training support. None performs online fit to realized forecast targets.

All six share the canonical fit and predict boundaries; runner fits from train,
predicts with context/grid and evaluates after predictions are fixed. Ordinary
future perturbations do not alter parameters or forecasts. **This ordinary
mathematical correctness is bounded by N1 and the open F7/F9 limitations.** It
does not certify a physical model, event definition, or scientific forecast skill.

## 11. Trajectory and event mathematics

For errors `[-1,-3,4,-1]` with lead weights `[1,3]`, independent reductions give
MAE `17/8`, RMSE `sqrt(47/8)`, unique adjacent valid training scale `9/4`, MASE
`17/18`, persistence-relative MAE skill `-1/16` and MSE skill `-15/32`.
The correlation control is `26.5/sqrt(35*44.75)`. Pinball controls give 0.8 at
q=0.2 with a prediction four below target, and 0.4 at q=0.8 two above target.
Only supplied ordered quantiles are scored; point forecasts do not create them.

The independent sweep covers **60 exact-Fraction masked/weighted trajectory
cases**, with pairwise covariance correlation and rational pinball oracles.
MAE/RMSE pool valid weighted cells, MASE uses valid adjacent unique training
targets, and native aggregate unit compatibility is checked. Empty masks,
single-pair/constant correlation, zero training scale/reference loss, and
zero-origin coverage use explicit null values and reasons.

For event counts TP=3, FP=2, FN=1, TN=5:

| Metric | Formula | Independent value |
|---|---|---|
| Precision | TP/(TP+FP) | 3/5 |
| Recall/POD | TP/(TP+FN) | 3/4 |
| FAR | FP/(TP+FP) | 2/5 |
| FPR | FP/(FP+TN) | 2/7 |
| F1 score | 2TP/(2TP+FP+FN) | 2/3 |
| TSS | TP/(TP+FN) − FP/(FP+TN) | 13/28 |
| HSS2 | 2(TP·TN−FP·FN)/((TP+FN)(FN+TN)+(TP+FP)(FP+TN)) | 26/59 |
| Brier | Mean supplied valid probability squared error | Matches independent per-case reductions |

All **625 tables** with each count from zero through four agree with independent
oracles, including marginal chance-agreement derivation of HSS2. Zero denominators,
all-negative/all-positive/immature/empty cases are undefined with explicit
reasons. Probability-only inputs do not invent decisions or confusion counts.

F5 remains a fresh **MEDIUM** correctness finding at extreme accepted tiny errors:
target `a`, model 0, reference `3a`, with `a=1e-170` or `1e-200`. Correct RMSE is
`a` and MSE skill is 0.75, both representable. Square-first float64 arithmetic
returns RMSE 0 and null skill/`zero_persistence_loss`. Decimal precision 80 and
isolated square-underflow checks establish the discrepancy. At large errors the
evaluator explicitly fails; ordinary-range formulas pass. This limitation is not
hidden by the new HIGH verdict.

F9 also remains freshly executed: native/reference ratios with true log values
±400 and finite final inverse outputs are refused through avoidable intermediates.
No safe numerical fix was applied during this audit.

## 12. Temporal/leakage red team and failure coverage

Actual `splitting.py` and `windows.py` partition raw chronological intervals
before window construction. Dependency lookback, label maturity, cadence gaps,
provided group purging, eligibility and retained/excluded origin reasons are
explicit. Masks preserve missingness without imputation, operational delivery
is distinct from earliest bin-end availability, and FutureGrid is target-free.
The split/window test sources were inspected; their dedicated entire modules
were not newly run after the HIGH gate closed.

Fresh executed controls in F1/R1/baseline/runner scopes and independent probes
cover future-target/feature perturbations, issue-time support/availability,
malformed/reordered/duplicate origins, copied and serialized contexts, subclass
overrides, missing/dependent training support, masks, coordinates, units and
empty support. This is bounded adversarial evidence, not exhaustive proof.

Fitting uses only a validated train slice. Prediction receives context and a
target-free grid. Evaluation obtains realized labels after forecasts exist.
Retrospective complete eligibility may select common evaluated origins using
target quality; that does not expose realized target values to fitting/predict.
N1's availability-policy collision prevents a general operational guarantee.

Fresh actual runner probes preserve common attempted origins and valid target
coverage when models fail. An ordinary in-memory scenario executes 18/18 model/
partition evaluations; empty test gives 12/18 plus six prediction failures;
empty train gives 0/18 plus 18 fitting failures. Failures preserve null losses
and attempted coverage, without selecting model-specific favorable subsets.

**INFORMATIONAL N2:** all-masked test labels can still produce `complete` and
18/18 successful evaluator calls, with every test report explicitly showing
coverage zero and NA/`empty_mask`. Complete describes execution, not positive
scored evidence. The coverage fields must be read. No labels or scores were
fabricated; no new scientific definition is inferred from this status.

## 13. Provenance, fingerprints and artifact behavior

For ordinary primitive-string inputs, fresh independent reconstruction of a
runner's actual TrainingSlice matches its training fingerprint
`dcee516048acc2e5d8d16b90bfb962d8ae39934361a2c0d91076c324aef6046e`
and all four model records. Rehashing `{config,dataset,split,source,training,seed}`
matches the semantic experiment ID. Raw coordinates, values, masks, availability,
partition/origins and spec participate in effective training identity; declared
full-dataset/split labels alone do not determine it.

Fresh small artificial runner reruns have equal semantic IDs and selected
prediction/metric/parameter/split bytes, with distinct execution IDs. Changing
fixture seed or ordinary dimensional log transform changes effective identities.
These are bounded reviewer probes, not the required real acceptance pairs.

Git/source/package provenance records actual identities and runtime versions;
the runner rechecks source/Git after execution. Fresh scoped tests reject tracked
dirty files, ordinary untracked source, import/source mismatch and changes during
execution. F4 still limits the quoted-source tracking gate. Semantic IDs are not
full dependency-binary or cross-platform attestations; Git/docs/runtime labels
are not all hashed as scientific semantics.

N1 explicitly defeats the general premise that these hashes describe effective
consumed spec semantics. Hashing numeric category zero omits its transform and
availability equality behavior. Distinct effective inputs/semantics can share
the spec/training identities even though ordinary runner controls pass.

Fresh artifact controls:

- Indexed byte corruption and extra ordinary files reject.
- Regular artifact copy relocation verifies unchanged bytes.
- Eight tasks across four processes yield one publication winner and seven
  FileExistsError losers; the winner verifies and no staging directories remain.
- Nonfinite staging aborts without a published execution or staging leftovers.
- Structured model failures retain attempted common origin/target coverage.

F3's symlink/index containment and F8's malformed index types remain open. No
power-loss durability, parent-symlink race, dependency substitution or universal
loaded-bytecode attestation is claimed. The result schema exposes training hash
but retains optional historical-v1 fields; generated artifacts are not a general
proof of schema enforcement at every public input boundary.

## 14. Fresh executed test results and stop gate

| Executor and actual scope | Fresh result |
|---|---|
| Primary: complete TrainingSlice + prediction-context modules | **238 passed in 0.56s**: 53 F1 + 185 R1 |
| Boundary reviewer: contracts + TrainingSlice + baselines + prediction-context | **327 passed in 0.69s** |
| Mathematics reviewer: baselines + trajectory + events + runner | **122 passed in 4.52s** |
| Provenance reviewer: provenance + reference + runner, installed tests deselected | **59 passed, 2 deselected, 1 warning in 2.95s** |
| Primary independent N1 probes | Exit 0 with defect assertions; material transform/policy collisions and caller alias observed |
| Boundary independent probes | 159 labeled assertions pass, plus the separate N1 reproduction |
| Mathematics independent probes | 41 named controls; 60 rational trajectory cases; 625 confusion tables; four runner cases and numerical edges |

These scopes overlap. Their counts must **not** be summed or represented as the
complete P1 or repository suite. Reported historical **480 targeted**, **646
full**, and **295 review probes** are reference claims, not fresh full runs by
this audit. This audit found HIGH N1 and closed the downstream gate; the complete
P1 targeted suite and complete repository suite were **NOT RUN** here.

Representative exact commands actually executed:

```sh
.venv/bin/python -B -m pytest -q tests/test_training_slice_consistency.py tests/test_prediction_context_causality.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider -o pythonpath=src tests/test_forecasting_contract.py tests/test_training_slice_consistency.py tests/test_baselines.py tests/test_prediction_context_causality.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/solarjepa-p1-final-audit-20261005/mathematics/pytest-temp tests/test_baselines.py tests/test_trajectory_metrics.py tests/test_event_metrics.py tests/test_experiment_runner.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_experiment_provenance.py tests/test_experiment_reference.py tests/test_experiment_runner.py --basetemp=/private/tmp/solarjepa-p1-final-audit-20261005/provenance/pytest -k 'not installed'
.venv/bin/python -B /private/tmp/solarjepa-p1-final-audit-20261005/primary-category-review.py
```

The existing warning was preserved, not filtered to clean a log:

```text
tests/test_experiment_reference.py::test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability
<frozen importlib._bootstrap>:488: RuntimeWarning: numpy.ndarray size changed,
may indicate binary incompatibility. Expected 16 from C header, got 96 from PyObject
```

Fresh observed reference tests still pass with that warning. No resolution of
the installed NumPy/netCDF binary warning is claimed.

## 15. Acceptance and reproducibility limits

Fresh bounded synthetic acceptance pair and real pinned GOES acceptance pair:
**NOT RUN**, because HIGH N1 was confirmed first. No scored partition/model
failure count for those pairs is asserted. No byte-identical real acceptance
artifact claim is made. Previous remediation acceptance outputs remain historical
evidence, not a replacement for the required fresh gate.

The fresh small artificial reviewer pairs establish deterministic IDs and byte
identity only for their selected JSON artifacts in this environment. Corruption,
relocation and multi-process controls are freshly executed as described above.
Semantic reproducibility with ordinary string specs has bounded positive
evidence; N1 refutes its universal effective-metadata premise.

Not demonstrated by this audit: fresh clean-environment installation/build,
independent dependency environments, cross-platform reproducibility, complete
byte identity including execution/provenance labels, or all finite-range numerical
correctness. Documentation must not extend same-environment selected-byte
results to those stronger claims.

## 16. Installed behavior outside checkout

Fresh primary check ran from `/private/tmp`, with `PYTHONPATH` removed and the
absolute repository `.venv/bin/python`, without installing or modifying it.
Package `__file__` was
`/Users/nealsalian/Desktop/SolarJEPA/.venv/lib/python3.13/site-packages/solar_flare_jepa/__init__.py`,
not checkout `src`. Normal package/forecasting/provenance imports succeeded.
All **22 enumerated installed/source module files matched** their checkout
SHA-256 values. Some unused module files were hashed without being imported;
this is file parity, not a claim that every possible module execution path ran.

The absolute `scripts/run_experiment.py --help` invocation outside checkout,
with no PYTHONPATH, exited **0** and imported the installed runner. This verifies
the provided CLI script and package import path, not a separately installed
console entry point: pyproject declares none, and no new packaging behavior is
in the branch diff.

Recorded source fingerprint:
`88dafe453e95b9542655f1a8f3f4c5aa45f50099c3550b9b60e67849da253241`.
Reported Git commit was actual feature HEAD `8fa3877f...`. Runtime: Python
3.13.3, macOS 26.3 arm64; package 0.1.0, NumPy 2.2.6, pandas 2.3.3, xarray
2026.7.0, netCDF4 1.7.2, pyarrow 25.0.1. This is a matching existing installation
on this machine, not a new isolated wheel/dependency build or cross-platform proof.

## 17. Preserved scientific state and Phase E

The historical 109-entry preservation inventory was used only as a list of
paths and baseline bytes; every current path was **freshly hashed**. Inventory
SHA-256 is
`3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193`.
OBSERVED: **109/109 matched**, zero missing or changed entries. Categories are
one `.agents` file, six configs, 70 data paths and 32 results paths; the list
includes placeholders/housekeeping, so this is a preservation result, not 109
independent scientific certifications.

Inherited frozen code/config/manifest/document identities were also compared
against main. AGENTS, ignore rules, packaging/lock, scientific configs, existing
data readers/manifests and SoLEXS reports have no changes. Actual ignore checks
protect raw NOAA files, processed Parquet and generated experiment outputs.
No original archive, sidecar, processed scientific file, calibration candidate
or gate was rewritten; no data was acquired.

`data/manifests/solexs_phase_d1_requirements.json` still has
**`BLOCKED_FOR_PHASE_E`**. Phase E requirements still have **`BLOCKED`**. No new
scientific evidence resolves timing interpretation, LC bin semantics, GTI/
exposure, HK/correction compatibility, PI/response indexing, calibration,
cross-payload alignment or defensible real-event definitions. Native missingness
and unknowns remain unknown. No SoLEXS semantics were inferred from P1 math tests.

The GOES adapter was inspected and its artificial-format tests freshly executed:
it is read-only, checks pinned source/prepared bytes and content/policy association,
preserves selected quality masks and unknown actual availability, and does not
rewrite historical sidecars. A real pinned GOES rerun was stopped at the HIGH
gate. GOES infrastructure success, historical or synthetic, does not establish
SoLEXS science readiness. Phase E, SolarJEPA training and ARCH/GARCH remain outside
this audit and were not started.

## 18. Integration simulation and eventual human procedure

**Fresh merge-tree integration simulation: NOT RUN.** The user specifically
conditions it on zero BLOCKER/HIGH findings. The verified ancestry supports
ordinary fast-forward topology, but no fresh simulated merge tree or integration
test result is asserted. Main was never moved or used to create a real merge.

**Integration of this candidate is blocked.** There is no recommended command
to integrate `8fa3877f...` as a ready candidate. Required sequence is separately
authorized focused remediation of N1, fresh verification/final audit including
all skipped gates, then explicit human integration approval for the resulting
exact reviewed SHA. Milestone/research branches must be retained.

For a future candidate that actually receives a READY audit and explicit human
authorization, the following is the guarded proposed procedure. Replace the
placeholder only with that future approved SHA; these commands were **not run**.
Stop on any failed guard, changed main, unexpected working-tree state or upstream
divergence. Do not reset user work.

```sh
git fetch origin
git switch feat/p1-experiment-evaluation-foundation
approved_p1_sha='<future-human-approved-and-audited-feature-SHA>'
test "$(git rev-parse HEAD)" = "$approved_p1_sha"
test "$(git rev-parse origin/feat/p1-experiment-evaluation-foundation)" = "$approved_p1_sha"
test "$(git rev-list --left-right --count HEAD...@{upstream})" = "$(printf '0\t0')"
git diff --exit-code
git diff --cached --exit-code
git status --porcelain=v1 --untracked-files=all
# Inspect untracked state: only the explicitly retained Paperclip tooling is expected.
test "$(git rev-parse main)" = '1a4991da4dda9676caeb1d7e35a03408528c3188'
test "$(git rev-parse origin/main)" = '1a4991da4dda9676caeb1d7e35a03408528c3188'
git merge-base --is-ancestor main "$approved_p1_sha"
git merge-tree --write-tree main "$approved_p1_sha"
# Require a clean simulation, the fresh READY audit, and explicit merge approval.
git switch main
git merge --ff-only "$approved_p1_sha"
# Only with a separate explicit authorization to push protected main:
git push origin main
```

A human-managed PR satisfying the protected branch's review rules is also
appropriate. A READY label never grants merge or push permission. No branch
deletion is part of either procedure. Changed main or a different approved tree
requires renewed evidence, not reuse of this failed report.

## 19. Discrepancies, severity summary and limitations

| Historical/report claim | Fresh disposition |
|---|---|
| F1 raw/window contradiction corrected | Supported for the exact numerical join mechanism and subclass validator route; stronger transformed-semantic identity is defeated by N1. |
| All-six prediction logic consumes canonical detached snapshots | Supported for exact-base objects and immutable array buffers; false for surviving non-string category hooks/caller aliases. |
| Primitive string normalization closes identity/availability hooks | Supported for real string subtypes; numeric enum-like categorical variants bypass its scope. |
| 480 targeted / 646 full / 295 reviewer probes | Historical only. Fresh scopes/counts reported separately; full runs stopped after HIGH. |
| 109 preserved identities | Independently reproduced 109/109 current byte matches, with inventory scope explained. |
| 22 installed/source modules | Independently reproduced 22 file matches and normal installed imports outside checkout; no fresh independent environment/build. |
| Fresh acceptance pairs support current readiness | No such claim is supported by this audit; required pairs were stopped at HIGH. |
| Artifact completeness/strict tracking/finite-input guarantees | F3/F4/F6/F8 remain bounded open limitations with fresh counterexamples. |
| Ordinary metric formulas correct for every accepted finite magnitude | F5/F9 remain numerical range limitations; ordinary math agrees. |

New severity summary:

- **BLOCKER:** none separately identified.
- **HIGH N1:** non-string category equality/aliasing survives canonical reconstruction,
  yielding same identity with different effective transforms/fits and availability
  policy. This is the concrete integration blocker.
- **MEDIUM:** no separate new finding; historical F3/F4/F5 remain open.
- **LOW:** no separate new finding; historical F6/F7/F8/F9 remain open.
- **INFORMATIONAL N2:** runner complete can describe zero-label successful evaluation;
  coverage remains explicit and must be inspected.

The audit is bounded: no exhaustive Python object fuzzing, universal concurrency/
filesystem/power-loss guarantee, physical unit authentication, new scientific
event/calibration validation, clean independent dependency environment, or
cross-platform proof. Stopped tests/acceptance/simulation are explicit omissions,
not successful checks. No defect was silently fixed or downgraded to obtain READY.

## 20. Evidence, preservation and final stop

Fresh evidence directory:
`/private/tmp/solarjepa-p1-final-audit-20261005`.

Key files: `initial-state.json`, `main-candidate.diff`,
`primary-focused-tests.log`, `primary-numeric-enum.log`,
`primary-category-review.py`, `primary-category-results.json`,
`primary-category-review.log`, `scientific-preservation.json`,
`installed-verification.json`, `installed-cli-help.log`, and the three fresh
reviewer directories (`boundaries`, `mathematics`, `provenance`). Each contains
its actual scripts/results/logs and REVIEW.md. These are local scratch evidence,
not tracked scientific artifacts or new data. The public reproducer and key
values above preserve the central finding without relying on temporary files.

Historical failed checkpoints remain unchanged:

| File | SHA-256 preserved through this audit |
|---|---|
| P1_INTEGRATION_READINESS_AUDIT.md | `74eda048a70f80bde4ecdff2d443271aa66e6878573f5b94dd9a8089e196cba2` |
| P1_INTEGRATION_READINESS_REAUDIT.md | `5ee9f5180cc5f8f3f9aeea5b0fb5f4c0c66e6499bb28c10c8014b3dba4c28646` |
| P1_TRAININGSLICE_REMEDIATION.md | `fbf6f50088f362c9a719b640bcba1f15140d5f28a4e7586bde2c0a2f02894bbe` |
| P1_PREDICTION_CONTEXT_REMEDIATION.md | `01cf813e08f1a24020d92bdc83fc57e7b56e026bfee37574d80a0b8f7e680759` |

Final OBSERVED checks: `git diff --exit-code`, `git diff --cached --exit-code`
and `git diff --check` all exit 0. Existing tracked files and index are unchanged;
the sole new repository content is this uncommitted audit report. Full untracked
status lists exactly the report and the unchanged Paperclip file. Initial hashes
of all historical reports, implementation/status documents, README and Paperclip
match. Fresh `git ls-remote --heads origin` confirms protected main, feature and
research at the exact SHAs in section 1. Feature upstream divergence is 0/0.
Source/test/config/schema/CLI/data/packaging paths have no delta between audited
implementation `0095479` and feature `8fa3877`. The self-contained section 6
reproducer was extracted from this report and executed successfully, printing
the mean and Ridge differences reported above. No documentation-only commit was
created under the failed-gate policy.

**NOT_READY_FOR_INTEGRATION.** Stop for human review of HIGH N1. No integration,
push, implementation repair, scientific gate change or Phase E action is
authorized or performed by this audit.
