# V2 controlled validation recheck — 2026-10-19

**Verdict: BLOCKED at G3/G4.** Existing preparation passes the checks below; no
new must-fix implementation, scientific or statistical defect was found. The
named reservation remains inactive and one bounded pilot remains unauthorized.
No model fitting, real-data prediction, pilot, test release or acquisition ran.

This is a dated continuation of the [lifecycle checkpoint](PHASE2_V2_G4_LIFECYCLE_SAFETY.md),
not a replacement for historical evidence. The compact machine record is
[the October 19 verification record](evidence/phase2_v2_recheck_20261019.json).
Large logs and helper snapshots remain ignored under
`results/phase2_v2_readiness_20261019/`.

## Verified starting state and reference

**OBSERVED:** fetched `main=origin/main=94a99cb60a6729c7358a3d8e553d154330d95601`.
The published annotated `v0.1.0` tag object is
`d648e3c3d2f4d7fed758c2bcfdf07c0ba0ff9c55`; its peeled commit equals main locally
and on GitHub. Main's worktree is clean. This tag is the Stable Baseline reference.

The latest clean V2 checkpoint, published locally and on GitHub, is
`8e9ce06407d5fab50ca5766fc061b45a3fb277a8` on
`codex/v2-experimental-validation-readiness`. Its implemented protocol, native
loader, guarded worker/driver, reporting, resource supervision and cancellation
fixes already exist. Earlier V2 M0–M5 branches and reports were inspected; no
infrastructure was recreated. Continuing this existing milestone branch also
preserves the exact branch required by the execution validator. Its common
ancestor with current main is V1 audit `644648f`; unrelated baseline/UI changes
were not imported into the frozen V2 source.

The original nine V1 checkpoints, summary, per-origin scores and saved prediction
archive match their Stable Baseline copies by size/SHA-256. Relevant original
JEPA, normalization, forecasting contracts/windows, checked V1 configurations
and the three original lock files match the tag. V2's existing additive embargo
validation and acceptance machinery are separately retained. V1 checkpoints
are historical references, not substitutes for V2's distinct selected-checkpoint
schema. No checkpoint was loaded and no saved prediction archive was decoded.
The baseline's earlier numerical replay is historical evidence, not a fresh
replay in this task.

## Unchanged protocol and scientific boundaries

| Binding | Observed value |
|---|---|
| Ratified design | `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624` |
| Ordered job configurations | `a7ce71194dac05c7ac14e5a5fc09f478b7b6d88ad0744a97bc7c3c7af02a641b` |
| Executable source | `fbb17789683545fae55b8aa5c19085bd4dadf9cdb0d72922bdad37e8b6c567ee` |
| Reviewed starting runtime | `08e6f763ff8aa88d96a18ffcd076e996646b6546fcb5d69964d566b803c57ae4` |
| Host | `58c5a228d2cc695f0bba3ae9917b61c041556a10a44261ec6a6d4b465dbe77dd` |

All 24 historical source pins, 17 decisions, 20 per-job configuration hashes,
dependencies and seeds `1261866429,1291916211` match. The matrix remains two
shared SSL jobs plus 18 selected models: 14 primary and four alternate-loss;
the two linear jobs contain the same 14 nested candidates. Same-seed sealed SSL,
paired support, selected-weight compatibility and exact weights-only reload
parity remain enforced by existing code and synthetic boundary tests. Actual
real-data fitting/reload feasibility remains UNKNOWN.

**OBSERVED:** fresh native preflight audited exactly 92 pinned May–July GOES-16
files, 27,280,082 bytes and 132,480 minute bins over
`[2024-05-01T00:00Z,2024-08-01T00:00Z)`, with no missing/duplicate timestamps.
It verified native identities, units, clocks, QC/masks and final source hashes.
No excluded raw science or checkpoint was opened in that process; Torch imports
were forbidden. All eight data-identity fields equal retained evidence.

Train/validation retain 3,609/412 origins and exclude 327/68. Context/target
support is complete and contained in each half-open partition. Training ends
and validation begins July 22 00:00 UTC. Normalization independently matches
unique valid raw training cells only (118,080 unique rows; channel counts
113,926/116,125); stride-one training uses the fixed 20,000 of 108,199 eligible
windows. No split, embargo, QC or normalization default changed.

The scientific restrictions documented in the ratified protocol remain binding:
exposed development, post-selection validation, zero embargo, accepted partial
minute means and two seeds do not establish independence or generalization.
Complete-case target QC excludes 68/480 validation candidates (14.17%); results
would describe that retained population. M2/M3's `NO_VALIDATED_REPLACEMENT`
remains enforced; uncertainty-of-estimate intervals, p-values and significance
stay unavailable. Marginal predictive quantiles are not trajectory probabilities.
Classical comparisons, new test access, V3, operational forecasting and
scientifically blocked SoLEXS modeling remain excluded. August/January are
excluded here and are not certified untouched holdouts. Actual operational
delivery/upstream causality and unrecorded exposure remain UNKNOWN.

## Executed verification and independent reviews

| Check executed October 19 | Observed result |
|---|---|
| Existing pilot/worker/driver/report/resource/loader/descriptive/lifecycle suite | 257 passed, 117.71 s, no warnings |
| GOES/native/forecast-contract/split/window/integrity/provenance/storage suite | 176 passed, 4.94 s, one existing warning |
| Native preparation, with Torch forbidden | Exit 0; 15.46 s monitored; 452,493,312-byte sampled process-group peak |
| Native support and train-normalizer recomputation | All eight identities match; exact 92-file access audit |
| Normally installed package and locks | 64 modules byte-match; 42 explicit requirements match |
| Fresh outside-checkout runtime repeated twice | Byte-identical; matches existing October 18 external binding at starting HEAD |
| Production metadata/help and missing/pending approval | Metadata/help exit 0; both denied requests exit 2 before scientific I/O/output creation |
| NumPy-first NetCDF4 import | Ordinary import exits 0; strict RuntimeWarning-as-error import exits 1 with known ndarray-size warning |
| Preservation before/after checks | 92 raw files, nine checkpoints, both ratified files, all 72 inspected refs and other 15 worktree states unchanged |

The scientific subagent independently checked protocol/pins/scope and 14
consistency conditions in the fresh native record, including support, masks and
normalization. The statistical subagent independently recomputed all job/seed
identities, rehashed nine checkpoints and passed seven selected pure synthetic
arithmetic/report checks. The technical subagent independently recomputed the
runtime and denial behavior, inspected current resources and traced worker,
reload, cancellation, ownership and publication boundaries. All three found no
new must-fix issue within the approved preparation scope.

Technical review highlighted the existing procedural limitation that the exact
18-field authorization schema does not machine-enforce reservation start/end or
expiry. Owner activation must therefore name an immediate window, followed by
resource/source/data/output revalidation just before launch. Adding fields or
silently altering this protocol is outside this recheck. No source fix was
needed. Final evidence review also required labeling copied design-time resource
annotations as historical and recording the observed storage/no-resume controls
separately; that documentation correction is resolved without changing protocol
bytes. Historical reports and existing external handoff files remain intact.

The full project suite was not run: it contains fitting/experiment tests outside
this preparation gate. No actual fitting benchmark, real-data model construction,
validation prediction/replay or full-pilot completion test was performed. The
NetCDF4 warning is reproducible and unsuppressed; passing native identities does
not establish binary correctness. Cross-platform behavior remains untested here.

## Resource readiness and exact remaining gates

At `2026-10-19T07:16:18Z`, the same Apple M2/Mac14,2/arm64 host reports eight
logical CPUs and 8 GiB RAM. The output filesystem has 3,799,490,560 free bytes,
above the 1,073,741,824-byte floor. `memory_pressure -Q` reports 38% free and
swap use is 548.81 MiB. These are volatile observations, not allocated headroom
or a reservation; the earlier October 17/18 resource snapshots are historical.

Limits remain serial CPU float32, four library/Torch threads, 2 GiB sampled live
worker-plus-descendant RSS, 7,200 seconds total including preparation/finalization,
zero retries/no automatic resume and at least 1 GiB free output storage before
launch/every attempt. SSL/controlled/TCN/whole-linear-path ceilings remain
300/600/1,800/600 seconds. Their 13,800-second sum cannot override the two-hour
total. **UNKNOWN:** actual fitting/optimizer/output/reload/report cost and whether
all 20 jobs finish. No completion guarantee or extrapolated speed claim is made.

| Gate | Current status | Required action |
|---|---|---|
| G1 ratification | Recorded complete; exact fingerprint reverified | Preserve design |
| G2 infrastructure | Implemented; current nonfitting checks/reviews pass | No new implementation required |
| G3 reservation | PREPARED, inactive; no activated start/end window | Owner activates exact named host/source/data/output/window and accepts resource/feasibility risks |
| G4 bounded pilot | NOT AUTHORIZED | Explicit owner approval for one unchanged 20-job May–July fitting/prediction/reload/selection/descriptive-reporting pilot against final published bindings |
| G5 test release/confirmation/inference | Outside scope | Separate future scientific/access design |

The sole allowed next execution target is the still-absent
`SOURCE/results/v2-development-v1-first-pilot`, with source this V2 worktree and
data `/Users/nealsalian/Desktop/SolarJEPA`. Reservation
`SolarJEPA-G4-MBA-M2-20261017-01` remains prepared, not activated.

After this report's final clean commit is published, refresh runtime and resource
bindings into a **new** ignored handoff directory:
`/Users/nealsalian/Desktop/SolarJEPA/results/v2-g4-mba-m2-20261019/`.
Its `execution-binding.json`, `runtime-final.json`, `reservation.json` and exact
18-field `owner-approval.pending.json` will identify that published commit.
The starting-runtime value above becomes historical after publication. A final
runtime cannot be committed into the commit it binds without changing that
identity. Preserve the October 17/18 handoff; do not approve its superseded
runtime. New owner/time fields remain null, approval PENDING, reservation false
and execution/fitting/test-release false until explicit owner authority.

**Recommended next action:** review the final external binding, activate one
immediate named compute window and explicitly approve the unchanged bounded
pilot, accepting the documented warning, sampled controls, uncatchable-loss
limits and UNKNOWN fitting feasibility. Recheck resources/source/data/output
immediately before any separately authorized launch. First failure remains
INCOMPLETE; no retries, resume, expanded limits or additional fits follow.

Only V2 documentation/evidence is published by this recheck. No PR, merge, main
push, branch deletion, protocol change or pilot execution is authorized here.
