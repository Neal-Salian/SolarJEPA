# Phase C scientific access contract

This contract follows the verified repository audit, original reconnaissance,
official PRADAN manual/release-note reconciliation and complete sample PI probe.
The user authorized Phase C and directed unresolved semantics to remain explicit.
The evidence permits a lossless native-product foundation; physical/time/QC
transformations stay at the scientific gate. The original archives and registration
inventory remain immutable. This contract constructs no downstream dataset.

## Representation and boundary

Add `solar_flare_jepa.data.solexs` beside the existing storage/inspection modules.
Reuse `storage.validate_inventory`, `verify_inventory` and root-containment rules;
use already-pinned Astropy, NumPy and the standard library. No dependency changes,
GOES changes, UI, network access or calibration execution are needed.

- `open_solexs_product(root, record, member, *, limits=AccessLimits())` is a
  context manager yielding identified FITS HDUs and source/member/payload identities.
  It verifies registered source bytes, rejects unsafe/unsupported inputs, streams
  nested gzip to a unique ignored temporary directory, caps gzip input at 16 MiB
  and FITS output at 512 MiB, verifies checksums when present, and removes scratch
  data on success and failure. FITS access is readonly and memory mapped.
- Product kind is established from FITS HDUs/required fixed-width columns, with
  L1 archive/member agreement and cross-HDU instrument/detector consistency
  checked. Variable-length columns are unsupported and fail before payload
  loading. Missing detector cards remain explicit
  filename-based INFERENCE, never silently OBSERVED. Unsupported layouts fail.
- `load_light_curve(product)` and `load_gti(product)` return copied native arrays,
  encoded column units including nulls, original clock cards, warnings and
  kind/detector/source provenance. Cap
  these eager products at 1,000,000 rows. Preserve NaNs, unusual counts and invalid
  GTI diagnostics. Do not filter, fill, resample, shift epochs, repair headers or
  assign physical quantities based on names.
- `iter_spectra(product, *, chunk_rows=1024)` yields bounded copies of all six
  native Type-II columns. Validate scalar/vector dimensions and DETCHANS; preserve
  channel numbering/counts/exposure without energy mapping or response correction.
  Remove cached FITS column bindings before closing the file so Astropy does not
  retain complete table copies. Caller-held HDUs/views remain context scoped.
- `inspect_solexs_archive(root, record, *, limits=..., chunk_rows=1024)` returns
  deterministic compact metadata, full integrity status, dimensions, numeric/time/
  GTI quality summaries and measured expanded/table sizes. It serializes no full
  observation arrays and no scratch/host paths. Native times are numeric; all
  UTC, continuous exposure, GTI filtering and calibration policies remain unapplied.
  Compare LC/PI coordinates and sums only as native diagnostics; quantity
  equivalence remains UNKNOWN. Inclusive GTI membership is a pointwise diagnostic,
  never a scientific filter. Exact integer/mixed numeric diagnostic arithmetic
  must avoid wrapping or silently equating distinct stored values.
- `scripts/validate_solexs.py` consumes the existing explicit storage config and
  inventory; it writes the ignored report under `results/`. It performs no network
  access or acquisition. Installed CLI behavior must work outside the checkout.
  Publish reports by atomic replacement so a hard-linked report cannot overwrite
  an original archive; failed validation preserves an existing report.

Documented Unix/UTC conventions, LC band/rate, PI integration start and GTI criteria
are evidence definitions in the scientific report. Encoded FITS metadata and
version conflicts remain separate. The API does not convert timestamps even where
the manual defines an epoch. LC bin position, GTI endpoint duration and correction
applicability are unresolved; absolute chronology/physical spectra stay gated.

## Verification and failure rules

Synthetic gzip/FITS-in-ZIP fixtures exercise source identity, limits, corruption,
malformed/mismatched schemas, detector conflict/inference, missing cards and units,
invalid GTIs, missing values, spectra chunking, deterministic/portable summaries,
and cleanup. No real scientific products are tracked as fixtures. Every retained
behavior has a failing test before implementation. Scientific anomalies become
diagnostics; corrupted containers/checksums and incompatible layouts raise errors.

Fresh verification covers full/targeted tests, normal installation/import/CLI,
both complete samples, report determinism and relocation, GOES regressions,
dependency integrity, immutable hashes, actual ignore rules, index/history scanning,
diff/status and independent whole-branch review. Commit/push only the Phase C branch;
main integration and any next milestone require the user's separate decision.
