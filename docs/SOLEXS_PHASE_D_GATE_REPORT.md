# Phase D — SoLEXS timing, calibration and cross-instrument readiness

Investigation date: **2026-10-02**; final verification/handoff:
**2026-10-03 (Asia/Kolkata)**. Milestone branch:
`data/solexs-timing-calibration`. This report concerns the two obtained July 2024
L1 data-version-1.1 samples, not all SoLEXS releases. The investigation is complete
when its evidence, reproducibility and review checks pass; that does not make the
scientific acquisition gate pass.

**Result: BLOCKED for Phase E historical acquisition.** Native access remains
validated. Exact pipeline-1.1 chronology, continuous GTI/exposure policy and an
approved correction/response compatibility chain are still missing. No UTC
repair, correction, calibration, gap filling, inter-instrument alignment or final
dataset was produced.

## 1. Verified repository starting state

The applicable root `AGENTS.md` was read before work. Remote metadata was fetched;
the clean local `main` and `origin/main` both pointed to
`f9a0d2b7e266680234f70a9130edf83a45c04a13`, the user-managed Phase C merge. Its
tree exactly matched Phase C's final `bc364dc` tree. The Phase D branch did not
exist locally or remotely; it was created from that main and immediately published
with upstream tracking. No Phase D change is integrated into main.

| Functionality at that base | Classification and executable evidence |
|---|---|
| Registration, source identities, immutable ZIP inventory | VERIFIED: actual two ZIP sizes/hashes, inventory validation and storage tests. |
| Bounded gzip/FITS access; native LC/GTI loading and chunked PI | VERIFIED: merged code, 144-test baseline and complete sample execution. |
| Portable native integrity/time/quality summaries | VERIFIED: eight FITS products, sixteen DATASUM checks, deterministic Phase C summary. |
| Exact SoLEXS UTC conversion, LC bin policy, continuous GTI/exposure filtering | MISSING implementation; scientific applicability UNKNOWN. |
| Approved HK/correction/energy/response/flux pipeline | MISSING implementation; candidate source inspection exists, compatibility UNKNOWN. |
| GOES reference loading, quality masks and saved outputs | VERIFIED against six original files and saved artifacts. |
| Cross-instrument dataset, training and frontend | PLANNED/DOCUMENTED ONLY; no implementation or execution. |

Inspection covered refs/branches/history, source/tests, the six existing scripts
(Phase D adds a seventh),
configuration/manifests, dependencies, actual raw inputs and generated artifacts.
Astropy and NumPy were already available and pinned; no dependencies were added.
The initial current tracker still described Phase C awaiting integration even
though the Git tree proved it merged. README/current tracker are updated for
Phase D; historical Phase A/B/C reports and acquisition inventory retain their
original scope. Documentation did not decide what to reimplement.

## 2. Evidence sources, versions and authority

**DOCUMENTED** means an authoritative definition within its stated applicability;
**OBSERVED** means direct bytes, metadata or execution; **INFERRED** means a
derivation; **UNKNOWN** means not established. Observed author-tool code is not
automatically a mission-approved definition for pipeline-1.1 products.

| ID | Source and version | Scope |
|---|---|---|
| M | [Official SoLEXS guide][M], v1.0, January 2025, 19 PDF pages | User-supplied PRADAN original; generic product definitions, predates the 1.1 re-release. Printed pages 2/3/4 are PDF pages 5/6/7. |
| U | [Official release/update notes][U], updated 2026-06-09 | Explicit data/software release lineage; not an exact header-repair instruction. |
| T11 | [Author tools 1.1][T11], commit `24693afeeab5f67ce0277fe84de059bbe54223cb` | Legacy code/resources; not the generating pipeline. |
| T13 | [Author tools 1.3][T13], commit `a2db6a92da6399fb3abafc115a430e9be08ddce1` | HK-based correction workflow. |
| T16 | [Author tools 1.6][T16], commit `51403b02fbb7ae2eb0b4eb539e881ffd56c1c772` | Public HEAD observed at investigation; changed corrections and candidate CALDB. |
| W | [Instrument-team workshop][W], commit `d7453029cfac574c0cf444ca47d2ce97fcc17245` | Tools-1.3 examples and pipeline-2.0-beta.1 headers; not pipeline-1.1 policy. |
| P | [Instrument calibration paper][P], arXiv v2, 2025-11-03; DOI 10.1117/1.JATIS.11.4.045005 | Instrument calibration/response context; not a version compatibility certificate. |
| F | [FITS standard 4.0][F], updated 2016-07-22; language-edited 2018-08-13 | Standard keyword definitions; not authority to repair this mission release. |
| O | [OGIP CAL/GEN/92-002][O], version 2020-12-08; 2022 URL edits | Response/channel correspondence requirements. |
| N | [NOAA XRS L2 guide][N], 2025-12-15 | GOES reference conventions, reconciled with actual local v2-2-1 files. |
| C | [PRADAN FAQ][C] and anonymous protected-route checks | Resource families/access behavior; authenticated catalogue contents not inspected by the agent. |

The [Phase C source manifest](../data/manifests/solexs_guidance_sources.json)
retains 27 pins; the [Phase D source manifest](../data/manifests/solexs_phase_d_sources.json)
adds nine. All **36** local source byte sizes/SHA-256 values were rechecked,
including the supplied originals against their ignored repository copies.
Manual: 363,311 bytes, SHA-256
`d97c83618c85a0984e7dd0300ce5c16c4748ed5facde525949f902fe9f72abda`.
Updates: 2,481 bytes, SHA-256
`7fc0229985fef2bd60ab23bc554c09e64f526719f11825e44a60eed12f5396ce`.
Portal origin is attributed to the user's download; no independent portal
checksum was supplied. The agent did not install or execute external tools.

## 3. Timing findings and conflicts

**DOCUMENTED:** M §2.2 defines Unix seconds from 1970-01-01 00:00:00 UTC.
M §2.1.3 defines PI `TSTART` as integration start and `TELAPSE` as its one-second
duration. It does not specify LC start/centre/end placement. U records the
2025-02-14 re-release of July–September 2024 as data 1.1 / processing 1.1 with
UTC-consistency timestamp updates; processing 1.2 subsequently updated date and
MJD reference cards. Neither statement supplies an exact 1.1 precedence rule.
Data, processing and analysis-tools versions are distinct identities. [M][M], [U][U]

**OBSERVED:** each SDD2 LC has 86,400 rows. `TIME` equals every corresponding PI
`TSTART` exactly, is finite/strictly increasing, and has step 1 throughout. There
are no duplicate coordinates, backwards steps or absent internal grid rows.
The missing measurements are NaNs on that grid, not missing timestamp rows.

| Nominal archive date | First / last native LC and PI coordinate | LC date cards, as stored | Unix-calendar comparison only |
|---|---|---|---|
| July 1 | 1719792000 / 1719878399 | `2024-07-01 05:30:00` / `2024-07-02 05:29:59` | July 1 00:00:00–23:59:59 |
| July 3 | 1719964800 / 1720051199 | `2024-07-03 05:30:00` / `2024-07-04 05:29:59` | July 3 00:00:00–23:59:59 |

The last column is **INFERRED under the manual's Unix hypothesis**, not accepted
SoLEXS absolute coverage and not an alignment input. The inter-archive native
jump is 86,401, leaving 86,400 one-step coordinate slots unrepresented locally.

**OBSERVED:** LC `RATE` cards contain `MJDREFI=40587`,
`MJDREFF=0.22916666651`, `TIMEUNIT=s`, `TIMESYS=UTC`, `TIMEREF=LOCAL`,
`TIMEDEL=1`, `TIMZERO=0`, and `NUMBAND='4'`. The fraction is approximately
19,799.999986 seconds, or 5.5 hours, of a reference day. `TIMEZERO`, `TIMEPIXR`,
`TREFPOS` and absolute clock-error/correction cards are absent. LC column TUNITs
are absent. PI time columns encode seconds, but **neither PI HDU carries the
epoch/date/time-reference cards**. GTI tables lack an encoded epoch/unit;
SDD2 primary envelope strings carry `+00:00` and nominal midnight–23:59:59.
All original cards remain intact in the native evidence.

**DOCUMENTED standard context:** F §§9.2–9.5 define split MJD reference epochs,
`TIMEOFFS`, reference position and `TIMEPIXR` (default 0.5; 0/1 denote bin
start/end). `TIMZERO` is not the standard `TIMEZERO` spelling. A standard default
does not prove this pipeline used it correctly, or authorize discarding conflicting
cards. Missing clock-error cards do not establish measured zero timing error. [F][F]

**OBSERVED / INFERRED:** the pinned legacy LC writer generates this fractional
reference and timezone-dependent date strings. A similar pipeline header defect
is plausible, but its creator differs from these pipeline-1.1 products. The
manual §3.3 numerical example also labels Unix 1707715800 as 11:00 UTC, whereas
explicit UTC calendar projection gives 05:30. This 5.5-hour inconsistency is a
conflict, not an alternative scientific timezone. Later author code uses UTC
utilities; that change does not certify the generating pipeline. [T11][T11]

**UNKNOWN:** exact TIME/date/MJD precedence; LC bin placement; product clock
accuracy and leap-second handling; GTI time-reference linkage and continuous
endpoints. Coordinate equality with documented PI integration starts supports
an **INFERRED** LC-start hypothesis only. The [NIST leap table][L] establishes
no leap insertion in July 2024, but does not validate the mission counter or its
historical offset handling. No assumed epoch/timezone, header repair, fixed
5.5-hour shift or leap correction is implemented.

## 4. GTI, exposure and detector findings

**DOCUMENTED:** M §2.1.1 defines GTIs by Sun-in-FOV, operational detector and
recommended instrument-health ranges. M §2.3 says detectors without valid
observations have no generated LC/PI. These describe scientific intent, not
exact continuous endpoints, leap handling or exposure arithmetic. [M][M]

**OBSERVED:** two separate detector directories are present. SDD2 `FILTER`
metadata confirms its LC/PI association. SDD1 has an empty GTI only; its detector
association is **INFERRED from the member name**, not an observed detector card.
All SDD2 intervals are finite, ordered, nonoverlapping and START ≤ STOP.

| Nominal date | SDD2 intervals | Sum(STOP−START), native | GTI extension `EXPOSURE` string | Finite LC points inside inclusive endpoints | LC NaNs outside |
|---|---:|---:|---|---:|---:|
| July 1 | 4 | 86,268 | `86272.0` | 86,272 | 128 |
| July 3 | 3 | 86,395 | `86398.0` | 86,398 | 2 |

Inclusive point membership exactly equals the finite LC mask: no finite point
outside and no NaN inside. The EXPOSURE strings equal those point counts, not
the sum of endpoint differences. Exact seven endpoint pairs are retained in the
[observation manifest](../data/manifests/solexs_phase_d_observations.json).
**INFERRED:** endpoints likely label included one-second sample coordinates in
these files. **UNKNOWN:** continuous valid duration, bin edges, partial exposure
and a scientifically approved filtering rule. Neither endpoint count nor header
string is assigned as corrected continuous exposure.

**OBSERVED:** SDD1 GTIs have zero rows, `EXPOSURE='0.0'`, blank envelope strings,
and no LC/PI payloads. **DOCUMENTED:** the guide reports frequent SDD1 saturation
in 2024 and recommends SDD2 spectral analysis. **UNKNOWN:** why SDD1 is empty on
these particular dates; saturation, pointing, health and operational causes are
not distinguished by these files. No synthetic GTI or detector flag is created.

## 5. Calibration and physical-quantity findings

**DOCUMENTED:** M calls the L1 PI energy-resolved calibrated Type-II spectra;
CHANNEL is an energy-channel index and COUNTS integration counts. This does
**not** establish incident physical flux or remove response/correction requirements.
M §2.4 requires CALDB ARF/RMF for physical spectral interpretation. M §4.5
describes 340 grouped channels and cautions against spectral fitting below
2.8 keV with that calibration. Applying a separate gain recalibration by default
would be unsupported. [M][M]

**DOCUMENTED:** P discusses gain/temperature, fast/spectral-chain corrections,
redistribution and effective area. Its corrected May 2024 GOES comparison does
not certify our pipeline-1.1 absolute chronology or these resource identities. [P][P]

**OBSERVED:** sample CHANNEL labels are 0–339, constant on all rows; COUNTS is
86,400 × 340 floating values. Candidate response metadata are:

| Local candidate | Bytes | Measured structure / encoded units | Applicability |
|---|---:|---|---|
| `solexs_gaussian_SDD2_v1.rmf`, public tools 1.6 | 6,168,960 | EBOUNDS: 340 labels **1–340**, energy [keV]; MATRIX: 2,250 × 340, incident energy [keV]; creator pipeline-1.0 | UNKNOWN for sample indexing/version. |
| `solexs_arf_SDD2_v1.arf`, public tools 1.1 | 34,560 | 2,250 rows, incident energy [keV], area [cm2]; creator pipeline-1.0 | Grid/units exactly match candidate RMF; compatibility UNKNOWN. |
| `solexs_arf_pi_SDD2_v1.arf`, public tools 1.6 | 11,520 | 340 rows, energy [keV], area [cm2] | Grid/units exactly match candidate EBOUNDS; compatibility UNKNOWN. |
| `energy_bins_out_SDD2_v1.dat`, public tools 1.1 | 6,423 | 340 × 2 finite values; **no encoded unit** | Numerical proximity to EBOUNDS is insufficient to approve mapping. |

The standard ARF and text bounds are byte-identical to the inspected tools-1.6
tree resources. The RMF matrix has no nonfinite/negative cells. Structural/grid
agreement does not certify response accuracy. O §3.2.2 requires response channel
labels to correspond to spectrum channels; the **0-based PI / 1-based candidate
RMF discrepancy needs an official mapping or compatible file**. No automatic +1,
energy substitution, response normalization or flux conversion was applied. [O][O]

**LC:** the guide documents nominal 2–22 keV counts/s; the files encode no COUNTS
unit or band endpoints and `NUMBAND='4'` is undefined in the available guidance.
The diagnostic reproduces the legacy/current author-source strict energy-bound
selection and exclusive upper endpoint, on the unapproved text grid. [M][M],
[LC source][LC]

| Date | Finite rows | Tools hypothesis `[41:313]` differing rows | Upper-end control `[41:314]` differing rows | Maximum difference |
|---|---:|---:|---:|---:|
| July 1 | 86,272 | 19 | 14 | 1 native numerical unit |
| July 3 | 86,398 | 15 | 5 | 1 native numerical unit |

Neither hypothesis matches every row. Full 340-channel sums match **zero** finite
LC rows; maximum differences are 695/661. **UNKNOWN:** exact LC band-generation
policy, NUMBAND meaning and small residual cause. Close agreement is not a
validated reconstruction or an approved channel-energy calibration.

## 6. HK, correction state and quality

**DOCUMENTED:** the January guide says deadtime is not currently applied, hence
PI EXPOSURE equals TELAPSE. **OBSERVED:** both columns equal 1 on every sample
row, including all-NaN spectra; `DTCORR`, `GAINAPP`, `RESPFILE` and `ANCRFILE`
are absent. **INFERRED:** consistent with the guide's uncorrected-exposure
description. **UNKNOWN:** complete actual correction state/provenance of the
1.1 re-release; missing cards and constant exposure are not a certificate. [M][M]

**DOCUMENTED for newer workflow / OBSERVED in code:** the workshop supplies an
HK filename template; tools 1.3/1.6 use HK `FAST_COUNTS` and `SLOW_COUNTS` for
deadtime/exposure correction. Tools 1.6 additionally requires `DTCORR-MODE`;
it checks row counts but not timestamp correspondence. A pipeline-2.0-beta.1
workshop example does not establish availability/schema or backward compatibility
for July 2024 pipeline-1.1 HK. Matching HK is absent from the inspected repository
inputs. [W][W], [deadtime source][DT]

**OBSERVED:** two same-named `solexs_deadtime_params_SDD2_v1.fits` candidates
are 8,640 bytes each, with different hashes/schema/coefficients: tools 1.3 has
one deadtime column and offsets 364.438588/182.721482; tools 1.6 has separate
temporal/spectral columns and offsets 500/210. No coefficient column unit is
encoded. Public CALDB date-start 2024-01-01 with no end does not approve every
data/pipeline version. Content identity, mode, units and software/date compatibility
must all be established before correction.

Current band-flux code requires corrected input (`DTCORR`) and PI-grid area,
and replaces nonfinite channel flux with zero. That behavior requires explicit
gap-preservation validation before adoption. External source was inspected, not
executed; no coefficients, generated quality flags or systematic errors were
assigned to the native data. [LC][LC]
**OBSERVED in T16 source:** its spectral writer generates QUALITY for channel
labels ≤56 or ≥240, with comments placing the upper threshold near 15 keV.
This is tool policy, not an observed native flag or an approved pipeline-1.1
energy/quality filter. [Spectral writer][S]

**OBSERVED quality:** July 1 has 128 all-NaN PI rows / 43,520 NaN cells; July 3
has 2 / 680. Their masks exactly match LC NaNs. No partial-NaN spectra, infinities,
negative or finite fractional counts were found. Finite LC ranges are 3–1,554
and 2–943; PI cell ranges are 0–105 and 0–81. Native products contain no explicit
quality/saturation column. These observations do not certify healthy or unsaturated
acquisition: GTI criteria and HK/correction state still matter. Unusual finite
values were neither cleaned nor classified as erroneous.

## 7. July 2 availability

**OBSERVED locally:** July 2 is missing from the currently obtained collection.
**User-reported observation, not independently verified:** an authenticated PRADAN
SoLEXS catalogue search for 2024-07-02 returned “File not found”; the user could
not identify a product name, level, version, availability or size and did not find
matching HK/calibration through that search. The query time/parameters beyond
that transcription are not independently established.

**UNKNOWN — option C:** current evidence cannot distinguish an unacquired
applicable product from no applicable product. A search result does not prove
that observations never existed or that no suitable product can exist. Reason,
historical availability and exact applicable product remain unknown. Do not
interpolate the date or treat its absence as a negative scientific label. An
authoritative catalogue/support explanation could narrow this uncertainty.

## 8. Required PRADAN resources and acquisition plan

The [machine-readable prerequisite plan](../data/manifests/solexs_phase_e_requirements.json)
records **14 resources**, each with purpose, evidence, applicable versions/date
rules, local candidate/approval status, PRADAN/access scope and measured candidate
versus unknown official size. Unknown names remain null; explicitly classified
inferred candidates and workshop templates are retained as naming clues.

| Priority / requirement | What to obtain or establish | Why / present limit |
|---|---|---|
| Required evidence first | Pipeline-1.1 timing/bin/GTI/exposure and correction-state guidance or errata; exact resource name UNKNOWN | Manual/updates do not resolve contradictory cards or exposure semantics. |
| Required | Mission-approved SoLEXS tools + complete CALDB and release/compatibility instructions | Probed candidate name `solexs_tools-1.1.tar.gz` is INFERRED from the package pattern/release version; actual current catalogue name, payload/size and equivalence to author tags UNKNOWN. |
| Required if approved workflow uses HK | Matching SDD2 HK for July 1/3; workshop template `AL1_SOLEXS_YYYYMMDD_SDD2_L1.hk.gz` | Exact legacy files/schema/versions/sizes UNKNOWN; require row-time, detector, mode, unit, gap and correction-state compatibility. |
| Required for physical spectra | Compatible RMF + standard ARF + index/mapping and gain/energy provenance | Public candidates exist locally; channel discrepancy and mission applicability unresolved. |
| Required for observed deadtime workflow | Correct version of `solexs_deadtime_params_SDD2_v1.fits` plus selection/index rules | Same filename changed content; coefficients must match the approved workflow. |
| Conditional | `solexs_arf_pi_SDD2_v1.arf` for an approved PI-grid band-flux workflow | Candidate local; not a substitute for spectral RMF/ARF. |
| Conditional, exact names UNKNOWN | Additional gain/temperature, background/health/reference-correction resources | Acquire only what mission guidance requires; L1 PI is already described as energy-calibrated. |
| Conditional | July 2024 optimal SPK/CK + labels and appropriate clock/generic kernels | Only for a chosen observer/light-time reference policy; not automatically a UTC-repair prerequisite. |
| Conditional / optional | Small alternate validated sample, or date-specific SDD1 status explanation | Only if existing version cannot be validated, or SDD1 coverage is needed. |

**DOCUMENTED:** the manual places ARF/RMF in the tools CALDB and describes PRADAN
tools download. **OBSERVED:** anonymous requests to protected manual/tools/download
routes redirect to ISSDC login, not science bytes. Redirects establish access
gating, not that every requested filename currently exists. Authenticated browser
inspection was unavailable because computer-use permission was not granted.
No login, credentials or mission communications were attempted. [M][M]

**DOCUMENTED resource family:** PRADAN FAQ describes provisional current-month
daily SPK/CK and previous-month optimal monthly SPK/CK with XML labels, plus
clock/generic kernels. Exact July 2024 filenames, sizes and authenticated holdings
are UNKNOWN. [C][C]

All official expected download sizes remain **UNKNOWN** until an authenticated
inventory is provided. Measured public candidate sizes above are planning clues,
not verified PRADAN bundle sizes. First obtain the applicability/inventory evidence;
then pair a bounded pilot with approved correction/reference products. Do not
download a historical corpus to compensate for unresolved semantics.
Resource-selection/date-validity/content-identity metadata are required, but the
specific `caldb_index.json` file is conditional on the approved workflow: newer
tools use it, whereas tools 1.1 select response files directly. Equivalent official
selection guidance may satisfy that requirement. [T11][T11], [T16][T16]

## 9. Cross-instrument readiness

**DOCUMENTED:** NOAA's guide defines its epoch as 2000-01-01 12:00 UTC with
leap seconds neglected; this is not a TT/J2000 epoch. The local convention uses
the stated calendar interpretation, not elapsed SI seconds across leap insertions.
XRS-A/B bands are 0.05–0.4 / 0.1–0.8 nm, not the nominal SoLEXS LC band. [N][N]

**OBSERVED:** all three local GOES v2-2-1 avg1m NetCDF files encode that epoch,
record-start timestamps and PT1M resolution. The existing strict adapter preserves
raw flux [W/m2], flags, sample counts and AU factor, with separate channel-valid
masks and bin end=start+60 seconds. Fresh extraction exactly equals the saved
4,320-row frame over `[2024-07-01T00:00Z, 2024-07-04T00:00Z)`; XRS-A has
2,267 valid rows and XRS-B 4,318. The encoded AU factor is a multiplier for
conversion to 1 AU, not a correction already applied by `read_goes`.

**UNKNOWN readiness:** SoLEXS absolute clock/bin/exposure is not certified,
so matching nominal dates or plotting apparent peaks cannot justify a join.
Before alignment choose and validate both clock/bin conventions, interval overlap
and quality/missingness handling, response/band/quantity interpretation and an
observer/distance reference appropriate to the precision. GOES readiness does not
remove the SoLEXS gate.

**DOCUMENTED / INFERRED context:** [ISRO's mission description][I] places Aditya-L1
about 1.5 million km sunward of Earth. Distance/c gives an **order-five-second
estimate** of differential light travel, not an exact product shift. A common
observer/light-time policy and ephemerides may be needed for sub-minute physical
chronology; no fixed five-second correction, assumed reference position, full
temporal alignment, flare matching or dataset construction was performed.

## 10. Implementation and retained artifacts

- `scripts/probe_solexs_readiness.py` reuses the Phase C science API. Its small
  functions verify pinned input identities, inspect bounded uncompressed candidate
  FITS with Astropy, preserve units, compare exact native LC/PI coordinates in
  chunks, and emit deterministic metadata to stdout. No network or output-file
  mutation is part of this CLI. No accepted calibration/clock policy is returned.
- Floating count sums/differences refuse overflow before publication. Compressed
  response inputs cannot bypass the 16 MiB uncompressed FITS bound. Variable-length
  candidate tables are unsupported. Native science archive access remains owned by
  the unchanged Phase C loader, including source/member/payload lineage and cleanup.
- `tests/test_solexs_readiness_probe.py` contains 22 small synthetic cases:
  bounds, exact coordinates, NaN preservation, chunk independence, label/unit
  mismatches, source identity/size, compressed-input and arithmetic regressions,
  relocation and deterministic CLI output. Real raw products are not fixtures.
- Source pins, compact observed metadata and the acquisition specification are
  tracked under `data/manifests/`. Original documentation/calibration/science,
  temporary FITS, full generated reports and local verification scratch remain
  ignored. No package API, dependency, configuration, registration, GOES or UI change.

### Reproduce the retained scientific checks

From the repository/storage root, use the pinned environment and place the
identity-matching original documents/candidates at the ignored relative paths in
the two source manifests. These commands are offline and do not acquire inputs:

```bash
python -m pytest tests/test_solexs.py tests/test_solexs_readiness_probe.py -q
python -m pytest -q
python scripts/register_aditya.py --config configs/data/solexs_storage.json --verify
python scripts/validate_solexs.py --config configs/data/solexs_storage.json \
  --output results/solexs_timing_calibration/native_report.json
python scripts/probe_solexs_readiness.py \
  > results/solexs_timing_calibration/readiness_probe.json
```

The stdout redirection shown targets an ignored diagnostic report only; never
redirect a shell command to an original source. The existing validator constrains
its own output to `results/`. Detailed reports can be regenerated; the tracked
[observation manifest](../data/manifests/solexs_phase_d_observations.json) retains
compact findings, source artifact hashes and the probe revision, not large arrays.
FITS/GTI/native quantities remain available through the
[Phase C access contract](SOLEXS_SCIENCE_CONTRACT.md).

## 11. Verification and review

Fresh checks on the final scientific implementation:

| Check | Executed result |
|---|---|
| Targeted native-loader + probe tests | 85 passed, including 22 new probe cases. |
| Complete suite | 166 passed; one pre-existing NumPy/netCDF binary-size warning. |
| Normal installed imports outside checkout, no PYTHONPATH | Passed; installed SoLEXS/GOES bytes equal current source. |
| Seven script `--help` checks; local registration verification | Passed. |
| Actual two sample archives | Original sizes/hashes unchanged; ZIP CRC, gzip/FITS structure and 16 DATASUM checks pass; no CHECKSUM cards present. |
| Native and readiness summary repeat | Byte-identical metadata; hashes recorded below. |
| Source/dependency integrity | 36 pins and both supplied originals match; `pip check`: no broken requirements. |
| GOES regression | Six source identities, eight saved artifact hashes, exact fresh frame, numeric EDA/catalogue fields and six schema snapshots unchanged. |
| Data protection | Actual ignore checks plus index/all-reachable-history path/content scan: no prohibited payload; existing empty `.gitkeep` placeholders verified. |
| Portability/source preservation | No absolute machine paths or full science arrays in retained metadata; native loader/configuration/GOES/historical reports unchanged. |
| Git/review | `git diff --check` passes; independent whole-branch review completed and required findings resolved. Final feature-only publication/ref/status results are reported in the Git handoff. |

The independent review reproduced a compression-bound bypass and a floating
arithmetic overflow case. Both were reproduced in synthetic failing tests,
fixed, and reverified without changing sample results. Review is not a mission
scientific compatibility certification. Final verification records remain local
under `results/solexs_timing_calibration/`; only compact evidence is tracked.
The final scientific review also corrected an over-specific mandatory CALDB-index
requirement and clarified numerical units, candidate names and alternate-version
unknowns. No remaining required fix was identified. An independent relocated-root
run reproduced both actual sample reports byte-for-byte and the GOES frame exactly.

| Regenerable ignored report | Bytes | SHA-256 |
|---|---:|---|
| `native_report.json` | 100,275 | `70241bdde078c8e0986bb23117c6543a262fe1846bfd81e64d4b49380f43eb8a` |
| `readiness_probe.json` | 22,739 | `3df12394d6e9f4f4fe94b7adb787c9a8cb9af41bb460b7dbe21cd2436f4df174` |

## 12. Unresolved and untested questions

The gates are **UNKNOWN**, not implementation defects to bypass: exact 1.1
clock/date/MJD precedence and clock accuracy/leap behavior; LC bin and NUMBAND
semantics; continuous GTI/exposure convention; correction provenance; compatible
legacy HK schema/modes/clock and complete approved correction resources; response
channel indexing/date/software compatibility; applied gain provenance and any
additional physical calibration/quality/background requirements. SDD1's date-specific
absence cause and July 2's authoritative availability remain unknown.

No actual HK, corrected reference spectrum, authenticated tools bundle or
mission-certified response was available for end-to-end calibration. No authoritative
pipeline source was obtained. Alternate releases/layouts, integer-count diagnostic
inputs, variable-length/compressed calibration tables, other platforms/environments
and independently reproduced mission chronology remain untested or unsupported.
Successful structural FITS validation is not a full OGIP compliance certification.
The existing dependency warning persists despite passing numerical regressions.

## 13. Storage and memory implications

All values below are **OBSERVED measurements**, not nominal archive estimates.

| Quantity | Bytes |
|---|---:|
| Both ZIPs (July 1 / July 3 individually 6,036,792 / 6,216,112) | 12,252,904 |
| Sum of uncompressed ZIP members, still containing inner gzip | 17,869,082 |
| All eight fully expanded FITS payloads | 947,698,560 |
| One day's PI FITS / PI table | 472,443,840 / 472,435,200 |
| One day's LC FITS / table | 1,391,040 / 1,382,400 |
| Copied PI arrays for a 1,024-row chunk | 5,599,232 |
| Candidate RMF matrix array | 6,120,000 |
| Newly acquired small candidate RMF + PI-grid ARF | 6,180,480 |
| Three additional standard/NOAA reference PDFs | 4,674,171 |

One earlier measured native validation run took 7.28 s and peaked at 583,712,768
RSS bytes; the diagnostic probe took 7.18 s and peaked at 569,425,920 bytes,
measured by macOS `/usr/bin/time -l`. These are observed whole-process peaks,
not a guaranteed array-only memory bound or a portable performance benchmark.
The final repeat, with the two read-only CLI processes running concurrently,
measured 11.25 s / 565,592,064 RSS bytes for native validation and
10.60 s / 565,084,160 bytes for the probe; contention affects timing.
Memory mapping/chunks still touch substantial data. Budget one temporary
~472 MB PI payload, scientific-library/process memory and the 16 MiB gzip /
512 MiB expanded-product caps. No permanent bulk extraction was performed.

**INFERRED planning estimate only:** at exactly these two days' average sizes,
365 comparable days would be about 2.24 GB of ZIPs versus 173 GB fully expanded
FITS (decimal GB). This is not a forecast of available days, another release's
size or total corrected/HK storage. HK/bundle sizes and processed representation
budget are UNKNOWN. Retain immutable compressed sources, disposable bounded
scratch and regenerable versioned derived representations after policies pass.

## 14. Exact recommendation for Phase E

Do not begin historical acquisition yet. Obtain mission-applicable timing/bin/
GTI/exposure and correction guidance, authenticated tools/CALDB inventory and an
approved response/channel/gain compatibility chain. If the approved workflow
uses HK, obtain matching July 1/3 HK and appropriate correction coefficients,
then validate a bounded reference correction while preserving all source values,
missingness and immutable lineage. If 1.1 cannot be validated, propose a small
official alternate-version pilot for the user's decision.

The safe current representation is **native** LC coordinates/counts, PI
integration coordinates/counts/channel labels/TELAPSE/EXPOSURE, native GTIs,
encoded units including missing units, missingness diagnostics and original
metadata/provenance from the Phase C API. It supports scientific inspection;
it is not UTC-aligned physical flux or an ML training representation.

Only after the scientific gates pass should a subsequent dataset phase consume
a separately versioned representation with an evidenced UTC/bin policy,
quality/exposure/correction masks, approved calibration identities/units and
observer-reference convention alongside unchanged native lineage. A later
historical acquisition decision must select a bounded paired science/HK collection,
document catalogue gaps and budget measured storage. July 2 must remain missing
unless an actual applicable product is obtained. No future branch, dataset,
model, full alignment or frontend is started; Phase D main integration awaits
the user's separate authorization or user-managed PR.

**BLOCKED — pipeline-1.1 timing/bin/continuous-GTI/exposure policy, approved
correction/HK compatibility and response/channel/calibration applicability
remain unresolved.**

[M]: ../data/raw/aditya/documentation/pradan-official/SoLEXS-UserManual.pdf
[U]: ../data/raw/aditya/documentation/pradan-official/SoLEXS_Release_Updates.txt
[T11]: https://github.com/abhilash-sw/solexs_tools/tree/24693afeeab5f67ce0277fe84de059bbe54223cb
[T13]: https://github.com/abhilash-sw/solexs_tools/tree/a2db6a92da6399fb3abafc115a430e9be08ddce1
[T16]: https://github.com/abhilash-sw/solexs_tools/tree/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772
[W]: https://github.com/ISRO-ESA-Heliophysics-Workshop/hands-on-materials/tree/d7453029cfac574c0cf444ca47d2ce97fcc17245/aditya-l1/solexs
[P]: https://arxiv.org/html/2509.26292v2
[F]: https://fits.gsfc.nasa.gov/standard40/fits_standard40aa-le.pdf
[O]: https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/docs/memos/cal_gen_92_002/cal_gen_92_002.pdf
[N]: https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf
[C]: https://pradan1.issdc.gov.in/al1/faq.xhtml
[L]: https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds
[I]: https://www.isro.gov.in/Aditya_L1-MissionDetails.html
[LC]: https://github.com/abhilash-sw/solexs_tools/blob/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772/solexs_tools/genlc.py
[DT]: https://github.com/abhilash-sw/solexs_tools/blob/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772/solexs_tools/deadtime.py
[S]: https://github.com/abhilash-sw/solexs_tools/blob/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772/solexs_tools/genspec.py
