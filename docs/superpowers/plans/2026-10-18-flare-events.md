# Flare-event implementation plan

**Goal:** A tested retrospective event layer over existing frozen GOES forecasts.
**Spec:** [design](../specs/2026-10-18-flare-events-design.md).
**Execution:** User authorized autonomous subagent implementation and review.
**Architecture:** Narrow events package; preserve main readers and historical branches.
**Tech stack:** Existing Python, NumPy, pandas, pytest; no added dependency.

## Global constraints

No retraining, V2 pilot, checkpoint/data mutation, PR, merge or push to main.
Preserve native half-open bins, retrospective peak-class truth and UNKNOWN facts.
Reject mismatched provenance; scores remain exploratory and QC-conditional.

## Review focus

Future peak maturity (including subthreshold peaks); zero-lead detection versus
advance prediction; corrupted/reordered artifacts; partial catalogs and gap
coverage; scarce/undefined class metrics and correlated origins.

## Tasks

- [x] 1. Core labels: `events/labels.py`, `tests/test_event_labels.py`.
  Extract existing label support/maturity logic into a minimal array interface.
  Test first: gaps, incomplete states, duplicate conflicts, class boundaries,
  peak after horizon, partition crossing, future feature availability, zero lead.
- [x] 2. Subagent matching/scoring: `events/{matching,scoring}.py`, corresponding
  tests. Adapt historical maximum-cardinality matcher, add explicit minimum lead,
  contingency metrics and deterministic UTC-block percentile intervals. Verify
  ambiguous matching, permutations, empty classes and excluded support.
- [x] 3. Artifact adapter: `events/frozen.py`, `scripts/evaluate_flare_events.py`,
  pinned `configs/events/january2025_frozen.json`, tests. Write failing tests for
  changed hashes, shifted/reordered coordinates, incompatible label definitions,
  mask/fingerprint mismatch and unsafe paths; implement strict read-only binding
  and deterministic threshold policies. Execute synthetic and real frozen runs.
- [x] 4. Independent scientific/code review, remedy defects, rerun covering tests,
  full main-based suite, isolated installation/import and CLI smoke, source/data
  identity and ignore/index checks; document executed evidence and readiness.
- [x] 5. Focused Conventional Commits and push only this feature branch; verify
  clean status and remote equality. Preserve source branch refs and artifacts.

## Progress

- Audit and research subagents completed. Baseline: 166 tests pass; one existing
  NumPy/netCDF binary-compatibility warning. No baseline failures.
- First scientific-design reviewer failed with a service usage-limit error;
  a fresh scientific reviewer and a separate code reviewer subsequently completed
  review. Both final verdicts reported no unresolved important/blocking findings.
- Matching/scoring implementer: 61 deterministic tests. Final whole feature
  suite: 270 passed, one existing environment warning. Installed-package run
  reproduced 1007 retained /1488 candidate origins and all22 model outputs.
- Review defects were reproduced before correction: configurable lead/exposure,
  full label/support and calibration declarations, catalog hash conflicts, missing
  candidate coverage, source/semantic fingerprints and lineage, cohort selection,
  missing peak flux, mixed booleans and exhausted event generators. Regressions
  cover these; final review and execution evidence is in FLARE_EVENT_VERIFICATION.md.
- Publication verified: implementation `3d246f8` and scientific report `9c98585`
  pushed only to `origin/codex/solar-flare-event-forecasting`; local and upstream
  hashes matched with clean status. No raw/model/report files entered the 16-file
  milestone history. Main/V1 and inspected V2 refs remained at their audited heads.
