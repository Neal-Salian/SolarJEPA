# Solar Flux Prediction

The fifth dashboard page performs bounded retrospective inference with the
frozen V1 `jepa_finetune_seed17.pt` checkpoint. The existing four pages retain
their May–June observation and archived aggregate access paths.

Run from a repository checkout with the approved local scientific inputs:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dashboard-prediction-lock.txt
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m streamlit run streamlit_app.py
```

The extension lock records the tested CPython 3.13/macOS arm64 environment. Torch
wheels and additional accelerator dependencies vary by platform; this is not a
cross-platform hash lock. `requirements-dashboard-prediction.txt` is the smaller
explicit runtime request; `dashboard-prediction` is also a package extra. The
original dashboard requirements and lock remain unchanged. Tests of the whole
research repository additionally require its existing optional science/test
packages; the prediction page itself uses GOES, not SoLEXS.

Select **Solar Flux Prediction** and choose a whole UTC minute in August 2024.
The complete preceding 120 minutes and next 30 minutes must lie within
`[2024-08-01T00:00Z, 2024-09-01T00:00Z)`. Thus the earliest permitted issue is
01 August 02:00 UTC and the latest is 31 August 23:30 UTC. Every context cell
must be observed, positive, finite and native-quality-valid in both channels.
An ineligible context produces an unavailable state, without a forecast or
filled observations. The default is the first saved benchmark origin,
01 August 02:00 UTC, chosen independently of performance.

The graph shows the 120 context bins and 30 JEPA forecast bins for XRS-A
(0.05–0.4 nm) and XRS-B (0.1–0.8 nm). Both axes use physical irradiance W/m²,
with logarithmic flux axes. Time coordinates are UTC **interval starts**. The
first forecast bin starts at issue time; lead 1 ends at issue + 1 minute.
Vertical lines mark context start, issue and forecast end. Hover and zoom retain
all 150 minute coordinates; no averaging or time shift is applied.

Bands are nominal central 50% (q25–q75) and 90% (q05–q95) model quantiles. They
are uncalibrated: those numbers do not assert empirical coverage. The point
forecast is the inverse-transformed q50 median. The optional supervised seed 17
comparator receives the identical context and future grid; its median is drawn
with a dashed line. These are fixed-seed examples, neither seed ensembles nor
best-seed selections.

Quality-valid actual future observations may be hidden with a checkbox. Missing,
rejected, nonfinite and nonpositive future cells remain gaps and never enter
the model. The count table distinguishes valid and masked bins per channel and
support; missing bins are a subset of masked bins. The native policy requires
status flag zero, allowed channel-specific electron-correction bits, native
valid flux bounds and sample counts 1–60. No interpolation or imputation occurs.

The saved normalization uses unique raw training support only: log₁₀(flux /
[1 W/m²]), followed by saved means/scales. August is not used to fit new
statistics, select checkpoints or evaluate new metrics. August is the historical V1 test partition and has already been evaluated; it
is not an untouched holdout for future evaluation. The original forecast
specification, including stride 30 and its fingerprint, is unchanged. Additional
minute origins are retrospective inference examples outside the original
1,436-origin benchmark cohort; archived benchmark metrics are not extended.

The provenance expander exposes source/checkpoint hashes, V1 executed commit,
normalization/spec fingerprints and the fixed seed. Parent dataset identity
refers to the full frozen V1 lineage; the page opens only its pinned August
partition. The separate prediction registry is itself hash-pinned. Missing or
changed native files, checkpoints, configuration or inference code fail closed.
Native reads across dashboard reruns/sessions are serialized for the complete
NetCDF open/read/close lifetime; an overlapping request may wait. The page
rechecks identities on each run and does not read saved prediction
arrays or invoke acquisition, experiment execution, fitting or training.

Scientific status is bounded:

- **OBSERVED:** local manifest/checkpoint/code byte identities, QC masks and
  replay checks are directly verified by the implementation and verifier.
- **DOCUMENTED:** the existing native GOES adapter preserves record-start UTC
  intervals and product quality metadata. Original acquisition provenance and
  native data definitions remain in the existing manifests and foundation docs.
- **INFERRED:** bin-end is the earliest retrospective availability boundary.
  It does not establish when a historical operational user received a record.
- **UNKNOWN:** actual operational delivery latency, real-time suitability,
  calibrated interval coverage and forecast skill beyond existing archived
  evidence. The page asserts no flare events, model superiority or new accuracy.

Local source archives/products remain immutable and ignored by Git. Restore the
approved files through the repository's existing storage workflow; the page
never downloads them. New storage/acquisition, retraining, V2, G4, operational
inference and new evaluation are outside this feature.

For an independent replay, run explicitly:

```bash
.venv/bin/python scripts/verify_flux_prediction.py --root /path/to/SolarJEPA
.venv/bin/python scripts/verify_flux_prediction.py --issue-utc 2024-08-01T02:30Z
```

This verifier alone opens the pinned saved archive and summary. It checks raw
context and mask exactly before comparing both seed 17 model points/quantiles.
Only exact saved benchmark origins are accepted; an additional minute origin is
rejected without selecting a neighbor. Network calls are blocked. The CLI emits
JSON and returns nonzero on failure; it does not recompute evaluation metrics.
The default single-origin comparison uses `rtol=1e-6`, `atol=1e-15 W/m²` because
float32 numerical results vary slightly with the original batch shape. See the
[verification record](SOLAR_FLUX_PREDICTION_VERIFICATION.md).
