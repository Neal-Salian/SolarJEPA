# Experiment protocol (proposed; no training authorized yet)

## Tasks and common data contract

Use calibrated SoLEXS trajectory forecasting as primary. Primary candidate
history/horizon: 6 h → 1 h at 1-minute cadence, chosen for tractable resolution
and a useful warning scale, not because skill is established. Core alternatives
are 3 h → 30 min and 6 h → 2 h. Screen history 1/3/6/12 h and horizon
30 min/1/2/6 h **one axis at a time** with cheap baselines on development data.
Do not run the full Cartesian grid. Six-hour forecasts and X+ warnings are
exploratory if event counts are low. Keep a fixed primary task before test use.

Issue forecasts every 10 minutes initially. Observation intervals end by issue
time. Target grid starts after issue time. Track valid fractions per band.
Require ≥90% valid history, no history gap >10 min and ≥95% valid targets for
continuous comparisons (provisional development choices). Do not invent event
negatives when catalogue/flux coverage is incomplete. Report exclusions by
class and period, because dropping saturated flare windows can bias results.

For fusion compare SoLEXS-only, ASPEX-only and fused models on exactly the same
eligible origins; additionally report SoLEXS on its larger standalone coverage.
Do not conflate better coverage with a model improvement. All baselines receive
the same information (GOES input allowed only in a separately labeled track).
Risk baselines include training climatology, previous-event/activity persistence
and regularized logistic regression on the same past features.

## Split and leakage controls

1. Enumerate eligible dates first. Propose contiguous chronological 60/15/10/15%
   blocks for training / tuning / calibration / final test, measured in calendar
   duration. Freeze exact UTC boundaries and dataset hash after availability
   audit; never use a random split. No dates are invented while Aditya is absent.
2. For every origin store support `[t-Lmax,t+Hmax]`, expanded by any causal
   feature lookback and label maturity time. Assign only when the full support
   is inside its partition. With Lmax=12 h and Hmax=6 h this purges at least
   18 h of origin space across a boundary; event-label maturity can require more.
3. Group full catalogue events across boundaries, including overlapping-event
   clusters and recovery intervals; drop straddling groups from both sides.
   Inspect connected groups before fixing split cutoffs. A single flare cannot
   contribute examples on both sides. Frozen-buffer sensitivity: 24/48 h.
4. Self-supervised pretraining sees only training-period future targets. No
   test-period “unlabeled” pretraining, target normalization, early stopping,
   response fitting, cross-correlation lag selection or hyperparameter choice.
5. Fit scalers, feature selections, counts-to-flux mappings and weights only on
   train. Calibrate probability/interval outputs only on calibration. Choose
   binary thresholds on tuning; lock them before testing. No test resampling to
   equalize class frequency. Report deployment prevalence.
6. No centered smoothing, retrospective interpolation, nearest-future joins,
   backward fill, future peak normalization or catalogue-derived future input.
   Preserve instrument availability times; retrospective calibrated products
   make this a retrospective study unless latency can be measured.
7. Report pre-onset and ongoing-event strata separately. Onset labels use true
   documented onset, not delayed detection timestamps. Retrospective event
   strata are evaluation annotations, not available-time features.
8. OOD = later untouched active periods after a substantial temporal gap and
   quality/regime strata. Full-disk X-rays cannot support a pure held-out active
   region experiment without extra spatial data; repeated regions may return.
   Add such a study only with justified region attribution and grouped embargoes.

## Baselines and ARCH/GARCH reasoning

| Group | Required initial candidates | Scope |
|---|---|---|
| Naive | last valid persistence, trailing 30-minute mean, EWMA | Same origin/quality policy; no future gap filling |
| Linear/statistical | direct ridge/linear multi-horizon, AR, small ARIMA | AR lags and ARIMA (p,d,q) from a small preregistered grid selected on tuning |
| Volatility | AR+constant variance, AR+ARCH(p), AR+GARCH(1,1), Gaussian and Student-t innovations if stable | Probabilistic log differences/residuals; compare to constant-variance control |
| Neural | small LSTM, causal TCN, supervised patch Transformer | Comparable parameter/tuning/training budgets; GRU optional if LSTM costly |
| SSL | temporal JEPA and masked reconstruction or TS2Vec | Same input, decoder, backbone where possible, pretraining budget disclosed |
| LLM | Qwen2.5-1.5B 4-bit LoRA, optional Chronos-small | Secondary, reduced task with matching numerical baselines |

For positive valid flux F, investigate y=log10(F/Fref) (Fref=1 W/m²) and
r_t=y_t−y_{t−1}. Reject gaps and nonpositive measurements. On TRAIN ONLY inspect
ACF/PACF, stationarity (ADF/KPSS interpreted cautiously), tail behavior,
residual ACF/Ljung–Box and squared-residual ACF/ARCH-LM. Fit mean dynamics first.
ARCH models variance from lagged squared residuals; GARCH also uses lagged
variance: σ²_t=ω+αε²_{t−1}+βσ²_{t−1}. Check ω>0, α,β≥0 and stationary-variance
conditions where invoked. Log optimization/convergence, persistence α+β, and
sensitivity to regime shifts. Stationarity and residual adequacy are hypotheses,
not consequences of taking logs. Flare shots are not financial returns.

Forecast variance is neither mean flux nor flare probability. Use simulated
conditional paths, integrate log differences, invert the transform, and then
score flux quantiles or horizon-threshold probabilities. Median exp/log inversion
is not the mean; avoid Jensen bias. Compare interval coverage/width, pinball,
CRPS and, secondarily, held-out squared residual proxies/QLIKE where valid.
Do not train directly on integer flare classes with ARCH/GARCH. If diagnostics
fail, report model inadequacy rather than force a volatility interpretation.
Fractional variants are literature-supported but outside the first small grid.

## Ablations, fairness and staged matrix

Core: 4 JEPA variants (plain, measurement constraint, multiresolution, both),
with physics variants conditional on the measurement gate. Run the same physical
constraint on the strongest conventional model. Match receptive field and
capacity; log exact parameters and optimization steps, including pretraining.
Compare no-pretraining and latent versus reconstruction objectives to isolate
JEPA benefit. Feature ablations start with spectral bands versus broadband;
particle ablations follow only if overlap/quality warrants them.

Stage A: CPU statistical/linear screening; no hundreds of configurations.
Stage B: one seed, up to 3 configurations each for LSTM/TCN/Transformer/plain
JEPA, max 20 epochs, early stopping patience 5 using tuning pinball loss.
Stage C: freeze hyperparameters; seeds [17,29,43] on retained baselines and
ablations, ideally 5 seeds [17,29,43,71,101] if affordable. Only then evaluate
the untouched period once. Report all tried configurations and failures.
Stage D: secondary horizon/feature/OOD sensitivity with fixed settings.

## LLM protocol

Use a base Qwen checkpoint pinned by revision. Convert training-scaled log
values to fixed precision signed decimal text with explicit delimiters, missing
tokens and channel IDs; no narrative that reveals labels. Audit tokenizer
length and quantization error. Start at 5-minute resolution, univariate 3 h →
30 min, max sequence length 1024, LoRA rank 8–16, NF4, FP16 on T4, microbatch
1–2 with accumulation/checkpointing. These are starting budgets, not guarantees.
Match the numerical baseline's grid and training windows. Score invalid,
truncated and unparseable generations explicitly; never silently discard them.
Evaluate sample-based uncertainty only with enough generated trajectories and
report sampling cost. Compare to native small Transformer; pretraining is an
external data/compute advantage and cannot be erased by parameter matching.
Any explanation layer summarizes model outputs and uncertainty, not new evidence
about magnetic reconnection or operational safety.

## Metrics and estimands

- Continuous: MAE and RMSE in physical units and log space, per horizon/band;
  skill relative to persistence, optionally MASE with TRAIN-only denominator.
  Report quiet/pre-onset/rise/decay strata without cherry-picking flare days.
- Warnings: TSS, HSS2, precision, recall, F1, PR-AUC, confusion matrix, FAR
  `FP/(TP+FP)` and false positive rate `FP/(FP+TN)` separately. Undefined
  denominators yield NA with counts. Distinguish per-origin and per-event scores;
  merge contiguous alarms by a frozen rule and report false alarms/day and lead
  time, not only thousands of correlated true-positive windows.
- Probability: Brier score and training-climatology Brier skill, reliability
  diagrams with uncertainty, log score if stable. ECE alone is insufficient.
- Intervals: pinball loss, 50/90% coverage and width by horizon/class; weighted
  interval score. CRPS only for a declared full distribution or adequate samples,
  not asserted exact from five quantiles. Pointwise and trajectory coverage differ.

Use one preregistered primary continuous endpoint (mean pinball over target
bands/horizons) and one secondary warning endpoint (M+ Brier skill with fixed
onset definition). Superiority requires practical effect size and uncertainty,
not isolated p-values. Negative results are reportable.

## Statistical inference and compute

Store losses on identical origins for paired comparisons. Resample contiguous
time blocks at least longer than forecast overlap; choose block length from
development residual dependence, examine 1/3/7-day sensitivity. For event
metrics resample full event clusters with quiet-time blocks, preserving exposure.
Do not bootstrap windows IID. Seed variability and data-sampling uncertainty
are different: show per-seed scores and paired block CIs, not a single mixed SD.
Use ~2000 CPU bootstrap replicates initially. Diebold–Mariano with HAC errors
is a secondary sensitivity for appropriate losses, not a cure for rare events
or regime shifts. Adjust multiple primary comparisons (e.g., Holm) and report
effect sizes/95% CIs; compute event-count-based power/precision before expansion.

CPU/Apple Silicon: acquisition/EDA and classical models. T4 target: 1–3M model,
batch 16–64, ≤144 history patches for 12 h at 5-minute patch length. Budget
<8 GiB VRAM for native models, <13 GiB for QLoRA; measure before committing.
First profile ≤200 optimizer steps after approval; log RAM/VRAM, seconds/step,
tokens, energy proxy GPU-hours and estimated full run. Provisional ceiling
30 GPU-hours for core pilots/repeats, 6 GPU-hours for LLM trial; stop/re-scope
if profiling exceeds it. These are caps, not benchmarked runtime claims.
Resume checkpoints with RNG/optimizer/EMA state; T4 uses FP16, not assumed BF16.
No CUDA-specific quantization requirement is imposed on Apple development.
