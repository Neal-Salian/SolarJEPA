# SolarJEPA V2 M5 — resource, fairness and baseline review

Date: 2026-10-11. Branch `research/v2-m5-protocol-review`. Evidence sections B (experiment design) and C (compute) of
[`docs/evidence/v2_m5_protocol_review_evidence.json`](evidence/v2_m5_protocol_review_evidence.json).
Decisions: [register](V2_M5_EXPERIMENTAL_DECISION_REGISTER.md). Nothing here is approved.

**Evidence basis.** Measurements are synthetic or come from committed real-data evidence (OBSERVED on an Apple M4, 16 GiB). Projections are INFERRED.
No real-data training was run.

## 1. Training fairness

### 1.1 Update accounting at 20,000 windows, batch 256

Batches use ceiling division: 79 steps per epoch, with a last batch of 32. The formula was verified on synthetic runs, including a tiny fixture at 76 windows and batch 16, which gives 5 steps per epoch.

| Arm | Encoder+predictor updates | Head updates | Window presentations | Trainable parameters |
|---|---|---|---|---|
| J `jepa_finetune` | 632 SSL + 1,185 = **1,817** | 1,185 | 460,000 | 136,332 |
| B `supervised_extra_updates` | 632 warmup + 1,185 = **1,817** | **1,817** | 460,000 | 136,332 |
| S `supervised` | 1,185 | 1,185 | 300,000 | 136,332 |
| Frozen JEPA | 632 (shared SSL) + 0 | 1,185 | 460,000 (SSL attributed) | 67,948 head |
| Frozen random | 0 | 1,185 | 300,000 | 67,948 head |
| TCN | 1,185 (all weights) | — | 300,000 | 44,620 |
| Quantile-linear | 7,900 per λ (100 epochs) × 8 λ per seed | — | 2,000,000 per λ | 72,300 |

The J/B step counts match M4A's report. B's head receives 632 more updates than J's.

**Recommended report terminology:**
- J vs B: "step-matched encoder/predictor update opportunities (1,817 each); B's head receives 632 additional updates; not FLOP-, objective- or compute-matched."
- TCN and linear: "same training windows, normalization and validation support; not capacity-, step- or compute-matched."
- Never write "equal compute" or "fair budget" without naming the matched dimension.

### 1.2 Data equality

All arms share training rows, normalization, the 20,000-window subset and validation support (OBSERVED on synthetic runs; the real-data equivalent follows from the same code but was not executed).

M4B's validation **content** fingerprint is effective. Doubling validation values while keeping origin IDs leaves M4A's origin fingerprint unchanged, but both `check_paired_cohort` and M4B `check_comparator_cohort` reject the cohort.

`check_comparator_cohort` does not bind thread count or seed for TCN/linear.

### 1.3 Selection opportunities and cost attribution

**Selection opportunities:**
- Neural arms: 15 checkpoints each (earliest minimum).
- Linear: 8 λ at the final epoch (recommended grid).

Selected validation losses are optimistic and must be labelled post-selection. The V1-loss comparison cohort must not become an extra selection step: the primary objective is declared before fitting.

**Cost attribution.** Frozen JEPA reuses J's SSL artifact, so SSL wall time is attributed once. `attributed_training` must not be summed across J and frozen J.

## 2. Loss and checkpoint selection

Results are OBSERVED from evidence B.

| Property | Result |
|---|---|
| Units | `dex_pinball_equal_channel_v2` equals the direct dex mean pinball (difference 2.8e-17). Per-channel mean, then equal channel weight |
| Masking | NaN targets in masked cells give a finite loss and zero gradient there |
| Gradients | `gradcheck` passes |
| Train vs validation | Batched validation metric equals the one-shot metric (difference 9.5e-11) |
| Selection determinism | Earliest minimum; exact ties go to the earliest epoch. A 1e-12 difference decides, so thread-level noise can flip near-ties |
| V1 compatibility | Patience mode reproduces V1 semantics. A targeted pytest selection (14 tests covering ties, pairing, seeds, steps and λ) passed |
| Quantile ordering | J and TCN are monotone by construction. TCN spacing can underflow to exactly 0 (zero-width intervals). Linear trains on raw quantiles and is scored sorted |
| Test independence | No fit function takes a test partition. Loader-level reads are a separate issue (review R1) |

## 3. Baselines

### 3.1 TCN

Re-verified at 44,620 parameters with a 253-bin receptive field. The receptive field exceeds the 120-bin context, so the dilation-16 and 32 taps mostly read padding.

Measured in the clean rerun at 16.1–17.6 s per epoch on the M4 CPU (≈262 s per 15-epoch job), about 18% above M4A's 15 s per epoch (223 s). On MPS it runs about 10× faster (informational only).

### 3.2 Quantile-linear

**Per-seed fitting.** M4B's per-seed requirement is confirmed. Zero initialization does not make fits seed-invariant: seeded shuffling plus Adam give different weights per seed (OBSERVED).

**λ path** (real dimensions, synthetic data, 100 epochs):

| λ | 0 | 0.1 | 1 | 100 | 1e4 | 1e5 |
|---|---|---|---|---|---|---|
| Mean W² | 3.78e-3 | 2.06e-3 | 7.5e-4 | 3.4e-5 | 2.4e-7 | 6.1e-8 |
| Validation loss | 0.016739 | 0.016647 | 0.01711 | 0.02270 | 0.0303 | 0.0307 |

- The penalty gradient dominates the data-fit gradient from λ ≈ 1000. The raw crossing fraction falls from 0.245 to 0.
- The M4A grid has no value below 1, where the synthetic optimum lies.
- The second seed shifts validation loss by 2.9e-4 at λ = 0, three times the λ = 0 vs 0.1 gap.

**Options (owner decision, M5-LIN):** keep the M4A grid {0, 1, …, 10⁵}, or use {0, 0.01, 0.1, 1, 10, 100, 1000, 10000}, which covers the weak range but adds selection opportunities whose differences sit inside seed noise and partly reverses M4A's earlier removal of near-unregularized values. Either way: per seed, selected λ reported per seed. Synthetic data cannot identify the scientific optimum.

**Cost:** 7.1–7.7 s per λ per 100 epochs on the M4 (quiet), so about 59 s per seed for 8 λ.

### 3.3 Classical models

- `persistence_empirical` is deterministic (bitwise-repeatable). Replicate it under both seed labels with `independent_seed_runs=False`.
- ARIMA and volatility models are excluded while fit acceptance is `POLICY_UNAVAILABLE`: V1 accepts non-converged volatility maxima.
- Classical models use all unique training bins, not the window subset. Declare this.

## 4. Seeds and reproducibility

- All 20 seeds reproduce. The pilot uses the first two: 1261866429 and 1291916211.
- **Seeded components:** initialization; SSL and warmup order `[seed,0]`; SSL masks `seed+2`; downstream order `[seed,1]`; linear `PCG64(seed)`, which is numerically identical to `[seed,0]`.
- **Deterministic:** window subset, monitor subset, EMA teacher.
- **Not controlled:** thread count, BLAS, CPU model and torch build.

Same seed and same thread count give bitwise-equal weights across processes.

Moving from 1 to 4 threads changes all five JEPA-family arms bitwise (validation metric difference up to 2.4e-6 in a short synthetic run). TCN and linear are thread-invariant. Fix threads at 4 and record the host. Cross-host bitwise reproducibility is **UNKNOWN**.

## 5. Computational feasibility

### 5.1 Measurements

| Item | Value | Source |
|---|---|---|
| Per-epoch times vs M4A extrapolation (clean rerun) | SSL ×1.06; J ×1.10; S ×1.12; TCN ×1.18 (≈262 s vs 223 s) | C |
| Quantile-linear | 7.12–7.65 s per λ per 100 epochs | C |
| Real-data preparation per job (GOES integrity evidence) | 17.8 s `pipeline_smoke` + 1.7 s identity/time series; synthetic was 5.5 s | committed evidence |
| Peak RSS | 0.53–0.61 GiB per job (synthetic; 546–625 MiB); 0.69 GiB (real loader + V2 preparation). INFERRED 0.7–0.9 GiB per real training job | C |
| Concurrency penalty | One concurrent 4-thread process slowed epochs 1.4–2.2× and preparation 1.35–1.9× | C |
| MPS | TCN and JEPA ran with the deterministic flag; repeats bitwise-equal; CPU vs MPS parameters differed by 3e-7 to 5e-6. Not a long-run determinism proof | C |

### 5.2 Pilot totals

The pilot runs 20 processes:
- 2 SSL
- 14 neural downstream (J/S/B/frozen × 2 seeds, plus 4 loss-comparison runs)
- 2 TCN
- 2 linear

| Scenario | Rule | Total |
|---|---|---|
| M4A historical | 1 linear fit, synthetic preparation | 1,130 s |
| Optimistic | M4A per-job compute + measured 17.8 s real preparation per process | 1,449 s (24 min) |
| Expected | compute × 1.25 + 19.6 s preparation | 1,756 s (29 min) |
| Conservative | (compute + preparation) × 3 | 4,450 s (74 min) |
| Every job retried once | optimistic / expected / conservative | 2,897 / 3,513 / **8,900 s** |
| Clean-rerun compute (6–18% heavier), INFERRED | optimistic / expected / conservative / all retried | ≈1,575 / 1,915 / 4,830 / 9,650 s |

The M4A ×1.25 rationale cited 29-day validation partitions. The pilot validates on 10 days (412 origins), so that rationale does not apply; the factor is kept as a generic real-data allowance.

These totals assume the 7-λ grid. The recommended 8-λ grid adds about 15 s per pilot, which is negligible.

### 5.3 Storage

| Item | Size |
|---|---|
| 20 checkpoints and artifacts | ≈13.1 MB |
| Validation predictions (18 instances × 412 origins × 2,880 B) | ≈21.4 MB |
| Run directory | ≈40 MB |

Reserve 1 GiB.

### 5.4 Risks on an 8 GB Apple Silicon host

**Memory.** It is not the binding constraint: about 0.7–0.9 GiB per job.

**4 GiB ceiling.** It is half the machine and 4–6× the expected peak. It serves as a runaway backstop, not as protection.

**CPU and thermals.** These are binding. The design host (Mac14,2, documented as 8 GiB) is, to the reviewer's knowledge, a fanless MacBook Air. Sustained throttling over 25–75 minutes was never measured, so the ×3 conservative factor is plausible.

**Threads:**
- Only `torch.set_num_threads` is set.
- Interop threads (10) and BLAS (Accelerate) are unset.
- `JepaConfig.threads` defaults to 8, which M4A measured as slower than 4.
- The ledger records requested threads, not observed threads.

### 5.5 Enforcement audit (OBSERVED; M4B runner and safety modules, scripts)

| Proposed limit | Implemented? |
|---|---|
| Per-job timeouts (300 / 600 / 1,800 s) | **No.** `_run_job` calls `fit_fn` in-process with no timer |
| Total budget (7,200 s) | **No** |
| 4 GiB RSS | Partly. Cumulative process `ru_maxrss` is checked only after a job and only if jobs remain. Defaults to `None`. Children are excluded |
| One job per process | **No.** It exists only in the benchmark harness |
| ≤ 1 infrastructure retry | **No.** Failed jobs are terminal. Crashed jobs re-run on every resume with no cap. A timeout kill has no ledger outcome |

### 5.6 Recommended D11 values (RECOMMENDED_NOT_APPROVED)

**Driver.** A parent driver runs one job per subprocess, serially, with TCN last. It:
- kills a job on timeout;
- samples child RSS and records child `ru_maxrss`;
- writes an explicit ledger outcome for kills;
- caps retries at 1.

**Timeouts** (per job, including data preparation):

| Job | Timeout | Note |
|---|---|---|
| SSL | 300 s | |
| Neural downstream | 600 s | |
| TCN | 1,800 s | |
| Quantile-linear per seed | 600 s | revised from 1,800 s; still ≥ 2.4× conservative |

With clean-rerun compute, the TCN timeout margin over its conservative estimate falls from about 2.5× to about 2.1×.

**Other limits:**
- 2 GiB per-job RSS kill, or 2.5× the measured real peak if larger. Keep the 4 GiB between-job check as a backstop.
- 7,200 s total, enforced by the driver.
- Threads: `torch.set_num_threads(4)` plus `OMP_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` set to 4, low interop threads. Record observed threads.
- Storage reservation: 1 GiB.

**Remeasure on the owner's execution host before the pilot:**
- real preparation time and RSS with the approved May–July loader;
- 25–75 min sustained thermal behaviour;
- a 1/4/8-thread sweep;
- B, frozen and TCN epoch times;
- the J/B wall ratio (M4A estimated 1.07; not remeasured here);
- the kill and retry path end to end.
