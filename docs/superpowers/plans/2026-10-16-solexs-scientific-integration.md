# Guarded SoLEXS scientific integration plan

> Execution: coordinator implementation with Superpowers scientific and code
> review subagents, test-first behavior changes and independent final review.

**Goal:** make verified native SoLEXS observations reusable for future JEPA
integration while refusing unsupported scientific interpretation and training.

**Architecture:** reuse the existing bounded archive/FITS loaders; add immutable,
dtype-preserving native batches, numerical quality masks and continuity
diagnostics. Keep native arithmetic distinct from scientific quality. Bind an
offline readiness audit to exact configuration, inventory and Phase E evidence
bytes. No new scientific constants, dependency, model or experiment changes.

**User brief:** audit existing SoLEXS work and original inputs, implement validated
missing preprocessing/QC, preserve unknowns, test and independently review,
commit/push this new branch only, without PR, merge or retraining.

**Base:** `3baad2bc2f8cf926e2bf58b782528abc7c6e840d`, containing Phase E
`83b54435c1634f7de0a3ec6494439c023a4d0296`; verified fetched main
`1a4991da4dda9676caeb1d7e35a03408528c3188` is an ancestor. The explicitly
requested SoLEXS checkpoint takes precedence over the generic main-base rule.

## Constraints and review focus

- All writes occur in the new managed worktree; original raw inputs are copied
  into ignored storage before loaders can create scratch directories.
- Preserve native dtype, values, row order, NaNs, detector/channel identifiers,
  encoded units (including null), original warnings and complete member lineage.
- Finite masks and unit-step boundaries describe stored numbers; they are not
  mission quality clearance, live exposure, seconds, event labels or UTC.
- Compare both closed and half-open native GTI membership as explicit hypotheses;
  neither is applied as a scientific filter. Reject mismatched source/detector.
- Do not normalize, sort, deduplicate, interpolate, renumber channels or convert
  exposure/counts/units. Native preparation is the only permitted representation.
- Readiness cannot be unlocked by config, a finite mask or matching hashes.
- Tests must cover exact large integers, partial/empty/nonfinite data, chunk
  boundaries, malformed evidence, changed identities and portable CLI execution.

## Tasks

- [x] 1. Audit branch ancestry, source, tests, archive integrity, original
  PRADAN/tool/calibration identities and frozen provisional artifacts. Run an
  isolated baseline; record scientific/implementation reviewer findings.
- [x] 2. Add `data/solexs_quality.py`: `numerical_quality(native,
  expected_step, previous_coordinate=None)` and native GTI endpoint diagnostics.
  Write failing tests for missingness/anomaly separation, exact arithmetic,
  shape validation and cross-detector/source rejection; implement; verify.
- [x] 3. Add `data/solexs_interface.py`: immutable `NativeBatch`,
  `prepare_native_batch` and bounded `iter_native_batches`; refuse semantic and
  JEPA/training requests. Test dtype/value preservation, detached metadata,
  immutability, partial PI rows, empty GTIs and chunk-independent boundaries.
- [x] 4. Add a pinned native audit configuration and reusable offline readiness
  runner/CLI. Reverify scientific inputs, retain E1-E6 blocks, report numerical
  masks and lineage without arrays; reject tampered gates/config/inputs and
  existing output. Test relocated execution and deterministic reports.
- [x] 5. Run real two-archive native integrity/readiness audits and calibration
  preflight, verify documentation/calibration and provisional artifact identities,
  full tests, normal installed imports/CLI, preservation and ignore/history checks.
  Record DOCUMENTED/OBSERVED/INFERRED/UNKNOWN evidence and next readiness gate.
- [ ] 6. Independently review science and implementation, fix required findings
  with regression tests, reverify final source, commit and push only
  `codex/solexs-scientific-integration`; verify upstream/remote equality.

## Decisions

The user supplied the scope and authorized autonomous implementation and branch
publication. This plan records that scope without adding intermediate approval
gates. Historical Phase E/provisional reports and experiments remain unchanged.
The new interface does not reuse the provisional float64 conversion: reviewer
inspection found that it can round large integer inputs outside the frozen
floating pilot's domain. Existing scientific gates stay closed.

## Verification ledger

Tasks 1–5 passed. Task 6 implementation/scientific review and fixes passed;
final publication is the remaining action. See
`docs/SOLEXS_SCIENTIFIC_INTEGRATION_VERIFICATION.md` and
`data/manifests/solexs_scientific_integration.json` for executed results.
Logs remain under ignored `results/solexs_integration_audit/` in this worktree.
The explicit user instruction is push-only, without PR or merge. Final remote
equality will be checked after publication and reported in the handoff.
