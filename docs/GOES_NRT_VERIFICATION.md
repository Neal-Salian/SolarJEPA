# Near-real-time foundation verification

Verified on 2026-10-18 in isolated worktree
`/Users/nealsalian/.codex/worktrees/goes-near-real-time/SolarJEPA`.
Baseline `a495151`; branch `codex/goes-near-real-time-foundation`.
For portable operation use repository-relative paths and the CLI root options;
this absolute path identifies the verification workspace only.

## Executed checks

| Check | Actual result |
|---|---|
| Clean published dashboard baseline and remote | Fetched origin; dashboard branch equals origin at a495151; main equals origin/main at 1a4991d. Original checkout's two unrelated untracked entries preserved. |
| Baseline full suite | 1,239 passed, one pre-existing NumPy/native-extension ABI warning, 114.07 s. |
| Final full suite after source freeze and normal reinstall | **1,292 passed**, same warning, 125.88 s. No skipped tests in this environment. |
| New tests, CLI-first order | 53 passed, same warning; includes real saved-observation/checkpoint replay and local HTTP adversarial cases. |
| Independent reviewer | 53 new tests and 41 existing dashboard/prediction tests passed. Independent drip/framing, FIFO, oversized-cache and numeric-overflow probes passed after fixes. No remaining blocking findings. |
| Existing five-page behavior | Existing Streamlit AppTest tests passed in full suite and independent review; streamlit_app.py, dashboard tree/registries and pinned core/configs have no diff from baseline. |
| Normal package installation | Isolated local Python 3.13 environment, normal noneditable `pip install --no-deps --no-build-isolation --ignore-installed .`; package imports from its site-packages when invoked from /tmp. Existing dependency libraries reused without altering the original environment. |
| Installed live refusal | Imported installed modules from /tmp; forecast_snapshot with an attempted unvalidated override raised NrtForecastUnavailable. Cold-process subagent check also blocked model imports successfully. |
| CLI from /tmp | Saved snapshot assess exit 0/ASSESSED, forecast exit 2/FORECAST_UNAVAILABLE, pinned science replay exit 0/PASS; each actual offline process reported network audit denial active. |
| Independent V1 archive verifier | scripts/verify_flux_prediction.py PASS: exact context/mask/grid/actuals; both saved models' point and quantiles match at rtol 1e-6, atol 1e-15 W/m²; network blocked. |
| Storage and final diff | git diff --check passed. Actual cache JSON, raw science, checkpoints and local environment match .gitignore. Tracked science/model path scan contains only existing .gitkeep placeholders; final index/history contains code, tests and documentation only. |

The warning is `numpy.ndarray size changed, may indicate binary incompatibility`
(expected 16 from C header, got 96 from PyObject). It existed in the baseline.
Tests passing does not resolve that environment warning or establish operational
forecast validity.

## Live NOAA observations (single samples, not latency guarantees)

Raw response bytes and full receipt records remain in ignored cache storage.
These summaries retain provenance without committing observations.

| Role | Satellite | Receipt UTC | Latest native tag UTC | Measured tag age | Bytes / paired samples | Flagged rows |
|---|---|---|---|---|---|---|
| Primary | 18 | 2026-10-18T12:31:29Z (rounded for display) | 2026-10-18T12:28:00Z | 209.713321 s at assessment | 163280 / 358 | 267 |
| Secondary | 19 | 2026-10-18T12:32:25Z (rounded for display) | 2026-10-18T12:28:00Z | 265.205889 s at assessment | 163254 / 358 | 290 |

Flagged rows count native `electron_contaminaton=true` across both channels.
Both samples had paired tags and no internal minute gaps, and neither had a
numerically usable latest 120-minute context after conservative contamination
rejection. Both reported model_input_ready=false; no live forecast was made.
Publication time remains null. Tag position within a minute is UNKNOWN, so the
reported age is not measured publication/delivery latency.

Primary payload SHA256:
`3759d1d380214f4b42c773a2f3e3a3d4b769ef5bfdefd6d86eee6d2ea644fc2c`.
Secondary payload SHA256:
`7e955f2f232669105d3d2ff60c673fb03f1746a0de9bc2d4db5ea71830162bfe`.
Both final acquisitions used the final Content-Length-only parser and returned
ACQUIRED. An earlier primary request timed out and returned FAIL without cache
fallback; a later explicit invocation succeeded. This is observed failure
handling, not availability certification.

## Development/review findings and resolutions

Architecture and implementation were performed with a Superpowers subagent; a
separate fresh subagent reviewed the final code, tests and operational docs.
An initial ingestion worker hit a service usage limit before writing files, so
the controller implemented intake/CLI with test-first cycles. The architecture
worker completed the inference adapter and real replay tests independently.

Independent review identified and reproduced: full-buffer body reads exceeding
budget under drip traffic; unbounded reads of corrupt existing cache objects;
FIFO cache entries blocking offline reads; numeric overflow escaping domain
errors; and in-process CLI audit hooks contaminating later tests. Regression
tests failed before fixes, then passed. Final intake uses single-raw-read body
reads with remaining socket budget, rejects chunked/unknown framing, checks
regular files and capped reads, rejects overflow, and installs permanent audit
denial only in actual CLI processes. Drip tests confirm the server was contacted
to prevent a false pass caused by an inherited offline hook. Review also corrected
case-sensitive NOAA ReadMe URL spelling and cross-receipt monitoring wording.

Two intermediate full-suite runs were not clean: one used a stale normal package
installation missing the new modules; another overlapped source fixes and
correctly failed executed-source provenance. The environment was reinstalled
and the final full run used a fresh interpreter after source freeze, with the
clean result above. Neither intermediate failure was suppressed or accepted as
a passing verification.

## Verdict and remaining work

Foundation implemented and independently reviewed for explicit intake,
diagnostics and deterministic saved science replay. Live model inference is
blocked before checkpoint loading. Scientific JSON time/QC parity, operational
availability histories, GOES-18/19 transfer validity, prospective model skill and
uncertainty calibration remain unestablished. DNS/TLS/header wall-clock bounds,
automated retention and hostile concurrent file replacement are outside this
foundation's guarantees; see [operational documentation](GOES_NEAR_REAL_TIME.md).

Next milestone: authoritative time/QC mapping plus prospective shadow capture and
matched operational/science cross-satellite validation. No retraining, V2 change,
page replacement, PR or integration into main belongs to this milestone.
