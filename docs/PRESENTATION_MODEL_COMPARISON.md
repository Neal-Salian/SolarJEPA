# Verified V1 model comparison for the presentation

**OBSERVED:** Independent arithmetic replay of `v1-full-20261009` confirms
fine-tuned JEPA mean pinball **0.0392450927 dex**, versus **0.0395002178** for
the matched supervised control: **0.645883% lower**. **INFERRED:** this is a
small, seed-sensitive pilot result, not robust evidence of general pretraining
superiority. Removing seed 43 reverses the aggregate comparison. Frozen JEPA
underperforms the control for every paired seed.

This presentation preserves all historical source, configurations, models and
results. It performs no training or test-driven tuning. **DOCUMENTED** denotes
external definitions; **OBSERVED** denotes code/file/calculation evidence;
**INFERRED** denotes interpretation; **UNKNOWN** denotes unestablished claims.

## Experiment and common support

Executed source commit: `4a3f88227ce28dea0e885e68987282285963f38e`. Audited
presentation base: `644648f7d555fcbcb3eed4495d37fecffdd1863a`. Input bundle:
`results/experiments/v1-full-20261009/{summary.json,per_origin.json,test_predictions.npz}`.
Their SHA-256 identities match the earlier scientific audit and are recorded in
[model_evidence.json](presentation/model_evidence.json).

| Partition | UTC half-open dates | Retained origins |
|---|---|---:|
| Training | May 1–July 22, 2024 | 3,609 stride-30 evaluation windows |
| Validation | July 22–August 1, 2024 | 412 |
| Test | August 1–September 1, 2024 | 1,436 |

GOES-16 XRS-A/B targets are one-minute irradiances in W m⁻². Context length is
120 minutes, horizon 30 minutes, issue stride 30 minutes. All 22 saved test
models share **1,436 origins and 86,160 valid target cells**; native measurements
match saved contexts and targets exactly. Target windows do not overlap;
adjacent contexts overlap by 90 minutes, and activity introduces further
dependence. Of 1,488 test candidates, four lack partition-boundary support and
48 fail quality eligibility. Scores are conditional on this complete-case sample.

Neural training uses 20,000 evenly spaced windows selected from 108,199 eligible
stride-one training windows. Normalization is fitted on unique raw training
rows. Test measurements were never fitted in this presentation. August was
already inspected in V1 smoke/full runs and audit; it is a spent historical
benchmark for subsequent research design. The old runner's “test scored once
after all selections” wording is stronger than its interleaved execution order;
no automated test-based selector was found, but private manual actions are
unknown. Historical documents are preserved rather than retroactively edited.

## Model specifications actually evaluated

| Model | Verified method and relevant qualification |
|---|---|
| ARIMA(2,1,0) | Per-channel Gaussian log-flux model, selected on validation dex pinball from (1,1,0), (2,1,0), (1,1,1), (2,1,1). Fixed train-fitted parameters re-filter each 120-minute context. |
| AR(1) + constant variance | OLS AR(1) on log differences, then constant Normal residual variance; useful reference for the volatility methods. |
| AR(1) + ARCH(1), Normal | Same two-stage mean; residual conditional variance depends on previous squared innovation. |
| AR(1) + GARCH(1,1), Normal / Student-t | Same mean; residual variance includes previous innovation and variance. XRS-A selected optimizer flag is 8 for both variants. |
| AR(1) + GJR-GARCH(1,1), Student-t | Same mean; asymmetric signed-innovation variance term. Validation-best volatility comparator; flags [0,0], but A persistence is 1.00000147383. |
| Empirical persistence | Train-only per-lead log-increment quantiles anchored to latest context. Its median is not identical to last-value persistence. |
| Supervised neural control | Same Transformer encoder/predictor/ordered quantile head and initialization/downstream recipe as JEPA; skips representation pretraining. Seeds 17/29/43. |
| Frozen JEPA | JEPA pretraining followed by forecasting-head training; encoder and predictor frozen. |
| Fine-tuned JEPA | JEPA pretraining followed by encoder/predictor/head supervised optimization. Auxiliary JEPA weight during fine-tuning is exactly 0. |

Volatility methods use 1,000 simulated paths per forecast with simulation seed
0. They are **two-stage AR(1)-volatility forecasts**, not standalone “pure
GARCH” mean forecasts. Variance fitting concatenates valid adjacent training
residuals across gaps, an approximation. Largest finite likelihood can be
selected despite nonconvergence. Near-unit persistence is a numerical/long-run
qualification, not proof that the recorded finite-horizon forecasts are invalid.
These implementations cannot represent all classical forecasting methods.

SARIMA has no result: the training-only diagnostics establish no stable justified
period, and the historical timing report is not a fresh measurement. See
[EDA/SARIMA decision](PRESENTATION_EDA_REPORT.md#sarima-decision).

The six additional P1 point baselines are persistence, training mean, trailing
30-minute mean, 30-minute drift, AR(1), and direct ridge (10 lags, α=0.1). All
have verified log MAE; none has invented quantiles, pinball or coverage. The
direct-ridge information/budget is weaker than the 120-minute neural setup.
No LSTM, TCN, PatchTST or other modern supervised baseline was evaluated in V1;
their performance is **unavailable**, not implied by the matched control.

## Metric definitions

For each valid cell let `y = log10(F / 1 W m⁻²)`. Log MAE is the mean of
`|y − median_prediction|` in dex. Mean pinball averages
`ρτ(u) = u(τ − I[u < 0])`, `u = y − predicted_quantile`, over τ =
0.05, 0.25, 0.50, 0.75, 0.95 and all valid origins/leads/channels, equally
weighted. Five-quantile mean pinball is not exact CRPS or a joint predictive
density. A relative loss reduction is not a percentage change in physical flux.

Coverage is the fraction of cells inclusively inside the 25–75% or 5–95% bands.
Width is mean log upper-minus-lower quantile in dex; narrower is useful only
with adequate coverage. Coverage is marginal, not simultaneous over an entire
30-minute trajectory. Neural family rows below are **arithmetic means of three
fitted-seed metrics**, not metrics of averaged forecasts or an ensemble.

## Verified probabilistic comparison

| Model | Mean pinball (dex) | Log MAE (dex) | 50% coverage | 90% coverage | 50% width (dex) | 90% width (dex) |
|---|---:|---:|---:|---:|---:|---:|
| Empirical persistence | 0.045853165 | 0.132103713 | 48.52% | 91.20% | 0.15545 | 0.64666 |
| ARIMA(2,1,0) | 0.047582415 | 0.130802634 | 75.52% | 93.99% | 0.30953 | 0.75483 |
| AR(1) + constant Normal variance | 0.050652472 | 0.132364670 | 80.19% | 95.18% | 0.36420 | 0.88719 |
| AR(1) + ARCH(1), Normal | 0.048610581 | 0.132195818 | 70.42% | 95.04% | 0.30752 | 0.93324 |
| AR(1) + GARCH(1,1), Normal* | 0.047041329 | 0.132120408 | 67.08% | 94.32% | 0.28364 | 0.83696 |
| AR(1) + GARCH(1,1), Student-t* | 0.045149454 | 0.131996471 | 48.09% | 86.83% | 0.16561 | 0.51938 |
| AR(1) + GJR-GARCH(1,1), Student-t† | 0.044591839 | 0.130401695 | 47.59% | 85.81% | 0.16530 | 0.51178 |
| Supervised, three-seed mean | 0.039500218 | 0.117985460 | 48.44% | 90.91% | 0.15724 | 0.54208 |
| Frozen JEPA, three-seed mean | 0.041430015 | 0.123758671 | 47.58% | 90.72% | 0.16244 | 0.56851 |
| Fine-tuned JEPA, three-seed mean | 0.039245093 | 0.116593228 | 45.92% | 89.72% | 0.14512 | 0.52721 |

* XRS-A convergence flag 8; † near-stationarity-boundary XRS-A GJR fit.
Full-precision scores and observed compute are in [model_metrics.csv](presentation/model_metrics.csv).
The charts include all ten comparable probabilistic family/model rows, without
discarding an inconvenient result. Point-only MAE values: persistence 0.133855459,
training mean 0.246614084, trailing mean 0.166161430, drift 0.188146478, AR(1)
0.128617438 and direct ridge 0.124311806 dex. They are tabulated in the CSV and
excluded from probabilistic charts because they have no interval forecasts.

## Seed influence and conditional uncertainty

Paired differences below are **fine-tuned JEPA minus supervised**; negative
favours JEPA. Existing block-bootstrap code resamples whole UTC issue-date
blocks, retaining paired origins: 31 days, 2,000 draws, RNG seed 17. Day sums and
counts preserve the origin-weighted mean when day support differs.

| Fitted seed support | Pinball difference (dex) | Conditional 95% daily-block interval |
|---|---:|---|
| Seed 17 | +0.000431818008 | [−0.000026998927, +0.000819475245] |
| Seed 29 | +0.000083281704 | [−0.000271280825, +0.000459744834] |
| Seed 43 | −0.001280474879 | [−0.001981236444, −0.000729293690] |
| Mean of all three fitted seeds | −0.000255125056 | [−0.000551146471, −0.000022307370] |
| Mean excluding seed 43 | +0.000257549856 | [+0.000013935314, +0.000515424851] |

Omission of seed 43 is an exploratory influence diagnostic, not a new selection
rule. Intervals condition on fitted seeds and omit training, selection and
seed-population uncertainty. Temporal dependence can extend beyond one day;
daily-block coverage is not guaranteed by this short record. Multiple model,
lead and stratum contrasts are exploratory; no simultaneous error control or
minimum operationally meaningful effect was prespecified. The bootstrap draw
fraction below zero is not a posterior probability or calibrated p-value.

**OBSERVED:** Fine-tuned/frozen JEPA beat the selected GJR implementation in
aggregate pinball by **11.9904% / 7.09059%**. Supervised already accounts for
**95.2284%** of the absolute fine-tuned/GJR gap. Frozen JEPA is **4.88554% worse**
than supervised. The fine-tuned/control log-MAE reduction is **1.18000%**.
Fine-tuned JEPA has higher pinball than GJR at leads **1–5**, despite its better
aggregate. No blanket all-horizon or all-classical-model superiority is supported.

**OBSERVED:** Fine-tuned JEPA's pooled 90% coverage is 89.7199%, comprising
87.0257% A and 92.4141% B; its pooled 50% coverage is only 45.9173%. Aggregates
hide channel differences. The largest-rise fan example misses the sharp peak
with all displayed upper bands. Prior V1 audited difficult-stratum results
also limit event claims; these annotations depend on realized future flux and
are not independent event-warning labels.

## Architecture and methodology

See [reproducible architecture diagram](figures/presentation/jepa_architecture.png).
The implemented width-32, three-layer, four-head Transformer encodes 24
five-minute context patches containing two normalized log channels and masks.
A two-layer latent predictor uses six future mask queries. During JEPA
pretraining, a full-window EMA teacher sees 150 training minutes without
gradients; the student predicts four hidden context-patch and six future-patch
embeddings with Smooth-L1 loss. EMA momentum increases 0.996→1.0.

The downstream 128-hidden-unit head combines mean context embeddings and
predicted future embeddings, producing 30×2×5 ordered marginal quantiles.
Softplus cumulative increments enforce quantile ordering. Prediction receives
only observed context; the teacher is unused at inference. Frozen training
updates only the head; fine-tuning updates encoder, predictor and head using
pinball. Representation pretraining and downstream supervised forecasting are
distinct stages. There is no physics constraint, neural autoregressive rollout
or joint trajectory generator. [I-JEPA](https://arxiv.org/abs/2301.08243) is the
prior latent-prediction principle, not a claim of architectural novelty here.

Recorded V1 settings: eight pretraining epochs; at most 15 downstream epochs;
patience 3; AdamW lr 0.001/weight decay 0.0001; batch 256; gradient norm cap 1;
CPU four threads. Encoder/predictor/head have 39,808/28,576/67,948 parameters
(136,332 total, plus a separate 39,808-parameter EMA teacher). JEPA adds 632
pretraining updates; total optimization budget is not matched to supervised.

Neural checkpoint selection uses **standardized-log pinball**, while final
scoring and classical selection use equal-channel dex pinball. Training standard
deviations imply approximately 37.30% A / 62.70% B neural selection weighting,
versus 50/50 final evaluation. This shared neural recipe does not establish
differential bias, but is a material objective mismatch that was not “fixed”
after seeing test results.

## Compute, assets and reproducibility limits

Observed mean `fit_seconds` per fitted seed: supervised **64.82 s**, frozen
**101.54 s**, fine-tuned **111.31 s**. Selected ARIMA was **11.19 s**; variance
models were **2.11–4.97 s**. These saved runner timings include its fitting
envelope, not isolated algorithm kernels. Mean test predict/scoring envelopes
are **3.74–3.79 s** per neural seed and **8.66–12.04 s** for selected ARIMA/
volatility models. They are not per-origin online latency measurements. The
strict run took 18.44 minutes on the recorded Mac14,2/8 GiB CPU host; no M4,
GPU or cross-platform speed claim is made.

Regenerate with `python scripts/build_presentation.py` in the installed V1
environment; no retraining is required. New charts: [pinball](figures/presentation/comparison_pinball.png),
[log MAE](figures/presentation/comparison_log_mae.png), [lead error](figures/presentation/comparison_lead_errors.png),
[coverage](figures/presentation/comparison_coverage.png), [seed influence](figures/presentation/jepa_seed_comparison.png),
[training curves](figures/presentation/jepa_training_curves.png). Reused
[largest-rise fan](figures/v1/fig_fan_largest_rise.png) shows validation-selected
**seed 43**, not a seed ensemble. Exact captions and hashes are in the
[figure manifest](presentation/figure_manifest.json).

The replay performed **422 numerical comparisons**, with maximum absolute
discrepancy **0** at recorded precision, and exact native/context/target alignment.
An independent reviewer separately reproduced metrics to within 1.67×10⁻¹⁶.
This verifies saved-output arithmetic, not independent training replication.
Raw files, NPZ and checkpoints remain local and ignored; a fresh clone needs
the existing pinned data and the exact V1 result bundle to rebuild model plots.
No automatic download is performed. See [verification record](PRESENTATION_VERIFICATION.md).

**UNKNOWN / limits:** robust benefit over training randomness, other periods or
satellites; effectiveness against stronger modern neural baselines; event-onset
warning skill; operational latency; general seed-aware confidence intervals;
cross-platform training reproduction. This is presentation-ready evidence for
a bounded retrospective pilot, not operational or publication-ready validation.
