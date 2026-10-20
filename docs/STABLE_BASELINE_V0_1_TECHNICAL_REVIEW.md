# Stable Baseline v0.1 independent technical review

Review date: **2026-10-18, Asia/Kolkata**. Reviewer: independent technical
subagent; no implementation ownership. Reviewed base:
`1a4991da4dda9676caeb1d7e35a03408528c3188`; integration HEAD at review:
`e92efdd`, plus the final uncommitted setup/preflight/replay/package/documentation
changes and the presentation-only unavailable-message correction. This report
was the only repository file written by this reviewer.

**Verdict: PASS for the bounded historical baseline technical scope. No unresolved
P0/P1/P2 or P3 findings.** The coordinator's final combined suite, post-fix
verification, source reinstall where required, index/history inspection and
feature-branch publication remain separate completion gates. This review is not
main integration authorization.

Evidence labels: **OBSERVED** denotes this reviewer's file/Git inspection or
executed checks; **DOCUMENTED** denotes attributed requirements/report statements;
**INFERRED** denotes conclusions from inspected evidence; **UNKNOWN** denotes
unverified behavior. Other agents' passing reports are not counted as checks
executed by this reviewer.

## Scope and inspected implementation

The review followed the requesting-code-review approach: compare implementation
against the explicit integration plan, inspect actual source and runtime, and
report findings with severity and concrete evidence. The integration plan,
repository rules, audit, setup guide, release report and scientific preservation
report were read. The review inspected the base-to-HEAD change inventory and
focused on source preservation, dependency/package installation, artifact trust,
CLI exit behavior, UI isolation, no-fit replay and source-only checkout behavior.

**OBSERVED:** the current tree retains the requested GOES/QC, forecasting and V1
lineage. Direct Git comparisons against prediction tip
`a4951516dc2094ceb246b016700d1483a808212b` found no byte changes in the scientific
`data/`, `forecasting/`, `training/`, `evaluation/` or `experiments/` packages,
`_executed_source.py`, frozen V1 experiment/model configurations, prediction
service, or the two dashboard registries. The scientific time-series sources
`presentation/time_series.py` and `presentation/classical.py` and their tracked
identity/report files match time-series tip
`abe4b79d2fe7549552b0a1f467be1cd949b652a7`. Composition is in presentation routing;
the final renderer correction below does not alter pinned scientific source.

**OBSERVED:** Streamlit routes all five pages, uses conditional historical
sidebar scope and lazily imports the neural prediction page. Shared native I/O
locking remains in the two observation loaders. Forecast preparation preserves
120 completed context bins, a separate 30-bin future grid, channel masks and
actual-future display values. Normalization/spec/checkpoint identity checks and
loaded-source ownership verification remain intact. The four presentation pages
continue to read their saved diagnostic payload rather than fit models. The
classical inference button applies saved parameters and verifies its outputs.

**OBSERVED:** `pyproject.toml` explicitly includes the dashboard JSON resources.
The stable dependency lock includes the preserved dashboard-prediction lock with
an additive science/import test dependency set. The guide clearly scopes the
observed environment to CPython 3.13.3/macOS arm64/CPU and warns against overlaying
incompatible historical lock families. `scripts/check_stable_baseline.py` is
standard-library-only, anchors original registry/identity bytes, verifies path
containment and SHA-256, and checks all nine checkpoint identities with
`--references`. The full-reference verifier checks original records, raw support,
normalization and saved neural predictions without fitting or creating outputs.

## Finding resolved during review

**P3, addressed:** `src/solar_flare_jepa/dashboard/time_series.py::_evidence`
previously displayed the inherited scientific loader's recommendation to run
`scripts/build_time_series_presentation.py` when the pinned payload was missing
or changed. That builder fits/rebuilds scientific evidence and is inappropriate
as a stable artifact-restoration instruction.

The implemented presentation-only correction preserves the diagnostic reason,
recommends restoring original pinned payload/sources, and points to
`docs/STABLE_BASELINE_V0_1_RUN.md`. The pinned scientific loader remains unchanged.
`tests/test_time_series_ui.py::test_unavailable_new_evidence_preserves_existing_explorer_charts`
now checks the real inherited error form, removal of the builder suggestion,
the restoration guidance and preserved existing charts. The reviewer inspected
the diff and independently reran the affected failure tests successfully.

## Checks independently executed

| Command/check | Observed result |
|---|---|
| `.venv/bin/python -m pip check` | Exit 0; no broken requirements |
| `.venv/bin/python -m pip show -f solar-flare-jepa` | Normal installed distribution found; both dashboard JSON registries present |
| Targeted stable/prediction dependency, artifact, registry, installed-package and missing-input tests | **9 passed, 25 deselected**, 2.85 s |
| Fresh-process presentation file/import isolation; fifth-page controls; classical saved inference with fitting/network forbidden | **3 passed**, 10.65 s; one existing NumPy/netCDF warning |
| Post-fix time-series unavailable/mismatch tests | **2 passed, 7 deselected**, 2.34 s; one existing warning |
| Read-only `check_artifacts(root, references=True)` | All **222** artifact identities matched; **123** native files enumerated |
| Git byte comparison against the two selected source tips | Frozen scientific/config/registry/evidence paths unchanged as described above |
| `git diff --check` | Exit 0, no whitespace errors |
| Tracked paths and base-to-HEAD history for `.nc`, `.npz`, `.pt`, `.npy`, `.fits`, `.cdf` | No matching tracked scientific payloads introduced |
| `git check-ignore -v` on actual raw/checkpoint/result destinations | Expected `data/raw/**` and `results/**` protections apply |

The 14 completed targeted tests above are this reviewer's executed test evidence;
the coordinator's full suite and the scientific review's all-nine numerical
replay are reported separately. An earlier long-running targeted invocation was
not counted because its final output was not retained by this reviewer.

A temporary **source-only copy** excluded `.venv`, raw/intermediate/processed data
and all results. Its checker returned structured JSON, exit **1**, `FAIL`,
**136 precise missing-artifact errors** and 123 expected native entries. The
first missing paths named the seed17 checkpoints, prediction archive and summary.
Each of its five AppTest routes rendered an explicit unavailable message without
an uncaught exception; chart counts were **0 / 0 / 1 / 1 / 0**. The retained charts
were independently available archived diagnostics/comparisons. No fabricated
forecast appeared. This was a source-only copy exercise, not a network clone or
a fresh dependency installation performed by the reviewer. It preceded the
presentation error-guidance correction; the correction received the separate
post-fix test run above. The temporary copy was removed afterward.

## Limits and remaining integration gates

**INFERRED:** byte preservation, guarded source/asset loading, tested route
isolation and successful targeted runtime checks support technical compatibility
for the named historical baseline. A source clone deliberately lacks the raw and
checkpoint bundles; successful release preflight and numerical replay require
custodian restoration of the exact originals. The run guide correctly makes this
explicit and forbids replacing originals by refitting or changing hash pins.

**UNKNOWN in this review:** cross-platform/GPU behavior, prospective or live
inference, scientific generalization, operational delivery latency and the cause
of the retained NumPy/netCDF binary-size warning. Successful reads do not resolve
that warning's underlying cause. No human-browser visual assessment, clean
installation from an empty package cache, scientific fitting, acquisition, pilot,
PR, commit, push, merge or mutation of original data/worktrees was performed by
this reviewer. The final full-suite result must come from the coordinator's
actual completed execution, including reruns affected by the final correction.

V2 pilot, V3 research, live/NRT inference and SoLEXS physical forecasting remain
explicitly excluded. Inherited foundation tools do not establish those scientific
capabilities. Before publication, retain the original artifact bundle, complete
the documented final verification and inspect staged/history paths. Publish only
the authorized integration feature branch. A merge into `main` and any push to
`main` each require their separately explicit user authorization.
