# V2 M0/M1 Validation Foundation Implementation Plan

> **For agentic workers:** Use Superpowers TDD, executing-plans and independent review. Current user explicitly authorizes continued safe M1 implementation and subagents; no additional approval of scientific defaults is inferred.

**Goal:** Complete M0 documentation, then implement safe model-independent M1.
**Architecture:** Reuse P1/P2 canonical contracts/windows/normalization. Add strict
evaluation records, explicit embargo and crossed paired statistical diagnostics.
**Tech Stack:** Existing Python/NumPy/pytest only.
**Spec:** `docs/V2_M1_DESIGN.md`; scientific decisions `docs/V2_M0_RESOLUTION.md`.

## Global constraints

No candidate/raw/processed holdout access, new scientific training, confirmatory
evaluation, V1 artifact changes, teammate branch changes, merge or PR. Synthetic
regression tests may execute existing tiny neural software fixtures; these are
not new scientific models. Preserve existing untracked files. Publish only the
isolated authorized feature branch, with explicit files staged.

## Review focus

* Copies/deserialization must not bypass P1 canonical validators.
* Pairing requires identical observed targets/masks/times and metric definitions.
* Embargo checks must preserve explicit dates and reject bool/overflow inputs.
* Empty calendar-day blocks must not be filtered or redrawn to manufacture CIs.
* Masks/normalization and logarithmic domains must reject false-valid values.

## Task 1: M0 and design evidence

Files: `docs/V2_M0_RESOLUTION.md`, `docs/V2_M1_DESIGN.md`, this plan.
Produces: documented source audit, exposure ledger, decision gates and interface proposal.

- [x] Compare refs/ancestry/worktrees and source/tests/configs/tracked manifests.
- [x] Independently audit scientific protocol, provenance and architecture.
- [x] Record proposed decisions and blockers, preserving older reports.
- [x] Commit M0 evidence before implementing M1.

## Task 2: Temporal and record contracts

Files: `forecasting/splitting.py`, new `evaluation/records.py`,
`tests/test_independent_records.py` and `tests/test_independent_integrity.py`.
Consumes: P1 canonical classes/window builder; P2 Normalization.
Produces: explicit `embargo_ns`, `EvaluationIdentity`, `EvaluationRecord`,
`validate_fitting_artifacts`; exact signatures recorded in implementation docs.

- [x] Write failing tests for minimum gaps and schema/roundtrip/support mismatch.
- [x] Run targeted pytest; missing API or assertion failure proves RED.
- [x] Implement canonical snapshots and strict provenance/normalization checks.
- [x] Add synthetic boundary/gap/mask/future-feature/heldout-perturbation regressions.
- [x] Run targeted pytest; require all pass. Commit logical contract changes.

## Task 3: Paired statistics and calibration

Files: new `evaluation/{comparison,diagnostics}.py`,
`tests/test_independent_{comparison,diagnostics}.py`.
Consumes: P1 canonical predictions/targets; panels from caller losses.
Produces: `LossPanel`, `paired_comparison`, `calibration_diagnostics`.

- [x] Write literal paired-effect/calibration tests plus bad-pair/calendar cases.
- [x] Run tests and observe RED before implementation.
- [x] Implement shared seed/day resampling, sums/counts and finite JSON outputs.
- [x] Verify deterministic outputs, exact effect signs/weights, empty draws,
  zero reference, ordered cohorts, quantile domains and empty mask diagnostics.
- [x] Run targeted pytest; require all pass. Commit logical statistical changes.

## Task 4: Independent review, verification and publication

Files: new `docs/V2_M1_VERIFICATION.md`; update design with exact APIs.
Consumes: complete implementation and all test evidence.
Produces: reproducible verification report and published feature branch.

- [x] Independently review complete branch and scientific methodology.
- [x] Reproduce correctness findings with failing tests and fix root causes.
- [x] Reinstall normally; run targeted/full suites and installed import smoke.
- [x] Inspect complete diff/check/status/history, data ignores/index and ref isolation.
- [x] Document observed warnings/limitations and readiness; commit and push.

## Execution ledger

Ruling: native implementation plus an independent contract implementer and fresh
whole-branch reviewers follows the user's explicit delegation/continuous execution
request. Skill approval handoffs do not override that authorization. Scientific
protocol approval remains pending in the decision register.

Pre-flight: Task 2 reuses canonical P1 targets/predictions; Task 3 diagnostics use
the same canonical classes and comparisons bind caller-provided support identity.
No concurrent edits to shared files; model/experiment training code is read-only.


Task 1: complete — source/ref/config/tracked-evidence reconnaissance and three
independent audits; M0 documentation committed before implementation.
Task 2: complete —58 new contract/integrity tests, normalizer/schema/empty-record
review corrections RED→GREEN. Reused existing P1 support logic.
Task 3: complete —63 comparison/diagnostic/integration tests; paired calendar
arithmetic, units and model/spec identity review corrections RED→GREEN.
Task 4: verification complete —full suite1292passed/1existingwarning, targeted
121passed, normal installed isolated imports/pipcheck and branch/storage audit.
Publication follows this documentation commit as the final authorized action.

Ruling: a draft seed-list transcription was corrected by checking the exact
existing V2.1 SHA-generated cohort; no experiment used the draft values.
Ruling: disjoint fold calendars are required because this kernel draws each
fold's calendar independently; overlapping physical paths need another contract.
Ruling: raw LossPanel labels are trusted inputs; a canonical-record adapter
provides observed support/quantile/spec binding for primary equal-cell dex loss.
Ruling: mixed native units have no pooled unit-sensitive score; proper central
interval scores require relatively symmetric tail masses.
Final review: independent statistical and fresh whole-branch reviewers; all
reproduced correctness findings fixed with failing-then-passing tests. Declined
scientific/authentication topics remain limitations in V2_M1_VERIFICATION.md.
No deferred implementation finding remains; scientific decision gates persist.
