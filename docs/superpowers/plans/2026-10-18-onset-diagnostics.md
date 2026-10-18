# Onset diagnostics implementation plan

> **For agentic workers:** Use Superpowers subagent-driven development for the
> independent evaluation utility and scientific review; coordinator owns diagnostics.

**Goal:** Explain exposed event errors and establish defensible onset-rule gates.

**Architecture:** Add diagnostics beside the unchanged frozen adapter; keep
prospective split auditing independent of forecasting and UI. Preserve source data.

**Tech stack:** Existing Python, NumPy, pytest; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-18-onset-diagnostics-design.md`.

## Global constraints

- No training, inference, V2 pilot, or V1/V2 protocol changes.
- January/August outcomes cannot select models, rules or thresholds.
- All model cohorts and pinned source artifacts remain intact.
- Unknown scientific support prevents rule certification.
- Commit/push only `codex/flare-onset-diagnostics`; no PR or merge.

## Review focus

- An onset whose class peak lies beyond the forecast horizon remains an onset.
- Threshold sweeps must retain the same eligible events and select no winner.
- Half-open horizon endpoints and zero/short lead must remain explicit.
- Shared event support and unknown boundaries must fail split certification.
- Catalog evolution flags are retrospective diagnostics, never predictors.

## Tasks and evidence ledger

- [x] Verify checkpoint/main/remote and create/publish isolated feature branch.
- [x] Establish baseline in the existing dependency environment.
- [x] Research real error artifacts and development/exposure support in parallel.
- [x] Write failing split tests; implement strict chronological event-group audit.
  Files: `events/evaluation.py`, `tests/test_event_evaluation.py`.
  Interface: `audit_chronological_split(origins, events, partitions, *, embargo_seconds)`.
  Ordered partition intervals and explicit origin/event support produce retained
  origin IDs, purge reasons and event-group assignments, or reject invalid input.
- [x] Write failing diagnostic tests; implement `diagnose_frozen(config, roots)`
  in `events/diagnostics.py` and `scripts/diagnose_flare_events.py`.
  Reuse the existing synthetic frozen bundle fixture and validate real counts.
- [x] Independently review implementation and scientific conclusions, address findings.
- [x] Run full tests, installed CLI/import smoke, deterministic replay, preservation,
  index/ignore audit and `git diff --check`; document only executed results.
Publication procedure: commit focused changes, push only the new branch and
verify its remote SHA. Final publication identity is reported after the push.

Execution note: system Python lacks xarray/astropy; this is environment evidence,
not a source regression. Use the pre-existing project virtual environment.

## Verified execution record

- Baseline: 270 passed; final full suite: 388 passed with one existing warning.
- Split implementation: 110 cases plus 300 independent randomized probes.
- Diagnostics: 8 tests, all 66 historical class/model comparisons preserved.
- Real final source/installed reports exactly equal; all nine checkpoints and
  August test forecasts match the prior preservation audit.
- Independent scientific/code review: no unresolved P0/P1/P2 within scope.
- Numeric onset rule freezing stopped at missing full-cohort development
  forecast/catalog support. Readiness parameters remain null.
- No historical cohort is certified unseen. Future November 2026 is a candidate
  outcome interval only, without validated source continuity or event adequacy.
- User-requested push-only publication preserves this branch/worktree; no PR,
  merge, main push or another milestone is authorized.
