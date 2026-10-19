# V2 controlled pilot — results on the M4 (2026-10-19)

**DEVELOPMENT FEASIBILITY ONLY — EXPOSED MAY–JULY 2024 — POST-SELECTION VALIDATION — ONE FOLD / TWO SEEDS — DESCRIPTIVE ONLY — INFERENCE UNAVAILABLE (M3.1 NO_VALIDATED_REPLACEMENT)**

Machine record: [`evidence/phase2_v2_m4_pilot_results_20261019.json`](evidence/phase2_v2_m4_pilot_results_20261019.json).
Preparation: [M4 host preparation](PHASE2_V2_M4_HOST_PREPARATION_20261019.md).

## Execution

- **Pilot COMPLETE: 20/20 jobs succeeded** (2 SSL + 18 selected models), one attempt each, zero retries, no resume, published atomically. Test release false.
- **Time:** 3,014.8 s total (50 min) of the 7,200 s budget, including preparation and finalization. Peak sampled job RSS 0.94 GB (cap 2 GiB). CPU float32, 4 threads.
- **Authority:** owner approval by Veer Shetty for this changed environment, reservation `SolarJEPA-G4-M4-20261019-01`; all 15 pre-launch gates passed; binding `37ee71f4…`.
- **Host:** Mac16,12 (Apple M4, 16 GiB), macOS 27.0.1, Python 3.13.7, from `codex/v2-experimental-validation-readiness` @ `1c5b699`. Seed-2 jobs ran 1.3–2.6× slower than seed 1 (consistent with thermal throttling on this fanless machine; not measured directly).

## Validation results (mean dex pinball over 412 origins × 30 leads × 2 channels; lower is better)

| Model (primary cohort) | Seed 1261866429 | Seed 1291916211 |
|---|---|---|
| JEPA fine-tuned (J) | 0.04767 | 0.04676 |
| Supervised (S) | 0.04682 | 0.04689 |
| Supervised + extra updates (B) | 0.04626 | 0.04642 |
| JEPA frozen encoder | 0.05113 | 0.04922 |
| Random frozen encoder | 0.06762 | 0.06842 |
| TCN | 0.04690 | 0.04724 |
| Quantile-linear (selected λ = 0) | 0.05157 | 0.05347 |

## Fixed comparisons (A − B; negative favours A; per-seed values shown, no intervals)

| Comparison | Mean difference | Per seed |
|---|---|---|
| J − S | +0.00036 | +0.00085, −0.00013 |
| J − B (step-matched control) | +0.00087 | +0.00141, +0.00034 |
| J − TCN | +0.00014 | +0.00077, −0.00048 |
| J − quantile-linear | −0.00530 | −0.00390, −0.00671 |
| J − JEPA frozen | −0.00296 | −0.00346, −0.00246 |
| JEPA frozen − random frozen | −0.01784 | −0.01649, −0.01920 |
| B − S | −0.00051 | −0.00056, −0.00046 |
| Alternate loss (normalized pinball): J − S | +0.00062 | +0.00114, +0.00010 |

## What this does and does not show

- **Pipeline:** the full guarded pipeline runs end to end on real data within every resource limit.
- **Representation:** the pretrained JEPA representation carries real information. Frozen JEPA beat a frozen random encoder by about 0.018 dex in both seeds.
- **Pretraining value:** in this pilot, JEPA pretraining did **not** improve on matched supervised training. Fine-tuned JEPA was on average slightly worse than supervised (+0.0004 dex) and than the step-matched extra-updates control (+0.0009 dex, both seeds). Its gap to S and TCN changes sign across seeds.
- **Size of differences:** all J/S/B/TCN differences are below 0.001 dex, at about 1–2% of the loss level, and comparable to seed-to-seed variation.
- **No inference:** two seeds, one 10-day exposed validation fold and post-selection losses support no statistical, generalization or operational claim. No intervals or p-values are reported, by protocol.
- **Comparability:** results are not bitwise comparable to any M2 run. Thread count and CPU affect weights.
