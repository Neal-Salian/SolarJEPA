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

Two searches were made:

- **Manual search, before restoration.** A shell command searched the repository's own data locations (`data/`, `results/`, `.cache/`) and the
  checkout for `.nc`, `.part` and `.tmp` files. It found only `.gitkeep` placeholders. The command and result are recorded in
  `pre_restoration_search` of the runs evidence; the output itself was not machine-captured.
- **Tool inventory.** `inventory()` scans only the managed tree `data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/`. Its runs are recorded in full.

No unrestricted personal-directory scan was performed. M4A had already recorded that no GOES copies existed in
`~/Documents`, `~/Downloads` or `~/Desktop`.

| Category | Count |
|---|---|
| Present and verified | 0 |
| Present but unverified | n/a (the tool hashes every present file, so this category cannot arise) |
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
  for all four manifests (31/30/31/31). Recorded as `original_verifier` in the runs evidence.

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

## 8. Independent review

An independent reviewer with read-only access, its own probes and no network reviewed `ac3428f..d57a4e9`.
It reported **no BLOCKER and no HIGH**. It confirmed:

- authorization ordering (rejections happen before any network or file access)
- the canonical-identity binding of URL, path and version
- no-replace installation, the disk-check arithmetic and idempotence
- that the `_download` stats change preserves behaviour (404 → no retry; 503 → bounded retries)
- leakage containment, and the absence of test windows
- every documented number against the evidence
- that no raw data are tracked

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | MEDIUM | Valid-bin partial-sample counts (11,237 / 2,440; < 30: 177 / 179) were documented but absent from the evidence | **Fixed**: `quality_summary` emits `valid_samples_1_to_59` and `valid_samples_lt_30`; evidence regenerated (values unchanged) |
| F2 | LOW | Resource figures: 0.74 GiB was really 0.69 GiB; 0.58 GiB and 15–18 s were unbacked | **Fixed**: evidence-backed figures, with the remainder labelled INFERRED |
| F3 | LOW | Pre-restoration search scope, the impossible "present but unverified" row, and the original-verifier result were not in the evidence | **Fixed**: recorded in the runs evidence (manual search labelled as such); row marked n/a |
| F4 | LOW–MEDIUM | Failure counters were lost when a restore raised | **Fixed**: caller-owned `stats`; the CLI writes a `restore_failed` report, then re-raises. Test asserts 3 attempts, 2 retries and 3 recorded failures |
| F5 | LOW | Tracked-manifest identity was only checked after acquisition | **Fixed**: checked against the plan before acquisition too (test) |
| F6 | LOW | A symlink at a pinned path crashed `inventory` | **Fixed**: classified as `mismatch`, never followed; restore refuses (test: real and dangling links) |
| F7 | LOW | A test name claimed retry counting it did not assert | **Fixed**: counts asserted |
| F8 | LOW | `test_windows_built` was hard-coded | **Fixed**: derived from the built partitions |
| F9 | LOW | The normalization recomputation shares the window builder's boundary rule | **Documented**: wording changed from "independent" to "direct recomputation", with the limitation stated |
| F10 | LOW | The experiment config's identity was not recorded | **Fixed**: `experiment_config.sha256` in the evidence; `git_dirty` also covers `configs/` and `data/manifests/` |
| F11 | LOW | Coverage times used a prefix match, which accepted UTC offsets | **Fixed**: exact UTC-midnight parse (test with a +05:30 offset) |
| F12 | trivial | A missing `plan_id` raised a raw `KeyError` | **Fixed**: reported as a malformed plan |

All new or tightened behavioural tests were confirmed to fail on the pre-fix code (7 failures) and pass after the fix.
Full suite: **1348 passed**, 1 pre-existing warning.
