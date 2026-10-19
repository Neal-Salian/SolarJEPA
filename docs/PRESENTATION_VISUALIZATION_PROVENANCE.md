# Presentation visualization provenance

The executable registry is `src/solar_flare_jepa/dashboard/registry.json`. It records SHA-256 pins, source commits, dataset/experiment identities, UTC half-open periods, transformations, masks, units, metrics, verification evidence and limitations for every graph and numerical panel. Source changes fail closed. A filename is never the validity criterion.

## Evidence classification and commits

- **OBSERVED:** current native May/June file bytes and hashes; native metadata, timestamps, counts and masks; pinned tracked evidence equals historical Git blobs; saved arrays and stationarity evidence replayed on the exact permitted June segment; published model aggregate consistency.
- **DOCUMENTED:** native GOES time/unit/flag conventions enforced by the existing source-specific adapter and pinned product metadata. The dashboard does not invent calibration or operational latency.
- **INFERRED:** any interpretation of temporal dependence or relative archived model scores. Interpretations are restricted to their stated support; no causal/general-superiority or global-stationarity conclusion follows.
- **UNKNOWN/unvalidated:** V2 real-data forecast accuracy, replacement inferential validity, SoLEXS scientific integration, and timestamp-matched predictions within permitted dashboard inputs.

Historical presentation commit: `660f469683557a0f3134f72ec69b174a5bcdd917`; V1 audit/base: `644648f7d555fcbcb3eed4495d37fecffdd1863a`; executed V1 experiment commit: `4a3f88227ce28dea0e885e68987282285963f38e`. The new status snapshot and dashboard transformations belong to this presentation milestone, not to those historical commits. The snapshot records its underlying source commits/paths/hashes per item; its own registry commit is null until identified by the enclosing final dashboard Git commit.

## Inventory

| Registry ID / displayed graph or panel | Source artifacts | Dataset/experiment and UTC period | Transformation and units | Verification and limits |
|---|---|---|---|---|
| `overview_flux` — GOES Solar X-Ray Flux Over Time | May/June manifests; native files; existing GOES adapter/foundation/verifier | `v1-goes16-202405-science-avg1m-v2-2-1` + `v1-goes16-202406-science-avg1m-v2-2-1`; May 1–July 1 exclusive | Actual bin-start timestamps; QC-valid flux W/m²; logarithmic y-axis; extrema envelope | All 61 file hashes/sizes/native contracts verified. At most 2,400 points/channel; no interpolation or averages; gaps/peaks retained. Display-only, not an experiment. |
| `dataset_summary` — instrument, observation count, cadence | Same pinned native selection | Same May/June scope | Count observed minute timestamps once; cadence 60 seconds; channel valid counts separate | 87,840 observations; 85,769 valid A, 85,891 valid B; no absent grid bins. Counts are not events or channel cells. |
| `channel_flux` — XRS-A and XRS-B comparison | Same as Overview | Same May/June scope | Same timestamped flux/log-axis envelope, W/m² | Same identities/masks; contextual channel comparison, no cross-instrument conversion. |
| `flux_histogram` — Flux distribution | Same selection plus original `presentation/figures.py` algorithm | Same May/June scope, explicitly smaller than original EDA | Display-only `np.histogram(log10(valid_flux / [1 W/m²]),bins=70)` independently per channel; counts of valid minute bins | All valid observations, not line-sampled values. Equal-width edges from each channel's actual min/max; last bin includes upper edge. Counts sum to valid rows. Full-precision edges are retained in chart trace customdata; formatted edges are available in hover. Minute bins are correlated observations, not independent flares. |
| `rolling_statistics` — Rolling statistics, original analysis | Unchanged `docs/figures/presentation/eda_rolling_statistics.png`; pinned `presentation/figures.py` | Original V1 May 1–September 1 exclusive | `log10(flux)`; trailing 360 bins, `min_periods=360`; mean dex and sample variance dex² (`ddof=1`) | Image hash equals original figure manifest and Git blob. Full-window missing policy preserved. It is **variance**, not standard deviation. Original std unavailable. Original full interval is explicitly labelled; this milestone did not open raw August data. |
| `acf` — Autocorrelation | `docs/presentation/eda_evidence.json`; original `presentation/eda.py` | June 11 16:38–June 18 17:47 exclusive; 10,149 jointly valid minute bins | Stored log10 levels / first log differences; FFT, `adjusted=False`; plotted lags 1–120 minutes | Exact array replay from verified June inputs; no re-estimation in app. Difference support begins 16:39. No iid significance bands. |
| `pacf` — Partial autocorrelation | Same diagnostic evidence/algorithm | Same exact June block | Stored levels/differences; Yule–Walker MLE (`ywm`); lags 1–60 minutes | Exact same-block replay. No new dataset, no global stationarity inference. |
| `stationarity` — ADF/KPSS panel | Same EDA JSON; historical verification JSON | Same June block; first differences start one minute later (10,148 inputs) | Raw flux/segment mean, log10 level, first log difference. ADF constant, fixed lag30, no autolag; KPSS constant/level, auto bandwidth | Six stored rows reproduced exactly. ADF null unit root; KPSS null level stationarity. Preserve p-value bounds; returned ADF zero is approximation floor. At 5%, log-level ADF rejects unit root while KPSS rejects level stationarity: no blanket global-stationary claim. |
| `model_comparison` — Model comparison, log-space MAE | `model_metrics.csv`, `model_evidence.json`, V1 dataset/models configs, historical `verification.json` | `v1-full-20261009`; historical August 1–September 1 exclusive | Equal-cell MAE of predicted minus observed **log10** flux, dex; shared 1,436 origins × 30 leads × two channels = 86,160 complete cells | Published table equals grouped evidence; every selected seed/member has identical counts, targets and lead length. Config/hash identities establish period/horizon. Historical replay recorded 422 checks/zero discrepancy; current milestone only rechecks aggregates and does not reopen prediction arrays. |
| `research_status` — Research status / Overview status | New `docs/presentation/dashboard_status.json`; branch source commits/paths/hashes per item | Snapshot October 11, 2026 | Source audit summary, no scientific score | EDA/V1 historical evidence; M4B `2e3f871…` infrastructure and unvalidated inference; M5 `6071868…` preflight-only/null pilot approvals; SoLEXS rejection in presentation source. Registry explicitly distinguishes new snapshot artifact from historical source commits. |

## Quality and plotting contract

The unchanged GOES adapter accepts finite positive native irradiance, status flag zero, count 1–60, native valid ranges, and channel-specific electron-correction masks. Invalid and absent values remain NaN. GOES timestamps are record starts under its documented UTC/leap-second convention; the earliest bin availability is its end, and operational latency remains unknown. No filesystem timestamp substitutes for a scientific timestamp.

The interactive scope is deliberately limited to permitted V1 training observations. Loading explicitly allowlists the May and June manifests and validates their identities before any native access. It never discovers arbitrary data, opens July/August raw inputs, runs a test release, or imports experiment/training runners. Historical graphs/aggregate records may describe other explicitly labelled periods without opening those underlying observations.

Envelope buckets keep original first/last/minimum/maximum measurements and timestamps. Missing runs retain explicit NaN separators plus valid edge observations. If the gap budget cannot be honored, the chart fails with an explanation rather than connecting gaps. The min/max presentation does not estimate a scientific average or new event metric.

## Model values actually displayed

| Model label | Log-space MAE (dex, rounded here) |
|---|---:|
| Empirical persistence | 0.1321037126 |
| ARIMA(2,1,0) | 0.1308026342 |
| Supervised control (three-seed mean) | 0.1179854600 |
| Frozen JEPA (three-seed mean) | 0.1237586706 |
| Fine-tuned JEPA (three-seed mean) | 0.1165932281 |

Neural bars average fitted-seed losses at seeds 17/29/43; they are not ensemble forecasts. All target channels and 30 one-minute leads have equal weight. Volatility comparators are omitted to keep the comparison interpretable without optimizer/boundary qualifications. Pinball, coverage and bootstrap values present in historical artifacts are not displayed as additional results. No V1/V2 mixed comparison, significance claim or reconstructed prediction is shown.
