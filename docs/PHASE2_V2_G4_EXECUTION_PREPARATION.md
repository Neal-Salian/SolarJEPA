# Phase 2 V2 G4 execution preparation

**2026-10-18 follow-up:** the historical SIGINT-only condition and source/runtime bindings below are superseded by the [G4 lifecycle safety correction](PHASE2_V2_G4_LIFECYCLE_SAFETY.md). The earlier observations remain unchanged. The corrected implementation still supplies no reservation activation or G4 execution authority.

Date: 2026-10-17, Asia/Kolkata. Reservation: **SolarJEPA-G4-MBA-M2-20261017-01**.
Branch: `codex/v2-experimental-validation-readiness`.

**Verdict: nontraining revalidation PASS with an operator condition; reservation PREPARED, not activated; G4 NOT AUTHORIZED.** No pilot was run. No model was constructed or trained on real data, no predictions were made on real validation data, and no test partition was constructed. Scalar normalization statistics were recomputed only from permitted unique raw training cells. Protocol decisions, datasets, historical checkpoints and executable source were not changed.

The owner confirmed the concurrent SoLEXS changes are expected and instructed this task to continue on V2 only. That worktree remains untouched. Preparation publication is authorized only on the existing V2 branch; it supplies no G3 window activation or G4 execution authority. The tracked [reservation](evidence/phase2_v2_g4_reservation.json), [verification](evidence/phase2_v2_g4_verification.json) and [native evidence](evidence/phase2_v2_g4_native_preflight.json) retain the review snapshot. The external pending approval and final runtime binding live under `/Users/nealsalian/Desktop/SolarJEPA/results/v2-g4-mba-m2-20261017/`, outside the source worktree and ignored by Git.

## Named reservation

- Host: `Neals-MacBook-Air.local`, MacBook Air `Mac14,2`, Apple M2, arm64, eight logical CPUs, 8,589,934,592 bytes physical RAM.
- Source: `/Users/nealsalian/.codex/worktrees/v2-experimental-validation-readiness/SolarJEPA`.
- Python: `SOURCE/.venv/bin/python`, normal noneditable local package; dependencies remain shared through existing read-only dependency paths.
- Data: `/Users/nealsalian/Desktop/SolarJEPA`, restricted to the three frozen May–July 2024 GOES manifests.
- Output: `SOURCE/results/v2-development-v1-first-pilot`. The directory is absent; its parent exists and is canonical. Do not create it during preparation.
- Window: one continuous session, starting only after a subsequent explicit owner start instruction; at most 7,200 elapsed seconds from driver entry, including preparation/finalization. Calendar start/end remain unknown until owner activation. The declaration does not allocate or lock OS resources and its schema has no expiry enforcement.
- Controls: serial CPU float32, six library thread variables and Torch threads four; sampled live worker-plus-descendant RSS 2,147,483,648 bytes; zero retries; no automatic resume. Attempt ceilings SSL 300, controlled 600, TCN 1,800 and the entire seven-λ linear path 600 seconds. At least 1,073,741,824 free output bytes before launch and every attempt.
- Latest measured output free space at the completed-check snapshot: 5,104,422,912 bytes. `memory_pressure -Q` reported 42% system-wide memory free; `vm_stat` and swap observations are in [the verification record](evidence/phase2_v2_g4_verification.json). Swap was in use. Neither that percentage nor physical RAM is a guaranteed allocatable headroom measurement. Recheck immediately before launch.

The full tracked reservation is [phase2_v2_g4_reservation.json](evidence/phase2_v2_g4_reservation.json); its external copy is `reservation.json`. It is **PREPARED_PENDING_OWNER_ACTIVATION**, not a fabricated owner reservation or execution claim. Both JSON records distinguish unchanged ratified design-time bookkeeping from current observed resource gates; the historical `storage_gate_implemented=false` annotation is not a claim about the implemented driver, whose launch/per-attempt storage gates are verified.

## Observed identities and scientific inputs

Reviewed published HEAD: `24b9400351f4c9c5172ce38f0674d9c03d56d253`. The implementation/cleanup commits `5d2f0b1` and `b0157f2` were inspected, and G3's report `24b9400` was checked against code and fresh execution.

| Identity | SHA-256 fingerprint |
|---|---|
| Ratified Protocol v1 design | `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624` |
| Ordered 20-job configurations | `a7ce71194dac05c7ac14e5a5fc09f478b7b6d88ad0744a97bc7c3c7af02a641b` |
| Executable source | `60423ce156686e6e7681b2744d678f7f8668463d11290fb99655b369d9af56b0` |
| Host | `58c5a228d2cc695f0bba3ae9917b61c041556a10a44261ec6a6d4b465dbe77dd` |
| Runtime at reviewed HEAD, before preparation publication | `eb38ca13e0e4cb3f057a6f645fc5d4ed70ed34ebcfca48eb5f2e32b65373c840` |

**The runtime row is a review snapshot. A preparation documentation commit changes the runtime fingerprint through `git_commit`. Regenerate the external pending declaration and final runtime record after the last clean published commit. Never approve a stale G3 or prepublication runtime.** The runtime contains exact source files, Python/executable, package inventory, lock hashes and host, but is not binary-build authentication. The external `runtime-final.json` and pending approval must identify the final published preparation commit; they are deliberately not committed into that same branch, avoiding a self-changing Git binding.

All 24 historical source pins, all 42 explicit lock requirements and all 63 installed package modules match. Metadata/runtime inspection from `/tmp` repeats byte-identically without importing Torch. Production help succeeds; missing approval is refused with exit 2 before scientific I/O/output creation. The unsigned pending declaration is also refused.

**OBSERVED:** 92 of 92 native May–July GOES-16 files match pinned bytes/SHA-256 and product identities, totaling 27,280,082 bytes. Audit instrumentation recorded exactly these 92 scientific input paths and no weights/excluded science file. Source bytes were reverified after preparation and at the task's after-check snapshot. The grid has 132,480 minute bins, no gaps/duplicate timestamps, over `[2024-05-01T00:00Z, 2024-08-01T00:00Z)`; August 1 is the exclusive July end, not August-data access.

Training/validation retain 3,609/412 origins and exclude 327/68; contexts and targets stay entirely within their own half-open partitions, with the unchanged zero embargo and complete masks. Normalization uses each valid unique raw training cell once: 118,080 raw training rows, channel counts 113,926/116,125, means `[-6.975172762067082, -5.475295794509493]`, population scales `[0.5742480619158656, 0.34159742190236464]`. The fixed stride-one subset uses 20,000 of 108,199 eligible windows. Dataset, forecast, combined/per-role splits, training, normalization, subset and validation-content identities match G3 exactly; all eight exact approval fields are in the external `owner-approval.pending.json` and tracked [native evidence](evidence/phase2_v2_g4_native_preflight.json).

Native/QC/support/normalization revalidation took 15.57 seconds including external monitoring, with sampled process-group RSS peak 444,628,992 bytes. Torch import was explicitly blocked. **INFERRED:** this preparation route fits the resource limits. **UNKNOWN:** actual fitting, optimizer, reload, prediction, report costs/output volume and whether the full pilot completes. The attempt ceilings sum to 13,800 seconds; the 7,200-second total takes precedence. No fitting benchmark was run.

The exact matrix remains two seeds `1261866429, 1291916211`, each with one shared SSL process, five primary controlled arms, TCN, linear and two alternate-loss controlled arms: **20 processes, 18 selected models, 14 primary plus four alternate**. Each linear process contains the unchanged seven-λ candidate path, 14 candidates across seeds. Dependencies reuse the same seed's sole sealed SSL artifact. Per-job model-configuration and full descriptor fingerprints are recorded in [the verification record](evidence/phase2_v2_g4_verification.json); complete exact recipes remain in the unchanged ratified JSON.

**DOCUMENTED:** Protocol v1 fixes retrospective/exposed development scope, QC, partial-minute acceptance, calendars, schedules, validation selection, losses, limits and descriptive reporting. **OBSERVED:** the current inputs and code/tests match those controls. **INFERRED:** the intended guarded path preserves these comparisons when approved inputs remain unchanged. **UNKNOWN:** operational delivery/upstream causality, unrecorded exposure, generalization and any JEPA benefit. No new scientific conclusion or protocol decision is made.

## Cleanup, publication, failures and execution risks

Normal supervised guards have fresh test coverage: serial scheduling, worker plus descendants sampled RSS, thread settings, CPU float32/determinism, fixed timeouts, total deadline through finalization, zero retries, first failure leaving pending jobs, sealed same-seed SSL reuse, weights-only reload parity, source/runtime/data drift rejection, both guarded runs ending at `D_LOCKED`, complete-cohort reporting, collision protection and publication withdrawal. Both reports and final accounting become visible only through one exclusive directory rename after all 20 processes and 18 models pass. Failures preserve evidence and retain `INCOMPLETE`; they do not publish the completed comparison or permit automatic resume.

**Newly OBSERVED supervisor-loss limitation:** direct SIGTERM/SIGHUP sent only to the supervisor bypasses Python cleanup and leaves its separate-session worker alive. Two synthetic sleeper probes reproduced exit -15/-1, a live orphan and a persisted `running` attempt. The probes then killed their own exact groups and confirmed zero live group processes. No scientific/model/pilot execution occurred. The existing Ctrl-C/KeyboardInterrupt and deadline cleanup regressions pass; those results must not be generalized to all process termination.

**Operator condition for the current source:** use a foreground, owner-controlled supervisor, cancel with SIGINT/Ctrl-C, and avoid a launcher/terminal shutdown that only sends TERM/HUP. On any supervisor loss, inspect the exact recorded process group and safely stop it, preserve incomplete evidence and do not resume or launch further jobs. If this procedure cannot be supplied/accepted, G4 is blocked pending a separately reviewed pilot-only signal-cleanup correction and fresh identity binding. SIGKILL, host loss and monitor loss cannot be described as continuously supervised execution. No source fix is silently included here.

The known NetCDF4/NumPy size-changed RuntimeWarning remains reproducible when **NumPy is imported first**, and strict warning-as-error import exits 1. NetCDF4-first ordinary/strict imports exit 0. Native decoding and frozen identities pass; this does not prove binary correctness or resolve the warning. No warning suppression, package upgrade or lock change was made.

RSS sampling can miss brief peaks; library threads are not an OS thread cap; termination/polling overhead is not a hard realtime bound. RSS applies to live worker/descendant scope, not a whole-machine allocation guarantee. The declaration itself reserves no CPU/RAM/disk. These limitations require explicit owner acceptance with the known warning and unknown fitting feasibility.

Reporting remains **DEVELOPMENT FEASIBILITY ONLY — EXPOSED MAY–JULY2024 — POST-SELECTION VALIDATION — ONE FOLD/TWO SEEDS — DESCRIPTIVE_ONLY — INFERENCE_UNAVAILABLE — NO_VALIDATED_REPLACEMENT**. All 10 fixed comparisons are retained; all six sampling-inference fields remain null. Predictive intervals remain descriptive diagnostics. No significance, acceptance, operational, fresh-test or generalization conclusion is authorized.

## Executed verification and preservation

- Parent nonfitting suite: **229 passed, 96.51 seconds**. Exact command and local log hashes are in [the verification record](evidence/phase2_v2_g4_verification.json).
- Independent scientific review: canonical hash/source review, then **111 passed, one deliberately deselected, 7.72 seconds**, for protocol/reporting/descriptive checks. No native decoding or model fitting by that reviewer.
- Independent technical review: static source/protocol/test audit. Parent separately replayed its TERM/HUP finding with synthetic sleepers.
- Normal installation/source/locks, repeated outside-checkout metadata, help, missing/pending approval denials, native revalidation, import diagnostics, `git diff --check`, actual ignore rules and latest-three-commit prohibited-data audit were executed.
- Full project suite was not run because it includes fitting outside preparation authority. No actual real-data training/prediction/reload path or fitting benchmark was run.
- All 92 raw files and nine historical checkpoints retain their before/after byte sizes and hashes; all 101 paths match actual ignore rules. No raw science products, arrays, weights, credentials or pilot output are included in preparation publication. Other scientific datasets were not exhaustively rehashed and were not opened/written.
- Protected local/remote `main` remains `1a4991da4dda9676caeb1d7e35a03408528c3188`. No branch/worktree was created, deleted, reset or archived; no PR or merge was attempted. The separate SoLEXS worktree changed concurrently and remains untouched.

## Exact G4 authorization handoff

The external `owner-approval.pending.json` has exactly the existing validator's 18 fields and the measured identities. After publication it is rebound to the final clean published HEAD; `runtime-review.json` remains the historical prepublication snapshot. It deliberately uses status `PENDING`, null owner/time, execution/fitting false and reservation false. It cannot execute. No owner signature, approval timestamp or active reservation was fabricated.

Before any approval/start:

1. Publish only the reviewed V2 preparation records to the existing branch; concurrent SoLEXS work is owner-confirmed and remains untouched.
2. From a **fresh interpreter at that final clean published HEAD**, recompute `runtime_identity(SOURCE_ROOT)`, rerun the unchanged protocol/source/installed checks, recheck actual May–July data/support and current memory/storage, and confirm the output remains absent. Write `runtime-final.json` and update the pending declaration outside source. Do not commit the final runtime record into the same branch: that would change the commit it binds.
3. Owner explicitly activates the named reservation/window and accepts its exact roots, limits, import warning, unknown fitting feasibility and supervisor-loss procedure. If that cancellation procedure is unavailable, remediate/review/rebind before proceeding.
4. Owner separately authorizes **one** bounded 20-job May–July fitting pilot with fixed validation prediction/reload/selection and descriptive-only post-selection reporting. Name the final commit/runtime/source/design/configuration and exact data object.
5. Only after that explicit authority, create an external approved declaration by changing exactly `approval_status` to `APPROVED`, `authorized_by` to the owner's supplied name, `approved_utc` to its actual past/present UTC time, execution/fitting to true, and `host_reservation.reserved` to true; finalize its `rationale` with the activated window and accepted operator commitments. Test release remains false. Preserve all other measured bindings. `validate_execution` can then check it without loading science or starting jobs. Local claims are not authenticated signatures.

Suggested exact owner statement, with the final binding supplied by the external record:

> I activate reservation SolarJEPA-G4-MBA-M2-20261017-01 for one immediate, continuous local MacBook Air M2 session. I approve the exact final clean published V2 commit, runtime, source, Protocol v1 design, ordered configurations and eight-field May–July data identity in the external execution record. I authorize one bounded 20-job pilot, including fitting, validation prediction/reload, the frozen validation selection and descriptive-only post-selection reporting. I accept serial CPU float32, four threads, 2 GiB sampled worker-plus-descendant RSS, 7,200 seconds total including preparation/finalization, unchanged attempt ceilings, at least 1 GiB free output space, zero retries and no automatic resume. I accept the known NumPy-first NetCDF4 warning, unknown fitting feasibility and foreground SIGINT cancellation/orphan-recovery procedure. Any failure retains INCOMPLETE and pending jobs. No classical references, August, January, other datasets, new acquisition, checkpoint substitution, test release, confirmation or sampling inference is authorized.

After all gates are satisfied, the existing interface is `SOURCE/.venv/bin/python SOURCE/scripts/run_v2_goes_pilot.py --root SOURCE --execute --approval /absolute/external/owner-approval.json`. This is a description of the gated interface, **not an executed command or authorization**. Completion accounting is `OUTPUT/publication/pilot_accounting.json`; an incomplete engineering outcome uses `OUTPUT/pilot_failure.json` when the supervisor can finalize. Supervisor loss can leave only an unfinished ledger and requires operator investigation. Additional fitting requires reviewed amendment and explicit approval.
