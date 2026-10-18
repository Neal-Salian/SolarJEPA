# Solar flare-event forecasting: retrospective foundation

Scientific verdict, 2026-10-18: **READY for the bounded exploratory retrospective
demonstration; NOT established as confirmatory or operational forecasting.**
No model was trained, refitted, recalibrated or selected here. No V2 pilot was
executed. All 22 existing January model trajectories are evaluated, including
persistence, classical baselines, three finetuned JEPA seeds, three frozen JEPA
seeds and three supervised controls. Preserved V1/V2 protocols remain unchanged.

## Authoritative catalog and definitions

**DOCUMENTED:** C+, M+, X+ denote total peak XRS-B irradiance of at least
1e-6, 1e-5 and 1e-4 W/m2 in the 0.1–0.8 nm band. Exclusive C and M classes
stop at the next decade. NOAA recommends science-quality data for research;
the composite NCEI flare report combines satellite sources and is distinct from
the legacy operational lists. A version, source satellite and byte identity are
necessary when identifying a catalog. [NCEI product guidance](https://www.ncei.noaa.gov/products/goes-1-15/space-weather-instruments),
[SWPC class definitions](https://www.swpc.noaa.gov/sites/default/files/images/u2/Usr_guide.pdf).

**DOCUMENTED:** Historical GOES-1–15 operational scaling differs from modern
science-quality calibration. Removing that historical scaling divides XRS-A by
0.85 and XRS-B by 0.7; these factors must not be applied again to the selected
science-quality GOES-R irradiances. This package requires the explicit convention
`GOES_science_quality_W_m2_no_legacy_scaling`, including empty catalog selections.
[NOAA operational data ReadMe](https://www.ngdc.noaa.gov/stp/satellite/goes/doc/GOES_XRS_readme.pdf).

**DOCUMENTED:** SWPC's public begin description uses four minutes of steep
monotonic rise; peak is the maximum minute and end is a decay criterion relative
to preflare background. This is not a specification for reproducing the current
NCEI science algorithm. [SWPC product description](https://www.swpc.noaa.gov/products/goes-x-ray-flux).

**DOCUMENTED:** The instrument team's science algorithm uses nine good minute
values and a jump/rise trigger, confirms peaks using later observations, and
handles end/post-event states separately. Overlap can leave an end unknown.
Thus a retrospectively assigned onset is not its recognition/publication time.
The package consumes catalog states and does not implement a substitute NOAA
detector. [Machol et al. (2026), Appendix A](https://doi.org/10.1029/2026JA035181).

**OBSERVED:** Current NCEI directory filenames extend into 2026 while the ReadMe
summary and separately updated metadata contain different date descriptions.
No new catalog was downloaded for this milestone. Existing pinned annual 2025
catalog/metadata snapshots are used through their verified preparation artifacts.
Filename date, retrieved metadata, actual event coverage and retrieval UTC must
remain separate. **UNKNOWN:** physical detection completeness and historical
event-level availability times. No catalog event is not proof of physical quiet.
[Flare Report ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES_Flare_Report_ReadMe.pdf),
[official catalog directory](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/).

## Verified repository and data audit

**OBSERVED:** Main and origin/main were both `1a4991d` after fetch. Main has
GOES ingestion/readers but no V1 forecaster. V1 is preserved at `644648f`;
external validation at `f30992` (full revision `f309921d776cf2deb632a886e8426e42bac1a050`)
and frozen external evaluation at `a502d3f`. This feature branch starts from
main, adds only the event layer, and imports no training framework. Existing
external label/matching rules were inspected and adapted rather than overlooked.

The existing GOES reader retains raw values and applies channel-specific quality,
electron-correction, count, range and cadence checks without interpolation.
Read-only audit measured the following native one-minute coverage:

| Month | Rows | Valid XRS-A | Valid XRS-B |
|---|---:|---:|---:|
| May 2024 | 44,640 | 42,695 | 42,696 |
| June 2024 | 43,200 | 43,074 | 43,195 |
| July 2024 | 44,640 | 42,329 | 44,406 |
| August 2024 | 44,640 | 44,548 | 44,548 |
| January 2025, external | 44,640 | 39,170 | 44,317 |

July 1–3's local flsum files contain 94 states, 28 IDs, 27 starts, 27 peaks,
21 ends and 19 post-event states. Peaks comprise 25 C and 2 M classes. The
June-30 event has only a post-event state in this selection; six other IDs lack
ends. Reconstruction preserves these unknowns. The generic labeling API
conservatively invalidates a selected collection containing incomplete start/peak
information until its coverage is resolved; it never fills timestamps from IDs.

V1 uses 120 minutes of context, a 30-minute trajectory and 30-minute issue stride.
Train/validation/test boundaries are May 1–July 22, July 22–August 1, and August
1–September 1. Complete support stays in each partition; normalization uses raw
training cells and checkpoints were selected on validation flux pinball. These
are flux safeguards, not evidence of event-disjoint splits. Event-group lists
were empty, and no independent event-probability calibration split exists.

August's saved test artifact has 1,436 origins and SHA-256
`59bcd596fefd6b10edeec93a69d7172343d4ffb7dc120f98a5185c1e35a3da82`
(64,965,489 bytes). The audit matched its contexts/targets exactly to native
NetCDF bins. NPZ omits explicit future coordinates and quantile levels, so those
must be bound to its source config rather than inferred from array shape alone.
This milestone's executable demonstration instead uses January JSON artifacts
with explicit grids and pinned provenance.

## Predictands, chronology and matching

Preserve the existing native `[issue,horizon_end)` catalog-coordinate definition.
At issue `t`, future bin j is `[t+j*60s,t+(j+1)*60s)`, j=0…29. The first
predicted average starts at issuance and completes one minute later. Do not shift
its start by one minute. Onset, peak, bin completion and publication are separate.

`events.labels` provides separate catalog-onset and catalog-peak labels. Final
catalog class is future truth only. Full XRS-B horizon quality and every candidate
start-through-peak bin are required, including subthreshold events. Maturity is
`max(horizon_end, all candidate peak-bin ends)`. Partition checks censor class
support or maturity across the boundary; feature availability cannot follow issue.
Source mismatch and saturation prevent valid negatives. Missing end alone does
not invalidate onset occurrence. Explicit selection coverage is not completeness.

`events.frozen` uses a fixed descriptive rule: predicted point-trajectory maximum
at least the native class threshold. It reports the first threshold-bin interval
and completion lead. This is a **candidate flux-derived alarm**, not a detected
NOAA flare or calibrated onset probability. All class thresholds/models are
reported; no winner or threshold is selected from January results.

Native catalog opportunity scores retain zero-lead onsets for compatibility.
Advance opportunity scores censor qualifying onsets before the declared minimum
lead (60 seconds by default). The one-to-one maximum-cardinality matcher maximizes
hits, then resolves ties by issue/alarm ID and onset/event ID. It counts each
observed event once; event lists do not have true negatives. With `minimum_lead=0`
the generic matcher supports descriptive zero-lead matching and marks it as not
advance warning. It cannot establish genuine operational advance forecasting.

There is no implicit refractory interval or alert suppression: each positive
issuance is an alarm and unmatched repeated alarms are false alarms. Duplicate
eligible alarms are reported. Events without eligible mature forecast exposure
are counted separately from misses inside exposure. False alarms/day uses the
union of eligible nonoverlapping `[issue+minimum_lead,horizon_end)` intervals;
issued-horizon days and warning fraction use full issued intervals separately.

Catalog start-to-known-end (or peak when end is missing) defines an evaluation-only
evolution stratum. A prior missing end after peak remains unresolved; it is never
silently treated as physical cessation. These strata can overlap. Absence of known
catalog evolution is not physical quiet. No retrospective state enters prediction.

## Exploratory January result

**OBSERVED:** 1,488 candidate origins, 1,007 retained and 481 excluded by the
historical preprocessing/window policy. All candidate positions remain in the
UTC-block resampling axis with exclusions invalid. Complete future two-channel
quality conditions the population, so this is not a deployment availability rate.
All 22 frozen model outputs and their historical semantic fingerprints were
verified, together with source sizes/hashes, full label definitions, grids,
catalog identities, provenance/support diagnostics and class maturity.

Candidate catalog positives are C+194, M+39, X+3. Three M+ and thirteen C+ origins
have zero-lead onsets and are censored from advance scoring. M+ has 36 eligible
events; 7 of 43 aligned M+ events lie outside evaluated exposure. C+ has 188
eligible events versus 181 positive advance windows, illustrating why window
positives and unique event counts differ. At M+, observed future threshold
exceedance occurs in 64 windows: 29 overlap onset windows, 35 are flux-only and
10 onset-only. These tasks cannot be substituted.

The fixed M+ alarm rule yields the following unique-event contingency counts;
opportunity CSI happens to equal event CSI for this M+ selection:

| Frozen model | Hits | False alarms | Misses | CSI |
|---|---:|---:|---:|---:|
| Persistence | 4 | 23 | 32 | 0.0678 |
| JEPA finetuned seed17 | 4 | 26 | 32 | 0.0645 |
| JEPA finetuned seed29 | 4 | 23 | 32 | 0.0678 |
| JEPA finetuned seed43 | 4 | 22 | 32 | 0.0690 |

This supports no robust improvement claim. All three finetuned models miss the
three eligible X events with no X alarms. C+ finetuned alarms occur at every
eligible issuance: background exceedance is an inadequate new-onset rule.

The report includes prevalence, TP/FP/FN/TN, precision/recall, FAR/FPR, CSI,
TSS/HSS, balanced accuracy, event IDs/leads, coverage and stratified counts.
Undefined denominators are null. Descriptive 1,000-replicate day-block intervals
use seed17. M+ CSI ranges broadly, with lower endpoint zero for these four models.
For X+, 149/1,000 bootstrap replicates have undefined CSI; a conditional [0,0]
interval among defined replicates is not evidence of certainty or predictive
coverage. One-day blocks exceed 150-minute context+horizon support but cannot
establish independence or capture solar-cycle/active-region variability.

Five marginal flux quantiles do not determine the joint probability of any flare
or threshold crossing within 30 minutes. No maximum-marginal or independence
product conversion is used. Brier/reliability/PR probability analysis awaits a
scientifically identified, development-calibrated event-probability model.

## Reproduce without training

Install this branch normally (`python -m pip install --no-deps .`) into an
appropriate existing dependency environment. Locate the two immutable historical
output directories explicitly; roots are not stored as machine-specific paths:

```bash
python scripts/evaluate_flare_events.py \
  --forecast-root "$FORECAST_ROOT" \
  --label-root "$LABEL_ROOT" \
  --output results/events/january2025.json
```

`FORECAST_ROOT` contains the existing
`goes-v1-external-january2025-approved-run/{inputs,predictions,resolved_protocol,summary}.json`.
`LABEL_ROOT` contains existing `goes-external-january2025-acceptance-d/` preparation
artifacts. [The config](../configs/events/january2025_frozen.json) pins every
consumed file. It refuses changed hashes, unsafe paths, mismatched lineage,
missing/reordered origins, selected model subsets, altered label/support semantics,
nonfinite/boolean flux and output overwrite. It performs no downloads, inference
or fitting. Reports stay under ignored `results/`; missing historical files are
an explicit dependency, not an instruction to regenerate or retrain.

## Readiness and next experimental milestone

**OBSERVED:** the deterministic retrospective foundation is implemented and was
independently scientifically reviewed. **INFERRED:** simple flux exceedance is
unlikely to provide useful new-onset discrimination at elevated background;
current observations motivate testing an independently frozen onset decision rule.
**UNKNOWN:** catalog completeness, historical delivery latency, native reprocessing
causality, calibrated event probabilities, operational skill and broad generalization.

Next: define an onset-specific rule/calibrator using development support only;
freeze its cohort, alert episodes, thresholds, exposure, latency assumptions,
event-disjoint splits, maturity/purge rules and metrics. Select and verify a
genuinely uninspected period with enough M/X support, then run that frozen
evaluation without adapting it to its labels. Existing August/January exposures
cannot become confirmatory by renaming them. Any future retraining or acquisition
is a separate milestone decision.
