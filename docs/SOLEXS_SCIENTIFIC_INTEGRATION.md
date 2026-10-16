# Guarded SoLEXS scientific integration

Evidence date: **2026-10-16, Asia/Kolkata**. Scope: the two registered July
2024 L1/data-version-1.1 archives. This milestone advances native scientific-data
engineering independently of external email. It does not modify/retrain V1/V2,
replace checkpoints, reinterpret historical experiments or establish a new
physical forecasting result.

**Verdict: native preparation is supported; physical analysis and scientific
JEPA integration remain blocked.** Evidence identity, structural compatibility
and numerical usability are separate from scientific applicability.

## Verified checkpoint and preserved work

Fetched `main` was `1a4991da4dda9676caeb1d7e35a03408528c3188`, matching
the local ref. The latest verified SoLEXS checkpoint was
`research/solexs-provisional-sequence-modeling` at
`3baad2bc2f8cf926e2bf58b782528abc7c6e840d`, containing Phase E
`83b54435c1634f7de0a3ec6494439c023a4d0296`. The earlier ingestion, scientific
validation, timing/calibration and authoritative-evidence branches are in this
ancestry. `git log`/source inspection, rather than report titles alone, established
the existing implementation.

The new managed worktree/branch is `codex/solexs-scientific-integration`, created
from that checkpoint and published with upstream before implementation. Original
archives/documentation/calibration were copied into its ignored raw storage.
Existing loaders therefore create temporary scratch only in this new worktree.
The original presentation checkout, its untracked files and other worktrees
remain untouched. No PR or main integration is part of this milestone.

The previous loader already verifies ZIP identity/listing/CRC, gzip integrity,
FITS layout and present HDU checksums, and supplies bounded PI chunks. Previous
exploration and provisional sequence tools already exist. This milestone reuses
them where appropriate; it does not replace the FITS reader or rerun the pilot.

## Scientific evidence

**DOCUMENTED** means the identified source states the claim within its scope;
**OBSERVED** means direct file/execution evidence; **INFERRED** means a derivation;
**UNKNOWN** means not established. PRADAN acquisition is explicitly user-reported;
local hashes do not independently authenticate the portal or establish release
applicability.

| Topic | Evidence and consequence |
|---|---|
| Archive identity | **OBSERVED:** July 1 ZIP SHA-256 `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4`; July 3 `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf`. Both match the unchanged registration inventory. |
| Detector separation | **OBSERVED:** each archive contains SDD2 LC/PI/GTI and empty SDD1 GTI, with no SDD1 LC/PI or HK. LC/PI FILTER establishes SDD2; GTI association is **INFERRED** from member names. The cause of empty SDD1 GTIs and missing HK availability remains **UNKNOWN**. |
| Native chronology | **OBSERVED:** each LC and PI has 86,400 matching coordinates, incrementing by one native numerical unit. No UTC claim follows from this arithmetic. Filename dates remain nominal dates. |
| Absolute timing | **DOCUMENTED:** manual §2.2 defines Unix UTC seconds and §2.1.3 defines PI TSTART as integration start. **OBSERVED:** native first values are `1719792000`/`1719964800`; LC DATE-OBS says 05:30, while the documented Unix projection is 00:00. LC MJDREFF is `0.22916666651`; PI lacks epoch/reference cards. Precedence, bin availability, corrections and uncertainty are **UNKNOWN** for these bytes. No timestamp shift is applied. |
| Missingness | **OBSERVED:** July 1/3 LC has 128/2 NaNs; PI has the same all-NaN row mask and no partial-NaN rows. Finite values do not certify detector health, saturation, deadtime or scientific quality. |
| GTI endpoints | **OBSERVED:** closed point membership selects 86,272/86,398 native rows; half-open membership selects 86,268/86,395. The 4/3-point differences demonstrate endpoint sensitivity. These are alternative numerical hypotheses, never applied filters or seconds of exposure. |
| Exposure | **OBSERVED:** PI EXPOSURE and TELAPSE encode 1 s on every row, including missing spectra. **DOCUMENTED:** the dated manual describes exposure/deadtime concepts and says deadtime correction was then unapplied. Applicable upstream correction state and effective continuous live exposure remain **UNKNOWN**. |
| Response compatibility | **OBSERVED:** native PI CHANNEL is 0–339; candidate/official-package RMF EBOUNDS is 1–340 and F_CHAN begins at 1. RMF/legacy ARF creator is pipeline 1.0 while science says 1.1. No +1 relabeling, gain correction or response application is justified by equal dimensions alone. |
| Physical units | **DOCUMENTED:** manual §2.1.2 describes LC COUNTS as counts/s over nominal 2–22 keV; §2.1.3 describes PI channel counts during integration. **OBSERVED:** these science COUNTS columns have no encoded FITS unit. The interface retains null units and documents the manual separately. It does not silently assign counts/s, photon flux or W/m². |
| Calibration state | **DOCUMENTED:** the manual calls the delivered PI energy-resolved calibrated spectra. `local_transformations.calibration=False` means SolarJEPA applied no additional calibration; it is not evidence that the upstream pipeline performed none. Response/gain/correction applicability is still **UNKNOWN**. |

The official tools-1.1 TAR.GZ is 19,730,838 bytes, SHA-256
`348014aefa50ade556ec4a160a3cfe0b08095bde84b4650a27d6b5d3bf7fa2d3`.
All 45 outer member declarations and 35 regular-member hashes were rechecked
against D.1. Nested distributions were not installed or scientifically approved.
The existing C/D/D.1 source manifests supply 39 unique local documentation/tool/
calibration identities. Reverification proves local consistency, not calibration
selection authority. Same-basename deadtime resources with different hashes,
schemas and coefficients must remain distinct.

## Sources and applicability

- User-reported original PRADAN **SoLEXS User Manual**, v1.0, January 2025,
  363,311 bytes, SHA-256
  `d97c83618c85a0984e7dd0300ce5c16c4748ed5facde525949f902fe9f72abda`:
  §2.1 (PDF p5), §2.2 (p6), §2.4 (p7), §4.5 (pp17–19). The portal download
  endpoint is protected. The current authenticated manual was not retrieved.
- Pinned release updates, SHA-256
  `7fc0229985fef2bd60ab23bc554c09e64f526719f11825e44a60eed12f5396ce`:
  dated re-release/timestamp/reference-card changes do not specify an approved
  repair for these exact files.
- Original tools-1.1 `solexs_genlc.py` lines42–50 writes the fractional reference
  and uses local-time `datetime.fromtimestamp`; `solexs_genspec.py` lines163–166
  uses inclusive GTI point membership and lines204–229 preserves channel labels.
  These are **OBSERVED implementation details**, not permission to repair clocks
  or apply calibration. Original members remain pinned by D.1.
- [ISRO PRADAN payload overview](https://pradan.issdc.gov.in/al1/) documents the
  instrument and its nominal range. [Sarwade et al., versioned instrument paper](https://arxiv.org/html/2509.26292v2)
  discusses detector calibration, deadtime and comparisons (§§4–5). General
  instrument capabilities do not establish this July pipeline's applicability.
- [OGIP response specification](https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/docs/memos/cal_gen_92_002/cal_gen_92_002.html)
  provides response/channel conventions, not mission-specific indexing authority.

## Implemented native contract

`data/solexs_quality.py` derives immutable finite, NaN and positive/negative
infinity masks from captured values. Separate row flags describe negative,
zero/fractional entries, finite coordinates, exact requested numerical-step
breaks, and positive finite exposure/elapsed fields. No flag is called mission
validity, and no value is removed. The streaming interface carries the actual
previous coordinate across chunks, then resets at each product boundary.

`data/solexs_interface.py` returns detached `NativeBatch` snapshots. Native dtype,
endian, values, order, units, channel/counter identifiers, time cards, warnings
and full archive/member/FITS lineage survive closure of the loader context.
Fingerprints bind arrays, metadata, row origin and every derived diagnostic mask.
Direct PI snapshots must meet loader-equivalent structural identifier rules;
no channel-number convention is invented. GTI diagnostics retain both product
lineages and reject different source/detector associations, even for empty
streams. The audit refuses ambiguous GTI selection.

Only `representation='native'` is supported. `require_jepa_ready()` always raises
while this contract is in force. No `TimeSeriesDataset`, physical time axis,
normalization, training window, fitted model or new checkpoint is produced.

`data/solexs_integration.py` and `scripts/prepare_solexs_native.py` verify pinned
configuration/inventory/Phase E/source manifests, recheck original source
identities, run the existing native integrity inspector, and aggregate native
preparation diagnostics. JSON is parsed from the pinned snapshots, including
inventory consumption. Unknown/duplicate/changed gates and unsupported schemas
fail closed. Clean executed/installed source is attested using existing project
provenance machinery. Reports use existing atomic, exclusive artifact publication.
All arrays/scratch/results remain ignored; tracked artifacts contain only small
code, configuration, evidence summaries and identities.

## Frozen provisional experiments

**OBSERVED:** 26 pinned artifacts in the prior pilot, reproduction and supporting
audit collection were rehashed successfully, including its checkpoints and
predictions. No real-data training or pilot metric recomputation occurred. Prior scores retain
their original exploratory/numerical meaning and do not clear a scientific gate.

Review found two reasons to keep the pilot adapter separate: it casts to float64
(which can round integer values above 2**53 outside the frozen floating pilot's
domain), and directly constructed provisional sequences can supply a mask that
does not match their data. Those observations do not establish an error in the
pinned real pilot. The new native contract preserves dtypes and derives masks
from captured values. Historical source/results remain unchanged.

## Readiness gates and next milestone

| Gate | Retained disposition | Required evidence |
|---|---|---|
| E1 timing | BLOCKED_EXTERNAL_EVIDENCE | Applicable epoch/card precedence, clock uncertainty, bin support/completion and reference boundary rows. |
| E2 calibration | BLOCKED_EXTERNAL_EVIDENCE | Detector/pipeline/epoch applicability, native/response channel correspondence, gain/correction lineage and reference physical output. |
| E3 quality/exposure | BLOCKED_EXTERNAL_EVIDENCE | Approved GTI/bin arithmetic, effective exposure/deadtime/health rules and matching HK if required. |
| E4 detector/product selection | PARTIALLY_VERIFIED | SDD2-only product/task policy and approved LC band-generation semantics; no combined detector stream. |
| E5 GOES compatibility | PARTIALLY_VERIFIED | Response-aware quantity, band/observer conventions, independent source QC and validated clocks/bin support. |
| E6 forecasting | BLOCKED_EXTERNAL_EVIDENCE | Validated target/issue-time availability, scientific quantity/units/uncertainty and an approved experiment contract. |

The next milestone is **clock/bin and response/HK reference validation on one
explicitly selected release**: assemble applicable published documentation,
versioned official workflow and reproducible reference products; test clock
boundaries, channel correspondence and corrected exposure without training.
This work can use published evidence or an explicitly selected documented
release independently of email. Do not adopt a newer release or acquire bulk
science/HK implicitly. If evidence remains absent, retain UNKNOWN and the gates.
Only after these acceptance cases pass should a bounded SoLEXS/GOES comparison
or model integration be considered.

## Reproduction

Use a normal package installation with existing `[aditya,test]` dependencies.
The CLI requires a clean source tree and matching installed source. The data root
contains immutable raw inputs and the relative pinned manifests/config; it can
be relocated independently of the code worktree. Reports are exclusively created
under a fresh `results/experiments/<identity>/` directory.

```bash
python -m pip install --no-deps .
python -m pytest -q
python scripts/prepare_solexs_native.py --data-root "$SOLEXS_DATA_ROOT" \
  --output-dir results/experiments/solexs-native-new-audit
python scripts/probe_solexs_readiness.py --root "$SOLEXS_DATA_ROOT"
```

The native audit/probe perform no network call, original-archive mutation or
training. Package setup may fetch build tooling; the full test suite includes
small artificial CPU-training fixtures without retraining the real pilot.
Source hashes and the separate verification report delimit what was actually
executed on the real sample.
