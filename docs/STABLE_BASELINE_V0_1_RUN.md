# Stable Baseline v0.1: setup and launch

This baseline supports offline historical GOES research and the existing frozen
V1 models. V2 pilot execution, V3 research, live inference and scientifically
blocked SoLEXS functionality are excluded. No setup or verification command below
re-trains a model, rebuilds scientific evidence or downloads observations.

## Install one compatible environment

The observed reproduction platform is CPython **3.13.3**, macOS arm64, CPU.
The package declares Python >=3.11; other Python/platform combinations are not
verified by this release. PyTorch wheels and accelerator dependencies differ by
platform. The version lock records an observed environment, not a portable
hash-locked package archive.

From the integration checkout:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-stable-lock.txt
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m pip check
.venv/bin/python scripts/check_stable_baseline.py --references
```

`requirements-stable-lock.txt` includes the unchanged dashboard-prediction lock
and pins the inherited Astropy/cdflib test dependencies. Their presence enables
inherited imports/tests; it does not enable blocked SoLEXS scientific processing.
Do not overlay `requirements-lock.txt`, `requirements-training-lock.txt` or
`requirements-v1-lock.txt`: historical Pillow/packaging pins conflict with
Streamlit 1.50. Reinstall the package after changing source; ordinary installation
is a snapshot, and checkpoint inference verifies loaded source identities.
Both dashboard registry JSON resources are included in the installed package.

## Restore original ignored artifacts

Git supplies reproducibility code, configurations, manifests and small evidence
documents. Restore the exact original files at their manifest-relative paths
inside this checkout; do not replace them with synthetic inputs, retraining or
recomputed reports. Original source copies must remain untouched. Out-of-root
symlinks are rejected. See [storage policy](DATA_STORAGE.md).

| Purpose | Required originals |
|---|---|
| Overview and Data Explorer | 31 May and 30 June GOES NetCDF files listed in `data/manifests/goes_v1_202405.json` and `goes_v1_202406.json` |
| Solar Flux Prediction | 31 August GOES files listed in `goes_v1_202408.json`; `jepa_finetune_seed17.pt` and optional displayed comparator `supervised_seed17.pt` |
| Extended time-series displays and classical replay | `results/presentation_time_series/diagnostics.json`, pinned by `docs/presentation/time_series_evidence.json` |
| Full release verification | All 123 May–August GOES files, including `data/manifests/goes_p2_july2024.json`; the complete frozen V1 bundle below |

Native products belong under
`data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/{05,06,07,08}/`
with their original names. The V1 bundle belongs under
`results/experiments/v1-full-20261009/` and contains:

- `summary.json`, `per_origin.json`, `test_predictions.npz`.
- `jepa_finetune_seed{17,29,43}.pt`, `jepa_frozen_seed{17,29,43}.pt`,
  `supervised_seed{17,29,43}.pt` (nine separate original checkpoints).

The default preflight hashes all five-page inputs: 92 May/June/August native
files, both displayed seed17 checkpoints, pinned source/evidence identities and
the saved time-series payload. `--references` additionally requires July, all
nine checkpoints, summary, per-origin scores, the prediction archive and original
presentation identities. Both modes print JSON and exit nonzero for missing or
changed artifacts or mismatched installed dependency versions. They read bytes
only: no native parsing, checkpoint loading, inference, fitting or networking.
Missing inputs are an explicit release blocker; preflight does not restore them.

Verify individual native selections read-only with explicit manifests:

```bash
.venv/bin/python scripts/acquire_goes_history.py --verify --manifest data/manifests/goes_v1_202405.json
.venv/bin/python scripts/acquire_goes_history.py --verify --manifest data/manifests/goes_v1_202406.json
.venv/bin/python scripts/acquire_goes_history.py --verify --manifest data/manifests/goes_p2_july2024.json
.venv/bin/python scripts/acquire_goes_history.py --verify --manifest data/manifests/goes_v1_202408.json
```

## Launch the five pages

Run from the checkout root so the local Streamlit configuration is applied:

```bash
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

Open [the loopback dashboard](http://127.0.0.1:8501). Stop with Ctrl-C. The
configuration binds to loopback, disables telemetry and disables file watching;
restart after edits. No external chart assets or network connection are needed.

1. **Overview:** May–June quality-controlled irradiance and 87,840 observed
   timestamps before channel rejection.
2. **Data Explorer:** May–June flux/histograms plus separately labelled saved
   May–August descriptive statistics, paired scatter and Normal QQ plots.
3. **Time-Series Analysis:** archived rolling mean/variance, channel/transform
   controls, ACF/PACF and stationarity evidence; saved exploratory STL. A daily
   decomposition period is an assumed diagnostic, not physical solar seasonality.
4. **Model Results:** the archived V1 benchmark and a separate classical
   training demonstration with saved-parameter replay. **Run saved-model
   inference** checks its pinned forecast/metrics without fitting. Its single
   origin is separate from benchmark ARIMA/ARCH comparisons.
5. **Solar Flux Prediction:** historical August 120-minute context to 30-minute
   seed17 JEPA forecast, optional seed17 supervised comparator and masked actuals.
   All context cells must be observed, finite, positive and quality-valid.

Prediction timestamps are UTC interval starts; lead 1 starts at issue time.
The saved normalization and original spec remain unchanged. Additional minute
origins are examples outside the original 1,436-origin benchmark. August has
already been evaluated; it is not an untouched future holdout. Nominal quantile
bands are uncalibrated. Operational delivery latency and real-time suitability
remain **UNKNOWN**. Archived V2 status is historical context, not a stable feature.

## Verify behavior and original outputs

```bash
.venv/bin/python -m pytest -q tests/test_stable_baseline.py tests/test_dashboard.py tests/test_dashboard_ui.py tests/test_flux_prediction.py tests/test_flux_prediction_replay.py tests/test_flux_prediction_ui.py tests/test_time_series_presentation.py tests/test_time_series_ui.py
.venv/bin/python scripts/verify_dashboard.py
.venv/bin/python scripts/verify_presentation.py
.venv/bin/python scripts/verify_flux_prediction.py
.venv/bin/python scripts/verify_v1_reference.py
```

AppTest exercises all five routes and controls. The presentation isolation test
retains its network, training/model imports, checkpoint/NPZ and raw August access
guards, checking exactly 61 native May/June files. Its one integration exception
allows only the exact tracked August manifest metadata: the time-series identity
hashes that manifest without opening August science products. Expected legacy
page chart counts are **1 / 4 / 2 / 2**.

The release preflight and prediction replay have different purposes: hashes prove
artifact identity; replay executes unchanged checkpoint inference and compares
original numerical arrays. The full V1 reference verifier covers all nine neural
checkpoints; no retraining or new accuracy evaluation is required. The separate
presentation verifier reconciles original score records. See the release report
for actual executed counts, differences and the readiness verdict.

New artifact-dependent release tests explicitly skip on an absent original local
bundle, while missing/mismatch unit tests continue to run. Corrupt present files
fail. A skipped asset test does not satisfy release readiness: the explicit
`--references` preflight and numerical verifier must pass with originals present.

The observed environment emits the existing NumPy/netCDF binary-size warning.
Successful native/runtime checks are recorded alongside it; the warning is not
hidden. Cross-platform native concurrency and GPU behavior remain unverified.
For a visible unavailable state, restore the pinned original named by the error;
never edit a hash pin to conceal a mismatch.
