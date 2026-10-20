# SolarJEPA: suggested ten-slide academic presentation

Audience: Applied Time Series students and project evaluators. Evidence date:
2026-10-10. Present the question as **continuous solar X-ray flux forecasting**.
Use the PNGs on slides; use SVGs when editable/vector labels are useful. Captions,
sources and hashes are in [the asset inventory](PRESENTATION_ASSET_INVENTORY.md)
and [figure manifest](presentation/figure_manifest.json). Explain the small
seed-sensitive JEPA effect with the same prominence as the classical comparison.

## Slide 1 — SolarJEPA: forecasting solar X-ray flux

**Main points:** Can representation pretraining improve a small neural
forecaster? Compare classical uncertainty models, matched supervised learning,
frozen JEPA and fine-tuned JEPA using the same historical targets.

**Recommended visual:** Project title with a small [log-flux overview](figures/presentation/eda_log_flux.png).
**Key numbers:** Two channels; 120-minute context; 30-minute forecast.
**Presenter note:** “This is a reproducible retrospective pilot. We evaluate
flux forecasts, and do not claim operational flare warnings.”

## Slide 2 — Why short-term solar X-ray flux forecasting is difficult

**Main points:** Irradiance can change rapidly over orders of magnitude. A
point prediction hides uncertainty; quantile bands expose spread. Predicting
an observed irradiance trajectory differs from detecting a future flare onset.

**Recommended visual:** [Native irradiance](figures/presentation/eda_raw_flux.png),
with the largest peaks visible on a linear axis.
**Key numbers:** Maximum valid XRS-B irradiance 8.68849×10⁻⁴ W m⁻² in this archive.
**Presenter note:** “These are supplied science-product irradiances before
repository QC, not raw detector counts. Bright peaks dominate native-unit error.”

## Slide 3 — GOES-16 data, quality and chronological splits

**Main points:** Four pinned calendar months of one-minute EXIS/XRS data.
XRS-A 0.05–0.4 nm; XRS-B 0.1–0.8 nm. Keep quality masks and split whole
context-plus-target support chronologically. Missing records differ from
unusable measurements.

**Recommended visual:** [Data-quality summary](figures/presentation/eda_data_quality.png)
plus a simple split line: train May 1–July 22; validation July 22–August 1;
test August 1–September 1 (half-open UTC).
**Key numbers:** 177,120 bins; zero absent/duplicate timestamps; 4,474 A and
2,275 B rejected bins; 1,436 retained test origins.
**Presenter note:** “No interpolation fills gaps. Complete-case evaluation
excludes difficult unavailable issue times. Actual operational latency is unknown.”

## Slide 4 — EDA: flux levels, distributions and variability

**Main points:** Native flux has a long right tail. Log₁₀ converts multiplicative
changes to additive changes. Daily IQR and rolling variance show changing activity.

**Recommended visuals:** [Log flux](figures/presentation/eda_log_flux.png) and
[histograms](figures/presentation/eda_distribution.png), revealed sequentially.
[Rolling statistics](figures/presentation/eda_rolling_statistics.png) and
[daily variability](figures/presentation/eda_daily_variability.png) are backup figures.
**Key numbers:** Median A/B 8.46184×10⁻⁸ / 3.25223×10⁻⁶ W m⁻²; rolling window
six hours with all 360 valid minutes required.
**Presenter note:** “A log transform helps describe the range; it does not
automatically make a series stationary. Daily summaries do not imply seasonality.”

## Slide 5 — ACF, PACF and stationarity: a nuanced diagnosis

**Main points:** Persistent levels become less dependent at long lags after
differencing. ACF measures lag correlation; PACF conditions on shorter lags.
ADF and KPSS test different nulls. Use one contiguous training segment and
retain gaps elsewhere.

**Recommended visuals:** Reveal [ACF](figures/presentation/eda_acf.png) then
[PACF](figures/presentation/eda_pacf.png); give a two-row log-level test summary
from the [EDA report](PRESENTATION_EDA_REPORT.md#stationarity-protocol-and-results).
**Key numbers:** 10,149-minute June 11–18 segment. ADF log-level p values
2.64×10⁻¹⁴ / 6.32×10⁻¹³; KPSS p=0.02944 / 0.01734. Log differences have
KPSS p>0.10 for both channels.
**Presenter note:** “Rejecting a unit root and rejecting level stationarity
can happen together. These exploratory tests do not establish global stationarity.
Squared-increment lag-1 ACF is 0.297/0.449, consistent with volatility clustering.”

## Slide 6 — Classical models: mean dynamics and conditional variance

**Main points:** ARIMA models lagged mean behavior after differencing. ARCH
uses recent squared shocks to vary uncertainty; GARCH also carries past
variance; GJR adds a signed-shock term. Here each volatility model follows
the same separately fitted AR(1) mean on log differences.

**Recommended visual:** A concise method table from
[model specifications](PRESENTATION_MODEL_COMPARISON.md#model-specifications-actually-evaluated).
**Key numbers:** ARIMA(2,1,0) selected from four orders; 1,000 simulated paths
for each volatility forecast; five evaluated quantiles.
**Presenter note:** “These are two-stage AR(1)-volatility implementations, not
pure GARCH forecasts. Two GARCH A fits have optimizer flag 8; GJR is near a
stationarity boundary. SARIMA is omitted because no stable seasonal period
was justified, not because it was tested and lost.”

## Slide 7 — JEPA: predict representations, then learn a forecast

**Main points:** Pretraining predicts hidden embeddings from visible context.
The no-gradient EMA teacher sees the full training window. Downstream the
forecast head learns ordered quantiles from observed context only. Compare
skipping pretraining, freezing pretrained features and fine-tuning them.

**Recommended visual:** [Verified architecture](figures/presentation/jepa_architecture.png).
[Training curves](figures/presentation/jepa_training_curves.png) are a backup.
**Key numbers:** 24 context patches + six future patches, five minutes each;
width 32; encoder/predictor depths 3/2; five quantiles; seeds 17/29/43.
**Presenter note:** “Representation learning and supervised forecasting are
separate stages. This model directly predicts all leads; it has no physical
evolution loss or neural autoregressive trajectory generator.”

## Slide 8 — Comparison: small JEPA gain, substantial seed sensitivity

**Main points:** All models use the same test cells and metric. Neural models
beat these selected classical implementations in aggregate. The matched
supervised control explains most of that gap. JEPA's incremental benefit is small.

**Recommended visuals:** Reveal [mean pinball](figures/presentation/comparison_pinball.png)
then [paired seed comparison](figures/presentation/jepa_seed_comparison.png).
[Log MAE](figures/presentation/comparison_log_mae.png) is backup.
**Key numbers:** Fine-tuned/supervised/frozen pinball 0.0392451 / 0.0395002 /
0.0414300 dex. Fine-tuned improvement over supervised 0.6459%; over GJR
11.9904%. Omit seed 43: JEPA minus control +0.00025755 dex, reversing direction.
**Presenter note:** “The bars average losses, not forecasts. Day-bootstrap
intervals condition on already fitted seeds. This is not a robust pretraining
breakthrough; frozen JEPA is worse than supervised.”

## Slide 9 — Forecast uncertainty and a difficult example

**Main points:** Error changes with lead. Quantile intervals must balance
coverage and width. A retrospectively selected sharp-rise example exposes a
failure that average metrics hide.

**Recommended visuals:** [Existing fan chart](figures/v1/fig_fan_largest_rise.png),
with [lead errors](figures/presentation/comparison_lead_errors.png) and
[coverage](figures/presentation/comparison_coverage.png) as sequential/backup visuals.
**Key numbers:** August 8, 19:00 UTC issue; XRS-B rises ×21.08. All displayed
upper bands miss its peak. Fine-tuned 90% coverage: 89.72% pooled,
87.03% A / 92.41% B. Fine-tuned pinball is worse than GJR at leads 1–5.
**Presenter note:** “This fan uses validation-selected JEPA seed 43, not the
three-seed mean. It is a selected difficult case, not average performance.
Coverage is per target cell, not for an entire future trajectory.”

## Slide 10 — Conclusion: reproducible evidence with clear limits

**Main points:** A gap-preserving GOES EDA and saved-prediction replay support
a transparent pilot. Fine-tuned JEPA has a small seed-sensitive advantage;
frozen transfer disappoints. Future authorized research needs fresh time
regimes, more paired seeds, stronger controls and fit/calibration checks.

**Recommended visual:** Three concise statements: reproducible pilot;
seed-sensitive effect; broader validation still needed. Link the notebook,
reports and source repository for discussion.
**Key numbers:** 22 saved test models verified; 15 new figures plus four
preserved V1 assets; no V1/V2 training in this milestone.
**Presenter note:** “Negative results are part of the outcome. Continuous
irradiance skill does not establish operational flare-onset warnings. Future
work is a proposal, not an implemented capability.”

## Presentation preparation and sources

Keep figure titles/axes intact. Use exact two-stage model names and identify
seed averages. Main-slide precision of 4–6 significant digits is sufficient;
full precision stays in [model_metrics.csv](presentation/model_metrics.csv).
Do not crop away zero baselines, seed sensitivity, QC masks or optimizer notes.
Do not call a five-quantile score CRPS or pooled coverage a trajectory probability.

The reproducible outputs support a ten-slide presentation, but no PowerPoint
or PDF deck is part of this checkpoint. The user requested a slide guide;
the supplied images and notes are ready for assembly in their presentation tool.

Source definitions: [NOAA XRS guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf),
[ADF](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html),
[KPSS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html),
[I-JEPA](https://arxiv.org/abs/2301.08243). Code and exact artifact identities
are primary evidence for SolarJEPA-specific claims; see
[verification](PRESENTATION_VERIFICATION.md).
