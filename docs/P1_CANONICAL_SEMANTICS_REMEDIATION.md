# P1 canonical-semantics and snapshot-ownership remediation

Checkpoint: **2026-10-06**, Asia/Kolkata. Outcome: **READY_FOR_P1_REAUDIT**.
This is a focused N1 correctness remediation, not an integration-readiness
approval. Another independent integration audit is required. Main was not
merged or pushed; Phase E remains **BLOCKED_FOR_PHASE_E**.

## Exact checkpoints and preserved evidence

| Identity | SHA |
|---|---|
| Feature branch at start | `8fa3877f66264ab2f9309c8f5a3aa7fa225df224` |
| Implementation before N1 | `009547932e398edeef1bd2ede2ff3d10bc9e1862` |
| Verified N1 implementation | `edea3df87c0b08fdc08e66fe1df597334270dad8` |
| Protected main, local and remote | `1a4991da4dda9676caeb1d7e35a03408528c3188` |
| Frozen research branch, local and remote | `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe` |

Work continued only on `feat/p1-experiment-evaluation-foundation`. Initial
fetch verified synchronized feature/main/research refs and a clean tracked
tree. The existing untracked failed audit was preserved byte-for-byte and
committed before production changes:

- [Failed final audit](P1_FINAL_INTEGRATION_READINESS_AUDIT.md), SHA-256
  `d7b379684532b2ba76bf1fc96e552b9a86fdf576b63ba68b60f18486dac8decf`.
- Original audit, failed re-audit, TrainingSlice remediation and prediction
  remediation reports were neither edited nor replaced.
- `.agents/skills/paperclip/SKILL.md` remains untracked and unchanged, SHA-256
  `4eb4af34af6a01356ce5c58cb164b48296319c2f351b90599efbf86810254424`.

All implementation verification and acceptance below ran at the exact clean
implementation SHA above. The subsequent report/status commit changes only
documentation. Its SHA, push result and final ref/cleanliness checks are
reported in the completion checkpoint; a report cannot embed its own commit
SHA without changing that SHA.

## Independently reproduced N1

**Original finding: HIGH.** Non-string categorical objects survived canonical
snapshots while JSON fingerprints encoded their primitive numeric content.
Caller-owned behavioral metadata remained reachable by model logic.

**OBSERVED before production edits:** genuine numeric/IntEnum categorical
variants with underlying value `0` but different equality behavior produced
identical training identities and different effective transforms. The primary
reproduction yielded:

| Comparator | Native interpretation | Log interpretation under the same identity |
|---|---:|---:|
| TrainingMean | 9.625 | 7.470415055041088 |
| Direct Ridge, first forecast | 5.550083672005735 | 5.8538418522175695 |

A separate read-only root-cause reviewer used the explicit artificial sequence
`[1,2,4,8,16,32,64,128]`. Its equal-identity mean forecasts were `31.875` and
`11.31370849898476`; Ridge forecasts and coefficients also differed. Mutating
the caller's retained category after fitting changed a mean prediction to
`7.498942093324558e31` without changing its serialized identity. The independent
inventory also reproduced availability, role, partition, unit/name/origin
uniqueness and configuration/factory alias routes. These are artificial
correctness probes, not solar scientific results.

All six pre-fix baseline paths admitted an availability-policy impersonation:
an operational fitted identity could be used with unknown actual availability
because the supplied category compared equal to retrospective mode. Numeric
window/support consistency and issue-time validation themselves still passed;
the metadata controlling their interpretation disagreed with the fingerprint.

## Common root cause and established invariant

Previously category membership used equality against known strings before
normalization. Arbitrary numeric objects could answer that equality with
caller-defined semantics; JSON encoded their numeric value instead. The R1
snapshot helper stripped genuine string subclasses but returned other objects
unchanged. Constructor, snapshot, fingerprint and model therefore did not share
one interpretation. Frozen outer dataclasses did not detach these behavioral
objects or their mutable nested state. Configuration `deepcopy` also trusted
subtype hooks and preserved categorical subclasses.

The invariant was recorded before implementation:

1. Categorical declarations must be actual strings. Genuine string subclasses,
   StrEnum and NumPy strings contribute only their underlying plain string.
   `.value`, `.name`, custom equality/hash, `__str__` and numeric coincidence do
   not define a category.
2. Closed vocabularies validate that plain content before dependent branches.
   Unknown values fail; no case folding, guessing, clipping or row dropping.
3. Validation, identity and consumption use the same canonical captured state.
   Different accepted transforms/availability semantics have different IDs.
4. Capture owns strings and containers and copies numerical arrays onto
   immutable bytes owners. Caller subtype attributes and mutable nested objects
   cannot change the captured snapshot or subsequent prediction.
5. JSON object/keyword keys must be genuine strings and normalize before field
   lookup. Duplicate canonical keys fail. Actual dict/list/tuple subclasses are
   captured through their base container content, not their lookup/iteration or
   deepcopy hooks.
6. Existing F1 raw/window joins and R1 exact-base consumption snapshots remain
   mandatory at fit and predict; construction alone is not trusted.

## Categorical inventory and representations

Every row uses canonical plain `str`; fingerprints and model/validation logic
receive that same content. Numeric values, booleans, ordinary Enum and custom
`.value` objects are rejected as categorical representations. Supported JSON
string forms normalize identically to their literal string counterparts.

| Declaration | Vocabulary / validation | Identity and use |
|---|---|---|
| Forecast availability | `operational`, `retrospective_bin_end` | Spec/training IDs; availability and causal support checks |
| Forecast eligibility | `complete`, `masked` | Spec IDs; origin eligibility |
| Forecast transform | `identity`, `log10` | Spec/training IDs; all model transform/inverse paths |
| Dataset role | `synthetic_fixture`, `goes_reference` | Dataset ID; manifest/result role |
| Dataset availability policy | `explicit`, `bin_end_earliest` | Dataset ID; raw support/window availability |
| Training partition | `train` | Training identity; fitting gate |
| Temporal/config partition names | `train`, `validation`, optional `calibration`, `test`; positional chronology checks | Split manifests/IDs; raw-first partitions |
| Prediction interpretation | `native_point`, `inverse_transformed_point` | Prediction/evaluation declarations |
| Config input kind | `synthetic_fixture`, `goes_reference` | Config ID; dataset dispatch |
| Config/factory baseline name | The six implemented names only | Config ID; factory dispatch and recorded model settings |
| Config/parameter keys | Genuine strings; required/optional schema fields or constructor keywords | Config ID; resolved fields and kwargs binding |
| Pinned GOES paths | The existing manifest, preparation and sidecar literals only | Config ID; actual read-only paths |
| Feature/target names and units | Explicit nonblank ordered strings; names unique after normalization | Spec/dataset IDs; channel selection, dimensional checks and score labels |
| Dataset name/time/quality policies | Extensible nonempty declared strings | Dataset identity and provenance; no inferred instrument semantics |
| Origin IDs, dataset/split identity labels, model IDs, EventGroup IDs | Extensible strings; existing nonblank/order/uniqueness rules preserved | Alignment, training/model records and manifests |
| Supplied event definition/origin labels | Extensible explicit nonblank strings, unique origins | Returned event metadata; no new real-event definition |
| UTC configuration strings | Plain captured strings, explicit UTC validation | Resolved coordinates/config identity |
| Dataset JSON metadata | Existing finite JSON object text/bytes/bytearray input | Owned canonical JSON string; detached decoded views |
| Producer status/reason/space/phase/schema labels | Existing code-produced primitive constants and schema rules | No new caller category surface or schema change |

Masks, integer coordinates/lengths, reference/minimum scalars, model numerical
settings, probabilities and quantiles are numerical controls, not textual
categories. Existing numerical/container validation was preserved. In
particular tuples do not silently become valid configuration seeds, splits or
baseline lists. Generic JSON/fingerprint/artifact helpers remain serializers;
they are not substitutes for the forecasting/configuration validators.

## Test-first evidence and independent review follow-ups

Tests were added and executed before each corresponding production change.
Failures were missing rejection or incorrect captured/consumed semantics,
not import/setup errors. Positive controls deliberately stayed green.

| RED checkpoint | New cases exercised | Actual pre-fix result | Closure |
|---|---:|---|---|
| Initial N1, test commit `f7f678c` | 129 | **110 failed, 19 passed** | `ef45f85` |
| Numeric mapping keys and pinned-path objects, `59212da` | 24 | **19 failed, 5 passed** | `1eebb0c` |
| Public factory keyword aliases, `f11e4e4` | 22 | **12 failed, 10 passed** | `7fd9d60` |
| Dictionary-subclass capture hooks | 4 | **4 failed** | `edea3df` |

The latter three cycles resulted from executable independent review, not a
documentation claim of safety. Two additional config identities were proved:

- Numeric mapping keys aliased `lead_weights` and `target_weights`. Both configs
  shared config hash `bc8b37a2f279a2d6a36299924fa25dd3937d2dbb3ab451f8a48dd454b6d1cac9`
  and identical dataset/spec/training/split identities, but unmodified
  TrainingMean/evaluation produced aggregate MAE `2.2396377220773576` versus
  `2.3190069112604816`, and RMSE `2.264483344459194` versus `2.3449463061289673`.
- Numeric `.fspath` objects impersonated pinned path strings while selecting
  different actual paths under the same config hash. The probe validated paths
  only; it did not read alternate files or acquire data.

The fresh final reviewer then found string-subclass kwargs and a dict-subclass
lookup hook could swap Ridge lag/alpha. All four copy/reconstruction routes
reproduced each gap. Actual fitted parameter records truthfully exposed the
different settings, and config-loaded runs were already protected; this was a
remaining public factory semantic disagreement, not a hidden collision of the
entire fitted model record. The reviewed final capture closes both routes.

New coverage totals **179 parametrized cases** in
`tests/test_canonical_semantics.py`. It covers categories controlling transforms,
eligibility and availability, genuine Enum/IntEnum and `.value` objects, caller/nested
list/dict/set/array subtype state, shallow/deep copies, pickle, unchecked
subclasses and `__new__` reconstruction, all six fit/predict paths, supported
canonical string forms, actual string-key content, duplicate primitive keys,
strict collection controls, unknown names and read-only Mapping compatibility.

## Exact implementation and ownership behavior

Five existing source files changed:

- `forecasting/contracts.py`: shared base-content string/container capture;
  strict `_string`/`_category`; constructor normalization before branches;
  plain ordered names/origins/units/identities; genuine mapping keys only.
- `forecasting/splitting.py`: canonical partition and EventGroup identifiers.
- `forecasting/baselines.py`: canonical factory name and owned parameters before
  kwargs dispatch. Existing common fit/predict snapshots are still consumed.
- `experiments/config.py`: detached native-container capture before finite JSON
  and schema validation; canonical input/split categories and pinned path
  strings. No unconditional JSON round-trip that weakens strict type checks.
- `evaluation/events.py`: canonical supplied labels before uniqueness/return.

There are no algorithm, metric-formula, dependency, schema, scientific config,
data or calibration changes. This is not a model-specific correction or a
fingerprint-only patch. All six comparators use the common validated snapshots;
Ridge still fits canonical matched windows and predicts from target-free grids.

Caller-owned string subtype attributes are discarded rather than deep-copied.
Nested config dict/list/tuple content is captured into owned base containers;
dictionary capture bypasses genuine dict-subclass hooks. Non-dict Mapping uses
its declared Mapping protocol followed by canonical key validation. Dataset
metadata retains its existing JSON-only contract: finite object text/bytes/
bytearray becomes owned canonical text, and decoded views are independent.
Arbitrary Python dict/list/set/array `metadata_json` inputs remain rejected.
Arrays nested in subtype attributes are discarded; supported observation/mask/
availability arrays retain their bytes-backed immutable copies.

## Final executed verification

All following primary checks ran against `edea3df`, after normal installation
was rebuilt to match source. No warnings were suppressed.

| Check | Observed result |
|---|---|
| N1 module | **179 passed**, 0.89 s |
| Complete F1 TrainingSlice module | **53 passed**, 0.16 s |
| Complete R1 prediction module | **185 passed**, 0.50 s |
| Combined N1/F1/R1 | **417 passed**, 1.49 s |
| Complete P1 targeted suite | **659 passed, 1 warning**, 5.32 s |
| Complete repository suite | **825 passed, 1 warning**, 38.61 s |
| Installed imports, outside checkout without PYTHONPATH | **22 actual module imports**, all installed files match source |
| CLI help and four installed experiment commands | Exit **0**, outside checkout without PYTHONPATH |
| Invalid numeric availability in CLI config | Exit **2**, no artifact directory published |

Targeted command:

```sh
.venv/bin/python -m pytest -q \
  tests/test_canonical_semantics.py tests/test_prediction_context_causality.py \
  tests/test_training_slice_consistency.py tests/test_forecasting_contract.py \
  tests/test_forecasting_splits.py tests/test_forecasting_windows.py \
  tests/test_baselines.py tests/test_trajectory_metrics.py tests/test_event_metrics.py \
  tests/test_experiment_provenance.py tests/test_experiment_reference.py \
  tests/test_experiment_runner.py
.venv/bin/python -m pytest -q
```

Warning retained at
`test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability`:

```text
RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject
```

A first targeted attempt after the initial source fix had one expected installed/
checkout mismatch (608 other cases passed); the old installed contracts file was
stale. Rebuilding the package corrected that mismatch. A preliminary
`--no-build-isolation` install failed because setuptools was absent from the
runtime environment; normal declared build isolation succeeded. Final normal
`pip install --no-deps --force-reinstall .` succeeded, preserving runtime
dependencies. Final wheel SHA-256:
`8906efe453312599e6ea8754ba2c74eb64fff2887c4f7316e6499ea6f3638eb1`.

Observed environment: Python 3.13.3, macOS 26.3 arm64, package 0.1.0. Provenance
records the actual installed files under `.venv/lib/python3.13/site-packages`,
package versions, Git commit/branch, clean tracked state and all 22 hashes.
The CLI remains the supplied `scripts/run_experiment.py` wrapper importing the
installed distribution; no new installed console-entry-point claim is made.

## Fresh acceptance, identities and artifact verification

The old failed audit correctly stopped before full/acceptance verification.
These are newly executed bounded acceptance pairs after correctness tests and
closure of the independent reviewer findings. All six models and all three
seeds score train, validation and test: **54 successful scores per run, zero
model failures**, complete status and target-free prediction interfaces.

| Dataset | Execution IDs, a / b | Retained origins, train / validation / test |
|---|---|---|
| Synthetic | `bab775aec5a3450fadea72eb2bd84b11` / `82c8cfd0063646aea4afb48b07439cd5` | 112 / 52 / 52 |
| Pinned GOES | `84488b142839487790caa08795710ca0` / `17844ced6f4d49208b5c3a37c921f751` | 103 / 62 / 103 |

Command pattern, executed from `/private/tmp`:

```sh
env -u PYTHONPATH /Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -B \
  /Users/nealsalian/Desktop/SolarJEPA/scripts/run_experiment.py \
  --root /Users/nealsalian/Desktop/SolarJEPA \
  --config configs/experiments/p1_synthetic.json \
  --output-dir results/experiments/p1_canonical_20261006_synthetic_a
```

Second synthetic uses `_synthetic_b`; GOES uses `p1_goes_reference.json` and
`_goes_a`/`_goes_b`. These four result directories are ignored local artifacts.
The GOES adapter only verified/read the existing pinned sources, preparation
and historical sidecar; no sidecar or scientific source was modified.

Source fingerprint:
`203d0a05d46a75e968ae31e8457b19dc3c7d6c0004b5b1e64616308ca9a6ef9c`.

Canonical datasets, chronological windows and raw training support were rebuilt
from actual inputs. Each result's config/dataset/split/source/training hashes
and all three seed-tagged semantic experiment IDs were checked by SHA-256 over
canonical content. Every one of the 18 fitted records per run names the rebuilt
effective training hash; all predicted/scored records preserve common origins.

| Effective training identity | SHA-256 |
|---|---|
| Synthetic | `17387eddad257ef19ec90bbc17207a8714a94060f59b96f9712efd0c15172dc7` |
| GOES | `26d9521b28c91bc645b48771c11af9b4ffc65898d6c7aeffe1028b6c153b835c` |

All four indexes verified nine files each, with independent byte/size hashes.
Eight JSON artifacts were byte-identical within each pair: resolved config,
dataset manifest, split manifest, provenance, model parameters, predictions,
metrics and failures. Execution UUIDs differ. `result.json` and its index digest
vary with UUID/path/timestamps; whole directories are not byte-identical.
Four relocated scratch copies verified, then all four corrupted prediction
files were rejected with `Artifact identity mismatch: predictions.json`.

The seven stable non-provenance artifacts were also compared against the valid
R1 acceptance pair's first run for each dataset and remain byte-identical.
Config/dataset/split/training hashes are unchanged for valid declared categories.
Source/provenance and therefore semantic experiment IDs change as expected with
the corrected implementation. No identity schema or fingerprint-only workaround
was needed. Invalid categories reject before publication; existing structured
model-failure/common-coverage tests remain green.

This demonstrates deterministic **same-environment** semantic reruns and
byte identity for the named artifacts only. Installation was rebuilt in the
existing environment; a clean independent environment, wheel-byte
reproducibility and cross-platform reproducibility were not demonstrated.

## Scientific-state preservation

Fresh SHA-256 comparisons before and after acceptance matched **109/109**
entries in the pre-P1 inventory, with zero changed/missing files. Inventory
SHA-256: `3d7a29667d871ad037468d683f412ee3874ba7eb7c6ee15e91bb0587bc586193`.
The selection contains 1 skill, 6 config, 70 data and 32 result entries,
including placeholders/housekeeping files; it is a preserved-file inventory,
not 109 independent scientific certifications. Scientific configs/manifests,
raw archives, prepared data/sidecar and frozen gate identities remain unchanged.

D.1 manifest gate is `BLOCKED_FOR_PHASE_E`; the historical E manifest remains
`BLOCKED`. No new authoritative evidence resolves SoLEXS timing/bin semantics,
GTI/exposure, housekeeping compatibility, PI/response mapping, calibration,
alignment or defensible real-event definitions. GOES smoke success validates
infrastructure only. No Phase E, acquisition, ARCH/GARCH or SolarJEPA training
was performed.

## Independent review and workflow effects

Read-only root-cause and categorical/ownership inventory agents inspected code
and executed pre-fix probes. A separate initial adversarial reviewer found the
numeric configuration-key/metric collision. A fresh final reviewer, who authored
no implementation change, inspected actual source/tests and discovered both
factory variants. It rechecked the fixes and ran:

- **417 focused tests**, independently.
- **686 bounded independent public-API probes**, zero failures, covering all six
  fit/predict paths, categorical types, reconstruction and nested container
  hooks, units/labels, configuration keys and pinned paths.
- **8 factory copy/serialization variants** and **6 Mapping variants**.
- The same 686/8/6 probes against the installed package outside checkout with
  PYTHONPATH unset.

Final scoped verdict at `edea3df`: **PASS; no surviving related BLOCKER/HIGH**.
Probe counts are not added to pytest totals or treated as different scientific
observations merely because source and installed variants were repeated.

Superpowers systematic debugging traced equality/serialization/ownership
through actual model consumption before correction. TDD retained four RED
checkpoints and positive controls before code changes. Parallel review separated
root cause, whole-field inventory and fresh general-invariant attacks; it
materially changed the fix by finding config and factory gaps. Code review drove
bounded follow-up tests/fixes, not unverified acceptance of suggestions.
Verification-before-completion kept downstream acceptance gated on correctness,
fresh suite results, installed parity, artifacts and preserved identities.

Primary scratch evidence is under
`/private/tmp/solarjepa-p1-n1-remediation-20261005`, including RED/GREEN/test logs,
`installed-verification.json`, `acceptance-verification.json`,
`valid-workflow-parity.json`, `scientific-preservation-final.json` and
`final-review-v2/REVIEW.md`. This local scratch path is supplementary and
ephemeral; the tracked regressions, historical report and this report retain the
reproducible contract/evidence summary.

## Remaining limitations

- Historical F3-F9 were not repaired or reclassified by this focused task:
  artifact symlink/tree containment, Git-quoted untracked-path gating, extreme
  squared-loss underflow, duplicate dataset metadata keys, explicit mutation of
  fitted settings, malformed numeric/index handling and dimensional-log
  intermediates retain their failed-audit limitations. Ordinary copied array
  writability likewise remains distinct from protected model consumption.
- **LOW, nonblocking pre-existing numeric-input observation:** a custom int
  subtype can pass range validation before `int(value)` returns zero. All six
  fit snapshots reject a malformed zero-context spec. A malformed trailing-mean
  constructor records lookback zero, fits, then raises IndexError at prediction.
  No hidden effective-identity disagreement was established. This falls outside
  the authorized categorical correction; normal strict JSON config rejects the
  numeric subtype. It was documented, not silently repaired.
- The existing NumPy/netCDF warning remains unresolved.
- Custom non-dict Mapping input is captured through its declared protocol;
  validation is not a sandbox against arbitrary Python code, malicious hooks,
  concurrent interpreter mutation or explicit estimator tampering.
- No clean-environment/cross-platform or scientific-readiness claim follows
  from these same-environment checks.

## Traceable commits and next gate

| Commit | Purpose |
|---|---|
| `bb044b9376fcae1de3a4bd1a288602baf621ed7c` | Preserve failed final audit unchanged |
| `f7f678ca02c015681d4f70a238cc8ea1321c0a33` | Initial failing canonical-semantics regressions |
| `ef45f851b4d49cb242770ed42a59ddbf13f76ef9` | Shared canonical categories and owned containers/labels |
| `59212da68d3b268f8e96386c5be282764efdbf4c` | Reproduce config key/path identity collisions |
| `1eebb0c8be37cd0186772e5091767590b0bae616` | Reject ambiguous config keys and pinned path objects |
| `f11e4e4b6893a7899cf5e3a4f1ea288729bd827c` | Reproduce public factory keyword aliases |
| `7fd9d604c9248bfe5227d1fd2fdc42e822fff770` | Canonicalize public factory parameter keys |
| `edea3df87c0b08fdc08e66fe1df597334270dad8` | Capture dictionary parameters without subtype hooks; verified implementation |

The final documentation commit adds this report and updates README/status plus
an implementation-report addendum. It changes no source/tests/config/data/package
identities. Only the feature branch is authorized for publication; main and the
research branch remain preserved. A new integration-readiness audit must assess
the complete candidate, historical limitations and integration before human
approval. **READY_FOR_P1_REAUDIT** is the remediation stop state.
