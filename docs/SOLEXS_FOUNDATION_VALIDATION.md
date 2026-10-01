# SoLEXS storage-foundation verification

Date: **2026-10-01**. Branch: `data/solexs-ingestion`.
Stable base: `278011ce27796781db873cd8d40578e1584e81d3` (`main`).
Registration foundation: `6b8eb17`; portable generated identifiers: `510f890`.
The initial branch checkpoint was `7784d67`; the fresh pre-integration pass below
supersedes its final verification/review disposition. The remaining sections
preserve the initial checkpoint's evidence and limitations.
This is an approved local storage milestone, not scientific SoLEXS validation.
No downloads, member extraction, alignment, model training, merge or push occur.
[VALIDATION_REPORT.md](VALIDATION_REPORT.md) remains the historical checkpoint.

## Fresh pre-integration verification and corrections

The user requested an independent pass on exact HEAD
`7784d67f6679c8b2fce3c2631534b026deabedc1`. Verification derived correctness from
current source/tests/config, Git objects/history, manifests, actual file hashes
and executable behavior; documentation claims were not used as the verdict.

The fresh full suite passed **75 tests**, one existing NetCDF4 warning, but a
new independent review of `278011c..7784d67` found two genuine boundary issues:

- **Important:** acquisition UTC could be later than registration UTC. Parsing
  checked UTC syntax without comparing the two timestamps.
- **Minor:** a truthy missing-coverage statement could contradict the fixed
  collection-only schema or be a non-string value.

Five focused regression cases failed before correction and passed afterward.
The only implementation change compares parsed acquisition/registration times
and requires canonical `_missing` records. Real provenance records remain
byte-identical; no acquisition time or scientific field was added/invented.
The focused reviewer follow-up independently passed 12 checks, including earlier/
equal acquisition, new/partial rejection, loaded metadata, installed CLI failure
paths and preserved source/inventory bytes. No review findings remain unresolved.

Final corrected-source suite:

```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short
```

**80 passed, one existing RuntimeWarning**, 30.72 seconds. The local installed
package was refreshed with `pip install --no-deps .`; no dependency configuration
changed. Package/source identities and CLI checks are verified against the final
commit before stopping.

Additional independently executed evidence:

- Seven installed package files matched Git source byte-for-byte. Normal import,
  five CLI help commands and actual archive `--verify` worked from outside the
  repository with `PYTHONPATH` removed.
- Fresh SHA-256/size and ZIP central-directory comparisons matched both real
  records. Registration using local inputs and a copied inventory in a relocated
  temporary workspace was byte-idempotent; original records remained unchanged.
- Real NOAA preprocess/EDA CLIs ran in that temporary workspace. All **4,320**
  Parquet rows and Parquet bytes, numerical/catalogue summaries and all **four
  PNG bytes** matched saved outputs. Generated source identifiers were relative,
  with neither a host prefix nor the temporary root embedded in metadata.
- All **14** artifacts matched the measured pre-work hash baseline. All **16**
  original local inputs/artifacts (including the two ZIPs), plus the tracked
  inventory, retained their bytes during this fresh execution.
- Reachable Git-tree/path and blob scans found no raw science paths/products.
  All reachable blobs were UTF-8 text; ZIP/FITS/gzip/NetCDF/Parquet signature checks
  and common credential-signature checks found no matches. Actual ZIP/FITS ignore
  checks and branch/staged whitespace checks passed.
- Original GOES numerical code, pinned configs, retrieval receipt, dependency
  files and historical validation report remain byte-identical to stable `main`.

The fresh review deliberately leaves payload integrity/science semantics,
independent portal receipts/authenticity, concurrency/hostile filesystem races,
future extraction collisions/expansion controls, fresh environment/Linux/GPU
support, the hidden-flag origin and dependency warning unresolved as scope limits.
Filename-inferred dates are not used to assert acquisition-versus-observation
chronology. Independent historical artifact preservation relies on the measured
pre-work baseline; fresh regeneration independently checks current saved outputs.

No merge, push, PR, branch deletion or next milestone is authorized. The corrected
feature branch remains for the user's explicit integration decision.

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

**Initial checkpoint VERIFIED:** full suite **75 passed**, with one existing NetCDF4
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
and normalized event-catalogue summary equal the saved JSON, excluding the one
intentionally corrected descriptive availability statement. All **14** original
raw/Parquet/sidecar/schema/summary/PNG artifacts retain their pre-work bytes/hashes.
The processed Parquet SHA-256 remains
`cc197f8186e0ec15b8ababd5a8c5549349d10fd15112cf4320ca4f23c114c068`.

The check was read-only; original historical sidecars/results were not regenerated
or rewritten. Future source identifiers are portable; fresh EDA wording now
states that the report contains only GOES references rather than falsely claiming
SoLEXS files are absent. Neither adjustment changes GOES numerical preparation.
At the initial checkpoint, reproduction of real PNG bytes was not tested;
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
assert summary.pop("aditya_cross_instrument_alignment") == "not performed: this report contains GOES reference data only"
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

Initial independent whole-branch review inspected `278011c..3d96048` with fresh context
and no source/data mutation. No Critical issues; three Important provenance
defects and one Minor descriptive issue were identified. Each was reproduced
with a failing synthetic regression before a single branch-local fix pass:

| Finding | Correction and verification |
|---|---|
| Duplicate JSON keys could discard earlier records or acquisition facts. | Shared strict inventory loader rejects duplicate keys at every nesting depth in registration and verification; malformed source bytes remain unchanged. |
| Case aliases could register one physical archive twice or claim a nonexistent filename spelling. | Exact on-disk basename spelling and case-folded identity uniqueness; aliases cannot replace/create conflicting historical facts. |
| Normalized member paths and NUL truncation lost original identity. | Validate original decoded ZIP names; reject truncation, NULs, dot/repeated-slash aliases; equivalent checks apply to loaded member metadata. |
| Fresh EDA repeated obsolete absence text. | Regraded as Important factual metadata: use GOES-only scope wording, preserve saved outputs and all numerical/catalogue values. |

Nine new registration regressions failed before the fix and passed afterward;
the existing CLI portability test also failed on the obsolete report statement
before correction and passed afterward. Final suite: **75 passed, one known
warning**. The installed package was refreshed and matches current source.
No reviewer findings remained deferred as polish at that checkpoint. Its fixes were verified
by tests and preservation checks; no second independent review was performed.

The reviewer additionally tested failure after a later corrupt batch member,
coverage conflict and atomic replacement failure: original inventory bytes were
preserved, with temporary-file cleanup on replacement failure.

Workflow/review rulings and their practical limits:

| Decision | Reason and limit |
|---|---|
| Use the approved existing checkout on its feature branch. | Preserves ignored user data; no extra checkout isolation from concurrent edits. |
| Keep plan/ledger in ignored `.cache/solexs-foundation/`. | Avoids unrelated ignore changes; bookkeeping remains manual. |
| Preserve that ignored evidence workspace. | Retains pre-work hashes and local checks; a small local scratch directory remains. |
| Keep the branch and stop before integration. | Explicit user instruction overrides the finishing skill's default menu; integration stays pending. |
| Correct fresh EDA's factual scope statement. | Scientific reporting must not assert absent archives; one descriptive field intentionally differs from historical reports. |
| Defer payload/scientific suitability judgment. | Extraction/scientific work is outside authorization; unsuitable data may be discovered at the later gate. |
| Keep portal/acquisition evidence reported or unknown. | No independent portal receipt; local hashes establish identity, not independent authenticity. |
| Support serialized registration only. | No concurrency/hostile-filesystem contract; concurrent writers or input mutation invalidate that guarantee. |
| Leave fresh environment/Linux/hidden-flag-origin judgment open. | Local installed checks pass; untested environments and the recurring flag cause remain unresolved. |
| Defer extractor collision recovery/expansion limits. | No extractor exists; those safeguards must be implemented before future payload extraction. |

Integration is not authorized by any test/review result. `main` stays at the stable
base, no commits are pushed, and the clean feature branch is retained for review.

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
