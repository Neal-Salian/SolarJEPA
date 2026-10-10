# SolarJEPA V2 GOES development data — scientific validation

Date: 2026-10-11. Branch `data/v2-goes-development-restoration`. Inputs: the 123 restored and verified
files ([restoration report](V2_GOES_DATA_RESTORATION_REPORT.md)). Evidence:
[`docs/evidence/v2_goes_development_integrity.json`](evidence/v2_goes_development_integrity.json), produced by
`scripts/validate_goes_development.py` at the committed code (`code.git_head` in the file).

All figures are **OBSERVED** on the restoring host unless labelled otherwise.

**Rules applied.** The validation applies the repository's existing rules unchanged:
- `data/goes.read_goes` quality masks
- the native contract `data/foundation.validate_goes_files`
- P1 window construction
- train-only `Normalization`

Nothing was interpolated, filled, removed, renormalized or relabelled. No model was trained, no optimizer step ran, and no test window was built.

## 1. Timestamp coverage and cadence

| Month | Files | Observed rows | Grid rows | Missing bins | Duplicates | First bin start (UTC) | Last bin end (UTC) |
|---|---|---|---|---|---|---|---|
| May | 31 | 44,640 | 44,640 | 0 | 0 | 2024-05-01 00:00 | 2024-06-01 00:00 |
| June | 30 | 43,200 | 43,200 | 0 | 0 | 2024-06-01 00:00 | 2024-07-01 00:00 |
| July | 31 | 44,640 | 44,640 | 0 | 0 | 2024-07-01 00:00 | 2024-08-01 00:00 |
| August | 31 | 44,640 | 44,640 | 0 | 0 | 2024-08-01 00:00 | 2024-09-01 00:00 |
| **Total** | **123** | **177,120** | **177,120** | **0** | **0** | | |

**Contract checks.** The native contract passed for every file and every month:

- the time convention is "seconds since 2000-01-01 12:00:00 UTC", record start, leap seconds neglected
- times are monotonic and unique within and across files
- every timestamp is on the one-minute grid, with no sub-minute or non-integer-minute steps
- no two files overlap
- each file's coverage metadata matches its first and last bins
- each file's coverage lies inside its nominal day
- every day has exactly 1,440 bins
- all four months are exactly contiguous, as the multi-manifest loader requires

The 177,120 total reproduces the V1 audit's DOCUMENTED figure.

**Leap seconds.** The product neglects them. No leap second was inserted between 2017 and this interval, so the convention has no effect
on May–August 2024 timestamps (INFERRED from the public IERS leap-second record).

## 2. Channels and units

- XRS-A (0.05–0.4 nm) and XRS-B (0.1–0.8 nm) primary-composite irradiance, both in **W/m²**, confirmed in every file.
- Channel order in the pipeline is `('xrsa_flux', 'xrsb_flux')` for features and targets.
- Per-bin primary detector (`xrs_primary_chan`, retained as diagnostic, not a model input):

| Value | Bins |
|---|---|
| 5 | 175,630 |
| 6 | 1,003 |
| 10 | 487 |

  Code semantics are NOAA's and are not interpreted here.
- Valid log10 flux ranges by month:

| Month | XRS-A | XRS-B |
|---|---|---|
| May | −7.93 to −3.36 | −6.09 to −3.06 |
| June | −7.90 to −4.33 | −6.00 to −3.82 |
| July | −7.86 to −4.23 | −5.96 to −3.71 |
| August | −7.66 to −4.27 | −5.74 to −3.77 |

  No non-positive raw flux values occur. These ranges are distribution facts of exposed data. They are not event labels.

## 3. Quality flags and validity (existing strict policy)

A bin is valid for a channel only if **all** of the following hold:

- the flux is finite and positive, within `valid_min`/`valid_max`
- status flag = 0
- 0 < samples ≤ 60
- the electron correction is not invalid, interpolated or decaying (bits 1, 2, 4)
- the channel's own significant-contamination bit is clear (8 for A, 16 for B)

| Month | XRS-A valid | XRS-B valid | Status flags (0 good / 1 eclipse / 2 bad / 4 interpolated) | Electron flag values |
|---|---|---|---|---|
| May | 42,695 (95.64%) | 42,696 (95.65%) | 42,705 / 0 / 1,924 / 11 | 0: 44,630 · 3: 9 · 40: 1 |
| June | 43,074 (99.71%) | 43,195 (99.99%) | 43,200 / 0 / 0 / 0 | 0: 43,074 · 3: 5 · 40: 121 |
| July | 42,329 (94.82%) | 44,406 (99.48%) | 44,416 / 0 / 208 / 16 | 0: 42,553 · 3: 9 · 40: 2,077 · 43: 1 |
| August | 44,548 (99.79%) | 44,548 (99.79%) | 44,557 / 61 / 21 / 1 | 0: 44,631 · 3: 9 |
| **Total** | **172,646 (97.47%)** | **174,845 (98.72%)** | 174,878 / 61 / 2,153 / 28 | |

XRS-A and XRS-B status-flag counts are identical in every month of this period.

**Interpretation of the counts:**
- Bad-data bins (status 2) carry non-finite flux: 2,153 bins, exactly the non-finite raw count.
- Electron flag 40 = 32 + 8 (A1 and A significant contamination) masks **only XRS-A**, as designed. This explains July's lower
  A validity (2,077 bins).
- Flag 3 (correction invalid + interpolated) masks both channels.
- August's 61 eclipse bins (status 1) are masked.

**Sample counts (`xrs?_num`):**

| Count | XRS-A | XRS-B |
|---|---|---|
| Full 60-sample bins | 163,549 | 172,495 |
| Observed bins with 1–59 samples | 11,390 | 2,444 |
| **Valid** bins with 1–59 samples | **11,237** | 2,440 |
| Valid bins with < 30 samples | 177 | 179 |
| Zero or invalid count | 2,181 | 2,181 |

The 11,237 valid XRS-A figure reproduces the V1 audit's DOCUMENTED number exactly.

## 4. Missing-data observations

- **No missing timestamps** in any month. Every invalid bin is an observed native record that fails the quality policy, and keeps
  `observed=True` and `valid=False`. The grid reindex conserved every native record, so no observation was dropped.
- Missing values stay `NaN` with a false mask. Origins with any invalid context or target cell are **excluded** (complete-case
  policy), never imputed. See §6.

## 5. Preprocessing compatibility

These checks ran through `goes_training`, then the P1 windows, then the V2 trainers' own `training.controlled._prepare`.

| Interface | Result |
|---|---|
| Loader | `goes_training(configs/experiments/v1_goes_2024.json)` accepts all four manifests: 177,120 rows, 2 channels, 60 s cadence, W/m². It re-verifies every file hash. Dataset fingerprint `d21b81b4…68ba12` |
| Forecast spec | 120-step context, 30-step horizon, stride 30, log10 transform, references 1 W/m², `retrospective_bin_end`, `complete` eligibility — unchanged |
| Train windows (V1 split) | 3,609 retained / 327 excluded origins. Context `[3609, 120, 2]`. All masks complete. 118,080 raw training rows |
| Validation windows | 412 retained / 68 excluded origins. Context `[412, 120, 2]`, targets `[412, 30, 2]`. Masks complete |
| V2 preparation | 108,199 eligible stride-1 complete training windows. Deterministic evenly spaced subset of 20,000 used. Window tensors `[·, 150, 2]` (context + future for SSL), targets `[·, 30, 2]`. Validation tensors `features/feature_mask [412, 120, 2]`, `targets/target_mask [412, 30, 2]`, all finite. Normalization fingerprint identical to the direct `Normalization.fit` |
| Determinism | Rebuilding windows gives identical split fingerprints and origin lists (train `faa586db…`, validation `024bfa6f…`) |
| Train-only normalization | Feature mean/std (log10): A −6.9752 / 0.5742, B −5.4753 / 0.3416. These come from 113,926 (A) and 116,125 (B) valid unique training bins. **Equal** (|Δ| ≤ 1e-12) to an independent recomputation from rows inside the training partition only, and **different** from a train+validation fit. So the check can detect validation leakage, and none occurs |

The V1 audit's DOCUMENTED counts are 3,609 / 327 (train) and 412 / 68 (validation). Both are reproduced exactly.

## 6. Temporal leakage findings

| Check | Finding |
|---|---|
| Training windows cross forbidden boundaries | **No.** Every retained origin's context and targets lie inside its own partition (`context_inside`, `targets_inside` true). V2 stride-1 windows are built from training-partition rows only |
| Forecast targets inside authorized partitions | **Yes**, by containment. Validation contexts start at or after the training end (`validation_starts_after_training` true) |
| Validation used for normalization | **No.** See §5 (independent recomputation) |
| Embargo | **None defined on this branch.** V1 partitions touch (train end = validation start = 2024-07-22 00:00; validation end = test start = 08-01 00:00). Containment prevents shared windows or targets, but autocorrelated flux crosses each boundary. `embargo_ns` exists only on the M0/M1 evaluation branch. The V2 protocol's one-day embargo is proposed for new folds, not for this calendar. **No embargo length was invented. Decision required (D09)** |
| Overlapping horizons | Stride 30 = horizon 30, so target intervals are disjoint. Contexts overlap by 90 min and earlier targets become later context. Consistent with the protocol's causal rolling design; evaluation dependence is a statistics question (M3.1) |
| Evaluation identities | Split fingerprints are deterministic. The dataset fingerprint covers all four months, so a May–July-only dataset would change every identity |
| Fingerprints vs declared support | `goes_training` records each source path, SHA-256 and size from the verified files. Manifest hashes are re-verified before decoding |
| Test isolation | The smoke run builds `train` and `validation` windows only. The V1 `test` partition (August) is never windowed or scored. August bytes **are** decoded by the loader, because the multi-manifest dataset requires contiguous manifests. This is authorized (development-exposed) |

## 7. Questionable rules — reported, not changed (approval required)

1. **Partial-minute averages are valid.** 11,237 valid XRS-A bins (6.5% of A-valid bins) and 2,440 XRS-B bins average fewer than 60 one-second
   samples. 177 and 179 respectively average fewer than 30. Raising the threshold would change support and normalization. It is a protocol decision.
2. **No embargo** on the V1 calendar (§6).
3. **Electron-correction reprocessing.** All files use LUT v3 from the December 2025 reprocessing. Comparability with any earlier copies is UNKNOWN (none were pinned).
4. **Stale exposure wording.** The August manifest `basis` says "untouched v1 test holdout", as do `v1.py` and `tests/test_v1_foundation.py:24`.
   These conflict with the V1 audit (F10) and the V2 protocol §3. They are historical files and were not edited.
5. The primary-detector code (`xrs_primary_chan`) is not interpreted. The composite flux is used as NOAA provides it.
