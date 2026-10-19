# V2 controlled validation recheck plan

> Use Superpowers verification-before-completion and independent scientific,
> statistical and technical reviewers. This is a verification continuation of
> the ratified design and implemented pilot, not a new implementation milestone.

**Goal:** Revalidate the latest V2 checkpoint and produce an explicit execution
gate without fitting models or changing the protocol.

**Architecture:** Reuse the existing isolated V2 branch, installed package,
native loader, immutable protocol and nonfitting tests. Keep dated evidence
separate from historical reports. Preserve external pending declarations.

**Spec:** `docs/protocols/PHASE2_V2_DEVELOPMENT_PROTOCOL_V1.md` and its JSON design.

## Constraints

- Continue `codex/v2-experimental-validation-readiness` from `8e9ce06`; its
  execution validator requires this exact branch. Do not import unrelated
  baseline/UI changes or recreate completed infrastructure.
- Verify `main=origin/main=v0.1.0^{}` at `94a99cb` as the reference; preserve all
  existing branches, worktrees, untracked work, raw inputs and nine checkpoints.
- Preserve 20 jobs, two seeds, all schedules/controls, development-only data,
  CPU float32/four threads, sampled 2 GiB RSS, 7,200 seconds total, 1 GiB free
  output floor, zero retries and no automatic resume.
- No real-data models, optimizers, prediction/replay, fitting benchmarks, pilot,
  test release, new science acquisition, V3, live or SoLEXS work.
- Commit/push only reviewed V2 documentation/evidence; no PR, merge or main push.

## Review focus

Stale bindings after publication; changed native inputs or support; train-only
normalization; incomplete/selected report cohorts; inactive or stale resource
claims. Unknown fitting feasibility must remain unknown.

## Verification tasks

- [x] Fetch and inspect Git/tag/history, source, existing protocols and gates.
- [x] Snapshot raw/checkpoint/protocol identities and installed-source/lock match.
- [x] Recompute native QC/support/normalization with exact-input audit and Torch
  import denial; independently review the generated evidence.
- [x] Run existing nonfitting pilot/lifecycle and scientific/provenance regressions;
  inspect CLI metadata, help, denial and fresh runtime determinism.
- [x] Resolve independent findings. A genuine implementation defect requires
  root-cause diagnosis and a failing regression before a minimal fix; otherwise
  leave executable code unchanged.
- [ ] Publish dated readiness evidence and report, verify preservation/ignore
  rules/index/history/diff, commit and push the existing V2 feature branch.
- [ ] After the final clean published commit, create a new ignored external
  runtime/execution-binding and 18-field PENDING declaration. Preserve the old
  handoff; leave every authorization/reservation flag inactive. Verify refusal.
- [ ] Report exact blockers and request explicit owner reservation/approval at
  the pilot gate.

## Verification ledger

October 19: 257 pilot/lifecycle tests passed; 176 scientific/provenance tests
passed with one known NetCDF4 warning. Three independent audits found no new
must-fix defect. Native evidence matches all eight identities; no source or
protocol changes are required. New dated report/evidence are prepared. Final
publication and postpublication checks are recorded in the external execution
binding after the commit; no self-changing runtime binding is committed here.
