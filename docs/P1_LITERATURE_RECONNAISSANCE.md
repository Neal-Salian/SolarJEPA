# P1 literature reconnaissance

Date: 2026-10-03 (Asia/Kolkata). This is a bounded design reconnaissance,
not a systematic review, a reproduction study, or an experimental result.
**Phase E remains BLOCKED_FOR_PHASE_E.** Literature cannot resolve the
version-specific SoLEXS timing, exposure, correction, or response gate.

## 1. Scope, method, and evidence labels

The first Paperclip command was `paperclip skill`; the current instructions and
`.agents/skills/paperclip/SKILL.md` were read. Eleven searches returned 49 entries
before deduplication. Ten searches used arXiv; one used the scholarly abstract
corpus to find a specific solar statistics paper missing from the arXiv results.
Selected papers were read with `cat --lines` and narrowly bounded `grep`, and
bibliographic metadata came from `meta.json`. Phys-JEPA's empty author metadata
was supplemented by its full-text author line. Search titles alone support no
scientific claim here. No Paperclip repository, verification commit, clipboard
upload, biomedical database query, or SolarJEPA training was performed.

- **VERIFIED FROM PAPER:** a statement supported by the content actually read;
  this does not mean the paper's experiment was independently reproduced.
- **REASONABLE DESIGN INFERENCE:** an implication drawn from that evidence.
- **PROJECT DESIGN DECISION:** a proposed SolarJEPA choice, awaiting approval.
- **UNKNOWN:** not established by this reconnaissance or repository evidence.

Paperclip searches and arXiv full-text reads worked. `paperclip status` reported
a healthy connection, but its corpus-status helper was unavailable; corpus
freshness/counts were therefore not verified. The abstract corpus exposed an
incomplete record for the 2019 solar heteroskedasticity paper. Its advertised
section path failed, so its primary publisher text was read as an explicitly
identified supplement. No invented Paperclip line citation is attached to it.
Search ranking/index versions were not exposed; this is an exact query log,
not a promise that future searches return identical results.

### Exact searches

```bash
# Q1: solar forecasting formulation
paperclip search -s arxiv 'solar flare forecasting GOES X-ray flux continuous time series forecast horizon evaluation' -n 5
# Q2: solar validation and warning metrics
paperclip search -s arxiv 'solar flare prediction chronological temporal split data leakage active region skill scores TSS HSS' -n 5
# Q3: continuous baselines and metrics
paperclip search -s arxiv 'time series forecasting persistence mean drift autoregressive baselines MAE RMSE scaled error' -n 5
# Q4: conditional variance and solar X-rays
paperclip search -s arxiv 'solar X-ray flux ARCH GARCH conditional variance volatility forecasting' -n 5
# Q5: continuous soft X-ray forecasting
paperclip search -s arxiv 'forecasting solar soft X-ray flux continuous trajectory autoregressive LSTM multi step prediction' -n 5
# Q6: temporal coherence
paperclip search -s arxiv 'How to Train Your Flare Prediction Model temporal coherence' -n 3
# Q7: predictive representation learning
paperclip search -s arxiv 'joint embedding predictive architecture JEPA time series forecasting future latent representations' -n 5
# Q8: structural cross-domain analogy
paperclip search -s arxiv --ranking analogical 'Learning predictive representations from multivariate physical sensor time series to forecast future continuous trajectories while preserving physically meaningful temporal structure.' -n 5
# Q9: targeted solar statistics title
paperclip search -s arxiv 'Solar X-ray variability in terms of a fractional heteroskedastic time series model' -n 3
# Q10: multivariate continuous space-weather forecasts
paperclip search -s arxiv 'multivariate space weather time series continuous forecasting solar flux geomagnetic indices persistence RMSE' -n 5
# Q11: relevant scholarly fallback for Q9
paperclip search -s abstracts 'Solar X-ray variability in terms of a fractional heteroskedastic time series model' -n 3
```

`paperclip lookup doi 10.1093/mnras/stz656` returned no documents before Q11.
Q6 did not retrieve its intended paper among the three results; that paper was
accessed using the identifier already present in the repository's literature
notes. The same targeted-reading route checked I-JEPA, TS-JEPA, Phys-JEPA, and
TS2Vec. These are additional reads, not unrecorded successful search results.
The publisher fallback used the web query `"10.1093/mnras/stz656"`, restricted
to `academic.oup.com`, followed by opening the primary article.

Q1/Q5 also returned photovoltaic/terrestrial irradiance material and unrelated
instrument papers. Those results do not establish solar-flare forecasting
practice. Q8's molecular and home-health matches were not used. The relevant
transportation candidate was read; climate/energy analogies additionally came
from the directly read time-series JEPA papers.

## 2. Solar forecasting formulations and reported windows

**VERIFIED FROM PAPER:** the reviewed flare-warning work mainly predicts whether
a class of flare occurs in a future interval, sometimes as a probability. Using
time-series inputs does not by itself make the output a continuous trajectory.
The Ahmadzadeh paper explicitly describes much prior work as point-in-time
binary/probabilistic forecasting. [1] [2]

| Work | Output and temporal specification actually read | Boundary of relevance |
|---|---|---|
| Landa & Reuveni | GOES X-ray classification; 48-hour input; prediction frames of 1, 3, 6, 12, 24, 48, 72, and 96 hours; compares random and chronological splits. [1] | Event-selected classification, not a dense future-flux forecast. Its missing-value replacement and balanced sampling are not adopted. |
| Ahmadzadeh et al. | SWAN-SF magnetic-property time series; 12-hour observation, 24-hour prediction, one-hour stride; strongest flare in the future interval supplies the label. [2] | Region-based magnetic features and class labels differ from full-disk X-ray trajectories. |
| Stanislavsky et al. (2008 preprint) | FARIMA modelling of daily aggregated flare-energy values; describes a one-day-ahead prediction. [3] | Neither a one-minute flux benchmark nor evidence for a 60-minute SoLEXS horizon. |
| Benson et al. | Continuous multivariate radio-flux/geomagnetic-index forecasting; daily cadence, 108-day input, 27-day output; RMSE and persistence/running-average comparisons. [4] | Different physical quantities and time scale; December of each year is validation, rather than a strict future holdout. |
| Dhuri et al. | Continuous solar-wind-speed forecasts for the following four days; uses RMSE/Pearson correlation and evaluates later cycle-25 observations separately. [5] | Solar wind is not flare X-ray flux; rotational persistence is quantity-specific. |

**REASONABLE DESIGN INFERENCE:** support continuous forecasting and event/risk
evaluation as separate tasks. Horizons cannot be transferred between these
physical targets merely because all are called solar forecasting. The existing
6-hour context / 1-hour horizon is a project proposal, not a literature-validated
choice. Its adequacy for an approved SoLEXS dataset remains **UNKNOWN**.

## 3. Defensible continuous baselines

**VERIFIED FROM PAPER:** persistence uses the last known value and is an
essential simple comparator in general forecasting. Benson et al. directly
compare persistence, running averages, and linear/neural models for continuous
space-weather indices. [6] [4] Event-occurrence persistence and climatology also
appear in operational flare-warning verification, but are different baselines
from flux persistence and a flux mean. [7]

**PROJECT DESIGN DECISION:** the initial foundation should support persistence,
a training-period mean, a causal trailing mean, a simple drift forecast, a small
AR model, and direct ridge regression. Keep the drift as a transparent trend
comparator; this search did not establish its superiority for flare flux.
Call the short-sample mean a *training-period mean*, not a validated solar
climatology. AR/linear models test whether past dependence adds value; taking
logs does not prove stationarity. Do not infer daily or 27-day seasonality for
SoLEXS from photovoltaic or solar-wind forecasting. ARIMA/fractional models
remain later comparisons rather than new P1 dependencies.

## 4. ARCH/GARCH assessment

**VERIFIED FROM PAPER:** ARCH models conditional variance using past squared
innovations; GARCH additionally uses past conditional variance. The read GARCH
specification separates an ARMA-like conditional mean from its conditional
variance equation. The mathematical role is variance/volatility prediction,
not automatically mean-level trajectory prediction. [8] [9]

The primary publisher paper by Stanislavsky et al. analyses one-minute GOES
observations in July–September 2017 and distinguishes active ARFIMA-GARCH and
quieter ARFIMA regimes. It explicitly assigns GARCH the conditional-variance
role. This supports investigating heteroskedasticity; it does not establish
the proposed SoLEXS forecast task or its skill.
[Primary publisher text, abstract and §§1–2](https://academic.oup.com/mnras/article/485/3/3970/5371166).

**PROJECT DESIGN DECISION:** ARCH/GARCH are secondary conditional-variance
comparisons, conditional on training-only residual diagnostics and adequate
data. Compare the same mean model with constant variance, ARCH, and GARCH(1,1).
Keep convergence, parameter constraints, residual dependence, and regime
sensitivity visible. The three-day GOES reference sample is a mechanics smoke
fixture, not an adequacy or scientific-performance study.

**REASONABLE DESIGN INFERENCE:** for point trajectories, the variance equation
alone is not a primary comparator. For probabilistic trajectories it may be
useful with a specified mean model, innovation distribution, and path-generation
procedure. For event probabilities it additionally needs a separately defined
event and validated probability mapping. Conditional variance is not itself
flare probability. Log inversion of a point forecast is not automatically a
conditional mean in physical units. P1 should reserve these interfaces and
record applicability decisions; no ARCH/GARCH fitting is proposed at this
checkpoint. Applicability to an approved SoLEXS target remains **UNKNOWN**.

## 5. Evaluation metrics: keep the estimands separate

| Task | Evidence | Proposed P1 treatment |
|---|---|---|
| Continuous point trajectory | Space-weather studies use RMSE; solar-wind work also reports Pearson correlation. The evaluation review explains persistence-relative and scaled errors. [4] [5] [6] | MAE/RMSE per target and lead, explicit aggregate weights, matched-origin persistence skill, train-scaled MASE, and diagnostic Pearson correlation. Correlation alone cannot measure bias or amplitude error. |
| Continuous uncertainty | ARCH/GARCH's output is conditional variance; a variance is not an interval or a complete forecast distribution by itself. [8] [9] | Reserve quantile/sample metadata; test pinball loss when quantiles are supplied. Broader interval/CRPS evaluation waits for a declared probabilistic forecast contract. |
| Event decisions | Operational verification defines precision, recall/POD, FAR, F1, TSS and HSS; FAR and FPR have different denominators. [7] | A separate evaluator consumes supplied binary outcomes/decisions and returns confusion counts plus these metrics. Use HSS2's explicit formula; return NA and counts for undefined denominators. |
| Event probabilities | Brier score and reliability diagrams evaluate probability forecasts without first discarding probabilities through thresholding. [7] | Separate probability inputs and Brier scoring; thresholds must be selected before test use. No conversion of flux errors into warning skill. |

**PROJECT DESIGN DECISION:** do not use percentage error as the primary score
for small fluxes. MASE uses only adjacent valid training differences; never
bridge gaps or estimate its denominator from test. Constant training data can
make MASE undefined. Peak/timing/integrated-trajectory diagnostics and event
lead-time matching require explicit definitions and are deferred. The older
experiment proposal's mean-pinball primary endpoint remains a proposal for a
future probabilistic study; foundation point-metric tests do not replace it.

## 6. Temporal validation and leakage

**VERIFIED FROM PAPER:** adjacent SWAN-SF windows share substantial observation
support, and placing such clusters in both training and validation can produce
misleading apparent generalization. [2] Landa & Reuveni compare chronological
solar-cycle partitions with random selection. [1] The forecasting evaluation
review identifies whole-series normalization, smoothing, and feature extraction
as leakage routes and distinguishes fixed and rolling forecast origins. [6]
Later-cycle solar-wind testing supplies a useful future-holdout analogy, while
Benson's interleaved December validation should not be described as strictly
chronological. [5] [4]

**PROJECT DESIGN DECISION:** split raw temporal support before window creation;
require full context, feature lookback, target intervals, and any label-maturity
support to fit within one partition. Freeze actual origins and exclusions.
Train-only fitting also applies to representations, scalers, and diagnostic
choices. Keep validation for tuning and a later calibration partition when
needed; final test remains untouched. Event-cluster purging requires approved
event definitions, so P1 exercises that contract with synthetic supplied groups.
Do not create real catalogue negatives from incomplete coverage.

**REASONABLE DESIGN INFERENCE:** overlapping origins also preclude treating
window losses as independent replicates. Preserve per-origin losses for later
paired time-block/event-cluster uncertainty analysis; P1 does not claim
confidence intervals from a three-day reference sample.

## 7. JEPA and predictive representation prior work

- **VERIFIED FROM PAPER:** I-JEPA predicts image-block representations and is
  explicitly non-generative. A decoded future trajectory is an additional
  interface, not a consequence of naming a model JEPA. [10]
- **VERIFIED FROM PAPER:** TS-JEPA learns masked time-series representations
  using an EMA target encoder, then evaluates frozen representations with small
  downstream heads. It includes short/long forecasting and matched-backbone
  autoregressive, reconstruction, contrastive, random-encoder, and supervised
  controls. Its main formulation is univariate. [11]
- **VERIFIED FROM PAPER:** Phys-JEPA directly combines future latent prediction,
  a trajectory decoder, and physical/residual latent components for multivariate
  forecasting, with climate/traffic/electricity experiments. This is close
  methodological prior art, not solar-instrument validation. [12]
- **VERIFIED FROM PAPER:** TS2Vec supplies hierarchical timestamp/subsequence
  representations and a ridge-regression forecasting protocol; it also warns
  that image-style transformation/cropping invariances can be inappropriate for
  time series. [13]

**PROJECT DESIGN DECISION:** P1 should be model-independent and later accept
these controls through the same prediction interface. Preserve timing, masks,
units, and origin identities. JEPA architecture, pretraining, physics losses,
and neural training are outside P1 implementation at this checkpoint.
Whether a carefully validated SolarJEPA experiment offers a new contribution
is **UNKNOWN**; no exact-match search failure establishes novelty.

## 8. Cross-domain methodological analogies

Q8 returned Jiao et al.'s transportation representation method. Its topology
and graph-geometry regularizers preserve similarity structure, and its evaluated
tasks include traffic prediction. [14] This is a useful representation-audit
analogy; it is not evidence that solar flux obeys traffic geometry.
TS-JEPA's weather/temperature/electricity tasks and Phys-JEPA's climate/energy
tasks provide closer continuous sensor forecasting analogies. [11] [12]

**REASONABLE DESIGN INFERENCE:** preserve explicit temporal positions and
measurement identities through the forecasting contract; later audit whether
learned representations preserve relevant temporal information. Import no
augmentation, spatial graph, physical law, or solar performance claim solely
because an analogical search ranked a paper highly.

## 9. Implications for P1 and unresolved questions

The [proposed P1 design](P1_PROPOSED_DESIGN.md) turns these findings into a small
forecast contract, purged chronological windowing, cheap baselines, separate
trajectory/event evaluators, and recorded experiment identities. Synthetic data
test deterministic mechanics; existing verified GOES data may supply a clearly
labelled reference smoke. Neither is a final SoLEXS benchmark.

Remaining **UNKNOWN** questions include the approved SoLEXS representation and
scientific time/quality/exposure/calibration contract; adequate context/horizon
and event counts; residual stationarity and ARCH effects; useful event onset
definitions and label maturity; calibrated uncertainty; safe augmentation and
any valid physical constraint; and comparative JEPA benefit on genuinely later
observations. Resolve the instrument gate through authoritative evidence, and
empirical questions through separately approved experiments.

--------
REFERENCES

[1] Landa, V. & Reuveni, Y. "Low Dimensional Convolutional Neural Network For
Solar Flares GOES Time Series Classification." arXiv (2021).
doi:10.3847/1538-4365/ac37bc (journal version).
https://paperclip.gxl.ai/citations/papers/arx_2101.12550#L22,L47-L49,L54-L75

[2] Ahmadzadeh, A., Aydin, B., Georgoulis, M. K., Kempton, D. J., Mahajan,
S. S. & Angryk, R. A. "How to Train Your Flare Prediction Model: Revisiting
Robust Sampling of Rare Events." arXiv (2021). doi:10.3847/1538-4365/abec88.
https://paperclip.gxl.ai/citations/papers/arx_2103.07542#L22-L25,L32-L35,L43-L55

[3] Stanislavsky, A. A., Burnecki, K., Magdziarz, M., Weron, A. & Weron, K.
"Statistical Modeling of Solar Flare Activity from Empirical Time Series of
Soft X-ray Solar Emission." arXiv (2008); journal version (2009).
doi:10.1088/0004-637X/693/2/1877.
https://paperclip.gxl.ai/citations/papers/arx_0805.0968#L43,L55-L59

[4] Benson, B. et al. "Simultaneous Multivariate Forecast of Space Weather
Indices using Deep Neural Network Ensembles." arXiv (2021). DOI not supplied
by the inspected metadata.
https://paperclip.gxl.ai/citations/papers/arx_2112.09051#L27,L31,L36

[5] Dhuri, D. B., Hanasoge, S. M., Joon, H., Gopika SM, Das, D. & Kaul, B.
"Multi-modal encoder-decoder neural network for forecasting solar wind speed
at L1." arXiv (2025). DOI not supplied by the inspected metadata.
https://paperclip.gxl.ai/citations/papers/arx_2507.17298#L11,L18,L68,L73-L75

[6] Hewamalage, H., Ackermann, K. & Bergmeir, C. "Forecast Evaluation for Data
Scientists: Common Pitfalls and Best Practices." arXiv (2022). This is a
methodological review; DOI not supplied by the inspected metadata.
https://paperclip.gxl.ai/citations/papers/arx_2203.10716#L27,L40-L54,L62-L65,L233-L247

[7] Camporeale, E. & Berger, T. E. "Verification of the NOAA Space Weather
Prediction Center solar flare forecast (1998–2024)." arXiv (2025).
doi:10.1029/2025SW004546.
https://paperclip.gxl.ai/citations/papers/arx_2508.01114#L38-L76

[8] Fryzlewicz, P., Sapatinas, T. & Subba Rao, S. "Normalized least-squares
estimation in time-varying ARCH models." The Annals of Statistics 36,
742–786 (2008). doi:10.1214/07-AOS510.
https://paperclip.gxl.ai/citations/papers/arx_0804.0737#L12-L18,L27

[9] Michańków, J., Kwiatkowski, Ł. & Morajda, J. "Combining Deep Learning and
GARCH Models for Financial Volatility and Risk Forecasting." arXiv (2023).
DOI not supplied by the inspected metadata; used for its explicit specification,
not as evidence of solar performance.
https://paperclip.gxl.ai/citations/papers/arx_2310.01063#L18-L26

[10] Assran, M. et al. "Self-Supervised Learning from Images with a
Joint-Embedding Predictive Architecture." arXiv (2023).
https://paperclip.gxl.ai/citations/papers/arx_2301.08243#L5,L13

[11] Ennadir, S., Golkar, S. & Sarra, L. "Joint Embeddings Go Temporal."
arXiv (2025).
https://paperclip.gxl.ai/citations/papers/arx_2509.25449#L11-L27

[12] Nie, W., Liu, W., Guo, H. & Su, Y. "Phys-JEPA: Physics-Informed Latent
World Models for Multivariate Time-Series Forecasting." arXiv (2026).
Authors verified from the full-text front matter; metadata author field empty.
https://paperclip.gxl.ai/citations/papers/arx_2606.16076#L2,L4,L11-L20

[13] Yue, Z., Wang, Y., Duan, J., Yang, T., Huang, C., Tong, Y. & Xu, B.
"TS2Vec: Towards Universal Representation of Time Series." arXiv (2021).
https://paperclip.gxl.ai/citations/papers/arx_2106.10466#L5,L8-L14,L23,L155

[14] Jiao, Y., van Cranenburgh, S., Calvert, S. & van Lint, H.
"Structure-preserving contrastive learning for spatial time series."
arXiv (2025). doi:10.1016/j.ait.2025.100031.
https://paperclip.gxl.ai/citations/papers/arx_2502.06380#L7,L12-L15

Publisher supplement: Stanislavsky, A. A., Burnecki, K., Janczura, J., Niczyj,
K. & Weron, A. "Solar X-ray variability in terms of a fractional
heteroskedastic time series model." Monthly Notices of the Royal Astronomical
Society 485, 3970–3980 (2019). doi:10.1093/mnras/stz656.
[Primary article](https://academic.oup.com/mnras/article/485/3/3970/5371166).
Paperclip's metadata/abstract record was read, but did not provide usable
line-addressable full text; the cited supplement is the publisher evidence.
