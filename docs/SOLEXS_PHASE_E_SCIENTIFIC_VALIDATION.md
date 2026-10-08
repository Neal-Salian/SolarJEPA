# Phase E — authoritative SoLEXS scientific validation

Investigation began **2026-10-08**; continued and reviewed **2026-10-09,
Asia/Kolkata**. Branch: `research/phase-e-solexs-validation`. Scope: the two
registered July 2024 archives, not every SoLEXS release.

**Verdict: BLOCKED for defensible SoLEXS forecasting.** Native integrity,
loadability and descriptive diagnostics are verified. Applicable absolute timing,
effective exposure/quality and calibration contracts remain unresolved. No
scientific gate is fully passed. This is a published evidence checkpoint for
human review, not scientific clearance or integration permission.

## Objective and repository baseline

Determine what can be trusted for future time-series experiments without
developing, training or modifying SolarJEPA models. The independently verified
base is P2 `656e540162c635d4c2274b4469ae11247290f986`, whose title and ancestry
match the expected foundation. Its source, tests, dependencies, scripts,
manifests and relevant history were inspected before conclusions were drawn.

The original checkout stayed on P2, retaining its untracked `.agents/` skill and
`docs/P1_FINAL_INTEGRATION_REAUDIT.md`. A native managed worktree was created from
the exact commit, the explicitly named Phase E branch was created there and
pushed with upstream before milestone edits. Main remained
`1a4991da4dda9676caeb1d7e35a03408528c3188`; P1 remained
`595371190177de4638962aafa327f611b2045b90`. P3 was absent from the observed local
refs and remote advertisement. This does not establish the state of an unpublished
teammate checkout. No P3 ref or model file was changed.

Evidence vocabulary: **DOCUMENTED** is an original source's stated meaning
within its applicability; **OBSERVED** is directly inspected bytes/execution;
**INFERRED** is a derivation; **UNKNOWN** is not established. Portal acquisition
remains explicitly user-reported. Hash agreement is not independent portal
authentication or a scientific compatibility certificate.

The [evidence matrix](SOLEXS_PHASE_E_EVIDENCE_MATRIX.md) supplies original source
versions, page/section locators, code links and uncertainty for the claims below.
The [Phase E evidence record](../data/manifests/solexs_phase_e_evidence.json)
contains measured identities and machine-readable decisions.

## Actual data and calibration inventory

No science archive was downloaded, replaced or persistently extracted.

| Registered archive | Bytes | Full observed SHA-256 |
|---|---:|---|
| `AL1_SLX_L1_20240701_v1.1.zip` | 6,036,792 | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` |
| `AL1_SLX_L1_20240703_v1.1.zip` | 6,216,112 | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` |

Both match the unchanged registration inventory. Each ZIP has three directory
members and four gzip FITS members: SDD2 LC, PI and GTI, plus empty SDD1 GTI.
There is no SDD1 LC/PI or HK in these archives. The inspected local Aditya tree
has no matching July HK science product. Acquisition time, globally available
coverage and July 2 availability remain UNKNOWN; nominal filename dates and
filesystem timestamps do not establish measured UTC coverage.

Eight FITS products passed structure, ZIP CRC, gzip integrity and all sixteen
present HDU DATASUM checks. CHECKSUM cards are absent. Each PI expands to
472,443,840 bytes and was inspected through the existing bounded temporary
loader and chunked iteration. No arrays or extracted FITS were committed.

All **39** local source entries in the C/D/D.1 manifests match their pinned
size/SHA-256. The supplied official tools archive is present: 19,730,838 bytes,
SHA-256 `348014aefa50ade556ec4a160a3cfe0b08095bde84b4650a27d6b5d3bf7fa2d3`.
Its 45 outer members and 35 regular-member hashes match D.1 records; nested
distribution archives were not recursively interpreted or installed. Its
CALDB contains the same three ARF/RMF/bounds resources already inspected in D.
This establishes local byte identity, not epoch or pipeline applicability.

## Literature and documentation findings

The requested paper is verified as Sarwade et al., *Solar Low Energy X-ray
Spectrometer on board Aditya-L1: Ground Calibration and In-flight Performance*,
arXiv **2509.26292v2**, revised **2025-11-03**, JATIS **11(4), 045005 (2025)**,
DOI [10.1117/1.JATIS.11.4.045005](https://doi.org/10.1117/1.JATIS.11.4.045005).
The original versioned full text and Paperclip source lines were read. Publisher
page retrieval failed; journal metadata was verified from arXiv. [Paper P](https://arxiv.org/abs/2509.26292v2).

P §§4–5 describes temperature-dependent gain, redistribution/effective area,
different ground/flight deadtime behavior and detector limitations. Its §5.4
GOES comparison uses corrected SDD2 and one-minute XRS-A observations in
April–May 2024, with quiet/peak residuals. XRS-B is compared through counts and
plasma-model relations. Its XSM comparison also shows residual calibration
effects. These establish methodology and limitations, not applicability to
our July pipeline-1.1 files or a forecast result. [P](https://arxiv.org/html/2509.26292v2#S5.SS4).

The locally verified PRADAN manual M is v1.0, January 2025. It describes L1
energy-calibrated counts and unapplied deadtime at that date, cautions against
fitting below 2.8 keV, and gives dated uncertainty/high-rate guidance. None of
those statements supplies a complete release-1.1 correction contract. U, updated
2026-06-09, distinguishes data, processing and analysis-tools releases. M/U
original provenance is user-reported PRADAN download, with local hashes verified.

Woods et al. (2024), *GOES-R Series X-Ray Sensor (XRS): 1. Design and Pre-Flight
Calibration*, explains wavelength-dependent photodiode response and flux
conversion assumptions. NOAA's science-product guide independently defines
GOES bands, clocks and quality. A disagreement between instruments need not
isolate a SoLEXS calibration error. [G](https://doi.org/10.1029/2024JA032925),
[N](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf).

Paperclip was used for targeted arXiv discovery, exact metadata lookup and
original line retrieval, including the additional GOES paper. AI summaries
were not accepted as evidence. Live PRADAN downloads remain protected or
inaccessible to anonymous retrieval; that is not global resource unavailability.
The bounded official search found no applicable pipeline-1.1 erratum.

## E1 — timing validity: BLOCKED_EXTERNAL_EVIDENCE

**DOCUMENTED:** M §2.2 defines Unix seconds from 1970-01-01 UTC; §2.1.3 defines
PI TSTART as integration start. U associates July–September re-release data 1.1
with processing 1.1 and timestamp updates. Later processing 1.2 changed date/MJD
cards. Neither resolves precedence for the actual conflicting 1.1 headers.

**OBSERVED:** LC TIME equals PI TSTART at all 86,400 rows on each day. Each native
increment is one, with no duplicate, backwards or absent internal coordinate row.
The LC RATE extension carries `MJDREFI=40587`, `MJDREFF=0.22916666651`,
`TIMESYS=UTC`, `TIMEREF=LOCAL`, `TIMEUNIT=s`, `TIMEDEL=1`, `TIMZERO=0`.
`TIMEPIXR`, standard `TIMEZERO`, and measured clock-error/correction cards are
absent. Both PI HDUs lack epoch/date/reference cards; its time columns encode s.
GTI table columns lack time units/epoch, although SDD2 primary envelope strings
include `+00:00`.

| Nominal date | Native first / last | LC stored DATE-OBS / DATE-END |
|---|---|---|
| July 1 | 1719792000 / 1719878399 | July 1 05:30:00 / July 2 05:29:59 |
| July 3 | 1719964800 / 1720051199 | July 3 05:30:00 / July 4 05:29:59 |

**INFERRED:** Unix projection gives nominal midnight–23:59:59, conflicting with
the LC date/MJD cards by approximately 5.5 hours. This is a comparison hypothesis,
not accepted coverage or permission to shift/repair data. Coordinate equality
supports a possible LC-start convention, not absolute UTC or bin support proof.
FITS standard timing defaults cannot establish what this pipeline actually did.

**Required:** mission-approved TIME/card precedence, LC bin position/completion,
GTI clock/endpoints, correction/leap handling and clock uncertainty for these
archive identities. Validate boundary rows against a mission reference before
UTC conversion, alignment or forecasting windows.

## E2 — calibration validity: BLOCKED_EXTERNAL_EVIDENCE

**OBSERVED:** all PI CHANNEL vectors are constant 0–339. The official/candidate
RMF EBOUNDS labels are 1–340; MATRIX F_CHAN starts at 1. RMF/legacy ARF encode
`CREATOR=solexs_pipeline-1.0`, whereas science files encode pipeline 1.1.

| Resource | Measured structure | SHA-256 |
|---|---|---|
| Official/candidate SDD2 RMF | 340 EBOUNDS; 2,250 × 340 finite nonnegative matrix; keV | `fc8ab03f15bb21ff066426cd6047519d57ffe017bb776bb88a5a65136deb63db` |
| Official/candidate incident-grid ARF | 2,250 rows; keV/cm2; exact RMF incident grid | `0f08199b3ef2f346979c58e0df83451fa23ae72a39fcaaa3d85bfe66b4b5bdc7` |
| Official/candidate text bounds | 340 × 2; no encoded unit | `684f916612003706062d509ab805ae2cda763f99a83f85ce81028a94aea0949e` |
| Newer candidate PI-grid ARF | 340 rows; keV/cm2; exact EBOUNDS grid | `a07eec19cfee37bc0f840e77f0eeaea7a232940f034a20ca04c6c5ca1dec6257` |

Grid agreement is structural evidence. OGIP O requires response/spectrum channel
correspondence; a +1 relabeling requires applicable authority. The newer PI-grid
ARF is not in the inspected official tools-1.1 CALDB. Public tools-1.3 and 1.6
deadtime files share a basename but have different hashes, schemas and offsets;
selection by basename is invalid. Full pins remain in the source manifests.

**Required:** approved detector/epoch/pipeline response pairing and indexing,
gain/temperature lineage, correction state, units/uncertainties, and numerical
reference output. No calibration, channel renumbering or flux conversion was
applied. Missing implementation is downstream of missing scientific authority.

## E3 — exposure and quality: BLOCKED_EXTERNAL_EVIDENCE

| Nominal date | GTIs | Sum(STOP−START), native | EXPOSURE card | Finite LC / all-NaN PI rows | LC NaNs |
|---|---:|---:|---|---:|---:|
| July 1 | 4 | 86,268 | string `86272.0` | 86,272 | 128 |
| July 3 | 3 | 86,395 | string `86398.0` | 86,398 | 2 |

Intervals are finite, ordered and nonoverlapping. Inclusive point membership
exactly equals finite LC rows and PI's all-NaN mask complement. This establishes
a native sample-count relation; **continuous good exposure remains UNKNOWN**.
PI EXPOSURE and TELAPSE equal 1 s on every row, including missing spectra;
summing them across the whole file gives 86,400, not verified live exposure.
No partial-NaN PI rows, negative/nonfinite finite-value anomalies or embedded
quality/error columns were found. These are numerical findings, not saturation
clearance, uncertainty estimates or validated health screening.

**Required:** applicable continuous bin/GTI arithmetic, deadtime/reset/operational
quality rules and a reference correction output. If the approved workflow uses
HK, matching July HK becomes a BLOCKED_DATA dependency. Its exact names,
availability and compatible schema are UNKNOWN. Preserve NaNs and empty GTIs;
do not interpolate July 2 or classify it as physically unobserved.

## E4 — detector/product selection: PARTIALLY_VERIFIED

SDD2 LC/PI association is OBSERVED from FILTER cards; GTI detector association
is INFERRED from member names. SDD1 provides only empty GTIs. M recommends SDD2
for 2024 spectral work, but the reason for these specific empty SDD1 GTIs remains
UNKNOWN. SDD2 alone is the supported inspection candidate; combining streams is
neither supported by available products nor scientifically approved.

LC/PI coordinates and missingness match. Their quantities are not established as
equivalent: full-channel sums match zero finite LC rows. The unapproved text-grid
tools hypothesis `[41:313]` differs on 19/15 rows; control `[41:314]` differs on
14/5, maximum difference 1. `NUMBAND='4'` and exact LC band-generation policy
remain unresolved. Do not tune a band to force agreement.

**Required:** approved SDD2 task-specific selection/LC generation policy, with
response and quality gates passed. SDD1 science is BLOCKED_DATA for this sample;
its absence explanation is optional for an SDD2-only milestone.

## E5 — GOES/SoLEXS compatibility: PARTIALLY_VERIFIED

NOAA defines XRS-A 0.05–0.4 nm and XRS-B 0.1–0.8 nm, versus nominal SoLEXS
2–22 keV spectroscopy/counts. **INFERRED:** the nominal XRS-A/SoLEXS intersection
is approximately 3.1–22 keV; it is not an equal detector response or an approved
flux representation. P's §5.4 describes a 3.1–24.8 keV comparison, so treatment
above the stated SoLEXS range must be resolved rather than extrapolated.

Future response-aware comparisons are plausible, as demonstrated in P, but need
approved incident-spectrum/band construction, response assumptions, observer and
1-AU conventions, UTC/bin/cadence alignment and separate source quality. A
shared metadata contract is implemented; a shared calibrated numeric scale is
not. Correlation or nominal calendar overlap cannot establish transfer-learning
validity. No GOES conversion, resampling, alignment or split was changed.

## E6 — forecasting readiness: BLOCKED_EXTERNAL_EVIDENCE

| Use | Decision for these observations |
|---|---|
| Inspection and visualization | VERIFIED as native diagnostics; physical axes/calibration are not implied. |
| Calibrated physical analysis | BLOCKED_EXTERNAL_EVIDENCE by E1–E3. |
| Exploratory statistical modeling | PARTIALLY_VERIFIED only for descriptive native statistics; sequence fitting/training remains blocked. |
| Defensible forecasting | BLOCKED_EXTERNAL_EVIDENCE; no validated target/causal time support or scientific experiment exists. |

No forecasting target, issue-time availability, uncertainty model or flare label
is established. Two noncontiguous pilot days do not demonstrate suitable activity
coverage or independent chronological train/tune/calibration/test support. No
arbitrary minimum duration is imposed here. Missingness may depend on instrument
state; treating it as random would be an unsupported assumption. Training remains
rejected by the unchanged source gate.

## Verification and next milestone

The inherited full suite passed **1,084 tests**, with one retained netCDF4/NumPy
ABI warning. The native scientific subset passed **109 tests**. Actual archive
summaries exactly match preserved P2 summaries; native response comparisons match
Phase D. Installed scientific module bytes match the worktree. Rechecked prior
109 scientific/source identities, 290 historical output hashes and 32 indexed
experiment directories; no scientific training experiment was run. See the
[implementation report](SOLEXS_PHASE_E_IMPLEMENTATION_REPORT.md) for executed
commands, strict-warning failure, final checks and review limitations.

Recommended next scientific milestone: **mission-authoritative release-1.1
timing/exposure/correction and response applicability closure**. Obtain written
guidance or an applicable erratum tied to these identities, then a small approved
reference product/output and conditional HK. Validate boundary timing, live
exposure, channel mapping and uncertainty on the immutable pilot before selecting
a bounded historical science/HK collection and forecasting contract. A newer
recommended release is an alternative only if the mission cannot validate this
one. No bulk acquisition, P3 integration, model development or merge is authorized
by this verdict.
