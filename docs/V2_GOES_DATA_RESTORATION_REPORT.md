# SolarJEPA V2 GOES development data restoration report

Date: 2026-10-11. Branch `data/v2-goes-development-restoration`, based on
`feat/v2-training-protocol-feasibility` @ `ac3428f`. Companion documents:
[scientific validation](V2_GOES_SCIENTIFIC_VALIDATION.md), [M5 readiness](V2_GOES_M5_READINESS.md).
Machine-readable evidence:
- [`docs/evidence/v2_goes_development_integrity.json`](evidence/v2_goes_development_integrity.json)
- [`docs/evidence/v2_goes_restoration_runs.json`](evidence/v2_goes_restoration_runs.json)

Evidence labels: **OBSERVED** (executed on the restoring host in this milestone),
**DOCUMENTED** (stated by an earlier report), **INFERRED**, **UNKNOWN**. No model was trained,
nothing was scored, and no test window was built.

## 1. Required dataset (OBSERVED from tracked manifests and executable contracts)

The V1/V2 development experiment `configs/experiments/v1_goes_2024.json` loads exactly four manifests through
`foundation.goes_training` (`goes_historical_multi`). Their declared intervals must be contiguous.

| Manifest | Acquisition config | Interval (UTC, half-open) | Files | Pinned bytes | V1 role | Exposure |
|---|---|---|---|---|---|---|
| `data/manifests/goes_v1_202405.json` | `configs/data/v1_goes_202405.json` | 2024-05-01 → 06-01 | 31 | 9,169,020 | train | development / exposed |
| `data/manifests/goes_v1_202406.json` | `configs/data/v1_goes_202406.json` | 2024-06-01 → 07-01 | 30 | 8,910,715 | train | development / exposed |
| `data/manifests/goes_p2_july2024.json` | `configs/data/p2_goes_july2024.json` | 2024-07-01 → 08-01 | 31 | 9,200,347 | train to 07-22, validation 07-22 → 08-01 (P2 used 07-27 → 08-01 as its test) | development / exposed |
| `data/manifests/goes_v1_202408.json` | `configs/data/v1_goes_202408.json` | 2024-08-01 → 09-01 | 31 | 9,255,392 | test, **already scored in V1** | development / exposed |
| **Total** | | 2024-05-01 → 09-01 | **123** | **36,535,474** | | |

The **123-file count reported in M4A is confirmed**.

**Product identity** (identical for every file):

| Field | Value |
|---|---|
| Satellite | GOES-16 (native `platform = g16`, `instrument_id = FM1`) |
| Instrument | EXIS/XRS |
| Product | `xrsf-l2-avg1m_science`, Level 2 one-minute averages, version `v2-2-1` |
| Filename | `sci_xrsf-l2-avg1m_g16_dYYYYMMDD_v2-2-1.nc`, one file per UTC day |
| Local path | `data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/YYYY/MM/` (git-ignored) |
| Variables used | `xrsa_flux` and `xrsb_flux` (W/m²), the status flags `xrs?_flag`, sample counts `xrs?_num`, `electron_correction_flag`, `time` (seconds since 2000-01-01 12:00 UTC, record start, leap seconds neglected) |

**Pinning.** Each manifest pins every file's size and SHA-256 and passes its config-hash check
(`config_sha256` matches; OBSERVED). The pins are trust-on-first-use local hashes from the original 2026-10-08/09
acquisition, not NOAA-issued checksums.

**Lineage.** 120 rows record `download_official_noaa`. July 01–03 record `copy_pinned_reference`,
a copy of reference files that are not present here. Their pinned bytes are unchanged.

**Exposure.** August is labelled "untouched v1 test holdout" in its manifest `basis` text. That text predates the V1
scientific audit (F10), which found August scored in V1. The V2 protocol §3 and M0 decision D02 (VERIFIED)
classify **all of May–August 2024 as development/exposed**. No repository source assigns it a more restrictive role.
Restoration was therefore authorized for all four months as exposed development data. The historical manifest text
was not edited.

**Not required, not accessed:** the January 2025 external-validation selection and the 2025 flare-catalog manifest
named on other refs, the `data/raw/noaa/` reference files of `configs/data/noaa_sample.json`, and any SoLEXS data.

## 2. Pre-restoration inventory (OBSERVED)

The search covered the repository's own data locations (`data/`, `results/`, `.cache/`) for GOES files,
`.part`/`.tmp` partial downloads and caches. No unrestricted personal-directory scan was performed. M4A had already
recorded that no GOES copies existed in `~/Documents`, `~/Downloads` or `~/Desktop`.

| Category | Count |
|---|---|
| Present and verified | 0 |
| Present but unverified | 0 |
| Missing | **123** |
| Corrupt or mismatched | 0 |
| Partial downloads | 0 |
| Unexpected files | 0 |

Disk had 17,370,587,136 B free, against a requirement of 304,970,930 B (missing bytes plus a 256 MiB margin).

## 3. Restoration workflow

The existing bounded acquisition (`data/goes_acquisition.py`) was reused, not duplicated. It already provides:

- the official URL per file, TLS verification and no redirects
- a 1 MiB per-file cap and a `Content-Length` check
- at most 3 attempts per file
- a unique `.part` temporary file and pinned-hash verification **before** installation
- no-replace installation via a hard link
- a byte-stable ledger rewrite

New in this milestone:

| Component | Purpose |
|---|---|
| `configs/data/v2_goes_development_restoration.json` | Explicit authorization plan: only the four manifests, only GOES-16/`xrsf-l2-avg1m_science`/`2-2-1`, only nominal dates in [2024-05-01, 2024-09-01), role `development_exposed`, byte budget, disk margin, forbidden list with basis |
| `data/goes_restoration.py` | `load_plan` rejects any identity outside the plan (`UnauthorizedSelection`). Read-only `inventory`. `restore`: refuses mismatches before any network access, checks disk space, downloads only missing pins, asserts tracked manifests stay byte-identical, re-inventories. `compare_official_listing` |
| `goes_acquisition.acquire_history(..., stats=)` | Optional attempt/retry/byte/failure counters. Behaviour unchanged when omitted |
| `scripts/restore_goes_development.py` | CLI: read-only inventory by default, `--restore` to download. Reports go to `results/` (ignored, never overwritten) |
| `scripts/validate_goes_development.py` | Integrity, native identity, time-series and pipeline evidence (read-only). `--official-listing` compares with NOAA directory listings |

Reproduce on another host:

```bash
PYTHONPATH=src .venv/bin/python scripts/restore_goes_development.py --restore
PYTHONPATH=src .venv/bin/python scripts/validate_goes_development.py --official-listing --out results/v2_goes/integrity.json
```

## 4. Restoration results (OBSERVED)

| Run | Network attempts | Retries | Downloaded | Result | Wall time |
|---|---|---|---|---|---|
| Inventory (read-only) | 0 | 0 | 0 | 123 missing | 0.02 s |
| Restore | 123 | 0 | 123 files, **36,535,474 B** | 123 present_verified | 420.7 s (`/usr/bin/time`: 420.78 s real, 70.96 MB max RSS) |
| Restore again (idempotence) | 0 | 0 | 0 | 123 present_verified, no file rewritten | 0.11 s |
| Restore with the committed code | 0 | 0 | 0 | 123 present_verified | 0.13 s |

- **Failed downloads:** none.
- **Partial or unexpected files afterwards:** none.
- **Tracked manifests:** byte-identical (no `git diff`).
- **Raw files:** git-ignored by `data/raw/**` (`git check-ignore` confirmed). 38 MB on disk.
- **Independent check:** the original verifier `scripts/acquire_goes_history.py --verify` reports `VERIFIED_RAW_IDENTITIES`
  for all four manifests (31/30/31/31).

## 5. Integrity verification

Two separate claims are made.

**Manifest verification (OBSERVED, 123/123).** Each file's name, size and SHA-256 equal the repository pin.
Each was checked at download before installation, again by `inventory`, and again by `verify_history` inside the validator. The
per-file hashes are listed in the integrity evidence (`files[].sha256`).

**Authoritative provenance (OBSERVED, 123/123).**
- **Source.** The bytes were downloaded in this milestone from the official NOAA NCEI archive URL recorded per file, over verified TLS
  with no redirects. The downloader enforces `Content-Length` whenever the server sends it; NOAA sent it on an observed
  HEAD request, but per-download headers were not logged. Every downloaded byte stream then matched its pinned SHA-256,
  so the official archive currently serves exactly the pinned bytes.
- **Native identity** (read from each file's own metadata): `id` equals the filename, `platform = g16`, the EXIS instrument string,
  `title = "L2 XRS 1 minute average"`, `processing_level = "Level 2"`, `time_coverage_resolution = PT1M`,
  `naming_authority = gov.nesdis.noaa`, publisher NCEI, coverage from the nominal day 00:00 to the next day 00:00,
  flux units W/m², and the documented time units. All checks passed for every file.
- **Production.** One algorithm (`xrs04_avg.py`, version [2 4], dated 2025-08-13), one electron-contamination LUT
  (`g16_xrs-avg-electron-contam-lut_v3.h5`), one production git commit (`162d7a28…`), L1b site NCEI Boulder.
  `date_created` falls between 2025-12-05 18:37 and 18:44 UTC.
- **Official listings** (fetched 2026-10-11). Each monthly NOAA directory lists exactly the manifest's files (31/30/31/31) and nothing else.
  All are `v2-2-1`, all were last modified 2025-12-05, and every rounded size label is within 1 KiB of the pin.
  Listings carry no checksums, so they corroborate rather than prove bytes.

**Interpretation.** NOAA reprocessed these daily files in December 2025 under the unchanged `v2-2-1` filename.
The pins were taken after that (October 2026) and match today's archive. A future NOAA reprocessing under the
same name would make re-acquisition **fail closed** on the pinned hash rather than silently substitute data. That is the intended
behaviour, but it would block restoration until a reviewed pin update.

## 6. Missing or invalid files

None. 123/123 are present and verified. No substitution of product, version or satellite was needed or made.

## 7. Scientific limitations

- **Self-issued hashes.** SHA-256 pins are repository-issued (trust-on-first-use). NOAA publishes no per-file checksums, so byte
  identity with the historical V1 run rests on the V1 manifest, which matches here.
- **Not a scientific-correctness proof.** The native metadata ties files to the official product. It does not certify their scientific
  correctness. The calibration/electron-correction semantics are NOAA's (product documentation, DOCUMENTED in the V2 protocol).
- **Reprocessing.** The reprocessing date (2025-12-05) postdates the observation period. Earlier analyses on pre-reprocessing bytes, if any
  existed outside these pins, are not comparable byte-for-byte (UNKNOWN whether any existed).
- **Exposure.** All restored data are exposed development data. They cannot support confirmatory claims ([M5 readiness](V2_GOES_M5_READINESS.md)).
