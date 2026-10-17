# Phase 2 V2 G4 lifecycle safety correction

Date: **2026-10-18, Asia/Kolkata**; verification began October 17. Base: `d07a4070278a784da5cdb69842fd1f66c4156e86`. Branch: `codex/v2-experimental-validation-readiness`.

**Verdict: supported catchable-signal lifecycle checks PASS. G4 remains NOT AUTHORIZED; reservation SolarJEPA-G4-MBA-M2-20261017-01 remains PREPARED and inactive.** No real-data model construction, optimizer step, validation prediction, pilot or reservation activation occurred. Native verification recomputed only permitted scalar training normalization/support statistics, with Torch import blocked.

This dated correction supersedes the SIGINT-only operator condition in the [historical G4 preparation](PHASE2_V2_G4_EXECUTION_PREPARATION.md). The earlier TERM/HUP orphan observations and [reservation snapshot](evidence/phase2_v2_g4_reservation.json) remain historical evidence. Their source/runtime bindings cannot authorize the corrected source. Current checks are in the [verification record](evidence/phase2_v2_g4_lifecycle_verification.json) and [native revalidation](evidence/phase2_v2_g4_lifecycle_native_preflight.json).

## Verified correction

The pilot owns SIGINT, SIGTERM and SIGHUP for the whole driver lifetime, restores prior handlers, and routes the total SIGALRM deadline through the same cancellation state. During spawn, Python exceptions are deferred until the actual `Popen` object and PID are retained, closing the catchable-signal assignment gap. OS signal masks are not blocked/inherited by workers. During teardown, repeated cancellation is deferred through TERM, mandatory KILL, owned-child reap and live-process-group absence verification. A TERM-grace monitoring failure cannot skip the hard stop; unresolved observation remains a failure rather than a successful cleanup claim.

Each attempt records a random ownership token and exact PID/process-group/session/UID/birth identity in an atomic read-only sidecar under `supervisor/ownership/`. Private OS environment inspection checks only that token; unrelated environment bytes are neither returned nor logged. Missing or zombie/confirmed-terminal processes yield no identity. Differing live identities or missing/malformed/wrong tokens remain terminal, even if the worker subsequently exits. The exact transition behind one intermittent broad-test failure was not captured; its natural-exit explanation is **INFERRED**. Deterministic real-child exit and mismatch regressions independently exercise the corrected distinction.

An exclusive-create `.pilot-started` marker, written once through the pilot API, and any prior attempt prevent another execution session. Ownership/session metadata stays outside sealed model artifacts and the exact existing supervisor/attempt/report schemas. The 20-success/18-model reporting guard and all scientific metadata restrictions remain unchanged. Atomic publication, collision protection and withdrawal are preserved; the final cancellation checkpoint immediately after publication defines terminal completion. Later signals are deferred through timer/handler restoration without converting an already completed publication into an interrupted outcome.

`PilotSupervisor.cleanup_orphan()` is an explicit **stop-only** operation under the execution advisory lock. It checks the persisted plan/storage and exact ownership before any signal. Unknown spawn PID, missing leader with live descendants, missing/mismatched ownership, reused/unowned identities, unsafe storage and an active supervisor lock refuse recovery. It never calls fitting, resumes jobs, retries, acquires data or publishes a comparison. After verified cleanup, the attempt is failed, remaining jobs stay pending, and `ORPHAN_CLEANUP_ONLY` prevents a complete result. A monitoring failure can leave the unchanged incomplete ledger even when the hard stop was attempted; investigation/another explicit cleanup may be needed to establish the outcome.

The generic supervisor is one of the 24 ratified historical source pins. It remains byte-for-byte unchanged; the bounded attempt/cancellation correction is pilot-specific. Scientific loading, QC, normalization, model recipes, schedules, worker logic, report validation and inference code are unchanged.

## Executed checks

| Check | Observed result |
|---|---|
| Final relevant nonfitting suite | **257 passed**, 117.69 seconds, no warnings |
| Final focused lifecycle/safety/driver suite | **41 passed**, 34.56 seconds |
| Independent technical review and scoped re-review | No remaining must-fix finding; frozen identities/pins independently matched |
| Independent scientific review and scoped re-review | No scientific/reporting boundary change; dated handoff refresh required |
| Normal noneditable installation | All **64** package modules match checkout; all **42** explicit lock requirements match |
| Native/QC/support/normalization revalidation | All **92** pinned files and all eight data-identity fields match prior frozen evidence |
| Native preparation measurement | 15.23 seconds; 458,342,400-byte sampled group peak; Torch import blocked |
| Preservation | 92 raw files, nine historical checkpoints and both ratified protocol files retain sizes/hashes; 101 actual paths ignored |
| Metadata/help/denial | Repeated outside-checkout metadata is byte-identical with Torch blocked; help exits 0; missing approval exits 2 before science/output access |

Deterministic synthetic tests cover supervisor-only INT/TERM/HUP, stubborn workers and descendants, repeated signals during TERM grace and actual hard-stop boundary, spawn-to-assignment interruption, timeouts/nonzero exits/monitor loss, restoration of custom handlers, authenticated orphan cleanup after SIGKILL, ownership/lock/collateral refusal, confirmed exit versus live mismatch, no retry/next job/publication, and the real 20-attempt accounting path through the closed 18-model report validator. Test emergency cleanup targets its own groups. Synthetic fixtures construct predictions/weights as needed for guards; they do not fit real or synthetic scientific models.

Recorded red evidence includes original TERM/HUP/spawn orphan failures, missing-token recovery and monitoring-loss defects, and terminal-identity regressions. The first broad run had one failure and 254 passes before the final identity correction; twelve isolated replays alone did not reproduce its exact transition. The full final suite above passed after the correction. No failed check is relabelled as an earlier success. The full project suite was not run because it contains unauthorized fitting/experiment tests. No actual fitting/prediction/reload feasibility benchmark was performed.

## Frozen and updated identities

| Binding | Fingerprint |
|---|---|
| Protocol v1 design, unchanged | `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624` |
| Ordered 20-job configuration, unchanged | `a7ce71194dac05c7ac14e5a5fc09f478b7b6d88ad0744a97bc7c3c7af02a641b` |
| Corrected executing source | `fbb17789683545fae55b8aa5c19085bd4dadf9cdb0d72922bdad37e8b6c567ee` |
| Host, unchanged M2 | `58c5a228d2cc695f0bba3ae9917b61c041556a10a44261ec6a6d4b465dbe77dd` |

All 24 historical source pins, 17 decisions, ordered seeds `1261866429, 1291916211`, dependencies and per-job model-configuration hashes were independently recomputed. The matrix remains two shared SSL jobs and 18 selected models (14 primary plus four alternate-loss), including the same 14 nested linear candidates. All dataset/forecast/split/training/normalization/subset/validation-content identities equal the prior evidence. No August/January/other scientific input or historical checkpoint content was used for model computation.

The final runtime fingerprint must be measured **after the last clean published commit** with the refreshed normal installation. It is intentionally external: committing that final record into the same branch would change the Git commit it binds. The local handoff directory is `/Users/nealsalian/Desktop/SolarJEPA/results/v2-g4-mba-m2-20261017/`: `runtime-final.json`, `execution-binding.json`, `reservation.json`, and the exact 18-field `owner-approval.pending.json` are regenerated there after publication. Earlier bindings to `d07a407`, source `60423ce…`, or prior review/source candidates are stale and must not be approved for this correction. Historical records remain retained; no owner claim is fabricated.

## Reservation, remaining risks and approval

Canonical roots remain source `/Users/nealsalian/.codex/worktrees/v2-experimental-validation-readiness/SolarJEPA`, data `/Users/nealsalian/Desktop/SolarJEPA`, and absent output `SOURCE/results/v2-development-v1-first-pilot`. The named reservation still has no activated start/end window. The observed host remains MacBook Air M2/Mac14,2/arm64/eight logical CPUs/8 GiB physical RAM. Latest measured prepublication output free space was 6,706,368,512 bytes; volatile memory-pressure, swap and storage observations are in the evidence and must be rechecked immediately before execution. No OS CPU/RAM/storage allocation guarantee is claimed.

Limits remain serial CPU float32, four native-library/Torch threads, 2,147,483,648-byte sampled live worker-plus-descendant RSS, 7,200 seconds total including preparation/finalization, zero retries and no automatic resume. Attempt ceilings remain SSL 300 seconds, controlled 600, TCN 1,800, and the whole linear path 600; at least 1 GiB free output storage is checked before launch and each attempt. The 13,800-second sum of attempt ceilings does not override the 7,200-second total or guarantee completion.

**Remaining limitations:** SIGKILL, host loss and loss before durable PID/ownership publication cannot be made catchable. Explicit recovery refuses ambiguous cases; it does not authorize killing by a bare PID. Trusted workers and descendants must remain in the original process group; intentionally escaping/hostile processes are outside this local guarantee. RSS is sampled, library thread settings are not an OS thread cap, and termination/monitoring overhead is not a hard realtime bound. Linux ownership inspection is implemented but this verification ran on the local Mac; Linux behavior is untested here. Actual fitting/optimizer/reload/prediction/report cost and full-pilot completion remain **UNKNOWN**.

The known NumPy-first NetCDF4 `numpy.ndarray size changed` RuntimeWarning remains reproducible; strict import exits 1, while ordinary native decoding and frozen identities pass. No dependency upgrade, lock change or warning suppression was made, and binary correctness is not established by these checks. No operational causality, unrecorded exposure, generalization or JEPA-benefit claim follows from this engineering preparation.

The owner must separately activate the named host/path/window reservation, accept these remaining limits/risks, and explicitly authorize one unchanged bounded 20-job May–July development pilot against the **final published commit/runtime/source/design/configuration and exact eight-field data identity**. Approval includes fixed fitting, validation prediction/reload/selection and descriptive-only post-selection reporting. Classical references, August, January, other datasets, new acquisition, test release, confirmation, sampling inference, additional fits and automatic resume remain excluded.

The external declaration retains exactly the existing validator's 18 fields. Until explicit owner approval it stays `PENDING`, owner/time null, execution/fitting/test-release false, and `host_reservation.reserved=false`. After explicit authority, only the owner-authorized fields become `APPROVED`, named owner, actual past/present UTC approval time, execution/fitting true and reservation true with its activated window/rationale; test release stays false and all measured identities must still match. Pending/stale bindings fail closed. Implementation publication and cleanup fixes supply no G3 activation or G4 authority.

Suggested owner statement referencing the regenerated exact external record:

> I activate reservation SolarJEPA-G4-MBA-M2-20261017-01 for one explicit immediate execution window on the verified local MacBook Air M2. I approve the final clean published commit/runtime/source, ratified Protocol v1 design, unchanged ordered 20-job configurations and exact May–July data identity in the external execution-binding and authorization records. I authorize one bounded pilot including fitting, fixed validation prediction/reload/selection and descriptive-only post-selection reporting. I accept serial CPU float32/four threads, 2 GiB sampled worker-plus-descendant RSS, 7,200 seconds total, unchanged attempt ceilings, at least 1 GiB free output storage, zero retries and no automatic resume. I accept the NetCDF4 warning, unknown fitting feasibility and documented uncatchable-loss/process-group limits. Catchable INT/TERM/HUP must stop workers; any explicit orphan recovery is stop-only and must refuse ambiguous ownership. Failures remain INCOMPLETE with failed/pending jobs preserved. No excluded data/test access, confirmation, inference or additional fitting is authorized.
