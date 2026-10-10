# SolarJEPA V2 GOES development data — M5 pilot readiness

Date: 2026-10-11. Branch `data/v2-goes-development-restoration`. Scope: whether the restored GOES development data are
ready for the planned **two-seed development feasibility pilot**. The pilot plan is
`configs/v2_proposed/feasibility_pilot_proposal.json` from M4A: PROPOSED, unapproved, not executed.

**Data verdict: READY_FOR_M5_DATA.** All 123 required files are restored, verified against their pins and the
official archive, scientifically checked, and loadable through the V1/V2 pipelines.

This verdict concerns **data only**. It does not approve the pilot. It does not make any result confirmatory.

## 1. Eligible development periods

| Period (UTC, half-open) | Exposure | Eligible use |
|---|---|---|
| 2024-05-01 → 2024-07-22 | Exposed (V1 training; P1/P2/presentation inspection) | Pilot training support |
| 2024-07-22 → 2024-08-01 | Exposed (V1 validation and ARIMA/checkpoint selection; contains P2's 07-27 → 08-01 test) | Pilot validation / checkpoint selection |
| 2024-08-01 → 2024-09-01 | Exposed (V1 test, **scored** in V1 smoke and strict runs; V1 audit F10) | Development only. **Never confirmatory.** Under the M4A pilot proposal it stays unscored (the run stops at `D_LOCKED`). Using it as a retrospective pseudo-test needs an explicit decision |

Sources: V2 protocol §3 ("all May–August 2024 data … development/exposed"), M0 decision D02 (VERIFIED), V1 audit F10.

No restored period is untouched. **None can support a confirmatory claim.** Confirmatory folds (the candidate
2020/2022/2023 calendar) remain unacquired and are gated by D03–D05 and D18. They were not accessed.
The January 2025 external-validation data were not accessed either.

## 2. Available training and validation support (OBSERVED)

| Quantity | Value |
|---|---|
| Raw one-minute rows, May–Aug | 177,120 (0 missing timestamps) |
| Training partition raw rows | 118,080 |
| Valid unique training bins (normalization support) | XRS-A 113,926 · XRS-B 116,125 |
| Training origins (stride 30) retained / excluded | 3,609 / 327 |
| V2 stride-1 complete training windows | 108,199 eligible. The proposed 20,000-window subset is available (79 steps/epoch at batch 256) |
| Validation origins retained / excluded | 412 / 68 (10 days) |
| August origins | 1,436 retained (DOCUMENTED by V1; **not recomputed** — test windows were deliberately not built) |
| Identities | Dataset `d21b81b4…68ba12`. Train split `faa586db…`. Validation split `024bfa6f…`. Normalization `84862300…`. Full hashes are in the evidence JSON |

The M4A synthetic benchmark assumed 117,931 eligible windows. The real figure is 108,199. Both exceed the 20,000 cap,
so steps per epoch, and the M4A compute projections, are unaffected (INFERRED).

## 3. Exposure restrictions

1. All pilot outputs are **development evidence**. They may inform protocol decisions only through a new versioned protocol,
   never as confirmation of JEPA value.
2. Do not score August in the pilot unless that use is explicitly approved and labelled retrospective. Never present it as a holdout.
3. Do not choose seeds, epochs, λ, losses, quality thresholds or embargo lengths **from August** results.
4. M3.1 verdict **NO_VALIDATED_REPLACEMENT**: no inference method is validated. Pilot summaries must be descriptive
   (per-seed values, differences, run diagnostics). Do not report intervals or p-values as reliable evidence.

## 4. Prerequisites before the two-seed pilot

| # | Prerequisite | Status |
|---|---|---|
| 1 | Development data restored and verified on the execution host | **DONE** on this host. On any other host, run `scripts/restore_goes_development.py --restore`, then `scripts/validate_goes_development.py` |
| 2 | M4B model–evaluation integration merged on its branch (adapters, record round-trip, fold lock) | Pending (other developer) |
| 3 | Protocol approvals: seeds, budgets, training loss, λ grid, TCN, retry policy (D10); resource ceilings (D11) | Pending |
| 4 | August handling in the pilot (sealed in-run vs pseudo-test config) (D02/D18) | Pending |
| 5 | Embargo policy for the V1 calendar (D09) — none is defined; none was invented | Pending |
| 6 | Quality threshold for partial-minute averages: keep `count ≥ 1` or tighten | Pending (new; [validation §7](V2_GOES_SCIENTIFIC_VALIDATION.md#7-questionable-rules--reported-not-changed-approval-required)) |
| 7 | Classical fit-acceptance policy owner, if the pilot includes classical models | Pending |
| 8 | Statement that pilot statistics are descriptive given M3.1 | Pending (protocol wording) |

## 5. Remaining approval decisions (data-specific)

- **D09 embargo.** Keep the touching V1 boundaries for development, or adopt a declared embargo before the pilot.
- **Partial-minute threshold.** 11,237 valid XRS-A bins have fewer than 60 samples.
- **August use** in the pilot, and its labelling.
- **Re-acquisition policy** if NOAA reprocesses `v2-2-1` again. Pins will fail closed, and updating them needs a reviewed manifest change.
- **Retiring stale wording.** Whether to retire the "untouched" wording in historical files (`v1.py`, `tests/test_v1_foundation.py`, the August manifest
  basis). These are documentation-only historical artifacts, left unchanged here.

## 6. Recommended pilot execution constraints (data side)

1. **Preflight gate.** Before any fit, run `scripts/validate_goes_development.py --out <new path>`. Require:
   - inventory 123/123 `present_verified`
   - all native identities passing
   - dataset and split fingerprints equal to §2

   Stop on any difference.
2. **Load path.** Load only through `goes_training(configs/experiments/v1_goes_2024.json)`, or a reviewed successor config that
   passes `check_split_authorization` against `configs/data/v2_goes_development_restoration.json`.
3. **Windows.** Build `train` and `validation` windows only. Keep `StagedRun` test release disabled, and stop at `D_LOCKED`.
4. **No changes during the pilot.** Do not alter masks, quality rules, normalization or windows. Any change is a new protocol version.
5. **Resources.**
   - The full validator peaked at **0.69 GiB RSS** (739,655,680 B in the evidence). That run includes data loading, windowing,
     Torch import and the V2 preparation, and is well under the proposed 4 GiB job ceiling.
   - Its `pipeline_smoke` phase (loading, windows built twice, normalization, V2 preparation) took **17.8 s**. Per-job real-data
     preparation is therefore of order 10–20 s (INFERRED). Budget for it in per-job timeouts. M4A's synthetic preparation took about 5.5 s.
6. **Record per job:** code commit, evidence file hash, dataset/split/normalization fingerprints, and per-job RSS.

## 7. Verification summary

| Check | Result |
|---|---|
| Required files identified | 123 (4 manifests), 36,535,474 B |
| Restored | 123 downloaded, 0 retries, 0 failures. Idempotent re-runs: 0 requests |
| Manifest verification | 123/123 SHA-256 and size match |
| Authoritative provenance | 123/123 native identity checks. Official listings consistent (names, version, dates, sizes) |
| Time series | 0 missing, 0 duplicate, 0 off-grid timestamps. Valid fractions A 97.47%, B 98.72% |
| Pipeline | Loader, P1 windows and V2 preparation compatible. V1 counts reproduced. Normalization train-only (recomputed from training rows) |
| Test isolation | No test windows built. No sealed or external data accessed |
| Training | None. No optimizer step |
