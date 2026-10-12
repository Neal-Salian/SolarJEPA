# Time-series presentation completion plan

> Execute with Superpowers executing-plans, targeted TDD and independent final review. User mission supplies scope and explicitly authorizes execution without further ordinary-change approval.

**Goal:** Demonstrate the 11 professor requirements honestly through the existing four-page Streamlit application.
**Architecture:** Preserve archived V1 assets and four-page navigation. Add UI-independent presentation diagnostics, a bounded classical fitting/replay module, and a small hash-bound evidence bundle. No research architecture changes, new scientific acquisition, neural training, main changes, or PR.
**Base:** d718177 (dashboard), descendant of EDA 660f469; new branch presentation/time-series-requirements-completion. Original checkout's untracked .agents/ and P1 reaudit preserved.
**Environment:** Existing dashboard Python 3.13 / statsmodels 0.14.6 for new demonstration; original V1 0.14.5 results retain their original identities.

## Audit and decisions

- [x] Inspect branch/upstream/main/remote state and preserve untracked work.
- [x] Create managed isolated worktree and publish requested branch before implementation.
- [x] Dispatch independent dataset, methods and UI audits; primary audits leakage/reproducibility.
- [x] Verify all 123 May–August files via explicit manifests; no extra data download.
- [x] Record initial/final requirement states in checklist with exact source/tests/artifacts.

## Task 1: Scientific evidence and classical demo

Files: new presentation/time_series.py, presentation/classical.py, scripts/build_time_series_presentation.py, tests/test_time_series_presentation.py; new docs/presentation/time_series_evidence.json plus identity sidecar.

- [x] First write and run failing tests for channel-mask pairing, raw/log statistics and QQ, contiguous STL reconstruction, fit-only support/IC identity, causal saved-parameter inference and timestamps.
- [x] Reuse load_v1_frame, longest_complete_block, stationarity_analysis/dependence_analysis and existing statistical.ARIMA adapter.
- [x] Full-scope EDA uses joint valid pairs for scatter, per-channel QC for QQ/stats; deterministic display thinning and explicit counts.
- [x] Robust STL on full contiguous June training segment with period=1440 as a prespecified daily-cycle diagnostic, not evidence of physical seasonality. Preserve all native timestamps; display bounded points with exact method metadata.
- [x] Fit seven small candidate orders (AR1/2, MA1/2, ARMA11, ARIMA110/210) to identical first2880 training minutes. AIC/BIC compared only within d/trend/burn groups. Record convergence/warnings and n/k/llf. No seasonal candidate without defensible seasonal evidence.
- [x] Select converged d=1 model per channel by training BIC before any August targets; forecast earliest eligible August origin from 120 past bins for 30 target bins. Explicitly separate this small demo from V1 benchmark.
- [x] Serialize finite JSON parameters and context/targets. Replay inference without fitting, validate schema, units, positive finite values, ordered contiguous UTC minute timestamps, issue-time and channel identity; metrics match saved overlay.
- [x] Bind sources/code/config/manifests/environment/output identities, refuse stale/tampered bundle. Preserve existing EDA and model evidence byte-for-byte.

## Task 2: Thin dashboard extension

Files: streamlit_app.py, new dashboard/time_series.py, new tests/test_time_series_ui.py, adjust existing UI regression counts only where intentionally changed.

- [x] Keep Overview/native May–June overview intact and distinguish full May–August new report scope.
- [x] Data Explorer: paired log scatter, Normal QQ diagnostics, full raw/log summary including missing/rejected counts.
- [x] Time-Series Analysis: clarify nulls, local transformations, ACF/PACF meanings/order notation; new four-component exploratory STL + explicit limitations.
- [x] Model Results: comparable-group AIC/BIC table separate from forecast errors and archived V1; actual saved-parameter inference with timestamp overlay/metrics; no fitting while rendering.
- [x] Test all four pages, chart contents, failure behavior and no fitting; run local Streamlit and inspect browser if available.

## Task 3: Verification and guide

Files: docs/PRESENTATION_TIME_SERIES_CHECKLIST.md, docs/PRESENTATION_TIME_SERIES_GUIDE.md, docs/PRESENTATION_TIME_SERIES_VERIFICATION.md.

- [x] Recompute statistical outputs/artifact replay; targeted + relevant full regression tests, normal installation/import + CLI smoke, diff/check/status/prohibited-data/index/history checks.
- [x] Independent scientific/code review; fix material findings with regression tests.
- [x] Guide: all11 sections with actual observations, interpretation, viva answers, precise setup/rebuild/run commands; distinguish DOCUMENTED/OBSERVED/INFERRED/UNKNOWN.
- [x] Focused Conventional Commits, push only new branch, verify ls-remote/upstream/local identity and unchanged protected refs. No PR/merge.

## Review focus

Mask mismatch; gaps/duplicate/naive timestamps; target-influenced fit/order choice; IC ranking across incompatible likelihoods; stale artifacts or unfitted inference; accidental archived experiment overwrite.

## Execution evidence

Baseline presentation/dashboard selection: 35 passed. Existing scientific/forecasting selection: 144 passed. Final full suite: 1,259 passed, zero failures and zero skips.

Original V1 replay passed 52 identities, 12 independently reconstructed stationarity statistics, 422 score checks and exact native alignment. Independent review regenerated every new scientific output exactly.

The timestamp helper finding was reproduced by two failing tests and fixed; both passed afterwards. Rebuilt scientific payload identity was unchanged. No code findings remain deferred.

SARIMA fitting is intentionally omitted because stable seasonality is unestablished; checklist requirement 8 remains PARTIAL. Browser visual inspection was unavailable because IAB/native permission was unavailable; AppTest rendered all four pages and actual inference passed. See the final verification report for commands and environment boundaries.

Implementation committed and pushed as `5618bc4042d4a88b019504768772880cc15d2fcd`. Documentation is published in a separate focused commit; final local/remote identity is checked after that push and reported to the user. Main, prior presentation branches and research branches are preserved.
