# P1 causal prediction-context remediation

Checkpoint: 2026-10-05 (Asia/Kolkata). This is the focused correction of R1,
the HIGH prediction-consumption finding from the failed fresh re-audit of
`0f587d96d09583e3f7d15ce5b3d40145264e1ab6`. It is not an integration approval.
The remediated code requires another integration-readiness audit.

## Revisions and preserved evidence

All work continues on `feat/p1-experiment-evaluation-foundation`.
Protected main remains `1a4991da4dda9676caeb1d7e35a03408528c3188`;
the frozen research checkpoint remains
`805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe`.

| Commit | Purpose |
|---|---|
| `990d6f3d04ce3028947059b2d8b5da3103f1c991` | `docs(p1): preserve failed integration reaudit`; original report bytes only |
| `5048d42616c41249b4115f2f2a1cbacde6ce4017` | `test(forecasting): reproduce prediction context leakage`; tests observed RED before source changes |
| `009547932e398edeef1bd2ede2ff3d10bc9e1862` | `fix(forecasting): enforce causal prediction snapshots`; verified implementation and acceptance-run Git identity |

This report and necessary current-status updates are a subsequent documentation
commit. Its containing SHA and feature-only publication verification are supplied
in the user checkpoint; source verification refers to `0095479`.

Historical reports were not rewritten:

| Preserved file | SHA-256 |
|---|---|
| `P1_INTEGRATION_READINESS_AUDIT.md` | `74eda048a70f80bde4ecdff2d443271aa66e6878573f5b94dd9a8089e196cba2` |
| `P1_INTEGRATION_READINESS_REAUDIT.md` | `5ee9f5180cc5f8f3f9aeea5b0fb5f4c0c66e6499bb28c10c8014b3dba4c28646` |
| `P1_TRAININGSLICE_REMEDIATION.md` | `fbf6f50088f362c9a719b640bcba1f15140d5f28a4e7586bde2c0a2f02894bbe` |

## Independently reproduced R1 and root cause

**OBSERVED before production edits:** a literal artificial series contains values
1 through 12 on one-second bins, train support `[0,8)`, test support `[8,12)`,
two context steps and one forecast lead. Test issue times are seconds 10 and 11.
Canonical Persistence produces `[10,11]`; realized future targets are `[11,12]`.
Deepcopy/pickle contexts were changed to expose those target values, with final
context ends and actual availability at seconds 11 and 12. All declared issue,
dataset and fitted parameter identities remained unchanged. Persistence consumed
the invalid context and returned `[11,12]`. The exact base constructor rejected
the same declarations. Independent reviewers reproduced acceptance across all
six baseline APIs, not only Persistence.

`_Baseline.predict` checked Python inheritance, alignment labels and fitted
identity, then passed the original caller objects directly to `_predict`.
Alignment never revalidated a context's interval or availability constraints.
All six baselines inherit this boundary. Persistence/trailing mean use valid
counterpart cells; drift/AR1 also use interval ends for elapsed steps; Ridge
reads selected context lags. Training mean does not read context values, but
still admitted a context violating its public input contract.

Canonical construction already requires integer, ordered issue coordinates,
unique named origins, Boolean masks, finite valid cells, exact completed past
bins and eligible-cell delivery between bin completion and issue time.
Operational availability cannot be unknown. Those validators were omitted at
the prediction trust boundary:

- Ordinary deepcopy and pickle restored writable NumPy buffers without calling
  constructor validators. Direct array assignment sufficed for R1.
- Shallow copy alone retained immutable buffers. Its exploit required explicit
  field rebinding, as did direct dictionary mutation or `__new__` reconstruction.
- A subtype's no-op `__post_init__` bypassed inherited dataclass construction;
  replacement of that subtype preserved the bypass.
- Cached spec fingerprints, cadence/transform methods and extra grid state
  remained caller-controlled. Returned prediction grids also aliased callers.

Existing tests exercised malformed canonical construction, valid builder output,
alignment mismatch and copied/subclassed inputs at **fit**, where F1 already
installed a canonical boundary. They did not feed restored or unchecked
contexts with still-matching labels into **predict**. Five existing literal
baseline cases explicitly asserted output grid object identity, preserving the
alias rather than its intended semantic coordinates.

## Invariant established before implementation

Immediately before any baseline consumes prediction information, reconstruct
the declared fields into exact base `ForecastSpec`, `ForecastContext` and
`FutureGrid` snapshots. Independently reconstruct both incoming specs; do not
substitute the fitted spec to hide a mismatch. Reapply canonical validators,
alignment and fitted identity checks to the detached snapshots, then consume
those same snapshots.

All context intervals must be exactly the completed past grid, regardless of
mask. Every eligible cell must be finite and, when actual delivery is supplied,
have availability in `[bin end, issue time]`. Operational unknown delivery
rejects. False-mask cells remain ineligible: their inert payload/delivery is
preserved under the existing masked contract, never clipped, filled or exposed.
Retrospective unknown delivery remains explicitly unknown.

The future grid starts at issue time, contains only declared coordinates,
identity and spec, and cannot pass realized target state to model code. Returned
coordinates are a detached immutable snapshot. Valid declarations preserve
values, masks, order, units, transforms and numerical predictions. Invalid
declarations reject deterministically before `_predict`.

Training continues to use the F1 canonical raw/window join and the effective
fingerprint of the exact snapshot consumed by fitting. Declared string content,
not custom equality/conversion methods, governs semantics at both boundaries.

## TDD evidence and related subtype attack

Before source changes, these commands were executed against the defective code:

```sh
.venv/bin/python -m pytest -q tests/test_prediction_context_causality.py
.venv/bin/python -m pytest -q tests/test_experiment_runner.py::test_invalid_prediction_context_records_failures_without_scoring_future_values
.venv/bin/python -m pytest -q tests/test_baselines.py::test_literal_outputs_for_five_baselines
```

The new prediction module produced **148 failed, 37 passed**. Expected rejection
assertions failed with `DID NOT RAISE ValueError`; alias, subtype-dispatch and
primitive-semantic assertions exposed their corresponding defects. The 37
passing controls were 36 valid reconstruction/model combinations and one inert
masked-cell case. The runner regression separately failed because status was
`complete` instead of `complete_with_model_failures`. The five existing literal
tests failed only on the deliberately changed detached-grid expectation.
Tests were committed separately as the RED checkpoint `5048d42`.

The bounded subtype review found a related hole in exact-base reconstruction:
a string subtype storing `"identity"` could compare as `"log10"`. Exact spec
construction retained that subtype. **OBSERVED:** two Ridge fits had identical
recorded/effective identities but intercepts `[1.5113960113960112]` versus
`[0.42736571113512234]`. Another subtype stored `"operational"` while selecting
retrospective comparisons and hiding unknown delivery. Equality hooks also hid
duplicate origin strings. This is part of the same semantic boundary/F1
preservation problem, not an unrelated model extension.

Six-model regression cases were added before the fix. Primitive string extraction
uses `str.__str__` directly, preserving stored text without invoking overridden
equality, serializer, `strip` or dynamic `str(value)` behavior. A misleading
`__str__` control confirms unit text is preserved rather than rewritten.

## Minimal implementation and changed files

`forecasting/baselines.py` installs a single shared prediction boundary. It
checks nested spec types, reconstructs each exact base spec, context and grid,
then validates alignment/fitted identity and invokes model logic with those
snapshots. The algorithms and numerical fitting formulas are unchanged.
`ForecastPrediction` receives the validated detached grid.

`forecasting/contracts.py` adds `_canonical_fields`: select the fixed base field
list and normalize string subtypes and ordered containers to primitive declared
content. Exact constructors continue to copy arrays into bytes-backed immutable
buffers and perform all existing semantic checks. TrainingSlice's existing
nested reconstruction and the shared fitting boundary reuse this helper.
Raw/window equality, masks, availability, gap/bounds validators and the training
fingerprint schema remain intact. No input is silently repaired.

The complete remediation inventory relative to `0f587d9` is ten paths:

| Group | Files |
|---|---|
| Production | `src/solar_flare_jepa/forecasting/contracts.py`, `src/solar_flare_jepa/forecasting/baselines.py` |
| Tests | `tests/test_prediction_context_causality.py` (new), `tests/test_baselines.py`, `tests/test_experiment_runner.py` |
| Documentation | `docs/P1_INTEGRATION_READINESS_REAUDIT.md` (unchanged failed checkpoint added), this report, `README.md`, `docs/PROJECT_STATUS.md`, dated addendum to `docs/P1_IMPLEMENTATION_REPORT.md` |

No dependency, configuration, schema, dataset, scientific manifest, adapter,
metric formula or gate was changed. Intentional API consequence: the returned
grid no longer has the caller object's Python identity; valid semantic content
is unchanged.

## Regression coverage and executed verification

There are **186 additional parametrized test cases**: 185 in the new module and
one runner failure-record test. The five grid-alias checks modify existing cases.

| Coverage | Current executable evidence |
|---|---|
| Future values/intervals/delivery via shallow/deep copy, pickle, subtype/replacement, `__new__`, dictionary mutation | `test_every_prediction_rejects_reconstructed_future_context`: seven routes × all six models |
| Actual content: active delivery late/early/unknown, off-grid/extended bins, numeric masks, duplicate/reordered origins | `test_prediction_validates_actual_content_not_python_type`: eight attacks × six models |
| Malformed target-free grid | `test_every_prediction_revalidates_future_grid`: three attacks × six models |
| Canonical/copy/deepcopy/pickle/replacement/subtype valid controls | `test_valid_prediction_reconstructions_preserve_literal_outputs`: six routes × six models |
| Output and consumed-context detachment; extra realized-target grid state | Snapshot/alias tests; exact base grid has no `values`, `targets` or mask field |
| Cached identity, cadence and broken spec hooks | Declared spec reconstruction/rejection tests |
| Nested string semantics and effective fitting identity | Six-model availability/origin/transform tests and misleading unit conversion control |
| Failure provenance without scoring leaked values | Runner records six test-partition `predict` ValueErrors, attempted origins and common target counts; failed values/metrics null; 12 unaffected train/validation scores |
| F1 and future-only perturbations | Existing 53 TrainingSlice adversarial cases and whole-chain/all-six baseline tests remain green |

Primary observed results after source changes and matching installation:

| Command/scope | Result |
|---|---|
| New prediction module | **185 passed**, 0.54 s |
| Existing TrainingSlice adversarial module | **53 passed**, 0.15 s |
| New runner rejection case | **1 passed**, 1.08 s |
| Complete P1 targeted suite below | **480 passed, 1 warning**, 5.63 s |
| `.venv/bin/python -m pytest -q` | **646 passed, 1 warning**, 39.52 s |
| `git diff --check` | Exit 0 |

```sh
.venv/bin/python -m pytest -q \
  tests/test_prediction_context_causality.py tests/test_training_slice_consistency.py \
  tests/test_forecasting_contract.py tests/test_forecasting_splits.py \
  tests/test_forecasting_windows.py tests/test_baselines.py \
  tests/test_trajectory_metrics.py tests/test_event_metrics.py \
  tests/test_experiment_provenance.py tests/test_experiment_reference.py \
  tests/test_experiment_runner.py
```

No warning filters were added. Targeted and full suites retain:

```text
tests/test_experiment_reference.py::test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability
<frozen importlib._bootstrap>:488: RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility. Expected 16 from C header, got 96 from PyObject
```

## Installed execution, fingerprints and acceptance pairs

Normal `.venv/bin/python -m pip install --no-deps .` built and installed the
matching wheel. The sandboxed attempt failed resolving build dependencies;
the permitted retry obtained setuptools and succeeded. Existing scientific
dependencies were not reinstalled or changed. Outside the checkout, with
`PYTHONPATH` removed, package/core imports resolved under site-packages and
all **22** execution module files matched checkout hashes. The absolute-path
`scripts/run_experiment.py --help` invocation exited 0. There is no separate
console-script entry point; the existing wrapper uses the installed core.

Observed environment: Python 3.13.3, macOS 26.3 arm64; package 0.1.0,
NumPy 2.2.6, pandas 2.3.3, xarray 2026.7.0, netCDF4 1.7.2, pyarrow 25.0.1.
This is a rebuilt normal installation in the existing environment, not an
independent clean dependency environment or cross-platform validation.

Four bounded CLI runs used clean tracked Git identity `0095479`, installed
matching modules, `/private/tmp` as cwd and no `PYTHONPATH`. For each `a`/`b`
pair the command was equivalent to:

```sh
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B \
  /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py \
  --root /Users/nealsalian/Desktop/SolarJEPA \
  --config configs/experiments/p1_synthetic.json \
  --output-dir results/experiments/p1_prediction_remediation_20261005_synthetic_a
```

The second synthetic output ends in `_synthetic_b`; GOES uses
`p1_goes_reference.json` and `_goes_a`/`_goes_b` outputs. All four directories
are new ignored local artifacts, not committed scientific results.

| Dataset | Execution IDs (`a`, `b`) | Each run |
|---|---|---|
| Synthetic | `8182c62d6f444593a1c0b9fd10f7a624`, `1126f2790d2f474babde485dfe2eff87` | complete; 54 successful scores; zero failures |
| Pinned GOES | `6b4da89cedca421286d82753fed742e9`, `e230aeebb66f4097aefb992ce7026aed` | complete; 54 successful scores; zero failures |

Source fingerprint:
`88dafe453e95b9542655f1a8f3f4c5aa45f50099c3550b9b60e67849da253241`.
Each result's three seed-tagged semantic IDs were independently recomputed
using SHA-256 of canonical JSON over config/dataset/split/source/training/seed.
They match within each pair; execution UUIDs differ.

Canonical raw support and retained origins were rebuilt, and effective training
hashes independently recomputed from their exact payload. All 18 fitted model
records per dataset matched the effective hash:

- Synthetic: `17387eddad257ef19ec90bbc17207a8714a94060f59b96f9712efd0c15172dc7`.
- GOES: `26d9521b28c91bc645b48771c11af9b4ffc65898d6c7aeffe1028b6c153b835c`.

All four artifact indexes verified their nine indexed files. Eight files were
byte-identical within each same-environment pair: resolved config, dataset
manifest, split manifest, provenance, model parameters, predictions, metrics
and failures. `result.json` and its indexed digest differ for execution-specific
UUIDs, paths and timestamps; entire directories are not byte-identical.
Relocated scratch copies with a changed `predictions.json` byte were rejected
with `Artifact identity mismatch: predictions.json` for both datasets.

The prior F1 final acceptance directories at `8ba57aa` were also verified.
Their seven stable non-provenance artifacts are byte-identical to the current
valid runs; config/dataset/split/training hashes are unchanged. Source/provenance
and therefore semantic experiment IDs change with the corrected source.
No new fingerprint schema was needed. Malformed contexts produce explicit
failure records, not apparently successful forecasts.

## Fresh independent review and workflow effects

A fresh reviewer that authored no fix inspected source, tests, Git and
runner/provenance code, then executed checkout-source attacks independently.
It reported **zero unaddressed BLOCKER/HIGH findings in this bounded review**.
The primary independently reran its probe script: **295 passed, zero failed**.

The 295 probes comprise 198 malformed predictions (33 variants × six models),
18 valid prediction controls, 48 inconsistent fits, 24 valid fit reconstructions,
six effective-identity controls, and one privately loaded original-defect control.
Sentinels proved invalid inputs were rejected before `_predict` or `_fit`.
Additional variants included future property/getattribute overrides, unsigned
time overflow, negative coordinates, multichannel delivery, masked future
intervals, blank metadata hooks, cached semantic identities, caller mutation
during consumption and stale fitting fingerprints. The original `0f587d9`
modules still accepted the attack, proving probe sensitivity. The reviewer also
ran 291 focused and three runner tests successfully.

Superpowers systematic-debugging required independently reproducing the data
flow and distinguishing shallow from restored writable buffers before choosing
a fix. TDD preserved a separate executable RED test commit. Parallel-agent
review exposed the related nested-string identity hole before implementation.
Requesting-code-review supplied a fresh, read-only adversarial final reviewer;
verification-before-completion required actual test/install/artifact/hash results
before committing source and reporting readiness. The bounded preimplementation
invariant/plan was recorded in scratch; no additional milestone was started.

## Scientific preservation and remaining limits

**OBSERVED:** all **109/109** entries in the original starting SHA-256 inventory
match. Categories are one skill pointer, six configs, 70 data/manifests/products
and 32 prior results/placeholders. This is a preservation inventory, not 109
independent scientific validation certificates. Read-only registration
verification also passed both existing SoLEXS archives; July 2 remains absent
from the obtained collection, not inferred absent mission-wide.

`.agents/skills/paperclip/SKILL.md` remains unchanged and untracked, SHA-256
`4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`.
Actual ignore checks cover new experiment outputs, NOAA raw inputs and Parquet.
No raw data, generated experiment output or Paperclip tooling enters the commits.

The D.1 manifest still says `BLOCKED_FOR_PHASE_E`; Phase E requirements still
say `BLOCKED`. Existing timing, bin, GTI/exposure, HK/correction compatibility,
PI/response indexing, calibration, alignment and defensible real-event gates
remain unresolved. GOES runs are retrospective infrastructure validation only,
explicitly `foundation_smoke_not_scientific_skill`, with operational latency
UNKNOWN. No scientific reinterpretation, acquisition, Phase E work, ARCH/GARCH
fit or SolarJEPA training was performed.

Remaining limitations:

- This fixes R1 consumption and preserves F1; it does not turn every copied or
  pickled dataclass into a universally immutable object. Model boundaries now
  validate their own detached snapshots. Pickle loading is not made safe for
  untrusted code execution.
- Causality is validated against declared support. The prediction API cannot
  authenticate values deliberately relabeled with false historical coordinates
  or delivery times without independent observation provenance.
- Arbitrary monkeypatching, process-state mutation, memory corruption and
  concurrent caller mutation during multi-field extraction are not sandboxed.
  Ordinary copies, reconstruction, property overrides, metadata hooks and
  mutations after capture were exercised.
- Previous F3–F9 nonblocking limitations are preserved, including artifact
  symlink completeness, quoted Git paths, tiny-loss underflow, metadata/type
  edges, caller-mutated model hyperparameters and extreme transform range.
  Their disposition belongs to the next integration audit; they were not
  silently repaired here.
- Determinism and stable-byte results apply to the tested same environment.
  Clean independent dependencies, cross-platform bitwise behavior and snapshot
  performance at scientific scale are unverified. The existing ABI warning
  remains unresolved and unsuppressed.

Outcome of this focused remediation: **READY_FOR_P1_REAUDIT**. A fresh
integration-readiness audit and explicit human approval are still required.
No merge or push to main is authorized by this report.
