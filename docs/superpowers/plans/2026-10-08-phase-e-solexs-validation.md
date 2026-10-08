# Phase E SoLEXS scientific validation plan

> **For agentic workers:** Use Superpowers executing-plans for the coordinator's sequential work and dispatching-parallel-agents for independent read-only research. The user has authorized execution and publishing on the Phase E branch.

**Goal:** Establish what the two registered SoLEXS archives can scientifically support, preserving blocked conclusions where applicable evidence is missing.

**Architecture:** Reuse the existing bounded native FITS inspector, readiness probe and exploration API. Keep scientific source review separate from observed byte/array diagnostics. Publish compact provenance and gate decisions; keep raw inputs and detailed generated outputs ignored.

**Tech stack:** Existing Python environment, Astropy, NumPy, pytest, Paperclip, primary-source web retrieval, Git.

**Spec:** User's Phase E milestone instructions; repository `AGENTS.md` and `docs/DATA_STORAGE.md` apply except that the exact P2 base and explicit Phase E branch override the default main-based workflow.

## Global constraints

- Exact base: `656e540162c635d4c2274b4469ae11247290f986`.
- Only publish to `research/phase-e-solexs-validation`; no merges, P3 changes, model development or training.
- Preserve original data, existing manifests' historical meaning, local audit files and Paperclip skill.
- Native sequence agreement cannot authorize UTC conversion, response indexing or corrected exposure.
- Sources must have versions/locators, applicability and uncertainty; no fabricated observations or citations.

## Review focus

- Product version, processing version and tools version must remain distinct.
- Candidate calibration structural compatibility must not be promoted to mission applicability.
- Empty GTIs, NaNs and absent dates must not become synthetic measurements or quality labels.
- Provenance hashes prove byte identity, not portal authenticity or scientific validity.
- Forecast readiness requires causal availability, stable quantities and evaluation support beyond loadability.

## Tasks

- [x] Inspect/fetch Git, verify P2, create native isolated worktree and publish the named branch with upstream.
- [x] Read installed Superpowers and repository Paperclip instructions; decompose independent literature, timing/quality and calibration research.
- [x] Audit source/tests/configuration/manifests/history and run the inherited full test baseline.
- [x] Reproduce complete native integrity diagnostics, response comparison and gated native exploration with the isolated source and existing raw-data root.
- [x] Recheck every available pinned local source and archive identity; record software/source versions and missing dependencies.
- [x] Independently verify primary literature and mission documentation; decide gates E1–E6 with explicit subrequirements.
- [x] Implement only a reproduced, evidence-justified validation defect if discovered; use a failing targeted test first. Otherwise preserve executable code and report why no new utility is needed.
- [x] Write scientific validation, evidence matrix and implementation reports; extend the existing requirements manifest without altering its historical fields. Store only compact provenance summaries.
- [x] Conduct independent scientific/implementation review and resolve substantiated findings.
- [x] Run final scoped verification, inspect exact inventory and ignored/indexed paths, verify protected refs and original raw hashes, commit explicitly staged files and push only Phase E.
- [x] Verify upstream synchronization and stop for human review; report blockers and next scientific milestone.

## Execution notes

Three read-only investigators cover the five suggested scientific domains because the available concurrency limit is four including the coordinator. Independent final review follows once a slot is available. Implementation is conditional on reproduced defects; tests of unchanged artificial fixtures establish software behavior, not instrument validity.

## Verification ledger

- Inherited baseline: 1,084 passed, one retained warning; native subset: 109 passed.
- Final full suite: 1,084 passed, same warning, 79.20s. Strict-warning diagnostic: one inherited netCDF4 import failure.
- Existing inspector/probe/exploration reproduced real archive findings; no executable defect justified changes. No new scientific algorithm or test was needed.
- Fresh final review: no actionable findings; review limits are recorded in the implementation report.
- Historical requirement fields, all original raw inputs, local audit/skill and prior scientific/experiment identities were rechecked unchanged.
- Authorized finishing path is feature-branch publication and human review only; no merge, PR creation, branch deletion or worktree cleanup.

- Scientific evidence publication: `dc61dd0803f47cfd0dbf4f44ecaf7bc470948003`, local/upstream/remote equality verified; final closure records this result without changing the scientific verdict.
