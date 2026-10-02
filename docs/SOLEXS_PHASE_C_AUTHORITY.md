# Phase C authority follow-up — clock and correction gate

2026-10-02; `data/solexs-science-validation`; follows the
[read-only reconnaissance](SOLEXS_PHASE_C_RECONNAISSANCE.md).
The user selected the recommended authority-first path and subsequently supplied
the official PRADAN manual and release/update notes. This follow-up reconciles
those documents, versioned primary tool sources and complete sample products.
No timestamp/correction policy is applied. **Phase C implementation is in progress.**

## What the primary sources establish

The instrument-team workshop [tools guide](https://github.com/ISRO-ESA-Heliophysics-Workshop/hands-on-materials/blob/d7453029cfac574c0cf444ca47d2ce97fcc17245/aditya-l1/solexs/SoLEXS_Tools_Guide.ipynb)
links the public author-maintained `abhilash-sw/solexs_tools` repository. The
calibration paper identifies Abhilash R. Sarwade as its corresponding author at
URSC. These are primary tool sources, separate from the pipeline that generated the
obtained archives. Tools, pipeline and archive versions are separate identities.
The newly supplied official documents provide product definitions and release
lineage; they do not supply the exact pipeline source.

| DOCUMENTED tool version, verified from source | Immutable source commit | Relevance |
|---|---|---|
| 1.1 | `24693afeeab5f67ce0277fe84de059bbe54223cb` | Legacy Level-1 PI/GTI utilities and LC header writer. Commit dated January 30, 2025; public tag released October 25, 2025. |
| 1.3 | `a2db6a92da6399fb3abafc115a430e9be08ddce1` | January 2026 workshop release; introduces HK-based correction and flux prerequisites. |
| 1.6 | `51403b02fbb7ae2eb0b4eb539e881ffd56c1c772` | Repository HEAD observed on October 2, 2026; updated correction inputs and coefficients. Pin this commit, not the moving branch. |

The [source manifest](../data/manifests/solexs_guidance_sources.json) records
27 relative local paths, exact URLs, byte sizes and SHA-256 values. Original
sources remain ignored under `data/raw/aditya/documentation/solexs-tools-source/`;
four small calibration originals remain ignored under
`data/raw/aditya/calibration/solexs/`. No tool installation, external source
execution, calibration application or substantial science acquisition occurred.
The public pre-launch `solexs_pipeline_old3` repository is version 0.0.4 from
2021; it is not evidence for the obtained pipeline-1.1 implementation.

## Clock: stronger evidence, but product applicability still unresolved

- **DOCUMENTED:** legacy tools [time utilities](https://github.com/abhilash-sw/solexs_tools/blob/24693afeeab5f67ce0277fe84de059bbe54223cb/solexs_tools/time_utils.py)
  convert Unix seconds with an explicit UTC timezone. Its [spectral utility](https://github.com/abhilash-sw/solexs_tools/blob/24693afeeab5f67ce0277fe84de059bbe54223cb/solexs_tools/solexs_genspec.py)
  interprets the Level-1 PI `TSTART` coordinate using that utility and compares
  it directly to numeric GTI endpoints. This documents legacy *tool* behavior.
- **OBSERVED in primary source:** the legacy [LC writer](https://github.com/abhilash-sw/solexs_tools/blob/24693afeeab5f67ce0277fe84de059bbe54223cb/solexs_tools/solexs_genlc.py)
  assigns `MJDREFI=40587`, `MJDREFF=0.22916666651`, `TIMESYS=UTC`,
  `TIMEREF=LOCAL`, `TIMEUNIT=s` and `TIMZERO=0`. It generates date strings using
  `datetime.fromtimestamp` without an explicit timezone. Numeric input times
  are retained. The reference fraction and date behavior match the discrepancy
  observed in our LC products, but this writer identifies itself as tools,
  whereas our files identify their creator as pipeline-1.1.
- **DOCUMENTED correction in tools:** the [January 5, 2026 change](https://github.com/abhilash-sw/solexs_tools/commit/878e10c296e99ecd94c6645253b1d68e382f788a)
  actually changes the fraction to zero and generates dates using the UTC
  utility. The [1.3 writer](https://github.com/abhilash-sw/solexs_tools/blob/a2db6a92da6399fb3abafc115a430e9be08ddce1/solexs_tools/genlc.py)
  contains these changes; the evidence includes the code diff, not just its
  commit message. The 1.1 README's numerical UTC example is also inconsistent
  with its own conversion code and was later changed; prose/examples alone
  cannot certify the obtained clock.
- **INFERRED:** a similar timezone-dependent header-generation defect is a
  plausible explanation for the obtained LC cards. For each sample,
  interpreting the raw coordinate as Unix seconds and formatting it explicitly
  in Asia/Kolkata reproduces the LC date strings. This is a diagnostic comparison,
  not evidence of the actual processing host timezone or a validated conversion.
- **UNKNOWN:** whether pipeline-1.1 used the same writer; whether a mission
  correction notice authorizes treating its numeric LC/PI/GTI times as Unix UTC
  while disregarding the conflicting LC reference/date cards; timestamp bin
  LC bin start/centre/end and continuous GTI exposure conventions. No UTC coordinate or
  repaired FITS header has been produced.

The obtained LC files have creation-date cards `2025-01-29`, a temporal proximity
to the legacy sources, not proof of processing lineage. The SDD2 GTI envelope
strings explicitly carry `+00:00`; they support the Unix interpretation but do
not resolve its applicability independently. Absolute sample coverage remains
uncertified. The earlier comparison-only dates must not become alignment inputs.

## Correction guidance: compatibility needs explicit validation

| Evidence | Established requirement or observation | Limitation |
|---|---|---|
| DOCUMENTED, [tools 1.1 spectral preparation](https://github.com/abhilash-sw/solexs_tools/blob/24693afeeab5f67ce0277fe84de059bbe54223cb/solexs_tools/solexs_genspec.py) | Associates detector-specific ARF/RMF files with generated spectra and sums the input exposure column. | No retained deadtime module in this tag; its existence does not establish corrected input exposure or calibrated counts. |
| DOCUMENTED, [tools 1.3 correction](https://github.com/abhilash-sw/solexs_tools/blob/a2db6a92da6399fb3abafc115a430e9be08ddce1/solexs_tools/deadtime.py) | Uses HK `FAST_COUNTS`/`SLOW_COUNTS`, calibration offsets and rewrites PI `EXPOSURE`, marking `DTCORR`. | Matching HK is absent locally. This implementation differs from current correction logic. |
| DOCUMENTED, [tools 1.6 correction](https://github.com/abhilash-sw/solexs_tools/blob/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772/solexs_tools/deadtime.py) | Also requires HK `DTCORR-MODE`, inverts temporal deadtime, checks row counts and rejects already-corrected PI input. | This does not establish backwards compatibility or timestamp alignment for legacy HK; neither routine was run. |
| DOCUMENTED, [1.3 CALDB index](https://github.com/abhilash-sw/solexs_tools/blob/a2db6a92da6399fb3abafc115a430e9be08ddce1/solexs_tools/CALDB/caldb_index.json) | Lists SDD2 ARF, RMF, energy bounds and deadtime candidates from January 1, 2024, with no stop; SDD1 entries are null. | A date-valid candidate is not proof of pipeline/version compatibility. The index is unchanged at the inspected 1.6 commit. |
| OBSERVED, downloaded deadtime FITS | The same `solexs_deadtime_params_SDD2_v1.fits` filename has different bytes, schemas and offsets in 1.3 and 1.6. | Calibration identity must include bytes/source commit; a filename or `v1` label is insufficient. |
| DOCUMENTED, [current spectral preparation](https://github.com/abhilash-sw/solexs_tools/blob/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772/solexs_tools/genspec.py) | Generates spectral QUALITY using channel thresholds, including an upper-energy restriction near 15 keV. | This is generated tool policy, not an observed flag in the obtained PI tables or a verified mask for them. |

The current calibration paper [v2, sections 4.5 and 5.3–5.4](https://arxiv.org/html/2509.26292v2)
requires deadtime/spurious-count and response treatment for physical flux.
Applying an older routine merely because it accepts the filename would be
scientifically unjustified. The obtained archives contain neither HK nor
response files; downloaded candidate calibration alone does not remove this
block. Missing `DTCORR` cannot certify the actual input correction state. No
physical energies, flux, uncertainties or saturation mask have been assigned.

### Small calibration measurements (OBSERVED)

The four retrieved originals total **58,263 bytes**, within the authorized small
essential calibration/documentation investigation. All three FITS calibration
files pass Astropy structural verification; no full RMF was downloaded.

| Artifact | Measured structure | SHA-256 |
|---|---|---|
| Legacy energy-bound text, 6,423 bytes | 340 × 2 finite values; first pair 0.074341–0.121986, last 24.373322–24.468612; no encoded unit. Legacy genlc treats this candidate grid as keV. | `684f916612003706062d509ab805ae2cda763f99a83f85ce81028a94aea0949e` |
| Legacy ARF, 34,560 bytes | Primary + SPECRESP; 2,250 rows; ENERG_LO/ENERG_HI [keV], SPECRESP [cm2]. | `0f08199b3ef2f346979c58e0df83451fa23ae72a39fcaaa3d85bfe66b4b5bdc7` |
| 1.3 deadtime, 8,640 bytes | Primary + DT_COEFFS, one row, four columns; offset values 364.438588 and 182.721482; no column units. | `cdc51ad0dc8ca313cd8136ddb1fd7a8335d2b89d94a93f0c0721d841af62da8b` |
| 1.6 deadtime, 8,640 bytes | Primary + DT_COEFFS, one row, five columns; adds separate temporal/spectral parameters; offset values 500 and 210; no column units. | `445174f5ece890233690ec1a9faeba9c53f762117474d124aa3f706e24c205e1` |

The calibration values are inspection evidence, not a recommended conversion.
The energy-grid range is not the usable science band, and agreement with a
declared 340-channel PI width does not authenticate its channel mapping.

## Additional sample observation: GTI correspondence

Bounded rereading of the actual SDD2 LC/GTI products establishes an exact
**OBSERVED** pointwise correspondence when testing inclusive numeric endpoints:

| Nominal sample | LC rows | Inside inclusive GTI | LC NaNs | Finite outside / NaN inside |
|---|---:|---:|---:|---:|
| July 1 | 86,400 | 86,272 | 128 | 0 / 0 |
| July 3 | 86,400 | 86,398 | 2 | 0 / 0 |

The legacy spectral utility also uses inclusive GTI comparisons (DOCUMENTED
tool behavior). Together these support an INFERRED inclusive *sample-coordinate*
rule for these products. They do not define continuous interval duration, bin
edges, calibration state, or all validity criteria. No rows were removed or
filled. July 2 remains missing from the currently obtained collection.

## Official PRADAN documents and reconciliation

The user supplied both originals after downloading them from PRADAN. Local
contents and identities are OBSERVED; portal origin is attributed to the user,
with no independent portal checksum. Copies remain ignored and unmodified.

| Source | Observed identity | Applicability |
|---|---|---|
| [Data Analysis Guide](../data/raw/aditya/documentation/pradan-official/SoLEXS-UserManual.pdf), URSC/ISRO | Version 1.0, January 2025; 19 PDF pages; 363,311 bytes; SHA-256 `d97c83618c85a0984e7dd0300ce5c16c4748ed5facde525949f902fe9f72abda` | Explicit L1 definitions; document predates the 1.1 timestamp update. |
| [Release/update notes](../data/raw/aditya/documentation/pradan-official/SoLEXS_Release_Updates.txt) | Updated June 9, 2026; 2,481 bytes; SHA-256 `7fc0229985fef2bd60ab23bc554c09e64f526719f11825e44a60eed12f5396ce` | Specifically records Jul–Sep 2024 data 1.1 / processing 1.1, released February 14, 2025. |

**DOCUMENTED definitions:** guide §2.2 (PDF page 6 / printed page 3) defines
Unix seconds from January 1, 1970, 00:00:00 UTC. §2.1.2 defines LC as 2–22 keV
counts per second at one-second cadence. §2.1.3 defines PI TSTART as integration
start, TELAPSE as its one-second duration, CHANNEL as an index and COUNTS as
per-channel integration counts; its exposure note says deadtime is not applied
in that release. §2.1.1 defines GTI validity using Sun-in-FOV, detector operation
and instrument health. §2.3 explains LC/PI omission for detectors without valid
observations, consistent with empty SDD1 GTIs here; the specific physical cause
of those empty GTIs is still UNKNOWN.

The notes separately document processing-1.1 timestamp changes for UTC consistency
and processing-1.2 changes to DATE-OBS/DATE-END and MJDREFI/MJDREFF on April 5,
2025. They do not state exactly how to repair the reference cards in older files,
which keywords changed numerically, or LC/GTI endpoint conventions. The actual
files are pipeline-1.1 with January 29, 2025 creation-date cards. No earlier data
1.0 file was obtained for a before/after comparison.

The guide's explicit epoch is not the same evidence as the release note's UTC
wording. Some guide numerical examples are inconsistent with that epoch:
`1707715800` maps to 05:30 UTC, while §3.3 states 11:00; §4.4.2's numbers likewise
differ from its stated UT times by 5.5 hours. Explicit standard-library UTC
comparisons established these discrepancies. They are not silently adopted as
correct examples. The later product timestamp and reference-keyword changes are
DOCUMENTED; a shared timezone defect is INFERRED, not a proven pipeline cause.

**OBSERVED full PI reconciliation:** both complete FITS files contain exactly
Primary + SPECTRUM HDUs, each 472,443,840 bytes. All four PI HDU DATASUM checks
pass and full gzip/selected ZIP member integrity passes. Every PI TSTART equals
the same-row LC TIME and successive numeric differences are one. TELAPSE and
EXPOSURE are both exactly one for every row, including invalid rows; SPEC_NUM is
unique 1–86,400. Native CHANNEL is constant **0–339**, whereas the manual describes
its binning using 1–340 labels. This is a numbering distinction to preserve, not
permission to shift channels or bind a response without validation.

July 1 PI has 43,520 NaNs in 128 entirely missing spectra; July 3 has 680 in two.
There are no partial-NaN rows, infinities, negative or fractional finite counts.
Finite per-channel values range 0–105 and 0–81. The all-channel sum never equals
LC at a compared finite row; maximum absolute differences are 695 and 661. The
LC/PI detector-chain and band relationship is UNKNOWN for these actual products;
no band equivalence, scaling correction or error label is inferred from the sum.

The guide calls for ARF/RMF, warns about response below 2.8 keV and high-rate
resolution degradation, and describes Poisson/systematic errors for generated
Type-I spectra. Those statements do not provide an observed error column or a
verified numeric saturation/energy mask for these Type-II files. The exposure
equality agrees with the old uncorrected release description (INFERRED state
for these samples), but does not independently certify all correction history.
The newer HK/CALDB compatibility questions above remain unresolved.

## Scientific gate after official-document reconciliation

The documented epoch/product definitions and observed complete layouts justify
[lossless native inspection/loading](SOLEXS_SCIENCE_CONTRACT.md). The user directed
insufficiently established timing/GTI/calibration behavior to remain unresolved.
No implementation may silently choose between Unix definitions and conflicting
LC cards, repair headers, normalize physical units, filter GTIs or apply current
correction routines. Numeric times and all original metadata are retained.

Still UNKNOWN: LC bin start/centre/end; the authoritative precedence/repair policy
for pipeline-1.1 reference/date cards; continuous GTI duration/endpoints and exact
health thresholds; channel-response binding and correction/HK compatibility;
NUMBAND meaning and the actual LC/PI count relationship. Downstream absolute
chronology, alignment and calibrated physical spectra remain at this gate.
No communication to the instrument team, additional mission data, calibration
application, dataset construction or modeling occurred.

## Complete PI storage and memory observation

Two complete archives expand to 947,698,560 FITS bytes in total, measured by
sequential member access. Each PI table is 472,435,200 bytes. The first one-off
probe reached 1,013,874,688 process RSS bytes: it retained prior mapped-array
references across the second archive despite deleting temporary filenames.
This is a measured whole-process peak, not an intrinsic table-allocation estimate.
The retained API must scope views to product lifetimes and yield bounded copies;
memory mapping alone does not guarantee low RSS. No full science arrays were saved.

## Reproduction

Run the following from a relocated repository/storage root with the existing
pinned environment and the source originals listed in the manifest. It checks
identities, parses tool source as syntax only, opens bounded LC/GTI products and
small calibration files, and writes portable diagnostics to ignored results.
The recipe neither imports the tool sources nor applies corrections. No network
access is required once those originals are present.

```python
import ast
import gzip
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
from astropy.io import fits

root = Path.cwd()
manifest = json.loads((root / 'data/manifests/solexs_guidance_sources.json').read_text())
for source in manifest['sources']:
    payload = (root / source['path']).read_bytes()
    assert len(payload) == source['bytes']
    assert hashlib.sha256(payload).hexdigest() == source['sha256']

def writer_constants(commit, filename):
    path = root / 'data/raw/aditya/documentation/solexs-tools-source' / commit / 'solexs_tools' / filename
    tree = ast.parse(path.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'write_lc')
    cards = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    if target.slice.value in ['MJDREFI', 'MJDREFF', 'TIMESYS', 'TIMEREF', 'TIMEUNIT', 'TIMZERO']:
                        cards[target.slice.value] = node.value.value
    return cards

old = writer_constants(manifest['versions']['1.1'], 'solexs_genlc.py')
new = writer_constants(manifest['versions']['1.3'], 'genlc.py')
assert old['MJDREFF'] == 0.22916666651 and new['MJDREFF'] == 0
result = {'schema_version': 1, 'status': 'authority_gate_incomplete',
          'accepted_product_utc_policy': None, 'applied_corrections': [],
          'tool_writer_constants': {'1.1': old, '1.3': new},
          'source_identities': manifest['sources'], 'samples': [], 'calibration': []}
checkpoint = json.loads((root / 'results/solexs_science_validation/reconnaissance.json').read_text())
for archive in checkpoint['archives']:
    path = root / archive['path']
    assert path.stat().st_size == archive['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == archive['sha256']
    with zipfile.ZipFile(path) as z:
        def open_small(suffix):
            names = [n for n in z.namelist() if '/SDD2/' in n and n.endswith(suffix)]
            assert len(names) == 1 and z.getinfo(names[0]).file_size < 2_000_000
            with gzip.GzipFile(fileobj=io.BytesIO(z.read(names[0]))) as g:
                payload = g.read(2_000_001)
            assert len(payload) <= 2_000_000
            return fits.open(io.BytesIO(payload), memmap=False)
        with open_small('.lc.gz') as lc, open_small('.gti.gz') as gti:
            for product in [lc, gti]:
                product.verify('exception')
                assert all(h.verify_datasum() == 1 for h in product)
            t = lc['RATE'].data['TIME']
            counts = lc['RATE'].data['COUNTS']
            inside = np.zeros(len(t), dtype=bool)
            for start, stop in zip(gti['GTI'].data['START'], gti['GTI'].data['STOP']):
                inside |= (t >= start) & (t <= stop)
            assert np.array_equal(inside, np.isfinite(counts))
            compare = lambda x, tz: datetime.fromtimestamp(float(x), tz).isoformat()
            result['samples'].append({
                'archive': archive['path'], 'raw_time_first': float(t[0]), 'raw_time_last': float(t[-1]),
                'comparison_only_unix_utc': [compare(t[0], timezone.utc), compare(t[-1], timezone.utc)],
                'comparison_only_unix_kolkata': [compare(t[0], ZoneInfo('Asia/Kolkata')), compare(t[-1], ZoneInfo('Asia/Kolkata'))],
                'observed_lc_date_cards': [lc['RATE'].header['DATE-OBS'], lc['RATE'].header['DATE-END']],
                'lc_rows': len(t), 'inside_inclusive_gti': int(inside.sum()),
                'nan_rows': int(np.isnan(counts).sum()), 'pointwise_gti_equals_finite_lc': True})
for source in manifest['sources']:
    if '/calibration/' not in source['path']:
        continue
    path = root / source['path']
    entry = {'path': source['path'], 'sha256': source['sha256'], 'bytes': source['bytes']}
    if path.suffix == '.dat':
        data = np.loadtxt(path)
        entry.update({'shape': list(data.shape), 'finite': bool(np.isfinite(data).all()),
                      'first_pair': data[0].tolist(), 'last_pair': data[-1].tolist(), 'encoded_unit': None})
    else:
        with fits.open(path, memmap=False) as hdus:
            hdus.verify('exception')
            entry['hdus'] = [{'name': h.name, 'rows': h.header.get('NAXIS2'),
                              'columns': [{'name': c.name, 'format': c.format, 'unit': c.unit} for c in h.columns]
                              if hasattr(h, 'columns') else []} for h in hdus]
            if path.suffix == '.fits':
                entry['parameters'] = {c.name: float(hdus[1].data[c.name][0]) for c in hdus[1].columns}
    result['calibration'].append(entry)
output = root / 'results/solexs_science_validation/authority_followup.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
```

This is a bounded investigation recipe for the identified samples/source files,
not a general scientific loading API. Regenerate the earlier reconnaissance
artifact first if needed. Unknown clock/correction applicability is preserved in
the output, and the comparison timestamps are explicitly marked as diagnostic.
