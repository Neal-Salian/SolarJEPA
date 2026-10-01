# Investigation and foundation report

Investigation: 2026-09-29; final validation after directory rename: 2026-10-01.
No training performed. Local repository initialized on `main`; an `origin`
remote is now configured at `https://github.com/Neal-Salian/SolarJEPA.git`.
No push was performed in this session. The requested seven research documents, detailed implementation
plan, bounded reference downloader, metadata inspector and reusable reference
EDA are present. **Aditya-specific validation is blocked on registered data and
manuals; it is not represented as complete.**

## 1. Data findings

Official Aditya products exist, but the tested PRADAN Access Data URL redirects
to an ISSDC account sign-in/registration page. No anonymous telemetry API/sample
was verified. Post-login holdings, sizes, coverage and field definitions remain
unknown. Public documentation supports SoLEXS-first investigation, with ASPEX
treated as a separate local particle stream. See [dataset card](DATASET_CARD.md)
and [manual acquisition instructions](DATA_DOWNLOAD.md).

## 2–3. Downloaded data and exact sizes

Only official **NOAA GOES-16 external reference** science-quality L2 NetCDF
v2-2-1 files were acquired. They are not Aditya data and are not a training set.
All raw bytes remain ignored by Git; SHA-256/source URLs are in
`configs/data/noaa_sample.json` and `data/manifests/noaa_retrieval.json`.

| UTC day | 1-minute flux bytes | Flare summary bytes |
|---|---:|---:|
| 2024-07-01 | 291,751 | 42,633 |
| 2024-07-02 | 291,557 | 43,183 |
| 2024-07-03 | 291,598 | 41,863 |
| Total | 874,906 | 127,679 |

**Six raw files: 1,002,585 bytes (0.95614 MiB). Aditya: 0 files, 0 bytes.**
Dependency packages and generated outputs are not included in dataset volume.

Real validation results:

- Files open with the NetCDF reader; 4,320 flux records over
  `[2024-07-01T00:00:00Z, 2024-07-04T00:00:00Z)`.
- Every adjacent record is 60 seconds apart; zero missing grid timestamps,
  duplicate timestamps or nonpositive/raw-missing primary flux values here.
- Preserve bin start and bin end separately. Earliest feature availability is
  the bin end, plus operational latency if known. Use the documented nominal
  UTC clock (leap seconds neglected), not an assumed TT/J2000 conversion.
- XRS-A: 2,267 valid / 2,053 masked rows. XRS-B: 4,318 valid / 2 masked rows.
  All primary status flags are zero; exclusions arise from electron correction
  bits. Bit value 40 predominantly marks A/A1 contamination and does not by
  itself invalidate B. Strict per-primary-channel masking is implemented.
- Longest masked stretch: A 254 minutes; B 2 minutes. These are quality
  exclusions, not archive timestamp gaps. Valid 1-second samples contributing
  to minute means range from 28 to 60; counts are retained, not hidden.
- Valid XRS-B range: 1.0978928912663832e-6 to 2.1691328583983704e-5 W/m².
  Median: 1.3738258530793246e-6 W/m². Log-space distributions are strongly
  nonuniform; no fitted distribution or stationarity claim is made.
- 94 catalogue **state rows**, 28 event IDs; 27 observed peaks (25 C, 2 M,
  no X). Only 21 IDs have start, peak and end states within this sample.
  Missing states can reflect boundary truncation or overlapping event behavior;
  do not count all rows as independent flares or label absent states as quiet.
- Largest example: catalogue M2.1, 2024-07-01 11:02 UTC; other M peak: M1.5,
  2024-07-03 07:41 UTC. These are observed catalogue examples, not predictions.
- Backward log derivatives use only adjacent valid 60-second pairs: 2,170 A
  pairs and 4,316 B pairs. No interpolation across quality gaps.
- No SoLEXS–ASPEX overlap, cross-instrument correlations, or calibration were
  measured. A/B correlation is within the same GOES instrument and cannot
  answer the proposed multi-instrument research question.

Artifacts (regenerable and ignored): `results/schema.json`,
`data/processed/noaa_reference.parquet` (261,174 bytes at this validation),
its metadata sidecar, and `results/noaa_reference/{summary.json,time_series.png,
distributions_quality.png,cadence.png,event_example.png}`. Flux/log/derivative,
distribution/quality and event plots were visually inspected.

## 4. Unavailable evidence

Actual SoLEXS formats/HDU names, released date range, daily volume, quality
definitions, clock conversion, usable flux products, response/ARF/RMF semantics,
dead-time/pile-up treatment, ASPEX calibrated channels and contemporaneous
coverage. FITS/CDF metadata inspection capability does **not** validate these.
No broad archive inventory, calibrated Aditya EDA or training-ready split exists.

## 5–6. Proposed architecture and controls

Small probabilistic temporal encoder/decoder using SoLEXS history, masks and
observation age. Start with calibrated 1-minute bands if supported by actual
files. Initial task 6 h → 1 h, with limited development sweeps and configurable
history/horizon. Controls: persistence, moving mean/EWMA, linear/ridge, AR/ARIMA,
LSTM, TCN and supervised patch Transformer. Add a matched non-JEPA SSL control.
Qwen2.5-1.5B QLoRA is optional and secondary; match its reduced numerical task.

## 7. ARCH/GARCH role

Diagnose train-only log differences or mean-model residuals for conditional
heteroskedasticity, then compare AR+ARCH/GARCH against constant-variance AR.
Forecast conditional variance and simulate paths for interval/flux comparisons;
variance is not flare probability. Solar ARFIMA–GARCH literature exists, but
applicability to this cadence/period still needs diagnostics. No ARCH/GARCH
model or diagnostic fit has been run on this three-day sample.

## 8. JEPA proposal

5-minute temporal patches; width 128, 3 encoder layers, 4 heads; EMA future
target encoder used only during training, stop-gradient targets and 2-layer
predictor. Ordered quantile decoder predicts physical/log trajectories. Aim for
1–3M parameters; not measured because model implementation has not begun.
Monitor latent collapse. Compare equal-backbone supervised and reconstruction
controls; pretraining uses training periods only. Deterministic JEPA is not
itself a generative model. Multi-resolution 1/5/15-minute branches are an ablation.

## 9. Physics additions

Candidate: a documented detector-response observation model connecting predicted
nonnegative spectra to counts with exposure and background. Gate Poisson
likelihood on detector/calibration assumptions; band integration provides
additivity. Thermal/emission-measure constraints require spectral validation.
Positivity and nested risks alone are not substantive physical novelty.
No arbitrary smoothness, unresolved MHD conservation or STEPS-based Neupert loss.

## 10. Main leakage controls

Chronological train/tune/calibration/test; all window/feature support and label
maturity within partitions; purge event clusters and boundary windows; train-only
pretraining/scaling; no future joins or backfill; lock thresholds before test;
no matching particle arrivals backwards in time. Evaluate pre-onset warning
separately from continuing flares and use common origins across model variants.
Future catalogue peaks may legitimately define outcomes, never input features.

## 11. Scientific weaknesses

Short mission duration, unknown event counts/overlap, full-disk source ambiguity,
rare X events, calibration changes, background/cadence effects and retrospective
latency. Particle propagation complicates any precursor claim. Three days of
GOES establish engineering feasibility only. No physical constraint or model
advantage is demonstrated yet.

## 12. Likely contribution

An auditable calibration-aware Aditya benchmark and controlled uncertainty/shift
study could be useful. Time-series JEPA and Phys-JEPA already exist. A solar
measurement-specific extension must earn its claim through response validation,
matched controls and independent-event skill. See [novelty analysis](NOVELTY.md).

## 13. Compute

Foundation runs on CPU. Proposed native model budget <8 GiB T4 VRAM;
QLoRA trial <13 GiB, starting sequence length 1024 and microbatch 1–2.
Profile first; caps of 30 GPU-hours core and 6 GPU-hours LLM are proposals, not
runtime measurements. No GPU, model weights or training compute used here.

## 14. Implementation phases

Completed foundation → registered Aditya calibration validation → causal
window/split/label manifests → numerical baselines and evaluation → plain JEPA
and SSL controls → validated physics/multiresolution/fusion ablations → optional
LLM comparison and paper artifacts. Concrete files/tests/gates are in
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Stop remains in force now.

## 15. Decisions for approval before further research implementation

1. Adopt SoLEXS-first scope and a provisional title without unearned physics or
   generation claims; keep particles conditional on evidence.
2. Obtain registered PRADAN manuals and matched small products; no credentials
   should be shared in the repository. If unavailable, pause Aditya experiments
   or explicitly approve a different GOES-only project.
3. Approve target definitions (continuous trajectory plus M+ onset), provisional
   minimum event-count/precision gates and the bounded compute plan.
4. Decide whether Qwen comparison deserves the secondary budget after baseline
   profiling. No need to commit GPU time before data gates pass.
5. Exact split dates, response-based physical loss and broader download volume
   require evidence from acquired Aditya products; these cannot be finalized now.

## Verification and environment

Python 3.13.3, macOS Apple Silicon, isolated `.venv`; exact installed packages
are pinned in `requirements-lock.txt`. Tests contain artificial metadata/byte
fixtures clearly labeled as unit tests, never presented as telemetry evidence.

The repository moved from `isro` to `SolarJEPA` during the session. Existing
commits and raw files were retained. Local virtual-environment paths were updated,
and the editable `.pth` file's macOS hidden flag was cleared after tracing why
Python skipped it. Package imports and command-line scripts now use the new root.
The independent review found that EDA wildcards could include unrelated July
dates. Preparation and EDA now select only pinned manifest entries and verify
their hashes and sizes; regression tests cover added files and changed bytes.

Commands used:

```bash
python -m pytest -q
python -m pip check
python scripts/download_data.py --manifest configs/data/noaa_sample.json
python scripts/inspect_data.py data/raw/noaa/*.nc --output results/schema.json
python scripts/preprocess.py --config configs/data/noaa_eda.json
python scripts/eda.py --config configs/data/noaa_eda.json
git check-ignore data/raw/noaa/*.nc
git diff --check
```

Initial tests failed because implementation modules did not yet exist. A
hand-counted byte-fixture expectation was corrected (46 bytes); a new regression
test exposed overly broad electron masking and drove the channel-specific fix.
No test failure was hidden. The initial NumPy 2.5/pandas combination produced a
timedelta deprecation; NumPy 2.2.6 removes it. A NetCDF4 import emits a
`numpy.ndarray size changed` RuntimeWarning when pytest overrides NumPy's default
warning filters, including with NetCDF4 1.7.2. Tests normally pass with this one
warning; a diagnostic warnings-as-errors run fails on that dependency import.
The warning is not suppressed by this project's configuration. Numerical
extraction is checked against the file metadata and real sample. Treat broader
platform support as unverified; do not claim a warning-free environment.

Final verification on 2026-10-01: **26 passed, 1 dependency warning**;
`pip check` reports no broken requirements; preparation and EDA complete on the
six pinned real files. The independent patch review found no remaining blocking
issue. Local document links resolve, and raw/processed data, results, the virtual
environment and checkpoints are ignored. No GPU training or Git push occurred.
