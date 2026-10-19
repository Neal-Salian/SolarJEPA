# SolarJEPA P2: self-contained Claude Code handoff

Evidence date: 2026-10-08. **READY_FOR_CLAUDE_CODE_HANDOFF**, for human review.
Read `AGENTS.md` and verify Git/source/runtime state before editing. This file
is a reproducible starting point, not proof that later changes still work.
No prior Codex conversation is required.

## A. Scientific objective

Develop solar X-ray trajectory forecasting and, after separately establishing
event definitions, solar-flare risk prediction. The original instrument pathway
is ISRO Aditya-L1 SoLEXS. NOAA GOES supplies the functional retrospective flux
benchmark. Keep their identities, bands, detector responses, units, timing,
calibration and evaluation separate. A GOES experiment cannot establish SoLEXS
forecast skill. No actual SolarJEPA architecture or training is complete.

Evidence terms: **DOCUMENTED** means an applicable authoritative source;
**OBSERVED** means directly inspected files/execution; **INFERRED** means a
derived relationship; **UNKNOWN** means not established. User reports remain
attributed. Never replace missing scientific facts with guessed values.

## B–D. Repository state, dependency and exact SHAs

Repository location on this Mac: `/Users/nealsalian/Desktop/SolarJEPA`.
Only P2 branch `feat/p2-dual-source-training-foundation` was changed/pushed;
upstream is `origin/feat/p2-dual-source-training-foundation`. It depends on
**unmerged P1**, not main. The user's specific P2 branch instruction overrides
the repository's default main-based milestone rule.

| Reference | Verified SHA |
|---|---|
| P2 parent / local and origin P1 | `595371190177de4638962aafa327f611b2045b90` |
| P2 executable implementation verified by final acceptance | `a2d76f8cc561bcb412b5e2c64043e979ad59136c` |
| Protected local and origin main | `1a4991da4dda9676caeb1d7e35a03408528c3188` |
| Frozen research checkpoint | `805f1c3f8bc0d4218fb4f4e6f8b511ea456e5ffe` |
| P1 implementation checkpoint | `cde534d67820bc34fbaf83a131667b72edab0016` |
| P1 verification checkpoint | `3028ad10f3e6bcac0ce4df93650ae87465083460` |

The final handoff commit adds these documents, plan completion and the optional
training environment lock, without executable changes. Get that exact full tip
from Git; a commit cannot embed its own hash:

```bash
git branch --show-current
git rev-parse HEAD
git rev-parse origin/feat/p2-dual-source-training-foundation
git log --format='%H %s' 595371190177de4638962aafa327f611b2045b90..HEAD
git status --short --branch
```

P2 implementation commits, oldest first:

1. `8650896fd839417808489c1e0a4d26c6640cec1d`: leakage-safe historical GOES foundation.
2. `3eb48d637b427ac357845d617a78271832363662`: pinned NOAA acquisition and manifest.
3. `7920111afb11170568566df1b826ea3c36bfcfc7`: gated native SoLEXS diagnostics.
4. `8b0066ec536fcb27e91ee04dd631bd88aad44153`: bounded deterministic smoke training.
5. `a2d76f8cc561bcb412b5e2c64043e979ad59136c`: native/checkpoint consistency regressions and fixes.

P1 remains **NOT_READY_FOR_INTEGRATION**. Its generalized alternate-module source
audit was incomplete after an external tool/product restriction; P2 did not
resolve that question. Passing tests and handoff readiness are not integration
permission. Do not merge P1/P2, push main, rewrite shared history, delete
milestone branches or alter frozen research without action-specific approval.

## E–F. Implemented versus verified versus future work

| State | Functionality |
|---|---|
| IMPLEMENTED + VERIFIED | Official bounded GOES daily acquisition/resume, pinned raw integrity and complete July inventory. |
| IMPLEMENTED + VERIFIED | GOES native validation, explicit masks, source metadata and P1 chronological dataset/windows. |
| IMPLEMENTED + VERIFIED | Six fixed P1 baselines on actual July flux; physical-unit scores, skill, coverage, failures and indexed artifacts. |
| IMPLEMENTED + VERIFIED | Two existing SoLEXS archives, native metadata/LC/PI/GTI diagnostics, four plots and task readiness dispositions. |
| IMPLEMENTED + VERIFIED | CPU tensorization, masks, train-only normalization, deterministic optimizer/validation loop, checkpoint save/reload, inference and P1 evaluation. |
| IMPLEMENTED, actual device run untested | Explicit MPS capability selection; CPU is verified and default. |
| PLANNED | SolarJEPA encoder, temporal predictive embeddings, JEPA losses, forecasting head/decoder and optional justified conditioning. |
| BLOCKED | SoLEXS scientific sequence training, calibrated time/flux, flare labels, cross-instrument alignment and transfer. |

Detailed measured results and all twelve validation/test baseline rows are in
[P2 foundation](P2_DUAL_SOURCE_FOUNDATION.md). Source/authority details are in
[GOES assessment](P2_GOES_SOURCE_ASSESSMENT.md) and
[SoLEXS readiness](P2_SOLEXS_READINESS.md). Those reports supplement source and
artifacts; they do not replace executable checks.

## G. Existing P1 APIs to reuse

| Module | Existing interface and boundary |
|---|---|
| `forecasting/contracts.py` | `ForecastSpec`, `TimeSeriesDataset`, `ForecastContext`, `FutureGrid`, `ForecastTargets`, `ForecastPrediction`, `TrainingSlice`. Immutable canonical semantic identities. |
| `forecasting/splitting.py` | `chronological_partitions(dataset, boundaries)`; raw half-open support first. |
| `forecasting/windows.py` | `build_partition_windows(dataset, spec, partition)`; context, targets, training slice, retained/excluded origins and support manifest. |
| `forecasting/baselines.py` | `make_baseline(name, parameters).fit(training_slice).predict(context, future_grid)`. Six comparators and strict causal fit/predict contracts. |
| `evaluation/trajectory.py` | `evaluate_trajectory(targets, prediction, training, persistence=..., lead_weights=..., target_weights=...)`. Native-unit and per-channel skill/accounting. |
| `experiments/config.py` | `load_config`, `utc_ns`; strict portable resolved experiment schema. |
| `experiments/runner.py` | Existing CLI experiment execution and dataset dispatch. Historical GOES dispatch is a narrow P2 addition. |
| `experiments/provenance.py` | `code_provenance`, source verification, fingerprints, `verify_artifacts`, finite-JSON exclusive `atomic_record`. |

Do not replace the P1 fit/predict/evaluation contracts with unchecked tensor
shortcuts. Features must be available by issue time; `FutureGrid` supplies
coordinates, never future values. Preserve F1/R1/N1/N2/N3 defenses and failure
accounting. P2 modified only the supported historical role and dispatch/config
validation in those old modules; historical test files remain unchanged.

## H. GOES schema, paths and scientific semantics

**DOCUMENTED:** official [NOAA/NCEI EXIS products](https://www.ncei.noaa.gov/products/goes-r-extreme-ultraviolet-xray-irradiance)
and [July directory](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2024/07/).
GOES-16 EXIS/XRS `sci_xrsf-l2-avg1m`, version 2-2-1. Selected all July by
calendar/nominal SoLEXS overlap before observing metrics. Product documentation,
UTC convention and flags are cited in the assessment.

**OBSERVED:** 31 files, 9,200,347 bytes, 44,640 native minute rows; no absent
grid bins, duplicate or off-grid timestamps. XRS-A `xrsa_flux` is 0.05–0.4 nm;
XRS-B `xrsb_flux` is 0.1–0.8 nm; both W/m2, primary composite detectors. Valid
bins A/B: 42,329/44,406; quality-rejected 2,311/234; nonfinite raw 208 each.
Upstream interpolated rows remain masked by the strict native policy. No new
filling. The prior six reference files and 4,320 rows were independently checked
and retained; the three selected flux files were copied, the other 28 downloaded.

- Acquisition config: `configs/data/p2_goes_july2024.json`.
- Tracked ledger: `data/manifests/goes_p2_july2024.json` (schema version 1).
- Ignored raw root: `data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/07/`.
- Raw basename: `sci_xrsf-l2-avg1m_g16_dYYYYMMDD_v2-2-1.nc`.
- Experiment config: `configs/experiments/p2_goes_july2024.json`.
- Actual prepared output: `results/experiments/p2-goes-prepared-20261008/`.

Manifest fields include platform/product/version, selected interval, config path
and hash, complete flag/total bytes, and per-file path/URL/date/size/SHA-256,
source identity and copy/download time lineage. Hashes are local observed pins,
not NOAA-issued authentication. `verify_history` rereads raw pins; native science
validation separately checks IDs/platform/instrument/clock/units/flags/counts and
decoded nominal-day coverage. Resume refuses unknown or changed existing bytes;
serialize writers. Downloads have caps, retries/timeouts and no-replace paths.
Check disk space before future acquisition; the CLI has no automatic preflight.

`data/foundation.py`: `goes_training(config, root)` returns `TimeSeriesDataset`.
Its schema is `[N,F]` features and `[N,K]` targets plus boolean masks, ordered
names/units, UTC nanosecond bin starts/ends, cadence, availability and quality
policies and JSON source/provenance metadata. Invalid semantic cells are NaN
in memory, JSON null plus false masks. Native diagnostic payload retains raw
flags/values and an `observed` grid-row indicator. Missing rows can be represented
without invented observations. Use this adapter to rebuild contracts; the
prepared JSON is a regenerable semantic artifact, not a generic tensor loader.

**INFERRED retrospective assumption:** features are available at completed-bin
end. **UNKNOWN:** actual historical delivery of these revised science bytes.
No operational availability/backtest certification. No event labels were added;
native flare-summary state records are not supervised labels or event distribution.

Half-open UTC raw splits: train `[July 1, July 22)`, validation `[July 22,
July 27)`, test `[July 27, August 1)`, 2024. Raw rows 30,240/7,200/7,200;
retained origins 855/199/209, excluded 153/41/31. Context 120, horizon 30,
stride 30, two features/two targets, complete context/target masks. Entire
context/targets stay in their split; no overlapping future targets across splits
or within each split, but contexts overlap and origins are not independent.
Baseline scoring covers every retained cell; retained candidate fractions are
84.82%/82.92%/87.08%, not complete observational coverage.

Transform `log10(F / (1 W/m2))`, inverse `1 W/m2 * 10**z`; neural means/scales
fit only unique valid raw train rows. No held-out statistics or future imputation.
Dataset fingerprint:
`521d0c87b416c4d6e33f5bd09f45ea6f7b606ceb15332f3d1414b5e7fa2c348c`.

## I–J. SoLEXS schema, paths and restrictions

- Existing inventory: `data/manifests/aditya_inventory.json`.
- Existing native APIs: `data/solexs.py` (`inspect_solexs_archive`,
  `load_light_curve`, `iter_spectra`, `open_solexs_product`); reuse bounded loaders.
- Archives under `data/raw/aditya/solexs/l1/v1.1/archives/2024/07/`:
  `AL1_SLX_L1_20240701_v1.1.zip` (6,036,792 bytes, SHA
  `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4`),
  `AL1_SLX_L1_20240703_v1.1.zip` (6,216,112 bytes, SHA
  `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf`).
- New config: `configs/data/p2_solexs_exploration.json`.
- New API: `data/solexs_exploration.py`; CLI `scripts/explore_solexs.py`.
- Verified output: `results/p2_solexs/20261008-native-02/report.json` and four PNGs.
- Immutable gate: `data/manifests/solexs_phase_d1_requirements.json`, SHA
  `130913b5059895423799d36e265ce768271c060cc2b39f43221268e782da4872`;
  status **BLOCKED_FOR_PHASE_E**. Existing Phase E/evidence manifests unchanged.

**OBSERVED:** each ZIP contains SDD2 LC/Type-II PI with 86,400 rows, SDD2 GTI
(4/3 rows), empty SDD1 GTI; no SDD1 LC/PI or HK in this obtained collection.
LC schema is native TIME/COUNTS; PI TSTART/TELAPSE/SPEC_NUM/CHANNEL/COUNTS/
EXPOSURE, 340 channels 0–339. Missing LC/PI rows 128/2. Native increments one
numeric unit. Detector association observed for LC/PI headers, inferred from
filenames for GTI. Full ZIP/gzip/FITS/DATASUM checks passed; absent CHECKSUM
cards were not declared verified. PI expands to 472,443,840 bytes per product;
load one bounded product at a time and retain temporary cleanup.

Report schema preserves archive/member and runtime-source identities, native
headers/units, LC/PI/GTI numerical summaries, gaps/concerns, detector evidence,
candidate task dispositions and plot hashes. Shared `SourceIdentity` preserves
mission/platform/instrument/channels/native units/time basis/sampling/measurement/
quality/preprocessing/validation/target fields. Missing units remain `UNKNOWN`;
native details remain separate. Status is `OBSERVED_NATIVE`, exploratory tasks
`EXPERIMENTAL_UNCALIBRATED`, never `SCIENTIFICALLY_VALIDATED`.

Clock cards conflict: UTC/LOCAL/reference offset/date metadata and absent PI
epoch. Absolute UTC/bin position/causal availability are UNKNOWN. GTI endpoint
and effective exposure semantics, HK/correction compatibility, PI-to-response
mapping, detector calibration/response applicability, instrument alignment and
authoritative event rules remain unresolved. The user reports a clarification
email sent without reply; do not wait for it or invent an answer. No UTC repair,
GTI quality filtering, counts-to-rate/flux conversion, response relabelling,
alignment, gap fill or training is authorized. Every narrowly proposed native
sequence task remains blocked, including masked reconstruction. Native diagnostics
continue safely; no SoLEXS forecasting/evaluation is claimed.

## K. Training and future SolarJEPA interface

Read [the model contract](P2_MODEL_CONTRACT.md). Optional Torch imports are lazy.
`training.Normalization.fit(training_slice)` records train-only transformed
statistics; `tensor_batch` returns `[B,120,2]` features and masks, `[B,30,2]`
targets and masks. `build_smoke_model(spec)` consumes feature values/masks;
`masked_mse` uses valid targets and rejects empty/nonfinite support.

`fit_smoke(training_slice, validation_window, config=TrainingConfig(...),
source_identity=..., split_identity=..., device='cpu')` performs bounded Adam
steps and earliest minimum validation-loss checkpoint selection.
`TrainedSmoke.predict(context, future_grid)` returns physical-unit P1 predictions.
`save_checkpoint` is exclusive; `load_checkpoint(path,
expected_identities=..., device='cpu')` uses weights-only deserialization and
checks spec/source/data/split/training/normalization/config, weights and monitoring
consistency. Expected identities must come from trusted external execution/data
records; reading them from an untrusted checkpoint defeats the boundary.

Actual `TRAINING_INFRASTRUCTURE_SMOKE_TEST`: 28,860-parameter masked linear
network, seed 17, CPU, batch 16, two epochs, four train/two validation batches,
eight optimizer steps. 64/855 train and 32/199 validation origins; first 32 each
partition scored after selection. Validation loss 1.2186553478 → 1.2063427567,
best epoch 2. Reload predictions bitwise equal on all three subsets. This is
infrastructure evidence, not SolarJEPA or month-wide scientific performance.

Actual output `results/experiments/p2-goes-training-smoke-20261008/` contains
`best.pt`, result/config/training_config/provenance/dataset_manifest/split_manifest,
normalization/training_record/predictions/metrics JSON and artifact index.
Checkpoint inference reload alone:

```python
import json
from pathlib import Path
from solar_flare_jepa.experiments.provenance import verify_artifacts
from solar_flare_jepa.training import load_checkpoint

run = Path('results/experiments/p2-goes-training-smoke-20261008')
verify_artifacts(run)
record = json.loads((run / 'result.json').read_text())  # externally trusted run
model = load_checkpoint(run / 'best.pt', expected_identities=record['identities'])
# Rebuild matching P1 context/grid using the adapter/split/window APIs above.
# model.predict(context, future_grid) supplies no future target values.
```

Future SolarJEPA must use the same mask/normalization/causality/evaluation
boundary and an explicit new architecture/version/checkpoint identity. The
current dispatch/loader accepts only `masked_linear`. JEPA representation losses,
predictive embeddings and trajectory decoding are PLANNED. Conditioning metadata
must have explicit source, units and availability; none is guessed by this model.

## L–N. Validation, baseline and smoke commands

Run from repository root with clean tracked code/config and a matching normal
installed package. Use new output names; existing directories are refused.
Below `_reproduction` names are examples and were not the acceptance directories.

```bash
df -h .
.venv/bin/python scripts/acquire_goes_history.py --root "$PWD"
.venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --verify \
  --manifest data/manifests/goes_p2_july2024.json
.venv/bin/python scripts/prepare_goes_training.py --root "$PWD" \
  --config configs/experiments/p2_goes_july2024.json \
  --output-dir results/experiments/p2-goes-prepared_reproduction
.venv/bin/python scripts/run_experiment.py --root "$PWD" \
  --config configs/experiments/p2_goes_july2024.json \
  --output-dir results/experiments/p2-goes-baselines_reproduction
.venv/bin/python scripts/explore_solexs.py --root "$PWD" \
  --config configs/data/p2_solexs_exploration.json \
  --output results/p2_solexs/native_reproduction
.venv/bin/python scripts/train_smoke.py --root "$PWD" \
  --config configs/experiments/p2_goes_july2024.json \
  --training-config configs/training/p2_smoke.json \
  --output-dir results/experiments/p2-goes-smoke_reproduction --device cpu
```

Acquisition resumes verified pins, including downloading absent raw files on a
fresh clone; changed upstream versions fail instead of replacing pins. It does
not redownload existing correct files. Other dates require an explicit new bounded
selection/config/ledger; do not overwrite July identities. Unit tests are offline.

Acceptance baseline directory: `results/experiments/p2-goes-baselines-20261008/`.
All six models, 18 scores across train/validation/test, zero failures. Validation
199 and test 209 common origins; all 11,940/12,540 retained cells scored.
Direct ridge validation/test MAE 3.86181159e-7/1.40344566e-6 W/m2;
test MAE skill A/B 0.315772/0.290142. Persistence corresponding MAE
4.06962282e-7/1.98801483e-6. Drift's negative skill is preserved. Fixed parameters
were set before results, with no test tuning. Full per-channel/lead metrics,
coverage and failures are retained; no event metrics are defined.

## O. Test commands and actual results

```bash
.venv/bin/python -m pytest -q tests/test_goes_acquisition.py \
  tests/test_p2_foundation.py tests/test_solexs_exploration.py \
  tests/test_training_foundation.py
.venv/bin/python -m pytest -q tests/test_solexs.py tests/test_solexs_readiness_probe.py
.venv/bin/python -m pytest -q
```

**OBSERVED:** fresh untouched P1 parent 971 passed; final P2 targeted 113 passed;
native loader/readiness plus exploration 109 passed (85 inherited + 24 new);
final full suite **1,084 passed, zero failed**, 119.58 s. All 971 inherited tests,
including F1/R1/N1/N2/N3 protections, are included unchanged. These counts overlap;
do not sum them. One existing NumPy/netCDF ABI warning was retained:
`numpy.ndarray size changed, may indicate binary incompatibility. Expected 16
from C header, got 96 from PyObject`.

Independent reviewer checked 104 then-current P2 tests and actual raw month,
finding three MEDIUM defects and no BLOCKER/HIGH in the bounded review. Off-grid
row loss, contradictory native file ID and checkpoint metadata acceptance were
reproduced RED, fixed with nine regressions, then verified GREEN/full/actual
acceptance. See [review dispositions](P2_INDEPENDENT_REVIEW.md); no claim of a
second reviewer cycle or universal alternate-module source certification.

Normal noneditable installation and outside-checkout imports without PYTHONPATH
verified 30/30 module source parity and runtime code provenance. All three P2
indexed artifact directories verified. Source fingerprint:
`b3e457ad7aa169d07badcb2e5e51270b1835ebeaa49d6d7976441ac56bcbf04c`.
The smoke's source identity additionally binds explicit config bytes and is
`003539aceb08910a73237e8669f9846a8cd9729b2f948ade89e1f42930f3ee36`.

109 inherited scientific identities and 29 prior indexed experiments/290 files
were rehashed; local P1 audit and Paperclip remain unchanged. Logs, parity,
metrics and preservation evidence live under ignored `results/p2_verification/`
and `results/p2_preservation/`. These artifacts are available on this Mac, not
in Git. A fresh clone must regenerate them and independently obtain/preserve
the real SoLEXS archives; it must not fabricate them.

## P. Apple Silicon limits and environment

**OBSERVED:** MacBook Air M2, Mac14,2, 8,589,934,592 bytes RAM; Python 3.13.3,
macOS arm64, Torch 2.6.0. MPS built/available, but actual MPS training is untested.
CPU is deterministic/default, one Torch CPU thread in the training loop. Disk
preflight showed 5.1 GiB free; later 5.0 GiB. Recheck before new downloads or
temporary PI expansion. No large pretrained model was downloaded.

`requirements-lock.txt` is the unchanged P1 lock. New
`requirements-training-lock.txt` pins the observed optional training environment
and includes it. Fresh-environment installation of that combined lock has not
been independently rerun; installed versions/CPU execution were verified.
Avoid parallel raw extraction, large eager PI arrays, large batch sizes and
expensive tuning. Increase resource budgets only deliberately.

## Q. Immediate Claude Code tasks after human review/authorization

1. Verify this branch, refs, manifests and current tests; run normal installation
   and reproduce bounded smoke before model changes. Stay on the authorized
   branch/milestone; get scope approval for the actual model milestone.
2. Implement a small GOES-only temporal encoder, predictive embedding objective
   and explicit trajectory head under a new SolarJEPA identity. Keep masks,
   train-only statistics, physical inverse transform and causal P1 prediction.
3. Add meaningful architecture/loss/causality/checkpoint tests. Run tiny CPU
   optimizer/reload acceptance before increasing batches or epochs.
4. Select design/hyperparameters on training/validation only; retain the fixed
   test. It is already reported here, so do not use its results to select a model.
   If test results influence development choices, arrange a new untouched
   chronological holdout before claiming final generalization. Compare all six
   fixed baselines on exactly matched origins/cells and retain failures.
5. Produce a bounded GOES demo with native-unit trajectories and explicit
   retrospective/source labels. Any frontend remains thin Streamlit with reusable
   core logic. Define authoritative events separately before adding flare risk.
6. Keep SoLEXS at native diagnostics until mission-applicable evidence resolves
   the gate. A reply is evidence to assess, not automatic scientific clearance.

## R–S. Deferred work and limitations

Deferred: large architecture/pretraining, large LLMs, expensive hyperparameter
search, unsupported calibration, SoLEXS flare forecasting, GOES-to-SoLEXS
transfer, React/FastAPI migration and major frontend changes. One-month results
with overlapping contexts establish a working benchmark, not broad generalization,
uncertainty or validated flare classification. Smoke scores cover only bounded
subsets. SoLEXS time/response/quality and cross-source UTC overlap remain UNKNOWN.
No common numeric scale or band equivalence was implemented.

Desktop filesystem metadata/read stalls were observed. One baseline attempt
refused source metadata changing during hashing and published nothing; unchanged
normal retry succeeded. A stale-installed-package intermediate CLI test was
resolved by normal reinstall. Keep provenance guards enabled; stop on genuine
identity mismatch. The ABI warning, actual MPS/cross-platform behavior, clean-env
lock installation and P1 restricted alternate-module audit remain limitations.
No unrelated HIGH issue was discovered in this bounded P2 work.

## T. Reproduction, storage and final policy

From the preserved checkout, verify the branch first, then install:

```bash
python3 -m venv .venv  # only if absent; do not replace an existing environment
.venv/bin/python -m pip install -r requirements-training-lock.txt
.venv/bin/python -m pip install --no-deps .
```

After any executable change, test it, commit approved scoped work, and reinstall
normally before strict acceptance CLIs. Their guard requires clean tracked
source and installed/repository parity. Never work around it with PYTHONPATH,
editable source shadowing, disabled checks or forged provenance. Use unique
result directories and `verify_artifacts` for all indexed executions.

Only reproducibility code, small config/manifests, tests and documentation belong
in Git. Actual raw `.nc`/`.zip`/FITS, expanded arrays, plots/results and `best.pt`
are ignored according to `.gitignore` and `docs/DATA_STORAGE.md`. Never force-add
them. Preserve originals and old audits. Expected untracked items on this Mac
are `.agents/` (Paperclip) and `docs/P1_FINAL_INTEGRATION_REAUDIT.md`; neither
was added or changed. Final protected ref, scientific identity, index/history,
ignore and upstream checks are recorded in local final verification evidence.

**P2 handoff readiness is not permission to integrate or begin Phase E. Stop
for human review.**
