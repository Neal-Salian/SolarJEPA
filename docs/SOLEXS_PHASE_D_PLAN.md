# Phase D research and verification plan

The user authorized SoLEXS timing, calibration and cross-instrument readiness
investigation. The deliverable is an evidence-based gate report and a precise
PRADAN acquisition plan, including a justified BLOCKED result when necessary.
This is an investigation of the existing scientific foundation, not a new data
pipeline design. Retained implementation depends on established semantics.

## Verified starting point

- Main/origin-main: `f9a0d2b7e266680234f70a9130edf83a45c04a13`, the user-managed
  Phase C merge. Its tree equals the final Phase C checkpoint `bc364dc`.
- Initial tree clean; Phase D branch absent locally/remotely after fetch.
- `data/solexs-timing-calibration` created from main and immediately published
  with upstream tracking before Phase D research.
- Actual baseline suite: 144 passed, one existing NumPy/netCDF warning.
- Official manual v1.0/January 2025 and updates dated June 9, 2026 accessible;
  original hashes agree with the Phase C manifest. Two original ZIPs exist;
  matching HK, complete RMF and July 2 are absent locally.

## Investigation sequence

- [x] Read applicable AGENTS.md; inspect refs/history, merged source/tests,
  dependencies/configuration/manifests and local scientific inputs/artifacts.
- [x] Verify clean synchronized main; check data protection; create/publish branch.
- [x] Re-read official documents and public primary sources with version
  applicability; preserve exact URLs/identities and conflicting definitions.
- [x] Reinspect the actual samples with retained Phase C access. Separate native
  clock/GTI/exposure observations from comparison hypotheses and accepted policy.
- [x] Establish FITS/OGIP time-keyword and leap-second context without treating a
  standard or another mission's convention as a pipeline-1.1 repair instruction.
- [x] Determine correction/HK/response requirements, exact candidate resource
  identities/sizes and date/software compatibility; do not apply unvalidated files.
- [x] Investigate PRADAN access and July 2 catalogue evidence. Authenticated browser
  access currently fails because computer-use permission is not granted; anonymous
  redirects and user-provided catalogue information must remain separately scoped.
- [x] Assess GOES prerequisites from actual inputs, metadata and official sources;
  include bin/clock/quality, observer-reference and band/flux compatibility.
- [x] Write a portable machine-readable acquisition/evidence record and the
  fourteen-part Phase D gate report. Preserve historical Phase C reports.
- [x] Add only justified reproducibility code, if needed; test meaningful new
  behavior and keep the native loader backward compatible. No presumed conversion.
- [x] Fresh regression/scientific checks, source identities, output determinism,
  raw ignore/index/history protection, portability and whole-branch review.

Final publication follows verification: focused Conventional Commits on the Phase D
branch only, feature-only push, fresh local/remote ref comparison and clean status.
Main integration, Phase E acquisition and dataset/model work remain user decisions.

The completed investigation is recorded in
[the Phase D gate report](SOLEXS_PHASE_D_GATE_REPORT.md). The result is BLOCKED
for historical acquisition; UNKNOWN timing/correction/calibration policies remain
unapplied. Native inspection is preserved. Independent review findings were
reproduced/verified and addressed within this milestone.

## Scientific and acquisition boundaries

Important claims use DOCUMENTED / OBSERVED / INFERRED / UNKNOWN. Native values,
missingness, clock cards and immutable lineage remain available. No automatic
UTC repair, GTI/exposure correction, channel-energy/flux conversion, flag creation,
interpolation, full alignment, training dataset, modeling or bulk acquisition.
Small essential public documentation/source/metadata reads are within this phase;
additional substantial scientific acquisition or a major architecture change
requires a concrete scope decision first.
