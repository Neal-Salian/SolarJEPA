# Presentation dashboard verification — 11 October 2026

**Verdict: PRESENTATION_READY**, with the explicitly omitted results listed below. This verdict is for the local presentation milestone, not for model deployment, V2 pilot authorization or scientific inferential validity.

## Audit and Git isolation

Fetched origin before work. `main` and `origin/main` matched `1a4991da4dda9676caeb1d7e35a03408528c3188`. Verified presentation `660f469683557a0f3134f72ec69b174a5bcdd917`, V1 `644648f7d555fcbcb3eed4495d37fecffdd1863a`, M4B `2e3f87111ab7c3a881064aaad9dbd6d6298c69cd`, M5 `60718686f016485cf7efadef5772b1d5813d1a43`, and restoration remote `8a9c98db66eca545eeaf062f5fb07e47ec6bdc63`. The newly discovered protocol-review remote was inspected as context, not integrated.

Used a managed isolated worktree at `/Users/nealsalian/.codex/worktrees/solarjepa-dashboard/SolarJEPA`, based on the verified presentation branch. Created and published `presentation/solarjepa-streamlit-dashboard` with upstream before implementation. No V2 research branch was merged. The original checkout, existing scientific worktrees, ignored data and pre-existing `.agents/` / `docs/P1_FINAL_INTEGRATION_REAUDIT.md` untracked items were preserved. Presentation dependencies use a separate worktree environment; the original research Pillow/packaging pins were restored after initial dependency inspection.

## Data integrity and scientific evidence

- **OBSERVED:** all 61 explicitly selected May/June native files match manifest SHA-256/byte identities, totaling 18,079,735 bytes. Native platform, instrument, product/version, units, flag schemas, timestamps and minute grid pass the existing GOES contracts.
- **OBSERVED:** 87,840 observed minute timestamps, no absent/duplicate bins; cadence 60 seconds. XRS-A valid 85,769; XRS-B valid 85,891. Quality rejection remains NaN with no interpolation. The count is timestamp records, not channel cells or events.
- **OBSERVED:** 17 dashboard source identities pass. Six underlying research-status source blobs plus 16 historical source blobs match their recorded Git commits (22 total Git-blob checks). The newly generated status snapshot is correctly distinguished from historical source files.
- **OBSERVED:** June-only replay recovered the original 10,149-bin diagnostic block `[2024-06-11T16:38Z, 2024-06-18T17:47Z)`. Stored ACF/PACF arrays and six ADF/KPSS rows reproduced exactly (maximum discrepancy 0.0). This verification used permitted June inputs, never raw August observations.
- **OBSERVED:** original rolling PNG matches its figure-manifest identity and Git blob. Its verified source code computes 360-bin trailing log mean and sample variance, not standard deviation. Original May–August support is retained and labelled.
- **OBSERVED:** historical aggregate table equals saved grouped model evidence. Each selected model/seed uses 1,436 origins, 86,160 cells, both channels and 30 leads. Neural aggregation is arithmetic mean of seed losses. The historical evidence records 422 score checks with zero discrepancy and native alignment; this milestone does not claim to have repeated those prediction-array checks.
- **INFERRED/limited:** temporal-dependence interpretations apply only to the June segment. Descriptive V1 ordering does not validate significance, general pretraining superiority or V2 accuracy.

## Offline and execution safety

`python scripts/verify_dashboard.py` passes with outbound sockets/DNS blocked, training/experiment-runner imports blocked, native files restricted to the exact May/June allowlist, and experiment-array reads rejected. The actual loader opens only those 61 files. No acquisition function, forecasting fit, model download, real prediction-array read or test-release operation was executed. Existing boundary tests may create artificial arrays in pytest temporary directories; these never enter production views.

The app imports UI/core plotting and GOES validation, not training runners. Streamlit telemetry is disabled, the server binds to loopback, file watching is disabled, charts/fonts/images are local, and no remote asset is needed for demonstration. This establishes software behavior under blocked networking; host Wi-Fi settings were not changed.

## Tests and error behavior

The new dashboard suites pass **25 tests**: 15 core/provenance tests and 10 chart/UI tests. Test cases cover registry completeness/role binding, path safety, dataset identity, filtering and unsupported intervals, channel QC/log validity, extrema/gaps, histogram counts/bins, comparable metrics/support, missing/corrupt evidence, no fallback fabrication, offline native access, no training imports/test release, four-page rendering and cached plotting reuse.

TDD failures were observed before implementation/fixes: missing core module, explicit-UTC integration mismatch, malformed contract/status attribution, original-lag mismatch, dependency/metadata substitution (five corruption regressions), and repeated envelope transformation. Targeted fixes turned these green. Independent reviewers reproduced and approved the registry and cache fixes.

The final relevant regression command is:

```bash
.venv/bin/python -m pytest tests/test_dashboard.py tests/test_dashboard_ui.py tests/test_goes.py tests/test_goes_acquisition.py tests/test_eda.py tests/test_metadata.py tests/test_storage.py tests/test_presentation.py tests/test_v1_foundation.py -q
```

Final regression result: **145 passed, 1 existing warning, 269.92 seconds**. This combines the 25 dashboard tests with 120 relevant existing tests. The storage/CLI regression run was much slower than the dashboard-only suite; it does not represent app interaction latency.

The full model-training suite is intentionally not run. Normal installed imports with Python `-I`, `pip check`, standalone verifier and `git diff --check` pass. One existing NumPy/netCDF binary-size warning appears once during native backend import; native verification and tests succeed. AppTest bare-runtime notices are test-harness notices, not dashboard errors.

## UI inspection

Inspected all four pages in the in-app browser at 1366×900 and Overview at 390×844. Confirmed readable labels/units, distinct channel legends, no overlapping elements, aligned spacing, no document horizontal overflow, quality gaps, visible rare peaks, exact archived interval captions, usable provenance expanders and no empty chart presented as a result. The narrow viewport collapses navigation and stacks the three summary metrics; the flux chart and captions remain readable. Wide stationarity tables support horizontal scrolling.

AppTest separately renders all four pages under blocked sockets. It verifies expected chart counts (1/2/1/1), no application exceptions, and explicit unavailable behavior with no fabricated chart/metric when required evidence is absent. The ACF/PACF display preserves original positive lags (1–120 / 1–60), and histogram hover shows its actual bin edges. The original rolling image retains its light archived style and fullscreen control.

## Performance

Measurements are local Python 3.13.3/macOS arm64 observations, not promises for every machine. Machine-readable results are in `docs/presentation/dashboard_verification.json` and `dashboard_ui_performance.json`.

- Streamlit HTTP health startup: 0.535 seconds; HTTP 200; server RSS at health 73.9 MiB.
- First Overview execution observed at 3.114 seconds initially, and 6.416 seconds while a broader test suite was concurrently active. Cached page switches remained below 0.5 seconds in both runs.
- UI test-process peak RSS: 227.2–247.8 MiB across measured runs. This includes Python/Streamlit/scientific dependencies, not the separate browser process.
- Standalone safe verifier: approximately 2–3 seconds and 155–165 MiB peak RSS across observed runs; the bounded frame occupies 4.28 MiB.
- XRS-A renders 2,252 points (143 gap markers); XRS-B 2,188 (125), each below the 2,400 budget. Global maxima are unchanged. All histogram counts equal their channel's valid-observation count.
- Verified observation loading, summaries, histogram and flux-envelope chart transformations are cached with bounded entries; native file stats and pinned manifest/code identities are checked before cache access. A cache regression proves reruns do not recompute the envelope.

The actual demonstration host's complete 8-GB memory pressure and a 5–7 minute audience rehearsal were not measured. The observed application footprint is comfortably below that budget; browser resource consumption remains a separate factor.

## Missing/omitted results and readiness limits

- Original rolling standard-deviation output: unavailable. The exact archived **mean/variance** plot is displayed with correct units and a clear limitation.
- Observed-versus-predicted graph: omitted, because timestamp-matched prediction arrays are outside this milestone's permitted access. No prediction reconstruction occurs.
- V2 real-data accuracy, inference/significance, SoLEXS calibrated scientific integration: unavailable/pending, stated explicitly.
- Interactive scope is fixed May–June training observations. No unrestricted date browser or unauthorized periods are offered. Standalone filtering contracts reject unsupported ranges.
- No raw data, large arrays, checkpoints or generated science payloads are committed. Actual native paths, environment and scratch logs pass ignore checks; historical original source/evidence files remain unchanged.

The ready experience deliberately uses fewer verified results. Publication is only to the dedicated presentation branch, with no PR, protected-branch update or integration implied.
