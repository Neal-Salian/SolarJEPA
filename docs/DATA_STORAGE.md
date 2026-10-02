# Data storage and local archive provenance

Established on `data/solexs-ingestion`, 2026-10-01. This milestone registers two
real SoLEXS ZIPs as an **initial ingestion/validation sample**, not the final
SolarJEPA training dataset. Phase C now adds a bounded native scientific inspection
layer; see [the scientific validation](SOLEXS_SCIENTIFIC_VALIDATION.md). Calibration,
absolute time conversion, GTI filtering, temporal alignment, model-ready datasets,
acquisition expansion and training remain gated. Historical storage validation
and the acquisition inventory remain unchanged.

## Storage layers

All paths below are repository-relative. Original filenames remain unchanged.
The existing GOES layout and reference configurations retain their locations.

| Location | Policy |
|---|---|
| `data/raw/noaa/` | Existing immutable, pinned GOES reference NetCDF files. |
| `data/raw/aditya/<instrument>/<level>/<version>/archives/<YYYY>/<MM>/` | Immutable original PRADAN ZIPs; year/month follow the nominal observation date. |
| `data/raw/aditya/documentation/` | Original mission manuals/product definitions, when obtained. |
| `data/raw/aditya/calibration/<instrument>/<calibration-id>/` | Original external calibration/response products, when obtained. |
| `data/interim/aditya/solexs/<level>/<version>/extracted/<archive-sha256>/` | Future regenerable unpacked raw-product cache, preserving archive hierarchy. |
| `.cache/aditya/solexs/` | Current unique temporary gzip/FITS staging; product scratch is removed on success/failure. |
| `data/interim/aditya/<instrument>/<processing-id>/` | Future intermediates; never confused with validated calibrated data. |
| `data/processed/aditya/<instrument>/<processing-id>/` | Future validated processed data, with calibration/QC lineage and masks. |
| `data/processed/aligned/solexs_goes/<alignment-id>/` | Future aligned products with explicit timing, masks and source identities. |
| `data/processed/datasets/<dataset-id>/` | Future model-ready features/windows/shards, tied to a frozen dataset manifest. |
| `data/manifests/aditya_inventory.json` | Tracked, small acquisition/identity inventory. |
| `data/manifests/datasets/<dataset-id>.json` | Future tracked derivation/source-selection records. |

Registration requires only the archive directory, inventory and current config.
Phase C creates disposable cache/report directories as needed. Create subsequent
processing/dataset directories when their stages actually begin. Instrument
names such as `solexs`, `aspex_steps` and `aspex_swis` preserve the documented
mission prefix; each future payload needs its own reviewed identity adapter.

## Current files and future placement

Place untouched current archives in:

```text
data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240701_v1.1.zip
data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240703_v1.1.zip
```

Future approved SoLEXS archives follow:

```text
data/raw/aditya/solexs/<level>/<version>/archives/<YYYY>/<MM>/<original-filename>
```

Normalize directory labels (`l1`, `v1.1`) while retaining the exact original
filename spelling from its directory entry. Case aliases cannot create a second
identity; inventory paths are unique under case folding for portability.
The current intake recognizes `AL1_SLX_L<level>_<YYYYMMDD>_v<version>.zip`;
this is a contract based on the acquired filenames, not a claim that every
future PRADAN product uses it. Other naming schemes require review. Dates in
filenames are nominal dates, not measured observation intervals.

Year/month/version partitions accommodate hundreds of daily archives without
moving GOES data. Registration selects explicit inputs, never a broad glob or
an automatic portal inventory. Extend or create an acquisition config only for
an approved selection; adding a config does not authorize downloading data.
Manifests contain logical paths, not drive names. `--root` supplies a relocated
repository/storage workspace; resolved paths must stay inside that root.
Escaping symlinks are rejected. An external disk can host that workspace;
individual outside-root mounts need a later explicit locator design.

## Registration and verification

Install the local package normally, using the documented pinned environment:

```bash
python -m pip install --no-deps .
python scripts/register_aditya.py --config configs/data/solexs_storage.json
python scripts/register_aditya.py --config configs/data/solexs_storage.json --verify
```

The registration CLI locates the repository from its script path by default,
so it also works from another current directory. Config paths resolve against
`--root`; an explicit absolute config path is accepted. Existing NOAA CLIs
continue to run from repository root. A normal installation is a source
snapshot: reinstall after package-source changes before exercising installed
CLIs. Unit tests' `src` injection is not installation verification.

Registration streams SHA-256 calculation, measures ZIP bytes, reads only its
central directory and atomically writes JSON. It performs no network access,
extraction, member decompression, FITS parsing or source mutation. `--verify`
rechecks all registered identities without writing provenance. Serialize
registration commands: concurrent inventory writers are not supported.

Repeat registration preserves original records and timestamps. Different
bytes/listings or conflicting source/acquisition facts raise an error before
replacing the inventory. Partial registration retains other registered files.
Malformed or inconsistent metadata, including duplicate JSON object keys at any
depth, also fails before write and is rejected by `--verify`. Member names must
retain their original decoded spelling; NULs, truncation and noncanonical dot/
repeated-slash paths are rejected before registering declarations. A changed product
must not replace an immutable source path: retain the old source and investigate
the archive revision before approving a distinct identity/location.

Supply `--acquired-utc` only when the original acquisition time is documented;
it applies to the selected batch. Otherwise it remains JSON `null`. Registration
time is measured independently in UTC. File modification times are never used
as acquisition evidence. A known acquisition time cannot be later than its
registration time; this relationship is checked on new and loaded records.
Correcting old provenance requires an explicit,
reviewed correction with evidence; repeat registration cannot silently enrich
or replace historical acquisition facts.

## Evidence and inventory schema

Schema version 1 records mission/instrument, filename, level, version, nominal
date, source portal, acquisition/registration times, bytes, SHA-256, relative
path, processing status, scientific-validation status and member declarations.
`metadata_evidence` distinguishes:

- **DOCUMENTED:** user-reported official PRADAN/manual acquisition and mission
  identity; the portal was not re-authenticated and no portal checksum was given.
- **OBSERVED:** local filenames, archive byte sizes/hashes, registration time,
  and central-directory member names, sizes and declared CRCs.
- **INFERRED:** nominal date, processing level and product version parsed from
  the archive filename; these are not FITS-header-verified fields.
- **UNKNOWN:** original acquisition time, header-verified detector identity,
  actual coverage/time scale, units, cadence, quality, calibration and usable
  observation volume. Unknown fields remain null or explicitly unvalidated.

Both archive listings expose directory labels `SDD1` and `SDD2`. Each lists
SDD2 `.gti.gz`, `.lc.gz`, `.pi.gz` and SDD1 `.gti.gz`. The registration record
treats these as observed names and asserts no detector/product semantics;
`detector` remains null. Scientific associations are recorded separately in the
Phase C findings and native inspection report.
Declared ZIP uncompressed sizes describe ZIP member bytes, which still include
gzip files. They are not fully decompressed FITS sizes. Registration records
deliberately retain their original scope: they do not assert payload/CRC/science
validity. Phase C separately verifies full members and records portable inspection
reports, without rewriting acquisition facts.

July 2 is recorded as `missing_from_obtained_collection`, based on the user's
report. This asserts neither portal-wide nor mission-wide unavailability and
creates no observation, interpolation or negative scientific label. Nominal
archive dates alone do not establish complete coverage on July 1 or July 3.
The fixed inventory schema requires the canonical collection-only gap statement;
contradictory or non-text prose is rejected rather than marked consistent.

## Extraction, derivation and Git policy

Retain original ZIPs independently of disposable caches and back them up
outside Git. The current native inspector never uses member names as extraction
paths and stages one bounded FITS payload in a unique temporary directory. A
future persistent extractor must preserve member hierarchy/bytes, reject
unsafe paths and links, enforce measured expansion limits, verify member
integrity, stage partial work separately and publish a cache only after success.
It must handle the observed nested gzip layer explicitly after format review.
Record parent archive hash, member identity and extraction/code version.
Do not permanently unpack every archive merely because it is available.

Calibrated/QC, aligned and model-ready products must be regenerable, separately
versioned by input/config/code/calibration identities and accompanied by units,
timing policies, masks and exclusions. Avoid duplicating complete tables merely
to apply QC; preserve validity information with the appropriate products.
Detailed generated schema snapshots/results and data sidecars stay ignored;
small portable provenance and scientific definitions belong in tracked manifests
and documentation. New NOAA metadata uses relative source identifiers; historical
sidecars are preserved, and new EDA reports normalize their source identifiers.
New EDA availability wording describes the GOES-only report scope, without
claiming that separately registered Aditya archives are absent.

Track code, tests, acquisition configs, filenames, versions, hashes, sizes,
credential-free sources, known dates, definitions and lineage. Ignore all raw
ZIP/FITS/gzip/science products, intermediates, processed/aligned/model-ready
data, caches and generated results. Existing directory ignores protect arbitrary
science extensions; case-insensitive ZIP/FITS extension guards add protection
outside those directories. Never bypass ignore rules with forced staging.

## Next scientific/acquisition gate

Before approving a larger selection, obtain official definitions/calibration and
validate actual variables, FITS/product semantics, cadence/clocks, GTI/quality,
response requirements, full expanded size, usable coverage, GOES overlap and
activity distribution. Then determine prediction windows, chronological
train/tune/calibration/test support and storage/compute budgets. Latest 2025/2026
observations and bulk acquisition remain undecided and outside this milestone.
See [foundation verification](SOLEXS_FOUNDATION_VALIDATION.md) and the
[canonical tracker](PROJECT_STATUS.md).
