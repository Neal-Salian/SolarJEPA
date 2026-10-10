# SolarJEPA V2 compute feasibility (M4A)

Date: 2026-10-10. Branch `feat/v2-training-protocol-feasibility` (base `1826400`).
Companion documents: [training protocol](V2_TRAINING_PROTOCOL.md), [baseline audit](V2_BASELINE_AUDIT.md),
[M4B handoff](V2_M4_INTEGRATION_HANDOFF.md).

**Everything measured here used synthetic data on one host.** Measurements are
OBSERVED. Projections are EXTRAPOLATED from them and labelled as such. No real-data
training and no full schedule was run. Earlier figures (0.19 s/step TCN, TCN ≈4.6×
slower than supervised, 0.46 GB peak) are treated as historical observations and were
re-measured below.

## 1. Environment (OBSERVED)

| Item | Value |
|---|---|
| Hardware | Apple M4 (`Mac16,12`), 10 cores (4 performance + 6 efficiency), 16 GiB unified memory |
| OS | macOS 26.3.1 arm64 |
| Python / frameworks | Python 3.13.7, torch 2.6.0, numpy 2.2.6 (repository `.venv`) |
| Device / precision | CPU, float32. `torch.use_deterministic_algorithms(True)` (set by `_setup`). MPS available; measured informationally only (§3.3) |
| Threads | 4 Torch threads for jobs (protocol value). Microbench at 1/4/8 |
| Host differs from the earlier design host | The V2 design docs record a Mac14,2 with 8 GiB. Numbers here do not transfer to it |

## 2. Method

Harness: [`scripts/benchmark_v2_feasibility.py`](../scripts/benchmark_v2_feasibility.py).

- **Workload.** A deterministic synthetic two-channel 1-minute positive series (log-AR(1) plus bursts), complete masks,
  with the **V1 GOES dimensions**: 82-day training partition, 10-day validation partition, 120-min context,
  30-min horizon, stride 30. This gives 117,931 eligible training windows, capped at **20,000**
  (79 steps/epoch at batch 256), and 476 validation origins. No test partition is built.
- **Configurations.** The proposed architectures from
  [`training_protocol_proposal.json`](../configs/v2_proposed/training_protocol_proposal.json): V1 JEPA architecture,
  proposed TCN, quantile-linear with 5 λ. Train and select on `dex_pinball_equal_channel_v2`, diagnostic `normalized_pinball_v1`.
- **Short schedules.** 1 SSL epoch, 1 warmup epoch, 2 downstream epochs, 2 linear epochs per λ.
- **Isolation.** Each job runs in its **own subprocess**, so `ru_maxrss` is a per-job peak. JEPA arms reuse the
  `ssl` job's saved artifact, as the protocol does.
- **Warm-up.** Downstream phases ran 2 epochs; epoch 1 includes one-off warm-up costs.
  The microbench discards 5 warm-up steps and times 30.
- **Measurement.** Epoch wall times come from the model records. They include validation for both metrics and
  the per-epoch monitor. The microbench times forward + backward + clip + AdamW on a fixed random batch,
  with no data loading or validation. Checkpoint sizes come from `QuantileForecaster.save` and `PretrainingArtifact.save`.
- **Runs.**
  - Run A: a scratch run, not committed, with the same settings.
  - Run B: [`docs/evidence/v2_m4a_compute_benchmark_apple_m4.json`](evidence/v2_m4a_compute_benchmark_apple_m4.json).
  - Run C: a quiet rerun of the TCN job and microbench, [`…_quiet_rerun.json`](evidence/v2_m4a_compute_benchmark_apple_m4_quiet_rerun.json).
  - Run D: MPS microbench, [`v2_m4a_microbench_apple_m4_mps_informational.json`](evidence/v2_m4a_microbench_apple_m4_mps_informational.json).
- **Contention disclosure.** Short targeted pytest runs (≤5 s) overlapped Run B's TCN job and microbench. Run B's 4-thread
  microbench was 0.043 s/step against 0.028 in Runs A and C, and its TCN epochs were 16.5–17.2 s against 14.7–15.4 s.
  Run C was taken on an otherwise idle machine and agrees with Run A. **Run C supersedes Run B for those two jobs.** All other jobs agree
  across A and B within about 3% except S epoch 1 (3.52 vs 2.81 s, warm-up).
- **Script versions.** Runs A–C used the harness before the opt-in `--micro-devices` option was added.
  The CPU code path is unchanged.

Reproduce:

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_v2_feasibility.py --out results/v2_m4a/benchmark.json
```

## 3. Measured results

### 3.1 Per-job (4 threads, 20,000 windows, 79 steps/epoch)

| Job | Epoch wall times, s (Run A / Run B) | Steady s/epoch | s/step incl. validation+monitor | Peak RSS (MiB) | Checkpoint |
|---|---|---|---|---|---|
| SSL (1 epoch) | 2.62 / 2.65 | ≤2.65 (single epoch, incl. warm-up) | 0.034 | 617 / 614 | 744,386 B |
| J downstream | 2.38, 2.36 / 2.69, 2.41 | 2.36–2.41 | 0.030 | 630 / 645 | 750,018 B |
| S downstream | 3.52, 2.57 / 2.81, 2.34 | 2.34–2.57 | 0.030–0.033 | 642 / 642 | 748,418 B |
| B warmup / downstream | 2.37 / 2.37, 2.37 · 2.31 / 2.35, 2.37 | 2.31–2.37 | 0.030 | 636 / 628 | 749,634 B |
| Frozen JEPA (head only) | 1.77, 1.75 / 1.78, 1.76 | 1.75–1.76 | 0.022 | 583 / 585 | 750,018 B |
| Frozen random (head only) | 1.74, 1.73 / 1.76, 1.75 | 1.73–1.75 | 0.022 | 570 / 569 | 748,418 B |
| TCN | 14.88, 15.35 (A) · 14.66, 14.86 (C) | 14.7–15.4 | 0.186–0.194 | 664 (A) / 644 (C) | 191,874 B |
| Quantile-linear (5 λ × 2 epochs) | per-λ 2-epoch fits 0.145–0.19 s (first λ 0.41 s) | 0.073–0.095 per λ-epoch | — | 566 / 569 | 296,408 B |

Common to all jobs:

- Synthetic data generation and windowing take **5.4–5.7 s per job**.
- Process RSS is 177 MiB after imports and **486 MiB after data**. Training adds 80–180 MiB.
- Inference on the 476 validation origins takes 0.17 s for the JEPA family, 0.35–0.37 s for the TCN and 0.13–0.15 s for linear.

### 3.2 Isolated step microbench (CPU, batch 256; median of 30 after 5 warm-up)

| Model (trainable params) | 1 thread | 4 threads (Runs A / C) | 8 threads |
|---|---|---|---|
| JEPA full fine-tune (136,332) | 0.0705 | 0.0281 / 0.0275 | 0.0337–0.0341 |
| JEPA head only (67,948) | 0.0294 | 0.0116 / 0.0112 | 0.0141–0.0148 |
| TCN (44,620) | 0.258 | 0.212 / 0.210 | 0.241–0.251 |
| Quantile-linear (72,300) | 0.0012 | 0.0008 | 0.0010–0.0012 |

The microbench shows four things:

- **4 threads is fastest for every model.** 8 threads is slower, consistent with 4 performance cores (INFERRED).
- **The TCN barely benefits from threads.** It is 1.2× faster from 1 to 4 threads.
- **The TCN costs 7.6× a full fine-tuning step** in isolation (0.210/0.0275).
- **Per epoch, including validation and monitoring, the TCN costs about 6.3× S** (14.86/2.34). The historical 4.6× was measured
  on a smaller workload (7,000-minute series, 4,851 windows, 19 steps/epoch), where fixed validation/monitor overhead weighs more.
  The historical **0.19 s/step reproduces** (0.186–0.194 here).

### 3.3 MPS (informational, Run D; not proposed for protocol use)

| Model | MPS median s/step | CPU 4-thread |
|---|---|---|
| JEPA full fine-tune | 0.0331 | 0.0275 |
| JEPA head only | 0.0166 | 0.0112 |
| TCN | **0.0201** | 0.210 |
| Quantile-linear | 0.0057 | 0.0008 |

MPS makes the TCN about 10× faster and makes everything else slower. Two consequences:

- Running only the TCN on MPS would cut its cost from about 4 minutes to well under 1 minute per job. But it would put one model
  on a different numerical backend. Determinism guarantees and the `use_deterministic_algorithms` behaviour on MPS were not
  verified.
- It would therefore require explicit approval and a declared reproducibility caveat. **Not proposed.**

### 3.4 Memory

- **Per-job peak RSS is 0.55–0.65 GiB** on V1-sized data (OBSERVED).
- **The proposed 4 GiB ceiling leaves at least 6× headroom.**
- About 75% of the peak is the data/window arrays. Real data adds NetCDF decoding for 123 files (≈36.5 MB on disk). V1
  documented 0.56 GB peak for its strict run on another host.
- Real-data peak is UNKNOWN until the pilot. Batch-256 activations are not the bottleneck at these sizes.

## 4. Per-job projections

EXTRAPOLATED, M4 host, proposed schedule. Each phase is projected as first epoch + (N−1) × last epoch, and data preparation is counted once.
These are the harness's `projection` field, with the TCN taken from Run C.

| Job | Projection (s) | Notes |
|---|---|---|
| SSL phase (8 epochs) | **≈21** | 8 × single measured epoch (conservative) |
| J downstream (15 epochs) | **≈42** | + shared SSL 21 ⇒ J total ≈63 |
| S | **≈41** | |
| B (8 warmup + 15) | **≈59** | |
| Frozen JEPA | **≈32** | SSL shared with J, not repeated |
| Frozen random | **≈32** | |
| TCN (15 epochs) | **≈228** (Run C) to 253 (Run B, contended) | dominant cost |
| Quantile-linear, 7 λ × 100 epochs | **≈57–72** | 7.3–9.4 s per λ |

Implied J/B wall-time ratio ≈ 63/59 ≈ **1.07** on synthetic data (INFERRED). That is below the proposed H5 1.10
threshold, but close enough that real-data overhead or monitoring differences could cross it. The pilot must measure it.

## 5. Study and pilot totals

Scenarios (all EXTRAPOLATED):

- **Optimistic** = §4 values.
- **Expected** = ×1.25, for real NetCDF loading, I/O, thermal throttling and larger 29-day validation partitions (≈1,392 origins against 476).
- **Conservative** = ×2, for a slower or 8 GiB host, sustained throttling, and one infrastructure retry on ~10% of jobs.

### 5.1 Two-seed feasibility pilot (proposal §8: 2 SSL, 12 downstream, 1 linear fit, 4 loss-comparison jobs)

| Component | Optimistic (s) |
|---|---|
| 2 SSL | 42 |
| J, S, B × 2 | 84 + 82 + 118 |
| Frozen JEPA / random × 2 | 64 + 64 |
| TCN × 2 | 456 |
| Linear (7 λ) | 57 |
| Loss comparison (J, S × 2 with V1 loss) | 166 |
| **Total** | **≈1,130 s ≈ 19 min** |

Expected is ≈24 min and conservative is ≈38 min. The proposed 2 h pilot wall budget gives about 3× margin over conservative.

### 5.2 Proposed main study (protocol: 3 folds; J/S/B × 20 seeds; frozen/random/TCN × 5 seeds; 60 SSL)

| Component | Jobs | Optimistic (s) |
|---|---|---|
| J (incl. own SSL) | 60 | 3,780 |
| S | 60 | 2,460 |
| B | 60 | 3,540 |
| Frozen JEPA | 15 | 480 |
| Frozen random | 15 | 480 |
| TCN | 15 | 3,420–3,795 |
| Linear (7 λ) | 3 | 171–216 |
| **Total** | | **≈14,300–14,750 s ≈ 4.0–4.1 h** |

Expected is ≈5.1 h and conservative is ≈8.2 h serial on this host.

- This sits inside the design's 8–16 h reservation and 24 h stress ceiling.
- Classical models (ARIMA/volatility) and analysis are **not** included. They were not benchmarked here; the design reserved 0.2–2 h.
- **The TCN is about 25% of the main study and about 40% of the pilot from only 15 (or 2) jobs.** It is the main bottleneck.

### 5.3 Storage (EXTRAPOLATED from measured checkpoint sizes)

| Item | Estimate |
|---|---|
| Selected checkpoints: 210 JEPA-family × 0.75 MB + 15 TCN × 0.19 MB + 3 linear × 0.30 MB | ≈161 MB |
| SSL artifacts: 60 × 0.74 MB | ≈45 MB |
| Validation predictions, float64 point + 5 quantiles: 2,880 B/origin/model × ~1,392 origins × 84 instances × 3 folds | ≈1.0 GB |
| Test predictions (design estimate, DOCUMENTED) | ≈0.97 GiB |
| Pilot total (checkpoints, records, validation predictions) | < 50 MB |

Keep only selected and SSL states, not per-epoch checkpoints. The design's 0.25 GiB checkpoint reservation suffices.

## 6. Bottlenecks and recommended execution limits

1. **TCN CPU cost.** Run TCN jobs last in the interleaved schedule. Use the proposed 1,800 s timeout. Thread scaling
   gives little, so do not raise threads for it. MPS would help but requires approval (§3.3).
2. **Threads.** Keep 4. 8 threads was slower for every model on this host. Re-check on any other host with the microbench
   before the pilot (`--jobs microbench`).
3. **Serial execution, one job per process.** This gives per-job RSS and avoids process high-water contamination. `StagedRun(max_rss_bytes=4 GiB)` stays as the
   between-job guard.
4. **Timeouts** (proposed): SSL 300 s, neural downstream 600 s, TCN 1,800 s, linear 1,800 s. That is about 5–8× the
   expected values.
5. **Pilot wall budget** 2 h. **Main-study reservation:** keep the design's 8–16 h, stress ceiling 24 h.
6. **Avoid measurement contamination.** No other CPU-heavy work during timed runs. Run B shows that even a 5 s pytest run
   inflates TCN epochs by about 10%.
7. **Re-measure on the execution host.** This host is not representative of the 8 GiB design host or any server.
   The pilot replaces these extrapolations with measurements.

## 7. Limitations

- The data are synthetic. Real flux has gaps (fewer eligible windows, though still above the 20,000 cap), and real
  loading costs differ. The selection behaviour of the models on synthetic data says nothing about real data.
- Only 1–2 epochs were timed per phase. Long-run thermal throttling was not measured.
- RSS is the per-process high-water mark. Children are excluded.
- Classical models, bootstrap analysis and artifact streaming were not timed.
