# v1 demo plan: temporal JEPA vs ARIMA/SARIMA vs ARCH/GARCH (3 days)

Branch `v1`, created from P2 tip `656e540162c635d4c2274b4469ae11247290f986`
(`feat/p2-dual-source-training-foundation`). P1/P2/main and all other branches
are untouched. This is a bounded demo milestone, not P1/P2 integration, not a
SoLEXS result (`BLOCKED_FOR_PHASE_E` unchanged) and not a final paper protocol.

## Question

On GOES-16 XRS-A/XRS-B one-minute flux, 120-minute context and 30-minute
horizon, does a small self-supervised temporal JEPA give better point and
probabilistic forecasts than (a) the six P2 baselines, (b) ARIMA/SARIMA and
(c) AR-ARCH/GARCH/GJR-GARCH volatility models, and is any gain caused by JEPA
pretraining rather than the architecture (identical supervised control)?

## Data (small, a priori, pinned)

| Partition | UTC half-open | Notes |
|---|---|---|
| Train | 2024-05-01 → 2024-07-22 | Includes the May 2024 AR 13664 active period |
| Validation | 2024-07-22 → 2024-08-01 | Contains the 5 days P2 used as test; used only for selection now |
| Test | 2024-08-01 → 2024-09-01 | Never touched by P1/P2 or any v1 selection |

Four pinned NOAA/NCEI monthly selections (~37 MB). May, June and August use
new configs/manifests via the unchanged bounded acquisition pipeline; July
reuses the P2 manifest. The new `goes_historical_multi` dataset kind
concatenates verified selections only when exactly contiguous.

## Models (all fitted on train only)

- P2 point baselines: persistence, training mean, trailing mean, drift, AR(1), direct ridge.
- `persistence_empirical`: persistence plus train-only empirical increment quantiles per lead.
- ARIMA(p,1,q) small grid on log10 flux, order chosen by validation pinball.
  SARIMA is implemented but excluded from the run: no 60-min/daily periodicity
  in the log-difference ACF and an s = 60 fit did not finish in 28 min.
- Two-stage AR(1) mean (OLS) on log-differences, then constant variance,
  ARCH(1), GARCH(1,1) (Normal and Student-t) and GJR-GARCH(1,1)-t fitted on the
  residuals by multi-start MLE; simulated paths → quantiles. Joint MLE gave an
  explosive mean on these heavy-tailed data (see `docs/V1_RUN.md`).
- Temporal JEPA (patch encoder, EMA target encoder, latent predictor) with a
  quantile head: `jepa_finetune`, `jepa_frozen`; `supervised` = identical
  architecture without JEPA pretraining (the key ablation); 3 seeds.

## Metrics

Log-space (dex) MAE of the median, mean pinball over five quantiles, 50/90%
pointwise interval coverage and width, by lead and by retrospective strata
(M+ flaring targets, quiet < C1, rising ≥2×). Native W/m2 MAE/RMSE and skill
via the existing P1 evaluator. Paired daily-block bootstrap CIs on test vs
persistence_empirical, the best GARCH-family model and selected ARIMA.

## Three-day schedule

| Day | Work | Owner / resource |
|---|---|---|
| 1 | Branch, data, multi-manifest adapter, classical models, JEPA module, tests | This Windows machine (CPU) |
| 2 | Smoke + full strict run (3 seeds), results doc + figures | Mac M4 16 GB (the Windows laptop ran out of memory); see `docs/V1_RUN.md` |
| 3 | Review, reproduce on Mac M4 (canonical platform), demo notebook/slides; optional Kaggle rerun with more seeds/longer pretraining | Team |

## Team split for after the demo

- **Mac M4 16 GB**: strict reproduction (`pytest`, `scripts/run_v1_comparison.py`
  without `--dev`), multi-year GOES acquisition (one bounded config per month),
  classical models on longer data, statistics and writing.
- **Kaggle GPU**: JEPA pretraining on multi-year data, more seeds, LSTM/TCN/
  PatchTST and time-series foundation model comparisons.
- **Data**: GOES-16 2017–2025 + GOES-18/19 and the NCEI composite flare report
  for event labels (see the onboarding notes); SoLEXS only after the Phase E gate clears.

## Known limits (by design)

Four months of one satellite near solar maximum; overlapping contexts; no
event labels or flare-probability claims; retrospective archive data; CPU
budgets bound model size and epochs. Results are a demo benchmark, not
generalizable skill.
