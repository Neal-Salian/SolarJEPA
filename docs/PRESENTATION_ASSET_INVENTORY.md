# Presentation asset inventory

Inventory scope: existing tracked V1 assets, the exact strict V1 bundle and
explicit reference-EDA paths; no V2 holdout discovery or evaluation. Historical
reports are context, not proof. All listed V1 forecast figures were checked
against the saved run. No pre-existing Jupyter analysis notebook was found in
the tracked V1 tree; `notebooks/README.md` was the only notebook-area file.

## Existing assets and saved evidence

| Location | Scientific meaning / period / models | Metric definition | Suitability and regeneration |
|---|---|---|---|
| `docs/figures/v1/fig_lead_log_mae.png` | August 2024 lead errors; persistence, selected ARIMA, selected GJR, validation-selected JEPA seed 43 | Equal-channel log-median MAE, dex | Verified byte-identical to strict run. Correct single-seed illustration; new seed-mean chart preferred. No historical rewrite. |
| `docs/figures/v1/fig_fan_largest_rise.png` | August 8 19:00 UTC; retrospectively largest XRS-B rise ×21.0776; ARIMA(2,1,0), GJR-t, JEPA seed 43 | Median and central 50/90% marginal quantile bands in W m⁻², log axis | Reuse on slide 9. All displayed upper bands miss the peak. A difficult selected example, not average skill. Positive leads denote target-bin ends. |
| `docs/figures/v1/fig_coverage.png` | All 16 probabilistic seed/model records, August 2024 | Achieved per-cell central 50/90% interval coverage | Verified byte-identical to strict run. Dense appendix figure; new family chart preferred. |
| `docs/figures/v1/jepa_training_curves.png` | Train May–July 21 and validation July 22–31; all three neural variants/seeds; 3×4 grid | Latent loss, normalized pinball, latent standard deviation/effective rank | Exists, 288,162 bytes; hash matches V1_RESULTS. Appendix diagnostic; compact history rendering generated. Loss decline does not establish representation utility. |
| `results/experiments/v1-full-20261009/summary.json` | Strict full V1 record; 25 validation / 22 test model records, selections, histories, fits, timing | Native and dex scores; fit histories/configs | Verified against predictions. Reuse as read-only evidence, remains ignored. |
| `results/experiments/v1-full-20261009/per_origin.json` | Common validation/test origins and losses, retrospective strata | Per-origin cell-average MAE/pinball | Verified origin alignment and arithmetic. Reuse for paired daily-block uncertainty, remains ignored. |
| `results/experiments/v1-full-20261009/test_predictions.npz` | 1,436 test origins, contexts, targets, six point models and 16 quantile model/seed records | Native W m⁻² point/quantile arrays; five quantiles | Exact native alignment checked; independent score replay. Required local input, never committed. |
| `results/experiments/v1-full-20261009/*.pt` (nine explicitly named neural checkpoints) | Three seeds × three variants | Saved weights/configs, not evaluation metrics by themselves | Existing checkpoints left unchanged; not needed to regenerate presentation from predictions, not retrained/replayed in this milestone. |
| `docs/V1_RESULTS.md`, `docs/V1_SCIENTIFIC_AUDIT.md` | Historical numerical/diagnostic reports | Reported numbers and qualifications | Preserved. Current metrics reverified. V1_RUN's “not completed yet” opening records an earlier state and is not present implementation evidence. |
| `configs/data/noaa_eda.json`, `scripts/eda.py`, `src/solar_flare_jepa/data/eda.py` | Existing small reference-sample preparation/plots; explicit `results/noaa_reference/` path | Reference descriptive/QC summaries | Reuse summary logic, rather than applying an incompatible short-sample report to the four-month V1 benchmark. Not a model comparison. |
| `results/noaa_reference/{time_series.png,distributions_quality.png,cadence.png,event_example.png,summary.json}` | Existing July 1–4, 2024 reference sample, 4,320 bins; channels A/B, no forecast model | Flux/log/derivative, sampling and quality; catalog-state example | Files and saved period verified. Historical descriptive assets, not independently regenerated here; superseded for main-slide full-period EDA. Catalog states are not V1 onset labels. |
| Four `data/manifests/goes_*.json` selected in V1 config | May–August 2024 GOES-16 pins; 123 files | Filename/version/size/hash provenance | All verified. Reuse without downloading or changing manifests. |

No separately saved interval-calibration fit or operational-warning evaluation
is present in the selected V1 bundle. Coverage is a calibration diagnostic,
not evidence of an additional calibration procedure. No SARIMA, LSTM, TCN or
PatchTST evaluation is invented. Exact numerical tables now come from the
saved predictions rather than manual report transcription.

## New presentation assets

Every stem below has PNG (220 dpi) and SVG exports under
`docs/figures/presentation/`. SVG preserves vector text/axes; long series marks
are rasterized for manageable size. All files are below 600 KB each at this
checkpoint. Full captions, source identities, code hashes and environment
versions are in [figure_manifest.json](presentation/figure_manifest.json).

| Stem | Meaning / metric | Period and models | Decision |
|---|---|---|---|
| `eda_raw_flux` | Native primary electron-corrected irradiance before repository QC, W m⁻², linear axes; rejected finite values marked | May–August, A/B | New; supplies raw-scale requirement without invented counts/calibration. |
| `eda_log_flux` | QC-valid log₁₀(F / 1 W m⁻²), gaps retained | May–August, A/B | New. |
| `eda_distribution` | Valid-minute counts in native and log-space histograms | May–August, A/B | New. Counts are not independent events. |
| `eda_rolling_statistics` | Six-hour trailing log mean / sample variance, 360 valid bins required | May–August, A/B | New. Does not bridge missing observations. |
| `eda_acf` | Level and first-difference ACF; no iid bands | Contiguous training June 11 16:38–June 18 17:47 UTC, A/B | New. |
| `eda_pacf` | Level and first-difference Yule–Walker MLE PACF | Same training block, A/B | New. |
| `eda_daily_variability` | Daily log median/IQR, descriptive variability | May–August, A/B | New; no daily-seasonality claim. |
| `eda_data_quality` | Daily rejected fraction; nonadditive missing/nonfinite/rejected counts | May–August, A/B | New. |
| `comparison_pinball` | Mean five-quantile pinball, equal cells, dex, zero-based axis | August; all seven statistical rows plus three neural seed means | New. Includes optimizer qualifications. |
| `comparison_log_mae` | Log MAE of median, dex, zero-based axis | Same ten probabilistic comparison rows | New; six point-only scores separately tabulated. |
| `comparison_lead_errors` | Equal-channel pinball and MAE by target-bin-end lead | August; ARIMA, GJR, supervised/fine-tuned seed means | New; avoids historical single-best-neural-seed ambiguity. |
| `comparison_coverage` | Marginal central 50/90% achieved cell coverage | Same ten comparison rows | New, condensed; widths in comparison table. |
| `jepa_seed_comparison` | Paired seed pinball differences and conditional daily-block intervals | August; fine-tuned versus matching supervised; three seeds plus omit43 influence | New, central scientific limitation. |
| `jepa_training_curves` | All three pretraining histories and all nine validation histories | Train/validation only; three neural variants | New compact view, not a duplicate copy of historical grid. |
| `jepa_architecture` | Source-verified computation graph and training stages | V1 implementation/configuration; no dataset metric | New reproducible diagram. |

Fifteen new scientific figures, four preserved historical figure references.
PNG/SVG are format variants, not independent results. The existing fan chart is
reused by reference instead of copied or cosmetically regenerated.

## Numerical and narrative outputs

- `docs/presentation/eda_evidence.json`, `stationarity.csv`: QC, block selection,
  test statistics/settings/sensitivities, ACF/PACF, seasonal-lag/spectral diagnostics.
- `docs/presentation/model_evidence.json`, `model_metrics.csv`: every test model's
  replayed metrics, seed-family aggregation and paired conditional intervals.
- `docs/presentation/figure_manifest.json`, `environment.txt`: source/figure
  identities and installed versions, with portable logical paths.
- `notebooks/presentation_goes_eda.ipynb`: executed EDA narrative, compact outputs.
- `docs/PRESENTATION_EDA_REPORT.md`, `PRESENTATION_MODEL_COMPARISON.md`,
  `PRESENTATION_GUIDE.md`, `PRESENTATION_VERIFICATION.md`: interpretation, slide
  guidance, checks and limitations. `PRESENTATION_PLAN.md` records scope choices.

Rebuild using `python scripts/build_presentation.py` from the normally installed
project environment. Inputs remain ignored under the existing storage policy.
The EDA notebook separately regenerates only EDA assets/evidence; rerun the full
CLI after changing analysis source or plot formatting to refresh all hashes.
