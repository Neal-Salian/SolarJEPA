# Phase D.1 — SoLEXS authoritative evidence and calibration acquisition

Evidence checkpoint: **2026-10-03 (Asia/Kolkata)**; public source access on
2026-10-02/03 UTC. Branch: `data/solexs-authoritative-evidence`. The official tools
bundle has been obtained and inspected. The scientific gate remains blocked;
mission-specific timing/exposure and correction/response guidance is still needed.
This is an ongoing evidence milestone, not permission for historical acquisition.

## 1. Verified repository and Git starting state

The actual root AGENTS.md was read first. After fetching origin, clean main and
origin/main both pointed to `e1cfa8546b92d60aed5f187714a7aa304f3e1864`, the
user-managed Phase D PR merge. Its tree equals Phase D's final `cd6f9c5` tree.
The D.1 branch was absent locally/remotely, created from that main and immediately
published with upstream tracking. Main and the meaningful C/D branches are preserved.

Inspection covered source, tests, dependencies, configs, manifests, seven CLIs,
scientific inputs and generated artifacts. The baseline suite ran: **166 passed,
one existing NumPy/netCDF4 warning**. Registration, bounded native access and the
Phase D probe were then rerun against the real samples, rather than inferred from
status prose. No source/dependency changes are currently justified.

| Existing functionality | Verified disposition |
|---|---|
| ZIP registration; native LC/GTI and chunked PI access | VERIFIED by merged source/tests and complete actual-sample execution. |
| Phase D response/band/native-row diagnostics | VERIFIED; reproduced output is byte-identical to the preserved Phase D result. |
| Official manual/release notes and 36 C/D source pins | VERIFIED local identities; version applicability remains separately assessed. |
| Official tools bundle identity | MISSING locally at the base; now OBSERVED from the supplied intact package. |
| Approved UTC, continuous exposure and correction/response contract | UNKNOWN scientifically; no implemented repair/calibration is approved. |
| Matching July 2024 HK | MISSING from inspected local inputs; official availability remains UNKNOWN. |
| Final dataset, alignment, models and frontend | PLANNED/DOCUMENTED ONLY, outside D.1. |

README/current status still described D awaiting integration despite the verified
merge; current summaries are corrected. Historical C/D reports and the original
acquisition/checklist manifests retain their dated scope.

## 2. Authoritative sources and version applicability

DOCUMENTED denotes an authoritative definition within its applicability;
OBSERVED denotes actual bytes/execution, including explicitly attributed user
catalogue observations. INFERRED denotes a derivation; UNKNOWN remains unestablished.

| Source | Version/identity and applicability |
|---|---|
| PRADAN SoLEXS User Manual | v1.0, January 2025, 19 PDF pages, 363,311 bytes. Generic product definitions; predates the 1.1 re-release. |
| PRADAN SoLEXS_Release_Updates.txt | Updated 2026-06-09, 2,481 bytes. Explicit July–September 2024 data/software lineage; no deterministic clock precedence rule. |
| Supplied PRADAN solexs_tools-1.1.tar.gz | 19,730,838 bytes. Inspected outer package metadata declares tools 1.1 and CALDB 1. Applicability is not implied by those numbers; nested distributions are not recursively inspected. |
| Pinned author tools/workshop | C/D source manifests preserve exact commits. Selected 1.1 source bytes now match the official download; newer 1.3/1.6 workflows still have unvalidated backwards compatibility. |
| FITS 4.0 / OGIP CAL/GEN/92-002 | Standard timing and response context, not mission-specific repair authority. |
| [URSC instrument page](https://www.ursc.gov.in/SoLEXS.jsp) | States last update 2026-06-22; broad detector/cadence capability, not pipeline-1.1 field or correction policy. |
| [PRADAN contacts](https://pradan1.issdc.gov.in/al1/contacts.xhtml) | Undated official contact route, locally pinned; not a scientific answer. |

The [D.1 evidence manifest](../data/manifests/solexs_phase_d1_evidence.json)
pins the new resources, complete small TAR metadata inventory and selected-member
hashes/lineage. It links the unchanged C/D source manifests. Official portal origin
is attributed to the user's downloads; local bytes are directly verified, without
an independently supplied portal checksum. No downloaded software was installed
or executed, and the agent sent no external message.

## 3. Fourteen-resource disposition

The [complete acquisition audit](../data/manifests/solexs_phase_d1_requirements.json)
records purpose, requirement/condition, dates, target data/pipeline versions,
observed resource versions, source/authentication, local identities/sizes,
compatibility, evidence and exact remaining action for every original entry.

A = AVAILABLE_AND_VALIDATED; B = AVAILABLE_NEEDS_COMPATIBILITY_VALIDATION;
C = REQUIRES_PRADAN_DOWNLOAD; D = REQUIRES_OTHER_OFFICIAL_DOWNLOAD;
E = REQUIRES_DOCUMENTATION_OR_CLARIFICATION; F = CURRENTLY_UNAVAILABLE;
G = NOT_ACTUALLY_REQUIRED. There are **7 B, 6 E, 1 G**. No A is claimed for
an unresolved scientific compatibility requirement; no F is inferred from access
restrictions or a scoped unsuccessful search.

| Requirement ID / exact name when established | Disposition | Exact next action and condition |
|---|---|---|
| pipeline_1_1_timing_policy; filename UNKNOWN | E | Await the requested clock/bin/GTI/exposure specification or erratum and validate its applicability. |
| approved_tools_caldb_bundle; solexs_tools-1.1.tar.gz | B | Obtain mission applicability/correction guidance; do not download another copy merely for identity. |
| matching_sdd2_housekeeping; July filename UNKNOWN | E | Identify an approved HK-dependent workflow and its exact July HK route/schema before requesting a file. |
| caldb_index; public candidate caldb_index.json | B | Confirm selection/date-validity policy; this JSON is required only by a workflow that uses it. |
| sdd2_redistribution; solexs_gaussian_SDD2_v1.rmf | B | Resolve PI/RMF indexing, epoch and version applicability with an authoritative rule/reference. |
| sdd2_effective_area; solexs_arf_SDD2_v1.arf | B | Approve detector/epoch/pipeline pairing with the RMF for physical spectra. |
| pi_energy_bounds; energy_bins_out_SDD2_v1.dat | B | Approve indexing/energy lineage; equivalent approved EBOUNDS may suffice. |
| deadtime_parameters; candidate solexs_deadtime_params_SDD2_v1.fits | B | Identify approved mode/units/schema/epoch; two local variants differ. Conditional on the correction method. |
| pi_grid_effective_area; candidate solexs_arf_pi_SDD2_v1.arf | B | Determine whether this newer band-flux workflow is needed and compatible. |
| gain_temperature_provenance; filename UNKNOWN | E | Establish L1 calibration already applied and whether separate coefficients are required. |
| quality_background_and_correction_reference; filename UNKNOWN | E | Obtain approved correction-state/quality and a small numerical reference; additional background is conditional. |
| observer_reference_spice; exact kernels UNKNOWN | E | Clarify any native clock requirement; defer observer/light-time resources until an approved later reference convention. |
| alternate_validated_science_pilot; filename/version UNKNOWN | E | Only request a bounded mission-recommended alternative if the existing version cannot be validated. |
| sdd1_coverage_reason; optional resource UNKNOWN | G | Not needed for this SDD2-only gate; preserve UNKNOWN cause and reactivate if SDD1 becomes required. |

The starting checklist was not treated as fourteen mandatory downloads. Conditional
index, PI-grid ARF, gain, background, SPICE and alternate-data requirements remain
conditional; an available public candidate does not imply an approved resource.

## 4. Timing evidence and conflicts

**DOCUMENTED:** manual §2.2 defines Unix seconds from 1970-01-01 00:00:00 UTC;
§2.1.3 defines PI TSTART as integration start. Release notes explicitly associate
the July–September re-release with data/processing 1.1 and UTC-consistency updates,
and record later processing-1.2 updates to date/MJD cards. Neither gives the exact
pipeline-1.1 conflict resolution rule or LC bin position.

**OBSERVED:** actual native LC TIME equals PI TSTART at all 86,400 rows per sample,
with increment 1 and no duplicate/nonmonotonic coordinates. Native bounds are
1719792000–1719878399 and 1719964800–1720051199. LC date cards instead begin at
05:30:00; MJDREFI=40587, MJDREFF=0.22916666651, TIMESYS=UTC, TIMEREF=LOCAL,
TIMEUNIT=s, TIMZERO=0. PI lacks epoch/date cards; GTI has no encoded time unit.

**OBSERVED:** official time_utils.py uses an explicit UTC datetime conversion.
Its README labels input 1707715800 as 11:00, while independent UTC projection
gives 05:30+00:00. The official LC/spectrum writers still use timezone-dependent
fromtimestamp calls; the LC writer hardcodes the same fractional MJD reference.
These bytes match the legacy candidate, so the conflict is now observed in the
officially acquired tools, not only a public candidate.

**OBSERVED, user-attributed:** the July 1 catalogue displays a UTC-labelled
midnight–23:59:59 envelope for the matching ZIP. **INFERRED:** that envelope
agrees with the manual's Unix projection of native coordinates. **UNKNOWN:**
whether catalogue envelopes define row chronology, TIME/card precedence, LC bin
placement, mission leap/clock convention and clock uncertainty. No accepted UTC
column or repair rule is produced.

## 5. GTI and exposure evidence

**DOCUMENTED:** the generic manual's GTI criteria concern Sun-in-FOV,
operational/health conditions; PI EXPOSURE is intended effective exposure, but
the guide states that deadtime correction is not currently applied.

**OBSERVED:** July 1/3 SDD2 GTIs have 4/3 intervals. Sum(STOP−START) is
86,268/86,395 in native coordinates, while EXPOSURE strings are 86,272/86,398.
Inclusive point membership exactly matches finite LC samples; the remaining
128/2 LC rows are NaN, with identical all-NaN PI row masks. All PI TELAPSE and
EXPOSURE values are 1, including NaN rows.

**OBSERVED:** official genspec.py selects native GTI sample coordinates using
START ≤ TSTART ≤ STOP, requested windows using tstart ≤ TSTART < tstop, and sums
selected per-row EXPOSURE. It clips a requested stop above the final coordinate
to that coordinate, which would exclude the final row under its half-open window.
Those are inspected helper operations, not an approved continuous filtering rule.

**INFERRED:** GTI endpoints likely label included integration-start samples in
these products. **UNKNOWN:** mission-approved continuous bin boundaries, partial
exposure, version applicability and whether that helper is the intended correction
chain. Native GTIs and per-row exposure remain unchanged.

## 6. HK and correction evidence

**OBSERVED:** neither ZIP contains HK. The inspected outer Tools-1.1 source/CALDB
tree has no HK resource, deadtime module/parameter FITS, PI-grid ARF or
caldb_index.json; its spectrum helper aggregates input counts/exposure without
an HK correction. Nested distribution contents were not recursively inspected.
These scoped absences do not establish global unavailability.

**OBSERVED, user-attributed:** a Filename Contains 20240701 search returned one
AL1_SLX_L1_20240701_v1.1.zip record and no separate HK entry. Its OtherDownloads
pointer displayed only the same tools/manual/updates entries, without an HK
resource or July-specific HK coverage. The ancillary route URL was not supplied
as an actual URL, so it is null in the audit. No new science ZIP was downloaded.
The external AL1_SLX catalogue naming must be distinguished from the actual
AL1_SOLEXS member names and newer workshop naming template.

**UNKNOWN:** which HK product/version applies, whether it is retrievable through
another route, pipeline-1.1 correction state and the required corrected/uncorrected
representation. Newer public tools/workshop HK requirements do not certify this
older pipeline. No substitution or correction is applied.

## 7. Calibration and response evidence

**DOCUMENTED:** manual §2.4 identifies ARF/RMF in tools CALDB as essential for
physical spectral interpretation; L1 PI is described as energy-calibrated, which
does not by itself mean calibrated incident flux. This generic definition does
not settle additional pipeline-1.1 gain/correction requirements.

**OBSERVED:** the outer package's CALDB tree contains exactly three regular files:

| Resource | Bytes | Structural finding |
|---|---:|---|
| solexs_gaussian_SDD2_v1.rmf | 6,168,960 | EBOUNDS 340 channels; MATRIX 2,250 × 340 doubles, finite and nonnegative. |
| solexs_arf_SDD2_v1.arf | 34,560 | 2,250-row SPECRESP; keV energy grid and cm2 area; incident grid exactly matches RMF MATRIX. |
| energy_bins_out_SDD2_v1.dat | 6,423 | 340 two-column rows; no unit encoded in the text. |

All three match existing Phase D candidate bytes. ARF/RMF CREATOR is
solexs_pipeline-1.0. Their FITS structure verifies; checksum cards are absent,
so no FITS checksum validation is claimed for these calibration files. The
official source identity is now established, while detector/epoch/pipeline
applicability, gain lineage and physical-flux interpretation remain UNKNOWN.

## 8. Native PI versus response channels

**OBSERVED:** sample PI CHANNEL is 0–339. The official bundle RMF EBOUNDS is
1–340 with TLMIN1=1, and MATRIX F_CHAN/TLMIN4 is 1 with N_CHAN=340. The official
spectrum helper copies the native channels unchanged and writes unindexed
TLMIN/TLMAX cards; it supplies no documented index reconciliation rule.

**UNKNOWN:** an approved mapping or response reader convention that establishes
the association for these exact products. A 340-row coincidence and paired energy
grids are insufficient. No +1 operation, energy relabelling, response application
or physical-flux result is exposed. The native PI remains accessible as before.

Official genlc uses the same strict bounds/exclusive-stop algorithm inspected in
Phase D. Its nominal 2–22 slice still disagrees with native LC on 19/15 finite rows;
the inclusive-upper control disagrees on 14/5. These are numerical observations,
not proof of an LC band definition. NUMBAND interpretation remains UNKNOWN.

## 9. July 2 status

The user previously reported that an authenticated July 2 query returned
“File not found.” This remains an attributed OBSERVED result of that query,
with UNKNOWN applicable product availability/reason. The newer July 1 search
clarifies catalogue naming but does not reclassify the July 2 result. July 2 is
missing from the obtained collection; no interpolation, observation or negative
label is fabricated.

## 10. Resources acquired and storage implications

The only new authenticated acquisition is the software archive, not additional
science/HK data. Small public URSC/contact HTML snapshots are also pinned locally.
The original user download remains intact; an equal ignored repository copy
provides a portable source location. No bulk extraction was performed.

**OBSERVED storage:** archive 19,730,838 bytes; complete gzip expansion to the TAR
stream 25,630,720 bytes; 45 entries (35 regular files, 10 directories); declared
regular-file bytes 25,543,346. There are no observed links, duplicate names or
traversal/absolute paths. Fifteen nested distributions account for 19,292,536
declared bytes; they were inventoried/hashed without recursive extraction.
Selected source/CALDB members only were staged in ignored cache.

The three selected calibration files total 6,209,943 bytes. The RMF matrix alone
requires 6,120,000 bytes as an array, excluding library/metadata overhead. This
was measured from shape/dtype, not process peak RSS. Existing science ZIPs total
12,252,904 bytes, but each PI expands to 472,443,840 bytes; full counts and repeated
channel arrays are each 235,008,000 bytes. Keep original compressed products and
one-product staging/chunked access; do not extrapolate a historical HK budget or
choose an acquisition date range from two validation samples.

## 11. Provenance and hashes

Portable official source path:
data/raw/aditya/documentation/pradan-official/solexs_tools-1.1.tar.gz.
SHA-256: **348014aefa50ade556ec4a160a3cfe0b08095bde84b4650a27d6b5d3bf7fa2d3**.
The local size equals the attributed catalogue size, and the original/copy hashes
agree before and after inspection. Actual acquisition time and the exact download
URL remain UNKNOWN; filesystem modification times are not used as evidence.

Each selected member retains parent archive/hash, member name, bytes and SHA-256;
full small TAR inventory and candidate equality links are in the evidence manifest.
Manual/release original hashes agree with the unchanged C/D pins. Generated native
and readiness outputs remain ignored and are separately pinned by size/SHA-256.
No absolute machine path, credential or large scientific array is recorded.

## 12. Implementation and reproduction

Retained changes are evidence/checklist manifests and documentation. Existing
package APIs, seven CLIs, configuration, dependencies, tests and the native loader
remain unchanged. No speculative transform or new calibration architecture is
introduced. Exploratory scripts/staged members remain ignored research scratch.

From an installed repository with the identity-matching inputs present:

```bash
mkdir -p results/solexs_authoritative_evidence
python scripts/register_aditya.py --config configs/data/solexs_storage.json --verify
python scripts/validate_solexs.py --config configs/data/solexs_storage.json \
  --output results/solexs_authoritative_evidence/native_report.json
python scripts/probe_solexs_readiness.py \
  > results/solexs_authoritative_evidence/readiness_probe.json
```

The native output's SHA-256 is
70241bdde078c8e0986bb23117c6543a262fe1846bfd81e64d4b49380f43eb8a;
the readiness probe's is
3df12394d6e9f4f4fe94b7adb787c9a8cb9af41bb460b7dbe21cd2436f4df174.
They are byte-identical to the preserved Phase D outputs. The probe still uses
its pinned candidate locations: byte identity with the official TAR members
establishes that the same numerical diagnostics apply, not compatibility approval.
Create the report directory before stdout redirection and use only ignored output
targets; an initial missing-directory redirection was corrected before the probe ran.

For the original official bundle, the following read-only verification reproduces
the complete pinned inventory/member identities without unpacking it:

```python
import gzip, hashlib, json, tarfile
from pathlib import Path

m = json.loads(Path('data/manifests/solexs_phase_d1_evidence.json').read_text())
a = m['official_archive']; p = Path(a['path'])
def digest(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(chunk)
    return h.hexdigest()
assert p.stat().st_size == a['bytes']
with p.open('rb') as f:
    assert digest(f) == a['sha256']
n = 0
with gzip.open(p, 'rb') as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b''):
        n += len(chunk)
        assert n <= a['reconnaissance_limits']['expanded_bytes']
assert n == a['gzip_expanded_bytes']  # full read also checks gzip CRC/trailer
with tarfile.open(p, 'r:gz') as t:
    entries = t.getmembers()
    assert len(entries) == a['member_count']
    for actual, expected in zip(entries, a['members']):
        assert actual.name == expected['name'] and actual.size == expected['bytes']
        assert (actual.isfile() and expected['kind'] == 'file') or (
            actual.isdir() and expected['kind'] == 'directory')
        if actual.isfile():
            assert actual.size <= 16 * 1024 * 1024
            with t.extractfile(actual) as f:
                assert digest(f) == expected['sha256']
```

The initial exact archive hash bounds the supported input before parsing; this
snippet verifies one pinned evidence resource, not an arbitrary TAR intake API.
Astropy readonly inspection of the selected RMF/ARF reproduces the HDU/grid
observations; no external tool installation is required.

## 13. Tests and verification checkpoint

Executed so far: baseline full suite (166 passed), pip check (no broken
requirements), registered identity verification, complete two-archive native
validation, Phase D probe reproduction, 36 existing source pins and original
document comparisons, official TAR full gzip integrity and bounded inventory,
all 35 regular-member hashes, selected source/CALDB equality and readonly FITS
structure/grid checks. All eight sample FITS products and their sixteen DATASUM
checks were verified by the existing native CLI; calibration checksums are absent.

Fresh checkpoint checks were executed after the evidence/doc changes:

| Check | Executed result |
|---|---|
| `.venv/bin/python -m pytest -q` | 166 passed, one existing warning, 33.44 seconds. |
| Isolated installed imports from `/tmp`, Python `-I` | Package, native SoLEXS, storage and GOES import from site-packages; version 0.1.0. |
| All seven scripts' `--help` | Exit 0 for download_data, inspect_data, preprocess, eda, register_aditya, validate_solexs and probe_solexs_readiness. |
| `.venv/bin/python -m pip check` | No broken requirements. |
| Source/member identities | All 39 C/D/D.1 source pins and 11 selected cache-member hashes match; three supplied official originals agree with canonical copies. |
| Official bundle reproduction snippet | Executed successfully: complete gzip expansion/trailer and all 35 regular-member hashes, without extraction. |
| GOES regression | Six raw identities, eight saved artifact hashes, exact reread/Parquet frame, numeric EDA/catalogue fields and six schema snapshots unchanged. |
| Protected foundation diff against e1cfa85 | Source, tests, config/dependencies, original inventories and historical C/D reports unchanged. |
| Strict JSON / portable metadata | Fourteen original IDs/dispositions, evidence enums, false application gates, pending sent request, source/artifact pins and local links verified. |
| Raw-data protections | Actual ZIP/software/CALDB/cache/result paths ignored; index and all reachable history scanned for prohibited paths/payloads, with only empty data/results .gitkeep placeholders allowed. |

The warning is the existing NumPy/netCDF4 `numpy.ndarray size changed` runtime
warning. Passing numerical regressions does not independently qualify another
platform/environment or remove that limitation. Fresh verification artifacts
remain ignored under results/solexs_authoritative_evidence.

Independent whole-checkpoint review directly rechecked the original archive,
selected sources, calibration FITS and native metadata/GTI values. Its one
Important wording issue was corrected: missing HK/deadtime/index/PI-grid ARF
claims apply only to the inspected outer source/CALDB tree; nested distribution
contents remain unestablished. No broader extraction or scientific repair was
needed. Final publication includes diff/whitespace and renewed index/history
protection checks; ref/status results are reported at handoff.

No new behavioral tests were added for documentation/metadata alone. Any later
retained behavior change requires meaningful coverage before application. No
external tool runtime, HK-dependent correction or physical calibration result
is claimed as tested.

## 14. Remaining unknowns and cross-instrument readiness

There is still no approved pipeline-1.1 absolute clock/card precedence, LC bin
position or continuous GTI/exposure policy; no compatible HK identity/required
correction-state chain; and no approved PI-to-response index, gain/epoch or
calibrated-flux contract. Quality/background and observer-reference prerequisites
are conditional on that contract. SDD1 cause and July 2 availability remain UNKNOWN.
The tools package license metadata is inconclusive (License UNKNOWN with an MIT
classifier); its source/binaries are not redistributed in Git.

The safe exposed representation remains native immutable lineage, unconverted
LC/PI coordinates, original counts/channels/units, GTIs, exposure and NaN masks.
Technical parsing and catalogue UTC labels do not establish cross-instrument
readiness. Existing GOES behavior is preserved; no paired alignment is performed.
External tools runtime, XSPEC/Sherpa response behavior, HK schemas and any
calibrated physical result remain untested and unapproved.

## 15. Smallest exact Phase E prerequisites and next action

The fourteen checklist entries reduce to three required evidence contracts:

1. Mission-applicable pipeline-1.1 clock/bin/GTI/exposure policy, reconciled with
   both immutable samples and defining uncertainty/leap/reference behavior.
2. Approved correction state and workflow; if it needs HK/parameters, exact
   matching day/schema/version/mode resources and a small validation reference.
3. Approved detector/epoch/software response, PI channel association and
   energy/gain provenance, with a reproducible physical representation/reference.

One authoritative specification may cover several contracts; fourteen separate
downloads are not required. The next required evidence is the response to the
[prepared timing/GTI/exposure clarification request](SOLEXS_PHASE_D1_AUTHORITY_REQUEST.md)
to the documented SoLEXS contact. **OBSERVED, user-attributed:** the user has sent
that request; no response is available. Preserve any official reply/artifact and
validate its applicability before changing the gate. No additional download filename is
invented and no further science file is currently requested.

Historical date selection/storage specifications are deferred until those gates
pass. Bulk Phase E, dataset construction, instrument alignment and main integration
remain unauthorized. The branch is an evidence checkpoint awaiting authoritative
clarification, not a scientifically ready acquisition pipeline.

BLOCKED_FOR_PHASE_E
