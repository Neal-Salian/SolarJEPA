# Time-series presentation verification — 12 October 2026

Conservative verdict: **PARTIALLY_READY** for a literal requirement to fit every
listed family; ten requirements are complete and requirement 8 documents the
scientifically justified SARIMA deferral. All applicable nonseasonal
demonstrations are implemented and verified.

Scope: presentation/time-series-requirements-completion, based on dashboard
checkpoint d718177 (which already contains EDA checkpoint 660f469). No research
branch was integrated or modified. This report supplements historical evidence.

## Scientific inputs and preservation

**OBSERVED:** all four explicit V1 GOES manifests hash/size/native-validated:
123 files, 36,535,474 bytes, 177,120 consecutive minute bins on
[2024-05-01,2024-09-01) UTC, zero absent/duplicate timestamps. XRS-A has
172,646 valid / 4,474 rejected bins; B has 174,845 / 2,275. No values were
imputed and original source files were not modified. Sources were copied
locally into this isolated worktree; there was no scientific-data download.

The earliest longest jointly valid training run contains 10,149 minutes on
[2024-06-11 16:38,2024-06-18 17:47) UTC. Existing ADF/KPSS and ACF/PACF evidence
was reused and independently checked. New STL uses an explicitly assumed daily
period, not a detected physical cycle. Its reconstruction error is
8.881784197001252e-16 dex. Full-sample statistics, QQ and paired scatter enforce
per-channel/joint masks explicitly; absent bins and QC rejects are distinguished.

Independent review regenerated EDA, STL, all classical fits and deployment
in memory from the native files: every output exactly matched the saved payload.

The original checkout's `scripts/verify_presentation.py` was run read-only:
**PASS**, 52 source/artifact identities, 123 native files, 12 independently
reconstructed ADF/KPSS statistics (maximum discrepancy 2.2815527245256817e-11),
422 score checks (maximum discrepancy 0), exact native context/target alignment,
and eight saved executed notebook cells without errors. This validates saved
notebook outputs; it does not claim a fresh notebook execution or neural refit.
Original V1 summary, per-origin record and prediction-array hashes match their
published identities. All nine original checkpoint files remain in the original
ignored experiment directory; no task command wrote to them.

## Classical calculation and leakage checks

Seven prespecified candidates per channel use exactly the first 2,880 minutes
of the complete June training run. All 14 fits converged. The existing ARIMA
adapter supplies fitting and fixed-parameter state filtering; no duplicate
scientific model implementation was introduced. Refiltering training observations
reproduced the adapter's likelihood and AIC before BIC was recorded.

IC groups hold channel, log transformation, support, differencing, deterministic
terms and likelihood burn fixed. d=0 groups have a constant, burn 0 and n=2,880;
d=1 groups have no trend, burn 1 and effective n=2,879. Criteria are never ranked
across those groups. Training BIC selects A order(1,1,0), B order(2,1,0).
Selection is frozen before held-out timestamps, masks or targets are accessed.
Tests change held-out targets and unused training-tail observations and confirm
that fitting/selection do not change. Explicit optional QC masks are enforced
when finite values are supplied alongside false masks.

The first eligible August complete-case window issues at 2024-08-01 02:00 UTC,
using context-bin starts 00:00–01:59 and target-bin starts 02:00–02:29. `infer`
accepts only past context and saved parameters. It validates channel identities,
units/transform, positive finite input, exact length, UTC minute cadence,
ordering/uniqueness, issue boundary, parameter schema/names/variance and training
end. Future targets are used only after inference for alignment and errors.
Fresh replay reproduces all 30×2 native predictions and metrics:

| Channel | Model | AIC | BIC | Single-origin log MAE (dex) | Log RMSE (dex) |
|---|---|---:|---:|---:|---:|
| XRS-A | ARIMA(1,1,0) | -12311.066341416 | -12299.135944835 | 0.218835296 | 0.256635485 |
| XRS-B | ARIMA(2,1,0) | -20686.727780484 | -20668.832185612 | 0.094347424 | 0.109055349 |

This is a separate bounded demonstration, not the archived V1 comparison or an
estimate of general forecast skill. SARIMA has no fit/score because a defensible
stable seasonal period is not established. The checklist conservatively keeps
requirement 8 PARTIAL for a literal five-family fitting rubric.

## Executed verification

- Baseline presentation/dashboard tests: 35 passed.
- Existing GOES/EDA/presentation/statistical/forecast-contract/split/window
  regression selection: 144 passed.
- Independent new scientific/classical/UI plus existing dashboard UI selection:
  59 passed before the final timestamp-regression additions.
- Final dashboard/data/UI selection: 34 passed, including four pages,
  channel/transform switching, failed-fit visibility, replay failures, network
  denial and denial of SARIMAX/ARIMA fitting during page render and inference.
- Timestamp-review correction: two reproductions failed first, then the targeted
  tests passed. UTC microsecond-storage indexes are normalized to nanoseconds;
  nonzero timezone offsets are refused. Scientific payload SHA-256 remained
  unchanged after rebuilding, proving the actual native calculations unchanged.
- Normal wheel installation/import and saved-parameter inference succeeded from
  `/tmp`, without injecting the repository's `src` directory.
- Offline original dashboard verifier: PASS; 61 May–June files, 87,840 rows,
  all expected native/metric identities, extrema/gaps and histogram totals;
  socket access/training imports/experiment-array access blocked.
- Streamlit server HTTP health and application shell: both HTTP 200 at
  http://127.0.0.1:8512. AppTest renders chart counts 1/4/2/2 on Overview,
  Data Explorer, Time-Series Analysis and Model Results with no errors or
  exceptions. Clicking the real saved-model action verifies forecasts/metrics.
- Browser visual QA unavailable: IAB creation returned unavailable; native
  Brave control returned computer-use permission denied. No fresh browser
  screenshots or visual-layout acceptance are claimed. Plotly figures serialize
  successfully with exact saved arrays and bounded display sizes.

The first broad run in the pre-existing research environment reported
1,237 passed / 1 failed: a clean subprocess imported an older normally-installed
package missing the dashboard module. The first attempt to collect UI tests
there also lacked Streamlit AppTest; the separate dashboard environment lacks
optional Astropy. These are environment boundaries, not waived tests.
A new ignored worktree-local verification environment was created, using
existing installed dependency directories and a fresh normal installation of
this branch. It provides Python 3.13.3, Streamlit 1.50.0, statsmodels 0.14.6,
PyTorch 2.6.0 and Astropy 8.0.1; no existing environment was altered. The guide
uses the pinned standalone dashboard lock for presentation setup.

A native NumPy/netCDF import emits an existing binary-size RuntimeWarning.
Native verification, numeric replay and regression results are reported
explicitly; the warning is not suppressed or treated as data evidence.

Final complete regression command in the isolated normally-installed environment:

```bash
.venv/bin/python -m pytest -q
```

**1,259 passed, 0 failed, 0 skipped in 104.31 seconds**, with the one existing
NumPy/netCDF RuntimeWarning. This supersedes the stale-install failure above;
no source/test waiver was used.

## Review, storage and Git boundaries

Three agents audited data, methods and dashboard independently; the primary
agent reviewed leakage/reproducibility. A fresh independent final reviewer found
no Critical/Important scientific issues. The raw/unlogged wording ambiguity and
timestamp helper issue were corrected. Prospective skill, physical seasonality,
professor rubric acceptance and unavailable browser visual QA remain unjudged.

Tracked compact report and sidecar bind source/config/manifests and the ignored
539,787-byte scientific payload. Payload arrays, local raw files, installed
runtime and caches pass actual `git check-ignore -v`. No raw science files,
context/target arrays, checkpoints or ignored outputs are staged. Existing
scientific/model modules, configurations, manifests, archived EDA/model evidence
and original figures are unchanged from d718177. Source paths are relative and
rebuild accepts `--root`; relocated installations require restoring exact raw
files and rebuilding the ignored payload. Changing a bound scientific source
invalidates the report until rebuilt.

Local/remote main remains 1a4991da4dda9676caeb1d7e35a03408528c3188.
The original checkout remains on presentation/eda-model-comparison and preserves
its pre-existing untracked .agents/ and docs/P1_FINAL_INTEGRATION_REAUDIT.md.
Only the new presentation branch is authorized for commits/push. No PR, merge,
force-push, branch deletion or main/research push is part of this milestone.

Implementation commit `5618bc4042d4a88b019504768772880cc15d2fcd` was pushed
and independently matched local HEAD, upstream and GitHub ls-remote. This
verification report, checklist and guide are published in a separate
documentation commit. The final local/remote tip is verified after its push
and reported in the completion response.
