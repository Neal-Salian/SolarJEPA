# SolarJEPA V2 model implementation report (M0/M1, model side)

Date: 2026-10-10 (Asia/Kolkata). Branch **`feat/v2-controlled-model-development`**,
created from **`origin/v1` = 644648f7d555fcbcb3eed4495d37fecffdd1863a** and published
with upstream tracking before any change. Companion documents:
[implementation plan](V2_MODEL_IMPLEMENTATION_PLAN.md),
[shared interface contract](V2_SHARED_INTERFACE_CONTRACT.md).

## Executive summary

This milestone adds model-side V2 infrastructure without changing any V1 file:
versioned losses (including the proposed equal-channel dex pinball), a
controlled trainer for five paired JEPA/supervised arms with explicit
budgets, a causal TCN and a full-context quantile-linear comparator, an opt-in
classical fit-acceptance integration layer, a staged A–F experiment runner with
a test-release gate that is off by default, and an adapter to Neal's
`EvaluationIdentity` schema. Everything was tested on synthetic fixtures only.
**No V2 confirmatory experiment, data acquisition, holdout access or full
training run was performed.** All proposed scientific values (seeds, epochs,
λ grid, TCN architecture, acceptance thresholds) remain **PROPOSED — REQUIRES
APPROVAL** and are not embedded in code.

Status legend: **IMPLEMENTED** (code exists), **TESTED** (executed tests in this
session cover it), **PROPOSED** (needs joint approval), **BLOCKED** (cannot
proceed without an external decision/resource).

## Reused V1 infrastructure (unchanged)

`training/jepa.py` (`build_jepa_model`, `pretrain_jepa`, `_setup`, `_monitor`,
`_windows`, `_validation_pinball`, `window_tensors`, `JepaConfig`),
`training/normalization.py`, `training/core.py` helpers, P1 contracts and window
builder, `forecasting/statistical.py` (`ARIMA`, `Volatility` as base classes),
`experiments/provenance.py` (`_rename_no_replace`, `verify_artifacts`).
`git diff origin/v1 --stat` over tracked files is empty: **no existing file was
modified**, so V1 code, configs and historical results are untouched.

## Implemented components

| Component | File | Status |
|---|---|---|
| Versioned losses `normalized_pinball_v1` (delegates to V1 `pinball_loss`) and `dex_pinball_equal_channel_v2`; exact streaming `MetricAccumulator` | `training/losses.py` | IMPLEMENTED, TESTED |
| `TrainingSchedule` (no defaults), `ControlledConfig` (recipe vs run fingerprint), arms `jepa_finetune`, `supervised`, `supervised_extra_updates`, `jepa_frozen`, `random_frozen`; fixed-schedule or patience mode; downstream-only earliest-minimum selection; per-phase budgets; `PretrainingArtifact` reuse; `check_paired_cohort`; V1-compatibility schedule | `training/controlled.py` | IMPLEMENTED, TESTED |
| Shared `QuantileForecaster` (context-only prediction to `ForecastPrediction`, optional rearrangement + crossing fraction) and checkpoint registry `load_forecaster` | `training/controlled.py` | IMPLEMENTED, TESTED |
| Causal TCN (`TcnConfig`, `ComparatorSchedule`, `fit_tcn`, `receptive_field`) | `training/comparators.py` | IMPLEMENTED, TESTED |
| Full-context quantile-linear (`QuantileLinearConfig`, `fit_quantile_linear`) | `training/comparators.py` | IMPLEMENTED, TESTED |
| Classical acceptance integration (`FitCandidate`, `AcceptanceDecision`, `FitAcceptancePolicy`, `RetryBudget`, `AcceptedVolatility`, `AcceptedARIMA`, `FitRejected`) | `forecasting/acceptance.py` | IMPLEMENTED, TESTED with test doubles; production policy BLOCKED on oracle owner |
| Staged runner (`RunConfig`, `JobSpec`, `StagedRun`, `TestReleaseAuthorization`) | `experiments/v2_runner.py` | IMPLEMENTED, TESTED |
| `EvaluationIdentity` field adapter, budget summary | `experiments/v2_interfaces.py` | IMPLEMENTED, TESTED; schema adoption PROPOSED |

## Training controls

- **Pairing (TESTED):** all arms of a seed share the full initial state
  fingerprint, the deterministic training-window subset, train-only
  normalization and the downstream permutation stream `default_rng([seed, 1])`.
  `supervised_extra_updates` replays JEPA's SSL window stream
  `default_rng([seed, 0])`, resets AdamW, then runs the identical downstream
  schedule. Torch is reseeded before each phase (pinned by a dropout-0.2 parity test).
- **Step accounting (TESTED):** per-phase optimizer steps, examples seen and
  per-module min/max parameter updates read from AdamW state; SSL counts follow
  the V1 optimizer definition and were cross-checked against real AdamW step
  calls (monkeypatched counter) and, by the reviewer, against AdamW state.
  EMA teacher updates are counted separately and never as optimizer updates.
- **Selection (TESTED):** validation only; downstream epochs only (warmup
  ineligible); earliest minimum; fixed schedule executes every epoch.
- **V1 compatibility (TESTED):** with `v1_compatible_schedule`, the controlled
  trainer reproduces V1 `fit_forecaster` weights, selected epoch, validation
  history and predictions **bitwise** for all three V1 variants.
- **Frozen/teacher isolation (TESTED):** frozen arms keep encoder/predictor
  fingerprints; the target encoder receives no gradient, is unchanged outside
  SSL and does not influence predictions.
- **Pretraining reuse (TESTED):** reusing a saved SSL artifact is bitwise equal
  to recomputation; mismatched seed/architecture/SSL epochs/window cap, forged
  weights and tampered files are rejected.
- **Cohort enforcement (TESTED):** `check_paired_cohort` rejects architecture,
  schedule, support or SSL-replay mismatches across independently configured arms.

## Baseline additions

| Model | Inputs | Capacity (V1-size synthetic smoke) | Notes |
|---|---|---|---|
| TCN | normalized values + masks, full context | 44,620 params with the proposed width 32 / dilations 1…32; receptive field 253 bins (TESTED arithmetic) | causal left padding verified by perturbation; monotone head |
| Quantile-linear | flattened normalized values, full context | 72,300 params at 120×2 → 300 | zero init, Adam, identical PCG64 stream per λ, final epoch, sort + crossing fraction, λ ties → smallest; requires complete context |
| JEPA / supervised arms | values + masks | 136,332 trainable (matches the V1 audit) | unchanged V1 architecture |

Remaining differences (not claimed equal): TCN and linear do not use JEPA's
patch transformer or latent predictor; TCN costs ~4.6× more per step than the
supervised transformer on this host; the linear model has no mask input and a
different optimizer (Adam, no weight decay, optional clipping); classical models
use all unique training bins rather than the window subset.

## Runner state machine

`CREATED → A_VALIDATED → B_FITTED → C_SELECTED → D_LOCKED → E_TEST_RELEASED →
F_PUBLISHED`. TESTED: every out-of-order call raises `InvalidTransition`;
release requires `allow_test_release=True`, an APPROVED plan, an APPROVED
authorization naming the exact config and lock fingerprints, and the declared
test identity; release is single-shot per run and per test identity per results
root; artifacts are write-once, sealed and re-verified; interrupted jobs are
quarantined and re-run; resume rejects changed plan, identities or provenance;
hooks can block transitions; an RSS ceiling stops further fitting with a recorded
failure; publication is a verified no-replace atomic rename. Enforced versus
procedural safeguards are listed in the module (`TECHNICALLY_ENFORCED`,
`PROCEDURAL_ONLY`) and in the interface contract. An end-to-end synthetic test
runs J/S/B/TCN × 2 seeds through A–F with the held-out partition supplied only at E.

## Test results (executed in this session)

Environment: Apple M4, 16 GiB, macOS 26.3.1 arm64, Python 3.13.7, torch 2.6.0,
numpy 2.2.6, `requirements-v1-lock.txt` + normal (non-editable) install.

| Check | Result |
|---|---|
| Baseline full suite on clean V1 | 1171 passed, 1 warning (107.7 s) |
| New tests: losses 9, controlled 25, comparators 12, acceptance 34, runner 35, interfaces 3, integration 1 | 119 passed |
| Final full suite after review fixes | **1290 passed, 1 warning** (64.5 s, peak RSS 0.56 GB) |
| `tests/test_statistical.py` (V1 classical) | 50 passed (acceptance-agent run) |
| Normal installed import outside the checkout; runner/acceptance/controlled imports do not import Torch | passed |
| `git diff --check` | clean |
| Mutation checks (7 mutants across controlled/losses/comparators) | 5 killed initially; 2 equivalent at dropout 0, one later killed by the added dropout parity test; acceptance agent's mutant (ignoring rejections) killed by 6 tests |
| Cross-branch interop with Neal's `fd7203b` (scratch, uncommitted) | `EvaluationIdentity`, `EvaluationRecord` JSON round trip, `loss_panel_from_records`, `paired_comparison` all accepted 6 synthetic V2 outputs |

The single warning is a pre-existing NumPy binary-compatibility RuntimeWarning
in `tests/test_experiment_reference.py`, also present on clean V1.

## Resource measurements (synthetic, OBSERVED, this host)

Synthetic 7,000-minute two-channel series, 120/30 spec, 4,851 training windows,
batch 256, 4 Torch threads, one epoch per phase (wall time includes validation
and monitoring): J 2.64 s / 38 steps; S 0.79 s / 19; B 1.45 s / 38; frozen JEPA
1.64 s / 38; random-frozen 0.68 s / 19; TCN 3.69 s / 19 (0.19 s/step);
quantile-linear 0.15 s / 19. Process peak RSS 0.46 GB. **INFERRED, unvalidated:**
at the proposed 79 steps/epoch and 8 + 15 epochs, a J job is on the order of
1–2 CPU minutes and a TCN job about 4 minutes on this host; real data, monitoring
cost and thermal behaviour may differ. No full schedule was run.

## Independent review

An independent Opus reviewer (read-only, ran probes) found **no BLOCKER or HIGH**
defects and four MEDIUM issues, all CONFIRMED by probes and **fixed** with
regression tests: forged pretraining artifact accepted; single-shot release only
per run directory; resume accepted changed provenance; B-arm budget matching not
enforced (now `check_paired_cohort`). LOW items fixed: checkpoint weights swap
across arms (now bound to selected fingerprints); quantile-linear validation on
empty-target batches. LOW items documented: policy fingerprint excludes approval
status/class; `attributed_training` double counts reused SSL if summed across
arms; a crash mid-release leaves the run fail-closed at D_LOCKED. The reviewer
confirmed the dex loss identity, SSL update counts, pairing, TCN causality,
absence of target leakage paths, acceptance selection and runner stage order.

## Scientific limitations

- Synthetic tests establish infrastructure behaviour, not forecast skill or
  that equal-dex selection changes conclusions.
- Determinism is verified within one host/process; cross-host bitwise
  reproducibility is UNKNOWN.
- Step-matched controls are not FLOP- or objective-matched; B's head also trains
  during warmup.
- Comparator fairness is limited to shared inputs, support, windows and
  selection data; capacity, optimizer and compute differ.
- The dex loss assumes log10 specs for its dex interpretation; for identity
  specs it is a train-std-weighted native pinball.
- No objective-specificity (masked-reconstruction) ablation is implemented.

## Integration requirements

Neal: accept or amend the `EvaluationIdentity` mapping (recipe fingerprint as
`config_fingerprint`); provide a `FitAcceptancePolicy` implementation; supply
validation hooks for the runner (e.g. `validate_fitting_artifacts`, comparing
job-record fingerprints with declared identities). Both: decide whether
`make_probabilistic`/V2 configs should route classical models through the
accepted wrappers.

## Unresolved protocol decisions (PROPOSED / BLOCKED)

Seed cohort and count; SSL/warmup/downstream budgets and fixed vs early stopping;
primary training/selection loss; λ grid and linear schedule; TCN architecture;
acceptance thresholds, start grids, retry budgets and simulation settings;
calendar/folds and exposure attestations (BLOCKED on both contributors);
custodian and test-release approval (BLOCKED); resource ceilings; whether an
objective-specificity ablation is required.

## Recommended next milestone

After joint approval of the decisions above: an exposed-data **M2 feasibility
pilot** on the existing May–August 2024 development partitions (no new test
data), running the first two protocol seeds through all arms with the staged
runner, measuring real RSS/runtime, comparing normalized- versus dex-selected
checkpoints, and exercising Neal's acceptance oracle and validation hooks.

## Files

Created: `src/solar_flare_jepa/training/{losses,controlled,comparators}.py`,
`src/solar_flare_jepa/forecasting/acceptance.py`,
`src/solar_flare_jepa/experiments/{v2_runner,v2_interfaces}.py`,
`tests/test_v2_{losses,controlled,comparators,acceptance,runner,interfaces,integration}.py`,
`docs/V2_MODEL_IMPLEMENTATION_PLAN.md`, `docs/V2_SHARED_INTERFACE_CONTRACT.md`,
this report. Modified: none.
