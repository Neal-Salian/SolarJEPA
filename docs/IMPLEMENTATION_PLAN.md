# Solar forecasting implementation plan

**Goal:** establish auditable data feasibility, then progress to controlled
forecasting experiments only after the user approves the research design.
**Architecture:** separate acquisition, source-specific inspection/decoding,
causal preparation, frozen window manifests, and later model/evaluation APIs.
**Stack:** Python 3.11+, NumPy/pandas/xarray/NetCDF4/Parquet/matplotlib;
Astropy/CDF inspection optional; no torch or LLM weights in the foundation.
**Spec:** [RESEARCH_PLAN.md](RESEARCH_PLAN.md) and [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md).
**Execution:** foundation in this session; later phases await explicit approval.

## Global constraints and review focus

- No random time splits, future-fill, guessed instrument epochs or raw-data Git.
- NOAA reference validation cannot be labeled Aditya validation.
- Every downloader has finite byte limits and immutable source hashes.
- Missing/bad/saturated flux is unknown, not zero or a negative flare label.
- No model training or large acquisition in this phase.
- Review truncated downloads, changed cached files, reordered/duplicate times,
  missing quality fields, and derivatives across gaps; tests pin these cases.

## Phase 0 — today's foundation

### Task 1: repository and research evidence

Files: README, LICENSE, .gitignore, pyproject, the seven requested docs, and
this plan. Check source links, scope and assumptions. Initialize local main
branch; no remote. Commit `chore: initialize research repository`, followed by
`docs: add research and experiment plan`.

### Task 2: bounded public acquisition

Files: `src/solar_flare_jepa/data/download.py`, `scripts/download_data.py`,
`configs/data/noaa_sample.json`, `tests/test_download.py`.
Interface: `download_manifest(manifest_path: Path, root: Path) -> list[dict]`.
Consume explicit public NOAA URLs, destination relative paths, byte limits and
optional initial/pinned hashes; produce verified files plus provenance JSON.

- [ ] Write tests for HTTPS/host/path rejection, byte cap/truncation, NetCDF
  magic, hash mismatch and cache corruption using fake network streams only.
- [ ] Run and observe missing implementation failures.
- [ ] Implement atomic bounded streams, no authenticated endpoints/redirects.
- [ ] Run tests; fetch six daily reference files; pin measured hashes/sizes.
- [ ] Commit `feat(data): add bounded public reference acquisition`.

### Task 3: metadata and reference EDA

Files: `data/inspect.py`, `data/goes.py`, `data/eda.py` in the package,
`scripts/inspect_data.py`, `scripts/preprocess.py`, `scripts/eda.py`,
`configs/data/noaa_eda.json`, `tests/test_goes.py`.
Interfaces: `inspect_file(path: Path) -> dict` (schema only);
`read_goes(paths: list[Path]) -> pandas.DataFrame` (UTC indexed reference
samples with raw values, masks, flags and source); `summarize(frame) -> dict`.

- [ ] Test CF timestamps/interval metadata, required units/quality, valid masking,
  unordered/duplicate times, positivity and gap-aware backward derivatives.
- [ ] Observe failures, implement only these source-specific behaviors.
- [ ] Inspect real sample before choosing metadata/quality mappings; retain flags.
- [ ] Produce Parquet and sidecar, JSON diagnostics and PNG flux/log/derivative/
  cadence/event plots. No Aditya channel mapping without actual data.
- [ ] Report measured rows/bytes/coverage/gaps/event records and limitations.
- [ ] Run full tests and real-data smoke; check Git ignores and commit small units.

STOP after Phase 0. The following are designs, not authorized implementation.

## Phase 1 — Aditya access and calibration validation

Acquire one matched interval and official manuals using DATA_DOWNLOAD.md.
New adapters `data/solexs.py` and `data/aspex.py` return a common long-form schema:
`time_start_utc,time_end_utc,instrument,detector,channel,value,unit,valid,quality,
exposure,calibration_id,source_sha256`. Retain original clock metadata.

Before code: fixtures derived from permitted real-file metadata; tests for
documented clock conversion, masks/fill values, detector changes, response units,
dead time and bad channels. Compare extracted calibrated lightcurve against an
official quicklook and spot-check counts/exposure. A generic FITS inventory is
not this adapter. Gate: reviewer accepts physics/time correctness and provenance.

## Phase 2 — causal data and fixed benchmark

Files planned: `features/causal.py`, `data/windows.py`, `data/splits.py`,
`data/labels.py`; versioned configs and split/window manifests.
Interfaces: each window stores origin, support interval, source hashes,
history/target masks, event IDs and label-availability time. Partition builder
accepts explicit UTC boundaries and returns immutable IDs, never random splits.

Tests: no overlap of support/event groups across partitions; perturb future
values and confirm all earlier features unchanged; never fit scaler on tuning;
backward joins cannot use later bins; target gaps remain unknown; future peak
labels mature correctly; mismatched calibration versions rejected. Freeze exact
periods and event-count precision analysis before model work. Gate: common-origin
baseline dataset and reproducible byte-identical window manifests.

## Phase 3 — baseline/evaluation harness

Add `models/statistical/`, `models/deep_learning/`, `training/`, `evaluation/`,
`scripts/train.py`, `scripts/evaluate.py` only here. Model contract:
`predict(history, mask, horizon) -> Forecast` containing timestamps, units,
quantiles or joint samples and optional nested risk probabilities.

Implement persistence/ridge first, then AR/ARIMA/ARCH/GARCH and LSTM/TCN/
supervised Transformer. Hand-computed metric tests, zero-event denominator
tests, transform inversion checks, fixed-seed reproducibility and forecast
origin alignment. Profiles precede full runs. Save resolved configs, environment,
Git revision/dirty diff, manifests, seeds/RNG states, checkpoints and per-origin
predictions/losses. Gate: baseline skill/variance diagnostics and runtime audit.

## Phase 4 — plain JEPA and controlled SSL

Add `models/jepa/encoder.py`, `predictor.py`, `heads.py`, `training/pretrain.py`.
Test stop-gradient on target, correct EMA update, absence of target inputs at
inference, full train-only window support, output shapes/quantile order and
collapse diagnostics. Use approved small 200-step profile then Stage B/C from
experiment plan. Compare equal-backbone supervised/reconstruction controls.
Gate: repeated baseline comparison and training/uncertainty stability.

## Phase 5 — defensible additions

Add measurement response module only after Phase 1 review. Hand-calculate folded
counts for a documented response fixture; check units/exposure/energy-bin widths,
nonnegative spectra and likelihood applicability. Add multiresolution with
future-perturbation and equal-context tests. Run factorial and conventional
physical control. Fusion requires matched-origin audit and causal arrival-time
features. No speculative MHD losses. Gate: physical residual and ablation evidence.

## Phase 6 — optional LLM and paper artifacts

Add isolated `models/llm/` dependencies after runtime approval. Test serialization
round trips, malformed outputs, tokenizer lengths and no label text leakage.
Pin checkpoint/tokenizer revision; record invalid output rates and sample costs.
Generate paper tables directly from immutable metrics, block CIs and manifests;
verify every claim against measured output. Publish code/data instructions subject
to source terms. No result or superiority text until those experiments exist.
