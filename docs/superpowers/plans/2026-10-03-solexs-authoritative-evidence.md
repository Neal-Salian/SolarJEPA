# SoLEXS D.1 evidence and acquisition plan

> **For agentic workers:** Use Superpowers executing-plans for authorized retained implementation, if evidence requires it. This milestone is presently an investigation; no new processing interface is justified by unresolved scientific semantics.

**Goal:** Determine whether authoritative evidence defines a reproducible timing,
exposure, correction and calibration contract for the obtained SoLEXS samples.

**Architecture:** Reuse the merged storage/native scientific layer and Phase D
probe. Keep original products immutable and downloaded resources ignored;
retain portable identities, resource dispositions and scientific findings.

**Tech stack:** Existing Python, standard-library archive access, Astropy and
NumPy; no new dependencies or interface framework.

**Spec:** The user's Phase D.1 contract; the fourteen starting requirements in
`data/manifests/solexs_phase_e_requirements.json`. Current evidence and the
remaining gate are in `docs/SOLEXS_PHASE_D1_REPORT.md`.

## Constraints and review focus

- Work only on `data/solexs-authoritative-evidence`, based on verified main
  `e1cfa8546b92d60aed5f187714a7aa304f3e1864`; no main integration.
- No historical bulk acquisition, dataset construction, alignment or models.
- No assumed clock repair, channel shift, HK substitution or correction policy.
- Catalogue observations are attributed; missing search results are not global absence.
- Preserve scientific unknowns and native NaNs, units, labels and lineage.
- Inspect compressed resources with limits; never install/execute downloaded tools.
- Review version matching, official versus candidate provenance, continuous versus
  point GTI semantics, conditional resource requirements and portable output.

## Evidence checkpoints

- [x] Read AGENTS.md first; inspect source/tests/configuration/CLIs/manifests,
  local products/artifacts and fetched Git history independently.
- [x] Verify clean synchronized main, merged C/D trees and baseline tests;
  create and immediately publish the D.1 feature branch with tracking.
- [x] Recheck local official manual/update versions and hashes; reproduce native
  validation and Phase D diagnostics against the immutable July 1/3 inputs.
- [x] Request one authenticated tools catalogue record, then its one exact package.
- [x] Verify supplied original size/hash/gzip, bounded TAR inventory, selected
  source/resource identities, FITS structure and candidate byte equivalence.
- [x] Request July 1 HK catalogue metadata, then follow its specific OtherDownloads
  pointer; preserve scoped negative results without inventing product identities.
- [x] Record all fourteen dispositions and a precise next mission clarification.
- [x] Record the user's sent timing/GTI/exposure request; reply remains pending
  and does not establish any scientific answer.
- [ ] Validate any subsequently supplied authoritative clarification/artifact
  before revising compatibility, timing or acquisition policy.
- [ ] Add retained code only if necessary to reproduce an evidence-justified
  inspection or prevent unsupported processing. For a behavior change, first
  reproduce it with a meaningful failing test, implement, then run affected and
  existing regressions; the native loader must remain compatible.
- [x] Fresh import/CLI/scientific/source/GOES checks, metadata portability and
  raw-data index/history review; review the whole checkpoint before publication.

Publication procedure: commit and push the reviewed evidence checkpoint only to
the feature branch; verify local/remote feature HEADs match and main remains
unchanged. Record executed publication/ref/status checks at the handoff, rather
than claiming them before the push completes.

The scientific gate is assessed independently of test success. A validated
BLOCKED_FOR_PHASE_E finding is a permitted research outcome. Only an adequately
evidenced READY_FOR_PHASE_E outcome permits drafting a historical acquisition
specification; neither outcome authorizes execution of Phase E or a main merge.
