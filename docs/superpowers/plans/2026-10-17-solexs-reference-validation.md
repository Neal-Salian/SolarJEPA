# SoLEXS release reference validation implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development. User has
> authorized investigation, justified implementation, independent review, commit
> and feature-branch push; execute within this scope without another plan gate.

**Goal:** Reproduce independently checkable release/tool behavior and native
numerical witnesses while retaining all scientific JEPA readiness blocks.

**Architecture:** Reuse the bounded native loaders and probe. Add an offline
reference validator and a small pinned reference manifest. Replay only reviewed,
exact-hash tools 1.1 functions on explicitly artificial inputs in isolated
temporary storage; never apply these algorithms to the real science products.

**Tech Stack:** Existing Python, NumPy, Astropy, pytest; no new dependencies.

**Spec:** User's 2026-10-17 continuation request; AGENTS.md; historical
docs/SOLEXS_SCIENTIFIC_INTEGRATION.md and Phase E evidence matrix. Investigation
reports in ignored results/solexs_reference_validation supply executable facts,
not a mission-approved contract.

## Global Constraints

- Work only in the existing isolated worktree on codex/solexs-scientific-integration,
  starting at 2b896c9. Commit/push only this branch. No PR, merge or main push.
- Preserve original inputs, prior reports, experiments and V1/V2 checkpoints.
- Never invent clock precedence, channel mapping, exposure correction, physical
  units, calibration approval, uncertainty, labels or model results.
- Distinguish DOCUMENTED, OBSERVED, INFERRED and UNKNOWN. Hash agreement proves
  identity, not mission applicability or independently authenticated acquisition.
- All E1–E6 statuses and training/physical conversion prohibitions stay in force.
- Raw inputs, extracted resources, synthetic FITS, runtime reports and caches stay
  ignored. Track only code, deterministic tests, small provenance and documents.
- One selected data release is July–September 2024 data1.1/pipeline1.1, released
  2025-02-14 per the supplied release notes. Tools1.1/CALDB1 is a separately
  identified release. Byte-equivalent resources from later tools are witnesses,
  not a claim of cross-release compatibility.

## Review Focus

- Changed pinned source/archive/member bytes must fail before replay/report.
- Reference agreement must never unlock physical conversion or training.
- Host timezone and current date must not change published diagnostic JSON.
- Native missing rows and unequal LC/PI numerical witnesses must remain visible.
- Endpoint/rebin examples must exercise actual pinned tools source rather than
  validating a locally duplicated formula against itself.

### Task 1: Executable tools and native release witnesses

**Files:**
- Create core module src/solar_flare_jepa/data/solexs_reference.py.
- Create scripts/validate_solexs_reference.py, a thin CLI.
- Create data/manifests/solexs_reference_cases.json, exact source/resource pins
  and small numerical expectations with source locators.
- Create tests/test_solexs_reference.py, artificial inputs only; no raw fixtures.
- If necessary, move existing probe helpers verbatim to a core module and keep
  scripts/probe_solexs_readiness.py as a backward-compatible wrapper/re-export.

**Interfaces:**
- Consume existing verified inventory/open_solexs_product/loaders and probe;
  reuse repository-relative path, duplicate-JSON and artifact publication guards.
- Produce an offline reference report with complete input/member/code identities,
  explicit case results, unknowns and readiness prohibitions. Existing-output
  publication must be refused. Native full-row probe may be reused with separately
  labeled release/candidate identities; do not conflate releases.

- [ ] Write failing deterministic tests before implementation; use the existing
  isolated results/solexs_integration_runtime/bin/python. Reproduce failure and
  record red/green commands/results in the implementer report.
- [ ] Bind replay to the supplied official tools1.1 TAR and its reviewed member
  SHA256 values in Phase D.1. Use bounded selected regular-member reads, no setup.py
  execution, no general extraction or installation. A temporary caldb_config
  adapter may point to copied pinned CALDB; identify that adapter in the report.
  Use subprocesses for timezone isolation and temporary outputs; source replay is
  explicitly tool behavior, not pipeline reconstruction or science processing.
- [ ] Execute the actual genlc/rebin/writer and genspec functions with artificial
  fixed time/count/channel/exposure arrays. Assert epoch helper UTC round-trip;
  None versus explicit time_bin=1; odd/even rebin and dropped remainder; integer
  FITS timestamp truncation; timezone-dependent DATE-OBS under UTC and Asia/Kolkata;
  closed GTI endpoint versus half-open request interval; stop clamping excludes
  final TSTART row; preserved native labels and summed stored EXPOSURE. No physical
  or uncertainty interpretation of artificial outputs is permitted.
- [ ] Add a native witness against the existing selected July1/3 files: 86400 rows
  each; finite rows 86272/86398; missing rows128/2; channels0..339; RMF1..340;
  LC/PI band equality remains false. Existing tool slice41:313 has equal rows
  86253/86383 and inclusive-upper41:314 has86258/86393, max residual1 for both;
  all-channel max residual695/661 and zero equal rows. Pin the observed facts and
  their provenance, compare exact expected observations, fail on disagreement.
- [ ] Keep HDU-specific timing cards/units and unknown correction state in native
  evidence. Do not select a preferred clock, renumber channels, filter GTIs, divide
  by exposure, repair timestamps or convert quantities. Unitless encoded COUNTS
  stays null, stored EXPOSURE/TELAPSE1 does not establish live exposure.
- [ ] Test malformed/duplicate manifest, changed source/member bytes, unequal
  native expectations, missing inputs, unsafe paths, immutable input preservation,
  chunk-independent native results, timezone-stable report and existing-output
  refusal as appropriate to the implementation. Tests can mock the replay boundary
  for malformed-input checks; real acceptance must replay pinned source.
- [ ] Run relevant tests and self-review. Commit focused verified implementation
  with a Conventional Commit. Do not push; root coordinates review and publication.

### Task 2: Scientific evidence, readiness and independent acceptance

**Files:**
- Create docs/SOLEXS_REFERENCE_VALIDATION.md and a small dated evidence manifest.
- Update docs/PROJECT_STATUS.md only where needed to link current verified state.
- Preserve historical reports/manifests unchanged.

- [ ] Run actual reference replay and native audit/probe, reproduce deterministic
  JSON, verify normal installed imports and CLI from another working directory.
- [ ] Obtain independent spec/quality review of Task1 and independent scientific
  whole-change review; fix material findings with covering tests and scoped review.
- [ ] Run relevant/full suite, inspect final diff/whitespace/index/history/ignore
  policy, verify preserved input/checkpoint identities and source provenance.
- [ ] Report resolved numerical/tool questions, unresolved mission applicability,
  exact readiness verdict and next evidence milestone. Record commands actually run.
- [ ] Commit evidence; push verified commits only to the existing feature branch;
  verify local/upstream/remote equality and unchanged main. Retain worktree.
