# Time-series presentation requirements checklist

This checklist covers the 12 October 2026 presentation completion milestone.
It supplements the historical presentation reports; their conclusions and
artifact identities remain historical records. Status describes an implemented,
reviewable demonstration within the stated scope, not operational solar-flare
warning capability.

The compact report and ignored diagnostic payload were inspected together;
saved-parameter inference was executed again and matched the stored predictions,
timestamps and errors. Final milestone-wide verification is recorded separately
in `PRESENTATION_TIME_SERIES_VERIFICATION.md`.

Evidence terms: **DOCUMENTED** means an authoritative instrument or method
definition; **OBSERVED** means inspected files or executed code;
**INFERRED** means an interpretation of those observations; **UNKNOWN** means
not established. Documentation alone does not establish implementation success.

## Requirements

| Requirement | Status | Evidence | Dashboard Location | Explanation | Remaining Limitations |
|---|---|---|---|---|---|
| 1. Data Collection | COMPLETE | Four explicit manifests in `configs/experiments/v1_goes_2024.json`; `presentation/eda.py::load_v1_frame`; `data/goes_acquisition.py::verify_history`; `data/foundation.py::validate_goes_files`; original `eda_evidence.json` | Overview; Data Explorer provenance | **OBSERVED:** 123 pinned GOES-16 daily files, 36,535,474 bytes, 177,120 unique minute bins covering `[2024-05-01,2024-09-01)` UTC. Native platform, instrument, units, clock and file identities validated. | Ignored local NetCDF files must be restored separately. Native Overview remains May–June, with 61 files and 87,840 bins. GOES is not Aditya-L1; operational delivery latency is UNKNOWN. |
| 2. EDA: line graph, scatter, histogram, Q–Q plot, descriptive statistics | COMPLETE | Original `presentation/figures.py::eda_figures`; new `presentation/time_series.py::eda_diagnostics`; `time_series_evidence.json`; `tests/test_time_series_presentation.py` | Overview and Data Explorer | Original line/histogram assets are preserved. Paired log scatter has 172,646 jointly valid A/B minutes, with 2,500 displayed. Raw/unlogged and log statistics use each channel's QC-valid population; normal Q–Q retains 301 order-statistic ranks per channel for display. | New table `raw` differs from native pre-QC `*_flux_raw`. Full May–August outputs are separate from interactive May–June plots. Display thinning is not statistical resampling. Q–Q describes marginal shape, not independent residual normality. |
| 3. Handling Missing Values | COMPLETE | `data/goes.py::read_goes`; `data/foundation.py::validate_goes_files`; `presentation/time_series.py::eda_diagnostics`; mask/absent-bin tests | Data Explorer quality and summary tables | **OBSERVED:** zero absent timestamps; A/B have 4,474/2,275 QC-rejected measurements, including 2,153 nonfinite values each. Missing values retain NaN and false masks. New summary uses `observed` to distinguish absent from rejected present bins. Contiguous diagnostics do not bridge gaps. | Zero missing timestamps does not mean every measurement is usable. No scientifically justified imputation is established. Historical `data/eda.py::summarize` remains limited for reindexed grids; current original evidence is unaffected because absent count is zero. |
| 4. Stationarity Testing: ADF | COMPLETE | `presentation/eda.py::stationarity_analysis`; `docs/presentation/eda_evidence.json`; `stationarity.csv`; `tests/test_presentation.py` | Time-Series Analysis → Stationarity | ADF is shown with constant regression, 30 fixed lags and no autolag; complementary KPSS uses a constant and automatic bandwidth. Both channels' log levels reject both nulls at 0.05; first log differences reject the ADF null and do not reject KPSS. | Results concern one contiguous 10,149-minute June training segment. Tiny p-values and non-rejection do not prove global stationarity. Saved ADF p=0 is an approximation cutoff. |
| 5. Transformations for Nonstationary Data | COMPLETE | `presentation/eda.py::stationarity_analysis`; log plots and transform selectors | Data Explorer; Time-Series Analysis | `log10(F / 1 W m^-2)` expresses multiplicative variation; the first log difference expresses one-minute log change. Tests and ACF/PACF distinguish levels and differences. Raw scaling is numerical conditioning only. | Logarithms do not guarantee stationarity. Differencing changes the target quantity; neither transformation adds observations. Raw irradiance and dex are not interchangeable units. |
| 6. Seasonality Analysis: seasonal decomposition | COMPLETE | `presentation/time_series.py::seasonal_diagnostic`; STL report/ignored arrays; reconstruction and rejected-segment tests | Time-Series Analysis → Exploratory STL | Robust STL decomposes the full 10,149-minute contiguous training run into trend, an assumed daily component and residual on log flux. Reconstruction maximum error is 8.88178×10^-16 dex. Period 1,440 is a prespecified diagnostic assumption, not a discovered solar period. | About seven days cannot establish stable daily seasonality. STL returns a component for its supplied period. LOESS jump interpolation approximates smoothing, not missing observations. No SARIMA seasonal period is validated. |
| 7. ACF/PACF | COMPLETE | `presentation/eda.py::dependence_analysis`; saved `eda_evidence.json`; original ACF/PACF assets | Time-Series Analysis → Autocorrelation and partial autocorrelation | ACF uses FFT/biased covariance normalization; PACF uses Yule–Walker MLE. Log levels and first differences use the same complete segment. Lag units are minutes. | No iid significance bands or automatic order-selection claim. Dependence structure may change across regimes. |
| 8. Identify a suitable AR, MA, ARMA, ARIMA or SARIMA model | PARTIAL | `presentation/classical.py::build_classical`; fourteen candidate and selected-model records in `time_series_evidence.json`; `tests/test_presentation_classical.py` | Model Results → Classical model identification | All fourteen fits converged: seven candidates per channel illustrate AR(1/2), MA(1/2), ARMA(1,1), ARIMA(1,1,0)/(2,1,0). Training BIC selects ARIMA(1,1,0) for A and ARIMA(2,1,0) for B. SARIMA is explicitly NOT_APPLICABLE because a defensible stable seasonal period is unestablished. | Applicable nonseasonal identification is complete. This conservative status reflects that no SARIMA fit/score exists; if justified applicability decisions satisfy the rubric, identification is complete. The small demo is separate from archived V1. |
| 9. Identify appropriate lags | COMPLETE | Existing ACF/PACF; `presentation/classical.py::ORDERS` and `build_classical`; common-training-support and held-out-mutation tests | Time-Series Analysis explanations; Model Results candidate table | Explain p as AR order, d as differencing order and q as innovation order. The fixed candidate list uses the same 2,880 training minutes. Training BIC within d=1 selects p=1 for A and p=2 for B; q=0 for both. | ACF/PACF heuristics motivate candidates, not a uniquely correct order. Candidate search is small. Seasonal lags remain unsupported. |
| 10. AIC/BIC | COMPLETE | `presentation/classical.py::build_classical`; comparable-group IDs, n, k, likelihood, criteria, convergence/warnings; criterion reconstruction tests | Model Results → AIC/BIC group expanders | Rankings are within compatible channel/d/trend/burn groups. Selected BIC is −12,299.135945 for A and −20,668.832186 for B. Selection is frozen before August targets are consulted. | Do not rank different channels, transformations or incompatible likelihood supports together. Criteria describe training-model tradeoffs, not held-out error or physical truth. |
| 11. Deploy the Model | COMPLETE | `streamlit_app.py`; `dashboard/time_series.py::render_models`; `presentation/classical.py::infer`; `presentation/time_series.py::replay_deployment`; causal replay/UI tests | Model Results → Run saved-model inference | Fresh saved-parameter inference matched the stored 30×2 forecast and errors at issue `2024-08-01T02:00:00Z`, using exactly 120 completed past bins. Target-bin starts span 02:00–02:29 UTC. No fitting occurs during dashboard rendering or replay. | Local offline deployment; requires installed dependencies and ignored diagnostic payload. Rebuild requires exact raw inputs. One deterministic origin is a demonstration, not aggregate validation. No public hosting, operational alert or V2 release is implied. |

## Initial audit and completion boundary

The initial read-only audit of dashboard commit `d718177` found collection,
ADF/KPSS, transformations and ACF/PACF already implemented. EDA lacked an
explicit paired scatter, Q–Q plot and full descriptive table. Seasonal
decomposition was absent. The dashboard presented archived model scores but
did not run inference. Classical family/order and AIC/BIC teaching evidence
needed a bounded addition. These findings motivated additions rather than a
replacement of existing scientific or model code.

| Requirement | Initial audit at `d718177` |
|---|---|
| 1. Data Collection | COMPLETE; full local collection verified outside the smaller dashboard data selection |
| 2. EDA | PARTIAL; paired scatter, Q–Q and full statistics table absent |
| 3. Handling Missing Values | COMPLETE for the selected archive; latent reindexed-grid summary limitation |
| 4. Stationarity Testing | COMPLETE |
| 5. Transformations | COMPLETE |
| 6. Seasonality Analysis | MISSING seasonal decomposition; existing seasonal-decision evidence retained |
| 7. ACF/PACF | COMPLETE |
| 8. Model Identification | PARTIAL presentation coverage of listed classical families |
| 9. Appropriate Lags | PARTIAL explicit teaching and candidate comparison |
| 10. AIC/BIC | PARTIAL presentation of comparable criteria/groups |
| 11. Deploy the Model | PARTIAL; app displayed existing scores without executing inference |

Initial targeted verification: 93 tests passed across GOES, acquisition, EDA,
P2/V1 foundation and presentation; all 52 original figure-manifest source and
artifact hashes matched. This is initial-audit evidence, not verification of
the later additions. Final executed checks belong in
`PRESENTATION_TIME_SERIES_VERIFICATION.md`.

An earlier new targeted scientific/classical/UI selection passed **49 tests**.
The final complete suite, including subsequent timestamp and UI regressions,
passed **1,259 tests, zero failures and zero skips** in the isolated installed
environment. The
saved-parameter replay also reproduced the actual native artifact's 30×2
predictions, timestamps and log errors. The environment emitted one existing
NumPy/netCDF binary-size warning; passing tests and numeric replay are the
verification evidence, rather than treating the warning as a scientific result.

## Reproducibility and artifact roles

Tracked `docs/presentation/time_series_evidence.json` contains the compact
scientific report: scope, summary statistics, candidate fits/selection, metrics
and provenance. `time_series_identity.json` binds the report and its sources.
Scientific arrays, including sampled EDA points, STL components, selected
context, targets and forecasts, belong in ignored
`results/presentation_time_series/diagnostics.json`. They are regenerable and
are not a portable dataset committed to Git.

Restore all four manifest-selected raw collections at their exact
repository-relative paths before rebuilding on a relocated checkout. Follow
[the guide](PRESENTATION_TIME_SERIES_GUIDE.md) for setup, rebuild, launch and
the scientific limits to explain during presentation.

## Exact source and test index

- [Original loader and diagnostics](../src/solar_flare_jepa/presentation/eda.py):
  `load_v1_frame`, `longest_complete_block`, `stationarity_analysis`,
  `dependence_analysis`.
- [Original figures](../src/solar_flare_jepa/presentation/figures.py):
  `eda_figures`; eight original EDA PNG/SVG pairs in `docs/figures/presentation/`.
- [New scientific report](../src/solar_flare_jepa/presentation/time_series.py):
  `eda_diagnostics`, `seasonal_diagnostic`, `build_evidence`, `load_evidence`,
  `replay_deployment`.
- [Classical fitting and inference](../src/solar_flare_jepa/presentation/classical.py):
  `build_classical`, `infer`, `_first_test_window`, `_forecast_record`;
  reuses `src/solar_flare_jepa/forecasting/statistical.py::ARIMA`.
- [Thin dashboard renderers](../src/solar_flare_jepa/dashboard/time_series.py):
  `render_explorer`, `render_analysis`, `render_models`;
  [four-page application](../streamlit_app.py).
- [Mask, Q–Q, decomposition and artifact tests](../tests/test_time_series_presentation.py);
  [causal fitting/inference and information-criterion tests](../tests/test_presentation_classical.py);
  [chart, UI and no-fitting tests](../tests/test_time_series_ui.py).
- [Offline rebuild CLI](../scripts/build_time_series_presentation.py), with
  `--root` selecting the repository/data workspace.
