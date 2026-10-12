# Time-series presentation and viva guide

This guide explains the eleven requested topics through SolarJEPA's existing
four-page Streamlit presentation. The initial audit and final evidence are
summarized in [the checklist](PRESENTATION_TIME_SERIES_CHECKLIST.md). Historical
V1 and presentation reports remain unchanged.

The new compact report and ignored diagnostic payload were inspected together.
Fresh saved-parameter replay reproduced the stored predictions, UTC timestamps
and errors. This guide reports those observed outputs; milestone-wide checks
are recorded in `PRESENTATION_TIME_SERIES_VERIFICATION.md`.

Use **DOCUMENTED** for authoritative instrument or method definitions,
**OBSERVED** for measured files/executed results, **INFERRED** for interpretation,
and **UNKNOWN** for facts not established. A working dashboard does not by
itself establish scientific forecasting skill.

## Setup, rebuild and launch

Run commands from the presentation checkout. Use the dashboard environment,
which includes statsmodels 0.14.6; archived V1/EDA results retain their original
environment identities. Do not combine this lock with the research lock.

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dashboard-lock.txt
.venv/bin/python -m pip install --no-deps -e .
PYTHONPATH=src .venv/bin/python scripts/build_time_series_presentation.py --root .
.venv/bin/python -m streamlit run streamlit_app.py
```

Install dependencies before going offline. For a new checkout, first restore
the 123 exact local NetCDF files using the four tracked manifest paths. The
rebuild validates identities, computes the new diagnostics and bounded
classical fits, and writes the compact report plus the ignored scientific-array
payload. It performs no acquisition. Rebuild is an explicit preparation step;
the dashboard's inference action uses saved fitted parameters.

Open the loopback address printed by Streamlit, normally
`http://127.0.0.1:8501`. Stop with Ctrl-C. Restart after code changes because
file watching is disabled. Missing or stale evidence should produce an
unavailable message; restore inputs and rebuild, rather than bypassing hashes.

The presentation scopes are deliberately visible:

| Scope | Support | Purpose |
|---|---|---|
| Interactive native observations | May–June 2024; 61 files, 87,840 minutes | Overview, channel lines and original interactive histograms |
| Full descriptive report | May–August 2024; 123 files, 177,120 minutes | Raw/log statistics, paired scatter and normal Q–Q diagnostics |
| Training diagnostics | `[2024-06-11 16:38,2024-06-18 17:47)` UTC; 10,149 minutes | ADF/KPSS, ACF/PACF and exploratory STL |
| Bounded classical demonstration | First 2,880 minutes of that June run; separate August inference origin | Candidate fitting, grouped AIC/BIC, saved-parameter inference |
| Archived V1 benchmark | Original fitted models and August scored support | Aggregate model comparison, preserved independently of the small demo |

The tracked report is `docs/presentation/time_series_evidence.json`; its
identity sidecar binds sources. The ignored payload is
`results/presentation_time_series/diagnostics.json`. A fresh clone therefore
needs raw-data restoration and rebuild; this is not standalone packaged
scientific-data deployment.

## 1. Data Collection

**What and why.** Collection establishes which instrument, product, measurements
and times the analysis actually represents. Explicit selection and checksums
make the same analysis reproducible without silently changing data versions.

**Actual result — OBSERVED.** Four manifests select 123 GOES-16 EXIS/XRS daily
NetCDF files, 36,535,474 bytes, spanning `[2024-05-01,2024-09-01)` UTC. All
177,120 minute-bin starts are present and unique. Native metadata and the loader
identify irradiance in W/m², record-start times, and UTC with leap seconds
neglected. Native primary flux has already undergone electron correction;
the native `*_flux_raw` fields retain source values before repository QC.
The new statistics table's `raw` transform means unlogged, **QC-valid** flux.
Neither means raw detector counts. Acquisition timestamps
and measured coverage are separate provenance fields. Operational delivery
latency is **UNKNOWN**.

**Tell the professor.** "I use a pinned retrospective GOES irradiance archive.
I verified byte identity and native time/quality metadata before analysis.
The initial live observation view covers May–June; the full descriptive report
covers May–August."

**Viva.** Why not use file modification time as observation time? It records
filesystem activity, not the instrument's measurement interval. Is this
Aditya-L1? No; cross-instrument calibration and alignment are not established.

## 2. EDA: line, scatter, histogram, Q–Q and descriptive statistics

**What and why.** A line plot preserves chronology; paired scatter describes
channel association; histograms summarize marginal distributions; normal Q–Q
plots compare ordered values with normal quantiles. A statistics table exposes
location, spread and tail shape alongside valid/missing counts.

**Actual result — OBSERVED.** Native-unit and log-flux line/histogram plots
already exist. New diagnostics use each channel's own QC-valid population for
raw/log statistics and Q–Q, and the intersection of both masks for paired
scatter. There are 172,646 jointly valid minute pairs, of which 2,500 evenly
spaced chronological pairs are displayed without averaging. Full-scope paired
log correlation is 0.963906. Q–Q uses all 172,646 A and 174,845 B observations
for the fitted reference line; 301 evenly spaced order-statistic ranks per
channel are displayed. The table's `raw` rows describe unlogged QC-valid
irradiance, rather than the pre-QC `*_flux_raw` fields.
Temporal dependence means the plotted minutes are not independent events.

| Channel / transform | Valid minutes | Mean | Median | Sample std (ddof=1) | Minimum | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| A / unlogged W/m² | 172,646 | 5.24529×10^-7 | 8.46184×10^-8 | 4.17789×10^-6 | 1.17708×10^-8 | 4.36458×10^-4 |
| B / unlogged W/m² | 174,845 | 5.66279×10^-6 | 3.25223×10^-6 | 1.41566×10^-5 | 8.12196×10^-7 | 8.68849×10^-4 |
| A / log10 dex | 172,646 | −6.951984 | −7.072535 | 0.546232 | −7.929194 | −3.360057 |
| B / log10 dex | 174,845 | −5.439995 | −5.487819 | 0.321245 | −6.090339 | −3.061056 |

The dashboard additionally shows 25th/75th percentiles and separate absent,
rejected-present and nonfinite-native counts. Values above are rounded for
presentation; the artifact retains full precision. Mean far above median on
the native scale is consistent with the observed right tail; a log scale does
not make that tail disappear or prove normality.

**Tell the professor.** "The raw distribution has bright, infrequent peaks.
The log scale makes multiplicative changes easier to compare. Channel pairing
uses the same UTC minute and both quality masks. Tail departures in Q–Q are
descriptive evidence against a simple marginal normal shape, not a residual
diagnostic for a fitted model."

**Viva.** Does a high correlation imply causation? No; both bands respond to
common solar activity. Does log transformation guarantee a normal distribution?
No; Q–Q and tail statistics must still be inspected. Is display thinning used
to calculate statistics? No; statistics use the full stated valid population.

## 3. Handling Missing Values

**What and why.** Missing timestamps and unusable recorded measurements are
different problems. Filling without a justified observation model could smooth
flare transients or introduce artificial dependence.

**Actual result — OBSERVED.** There are zero absent timestamps and zero
duplicates. XRS-A has 172,646 valid and 4,474 rejected bins; XRS-B has 174,845
valid and 2,275 rejected bins. Each channel has 2,153 nonfinite native values,
which are a subset of rejection and must not be added to it. Longest unavailable
runs are 263 and 245 minutes. QC checks status, positive finite native-range
irradiance, channel-specific electron bits and averaged-measurement count.
NaN and false masks remain; no interpolation or forward fill is applied.

**Tell the professor.** "The clock grid is complete, but not every recorded
measurement is usable. I retain missingness and select contiguous valid runs
for methods that require them. Zero absent timestamps is not perfect data
quality."

**Viva.** Why not interpolate? A scientifically justified fill policy has not
been established, especially around transients. Does rejection of A always
reject B? No; channel-specific electron contamination is treated separately.

## 4. Stationarity Testing: ADF

**What and why — DOCUMENTED.** ADF's null is a unit root; a small p-value
rejects that null under the chosen deterministic terms and lag specification.
KPSS supplies a complementary level-stationarity null. Their nulls differ;
non-rejection proves neither hypothesis. See the versioned
[ADF](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.stattools.adfuller.html)
and [KPSS](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.stattools.kpss.html)
documentation.

**Actual result — OBSERVED.** Tests use the 10,149-minute complete June training
run. ADF has a constant, 30 fixed lags and `autolag=None`; KPSS has a constant
and automatic bandwidth. Raw positive scaling divides by the sample mean for
conditioning. At α=0.05, ADF rejects for raw, log and first-log-difference
series. KPSS does not reject raw or first differences, but rejects both log
levels: p=0.02944 for A and p=0.01734 for B. First-difference KPSS p-values are
greater than 0.10; returned ADF zeros mark its approximation's lower cutoff,
not literal zero probabilities.

**Tell the professor.** "Log levels produce mixed evidence: ADF rejects a
unit root and KPSS rejects level stationarity. First log differences are more
compatible with mean stability within this block. This does not prove global
stationarity of solar irradiance."

**Viva.** Does ADF p<0.05 prove all stationarity assumptions? No; specification,
dependence and changing variance still matter. Why include KPSS? It asks a
different null hypothesis and exposes ambiguity that ADF alone would hide.

## 5. Transformations for Nonstationary Data

**What and why.** Let `z_t = log10(F_t / 1 W m^-2)`. One dex is a tenfold flux
ratio. First differencing gives `z_t - z_(t-1)`, a one-minute log change. The
log addresses scale and relative changes; differencing addresses persistent
level movement. They serve different purposes.

**Actual result — OBSERVED/INFERRED.** The dashboard distinguishes log levels
and first differences. ADF/KPSS and dependence diagnostics are evaluated on
each series, retaining consecutive minute support. Their results support
using d=1 as a bounded teaching-model choice, while leaving wider stationarity
**UNKNOWN**. No values are created by these transformations.

**Tell the professor.** "I compare transformations empirically. A log alone
does not settle stationarity. The forecast model reconstructs log levels and
inverts with `10**z` to return irradiance in W/m²."

**Viva.** Can you difference after simply dropping every missing value? No;
that may subtract across an unknown interval. Is exponentiating a log-space
point forecast an unbiased native-unit mean? Not generally; without a stated
distributional correction it is the inverse-transformed point forecast.

## 6. Seasonality Analysis: seasonal decomposition

**What and why — DOCUMENTED.** STL separates a series into an additive trend,
seasonal component and residual using local smoothing. Its period is an input
to the procedure. See the versioned
[STL documentation](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.seasonal.STL.html).

**Actual result — OBSERVED.** Robust STL is applied to
log flux on the full 10,149-minute complete training run, using a prespecified
period of 1,440 minutes as an exploratory daily-cycle diagnostic. Exact
settings are `seasonal=7`, `robust=True`, `seasonal_jump=1`,
`trend_jump=144`, `low_pass_jump=144`. Trend + seasonal + residual reconstruct
the original log series with maximum absolute error **8.88178×10^-16 dex**.
The plot retains 1,100 original timestamp positions for display. No gap is
interpolated to enable STL.
The trend and low-pass smoothing use jumps of 144 observations and linear
interpolation between local fits to bound computation; this approximates the
smoother, without filling or moving observed measurements.

**INFERRED limitation.** A seasonal component returned at an assumed period
is not proof that nature follows that period. Existing first-difference ACF
at one day is only 0.01421 for A and 0.00816 for B; cross-block stability and
seasonal forecast benefit remain **UNKNOWN**.

**Tell the professor.** "This plot illustrates decomposition under an assumed
daily period. The short block and transient behavior do not establish stable
daily solar seasonality, so I do not use it to justify SARIMA."

**Viva.** Why show STL if SARIMA is not fitted? To inspect and explain an
assumption explicitly, not to promote it into a validated seasonal model.
Is the trend a real-time prediction? No; this is a retrospective smoothing
diagnostic and is not fed into the forecast demo.

## 7. ACF/PACF

**What and why.** ACF measures correlation across a lag. PACF measures the
remaining linear association at that lag after conditioning on intervening
lags. Both help describe dependence and suggest candidate orders.

**Actual result — OBSERVED.** On the same complete June segment, ACF uses
FFT with biased covariance normalization; PACF uses Yule–Walker MLE (`ywm`).
Lag-1 log-level ACF is 0.98697 for A and 0.99247 for B; after differencing it
is 0.54339 and 0.64398. At lag 60 the differenced ACF is −0.00986 and −0.01603.
Squared-difference lag-1 ACF is 0.29700 and 0.44872, consistent with short-run
volatility dependence. No iid significance bands are asserted.

**Tell the professor.** "Levels are persistent; differencing reduces longer-lag
dependence but retains short-lag structure. The plots motivate a small candidate
set; they do not mechanically reveal a single correct model."

**Viva.** Does high ACF mean seasonality? No; persistence or trends also produce
high autocorrelation. Are the lags hours? No; the native cadence is one minute,
so lag 60 means 60 minutes.

## 8. Identify a suitable AR, MA, ARMA, ARIMA or SARIMA model

**What and why — DOCUMENTED.** AR(p) uses past values; MA(q) uses past
innovations; ARMA(p,q) combines them; ARIMA(p,d,q) includes differencing.
SARIMA adds seasonal orders `(P,D,Q,s)`, which require a justified period s.
These are supported special cases of the
[ARIMA interface](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.arima.model.ARIMA.html).

**Actual result — OBSERVED.** Seven candidates per
channel are fitted on the same first 2,880 minutes of the complete training
run: AR(1), AR(2), MA(1), MA(2), ARMA(1,1), ARIMA(1,1,0) and ARIMA(2,1,0).
All fourteen fits converged and their recorded warning lists are empty.
Orders **(1,1,0) for XRS-A** and **(2,1,0) for XRS-B** are selected by training
BIC within d=1. The existing research adapter uses SARIMAX for these
nonseasonal specifications, with fixed supplied orders, L-BFGS and a
100-iteration maximum; the new demonstration reuses that implementation.

**SARIMA decision — INFERRED.** A defensible stable seasonal period has not
been established; SARIMA is explicitly NOT_APPLICABLE for this demonstration.
No seasonal fit, AIC/BIC or forecast score is invented. If an assessment
requires every listed family to be fitted, disclose that this portion is
PARTIAL rather than treating a seasonal model with all seasonal orders zero
as evidence of a genuine seasonal fit.

**Tell the professor.** "I demonstrate the applicable nonseasonal families
and record their limitations. I select a d=1 candidate using training data.
I explain why fitting a seasonal model would add an unsupported assumption."

**Viva.** Is MA a moving average of recent observations? In MA(q), it is a
model of current and lagged innovations, not a smoothing window. Does lowest
BIC prove physical correctness? No; it identifies a preferred candidate
within a declared statistical comparison.

## 9. Identify appropriate lags

**What and why.** p counts AR lags; q counts innovation lags; d counts
differences and is not a time lag. Classical ACF/PACF cutoff heuristics can
motivate small candidate orders under their assumptions, but transient data
need explicit comparison and diagnostics.

**Actual result — OBSERVED.** Candidate AR orders 1/2,
MA orders 1/2 and ARMA(1,1) show short-memory alternatives. The selected d=1
orders are p=1, q=0 for A and p=2, q=0 for B, chosen within their compatible
training groups. The fitting block is
`[2024-06-11 16:38,2024-06-13 16:38)` UTC. The 120-bin inference context and
30-bin forecast horizon are separate design choices; they are not p or q.

**Tell the professor.** "I start with a bounded short-lag candidate set,
motivated by observed dependence. I record the training criterion and keep
August targets out of order selection."

**Viva.** Why not search hundreds of orders? This is a bounded teaching demo;
large searches increase computation and selection risk. Does a 30-minute
horizon mean AR order 30? No; forecast horizon and lag order serve different
roles.

## 10. AIC/BIC

**What and why.** For log likelihood ℓ and k fitted parameters, AIC is
`-2ℓ + 2k`; BIC is `-2ℓ + k log(n_effective)`. Lower values balance fit and
complexity within a valid comparison. The implementation records likelihood
burn/effective support; these criteria are not forecast error metrics. See
statsmodels [AIC](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.arima.model.ARIMAResults.aic.html)
and [BIC](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.arima.model.ARIMAResults.bic.html).

**Actual result — OBSERVED.** The compact artifact records
channel, order, deterministic trend, training support, burn, n, k, log
likelihood, AIC, BIC, convergence and warnings. Rankings are within groups
sharing channel/d/trend/burn, never a global minimum across unlike models.
The d=1 converged group supplies the saved inference models before any August
target values are scored. The dashboard groups candidates and displays family,
order, AIC, BIC and convergence; the artifact retains the additional settings.

The d=1 groups have no deterministic trend (`n`), likelihood burn 1 and
2,879 effective observations, from 2,880 input minute bins:

| Channel | Order | Fitted parameters k | AIC | BIC | Training-BIC selection |
|---|---|---:|---:|---:|---|
| A | (1,1,0) | 2 | −12,311.066341 | −12,299.135945 | Selected |
| A | (2,1,0) | 3 | −12,310.261033 | −12,292.365438 | — |
| B | (1,1,0) | 2 | −20,616.476402 | −20,604.546005 | — |
| B | (2,1,0) | 3 | −20,686.727780 | −20,668.832186 | Selected |

Compare the two A rows with each other, or the two B rows with each other.
Each channel's five d=0 candidates form another group with a constant, burn 0
and 2,880 effective observations. AR(2) has the lowest BIC in each of those
groups, but the declaration to deploy a d=1 model was made independently of
August errors. Neither d=0 nor cross-channel values form a global ranking
with the table above.

**Tell the professor.** "I compare like with like. Lower training BIC guides
the chosen order; held-out forecast errors answer a different question. A
negative AIC or BIC is allowed because the likelihood scale can produce it."

**Viva.** Can AIC be compared between A and B? Not as model-order evidence
for one response; the data and likelihoods differ. Is lower BIC guaranteed to
give lower test MAE? No; training-model preference and forecast performance
are related but distinct.

## 11. Deploy the Model

**What and why.** Deployment connects a fitted model's parameters, validated
past observations and prediction code to an application. Training estimates
parameters; inference applies those parameters to a new permitted context.
statsmodels exposes a separate
[filter operation](https://www.statsmodels.org/v0.14.6/generated/statsmodels.tsa.arima.model.ARIMA.filter.html)
for a supplied parameter vector.

**Actual result — OBSERVED.** The Model Results page
offers an explicit saved-model inference action. It uses the selected classical
parameters and 120 past minute bins to forecast 30 future bins at the earliest
eligible August origin. Saved-model W/m² and log-transform declarations,
channel identities, positive finite values,
unique consecutive UTC timestamps and issue-time boundaries are validated.
Future observations are used only for the later overlay/error calculation;
they do not enter filtering or fitting. The UI remains thin: reusable core
code performs inference, while Streamlit displays results.

The issue is **2024-08-01 02:00 UTC**. Completed context bins start at 00:00
through 01:59 UTC; forecast/realized target-bin starts run 02:00 through 02:29,
with exclusive target end 02:30 UTC. Lead 1 starts at issue time and ends one
minute later. The earliest eligible window is selected by chronology, cadence
and joint QC validity; model selection does not use future values. Selecting a
complete retrospective target window is not a live data-availability guarantee.

The overlay displays irradiance in W/m² on a logarithmic axis; its errors are
log-space MAE/RMSE in dex on the same held-out 30-minute support per channel:

| Channel | Saved order | Log MAE (dex) | Log RMSE (dex) |
|---|---|---:|---:|
| XRS-A | (1,1,0) | 0.218835296 | 0.256635485 |
| XRS-B | (2,1,0) | 0.094347424 | 0.109055349 |

Fresh replay matched all 30×2 predictions and the stored errors. No prediction
interval is claimed. Native outputs are conditional inverse-log predictive
medians under the fitted Gaussian log-space model, rather than bias-corrected
native means. A single origin does not establish aggregate skill.
The original V1 aggregate chart remains
separate and unchanged; its metrics must not be mixed with this new demo.

**Tell the professor.** "Clicking the action executes inference with saved
parameters; it does not train a model. The forecast begins at a known issue
time, and the timestamp-aligned overlay compares genuinely later bins. This
is local offline deployment with explicit input/artifact requirements."

**Viva.** Can the app forecast arbitrary uploaded data? This demonstration
accepts its declared validated input contract and bundled origin, not arbitrary
unvalidated uploads. Is it an operational flare-warning system? No; delivery
latency, event labels, alert thresholds and prospective skill remain UNKNOWN.
Why keep V1 separate? It has a different fitting/evaluation protocol and a
much larger aggregate evaluation support.

## Rehearsal and honest conclusions

Start at Overview for collection and units. In Data Explorer, explain QC,
paired association, distribution shape, Q–Q and the full-scope statistics.
In Time-Series Analysis, explain stationarity nulls, transformations,
ACF/PACF and the assumed-period STL limitation. In Model Results, show
comparable candidate groups, selected order and the inference action, then
identify the archived V1 benchmark as a separate result.

The supported conclusion is that the application demonstrates a reproducible,
quality-aware time-series workflow and executable bounded classical inference.
Stable physical seasonality, global stationarity, operational flare-warning
skill, V2 success and Aditya-L1 integration remain unestablished. Final
verification commands/results are recorded separately in
`PRESENTATION_TIME_SERIES_VERIFICATION.md`.
