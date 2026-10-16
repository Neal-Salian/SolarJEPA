# Phase 2 V2 — G3 readiness verification

Date: **2026-10-16, Asia/Kolkata**. Branch: `codex/v2-experimental-validation-readiness`.
Reviewed infrastructure: `5d2f0b1514561476649e27798b317e0adeeb78ab`.
Reviewed cleanup correction: `b0157f20ecff85dc810730807cd9a097b7aea6c2`.

**Verdict: non-training scientific and technical checks PASS. G3 is not cleared:
the named host/environment/data/output reservation is absent and actual fitting
feasibility remains UNKNOWN. G4 is NOT AUTHORIZED.** No real-data model training,
pilot, fitting benchmark, validation prediction or test release was performed.
Only scalar normalization statistics were recomputed from permitted raw training
cells. Both ratified protocol files, all 17 decisions and all 24 historical source
pins remain byte-for-byte unchanged.

The [verification record](evidence/phase2_v2_g3_verification.json) contains exact
identities, job hashes, runtime/lock checks, review findings and hashed local logs.
The [native preflight record](evidence/phase2_v2_g3_native_preflight.json) contains
the complete portable native/QC/support/normalization evidence. These extend the
historical [implementation report](PHASE2_V2_PILOT_INFRASTRUCTURE.md); they do not
rewrite its previously unmeasured native-readiness findings.

## Scientific inputs and leakage checks

**OBSERVED:** the three pinned manifests selected exactly 92 May–July 2024
GOES-16 science files, totaling 27,280,082 bytes. Every manifest/configuration,
raw size/SHA-256, native product identity and final source re-verification passed.
The decoded grid has 132,480 one-minute bins spanning
`[2024-05-01T00:00:00Z, 2024-08-01T00:00:00Z)`, with no missing bins or duplicate
timestamps and 1,440 observed bins per day. No August or January raw file was
opened. The final August 1 timestamp is the exclusive end of the last July bin.

The adapter checks record-start UTC convention, monotonicity, minute alignment,
coverage/nominal-day containment, nonoverlapping files, ordered A/B channels and
native `W/m2` units. Upstream native validation enforces scalar, integer-coded
quality/count fields. The unchanged mask requires finite positive bounded flux,
status zero, electron flag 0–511 with excluded bits `(7|8)` for A and `(7|16)` for B,
and contributing counts 1–60. It preserves invalid bins/masks without imputation.

| May–July observed QC | XRS-A | XRS-B |
|---|---:|---:|
| Valid bins | 128,098 | 130,297 |
| Invalid observed bins | 4,382 | 2,183 |
| Valid bins with 1–59 samples | 8,381 | 1,976 |
| Valid bins with fewer than 30 samples | 153 | 155 |

Partial-minute means remain accepted by the ratified analysis policy; their
acceptance does not establish full-minute measurement quality. No sensitivity
cohort or new QC rule was introduced. **DOCUMENTED:** NOAA describes the science
product as retrospectively reprocessed, specifies the leap-second-neglecting UTC
epoch and contributing counts, and warns about electron-correction limitations
([XRS L2 User Guide, §§2.1, 2.4, 4](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf)).
Exact numeric schemas are additionally **OBSERVED** in the pinned native files.
Operational delivery, causal upstream processing and unrecorded historical
exposure remain **UNKNOWN**.

**OBSERVED:** complete 120-bin context and 30-bin future targets remain inside
each half-open partition. Context ends no later than issue time; targets start
no earlier than issue time. Training ends at July 22 00:00 UTC; validation starts
there and ends August 1 00:00 UTC. Zero embargo is unchanged and does not imply
statistical independence.

| Support | Retained issue origins | Excluded issue origins |
|---|---:|---:|
| Training | 3,609 | 327 |
| Validation | 412 | 68 |

The raw training slice contains 118,080 unique minute rows. The preflight
independently recomputed `log10(F/(1 W/m²))` means and population SDs using each
valid raw training cell once: counts 113,926 for A and 116,125 for B; means
`[-6.975172762067082, -5.475295794509493]`; scales
`[0.5742480619158656, 0.34159742190236464]`. Feature and target statistics match.
No validation cells or repeated overlapping windows enter normalization.
The existing stride-one complete-window path has 108,199 eligible windows and
uses the fixed evenly spaced chronological subset of 20,000.

The dataset, forecast, combined/per-role splits, training slice, normalizer,
subset and validation-content identities were recomputed. All four historical
dataset/split/training/normalizer pins matched. Exact approval-ready
`data_identity` values are in both evidence records, including validation content
`bd0fbf759460b2392b0812ff825b215f3e020f9271cdfe20881cf5fa4e5c0870`.
The worker independently compares these actual identities against the external
approval at its consumer boundary before any fitting.

## Source, runtime and job identities

| Identity | Observed fingerprint |
|---|---|
| Unchanged Protocol v1 design | `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624` |
| Unchanged ordered 20-job configurations | `a7ce71194dac05c7ac14e5a5fc09f478b7b6d88ad0744a97bc7c3c7af02a641b` |
| Corrected executing source | `60423ce156686e6e7681b2744d678f7f8668463d11290fb99655b369d9af56b0` |
| Observed host | `58c5a228d2cc695f0bba3ae9917b61c041556a10a44261ec6a6d4b465dbe77dd` |

**OBSERVED:** the fresh clean implementation-commit runtime at `b0157f2` has
fingerprint `fcc548fd5d1ad43519ba5c1edf4121cf05a695a16fab4ef5629e910e777fa34f`.
It is a verification snapshot, **not a G4 approval identity**: documentation
publication changes `git_commit`, hence the runtime fingerprint. Obtain a fresh
`runtime_identity(SOURCE_ROOT)` from the final clean branch HEAD immediately
before an owner approves execution. Any later commit, source/configuration,
environment, executable path or host identity change invalidates that binding.

The normal noneditable installation was refreshed only in this worktree's
ignored `.venv`; every package module matched checkout source. Metadata calls
from outside the checkout repeated byte-identically without importing Torch.
Missing-approval execution was refused with exit 2 before scientific I/O or
outputs. The production canonical worker import plus help/provenance check
passed. All 42 explicit lock requirements matched installed versions, including
Python 3.13.3, Torch 2.6.0, NumPy 2.2.6 and NetCDF4 1.7.2. Dependencies remain
shared through the existing read-only dependency paths; other environments were
not changed. The binding inventories versions and locks; it is not binary-build
authentication or a security boundary.

**Environment caveat:** a fresh explicit warning capture and the additional
native tests expose NetCDF4's `numpy.ndarray size changed` RuntimeWarning
(`Expected 16 from C header, got 96 from PyObject`). Strict warnings-as-errors
import exits 1. Ordinary import, native decoding, QC and pinned identities pass;
no numerical corruption was observed. The exact warning is reported in
[Unidata issue 1354](https://github.com/Unidata/netcdf4-python/issues/1354), where a
maintainer also reproduced it with passing upstream tests. That is supporting
context, not proof of binary correctness on this host. Record this caveat in the
reservation/execution decision; no warning suppression, dependency upgrade or
lock change was made. This environment must not be described as warning-free.

## Resource and integration verification

**OBSERVED:** the available computer is `Neals-MacBook-Air.local`, Apple M2,
`Mac14,2`, arm64, eight logical CPUs and 8,589,934,592 bytes physical RAM. The
output filesystem had 5,317,255,168 free bytes at the recorded check, above the
1,073,741,824-byte floor. These volatile observations are not a reservation or
proof that RAM/CPU/storage will be available throughout a run.

| Unchanged limit | Value |
|---|---:|
| Sampled live worker plus descendant RSS | 2,147,483,648 bytes |
| Native-library/Torch CPU threads | 4 |
| Total wall time, including preparation/finalization | 7,200 seconds |
| Automatic retries | 0 |
| SSL / controlled / TCN / whole linear-path attempt | 300 / 600 / 1,800 / 600 seconds |

**OBSERVED:** May–July preparation completed in 19.03 seconds (19.26 seconds
including external monitoring), with 378,847,232-byte self RSS high-water mark
and 370,245,632-byte sampled process-group peak. Six native-library thread
variables were set to 4; Torch import was explicitly blocked. **INFERRED:** this
preparation route fits the stated memory/time ceilings on the observed host.
It gives no measurement of model fitting, optimizer/activation memory,
prediction/reload/report costs or complete-pilot output volume.

**UNKNOWN:** whether all 20 actual jobs will finish within two hours and 2 GiB.
Their attempt ceilings sum to 13,800 seconds; the 7,200-second total takes
precedence. No runtime extrapolation or completion guarantee is asserted.
RSS polling can miss brief peaks; library thread settings do not impose an OS
thread cap. The driver checks storage before launch and every attempt, and its
deadline includes preparation and finalization. Termination/polling overhead is
not a hard real-time bound. A fitting benchmark remains separately gated.

**Resolved technical defect:** the total alarm could interrupt the generic
supervisor's TERM grace wait before SIGKILL, leaving a synthetic worker alive.
The pilot-specific override now executes group SIGKILL and bounded reap in
nested `finally` blocks. This preserves every historical source pin. Two new
real-subprocess regressions failed on live-worker RSS before correction and
passed afterward, covering both the actual alarm and a keyboard interruption.
Independent replay and a normal-installed replay each left no workers alive.
An interrupted-cleanup ledger can conservatively retain a running attempt and
`MONITOR_UNAVAILABLE`; it remains **INCOMPLETE**, prohibits ordinary publication
and requires investigation. It must not be relabelled successful or resumed.

Synthetic integration checks cover first-failure stop with pending jobs retained,
zero retries, sealed same-seed SSL dependencies, explicit typed recipes, CPU
float32/determinism, weights-only reload parity, source/runtime drift rejection,
the 14+4 guarded runs ending at `D_LOCKED`, strict descriptive reporting and
atomic publication/withdrawal. Both reports and final accounting become visible
through one directory rename only after the complete cohort passes. No real
training/prediction/reload path has been empirically exercised in this review.

## Executed verification and preservation

- Final pilot/loader/resource/report suite: **254 passed, 1 fitting benchmark
  deliberately deselected, no warnings**, 96.86 seconds.
- Additional native/temporal/provenance suite: **158 passed, 1 RuntimeWarning**,
  37.27 seconds. The strict-import failure above is an intentional environment
  diagnostic, not an unreported test-suite failure.
- Independent scientific review: **163 passed, 1 warning**; source/identity/
  temporal/normalization/selection/report checks passed. The reviewer checked
  the parent's native record independently, without repeating raw decoding.
- Independent technical review: initial focused suites **162 passed**; post-fix
  driver/resource suite **53 passed**, plus original-trigger replay.
- Normal installation, installed-source attestation, denial/help checks,
  `git diff --check` and all 24 historical source pins passed. The full project
  suite was not run because it includes unauthorized fitting/experiment tests.

All 92 permitted raw files and nine historical V1 checkpoints retain their
before/after sizes and SHA-256 values; all 101 actual paths match ignore rules.
No raw science array, weights, credentials or pilot output is staged. Twelve
other worktrees retain their initial statuses. A separate SoLEXS checkout/branch
changed concurrently; the owner explicitly confirmed expected parallel work and
instructed this task to continue while leaving it untouched. This task made no
changes there. Protected local/remote `main` remains `1a4991d`; there is no PR or
merge. Other datasets were not exhaustively rehashed; no other scientific path
was opened or written by this task.

## Exact requirements before G4 execution

1. **Complete G3 reservation.** The owner/operator must name the actual host and
   execution window and approve canonical absolute source/data/output roots,
   CPU float32/four threads, the exact limits above, at least 1 GiB free output
   space, zero retries, the known environment warning and unknown fitting
   feasibility. Current candidate roots are the existing isolated V2 worktree
   for source, `/Users/nealsalian/Desktop/SolarJEPA` for data, and
   `SOURCE_ROOT/results/v2-development-v1-first-pilot` for output. These are
   candidates only: the output is absent and its parent exists; no reservation
   has been made. Recheck disk space and source/raw identities immediately
   before execution. Do not extend limits to obtain completion. Any requested
   real-data fitting benchmark requires its own authorization.
2. **Freeze reviewed execution state.** Use the final clean published feature
   branch HEAD with matching normal installation and corrected source fingerprint
   above. Recompute the full runtime/host fingerprints in a fresh interpreter.
   Use the exact unchanged design and ordered configuration fingerprints. Record
   that executing commit; `b0157f2` is the implementation correction reference,
   not permission to omit subsequent evidence publication or reuse a stale
   runtime snapshot.
3. **Bind actual data support.** Reverify only the three allowed May–July manifests
   and their sources. Recompute native/QC, dataset/spec, combined and per-role
   splits, unique-raw normalizer/training, exact `train_windows` record and
   validation-content identity. They must equal the observed `data_identity` in
   the new native evidence and the protocol's historical pins. Do not copy an
   expected hash in place of measuring actual inputs. No test object is allowed.
4. **Obtain separate explicit G4 authority for one bounded pilot.** Approval must
   name the frozen commit/runtime/source/config/design, G3 reservation and
   May–July fitting plus validation-prediction scope. It must cover all 20 jobs,
   seeds `1261866429, 1291916211`, shared SSL reuse, all fixed schedules/losses/QC,
   validation selection and descriptive-only post-selection reporting. Classical
   references, August, January, test release, confirmation and new inference
   remain excluded. Incomplete runs retain failures/pending jobs; there is no
   automatic resume. Additional fits require a reviewed protocol amendment and
   explicit approval.

The external owner-supplied finite JSON declaration must contain exactly:
`schema_version`, `kind`, `approval_status`, `authorized_by`, `approved_utc`,
`protocol_id`, `design_fingerprint`, `execution_authorized`,
`data_fitting_authorized`, `test_release_authorized`, `scope`, `source_root`,
`data_root`, `output_root`, `runtime_fingerprint`, `configuration_fingerprint`,
`host_reservation`, `data_identity`.

Required constants are version `1`, kind
`solarjepa_v2_pilot_execution_approval`, status `APPROVED`, protocol
`solarjepa.phase2.v2.development.v1`, scope
`EXPOSED_DEVELOPMENT_FEASIBILITY_ONLY`, execution/fitting `true`, and test release
`false`. `authorized_by` names the owner; `approved_utc` is a valid past/present
UTC timestamp. `host_reservation` contains exactly `reserved=true`, actual
`host_fingerprint` and a nonempty named reservation `rationale`. `data_identity`
contains exactly the eight fields shown in the evidence record. The file must
be outside the source worktree. These are local owner claims, not authenticated
signatures. **No approved declaration was created by this review.**

Only after G3 and G4 are separately satisfied, the operator interface is:

```bash
SOURCE_ROOT=/Users/nealsalian/.codex/worktrees/v2-experimental-validation-readiness/SolarJEPA
"$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/run_v2_goes_pilot.py" \
  --root "$SOURCE_ROOT" --execute --approval /absolute/external/owner-approval.json
```

This is an execution requirement, not an executed command or authorization.
`OUTPUT/publication/pilot_accounting.json` is the completed-run accounting
entrypoint; `OUTPUT/pilot_failure.json` is an incomplete engineering outcome.
Neither passing G3 checks nor editing historic approval flags authorizes fitting.
