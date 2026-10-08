# P2 — Dual-Source Data and Training Foundation

Evidence date: 2026-10-08. **READY_FOR_CLAUDE_CODE_HANDOFF**, subject to human
review. This is implementation and ordinary-execution verification, not P1/P2
integration approval, actual SolarJEPA training or SoLEXS scientific clearance.

## Repository dependency and exact checkpoints

- Branch: `feat/p2-dual-source-training-foundation`, upstream same name on origin.
- Exact parent: unmerged P1 `595371190177de4638962aafa327f611b2045b90`.
- Verified P2 executable checkpoint: `a2d76f8cc561bcb412b5e2c64043e979ad59136c`.
  Final handoff commit adds documentation and a training environment lock only.
  Resolve the final tip with `git rev-parse HEAD`; executable source is unchanged.
- Protected main: `1a4991da4dda9676caeb1d7e35a03408528c3188`.
- Frozen research: `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe`.
- P1 implementation / verification: `cde534d67820bc34fbaf83a131667b72edab0016` /
  `3028ad10f3e6bcac0ce4df93650ae87465083460`.

Local/fetched refs and checkpoint ancestry were independently checked before
branch creation. P2 was published from the exact P1 tip before implementation.
P1 remains **NOT_READY_FOR_INTEGRATION** because its generalized alternate-module
source review remains incomplete after the reported external restriction. That
question was not adjudicated by P2. No protected branch was merged or pushed.
The local untracked final P1 audit and Paperclip tooling remain unchanged.

## Implemented and verified paths

| State | Capability |
|---|---|
| IMPLEMENTED + VERIFIED | Bounded official NOAA acquisition, immutable pinned resume and complete month inventory. |
| IMPLEMENTED + VERIFIED | Native GOES identity/time/units/quality validation, explicit missingness, P1 raw partitions and windows. |
| IMPLEMENTED + VERIFIED | All six fixed P1 baselines on actual historical flux, indexed artifacts, failures and native-unit evaluation. |
| IMPLEMENTED + VERIFIED | Existing real SoLEXS native loaders, bounded summaries/plots, common identities and explicit blocked task dispositions. |
| IMPLEMENTED + VERIFIED | CPU PyTorch smoke batching, masks, train-only normalization, optimizer, validation monitoring, checkpoints, reload, inference and P1 evaluation. |
| PLANNED | Actual SolarJEPA representation learning, predictive embeddings, autoregressive forecasts and optional physics conditioning. |
| BLOCKED | SoLEXS model-ready absolute chronology/calibration, forecasting, alignment and domain transfer under Phase E. |

## GOES acquisition and native validation

**DOCUMENTED:** official NOAA/NCEI GOES-16 EXIS/XRS L2 science one-minute
products, version 2-2-1. Full July 1–31, 2024 was selected by calendar and nominal
SoLEXS overlap before metrics or quality outcomes. Sources and authoritative
time/quality definitions are linked in [the source assessment](P2_GOES_SOURCE_ASSESSMENT.md).

**OBSERVED:** the prior reference is six verified files: three avg1m plus three
flsum, 4,320 flux rows, July 1–4 half-open UTC. Valid XRS-A/B bins: 2,267/4,318.
Its catalogue has 94 state records and 28 distinct flare IDs; states were not
promoted into supervised event labels. This reference alone is too small for
generalizable evaluation.

**OBSERVED:** new [acquisition manifest](../data/manifests/goes_p2_july2024.json)
pins 31 flux files, **9,200,347 bytes**, range 291,557–300,863 bytes/file.
July 1–3 are independent copies of the existing pinned raw files; 28 files were
downloaded from official URLs. Original six files/manifests are unchanged.
Raw files are ignored beneath
`data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/07/`.
Config: `configs/data/p2_goes_july2024.json`. Every filename, URL, nominal date,
size, SHA-256 and copy/download lineage is in the tracked small manifest.

Acquisition is sequential, capped at 1 MiB/file and 31 MiB selected output, with
30-second timeouts, at most three attempts, TLS, no redirects, no-replace raw
publication and atomic per-file resume ledger. Disk free space was checked
before acquisition: 5.1 GiB available, versus approximately 8.77 MiB selected raw
output. The CLI does not implement an automatic disk-space preflight.
Checksums are local observed identities, not NOAA-issued hashes. Writers must
be serialized; an unpinned crash orphan is deliberately refused. Integrity and
science validation are separate stages. Fresh-clone pinned reacquisition is
possible without the original reference copy because official URLs and ledger
pins remain available; a source revision fails rather than replacing bytes.

**OBSERVED validation:** 44,640 native one-minute rows, July 1 00:00 to August 1
00:00 UTC, no duplicates, off-grid timestamps or absent bins. Native IDs,
platform `g16`, EXIS instrument, documented clock/unit/flag schemas and coverage
are checked. Primary channels are electron-corrected `xrsa_flux` (0.05–0.4 nm)
and `xrsb_flux` (0.1–0.8 nm), both W/m2. Native `xrs_primary_chan` records detector
selection; these are primary composite channels, not a constant assumed detector.

| Quantity | XRS-A | XRS-B |
|---|---:|---:|
| Valid native bins | 42,329 | 44,406 |
| Quality-rejected bins | 2,311 | 234 |
| Nonfinite raw bins | 208 | 208 |
| Nonpositive finite raw bins | 0 | 0 |
| Native status=bad / interpolated rows | 208 / 16 | 208 / 16 |

Invalid/interpolated bins remain masked and their raw payload/flags are retained
in native diagnostics. No new interpolation or future imputation occurs. The
adapter can represent genuinely absent grid bins as null/NaN with false masks
and `observed=false`; no native row can be silently discarded by reindexing.

**INFERRED benchmark assumption:** completed bins are available at bin end for
retrospective forecasting. **UNKNOWN:** actual operational delivery at historical
issue times. These are revised science-archive products, not contemporaneous
operational data. Feature causality is verified under the retrospective contract;
operational replay or live availability is not established.

## Dataset, splits and leakage

Config: `configs/experiments/p2_goes_july2024.json`. Two native flux channels,
60-second cadence, context 120 bins, horizon 30 bins, stride 30 bins, complete
selected context/target masks. Bounds are half-open and raw support is partitioned
before windows. Entire context and future target support stay inside one split.

| Split | UTC start | UTC end, exclusive | Raw bins | Candidate origins | Retained | Excluded | Valid target cells |
|---|---|---|---:|---:|---:|---:|---:|
| Train | 2024-07-01 00:00 | 2024-07-22 00:00 | 30,240 | 1,008 | 855 | 153 | 51,300 |
| Validation | 2024-07-22 00:00 | 2024-07-27 00:00 | 7,200 | 240 | 199 | 41 | 11,940 |
| Test | 2024-07-27 00:00 | 2024-08-01 00:00 | 7,200 | 240 | 209 | 31 | 12,540 |

Exclusion reasons/support are retained in split manifests. Coverage is not
100% of candidate origins: retained fractions are 84.82%, 82.92%, 87.08%.
All retained target cells are scored for every successful baseline. Targets do
not overlap between splits; stride=horizon also avoids overlapping future target
bins within each split. Contexts overlap, so origins are not claimed independent.
No random-window split, test optimization, outside-train scaler or label rule is used.

Log transforms are dimensioned `log10(F / (1 W/m2))`; forecasts are mapped back
with `1 W/m2 * 10**z` before physical-unit evaluation. Neural standardization
uses unique valid raw train bins, counts 28,157/30,234 for A/B, not window frequency.
Log means are -7.074270047880273 / -5.530090791417979, population standard deviations
0.43951272758830684 / 0.2543550984644398. Invalid tensor cells become normalized
zero alongside false masks; original data remain NaN/masked.

## Six-baseline actual experiment

Seed 17 is an identity tag; the six existing comparators are deterministic.
Fixed lookbacks: trailing mean/drift 30; direct ridge 10 lags, alpha 0.1; AR(1)
fits fixed train-only adjacent raw pairs. Training mean uses unique raw support
in the declared transform space, then inverts its point forecast. All parameters
were fixed before held-out evaluation. Train scores are in-sample diagnostics.

**OBSERVED:** 18/18 model-partition scores, zero model failures. Validation has
199 common origins / 11,940 target cells; test 209 / 12,540 for every model.
MAE/RMSE below pool equal-weight A/B cells; skill is separately reported per
channel as `1 - model MAE / persistence MAE`.

| Partition | Baseline | MAE (W/m2) | RMSE (W/m2) | MAE skill A | MAE skill B |
|---|---|---:|---:|---:|---:|
| validation | persistence | 4.06962282e-07 | 1.60887312e-06 | 0.000000 | 0.000000 |
| validation | training_mean | 7.94384340e-07 | 1.99529041e-06 | -0.260328 | -1.039944 |
| validation | trailing_mean | 5.10583581e-07 | 1.79497518e-06 | -0.111370 | -0.272839 |
| validation | drift | 6.90855159e-07 | 3.48909012e-06 | -0.998448 | -0.659330 |
| validation | ar1 | 3.89227355e-07 | 1.57257982e-06 | 0.108389 | 0.035337 |
| validation | direct_ridge | 3.86181159e-07 | 1.51961331e-06 | 0.150025 | 0.038479 |
| test | persistence | 1.98801483e-06 | 7.82381037e-06 | 0.000000 | 0.000000 |
| test | training_mean | 2.75914618e-06 | 7.76897873e-06 | 0.022533 | -0.461659 |
| test | trailing_mean | 2.25981714e-06 | 7.06747964e-06 | -0.019671 | -0.157759 |
| test | drift | 9.23019385e-06 | 1.21354599e-04 | -11.671628 | -2.199861 |
| test | ar1 | 1.78477892e-06 | 7.23030955e-06 | 0.202528 | 0.084203 |
| test | direct_ridge | 1.40344566e-06 | 6.31374783e-06 | 0.315772 | 0.290142 |

These are descriptive results for one month and one fixed split, with no
confidence interval or claim of generalizable flare prediction. The drift's
large errors and negative skills are retained. Event labels/distributions,
event-risk metrics, calibration and probabilistic forecasts are NOT_DEFINED here.

## Real SoLEXS pathway and remaining gates

**OBSERVED:** both existing untouched ZIPs verified: July 1, 6,036,792 bytes,
SHA `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4`;
July 3, 6,216,112 bytes, SHA
`b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf`.
No archive was downloaded. Full ZIP/gzip/FITS/DATASUM inspection reused existing
loaders; CHECKSUM cards are absent, not declared verified.

Eight products: each archive contains SDD2 LC and Type-II PI with 86,400 rows
each, SDD2 GTI with 4/3 rows, empty SDD1 GTI. SDD2 LC/PI detector association
is OBSERVED in FILTER headers; GTI associations are INFERRED from member names.
There is no SDD1 LC/PI or HK member in this inspected collection. Native channels
are 0–339; LC/PI missing rows are 128/2. Finite LC COUNTS ranges are 3–1,554 / 2–943.
Native coordinate increments are one numeric unit. Absolute UTC remains UNKNOWN.

Four scientifically labeled native diagnostic plots and structured identities
were generated. Common `SourceIdentity` metadata retains mission/platform,
instrument, ordered channels/native units, clock/sampling, measurement, masks/QC,
preprocessing, validation status and target definition. Native details separately
retain detector evidence, column units, provenance and clock conflicts. It does
not provide a common numeric scale. GOES uses P1's UTC-interval dataset adapter;
SoLEXS remains a native inspection payload and is rejected by training clearance.
Incompatible identities and unsupported units/conversions fail.

**BLOCKED:** Phase E unchanged. Absolute time/clock conflicts, LC bin position,
GTI endpoint/exposure semantics, HK compatibility, PI-response mapping,
detector calibration/response applicability, cross-instrument alignment and
authoritative flare definitions remain unresolved. The user reports a sent
clarification email and no reply. Every evaluated candidate sequence task remains
blocked for training; descriptive native exploration is allowed. Full task-by-task
decisions and measured contents are in [SoLEXS readiness](P2_SOLEXS_READINESS.md).

Transfer feasibility: nominal SoLEXS July 1/3 filenames fall inside the GOES
calendar interval; measured common UTC coverage is UNKNOWN. Counts and irradiance,
native PI labels and XRS bands, detector responses and availability cannot be
equated. Future transfer requires accepted timing/exposure/calibration/bands,
independent SoLEXS labels/evaluation and cleared gates. No alignment or transfer
model was implemented.

## Training and model contract

**OBSERVED:** PyTorch 2.6.0, CPython 3.13.3/macOS arm64, CPU smoke model with
28,860 parameters, batch 16, two epochs, four training batches/epoch and two
validation batches/epoch. It trained 64 of 855 origins, monitored the first 32
of 199 validation origins, and evaluated the first 32 origins of each partition
(1,920 valid target cells each). Selection is predetermined chronological order.

Eight optimizer steps; normalized train losses 0.9202021025 → 0.3858939148;
validation losses 1.2186553478 → 1.2063427567. Validation selected epoch 2.
Checkpoint reload predictions are bitwise equal on all three subsets. Native
smoke MAE/RMSE: train 2.99936210e-7 / 7.85280568e-7; validation 9.52896524e-7 /
2.22056976e-6; test 1.99214280e-6 / 4.78387566e-6 W/m2. These prove infrastructure,
not scientific skill; smoke coverage differs from full baseline coverage.

The checkpoint binds source/data/spec/split/training/normalization/config, weights,
optimizer and monitoring state. Reload is weights-only, rejects contradictions,
and requires external expected identities. Model forward uses `[B,120,2]` values
plus masks and produces `[B,30,2]` normalized targets; inference inverts to W/m2
`ForecastPrediction`. No JEPA architecture, autoregressive decoder, learned
uncertainty or physics conditioning is implemented. See [model contract](P2_MODEL_CONTRACT.md).

## Verification, provenance and local artifacts

- Fresh untouched P1 parent: 971 passed, one retained ABI warning (242.92 s).
- Final P2 targeted: 113 passed, one retained warning (6.96 s).
- Existing native loader/readiness plus new exploration: 109 passed (85 old + 24 new).
- Final full repository: **1,084 passed, zero failed**, one retained warning (119.58 s),
  including unchanged historical F1/R1/N1/N2/N3 and all other 971 inherited tests.
- Normal noneditable reinstall; outside-checkout imports with PYTHONPATH absent:
  30/30 module source parity plus runtime code provenance verified.
- Independent bounded review found three MEDIUM defects; all reproduced RED and
  fixed GREEN, then full suite/actual data/acceptance passed. See [review dispositions](P2_INDEPENDENT_REVIEW.md).
- Actual source/quality/leakage checks, six baselines, native inspection, CPU smoke
  and real serialized reload executed. All three P2 indexed execution directories verify.
- 109 inherited scientific identities, 29 existing indexed experiments / 290 files,
  local final P1 audit and Paperclip bytes were rechecked and preserved.

Retained warning: `numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject`. No suppression or ABI-safety claim.
Desktop filesystem reads also intermittently stalled. First baseline execution
exited 2 before publication on source metadata change during hashing; unchanged
normal retry completed. Guards stayed enabled, source bytes/installed parity
matched, and no isolated-checkout fallback was needed.
An intermediate installed-CLI check refused the stale installed distribution;
normal reinstallation resolved it before final tests and actual acceptance.

Portable artifact roots (ignored, available locally):

| Artifact | Path |
|---|---|
| Prepared semantic data + native diagnostics, masks, splits, provenance, indexed hashes | `results/experiments/p2-goes-prepared-20261008/` |
| 18 baseline scores, predictions, fitted parameters, failures and provenance | `results/experiments/p2-goes-baselines-20261008/` |
| Training record, normalization, best.pt, reload, predictions/scores and provenance | `results/experiments/p2-goes-training-smoke-20261008/` |
| Final native report and four plots | `results/p2_solexs/20261008-native-02/` |
| Verification stdout, installed parity and compact metrics | `results/p2_verification/` |
| Preservation identities | `results/p2_preservation/` |

Native-01 is retained historical evidence from an earlier installed metadata
format; native-02 is the verified final native source. It does not overwrite old
results. Dataset fingerprint:
`521d0c87b416c4d6e33f5bd09f45ea6f7b606ceb15332f3d1414b5e7fa2c348c`.
Executable source fingerprint:
`b3e457ad7aa169d07badcb2e5e51270b1835ebeaa49d6d7976441ac56bcbf04c`.
Full identities are stored in the execution records. Final Git/data policy checks
and reproduction commands are recorded in [Claude Code handoff](P2_CLAUDE_CODE_HANDOFF.md).

## Complete P2 changed-file inventory

32 paths differ from the exact P1 parent; no raw data or generated experiment
outputs are tracked. This list includes the final documentation/lock commit.

```text
configs/data/p2_goes_july2024.json
configs/data/p2_solexs_exploration.json
configs/experiments/p2_goes_july2024.json
configs/training/p2_smoke.json
data/manifests/goes_p2_july2024.json
docs/P2_CLAUDE_CODE_HANDOFF.md
docs/P2_DUAL_SOURCE_FOUNDATION.md
docs/P2_GOES_SOURCE_ASSESSMENT.md
docs/P2_INDEPENDENT_REVIEW.md
docs/P2_MODEL_CONTRACT.md
docs/P2_SOLEXS_READINESS.md
docs/superpowers/plans/2026-10-08-p2-dual-source-training-foundation.md
pyproject.toml
requirements-training-lock.txt
scripts/acquire_goes_history.py
scripts/explore_solexs.py
scripts/prepare_goes_training.py
scripts/train_smoke.py
src/solar_flare_jepa/data/foundation.py
src/solar_flare_jepa/data/goes_acquisition.py
src/solar_flare_jepa/data/solexs_exploration.py
src/solar_flare_jepa/experiments/config.py
src/solar_flare_jepa/experiments/runner.py
src/solar_flare_jepa/forecasting/contracts.py
src/solar_flare_jepa/training/__init__.py
src/solar_flare_jepa/training/core.py
src/solar_flare_jepa/training/normalization.py
src/solar_flare_jepa/training/runner.py
tests/test_goes_acquisition.py
tests/test_p2_foundation.py
tests/test_solexs_exploration.py
tests/test_training_foundation.py
```
