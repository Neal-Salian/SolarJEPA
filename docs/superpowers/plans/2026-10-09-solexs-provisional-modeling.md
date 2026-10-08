# SoLEXS Provisional Modeling Implementation Plan

> **For agentic workers:** Use Superpowers TDD, independent investigations and final review. User explicitly authorizes autonomous execution without approval handoffs.

**Goal:** Reproducible numerical prediction of native SDD2 recorded LC values.
**Architecture:** An isolated sample-index package reuses bounded native access and compatible P2 numerical Torch helpers. Existing scientific/GOES contracts stay unchanged.
**Tech Stack:** Existing NumPy, Astropy, optional PyTorch and pytest.
**Spec:** `docs/superpowers/specs/2026-10-09-solexs-provisional-design.md`.

## Global Constraints

- Base Phase E 83b54435c1634f7de0a3ec6494439c023a4d0296; push feature branch only.
- Every output: EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED.
- No physical time, units, exposure, calibration, quality or flare inference.
- No old scientific record edits, P3 use, GOES change, test tuning or raw/checkpoint commits.
- Frozen 64/8/8 windows; July 1 row60480 split; July 3 separate engineering holdout.

## Review Focus

- Duplicate/reversed coordinates abort; unexpected positive steps split, never sort.
- NaNs persist in source masks; missing runs and split boundaries cannot be crossed.
- Normalization sees unique raw train rows only; validation/test never fit models.
- No implicit scientific clearance through units, labels or checkpoint deserialization.
- Artifact publication is exclusive; code/config/input identities bind all outputs.

### Task 1: Read-only feasibility and preservation

- [x] Inspect/fetch refs, preserve current files and publish exact Phase E branch in worktree.
- [x] Run inherited suite; independently inspect source, manifests and scientific data.
- [x] Delegate literature/native/contract audits without shared edits.
- [ ] Capture independent evidence and Stage A numerical-only verdict in report.

### Task 2: Native sample-index dataset and baselines (coordinator)

Files: `src/solar_flare_jepa/provisional/sequences.py`, `baselines.py`,
`tests/test_solexs_provisional_sequences.py`, `tests/test_solexs_provisional_baselines.py`.
Interfaces: `sequence_from_native(native)` preserves values and provenance;
`make_windows(sequence,start,stop,context,horizon,stride)` returns explicit x/y/masks
and source row indices; `fit_normalization(sequence,start,stop)` returns train stats;
`fit_baselines(train_windows,normalization)` then `predict(values,mask)` without targets.

- [ ] Write failing tests for identity/order/missingness/gaps/splits/normalization/causality.
- [ ] Run RED, implement minimal contracts/windows, run GREEN.
- [ ] Write/run RED for fixed predictors, masked metrics/coverage and persistence skill.
- [ ] Implement numerical comparators/evaluator and verify GREEN.
- [ ] Commit focused source/tests after diff and scientific-label checks.

### Task 3: Conditional neural adapter (separate implementer)

Files: `src/solar_flare_jepa/provisional/neural.py`,
`tests/test_solexs_provisional_neural.py` only.
Interfaces: `fit_neural(train_x,train_y,train_x_mask,train_y_mask,val_x,val_y,val_x_mask,val_y_mask,mean=...,scale=...,identities=...,config=...)`;
returned `predict(values,mask)`, `save_checkpoint(path)` and matching `load_checkpoint`.

- [ ] Test RED for masks/determinism/reload/invalid identity and scientific labels.
- [ ] Reuse build_smoke_model and masked_mse; implement fixed CPU training/selection.
- [ ] Verify GREEN with synthetic small support; coordinator reviews exact diff.

### Task 4: Frozen experiment runner and real execution

Files: `src/solar_flare_jepa/provisional/experiment.py`,
`scripts/run_solexs_provisional.py`, `configs/experiments/solexs_provisional_v1.json`,
`tests/test_solexs_provisional_experiment.py`.

- [ ] Test RED for source pin mismatch, config labels, output exclusivity, artifact hashes.
- [ ] Implement runner: verify sources, construct windows, fit baselines, verify repeat,
      train/select/reload if gates hold, then final test evaluation and exclusive publication.
- [ ] Freeze config/code in commit before real experiment.
- [ ] Run real baseline/neural experiment and deterministic reproduction in new directories.
- [ ] Compare predictions, data/split/normalization, metrics and weights independently.

### Task 5: Review, reports and publication

- [ ] Independent code/scientific review; reproduce and fix required defects with TDD.
- [ ] Full tests, 109-test native subset, normal installed import and CLI smoke checks.
- [ ] New report and concise implementation report with actual results and limitations.
- [ ] Verify archived inputs and old results unchanged, Git ignores/index/history, protected refs.
- [ ] Commit only small allowed files, push feature branch, verify remote equality; stop.
