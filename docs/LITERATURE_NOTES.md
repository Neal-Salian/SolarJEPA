# Literature and source notes

Investigated 2026-09-29. A = established prior art/documented instrument fact;
B = proposed adaptation; C = candidate contribution requiring experiments.
Abstract-level screening is identified below; no citation implies reproduction
or acceptance of all reported performance claims. Bibliographic metadata can be
obtained from the linked primary records rather than guessed.

## Mission / measurement sources

| Source | Evidence read and relevance |
|---|---|
| [ISRO second data release, 2025](https://www.isro.gov.in/Second_Set_of_Aditya_L1_Science_Data.html) | Official release/access announcement; registration for manuals. Does not establish complete per-file holdings. A |
| [PRADAN FAQ](https://pradan1.issdc.gov.in/al1/faq.xhtml) | Public payload guidance; distinguishes SWIS/STEPS and their products/cadences. A |
| [URSC SoLEXS instrument page, updated June 2026](https://www.ursc.gov.in/SoLEXS.jsp) | Specifications and links to design/calibration publications; operational plots are not downloadable telemetry. A |
| [Sarwade et al., SoLEXS ground calibration and in-flight performance, 2025](https://arxiv.org/abs/2509.26292) / [HTML](https://arxiv.org/html/2509.26292v1) | Read instrument/calibration sections: response and temperature-dependent gain matter; higher-level products flow through POC/PRADAN. Supports calibration audit, not a guessed FITS schema. A |
| [Sebastian et al., One Year of ASPEX-STEPS Operation, 2025](https://arxiv.org/abs/2507.18117) | Abstract screening: four stable units and energetic-ion observations; studied period is not an archive inventory. A |
| [Gupta et al., Multi-directional investigations on quiet time suprathermal ions, 2025](https://arxiv.org/abs/2507.11952) | Abstract screening: direction-dependent energy coverage, quiet suprathermal population with historical-event interpretation. Cannot equate these ions to immediate flare heating. A |
| [NCEI GOES-R EXIS](https://www.ncei.noaa.gov/products/goes-r-extreme-ultraviolet-xray-irradiance) | Official product directory: science/operational distinction, NetCDF, XRS irradiance and event products. A |
| [NCEI XRS L2 ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf) | Read version/coverage notes; 2-2-1 revises calibration and fills some short gaps. Pin version and reject interpolated input for strict baseline. A |
| [NCEI XRS L2 User Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf) | Read clock, flags and event sections. Metadata and bin edges must guide alignment; event state rows require grouping. A |
| [SWPC user guide](https://www.swpc.noaa.gov/sites/default/files/images/u2/Usr_guide.pdf) | Official GOES-band flare classification definitions. Do not apply thresholds to SoLEXS counts. A |

## Solar forecasting and evaluation

| Source | What it establishes / project consequence |
|---|---|
| [Landa & Reuveni, Low Dimensional CNN for Solar Flares GOES Time Series Classification, 2021](https://arxiv.org/abs/2101.12550) | Abstract: X-ray-only CNN warning and chronological/random evaluation already investigated. Our contribution needs stronger controls and useful uncertainty, not “X-rays + deep learning”. A/B |
| [Reep & Barnes, Forecasting the Remaining Duration of an Ongoing Solar Flare, 2021](https://arxiv.org/abs/2103.03957) | Abstract: ongoing-flare evolution is a distinct established problem. Report it separately from onset warning. A |
| [Ahmadzadeh et al., How to Train Your Flare Prediction Model, 2021](https://arxiv.org/abs/2103.07542) | Abstract: temporal coherence and rare events can distort evaluation. Motivates purging, chronological partitions and event counts. A |
| [Camporeale & Berger, Verification of NOAA SWPC solar flare forecast (1998–2024), 2025](https://arxiv.org/abs/2508.01114) | Abstract/preprint: evaluate probabilistic forecasts against cheap baselines, including first flare after quiet periods. Reproduce methods before importing conclusions. A/B |

## Representation and forecasting architectures

| Source | Prior art and decision |
|---|---|
| [Assran et al., I-JEPA, 2023](https://arxiv.org/abs/2301.08243) | Abstract: latent target prediction is explicitly non-generative self-supervision. Temporal adaptation B; not new in itself. |
| [Girgis et al., Time-Series JEPA for Predictive Remote Control, 2024](https://arxiv.org/abs/2406.04853) | Abstract: temporal JEPA predates this proposal, though applied to control. A |
| [Ennadir, Golkar & Sarra, Joint Embeddings Go Temporal, 2025](https://arxiv.org/abs/2509.25449) / [author code](https://github.com/Sennadir/TS_JEPA) | Abstract and repository: TS-JEPA representation/forecast evaluation is direct prior art. Include comparable SSL control. A/B |
| [Nie et al., Phys-JEPA, 2026](https://arxiv.org/abs/2606.16076) | Preliminary manuscript/abstract: physical and residual latent components with consistency regularization for multivariate forecasts. Broad physics-JEPA novelty is unavailable. A; solar measurement-specific validation remains candidate C. |
| [CF-JEPA author repository](https://github.com/WDSLab/CF-JEPA) | Repository screening: forward crop-based temporal JEPA and shared benchmark evaluation. Code existence verified; publication status/results not independently validated. A |
| [Yue et al., TS2Vec, 2021/AAAI 2022](https://arxiv.org/abs/2106.10466) | Abstract: hierarchical temporal contrastive representation learning. Candidate SSL comparison, not all SSL controls at once. A/B |
| [Nie et al., A Time Series is Worth 64 Words, 2022/ICLR 2023](https://arxiv.org/abs/2211.14730) | Abstract: PatchTST makes patching an established forecasting technique. Match patching in supervised Transformer control. A/B |
| [Bai, Kolter & Koltun, empirical convolutional/recurrent sequence study, 2018](https://arxiv.org/abs/1803.01271) | Abstract: motivates a small causal TCN alongside LSTM; no solar superiority inferred. A/B |
| [Zeng et al., Are Transformers Effective for Time Series Forecasting?, 2022](https://arxiv.org/abs/2205.13504) | Abstract: simple linear baselines must not be omitted. Include direct linear/ridge forecasting. A/B |

## LLMs / foundation models

| Source | Decision |
|---|---|
| [Gruver et al., Large Language Models Are Zero-Shot Time Series Forecasters, 2023](https://arxiv.org/abs/2310.07820) | Abstract: numerical text serialization is established; tokenization and calibration matter. Qwen comparison is adaptation B. |
| [Tan et al., Are Language Models Actually Useful for Time Series Forecasting?, 2024](https://arxiv.org/abs/2406.16964) | Abstract: removal/replacement controls challenge LLM benefit. Include native model matched task and report compute. A |
| [Ansari et al., Chronos, 2024](https://arxiv.org/abs/2403.07815) | Abstract: numerical tokenization and pretrained TS foundation models differ from general-text Qwen. Optional small checkpoint benchmark; audit pretraining overlap. A/B |
| [Dettmers et al., QLoRA, 2023](https://arxiv.org/abs/2305.14314) | Abstract: quantized frozen base + LoRA; no guarantee of T4 memory at arbitrary context. A |
| [Qwen2.5-1.5B author model card](https://huggingface.co/Qwen/Qwen2.5-1.5B) | Verify exact revision/tokenizer/license before download. Base model is candidate for numerical completion; explanation layer is separate and non-evidentiary. A/B |

## Physics, statistics and uncertainty

| Source | Decision |
|---|---|
| [Karniadakis et al., Physics-informed machine learning, 2021](https://doi.org/10.1038/s42254-021-00314-5) | Review-level context: constraints need applicable known physics. It does not supply a valid solar-flux PDE. A |
| [Veronig et al., Neupert effect and coronal heating, 2002](https://arxiv.org/abs/astro-ph/0208089) | Abstract: relation is not universal even with SXR/HXR. Reject hard Neupert loss with STEPS ions. A |
| [Stanislavsky et al., Solar X-ray variability in terms of a fractional heteroskedastic time series model, MNRAS 2019](https://doi.org/10.1093/mnras/stz656) | Abstract: ARFIMA–GARCH for active and ARFIMA for quieter solar states already studied. Justifies investigating residual variance; does not prove short-horizon flare-warning skill. A/B |
| [Stanislavsky et al., Statistical Modeling of Solar Flare Activity, 2008](https://arxiv.org/abs/0805.0968) | Abstract: long-memory/heavy-tail statistical behavior is prior art. Do not equate event-energy statistics with our regularly sampled target. A |
| [arch official forecasting documentation](https://bashtage.github.io/arch/univariate/forecasting.html) | Mean, residual variance and process variance differ; multi-step simulation supports probabilistic comparisons. A/B |
| [Gibbs & Candès, Adaptive Conformal Inference Under Distribution Shift, 2021](https://arxiv.org/abs/2106.00170) | Abstract: adaptive coverage frequency is different from exchangeable finite-sample conditional coverage. Our event-conditioned calibration remains empirical. A/B |

## Remaining literature work before architecture freeze

Read full methods/splits and inspect code for TS-JEPA, Phys-JEPA, CF-JEPA and the
strongest X-ray baseline; reproduce a small reference result if affordable.
Check solar-specific uncertainty papers and spectral inversion literature with
a heliophysics collaborator. Search exact solar/Aditya + JEPA combinations again
before claiming C. No direct solar JEPA counterpart was established in this
scoped search; that is not evidence of absence. No references are invented.
