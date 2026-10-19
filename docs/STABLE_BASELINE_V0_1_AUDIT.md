# Stable Baseline v0.1 integration audit

Audit date: **2026-10-18, Asia/Kolkata**. This report records the pre-integration
source, history, dependency and worktree inspection. Fresh execution results and
the release verdict belong in the release-readiness report; historical test
counts below are attributed to their original reports.

Evidence labels: **OBSERVED** means inspected files, Git objects or execution;
**DOCUMENTED** means authoritative documentation states it; **INFERRED** means a
conclusion from that evidence; **UNKNOWN** means not established.

## Verified starting state

**OBSERVED:** `main` and `origin/main` both resolved to
`1a4991da4dda9676caeb1d7e35a03408528c3188`. The new integration worktree was clean
on `codex/stable-baseline-v0.1`, initially at that commit, with its corresponding
origin branch and upstream configured. No existing worktree was repurposed.

The primary checkout remained on `presentation/eda-model-comparison` at
`660f469683557a0f3134f72ec69b174a5bcdd917`, with exactly these existing untracked
entries: `.agents/` and `docs/P1_FINAL_INTEGRATION_REAUDIT.md`.

**OBSERVED:** the onset-diagnostics worktree also had three untracked paths at
audit: `docs/superpowers/plans/2026-10-18-onset-diagnostics.md`,
`docs/superpowers/specs/2026-10-18-onset-diagnostics-design.md` and
`tests/test_event_diagnostics.py`. These belong to another workstream, remain
untouched and are excluded. All other pre-existing linked worktrees had clean
tracked/untracked status. This audit did not inspect or claim ignored artifacts
were absent merely because Git status was clean.

## Branch and worktree inventory

Prefixes below are unique 12-character commit identities at audit. `—` means no
linked worktree; `remote only` means no corresponding local branch. All existing
local branches with corresponding origin refs resolved to matching tips.
`main` and `data/solexs-ingestion` had matching remote counterparts without a
configured upstream. Worktree labels identify entries in `git worktree list
--porcelain`, not portable storage paths.

| Branch | Tip | Worktree / integration disposition |
|---|---|---|
| `main` | `1a4991da4dda` | —; immutable integration base |
| `chore/agent-instructions` | `7ce7f02cf3ad` | —; main ancestor |
| `codex/developer-handoff-recovery` | `d5e1677fabef` | developer-handoff-recovery; documentation reference |
| `codex/flare-onset-diagnostics` | `16b975fa945d` | flare-onset-diagnostics; excluded, dirty untracked paths above |
| `codex/goes-near-real-time-foundation` | `eacdb2c54b6a` | goes-near-real-time; excluded |
| `codex/solar-flare-event-forecasting` | `16b975fa945d` | solar-flare-event-forecasting; excluded |
| `codex/solar-flux-prediction` | `a4951516dc20` | solar-flux-prediction; selected stable runtime lineage |
| `codex/solexs-scientific-integration` | `df88009ae87c` | solexs-scientific-integration; excluded |
| `codex/stable-baseline-v0.1` | `1a4991da4dda` | stable-baseline-v0-1; new integration branch, starting tip |
| `codex/v2-experimental-validation-readiness` | `8e9ce06407d5` | v2-experimental-validation-readiness; excluded |
| `codex/v3-research-design` | `3692c5bc2d7e` | v3-research-design; excluded |
| `data/solexs-authoritative-evidence` | `1abed0f86c1c` | —; already in main |
| `data/solexs-ingestion` | `351482dc11aa` | —; already in main |
| `data/solexs-science-validation` | `bc364dca5b0c` | —; already in main |
| `data/solexs-timing-calibration` | `cd6f9c5dd29f` | —; already in main |
| `data/v2-goes-development-restoration` | `8a9c98db66ec` | remote only; excluded |
| `feat/p1-experiment-evaluation-foundation` | `595371190177` | —; selected ancestor contracts/evaluation |
| `feat/p2-dual-source-training-foundation` | `656e540162c6` | —; selected ancestor GOES foundation |
| `feat/v2-controlled-model-development` | `1826400ca9ca` | remote only; excluded |
| `feat/v2-m0-m1-validation-foundation` | `fd7203bf9a2e` | —; excluded |
| `feat/v2-m5-pilot-readiness` | `60718686f016` | —; excluded |
| `feat/v2-model-evaluation-integration` | `2e3f87111ab7` | —; excluded |
| `feat/v2-training-protocol-feasibility` | `ac3428f910b3` | —; excluded |
| `presentation/eda-model-comparison` | `660f46968355` | primary; selected ancestor EDA/comparisons |
| `presentation/final-time-series-presentation` | `a41c3dd803ea` | final-time-series-presentation; excluded deck |
| `presentation/solarjepa-streamlit-dashboard` | `d718177a9a41` | solarjepa-dashboard; selected ancestor four-page app |
| `presentation/time-series-requirements-completion` | `abe4b79d2fe7` | time-series-requirements; two selected commits |
| `research/experiment-evaluation-foundation` | `805f1c3f8bc0` | —; selected historical ancestor |
| `research/goes-external-model-evaluation` | `a502d3fbf65f` | goes-external-model-evaluation; excluded |
| `research/goes-external-validation` | `f309921d776c` | goes-external-validation; excluded |
| `research/phase-e-solexs-validation` | `83b54435c163` | —; excluded |
| `research/solexs-provisional-sequence-modeling` | `3baad2bc2f8c` | —; excluded |
| `research/v2-independent-validation` | `90571dfe1444` | —; excluded |
| `research/v2-m2-statistical-validation` | `94cae59398e5` | v2-m2-statistical-validation; excluded |
| `research/v2-m3-inference-remediation` | `5e88f3a71092` | —; excluded |
| `research/v2-m5-protocol-review` | `c872e4a2b8ea` | remote only; excluded |
| `v1` | `644648f7d555` | —; selected frozen V1 ancestor |

## Selection and dependency map

**OBSERVED:** `main` is an ancestor of V1, EDA, dashboard, prediction and
time-series branches. The common ancestor of prediction and time-series is
`d718177a9a4133c77602f3f02bd6fb04d83aca65`. Time-series is a sibling extension
of the four-page dashboard: its tree does **not** contain `prediction.py`,
`prediction_page.py` or prediction replay tests. The final deck starts from
old-main lineage and cannot supply the requested application.

Selected integration:

1. Integrate exactly the `codex/solar-flux-prediction` lineage at
   `a4951516dc2094ceb246b016700d1483a808212b`. It includes 67 commits after
   main, preserving the tested P1/P2/V1 ancestry and existing source identities.
2. Apply `5618bc4042d4a88b019504768772880cc15d2fcd` (time-series features)
   and `abe4b79d2fe7549552b0a1f467be1cd949b652a7` (time-series guides).
   Resolve presentation composition only; preserve pinned scientific sources.
3. Reference the developer handoff at `d5e1677fabeff019873c2c1ea2a20aabdb773df4`.
   Any retained handoff/recovery copy is historical context; write current
   baseline setup/status separately. Do not replace current repository rules
   with a blanket cherry-pick of its `AGENTS.md` edit.

| Required behavior | Existing source / dependency | Runtime inputs / verification |
|---|---|---|
| Historical GOES ingestion/QC | `data/goes.py`, `goes_acquisition.py`, `foundation.py`; P2 `8650896`, `3eb48d6`, V1 `3452d44` | Four pinned May–August configs/manifests; 123 raw files; native minute grid, channel flags/counts, positive finite flux; no imputation |
| Canonical support and leakage controls | `forecasting/contracts.py`, `windows.py`, `splitting.py`; remediations through `5953711` | Complete 120-minute context, 30-minute horizon, purged chronology, explicit availability and masks |
| V1 neural inference | `training/jepa.py`, `core.py`, `normalization.py`; `a4f53ce`, `4a3f882` | Trusted seed17 JEPA/supervised checkpoints; saved train-only normalization; torch 2.6.0 |
| Existing baselines | `forecasting/baselines.py`, `statistical.py`; `fcb928e`, `88131aa` | Archived V1 scores for deterministic/statistical/neural families; no real-data fitting during integration |
| EDA/model comparison | `presentation/eda.py`, `comparison.py`, figures/pipeline; `660f469` | Original summary/per-origin/NPZ, raw files, committed evidence/figure identities |
| Four original dashboard pages | `dashboard/data.py`, `charts.py`, registry and `streamlit_app.py`; `d718177` | May/June 61 raw files, 17 pinned sources, archived model/diagnostic evidence |
| Fifth prediction page | `dashboard/prediction*.py`, separate registry, `4dab5c1`, `a495151` | August 31 raw files, seed17 checkpoint(s); no prediction-array access by app |
| Complete time-series views | `presentation/time_series.py`, `classical.py`, `dashboard/time_series.py`; `5618bc4` | Ignored `results/presentation_time_series/diagnostics.json`, exact report/source hashes; saved-parameter replay only |

Inherited P2 smoke/training entry points and pre-existing main SoLEXS inspection
remain historical infrastructure. Their presence does not authorize execution
or clear scientific gates. No V2 model/pilot, V3, external-evaluation, event, NRT
or later SoLEXS research lineage is needed for the stable runtime.

## Conflict and preservation controls

The selected time-series feature modifies `streamlit_app.py` and
`tests/test_dashboard_ui.py`; other added time-series files are independent.
Compose its reusable renderer calls with prediction's fifth-page route,
conditional sidebar scope and lazy model import. Expected chart counts become
Overview 1, Data Explorer 4, Time-Series Analysis 2, Model Results 2,
Solar Flux Prediction 1.

`tests/test_flux_prediction_ui.py::run_legacy_boundary` contains pre-extension
chart counts `[1,2,1,1]` and a matching JSON assertion. Update those expected
counts to `[1,4,2,2]` while retaining its fresh-process guards against network,
torch/training/prediction imports, August raw inputs, checkpoints and prediction
archives on the four presentation pages. The 61 native-file count remains exact.

Prediction's shared `_NATIVE_IO_LOCK` in `dashboard/data.py` must survive the
composition. Keep every registry, checkpoint, normalization, core source and
scientific evidence identity unchanged. Prediction checks actual loaded source
ownership and hashes as well as file hashes. Its registry pins 13 core modules;
time-series pins its scientific sources and `requirements-dashboard-lock.txt`.
Neither pins `streamlit_app.py`, so presentation composition needs no registry
rebinding and no scientific-array regeneration.

## Dependencies and storage

**OBSERVED:** the prediction lock extends `requirements-dashboard-lock.txt` with
torch 2.6.0. Dashboard uses statsmodels 0.14.6 and Pillow 11.3.0; the historical
V1 lock uses statsmodels 0.14.5, Pillow 12.3.0 and packaging 26.3 through its base
lock. Installing the V1 and dashboard locks together is not a reproducible
resolution. Preserve historical locks as evidence; use the dashboard-prediction
family for the combined runtime and test it independently. The dashboard lock
does not include Astropy/cdflib needed by inherited SoLEXS foundation tests;
choose a compatible additive stable lock rather than silently skipping those
tests or installing the incompatible older lock family. Portability beyond
the recorded CPU/macOS environment remains unverified until actually tested.

Raw data and checkpoints are ignored assets, not release source. Provision exact
manifest-listed files by copying bytes into this isolated checkout, without
changing originals. Avoid symlinks escaping the root: path guards intentionally
reject redirected input paths. Do not bulk-copy all results or environments.
Hash-match each copy against its scientific manifest/registry before use and
check its actual destination with `git check-ignore -v`. Keep arrays, NetCDF,
checkpoints, original archives and environment directories out of the index and
integration history. No acquisition, real-data fitting, checkpoint conversion,
normalization refit or plot regeneration is required.

Required local artifact groups:

- All 123 May–August raw GOES files, 36,535,474 bytes, authenticated by four
  acquisition manifests; May/June dashboard subset has 61 files/87,840 rows.
- Original V1 bundle `results/experiments/v1-full-20261009/`; the prediction app
  needs seed17 JEPA and optionally supervised checkpoints. Reference replay
  additionally needs `summary.json` and `test_predictions.npz`; presentation
  verification also needs the bundle files listed by its existing manifest.
- Exact time-series payload `results/presentation_time_series/diagnostics.json`,
  SHA-256 `69935892e311ef4aacd00a7e9e6ccb055aac8abb1cda7ee988195d6f2fcc5675`.

## Handoff discrepancies and limits

The handoff's historical claim that all earlier linked worktrees were clean was
accurate for its own snapshot, but the dirty onset paths above are now observed.
Several worktree labels in its table no longer have linked worktree entries;
their branch refs remain. Its own table intentionally records main's creation
base in the handoff row; the delivery SHA is `d5e1677fabef`. The handoff explicitly
distinguishes classical time-series from the separate prediction extension;
integration must preserve that distinction rather than assume either tip is a
complete superset. Its older passing test counts are supporting history, not
fresh Stable Baseline v0.1 results.

**DOCUMENTED:** handoff checks reported 166 base tests, 87 selected V1 tests,
58 dashboard/prediction tests, 53 classical/time-series tests, a passing 52-identity
presentation verifier and seed17 replay within `rtol=1e-6`, `atol=1e-15`.
Those suites overlap; do not sum them as an integration test count. It did not
perform a fresh environment rebuild and reported an existing NumPy/netCDF
ndarray-size warning. Numerical impact of that warning is **UNKNOWN** until
further evidence; dependency checks and numerical replay must report it honestly.

V1 is retrospective continuous flux forecasting, with source run
`4a3f88227ce28dea0e885e68987282285963f38e`. Marginal quantiles are uncalibrated.
August was previously inspected; no untouched confirmatory holdout claim or
statistically supported JEPA-superiority claim follows from the descriptive
seed-mean comparison. Minute-bin starts and retrospective bin-end availability
are distinct; operational latency is unknown. STL's imposed daily period is a
diagnostic assumption. SARIMA fit/score remains unavailable.

Excluded release workstreams: V2 pilot and its execution/reservation machinery,
V3 research, unvalidated live inference/NRT acquisition, event forecasting,
external January model-evaluation research, and later native/provisional SoLEXS
research. SoLEXS time/calibration/exposure/quality/physical quantity gates remain
blocked; inclusion of main's inspection tools is not scientific clearance.

## Executable validation and merge gate

The [implementation plan](superpowers/plans/2026-10-18-stable-baseline-v0-1.md)
specifies exact commands. Execute source/import/dependency checks, GOES manifest
verification, all five offline dashboard routes and controls, time-series
saved-parameter replay, full saved-score verification, and explicit original V1
prediction replay. Do not regenerate the frozen scientific artifacts to make
checks pass. Full test selection must distinguish synthetic bounded fitting
from forbidden real-data retraining, and describe any deliberately excluded
training tests. Independent scientific and technical reviews must examine the
final combined tree and actual fresh outputs.

Before a proposed main integration: resolve release-blocking findings; record
actual test results, supported environment and artifact availability; review
the final diff/history/index and data-ignore checks; commit/push only this
feature branch; recheck main/remote for intervening movement. No PR is authorized.
Stop and request the user's explicit merge approval. Approval to merge does not
authorize a push to main; obtain that action's explicit authorization separately.
