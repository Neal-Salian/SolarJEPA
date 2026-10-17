# SoLEXS release reference validation

Evidence date: **2026-10-17, Asia/Kolkata**. Continuation from `2b896c9` on
`codex/solexs-scientific-integration`. This report supplements the historical
[native integration report](SOLEXS_SCIENTIFIC_INTEGRATION.md) and
[Phase E evidence matrix](SOLEXS_PHASE_E_EVIDENCE_MATRIX.md); it does not rewrite
their findings or authorize a new experiment.

**Scientific JEPA integration remains blocked.** Reproducible native observations
and executable analysis-tool behavior do not establish mission clock precedence,
applicable calibration, effective exposure, physical flux or forecast readiness.

## Selected releases and provenance

**DOCUMENTED:** the supplied release notes, updated 2026-06-09, identify the
2025-02-14 release of July–September 2024 **L1 data 1.1 / processing pipeline 1.1**.
They separately identify **analysis tools 1.1**. This audit selects the existing
registered July 1/3 SDD2 samples and the original tools 1.1/CALDB 1 bundle. It does
not claim that the analysis tools generated these L1 files.

The release notes describe timestamp changes in pipeline 1.1 and later
DATE-OBS/DATE-END/MJDREF changes in pipeline 1.2. Those statements do not specify
which disagreeing card or column governs these pipeline 1.1 bytes.

**OBSERVED:** the immutable original tools TAR contains the reviewed source,
SDD2 bounds, ARF and RMF. Its RMF is byte-identical to the later-source RMF used
in the earlier probe. A coherent single-bundle reference is therefore possible
without adopting a later correction algorithm or the later `arf_pi` resource.

| Input | SHA-256 |
| --- | --- |
| July 1 ZIP | `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4` |
| July 3 ZIP | `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf` |
| Original tools 1.1 TAR | `348014aefa50ade556ec4a160a3cfe0b08095bde84b4650a27d6b5d3bf7fa2d3` |
| User manual v1.0, January 2025 | `d97c83618c85a0984e7dd0300ce5c16c4748ed5facde525949f902fe9f72abda` |
| Release notes | `7fc0229985fef2bd60ab23bc554c09e64f526719f11825e44a60eed12f5396ce` |

The original PRADAN acquisition is **user-reported**. Local hashes and matching
public source bytes establish identity; they do not independently authenticate
the protected portal download. No new science archive or HK product was acquired.

Primary sources checked include the [URSC instrument page](https://www.ursc.gov.in/SoLEXS.jsp),
the [exact author tools 1.1 source](https://github.com/abhilash-sw/solexs_tools/tree/24693afeeab5f67ce0277fe84de059bbe54223cb),
[OGIP response definitions](https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/docs/memos/cal_gen_92_002/cal_gen_92_002.html),
and the [versioned instrument calibration paper](https://arxiv.org/html/2509.26292v2).
The locally pinned manual/release notes and earlier FITS/OGIP references were
read alongside these sources. The protected manual endpoint was not anonymously
retrievable. The bounded search found no new applicable clock/indexing erratum;
that does not establish that no such document exists.

## Scientific findings

**DOCUMENTED:** manual §2.2 defines Unix seconds from UTC midnight at the 1970
epoch; §2.1.3 calls PI TSTART the integration start. It describes TELAPSE as the
one-second integration and EXPOSURE as effective integration after deadtime
correction. Its dated processing description says correction was not applied
and EXPOSURE equals TELAPSE. LC COUNTS is described as counts/s. These generic
definitions must be kept separate from the actual encoded metadata and the
unknown correction state of an individual release.

**OBSERVED:** LC has MJDREFI40587, MJDREFF0.22916666651, TIMESYS UTC,
TIMEREF LOCAL and DATE-OBS05:30. PI time columns encode seconds, while its table
lacks those clock-reference cards. GTI primary TSTART is midnight with `+00:00`;
its extension lacks the LC clock cards. TIMEPIXR is absent. `TIMZERO` is present
in LC; this is not a license to treat it as the distinct `TIMEZERO` keyword.

**INFERRED:** interpreting the native first coordinate using the manual's Unix
convention yields midnight; including the encoded fractional MJD reference adds
approximately 5.5 hours. Reproducing similar writer behavior explains a possible
mechanism, not the generating pipeline or an approved repair. **UNKNOWN:**
absolute precedence, corrections/error, actual LC bin support/completion and
causal availability. No absolute UTC conversion is accepted.

**OBSERVED:** the exact tools 1.1 source has useful software witnesses:

- `time_utils` converts numeric input with explicit UTC. Its inverse appends an
  offset unconditionally and rejects the already offset-bearing output of its
  forward helper; the reference distinguishes that rejection from a successful
  inverse call using a timezone-free string interpreted by the helper as UTC.
  The LC writer uses the host timezone for DATE-OBS while retaining a fixed
  fractional MJD reference.
- Explicit `time_bin=1` shifts intended centers by 0.5 before an integer FITS
  writer truncates them; omitted binning retains the input coordinates. Stored
  integer TIME can hide a difference still visible in header TSTART.
- Odd rebin sizes produce fractional centers; incomplete trailing blocks are
  discarded. Native L1 LC uses double TIME, so this writer is not proof of its
  pipeline implementation.
- Spectral extraction uses closed GTI point membership and a half-open requested
  range. A requested stop beyond the maximum TSTART is clamped to that maximum;
  the final stored row is excluded. This is a pinned tools behavior, not a
  continuous-exposure rule to adopt.
- Spectral extraction preserves input channel labels and adds stored EXPOSURE.
  These operations do not certify channel correspondence or live exposure.

These observations are independently reproducible from the pinned
[LC source](https://raw.githubusercontent.com/abhilash-sw/solexs_tools/24693afeeab5f67ce0277fe84de059bbe54223cb/solexs_tools/solexs_genlc.py)
and [spectral source](https://raw.githubusercontent.com/abhilash-sw/solexs_tools/24693afeeab5f67ce0277fe84de059bbe54223cb/solexs_tools/solexs_genspec.py).
Artificial reference fixtures are software checks, not additional observations.

| Native numerical witness | July 1 | July 3 |
| --- | ---: | ---: |
| LC/PI rows each | 86400 | 86400 |
| Finite LC / fully finite PI rows | 86272 | 86398 |
| All-NaN PI rows matching LC NaNs | 128 | 2 |
| Exact LC matches to tools slice 41:313 | 86253 | 86383 |
| Exact matches to inclusive-upper control 41:314 | 86258 | 86393 |
| Maximum absolute residual, either slice | 1 | 1 |
| All-channel matches | 0 | 0 |
| All-channel maximum absolute residual | 695 | 661 |

**OBSERVED:** the inclusive-upper control resolves some differences but leaves
others. For example, July 1 zero-based row 1933 has LC 32 versus 31 from both slices;
row 21594 has LC 19, tools 18 and control 19. July 3 row 16974 has 17 versus 16/16;
row 3580 has 48 versus 47/48. **UNKNOWN:** the remaining band-generation semantics.
An endpoint change alone does not establish equivalence.

**OBSERVED:** PI labels are 0..339; the original bundle RMF EBOUNDS labels are 1..340,
with TLMIN1=1 and MATRIX F_CHAN starting at 1. RMF shape is 2250×340 and its cells
are finite/nonnegative. ARF energy bounds encode keV and SPECRESP encodes cm2;
both response products record creator pipeline 1.0. **DOCUMENTED:** OGIP requires
channel correspondence and distinguishes nominal channel bounds from incident
response energies. **UNKNOWN:** approved indexing and detector/epoch/gain/pipeline
applicability. Neither equal widths nor a common filename authorizes adding 1.

**DOCUMENTED:** manual §4.5.1 describes delivered-channel grouping, but does not
give an explicit native-to-RMF label offset. Its dated §4.5.2 warns that the CALDB
is not optimized below 2.8 keV; §4.5.4 provides model/systematic guidance. Those
statements do not supply a measured uncertainty or an approved correction for
these two files. They remain relevant limits for a later physical reference.

**OBSERVED:** COUNTS has no encoded TUNIT in the inspected native products.
EXPOSURE=TELAPSE=1 even on missing PI rows. No HK member is present in either ZIP;
the acquired sample has no matching HK product. **UNKNOWN:** effective live
exposure, applicable health/saturation rules, correction state and any required
HK schema/mode/clock association. Missing HK is a conditional blocker for an
HK-dependent correction workflow, not proof that HK is unnecessary or unavailable
mission-wide. Later tools and the instrument paper cannot certify this release.

Dividing counts by ARF, applying a speculative channel offset, importing a later
deadtime correction, assigning a fixed Poisson/systematic uncertainty, or treating
counts/s as photon flux or W/m² remains unsupported. Response-aware physical
analysis requires an applicable, validated forward model and correction contract.

## Executable reference contract

The [reference manifest](../data/manifests/solexs_reference_cases.json) pins the
original bundle/member identities, documentary sources, registered inputs and
small expected witnesses. The validator checks the actual reviewed source on
artificial fixtures in fresh UTC and Asia/Kolkata subprocesses. It supplies an
explicit temporary `caldb_config` adapter; it does not run `setup.py` or install
the external tools. The known bundle/source allowlist cannot be changed merely
by repinning a different package in the manifest.

The native reference separately scans the real selected rows with existing
bounded loaders. It checks numerical summaries, selected row hashes, units and
HDU-specific cards against the independently inspected witnesses. It fails on
input or expected-value disagreement before publishing. Passing means agreement
with this reference, including its incompatibilities and unknowns.

With the original ignored inputs present and the project normally installed:

```bash
python scripts/validate_solexs_reference.py \
  --output-dir results/experiments/solexs-release-reference-local
```

`--data-root` supports a relocated input tree with the same relative paths;
`--chunk-rows` controls bounded PI access. Output directories must be new.
Reports record source/runtime/input identities, artificial replay results and
native evidence. Current creation dates and temporary paths are excluded from
the semantic reference output. They do not acquire scientific meaning by being
reproducible.

## Verification of the final implementation

Executed source commit: `c7ea3c90c215012d47b7eed8d6a71bcb9cca3420`.
Later evidence/documentation commits retain the executable source fingerprint
`dbcc4e5907b67640a611435300b666850a33cb28445882ff1946c2dccc9a9588`.
Detailed identities are in the
[dated verification manifest](../data/manifests/solexs_reference_validation.json).

| Executed check | OBSERVED result |
| --- | --- |
| Inherited full suite before changes | 1211 passed, one inherited warning, 84.98 s. |
| Final full suite after both review fixes | 1262 passed, same warning, 93.90 s. |
| Final reference plus legacy-probe tests | 73 passed; 51 new reference regression cases in total. |
| Exact original tools source replay | Artificial fixtures matched the reviewed oracle under UTC and Asia/Kolkata. No native science file entered the tools. |
| Normal installed CLI from `/tmp` | Passed with matching checkout/installed source; 61 executable/configuration provenance files captured. |
| Changed host timezone and chunk size | Full reference report byte-identical. |
| Relocated input tree, another chunk size | Full report byte-identical; nine pinned input files copied without source mutation. |
| Existing output | Refused before replay; prior report identity unchanged. |
| Atomic artifact indexes | All three reference indexes and the new native-audit index verified. |
| Existing native preparation and exploratory probe | Passed; eight complete products and 39 documentary/calibration source identities checked by the native audit. |
| Preservation | 52 input files, 13 original checkpoints and 319 artifacts across 32 historical experiment indexes matched their recorded identities. |
| Git/data policy | Actual raw/results paths ignored; no prohibited science-data paths in the index/reachable history; whitespace checks passed. |

The final three reference reports share SHA-256
`d0f72043336917a4c847cc2985ade6d70c23e87b5fb7a44829d4493227c348b5`.
Their ignored output directories are
`results/experiments/solexs-release-reference-20261017-final`,
`...-final-reproduction`, and `...-final-relocated`.
Runtime: Python 3.13.3, NumPy 2.2.6, Astropy 8.0.1. The final full suite was run
with `results/solexs_integration_runtime/bin/python -m pytest -q`. Acceptance
used the same normally installed runtime from outside the checkout; no test
`src` injection was used for those CLI runs. Full tests include inherited small
artificial-model fixtures, not retraining of V1/V2 or the real SoLEXS pilot.

The inherited netCDF4 import warning remains visible:
`numpy.ndarray size changed, may indicate binary incompatibility`.
These results do not establish ABI safety; dependencies were not upgraded or
the warning suppressed in this milestone.

Independent review found two fail-closed gaps before publication: empty nested
expectations could produce vacuous agreement, and release/approval metadata
could change separately from the numerical witnesses. Failing regressions
preceded both fixes. The complete reviewed expectations and both release records
are now bound into a code-owned canonical contract. Source and scientific
reviews verified the fixes; no operational science permission was opened by
either issue or its correction.

## Readiness gates and next milestone

| Gate | Current verdict | Evidence still needed |
| --- | --- | --- |
| E1 timing | BLOCKED_EXTERNAL_EVIDENCE | Release-specific card precedence, bin support/completion, GTI clock/endpoints and time error/corrections, with boundary reference output. |
| E2 calibration | BLOCKED_EXTERNAL_EVIDENCE | Approved SDD2 response identities, native/response channel correspondence, epoch/gain/pipeline applicability and numerical reference. |
| E3 exposure/quality | BLOCKED_EXTERNAL_EVIDENCE | Applicable quality, bin/GTI and effective-exposure rules; paired HK and approved correction reference if required. |
| E4 detector/product | PARTIALLY_VERIFIED | SDD2 structure verified; LC-band quantity equivalence and task selection remain unresolved; SDD1 LC/PI absent. |
| E5 GOES compatibility | PARTIALLY_VERIFIED | Common calibrated quantity and response/observer/time-bin conventions; no numerical conversion or alignment accepted. |
| E6 forecasting | BLOCKED_EXTERNAL_EVIDENCE | E1–E3, causal target/availability, uncertainties, labels as applicable, and sufficient independent chronological coverage. |

The next actionable milestone is a **mission-approved single-release boundary
and response/exposure reference**: resolve the observed clock and channel
discrepancies, identify the applicable correction workflow, and validate it
against supplied input/output examples. If the mission selects a newer release,
preserve this 1.1 evidence and authorize that bounded input selection separately.
Only after those gates close should a future authorized milestone define JEPA
features, causal windows and chronological evaluation. No model retraining or
checkpoint change is part of this work.

The evidence covers the two named samples and the exact reviewed bundle. It does
not establish other releases, additional detectors with real spectra, unknown HK
schemas, independently authenticated portal provenance, or behavior across other
dependency/platform combinations. Source reproduction and byte-identical reports
in the recorded runtime are narrower claims than cross-platform reproducibility
or scientific calibration accuracy.
