# GOES-16 presentation EDA

Analysis date: 2026-10-10 (Asia/Kolkata). Scope: the existing V1 archive and
read-only presentation diagnostics. **OBSERVED** numbers below were recomputed
from pinned local measurements; **INFERRED** statements are interpretations.
**DOCUMENTED** identifies instrument/API definitions; **UNKNOWN** stays unknown.

## Dataset and reproducibility

**OBSERVED:** 123 SHA-256-verified daily NetCDF files, 36,535,474 bytes, product
`xrsf-l2-avg1m_science`, version `2-2-1`, GOES-16 EXIS/XRS. Measured coverage is
**[2024-05-01 00:00, 2024-09-01 00:00) UTC**, not a filename or filesystem-date
estimate. All 177,120 record-start timestamps are present and unique; all
177,119 adjacent deltas are 60 s. Each measurement is a one-minute bin. The
native epoch uses UTC with leap seconds neglected, as validated by the loader.

| Month | Manifest | Bins | Files |
|---|---|---:|---:|
| May | `data/manifests/goes_v1_202405.json` | 44,640 | 31 |
| June | `data/manifests/goes_v1_202406.json` | 43,200 | 30 |
| July | `data/manifests/goes_p2_july2024.json` | 44,640 | 31 |
| August | `data/manifests/goes_v1_202408.json` | 44,640 | 31 |

**DOCUMENTED:** XRS-A covers 0.05–0.4 nm; XRS-B covers 0.1–0.8 nm. Irradiance
units are W m⁻². Science-quality products incorporate retrospective processing
and differ from operational data. See the [NOAA XRS L2 guide, sections 2–4](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf)
(6 October 2026 edition; accessed 2026-10-10).

**OBSERVED:** Native `xrsa_flux`/`xrsb_flux` metadata identifies electron-corrected
primary irradiance. “Raw flux” in the figure means this supplied product before
repository QC; it does not mean detector counts or uncorrected irradiance.
`*_num` is the number of averaged measurements, not exposure duration. No
extra calibration or orbital correction was introduced.

Run the installed project environment:

```bash
.venv/bin/python -m pip install --no-deps .
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/build_presentation.py
```

The optional notebook tools are in `requirements-presentation.txt`; scientific
dependencies are unchanged in `requirements-v1-lock.txt`. Open and run
[`notebooks/presentation_goes_eda.ipynb`](../notebooks/presentation_goes_eda.ipynb)
using this environment. It contains no embedded measurements or absolute
machine paths. Compact numerical outputs are retained. Input checksums,
statistical settings and plot lineage are in [`docs/presentation/`](presentation/).

## Data quality

V1's existing loader requires finite positive irradiance within native valid
bounds, channel status 0, valid channel-specific electron-correction bits and
an averaged-measurement count in 1–60. It rejects invalid/interpolated/decaying
electron correction and significant contamination for the relevant primary
channel. It does not reject B solely for A contamination. No interpolation,
forward fill, clipping, resampling or observation replacement is used here.

| Quantity | XRS-A | XRS-B |
|---|---:|---:|
| QC-valid bins | 172,646 | 174,845 |
| QC-rejected present bins | 4,474 (2.526%) | 2,275 (1.284%) |
| Nonfinite native values | 2,153 | 2,153 |
| Nonpositive finite native values | 0 | 0 |
| Longest unavailable run | 263 min | 245 min |
| Minimum valid irradiance, W m⁻² | 1.17708×10⁻⁸ | 8.12196×10⁻⁷ |
| Median valid irradiance, W m⁻² | 8.46184×10⁻⁸ | 3.25223×10⁻⁶ |
| Maximum valid irradiance, W m⁻² | 4.36458×10⁻⁴ | 8.68849×10⁻⁴ |

Nonfinite values are a subset of QC rejection, so these counts must not be
added. Zero absent timestamps does not mean zero missing usable measurements.
Observed channel-status counts are 174,878 good, 2,153 bad, 61 eclipse and
28 interpolated for each channel. Electron flags add channel-specific rejection.
These descriptive counts concern the whole archive, not the retained forecast
sample. See [data quality](figures/presentation/eda_data_quality.png).

## Descriptive findings

**OBSERVED:** The native-unit distribution has a long right tail. The 99th
percentiles are 8.65283×10⁻⁶ W m⁻² (A) and 5.12561×10⁻⁵ (B). Taking
`log10(F / 1 W m⁻²)` spreads the range and represents multiplicative changes
additively; it does not ensure stationarity. A one-dex change is a factor of
ten in flux. Loss differences measured in dex are not percentage flux changes.

**INFERRED:** Intermittent high peaks and changes in daily median/IQR show why
one aggregate native-unit error can be dominated by bright intervals. The
six-hour rolling log mean and sample variance vary substantially. Each rolling
point requires 360 consecutive valid bins; gaps invalidate windows instead of
being bridged. Changing variance alone does not establish a unit root.

Daily median/IQR summarizes within-day variability, rather than confidence
intervals for a daily mean or evidence of daily solar seasonality. All valid
minute bins enter distributions; temporal dependence means histogram counts
are not independent events. No flare event labels are generated.

## Stationarity protocol and results

Tests use the **earliest longest jointly valid contiguous training block**:
**[2024-06-11 16:38, 2024-06-18 17:47) UTC**, 10,149 minute bins (about seven
days), chosen by continuity rather than a favorable test statistic. No
held-out data enter these diagnostics. The population is this complete block,
not all four months or the solar cycle.

ADF uses an intercept (`regression='c'`), 30 fixed augmentation lags and no
autolag selection; it has 10,118 regression observations for levels and 10,117
for differences. KPSS uses an intercept and automatic HAC bandwidth. Native
flux is divided by its sample mean solely for conditioning in the raw-level
tests; constant positive rescaling does not change the statistical hypothesis.

**DOCUMENTED:** ADF tests a unit-root null against a stationary alternative
under its deterministic/lag specification. KPSS reverses the direction: its
null is level stationarity and its alternative is a nonstationary stochastic
component. See [ADF](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html)
and [KPSS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html)
API documentation; executed statsmodels version is **0.14.5**. Online stable
documentation can describe a newer version.

| Channel / series | ADF statistic | ADF p | KPSS statistic | KPSS p | KPSS HAC lags |
|---|---:|---:|---:|---:|---:|
| A / raw scaled | −12.4288 | 3.98×10⁻²³ | 0.1376 | >0.10 | 55 |
| B / raw scaled | −10.0640 | 1.31×10⁻¹⁷ | 0.2655 | >0.10 | 57 |
| A / log levels | −8.7630 | 2.64×10⁻¹⁴ | 0.5543 | 0.02944 | 58 |
| B / log levels | −8.2239 | 6.32×10⁻¹³ | 0.6582 | 0.01734 | 58 |
| A / first log differences | −22.3947 | lower approximation cutoff (returns 0) | 0.00245 | >0.10 | 15 |
| B / first log differences | −21.1906 | lower approximation cutoff (returns 0) | 0.00273 | >0.10 | 13 |

**OBSERVED:** statsmodels returns 0 for the two 30-lag log-difference ADF
p-values because these statistics are below its MacKinnon approximation's
lower cutoff (−18.83 for this specification). This is neither a measured
literal zero probability nor floating-point underflow.
KPSS values beyond its tabulated range are inequalities, not exact 0.10.
All ADF 10/30/60-lag sensitivities reject at 0.05; exact results, critical values
and warnings are in [stationarity.csv](presentation/stationarity.csv) and
[eda_evidence.json](presentation/eda_evidence.json) (the JSON retains sensitivities).

**INFERRED, at α=0.05:** Both log-level series reject a unit root **and** reject
level stationarity. This mixed diagnostic does not prove either global
stationarity or a unit-root model. Raw-scale tests do not reject KPSS; this
transformation dependence also counsels caution. First log differences are
more compatible with a stable mean in this block: ADF rejects its null and
KPSS does not reject its null. Non-rejection is not proof. Differencing also
changes the scientific quantity from irradiance level to one-minute log change.

Assumptions and limits: lag/deterministic specification matters; residual
dependence, heavy tails, flare transients and regime shifts can alter test size.
KPSS uses a HAC long-run variance estimate. Thousands of autocorrelated
observations can produce tiny p-values for small departures; they are not
independent replications. No residual-whiteness or cycle-wide invariance claim
is made. No stationarity decision was used to refit V1 models.

## ACF, PACF and volatility

ACF uses FFT with biased covariance normalization on the contiguous block;
PACF uses Yule–Walker MLE (`ywm`). Neither concatenates valid values across
gaps. No iid ±1.96/√N bands are shown as inferential evidence.

| Diagnostic | XRS-A | XRS-B |
|---|---:|---:|
| Log-level ACF, lag 1 min | 0.98697 | 0.99247 |
| Log-level ACF, lag 60 min | 0.35933 | 0.38841 |
| First-log-difference ACF, lag 1 min | 0.54339 | 0.64398 |
| First-log-difference ACF, lag 60 min | −0.00986 | −0.01603 |
| Squared-log-difference ACF, lag 1 min | 0.29700 | 0.44872 |

**INFERRED:** Levels are strongly persistent; differencing removes much of the
long-lag dependence but leaves short-lag structure. PACF describes remaining
lag relationships after conditioning on shorter lags; visual cutoffs do not
validate a specific ARIMA order. Squared increments retain short-lag
dependence, consistent with volatility clustering and motivation for ARCH
models, without proving any fitted ARCH/GARCH specification is adequate.

## SARIMA decision

**OBSERVED:** Training-block difference ACF at 1,440/2,880/4,320 minutes is
0.01421/0.00984/−0.00266 for A and 0.00816/0.00464/−0.00760 for B. The exploratory
periodogram's strongest retained peaks are around 65–91 minutes, with no
validated repeatable daily peak. These spectral peaks are not a selected
seasonal model: the series is transient, the block is short, frequencies are
many and no significance or cross-block stability was established.

**INFERRED:** No scientifically defensible stable seasonal period has been
established for a fair presentation-only SARIMA addition. The historical
60-minute fit exceeding 28 minutes is **a prior teammate report**, not a runtime
measured in this milestone. SARIMA is deliberately omitted; there is no
SARIMA score or claim that solar flux has no periodic structure. The primary
deliverables do not depend on an optional refit. No new data were downloaded.

## Figure index and limits

All eight required figures are under `docs/figures/presentation/`, as PNG (220
dpi) and SVG; long time-series marks are rasterized within SVG to limit size.
The reproducible [figure manifest](presentation/figure_manifest.json) supplies
captions, source paths and hashes. See [asset inventory](PRESENTATION_ASSET_INVENTORY.md).

- [Native flux](figures/presentation/eda_raw_flux.png) and [log flux](figures/presentation/eda_log_flux.png).
- [Distributions](figures/presentation/eda_distribution.png) and [rolling statistics](figures/presentation/eda_rolling_statistics.png).
- [ACF](figures/presentation/eda_acf.png) and [PACF](figures/presentation/eda_pacf.png).
- [Daily variability](figures/presentation/eda_daily_variability.png) and [data quality](figures/presentation/eda_data_quality.png).

**UNKNOWN:** true operational delivery/revision latency, event-warning skill,
generalization to other satellites/time regimes and robust stationarity outside
the diagnostic segment. EDA describes an already inspected retrospective
archive. It supplies neither confirmatory V2 evidence nor operational alerts.
