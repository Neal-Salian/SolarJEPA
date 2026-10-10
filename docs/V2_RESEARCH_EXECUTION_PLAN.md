# SolarJEPA V2.1 research execution plan

Date: 2026-10-10, Asia/Kolkata. Base origin/v1 644648f7d555fcbcb3eed4495d37fecffdd1863a; branch research/v2-independent-validation. **PROPOSED — REQUIRES APPROVAL.** This plan documents later work; it executes no training or acquisition. The [experimental protocol](V2_EXPERIMENTAL_PROTOCOL.md) is the scientific contract.

## Ordered milestones and gates

| Milestone | Dependencies / ordered work | Verification and deliverable | Stop/go criterion |
|---|---|---|---|
| M0: decisions and access | Approve protocol choices; obtain both contributors' candidate-exposure attestations; appoint test custodian and freeze access/report rules | Signed/versioned decision and exposure ledger, calendar, primary estimand, seeds, resource ceiling | Stop on UNKNOWN freshness unless explicit conditional retrospective scope is approved; no untouched claim from absent manifests |
| M1: validation foundation | Implement versioned V2 runner/loss, explicit stage schedules, accepted-fit selection, streamed artifacts and paired statistical analysis; preserve V1 defaults/configs | Synthetic split/mask/normalization/teacher-isolation tests; known-loss dex-weighting check; deterministic seed/stage counts; failed-fit/seed cases; bootstrap paired/calendar/count tests; installed CLI checks | No new scientific data required. Full relevant tests and normal installation pass; code/config manifests frozen; no test outcomes loaded by fitting/selectors |
| M2: exposed-data feasibility | Existing V1 May–August 2024 partitions only; first two protocol seeds, all six neural arms, fixed linear/classical grids; estimate RAM/time; check block-length assumptions and fit acceptance | Pilot histories, measured RSS/time/storage and development-only statistical/Monte Carlo diagnostics; revised precision/compute prediction | No significance-seeking tuning. Any decision change creates a new pre-test protocol version; stop if peak RSS>4 GiB or resource reservation cannot cover the fixed study |
| M3: approved bounded acquisition | After M0/M1/M2; nine monthly GOES-16 configs/manifests, train/validation opened, tests held by custodian | 276 nominal daily identities; measured UTC/units/schema/flags/QC, manifest hashes, common-origin cards, access log | No data acquired now. Stop on unavailable/version-incompatible files or QC gates; no silent replacement/imputation. Any calendar amendment precedes score access |
| M4: locked fitting | All three folds, full fixed seed list; classical/linear candidates use train/validation only; J/S/B20, frozen/random/TCN5 per fold | Immutable selected/pretraining checkpoints, phase/RNG/config hashes, every fit/failure/warning and validation-selection table | Freeze all folds' selections before any test release; unresolved primary failure means primary incomplete, not reduced cohort |
| M5: one confirmatory release | Custodian verifies locks, opens all tests for context-only prediction; no online refitting | Aligned per-origin point/five-quantile outputs, masks, seed/fold/model IDs, checksums and access timestamps | Reject any changed fitting inputs/config or dropped origin. Technical same-artifact inference reruns are logged; scientific revisions become exploratory |
| M6: frozen analysis | Run primary crossed intervals, seven secondary slots and all prespecified sensitivity/negative reporting | Effect/uncertainty/seed/fold/calibration/lead tables; convergence/failure/resource appendix; artifact index | Report weak/negative/inconclusive results. No added seeds, dates, horizons or bootstrap choices to obtain significance |
| M7: independent reproduction and writing | Other contributor creates clean pinned environment; replay all principal metrics/checkpoints; repeat J/S/B for the first protocol seed in the 2020 fold from scratch after authorization | Reproduction report separating saved inference, training and conclusions; manuscript claim/evidence matrix | No submission claim beyond measured scope. Missing artifacts, failed repeat or weak inference remains a disclosed limitation |

M0/M1 are the recommended next implementation milestone after review, bounded to **protocol validation on synthetic/exposed data**, without candidate holdout access. Do not begin them in this documentation task.

## Fit and update accounting

The main-study counts assume three eligible folds and the protocol's fixed grid; they are plans, not executed measurements. M2 development and M7 reproduction are accounted for separately below.

| Work | Count |
|---|---:|
| J/S/B downstream jobs | 3 arms ×20 seeds ×3 folds =180 |
| Frozen JEPA / frozen random / TCN downstream jobs | 3 arms ×5 seeds ×3 folds =45 |
| Total neural downstream jobs | 225 |
| JEPA pretraining phases | 20 seeds ×3 folds =60; reuse 15 of these for frozen-head runs |
| Extra supervised warmup phases | 20×3=60, within the 180 core jobs |
| Quantile-linear candidates | 5 λ ×3 folds =15 joint fits, not 4,500 independent scalar fits |
| ARIMA candidates | 4 orders ×2 channels ×3 folds =24 initial channel fits, ≤48 including one retry |
| Variance optimizations | Default+grid: constant 2, ARCH 4, GARCH-N 7, GARCH-t 7, GJR-t 6 =26 starts/channel; 52/fold; 156 initial; at most 10 fixed interior retries/fold, thus≤186 total |
| Empirical persistence | 1 joint two-channel fit/fold =3 |

Classical optimizer attempts are not separate reported forecast models. There are≤234 ARIMA/variance optimizer attempts in total, plus three empirical-persistence fits. Test only the validation-selected accepted ARIMA, all five volatility variants (including unavailable failures), empirical/point persistence and selected linear model. There are 75 neural forecast instances/fold (60 core +15 diagnostic), plus nine non-neural models =84 total. The storage budget below uses 84, with failures retained in metadata. Selected variants are not chosen by test score.

M2 adds 12 development downstream jobs (six arms×two seeds), two shared SSL phases, two B warmups, five joint linear fits, ≤78 classical optimizer attempts and one empirical fit. Reuse the first two J SSL states for frozen JEPA. Its three additional simulation configurations add 15 development forecast variants without refitting; store them under a separate V2-development namespace, preserving old V1 outputs. M7 adds three J/S/B reproduction jobs, one SSL phase and one B warmup. Neither stage contributes extra independent primary seeds or changes the 225-job main study.

At 20,000 windows, 79 batches/epoch: 632 SSL, 1,185 downstream and 1,817 B supervised updates. Across 225 downstream jobs and 60 SSL/60 warmup phases there are 342,465 optimizer updates, with different cost/updated-parameter sets. Linear fits add their own 100×79×15=118,500 cheap affine updates. This is step accounting, not equal FLOPs.

## Compute, RAM and storage

**OBSERVED:** sysctl reports Mac14,2, 8,589,934,592 bytes RAM (8 GiB), arm64; Python 3.13.3. Saved V1 uses CPU/Torch 4 threads. Its nine neural record.wall_seconds sum 829.674 s (13.83 min); individual fits 54.845–130.626 s, with early stopping. Its strict run timestamps span 18.44 min. Fixed full schedules, new models/data and artifact streaming have not been timed; these are not new benchmark results.

**INFERRED planning reservation:** 5.6–8.1 CPU hours for the proposed core/frozen schedules from recorded epoch/overhead timings; add roughly 0.3–2 h for 15 small TCN fits and 0.2–2 h for linear/classical/analysis. Reserve **8–16 serial CPU hours** for the main study, stress ceiling 24 h excluding installation/acquisition/development/reproduction; validate on M2 first. Separately reserve 1–4 h for M2 and 1–2 h for M7 replay/repeat, with actual costs unknown until measured. The proposed ceilings require approval. If infeasible, revise scope before test release rather than selectively omit hard seeds/folds. No GPU/MPS is assumed.

Serialize jobs and free arrays between models. Proposed process RSS gate 4 GiB, leaving room for OS/unified memory; actual peak is UNKNOWN until M2. Record RSS externally, wall time, hardware, threads, failed allocation and sustained thermal behavior. Do not infer RAM feasibility from disk size. TCN activations/batched loss evaluation must remain bounded. Existing V1 stores all model outputs in memory; streamed per-model outputs are a future validation-foundation requirement.

Nine new monthly selections contain 276 nominal daily files. V1's 36,535,474 bytes/123 files extrapolates to about 82 MB; candidates have not been downloaded or measured. Inherited 1 MiB/file caps imply ≤276 MiB raw flux under those caps, before documentation/catalog/transfers.

For point plus five quantiles in float64, each origin/model needs 30×2×6×8=2,880 bytes. Allocating this full slot to all 84 forecast instances/fold at 4,308 maximum total test origins gives a conservative **1,042,191,360-byte (~0.971 GiB)** uncompressed budget, before target/mask/metadata and validation outputs. Point-only persistence uses less; its unused quantile allocation is a budget allowance, not fabricated measurements. Compression is not assumed. V1 checkpoints are about 0.75 MB each; reserve ~0.25 GiB for selected/checkpoint-sharing artifacts, with actual TCN/optimizer-state sizes verified later. Keep only selected downstream and shared pretraining states plus resumable current-job state, not every epoch permanently.

Reserve 5 GiB for new outputs and 10 GiB free working space, excluding old artifacts; use measured M2 sizes to amend before acquisition. Store raw bytes, arrays, checkpoints and generated results under existing ignored policies. Track small configurations/manifests/reproduction code only in a separately authorized implementation milestone. Archive immutable artifacts with hashes outside Git before paper submission.

## Required verification and stop rules

- No random splitting, cross-fold normalization or later-fold warm starts. Inspect full context/target/dependency support and selected training indices.
- Validate exact paired initial weights and downstream order, equal-dex training/selection, fixed schedules and forecast-only inference.
- Verify quality masks/origin identities independently of model success. Keep every prespecified seed/model failure visible.
- Verify statistical sums/counts with unequal day counts and missing days; bootstrap draws shared across paired models/seeds; no outer-fold population bootstrap.
- Check staged paths and data ignores at each later publication. Preserve source/config/data/artifact identities and a full dependency inventory.
- Stop before test access if exposure, scientific thresholds, resources or ownership are unresolved. Stop broad claims if a period lacks a claimed activity regime or dependence invalidates uncertainty.

Acquisition/QC, model fitting and independent analysis can be assigned separately after shared decisions freeze. All test access, primary estimand/multiplicity, quality changes and publication claims require coordination. See [independent work plan](V2_INDEPENDENT_WORK_PLAN.md).
