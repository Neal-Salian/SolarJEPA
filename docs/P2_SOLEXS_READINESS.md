# P2 SoLEXS native exploration and readiness

**BLOCKED_FOR_PHASE_E remains unchanged.** P2 provides verified offline native
diagnostics and source identities. It performs no SoLEXS training, physical flux
conversion, UTC conversion, GTI filtering, correction, cross-source alignment,
gap filling or new acquisition. The two real archives retain their role as an
initial ingestion/validation sample rather than a training dataset.

Evidence date: 2026-10-08 (Asia/Kolkata). This report distinguishes **OBSERVED**
file/execution evidence, **DOCUMENTED** authoritative definitions with their
applicability, **INFERRED** relationships and **UNKNOWN** unresolved semantics.
Runtime status is `OBSERVED_NATIVE`; candidate tasks and diagnostic plots are
`EXPERIMENTAL_UNCALIBRATED`. Neither status establishes scientific validation.

## Verified local inventory

The existing registration inventory is unchanged. P2 verified presence, actual
size, SHA-256 and central-directory identity, then reused
`inspect_solexs_archive` to read every ZIP member, verify CRC, nested gzip
integrity, FITS structure and every present FITS DATASUM/CHECKSUM card. These
real products contain DATASUM cards that verify; CHECKSUM cards are absent.
An absent checksum is not described as verified.

| Nominal filename date | Observed ZIP bytes | Observed SHA-256 |
|---|---:|---|
| 2024-07-01 | 6,036,792 | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` |
| 2024-07-03 | 6,216,112 | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` |

Paths remain under
`data/raw/aditya/solexs/l1/v1.1/archives/2024/07/`, with original
`AL1_SLX_L1_YYYYMMDD_v1.1.zip` basenames. Combined compressed size is
12,252,904 bytes. Filename dates and data-version labels are **INFERRED** from
names; they are not measured UTC coverage. Both FITS products identify creator
`solexs_pipeline-1.1` (**OBSERVED**). Original acquisition time remains
**UNKNOWN**; registration and filesystem timestamps are not substitutes.

Each archive has seven ZIP entries: three directories and four gzip/FITS
products. It contains SDD2 GTI/LC/PI and SDD1 GTI. There is no HK member and no
SDD1 LC or PI member in these inspected archives. This does not establish
mission-wide product availability or the cause of missing SDD1 sequences.

| Product per archive | July 1 rows | July 3 rows | Expanded FITS bytes |
|---|---:|---:|---:|
| SDD1 GTI | 0 | 0 | 5,760 each |
| SDD2 GTI | 4 | 3 | 8,640 each |
| SDD2 LC | 86,400 | 86,400 | 1,391,040 each |
| SDD2 Type-II PI | 86,400 | 86,400 | 472,443,840 each |

SDD2 LC/PI association is **OBSERVED** from FILTER cards. GTI association for
both detector labels is **INFERRED** from member names because the relevant
detector card is absent. The new common identity retains this per-product
evidence; it does not upgrade filename inference into observed detector metadata.
SDD1 has no native sequence available here, and its absence reason is **UNKNOWN**.

## Native quantities, timing and quality

**DOCUMENTED:** the pinned PRADAN manual v1.0 describes LC as nominal 2–22 keV
counts per second at one-second cadence, PI TSTART as integration start,
TELAPSE as integration duration, PI COUNTS as per-channel integration counts
and GTI criteria as Sun-in-FOV, operational and health conditions. The generic
manual defines Unix/UTC seconds; it predates the 1.1 re-release and cannot
resolve these exact files' conflicting cards. Applicability and source
identities are documented in [Phase C authority](SOLEXS_PHASE_C_AUTHORITY.md)
and [Phase D.1 evidence](SOLEXS_PHASE_D1_REPORT.md). P2 does not reinterpret
missing encoded units from those definitions.

**OBSERVED:** LC TIME/COUNTS column units are unset. LC header TIMEUNIT is `s`,
TIMEDEL=1, TIMESYS=UTC, TIMEREF=LOCAL, MJDREFI=40587,
MJDREFF=0.22916666651 and TIMZERO=0. TIMEPIXR is absent. LC DATE-OBS is
05:30:00 on the nominal date and DATE-END is 05:29:59 on the following date.
These cards are retained with `TIME_REFERENCE_CONFLICT` and
`LC_BIN_POSITION_UNKNOWN`; no epoch or date repair is applied.

| Native diagnostic | July 1 | July 3 |
|---|---:|---:|
| LC TIME and PI TSTART bounds | 1719792000–1719878399 | 1719964800–1720051199 |
| Coordinate increment | 1 native numeric unit | 1 native numeric unit |
| Duplicate/nonmonotonic coordinate counts | 0 / 0 | 0 / 0 |
| Finite LC COUNTS / NaN rows | 86,272 / 128 | 86,398 / 2 |
| Finite LC native COUNTS range | 3–1,554 | 2–943 |
| PI all-NaN / partially-NaN rows | 128 / 0 | 2 / 0 |
| Native PI channel labels | 0–339, constant axis | 0–339, constant axis |
| PI COUNTS NaN entries | 43,520 | 680 |
| Finite PI native COUNTS range | 0–105 | 0–81 |

All LC/PI native coordinate rows match exactly, and their missing-row masks
match. PI retains TSTART, TELAPSE, SPEC_NUM, CHANNEL, COUNTS and EXPOSURE;
TELAPSE/EXPOSURE are always 1 in the native columns, including missing spectra.
PI epoch/date cards are absent. No infinities, negative counts or fractional
finite counts were observed in the two real LC/PI products. These numeric
properties are diagnostics, not certified scientific quality rules.

**UNKNOWN:** accepted UTC chronology, LC bin position/completed-bin availability,
clock uncertainty, correction state, pipeline-applicable quantity semantics
and the actual LC band/channel relationship. Full-channel PI sums disagree
with LC at every finite row; maximum native absolute differences are 695/661.
This does not define a physical band or authorize response/channel mapping.

**OBSERVED:** SDD2 GTI endpoints are finite, ordered and nonoverlapping; no
encoded GTI time units are present. Sum(STOP−START) is 86,268/86,395 native
units, while GTI EXPOSURE header strings are 86,272/86,398. Inclusive native
point membership matches finite LC rows exactly: 0 finite rows outside and
0 NaN rows inside. **INFERRED:** endpoints may identify included integration
starts. **UNKNOWN:** the approved continuous bin/exposure/endpoint policy.
Point membership is reported only as a diagnostic; no GTI filter is applied.

July 2 remains locally absent from the obtained collection. The previously
user-reported PRADAN “File not found” query is attributed in the unchanged D.1
requirements. Global availability and the reason remain **UNKNOWN**. P2
creates no interpolation, observation, negative flare label or inferred gap fill.

## HK, calibration and gate

**OBSERVED in this execution:** no HK member appears in the selected ZIPs;
DTCORR, GAINAPP, RESPFILE and ANCRFILE cards are absent from native science
tables. A missing card or constant EXPOSURE cannot establish correction state.

[Phase D.1](SOLEXS_PHASE_D1_REPORT.md) retains the historical observation that
the supplied official tools-1.1 bundle contains SDD2 RMF, ARF and energy bounds
matching prior candidates. That bundle's local identity is established;
scientific applicability remains **UNKNOWN**. P2 does not execute those tools
or repeat their calibration inspection. Native PI labels 0–339 and the
previously observed response labels 1–340 still lack an approved mapping.
No +1 relabelling, response application, count-to-rate conversion, deadtime
correction or incident irradiance is produced.

The new config pins the unchanged D.1 requirements manifest:
`data/manifests/solexs_phase_d1_requirements.json`, SHA-256
`130913b5059895423799d36e265ce768271c060cc2b39f43221268e782da4872`.
Its gate is `BLOCKED_FOR_PHASE_E`. Unexpected gate state or changed pinned
identity fails closed. Required evidence remains the mission-applicable
pipeline-1.1 clock/bin/continuous GTI/exposure policy, approved correction
workflow/HK applicability, and approved response/indexing/gain/date/software
compatibility. No gate, archive, inventory or original loader is modified.

## Candidate tasks and disposition

These are future task definitions, with **no training or metrics executed**.
Every candidate remains `EXPERIMENTAL_UNCALIBRATED` and
`BLOCKED_FOR_PHASE_E`. None has both established scientific semantics and
permission to train on this validation sample.

| Candidate | Measured variable → proposed target | Timing, quality and assumptions | Evaluation after a separate approved contract | Current permission |
|---|---|---|---|---|
| Native LC forecasting | Native SDD2 COUNTS → future native COUNTS | Native TIME; bin completion/clock/quantity/correction UNKNOWN. Preserve NaNs; require approved GTI/exposure and causal chronology. | Masked native MAE/RMSE on detector-separated chronological holdout; units stay explicit. | Diagnostics only; training blocked. |
| Native PI forecasting | Native CHANNEL/COUNTS vectors → future unchanged-channel vectors | Native TSTART/TELAPSE/EXPOSURE; require stable channel/detector semantics, clock, exposure and correction policy. Preserve native missingness. | Masked per-channel native errors on chronological holdout; no flux skill claim. | Diagnostics only; training blocked. |
| PI masked reconstruction | Native COUNTS → artificially hidden channel entries | Artificial masks distinct from native missingness. Split independence and scientific representation must be established. | Held-out-channel native errors; cannot establish forecasting or physical spectra. | Training blocked even without UTC conversion. |
| Calibrated irradiance forecasting | Incident irradiance UNKNOWN → target undefined | Requires mission-approved correction/HK/response/indexing/gain and physical units plus completed-bin availability/quality. | Undefined until physical reference targets and uncertainties exist. | Conversion and training blocked. |
| SoLEXS–GOES alignment | Distinct count/irradiance observations → common target undefined | Clock/bin support, source-specific quality/calibration and any observer convention unresolved. Nominal dates cannot align rows. | Undefined until an approved alignment/target contract exists. | Alignment and training blocked. |
| Flare-event forecasting | No established event labels → onset/class target undefined | Native count peaks and finite masks are not flare labels; requires authoritative events and timing/quality. | Undefined; continuous diagnostics cannot establish classification skill. | Labels and training blocked. |

The common P2 identity carries mission, platform, instrument, ordered channels
and parallel native units (`UNKNOWN` for absent units), native time/sampling,
measurement type, quality, preprocessing, validation status and target definition.
Additional `column_units`, `native_details`, detector evidence and
archive/member/gzip/FITS provenance preserve the complete native distinctions.
Constructing the shared `SourceIdentity` succeeds; its training clearance
explicitly rejects SoLEXS. This metadata interface does not create P1 windows
or imply a shared numeric scale with GOES.

## Reproduction and verification

Install the current package normally, then choose a new output directory:

```bash
.venv/bin/python -m pip install --no-deps .
.venv/bin/python scripts/explore_solexs.py \
  --root /Users/nealsalian/Desktop/SolarJEPA \
  --config configs/data/p2_solexs_exploration.json \
  --output results/p2_solexs/native_reproduction
.venv/bin/python -m pytest tests/test_solexs_exploration.py -q
.venv/bin/python -m pytest tests/test_solexs.py tests/test_solexs_readiness_probe.py -q
```

`--root` supports relocated storage; paths in reports are root-relative.
The CLI runs from another working directory after normal installation.
Only new directories under `results/p2_solexs/` are accepted. Existing output
directories, escaping symlinks, changed archive identities and corrupt inputs
are refused; failure removes only that run's newly reserved directory.
UTC, calibrated-flux, GOES-aligned and count-rate requests are rejected;
`--train` is rejected with the blocked gate.

Defaults cap selection at four archives, 2,048 LC display rows, four spectra,
1,024 channel labels and 1,024-row spectral chunks. Existing native access
limits still cap gzip input, expanded FITS and eager rows. Plots select native
row indices without averaging, filtering or smoothing; selected LC points are
unconnected. Plot subsampling can omit missing rows or peaks, so full numeric
diagnostics in JSON supply missingness/coverage evidence. PNG labels explicitly
identify native coordinates/COUNTS, unknown UTC/energy mapping, no calibration,
nominal filename date and the bounded display subset.

**Executed checks:** initial RED was 21 missing-API/CLI failures; the shared
identity compatibility test also failed before its representation was corrected,
and runtime-source provenance failed before implementation. The final dedicated
suite passed **24 tests in 3.36 s**. The original native loader/readiness suites
passed **85 tests in 3.86 s**. A fresh combined run against the final source
passed **109 tests in 5.84 s**. Normal package installation, installed CLI help
and synthetic relocated-root CLI/no-overwrite execution passed. The primary
agent owns full P2 acceptance; these scoped checks do not claim it has run.

The final source runtime SHA-256 is
`1032aed054e1e8e44ab6569b47197fcc08105a3be7b4503e6c77ec570fb8f11b`;
installed and repository exploration bytes were explicitly compared and match.
The immutable first run `results/p2_solexs/20261008-native-01/` is retained as
an earlier installed snapshot; it precedes the final display-format adjustment.
The final run and plots are retained under
`results/p2_solexs/20261008-native-02/`; runtime source hashes and every PNG
hash are embedded in `report.json` (215,226 bytes; SHA-256
`bab3e6ce818e39e2c44dbbf20416a4c65bc066a45a9825f7a874863ffed98990`).
All four final PNGs were opened and visually inspected: complete labels,
unconnected LC points and native channel axes were verified. Direct installed
CLI attempts at `--train`, UTC conversion, calibrated-flux conversion and
reusing the existing output each returned exit 2; the existing report hash
remained unchanged. Original archive hashes are rechecked by
the API before publication. `.gitignore` was verified against actual raw ZIP
and generated report paths; both remain ignored, and `git diff --check` passed.

Untested/blocked: other SoLEXS dates/versions/layouts, HK schemas/availability,
mission-certified timing/correction/calibration, continuous exposure policy,
UTC alignment, science-grade sequence construction and any SoLEXS model fit.
