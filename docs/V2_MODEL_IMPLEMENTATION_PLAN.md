# SolarJEPA V2 model implementation plan (M0/M1, model side)

Date: 2026-10-10 (Asia/Kolkata). Branch `feat/v2-controlled-model-development`,
created from `origin/v1` at **644648f7d555fcbcb3eed4495d37fecffdd1863a** (the V1
scientific-audit checkpoint) and published with upstream tracking before any edit.
Scope: model-side V2 infrastructure only. No confirmatory training, no new data,
no access to proposed holdouts, no change to V1 code, configs or results.

The V2 research documents on `origin/research/v2-independent-validation`
(**90571dfe144434bbbd681c410dcdf2c389eab409**) were read with `git show` and are
treated as **PROPOSED — REQUIRES APPROVAL**. Nothing in this plan approves them.

## 1. Verified starting state

| Reference | SHA | Notes |
|---|---|---|
| `origin/v1` | `644648f7d555fcbcb3eed4495d37fecffdd1863a` | Equals the known V1 audit checkpoint; base of this branch |
| `origin/research/v2-independent-validation` | `90571dfe144434bbbd681c410dcdf2c389eab409` | Equals the known V2 design checkpoint; four documents only |
| `origin/main` | `1a4991da4dda9676caeb1d7e35a03408528c3188` | Not used; not modified |
| `origin/feat/v2-m0-m1-validation-foundation` | `fd7203b` | **Newer Neal work** (not named in the task): canonical `EvaluationRecord`/`EvaluationIdentity`, `LossPanel`, paired seed/calendar bootstrap, calibration diagnostics, `embargo_ns`. Read-only |
| `origin/research/v2-m2-statistical-validation`, `.../v2-m3-inference-remediation` | `94cae59` | Newer Neal statistical reliability harness. Read-only |

**OBSERVED baseline:** clean V1 checkout, Python 3.13.7 venv from
`requirements-v1-lock.txt` plus normal (non-editable) install:
`pytest -q` → **1171 passed, 1 warning** in 107.7 s, peak RSS 0.56 GB.
Host: Apple M4, 16 GiB, 10 cores, macOS arm64. This differs from Neal's
documented Mac14,2 / 8 GiB host; resource figures are host-specific.

## 2. V1 components verified in source (reuse, do not reimplement)

| Capability | Location | Verified behaviour |
|---|---|---|
| Patch Transformer context encoder, EMA target encoder, latent predictor, monotone quantile head | `training/jepa.py` `build_jepa_model` | Target encoder `requires_grad=False`, EMA update, Softplus cumulative quantiles |
| JEPA pretraining (context block + future masking, Smooth-L1/MSE latent loss) | `pretrain_jepa` | Optimizer covers encoder+predictor only; head untouched during SSL |
| Fine-tuned / frozen JEPA / matched supervised | `fit_forecaster` | Same seed ⇒ same initial weights; downstream order stream `default_rng([seed,1])` shared across variants; early stopping (patience); selection on **normalized** pinball |
| Deterministic chronological train-window subset | `TrainWindows.subsample` | Evenly spaced, no randomness |
| Train-only normalization | `training/normalization.py` | Unique raw training bins; per-channel mean/std |
| Context-only inference + checkpoint save/load with weight fingerprints | `TrainedJepa` | `weights_only` safe load, internal identity checks |
| Canonical forecast contracts | `forecasting/contracts.py` | `ForecastSpec`, `ForecastContext`, `FutureGrid`, `ForecastTargets`, `ForecastPrediction` (finite, ordered quantiles), `TrainingSlice` |
| Persistence-empirical, ARIMA, two-stage AR(1)+(G)ARCH | `forecasting/statistical.py` | Multi-start variance MLE keeps highest finite likelihood **regardless of convergence** (audit F04) |
| Log-space (dex) pinball/coverage, daily block bootstrap | `evaluation/probabilistic.py` | Cell-weighted dex pinball |
| V1 runner, provenance, no-replace atomic publication | `experiments/v1.py`, `experiments/provenance.py` | `_rename_no_replace` (RENAME_EXCL on macOS), artifact manifests |

## 3. Discrepancies between plans and executable code

1. V1 neural training/selection uses train-standardized pinball (implicit B/A weight
   1.68107); reported and classical selection use equal-cell dex pinball (audit F05).
2. V1 uses early stopping (patience 3). The V2.1 proposal requires a fixed schedule
   with earliest-minimum selection among downstream epochs only.
3. No extra-supervised-update control (B), random-frozen control, quantile-linear
   or TCN comparator exists in code.
4. `Volatility._multistart` accepts non-converged maxima; no fit-acceptance hook exists.
5. V1 records `finetune_steps` but not per-module update counts, phase-separated
   budgets, initial-state fingerprints or the selected training-window identity.
6. V1's runner docstring says the test is scored once after all selections; the code
   scores baselines on test before neural fitting (documented by Neal's M0 audit).
7. `AGENTS.md` says milestone branches start from `main`; this task explicitly
   requires `origin/v1`. The task instruction was followed.
8. Neal's newer branches already define `EvaluationIdentity`/`EvaluationRecord`;
   this branch (based on V1) does not contain them. Model outputs must adapt to
   that schema rather than define a competing one.
9. No fit-acceptance oracle exists on any of Neal's branches at the inspected SHAs.

## 4. Scope classification

### IMPLEMENTABLE_NOW
- Versioned forecast losses: `normalized_pinball_v1` (V1 semantics, unchanged) and
  `dex_pinball_equal_channel_v2` (per-channel normalized pinball × train target std,
  averaged over channels), each with a validation metric of the same definition.
- Controlled trainer (`training/controlled.py`) reusing V1 model/SSL code:
  arms `jepa_finetune`, `supervised`, `supervised_extra_updates`, `jepa_frozen`,
  `random_frozen`; explicit schedules with no default budgets; fixed-schedule or
  patience modes; selection restricted to downstream epochs; separate recorded
  RNG streams; per-phase optimizer-step and per-module parameter-update accounting
  read from optimizer state; initial/phase/selected weight fingerprints; reusable
  immutable pretraining artifacts for frozen-head arms; V1-compatibility mode.
- Comparators (`training/comparators.py`): full-context quantile-linear (λ grid,
  fixed epochs, PCG64 shuffle stream, rearrangement + crossing frequency) and a
  small causal TCN, both on the same normalized context and the shared prediction
  path; all hyperparameters supplied by configuration.
- Classical acceptance integration (`forecasting/acceptance.py`): per-start fit
  diagnostics, versioned `FitAcceptancePolicy` protocol, opt-in accepted-fit
  wrappers for ARIMA/volatility, explicit failure records, configurable retries,
  test-double policies. No acceptance thresholds are chosen here.
- Staged runner (`experiments/v2_runner.py`): A–F state machine with persisted
  ledger, configuration fingerprint, dataset/split identities, checkpoint locks,
  failure records, resume, atomic no-replace publication and a test-release gate
  disabled by default.
- Interface contract document and tests on synthetic fixtures only.

### REQUIRES_SHARED_APPROVAL
Seed cohort and count; SSL/warmup/downstream epoch budgets; early stopping versus
fixed schedule; primary loss/selection metric; λ grid and linear schedule; TCN
architecture; classical acceptance thresholds, start grids and retry budgets;
simulation paths/seeds; resource ceilings; test-release authorization and
custodian; folds/calendar; final schema adoption against Neal's `EvaluationRecord`.

### REQUIRES_EMPIRICAL_VALIDATION
Whether equal-dex selection changes checkpoints; RSS/runtime of full schedules;
TCN/linear adequacy on development data; classical acceptance rates under a chosen
policy; bootstrap block validity (Neal); bitwise determinism across hosts/torch builds.

### OUT_OF_SCOPE
Statistical oracles, bootstrap, leakage validation, the acceptance oracle itself,
data acquisition, holdout access, confirmatory runs, the 225-job campaign, event
warnings, SoLEXS, objective-specificity (masked-reconstruction) ablation, MPS/GPU.

## 5. Milestones, files and acceptance tests

| # | Deliverable | Files | Model-specific acceptance tests |
|---|---|---|---|
| 1 | Versioned losses | `training/losses.py`, `tests/test_v2_losses.py` | literal arithmetic; channel weights equal train std; gradient ratio equals std ratio; equals `log_scores` dex pinball on complete support; V1 loss unchanged |
| 2 | Controlled trainer | `training/controlled.py`, `tests/test_v2_controlled.py` | V1-compat mode reproduces `fit_forecaster` weights bitwise; identical initial state across arms; step/update counts from optimizer state; fixed schedule executes every epoch; warmup epochs never selected; earliest-minimum ties; frozen encoder/predictor invariance; teacher isolation; pretraining reuse equals recomputation; seed determinism; config identity; checkpoint round trip |
| 3 | Comparators | `training/comparators.py`, `tests/test_v2_comparators.py` | shapes; ordering; causality (future/test perturbation invariance); invalid inputs; protocol TCN arithmetic (44,620 params, receptive field 253) when given those values; determinism; reload; λ tie rule |
| 4 | Classical acceptance | `forecasting/acceptance.py`, `tests/test_v2_acceptance.py` | V1 classes unchanged; policy sees every start; rejected maxima never selected; all-rejected ⇒ explicit failure with diagnostics; retries bounded and recorded; policy identity recorded |
| 5 | Staged runner | `experiments/v2_runner.py`, `tests/test_v2_runner.py` | invalid transitions rejected; test release disabled by default and gated; config/dataset identity changes rejected on resume; failures recorded; deterministic names; atomic publication refuses replacement |
| 6 | Docs | `docs/V2_SHARED_INTERFACE_CONTRACT.md`, `docs/V2_MODEL_IMPLEMENTATION_REPORT.md` | claims match executed checks |

## 6. Regression risks and mitigations

- Shared modules (`jepa.py`, `statistical.py`, `v1.py`, `probabilistic.py`,
  `provenance.py`) are **not modified**; V2 code imports and composes them.
  Verified by `git diff origin/v1 --stat` restricted to existing files.
- Private V1 helpers imported by V2 (`_setup`, `_monitor`, `_windows`,
  `_validation_pinball`) could change upstream; a bitwise V1-parity test detects drift.
- Duplicated prediction logic is guarded by a parity test against `TrainedJepa.predict`.
- Torch determinism is host/build dependent; tests assert determinism within one
  process/host only.
