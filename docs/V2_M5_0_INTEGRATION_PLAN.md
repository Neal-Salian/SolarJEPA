# V2 M5.0 Pilot Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. Execution is already delegated within the authorized M5.0 milestone; this document does not request or grant pilot approval.

**Goal:** Make the development-only GOES pilot concrete and reviewable through verified inputs, a deterministic job plan, an approval register, executable resource controls and preflight evidence, without real-data model fitting.

**Architecture:** Reuse the M4B scientific/model contracts and the normally merged GOES integrity implementation. Add a narrow May–July loader that validates the complete allowlist before opening raw bytes, a planning/preflight layer with no fitting entry point, and a reusable process supervisor exercised only on synthetic child jobs. Keep data, processing and execution logic independent of any frontend.

**Tech Stack:** Existing Python/NumPy/pandas/xarray/netCDF4 code, standard-library subprocess/process accounting and pytest; existing Torch trainers remain uncalled by preflight.

**Spec:** The user's M5.0 instructions, repository `AGENTS.md`, preserved [M4B handoff](V2_M4B_M5_HANDOFF.md), [M4B interface reconciliation](V2_M4B_INTERFACE_RECONCILIATION.md), [M4A training proposal](../configs/v2_proposed/training_protocol_proposal.json) and [historical pilot proposal](../configs/v2_proposed/feasibility_pilot_proposal.json). Historical proposals are inputs, not approvals. The separate M5.0 amendment records changed scope rather than rewriting them.

## Global constraints

- Work only on `feat/v2-m5-pilot-readiness` in the managed M5 worktree. Preserve `main`, M4A, M4B, M3.1, GOES restoration and other existing branches; no force push, history rewrite, branch deletion or integration into `main`.
- M5.0 authorizes audit, implementation, tests, explicit May–July reuse and no-fit pipeline checks. It authorizes no real-data model training, pilot execution, downloads, January 2025/sealed data access, test windows/scoring/release or new scientific conclusion.
- Active raw selection is exactly the three existing May–July manifests, 92 pinned files and 27,280,082 bytes. Preserve the source copies; copy only explicit pinned paths to the isolated worktree, reverify and keep all raw bytes ignored.
- Use only train `[2024-05-01T00:00:00Z, 2024-07-22T00:00:00Z)` and validation `[2024-07-22T00:00:00Z, 2024-08-01T00:00:00Z)`; the new loader constructs no test partition.
- Preserve native two-channel W/m² flux, 60-second record-start bins, existing strict status/electron quality masks and missing-value masks, 120-step context, 30-step horizon, stride 30, complete eligibility, log10 transform and reference 1 W/m². Fit normalization on unique valid training rows only. Operational latency remains UNKNOWN.
- Preserve proposed paired seeds `[1261866429, 1291916211]`, full primary controlled-arm cohorts, separate loss-comparison cohorts and proposed budgets. Record pending approvals rather than treating a successful preflight as consent.
- Reporting remains `DESCRIPTIVE_ONLY`, `INFERENCE_UNAVAILABLE`, reason `NO_VALIDATED_REPLACEMENT`; classical fit acceptance remains `POLICY_UNAVAILABLE`. No confidence intervals, p-values, significance or superiority claims follow.
- Supervisor ceilings are proposed 4,294,967,296 bytes RSS, 7,200 seconds cumulative wall time, four threads and at most one identical infrastructure retry. Job timeouts are SSL 300 seconds, neural downstream 600 seconds, TCN/quantile-linear 1,800 seconds. These controls do not themselves authorize real jobs.

## Review focus

1. A later unauthorized manifest, mode, calendar or forecast mutation must fail before the first raw byte is opened, including when an earlier selected manifest is valid.
2. A manifest/config pin mismatch or symlink must fail closed; no adoption, silent repair or source replacement is permitted.
3. Existing broad GOES defaults must never become the M5.0 entry point: they select August, and `inventory` enumerates the whole managed product tree.
4. Timeout/RSS/monitoring failures must stop child jobs, retain/quarantine evidence and preserve the same code/config/seed identity across the single allowed retry and resume.
5. Missing approvals, changed fingerprints or tampered completed artifacts must remain visible and block execution; a successful no-fit data check must still report `PILOT_NOT_AUTHORIZED`.

---

## Verified starting state and integration

**OBSERVED:** M4A is `ac3428f910b36b7f10cc0fbb0740ce6de62df5a7`, M4B is `2e3f87111ab7c3a881064aaad9dbd6d6298c69cd`, GOES restoration is `8a9c98db66eca545eeaf062f5fb07e47ec6bdc63`, and M3.1 is `5e88f3a7109296c9475378b77be0257a4f9363ab`. M4A is an ancestor of both M4B and GOES restoration and is their merge base. M4B contains M2 `94cae59398e52a65074ec66c73ad94bd47ca8867`; M3.1 is not an ancestor of M4B.

**OBSERVED:** The M5 branch was published with upstream at M4B before work. The normal two-parent merge succeeded as `c8da8d7ff0412584be1d2a5b648ea41140e923b4`, with parents exactly M4B and GOES restoration, subject `chore(v2): integrate verified GOES restoration for M5 readiness`. The two branches changed no common paths after M4A. The merge changes 14 GOES paths relative to M4B; its only changed existing production API is optional acquisition statistics. It introduces no raw science files. The exact file list and protected local/origin tracking refs are recorded in [the Git/source audit](evidence/v2_m5_0_git_audit.json).

**OBSERVED:** M4B already retains byte-identical M3.1 report and summary artifacts, while excluding the experimental inference implementation. Their SHA-256 roots are:

| Artifact | SHA-256 |
|---|---|
| `docs/V2_M3_INFERENCE_REMEDIATION_REPORT.md` | `3cb051f52bebf02e5233dec26dcd4c7e1965b755d49e109674ab3a7f1ccd471e` |
| `docs/evidence/v2_m3_inference_summary.json` | `f4ed208cad6e83d2e24fcf2a2d41dcf47e30a44ca50a4f1691e7fd080b38d71a` |

Do not merge M3 experimental code. M4B executable adapters and development publication already preserve the no-replacement/descriptive-only outcome. Thirteen preserved M4A/M4B/M3/GOES artifact identities are recorded in the audit JSON and checked against their source commits.

**OBSERVED source availability:** `/Users/nealsalian/Desktop/SolarJEPA` contains all 92 May–July files under `data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/{05,06,07}/`. Explicit path-by-path size and SHA-256 checks found no missing files, mismatches or symlinks. Initial M4B and M5 worktree audits found zero of these raw files there. Reuse them rather than download or broad-copy the source data tree.

| Selection | Files | Pinned bytes | Observed minute bins | Valid A / B bins |
|---|---:|---:|---:|---:|
| May 2024 | 31 | 9,169,020 | 44,640 | 42,695 / 42,696 |
| June 2024 | 30 | 8,910,715 | 43,200 | 43,074 / 43,195 |
| July 2024 | 31 | 9,200,347 | 44,640 | 42,329 / 44,406 |
| **Active M5.0 total** | **92** | **27,280,082** | **132,480** | **128,098 / 130,297** |

**OBSERVED:** Original `verify_history` and M4B `validate_goes_files` passed for each of those three manifests, with no missing timestamp bins. Native attributes agree on g16/EXIS, Level 2/PT1M, `xrs04_avg.py` version `[2, 4]`, electron-contamination LUT v3 and production commit `162d7a2889b4f88020950d212b0dfcc40f7937b2`. `date_created` is in December 2025 and is a production timestamp, not the May–July acquisition date. Valid partial-minute sample counts remain accepted under the existing policy; changing that scientific rule requires a decision.

**DOCUMENTED historical distinction:** GOES restoration reports describe 123 May–August files and 36,535,474 bytes. The additional 31 August files are outside this M5.0 active selection. August was already exposed/scored in V1; old “untouched holdout” prose is historical and must not be promoted into current fact. This audit did not reopen August, January 2025 or sealed raw bytes.

**DOCUMENTED execution-environment correction (root-reported):** The initial baseline attempt returned 1,581 passed / 2 failed / 1 warning in 125.76 seconds. Root identified an older package in the shared installed environment and a concurrent merge that changed loaded source, so that run does not establish a clean M4B baseline. Root then created the isolated M5 `.venv`, installed unchanged M4B and repeated the baseline: **1,583 passed / 1 warning in 120.77 seconds**. Preserve both outcomes and the correction in the final verification report; this documentation subtask did not execute either test run. The original environment was not replaced. Subsequent installation/import checks and test commands must use the isolated M5 environment and a stable source checkout.

### Task 1: Preserve provenance and reuse the bounded source selection

**Files:** `docs/evidence/v2_m5_0_git_audit.json`, this plan, ignored raw copies at the exact 92 manifest paths; historical manifests and reports stay unchanged.

**Interfaces:** Consumes pinned monthly manifests and source identities; produces source-identity evidence and verified isolated-worktree copies for the loader. Root owns Git operations and raw copying.

- [x] Inspect branch/ref/history/status, ancestry, source, tests and GOES diffs before edits; preserve unrelated untracked desktop work.
- [x] Verify normal merge identity, 14-path file list, protected tracking refs and preserved report SHA roots; write compact audit evidence.
- [x] Verify only the explicit 92 source paths with original hash/native APIs. Do not run broad restoration/validation defaults.
- [x] Copy those 92 paths into the isolated worktree without source mutation, overwrite or hard-link aliases; reverify there.
- [x] Check actual copied paths with `git check-ignore -v`, and inspect the index/history for prohibited science payloads before publication.

### Task 2: Add the development-only data boundary

**Files:** Create `src/solar_flare_jepa/data/goes_v2_development.py` and `tests/test_goes_v2_development.py`; minimally factor reusable assembly in `src/solar_flare_jepa/data/foundation.py` while preserving generic loader behavior.

**Interfaces:** `load_development(root, *, mode='development', manifests=None, forecast=None, splits=None, dataset_fingerprint=None, split_fingerprint=None, split_fingerprints=None, max_train_windows=20000)` returns `DevelopmentBundle` with `.dataset`, `.train`, `.validation`, `.training`, `.normalization` and `.evidence`. `forecast_definition()` and `split_definitions()` return the frozen allowed declarations. The preflight consumes this bundle/evidence without calling fitting. After successful source validation, the loader reuses NumPy-only `training.jepa.training_windows`; importing that module does not itself import Torch or fit a model.

- [x] Write and run failing tests for rejected mode/manifest order/August/January selection, changed calendar/test role/forecast fields, later manifest/config tampering, symlink and expected-fingerprint mismatch.
- [x] Implement complete metadata validation of all three exact manifest SHA-256/config identities before opening the first raw file. Reuse native verified assembly; construct only two `TemporalPartition` objects directly rather than using the generic three/four-split config path.
- [x] Verify synthetic full-calendar boundary fixtures: correct containment and retained support, train-only normalization, deterministic dataset/split fingerprints, no Torch call/fitting/optimizer and no test constructor. Separately test that loader import and the metadata/missing-file path do not import model modules.
- [x] Run `python -m pytest -q tests/test_goes_v2_development.py tests/test_training_foundation.py tests/test_forecasting_splits.py`; confirm the relevant cases pass before integration.

The regression assertions are owned by `test_mode_rejected_before_any_source_access`, `test_unapproved_manifest_selection_rejected_before_source_access`, `test_calendar_and_partition_roles_cannot_change_before_source_access`, `test_forecast_mutations_rejected_before_source_access`, `test_later_manifest_tampering_blocks_before_first_raw_read`, `test_later_config_tampering_blocks_before_first_raw_read`, `test_manifest_symlink_is_rejected`, `test_complete_synthetic_calendar_has_only_two_windows_and_train_only_scaler` and `test_measured_fingerprints_are_deterministic_and_expected_ids_are_checked`.

### Task 3: Add canonical planning, amendment and pending approval register

**Files:** Create `src/solar_flare_jepa/experiments/v2_m5_preflight.py`, `scripts/preflight_v2_goes_pilot.py`, `tests/test_v2_m5_preflight.py`, `configs/v2_proposed/m5_0_preflight_amendment.json` and `configs/v2_proposed/m5_0_approval_register.json`.

**Interfaces:** `build_plan(root)` returns a deterministic JSON job plan/configuration fingerprint. `load_approval_register(root, configuration_fingerprint)` and `check_approvals(register, configuration_fingerprint)` validate the complete frozen decision set and return outstanding decisions. `inspect_data(root)` reports measured readiness without model fitting; metadata-only and missing-file paths avoid model-module imports. `preflight(root, verify_data=True)` combines these results and always retains the M5.0 execution prohibition; `verify_data=False` is the explicit metadata-only option. The CLI publishes immutable finite JSON evidence through the existing artifact publisher, exposes no pilot/training mode and exits 3 while blocked. Repeated preflight evidence is deterministic without generated timestamps; code commit/source, data, split and normalization identities remain explicit.

- [x] Write and run failing metadata tests before implementation: deterministic planning, exact two-seed primary cohorts, both linear paths, full pending decision coverage, malformed/invented approvals, source-proposal mutation, missing data and immutable evidence.
- [x] Pin both historical proposal SHA-256 identities in the amendment. Preserve the original proposals byte-for-byte. Record only May–July/train+validation as active; explicitly exclude August and any test release.
- [x] Enumerate 20 planned jobs: two SSL phases, ten primary controlled-arm jobs, two TCN jobs, two quantile-linear paths and four separate loss-comparison jobs. Each linear path includes seven lambdas, so record 14 candidate fits. No model job runs in M5.0. Classical policy remains blocked on its owner's evidence; schedule no classical fit.
- [x] Bind all 17 decision entries to the exact configuration fingerprint: D09/D10/D11, data access, August, quality, seeds, budgets, losses, checkpoint, TCN, linear, classical, failure/retry, statistics, test prohibition and reproducibility. Do not fabricate approval timestamps/approvers/references.
- [x] Run `python -m pytest -q tests/test_v2_m5_preflight.py`; verify metadata dry run reports `PILOT_NOT_AUTHORIZED`, `training_executed=false`, `test_release_permitted=false`, 17 outstanding decisions and explicit not-checked data status.
- [x] After isolated raw reuse, run the no-fit real-data preflight twice and compare scientific identities/support. Record actual retained/excluded windows, normalization, fingerprints, data readiness and limitations in the final evidence/report; success must still report pilot unauthorized.

### Task 4: Enforce future job budgets with synthetic subprocess tests

**Files:** Create `src/solar_flare_jepa/experiments/v2_resource_controls.py` and `tests/test_v2_resource_controls.py`.

**Interfaces:** `ResourceLimits(max_rss_bytes, total_wall_seconds, threads, max_retries=1, poll_interval_seconds=.05)`, `ProcessJob(job_id, command, timeout_seconds)` and `ProcessSupervisor(directory, jobs, *, code_fingerprint, config_fingerprint, limits).run()` produce a detached JSON ledger with per-attempt evidence. This is reusable infrastructure, not an M5.0 model-job launcher.

- [x] Write/run the missing-module failure and synthetic assertions before implementation. Use only small Python child commands, sleeps, controlled exits, bounded allocations and tiny artifacts.
- [x] Implement deterministic sequential jobs in separate processes, thread-limiting environment, active timeout/RSS accounting, process-tree termination, stdout/stderr capture, failure classification, quarantine and immutable successful artifacts.
- [x] Permit at most one infrastructure retry with identical job/code/config identity; numerical exits are terminal. Count consumed wall time across retries, interruptions and resume. Refuse changed identities, symlink/foreign output, tampered artifacts and unmonitored execution.
- [x] Run `python -m pytest -q tests/test_v2_resource_controls.py`; verify success/sealing/resume, invalid declarations, timeout/retry identity, terminal numeric exit, total budget, child RSS, monitoring failure and interruption quarantine. No real model process is launched.

### Task 5: Review, verify and publish only M5.0

**Files:** M5.0 implementation/tests/configs, this plan, the audit JSON and root-owned final readiness/evidence artifacts.

**Interfaces:** Consumes the completed loader, plan/register and synthetic supervisor; produces a reviewable readiness state and a focused M5 branch publication, not training or integration approval.

- [x] Inspect the actual diff for source reuse, scope boundaries, preserved historical reports and no unauthorized data/test/inference path.
- [x] Run targeted new/changed tests, integrated full regression, normal installed imports/CLI smoke checks and the explicit no-fit May–July pipeline smoke. Record exact commands, counts and results; do not substitute source presence or old test reports.
- [x] Obtain independent whole-change review and repair material findings; rerun the tests affected by repairs before the final verification.
- [x] Run `git diff --check`, inspect final status/index/history and raw ignore rules, recheck preserved source/report/ref identities, and verify all deliverables match the approval/provenance declarations.
- [ ] Commit focused Conventional Commits and push only `feat/v2-m5-pilot-readiness` with its existing upstream, within root's task authorization. Do not commit/push from this documentation subtask. No merge or push to `main` follows from readiness.

## Completion boundary

The final report must distinguish **OBSERVED** execution evidence, **DOCUMENTED** historical findings, **INFERRED** consequences and **UNKNOWN** scientific or operational properties. Report concrete readiness blockers and proposed next decisions. A real GOES pilot, model fitting, any test release and a scientific inference design each remain outside M5.0 until explicitly authorized. A healthy preflight validates infrastructure and supplied identities; it does not establish JEPA value or promote pending protocol settings into approved defaults.
