# SolarJEPA V2.1 experimental protocol

Date: 2026-10-10, Asia/Kolkata. Research checkpoint based on origin/v1 **644648f7d555fcbcb3eed4495d37fecffdd1863a**. Branch: research/v2-independent-validation.

**Status: PROPOSED — REQUIRES APPROVAL.** This is a fully specified candidate protocol, not a preregistration already approved or an implemented experiment. All prospective choices below, including calendars, seeds, budgets, statistical procedures and decision thresholds, have this status. Commit publication authorizes no data acquisition, training or implementation. Freeze the approved version and analysis/configuration hashes before releasing any new test outcomes. An unresolved approval/access gate blocks execution, not this design deliverable.

## 1. Question, scope and verified starting evidence

Does adding JEPA latent pretraining improve direct probabilistic GOES X-ray flux forecasting beyond a matched supervised architecture, after accounting for training randomness, time dependence and additional optimization?

The task is retrospective continuous one-minute primary corrected GOES-16 XRS-A/B irradiance forecasting. It is neither demonstrated flare-onset warning nor neural trajectory generation, physical dynamics or Aditya-L1 validation.

**OBSERVED in this design session:** Reading the existing strict NPZ/per-origin artifacts reproduces fine-tuned pinball 0.0392450927216308 versus supervised 0.0395002177773946 dex: difference −0.000255125055763742, improvement 0.645882656%. Paired seed differences for 17/29/43 are +0.000431818008, +0.000083281704, −0.001280474879. Omitting 43 gives +0.000257549856. Paired-seed sample SD is 0.0009049177223 dex. Thus the audit's central seed concern survives independent checking; it does not prove JEPA cannot help.

Primary evidence paths:

| Evidence | Executable/source location |
|---|---|
| Context-only inference, EMA teacher, masking, objectives | [training/jepa.py](../src/solar_flare_jepa/training/jepa.py), build_jepa_model, pretrain_jepa, fit_forecaster |
| Train-only unique raw normalizer | [training/normalization.py](../src/solar_flare_jepa/training/normalization.py), Normalization.fit |
| Flags, counts, units and time | [data/goes.py](../src/solar_flare_jepa/data/goes.py), _times/read_goes |
| Closed support and explicit chronology | [forecasting/windows.py](../src/solar_flare_jepa/forecasting/windows.py), build_partition_windows; [splitting.py](../src/solar_flare_jepa/forecasting/splitting.py), chronological_partitions |
| Contiguous multi-manifest constraint | [data/foundation.py](../src/solar_flare_jepa/data/foundation.py), goes_training |
| Classical acceptance weakness | [forecasting/statistical.py](../src/solar_flare_jepa/forecasting/statistical.py), Volatility._multistart: largest finite likelihood wins irrespective of convergence |
| Metrics/bootstrap and test execution order | [evaluation/probabilistic.py](../src/solar_flare_jepa/evaluation/probabilistic.py), log_scores/block_bootstrap; [experiments/v1.py](../src/solar_flare_jepa/experiments/v1.py), run_v1 |
| Existing recipe and splits | [v1_models.json](../configs/experiments/v1_models.json), [v1_goes_2024.json](../configs/experiments/v1_goes_2024.json) |
| Historical outputs | results/experiments/v1-full-20261009/{summary.json,per_origin.json,test_predictions.npz,*.pt}, ignored |

**OBSERVED discrepancies/limits:** V1 neural selection uses standardized pinball, not equal-channel dex scoring; B/A effective weighting is 1.68107. The runner's once-after-all-selection description conflicts with actual early baseline/test evaluation. Current Mac14,2 / 8 GiB differs from V1_RUN's M4/16 GB assumption. The V1 dependency-lock header names Windows/Python 3.13.11, while the saved strict artifact records macOS 26.3/arm64/Python 3.13.3; a header is not a resolved environment inventory. Earlier audit scratch is no longer present at its documented temporary path; durable V1 artifacts are present. None of these historical documents is rewritten. Nine-checkpoint replay and the 1,171-test audit result are historical evidence, not checks rerun in this planning session.

## 2. Hypotheses and decision rules

Let J be fine-tuned JEPA, S the matched supervised model, B the extra-update supervised control. Lower loss is better. Section 7 defines the estimands and uncertainty. A proposed **1% relative mean-pinball reduction** is a research relevance threshold, not an established operational utility threshold. A solar/domain reviewer must approve or replace it before freeze.

| Hypothesis / motivation | Independent variable; outcomes and controls | Null / alternative | Acceptance; failure or inconclusive outcome |
|---|---|---|---|
| H1: incremental recipe value | JEPA pretraining present/absent; primary equal-weight dex pinball; secondary median log MAE/native MAE, widths. Same architecture, initial weights, data and downstream schedule | H0: Δ=E[J−S]≥0; H1: Δ<0 for the fixed protocol/periods | Joint 95% interval upper Δ<0 supports average improvement. Lower interval for G=1−J/S>0.01 supports the proposed practical margin. Upper G<0 contradicts improvement; spanning zero is inconclusive. Upper G<0.01 excludes the proposed meaningful benefit, not every tiny gain |
| H2: seed robustness | Paired seed changes, recipe fixed; seed-level equal-period Δ_s and win probability P(Δ_s<0); same seeds in every arm/fold | H0: win probability≤0.5; alternative>0.5 | Multiplicity-adjusted exact binomial lower bound>0.5; ties count as nonwins. Otherwise robustness unestablished; show every seed and influence, never choose a winner seed |
| H3: temporal robustness | Three named historical folds; each fold's pinball Δ_f, secondary lead/channel curves; fresh fold-specific fitting | H0: at least one named fold has Δ_f≥0; alternative all three<0 | All three adjusted fold intervals have upper bound<0. Otherwise report heterogeneity/inconclusiveness; these folds cannot establish cycle-wide or period-population superiority |
| H4: elevated activity/calibration | Recipe; M+ conditional pinball and marginal 90% channel coverage, with 50% coverage/interval scores secondary | H0a: M+ Δ≥0; H0b: marginal coverage error of J is no smaller than S; corresponding lower alternatives | Adjusted M+ interval upper<0 and/or conservative coverage-error bound upper<0 supports only the respective subclaim. Undefined support/unstable intervals are inconclusive. Future-conditioned coverage is diagnostic, not required to be nominal |
| H5: additional cost | J versus B, total training steps/time; pinball Δ_JB, fit wall time, peak RSS and inference time; same observations | Loss H0: Δ_JB≥0; alternative<0. Compute is a separate observed resource gate | Adjusted Δ_JB upper<0 plus the observed median of all 60 paired J/B full-training-time ratios≤1.10 passes the proposed criterion. Include SSL/warmup, downstream epochs, monitoring and checkpoint selection consistently; exclude acquisition/final inference. Report J/S cost too. No population runtime inference is claimed; step equality is not FLOP equality |

A broad favorable conclusion requires H1, practical relevance, H2/H3 robustness and acceptable failures/assumptions. H4/H5 cannot rescue a failed H1. Negative, negligible, conditional and inconclusive results are valid deliverables. Report a 95% G interval contained in [−0.01,+0.01] as compatibility with the proposed negligible-effect range, with its assumptions; do not equate non-significance with equivalence.

## 3. Exposure ledger and candidate datasets

All May–August 2024 data, V1 smoke/strict scores and P1/P2 periods are development/exposed. Git history also evidences January 2025 flux acquisition and an annual 2025 science flare-catalog manifest at 28e222ba042b32c84dad49a446f0849c677af4b9, plus external-validation documentation at bd128295c8529e064473e483751ca747de2f57a5 on other refs. Those refs are read only. January 2025 is not a fresh-test default. The extent of scientific inspection, broad catalog exposure, private teammate runs and unrecorded access is **UNKNOWN**.

**Candidate calendar, not certified untouched:** repeat the following for Y=2020, 2022, 2023, all bounds UTC half-open.

| Role | Start | End | Days | Structural stride-30 origin ceiling |
|---|---|---|---:|---:|
| Raw fold | Y-05-01 00:00 | Y-08-01 00:00 | 92 | — |
| Train | Y-05-01 00:00 | Y-06-01 00:00 | 31 | 1,484 |
| Embargo | Y-06-01 00:00 | Y-06-02 00:00 | 1 | 0 |
| Validation | Y-06-02 00:00 | Y-07-01 00:00 | 29 | 1,388 |
| Embargo | Y-07-01 00:00 | Y-07-02 00:00 | 1 | 0 |
| Test | Y-07-02 00:00 | Y-08-01 00:00 | 30 | 1,436 |

Calendar-year separation, one instrument and identical seasonal dates avoid selecting periods from favorable model results. NOAA places the cycle minimum in December 2019, motivating 2020 as an early-cycle candidate; actual quiet/elevated/event support remains unknown. May–July avoids equinox-centered eclipse seasons described in the instrument guide. This is a modest diversity check, not random sampling of solar regimes. The one-day embargo is conservative and does not establish active-region independence. [NOAA cycle announcement](https://www.spaceweather.gov/news/solar-prediction-scientists-announce-solar-cycle-25), [XRS guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf).

Use three separate fold datasets; never concatenate separated years into an apparently continuous time axis. Each joins only its own contiguous May/June/July monthly manifests. No 2024 model/normalizer or later-fold weights initialize an earlier fold. This evaluates repeated historical forward-time fitting, not zero-shot transfer of a single trained model.

Before acquisition, both contributors attest YES/NO/UNKNOWN for candidate raw/quality/plots/catalog access, supervised or self-supervised fitting, metrics, dates/tools and possible influence on design. Absence of a tracked manifest does not prove freshness. UNKNOWN prevents an untouched claim and requires approval of conditional retrospective scope or a new calendar. A 2021 May–July fallback is a proposal requiring an amendment, never automatic substitution for difficult data.

After approval, a custodian verifies sealed tests using integrity/schema/QC only; researchers see train/validation. Do not release test plots, activity counts, labels, losses or individual-fold outcomes until every model/configuration/checkpoint across all folds is locked. All test forecasts are produced from locked artifacts without updates. Log every access and deviation. Catalog data follows the same restriction. Technical reruns preserve configs/weights and receive an access-ledger entry; scientific changes after unsealing are exploratory and require fresh confirmation.

## 4. Measurement, preprocessing and common support

Use GOES-16 science XRSF-L2-AVG1M v2-2-1 primary electron-corrected XRS-A/B, native W/m², native record-start UTC plus 60-second bin ends. Pin official source URL, bytes, SHA-256, product/schema/version, measured coverage, flags and contributing-sample counts. Reject schema/unit/time changes pending instrument review; never silently substitute another satellite/version or calibrate from test data. [NOAA ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf).

**DOCUMENTED instrument/product limitation:** NOAA applies a 10⁻⁹ W/m² lower threshold to corrected irradiance, and electron correction can leave artifacts. This is a product processing threshold, not a demonstrated detector sensitivity limit. Interpret low-flux errors against the processed target; its prevalence/impact in candidate folds is UNKNOWN. [ReadMe §2.2/§4](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf), [User Guide §4](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf).

Preserve the actual V1 validity policy: finite positive in-native-range flux, status exactly zero, accepted electron bits separately by channel, contributing count 1–60. Verify integer native count semantics. Reject upstream interpolated bins. Preserve rejected observations/masks and report timestamps, duplicates, gaps, per-channel validity/count distributions and overlapping exclusion reasons. No filling, clipping-to-positive, forward interpolation or gap bridging. A count=60 sensitivity is optional/exploratory with a different population, not a replacement mask.

Forecasts issue every 30 minutes on the UTC grid. Context is [u−120 min,u); targets are the 30 one-minute averages in [u,u+30 min); leads 1–30 label bin ends. Both channels must be valid throughout the context and targets. Require full support inside its raw partition. First eligible issue is start+120 min; last is end−30 min. Embargo rows enter no training/validation/test support. No derivative, calendar, flare or future quality features are added.

Targets and features use log10(F / 1 W/m²). Fit mean/std once to unique valid raw training bins, not duplicated windows; use that fold normalizer everywhere. No fold pooling. Select the same deterministic evenly spaced chronological subset of min(20,000, eligible) stride-1 complete training windows for every neural/quantile comparator. Store selected starts/fingerprints. Classical models may use all unique raw training bins; declare this unequal repetition/support explicitly rather than claim identical sample counts.

All models score the identical manifest of retained test origins and both channels/leads. A model error does not change eligibility. As proposed feasibility gates, require ≥20,000 eligible training windows, ≥500 validation/test origins and ≥21 issue-days per validation/test partition. These are planning minima, not power guarantees. Custodian QC failure pauses the protocol; record failed periods and seek an amendment before any model-score inspection.

At stride=horizon, target intervals are disjoint. Contexts overlap by 90 minutes and earlier targets become later observations. This is causal rolling evaluation with dependence; it is not an online refitting allowance or independent-origin sampling. Science products do not establish historical operational delivery latency.

## 5. Controlled models, optimization and selection

| Arm | Fixed design and purpose | Seeds per fold |
|---|---|---:|
| J | V1 architecture: patch 5,width 32,depth 3,heads 4,predictor depth 2,MLP ratio 4,head 128,dropout 0; 8 JEPA epochs then 15 forecasting epochs | 20 |
| S | Exact J predictive architecture/initial weights, no pretraining; 15 forecasting epochs | 20 |
| B | Same initialization; 8 supervised warmup epochs, reset AdamW, retain weights/head, then same 15 forecasting epochs | 20 |
| Frozen JEPA | Reuse matching J's immutable pretraining encoder/predictor, train only the identically initialized head for 15 epochs | First 5 |
| Frozen random | Same seed's random encoder/predictor, train only head for 15 epochs | First 5 |
| Full-context quantile linear | Flatten 120×2 normalized inputs; affine 300 outputs, joint pinball with L2 on coefficients; zero initialization; sort five output quantiles per cell at prediction | Fixed optimization seed |
| Small TCN | Six causal residual blocks, width 32, two kernel 3 convolutions/block, dilations 1/2/4/8/16/32, GELU, dropout 0; final-state affine 300 outputs with ordered quantiles | First 5 |
| Empirical persistence / point persistence | Train-only per-lead log-increment quantiles; unchanged point persistence as context | Deterministic |
| ARIMA | Per-channel four (p,1,q) candidates, p∈{1,2},q∈{0,1}; fixed train parameters, re-filter same latest 120 min at issue | Deterministic |
| Volatility | Existing shared two-stage train-only AR(1) mean on adjacent valid log-differences + constant-N, ARCH-N, GARCH-N, GARCH-t, GJR-t; no test fitting | Fixed simulation seeds |

Point persistence supplies point-metric context only; its pinball/coverage entries are unavailable. The probabilistic empirical-persistence comparator supplies trained increment quantiles. All reported comparisons retain the same eligible origins.

TCN input has four channels (two normalized fluxes plus validity masks). Each kernel-3 convolution has bias and left padding 2×dilation; apply GELU after the first convolution and after residual addition. The first block projects four input channels to 32 with a biased 1×1 skip convolution without padding; later skips are identities. No normalization/weight normalization is added. Apply a biased 32→300 linear head to the final state; reshape to 30×2×5 and use base plus cumulative Softplus increments as in J. This gives 44,620 parameters and terminal receptive field 253 bins, covering the entire supplied 120-minute context through causal padding; this is not a 253-minute data input. Frozen/TCN five-seed outcomes are secondary/exploratory, not substitutes for the primary 20-seed comparison. Seasonal-naive/SARIMA expansion is deferred absent development evidence of seasonality and a feasible budget. The causal-convolution comparator is informed by [Bai, Kolter and Koltun](https://arxiv.org/abs/1803.01271); this exact small configuration is a protocol proposal.

J keeps Smooth-L1 normalized teacher latent loss, four hidden context patches plus six future patches, EMA 0.996→1, no gradient through teacher. Forecasting auxiliary JEPA weight remains zero. AdamW lr=0.001, weight decay=0.0001, batch 256, clip norm 1, CPU with four threads, no LR scheduler. All 15 downstream epochs execute; no early stopping. Choose the earliest minimum validation **equal-dex pinball** among these 15 checkpoints. Warmup checkpoints are ineligible. For 20,000 windows there are 79 steps/epoch: J=632 SSL+1,185 forecasting; S=1,185; B=632+1,185 supervised. B matches encoder/predictor update opportunities and optimizer reset, not total FLOPs or head learning (B's head also trains in warmup).

Change V2 forecast training loss to mean per-channel normalized pinball multiplied by its train-fitted target std, then average channels/leads/quantiles. This equals dex pinball; validation uses the same metric. This is a future versioned V2 implementation requirement, not a change to V1.

No JEPA/supervised hyperparameter search in confirmation. Development-only feasibility pilot uses existing 2024 training/validation/spent test support with pseudo-tests clearly exploratory; no new candidate test data. Select no favored seed. Quantile-linear λ∈{0,0.001,0.01,0.1,1}, Adam lr 0.01, batch 256, 100 fixed epochs, no validation epoch selection; objective is dex pinball plus λ times mean squared standardized-input coefficients, excluding intercepts. Generate its own 100-epoch shuffle stream with NumPy PCG64(first frozen seed), reinitializing that stream identically for every λ. Sort quantiles during validation and test, report raw crossing frequency, choose λ by validation dex pinball, ties smallest λ. Report it as finite-budget gradient optimization, not certified convex optimum. Prediction rearrangement follows the idea of [Chernozhukov, Fernández-Val and Galichon](https://arxiv.org/abs/0704.3649). TCN keeps fixed lr 0.001/weight decay 0.0001 and 15-epoch selection, batch 256/clip 1; no architecture sweep. Ties in ARIMA use lexicographic order. All settings are locked across folds before their tests open.

### Ablation priorities

| Rank | Controlled question | Cost / decision |
|---|---|---|
| 1 | J versus S and B: pretraining recipe versus random initialization and extra supervised updates | Essential; the 180 core jobs already include these controls. B reduces an optimization confound but does not isolate every property of the latent objective |
| 2 | Frozen JEPA versus frozen random: is the learned representation useful to the same forecast head? | The 30 head-only jobs reuse 15 existing SSL states; five seeds/fold give a descriptive mechanism check |
| 3 | Objective or masking specificity | Deferred. A separately approved, update-matched ablation is necessary before claiming the JEPA objective/mask itself caused a gain; develop it on exposed data first. No such specificity claim is supported by J/S/B alone |
| 4 | Pretraining-volume, masking sweeps or wider representations | Deferred rather than a combinatorial default. These add search/capacity/data-budget confounds; require a specific evidence gap and new budget/protocol before confirmation |

### Classical fit acceptance

For every start require convergence_flag=0 (ARIMA converged=true), finite likelihood/parameters, positive finite filtered/forecast innovation variance, and valid model constraints. For ARCH require α≥0 and α≤1−10⁻⁶; GARCH require α,β≥0, α+β≤1−10⁻⁶; GJR require α,β≥0, α+γ≥0, α+β+γ/2≤1−10⁻⁶. Require ω>0 (constant variance σ²>0), shared AR-difference mean |φ|≤1−10⁻⁶ and Student-t degrees of freedom≥2+10⁻⁶. Retain ARIMA's enforced stationary/invertible difference-model specification. No coefficient/variance clipping to pass acceptance. The margin 10⁻⁶ is a proposed dimensionless numerical/strict-stationarity choice, not an instrument constant. Record 10⁻⁸ boundary diagnostics without accepting negative coefficients. [ARCH constraints](https://arch.readthedocs.io/en/stable/_modules/arch/univariate/volatility.html).

Retain V1's default+fixed start grid except remove the infeasible GJR start (α=.15,γ=.05,β=.9,persistence 1.075); rank likelihood only among accepted starts. First pass maxiter 500. If none accepts for a model/channel, allow one fixed interior retry with maxiter 2000/ftol 10⁻¹⁰: constant variance=v; ARCH α=.1,ω=.9v; GARCH α=.05,β=.8,ω=.15v; GJR α=.05,γ=.05,β=.8,ω=.125v, where v is training residual variance and t starts use ν=8. Record every outcome, warnings, likelihood and slack; no new hand-picked starts after test access. ARIMA uses maxiter 200 then one retry at 1000 using the library's deterministic default initialization. Any finite-horizon IGARCH alternative requires a separately labeled development-only protocol, not silent relaxation.

Residual handling follows V1's consecutive-valid difference pairs and its disclosed concatenation approximation for variance fitting; segmented-gap sensitivity belongs to development and must freeze before confirmation. All five variance variants are reported, including failed ones; validation selects one accepted classical reference. If an entire family fails, report unavailable and make no superiority claim for it.

Use 1,000 simulated paths, seed 0, as primary volatility prediction. In M2 development only, compare exactly (paths,seed)=(10000,0),(1000,1),(1000,2) against (1000,0) for all five variants, with the same fitted parameters/origins. Report every combination, never select a favorable simulation seed. These extra 15 forecast variants are excluded from confirmation counts/storage; material instability requires a pre-test protocol amendment, not an opportunistic test rerun. Require finite ordered complete predictions and positive conditional variance at every retained origin; a failed forecast is a model failure, not an origin exclusion. Global optimum or parameter-uncertainty integration is not claimed.

## 6. Seeds, randomization and failure policy

Use 20 fresh paired seeds generated from the first four SHA-256 bytes of ASCII SolarJEPA-V2.1-paired-seed-i, big endian modulo 2³¹, starting i=0; skip duplicates and all old seeds 17/29/43. Same ordered list in every fold/arm. First five define the secondary arms:

1261866429, 1291916211, 1928562547, 510418947, 431928332, 21185310, 1222754442, 745890783, 878753449, 222572566, 957668480, 768280471, 627667792, 212882923, 1807776811, 780470138, 1784246101, 1670717663, 978924304, 1202725490.

Pair predictive initial states and downstream permutations for J/S/B; use separate recorded RNG streams for initialization, masks, warmup and downstream shuffling. J/B share warmup window order; J/S/B reset the downstream optimizer/RNG protocol identically. Record fingerprints before/after each phase. Run sequentially, interleaving arms by a recorded hash-sorted fold/seed/arm schedule to limit time/thermal bias.

**Precision/resource rationale:** V1 SD gives an illustrative t₁₉ seed-only half-width 0.000423515 dex at n=20, below a proposed 0.0005-dex precision target. The normal approximation for 80% power at the V1 effect gives about 99 seeds; n=20 does not promise that power or achieved precision, especially with time variation and an unstable three-seed SD. Twenty is an affordable first fixed study, not a significance-seeking stopping rule. Complete all 20 on all folds; no expansion/seed replacement based on test results. Further runs require a new declared study. Training/data/search variability are distinct sources of experimental uncertainty; see [Bouthillier et al.](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf).

All 120 primary J/S jobs must produce complete finite aligned predictions. Permit logged same-seed/config infrastructure retries before scoring; unresolved numerical/scientific failures make the formal primary analysis incomplete/inconclusive. Show descriptive successful pairs separately, never silently drop/impute failures. Failures in B/frozen/TCN/classical arms do not alter the primary cohort; their comparisons remain unavailable.

## 7. Primary estimand, inference and multiplicity

For model m, seed s, fold f, origin o, lead h, channel k and level q:

ρ_q(e)=max(qe,(q−1)e), e=log10(y)−log10(predicted quantile).

L_msf is the arithmetic mean over retained origins, 30 leads, two channels and levels {0.05,0.25,0.5,0.75,0.95}. Primary Δ=(1/(3×20))Σ_f,s(L_Jsf−L_Ssf). Each fold has weight 1/3 regardless of retained count. G=1−mean_f,s(L_Jsf)/mean_f,s(L_Ssf). Average individual losses, never ensemble predictions. Complete support makes channel/lead denominators equal; an approved masked extension would require explicit separate denominators and a new estimand.

Use a crossed paired bootstrap with **50,000 draws**, analysis RNG seed 20261010, NumPy linear percentiles:

1. Precompute each model/seed/fold/day's loss sums and shared origin counts, keeping all 30 UTC calendar issue-days, including zero-count days.
2. Draw one length 20 seed-index vector with replacement, shared across all folds, arms and endpoints.
3. Within each fixed fold independently draw circular contiguous three-calendar-day blocks, concatenate and trim to 30 days. Share that day's indices across all seeds/arms/endpoints. Preserve sums/counts, then mean selected seeds and equal-weight folds for the primary and fold/marginal endpoints. The separately defined M+ endpoint pools qualifying origins across folds instead.
4. Recompute both model means, Δ and G each draw. Report joint 95% percentile intervals as primary, plus seed-only and fixed-seed/time-only intervals as attribution diagnostics. Do not resample three outer folds to imply a solar-period population.
5. Repeat time blocks of 1 and 7 days as prespecified sensitivity. Report all. Classification changing at 7 days means dependence-sensitive evidence; never select the favorable block size. Seed/fold leave-one-out plots are descriptive.

For every endpoint and block length, a zero original or resampled required origin count makes that interval unavailable. Never discard/redraw a replicate or impute a loss; keep unaffected endpoints/lengths separately. A zero/nonpositive supervised mean also makes G unavailable. A missing sensitivity interval is disclosed as a limitation, not treated as agreement with the primary. The ≥21 issue-day gate does not ensure nonzero bootstrap support.

Three-day blocks are a proposal to be checked/frozen on exposed development loss autocorrelation and stability before new tests. If inadequate on development, amend before unsealing. Within-period approximate stationarity/weak dependence, representative seed draws and sufficiently informative blocks are assumptions, not validated facts. Test diagnostics revealing regime shifts or insufficient effective blocks qualify or invalidate nominal interval claims; they do not authorize tuning block length for significance. Circular wrap is artificial and disclosed. No inference includes full training-data/hyperparameter-selection variability. [Owen and Eckles](https://arxiv.org/abs/1106.2125) motivates preserving crossed factors, and [Politis and White](https://mathweb.ucsd.edu/~politis/SBblock-revER.pdf) discusses block-length selection; neither establishes exact coverage for this hybrid design.

There is one primary comparison. A fixed seven-slot secondary family covers H2 seed-win probability, three H3 fold contrasts, H4 M+ pinball, H4 coverage-error contrast and H5 J/B pinball. Use α=0.05/7 per slot (two-sided 99.285714% intervals); formal secondary superiority statements are gated on H1's practical criterion. Keep seven slots even when one is unavailable. This is conservative multiplicity accounting only under valid individual inference; it cannot repair bootstrap assumptions.

H2 uses exact Clopper–Pearson binomial limits for 20 independent seed-level signs, conditional on fixed test paths.

M+ means realized future XRS-B maximum≥10⁻⁵ W/m². Let A_fo be its binary indicator and d_sfo the J−S loss difference averaged over all leads/channels/quantiles at that origin. Define Δ_M=(1/20)Σ_s[Σ_f,o A_fo d_sfo / Σ_f,o A_fo]. This deliberately pools qualifying origins across the three fixed folds, a different conditional population from the equal-fold primary. In each replicate use the sampled seed vector and the same fold/day multiplicities in this pooled numerator/denominator. A fold with no M+ origins contributes zero count; globally absent support, or zero total count in any draw, makes the M+ interval unavailable. Report per-fold and pooled counts/days, without redrawing or inventing zero loss.

For calibration, use the 12 signed coverages p_(m,f,k), m∈{J,S}, averaged over seeds/origins/leads within each fold/channel. The target is C_m=mean_(f,k)|p_(m,f,k)−0.90|: absolute error after seed-averaging coverage, not mean per-seed absolute error. In the same bootstrap let c be the(1−0.05/7) quantile of max_j|p*_j−p_hat_j|. Construct simultaneous bands [a_j,b_j]=[max(0,p_hat_j−c),min(1,p_hat_j+c)]. Their absolute-error bounds are ℓ_j=max(0,0.90−b_j,a_j−0.90) and u_j=max(|a_j−0.90|,|b_j−0.90|). The C_J−C_S bound is [mean ℓ_J−mean u_S,mean u_J−mean ℓ_S], with each mean over its six fold/channel entries. An entirely negative bound supports only smaller marginal coverage error. Do not percentile-bootstrap the nonsmooth absolute-error difference directly. A nonfinite/zero c, absent support or an indicator component with no observed variation makes formal calibration inference unavailable. This conservative gate does not infer zero population variance from an empirical constant. The band remains approximate, conditional on the named periods and joint-bootstrap assumptions; its nominal simultaneous coverage is unproven.

All 30 lead curves, both channels, other models/quantiles/strata and native metrics are exploratory unless a later protocol declares a separate family. Do not count unadjusted significant horizons. Bootstrap fractions are neither p-values nor posterior probabilities. A DM/HAC analysis is optional development sensitivity only, with documented loss stationarity/bandwidth/weak-dependence checks; it cannot substitute for seed uncertainty. [Diebold–Mariano](https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524599), [Politis–Romano](https://www.jstor.org/stable/2290993).

## 8. Calibration, elevated activity and event scope

Report pinball, median dex MAE, native MAE/RMSE, 50%/90% pointwise coverage/width, proper central interval score, and quantile reliability by channel and lead. Interval score for α is width+(2/α)(lower−y)I(y<lower)+(2/α)(y−upper)I(y>upper), in stated log units. Five quantiles are not exact CRPS or a joint trajectory distribution. Raw forecasts are primary. No post-test recalibration.

Future-conditioned M+, rising×2 (future B maximum≥2×last observed context B) and quiet<C1 (future B maximum<10⁻⁶ W/m²) strata are retrospective diagnostics. They may overlap; nominal marginal coverage need not hold inside them. Show zero-support cases and failed peaks. Additional validation-only calibration would be a separately locked secondary model with its own budget and multiplicity, not silently substituted for J. [Gneiting–Raftery](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).

**Event extension: PROPOSED — REQUIRES APPROVAL; excluded from primary V2.1 execution counts.** A pinned NOAA science Flare Report can annotate start/peak/end, class and source satellite; it is XRS-derived reference annotation, not independent physical truth. Distinguish retrospective catalog-assigned EVENT_START from delayed detection timestamps and repeated summary states. For an approved descriptive analysis retain GOES-16-source M+ events entirely within a test partition; match issues strictly before start with start in [issue,issue+30 min). Report events as units, repeated-origin counts, ambiguous/source/boundary exclusions and pre-start lead bins. [NOAA Flare Report documentation](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES_Flare_Report_ReadMe.pdf).

An actual alarm study needs a separate approved alert score/threshold selected on validation, one-to-one event matching, alert episode/refractory rules, non-event exposure denominator, false alarms, missed events, lead-time distribution and observed operational data latency. Those decisions are unresolved; V2.1 makes no event-warning or Brier-score claim. Marginal flux quantiles do not identify threshold-crossing probabilities.

## 9. Freeze checklist and unresolved decisions

Before execution approve: candidate freshness/calendar and embargo; reduced one-month training scope; 1% relevance/10% cost thresholds; 20-seed precision/compute compromise; common quality gates; exact comparator contracts; strict classical stationarity policy; bootstrap assumptions/multiplicity; artifact/access ownership and compute ceiling. These choices are **PROPOSED — REQUIRES APPROVAL**, not scientific constants.

Freeze protocol/config/code/environment/data-manifest/seed/index hashes, permitted access, model search budgets, failures/retries, primary estimand and report template. The implementation must demonstrate split/normalization/inference isolation, equal initial states/data order, exact loss weighting, failure preservation and metric/bootstrap correctness on synthetic and exposed development data before new tests. Existing code supports parts of this contract; the complete V2 workflow is not implemented.

Open issues: private prior access; candidate bytes/schema/QC/activity/event support; achieved statistical precision; meaningful utility threshold; actual peak RAM; residual-gap adequacy; bootstrap validity under changing solar conditions; operational availability. An experiment may execute only after its relevant decisions are resolved, with truthful conditional or inconclusive outcomes allowed.
