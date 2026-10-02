# SoLEXS scientific validation — Phase C

2026-10-02, `data/solexs-science-validation`, base
`4ce0257ca02000fcd6e8207e30b8194440d4cee7`.
This validates the obtained samples and a native scientific access foundation.
It does not certify calibrated physical quantities, absolute chronology or a
training dataset. The broader Stage 1 remains gated. Final branch review and
the user's integration decision are separate from scientific findings.

## Evidence and starting state

**DOCUMENTED** means an authoritative definition; **OBSERVED** means direct file
or execution evidence; **INFERRED** means a derived interpretation; **UNKNOWN**
means insufficient evidence. Definitions do not overwrite missing FITS units or
resolve conflicting product metadata. Nominal dates and archive versions remain
filename-derived INFERENCE; acquisition time is UNKNOWN.

The [initial audit](SOLEXS_PHASE_C_RECONNAISSANCE.md#initial-audit) independently
verified clean synchronized main, AGENTS.md, history/branches, registration,
storage/config/inventory, existing code/scripts/dependencies, 80 tests and local
inputs/artifacts. It found generic FITS inspection VERIFIED, generic CDF support
IMPLEMENTED BUT UNVERIFIED on Aditya, nested instrument inspection PARTIALLY
IMPLEMENTED, science policies PLANNED/DOCUMENTED ONLY, the SoLEXS scientific
adapter MISSING, and clock/calibration applicability UNKNOWN. The feature branch
was absent and published before investigation. No existing science adapter was
reimplemented. Astropy 8.0.1 was already pinned and installed.

Historical storage/reconnaissance reports accurately describe earlier checkpoints
and are preserved. The old GOES generated report's sentence that Aditya files were
absent is historical; current code already restricts that statement to its GOES
report scope. Fresh numerical/catalogue results match, and the saved artifact is
byte unchanged. Current README/tracker/storage documentation reflects Phase C.

## Primary authorities and version reconciliation

The user supplied the official PRADAN originals. Their contents and hashes are
OBSERVED; portal acquisition is user-reported, without an independent portal
checksum. The [source manifest](../data/manifests/solexs_guidance_sources.json)
pins both originals and 25 small tool/calibration sources. Originals stay ignored.

| Authority | Defined or established scope |
|---|---|
| [URSC/ISRO Data Analysis Guide](../data/raw/aditya/documentation/pradan-official/SoLEXS-UserManual.pdf), v1.0, January 2025, 19 PDF pages | §2.1 product definitions; §2.2 Unix epoch; §2.3 omitted detector products; §2.4 responses; §4.5 limitations. PDF pages 5–6 correspond to printed pages 2–3. |
| [Official release/update notes](../data/raw/aditya/documentation/pradan-official/SoLEXS_Release_Updates.txt), updated June 9, 2026 | Jul–Sep 2024 changed from data 1.0/processing 1.0 to data 1.1/processing 1.1 on February 14, 2025, updating timestamps for UTC consistency. Processing 1.2 separately changed DATE-OBS/DATE-END and MJDREFI/MJDREFF on April 5, 2025. |
| [URSC instrument description](https://www.ursc.gov.in/SoLEXS.jsp) | Two silicon drift detectors, different aperture/dynamic-range roles. |
| Sarwade et al., [calibration/performance paper v2](https://arxiv.org/html/2509.26292v2), [published DOI](https://doi.org/10.1117/1.JATIS.11.4.045005) | Response, gain/effective area, deadtime/spurious counts and in-flight limitations. |

The [authority reconciliation](SOLEXS_PHASE_C_AUTHORITY.md) records primary
versioned code evidence without running it. Workshop examples have mixed
pipeline versions; they are not pipeline-1.1 authority. Tools 1.1, 1.3 and 1.6
have different correction logic. The same deadtime `v1` filename has different
bytes/schemas across releases. No correction package was installed or applied.

The guide explicitly defines Unix seconds from **1970-01-01 00:00:00 UTC**.
This is stronger evidence than the update note's UTC wording. However, some
guide numerical examples differ from that definition by 5.5 hours. The notes do
not specify numerical keyword repairs or precedence for old conflicting cards.
Those discrepancies are recorded; examples and legacy tool code cannot silently
authorize a product repair.

## Observed archive and product inventory

Both identities match the unchanged registration inventory and original files.
All ZIP member CRCs, eight complete gzip streams/FITS structures and 16 HDU
DATASUM values verify. CHECKSUM cards are absent in these science products;
absence is reported explicitly rather than called a successful CHECKSUM check.

| Archive | ZIP bytes | SHA-256 |
|---|---:|---|
| `AL1_SLX_L1_20240701_v1.1.zip` | 6,036,792 | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` |
| `AL1_SLX_L1_20240703_v1.1.zip` | 6,216,112 | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` |

Each ZIP contains three directories and four gzip members: SDD1 GTI, SDD2 GTI,
SDD2 LC and SDD2 PI. Every expanded product has Primary + one binary-table HDU.
Creators identify `solexs_pipeline-1.1`; there is no embedded HK, EBOUNDS, ARF,
RMF or response bundle. The absence is local, not mission-wide availability.

| Product / extension | Columns and native structure | Encoded column units |
|---|---|---|
| SDD1 GTI / GTI | START, STOP; zero rows; signed int16 (`I`) | Both absent |
| SDD2 GTI / GTI | START, STOP; float64 (`D`); 4 / 3 intervals | Both absent |
| SDD2 LC / RATE | TIME, COUNTS; float64; 86,400 rows per archive | Both absent |
| SDD2 PI / SPECTRUM | TSTART `D`, TELAPSE `D`, SPEC_NUM `J`, CHANNEL `340K`, COUNTS `340D`, EXPOSURE `D`; 86,400 × 340 vectors | `s` for TSTART/TELAPSE/EXPOSURE; others absent |

FILTER identifies SDD2 in LC/PI (OBSERVED). GTI detector association is INFERRED
from each member's identity; no FILTER card was found. PI declares CHANTYPE=PI,
DETCHANS=340, HDUCLAS3=COUNTS, HDUCLAS4=TYPE:II and POISSERR=false.

## Scientific meanings and safe interpretation

**DOCUMENTED detectors:** SDD1 and SDD2 are separate silicon drift detectors.
The larger approximately 7.1 mm² SDD1 aperture serves weaker emission; the smaller
approximately 0.1 mm² SDD2 serves higher intensity. They are not two assigned
energy bands. The guide explains omission of LC/PI when a detector has no valid
observations. That is consistent with these empty SDD1 GTIs (INFERRED); the
specific cause, including whether saturation occurred, is UNKNOWN. Empty GTIs
do not mean zero solar emission.

**DOCUMENTED GTI:** Sun within FOV, operational detector and recommended health
parameters define good intervals (§2.1.1). Actual thresholds and failure causes
are UNKNOWN here. OBSERVED inclusive numeric membership matches finite LC rows
exactly: 86,272 / 86,398 inside, zero finite outside and zero NaNs inside. This
supports an INFERRED sample-coordinate convention, not continuous bin exposure
or a general scientific filtering policy. Header EXPOSURE strings are
`86272.0` / `86398.0`; sums of STOP−START are only 86,268 / 86,395 native units.
The difference is visible; no endpoint choice or GTI filter is applied.

**DOCUMENTED LC:** the guide defines nominal 2–22 keV count-rate light curves at
one-second cadence (§2.1.2). OBSERVED RATE contains only TIME/COUNTS, no TUNIT,
exposure or quality columns, and NUMBAND=`4` without four band columns. The exact
band selection/NUMBAND meaning and its detector-chain relationship to PI are
UNKNOWN in these products. Preserve LC as a native instrument quantity; do not
assign flux units or derive calibrated flux from the name COUNTS.

**DOCUMENTED PI:** pulse-invariant, Type-II integration spectra (§2.1.3); TSTART
is integration start, TELAPSE duration, CHANNEL index and COUNTS per-channel
integration counts. Physical spectra require detector/version-compatible gain,
energy bounds and ARF/RMF. OBSERVED CHANNEL is constant **0–339**, whereas the
guide describes binning using **1–340** labels. Hardware PHA has 512 channels
reduced to 340 PI bins (§4.5.1). No channel renumbering or energy mapping occurs.

Every PI TELAPSE and EXPOSURE equals one, including missing rows; SPEC_NUM is
unique 1–86,400. The guide's initial-release note says deadtime exposure correction
is not applied; agreement suggests uncorrected exposure (INFERRED for these
samples), without certifying their complete correction history. All-channel PI
sums never equal LC at compared finite rows; maximum differences are 695 / 661.
These are native diagnostics, not a physical band comparison or an error label.

**DOCUMENTED calibration limits:** the guide requires ARF/RMF, warns about
response below 2.8 keV and resolution degradation at high rates, and recommends
systematic treatment for fitted spectra. The paper/current primary tools require
HK fast/slow-count and correction-mode inputs for current deadtime/spurious-count
handling. Matching HK, complete response and validated correction compatibility
are absent locally. Four small candidate calibration originals total 58,263
bytes; they do not establish applicability. No physical energy/flux conversion,
background subtraction, deadtime correction, spectral fit, uncertainty assignment
or numeric saturation mask is scientifically authorized by this validation.

## Time, coverage and quality

**OBSERVED LC clock cards:** TIMEUNIT=`s`, TIMEDEL=1, MJDREFI=40587,
MJDREFF=0.22916666651, TIMESYS=`UTC`, TIMEREF=`LOCAL`, TIMZERO=0 and no TIMEZERO.
DATE-OBS/END are 05:30:00 through the next day's 05:29:59. The nonzero reference
fraction corresponds to approximately 19,800 seconds. PI/GTI lack matching epoch
cards, though PI encodes seconds and SDD2 GTI envelope strings include `+00:00`.

Under the **explicit comparison assumption** of Unix UTC, numeric sample starts
map to nominal midnight and ends to 23:59:59. This agrees with the documented
epoch/release intent and GTI strings, but conflicts with LC date/reference cards.
The exact pipeline-1.1 precedence/repair rule remains UNKNOWN. No product UTC
coordinate has been accepted or generated. PI integration-start semantics are
DOCUMENTED; LC bin start/centre/end and continuous GTI endpoint exposure are UNKNOWN.

| OBSERVED measurement | July 1 nominal archive | July 3 nominal archive |
|---|---:|---:|
| First / last LC TIME = PI TSTART | 1719792000 / 1719878399 | 1719964800 / 1720051199 |
| Successive native steps | Exactly 1 throughout | Exactly 1 throughout |
| Duplicate / backward / irregular positive steps | 0 / 0 / 0 | 0 / 0 / 0 |
| LC finite / NaN rows | 86,272 / 128 | 86,398 / 2 |
| LC finite minimum / maximum | 3 / 1554 | 2 / 943 |
| PI NaNs / entirely missing rows | 43,520 / 128 | 680 / 2 |
| PI partial-NaN / infinite / negative / fractional finite values | All zero | All zero |
| PI finite count range | 0–105 | 0–81 |

LC missing row indices, inclusive and zero-based: July 1 `[5,130]`, `[23132,23132]`,
`[23138,23138]`; July 3 `[18033,18033]`, `[18039,18039]`. PI missingness matches
exactly. There are no missing timestamp rows inside either numeric grid; missing
measurements are present NaNs. July 2 is **missing from the currently obtained
collection**. Numeric separation is 86,401 between July 1's last and July 3's
first point; no observations are fabricated or interpolated across that gap.

GTIs and missingness provide quality evidence. No QUALITY, STAT_ERR, SYS_ERR,
housekeeping health, or saturation column is present in these Type-II/LC tables.
Portal quality categories in the guide are not obtained archive flags. Instrument
events/count jumps may be scientifically real; no automatic outlier cleaning was
performed. Completeness and finite counts do not establish calibrated suitability.

## Reusable access and downstream contract

[solexs.py](../src/solar_flare_jepa/data/solexs.py) extends the existing data
package; [the contract](SOLEXS_SCIENCE_CONTRACT.md) defines its scope. Reuse the
unchanged inventory/config and registration verifier. Open one explicitly
registered L1 member in a context; native LC/GTI arrays or PI chunks carry encoded
units (including null), clock cards, warnings, kind/detector/source provenance
and archive/gzip/FITS hashes. Returned arrays are readonly independent copies.
Do not retain mapped HDUs/views after closure or accumulate all spectral chunks.

Limits default to 16 MiB nested gzip, 512 MiB expanded FITS, 128 archive members
and 1,000,000 eager/summary time-coordinate rows. Unsupported names/layouts,
processing levels, variable-length columns, conflicting identities, dimensional
errors, corruption, changed source bytes and escaping paths fail. Missing cards
and unusual scientific values remain visible. Exact integer/mixed diagnostics
avoid wraparound/false equality; they do not alter native scientific arrays.

The **next dataset phase may consume** this native representation for further
inspection and source-preserving selection: separate detector/product quantities,
native timestamps, original NaNs, GTI endpoints, spectra/channel IDs/exposures,
units, warning states and immutable lineage. A presence mask may describe finite
native data, without being promoted to a complete calibrated quality mask.

Before constructing absolute time windows, GOES alignment, calibrated spectra or
physical targets, resolve the pipeline-1.1 clock-card precedence, LC bin position,
GTI endpoint/exposure/quality policy, LC band/count-chain meaning, response-channel
binding and correction state/compatible HK. Potential future inputs are matching
HK, authenticated ARF/RMF/energy/gain/deadtime products and mission guidance or
a reviewed revised product version. Additional substantial data acquisition,
dataset construction and modeling require the user's next decision.

## Measured storage and memory

| OBSERVED layer | Measurement |
|---|---:|
| Both original ZIPs | 12,252,904 bytes |
| Both ZIP-declared expanded members, still gzip | 17,869,082 bytes |
| All eight completely expanded FITS products | 947,698,560 bytes |
| One LC FITS / table | 1,391,040 / 1,382,400 bytes |
| One PI FITS / table | 472,443,840 / 472,435,200 bytes |
| One SDD2 GTI FITS / table | 8,640 / 64 or 48 bytes |
| One empty SDD1 GTI FITS / table | 5,760 / 0 bytes |
| All six copied PI columns at 1,024 rows | 5,599,232 bytes |

PI nested gzip bytes are 8,571,071 / 8,751,033; ZIP-compressed PI member bytes
are 5,791,399 / 5,968,476. One staged PI fits the 512 MiB cap and is removed before
the next product. Full sequential validation still faults mapped pages into RSS;
copied chunk size is not a process-memory guarantee. An initial implementation
peaked at 1,047,740,416 RSS bytes because Astropy preserved full columns on close.
A RED/GREEN lifetime regression and cached-column release fix reduced a measured
complete two-archive run to 556,580,864 bytes on macOS/Python 3.13; a final-core run
measured 582,664,192 bytes. These are observed runs, not deterministic memory
bounds. Measurements include imports, checksums, mapped pages and diagnostics,
not just arrays; runtime/machine variation is expected.

**ESTIMATES, not constructed representations:** the observed two-day average
projects to 612,645,200 ZIP bytes or 47,384,928,000 expanded FITS bytes for 100
similar days. They are not collection-wide distributions or acquisition advice.
Keeping the constant channel axis once with float64 counts and the four scalar
PI columns would occupy approximately 237,429,920 uncompressed bytes per day,
from measured dimensions/dtypes; compression, masks and container overhead are
excluded. No such processed dataset was built. Preserve compressed originals and
stage products sequentially until a later measured storage decision.

## Reproduction and verification record

Use the existing pinned environment and normally install the source snapshot;
raw samples and official originals remain local prerequisites. No network access
or bulk extraction is needed:

```bash
python -m pip install --no-deps .
python -m pytest tests/test_solexs.py tests/test_cli.py -q
python -m pytest -q
python -m pip check
python scripts/register_aditya.py --config configs/data/solexs_storage.json --verify
python scripts/validate_solexs.py --config configs/data/solexs_storage.json
python scripts/validate_solexs.py --config configs/data/solexs_storage.json --chunk-rows 256 --output results/solexs_science_validation/native_report_repeat.json
cmp results/solexs_science_validation/native_report.json results/solexs_science_validation/native_report_repeat.json
git diff --check
```

The offline CLI's `--root` supports relocation and runs outside the checkout with
no PYTHONPATH. Reports stay under ignored `results/`; raw/inventory outputs are
rejected, failed inspection preserves prior reports and atomic publication protects
source archives even if an old report path was hard-linked to them. The complete
portable metadata report is 100,275 bytes, SHA-256
`70241bdde078c8e0986bb23117c6543a262fe1846bfd81e64d4b49380f43eb8a`.
It includes full member/HDU/header/column inventories and compact native diagnostics,
without large arrays or local absolute paths. A repeat with 256-row chunks and
actual relocated copies of both ZIPs produced byte-identical reports. Independent
pre-implementation PI hashes/dimensions/counts/exposure/missingness comparisons pass.

Fresh targeted suite: **70 passed**; fresh full suite: **144 passed**, one existing
netCDF4/NumPy ABI RuntimeWarning;
dependency consistency passes, but the warning's cause remains unresolved.
Normal import and all six CLI help checks pass without source-path injection.
Both real samples pass complete integrity checks. Six pinned GOES sources, exact
prepared frame, numerical EDA/catalogue fields and six schema snapshots agree;
all eight saved artifacts are byte unchanged. Original official Downloads copies
and 27 source/calibration identities are unchanged. Actual raw/cache paths are
ignored and index/reachable-history scans contain no prohibited scientific data.
The final independent whole-branch review found no remaining Critical/Important
issue, separately confirming targeted tests, dependency consistency, source/report
identities and storage arithmetic. Reproduced review findings were fixed with
regression coverage for resource lifetime, identity/level checks, variable-length
arrays, exact native diagnostics and hard-linked report publication. The final
Git publication/ref checks follow the documentation commit; main integration
remains the user's decision. No independent OS/environment reproduction, GPU,
response application or unseen mission-product version has been validated.

## Answers to the sixteen scientific gates

| Question | Answer / evidence |
|---|---|
| 1. Actual format? | OBSERVED nested gzip-compressed FITS, Primary + binary table, all eight complete. |
| 2. SDD1/SDD2? | DOCUMENTED separate drift detectors/apertures/dynamic ranges; sample asymmetry OBSERVED, exact SDD1 loss cause UNKNOWN. |
| 3. GTI? | DOCUMENTED FOV/operation/health validity; OBSERVED endpoints/missingness; continuous endpoint rule UNKNOWN. |
| 4. LC? | DOCUMENTED nominal 2–22 keV count rate; OBSERVED TIME/COUNTS with no TUNIT; exact band/chain/NUMBAND UNKNOWN. |
| 5. PI? | DOCUMENTED pulse-invariant integration counts; OBSERVED 86,400 × 340, native indices 0–339, Type-II. |
| 6. Time/reference/cadence? | DOCUMENTED Unix UTC epoch and PI integration start; OBSERVED one-unit steps/conflicting LC cards; accepted repair/LC bins UNKNOWN. |
| 7. Coverage? | OBSERVED native ranges and NaN runs above; absolute observation boundaries remain gated. July 2 is a collection gap. |
| 8. Quantities/units? | Native instrument values preserved; PI time columns encode seconds. LC/GTI/PI-count TUNIT absent; physical flux/energy not assigned. |
| 9. Quality? | OBSERVED GTIs/NaNs/cadence/dimensions/integrity; no sample quality/error/saturation flags. Full scientific QC UNKNOWN. |
| 10. Calibration? | DOCUMENTED gain/energy/ARF/RMF and current HK/correction requirements; product-compatible complete inputs/state UNKNOWN. |
| 11. Safe directly? | Native values, encoded metadata, masks of presence and immutable lineage, with warnings and products kept distinct. |
| 12. Ambiguous/unusable? | Absolute chronology, LC bin/band interpretation, physical energy/flux/errors and correction/GTI filtering policies. |
| 13. Access? | Verified registered member context, bounded temp FITS, readonly native copies/chunks; UI-independent API and offline CLI. |
| 14. Storage/memory? | Measured gzip/ZIP/FITS/table/chunk/RSS above; sequential staging, no persistent raw decompression. |
| 15. Next representation? | NativeColumns plus original clock/unit/warning/kind/detector/source lineage, GTIs and unconverted Type-II chunks; not a training dataset. |
| 16. Important unknowns? | Clock precedence, LC bins/band/count-chain, GTI health/endpoints, calibration/HK compatibility, SDD1 cause and broader collection behavior. |
