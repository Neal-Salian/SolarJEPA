# Dataset card — provisional

Created 2026-09-29; intake update 2026-10-01. This describes a **proposed Aditya
research dataset**, two locally registered SoLEXS ingestion ZIPs, and a distinct
NOAA engineering sample. The two ZIPs are not the final training dataset;
archive identity verification is not scientific validation.

The [inventory](../data/manifests/aditya_inventory.json) pins July 1 and 3, 2024
L1 v1.1 archives with observed sizes/hashes/member listings. July 2 is missing
from the obtained collection, based on the user's report; no mission-wide
availability claim or gap filling is made. Nominal dates/levels/versions are
filename inferences. Actual coverage, header-verified detectors, cadence, units,
GTI/quality and calibration remain unknown. See [storage policy](DATA_STORAGE.md)
and [foundation verification](SOLEXS_FOUNDATION_VALIDATION.md).

| Product | Evidence-backed properties | Still unknown locally |
|---|---|---|
| SoLEXS | Full-disk 2–22 keV spectroscopy; nominal spectral 1 s and temporal 0.1 s; dual apertures [URSC](https://www.ursc.gov.in/SoLEXS.jsp) | Current released dates, bytes, file format/schema, usable cadence, data levels, calibration bundle, flags, gaps |
| ASPEX-SWIS | CDF; nominal 5 s scans, configurable; Level 2 science products; bulk plasma quantities and directional flux [FAQ](https://pradan1.issdc.gov.in/al1/faq.xhtml) | Actual released versions, usable species/energy bins, flags, overlap, bytes |
| ASPEX-STEPS | CDF; nominal 10 min; Level 2 preferred; SR/SP saturation exclusion [FAQ](https://pradan1.issdc.gov.in/al1/faq.xhtml) | Actual energy bins and quality fields by direction; gaps, overlap, bytes |
| GOES-16 XRS L2 sample | NetCDF v2-2-1; 2024-07-01 through 2024-07-03, 1-minute XRS-A/B and event state records | Measured details in [validation report](VALIDATION_REPORT.md) |

### Coverage is not instrument lifetime

The [SoLEXS calibration paper](https://arxiv.org/abs/2509.26292) reports operations
from late 2023/L1 observations in 2024. [STEPS operations](https://arxiv.org/abs/2507.18117)
analyzes January 2024–February 2025. These intervals do not establish the archive's
current completeness. No invented mission-wide missingness or sample counts.

### Intended uses and populations

Retrospective full-disk solar radiation forecasting and calibrated warning
evaluation; not region-localized warnings, MHD inference or operational alerts.
Aditya covers only part of the solar cycle, limiting cycle-wide generalization.
Selected days for engineering cannot establish rare-event skill. Multiple
detectors and external catalogue entries are not independent examples.

### Target definitions

Continuous target: future documented calibrated SoLEXS bands; retain peak-aware
native checks alongside one-minute averages. Optional auxiliary GOES XRS-B
trajectory must be declared as a different sensor target.

GOES peak 0.1–0.8 nm thresholds in W/m²: A1=1e-8, B1=1e-7, C1=1e-6, M1=1e-5,
X1=1e-4. Below A1 is sub-A, not “no event”. These are irradiance bands, not
valid flare labels for every nonzero background sample. Source:
[SWPC definitions](https://www.swpc.noaa.gov/sites/default/files/images/u2/Usr_guide.pdf).

Define separate targets: (a) maximum flux exceedance in `(t,t+H]`, including
ongoing events; (b) a catalogue event with **onset** in `(t,t+H]` whose eventual
peak is M+ or X+. For (b), the peak may occur after H, so label maturity extends
to the peak/end; enforce this in split purging and online calibration. If the
target instead requires a peak within H, name that distinct task explicitly.
An event peaking before t but continuing after t is not a new-onset warning.

### External catalogue and timing

Use NCEI L2 flare summary grouped by `flare_id`; the file contains state records,
not one independent flare per row. Validate actual variables from the downloaded
schema. The [guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf)
distinguishes algorithm detection time from physical event times. Preserve both.
Alternative: NCEI composite GOES 8–19 flare report / NOAA event records; audit
duplicate satellites and cataloguing changes. HEK can help regional association
but does not create region-resolved information in a full-disk input.

Convert each instrument's documented clock to UTC; retain time scale and bin
edges. Account for L1/Earth photon arrival differences using ephemerides for
fine alignment (order seconds, not a particle travel-time correction). Never
estimate a lag on test outcomes. Test sensitivity to ±one target cadence and
catalogue timing ambiguity on development data. Borderline class thresholds,
overlapping flares, occultation, background choice, saturation and gaps create
label uncertainty. Unknown/gappy target intervals are not negative labels.

### Quality and provenance policy

Keep raw immutable products, hashes, file sizes, download time, source URL,
instrument, level, response version, field definitions, uncertainty and flags.
Invalid inputs remain masked. The NOAA reference adapter conservatively keeps
only status-good positive finite flux, excludes interpolated/bad/eclipse
samples, and preserves electron-correction flags for sensitivity analysis.
No physical calibration is fabricated for Aditya. Processed data remain outside
Git; manifests and configuration are versioned. See download instructions for
mission terms and citations.

### Privacy and release

Telemetry is scientific observation, but portal credentials and account details
are private. Do not record them. Release scripts, manifests and aggregate
diagnostics; redistribute mission data only if source terms allow it.
