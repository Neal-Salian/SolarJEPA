# GOES external validation and solar flare benchmarking research

Date: 2026-10-09 (Asia/Kolkata). Milestone status: **PARTIALLY_VERIFIED**.
This is a reproducible retrospective evaluation foundation, not a demonstrated
SolarJEPA forecasting result or a validated operational flare-warning benchmark.
No model was fitted, selected, trained or scored against these observations.

## Objectives and evidence vocabulary

Determine whether future frozen predictors generalize beyond July 2024, and
establish separate, auditable flux and catalog-event tasks. Observed irradiance,
catalog onset, peak, end, class, predicted flux and predicted event occurrence
are different quantities. A flux threshold crossing is not an official event.

**DOCUMENTED** means an authoritative source states a definition; **OBSERVED**
means bytes or execution directly establish it; **INFERRED** identifies a derived
interpretation; **UNKNOWN** remains unestablished. Verification statuses are:

| Scope | Status | Evidence/limit |
|---|---|---|
| January raw identities, native schema, coverage and quality | VERIFIED | Official URLs, measured bytes/SHA-256, complete source validation |
| Versioned catalog bytes and strict parsing | VERIFIED | Annual CSV and metadata snapshot pinned independently |
| Synthetic software behavior and deterministic real alignment | VERIFIED | Controlled tests plus observational preparation; no forecast skill inference |
| Catalog-onset labels as physical flare truth | PARTIALLY_VERIFIED | Reproducible catalog-defined labels; detection completeness UNKNOWN |
| As-issued availability and causal native science preprocessing | BLOCKED_EXTERNAL_EVIDENCE | Revised science products list adjacent-day processing inputs |
| Flux-to-event decision procedure and operational event utility | BLOCKED_IMPLEMENTATION | Requires separately defined, development-only validated decision rules |
| Forecast performance/statistical improvement | BLOCKED_IMPLEMENTATION | No models/predictions evaluated in this milestone |

## Repository baseline and independent audit

Exact base: `656e540162c635d4c2274b4469ae11247290f986`, verified P2. Branch:
`research/goes-external-validation`. The original checkout, untracked Paperclip
skill/re-audit, ignored GOES/SoLEXS observations and experiments were preserved;
work occurs in a separate managed worktree. Main and the other research branches
were inspected, never checked out for edits, pushed, merged or rebased. The named
P3 branch was absent from the initial fetched local/remote refs; this does not
assert absence of the teammate's unpublished work. Nothing depends on P3.

**OBSERVED:** inherited suite: 1,084 passes, one unsuppressed NetCDF/NumPy ABI
warning. Audited source includes immutable acquisition, strict native quality
masks, `TimeSeriesDataset`, causal `ForecastContext`/`FutureGrid`, raw-axis temporal
partitioning, `TrainingSlice`, six existing baselines, trajectory/event scoring,
source/package identity checks and immutable experiment publication. Actual
manifests and frozen experiment configuration were inspected, not inferred from
documentation or historical counts.

Two consequential documentation/interface distinctions:

1. The historical P1 final integration audit records an earlier NOT_READY state.
   Subsequent N2/N3 remediation is present in the exact P2 ancestry/source/tests;
   historical reports are preserved rather than rewritten.
2. P1 trajectory scoring and fitted models require evaluation and training to
   share dataset identity. This invariant blocks direct external scoring with
   a July `TrainingSlice`. The new external adapter reuses strict forecast/grid
   contracts, omits train-scaled MASE, and never spoofs July identity or exposes
   external fitting support. Existing source, adapters and experiments are unchanged.

Frozen July ledger SHA-256:
`581a3c4b8cfba6b9b21ed1fdb0b2277e728e9bf329a8da1ddcc0bd49c3cc4b3d`.
Frozen July experiment-config SHA-256:
`e02b5e98a7430e11d09359cc270c68339ea7090e05fe991944d3575051d12ed1`.
The external loader checks the exact frozen ledger hash and rejects overlap of
entire raw support, stronger than checking test targets alone.

## Literature findings and limits of transfer

Paperclip was loaded from the installed repository skill and queried for solar
flare evaluation, GOES forecasting and event catalogs. Relevant passages were
read through Paperclip and important bibliographic/methodological findings checked
against original publications. Paperclip does not determine observation identities
or authoritative labels. This is a focused reconnaissance, not a systematic review.

- Ahmadzadeh et al. discuss rare-event imbalance and temporal coherence from
  sliding windows, showing why random splits can inflate apparent skill [1].
  This supports chronological separation and preservation of dependent origins.
- Bloomfield et al. show why a forecasting score must be interpreted with the
  event definition and class imbalance; TSS is useful but not a replacement for
  POD, false alarms, support counts and explicit operational objectives [2].
- Leka et al. use multiple verification metrics and prior-only climatology,
  prohibit threshold optimization on test outcomes, and warn that day bootstrap
  can understate uncertainty compared with active-region disk-passage units [3].
  Their 24-hour operational tasks do not validate this 30-minute onset task.
- Reep and Barnes study remaining duration of an ongoing GOES flare [4]. This
  motivates distinguishing onset prediction from continuation/duration; it is
  not evidence that onset can be inferred from continuous forecasting error.
- Plutino et al.'s independently detected historical GOES catalog illustrates
  event-definition/overlap sensitivity [5]. It is not authoritative 2025 truth,
  and its historical operational algorithm summary is not the newer NCEI science
  algorithm implemented in the official report.
- Dependence-preserving resampling is supported by block-bootstrap literature
  such as Politis and Romano [6]. The implemented nonoverlapping calendar-block
  percentile procedure is a transparent descriptive choice, not their stationary
  bootstrap algorithm and not proof of solar-process stationarity.

These studies motivate protections, not numerical performance expectations.
No transfer of published scores to SolarJEPA is justified.

## Dataset selection and official authority

**INFERRED design choice, frozen before model scoring:** January 1–31, 2025,
`2025-01-01T00:00:00Z <= t < 2025-02-01T00:00:00Z`. It is six months after
July 2024 and uses the same GOES-16 EXIS/XRS science L2 one-minute product
`xrsf-l2-avg1m_science`, version `2-2-1`. This minimizes spacecraft/version changes
while providing forward out-of-period support; one month cannot establish
solar-cycle generalization.

**OBSERVED listing survey only:** all expected v2-2-1 daily filenames were listed
for Jan–Jun and Aug–Dec 2024; selected Jan/Oct 2023; and Jan 2025. April 2025
lists only April 1–6. The 2025 GOES-16 year listing ends at April. Only January
2025 was acquired in bulk. Listing presence does not prove payload validity or
quality in the unacquired candidates.

Official authorities:

- [NCEI EXIS product overview](https://www.ncei.noaa.gov/products/goes-r-extreme-ultraviolet-xray-irradiance)
  and [L2 dataset DOI](https://doi.org/10.25921/94P8-YE57).
- [January 2025 archive](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2025/01/).
- [XRS L2 ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf)
  and [XRS L2 User Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf),
  15 December 2025 versions inspected.

Exact daily URLs, sizes, hashes and measured acquisition/registration UTC times
are in `data/manifests/goes_external_january2025.json`. The small observed summary
and dataset/split/label identities are in the derived external manifest. Original
NetCDF bytes remain immutable under Git-ignored `data/raw/noaa/history/...`.
Hashes identify locally acquired bytes; they are not NOAA-issued checksums.

## Instrument compatibility, timing, quality and missingness

**DOCUMENTED:** XRS-A spans 0.05–0.4 nm; XRS-B spans 0.1–0.8 nm. The primary
composite switches between photodiodes according to instrument conditions.
Irradiance is W/m². Native timestamps are record starts, elapsed seconds from
2000-01-01 12:00 UTC ignoring leap seconds; this is not TT/J2000. A timestamp
labels a one-minute average over a half-open bin. Operational delivery time is
not supplied by bin completion.

**OBSERVED:** 31 acquired files, **9,119,470 bytes**, **44,640 native records**;
1,440 per nominal day; no duplicate/off-grid timestamps or absent minute bins.
Measured coverage exactly matches the selected half-open month. Header identities
are g16, EXIS/XRS instrument FM1, Level 2, cadence PT1M. Processing algorithm is
`xrs04_avg.py`, version `[2,4]`, with product `v2-2-1`; these are distinct version
fields. Native processing/LUT/input-file metadata is retained in prepared artifacts.

| Channel | Valid bins | Quality rejected | Nonfinite raw flux | Nonpositive finite raw flux |
|---|---:|---:|---:|---:|
| XRS-A | 39,170 | 5,470 | 313 | 0 |
| XRS-B | 44,317 | 323 | 313 | 0 |

Both channels' status counts are 44,325 zero, 313 bad-data flag 2, and 2
interpolated flag 4. Electron-correction validity/significance additionally masks
channel-specific bins; status-zero alone does not certify usable data. Primary
selector counts are 5:44,564; 6:57; 10:19. These codes remain native metadata;
no calibration equivalence is invented from them.

P2 screening rejects nonzero status (including native interpolations), invalid/
interpolated/decaying electron corrections, channel-specific significant electron
contamination, nonpositive/nonfinite/out-of-range flux and sample counts outside
1–60. It retains partial-minute means when native flags pass and count is 1–59;
that does not imply sixty valid one-second samples. No extra interpolation or
cross-spacecraft gap filling is performed. Missing grid bins, if encountered,
remain NaN with false masks. Quality attrition must be reported with every score;
XRS-A rejection can alter the evaluated activity distribution.

**DOCUMENTED limitations:** science v2-2-1 includes revised calibration and
interpolation of short gaps, explicitly flagged; electron correction is imperfect,
and strong SEP events can cause residual artificial elevation. These flags do
not prove every retained value is physically error-free. No raw quality rule
was changed after seeing model performance.

**OBSERVED / UNKNOWN operational limitation:** native creation dates are December
2025 and processor metadata lists prior/current/next-day XRS/SEISS input files.
This establishes retrospective processing, but not which future samples influence
each retained value/flag. Context coordinates end by issuance, yet strict causal
native preprocessing and original as-issued availability remain UNKNOWN. This
milestone therefore cannot guarantee a live operational leakage claim. No such
claim or experiment is made; operational evaluation is blocked pending separate
versioned operational inputs and latency/dependency evidence.

## Authoritative flare catalog and disagreements

Selected authority: [NOAA NCEI science composite flare report archive](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/),
annual [2025 CSV v1-0-1](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/sci_xrsf-l2-flrpt_geo_y2025_v1-0-1.csv),
[metadata](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/sci_xrsf-l2-flrpt_geo_metadata.json),
and [flare-report ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES_Flare_Report_ReadMe.pdf).

**DOCUMENTED:** the science report consolidates `flsum` records, with SWPC location/
active-region supplements; it is indexed by peak and prefers designated spacecraft
with fallback. Timing/irradiance tolerances belong to NOAA's consolidation algorithm,
not a new local deduplication rule. Version 1-0-1 was released in June 2026 and
adds sequential flares beyond two. The metadata URL is unversioned and describes
an updating mission-length aggregation; its exact snapshot is independently pinned.
Future clean-room acquisition can be **BLOCKED_DATA** if that metadata changes:
retain the acquired snapshot, and never silently replace its pinned identity.
The pin establishes reproducibility of retained bytes, not indefinite remote
availability. Documentation reconnaissance timestamps that were not captured
remain null in the research-source ledger; registration time is separate.

**OBSERVED:** 3,277 annual unique records. January onset-selected and peak-selected
counts both equal **278: C=235, M=40, X=3**. Sources: GOES-16=275, GOES-18=3.
There are 26 missing ends, 26 sequential-number>1 events, only 3 in both sets,
and zero saturation flags. Missing ends remain null, never peak time or an
invented recovery. Catalog irradiance/class/source/timestamps remain independent
original fields; class is truncated by the authoritative algorithm, not recomputed
from rounded irradiance. Conflicting reuse of an event ID blocks parsing; exact
duplicate rows can be collapsed only with an explicit flag.

**DOCUMENTED:** C/M/X letter thresholds in one-minute XRS-B peak irradiance are
1e-6/1e-5/1e-4 W/m². Onset in the current science algorithm uses smoothed rising
irradiance and exponential-fit criteria; peak is the catalog peak, and end marks
half-height relative to background, not physical cessation. Detection notification
time can lag retrospective event start. The older operational four-rise rule in
[SWPC's product explanation](https://www.spaceweather.gov/products/goes-x-ray-flux)
must not be substituted for the science algorithm.

A bounded [SWPC edited-event Jan 1 cross-check](https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2025/01/20250101events.txt)
reveals disagreements: event 2060 is G18 C8.1 ending 04:03 UTC versus science
GOES-16 C8.1 ending 04:02; event 2110 is operational C7.1 ending 10:34 versus
science C7.2 ending 10:33. Both raw identities and the disagreement are retained
in the evidence ledger; science values are not overwritten or combined with
operational reports. No exhaustive cross-catalog comparison was performed.

**UNKNOWN:** detection completeness and minute-by-minute negative physical-flare
coverage. No catalog row means no qualifying *cataloged* onset under the fixed
policy, not proof of physical quietness. Peak-indexed annual data alone cannot
resolve every late-December ongoing event; the task is new onset, not ongoing
activity. Dataset edges and known crossing events are flagged conservatively.

## Alignment and candidate labels

The independent annotation layer preserves catalog/hash/original event ID/row,
start, peak, optional end, original class/source, sequence/saturation, dataset
identity, alignment policy and ambiguity flags. It inspects known intersecting
minute-bin support without rounding/snapping timestamps. Full-event known support
and onset-to-peak classification support are separate diagnostics. Missing end
limits known support to the peak minute without implying the flare ended then.
Overlapping known support is recorded; distinct events are never merged locally.

Fixed onset tasks: at least C1.0, M1.0, X1.0. For issuance `t` and horizon `H`,
label whether a catalog start is in **[t, t+H)** and its eventual catalog class
meets the task threshold. Start exactly at issuance has zero nominal lead; start
exactly at the horizon end belongs to the next window. An ongoing earlier event
is not a new onset, but an additional sequential onset can count. One-minute
coordinate precision is not a measured ±one-minute physical uncertainty.

Maturity is `max(horizon_end, every candidate onset's peak-bin end)`, including
subthreshold candidates used to certify a negative. Every candidate's start-to-
peak B support and the full B horizon must be usable. Source mismatch, saturation,
unsupported/off-minute coordinates, quality gaps, missing support and unresolved
classification maturity invalidate the affected candidate label without changing
its recorded class/outcome. Missing end is flagged but does not invalidate a task
whose quantity is onset, not duration. Zero-event inputs require explicit pinned
catalog provenance. Labels are separate artifacts, absent from features and fitting.

The initial complete two-channel P2 specification is reused: 120-minute context,
30-minute horizon, 30-minute stride. A single external test partition contains
both context and target support; there is no external train/validation/calibration
partition and no `TrainingSlice`. Complete-window attrition is distinct from
label validity. Prepared manifests report the exact retained/excluded origins,
label counts, class support and definitions; no event metric has been computed
from model output.

**OBSERVED preparation:** 1,488 candidate origins, 1,007 retained and 481 excluded;
60,420 valid target cells. Among retained origins, catalog-positive window counts
are C>=1:194, M>=1:39 and X>=1:3. These are window counts, distinct from the
278 selected catalog events and their exclusive class counts. All 1,007 retained
origins have valid, mature catalog-onset labels under the declared policy;
this does not establish physical catalog completeness.

## Evaluation protocol

**Flux:** fixed observation mask, native W/m² point forecasts, MAE and RMSE,
per-channel and per-lead scores, common-support persistence-relative MAE/MSE skill,
and observation/prediction coverage. Missing or nonfinite model outputs fail rather
than improve scores by shrinking support. Equal shapes do not establish alignment:
ordered origin IDs, issue times, bins, channel names/units, spec and dataset
fingerprints must match. RMSE is sqrt(pooled MSE), not mean lead RMSE. Train-scaled
MASE is deliberately omitted unless a future adapter binds independently verified
frozen training scales. The six July baselines are neither changed nor rerun.

**Origin-bin event decisions:** reuse P1 `evaluate_events` for explicitly supplied
binary decisions/probabilities and catalog outcomes on valid/mature origins.
POD=recall=TP/(TP+FN); FAR=FP/(TP+FP); precision=TP/(TP+FP);
F1=2TP/(2TP+FP+FN); TSS=TP/(TP+FN)-FP/(FP+TN);
HSS2=2(TP TN-FP FN)/[(TP+FN)(FN+TN)+(TP+FP)(FP+TN)]. Probabilities can yield
Brier score without an invented decision threshold. Zero denominators are null
with reasons. These are catalog-defined outcomes, not physical completeness claims.

**Event-level alarms:** require explicit alarm issue/validity intervals and a frozen
decision-policy identity. Deterministic maximum-cardinality one-to-one matching
prevents repeated alarms earning repeated credit. Ties prioritize earlier-issued
alarm/ID then earliest feasible onset/ID while preserving cardinality. Report
matched/unmatched events and alarms, event POD/FAR/precision/recall/F1, and nominal
lead times. Zero lead is separately flagged as no advance warning. Event lists
have no natural TN, so event-level TSS/HSS are not defined.

**Continuous forecasts to event decisions:** intentionally not implemented or
validated. Future rules must define onset versus threshold-exceedance, ongoing
flare handling, horizon, thresholds, debounce/refractory periods and probability
calibration on development data alone. Directly treating a flux threshold crossing
as NOAA onset would change the scientific target. Test-based threshold selection,
post-hoc matching tolerance selection and catalog definitions tuned to performance
are prohibited.

**Comparators:** persistence is appropriate for short-horizon flux and should be
supplied on exactly the same valid support from frozen causal contexts. Training
mean/climatology must be learned only from a declared development interval;
never January observations/labels. A 24-hour literature climatology is not an
assumed 30-minute event rate. No comparator is fitted or optimized here.

## Leakage, temporal generalization and uncertainty

Safeguards: separate source and evaluation identities; exact July-ledger pin;
raw-support overlap rejection; partition before windowing; context completion
before issuance; future grids strictly separated from context; no external fit
path/scalers or event-derived features; separate retrospective labels and maturity;
no interpolation; fixed a priori task thresholds; no external prediction/model
selection or threshold optimization. Retrospective native preprocessing causality
is explicitly unverified, so these safeguards must not be sold as operational
causality proof. No provisional SoLEXS values are mixed with GOES.

Future period comparisons must report flare-rich/quiet composition using a
predeclared catalog-based definition and all quality exclusions; do not choose
periods or subgroups based on model errors. “No cataloged onset” is not synonymous
with physically quiet solar emission. Same-spacecraft validation reduces, but does
not remove, calibration/activity-distribution confounding. Independent years,
spacecraft continuity checks and solar-cycle strata require separately selected
inputs and further authorization.

The implemented paired bootstrap resamples **whole nonoverlapping UTC-epoch
calendar blocks of the full regular origin axis**, preserving all paired origin
losses and empty target-support positions. Pool sums/counts, including unequal
edge-block sizes, rather than equally averaging block means. Initial future
analysis should predeclare 24-hour blocks and sensitivity at 3 and 7 days, with
minimum block duration at least the relevant context/horizon dependency support.
One day is a practical first unit, not established solar independence; longer
active-region evolution can dominate. Negative model-minus-reference loss favors
the model; intervals are descriptive percentile intervals, not significance tests.

Use the same blocks for paired model comparisons and keep channels/leads/masks
joint before loss reduction. Model failures cannot be hidden as missing loss
support. Event-rarity analysis should resample whole blocks and recompute confusion
counts, retaining undefined replicates for missing classes. The current bootstrap
implements scalar paired losses, not event skill confidence intervals. With three
X events and one month, strong significance/generalization claims are unjustified.
Two informative blocks are only a software minimum, not research adequacy. No
observational confidence interval or significance claim was produced.

## Recommended future experiments and scientific boundaries

1. Freeze an eligible P3 checkpoint, all development data and preprocessing/decision
   parameters before its independently authorized evaluation on this manifest.
2. Compare physical-unit flux errors against frozen persistence, by channel/lead,
   with coverage and descriptive paired block uncertainty; no January fitting.
3. Separately develop and validate an explicit event-risk interface on development
   catalogs, then test event matching with fixed zero/positive lead reporting.
4. Preselect additional distinct periods and instrument-transition studies;
   validate source versions and catalog differences before downloading broadly.
5. Obtain as-issued operational versions and processing/availability documentation
   before claiming deployable real-time flare-warning performance.

No improvement, event prediction skill, calibrated uncertainty, operational
readiness or solar-cycle generalization is established by this milestone.

## References

[1] Ahmadzadeh A. et al. “Challenges with Extreme Class-Imbalance and Temporal
Coherence: A Study on Solar Flare Data.” IEEE BigData (2019).
[Original](https://arxiv.org/abs/1911.09061).
[Paperclip passages](https://paperclip.gxl.ai/citations/papers/arx_1911.09061#L58-L69).

[2] Bloomfield D.S., Higgins P.A., McAteer R.T.J., Gallagher P.T. “Toward Reliable
Benchmarking of Solar Flare Forecasting Methods.” ApJL 747 L41 (2012).
[DOI](https://doi.org/10.1088/2041-8205/747/2/L41),
[original](https://arxiv.org/abs/1202.5995),
[Paperclip passages](https://paperclip.gxl.ai/citations/papers/arx_1202.5995#L60-L69).

[3] Leka K.D. et al. “A Comparison of Flare Forecasting Methods. II. Benchmarks,
Metrics and Performance Results for Operational Solar Flare Forecasting Systems.”
ApJS (2019). [DOI](https://doi.org/10.3847/1538-4365/ab2e12),
[original](https://arxiv.org/abs/1907.02905),
[Paperclip passages](https://paperclip.gxl.ai/citations/papers/arx_1907.02905#L68-L75,L86-L87,L104).

[4] Reep J.W., Barnes W.T. “Forecasting the Remaining Duration of an Ongoing Solar
Flare.” Space Weather (2021). [DOI](https://doi.org/10.1029/2021SW002754),
[original](https://arxiv.org/abs/2103.03957),
[Paperclip passages](https://paperclip.gxl.ai/citations/papers/arx_2103.03957#L22-L26).

[5] Plutino N., Berrilli F., Del Moro D., Giovannelli L. “A new catalogue of solar
flare events from soft x-ray GOES signal in the period 1986–2020.” Advances in
Space Research. [DOI](https://doi.org/10.1016/j.asr.2022.11.020),
[original](https://arxiv.org/abs/2211.10189).

[6] Politis D.N., Romano J.P. “The Stationary Bootstrap.” JASA 89(428), 1303–1313
(1994). [DOI](https://doi.org/10.1080/01621459.1994.10476870),
[author technical-report record](https://statistics.stanford.edu/technical-reports/stationary-bootstrap).
