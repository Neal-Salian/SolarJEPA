# SolarJEPA V2 M5 experimental decision register (independent review)

Date: 2026-10-11. Branch `research/v2-m5-protocol-review`, base `8a9c98d` (GOES restoration, which contains M4A).
Reviewed refs:

| Milestone | Commit |
|---|---|
| M4A | `ac3428f` |
| M4B | `2e3f871` |
| GOES restoration | `8a9c98d` |
| M3.1 | `5e88f3a` |
| `feat/v2-m5-pilot-readiness` (read only, equal to M4B at review time) | `2e3f871` |

Evidence: [`docs/evidence/v2_m5_protocol_review_evidence.json`](evidence/v2_m5_protocol_review_evidence.json)
(sections A–D). Narrative: [scientific review](V2_M5_PROTOCOL_SCIENTIFIC_REVIEW.md),
[resource and fairness review](V2_M5_RESOURCE_AND_FAIRNESS_REVIEW.md), [handoff](V2_M5_INDEPENDENT_REVIEW_HANDOFF.md).

**Nothing in this register is approved.** Statuses:

| Status | Meaning |
|---|---|
| `RECOMMENDED_NOT_APPROVED` | Evidence supports a recommendation; the owner must decide |
| `REQUIRES_OWNER_DECISION` | Several defensible options remain; the choice is a scientific or priority judgement |
| `BLOCKED_ON_EVIDENCE` | A prerequisite artifact or behaviour must exist before the decision can be made safely |

Register IDs D02–D18 refer to `docs/V2_M0_RESOLUTION.md` (present on M4B `2e3f871`, not on this branch). New IDs use the prefix `M5-`.

## Summary

| ID | Decision | Recommended option | Status |
|---|---|---|---|
| D09 | Temporal embargo | E_1d by truncating training to 2024-07-21; E0 acceptable if V1 identity is prioritised | REQUIRES_OWNER_DECISION |
| M5-AUG | August 2024 handling | Exclude from the initial pilot; never load; May–July-only route | RECOMMENDED_NOT_APPROVED (route BLOCKED_ON_EVIDENCE) |
| M5-LOADER | Development-only GOES input route | Explicit May–July manifest allow-list; train/validation partitions built directly; behavioural no-August test | BLOCKED_ON_EVIDENCE |
| M5-QC | GOES quality threshold | Policy C: V1 rule primary, predeclared `count ≥ 30` sensitivity | RECOMMENDED_NOT_APPROVED |
| M5-SEED | Seed-selection policy | First two protocol seeds, declared up front, no replacement, threads fixed at 4 | RECOMMENDED_NOT_APPROVED |
| D10 | Experimental protocol (arms, schedules) | Five arms + TCN + per-seed linear; 8/8/15 fixed; separate loss-comparison cohort | RECOMMENDED_NOT_APPROVED |
| M5-LOSS | Loss and checkpoint selection | Train and select on equal-channel dex pinball, earliest minimum; selected values labelled post-selection | RECOMMENDED_NOT_APPROVED |
| M5-LIN | Quantile-linear regularization | Per seed; owner chooses between the M4A 7-value grid and an 8-value grid adding 0.01 and 0.1 (dropping 10⁵); 100 epochs; selected λ reported per seed | REQUIRES_OWNER_DECISION |
| M5-TCN | TCN configuration | Keep the M4A proposal (width 32, k = 3, dilations 1…32, 15 fixed epochs, CPU) | RECOMMENDED_NOT_APPROVED |
| D11 | Resource ceilings | Parent driver; per-job kill timeouts; 2 GiB per-job RSS kill; 7,200 s total; 4 threads; serial | RECOMMENDED_NOT_APPROVED (enforcement BLOCKED_ON_EVIDENCE) |
| M5-FAIL | Failure and retry handling | Classified failures; ≤ 1 identical infrastructure retry; no seed replacement; incomplete stays incomplete | RECOMMENDED_NOT_APPROVED (enforcement BLOCKED_ON_EVIDENCE) |
| M5-CLASSICAL | Classical baseline policy | Empirical and point persistence only, replicated and flagged; ARIMA/volatility excluded | RECOMMENDED_NOT_APPROVED |
| M5-STATS | Descriptive-only reporting | `descriptive_comparison` and `descriptive_budget_table` only; mandatory labels; forbidden phrases | RECOMMENDED_NOT_APPROVED |

---

## D09 — Temporal embargo

**Question.** Should a gap separate the training and validation partitions? If so, how long, and on which side?

**Options.** Counts are OBSERVED on May–July data (evidence A: `embargo_options`).

| Option | How | Validation origins | Training origins | Stride-1 windows | Normalization change |
|---|---|---|---|---|---|
| E0 (current V1) | Touching bounds | 412 | 3,609 | 108,199 | — |
| E_h (150 min) | Truncate train end | 412 | 3,604 | 108,049 | ≤ 0.03% scale |
| E_1d | Truncate train end to 2024-07-21 00:00Z | 412 | 3,561 (−1.3%) | 106,759 | +0.38% / +0.47% scale |
| E_1d | Delay validation start | 370 (−10.2%) | 3,609 | 108,199 | none |
| E_2d | Delay validation start | 343 (−16.7%) | 3,609 | 108,199 | none |

**Evidence.**
- Containment already prevents shared context or target bins at E0 (OBSERVED: every retained origin's support lies inside its partition).
- Dependence across the boundary is real. Training-data autocorrelation of raw log10 flux (XRS-A / XRS-B):

  | Lag | Autocorrelation |
  |---|---|
  | 2 h | 0.50 / 0.59 |
  | 1 d | 0.31 / 0.38 |
  | 2 d | 0.25 / 0.32 |
  | 5 d | 0.09 / 0.11 |

- After 1-day detrending, the e-folding time is about 48 / 61 min, and block correlation falls to about 0 at gaps ≥ 120 min. So the fast component decorrelates within about 2 h. The multi-day level persists: raw block correlation is 0.33 / 0.40 at 1 d and 0.29 / 0.36 at 2 d (OBSERVED).
- The V2 protocol's 1-day embargo is proposed for new folds and is stated not to prove independence.
- M4B implements `embargo_ns` in `chronological_partitions` and in the fitting guard.

**Recommendation.** **E_1d by truncating the training end to 2024-07-21 00:00Z.**
- It keeps the full 412-origin selection set.
- It costs 1.3% of training support.
- It exercises the same embargo machinery and value proposed for later folds.
- It removes the fast dependent component: 1 day is about 12× the ~2 h decorrelation time and 24–30× the detrended e-fold.

**E0 is a defensible alternative** for a purely exposed-data feasibility pilot. It keeps V1's training origins and content (3,609 origins; training slice `8e5f200f…`; normalization `84862300…`) at the cost of a documented boundary-dependence limitation. Split fingerprints still change under a May–July-only dataset, because they include the dataset fingerprint. E_2d is not supported by the evidence: the multi-day level persists anyway, and it costs 16.7% of validation. Delaying validation costs 10–17% of a small selection set.

**Risks.**
- Any embargo changes training fingerprints and breaks bitwise V1 window reproduction.
- No finite embargo establishes independence. Pilot outputs remain descriptive regardless.

**Approval.** Owner (D09). A changed split requires a versioned amendment, and the guard must declare the matching `embargo_ns`.

**Status.** REQUIRES_OWNER_DECISION. The recommendation is E_1d-truncate. The choice between it and E0 is a priority call: protocol consistency against V1 comparability.

## M5-AUG — August 2024 handling

**Question.** Should August 2024 (V1 test, already scored) appear in the initial pilot at all?

**Options.**
1. Exclude entirely: never load or decode it.
2. Load it but keep it sealed behind `D_LOCKED`: this is the M4A pilot proposal.
3. Explicitly labelled development analysis, such as a retrospective pseudo-test.

**Evidence.**
- August is exposed (D02 VERIFIED; V1 audit F10).
- The historical loader `goes_training(configs/experiments/v1_goes_2024.json)` reads all four manifests including August (OBSERVED, `foundation.py:189-190`).
- The M4B handoff requires a route that never reads test inputs (`2e3f871:docs/V2_M4B_M5_HANDOFF.md`). Stopping at `D_LOCKED` cannot undo loader reads.
- Existing guards accept a dataset with an extra August-like segment and do not allow-list manifests (OBSERVED synthetic probes, evidence D: `isolation`).
- A May–July-only dataset reproduces V1 train and validation windows and normalization exactly (evidence A: `v1_reproduction`).
- **This review supersedes** `docs/V2_GOES_M5_READINESS.md` §6.1–6.2 (restoration milestone). Those sections recommended the all-manifest loader and its fingerprints. That recommendation predates the M4B requirement and conflicts with it. The historical document is not rewritten.

**Recommendation.** **Option 1.** Exclude August from the initial pilot and never open its files. Any later development use of August (option 3) needs its own approved, labelled amendment. It must never be called a holdout, test, sealed or untouched.

**Risks.** None to the pilot's purpose. August adds no feasibility information that May–July cannot supply.

**Approval.** Owner (D02/D18).

**Status.** RECOMMENDED_NOT_APPROVED. Execution depends on M5-LOADER.

## M5-LOADER — Development-only GOES input route

**Question.** How does the pilot load only approved train/validation inputs?

**Evidence.**
- `validate_config` requires a test split, and `chronological_partitions` rejects a test bound outside the data and rejects a train+validation-only list (OBSERVED, evidence A: `loader_gap`).
- A route that builds `TemporalPartition`s directly and calls `build_partition_windows` reproduces V1 support from the May/June/July manifests.

**Recommendation.** A versioned loader amendment with:
- an explicit manifest allow-list checked by SHA-256 **before** any read: May `9828b714…`, June `91e45449…`, July `581a3c4b…` (full hashes in evidence D);
- train and validation partitions only;
- the declared test identity carried as a string;
- `data_provenance_fingerprint` bound to the loaded `dataset.fingerprint`;
- new pinned fingerprints from a rerun validator;
- a behavioural test proving that August files are never opened (for example, an instrumented file-open check).

**Status.** BLOCKED_ON_EVIDENCE. The route and its no-August test do not yet exist.

## M5-QC — GOES quality threshold

**Question.** Should minute bins averaged from fewer than 60 one-second samples remain valid?

**Options.** Counts are OBSERVED on May–July, complete-case (evidence A: `qc_thresholds`).

| Policy | Rule | Training origins | Validation origins | Stride-1 windows | Normalization change |
|---|---|---|---|---|---|
| A | V1, `0 < count ≤ 60` | 3,609 | 412 | 108,199 | — |
| B30 | count ≥ 30 | 3,309 (−8.3%) | 382 | 99,193 | ≤ 0.004% |
| B45 | count ≥ 45 | 3,208 (−11.1%) | 376 | 96,149 | ≤ 0.009% |
| B59 | count ≥ 59 | 2,254 (−37.5%) | 300 | 67,572 | 0.04% |
| B60 | count = 60 | 0 | 0 | 22 | +0.81% / +0.25% |
| C | A primary, plus a predeclared sensitivity (for example B30) | as A | as A | as A | — |

**Evidence.**
- Partial valid bins in May–July: XRS-A 8,381 (6.54%), XRS-B 1,976 (1.52%). Rates are stable by month and similar in train and validation.
- 91.7% (A) and 77.7% (B) of partial bins have exactly 59 samples. About 99% of those A bins carry the native `xrs?_flag_excluded` particle-spike indication: they are isolated singletons across all hours.
- Bins with fewer than 45 samples (about 276 per channel) cluster at the edges of bad-data episodes and at instrument-mode transitions.
- The repository ignores `xrs?_flag_excluded` (OBSERVED).
- Normalization is insensitive to the threshold. The cost is origin support, because complete-case windows need 150 consecutive valid bins.

**Recommendation.** **Policy C.** Keep the V1 rule for the primary pilot, which preserves comparability. Predeclare a **count ≥ 30** sensitivity (development-only, descriptive) that targets the episode-edge bins and costs about 8% of origins. Do not adopt B59 or B60: they destroy support and would systematically remove particle-spike-flagged minutes. Partial-bin occurrence is not related to flux level in May–July (Spearman about −0.02 / −0.03, OBSERVED); any relation to space-weather conditions is INFERRED from domain knowledge, not established here. Record the limitation that partial-minute averages are treated as full observations.

**Risks.**
- The sensitivity run doubles some jobs. It may be limited to J and S for one seed if compute is tight; that is an owner decision.
- Any threshold must be chosen from May–July evidence only, never from August.

**Approval.** Owner (D08/D10).

**Status.** RECOMMENDED_NOT_APPROVED.

## M5-SEED — Seed-selection policy

**Evidence.**
- The 20 SHA-256-derived seeds reproduce exactly (OBSERVED, evidence B). Every stochastic component is seeded: initialization, SSL/warmup order `[seed,0]`, SSL mask `seed+2`, downstream order `[seed,1]`, linear `PCG64(seed)`.
- Same seed and thread count give bitwise-identical weights across processes.
- **Changing Torch threads from 1 to 4 changes JEPA-family weights bitwise** (OBSERVED). The validation metric moved by up to 2.4e-6. TCN and linear were unaffected.
- Initial-state fingerprints are identical across the five arms.
- `PCG64(seed)` produces the same stream as `default_rng([seed,0])`, a NumPy SeedSequence property. This is harmless but undocumented.
- Two seeds share data, windows, normalization and validation. Their spread measures optimisation variance only, with 1 degree of freedom. Under normality, the textbook χ²₁ 95% interval for the true standard deviation spans 0.45–31.9× the observed value (standard result, not computed from the data).

**Recommendation.**
- Use the first two protocol seeds in order (1261866429, 1291916211), declared before any fit, for every planned arm including TCN and linear.
- Never drop, replace or re-draw a seed. A failed job makes the pilot INCOMPLETE.
- Fix and record Torch threads at 4 and the host identity, because threads are part of the numerical result.

**Approval.** Owner (D10).

**Status.** RECOMMENDED_NOT_APPROVED.

## D10 — Experimental protocol (arms, schedules, cohort)

**Evidence.** M4A proposal; M4B amendments (per-seed linear, development-only loader); counts verified in evidence B.

**Recommendation.**
- **Arms:** J, S, B, frozen JEPA (reusing J's SSL artifact) and frozen random, plus TCN and quantile-linear, each × 2 seeds.
- **Schedules:** 8 SSL / 8 warmup / 15 downstream epochs, fixed (no early stopping); 20,000-window subset; batch 256; AdamW 1e-3 / 1e-4; clip 1.0.
- **Loss-comparison cohort:** J and S trained and selected on `normalized_pinball_v1`, checked as a **separate cohort**.
- **Classical:** per M5-CLASSICAL.
- **SSL artifacts:** persist exactly one per seed. An SSL retry invalidates **both** J and frozen J for that seed, because the artifact fingerprint includes wall time (OBSERVED; `controlled.py:418` on this branch, `:435` on M4B). A recomputed but weight-identical artifact therefore fails `check_paired_cohort`.

**Proposal amendments required.**
- The pilot JSON's `quantile_linear_fits: 1` and the linear `seed_rule: first paired seed` contradict the M4B per-seed requirement. They must become two fits.
- The August handling must change to exclusion.
- Linear timeout and RSS values must be updated (D11).

**Approval.** Owner (D10), via a new versioned proposal. The historical M4A JSONs stay unchanged.

**Status.** RECOMMENDED_NOT_APPROVED.

## M5-LOSS — Loss and checkpoint selection

**Evidence** (evidence B):
- `dex_pinball_equal_channel_v2` equals the direct dex mean pinball within 2.8e-17. Channels are weighted equally after per-channel means. Masked NaN targets leave finite losses with zero gradient. Gradcheck passes. Batched validation matches the one-shot metric within 9.5e-11.
- Earliest-minimum selection is deterministic on exact ties, but a 1e-12 difference decides it. Thread-level noise can flip near-ties.
- Neural arms choose among 15 epochs. Linear chooses among λ values at the final epoch.
- Selected validation values are optimistically biased (post-selection).

**Recommendation.**
- Train and select on equal-channel dex pinball with the earliest minimum among downstream epochs.
- Record `normalized_pinball_v1` as a diagnostic.
- Report selected-epoch validation losses explicitly as **post-selection**.
- Report the full validation curve and the selected epoch per arm and seed.
- Keep thread count fixed.

**Status.** RECOMMENDED_NOT_APPROVED.

## M5-LIN — Quantile-linear regularization

**Evidence** (evidence B; real dimensions; synthetic data; 100 epochs; 7,900 steps per λ):

| λ | Mean W² | Validation loss |
|---|---|---|
| 0 | 3.78e-3 | 0.01674 |
| 0.1 | 2.06e-3 | 0.01665 (synthetic optimum) |
| 1 | 7.5e-4 | 0.01711 |
| 100 | 3.4e-5 | 0.02270 |
| 1e4–1e5 | ≈ 1e-7 | 0.0303–0.0307 |

- The penalty gradient exceeds the data-fit gradient from λ ≈ 1000.
- The M4A grid {0, 1, …, 10⁵} spans unregularized to dominant, but it has **no point below 1**, and 10⁵ is redundant.
- A second seed changes validation loss by 2.9e-4 at λ = 0, three times the gap between λ = 0 and λ = 0.1. In the weak range, λ choice sits inside optimisation noise.
- Measured cost is 7.1–7.7 s per λ (evidence C, quiet host).
- M4A deliberately replaced the earlier grid {0, 0.001, 0.01, 0.1, 1} as near-unregularized (`training_protocol_proposal.json`, baseline audit B1). Adding 0.01 and 0.1 back partly reverses that choice.

**Options.**
1. **M4A grid** {0, 1, 10, 100, 1000, 10000, 100000}: fewer selection opportunities; no point between 0 and 1.
2. **8-value grid** {0, 0.01, 0.1, 1, 10, 100, 1000, 10000}: covers the weak range where the synthetic optimum lies, and drops the redundant 10⁵. The extra low-λ points mainly add post-selection optimism, because weak-range differences sit inside seed noise.

**Recommendation.** Either is defensible. Option 2 gives better coverage; option 1 gives fewer selection opportunities. Both run per seed, 100 fixed epochs, Adam lr 0.01, batch 256. Ties go to the smallest λ. Report the selected λ per seed and flag a boundary-selected maximum. Synthetic data cannot identify the scientific optimum. Never tune using August.

**Status.** REQUIRES_OWNER_DECISION.

## M5-TCN — TCN configuration

**Evidence.**
- 44,620 parameters and a 253-bin receptive field (re-verified). Causal. Monotone head.
- On synthetic data the minimum quantile spacing can hit 0.0 (softplus underflow): zero-width intervals, not crossings.
- Measured 16.1–17.6 s per epoch on the M4 CPU in the clean rerun, against M4A's 15 s; the 15-epoch job is ≈262 s against M4A's 223 s (+18%). About 10× faster on MPS (informational).

**Recommendation.**
- Keep the M4A configuration: 15 fixed epochs, CPU, 2 seeds.
- Report zero-width interval frequency as a diagnostic.
- MPS only as a separately approved variant.

**Status.** RECOMMENDED_NOT_APPROVED.

## D11 — Resource ceilings

**Evidence** (evidence C):
- Updated pilot totals on the M4 host:

| Scenario | Total |
|---|---|
| Optimistic | 1,449 s |
| Expected | 1,756 s |
| Conservative (×3) | 4,450 s |

  These rows use M4A's per-job compute plus measured real-data preparation, and 7 λ per linear fit. With the clean-rerun compute (6–18% heavier), the reviewer's recomputation gives about 1,575 / 1,915 / 4,830 s, and 9,650 s if every job retries once (INFERRED). An 8-λ grid adds about 15 s.

  These include 20 real-data preparations (about 17.8 s each) and two per-seed linear fits (51.7 s each).
- Per-job peak RSS is 0.53–0.61 GiB on synthetic data (546–625 MiB) and 0.69 GiB for the real loader with V2 preparation.
- **No per-job timeout, total budget, per-job RSS limit or one-job-per-process exists in the runner** (OBSERVED). `max_rss_bytes` checks the cumulative process high-water mark only between jobs.

**Recommendation.**
- A parent driver runs one job per subprocess, serially. It kills on timeout, samples child RSS and records child `ru_maxrss`.
- Per-job timeouts including data preparation:

  | Job | Timeout (s) |
  |---|---|
  | SSL | 300 |
  | Neural downstream | 600 |
  | TCN | 1,800 |
  | Linear per seed | 600 |

- 2 GiB per-job RSS kill ceiling. The 4 GiB between-job check is a backstop only.
- 7,200 s total budget enforced by the driver.
- `torch.set_num_threads(4)` plus `OMP_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` set to 4; record observed threads.
- 1 GiB storage reservation.
- Remeasure on the owner's host before execution: thread sweep, sustained thermals, real preparation time, kill and retry paths.

**Risks.**
- On an 8 GB fanless host, conservative ×3 is plausible.
- Concurrency slowed jobs 1.4–2.2×.

**Status.** RECOMMENDED_NOT_APPROVED. Enforcement is BLOCKED_ON_EVIDENCE until a driver exists and is tested.

## M5-FAIL — Failure and retry handling

**Evidence.**
- Failed `StagedRun` jobs are terminal. Crashed or interrupted jobs re-run on every resume with **no attempt cap**. A timeout kill has no defined ledger outcome (evidence C).
- SSL artifact identity includes wall time (evidence B).

**Recommendation.**

| Class | Examples | Retry | Outcome |
|---|---|---|---|
| Infrastructure | Process killed by OS, I/O error, host sleep | ≤ 1, identical seed/config/code/thread/host, logged with attempt number | Second failure means INCOMPLETE |
| Resource exhaustion | Timeout or RSS kill | ≤ 1 identical retry, only if attributable to host contention (logged); otherwise none | Record limit, elapsed time and peak |
| Numerical | Nonfinite loss/gradient/prediction, crossing native quantiles | None | Model failure; recorded and reported |
| Scientific validation | Cohort/containment/provenance/reload-parity failure | None | Stop the pilot; investigate |
| Missing data | Inventory not 123/123 (or not 92/92 May–July), hash mismatch | None | Stop before any fit |
| Nonconvergence | Classical candidates | n/a (classical excluded) | — |
| Configuration mismatch | Fingerprint or plan drift on resume | None | Stop; new run identity |

Further rules:
- Partial artifacts are quarantined, never reused.
- An SSL retry re-runs J **and** frozen J for that seed.
- Failed seeds are reported. Results with any missing primary job are labelled INCOMPLETE and never silently reduced to complete pairs.
- Resume is allowed only for an identical plan, code and data identity.

**Retry bias.** Retries can bias results if they are triggered by observed performance. Allow them only on classified non-scientific failures, before any metric is inspected.

**Status.** RECOMMENDED_NOT_APPROVED. The attempt cap and timeout ledger outcome are BLOCKED_ON_EVIDENCE (not implemented).

## M5-CLASSICAL — Classical baseline policy

**Evidence.**
- Classical fit acceptance is `POLICY_UNAVAILABLE` (M4B). V1 volatility accepts non-converged maxima (V1 audit F04).
- `persistence_empirical` is deterministic and bitwise-repeatable (OBSERVED).

**Recommendation.**
- Include `persistence_empirical` (quantiles, pinball-scorable) and point persistence.
- Fit each once, then replicate under both seed labels with `independent_seed_runs=False`. Never count them as seed replicates.
- Declare that they use all unique training bins, not the 20,000-window subset.
- Exclude ARIMA and volatility models from M5 comparisons until an acceptance policy exists. They may run as labelled diagnostics only.

**Status.** RECOMMENDED_NOT_APPROVED.

## M5-STATS — Descriptive-only statistical reporting

**Evidence.**
- M3.1 verdict NO_VALIDATED_REPLACEMENT.
- M4B `descriptive_comparison` returns `DESCRIPTIVE_ONLY` / `INFERENCE_UNAVAILABLE`, with all interval, p-value and bootstrap fields null (OBSERVED).
- `paired_comparison` still emits percentile CIs and accepts 2 seeds. A synthetic null with 2 seeds × 10 days gave 52.7% coverage of a nominal 95% interval (evidence D).
- `publish_development` accepts arbitrary JSON.
- Protocol §7 still prescribes percentile CIs.

**Recommendation.**

*Permitted reporting:*
- Report only through `descriptive_comparison` and `descriptive_budget_table`.
- Do not use `paired_comparison`, `run_v1` or `block_bootstrap` for pilot reporting.
- May report: wall time, RSS, completion and failure ledger, selected epochs and λ, reload parity, storage, identities, realized per-model × seed post-selection validation losses, and per-seed paired differences shown as both values.

*Mandatory header:* "DEVELOPMENT FEASIBILITY PILOT — DESCRIPTIVE ONLY — INFERENCE_UNAVAILABLE (M3.1 NO_VALIDATED_REPLACEMENT); exposed May–July 2024; post-selection validation losses; n = 2 seeds; one fold."

*Must not appear:* significant, CI, 95%, p =, ±, SE, outperforms, improves, robust, generalizes, consistent across seeds, wins 2/2, test, holdout, sealed, untouched, fresh, validated.

*Inference regimes:*
- **Seed-conditional:** fixed data, seed varies.
- **Calendar-conditional:** fixed seed, time varies.
- **Joint:** both vary.

Keep these three distinct. **None is supported by 2 seeds × 1 fold × 10 days** (about 100–110 effective validation units, INFERRED).

*Optional engineering:* `publish_development` could reject non-null interval or p-value fields.

**Status.** RECOMMENDED_NOT_APPROVED. Any future inference requires a separately validated method (D12/D13).
