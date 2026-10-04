# P1 TrainingSlice correctness remediation

This is a focused correction of HIGH finding F1 from the failed integration
checkpoint at `11b72bb0c714cf71edf1e5ccb390d38444bbb8c8`. The original
`P1_INTEGRATION_READINESS_AUDIT.md` is preserved unchanged in commit
`6868a258c512129b580169a94d7ec475b9cea1f5`; its SHA256 is
`74eda048a70f80bde4ecdff2d443271aa66e6878573f5b94dd9a8089e196cba2`.
Protected main remains `1a4991da4dda9676caeb1d7e35a03408528c3188` and the
research checkpoint remains `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe`.
This correction requires a fresh integration-readiness audit afterward.

## Independently reproduced failure and root cause

OBSERVED before any production edit: the audit's standalone Ridge reproduction
printed intercepts `[0.5000000000000004]` and `[-1666.1666666666663]` after
adding 1000 to context-window values alone. Raw arrays and the declared split
fingerprint were identical. A separate source-import probe exited 1 with three
unexpected acceptances: true window feature cells over invalid raw feature
support, true target cells over invalid raw targets, and conflicting repeated
coordinates. These executions confirm the finding independently of the report.

`TrainingSlice.__post_init__` validated coordinate support and each array
separately. It never joined window cells to raw rows. Ridge selected fitting
rows and values from windows, while mean/AR(1)/MASE consumed raw arrays. All
models recorded only declared dataset/spec/split identities. Builder-generated
inputs were consistent; independent public construction was vulnerable.

## Required invariant, established before implementation

The raw train arrays are canonical for the selected channels. Their masks
represent eligibility with dependencies contained in the raw train partition,
using partition-end availability. Canonical `raw_availability_ns`, when known,
represents actual delivery of the entire causal feature dependency, already
aggregated by the builder; it is not an inferred clock or latency.

Every context/target coordinate and its additional lookback/maturity support
must exist within those canonical raw coordinates and partition bounds.
At each indexed context cell, the mask must equal raw feature eligibility AND
canonical dependency availability by that origin's issue time. Context
availability must equal indexed raw availability. Retrospective unknown
availability remains unknown; operational fitting requires actual availability.
Target masks must equal indexed raw target masks. True window values must equal
the indexed raw values exactly; false window cells must contain NaN. Invalid
inputs reject before fitting, without imputation, row dropping or correction.

Consequently windows remain a validated view of canonical support. We keep the
existing public window objects for API compatibility and validate their supplied
state rather than reconstructing contradictory inputs silently.

A computed effective training fingerprint must include spec, train bounds,
canonical raw coordinates/values/masks/availability and ordered retained
origins/issues. Declared dataset/split identities remain separate provenance;
they cannot substitute for effective training content. Future-only changes must
not change this training fingerprint. Jointly consistent changes to raw and
derived data must change it. Every baseline records it, and semantic experiment
IDs incorporate it. The common fitting boundary revalidates a frozen snapshot
so copied objects cannot bypass this invariant through writable NumPy buffers.

## Bounded implementation and verification plan

- [x] Verify feature/main/research refs and preserved scientific identities;
  reproduce F1; commit only the original failed audit.
- [x] Add adversarial public-contract and fitting/identity tests, run them
  against unchanged production code, and record expected RED evidence.
- [x] Validate indexed values/masks/availability in `contracts.py`; carry
  dependency availability from `windows.py`; record the computed identity at
  common baseline fitting and runner identity boundaries. Correct inconsistent
  toy fixtures while retaining independent mathematical expectations.
- [x] Run focused, all P1 and complete suites, preserving warnings; obtain a
  fresh read-only independent final review and resolve BLOCKER/HIGH findings.
- [x] Commit source/tests, reinstall, verify imports/CLI outside the checkout,
  run paired bounded synthetic/GOES acceptances and artifact/determinism checks.
- [x] Recheck all 109 preserved identities, scientific gates, original audit
  bytes, Paperclip bytes and protected main/research refs.

Documentation publication and the candidate-only push follow these checks;
the final SHA and post-push ref verification are supplied in the user checkpoint.

## TDD evidence and why the original tests missed it

Production source and the schema were unchanged when RED was executed:

```sh
.venv/bin/python -m pytest -q tests/test_training_slice_consistency.py
.venv/bin/python -m pytest -q tests/test_experiment_runner.py::test_semantic_experiment_ids_and_models_record_effective_training_identity
```

The new contract module initially produced **34 failed, 9 passed**:
23 expected-rejection assertions failed because no ValueError was raised,
9 effective-identity assertions failed because training fingerprints were
absent, and 2 availability tests failed because the proposed canonical raw
availability field did not yet exist (`TypeError`, explicitly distinguished
from an accepted-input assertion). The runner regression independently failed
on the absent computed training identity. The 9 passing controls were legitimate
delayed/unknown-availability cases and literal outputs for all six baselines.
The original source-only contradiction probe additionally reproduced three
accepted inconsistent slices before the correction.

Original tests covered individual shapes, masks, finite values, bounds, cadence
gaps, ordered origins, and builder-generated leakage cases. They never joined a
supplied window cell to its raw coordinate. Existing hand-written Ridge fixtures
even assigned contradictory values to overlapping coordinates; their algebraic
expectations passed because Ridge consumed the independent window tensors.
The metric fixture similarly used decorative training windows inconsistent with
the actual raw MASE scale data. Both independent root-cause reviewers found these
problems in source/tests, not by trusting the implementation report.

The corrected fixtures retain their independent literal mathematical assertions.
Ridge rows now occupy disjoint context+horizon blocks backed by a single raw
grid. Raw and supervised masks agree; no fictional overlap is needed. The MASE
fixture uses valid empty supervised tensors because only unique raw pairs are
needed for the scale. No scientific observation or production data was changed.

After the initial implementation, **43/43** tests in the new contract module
passed and the runner identity regression passed in the targeted suite.
The fresh reviewer subsequently found a subtype-validator bypass, recorded
below. Ten additional cases were written and observed RED before its correction:
9 subclass validator cases failed with DID NOT RAISE, and a fixed-transform
subclass case changed the fitted Ridge intercept despite identical declared
semantics. They passed after canonical constructor dispatch replaced subtype
dispatch. The final new contract module has **53/53 passed**. Including the
runner regression, **54 additional parametrized cases** bring P1 from 240 to
**294**, and the repository from 406 to **460**, observed passing tests.

| Attack/control | Executable regression |
|---|---|
| Context and target value mutation, including repeated coordinates | `test_window_value_mutation_is_rejected_before_fitting`, `test_repeated_coordinates_cannot_disagree_with_one_another` |
| False/true mask flips, invented missing support and arbitrary row dropping | `test_window_mask_downgrade_cannot_drop_valid_raw_support`, `test_window_mask_upgrade_cannot_invent_missing_raw_support` |
| Finite payload hidden behind false masks | `test_false_window_cells_cannot_hide_finite_payloads` |
| Redeclared actual availability; exposing delayed cells; dropped raw availability | `test_context_cannot_redeclare_canonical_actual_availability`, `test_delayed_cell_cannot_be_exposed_by_redeclaring_its_delivery_time`, `test_known_training_availability_cannot_be_dropped` |
| Legitimate issue deadlines, causal lookback and unknown retrospective delivery | `test_canonical_delayed_masks_keep_legitimate_origin_deadlines`, `test_retrospective_unknown_availability_stays_unknown` |
| Same declared labels, coherently changed numerical fitting data | `test_joint_value_change_has_distinct_effective_ridge_identity`, `test_joint_mask_change_has_distinct_effective_ridge_identity` |
| Mutable copied values/masks bypassing construction, all six models | `test_every_fit_revalidates_copied_training_before_consumption` |
| Subtype hooks bypassing fitting/nested masks/origin grids or fixed transforms | `test_every_fit_uses_canonical_validator_even_for_training_subclasses`, `test_nested_subclass_hooks_cannot_bypass_origin_grid_validation`, `test_nested_subclass_hooks_cannot_bypass_boolean_mask_validation`, `test_spec_subclass_cannot_change_declared_fixed_transform_at_fit` |
| All six baseline outputs and future-only perturbations | `test_canonical_training_preserves_all_six_literal_baseline_outputs`, `test_future_perturbation_preserves_training_identity_fit_and_prediction` |
| Runner/model identity linkage and semantic experiment IDs | `test_semantic_experiment_ids_and_models_record_effective_training_identity` |

## Exact implementation and identity implications

Initial code commit: **`b5ae4c653a4268a7ff4b78a3b6d07d6c07350233`**, Conventional Commit
`fix(forecasting): enforce canonical training window consistency`.
Final constructor-boundary correction:
**`8ba57aa58242facf7614e805695fe9e71406ea3c`**, Conventional Commit
`fix(forecasting): require canonical validators at fitting boundaries`.

- `forecasting/contracts.py`: new canonical `raw_availability_ns` field;
  reconstruct nested context/targets/grid contracts; retain all existing
  support/bounds checks; index canonical rows and assert exact masks, delivery
  times and native values, including NaN for masked window cells. Compute
  `TrainingSlice.fingerprint` from canonical train content and retained origins.
  Final snapshots explicitly instantiate canonical contracts/specs from their
  declared fields; overridden subclass hooks cannot skip validation or substitute
  unrecorded transformation code.
- `forecasting/windows.py`: retain the existing dependency-aggregated
  availability calculation when constructing raw support. Eligibility,
  retention, splitting and scientific adapter semantics remain unchanged.
- `forecasting/baselines.py`: common `fit` reconstructs a validated immutable
  TrainingSlice snapshot, consumes that snapshot and records its
  `training_fingerprint`. No Ridge-specific correction or numerical algorithm
  change was made.
- `experiments/runner.py`: include `training` in the semantic fingerprint tuple
  before hashing seed-tagged experiment IDs.
- `schemas/experiment_result.schema.json`: allow the additive training hash in
  v1 results. It is optional in the schema for immutable historical v1 records;
  the corrected producer always emits it and the runner regression requires it.
- Four existing test modules were updated for coherent inputs; the new
  `test_training_slice_consistency.py` supplies the adversarial regressions.

The final unique file inventory relative to the original candidate is 15 paths:

| Group | Changed files |
|---|---|
| Production and schema | `src/solar_flare_jepa/forecasting/contracts.py`, `windows.py`, `baselines.py`; `src/solar_flare_jepa/experiments/runner.py`; `schemas/experiment_result.schema.json` |
| Tests | `tests/test_training_slice_consistency.py`, `test_forecasting_contract.py`, `test_baselines.py`, `test_trajectory_metrics.py`, `test_experiment_runner.py` |
| Documentation | `README.md`, `docs/P1_INTEGRATION_READINESS_AUDIT.md` (added unchanged), `docs/P1_TRAININGSLICE_REMEDIATION.md`, `docs/P1_IMPLEMENTATION_REPORT.md` (dated addendum), `docs/PROJECT_STATUS.md` |

The literal numerical expectations were retained: persistence 6, training mean
4, trailing mean 5 and drift 8/10 for their original toys; AR(1) 255/511 from
127 under intercept 1/slope 2; direct OLS 9/14 and alpha=2 ridge 6/9.5 from
lag 4, with an unpenalized intercept; separate dimensional log references give
10000/100000000. MASE's raw training scale remains 8/3 for the default metric
fixture. These tests are hand-derived controls and passed in the final suite.

Windows remain available to callers for compatibility. Contradictory supplied
state is rejected rather than silently regenerated. Exact validation makes the
fitting window tensors derivable from raw support, spec and origins; hashing
those tensors again would duplicate canonical information. The effective hash
includes the whole validated training contract, even information a particular
baseline does not use. Model constructor parameters and source identity define
each comparator's subset. This is an observed-content identity, not an assertion
that arbitrary caller-supplied scientific labels are authentic.

Config, dataset and split hashes retain their previous meanings and values for
the acceptance fixtures. The source hash and semantic IDs change intentionally;
model parameter/result bytes now include effective training identity. Existing
artifact indexing automatically hashes the new bytes. Historical experiments,
sidecars and manifests were not retrofitted or rewritten.

## Verification actually executed

All commands used the existing project Python 3.13.3 environment. Test logs and
scratch probes are in `/private/tmp/solarjepa-p1-remediation-20261004`.

| Check | Observed result |
|---|---|
| Final new contract module | 53 passed, 0 failed in 0.21 s |
| Initial contract/window/baseline/trajectory subset before subtype closure | 179 passed in 0.37 s |
| Final all P1 targeted modules including runner regression | **294 passed, 1 warning in 4.74 s** |
| Final complete repository command `.venv/bin/python -m pytest -q` | **460 passed, 1 warning in 38.89 s** |
| Normal noneditable installation `.venv/bin/python -m pip install --no-deps .` | Wheel built/installed successfully; no project dependency changes |
| `.venv/bin/python -m pip check` | No broken requirements |
| Installed imports outside checkout, `env -u PYTHONPATH`, `-B`, cwd `/private/tmp` | All 22 package source modules match checkout bytes; package resolves to `.venv/lib/python3.13/site-packages` |
| Installed CLI `scripts/run_experiment.py --help` outside checkout | Exit 0 |
| Four bounded installed-CLI acceptance runs | Each complete, 54/54 scores, 0 model failures |
| `verify_artifacts` on all four directories | Nine indexed files per run verified |
| Corrupted predictions in a scratch copy | Rejected with `Artifact identity mismatch: predictions.json`; original artifacts untouched |
| Declared source identities and actual package provenance | 35 source identities and 22 installed module identities match |
| `git diff --check` | Clean at each verification checkpoint |

The retained warning is:

```text
RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject
```

It appeared in both targeted/full suites at the GOES adapter test. No warning
filter was added. The first sandboxed build attempt could not resolve the
package index for setuptools; the authorized retry with network access succeeded.
pip also reported its unwritable cache in sandboxed invocations. Two initial
GOES commands referenced a nonexistent `p1_goes.json` and exited 2 before any
publication. The corrected commands below succeeded with the actual pinned
config. These command/environment failures were investigated and not suppressed.

Targeted command:

```sh
.venv/bin/python -m pytest -q tests/test_training_slice_consistency.py tests/test_forecasting_contract.py tests/test_forecasting_splits.py tests/test_forecasting_windows.py tests/test_baselines.py tests/test_trajectory_metrics.py tests/test_event_metrics.py tests/test_experiment_provenance.py tests/test_experiment_reference.py tests/test_experiment_runner.py
```

The paired acceptance runs used these commands from `/private/tmp`, replacing
`<a-or-b>` explicitly with `a` and then `b` in distinct directories:

```sh
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --config configs/experiments/p1_synthetic.json --root /Users/nealsalian/Desktop/SolarJEPA --output-dir results/experiments/p1_remediation_20261004_final_synthetic_<a-or-b>
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py --config configs/experiments/p1_goes_reference.json --root /Users/nealsalian/Desktop/SolarJEPA --output-dir results/experiments/p1_remediation_20261004_final_goes_<a-or-b>
```

The two same-config executions ran independently, including concurrent paired
publication to distinct output directories. Existing atomic-publication and
concurrency tests also ran in the full suite. No shared destination was replaced.

| Evidence | Synthetic | Pinned GOES |
|---|---|---|
| Retained train/validation/test origins | 112 / 52 / 52 | 103 / 62 / 103 |
| Excluded train/validation/test origins | 8 / 8 / 8 | 41 / 82 / 41 |
| Seeds, fixed comparators, raw partitions | 3 / 6 / 3 | 3 / 6 / 3 |
| Scores per execution | 54 succeeded, 0 failed | 54 succeeded, 0 failed |
| Effective training SHA256 | `17387eddad257ef19ec90bbc17207a8714a94060f59b96f9712efd0c15172dc7` | `26d9521b28c91bc645b48771c11af9b4ffc65898d6c7aeffe1028b6c153b835c` |

Both final pairs recorded code commit `8ba57aa58242facf7614e805695fe9e71406ea3c` on the
feature branch, clean tracked source, and source SHA256
`d7063a2cbfb126dd3593f77c24bb026458ff8eb7251f3bd3f1e2411f06389d51`.
All 18 model records in each run matched the independently reconstructed
TrainingSlice fingerprint. Seed-tagged experiment IDs were recomputed from the
recorded config/dataset/split/source/training tuple and matched.

The initial acceptance pairs at `b5ae4c65` also passed ordinary builder-path
controls but were not final acceptance of H1 closure. They remain in their
original ignored directories. Final executions use new `..._final_...` paths;
no prior execution was replaced. To satisfy the runner's tracked-clean gate,
only the coordinator's three pending documentation drafts were saved to scratch
and temporarily restored to their committed bytes; they were restored after
the final executions with a concurrent-edit check. Production source, scientific
inputs, the preserved failed audit and milestone refs were never rolled back.

Within each pair, eight stable JSON artifacts were **byte-identical**:
resolved config, dataset manifest, split manifest, provenance, model parameters,
predictions, metrics and failures. `result.json` and `artifacts.json` intentionally
differed because executions have distinct IDs/times/output paths and indexed
result hashes. Complete artifact directories are not byte-identical.
The six unchanged artifacts excluding provenance/model parameters also matched
the corresponding original audit runs byte-for-byte; valid numerical predictions,
metrics, origins and data semantics were preserved by the correction.

This demonstrates semantic and stable-artifact byte reproducibility on this
machine/environment, including installed use outside the checkout. A noneditable
wheel build is observed; fresh dependency resolution in a wholly separate
environment and cross-platform/cross-BLAS bitwise agreement are **not established**.
No such stronger claim is made.

## Preservation and scientific gates

The 109-path starting snapshot was rechecked before implementation and after
acceptance: **109 matched, 0 missing or changed**. The snapshot's SHA256 is
`3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193`.
All six pinned GOES source files verified from the existing manifest
(1,002,585 bytes total). The existing two SoLEXS archives passed read-only
`scripts/register_aditya.py --verify`; July 2 remains missing from this obtained
collection and no mission-wide availability inference was made.

There is no remediation diff under `data/`, `configs/`, dependency files,
`AGENTS.md` or existing skill identities. The GOES adapter is unchanged; its
read-only outputs use the same native units, quality masks and explicitly
retrospective bin interpretation. Historical Parquet/sidecar bytes and all
scientific manifests remain unchanged. The Paperclip file remains untracked,
uncommitted and byte-identical at SHA256
`4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`.

Actual gate files still report D.1 `BLOCKED_FOR_PHASE_E` and Phase E `BLOCKED`.
SoLEXS timing, bins, GTI/exposure policy, correction/housekeeping compatibility,
PI/response/channel mapping, gain/calibration applicability, cross-payload
alignment and defensible real event definitions remain unresolved. No new
authoritative evidence was obtained. GOES smoke success does not resolve any
SoLEXS gate. No acquisition, ARCH/GARCH fitting, Phase E work or SolarJEPA
training was performed.

## Independent final review

The fresh final reviewer did not implement this fix and was given the actual
`6868a258..b5ae4c65` source/test diff, requirements and attack targets. Its final
verdict at `b5ae4c65` identified **HIGH H1**: `dataclasses.replace` preserved
runtime subclasses, so a hook omitting the base validator could still change
Ridge fitting data under the same computed fingerprint. It also independently
exposed a future raw context interval through a nested context subclass.
The initial fresh review independently executed 190 scoped tests, 54 dependency
cases, 70 rejection events, actual Ridge design/response comparisons, all-six
identity/future-perturbation controls and literal baseline/MASE checks. It did
not approve that intermediate revision; its original verdict is preserved.

The coordinator independently reproduced H1 and the related mask/grid/spec
routes in ten new RED cases, then corrected them in `8ba57aa`. A bounded closure
check by the same non-implementing reviewer inspected only that three-path diff
and re-executed the exact original attacks against actual new source. All-six
subtype fitting attacks and the future-context attack reject before fitting;
fixed declared spec transforms produce equal canonical fitting records. The
reviewer independently ran **10 passed, 43 deselected in 0.07 s**, declared
**H1 CLOSED at `8ba57aa58242facf7614e805695fe9e71406ea3c`**, and found no new
BLOCKER/HIGH issue in the closure diff. No implementation file was edited by
any reviewer. Parent final suites and acceptance checks were separately executed,
not treated as reviewer-established results.

Scratch evidence is preserved under
`/private/tmp/solarjepa-p1-remediation-final-review`: `review.md` pins the failed
intermediate verdict; `closure_review.md` pins closure; the probe scripts and
JSON retain both reproductions. This bounded closure review establishes readiness
to re-audit the correction, not whole-branch integration readiness.

## Workflow effects and remaining limits

Superpowers systematic-debugging established the actual raw/window/fit boundary
and reproduced numerical corruption before any fix. TDD enforced recorded RED
on unchanged source before production changes and GREEN afterward. Bounded
parallel root-cause and identity reviewers independently found both the deadline
mask distinction and invalid hand-written fixtures; their executable evidence
prevented an incorrect equal-mask shortcut or a Ridge-only patch. The
requesting-code-review workflow supplied a fresh reviewer of the completed
actual diff. Verification-before-completion required observed counts, installed
source parity, artifact bytes and preserved identities before claims/commits.
The focused plan recorded the invariant before implementation, as requested.

Manual operational TrainingSlice constructors now need canonical
`raw_availability_ns` with shape `[raw_rows, selected_feature_channels]`; supplied
retrospective actual availability also needs this binding. It represents full
dependency delivery, not nominal bin completion. Caller workflows that omitted
that canonical information must provide it explicitly. No clock is inferred
for them. Existing builder/runner calls supply the information automatically.

The correction addresses F1 and the mutable-copy bypass at the **training fit**
boundary. It does not claim general deepcopy/pickle immutability of every public
forecast/dataset object. Scientific authenticity of externally declared hashes,
group semantics and delivery times still requires authoritative source evidence;
an internally consistent training content hash cannot provide that evidence.

The failed audit's other findings are preserved and were not silently fixed:
F2 generic writable copies (MEDIUM), F3 artifact-verifier symlink gaps (MEDIUM),
F4 Git-quoted untracked-source detection (MEDIUM), F5 tiny-error RMSE underflow
(MEDIUM), and F6–F9 metadata/numeric/model-mutation/log-transform edges (LOW).
The focused correction leaves the broader copy issue outside fitting, as stated.
These findings, the retained dependency warning and platform/environment limits
must remain visible to the fresh integration-readiness audit; this report does
not grant an exception or declare them acceptable for integration.

## Traceability and stop condition

| Revision | Role |
|---|---|
| `11b72bb0c714cf71edf1e5ccb390d38444bbb8c8` | Original failed integration-readiness candidate |
| `6868a258c512129b580169a94d7ec475b9cea1f5` | Unchanged failed audit committed as `docs(p1): preserve failed integration readiness audit` |
| `b5ae4c653a4268a7ff4b78a3b6d07d6c07350233` | Source/schema/tests correction and acceptance-run code identity |
| `8ba57aa58242facf7614e805695fe9e71406ea3c` | Reviewer-found subtype bypass corrected; final suites, installed package and final acceptance-run code identity |
| Commit containing this report | Verification/report/status documentation; final SHA is supplied in the user checkpoint and `git log -1 -- docs/P1_TRAININGSLICE_REMEDIATION.md` |

Only `origin/feat/p1-experiment-evaluation-foundation` is authorized for these
commits. No branch is merged, rebased, rewritten or deleted. Main/research refs
retain the exact identities above. Final publication synchronization and the
feature HEAD are reported after the push/ref verification, separately from the
acceptance code identity recorded in immutable artifacts.

The original NOT_READY audit is historical evidence, not final approval of this
correction. No integration-readiness conclusion is made here; a fresh audit
must independently assess the corrected feature HEAD and remaining findings.

Focused remediation state: **READY_FOR_P1_REAUDIT**. Integration remains
unauthorized. The next action is a fresh integration-readiness audit after
explicit user approval; no merge, main push or next-phase work is performed.
