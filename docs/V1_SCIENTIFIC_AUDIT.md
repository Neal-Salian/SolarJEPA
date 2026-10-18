# SolarJEPA V1 independent scientific audit

Audit date: 2026-10-10 (Asia/Kolkata). Scope: completed V1 only. This audit preserves the original experiments and results and proposes, but does not execute, follow-up experiments.

## 1. Executive summary

**Overall scientific verdict: PROMISING_BUT_INCOMPLETE. Publication readiness: NOT_READY.** V1 is a coherent, reproducible retrospective pilot of continuous GOES X-ray flux forecasting. Its saved numerical results are supported by independent raw-data, prediction, checkpoint and statistical checks. No confirmed temporal leakage or scoring error was found in the inspected execution path. That is narrower than proof of universal correctness or operational validity.

**VERIFIED RESULT / OBSERVED:** Fine-tuned JEPA has 0.0392450927 dex mean pinball versus 0.0395002178 for the supervised control, a 0.645883% reduction. The reported paired daily-block interval for the difference reproduces: −0.000255125056, 95% interval [−0.000551146471, −0.000022307370]. This interval conditions on three already fitted seeds. Removing seed 43 reverses the mean difference: +0.000257549856, interval [+0.000013935314, +0.000515424851]. A stable advantage over training randomness is therefore **INCONCLUSIVE**, not established by the headline interval.

**VERIFIED RESULT / OBSERVED:** Fine-tuned JEPA beats the validation-selected GJR-GARCH-t implementation by 11.9904% in mean pinball, with a substantially negative conditional interval. The supervised model already accounts for about 95.23% of that absolute neural/classical gap. Frozen JEPA has higher aggregate pinball than its matching supervised control for all three seeds. The evidence supports a neural forecasting advantage over these fitted comparators on this month, rather than a large or general JEPA-specific contribution.

**INFERRED:** For the proposed empirical publication claim, this audit recommends fresh temporal evaluation, additional paired training seeds, sharper controls and a stronger comparator/fit-acceptance protocol. These are evidence-based recommendations, not universal venue requirements. No finding invalidates every V1 score. Two HIGH findings concern generalization and pretraining-superiority claims; several MEDIUM findings constrain interpretation and publication design. There is no confirmed BLOCKER-level corruption or leakage in the bounded pilot.

## 2. Repository and commit identification

| Item | Audited identity |
|---|---|
| Repository | https://github.com/Neal-Salian/SolarJEPA.git |
| Local root | /Users/nealsalian/Desktop/SolarJEPA |
| Active branch / upstream | v1 / origin/v1 |
| HEAD and remote at audit entry and resumption | 3dbd67abad753c086dec51d0f8cf3b6382bfd10b |
| Executed strict-run source commit | 4a3f88227ce28dea0e885e68987282285963f38e |
| Original run directory | results/experiments/v1-full-20261009 |
| Source fingerprint | e4418cd34a326e9e429df87214182253ca2b050f7d6fba593ead54e7bd2467d2 |
| summary.json SHA-256 | 80eae588a706e4b4d84df0daa7e03dcfc54c53ee408d2d6aed30e4bcb9988daf |
| per_origin.json SHA-256 | 133025c6921bcd575b727287b504550ff15e6e1d3ade8bcc39a5ff432056aa7f |
| test_predictions.npz SHA-256 | 59bcd596fefd6b10edeec93a69d7172343d4ffb7dc120f98a5185c1e35a3da82 |
| Frozen model configuration SHA-256 | a7b9cb5606c108fc65fc542d4ee1a9544c604555c59e24810a565622d7854508 |
| Frozen experiment configuration SHA-256 | 230a3037910d995e8113ae90e69dc8e71c0ad8e26e89ecc4628c4dd8c31daccb |

**OBSERVED:** Fetched all remotes, switched to v1 and verified tracking. The tracked tree was clean. Pre-existing .agents/ and docs/P1_FINAL_INTEGRATION_REAUDIT.md were preserved; their file hashes were captured before review. A 235-file initial identity snapshot covers tracked files, these untracked files and original V1 execution artifacts. No source, model, configuration, raw-data, original result, existing report, index or branch was changed by reviewers. Only this document and V1_PUBLICATION_ROADMAP.md are delivery changes. Publication of these documents must stop if origin/v1 advances unexpectedly; no merge or overwrite is authorized.

## 3. Scientific audit methodology

Read AGENTS.md, V1_PLAN.md, V1_RUN.md and V1_RESULTS.md in order. Inspected code, configurations, manifests, tests, Git history, NetCDF measurements, saved model records, checkpoints, NPZ arrays and per-origin losses. Reports and earlier reviews were treated as claims to test.

Three separate reviewers examined (A) data and reproducibility, (B) architecture/training and baseline fairness, and (C) statistics. The coordinator separately inspected critical source paths and assessed literature/publication readiness. Reviewers produced independent calculations before synthesis; initial usage-limit interruptions were resumed from preserved scratch evidence. This is independent checking within the same project checkout and host, not an external laboratory replication or a blinded review.

Evidence labels: **DOCUMENTED** means supported by an authoritative document; **OBSERVED** means direct code/file/execution evidence; **INFERRED** identifies an interpretation; **UNKNOWN** identifies an unresolved quantity. Result statuses are **VERIFIED RESULT**, **REPORTED BUT NOT INDEPENDENTLY VERIFIED**, **INCONCLUSIVE RESULT**, and **UNSUPPORTED CLAIM**. Severity measures the impact on a scientific claim, not implementation effort. Absence of evidence is not automatically a defect.

Fresh executed checks included:

| Check | Independent result |
|---|---|
| Full .venv/bin/python -m pytest -q | 1,171 passed, 1 warning, 89.47 s |
| .venv/bin/python -m pip check | No broken requirements found |
| Raw manifest/file identities | 123 files, 36,535,474 bytes, all SHA-256/size matches |
| Raw timing, masks, windows and target alignment | Reconstructed directly from NetCDF; matches saved support and NPZ |
| Log score/per-origin/lead/quantile checks | 270 checks, maximum absolute discrepancy 9.99e−16 |
| Native metric/quantile-loss checks | 60 checks, maximum discrepancy 9.89e−19 |
| Test-model inventory | 22 matching model IDs in summary/NPZ: 6 point, 7 statistical probabilistic and 9 neural |
| Runner bootstrap contrasts | All 120 reproduce exactly |
| Neural checkpoint replay | All 9 reproduce every saved test point and quantile bitwise |
| Validation selection replay | All selected epochs are recorded minima; normalized loss difference ≤5.20e−9 from float precision; dex loss difference <1e−14 |
| Source and installation identity | All 53 recorded source identities and 35 installed module identities match |
| Statistical GJR prediction replay | Reproduces from stored parameters without refitting |

The warning is the existing NumPy ndarray-size warning in test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability: expected 16 from C header, got 96 from PyObject. Its cause and numerical impact are UNKNOWN; neither a clean scientific bill of health nor demonstrated corruption follows from it.

No expensive training, fresh end-to-end comparison, data acquisition or model fitting was performed in this audit. Independent formulas, analysis logs and machine-readable evidence are local scratch under /var/folders/51/8f1_33wn46d2ytlgwfhqvg2m0000gn/T/solarje-v1-audit-pjxnviq_/. The essential methods and principal measurements are recorded here so conclusions do not depend on private reviewer summaries. Scratch is not a publication archive.

Source references throughout this report resolve to the following exact repository paths; the listed functions locate the evidence behind module-name shorthand in the findings.

| Module / configuration | Primary evidence entry points |
|---|---|
| [src/solar_flare_jepa/data/goes.py](../src/solar_flare_jepa/data/goes.py) | _times, read_goes; status/electron/count/flux rules at lines 48–73 |
| [src/solar_flare_jepa/data/foundation.py](../src/solar_flare_jepa/data/foundation.py) | validate_goes_files, goes_training; coverage validation and retrospective availability |
| [src/solar_flare_jepa/forecasting/splitting.py](../src/solar_flare_jepa/forecasting/splitting.py) | chronological_partitions |
| [src/solar_flare_jepa/forecasting/windows.py](../src/solar_flare_jepa/forecasting/windows.py) | build_partition_windows, feature_eligibility, target_eligibility; support and exclusions |
| [src/solar_flare_jepa/training/normalization.py](../src/solar_flare_jepa/training/normalization.py) | Normalization.fit; unique raw-training statistics |
| [src/solar_flare_jepa/training/jepa.py](../src/solar_flare_jepa/training/jepa.py) | training_windows, build_jepa_model, pretrain_jepa, _validation_pinball, fit_forecaster, TrainedJepa.predict/load |
| [src/solar_flare_jepa/forecasting/baselines.py](../src/solar_flare_jepa/forecasting/baselines.py) | DirectRidge._fit/_predict and the six point comparators |
| [src/solar_flare_jepa/forecasting/statistical.py](../src/solar_flare_jepa/forecasting/statistical.py) | PersistenceEmpirical, ARIMA._fit/_predict, Volatility._multistart/_fit/_predict |
| [src/solar_flare_jepa/evaluation/probabilistic.py](../src/solar_flare_jepa/evaluation/probabilistic.py) | log_scores, block_bootstrap |
| [src/solar_flare_jepa/experiments/v1.py](../src/solar_flare_jepa/experiments/v1.py) | _strata, _score, run_v1 and its evaluate closure; selection/execution order |
| [src/solar_flare_jepa/experiments/provenance.py](../src/solar_flare_jepa/experiments/provenance.py) | source_fingerprint, code_provenance |
| [configs/experiments/v1_goes_2024.json](../configs/experiments/v1_goes_2024.json) | Chronology, context_steps=120, horizon_steps=30, stride_steps=30, direct-ridge lag_steps=10/alpha=0.1, equal-channel/lead evaluation |
| [configs/experiments/v1_models.json](../configs/experiments/v1_models.json) | Statistical candidates and all JEPA/training settings, including seeds and auxiliary weight=0.0 |

## 4. Dataset integrity findings

**VERIFIED RESULT / OBSERVED:** The native time axis contains exactly 177,120 consecutive one-minute bins over [2024-05-01T00:00Z, 2024-09-01T00:00Z). All 177,119 adjacent deltas are 60 seconds. There are zero duplicate or absent timestamps and no contradictions between measured coverage and file coverage metadata. Filename dates were not substituted for measured coverage.

| Month / tracked manifest | Files | Rows | Bytes |
|---|---:|---:|---:|
| May / data/manifests/goes_v1_202405.json | 31 | 44,640 | 9,169,020 |
| June / data/manifests/goes_v1_202406.json | 30 | 43,200 | 8,910,715 |
| July / data/manifests/goes_p2_july2024.json | 31 | 44,640 | 9,200,347 |
| August / data/manifests/goes_v1_202408.json | 31 | 44,640 | 9,255,392 |

Continuous timestamps do not mean continuous valid observations. [src/solar_flare_jepa/data/goes.py:48](../src/solar_flare_jepa/data/goes.py#L48) and line 68 apply the selected primary corrected flux quality policy: finite positive flux, acceptable status, positive averaged-measurement count up to 60 and channel-specific electron-contamination handling. NetCDF attributes and the [NOAA XRS L2 guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf), sections 2.1, 2.4 and 4, support the science/operational distinction, UTC epoch and variable/flag semantics. Leap seconds are neglected by the product's stated time encoding; no alternative clock was invented.

| Quality measure | XRS-A | XRS-B |
|---|---:|---:|
| Valid bins under actual policy | 172,646 | 174,845 |
| Invalid bins | 4,474 | 2,275 |
| Raw nonfinite flux | 2,153 | 2,153 |
| Finite nonpositive flux | 0 | 0 |
| Longest invalid-bin run | 263 minutes | 245 minutes |
| Valid averages containing fewer than 60 samples | 11,237 | 2,440 |
| Valid averages containing fewer than 30 samples | 177 | 179 |

The minimum accepted count is one. This follows the explicit policy and is not evidence of a parser bug or a documented requirement for a different threshold. It means effective measurement support varies; sensitivity needs physical justification rather than an invented quality cutoff. Status, electron and count rejection sets overlap and must not be added as disjoint counts.

Both features and targets are XRS-A/XRS-B primary corrected irradiances in W/m², transformed as log10(F / 1 W/m²). No imputation or invented observation is used in these retained complete windows. The [NOAA readme](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf) identifies science products as retrospectively corrected/calibrated; they are suitable for a retrospective benchmark but do not establish real-time availability.

| Partition, UTC half-open | Raw rows | Candidate origins | Retained | Excluded unique |
|---|---:|---:|---:|---:|
| Train, May 1–July 22 | 118,080 | 3,936 | 3,609 | 327 |
| Validation, July 22–August 1 | 14,400 | 480 | 412 | 68 |
| Test, August 1–September 1 | 44,640 | 1,488 | 1,436 | 52 |

All models use the same 1,436 retained test origins and 86,160 valid cells (30 leads × 2 channels). Of the 52 excluded test candidates, four lack support before the partition boundary and 48 fail quality eligibility. Invalid-feature/invalid-target counts are 39/12, with three shared exclusions; exclusion-reason counts overlap. Complete-case support deliberately excludes missing/flagged contexts and future targets; performance is conditional on that population, not the entire archive or all operational issue times.

## 5. Leakage assessment

| Mechanism | Assessment | Concrete evidence / limit |
|---|---|---|
| Split contamination | NO LEAKAGE FOUND | chronological_partitions, src/solar_flare_jepa/forecasting/splitting.py:63; window support bounds in windows.py:128,177,235. Entire retained context-plus-target support lies within its partition. First issue is 02:00 on each partition's first day. |
| Normalization or preprocessing fitted on future data | NO LEAKAGE FOUND | training/normalization.py:80; jepa.py:547. Recomputed unique raw-training counts A/B 113,926/116,125; means −6.9751727621/−5.4752957945; stds 0.5742480619/0.3415974219 dex match all nine checkpoints exactly. |
| JEPA training windows reaching held-out data | NO LEAKAGE FOUND | jepa.py:179,187,200,548. 108,199 eligible stride-1 windows, deterministically reduced to 20,000; last selected support ends July 21 at 23:55 UTC. |
| Target encoder exposing future observations at inference | NO LEAKAGE FOUND | jepa.py:317 versus 327: forecast takes only 120 context rows; teacher sees future only during training. Poisoning EMA target weights with NaNs leaves test predictions unchanged. |
| Target misalignment / overlapping test targets | NO LEAKAGE FOUND | Independent raw/NPZ equality; first target starts at issue, latest context ends by issue. All 43,080 target minute bins are unique. Contexts overlap by 90 minutes at adjacent stride-30 origins; this creates dependence, not cross-split target contamination. |
| Validation/checkpoint selection using test outcomes | NO LEAKAGE FOUND in automated path | jepa.py:497,507,595; v1.py:165–174. Selected neural epochs replay as validation minima; ARIMA order is chosen by validation dex pinball. Absence of undocumented manual experimentation is INSUFFICIENT EVIDENCE. |
| Retrospective strata as inputs | NO LEAKAGE FOUND | v1.py:33–43 creates future-conditioned evaluation annotations; forecast inputs are unchanged. Strata do not establish event labels. |
| True operational availability | INSUFFICIENT EVIDENCE | availability_mode=retrospective_bin_end; data/foundation.py:18,223. Bin end is a benchmark assumption, not observed downlink/product latency. Retrospective revisions may use information unavailable online. |
| Repeated test access and future research tuning | POTENTIAL LEAKAGE for future confirmatory claims | Prescribed smoke scores August; v1.py:137–204 evaluates test models before all subsequent fits/selections finish. Config hashes stayed unchanged and no automated test-based selector was found. August has now been inspected repeatedly and cannot be called a new untouched test for follow-up design. |

**CONFIRMED LEAKAGE:** None demonstrated. This conclusion covers the inspected data/code/artifacts, not unknown private actions or operational data provenance. Overlap within training or successive causal contexts is not itself leakage. The runner docstring's literal claim that test is scored once after all selections are frozen is contradicted by execution order; the original results document already clarifies this. That discrepancy does not demonstrate test-informed tuning.

## 6. JEPA architecture assessment

**OBSERVED:** [src/solar_flare_jepa/training/jepa.py:250](../src/solar_flare_jepa/training/jepa.py#L250), build_jepa_model, implements a legitimate JEPA-style latent-prediction recipe:

- Five-minute nonoverlapping patches concatenate two channels and validity masks. Learned positions feed a width-32, depth-3, four-head Transformer context encoder; the EMA target encoder copies that architecture.
- A depth-2 Transformer predictor receives visible context embeddings plus learned mask queries. Pretraining hides a contiguous four-patch context block and all six future patches; the teacher encodes the full 150-minute training window without gradients. Visible context never receives future measurements.
- Smooth-L1 predicts normalized teacher embeddings. Teacher weights update by EMA, linearly scheduled from 0.996 to 1.0 across pretraining steps. Noncausal attention within an already observed context or among mask queries does not introduce measured future inputs.
- A 128-hidden-unit head combines mean context embeddings and predicted future embeddings, and directly predicts 30 × 2 × 5 quantiles. Softplus cumulative increments impose quantile order.

**INFERRED:** This satisfies the main JEPA principles: asymmetric context/target views, latent prediction, stop-gradient target and EMA. It is an adaptation of established components, not demonstrated architectural novelty. Training loss decreases and nonzero latent variance/effective rank are useful diagnostics but do not prove semantically useful or physically meaningful representations. Frozen-random features are not evaluated.

| Actual capability | Assessment |
|---|---|
| JEPA representation pretraining | Implemented and verified in code/checkpoints |
| Supervised direct multi-horizon quantile forecasting | Implemented; includes no-pretraining control |
| Neural autoregressive rollout | Not implemented in this forecasting path; all horizon outputs are predicted directly |
| Generative neural trajectory sampling / joint predictive density | Not implemented; five marginal quantiles do not define a joint trajectory model |
| Classical autoregressive/simulated trajectories | Implemented in statistical baselines; does not make the neural JEPA a generative model |
| Physics-informed loss / physical dynamical constraint | Not implemented in V1; units, log transform and positivity are not physical dynamics |
| Validated Aditya-L1 / SoLEXS model result | Absent; V1 uses GOES only, SoLEXS remains gated |

This agrees with I-JEPA's explicitly non-generative framing in [Assran et al. (CVPR 2023)](https://arxiv.org/abs/2301.08243). A generative decoder could be added in later research, but planned components are not present evidence.

## 7. Training methodology assessment

**OBSERVED:** Frozen configs set AdamW learning rate 0.001, weight decay 0.0001, gradient norm cap 1, dropout 0, batch 256, eight pretraining epochs and at most 15 supervised epochs, patience 3, CPU threads 4, seeds 17/29/43. There is no learning-rate scheduler; the EMA schedule is not an LR schedule. Deterministic PyTorch operations and Python/NumPy/Torch seeds are set in jepa.py:401. Each epoch shuffles the same deterministic subset; supervised training and JEPA fine-tuning reset the same downstream shuffle protocol.

The architecture, initial seed, head initialization, subset, downstream optimizer and selection rule are matched. Actual jepa_weight_during_finetune is **0.0**, so there is no auxiliary JEPA-loss confound during the V1 fine-tuning stage. Frozen encoder/predictor fingerprints remain unchanged during head training. Architecture counts are 39,808 encoder + 28,576 predictor + 67,948 head = 136,332, excluding the separate 39,808 EMA parameters; frozen optimization updates only the head.

**INFERRED:** The control validly tests adding the JEPA pretraining stage to this architecture/downstream recipe. It does not distinguish JEPA-objective-specific representation benefit from extra optimization, alternative pretexts, or selected training exposure. JEPA adds 8 × 79 = 632 encoder/predictor updates. Selected epochs are 5/9/12 for fine-tuned JEPA versus 15/9/8 for supervised. Different selected epochs are a normal consequence of shared early stopping, not leakage, but prevent a claim of equal total compute.

**OBSERVED:** Neural training/selection pinball uses training-standardized log targets, whereas classical selection and final scoring use dex. The training scales imply relative channel weighting 37.30% A / 62.70% B (B/A 1.68107), versus 50/50 in final dex scoring. This applies equally to JEPA and supervised and therefore does not itself prove differential confounding. Whether equal-dex validation selection changes checkpoints/conclusions is UNKNOWN without archived epoch predictions or new training.

## 8. Baseline fairness assessment

| Comparator | What is fair / verified | Qualification |
|---|---|---|
| Supervised neural control | Same architecture, data subset, seed/init, full context, head, masks, optimizer and downstream selection | Extra pretraining budget is unmatched; only three seeds; no alternative-pretext or compute control |
| Frozen JEPA | Same pretrained encoder/predictor, forecast head and evaluation support | Tests frozen transfer, not an equal-capacity trainable model; no frozen-random control |
| ARIMA | Four (p,1,q) orders, p/q in {1,2}/{0,1}, train-only parameter fitting; validation selects (2,1,0); all channel fits report convergence | Per-channel Gaussian log-space model; fixed parameters re-filter the latest 120-minute context. Small grid does not represent classical methods generally |
| Constant/ARCH/GARCH/GJR | Common two-stage train-only OLS AR(1) mean on log differences; multi-start variance fitting; same origins/horizon/masks; 1,000 simulated paths | Residuals concatenate across quality gaps; simulation variance, fit feasibility and stationarity need qualifications |
| Empirical persistence | Train-only per-lead log-increment quantiles, observed issue-time anchoring | Pools regimes; its median is not exactly last-value persistence |
| Six P2 point baselines | Same retained evaluation population and units | Point-only models cannot enter pinball comparisons without a distribution model |
| Direct ridge | Valid train-only fitted point comparator | Only 3,609 stride-30 windows and 10-minute lags, versus 20,000 neural windows and full 120-minute context; not a fully information/budget-matched neural alternative |

Statistical source: [src/solar_flare_jepa/forecasting/statistical.py:143](../src/solar_flare_jepa/forecasting/statistical.py#L143), ARIMA; lines 270–309, Volatility._multistart; lines 318 onward, two-stage fit/simulation. _multistart chooses the largest finite likelihood even when convergence_flag is nonzero. Saved GARCH-normal and GARCH-t XRS-A fits have flag 8 and persistence 1.00019909596 / 1.00002475369 despite converged alternative starts. Thus zero recorded model exceptions does not mean every variance optimization succeeded.

The validation-best GJR-t has flags [0,0] and A/B persistence 1.00000147383 / 0.95851483707. The XRS-A stationarity inequality is violated by 1.47e−6; positivity inequalities pass. This is a near-boundary numerical qualification, not proof that its saved finite-horizon forecasts are invalid. No undocumented tolerance or stationary unconditional variance is assumed. ARCH/ACF diagnostics demonstrate conditional structure in the processed training series, not adequacy of these fitted models; concatenating residuals across gaps approximates temporal dynamics.

Replaying GJR from saved parameters is exact. Changing its simulation seed from 0 to 1/2 at 1,000 paths changes mean pinball from 0.04459183950 to 0.04455360437/0.04453959309. This Monte Carlo sensitivity is small relative to the 0.00535 neural/GJR gap. It does not resolve fitting uncertainty.

**INFERRED:** Comparisons are fair in target, timing, masks and evaluation population. Neural-control capacity is matched. Training information, context use, objective/selection weighting and comparator strength are not uniformly matched across families. No extra held-out training information was found. Better scores than these implementations do not prove superiority to all classical methods or modern supervised forecasters.

## 9. Statistical significance assessment

**VERIFIED RESULT:** Every runner bootstrap contrast and all checked metric arithmetic reproduce. Negative differences below favour the first method. Neural-family metrics average losses of three fitted seeds, not predictions of a three-model ensemble.

| Fitted-model contrast | Dex pinball difference | Original daily-block 95% interval |
|---|---:|---|
| Fine-tuned JEPA − supervised | −0.000255125056 | [−0.000551146471, −0.000022307370] |
| Frozen JEPA − supervised | +0.001929797466 | [+0.001385275712, +0.002548373654] |
| Fine-tuned JEPA − empirical persistence | −0.006608072214 | [−0.007784477698, −0.005499883605] |
| Fine-tuned JEPA − selected GJR-t | −0.005346746777 | [−0.006442474166, −0.004313065518] |
| Fine-tuned JEPA − selected ARIMA | −0.008337321811 | [−0.009324443463, −0.007358578182] |

The bootstrap in [src/solar_flare_jepa/evaluation/probabilistic.py:84](../src/solar_flare_jepa/evaluation/probabilistic.py#L84) correctly pairs origins and resamples whole UTC issue-date loss sums/counts, preserving the origin-weighted mean despite 42–48 origins per day. There are 31 day blocks. Test target intervals do not overlap; observed contexts do, and evolving solar activity still induces dependence. Treating 86,160 cells as independent samples would be incorrect. Daily blocks retain within-day dependence but do not prove across-day independence, stationarity or nominal interval coverage.

| Matching training seed | Fine-tuned − supervised pinball | Daily 95% interval |
|---|---:|---|
| 17 | +0.000431818008 | [−0.000026998927, +0.000819475245] |
| 29 | +0.000083281704 | [−0.000271280825, +0.000459744834] |
| 43 | −0.001280474879 | [−0.001981236444, −0.000729293690] |

Independent exploratory sensitivities use fixed predictions, no retraining/reselection:

| Sensitivity for JEPA − control | Difference / interval | Interpretation |
|---|---|---|
| Circular contiguous 2-day blocks, 20,000 draws | [−0.000564046001, −0.000044419812] | Fixed-seed contrast stays negative |
| Circular 3-day blocks | [−0.000549866188, −0.000055469011] | Same |
| Circular 7-day blocks | [−0.000518831016, −0.000066987745] | Same; only ~4.4 block lengths in record |
| Omit seed 43, original daily bootstrap | +0.000257549856; [+0.000013935314, +0.000515424851] | Direction reverses |
| Crossed empirical seed/day resampling | [−0.001240843213, +0.000511720414] | Illustrates omitted seed uncertainty; three seeds do not support a reliable population CI |
| Remove August 5, daily resampling | −0.000141171394; [−0.000297254866, +0.000017038891] | Most influential day contributes 46.5% of net gain; interval spans zero |

Circular methods sample blocks of consecutive calendar days, concatenate and trim to 31 days, preserve paired sums/counts and wrap August 31 to August 1; seed 17. This wrap and short record limit interpretation. Influence deletions were chosen after inspection. They are not alternative confirmatory tests or evidence that August 5 should be discarded. Longer blocks do not erase the fitted-seed gain; seed instability, scope and practical size are the central issues.

**Practical and metric sensitivity:** Fine-tuned/control log MAE difference is −0.001392231906 dex (1.1800% reduction), daily interval [−0.002136372711, −0.000746305579]. Native MAE improves 2.0393%; the mean of individual-seed native RMSEs improves 4.5358%. No minimum meaningful operational benefit was prespecified. A dex loss difference is not a percentage flux change. About 97.95% of net pinball improvement comes from XRS-B; A's exploratory interval spans zero. All 30 aggregate JEPA/control lead means improve, but only 10 unadjusted lead intervals exclude zero. Against GJR, JEPA has higher pinball at leads 1–5, despite better overall loss.

**Calibration and extremes:** Fine-tuned JEPA's achieved 90% coverage is 89.7199% overall, 87.0257% for A and 92.4141% for B; its 50% coverage is 45.9173% versus supervised 48.4420%. Aggregate 90% coverage hides compensating channel errors. On 193 M+ origins, achieved 90% coverage is 77.3604%; on 112 rising×2 origins it is 63.2192%. These strata condition on realized future outcomes, so nominal marginal coverage need not hold within them; they are achieved-tail-performance diagnostics, not clean calibration hypothesis tests. M+ JEPA/control pinball is worse by +0.001102675537, exploratory interval [−0.001064200374, +0.002708237268]; rising-target advantage is also inconclusive. There are zero quiet<C1 test origins and no independent event labels. The largest-rise figure misses the observed sharp peak with all displayed upper bands.

**Multiplicity and prespecification:** The original plan fixes splits, model families, three seeds, metrics and daily comparisons to classical references. It does not fix a primary endpoint, seed-mean/control bootstrap estimand, multiplicity family or seed-population analysis. The report adds 12 matching-seed and 16 seed-mean comparisons to the 120 runner intervals. Individual correlated intervals are not simultaneous evidence; bootstrap fraction 0.985 is neither a posterior probability nor a calibrated p-value. Exploratory widening to 99.375% for eight family pinball comparisons spans zero; this is sensitivity, not a proven familywise guarantee.

Paired block resampling is appropriate to explore common-sample forecast differences; future confirmatory use needs dependence diagnostics and a prespecified endpoint/family. A Diebold–Mariano-style HAC loss-difference test could provide sensitivity under suitable stationarity/weak-dependence assumptions and a defensible bandwidth. It does not solve three-seed uncertainty, model selection, solar-regime shift or repeated test inspection. No DM test or inferential p-value was blindly applied. See [Diebold and Mariano (1995)](https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524599) and [Politis and Romano (1994)](https://www.jstor.org/stable/2290993). Quantile/interval scores should be assessed jointly with calibration and sharpness, as developed by [Gneiting and Raftery (2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).

## 10. Reproducibility assessment

| Level | Verdict | What is actually established |
|---|---|---|
| A. Saved-checkpoint predictions | VERIFIED RESULT | All nine replay bitwise on the current CPU host; raw contexts/targets, source and installed module identities match |
| B. Training from scratch | REPORTED BUT NOT INDEPENDENTLY VERIFIED as a replication | Original histories/checkpoints support that training occurred; this audit did not repeat training or compare two independent training executions |
| C. Scientific conclusions | Narrow numerical contrasts VERIFIED; general superiority INCONCLUSIVE | Arithmetic and fixed-model uncertainty reproduce; new periods, seed populations and operational performance remain unestablished |

**OBSERVED:** Python 3.13.3, macOS arm64, Mac14,2, 8 GiB RAM; Torch 2.6.0, NumPy 2.2.6, pandas 2.3.3, xarray 2026.7.0, netCDF4 1.7.2, statsmodels 0.14.5, arch 7.2.0, SciPy 1.18.1, patsy 1.0.3. Current versions match the tracked lockfile and retained installation evidence. CPU threads/seeds/configuration are saved per neural run. A normal package installation matches checkout source.

**LOW provenance gap:** experiments/provenance.py:93 omits requirements-v1-lock.txt and requirements-training-lock.txt from the executed source manifest; line 167 omits statsmodels/arch/scipy/patsy from the summary's package inventory. Lockfiles and installation logs exist, but the run envelope alone is incomplete for these statistical dependency identities. This does not contradict current replay. A publication artifact bundle should include lockfile hashes, full dependency inventory, artifact checksums and documented reload commands outside Git's protected bulk-data paths.

**UNKNOWN:** Exact reproduction on M4/16 GB, MPS, another OS or a new training process. MPS was not used and is not required to validate a CPU-only claim. Lack of M4 hardware does not invalidate this run; it limits a platform-specific reproduction statement. The two historic source-metadata guard refusals are supported by retained logs; their external cause remains unknown. This audit's source checks passed without disabling guards.

## 11. Literature and novelty assessment

Searches used primary arXiv papers, publisher pages, official NOAA/ISRO sources and Paperclip arXiv discovery/readouts. Paperclip surfaced LaT-PFN and TS-JEPA, whose relevant text was read and cross-checked against primary records. This was a targeted reconnaissance as of 2026-10-10, not an exhaustive systematic solar-physics review. Search absence cannot establish a first-in-field claim. Preprints are identified as such; cited prior performance was not independently reproduced here.

| Primary source verified | Relevant prior contribution | Implication for SolarJEPA |
|---|---|---|
| [Assran et al., Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture (CVPR 2023)](https://arxiv.org/abs/2301.08243) | Non-generative latent target prediction with an asymmetric context/target design | JEPA and its core mechanism are prior art |
| [Verdenius, Zerio and Wang, LaT-PFN (arXiv 2024)](https://arxiv.org/abs/2405.10093) | JEPA integrated with PFN for time-series forecasting | JEPA applied to forecasting is not new in V1 |
| [Ennadir, Golkar and Sarra, Joint Embeddings Go Temporal (arXiv 2025; record notes NeurIPS 2024 workshop)](https://arxiv.org/abs/2509.25449) | TS-JEPA patch/encoder/predictor/EMA framework; classification and forecasting | Temporal JEPA is established; differentiate the solar task, protocol or an actual new mechanism |
| [Feng et al., Does Joint-Embedding Predictive Architecture Pretraining Help Time Series Forecasting? (arXiv, September 2026)](https://arxiv.org/abs/2609.31680) | Reports gains/degradation varying by backbone across multiple benchmarks | A single-backbone application cannot establish general JEPA superiority |
| [Nie et al., A Time Series is Worth 64 Words (ICLR 2023)](https://arxiv.org/abs/2211.14730) | PatchTST supervised and masked-pretraining time-series forecasting | Patching/Transformers alone are not a novel contribution; a relevant stronger comparator exists |
| [Huang et al., Predicting short-term X-ray flux with deep learning model (Astronomy and Computing 57, 101166, 2026)](https://www.sciencedirect.com/science/article/pii/S2213133726001083) | Publisher preview compares short-term GOES X-ray forecasters including iTransformer, recurrent models and MLP | Continuous short-term X-ray forecasting has prior work; preview was accessible, full paper not assessed. Different data/protocol prevent metric leaderboard comparisons |
| [Barnes et al., A Comparison of Flare Forecasting Methods, I (2016)](https://arxiv.org/abs/1608.06319) | Common datasets, consistent event definitions and verification statistics | Continuous flux loss is not a substitute for event-warning skill |
| [Gneiting and Raftery (JASA 2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf) | Proper quantile/interval scoring and calibration/sharpness principles | Five-quantile pinball is legitimate but is not exact CRPS or a full distribution |
| [Official ISRO/ISSDC Aditya-L1 portal](https://pradan.issdc.gov.in/al1/) and [SoLEXS ground calibration/in-flight performance paper (arXiv 2025)](https://arxiv.org/abs/2509.26292) | SoLEXS is a distinct spectral instrument with its own calibration | GOES results do not validate Aditya-L1 processing or make SoLEXS counts equivalent to GOES classes |

**INFERRED:** The current contribution is mainly empirical/application-oriented: a small, provenance-conscious two-channel GOES benchmark testing a lightweight JEPA recipe against explicit statistical and neural controls. Reproducible negative findings are valuable. Architecture novelty, uniqueness of JEPA-on-solar-flux, and novel physical insight remain UNKNOWN or unsupported; a first-application claim requires a much broader related-work search.

The original physics-informed, generative, Aditya-L1 ambition is still a research objective. README.md explicitly calls the title provisional and cautions against those capability claims. V1 has no physical evolution constraint, neural trajectory generator or validated SoLEXS forecast. Prior work on photovoltaic-power forecasting, proton-flux forecasting or flare-atmosphere inversion should not be presented as directly comparable XRS forecasting evidence simply because it contains solar/physics terminology.

## 12. Publication readiness verdict

| Dimension | Assessment |
|---|---|
| Engineering readiness | Strong for repeating this bounded CPU benchmark with available local artifacts; not operational deployment readiness |
| Experimental validity | Supported for conditional, retrospective complete-case flux forecasting; baseline optimization and objective alignment require qualification |
| Statistical validity | Arithmetic sound; exploratory fitted-model CIs credible within assumptions; training-population and broad scientific significance inconclusive |
| Scientific contribution | Plausible application study, without demonstrated methodological novelty or robust pretraining-specific gain |
| Publication readiness | **NOT_READY** for the broad research claims in the project ambition; the roadmap recommends a minimum evidence package for the proposed application claim |

A workshop demo or transparent technical report may describe this pilot accurately now. That is not equivalent to a completed research submission demonstrating general, physically informed or operational solar-flare forecasting. Venue-specific acceptance is UNKNOWN; the audit does not invent a journal's requirements.

## 13. Evidence-backed findings

### F01 — Fixed-seed interval exclusion does not establish stable pretraining benefit

Finding ID: F01. Severity: **HIGH**. Category: Statistical inference.

Description: The small average improvement depends on one of three training seeds; the reported CI fixes those seeds.

Evidence: Section 9's independently reproduced per-seed and leave-one-seed-out contrasts; probabilistic.py:84–105 resamples time blocks only. Omitting seed 43 reverses mean and daily interval direction.

Scientific impact: A general claim that JEPA pretraining reliably improves this architecture is unsupported, even though its particular three-seed mean improves.

Recommended action: Prespecify the seed/time estimand and collect additional paired seeds with controls on fresh evaluation periods (R01, R03, R04).

Confidence: High for the measured sensitivity; population-of-seeds performance UNKNOWN.

### F02 — Temporal and solar-regime generalization is untested

Finding ID: F02. Severity: **HIGH**. Category: Experimental completeness.

Description: One GOES-16 test month has no quiet-stratum origins and no event-catalog evaluation.

Evidence: Frozen split config; all 1,436 issues are in August 2024; quiet<C1 n=0; M+ n=193 and rising n=112 are retrospective flux strata, not independent events (v1.py:33–43).

Scientific impact: Cycle-wide, other-satellite, quiet-regime and genuinely pre-onset flare-warning claims are unsupported.

Recommended action: Evaluate a frozen protocol on multiple separated temporal regimes; use catalog-based pre-onset analysis if a flare-warning claim is retained (R04, R06).

Confidence: High; the unmeasured regimes remain UNKNOWN.

### F03 — Pretraining-objective specificity and representation utility are unresolved

Finding ID: F03. Severity: **MEDIUM**. Category: Ablation / training.

Description: The architecture-matched recipe comparison is valid, but there is no compute-matched supervised/alternative-pretext arm or frozen-random feature control.

Evidence: jepa.py:456–494 adds 632 updates; fit_forecaster:526–624 shares downstream settings; auxiliary weight=0.0. Frozen JEPA loses to supervised, while rank statistics alone cannot establish utility.

Scientific impact: Cannot isolate a uniquely beneficial latent objective from extra optimization or characterize the value of the frozen representation.

Recommended action: Add minimal budget-matched and frozen-random controls; consider a reconstruction pretext only if needed to defend objective-specific novelty (R03).

Confidence: High for missing controls; their effect on rankings is UNKNOWN.

### F04 — Some variance fits are accepted despite optimizer failure

Finding ID: F04. Severity: **MEDIUM**. Category: Baseline validity.

Description: Highest finite likelihood is used regardless of convergence/constraint feasibility.

Evidence: statistical.py:302–306; saved GARCH XRS-A flag=8 with converged alternative starts and persistence above 1. Best GJR has flags [0,0] with only a 1.47 ppm boundary violation; finite-horizon predictions remain reproducible.

Scientific impact: Limits blanket GARCH-family superiority and stationary-variance interpretation; does not invalidate the best GJR finite-horizon contrast.

Recommended action: Prespecify convergence/feasibility acceptance and perform train/validation-only sensitivity for a future protocol (R02).

Confidence: High for observed policy/parameters; ranking after a new accepted-fit protocol UNKNOWN.

### F05 — Training/selection and reported scores weight channels differently

Finding ID: F05. Severity: **MEDIUM**. Category: Estimand / fairness.

Description: Normalized neural pinball implicitly weights B/A by 1.68107 while final and classical dex pinball weight channels equally.

Evidence: normalization.py:80–117; jepa.py:507–523; v1.py:167; stored target scales. Approximately 97.95% of net pretraining gain is in B, but causation by weighting is unproved.

Scientific impact: Checkpoint selection answers a different optimization question; this is shared by both neural methods, not demonstrated leakage or asymmetric neural treatment.

Recommended action: Declare a scientifically justified primary metric/weights and align selection in the next frozen protocol (R01).

Confidence: High for weighting; outcome under aligned selection UNKNOWN.

### F06 — Multiplicity and exploratory endpoint selection limit confirmatory language

Finding ID: F06. Severity: **MEDIUM**. Category: Statistical inference.

Description: Many correlated intervals and supplementary seed-mean/control analyses lack a prespecified primary family or simultaneous-error treatment.

Evidence: v1.py:206–224 produces 120 intervals; V1_RESULTS adds 28. V1_PLAN fixes neither a primary endpoint nor the supplementary seed-mean estimator. Bootstrap fractions are resampling frequencies.

Scientific impact: An isolated nominal 95% interval exclusion does not provide familywise error control or account for training-seed uncertainty.

Recommended action: Prespecify the primary contrast/endpoint, label secondary analyses and use a justified multiplicity strategy (R01); keep current analyses exploratory.

Confidence: High.

### F07 — Aggregate uncertainty and horizon skill conceal failures

Finding ID: F07. Severity: **MEDIUM**. Category: Calibration / scientific utility.

Description: Aggregate near-90% coverage hides opposite channel deviations, 50% undercoverage and weak achieved coverage during rising targets; JEPA/GJR lead ordering reverses at short leads.

Evidence: Independent NPZ statistics in section 9; A/B 90% coverage 87.03%/92.41%, rising achieved coverage 63.22%; higher JEPA pinball than GJR at leads 1–5. Future-conditioned coverage caveat applies.

Scientific impact: Neither aggregate loss nor one fan example establishes reliable flare-peak warnings or uniform lead-wise superiority.

Recommended action: Report channel/lead reliability and sharpness, validation-only calibration and catalog-based onset/continuation separation where claimed (R06).

Confidence: High for achieved metrics; operational significance UNKNOWN.

### F08 — Comparator scope and information budgets are limited

Finding ID: F08. Severity: **MEDIUM**. Category: Baseline fairness.

Description: There is no strong full-context quantile-linear or alternative supervised temporal backbone; statistical models are per-channel while JEPA jointly uses both channels.

Evidence: v1_models.json model list; direct ridge uses 10 lags and 3,609 origins versus full neural context/20,000 windows; ARIMA/statistical.py:143 and baselines.py implementations.

Scientific impact: Improvement over this set cannot establish general classical or state-of-the-art superiority; most measured GJR gain is already reproduced by supervised learning.

Recommended action: Add one inexpensive full-context multivariate quantile comparator and one small modern temporal backbone with a bounded validation budget (R05).

Confidence: High for comparator absence; future ranking UNKNOWN.

### F09 — Complete-case quality selection limits the population being forecast

Finding ID: F09. Severity: **MEDIUM**. Category: Data quality / external validity.

Description: Continuous timestamps contain invalid-quality runs, complete-case exclusions and variable sample support within accepted minute averages.

Evidence: Section 4's raw measurements, goes.py:68–73, windows.py:205; 52/1,488 test candidates excluded; accepted counts can be one.

Scientific impact: Reported skill is conditional on complete accepted windows; no missing-data or all-issue-time operational claim follows. No alternative scientifically correct cutoff is established here.

Recommended action: Publish quality/exclusion data cards and justified exposure/missingness sensitivity; do not silently change masks (R01, R06).

Confidence: High for measured selection, medium for downstream impact.

### F10 — Test access order and future reuse need precise wording

Finding ID: F10. Severity: **MEDIUM**. Category: Research procedure / leakage risk.

Description: The literal once-after-all-selection docstring is inaccurate; August is already visible for future design.

Evidence: v1.py:3–5 versus 137–204; smoke instructions; unchanged frozen hashes. No code selector consumes test scores.

Scientific impact: No confirmed historical test tuning, but future experiments designed from this audit cannot present August as fresh confirmation.

Recommended action: Preserve historical results; preregister new held-out periods and clearly separate exploratory from confirmatory reports (R01, R04).

Confidence: High for automated order/access; manual actions UNKNOWN.

### F11 — Reproducibility envelope omits some dependency identities

Finding ID: F11. Severity: **LOW**. Category: Provenance.

Description: The run source manifest excludes V1/training lockfiles and the package inventory omits the statistical dependencies.

Evidence: provenance.py:93,167; current lockfiles/installed versions match and nine-checkpoint replay passes.

Scientific impact: A future reader cannot reconstruct every statistical dependency identity from summary.json alone; current replay evidence is not contradicted.

Recommended action: Archive a complete environment/lock/artifact manifest and an independent replay procedure (R07).

Confidence: High.

### F12 — Model taxonomy and novelty need bounded claims

Finding ID: F12. Severity: **MEDIUM**. Category: Scientific contribution / positioning.

Description: Genuine JEPA-style pretraining is present, but temporal JEPA/patch forecasting have prior art and V1 has no physics-informed, generative neural or Aditya-L1 result.

Evidence: jepa.py:250–359 and actual configs; primary papers in section 11; README's explicit provisional-title warning; GOES-only dataset selection.

Scientific impact: A methodological or physics/generative headline would overstate the implemented and demonstrated contribution.

Recommended action: Position the first paper around a controlled empirical solar-flux question; differentiate related work and defer additional capabilities to explicit scientific hypotheses (R08, R09).

Confidence: High for implemented scope; global first-application novelty UNKNOWN.

## 14. Scientific limitations and unsupported claims

**Supported:** Correctly aligned retrospective conditional forecasts; saved prediction reproducibility; a small fitted-seed JEPA/control mean advantage; larger gains over the implemented classical baselines; frozen JEPA's negative control result; multiple calibration and extreme-case limitations.

**INCONCLUSIVE:** Training-population superiority, practically useful incremental pretraining, universal representation utility, event-onset skill, quiet-regime skill, broader temporal/satellite generalization and performance after a stronger comparator/accepted-fit protocol.

**UNSUPPORTED if asserted:** First temporal JEPA, state-of-the-art solar forecasting, physics-informed dynamics, generative neural trajectories, validated Aditya-L1 forecasting, operational latency guarantees, exact CRPS, calibrated trajectory probability, or 86,160 independent evaluation samples. The current V1 report already avoids several of these claims; this audit is not alleging that every unsupported statement was made by the authors.

**REPORTED BUT NOT INDEPENDENTLY VERIFIED:** The teammate's earlier SARIMA 28-minute failure/joint-mean exploration. SARIMA was excluded before this executed benchmark; absence of a selected lag's ACF peak alone would not rule out all seasonal structure, and no SARIMA result is fabricated here. A second from-scratch training replication and reproduction on M4/MPS or another operating system were not performed or independently verified in this audit; no second training execution is established by the inspected evidence.

## 15. Prioritized recommendations

Detailed experiment definitions, motivations, deliverables, acceptance criteria, estimated costs, data needs and V2 timing are in [V1_PUBLICATION_ROADMAP.md](V1_PUBLICATION_ROADMAP.md).

| Priority / ID | Research gate | Motivating findings |
|---|---|---|
| P0 / R01 | Freeze claim, primary metric/weights, seed/time estimand, quality policy and fresh-test access protocol | F01,F02,F05,F06,F09,F10 |
| P0 / R02 | Establish converged/feasible classical fit acceptance and sensitivity | F04 |
| P1 / R03 | Paired seed extension and minimal JEPA/budget/frozen-random ablations | F01,F03 |
| P1 / R04 | Multiple separated temporal holdouts including lower activity | F02,F10 |
| P1 / R05 | Full-context multivariate quantile baseline plus one small temporal backbone | F08 |
| P1 / R06 | Channel/lead calibration, sharpness, exposure/missingness and conditional onset/continuation evaluation | F07,F09 |
| P1 / R07 | Publication artifact archive and independent replay / one scratch-training replication | F11 |
| P2 / R08 | Selected horizon and second-GOES transfer studies, after core claim survives | F02,F07,F12 |
| P3 / R09 | Gated SoLEXS/physics/generative hypotheses, outside the minimum first-paper route | F12 |

P0 means a validity/design gate for the next confirmatory publication claim, not an instruction to modify V1 retrospectively. No recommended experiment was run as an implementation change during this audit. A well-powered negative pretraining finding is an acceptable outcome; acceptance criteria must not require manufacturing a positive result.

## 16. Final conclusion

V1's engineering and numerical evidence withstand this audit as a small retrospective flux-forecasting pilot. There is no demonstrated temporal leakage, but operational availability is not established. The three fitted seeds have a lower average JEPA loss and a nominal daily-bootstrap 95% interval excluding zero under the stated resampling assumptions. The gain is small and sensitive to training seeds; its practical value and general pretraining benefit remain unestablished. The strongest result is that this neural architecture outperforms the fitted classical comparators in aggregate; supervised learning supplies most of that gain.

**Publication verdict: NOT_READY.** Prioritize an aligned, preregistered and more broadly evaluated empirical benchmark over model scaling, speculative physics terms or unvalidated instrument fusion. Preserve the negative frozen/seed/extreme results. The purpose of V2 should be to resolve these evidence gaps, not defend a preferred winner.

## Appendix A. Compact reproduction of the central fixed-prediction audit

Run from the repository root with the pinned normal installation and existing strict artifacts. This performs no training and does not overwrite results. The principal contrast uses seed-mean losses, not an ensemble forecast.

~~~python
import json
import math
from pathlib import Path
import numpy as np

p = Path('results/experiments/v1-full-20261009')
o = json.loads((p / 'per_origin.json').read_text())['test']
z = np.load(p / 'test_predictions.npz', allow_pickle=False)
assert z['target_mask'].all()
assert np.array_equal(z['origin_ids'], o['origin_ids'])
assert np.array_equal(z['issue_times_ns'], o['issue_times_ns'])
y = np.log10(z['targets'])
levels = np.array([.05, .25, .5, .75, .95])
loss = {}
for i, name in enumerate(z['model_ids']):
    key = f'quantiles_{i}'
    if key in z:
        residual = y[..., None] - np.log10(z[key])
        loss[str(name)] = np.maximum(
            levels * residual, (levels - 1) * residual
        ).mean(axis=(1, 2, 3))
days = z['issue_times_ns'] // (86400 * 10**9)
labels = np.unique(days)
counts = np.array([(days == d).sum() for d in labels])

def contrast(seeds):
    return np.mean([loss[f'jepa_finetune_seed{s}'] -
                    loss[f'supervised_seed{s}'] for s in seeds], axis=0)

def interval(delta, length=1, replicates=2000):
    sums = np.array([delta[days == d].sum() for d in labels])
    starts = np.random.default_rng(17).integers(
        0, len(labels), size=(replicates, math.ceil(len(labels) / length)))
    draw = ((starts[..., None] + np.arange(length)) % len(labels))
    draw = draw.reshape(replicates, -1)[:, :len(labels)]
    means = sums[draw].sum(1) / counts[draw].sum(1)
    return float(delta.mean()), np.percentile(means, [2.5, 97.5])

print('Original daily:', interval(contrast((17, 29, 43))))
print('Without seed43:', interval(contrast((17, 29))))
print('Exploratory seven-day:', interval(contrast((17, 29, 43)), 7, 20000))
~~~

Original data verification is available via scripts/acquire_goes_history.py --verify --manifest for the four tracked manifests; no acquisition is necessary when bytes are present. The nine checkpoint reload checks used training/jepa.py load plus raw reconstructed ForecastContext/FutureGrid support; loaded model records, normalization and each point/quantile array were compared, not merely whether inference returned successfully. Full scripts and detailed JSON evidence remain in the scratch paths recorded in section 3; archive them deliberately if a durable independent audit package is needed.
