# Phase C reconnaissance — scientific decision gate

2026-10-02; branch `data/solexs-science-validation`; base
`4ce0257ca02000fcd6e8207e30b8194440d4cee7`.
**Phase C is not complete. Scientific implementation stopped at the user's
scope-change gate before creating loaders or accepting transformation policies.**
This checkpoint records bounded read-only findings, not a validated dataset.
The original inventory and historical Phase A/B reports are unchanged.

## Initial audit

The checkout initially contained a clean `chore/agent-instructions` branch.
Fetching found the user-managed instructions PR merged at `origin/main` above;
local main was fast-forwarded from `6672671` to that already-published state.
Main and origin/main then matched, AGENTS.md existed on main, and the Phase C
branch existed neither locally nor remotely. The new branch was immediately
published with upstream tracking before payload investigation.

| Classification | Independently established starting state |
|---|---|
| VERIFIED | Immutable ZIP registration, canonical storage/provenance validation and read-only verification; both actual ZIP identities/listings match inventory. Existing suite: 80 passed. Installed package import and CLI checks pass. |
| VERIFIED | Generic standalone FITS metadata inspection, additionally exercised with synthetic primary/table HDUs and unit preservation. |
| IMPLEMENTED BUT UNVERIFIED | Generic CDF inspection exists; no actual Aditya CDF was validated in this phase. |
| PARTIALLY IMPLEMENTED | General science-file metadata infrastructure exists, but cannot access or interpret the nested SoLEXS gzip products. |
| PLANNED/DOCUMENTED ONLY | Instrument-aware clock, quality, calibration, alignment and dataset contracts in research/status documents. |
| MISSING | Reusable bounded SoLEXS science access/loading, validated GTI/LC/PI interpretation, response/HK products in the obtained collection. |
| UNKNOWN | Independently authenticated acquisition provenance, calibration applicability, accepted clock/GTI policy, scientific suitability for downstream targets. |

The current storage documentation accurately said member payloads had not been
validated. Earlier dated NOAA-only audit tables are historical evidence, not a
current assertion that no Aditya files exist. No previously implemented SoLEXS
science adapter was found. Astropy 8.0.1 is already installed and pinned; no new
dependency or UI architecture is needed for the proposed raw inspection layer.

## Sources and their applicability

Sources were accessed on 2026-10-02. Important claims below identify whether they
are DOCUMENTED, OBSERVED, INFERRED or UNKNOWN. A current guide does not establish
that its corrections apply unchanged to pipeline 1.1.

- **D1 — DOCUMENTED:** [URSC instrument description](https://www.ursc.gov.in/SoLEXS.jsp),
  updated 2026-06-22, payload configuration and capabilities. Two distinct silicon
  drift detectors use approximately 7.1 mm² (SDD1) and 0.1 mm² (SDD2) apertures;
  the former targets weaker emission and the latter stronger flares. Both are
  soft X-ray detectors, not a pair of independently defined energy bands.
- **D2 — DOCUMENTED:** Sarwade et al., [ground calibration and in-flight
  performance](https://arxiv.org/html/2509.26292v1), sections 4.4–4.5, 5.2–5.5 and
  Code and Data; published article DOI
  [10.1117/1.JATIS.11.4.045005](https://doi.org/10.1117/1.JATIS.11.4.045005).
  Instrument response, energy calibration, effective area and deadtime affect
  physical spectral/flux interpretation. The paper identifies a downloadable
  SoLEXS tools/calibration package; it is not proof of the correction state of
  these particular files. It also describes deferred SDD1 in-flight calibration
  during high solar activity, not a definitive cause for these empty GTIs.
- **D3 — DOCUMENTED:** instrument-team [L1 introduction notebook](https://github.com/ISRO-ESA-Heliophysics-Workshop/hands-on-materials/blob/d7453029cfac574c0cf444ca47d2ce97fcc17245/aditya-l1/solexs/SoLEXS_Workshop-Data-Introduction.ipynb)
  from the 2026 ISRO–ESA workshop. Its example names an L1 v1.1 archive path,
  converts LC numeric times with Python's UTC Unix conversion, and describes LC,
  Type-II spectra, GTI and housekeeping products. However, the stored LC/PI
  header outputs (cells 11 and 19) show `CREATOR=solexs_pipeline-2.0-beta.1`;
  that LC has `MJDREFF=0` and midnight dates. The path label does not establish
  pipeline-1.1 semantics or authenticate July's clock.
- **D4 — DOCUMENTED:** workshop [tools guide](https://github.com/ISRO-ESA-Heliophysics-Workshop/hands-on-materials/blob/d7453029cfac574c0cf444ca47d2ce97fcc17245/aditya-l1/solexs/SoLEXS_Tools_Guide.ipynb)
  at the same repository commit. It describes Unix times, L1 2–22 keV count-rate
  light curves, ARF/RMF calibration and housekeeping-based deadtime correction
  before flux or detailed spectral work. It references tools 1.3 and a v2.0
  example path, so version compatibility with these samples remains UNKNOWN.

The two original notebooks were obtained as small documentation artifacts only,
not executed, and remain ignored under `data/raw/aditya/documentation/isro-esa-2026/`.
Their source repository commit is `d7453029cfac574c0cf444ca47d2ce97fcc17245`.

| Original documentation file | Bytes | SHA-256 |
|---|---:|---|
| `SoLEXS_Workshop-Data-Introduction.ipynb` | 660,729 | `63900c3839a4e29776f820c96a9fc380641c966d0508f382fe2ee53e4d6c798d` |
| `SoLEXS_Tools_Guide.ipynb` | 1,797,753 | `5435872a84331ea039cb285e1519e8fa8a2642c35027a3d6401b207bf61400a6` |

The workshop links the [official manual](https://pradan1.issdc.gov.in/al1/protected/downloadFile/solexs/SoLEXS-UserManual.pdf).
The calibration paper links [tools 1.1](https://pradan1.issdc.gov.in/al1/protected/downloadFile/solexs/solexs_tools-1.1.tar.gz).
These official endpoints could not be retrieved anonymously; the tools endpoint
redirected to ISSDC authentication. They are **not** established globally
unavailable. No authentication bypass or substantial additional science
acquisition was attempted. A third-party manual mirror was located but was not
used as authoritative evidence.

## Observed identities, structures and quality

Both archive sizes/hashes and central directories match the unchanged registered
[inventory](../data/manifests/aditya_inventory.json), with ZIP CRC verification
now performed for every member. The following identities are OBSERVED:

| Archive | ZIP bytes | SHA-256 |
|---|---:|---|
| `AL1_SLX_L1_20240701_v1.1.zip` | 6,036,792 | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` |
| `AL1_SLX_L1_20240703_v1.1.zip` | 6,216,112 | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` |

Each ZIP has seven members: three directories and four gzip files. Each contains
SDD2 `.gti.gz`, `.lc.gz`, `.pi.gz` and SDD1 `.gti.gz`; neither contains HK, ARF,
RMF or an embedded calibration bundle. The fully inspected small members are
FITS, with a primary HDU and a binary-table extension. PI's initial primary and
SPECTRUM headers are FITS; its complete payload/HDU inventory is still unverified.
`CREATOR=solexs_pipeline-1.1` is observed. FITS/OGIP `HDUVERS` values are format
versions and must not be substituted for processing/calibration versions.

| Product | OBSERVED table structure | Established and unresolved meaning |
|---|---|---|
| SDD1 GTI, both days | `GTI`, zero rows; `START`, `STOP` are FITS `I` (16-bit integer); string `EXPOSURE='0.0'`. | Empty products, not zero-valued solar observations. Detector association is INFERRED from member and primary filename; no explicit detector card was found. Cause and general availability UNKNOWN. |
| SDD2 GTI | `GTI`; 4 rows July 1, 3 July 3; scalar double `START`, `STOP`, no column units or clock reference. | Good Time Interval role is DOCUMENTED by D3/D4. Exact generation criteria, endpoint convention and per-version filtering rules UNKNOWN. No observations were discarded. |
| SDD2 LC | `RATE`; 86,400 rows; scalar double `TIME`, `COUNTS`; no column units; `HDUCLAS3=COUNTS`, `TIMEUNIT=s`, `TIMEDEL=1`, `FILTER=SDD2`. | Instrument count quantity OBSERVED; count-rate and broad band described by D4. Exact sample band not encoded in energy-bound cards; `NUMBAND='4'` despite one COUNTS column. Bin start/centre/end, exposure and interpretation of NUMBAND UNKNOWN. |
| SDD2 PI | Initial `SPECTRUM` header declares 86,400 rows; `TSTART:D` [s], `TELAPSE:D` [s], `SPEC_NUM:J`, `CHANNEL:340K`, `COUNTS:340D`, `EXPOSURE:D` [s]. | `CHANTYPE=PI`, `HDUCLAS4=TYPE:II`, `HDUCLAS3=COUNTS`, `DETCHANS=340`, `FILTER=SDD2` OBSERVED. Full arrays, channel values, exposure, cadence and numerical integrity unverified. No EBOUNDS or response references in the inspected headers; subsequent HDUs UNKNOWN. |

LC numeric timestamps on each day are finite, strictly increasing, unique, and
have exactly 86,399 successive differences of 1. No missing timestamp rows were
found. Counts have 128 NaNs on July 1 and 2 on July 3; finite values range from
3–1,554 and 2–943 respectively, with no negatives, infinities or zeros.
These are observed diagnostics, not a validated saturation or cleaning rule.
No quality/error columns occur in the inspected LC/GTI tables. PI's inspected
column declarations likewise contain none; its numerical quality is UNKNOWN.

The SDD2 GTI string `EXPOSURE` values are `86272.0` and `86398.0`.
The sums of raw `STOP-START` are 86,268 and 86,395. Counting an endpoint-inclusive
unit-spaced coordinate grid instead yields 86,272 and 86,398, matching those
headers and LC finite-value counts. An inclusive *sample-coordinate* convention
is therefore INFERRED, not an established continuous exposure/bin-edge policy.
Pointwise GTI/NaN correspondence has not been checked. Units are not silently
assigned to GTI columns. All six small FITS products pass structural verification
and both HDU DATASUM checks; absence of CHECKSUM cards is not checksum failure.

July 2 is missing from the currently obtained collection. Nothing here establishes
portal-wide absence, continuous usable coverage, flare labels or a final dataset.

## Timing conflict — reason for stopping implementation

D3's mixed-version example and D4's time utilities document Unix/UTC
interpretation for their examples, not a verified pipeline-1.1 contract.
The actual pipeline-1.1 LC files include `MJDREFI=40587`,
`MJDREFF=0.22916666651`, `TIMESYS=UTC`, `TIMEREF=LOCAL`, and `TIMZERO=0`.
The fractional reference represents approximately 19,800 seconds (5.5 hours).
The header date strings also differ by 5.5 hours from a Unix interpretation:

| Sample | OBSERVED first / last TIME | Comparison under documented Unix convention | OBSERVED DATE-OBS / DATE-END |
|---|---|---|---|
| July 1 | `1719792000` / `1719878399` | `2024-07-01T00:00:00Z` / `2024-07-01T23:59:59Z` | `2024-07-01 05:30:00` / `2024-07-02 05:29:59` |
| July 3 | `1719964800` / `1720051199` | `2024-07-03T00:00:00Z` / `2024-07-03T23:59:59Z` | `2024-07-03 05:30:00` / `2024-07-04 05:29:59` |

The SDD2 GTI primary HDUs provide additional **OBSERVED** evidence: their string
`TSTART`/`TSTOP` cards explicitly include `+00:00`, from midnight to 23:59:59 on
each nominal date. For example, July 1's SDD2 GTI declares
`2024-07-01T00:00:00+00:00` / `2024-07-01T23:59:59+00:00`, whereas its LC date
cards show 05:30:00 to the following day's 05:29:59. The empty SDD1 GTIs instead
have blank `TSTART`/`TSTOP` string cards. SDD2's day-envelope strings alone do not
establish continuous good coverage. The relationship between these string cards
and the numeric GTI table clock remains unvalidated.

This is an example-convention versus observed-metadata discrepancy, with source
processing-version applicability unresolved, and a disagreement between date
metadata within the actual pipeline-1.1 products. The
comparison is **not an accepted timestamp conversion or measured UTC coverage**.
The numeric-coordinate span is observed; which UTC interpretation is correct
for these specific files remains UNKNOWN. PI and GTI omit equivalent epoch,
time-system and time-reference cards in their inspected headers. A timezone-related
pipeline defect is a possible INFERENCE, not an established cause. `TIMEREF=LOCAL`
is not used as authority for selecting a civil timezone. No clock, DATE card,
original file or registration fact has been altered.

## Calibration and downstream gate

D2 documents response/effective-area and deadtime requirements for physical
interpretation. D4's current correction workflow requires HK input, which these
archives do not provide. Local ARF/RMF/CALDB/HK availability is absent; broader
availability and compatibility with pipeline 1.1 are UNKNOWN. `POISSERR=False`
is observed in the PI header, so assigning square-root count errors is not
justified merely by the name COUNTS. Channel indices are not physical energies.
No counts-to-flux, channel-to-energy, deadtime, background, uncertainty, resampling
or GTI filtering transformation is implemented.

The current samples safely support preserving identifiable raw instrument
values/metadata and investigating their structure. They do **not yet support**
a validated absolute-UTC, calibrated-flux, physical-spectrum or exposure-aware
training representation. A subsequent dataset phase must not consume the
comparison timestamps or interpret NaNs as fabricated/interpolated observations.

The requested scope-change decision has seven parts:

1. **Discovery:** conflicting clock evidence within the products and an incomplete local correction
   bundle; both workshop notebooks contain differing processing/example versions.
2. **Evidence:** the LC reference/date cards versus D3/D4's Unix convention;
   absent HK/response members versus D2/D4's correction requirements.
3. **Scientific impact:** absolute coverage, bin timing, calibrated spectra and
   flux cannot be certified; GTI/exposure endpoint rules are also unresolved.
4. **Project impact:** keep Stage 1 blocked. A raw inspection layer can reuse
   the existing data package/Astropy, but its contract must expose these unknowns.
   No GOES or UI change is needed.
5. **Recommended solution:** obtain the official version-applicable manual/tools
   through the permitted route and resolve the clock discrepancy before accepting
   a time policy; establish whether HK or revised products are required for eventual
   calibrated use. This does not authorize bulk acquisition.
6. **Alternative:** explicitly continue Phase C as a raw instrument-space
   inspection/loading foundation, preserving numeric times, original cards,
   detector associations/evidence, units including nulls, LC NaNs, GTIs and PI
   dimensions; expose unresolved time/QC/calibration warnings. Keep UTC conversion,
   quality filtering, physical energies/flux and final dataset construction gated.
7. **Decision required:** choose the authority-first path or authorize the
   conservative raw-only contract despite the unresolved clock/correction issues.
   Neither choice starts dataset construction or another milestone.

## Storage evidence and validation limits

ZIP sizes total **12,252,904 bytes**. Declared ZIP member sizes total
**17,869,082 bytes**, still gzip payloads. Each completely inspected LC expands
to **1,391,040 bytes**, of which its table array has **1,382,400 bytes**. Each
SDD2 GTI expands to **8,640 bytes** and each empty SDD1 GTI to **5,760 bytes**.
These are measured decompressed sizes, not projections.

Each PI header declares `NAXIS1=5468`, `NAXIS2=86400`: **472,435,200 table bytes**,
with a minimum declared FITS extent of **472,443,840 bytes** including the two
inspected headers. These are **header-derived estimates**, not measured complete
PI sizes, verified array dimensions or process memory. The initial bounded July 1
probe exceeded its 128 MiB expansion limit and deleted its temporary file; full
PI decompression/integrity and peak RSS remain unverified. Later inspection should
budget scratch space and use bounded chunking/mapping before loading entire tables.
No collection-scale projection or additional science acquisition was performed.

The reproducible metadata artifact is the ignored
`results/solexs_science_validation/reconnaissance.json` (28,784 bytes; SHA-256
`5526ca38558a644ddfb8cf6c86f957d5f02738d16e16d694ad7286c9591adea1`). It contains
relative archive/member paths, small schemas/statistics and short GTI lists,
with no full time/count/channel arrays or host paths. The following bounded
checkpoint probe regenerates it. It is an investigation recipe for the verified
local samples, **not a production loader or general hostile-input safety API**.

Baseline checks actually executed: `git fetch origin`; main/ref/history/status
inspection; `.venv/bin/python -m pytest -q` (**80 passed**, one existing
NetCDF4/NumPy RuntimeWarning); `scripts/register_aditya.py --verify`; normal
installed import; synthetic FITS metadata check; `pip check` (no broken
requirements); actual ZIP/cache ignore checks and reachable-history binary/data
scan (73 UTF-8 blobs, no prohibited products). No new package source, dependency,
scientific unit test or CLI was added before the gate. TDD and an implementation
plan are deferred until a scientific contract can be accepted.

## Fresh checkpoint verification — not Phase C completion

- `.venv/bin/python -m pytest -q`: **80 passed**, one existing NetCDF4/NumPy
  RuntimeWarning, 29.34 seconds. These are existing tests, not validation of a
  new scientific loader. Source/tests/dependencies/CLIs remain unchanged.
- `.venv/bin/python -m pip check` and
  `.venv/bin/python scripts/register_aditya.py --verify`: pass. Normal installed
  core and Astropy imports also pass outside the repository with PYTHONPATH unset.
- Executed the exact fenced recipe below: source matches the local probe, repeat
  output is byte-identical, and execution from a relocated temporary storage root
  without PYTHONPATH produces identical bytes. No absolute paths are serialized.
- Fresh GOES regression with `verified_manifest_paths`, `read_goes`,
  `read_event_records`, `summarize` and `summarize_events`: all six pinned raw
  identities pass; 4,320-row output equals the saved Parquet exactly; numerical
  and serialized event summaries agree; all eight pre-work generated-artifact
  hashes are unchanged. The first event comparison used Timestamp objects against
  saved JSON strings; comparison through the existing JSON serialization convention
  passes. This required no pipeline change.
- Original SoLEXS ZIP hashes and inventory bytes are unchanged; original obtained
  documentation hashes still match. Actual raw/documentation/report/cache paths
  and a representative uppercase FITS cache path match existing ignores. No
  decompressed temporary payload is retained.
- The independent Superpowers requesting-code-review review reproduced the report
  byte for byte and checked primary sources, raw small products, hashes and ignore
  rules. Its source-version qualifier and GTI timestamp wording findings were
  verified and corrected before publication; no outstanding findings remain.
  It explicitly declined to certify absolute UTC, full PI integrity, calibration,
  usable coverage, training suitability or integration permission.

The initial scratch-file Astropy error was independently reproduced: a writing
file handle is incompatible with readonly FITS mode. Reopening that disposable
file with a read-only handle fixed the reconnaissance I/O. No original science
file was opened for writing. The 128 MiB PI cap stopped that separate expansion
probe as intended; the recipe below avoids full PI decompression entirely.

## Reproduce the bounded checkpoint

From repository root with the existing pinned environment and original registered
ZIPs, run `.venv/bin/python -m pip check` and
`.venv/bin/python scripts/register_aditya.py --verify`, then execute the Python
recipe below (for example, save it in the ignored `.cache/aditya/solexs/` directory).
The only write is the ignored metadata report; there is no extraction or network
access. It fully checks small products and deliberately reads only PI's first two
headers, leaving PI gzip/science integrity explicitly unverified.

```python
"""Bounded, read-only checkpoint probe for the two registered samples."""
import gzip
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from astropy.io import fits
from solar_flare_jepa.data.storage import load_inventory, verify_inventory


def header_only(stream):
    blocks = b''
    for _ in range(24):
        block = stream.read(2880)
        if len(block) != 2880:
            raise ValueError('Truncated FITS header')
        blocks += block
        if any(block[i:i + 8] == b'END     ' for i in range(0, 2880, 80)):
            return fits.Header.fromstring(blocks.decode('ascii')), len(blocks)
    raise ValueError('Checkpoint FITS header bound exceeded')


def metadata(header):
    return {c.keyword: c.value for c in header.cards
            if c.keyword not in {'', 'COMMENT', 'HISTORY'}}


def stats(values):
    values = np.asarray(values)
    finite = np.isfinite(values)
    good = values[finite]
    return dict(values=int(values.size), nan=int(np.isnan(values).sum()),
                infinity=int(np.isinf(values).sum()), negative=int((good < 0).sum()),
                zero=int((good == 0).sum()),
                minimum=float(good.min()) if good.size else None,
                maximum=float(good.max()) if good.size else None)


root = Path.cwd()
inventory = load_inventory(root / 'data/manifests/aditya_inventory.json')
verify_inventory(inventory, root)
report = dict(schema_version=1, status='phase_c_scope_gate_not_complete',
              interpretation='raw metadata and diagnostic statistics; no accepted UTC or quality policy',
              archives=[])
for record in inventory['files']:
    archive = dict(path=record['path'], bytes=record['bytes'], sha256=record['sha256'], products=[])
    with zipfile.ZipFile(root / record['path']) as z:
        assert z.testzip() is None
        archive['zip_crc_verified'] = True
        archive['member_count'] = len(z.infolist())
        for info in z.infolist():
            if info.is_dir():
                continue
            assert info.file_size <= 16 * 1024 * 1024
            product = dict(member=info.filename, zip_compressed_bytes=info.compress_size,
                           gzip_bytes=info.file_size, hdus=[])
            if info.filename.endswith('.pi.gz'):
                with z.open(info) as member, gzip.GzipFile(fileobj=member) as stream:
                    primary, primary_bytes = header_only(stream)
                    assert primary['NAXIS'] == 0
                    spectrum, spectrum_bytes = header_only(stream)
                product.update(payload_validation='initial_two_headers_only',
                               gzip_integrity_verified=False, full_hdu_count=None,
                               measured_expanded_bytes=None,
                               declared_table_bytes=spectrum['NAXIS1'] * spectrum['NAXIS2'],
                               minimum_declared_fits_bytes=primary_bytes + spectrum_bytes
                               + spectrum['NAXIS1'] * spectrum['NAXIS2'])
                product['hdus'] = [dict(header=metadata(h)) for h in [primary, spectrum]]
            else:
                with z.open(info) as member, gzip.GzipFile(fileobj=member) as stream:
                    payload = stream.read(2 * 1024 * 1024 + 1)
                assert len(payload) <= 2 * 1024 * 1024
                product.update(payload_validation='complete', gzip_integrity_verified=True,
                               measured_expanded_bytes=len(payload))
                with fits.open(io.BytesIO(payload), memmap=False) as hdus:
                    hdus.verify('exception')
                    product['full_hdu_count'] = len(hdus)
                    for hdu in hdus:
                        desc = dict(header=metadata(hdu.header),
                                    datasum_status=hdu.verify_datasum(),
                                    columns=[dict(name=c.name, format=c.format, unit=c.unit, dim=c.dim)
                                             for c in getattr(hdu, 'columns', [])])
                        if hdu.data is not None:
                            desc.update(shape=list(hdu.data.shape), array_bytes=hdu.data.nbytes,
                                        field_statistics={n: stats(hdu.data[n]) for n in hdu.columns.names})
                        product['hdus'].append(desc)
                    table = hdus[1]
                    if table.name == 'RATE':
                        time = table.data['TIME']
                        delta = np.diff(time)
                        steps, numbers = np.unique(delta, return_counts=True)
                        product['time_diagnostics'] = dict(first=float(time[0]), last=float(time[-1]),
                            duplicate_values=int(len(time) - len(np.unique(time))),
                            decreasing_steps=int((delta < 0).sum()),
                            step_distribution=[dict(step=float(s), occurrences=int(n))
                                               for s, n in zip(steps, numbers)])
                    elif table.name == 'GTI':
                        starts, stops = table.data['START'], table.data['STOP']
                        product['interval_diagnostics'] = dict(
                            intervals=[[float(a), float(b)] for a, b in zip(starts, stops)],
                            invalid_order=int((stops < starts).sum()),
                            sum_stop_minus_start=float((stops - starts).sum()),
                            endpoint_inclusive_unit_grid_count=float((stops - starts + 1).sum()))
            archive['products'].append(product)
    report['archives'].append(archive)
output = root / 'results/solexs_science_validation/reconnaissance.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print('Wrote results/solexs_science_validation/reconnaissance.json')
```
