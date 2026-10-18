# P2 GOES historical source assessment

Assessed 2026-10-08. Scope: the fixed July 2024 GOES-16 NOAA/NCEI science
one-minute flux selection. This is retrospective acquisition provenance, not a
forecast-skill finding or Phase E clearance.

## Selection and authoritative sources

**DOCUMENTED:** NOAA's [EXIS product page](https://www.ncei.noaa.gov/products/goes-r-extreme-ultraviolet-xray-irradiance)
identifies XRS one-minute averages as L2 NetCDF products and provides the science
archive and product documentation. The [July 2024 directory](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2024/07/)
listed 31 GOES-16 daily `sci_xrsf-l2-avg1m` files at version `2-2-1` when checked.
The acquisition selects the entire calendar month, July 1 through July 31,
before training or evaluation results. It does not select by flare activity or
quality outcomes. Other satellites, annual aggregates and flare-summary files
are outside this acquisition.

**DOCUMENTED:** The [NOAA XRS L2 ReadMe, 15 December 2025](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf)
describes a reprocessed science product with retrospective corrections and
updated calibrations. The `avg1m` product averages one-second measurements;
primary XRS-A and XRS-B fluxes are in physical W/m2. Version `2-2-1` adds
interpolation across one- and two-minute gaps, an interpolation flag and a
separate electron-correction flag. Such upstream interpolation must remain
visible and masked by the existing strict quality policy. No new interpolation
is authorized here. The ReadMe reports three-day science-archive latency; that
does not establish operational delivery of these reprocessed bytes in July 2024.

**DOCUMENTED:** The [NOAA XRS L2 User Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf),
section 2.4, defines the UTC reference epoch as 2000-01-01 12:00:00 with elapsed
seconds calculated without leap seconds. It is not the TT J2000 epoch. Section
4 describes native status and electron-correction flags. The historical adapter
must preserve and check these fields rather than infer missing scientific
semantics from filenames.

## Observed acquired inventory

**OBSERVED:** `data/manifests/goes_p2_july2024.json` contains 31 pinned flux
identities totaling **9,200,347 bytes**. Individual files range from 291,557 to
300,863 bytes. They are below the 1 MiB per-file and 31 MiB selected-output caps.
All 31 were reread for NetCDF/HDF5 magic, exact SHA-256 and byte size. Independent
NetCDF header inspection found each native `id` matching its original filename,
platform `g16`, and both primary flux units `W/m2`. Their `time` dimensions total
44,640 rows. Row presence alone does not establish valid observation coverage.

July 1–3 were copied from the existing pinned reference files to independent
inodes. Their lineage retains the original relative path, SHA-256, size and
prior `checked_utc`; their original acquisition time remains **UNKNOWN** (`null`),
since a check timestamp is not acquisition evidence. July 4–31 were downloaded
sequentially from the exact official URLs. New download completion and
registration times are measured separately in UTC. All six original NOAA files,
including the three flare-summary files, retain their prior pinned identities.
No existing reference manifest, loader or raw path was replaced.

## Contract, limits and reproducibility

The new config explicitly enumerates every nominal date and official URL. The
canonical raw directory is
`data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/07/`.
All serialized paths are relative to a supplied repository/storage root.
The manifest schema is version 1, with `platform`, `product`, `version`,
`selected_interval.start/end_exclusive/basis`, `config_path/config_sha256`,
`selected_file_count`, `max_total_bytes`, `complete`, `total_bytes`, and `files`.
Each file records `path`, `url`, `nominal_date`, `max_bytes`, `bytes`, `sha256`,
source identity, UTC provenance and lineage. The hashes are **OBSERVED local
identities**, not NOAA-issued checksums or a calibration-validation claim.

`acquire_history(config_path, root)` downloads only the enumerated flux files.
It checks all source/path identities and combined per-file caps before network
access, refuses redirects and symlink destinations, uses verified TLS, a
30-second timeout and at most three attempts, and removes temporary streams on
failure. Connection/eligible HTTP failures may retry; failed integrity checks
stop. The 31 MiB cap bounds selected output plus the current temporary file;
retry transfer volume can exceed output size, but attempts and per-attempt bytes
are bounded. Writers must be serialized.

Raw publication uses an atomic no-replace link from an independent temporary
file. Ledger updates use atomic JSON replacement after each verified identity.
A partial ledger retains completed pins; a resumed file must match its pinned
identity. Unknown existing files, changed configs, corrupt raw bytes and
inconsistent ledger identities fail without replacement. A crash between raw
publication and ledger publication can leave an orphan raw file: absent a config
pin, resume deliberately refuses adoption and requires investigation. Deleted
ledger-pinned files may be reacquired only with their original pinned bytes.
`verify_history(manifest_path, root)` accepts only a complete consistent pinned
inventory and returns selected one-minute flux paths without network or mutation.

Source execution used:

```bash
PYTHONPATH=src .venv/bin/python scripts/acquire_goes_history.py
PYTHONPATH=src .venv/bin/python scripts/acquire_goes_history.py --verify
```

These are source-workspace checks; normal installed-package CLI verification
belongs to the final P2 reinstall/verification. Offline tests use artificial
NetCDF magic payloads and replace only the HTTP boundary; they do not access
NOAA or assert scientific validity. The initial RED command
`.venv/bin/python -m pytest -q tests/test_goes_acquisition.py --tb=short`
produced 31 failures because the module was absent; the initial GREEN produced
31 passes. Two later RED cases exposed acceptance of a boolean schema version
and removal of an observed download time; both were fixed. The final acquisition
unit run produced 36 passes. The final acquisition/download/native-GOES
regression run produced 60 passes with the already-known netCDF/NumPy ABI
warning; final P2 verification covers the shared repository state.

**INFERRED benchmark assumption:** completed one-minute bins may be treated as
available at their end for a retrospective benchmark. **UNKNOWN:** real-time
operational availability and delivery latency for these exact revised bytes.
Scientific missingness, quality support, chronological windows and forecast
metrics require the separate P2 foundation validation. This acquisition creates
no event labels, uncertainty estimates, cross-instrument alignment or SoLEXS
calibration, and grants no Phase E permission.
