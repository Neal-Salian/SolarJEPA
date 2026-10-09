# GOES external validation implementation and reproduction

Date: 2026-10-09. Overall status: **PARTIALLY_VERIFIED**. Scientific definitions,
primary sources, literature and limitations are in
[the research report](GOES_EXTERNAL_VALIDATION_RESEARCH.md).

## Scope and preservation

Exact base: `656e540162c635d4c2274b4469ae11247290f986` (P2).
Branch: `research/goes-external-validation`, created and published with upstream
tracking before implementation. Implementation acceptance source commit:
`8f41ab2f7fac59fc12152040af32e10c69563091`.
Later reporting commits do not alter that executed source snapshot.

Only new milestone files were added. Existing acquisition, quality, forecasting,
split, baseline, training and metric modules/tests/configuration are unchanged.
No models, checkpoints, baseline forecasts or observational skill estimates were
run. No P3 code was imported. No SoLEXS values were combined with GOES.
No main/P3/Phase E/provisional branch was modified, and no merge, rebase,
history rewrite, force-push, branch deletion or PR was performed.

The original checkout remains on exact P2 with its pre-existing untracked
Paperclip skill and `docs/P1_FINAL_INTEGRATION_REAUDIT.md`. A before/after
SHA-256 check found **446 original regular data/config and experiment-root JSON
files unchanged**, including ignored scientific inputs and frozen experiment
identities. This bounded check does not claim to hash every ignored scratch file.
Protected local/remote refs were checked independently. Main remains
`1a4991da4dda9676caeb1d7e35a03408528c3188`.

## Inputs and measured preparation

| Quantity | Verified observation |
|---|---|
| External dataset | `external-goes16-january2025-science-avg1m-v2-2-1` |
| Observation interval | `[2025-01-01T00:00:00Z, 2025-02-01T00:00:00Z)` |
| Native files/bytes/records | 31 / 9,119,470 / 44,640 |
| Spacecraft/instrument/product | GOES-16 / EXIS-XRS FM1 / L2 science avg1m v2-2-1 |
| Missing/duplicate/off-grid timestamps | 0 / 0 / 0 |
| Valid XRS-A / XRS-B minute bins | 39,170 / 44,317 |
| Quality-rejected A / B bins | 5,470 / 323 |
| Raw nonfinite A / B | 313 / 313 |
| Flare authority | NOAA NCEI science composite annual 2025 v1-0-1 |
| Annual catalog records | 3,277 |
| January onset/peak-selected events | Both 278: C=235, M=40, X=3 |
| January spacecraft sources | 275 GOES-16; 3 GOES-18 (all C) |
| January missing ends / sequential-number>1 / saturated | 26 / 26 / 0 |
| Context/horizon/stride | 120 / 30 / 30 minutes |
| Candidate/retained/excluded origins | 1,488 / 1,007 / 481 |
| Valid target cells | 60,420 |
| Valid mature retained labels | 1,007 for each C1.0/M1.0/X1.0 task |
| Catalog-positive retained windows C+/M+/X+ | 194 / 39 / 3 (not event counts) |

Both channels have status counts zero=44,325, bad=313, interpolated=2. P2
electron-correction and channel-specific rules add exclusions beyond status
flags. Partial-minute means with 1–59 samples may remain if all existing rules
pass. No local interpolation/fill or hidden spacecraft replacement occurs.
Prepared context/target values are native W/m²; the unchanged forecast
specification records the fixed log10 transform without fitting statistics.

Machine-readable records:

- `data/manifests/goes_external_january2025.json`: exact official daily URLs,
  product/version, size/hash, acquisition UTC and coverage identity.
- `data/manifests/flare_catalog_2025.json`: CSV and metadata snapshot identities,
  acquisition UTC, parsing result and completeness caveat.
- `data/manifests/goes_external_research_sources.json`: official document and
  bounded SWPC cross-check identities plus original literature URLs. Unknown
  reconnaissance acquisition times are null, separate from registration time.
- `data/manifests/datasets/goes_external_january2025.json`: observed summary,
  dataset/split/label/source fingerprints and prepared artifact sizes/hashes.

Catalog CSV SHA-256:
`287c9ee0961e221368f3580c6e159e8dc17ef7607d02442dabf3ab48fa8c6c88`.
Metadata snapshot SHA-256:
`4a8af6ecce0df30d851b8500d362de537bb6e92646a4fc499fcf691a7eef68fb`.
Dataset fingerprint:
`b4ff51eff9d8a3d85f30375c07b7623915cd09be9c8f82e26ca17dca13dfcd7c`.
Preparation fingerprint:
`55ad86e40eb9455c9b4cbe1f60a1b00b9336ca00946417c5016c809ca8583c59`.
Executed source fingerprint:
`4ea44fda6ade364611e32d4c3c6a6608b61c5b6dfbbb1bba5080f10e9170507a`.

## Implemented interfaces

`data.flare_catalog` strictly acquires/verifies the bounded pinned 2025 product
and parses immutable `FlareEvent` records. It preserves original ID, row, UTC
start/peak/optional end, recorded class, flux/source, sequence/saturation and
catalog hash. Exact duplicate rows are flagged/collapsed; conflicting IDs or
invalid required fields fail closed. Missing ends remain null.

`data.external_validation` reuses P2 native validation and canonical P1/P2
`TimeSeriesDataset`, `ForecastSpec` and raw-axis test-window construction. It
pins the exact July ledger, rejects any raw-support overlap and constructs
one external test partition without `TrainingSlice`. JSON hashes identify the
same bytes parsed; source/config/raw identities are rechecked before publication.
Normal installed-package/source matching and P1 atomic no-replacement publication
are mandatory. External fitting and tuning have no implementation path here.

`evaluation.flare_alignment` aligns known support without timestamp snapping,
retaining catalog and dataset identities plus quality/boundary/overlap/unknown-end
diagnostics. Labels mean catalog onset in `[issue, horizon_end)` with eventual
recorded class at least C1.0/M1.0/X1.0. Every candidate onset, including a
subthreshold candidate used for a negative, requires valid start-to-peak B support
and maturity through its complete peak minute. Source mismatch, saturation,
off-minute times, missing/invalid support and unresolved maturity prevent scoring.
Separate label artifacts never enter predictor contexts.

`evaluation.external_flux.evaluate_external_flux(targets, prediction, persistence)`
reuses strict canonical snapshots and grid alignment. It supplies MAE/RMSE,
channel/lead analysis, common-mask persistence MAE/MSE skill, coverage, per-origin
losses and an evaluation-input fingerprint. Full finite predictions are required;
observation masks alone control support. Empty/zero-reference scores are null
with reasons. Overflow and nonzero square/reduction underflow fail explicitly.
Incompatible channel units prevent pooling. Train-scaled MASE remains undefined.

For explicitly supplied event decisions/probabilities, reuse unchanged P1
`evaluation.events.evaluate_events`: precision, recall/POD, FAR, FPR, F1, TSS,
HSS2 and Brier score with valid/mature masks and undefined-score reasons.
No automatic flux-to-event conversion is implemented or scientifically validated.

`evaluation.event_matching.match_events` accepts alarm issue/expiry intervals,
event onsets and a frozen decision-policy ID. Deterministic maximum-cardinality
one-to-one matching reports POD/FAR/precision/recall/F1 and nominal lead times,
including zero-lead warnings. Event lists do not define true negatives; event-level
TSS/HSS are consequently not computed. These are software capabilities verified
with synthetic fixtures, not real model results.

`evaluation.uncertainty.paired_block_bootstrap` jointly resamples whole
nonoverlapping UTC calendar blocks on the full regular origin axis, with common
missing-target positions, pooled sums/counts, a deterministic seed and descriptive
percentile intervals. Asymmetric model missingness fails. Caller-supplied scalar
origin losses must retain joint channel/lead/quality support. It does not implement
event-score uncertainty or establish independent blocks/statistical significance.

## Reproduction commands

Use a separate clean checkout/worktree on this branch. Preserve any existing
environment and ignored scientific files. Requirements already belong to P2;
no dependency declaration changed. An example new environment is:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install torch==2.6.0
.venv/bin/python -m pip install --no-deps .
```

Torch is required by inherited training tests, not by the external utilities.
The verified host used Python 3.13.3, NumPy 2.2.6, pandas 2.3.3, xarray 2026.7.0,
netCDF4 1.7.2, pytest 9.1.1 and torch 2.6.0. For this execution, a separate
task-local environment reused installed scientific dependencies read-only and
received its own normal package installation. The original environment was not
modified. Reinstall the package after source changes; tests' `src` injection
does not prove installed CLI correctness.

Acquire/verify only the explicit external inputs:

```bash
.venv/bin/python scripts/acquire_goes_history.py --config configs/data/goes_external_january2025.json
.venv/bin/python scripts/acquire_goes_history.py --verify --manifest data/manifests/goes_external_january2025.json
.venv/bin/python scripts/acquire_flare_catalog.py --config configs/data/flare_catalog_2025.json
.venv/bin/python scripts/acquire_flare_catalog.py --verify --manifest data/manifests/flare_catalog_2025.json
.venv/bin/python scripts/prepare_external_validation.py --config configs/evaluation/goes_external_january2025.json --output-dir results/experiments/goes-external-january2025-new-run
.venv/bin/python -m pytest -q
```

The GOES CLI defaults still select July: **always supply the external config or
manifest above**. Output must be a new single directory under
`results/experiments/`; existing output is refused. CLIs support `--root` for a
relocated repository and resolve default roots from script location. Do not
replace raw files, force-add ignored paths or modify pinned manifests to accept
changed remote bytes.

The unversioned metadata URL may change. A mismatching/missing pinned resource
is **BLOCKED_DATA**: use the retained exact snapshot or obtain separately reviewed
versioned evidence. Never silently repin. Creating a new logical acquisition ledger changes acquisition/registration
lineage. Restoring missing pinned payloads under a retained committed ledger
preserves its original logical acquisition identity; local recovery times are
separate audit evidence. Exact manifests/raw identities are required to reproduce
this dataset identity; a new Git commit also changes code provenance, even when
scientific preparation is identical.

A bounded actual clean-copy recovery additionally downloaded and verified both
634,597-byte-total catalog resources while preserving the committed ledger. Local
recovery UTC was 2026-10-09 14:00:51.931422 through 14:00:55.100858; it does not
replace the original logical acquisition timestamps. Later mutable metadata
changes can still block this operation.

The preparation emits 13 ignored files: artifacts.json, contexts.json,
dataset_manifest.json, event_alignment.json, future_grid.json, onset_labels_C.json,
onset_labels_M.json, onset_labels_X.json, provenance.json, resolved_config.json,
summary.json, targets.json and window_manifest.json. No predictions/scores exist.

## Executed verification and review

| Check | Observed outcome |
|---|---|
| Inherited exact P2 full suite before changes | 1,084 passed; 1 warning; 89.99 s |
| Final full suite after all source fixes | 1,272 passed; 1 warning; 78.45 s |
| Final eight new focused test files | 188 passed; 1 warning |
| Normal installed CLI acquisition/verification | Existing pinned bytes verified; immutable ledgers unchanged |
| Preparation C launched from `/tmp`, normal installed package | Success, clean source commit recorded |
| Preparation D from repository root | Success; all 13 files byte-identical to C |
| Source compile/import verification | compileall passed; every recorded package import is installed_distribution |
| Whitespace/inventory/ignore verification | git diff checks and scientific-storage checks passed |
| Original scientific/config/experiment identities | 446 checked, 0 changed |

The unsuppressed inherited warning is `RuntimeWarning: numpy.ndarray size changed,
may indicate binary incompatibility. Expected 16 from C header, got 96 from
PyObject`. It remains a disclosed environment limitation. Software tests do not
establish physical label completeness or operational readiness.

Synthetic fixtures cover official URL/product/version identity, download
size/hash failures, schema/timestamps/missingness/native quality, duplicate and
conflicting events, class boundaries, UTC onset/peak/end support, gaps, boundaries,
overlaps, saturation/source mismatch, all-candidate maturity, zero-event provenance,
causal contexts, no fitting, grid/target/prediction identity, hand-derived metrics,
zero/rare events, deterministic one-to-one matching, paired temporal dependence,
unequal blocks and missingness, immutable publication and changes to seven consumed
input types. They are distinguished from actual-data validation.

Independent code/scientific reviews and a fresh-context final reviewer identified
and resolved: all-candidate peak maturity/support for negative labels; asymmetric
bootstrap missingness; consumed-input hash/parse/publication races; frozen-ledger
hash/parse identity mismatch; nested malformed configuration handling; and
nonzero squared-loss/reduction underflow; and missing-payload restoration under
a committed catalog ledger. The review also corrected the documented prediction
constructor to use the point_interpretation keyword. Regression tests failed before fixes
and passed afterward. The independent reviewers checked the important fixes;
no unresolved actionable finding remains in the reviewed scope. Detailed execution
logs/review reports remain ignored under `results/external_research/`.
Concurrent early suite attempts encountered intentional RED-state tests and a
stale original installed package. These were investigated, not suppressed; the
final full run uses the matching task-local package and all source fixes.

## Future P3 integration contract (not implemented in P3)

Integration requires separate authorization and joint review. This milestone
does not assert P3 currently satisfies this interface. A future prediction
adapter must provide:

| Field | Required meaning/check |
|---|---|
| Model identity | Stable model/config ID; frozen development/selection provenance |
| Checkpoint identity | Cryptographic checkpoint SHA-256 and source commit |
| Evaluation identity | Dataset ID/fingerprint, acquisition manifests, preparation/split/spec fingerprints |
| Issuance and origins | Explicit UTC nanoseconds; ordered unique origin IDs exactly matching the prepared FutureGrid |
| Horizon/bins | 30 ordered one-minute bins with exact starts/ends; first starts at issuance |
| Channels/units | Ordered xrsa_flux/xrsb_flux, native W/m²; inverse-transform log output before scoring |
| Predicted values | Full finite shape `(origin, lead, channel)` and point interpretation |
| Validity | Full prediction validity on the fixed grid; failed/partial output is an evaluation failure, never mask shrinkage |
| Observation validity | Immutable prepared target quality mask, independent of model output |
| Training/preprocessing | Frozen July/development provenance only; no January fitting, tuning or test-based model selection |
| Event labels | Catalog ID/SHA, label definition ID/version, alignment/maturity policy and ordered origins |
| Event decisions | Separately validated development-only decision/calibration policy and explicit probabilities/alarms |
| Metric configuration | Native units, common masks, lead/channel reductions, persistence identity and predeclared block settings |

Construct unchanged `ForecastPrediction(values, grid, model_id, point_interpretation=point_interpretation)`
against the independently reconstructed canonical FutureGrid and pass it to
`evaluate_external_flux`. Model/checkpoint and development provenance must accompany
the surrounding future evaluation record; the existing prediction dataclass alone
does not contain every required lineage field. For event scoring, align decisions
by explicit ordered origins and use the pinned label definition/valid/mature masks.
Do not derive labels or optimize thresholds from this external dataset.

## Scientific limitations and status gates

- **VERIFIED:** pinned retrospective input identities, measured native coverage/
  quality, strict catalog parsing, deterministic preparation and controlled software
  behavior. Native peaks of the 275 selected GOES-16 events were independently
  checked for timestamp/quality compatibility; this is not a new label definition.
- **PARTIALLY_VERIFIED:** candidate catalog-onset labels. Catalog physical detection
  completeness/negative coverage are UNKNOWN; three GOES-18 fallback events and
  overlapping/unknown-end events retain diagnostics. January lacks known onset/
  peak boundary-crossing rows; adjacent-year peak-indexed coverage is not guaranteed.
- **BLOCKED_EXTERNAL_EVIDENCE:** live as-issued availability and causal native
  preprocessing. December-2025 reprocessing lists adjacent-day inputs. Coordinate
  causality alone cannot establish an operational leakage-free benchmark.
- **BLOCKED_IMPLEMENTATION:** validated flux-to-event decisions and any actual
  SolarJEPA/baseline scores or observational uncertainty. No such result is claimed.
- **BLOCKED_DATA** if pinned remote bytes cannot be recovered, particularly mutable
  metadata. Acquisition cannot silently substitute or update the ground truth.

One month, three X events, complete-window selection bias and long solar temporal
dependence prevent strong generalization/significance claims. UTC day blocks with
3/7-day sensitivity are a future predeclared analysis proposal, not verified
independence. The reusable bootstrap supports paired scalar losses, not event-score
intervals. The foundation is independently reviewable; operational research claims
remain gated on the missing evidence and separately authorized experiments.

## Complete changed-file inventory

All 26 files are new except that the new milestone plan/research report receive
follow-up reporting updates within this branch. No pre-existing file is changed.

```text
configs/data/flare_catalog_2025.json
configs/data/goes_external_january2025.json
configs/evaluation/goes_external_january2025.json
data/manifests/flare_catalog_2025.json
data/manifests/goes_external_january2025.json
data/manifests/goes_external_research_sources.json
data/manifests/datasets/goes_external_january2025.json
docs/GOES_EXTERNAL_VALIDATION_RESEARCH.md
docs/GOES_EXTERNAL_VALIDATION_IMPLEMENTATION.md
docs/superpowers/plans/2026-10-09-goes-external-validation.md
scripts/acquire_flare_catalog.py
scripts/prepare_external_validation.py
src/solar_flare_jepa/data/flare_catalog.py
src/solar_flare_jepa/data/external_validation.py
src/solar_flare_jepa/evaluation/flare_alignment.py
src/solar_flare_jepa/evaluation/external_flux.py
src/solar_flare_jepa/evaluation/event_matching.py
src/solar_flare_jepa/evaluation/uncertainty.py
tests/test_flare_catalog.py
tests/test_flare_alignment.py
tests/test_external_validation.py
tests/test_external_config.py
tests/test_external_preparation.py
tests/test_external_flux.py
tests/test_event_matching_external.py
tests/test_uncertainty.py
```
