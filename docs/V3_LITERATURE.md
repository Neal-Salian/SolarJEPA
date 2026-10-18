# V3 literature and implications

Research date: 2026-10-18. Sources below are original papers or official
instrument documentation, accessed through primary-source browsing. Preprints
are identified explicitly. Summaries are paraphrases. **DOCUMENTED** refers to
the source method/result; each SolarJEPA application is **INFERRED** and its
benefit **UNKNOWN**. This is targeted reconnaissance, not a systematic review.

| Source | Documented contribution | V3 use and limitation |
|---|---|---|
| Assran et al., [I-JEPA](https://arxiv.org/abs/2301.08243), 2023 | Context-to-target latent prediction; target scale and informative context are important design choices | Test temporal target locality/scale. Image results and large training resources do not establish solar forecasting skill. Existing SolarJEPA already implements latent prediction. |
| Bardes et al., [V-JEPA](https://arxiv.org/abs/2404.08471), 2024 | Masked feature prediction for video representations, with EMA target representations | Supports frozen-representation and reconstruction-control comparisons. Video representation benchmarks differ from calibrated continuous forecasts. |
| Bardes et al., [VICReg](https://arxiv.org/abs/2105.04906), ICLR 2022 | Variance and covariance penalties address constant/redundant representations | Test a small online regularizer only after measuring diversity across training origins. Overlapping adjacent windows can undermine batch diversity; vector LayerNorm is insufficient evidence. |
| Feng et al., [Does Joint-Embedding Predictive Architecture Pretraining Help Time Series Forecasting?](https://arxiv.org/abs/2609.31680), September 2026 preprint | One JEPA instantiation evaluated across nine backbones and eleven temporal/spatiotemporal datasets; benefits depend strongly on backbone | Direct reason to retain paired supervised controls. Non-solar datasets, one instantiation and fixed settings do not settle SolarJEPA's value. |
| He et al., [MTS-JEPA, version1](https://arxiv.org/abs/2602.04643v1), February 2026 preprint | Fine/coarse targets, codebook, EMA, reconstruction and regularization for multivariate anomaly prediction | Multi-scale prior art; not a flux-regression result. Its reconstruction/codebook ablations do not establish a universal collapse cure. Version1 is intended here; the later version is titled SC-JEPA. Defer codebooks until simpler targets justify added complexity. |
| Nie et al., [PatchTST](https://arxiv.org/abs/2211.14730), ICLR 2023 | Patching reduces attention-map cost for a fixed history; supervised and masked-pretrained forecasting | Extend history affordably, but preserve joint-channel information as a controlled choice. Patching is already implemented here and is not V3 novelty. |
| Zeng et al., [Are Transformers Effective for Time Series Forecasting?](https://arxiv.org/abs/2205.13504), AAAI 2023 | Simple direct linear models compete strongly on the tested long-horizon benchmarks | Include full-context quantile linear/ridge. A quantile adaptation and minute-scale solar conclusions require their own evidence. |
| Bai et al., [TCN sequence-modeling study](https://arxiv.org/abs/1803.01271), 2018 | Dilated residual convolutions provide an effective sequence-modeling alternative on tested tasks | One small causal TCN is a practical comparator. Verify receptive field for each context; this is not a solar probabilistic study. |
| Lin et al., [Focal Loss](https://arxiv.org/abs/1708.02002), ICCV 2017 | Classification loss reduces emphasis on easy examples in dense detection | Does not justify focal continuous regression or fabricated flare labels. Defer event classification until its label and sampling contracts exist. |
| Gneiting and Ranjan, [weighted probabilistic scoring rules, April 2008 technical report](https://stat.uw.edu/research/tech-reports/comparing-density-forecasts-using-threshold-and-quantile-weighted-scoring-rules), subsequently [published 2011](https://doi.org/10.1198/jbes.2010.08110) | Proper threshold/quantile-weighted scores can emphasize parts of predictive distributions | Use fixed quantile weights as an explicit secondary objective. Realized-outcome weights are a different construction; five quantiles are not an exact continuous CRPS or a joint path distribution. |
| Romano et al., [Conformalized Quantile Regression](https://arxiv.org/abs/1905.03222), NeurIPS 2019 | Calibrates heteroscedastic intervals; marginal validity under exchangeability | Use separate calibration support and report widths. Dependent/shifted solar residuals do not automatically satisfy the theorem's assumptions; marginal is not flare-conditional or simultaneous coverage. |
| Gibbs and Candès, [Adaptive Conformal Inference](https://arxiv.org/abs/2106.00170), NeurIPS 2021 | Online adjustment targets long-run coverage frequency under changing distributions | Consider only as a separately frozen secondary protocol with matured outcomes. Long-run coverage does not guarantee narrow intervals or rare-event calibration. |
| Yi et al., [Toward Operational Solar Flare Peak Flux Nowcasting](https://arxiv.org/html/2608.20062v1), August 2026 preprint | GOES-based peak nowcasting of ongoing flares, with preceding history and evaluations between onset and peak | Calendar-month-grouped folds across 1997–2024 are not forward temporal holdouts; retrospective science-quality inputs and recognition at catalog onset + 3 min limit operational equivalence. Ongoing-event nowcasting differs from pre-onset forecasting. No numerical cross-paper ranking is proposed. |
| NOAA, [solar flare definition and scales](https://www.swpc.noaa.gov/phenomena/solar-flares-radio-blackouts) | Class is defined using peak GOES XRS 0.1–0.8 nm flux; C/M/X thresholds are 10⁻⁶/10⁻⁵/10⁻⁴ W/m² | Apply to appropriate B-band semantics. Threshold-defined windows are not independently identified catalog events. |
| NOAA/NCEI, [GOES-R product documentation](https://www.ncei.noaa.gov/products/satellite/goes-r) and [official product metadata](https://data.noaa.gov/onestop/collections/details/f9463bd9-284c-42b8-bedf-58519529f80a) | Science-quality products incorporate retrospective corrections/calibration; channel passbands and product levels are defined separately | Archived science-quality performance cannot alone establish as-issued operational skill. Pin the exact L2 documentation/version during future qualification; L1b metadata is not an L2 per-value causality proof. |

The legacy NOAA L2-readme URL surfaced by search returned 404 when opened in
this audit. No L2 calibration/QC rule was inferred from that failed retrieval.
Existing source/manifest semantics were inspected without changing them; a future
data milestone must resolve the current authoritative L2 document and its identity.

## Research decisions supported by this reading

1. Test JEPA against S, extra-update S and reconstruction pretraining; pretraining
   recipe superiority cannot be assumed from representation papers.
2. Change target locality/scale separately from backbone, context and output loss.
3. Use chronological train/tune/calibration/evaluation separation, accounting for
   full feature/label support and unknown upstream processing.
4. Keep unweighted dex pinball primary, with tail weights/transition objectives
   secondary and raw calibration visible.
5. Score deterministic median-path peaks honestly; obtain a joint distribution
   or explicit event-probability model before any “probability of any flare” claim.
6. Treat compactness as an analytic design advantage until actual M2 throughput,
   sustained memory and scientific skill are measured under a later approval.
