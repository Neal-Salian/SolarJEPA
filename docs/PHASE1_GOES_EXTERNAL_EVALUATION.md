# Phase 1: one bounded retrospective January 2025 GOES-16 evaluation

Report date: **2026-10-15, Asia/Kolkata**. **Execution verdict: PASS; independent output audit: PASS.**

**OBSERVED:** One guarded invocation evaluated all nine frozen V1 checkpoints and all 13 restored classical fits on the unchanged January science archive. All mandatory guards passed; no fitting, normalization refit, checkpoint change, model replacement or external-data selection occurred. The complete immutable bundle is retained under ignored `results/experiments/goes-v1-external-january2025-approved-run/`. Source and pinned configuration were not modified for execution.

**OBSERVED:** Fine-tuned JEPA nearly matched supervised controls on mean dex pinball: **0.03900694 versus 0.03911919**, a **0.287%** relative reduction. Seed 17 favored supervised; seeds 29/43 favored fine-tuned JEPA. Every prescribed primary calendar interval includes zero. Frozen JEPA had **0.04212573**, **7.686% higher** than supervised, with higher loss in all three matched seeds. All three neural cohort means had lower dex pinball than the seven restored probabilistic references (**0.04389114–0.04983279**). These are fixed-cohort descriptive observations, not model selection or a statistical superiority claim.

**OBSERVED:** The small fine-tuned aggregate pinball difference masks channel directions: `xrsa_flux` loss was slightly higher than supervised, while `xrsb_flux` loss was lower. Fine-tuned empirical central 90% coverage was **85.346% / 88.697%** for A/B; both are below nominal 90%. The report does not claim operational forecasting readiness, historical blindness, population generalization or validated uncertainty coverage.

## Execution and frozen evidence

| Item | Observed record |
| --- | --- |
| Approval | User explicitly authorized one bounded retrospective run; recorded reference `user-2026-10-15-one-bounded-retrospective-evaluation` is a caller traceability assertion, not authentication by code. |
| Executed source | `26479e04f27bbd50fbe696cda7369c5074d2c0ee`; branch `research/goes-external-model-evaluation`; clean/matching normal installed package. |
| Measured execution | 2026-10-14T18:38:36.141669+00:00 through 2026-10-14T18:42:04.955688+00:00; 208.813 seconds. These UTC timestamps fall on October 15 in Asia/Kolkata. |
| Configuration | `configs/evaluation/goes_v1_external_january2025.json`; 7,141 bytes; SHA256 `2285ecd6858ca8c8500f300204c009ceb1d900d1808625be39119447bffb3caa`. |
| Inference source fingerprint | `ed43551c1771f5a9154046cd416ca37f32b6e604c57fc97adb3f5bfcae681de5` |
| Scientific protocol fingerprint | `9492ce5aab184ee0c35a0d05c16016d3209c62e92eb16f7d373cd680e3051417` |
| Input fingerprint | `a745891aa4f70d52f6675c63dafbb9ff9a9ca755a7b10a5fa0c107ab867b815f` |
| External dataset fingerprint | `b4ff51eff9d8a3d85f30375c07b7623915cd09be9c8f82e26ca17dca13dfcd7c` |
| Forecast contract | Two channels `xrsa_flux`, `xrsb_flux`, W/m²; dimensioned log10(F / 1 W/m²) in dex; 60-second bins; 120-minute context; 30-minute horizon; 30-minute origin stride; retrospective bin-end coordinate contract. |
| Support | 1,488 candidate origins; 481 original exclusions; 1,007 retained origins; 60,420 target cells per arm (30,210 per channel); all retained masks true. No failed arms, dropped seeds or model-dependent exclusions. |
| Frozen cohort | JEPA fine-tuned, JEPA frozen with trained head, and supervised Transformer; each seeds 17/29/43. Six point-only and seven probabilistic saved classical references; all 22 arms retained. |
| Neural execution | CPU; batch 256; 4 torch threads; deterministic algorithms; all nine original checkpoint/normalization records unchanged. |
| Classical execution | Original fixed fit/training identity and equations; genuine distinct external dataset binding; existing simulations 1,000/seed 0 recipe retained. |
| Current runtime | arch=7.2.0, numpy=2.2.6, pandas=2.3.3, scipy=1.18.1, statsmodels=0.14.5, torch=2.6.0. All three root lock hashes recorded; historical missing versions remain UNKNOWN. |
| Preservation | 259 original files / 265,951,467 bytes reproduced by stream hashes before and after execution; all 13 worktree status records and 54 branch/remote-tracking refs unchanged during the run. |

The independent input verifier hashed all 31 native January files and read 44,640 one-minute rows. Original QC retained 39,170 A bins and 44,317 B bins. Prepared contexts and targets matched the native values exactly. All 481 exclusions and reason sets were independently reproduced; overlapping reason occurrences were support-before-partition 4, invalid-features 442 and invalid-targets 297. Those occurrences must not be added as disjoint counts. Full May–August 2024 training/validation/internal-test envelopes are coordinate-disjoint from January 2025.

Original training normalization remains the unique-raw-training-partition record: counts 113,926/116,125, means -6.975172762067082 / -5.475295794509493, scales 0.5742480619158656 /0.34159742190236464, raw-support fingerprint `c64ecca1b7a1ee6965f8a337a0ea5fe04a1f68ca05d7c421823b0d4bf6145d64`. These are verified saved training quantities, not a January fit.

## All fixed models: aggregate dex losses

Lower is better. Neural rows average the same three saved seed losses/diagnostics; forecasts are not ensembled. RMSE is sqrt(pooled squared error), including across seeds. Six point-only references have no pinball or intervals; “—” is unavailable, never a fabricated distribution. Primary loss is equal origin then equal seed mean pinball over five quantiles, 30 leads and two channels. Every actual origin has 60 valid cells, so equal-origin and valid-cell pooling coincide here.

| Model / fixed cohort | Mean pinball(dex) | MAE(dex) | RMSE(dex) |
| --- | --- | --- | --- |
| `jepa_finetune` | 0.03900694 | 0.11177722 | 0.22244591 |
| `jepa_frozen` | 0.04212573 | 0.12176823 | 0.23245503 |
| `supervised` | 0.03911919 | 0.11264328 | 0.22545744 |
| `persistence` | — | 0.12733882 | 0.24112454 |
| `training_mean` | — | 0.32963331 | 0.41785290 |
| `trailing_mean` | — | 0.16111786 | 0.27824367 |
| `drift` | — | 0.17715634 | 0.33547566 |
| `ar1` | — | 0.12540330 | 0.23400735 |
| `direct_ridge` | — | 0.12905832 | 0.22840306 |
| `persistence_empirical` | 0.04489308 | 0.12596902 | 0.24230491 |
| `arima(2,1,0)` | 0.04752651 | 0.12635613 | 0.24075042 |
| `ar1-constant-normal` | 0.04983279 | 0.12650179 | 0.24242326 |
| `ar1-arch(1)-normal` | 0.04807279 | 0.12638991 | 0.24262850 |
| `ar1-garch(1,1)-normal` | 0.04640750 | 0.12622051 | 0.24235695 |
| `ar1-garch(1,1)-t` | 0.04419570 | 0.12617360 | 0.24241758 |
| `ar1-gjr-garch(1,1)-t` | 0.04389114 | 0.12513200 | 0.24181348 |

## Channel-specific dex performance

| Model | A pinball | B pinball | A MAE | B MAE | A RMSE | B RMSE |
| --- | --- | --- | --- | --- | --- | --- |
| `jepa_finetune` | 0.05616610 | 0.02184777 | 0.16206387 | 0.06149056 | 0.28612252 | 0.13076034 |
| `jepa_frozen` | 0.06029653 | 0.02395492 | 0.17524761 | 0.06828884 | 0.29888848 | 0.13688082 |
| `supervised` | 0.05607510 | 0.02216328 | 0.16243878 | 0.06284777 | 0.28983446 | 0.13288378 |
| `persistence` | — | — | 0.18508061 | 0.06959704 | 0.31081856 | 0.14026371 |
| `training_mean` | — | — | 0.43479746 | 0.22446917 | 0.52141680 | 0.27807662 |
| `trailing_mean` | — | — | 0.22838464 | 0.09385107 | 0.35519048 | 0.16934819 |
| `drift` | — | — | 0.25850975 | 0.09580292 | 0.43428389 | 0.19101133 |
| `ar1` | — | — | 0.18169657 | 0.06911003 | 0.30077590 | 0.13803164 |
| `direct_ridge` | — | — | 0.18651852 | 0.07159812 | 0.29389730 | 0.13401600 |
| `persistence_empirical` | 0.06420952 | 0.02557664 | 0.18303364 | 0.06890440 | 0.31235304 | 0.14092167 |
| `arima(2,1,0)` | 0.06767047 | 0.02738255 | 0.18523005 | 0.06748220 | 0.31119455 | 0.13812849 |
| `ar1-constant-normal` | 0.07053162 | 0.02913396 | 0.18610237 | 0.06690122 | 0.31426150 | 0.13703204 |
| `ar1-arch(1)-normal` | 0.07091810 | 0.02522748 | 0.18610511 | 0.06667471 | 0.31454367 | 0.13711112 |
| `ar1-garch(1,1)-normal` | 0.06816748 | 0.02464752 | 0.18586383 | 0.06657720 | 0.31420736 | 0.13692158 |
| `ar1-garch(1,1)-t` | 0.06413261 | 0.02425879 | 0.18579223 | 0.06655497 | 0.31423221 | 0.13707912 |
| `ar1-gjr-garch(1,1)-t` | 0.06363333 | 0.02414896 | 0.18396912 | 0.06629488 | 0.31329841 | 0.13708254 |

## Native point performance (W/m²)

Native points preserve their saved inverse-transformed interpretation; they are not reinterpreted as physical conditional means. Native and dex metrics can rank models differently. For example, frozen JEPA has higher dex RMSE than direct ridge despite lower pinball than every probabilistic classical reference. The fixed drift arm is retained despite large native errors; nothing was clipped or removed.

| Model | A MAE | B MAE | A RMSE | B RMSE |
| --- | --- | --- | --- | --- |
| `jepa_finetune` | 1.235189e-07 | 7.630791e-07 | 1.214742e-06 | 4.711732e-06 |
| `jepa_frozen` | 1.343561e-07 | 8.500454e-07 | 1.236973e-06 | 4.889729e-06 |
| `supervised` | 1.256778e-07 | 7.877727e-07 | 1.222092e-06 | 4.784457e-06 |
| `persistence` | 1.602677e-07 | 9.580003e-07 | 1.270514e-06 | 5.008065e-06 |
| `training_mean` | 1.909114e-07 | 1.920155e-06 | 1.272155e-06 | 5.524223e-06 |
| `trailing_mean` | 1.872949e-07 | 1.267488e-06 | 1.295414e-06 | 5.493569e-06 |
| `drift` | 1.833586e-06 | 2.577818e-06 | 4.498398e-05 | 2.899571e-05 |
| `ar1` | 1.445893e-07 | 9.261148e-07 | 1.228859e-06 | 4.910136e-06 |
| `direct_ridge` | 1.336726e-07 | 8.574795e-07 | 1.217617e-06 | 4.739112e-06 |
| `persistence_empirical` | 1.546028e-07 | 9.361789e-07 | 1.259338e-06 | 4.979736e-06 |
| `arima(2,1,0)` | 1.558308e-07 | 9.184780e-07 | 1.259097e-06 | 4.931378e-06 |
| `ar1-constant-normal` | 1.538218e-07 | 8.997498e-07 | 1.253153e-06 | 4.899680e-06 |
| `ar1-arch(1)-normal` | 1.539974e-07 | 8.986310e-07 | 1.255239e-06 | 4.897209e-06 |
| `ar1-garch(1,1)-normal` | 1.540083e-07 | 8.972471e-07 | 1.255446e-06 | 4.895769e-06 |
| `ar1-garch(1,1)-t` | 1.544430e-07 | 8.982737e-07 | 1.254749e-06 | 4.901969e-06 |
| `ar1-gjr-garch(1,1)-t` | 1.498627e-07 | 8.925696e-07 | 1.247795e-06 | 4.893469e-06 |

## Native pinball (W/m²; secondary)

| Model | A mean pinball | B mean pinball |
| --- | --- | --- |
| `jepa_finetune` | 5.528703e-08 | 3.109656e-07 |
| `jepa_frozen` | 5.866289e-08 | 3.371978e-07 |
| `supervised` | 5.508668e-08 | 3.132733e-07 |
| `persistence_empirical` | 6.431215e-08 | 3.745429e-07 |
| `arima(2,1,0)` | 6.405169e-08 | 3.690603e-07 |
| `ar1-constant-normal` | 6.481038e-08 | 3.721299e-07 |
| `ar1-arch(1)-normal` | 9.916192e-08 | 3.573795e-07 |
| `ar1-garch(1,1)-normal` | 2.131539e-07 | 3.901440e-07 |
| `ar1-garch(1,1)-t` | 7.846375e-08 | 3.576078e-07 |
| `ar1-gjr-garch(1,1)-t` | 1.252926e-07 | 3.574546e-07 |

## Marginal interval coverage and widths

Inclusive central 50% uses q.25/q.75; central 90% uses q.05/q.95. Percentages pool 30,210 observed cells per channel for each saved arm; neural entries are equal three-seed diagnostic means, not additional independent observations. Coverage is dimensionless. No iid/binomial significance interpretation is used.

| Model | A 50% coverage | A 90% coverage | B 50% coverage | B 90% coverage |
| --- | --- | --- | --- | --- |
| `jepa_finetune` | 46.042% | 85.346% | 49.930% | 88.697% |
| `jepa_frozen` | 45.761% | 85.440% | 48.989% | 89.197% |
| `supervised` | 48.947% | 87.182% | 53.191% | 89.650% |
| `persistence_empirical` | 51.761% | 90.904% | 56.316% | 91.794% |
| `arima(2,1,0)` | 73.184% | 93.592% | 81.774% | 94.856% |
| `ar1-constant-normal` | 76.703% | 94.899% | 85.485% | 96.329% |
| `ar1-arch(1)-normal` | 73.605% | 96.385% | 71.397% | 94.121% |
| `ar1-garch(1,1)-normal` | 69.788% | 95.581% | 69.765% | 93.512% |
| `ar1-garch(1,1)-t` | 50.884% | 88.573% | 52.721% | 86.511% |
| `ar1-gjr-garch(1,1)-t` | 51.526% | 87.865% | 50.510% | 85.429% |

### A interval diagnostics

| Model | 50% width (dex) | 90% width (dex) | 90% interval score (dex) | 90% width (W/m²) |
| --- | --- | --- | --- | --- |
| `jepa_finetune` | 0.21070737 | 0.72938347 | 1.21980299 | 4.795681e-07 |
| `jepa_frozen` | 0.22390309 | 0.75062705 | 1.29622069 | 4.462343e-07 |
| `supervised` | 0.21512200 | 0.72954593 | 1.21134013 | 4.221730e-07 |
| `persistence_empirical` | 0.22833690 | 0.91845711 | 1.41837279 | 5.217515e-07 |
| `arima(2,1,0)` | 0.43343994 | 1.05701422 | 1.46024431 | 5.640008e-07 |
| `ar1-constant-normal` | 0.50073426 | 1.21852743 | 1.54982785 | 7.310337e-07 |
| `ar1-arch(1)-normal` | 0.47781673 | 1.44904835 | 1.69671950 | 4.281874e-06 |
| `ar1-garch(1,1)-normal` | 0.42146307 | 1.28103662 | 1.58161278 | 1.562646e-05 |
| `ar1-garch(1,1)-t` | 0.25293561 | 0.79689514 | 1.39713762 | 1.971248e-06 |
| `ar1-gjr-garch(1,1)-t` | 0.25295106 | 0.78538093 | 1.39458424 | 6.714929e-06 |

### B interval diagnostics

| Model | 50% width (dex) | 90% width (dex) | 90% interval score (dex) | 90% width (W/m²) |
| --- | --- | --- | --- | --- |
| `jepa_finetune` | 0.07933629 | 0.28215864 | 0.50769262 | 3.219892e-06 |
| `jepa_frozen` | 0.08445235 | 0.30005923 | 0.54658712 | 3.166111e-06 |
| `supervised` | 0.08454987 | 0.28419461 | 0.50992055 | 3.029293e-06 |
| `persistence_empirical` | 0.08255345 | 0.37486141 | 0.64001106 | 3.077596e-06 |
| `arima(2,1,0)` | 0.18561335 | 0.45264853 | 0.65163768 | 3.600213e-06 |
| `ar1-constant-normal` | 0.22781634 | 0.55467845 | 0.70405307 | 4.600687e-06 |
| `ar1-arch(1)-normal` | 0.13637772 | 0.41379001 | 0.61408875 | 4.208557e-06 |
| `ar1-garch(1,1)-normal` | 0.13507047 | 0.36236537 | 0.58549779 | 7.259513e-06 |
| `ar1-garch(1,1)-t` | 0.07755732 | 0.23756404 | 0.59340273 | 1.944691e-06 |
| `ar1-gjr-garch(1,1)-t` | 0.07291043 | 0.22141634 | 0.59317764 | 1.857010e-06 |

All 50%/90% interval scores/widths in both spaces, five-level pinball and reliability, and all channel×lead breakdowns for all 22 arms are saved in `scores.json` and were independently recomputed. MASE is unavailable without an independently bound frozen training scale; five quantiles do not define exact CRPS, event probabilities, trajectory coverage or joint calibration.

## Matched neural seed comparisons

Differences are model minus supervised; negative favors the model. Relative reduction is1-mean(model loss)/mean(reference loss), not a mean of seed ratios. Seed SD and leave-one-out means are descriptive for these three checkpoints, not new-seed population intervals.

| Seed | Fine minus S pinball | Frozen minus S pinball | Fine minus S MAE | Frozen minus S MAE |
| --- | --- | --- | --- | --- |
| 17 | 0.00063987 | 0.00271949 | 0.00096092 | 0.00865340 |
| 29 | -0.00011711 | 0.00369764 | -0.00061463 | 0.01095102 |
| 43 | -0.00085953 | 0.00260249 | -0.00294446 | 0.00777044 |


| Comparison/loss | Mean difference | Relative reduction | Seed SD | Model wins |
| --- | --- | --- | --- | --- |
| jepa_finetune vs supervised / dex_mae | -0.00086606 | 0.769% | 0.00196479 | 2/3 |
| jepa_finetune vs supervised / dex_mean_pinball | -0.00011226 | 0.287% | 0.00074971 | 2/3 |
| jepa_frozen vs supervised / dex_mae | 0.00912495 | -8.101% | 0.00164189 | 0/3 |
| jepa_frozen vs supervised / dex_mean_pinball | 0.00300654 | -7.686% | 0.00060136 | 0/3 |


| Comparison/loss | Omit17 mean | Omit29 mean | Omit43 mean |
| --- | --- | --- | --- |
| jepa_finetune vs supervised / dex_mae | -0.00177955 | -0.00099177 | 0.00017314 |
| jepa_finetune vs supervised / dex_mean_pinball | -0.00048832 | -0.00010983 | 0.00026138 |
| jepa_frozen vs supervised / dex_mae | 0.00936073 | 0.00821192 | 0.00980221 |
| jepa_frozen vs supervised / dex_mean_pinball | 0.00315006 | 0.00266099 | 0.00320856 |

## Descriptive paired calendar sensitivity

Full 1,488-position 30-minute axis retained; both arms have missing loss at the same 481 observation exclusions. UTC-epoch nonoverlapping 1/3/7-day blocks have 31/11/6 informative blocks. The 3/7-day settings retain partial edge blocks. Each B=2,000/RNG seed 17 nominal 95% percentile summary has 2,000 defined draws and 0 undefined draws, conditioned on defined paired support. Draws pool paired loss sums/counts after equal-seed loss averaging; no seed resampling. These are **fixed-checkpoint descriptive sensitivities**, with `NO_VALIDATED_REPLACEMENT`; neither inclusion nor exclusion of zero is a hypothesis test. No p-values, significance or joint seed/calendar population claim follows.

| Comparison/loss | Block days | Lower percentile | Upper percentile |
| --- | --- | --- | --- |
| jepa_finetune vs supervised / dex_mean_pinball | 1 | -0.00048780 | 0.00023849 |
| jepa_finetune vs supervised / dex_mean_pinball | 3 | -0.00055068 | 0.00029551 |
| jepa_finetune vs supervised / dex_mean_pinball | 7 | -0.00038966 | 0.00026046 |
| jepa_finetune vs supervised / dex_mae | 1 | -0.00194396 | 0.00013941 |
| jepa_finetune vs supervised / dex_mae | 3 | -0.00203384 | 0.00037364 |
| jepa_finetune vs supervised / dex_mae | 7 | -0.00164892 | 0.00025982 |
| jepa_frozen vs supervised / dex_mean_pinball | 1 | 0.00213261 | 0.00405987 |
| jepa_frozen vs supervised / dex_mean_pinball | 3 | 0.00209664 | 0.00423390 |
| jepa_frozen vs supervised / dex_mean_pinball | 7 | 0.00224911 | 0.00392256 |
| jepa_frozen vs supervised / dex_mae | 1 | 0.00666158 | 0.01203418 |
| jepa_frozen vs supervised / dex_mae | 3 | 0.00671209 | 0.01262590 |
| jepa_frozen vs supervised / dex_mae | 7 | 0.00710760 | 0.01191022 |

The primary fine-tuned pinball and MAE summaries span zero at every block duration. Frozen losses exceed supervised for every matched seed; its descriptive ranges are positive, without a significance claim. Coverage, interval widths and RMSE receive point summaries only. All 41 paired comparisons and all 192 available calendar-loss summaries are preserved in `summary.json`; none was chosen for a favorable outcome.

## Fine-tuned JEPA versus every restored baseline

Each reference is its one original fixed fit, replicated for the three checkpoint comparisons; baseline copies are not independent training seeds. No baseline was selected, replaced or tuned from these results. All neural/classical contrasts remain available in the bundle and compact manifest.

| Fixed reference | Fine minus ref pinball | Pinball relative reduction | Fine minus ref MAE | MAE relative reduction |
| --- | --- | --- | --- | --- |
| `persistence` | — | — | -0.01556161 | 12.221% |
| `training_mean` | — | — | -0.21785610 | 66.090% |
| `trailing_mean` | — | — | -0.04934064 | 30.624% |
| `drift` | — | — | -0.06537912 | 36.905% |
| `ar1` | — | — | -0.01362608 | 10.866% |
| `direct_ridge` | — | — | -0.01728110 | 13.390% |
| `persistence_empirical` | -0.00588615 | 13.111% | -0.01419180 | 11.266% |
| `arima(2,1,0)` | -0.00851958 | 17.926% | -0.01457891 | 11.538% |
| `ar1-constant-normal` | -0.01082586 | 21.724% | -0.01472457 | 11.640% |
| `ar1-arch(1)-normal` | -0.00906586 | 18.859% | -0.01461269 | 11.562% |
| `ar1-garch(1,1)-normal` | -0.00740056 | 15.947% | -0.01444330 | 11.443% |
| `ar1-garch(1,1)-t` | -0.00518877 | 11.740% | -0.01439638 | 11.410% |
| `ar1-gjr-garch(1,1)-t` | -0.00488421 | 11.128% | -0.01335478 | 10.673% |

## All lead steps: neural mean dex pinball

The lead grid ends at60..1,800 seconds. These channel-pooled lead diagnostics are conditional point summaries; complete channel-specific lead results for all 22 arms are retained in `scores.json`.

| Lead minutes | Fine-tuned | Frozen | Supervised |
| --- | --- | --- | --- |
| 1 | 0.01051426 | 0.01674647 | 0.01153763 |
| 2 | 0.01359273 | 0.01945922 | 0.01476685 |
| 3 | 0.01659377 | 0.02224597 | 0.01735266 |
| 4 | 0.02012517 | 0.02545452 | 0.02078164 |
| 5 | 0.02258305 | 0.02799631 | 0.02339654 |
| 6 | 0.02534275 | 0.03028208 | 0.02586086 |
| 7 | 0.02827853 | 0.03287653 | 0.02913530 |
| 8 | 0.03099471 | 0.03518290 | 0.03144231 |
| 9 | 0.03256643 | 0.03656618 | 0.03283904 |
| 10 | 0.03405818 | 0.03807911 | 0.03428418 |
| 11 | 0.03584334 | 0.03937525 | 0.03639936 |
| 12 | 0.03768054 | 0.04095510 | 0.03761071 |
| 13 | 0.03874277 | 0.04197726 | 0.03899184 |
| 14 | 0.04027992 | 0.04335554 | 0.04023506 |
| 15 | 0.04180639 | 0.04448276 | 0.04163156 |
| 16 | 0.04307643 | 0.04556209 | 0.04261145 |
| 17 | 0.04403543 | 0.04638557 | 0.04359625 |
| 18 | 0.04503605 | 0.04741783 | 0.04492500 |
| 19 | 0.04591728 | 0.04844700 | 0.04601579 |
| 20 | 0.04661218 | 0.04921121 | 0.04669068 |
| 21 | 0.04770215 | 0.04975590 | 0.04740859 |
| 22 | 0.04910988 | 0.05088146 | 0.04882803 |
| 23 | 0.05027936 | 0.05232107 | 0.05012011 |
| 24 | 0.05144377 | 0.05307660 | 0.05115006 |
| 25 | 0.05187346 | 0.05336535 | 0.05164258 |
| 26 | 0.05263487 | 0.05399388 | 0.05236892 |
| 27 | 0.05305928 | 0.05446808 | 0.05258513 |
| 28 | 0.05332581 | 0.05451314 | 0.05288057 |
| 29 | 0.05347818 | 0.05448182 | 0.05317112 |
| 30 | 0.05362135 | 0.05485567 | 0.05331593 |

## Verification and preservation

Fresh focused adapter/guard/scoring/pairing/batching/causality/boundary and bounded historical-replay tests: **458 passed in 137.05 seconds**. The prior unchanged executable source had a 1,417-test full regression qualification; it was not redundantly repeated for report-only changes. Test fixtures are software verification, not solar-performance evidence. No scientific training or optimization was performed.

Independent pre-execution verification rebuilt native QC/support and authenticated original inputs. The independent output auditor used standard-library/NumPy equations, not production scoring/diagnostic/bootstrap functions, and invoked no models or fitting. It passed **3,162,332 scalar/declaration checks**, including all 22 arms, all 41 comparisons, full lead/channel diagnostics, all 1,007 per-origin rows per arm, pooled-MSE RMSE, every fixed calendar setting, content fingerprints, all five artifact-index members, and original checkpoint/normalization/fitted-state/preparation identities. This assertion count is not a count of independent scientific samples.

Tolerances were declared before forecast inspection: rtol 2e-12; dex/dimensionless absolute floor 2e-14, native 2e-22 W/m², native squared 2e-28 (W/m²)²; ratio/seed summaries floor 2e-12 for cancellation/division. Counts, null metadata, coordinates and SHA256 identities were exact. Maximum deltas were dex_or_dimensionless=4.729550e-14, native=5.421011e-20, native_squared=6.776264e-21, ratio_seed=3.330669e-16. The largest numerical error used 1.402% of its allowed bound.

The first output audit had one schema mistake: it required explicit optional availability coordinates even though the pinned preparation has `availability_ns=null` and the original retrospective contract permits it (operational mode requires known availability). The first script/result are retained. Only that auditor check was corrected; tolerances, scientific outputs, source and configuration were unchanged. Unknown actual delivery remains unknown. The second **saved-output audit**, not a second model run, passed all checks.

The guarded runner made one attempt, exited 0, repeated strict input/source/protocol/runtime/prediction/score checks at publication and used atomic no-replacement output. Original 259 files and all original worktree/ref states were preserved. Raw observations, checkpoints, full predictions/inputs/scores and generated audit arrays remain ignored; tracked material is this report and small provenance/aggregate manifest. No protected branch, PR or merge is authorized or modified.

## Scientific limits and interpretation

- **OBSERVED:** January acquisition/preparation preceded the recorded strict V1 run. **UNKNOWN:** influence on architecture/selection/human decisions and private/unrecorded runs. This is previously inspected retrospective replication, not an untouched confirmatory holdout.
- **OBSERVED/DOCUMENTED:** pinned reprocessed `v2-2-1` archive, later native creation, adjacent-day inputs, centered spike selection and calibration/electron-processing dependencies. **UNKNOWN:** exact per-value and LUT training support, matched production-code/calibration bytes and historical delivery/as-issued values. Coordinate isolation is verified; operational preprocessing causality is not.
- **OBSERVED:** actual availability is null; no arrival timestamps were invented or substituted with bin ends. The approved scope permits retrospective bin-end coordinates and establishes no live latency or operational readiness.
- **UNKNOWN:** historical scipy/statsmodels/arch versions, complete original-origin replay and independently reproduced optimization. Audit-time byte pins preserve present original artifacts; they do not create a missing contemporaneous manifest.
- One satellite/month, QC-conditioned retention, related channels/contexts/solar activity and three fixed selected seeds limit generalization. Calendar block choices do not prove independence or stationarity. `NO_VALIDATED_REPLACEMENT` remains; no validated confidence guarantee or significance claim is made.
- The 1,000-draw/seed 0 statistical recipe and fixed parameters are preserved. Simulation and parameter-estimation uncertainty are not quantified by these temporal summaries.
- No weights, preprocessing statistics, forecast recipe, uncertainty setting, model roster or product version was adjusted from January outcomes. No deployment model was chosen.

**INFERRED within the approved scope:** The frozen V1 pipeline transfers technically to this disjoint archived month. Fine-tuned JEPA has a small, mixed-seed average difference from supervised; the evidence supports reporting comparable conditional accuracy rather than a robust JEPA superiority claim. Lower neural mean pinball versus restored probabilistic references does not establish nominal calibration, live operational skill or future-period generalization. Further scientific or operational work requires its own scope and safeguards.

## Reproducible artifacts and exact audit replay

The tracked [execution manifest](../data/manifests/phase1_goes_external_execution.json) records all model/input/config/source/output hashes, full-precision aggregate/channel results, seed/classical comparisons, runtime/lock identities, approval assertion and verification-file identities. Full raw result members are deliberately ignored; preserve the local bundle and verification directory together.

| Immutable bundle member | Bytes | SHA256 |
| --- | --- | --- |
| `artifacts.json` | 624 | `679790feaa4fa9082f279fad2d53f0e87b5fc8342d8cbfca4aa0f01ea6d242db` |
| `inputs.json` | 18867383 | `9e16c11828281fa78bb8ccdcb264cbe05a68b482cc68802df765d68d99558d31` |
| `predictions.json` | 142602898 | `4610b818cd2ff89e258b7cf51eef2426d2bf6f235c024acbe0f4d39678596e78` |
| `resolved_protocol.json` | 5318 | `8724f54e64a5974d20390bf421b3764ebbf75befa9f93fb6a6806071eda86e9e` |
| `scores.json` | 86752070 | `6e77b32243fd97339499465ae09237a65a0ff31fec6bb53c200c85b58d4e8fe6` |
| `summary.json` | 6480915 | `f87c2825829763ad250e574806165d4f2ac778c0108e7dc786bfde6e5cab2917` |

The isolated worktree contains reproducible audit code/evidence under ignored `results/phase1_external_execution_20261015/`. The independent auditor source SHA256 is `6097a17924516b13f46f0c9b495fcf5644df67e0d7790a0953af799c86a6462f`; the pre-result tolerance declaration SHA256 is `cdabd7632f60ac9f1068a74822b2a9105453d9ad23c134a10f1906b59bdebfce`. The prepared auditor retains the inspected storage locators; relocate them only with identical pinned bytes. From this worktree, a forecast-only audit can be repeated without another model evaluation:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  results/phase1_external_execution_20261015/solarjepa-phase1-20261015-output-audit.py \
  --bundle results/experiments/goes-v1-external-january2025-approved-run
```

The audit CLI writes `/private/tmp/solarjepa-phase1-20261015-audit.json` and reads the identical predeclared tolerance JSON there. If temporary storage was cleared, restore that declaration from its hash-verified ignored verification copy first. The first-pass and final original audit records in the verification directory remain preserved. No `--output` option exists in this bounded audit helper.

The original command and observed UTC timing are retained in the attempt ledger and tracked manifest. **Do not repeat inference under this one-run approval** or overwrite the immutable directory. Any additional model experiment, recalibration, retraining, operational product qualification, PR or merge requires separate authorization.

## Independent final scientific-report review

The independent final scientific reviewer returned **spec PASS, scientific/quality PASS, feature-only publication ready**, with no findings requiring correction. Fresh read-only checks matched all **554 displayed numeric cells across 13 tables**, all 22 compact arm summaries, three neural cohort summaries and 41 comparison records to the saved outputs. All six bundle hashes, verification-file identities and configuration identity matched. The reviewer confirmed the null-availability audit correction preserves exact prepared-context binding and unchanged numerical tolerances. The reviewer inspected the 458-pass test log and independent audit implementation/results without rerunning tests, inference, fitting or the complete numerical auditor. Historical exposure, actual delivery, upstream per-value causality, missing historical runtime evidence, future performance and deployment selection remain outside what these results establish. This review approves feature-branch publication only; it grants no PR, merge or further-experiment authorization.

The final publication check encountered the previously documented local `main` cloud-placeholder read timeout (`dataless`; errno 60). Its current local contents could not be reverified; direct remote `main` remained `1a4991da4dda9676caeb1d7e35a03408528c3188`. All other enumerated branch/tracking refs and all 12 other worktree statuses matched the starting snapshot. A separate final preservation check matched all 257 nonempty original-file hashes and the two zero-length original-file sizes (259 files, 265,951,467 bytes total); all six result hashes, 13 verification-file hashes and executable/configuration identities also matched. No protected ref was repaired or rewritten. Independent review judged the recurring read limitation compatible with explicit feature-only publication, conditional on Git accepting the operation and subsequent remote verification.
