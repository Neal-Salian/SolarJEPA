# SolarJEPA presentation dashboard implementation plan

**Goal:** Deliver the user's four-page offline research dashboard without new experiments or restricted-data access.

**Architecture:** A thin Streamlit entry point uses reusable, UI-independent loaders and Plotly builders. A tracked JSON registry pins source hashes, commits, dataset scopes and scientific contracts. Missing or mismatched evidence fails closed.

**Spec:** The user's presentation milestone brief. This plan implements its supplied design and authorization directly; no additional research or integration milestone is authorized.

**Tech stack:** Python, existing GOES adapters, Streamlit 1.50.0, Plotly 6.3.1.

## Constraints and decisions

- Base: verified presentation/eda-model-comparison at 660f469; preserve the V1 loader and assets, merge no V2 branches.
- Work only in the managed dashboard worktree on presentation/solarjepa-streamlit-dashboard, already published with upstream.
- Interactive scope: May and June 2024, both within V1 training. Open only the two pinned manifests and their explicit files. Never load August raw observations, predictions, experiment runners, fitting, or acquisition functions.
- Published V1 aggregate scores are historical evidence; compare five unambiguous model families on the identical archived support. Recheck aggregate consistency without opening prediction arrays.
- Archived rolling plot is mean and sample variance, not standard deviation. Preserve original interval and label the limitation. Reuse exact June ACF/PACF and stationarity evidence; do not recompute different diagnostics.
- Downsample lines with original extrema and explicit gap separators, never means; histograms use every valid selected observation and 70 equal-width log10 bins per channel, labelled display-only.
- All numerical evidence must have pinned identity and transformation metadata. Test fixtures are confined to tests.

## Review focus

Missing/corrupt sources; path traversal and unsupported periods; gap and peak preservation; incompatible aggregate support; offline operation without training or sealed-test reads.

## Tasks

1. **Audit and provenance core** — write failing tests in tests/test_dashboard.py; implement src/solar_flare_jepa/dashboard/data.py and registry.json; verify native May–June identities, filtering/QC, artifact hashes and score contracts. Run targeted tests to green.
2. **Presentation layer** — implement src/solar_flare_jepa/dashboard/charts.py, streamlit_app.py and .streamlit/config.toml; use pure core functions, bounded charts, cached loading, four pages and concise provenance captions. Add Streamlit AppTest coverage and startup smoke test.
3. **Verification and handoff** — verify diagnostic arithmetic only on permitted June observations, run relevant existing/new tests, inspect all pages in browser, measure startup/RSS and offline behavior. Independently review and fix confirmed issues. Write the four requested guides/reports with observed evidence. Inspect ignore/index/history/diff, commit and push only the dedicated branch; no PR.

## Execution record

- Baseline: 34 relevant existing tests passed (presentation, GOES adapter, V1 foundation); one existing NumPy/netCDF warning.
- Native worktree preserves original ignored data and two pre-existing untracked items. Only May/June inputs will be copied into ignored worktree storage.

- Core/UI implementation complete:25 dashboard tests; final relevant regression145 passed,1 existing NumPy/netCDF warning.
- Independent scientific/architecture/final reviews completed; status provenance, registry dependency binding, positive lag support and plotting cache regressions fixed and approved.
- Browser inspection:all4 pages desktop1366×900; Overview responsive390×844; no overlap or document overflow.
- Verifier offline/native allowlist passes;17source identities and22historical/audit blob checks verified; protected refs and historical evidence unchanged.
- Four delivery documents and machine-readable measurements complete. Publication is only to the dedicated presentation branch; no PR or merge.
