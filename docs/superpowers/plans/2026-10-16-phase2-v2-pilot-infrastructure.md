# Phase 2 V2 pilot infrastructure implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development and test-driven-development. User explicitly authorized implementation and specialized agents; execution remains prohibited.

**Goal:** Connect the existing V2 components into a guarded, reproducible Protocol v1 pilot without executing scientific fits or experiments.

**Architecture:** Keep the frozen design unchanged. A protocol/approval layer binds exact jobs and runtime identities; a serial driver delegates fresh workers to the existing supervisor, then imports sealed results into separate guarded primary and alternate DevelopmentRuns. Workers reuse the existing loader, trainers, weights-only serialization and canonical evaluation adapters. Strict reporting derives descriptive payloads from complete canonical records.

**Tech stack:** Existing Python, NumPy, Torch and Unix supervisor; no new dependencies.

**Spec:** `docs/protocols/PHASE2_V2_DEVELOPMENT_PROTOCOL_V1.md` and canonical design SHA256 `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624`.

## Global constraints

- Infrastructure only; no real-data training, pilot experiments, full V2 evaluations, fitting benchmarks or checkpoint modification.
- Existing isolated `codex/v2-experimental-validation-readiness` branch only; no main repair, PR or merge. Published upstream already matches a097946.
- Exact 20 processes / 18 selected models / 2 shared SSL artifacts; primary14 and alternate4 guarded runs. Two fixed seeds; pinned May–July data only; January2025 and August2024 excluded.
- CPU float32/four threads; 2GiB sampled RSS; 7200s total; fixed job ceilings; 1GiB free output storage before launch/each job; zero retries or automatic resume.
- Preserve `NO_VALIDATED_REPLACEMENT`; no test release, sampling inference or unplanned comparisons.

## Review focus

1. Missing, fabricated, stale or broadened execution declarations must fail before data/model access or output mutation.
2. Changed source/environment/config/data or sealed dependency must fail; no fallback SSL recomputation.
3. Failure/interruption/disk exhaustion must retain failed/pending jobs and refuse complete reporting or automatic resume.
4. Report schemas must reject arbitrary fields/inference aliases while allowing marginal predictive interval diagnostics.
5. Every planned model/seed must retain exact paired support and reload parity; no cohort shrinking.

### Task 1: Protocol, authorization and supervised driver

**Files:** create `experiments/v2_pilot_protocol.py`, `experiments/v2_pilot.py`, `scripts/run_v2_goes_pilot.py` and corresponding tests.

**Interfaces:** `load_protocol(root)` returns validated register; `runtime_identity(root)` returns clean source/environment identities; `validate_execution(root, approval)` validates external G3/G4 approval against actual runtime and design before access. Worker receives root, approval file, job id, supervisor directory and writes cwd artifacts. Reporter `build_report(design, payloads, *, accounting)` consumes mapping descriptor job IDs to model/evaluation payloads.

- [x] Write failing tests for absent authorization, design/config drift, exact matrix, disk gate, incomplete/no-resume policy and clean metadata CLI.
- [x] Implement strict protocol/approval validation and metadata-only default CLI. No execution approval is created.
- [x] Integrate exact process matrix, source/environment binding, zero-retry limits and storage gates with supervisor.
- [x] Finalize complete sealed results through primary14/alternate4 DevelopmentRun guards at D_LOCKED; report failures separately.
- [x] Run targeted tests and record results; commit only owned files when root requests.

### Task 2: Production worker

**Files:** create `experiments/v2_pilot_worker.py` and worker tests.

**Interfaces:** CLI `python -m solar_flare_jepa.experiments.v2_pilot_worker --root ROOT --approval FILE --job-id ID --supervisor-directory DIR`; `execute_job(root, approval, job, directory, supervisor_directory)` calls authorization before scientific access. Artifact names `result.json`, `selected.pt` or `ssl.pt`, plus dependency/source/environment binding metadata.

- [x] Write failing tests proving unauthorized requests touch no loader/trainer, exact typed configs and bad dependencies are rejected without fitting.
- [x] Assert CPU/float32/four threads/deterministic seeded setup before model construction.
- [x] Load frozen development inputs and verify historical dataset/split/training/normalization identities.
- [x] Use existing SSL/controlled/TCN/linear fit functions, immutable SSL dependency verification and weights-only reload.
- [x] Compare full canonical validation predictions before/after reload exactly; preserve model budgets, curves and diagnostics.
- [x] Run synthetic/non-fitting tests only; never run production fit path in this milestone.

### Task 3: Strict descriptive reporting and scientific review

**Files:** create `experiments/v2_pilot_reporting.py` and reporting tests; independent review after implementation.

- [x] Write failing synthetic tests for incomplete matrix, extra aliases, changed support and null inference fields.
- [x] Use canonical descriptive comparison for all7 primary, alternate J–S and two bundled within-arm loss contrasts; retain per-model/seed native+dex calibration/median-point diagnostics and pooled errors.
- [x] Enforce an exact generated report schema, mandatory feasibility header and canonical null inference fields; reject arbitrary payload publication.
- [x] Record actual SSL once versus attributed recipe costs separately, budgets, selection, resource and environment evidence.
- [x] Independently review scientific defaults, temporal/QC isolation and approval boundaries; resolve findings with regression checks.

### Task 4: Verification, ratification record and publication

- [x] Record user's G1 ratification/G2 infrastructure authorization outside immutable design; leave G3/G4/G5 pending.
- [x] Run targeted integration/unit tests, synthetic fixtures, normal installed imports and CLI denial/metadata checks. Exclude tests performing optimizer fits or scientific experiments.
- [x] Report actual host/disk/environment readiness and unknown workload feasibility; preserve checkpoints/worktrees/remote refs.
- [x] Inspect diff/status/history, `git diff --check`, actual ignore paths and staged data policy; commit focused Conventional Commits and push this branch only.

## Progress ledger

- Initial audit: clean V2 branch a097946 matches live remote; remote main1a4991d readable, local main cloud placeholder remains UNKNOWN and untouched, as documented in readiness audit. Presentation untracked work preserved.
- Full design digest independently recomputed and17 decision consistency confirmed. Historical protocol files and existing preflight remain scientific design evidence, not execution authorization.
- Validation environment located at existing M5 `.venv` (Torch2.6.0/NumPy2.2.6); global Python packages differ and must not be used for execution readiness claims.

- Implementation review found and fixed actual supervisor-report schema/preparation-accounting drift, SSL metadata-seal drift, and runpy worker source-attestation incompatibility. Historical provenance code remains unchanged. Complete publication is staged and atomically exposed; finalization failures preserve incomplete diagnostics.

- Independent review PASS:111 pilot tests in27.07s; no unresolved Critical/Important findings. Production fits and workload/native/support readiness remain untested. Verification deliberately excludes fitting experiments. Branch publication follows the user’s explicit commit/push authorization; no PR, merge, worktree deletion or protected-ref repair.

- Final durable verification:252 passed,1 fitting benchmark deselected,no warnings; normally installed metadata/denial/source-match checks pass. Logs and protected-state evidence persist under ignored results/phase2_v2_infrastructure_20261016. All9 checkpoint hashes and all12 current other-worktree statuses match retained authority.
