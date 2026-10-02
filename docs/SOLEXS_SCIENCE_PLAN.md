# SoLEXS native scientific foundation implementation plan

**Goal:** Finish Phase C with reproducible product evidence and bounded native
access while preserving unresolved scientific interpretation.
**Architecture:** Extend the existing data package with one instrument module and
a thin offline CLI. Keep registration unchanged; temporary FITS access and chunked
spectra are scoped to context lifetimes.
**Stack:** Existing Astropy 8.0.1, NumPy 2.2.6, Python standard library, pytest.
**Spec:** [scientific access contract](SOLEXS_SCIENCE_CONTRACT.md).

## Constraints and review focus

Original ZIPs/inventory and GOES artifacts remain unchanged. Only
`data/solexs-science-validation` commits/pushes are authorized. No UTC conversion,
GTI filtering, calibration, imputation, dataset construction, acquisition or UI.
Review malicious paths/symlinks and expansion, header/layout inconsistencies,
nonfinite/irregular native values, resource cleanup, and portable determinism.
Missing unit/clock/calibration information must stay explicit.

## Task 1 — authority reconciliation and complete reconnaissance

Files: `docs/SOLEXS_PHASE_C_AUTHORITY.md`, source-identity manifest and ignored
investigation artifacts. No product implementation in this task.

- [x] Read/hash official originals; extract text and visually inspect relevant PDF
  pages; verify the release note independently of the user's summary.
- [x] Reconcile explicit epoch/PI start definitions with inconsistent legacy
  examples, actual LC cards and the separate processing-1.2 keyword change.
- [x] Inspect complete PI payloads under a 512 MiB cap; verify gzip/ZIP/FITS checks,
  all dimensions, native coordinates, missingness and exposure without corrections.
- [x] Update evidence classifications/remaining scientific gates; verify the
  portable source manifest and investigation recipe before a documentation checkpoint.
  Committed/pushed `03acbe9`; all 27 source identities and the authority recipe pass.

## Task 2 — bounded scientific product access and inspection

Files: create `src/solar_flare_jepa/data/solexs.py`, `tests/test_solexs.py`;
create `scripts/validate_solexs.py`, extend installed CLI help coverage.
Interfaces are exactly the five functions and `AccessLimits` in the contract.

- [x] Write synthetic tests for identity/integrity/caps/cleanup and LC/GTI native
  loading; run and observe failure because the science API does not exist.
- [x] Implement access and loaders; run those tests and the existing suite.
- [x] Write failing tests for PI dimensional validation/chunking and deterministic
  schema/quality/time summaries, then implement those behaviors and run the suite.
- [x] Add and exercise the offline CLI with synthetic relocated roots and explicit
  config inputs; verify normal installation outside the repository.
- [x] Commit/push a focused native-foundation checkpoint after raw-data/index checks:
  `931d033`. A subsequent source-protection regression was reproduced RED and
  fixed GREEN with atomic report publication in `e016cf5`.

## Task 3 — final real-sample verification and downstream scientific gate

Files: current scientific findings/report, `docs/PROJECT_STATUS.md`, ignored
machine-readable report and separate measured memory artifact.

- [x] Validate both complete samples through the retained API/CLI, compare the
  independent reconnaissance, repeat report bytes and verify relocation.
- [x] Characterize measured disk/table/chunk sizes and process memory, clearly
  separating mapped-file size, copied-array size, RSS and projections.
- [x] Document all sixteen success questions with evidence/unknowns and the exact
  native representation the subsequent phase may access; retain scientific gates.
- [x] Fresh targeted/full suite, import/CLI, pip check, GOES artifact/data regression,
  raw hashes, ignore/index/reachable-history scan, portability and diff checks.
- [x] Independent whole-branch review; reproduce/fix material findings with tests,
  rerun affected/final verification and review the result.

Final Git gate, performed after the documentation commit: push only the feature
branch, fetch/verify local and remote feature HEADs, main refs and clean status.
Record those final refs in the handoff and stop for the user's decision. No
integration or subsequent-phase work is authorized.

Progress/check evidence belongs here and in the final report; no workflow may
convert an unresolved scientific policy into an implementation assumption.

Executed TDD includes the initial 13 RED tests before implementation, PI/summary/
CLI RED→GREEN cases, and independently reproduced review regressions for cached
column lifetime, identities/processing level, variable-length arrays and integer/
mixed precision, and hard-linked report publication. Latest targeted suite:
70 passed; full suite: 144 passed with the existing dependency warning.
Actual repeat/relocation report SHA-256:
`70241bdde078c8e0986bb23117c6543a262fe1846bfd81e64d4b49380f43eb8a`.
Both PI summaries agree with the separate pre-implementation probe. All original
ZIPs, official originals, GOES files/artifacts and protected infrastructure agree.
Final independent whole-branch review found no remaining Critical/Important
issue. It separately ran the 70 targeted tests, pip check and source/report/data
protection checks. Final bookkeeping corrections are included in this plan and
the current tracker/findings; the final publication gate is recorded above.
