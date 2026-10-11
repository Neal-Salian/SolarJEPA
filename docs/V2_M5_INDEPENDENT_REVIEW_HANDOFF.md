# SolarJEPA V2 M5.0 — independent review handoff (for the M5.0 integration developer)

Date: 2026-10-11. From the independent review branch `research/v2-m5-protocol-review` (base `8a9c98d`) to the
M5.0 integration work on `feat/v2-m5-pilot-readiness` (`2e3f871` at review time; **not modified by this review**).
Full detail: [scientific review](V2_M5_PROTOCOL_SCIENTIFIC_REVIEW.md), [decision register](V2_M5_EXPERIMENTAL_DECISION_REGISTER.md),
[resource and fairness review](V2_M5_RESOURCE_AND_FAIRNESS_REVIEW.md), evidence
[`docs/evidence/v2_m5_protocol_review_evidence.json`](evidence/v2_m5_protocol_review_evidence.json).

**Nothing here approves the pilot.** The owner decides D09, D10, D11, M5-AUG, M5-QC, M5-SEED, M5-LIN, M5-FAIL, M5-CLASSICAL and M5-STATS.

## 1. Must exist before any real-data pilot (blocking)

| # | Implement or verify | Why | Where | Required test |
|---|---|---|---|---|
| 1 | **Development-only May–July loader.** Explicit allow-list of the May/June/July manifests by SHA-256, checked before any read. Build `train`/`validation` `TemporalPartition`s directly, because `validate_config` requires a test split and `chronological_partitions` rejects train+validation-only lists. Carry the test identity as a string only. Optional embargo per D09 | M4B handoff requirement; review R1/R10. The historical all-manifest loader reads August | `src/solar_flare_jepa/data/foundation.py` (`goes_training`, `_pinned_frame`, `validate_goes_files`), `forecasting/splitting.py`, `forecasting/windows.py` | Behavioural test that August files are **never opened** (instrument `open`/xarray or use a tripwire manifest). Test that a non-allow-listed manifest is rejected before any read. Reproduction test: train 3,609/327 and validation 412/68 retained/excluded, normalization fingerprint `84862300…`, training slice `8e5f200f…` on May–July (evidence A) |
| 2 | **Approved-identity preflight inside the run.** Bind `data_provenance_fingerprint` to the loaded `dataset.fingerprint`; check pinned dataset, split and calendar fingerprints and the manifest allow-list | R2. Guards currently accept an extra August-like segment and mislabelled calendars | M4B `experiments/v2_evaluation_safety.py` (`DevelopmentRun`, `register_fitting_guard`) | Synthetic test: a dataset with an extra segment, or a "validation" partition placed over a later calendar, is rejected |
| 3 | **Enforcing job driver.** One job per subprocess, serial. Kill on per-job timeout. Sample child RSS and kill at the approved ceiling. Record child `ru_maxrss`. Enforce the total budget. Write explicit ledger outcomes for timeout/RSS kills. Cap attempts at 1 + 1 identical retry | R3/R4. None of these exist in `StagedRun`/`DevelopmentRun`; crashed jobs re-run on every resume without a cap | `experiments/v2_runner.py` (`_run_job`, `fit`, `max_rss_bytes`), M4B `v2_evaluation_safety.py` | Synthetic jobs that sleep past the timeout, allocate past the RSS limit, and crash twice: each is killed or recorded, and none is retried more than once |
| 4 | **Versioned pilot amendment** (new file; historical M4A JSONs stay unchanged) | R6/R11. Historical `quantile_linear_fits: 1` and "sealed" August wording | `configs/v2_proposed/` | `tests/test_v2_m4a_proposals.py` pattern: the amendment constructs every config. Per-seed linear (2 fits). August excluded. Approved λ grid, timeouts and RSS. Job matrix listed |
| 5 | **SSL artifact rule.** Persist exactly one SSL artifact per seed. On an SSL retry, re-run both J and frozen J for that seed | R5. The artifact fingerprint includes `budget.wall_seconds` (`training/controlled.py:418`), so a recomputed weight-identical artifact fails `check_paired_cohort` | `training/controlled.py` (`_pretrain`, `PretrainingArtifact`, `check_paired_cohort`) | Either test the documented rule, or (if approved) exclude wall time from the identity fingerprint and test that recomputation passes |

## 2. Should be implemented or verified (non-blocking, recommended)

- **Threads:** set `OMP_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` to 4 and keep low interop threads. Record *observed* threads and the host. Bind the thread count in `check_comparator_cohort` (R7). `JepaConfig.threads` defaults to 8, so set it explicitly.
- **Reporting guard:** pilot outputs only via `experiments/v2_descriptive.descriptive_comparison` and `descriptive_budget_table`. Optionally make `publish_development` reject non-null `ci`/`p_value`/`se`/`bootstrap` fields (R9). Do not call `evaluation.comparison.paired_comparison`, `experiments.v1.run_v1` or `evaluation.probabilistic.block_bootstrap` in pilot reporting.
- **Post-selection labelling:** mark selected-epoch and selected-λ validation losses as post-selection in records and reports (R12).
- **Classical models:** replicate `persistence_empirical` and point persistence with `independent_seed_runs=False`. Keep ARIMA and volatility out of comparisons.
- **Provenance additions:** clean commit + `code_provenance` source fingerprint, torch version (missing from `code_provenance`), and SHA-256 of the approved amendment, loaded configs, restoration plan (`f782c942…`) and regenerated GOES integrity evidence. Include the per-job timeout/RSS outcome.
- **Diagnostics:** TCN zero-width interval frequency; linear raw crossing fraction per λ; the full validation curve per arm and seed.
- **Small corrections:** frozen-arm records report `trainable_total = 136,332`; report the head-only 67,948. Document that `PCG64(seed)` equals the `[seed, 0]` stream.

## 3. Recommended values to wire as configurable (not approved)

| Item | Recommended value |
|---|---|
| Seeds | 1261866429, 1291916211, fixed order, no replacement |
| Schedule | 8 SSL / 8 warmup / 15 downstream epochs, fixed; 20,000 windows; batch 256 |
| Loss / selection | Train and select on `dex_pinball_equal_channel_v2`, earliest minimum. Separate V1-loss cohort for J and S |
| Quantile-linear | Per seed; λ ∈ {0, 0.01, 0.1, 1, 10, 100, 1000, 10000}; 100 epochs; Adam lr 0.01 |
| Embargo | E_1d by truncating the training end to 2024-07-21, or E0 (owner choice). Declare the matching `embargo_ns` |
| Quality control | V1 rule primary; predeclared `count ≥ 30` sensitivity (development-only, descriptive) |
| Timeouts | SSL 300 s; neural downstream 600 s; TCN 1,800 s; linear 600 s per seed |
| Memory | 2 GiB per-job RSS kill; 4 GiB backstop |
| Total budget | 7,200 s |
| Threads | 4 |
| Storage | 1 GiB reserved |

## 4. Existing tests relevant to these areas

- `tests/test_v2_controlled.py`: pairing, step accounting, selection, frozen and teacher isolation, SSL reuse, cohort checks including validation identity
- `tests/test_v2_comparators.py`: TCN and linear behaviour; `tests/test_v2_losses.py`: losses and quantile-level validation
- `tests/test_v2_runner.py`: stage machine, release gate, RSS between jobs
- `tests/test_goes_restoration.py`, `tests/test_goes_development_validation.py`: authorized restoration, native identity, pipeline smoke
- `tests/test_v2_m4a_proposals.py`: proposal constructibility pattern
- M4B (`2e3f871`): `tests/test_v2_evaluation_*` and related integration tests (1,583 collected; 1,582 passed here, with 1 environmental failure from the shared venv's non-editable install)

## 5. Do not

- Run the historical all-manifest loader for the pilot, or describe August as unread because no release was called.
- Access January 2025, candidate folds or any sealed data.
- Change splits, quality rules or manifests without an approved versioned amendment.
- Report CIs, p-values, significance or generalisation.
- Retry with changed settings, or drop or replace seeds.
