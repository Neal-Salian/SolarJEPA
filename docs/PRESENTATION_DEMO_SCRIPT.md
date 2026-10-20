# SolarJEPA: 5–7 minute presentation walkthrough

Before the audience arrives, run the local verifier, start the app from the dashboard checkout, disconnect networking, and check all four pages. Return to Overview. Use a desktop-width window; keep provenance expanders closed until needed.

## 0:00–1:30 — Overview

Click **Overview**. “SolarJEPA studies short-horizon forecasting of solar X-ray time series. This dashboard presents verified observations and existing research evidence.”

Point to GOES-16 XRS, 87,840 observed minute records and 60-second cadence. “The interactive period is May and June 2024. This counts timestamps before quality rejection, not flare events.”

Point to both channels and the W/m² log axis. “Flux spans orders of magnitude. We retain the original timestamps and quality gaps. Display sampling keeps peaks rather than replacing them with averages.” Briefly follow the pipeline underneath. Do not imply that V2 training or an operational forecasting service has run.

## 1:30–2:45 — Data Explorer

Click **Data Explorer**. Show the two-channel comparison, then scroll to **Flux distribution**. “The channels cover different X-ray bands. The histogram counts every valid minute observation in the selected period after a log10 transform, with 70 equal-width bins per channel. These are correlated time samples, not independent flares.”

Open one **Scientific source and provenance** expander if asked about verification. Explain that missing/mismatched evidence yields an unavailable message, never fabricated values. Close it afterwards.

## 2:45–4:30 — Time-Series Analysis

Click **Time-Series Analysis**. “This archived rolling plot preserves the original May–August analysis. It shows a six-hour mean and sample variance of log flux. The original result is variance, and we label it accordingly.”

Scroll to the correlation plots. Keep **XRS-A / Log₁₀ level**, then switch **Transformation** to **First log₁₀ difference**. Optionally switch channel to XRS-B. “These are the original saved analyses on one fully observed June 11–18 training segment. ACF describes lagged dependence; PACF controls for shorter lags. Neither is a stationarity proof.”

Scroll to the stationarity panel. “ADF tests a unit-root null; KPSS tests a level-stationarity null. Their log-level conclusions differ. The scope is this contiguous segment only, not all solar observations. A returned zero p-value is an approximation floor, not an exact probability of zero.”

## 4:30–6:00 — Model Results

Click **Model Results**. “These are archived V1 log-space MAE values, in dex; lower is better. All five bars use the same 1,436 origins, 30-minute horizon, two channels and 86,160 scored cells. Neural bars average losses across three seeds; they are not forecast ensembles.”

Point out the descriptive ordering. “Fine-tuned JEPA and the supervised control are close in this retrospective benchmark. This does not establish general pretraining superiority or validated statistical significance.” Open **Exact displayed metrics** only if useful.

Finish at **Research status**. “GOES EDA and the historical V1 comparison are available. V2 infrastructure exists, but its real-data pilot is not authorized. Inference remains unvalidated and SoLEXS integration is pending. Infrastructure tests are not forecasting accuracy evidence.”

If a graph is unavailable during rehearsal, restore its exact local source using the guide. During the presentation, state the limitation and continue to a page with verified evidence; do not regenerate experiments or substitute synthetic data.
