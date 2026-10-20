# SolarJEPA presentation dashboard guide

This milestone presents pinned observations and archived evidence. It performs no model training, prediction generation, data acquisition or V2 test release. All pages work locally after installation and placement of the two permitted native data selections.

## Install once, before going offline

Use Python 3.13 on Apple Silicon (verified: 3.13.3). From the dashboard checkout:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dashboard-lock.txt
.venv/bin/python -m pip install --no-deps -e .
```

The dashboard environment is separate from the research environment: the historical research lock pins Pillow/packaging versions incompatible with the selected Streamlit release. Do not combine the two lock files. The dashboard lock includes verification dependencies but no PyTorch/model runtime. Dependencies require network only during installation; the app never installs or downloads anything.

## Launch

Run from the dashboard checkout so Streamlit loads its local theme and telemetry settings:

```bash
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

For the managed checkout created for this milestone, the exact command is:

```bash
cd /Users/nealsalian/.codex/worktrees/solarjepa-dashboard/SolarJEPA
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

Open `http://127.0.0.1:8501`. The server binds only to loopback. Stop with Ctrl-C. File watching is disabled for presentation reliability; restart after changing application code or registry schema.

## Required local files

The checkout supplies all small manifests, evidence tables, diagnostic arrays, registry and archived rolling image. Native scientific data remain ignored and are not in Git.

- `data/manifests/goes_v1_202405.json`: dataset `v1-goes16-202405-science-avg1m-v2-2-1`, 31 files, 9,169,020 bytes.
- `data/manifests/goes_v1_202406.json`: dataset `v1-goes16-202406-science-avg1m-v2-2-1`, 30 files, 8,910,715 bytes.
- Place the unchanged files at the exact manifest-relative paths beneath `data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/05/` and `2024/06/`. This checkout already has verified local copies.
- `docs/presentation/eda_evidence.json`, `model_evidence.json`, `model_metrics.csv`, `verification.json`, `dashboard_status.json`.
- `docs/figures/presentation/eda_rolling_statistics.png` and the pinned source/configuration files named by `src/solar_flare_jepa/dashboard/registry.json`.

Total native inputs: 61 files / 18,079,735 bytes. Never replace missing observations with fixtures. No July/August files, checkpoints, prediction arrays, experiment output directories or V2 release artifacts are needed. Relocate the whole checkout and copy only these manifest-selected native inputs into its ignored storage; no machine-specific scientific paths are encoded.

## Pages

1. **Overview:** GOES-16, 87,840 observed minute records, 60-second cadence, two-channel log-axis irradiance and research pipeline. The observation count counts timestamps before channel rejection, not two-channel cells.
2. **Data Explorer:** May–June channel comparison and display-only log10 distribution. Every valid value is counted in 70 equal-width bins per channel; no rebinning from downsampled chart values.
3. **Time-Series Analysis:** original May–August rolling mean/variance image; original June contiguous-block ACF/PACF and ADF/KPSS evidence. Select channel and transformation for correlation plots. The original standard-deviation artifact is unavailable and is not invented.
4. **Model Results:** five historical V1 log-MAE comparisons on identical support, exact-value table, and source-audited research status. No significance claim, V2 score or reconstructed prediction is shown.

Each visualization has a source/provenance expander. The registry documents scope, units, transformations, quality policy, experiment and source commits. Archived diagnostics and model evaluation intentionally have different, explicitly labelled intervals from the interactive data scope.

## Offline rehearsal

1. Install dependencies and confirm the 61 files are present while still online.
2. Run `.venv/bin/python scripts/verify_dashboard.py` from the checkout. It blocks outbound sockets and disallows native files outside the May/June allowlist.
3. Start the server, then disconnect networking and click all four pages. All charts, scripts, fonts and the rolling image are local. No remote chart assets are needed.
4. Leave the browser at Overview, collapse provenance expanders and use a desktop-width window. Rehearse the accompanying 5–7 minute script.

Observation loading is cached with source identity/stat invalidation, maximum two entries. Flux lines retain at most 2,400 original values per channel, preserving bucket extrema and every missing-run break rather than averaging rare peaks. Histograms count all valid selected observations. No full dataset processing occurs on every sidebar interaction.

## Troubleshooting and limits

- **Verified result unavailable:** the evidence is missing or fails identity/contract validation. Read the caption and verifier output. Restore exact local files; do not edit hash pins to conceal a mismatch. Other pages with independent evidence can still work.
- **Missing native observations:** place the 61 unchanged local files using manifest paths. There is no automatic NOAA retrieval.
- **Port in use:** stop the earlier dashboard, or pass `--server.port 8502` and use that loopback URL.
- **Old code after editing:** stop/restart the server; its file watcher is intentionally disabled.
- **Different current directory:** change to the checkout before launch to load `.streamlit/config.toml`.
- **Small screen:** Streamlit collapses its sidebar; open navigation with the upper-left control. Wide stationarity tables scroll horizontally. For projection prefer desktop width; use the image fullscreen control when discussing rolling diagnostics.
- An existing NumPy/netCDF binary-size warning is emitted once in the verified Python environment; native loading and relevant tests pass. It is not presented as scientific evidence.
- The original rolling figure preserves its light plotting style and variance units. No original rolling standard-deviation record or timestamp-matched prediction view is available within this milestone's permitted access.
- Model results are a retrospective V1 benchmark. Their small differences do not establish general pretraining superiority or validated inference. The Research status list is the pinned 11 October snapshot (it still lists the pilot as unauthorized). A dated 20 October update line beneath it, verified against `docs/evidence/phase2_v2_m4_pilot_results_20261019.json`, records that the V2 two-seed development pilot completed on 19 October (descriptive only); the dashboard shows no V2 scores. SoLEXS scientific integration remains pending.
