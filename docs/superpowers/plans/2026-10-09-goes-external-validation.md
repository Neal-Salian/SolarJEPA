# GOES external validation implementation plan

> **For agentic workers:** Use Superpowers TDD, parallel independent tasks, and verification before completion. The user's milestone specification authorizes autonomous execution and publishing to the research branch; no intermediate approval handoffs or PRs.

**Goal:** Establish a pinned, retrospective, model-independent external flux and catalog-onset evaluation foundation without fitting models.

**Architecture:** Reuse P2 immutable acquisition, GOES validation, TimeSeriesDataset, ForecastSpec, FutureGrid, ForecastTargets, ForecastPrediction and causal test windows. Add isolated catalog, alignment, external metric and uncertainty adapters. Existing trajectory scoring binds training and evaluation dataset identities, so do not spoof those identities or change that invariant.

**Tech stack:** Existing Python/NumPy/pandas/xarray/NetCDF dependencies only.

**Spec:** User's 18-section GOES External Validation and Solar Flare Benchmarking milestone request; scientific decisions and evidence recorded in GOES_EXTERNAL_VALIDATION_RESEARCH.md.

## Global constraints

- Exact base 656e540162c635d4c2274b4469ae11247290f986; only research/goes-external-validation may receive commits/pushes.
- No fitting, model training, P3 imports, existing baseline execution, threshold optimization, merges, or PRs.
- July 2024 raw files, split/experiment/config identities and all other workstreams remain untouched.
- Official raw bytes remain ignored and immutable; unknown metadata/end times/completeness stay unknown.
- January 2025 selected a priori for same-spacecraft forward temporal generalization. All external observations have evaluation-only status.
- Science products are retrospective reprocessing: actual operational latency and preprocessing causality remain UNKNOWN. Live benchmark claims are blocked.

## Review focus

1. Revised science processing can use adjacent-day inputs: do not assert live as-issued causality.
2. Sequential flares may have absent ends; annual peak-indexed records can cross dataset bounds. Preserve and flag, never impute.
3. Catalog final class is retrospective future truth, never a context feature. Maturity includes the complete peak minute.
4. Model failures/partial output must not shrink the target mask. Contract snapshots reject mutated or mismatched identities.
5. Repeated alarms, rare/zero events and temporally dependent errors require explicit matching/undefined scores and paired block units.

## Pre-flight interfaces

- Catalog -> alignment: immutable FlareEvent carrying original ID, UTC start/peak/optional end, recorded class, source, saturation, sequential counter and catalog hash; no flux-derived replacement labels.
- External builder -> alignment/metrics: unchanged P1/P2 TimeSeriesDataset and FutureGrid, explicit external dataset fingerprint.
- Metrics -> uncertainty: chronological per-origin paired scalar losses; resample UTC calendar blocks jointly. Retain all leads/channels/masks within each origin before reducing.
- All tasks own separate files. Independent scientific/code reviews after integration of files in this worktree; no branch merges.

### Task 1: Official inputs and catalog (research + catalog subagent)

- [x] Verify Git state, preserve original checkout, create/publish isolated branch.
- [x] Establish inherited full suite (1084 passed; one unsuppressed binary warning).
- [x] Research candidate availability and select January 2025 before external scoring.
- [x] Reuse acquire_history/verify_history; validate measured coverage/quality with validate_goes_files.
- [x] Write failing synthetic parser/integrity tests, implement data/flare_catalog.py and CLI/config/manifest, run GREEN tests.
- [x] Verify annual official catalog+metadata bytes; retain disagreements with operational SWPC as separate evidence.

### Task 2: Catalog alignment and onset labels (GOES research subagent)

Files: evaluation/flare_alignment.py; tests/test_flare_alignment.py.
Interfaces: align_events(events,dataset), label_onsets(events,dataset,grid,minimum_class,catalog_interval).
- [x] Write RED tests for UTC boundaries, unknown ends, overlaps, quality gaps, provenance, saturation, source mismatch and peak maturity.
- [x] Implement separate retrospective label artifacts, never modify features; new catalog starts in [issue, end), final class threshold C1/M1/X1 fixed a priori.
- [x] Run targeted GREEN tests and actual-data alignment; retain completeness limitations.

### Task 3: Model-independent evaluation (root + protocol subagent)

Files: data/external_validation.py; evaluation/external_flux.py, event_matching.py, uncertainty.py; scripts/prepare_external_validation.py; external config and focused tests.
- [x] RED tests for external/frozen interval separation, deterministic construction, causal contexts and no training slice; implement adapter using P2 source validation and a single test partition.
- [x] RED hand-calculated flux errors/coverage/skill and mismatched prediction identity tests; implement external flux scoring without TrainingSlice, reuse strict contract snapshots and alignment.
- [x] RED alarm matching and block-bootstrap tests; implement one-to-one deterministic maximum-cardinality alarms and explicit UTC calendar-block paired uncertainty.
- [x] Execute real preparation only, with no model predictions/scoring; publish small observed summaries and reproducible fingerprints in tracked manifest.

### Task 4: Verification, reporting and publication (root + independent reviewers)

- [x] Run targeted and full inherited suites; retain warnings and investigate failures.
- [x] Install source snapshot outside original environment, smoke CLI/import, reproduce twice in distinct no-replacement output dirs and compare scientific identities.
- [x] Independent code and scientific reviews; regressions for actionable findings.
- [x] Reports include literature/official source evidence, uncertainties, exact input identities, reproduction and future P3 interface.
- [x] Verify preservation snapshots, raw ignores/index/history, complete diff and remote protected refs.
- [x] Focused Conventional Commits; push only research branch; verify synchronization/clean state; stop for human review.

## Execution evidence

Initial worktree: /Users/nealsalian/.codex/worktrees/goes-external-validation/SolarJEPA. Original checkout remains at P2 with untracked resources preserved. Research agent notes and detailed command logs live under ignored results/external_research. The final implementation report records verified test and artifact identities; historical reports are not rewritten.

Final source suite: 1,272 passed, one inherited warning; focused suite: 188 passed,
one inherited warning. Normal installed preparations C/D produced 13 byte-identical
artifacts. Independent reviews resolved all actionable findings. Publication at
bd128295c8529e064473e483751ca747de2f57a5 was directly verified on origin with
0/0 upstream divergence, clean research worktree and unchanged protected refs.
This closing ledger update is the only subsequent change; source remains at
the verified 8f41ab2 implementation snapshot. Human review is the next action.
