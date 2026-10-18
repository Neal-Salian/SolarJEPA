# GOES Near-Real-Time Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Execute continuously within the user's authorized scope.

**Goal:** Explicit, safe NOAA snapshot ingestion with diagnostics and an honest V1 replay boundary.
**Architecture:** Separate ingestion/cache and inference service; explicit CLI; existing UI and pinned core untouched.
**Tech Stack:** Python standard library, existing NumPy/pandas/V1 Torch runtime, pytest.
**Spec:** `docs/superpowers/specs/2026-10-18-goes-near-real-time-design.md`

## Global Constraints

- Preserve all five pages and historical prediction behavior; no V2, training or normalization edits.
- No live SWPC inference until authoritative time/QC/satellite parity exists; no override.
- 120 complete paired minutes; exact frozen V1 normalization/spec/checkpoint.
- Raw observations and checkpoints remain ignored; only code/tests/docs/provenance summaries tracked.
- Commit/push only `codex/goes-near-real-time-foundation`; no PR, merge or main push.

## Review Focus

- Repeated unchanged HTTP payload must preserve separate receipt times.
- Missing/zero/contaminated observations must never become valid model inputs.
- Transport headers must not become per-observation publication time.
- A stale cache or failed download must not create a fresh successful live forecast.
- Pinned historical code/artifact identity and all five UI pages must remain intact.

### Task 1: Ingestion/cache (implementation subagent)

Files: create `src/solar_flare_jepa/data/goes_nrt.py`, `tests/test_goes_nrt.py`.
Interfaces: `Snapshot(payload, provenance)`, `fetch_snapshot`, `load_snapshot`,
`assess_snapshot`; return JSONable assessment with `model_input_ready=false`.

- [x] Write offline tests for persistence/hash/receipt provenance, continuity/freshness,
  paired channels, satellite switches, invalid flux/contamination, transport failures and bounds.
- [x] Run tests to observe missing-feature failures before implementation.
- [x] Implement bounded allowlisted transport, immutable cache and conservative assessment.
- [x] Run targeted tests; self-review and independent review before completion.

### Task 2: Bounded inference adapter (implementation subagent)

Files: create `src/solar_flare_jepa/forecasting/nrt.py`, `tests/test_nrt_forecasting.py`.
Interfaces: explicit `forecast_snapshot` rejects SWPC before model access;
`replay_v1(root, issue_utc)` returns forecast with timing/lineage and unvalidated status.

- [x] Write failing tests for SWPC denial and deterministic pinned science replay,
  complete context and checkpoint/source identity failures.
- [x] Reuse existing pinned science preparation and inference; do not generalize the
  historical page's contract or assert NRT availability in the retrospective spec.
- [x] Run targeted tests against saved real observations and saved forecasts, network blocked.

### Task 3: CLI, evidence and operational docs (controller)

Files: create `scripts/goes_nrt.py`, `tests/test_goes_nrt_cli.py`,
`docs/GOES_NEAR_REAL_TIME.md`, verification report.

- [x] Test CLI explicit fetch, offline assessment, live-inference refusal and offline science replay.
- [x] Implement JSON status/exit codes, explicit UTC inputs and distinct timing fields.
- [x] Document official sources, UNKNOWN semantics, bounded operation and failure handling.
- [x] Run full suite, installed imports/CLI, five-page regressions and independent review.
- [x] Resolve review findings; verify diff/ignore/index; focused Conventional Commits and branch-only push.
