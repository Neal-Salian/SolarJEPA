# SoLEXS storage-foundation verification

Date: **2026-10-01**. Branch: `data/solexs-ingestion`.
Stable base: `278011ce27796781db873cd8d40578e1584e81d3` (`main`).
Registration foundation: `6b8eb17`; portable generated identifiers: `510f890`.
This is an approved local storage milestone, not scientific SoLEXS validation.
No downloads, member extraction, alignment, model training, merge or push occur.
[VALIDATION_REPORT.md](VALIDATION_REPORT.md) remains the historical checkpoint.

## Locally observed archive identities

Canonical directory: `data/raw/aditya/solexs/l1/v1.1/archives/2024/07/`.
The [tracked inventory](../data/manifests/aditya_inventory.json) contains the
full central-directory listing, declared CRCs, evidence categories and status.
Original ZIPs remain immutable ignored inputs; these two days are an initial
ingestion/validation sample, **not the final training dataset**.

| Original filename | Measured bytes | SHA-256 |
|---|---:|---|
| `AL1_SLX_L1_20240701_v1.1.zip` | 6,036,792 | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` |
| `AL1_SLX_L1_20240703_v1.1.zip` | 6,216,112 | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` |

Total ZIP bytes: **12,252,904**. Each ZIP lists seven entries: three directories
and four files. The observed member pattern for each nominal date is:

```text
AL1_SLX_L1_<YYYYMMDD>_v1.1/
  SDD2/AL1_SOLEXS_<YYYYMMDD>_SDD2_L1.gti.gz
  SDD2/AL1_SOLEXS_<YYYYMMDD>_SDD2_L1.lc.gz
  SDD2/AL1_SOLEXS_<YYYYMMDD>_SDD2_L1.pi.gz
  SDD1/AL1_SOLEXS_<YYYYMMDD>_SDD1_L1.gti.gz
```

ZIP-declared uncompressed member totals are 8,843,085 and 9,025,997 bytes.
Those members still include gzip payloads; **fully expanded science/FITS size
is unknown**. Only the ZIP central directory was inspected: no payload reads,
CRC verification, gzip decompression, FITS headers or numerical science checks.
The SDD labels/suffixes are observed strings, not validated detector semantics.

## Provenance and evidence boundary

- **DOCUMENTED:** the user reports official ISRO PRADAN/manual acquisition;
  mission/instrument identity and the collection's July 2 absence derive from
  that report. No portal authentication or independent source checksum was used.
- **OBSERVED:** local archive names, byte sizes, SHA-256, member declarations
  and UTC registration times (July 1 record: `2026-10-01T16:20:52.638321+00:00`;
  July 3 record: `2026-10-01T16:20:52.650274+00:00`).
- **INFERRED:** L1, v1.1 and nominal July 1/3 dates are parsed from filenames,
  not verified against mission headers or actual observation intervals.
- **UNKNOWN:** original acquisition UTC, header-verified detector and actual
  coverage are null. Units, cadence, GTI/quality, calibration, usable observations
  and source authenticity independent of the user's report remain unvalidated.

Both records have `processing_status: archived` and
`scientific_validation_status: not_validated`. July 2 is recorded solely as
`missing_from_obtained_collection`; no observation, interpolation or negative
label is generated. The schema currently covers the reviewed SoLEXS naming
convention; additional instruments/metadata require their own later adapters.

Registration and read-only re-verification were executed:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/register_aditya.py --config configs/data/solexs_storage.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/register_aditya.py --config configs/data/solexs_storage.json --verify
```

**VERIFIED:** two identities and one collection-gap record. Actual repeat
registration left the inventory byte-identical, including original timestamps.
Input mutation/conflicting identities fail before manifest replacement; partial
registration preserves other entries. Atomic replacement applies only to the
manifest. Concurrent writers are unsupported; commands must be serialized.

## Tests and installation

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pip install --no-deps .
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short
```

**VERIFIED:** full suite **66 passed**, with one existing NetCDF4
`numpy.ndarray size changed` RuntimeWarning (expected 16, got 96). `pip check`
reports no broken requirements. No configured lint tool exists; Python AST and
JSON parsing checks pass. No dependencies or machine-specific package config
were added/changed.

Tests cover actual hashing/byte sizes, canonical relative paths, registration/
repeat/partial registration, changed bytes and acquisition conflict, malformed
provenance/evidence, null unknowns, missing coverage consistency, unsafe member
paths, escaping symlinks, credential-bearing source URLs and case-insensitive
ZIP/FITS ignores in an explicitly case-sensitive Git fixture. They create tiny
artificial ZIP/NetCDF fixtures at runtime; no satellite fixtures are committed.
Two NOAA CLI regressions verify identical scientific Parquet bytes/frame and
portable metadata after moving a synthetic workspace, including legacy sidecar
handling without rewriting that sidecar.

`tests/test_cli.py` spawns normal installed imports and all five CLI `--help`
commands from outside the repository, with `PYTHONPATH` removed. These checks
are separate from pytest's `src` injection; the registration CLI also runs from
a relocated storage root in its functional test.

The initial normal-import/help tests failed five times with
`ModuleNotFoundError`. The editable `.pth` pointed to the correct `src` but
carried macOS `UF_HIDDEN`; Python 3.13 `site.addpackage` skips hidden `.pth` files.
Clearing the flag allowed a normal child import within that invocation, but
the flag returned across commands. **UNKNOWN:** which process reapplied it.
A normal non-editable package install removes reliance on that hidden path
hook; imports/help pass across later invocations without `PYTHONPATH`.
This is a **local environment repair**, not a dependency or configuration
refactor. Reinstall after package-source edits; the installed wheel is a snapshot.

## Existing GOES regression and artifact preservation

**VERIFIED:** six raw GOES files retain their pinned SHA-256 and sizes totaling
**1,002,585 bytes**. Fresh `read_goes` output matches all **4,320** saved Parquet
rows via `pandas.testing.assert_frame_equal`. Fresh scientific summary fields
and normalized event-catalogue summary equal the saved JSON. All **14** original
raw/Parquet/sidecar/schema/summary/PNG artifacts retain their pre-work bytes/hashes.
The processed Parquet SHA-256 remains
`cc197f8186e0ec15b8ababd5a8c5549349d10fd15112cf4320ca4f23c114c068`.

The check was read-only; original historical sidecars/results were not regenerated
or rewritten. The portable adjustment changes future source identifiers only,
not GOES numerical preparation. Reproduction of real PNG bytes was not tested;
their original identities were preserved. Historical availability text in saved
reference outputs describes their original pre-Aditya context.

Core read-only numerical comparison:

```python
import json
from pathlib import Path
import pandas as pd
from solar_flare_jepa.data.download import verified_manifest_paths
from solar_flare_jepa.data.goes import read_goes, read_event_records
from solar_flare_jepa.data.eda import summarize, summarize_events

root = Path.cwd()
manifest = root / "configs/data/noaa_sample.json"
flux = verified_manifest_paths(manifest, root, "avg1m")
events = verified_manifest_paths(manifest, root, "flsum")
frame = read_goes(flux)
pd.testing.assert_frame_equal(frame, pd.read_parquet("data/processed/noaa_reference.parquet"))
saved = json.loads(Path("results/noaa_reference/summary.json").read_text())
summary = summarize(frame)
assert {key: saved[key] for key in summary} == summary
assert saved["catalogue"] == json.loads(json.dumps(summarize_events(read_event_records(events)), default=str))
```

The original NOAA retrieval digest is also reproducible by removing only pinned
per-file `bytes`/`sha256` from the current config and serializing with indent 2
plus a final newline. It records the pre-pinning acquisition config, not new
acquisition. The receipt, pinned NOAA configs, dependency files and historical
validation report are unchanged.

## Git, paths and final branch review

Executed actual file checks:

```bash
git check-ignore -v data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240701_v1.1.zip
git check-ignore -v data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240703_v1.1.zip
git check-ignore -v data/interim/aditya/solexs/l1/v1.1/extracted/example/SDD2/raw.fits data/interim/aditya/solexs/l1/v1.1/extracted/example/SDD2/raw.FITS
git ls-files -- data/raw data/interim data/processed results
git diff --check
git diff 278011c HEAD --check
git status --short --branch
```

**VERIFIED:** actual ZIPs match `.gitignore:2:data/raw/**`; representative FITS
cache paths match `data/interim/**`. Outside those directories, `.ZIP`/`.FITS`
match the added case-insensitive suffix guards. Broad raw/interim/processed/
results/cache protections are retained. Index inspection finds only existing
root `.gitkeep` placeholders under generated-data directories. Neither archive
appears in the index or its path history. New commits contain text code/config/
tests/provenance/docs, no science data or archive/FITS binary signatures.
Credential/private-key/common-token signature scans find no matches; this is a
bounded scan, not a guarantee about every possible secret encoding.

Tracked inventory/config paths are repository-relative. Escaping paths/symlinks
fail, and relocated-root CLI tests pass. The `--root` workspace can be relocated;
individual outside-root data mounts are deliberately not implemented. Markdown
links/documentation consistency and the whole-branch review are checked before
the final stop; their final disposition is recorded below.

Independent whole-branch review: **pending** at the documentation checkpoint.
Integration is not authorized by any test/review result. `main` stays at the stable
base, and no commits are pushed.

## Not tested and next research gate

No independent clean environment, Linux/GPU platform, CRC/gzip payload integrity,
FITS/product semantics, real SoLEXS numerical validation, calibration, coverage,
alignment, dataset construction or model execution was tested. Concurrent
registration is not supported. The existing dependency warning remains unresolved.

Next, separately approve official-definition review and bounded scientific sample
validation: variables, actual cadence/clocks, GTI/quality, calibration requirements,
fully expanded size, useful coverage and GOES overlap. Use those findings plus
activity distribution, prediction windows, chronological partition strategy and
storage/compute estimates before approving a larger acquisition selection.
No download of all holdings, newer-year dataset role or automatic next milestone
is authorized. See [storage policy](DATA_STORAGE.md) and
[canonical status](PROJECT_STATUS.md).
