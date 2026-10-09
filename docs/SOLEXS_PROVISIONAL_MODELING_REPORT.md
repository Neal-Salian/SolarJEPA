# SoLEXS provisional sequence-modeling report

**EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED**

Evidence date: 2026-10-09, Asia/Kolkata. Stage A **PASS_NUMERICAL_ONLY**;
Stage B baselines and Stage C limited neural training **COMPLETED**.
This establishes reproducible engineering feasibility for prediction of recorded
SDD2 LC numerical values. It does not clear any Phase E scientific gate, validate
physical count rate/irradiance, establish UTC forecast leads, or forecast flare events.

## 1. Objective and scientific boundary

Predict eight later recorded LC values from 64 earlier recorded values in one
finite native sequence. This is an offline numerical task, authorized separately
from physical forecasting. **UNKNOWN:** effective exposure, scientific quality,
absolute clock/bin completion, correction state, exact LC-generation policy and
response/gain applicability. A finite value is numerical support, not a valid
physical count rate or health-screened measurement. No conversion, interpolation,
exposure correction, response mapping, GOES alignment or flare label was applied.

Native RATE.COUNTS has no encoded TUNIT. Every reported MAE/RMSE is on its original
numerical recorded-value scale, labeled `UNKNOWN_UNENCODED_NATIVE_VALUE`. This label
records an absent unit; it invents none. Generic January-2025 guidance describes
LC counts per second, but cannot certify the particular pipeline-1.1 correction/
exposure/bin semantics of these files. [1] [2]

## 2. Git foundation, isolation and audit

- Exact base: `83b54435c1634f7de0a3ec6494439c023a4d0296` (verified Phase E).
- P2 ancestor: `656e540162c635d4c2274b4469ae11247290f986`, verified by Git ancestry.
- Branch: `research/solexs-provisional-sequence-modeling`, published from the exact
  base with upstream tracking before implementation.
- Frozen executable/configuration commit: `2f5b3b3cb66ea489ca8527dbdd6bd5fb5762b75b`.
  Subsequent report-only commits preserve this execution source. Final handoff tip
  is obtained with `git rev-parse HEAD`; a document cannot embed its own commit hash.
- Protected `main`: `1a4991da4dda9676caeb1d7e35a03408528c3188`, equal to fetched/remote main.
- Work used a separate managed worktree because the original P2 checkout contains
  untracked user files. P1/P2/Phase E and original files were preserved. The named
  P3 branch was absent from observed local/fetched/remote refs; no P3 code was used,
  modified, imported, merged or cherry-picked. This does not assert another
  developer's separate checkout state.

Source/tests/scripts/manifests and the listed Phase D/E and P2 documents were
inspected. Documentation supplied context; executable source and actual inputs
established behavior. Existing P1 contracts require integer-nanosecond completed-bin
coordinates and physical cadence, and P2 source clearance admits GOES only.
Therefore a separate sample-index adapter was necessary. These invariants/gates
remain unchanged. Reused code: bounded native access, canonical identities,
P2's numeric masked-linear factory and masked MSE. P1 baseline/training/checkpoint
classes were unsuitable without inventing time semantics, so small isolated
numerical adapters were implemented. There is no P3 dependency.

## 3. Original data and provenance verification

**OBSERVED:** both streaming archive SHA-256 values match registered full hashes;
ZIP CRC validation, all eight nested gzip streams, FITS structures and all
16 present DATASUM cards pass. CHECKSUM cards are absent. All eight expanded FITS
hashes reproduce Phase E. Original archive hashes remained unchanged after access.

| Nominal date | ZIP bytes | ZIP SHA-256 | SDD2 LC expanded FITS SHA-256 |
|---|---:|---|---|
| 2024-07-01 | 6,036,792 | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` | `8db1592fe86c59093a5d0ae2308da5db9848e408df00387b525bfbf411820cdb` |
| 2024-07-03 | 6,216,112 | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` | `f3baf21aadb2328701ede746a819b9bf65ed6dc8113fd07905b44814da8c5639` |

The original directory is
`data/raw/aditya/solexs/l1/v1.1/archives/2024/07/`. Exact selected LC members:

```text
AL1_SLX_L1_20240701_v1.1/SDD2/AL1_SOLEXS_20240701_SDD2_L1.lc.gz
AL1_SLX_L1_20240703_v1.1/SDD2/AL1_SOLEXS_20240703_SDD2_L1.lc.gz
```

LC primary CREATOR is `solexs_pipeline-1.1`; FILTER establishes SDD2 as OBSERVED.
Product version v1.1 follows pinned archive identity, not an invented FITS version
card. SDD1 has only empty GTIs in both archives. SDD2 LC and PI each have 86,400
rows; PI CHANNEL is constantly 0–339, SPEC_NUM 1–86400, and PI TSTART equals LC TIME.
All-NaN PI masks equal LC NaNs; no partial-NaN spectra. PI TELAPSE/EXPOSURE equal 1,
including missing spectra; these are stored fields, not measured effective exposure.
The existing readiness probe independently reconfirmed candidate RMF labels 1–340
and `accepted_for_application=false`; no relabeling was attempted.

LC has only TIME/COUNTS, no encoded column units, errors or row-quality flags.
TIMEUNIT=s, TIMEDEL=1, TIMESYS=UTC, TIMEREF=LOCAL, MJDREFI=40587 and
MJDREFF=0.22916666651 remain retained metadata, including their known conflict.
Header cards do not authorize converting the coordinate or declaring bin support.
Inclusive GTI point membership matches finite samples, but continuous GTI exposure
and scientific screening remain UNKNOWN. No GTI filter was applied.

Bounded existing access stages one FITS member and streams PI in chunks; PI expands
to 472,443,840 bytes per day. No complete PI array collection or persistent archive
extraction was introduced. Independent audit staging was temporary and removed.

## 4. Stage A feasibility

**OBSERVED:** native LC coordinates are finite, strictly increasing, duplicate-free,
and every adjacent numerical increment equals 1. No sorting or deduplication is
needed. LC finite values are integer-valued positive float64 in these inputs;
there are no zeros, negatives or infinities. Numerical code does not invent a
negative/zero physical screening rule.

| Nominal product | Rows | Finite | NaN | Recorded min/max |
|---|---:|---:|---:|---:|
| July 1 | 86,400 | 86,272 | 128 | 3 / 1,554 |
| July 3 | 86,400 | 86,398 | 2 | 2 / 943 |

Zero-based half-open NaN runs: July 1 `[5,131)`, `[23132,23133)`, `[23138,23139)`;
July 3 `[18033,18034)`, `[18039,18040)`. All finite runs remain separate; the small
five-row runs cannot support a 72-row window. The between-product numerical
coordinate difference is 86401; products are never stitched.

The ten feasibility requirements resolve as follows: recorded ordering is
unambiguous; duplicates/reversals are absent and rejected by the builder; NaN runs
and unexpected positive coordinate steps can delimit exclusions; no applicable
additional row-quality indicator is available, so physical QC remains unknown;
finite numerical targets exist; the exact recorded field/identity is stable and
unambiguous as a numerical target while its physical interpretation remains
unresolved; raw-row splits and complete-run windows prevent leakage; boundaries
are enforced; the observed window counts support this small engineering exercise;
and deterministic reproduction succeeded. **INFERRED:** this is sufficient for
the user's expressly permitted numerical fallback. It is insufficient for a
physical forecasting contract. Unknown exposure does not become assumed exposure.

## 5. Frozen provisional task and sequence assumptions

| Contract item | Policy |
|---|---|
| Target | Exact recorded SDD2 LC RATE.COUNTS values; units unencoded |
| Context / horizon / stride | 64 / 8 / 8 native samples |
| Ordering | Original file rows; finite strictly increasing native coordinates |
| Coordinate continuity | Exact numerical step 1; no physical duration asserted |
| Boundaries | One source, raw split and finite contiguous run per complete window |
| Missingness | Preserve source NaNs/masks; exclude crossing windows, no filling |
| Quality | Numerical usability only; scientific QC UNKNOWN_NOT_APPLIED |
| Exposure/calibration | UNKNOWN_NOT_APPLIED; no rate/flux conversion |
| Lattice | Anchor at raw split start + context, then stride 8; never reanchor runs |
| Transform | Identity; unique raw train population mean/std for normalization |
| Provenance | Archive/gzip/FITS hashes, metadata, native row origins and array identities |

Lengths are deliberately small engineering budgets, not variability-derived
physical timescales. No GOES 120/30-minute configuration was imported. The v1 runner
rejects changed lengths/splits/row counts and neural settings; a new reviewed
experiment is required to change them. Alternative reanchoring would produce a
different training count and identity and is not used.

## 6. Dataset construction, splits and leakage analysis

| Partition | Separate source/raw rows | Raw finite/NaN | Candidate origins | Retained/excluded | Target cells |
|---|---|---:|---:|---:|---:|
| Train | July 1 `[0,60480)` |60,352 /128 |7,552 |7,525 /27 |60,200 |
| Validation | July 1 `[60480,86400)` |25,920 /0 |3,232 |3,232 /0 |25,856 |
| Test | July 3 `[0,86400)` |86,398 /2 |10,792 |10,783 /9 |86,264 |

Candidate origins are generated before screening. All actual exclusions are from
missing-value crossings; no coordinate discontinuity occurs within either native
file. The validation first context starts at 60480; training last target ends at
60479. No raw row occurs in both partitions. Candidate target origins are train 64..60472,
validation 60544..86392, test 64..86392, each with 8 future target rows. After
missingness exclusions, retained training origins start at 200; validation/test
retained starts remain 60544/64. Missingness
removes individual candidates without changing the fixed lattice. All retained
feature/target masks are true; source missing masks remain separately preserved.
This exercise does not train a gap-reconstruction capability.

Adjacent target blocks are disjoint, but contexts share 56 rows; full windows
share 64 rows. Windows/errors are dependent and are not independent scientific
replications. The 70% split is a predeclared engineering allocation, not a claim
of a statistically meaningful solar population split. July 3 is one separate
nominal-product holdout, independent of the July 2024 GOES benchmark.

Normalization uses 60,352 unique finite raw training rows: mean 31.367079798515377,
population std 88.10555642339494. It does not reweight overlapping contexts or see
validation/test data. Validation/test values enter only their scoring and the
validation objective; test identities can be recorded before fitting without
using test values for optimization/selection. Prediction APIs accept only context
values/masks. No future targets, quality from future rows, hidden padding, cross-day
context or normalization fitted on holdout is passed to predictors.

## 7. Scientific research informing the contract

**DOCUMENTED:** the SoLEXS instrument paper distinguishes spectral and timing
chains, temperature-dependent gain, deadtime/correction assumptions and a corrected
SDD2 cross-calibration example. Those results do not certify this LC generation or
release-1.1 timing/exposure/response pairing. [1] The January 2025 manual and June 2026
release note provide dated guidance and subsequent timestamp-header changes,
without an applicable numerical repair/precedence contract. [2]

**DOCUMENTED:** GOES XRS uses wavelength-dependent photodiode response and
irradiance conventions. Nominal band overlap does not establish equivalent
observables. [3] An original XSM study distinguishes measured light curves from
response-derived band flux and identifies background/instrument contributions to
recorded variability; its parameters are not transferred to SoLEXS. [4]

**INFERRED:** native numerical variability is a defensible engineering signal, but
its causes/physical amplitude and flare identity are not established here.
Prediction intervals require their own procedure and assumptions: adaptive
conformal and time-series conformal papers distinguish coverage guarantees and
dependence/estimation conditions. No interval procedure or coverage guarantee is
applied to this pilot. [5] [6] MAE/RMSE are descriptive point errors, not photon,
calibration, parameter or probabilistic forecast uncertainty.

Paperclip skill and CLI succeeded. Exact original-paper lookup and line reads
were checked against versioned originals; broad searches missing an exact paper
were not treated as absence. Paperclip metadata has no explicit manuscript-version
field. Its Xu/Xie text is a later manuscript; original ICML 2021 assumptions were
checked separately. Anonymous protected-manual access failed and NOAA live access
timed out; pinned local original documents were read instead. No portal
reauthentication, mission email, calibration procedure or numerical error bar was
fabricated. Full commands/source caveats remain in ignored research artifacts.

## 8. Statistical baselines and native-scale results

Persistence repeats the latest context value. Training mean uses unique raw train
statistics. Trailing mean uses the last 16 context samples. Fixed AR(1)-style
mean reversion uses phi 0.9 and training mean; phi is not estimated. Direct Ridge
fits the standardized 64-value vector directly to 8 standardized targets with
alpha 1 and an unpenalized intercept, using train windows only. These fixed
comparators need no ARIMA search or physical assumptions. No positivity clipping
or log/physical reference transform is applied.

MAE/RMSE pool identical valid target cells across the 8 sample leads. Skill is
`1 - model_error / persistence_error` on the identical mask, separately for MAE
and RMSE. Zero persistence error produces null skill. All predictions are finite;
invalid predictions abort rather than reducing evaluated support.

| Method | Train MAE | Train RMSE | Validation MAE | Validation RMSE | Test MAE | Test RMSE | Test MAE skill | Test RMSE skill |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| persistence | 5.572076 | 8.311475 | 5.841004 | 7.628567 | 6.222016 | 8.924128 | 0.000000 | 0.000000 |
| training_mean | 21.248939 | 88.215317 | 15.086295 | 19.746186 | 23.399096 | 68.384808 | -2.760693 | -6.662912 |
| trailing_mean | 4.408351 | 8.736992 | 4.279597 | 5.598466 | 4.603606 | 6.824853 | 0.260110 | 0.235236 |
| fixed_ar1 | 9.332095 | 34.953295 | 7.269799 | 9.853432 | 10.287771 | 27.843052 | -0.653446 | -2.119975 |
| direct_ridge | 4.264101 | 5.946028 | 4.528771 | 5.928103 | 4.814436 | 6.811153 | 0.226226 | 0.236771 |
| numerical_linear | 4.598365 | 8.061419 | 4.607214 | 6.014515 | 4.972369 | 7.355389 | 0.200843 | 0.175786 |

These are unencoded native recorded-value errors, not counts/s or W/m². They cannot
be numerically compared to GOES irradiance errors. Prediction/target/scored coverage
is 1.0 **conditional on retained complete windows**. Candidate-origin retention is
99.6425% train, 100% validation and 99.9166% test; these are numerical selection
statistics, not good-exposure fractions. Raw NaNs and exclusions above are part
of the result. No per-lead scientific skill or calibrated uncertainty is implied.

## 9. Limited neural training

Stage C was permitted after numerical feasibility, supported splits, reproducible
baseline validation and compatible numerical training semantics were verified.
The model is a generic affine masked-linear predictor with 1,032 parameters,
reusing the P2 numeric factory/loss. It is **not JEPA, SolarJEPA, a nonlinear
representation learner or a flare model**. Its mask inputs are constant on this
complete-window dataset and redundant with bias; Ridge and Torch span broadly the
same affine function class with different optimization/regularization.

CPU only; NumPy/Torch seed 17, deterministic algorithms, one Torch thread, eight
epochs, all 7,525 train origins each epoch in seeded order, batch 128, Adam lr 0.001,
gradient clip 1.0. There are 59 optimizer steps/epoch, 472 total. No pretrained weights,
architecture search, early stopping, test-based tuning or repeated configuration
selection occurred. All 3,232 validation origins enter the masked normalized MSE.

Earliest minimum validation loss selected **epoch 4**: normalized validation
MSE 0.004660094087703688; its online epoch training loss 0.010178763199090165.
The latter averages evolving-weight batch losses, not the final checkpoint's
train evaluation. Selected-checkpoint train MAE/RMSE are 4.598365/8.061419;
validation 4.607214/6.014515; test 4.972369/7.355389. Full eight-epoch history, selected
Adam state and exact identities are retained. Selection was frozen in
`selection_frozen.json` before designated test scoring.

Neural errors are lower than persistence on this held-out recorded sequence,
but trailing mean and Ridge both outperform it on test MAE/RMSE. No neural
advantage, scientific superiority or generalization claim follows. All reported
results, including negative skill of training mean/fixed AR1, are preserved.

## 10. Reproducibility and artifact identities

Two executions at the same frozen source/configuration produced **identical bytes
for every indexed output**, identical predictions/targets/masks/origins, scores,
normalization, history, selected epoch and checkpoint SHA. Checkpoint reload also
produced bitwise-equal train/validation predictions before test evaluation. The
second execution was solely a fixed-configuration consistency check; nothing was
selected or changed using repeated holdout results.

Observed software: Python 3.13.3, NumPy 2.2.6, Astropy 8.0.1, Torch 2.6.0. A dedicated
normal package installation used existing dependencies without modifying the
shared P2 environment. Its source-provenance guard verifies all 53 source entries
and matching executed package files, clean tracked source and configuration bytes.
Cross-library/device/version bitwise equality is untested.

Main output: `results/experiments/solexs-provisional-v1-20261009/`.
Consistency execution: `results/experiments/solexs-provisional-v1-20261009-reproduction/`.
All are ignored, including checkpoints/arrays. Exact compact provenance and
metrics are tracked in [the new manifest](../data/manifests/solexs_provisional_v1.json).

| Main-run artifact | Bytes | SHA-256 |
|---|---:|---|
| `best.pt` | 17,856 | `619e0410bfe74f81a163fc1a00533c9ad5c74686a4c69bc4e53a31326b6ec449` |
| `predictions.npz` | 2,968,529 | `db09636148cfbc8da0dd6ab3ddae625036916fee65e6fd588f39cdaa531698a0` |
| `report.json` | 42,420 | `ee8bea0356ac0ffad5083ffdd6136bac97d61608f12ef9a7f2f3d815afff21f2` |
| `selection_frozen.json` | 3,879 | `72b9b03bfe4e2b408a8c4aa7cacd0e32b072377f1923fafe01c24f2efd8a80e5` |

## 11. Verification and independent review

Inherited full suite: **1,084 passed**, 77.54 s, one existing ABI RuntimeWarning.
Final implementation full suite: **1,149 passed**, 75.71 s, the same warning.
New provisional suite: **65 passed**; inherited native scientific subset:
**109 passed**, 5.70 s. Normal installed CLI and source identity checks passed.
Tests cover identity mismatches, order/duplicates, NaNs/gaps, invalid inputs,
raw splits, train-only normalization, masks/loss, coverage, deterministic windows/
baselines, checkpoint identities/loading/reproducibility, labels, frozen config,
configuration-byte hashes and exclusive symlink-safe publication.

Independent investigators covered full native integrity, literature and contract
compatibility. Independent implementation review reproduced publication/config/
optional-dependency issues; targeted RED/GREEN regressions fixed them before real
execution. It also independently checked 300 randomized window cases and synthetic
training/reload. Final reviewers independently rechecked real artifact identities,
metrics/selection and scientific interpretation. Review limits and executed checks
are retained in ignored review records; this is not mission scientific approval.

Two intermediate full-suite failures are explicitly retained in the implementation
report: stale installed-package provenance and source mutation during an active
verification run. After synchronization and freezing source, the full suite passed.
No warning suppression or inherited test change was used. The netCDF4/NumPy
binary-size warning is unresolved; no ABI-safety claim is made.

## 12. Scientific limitations and unchanged Phase E gates

| Gate | Unchanged status | Still required |
|---|---|---|
| E1 timing | BLOCKED_EXTERNAL_EVIDENCE | Applicable clock/card precedence, UTC/bin/availability/GTI policy and boundary reference |
| E2 calibration | BLOCKED_EXTERNAL_EVIDENCE | Response/channel/gain/epoch compatibility, correction and uncertainty reference |
| E3 exposure/quality | BLOCKED_EXTERNAL_EVIDENCE | Effective exposure, GTI endpoints, deadtime/reset/health rules; matching HK if required |
| E4 detector/product | PARTIALLY_VERIFIED | Approved SDD2 task/LC generation; SDD1 science absent here |
| E5 GOES compatibility | PARTIALLY_VERIFIED | Response-aware quantities, separate quality, observer/bin/UTC alignment |
| E6 scientific forecasting | BLOCKED_EXTERNAL_EVIDENCE | Valid target/causal availability and representative independent scientific evaluation |

The provisional Stage A pass is a separate user-authorized numerical disposition;
it does not rewrite historical E6 or grant the existing SoLEXS scientific training
clearance. Existing exploration/train refusal and GOES source contracts still pass.

Two noncontiguous nominal dates do not sample independent solar populations,
seasons, instrument states or calibration epochs. Recorded distributions differ;
missingness mechanism, calibrated uncertainty and scientific observation support
are unknown. Many correlated windows cannot replace missing date/activity diversity.
No statistical significance, operational lead, probabilistic interval, physical
flux, flare classification or prospective availability was validated.

## 13. Requirements for calibrated forecasting and future integration

Obtain mission-applicable pipeline 1.1 clock/bin/GTI/exposure/correction guidance,
response/channel/gain applicability and reference outputs; obtain matching HK
only if the approved workflow requires it. Validate these against immutable
products before calibrated target construction, uncertainty estimation or source
alignment. Then select bounded representative observations and independently
review causal delivery/splits and physical evaluation.

A future integration could expose a reviewed source-specific adapter returning
validated coordinates, quantities, masks and provenance into the existing P1/P2
contracts. Sample-index numerical results alone cannot satisfy that interface.
No speculative shared abstraction, GOES split/metric change, React/FastAPI work,
P3 model modification, main merge or PR was performed.

## 14. Reproduction and review handoff

From this branch/worktree with a normal package install and independently supplied
immutable inputs, use a new output identity each time:

```bash
python -m pip install --no-deps .  # dependencies must already satisfy project/training/aditya extras
python -m pytest -q
python scripts/run_solexs_provisional.py \
  --data-root "$SOLEXS_DATA_ROOT" \
  --output-dir results/experiments/solexs-provisional-human-reproduction
python -c 'from solar_flare_jepa.provisional.experiment import verify_outputs; verify_outputs("results/experiments/solexs-provisional-human-reproduction")'
```

`SOLEXS_DATA_ROOT` is a configurable root containing original archive-relative
paths. Code checkout supplies pinned manifests/configuration; inputs need not be
copied into it. Native diagnostic reproduction also uses existing
`validate_solexs.py`/`probe_solexs_readiness.py --root "$SOLEXS_DATA_ROOT"`.
Source must be clean and normal installed files must match it. Output publication
is exclusive and rejects symlink redirects. No network/data acquisition occurs.
See [implementation report](SOLEXS_PROVISIONAL_IMPLEMENTATION_REPORT.md) for full
changed-file inventory, local artifacts, checks/failures and final publishing rules.
Stop for human review after feature-only publication; do not merge or create a PR.

**Explicit final scientific statement: this experiment is EXPLORATORY / PROVISIONAL /
NOT SCIENTIFICALLY CALIBRATED. Engineering completion does not alter Phase E blockers.**

## 15. Primary references and access evidence

[1] Sarwade et al., *Solar Low Energy X-ray Spectrometer on board Aditya-L1:
Ground Calibration and In-flight Performance*, JATIS 11(4),045005 (2025),
[original v2](https://arxiv.org/html/2509.26292v2),
[DOI](https://doi.org/10.1117/1.JATIS.11.4.045005).
[Paperclip original instrument passage](https://paperclip.gxl.ai/citations/papers/arx_2509.26292#L38-L48),
[deadtime/cross-calibration passages](https://paperclip.gxl.ai/citations/papers/arx_2509.26292#L135-L157).

[2] URSC/ISRO, SoLEXS Data Analysis Guide v1.0 (January 2025), §§2.1–2.2/4.5,
[official protected manual](https://pradan1.issdc.gov.in/al1/protected/downloadFile/solexs/SoLEXS-UserManual.pdf).
Local source pins and June 2026 release-note provenance are preserved in
[Phase E evidence](SOLEXS_PHASE_E_EVIDENCE_MATRIX.md); exact release-note acquisition
URL remains unknown. Local manuals/release note were read and rehashed.

[3] Woods et al., *GOES-R Series X-Ray Sensor (XRS):1. Design and Pre-Flight
Calibration*, JGR 129,e2024JA032925 (2024),
[DOI](https://doi.org/10.1029/2024JA032925),
[Paperclip response assumptions](https://paperclip.gxl.ai/citations/papers/PMC11582350#L137-L142).

[4] Mithun et al., *Solar X-ray Monitor On Board the Chandrayaan-2 Orbiter:
In-flight Performance and Science Prospects*, Solar Physics 295,139 (2020),
[DOI](https://doi.org/10.1007/s11207-020-01712-1),
[Paperclip light curves and background](https://paperclip.gxl.ai/citations/papers/arx_2009.09759#L53-L66).

[5] Gibbs and Candès, *Adaptive Conformal Inference Under Distribution Shift*,
NeurIPS 34 (2021), [original proceedings](https://papers.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html),
[Paperclip long-run coverage passage](https://paperclip.gxl.ai/citations/papers/arx_2106.00170#L72-L85).

[6] Xu and Xie, *Conformal prediction interval for dynamic time-series*,
PMLR 139,11559–11569 (2021), [original ICML paper](https://proceedings.mlr.press/v139/xu21h.html).
[Later manuscript dependence assumptions](https://paperclip.gxl.ai/citations/papers/arx_2010.09107#L72-L104)
were version-distinguished from the original conference text. No interval method
or its guarantees was applied in this experiment.
