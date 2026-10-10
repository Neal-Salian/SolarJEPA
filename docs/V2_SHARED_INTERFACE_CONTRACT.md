# SolarJEPA V2 shared interface contract (model side)

Date: 2026-10-10 (Asia/Kolkata). Branch `feat/v2-controlled-model-development`
(base `origin/v1` 644648f). **Status: PROPOSED — REQUIRES JOINT APPROVAL.**
This document describes what the model-side code on this branch emits and
consumes. It does not change, and was not merged with, the independent-validation
work on `origin/feat/v2-m0-m1-validation-foundation` (`fd7203b`) or the M2/M3
branches (`94cae59`).

## Ownership boundary

| Neal (independent validation) | This branch (model development) |
|---|---|
| Statistical oracles, paired seed/calendar bootstrap, multiplicity | Model implementations, versioned losses |
| Leakage/fitting validation (`validate_fitting_artifacts`) | Training schedules, controls, budgets |
| Classical fit-acceptance **oracle** (thresholds) | Acceptance **integration** layer and wrappers |
| Scientific reproducibility checks, custodian/test access | Experiment orchestration, checkpointing, runner hooks |

## Interfaces

Versions: model records `schema_version = 1`; adapter `INTERFACE_VERSION =
'solarjepa-v2-model-interface-1'`; checkpoints `schema_version = 1`.

### 1. Forecast predictions — reuse, no new schema
Every V2 model (`QuantileForecaster.predict(context, future_grid)`) returns the
existing P1 `ForecastPrediction`: native target units, shape `[origins, horizon,
targets]`, quantiles `[..., levels]`, strictly validated non-crossing, point =
median (`inverse_transformed_point` for log10 specs). Model ids: `v2_jepa_finetune`,
`v2_supervised`, `v2_supervised_extra_updates`, `v2_jepa_frozen`,
`v2_random_frozen`, `v2_tcn_quantile`, `v2_quantile_linear` — none collide
with V1 ids. Inputs are `ForecastContext` + `FutureGrid` only (no targets).

### 2. Model fit diagnostics
Neural: `record['history']` (per-epoch phase, training loss + version, every
validation metric, steps, wall time, latent-collapse statistics for JEPA arms),
`record['selection']` (partition `validation`, metric, value, epoch,
`eligible_phase='downstream'`, `tie_policy='earliest_epoch'`, patience,
`stopped_early`). Quantile-linear: `record['lambda_candidates']` with validation
metric, raw crossing fraction, coefficient norm, shuffle-order fingerprint.
Classical: `forecasting.acceptance.FitCandidate.as_dict()` per optimizer attempt
(convergence report/flag, likelihood, parameters, min conditional variance,
persistence, slacks `1 − persistence`, `1 − |φ|`, `ν − 2`, root moduli, warnings,
error, `nonfinite_fields`) plus `AcceptanceDecision` (accepted, reasons,
policy id/version). An all-rejected fit raises `FitRejected(ValueError)`
carrying every candidate; nothing is dropped.

### 3. Training-budget metadata
`record['budget'] = {phases: [...], totals: {...}}`; each phase: `phase`
(`pretrain` / `supervised_warmup` / `downstream` / `lambda_grid`), epochs
planned/executed, optimizer steps, examples seen, optimizer + reset flag, lr,
weight decay, per-module parameter-update min/max (`source = optimizer_state`,
or `v1_ssl_optimizer_definition` for SSL), wall seconds. Totals add
`ema_target_updates`. `experiments.v2_interfaces.training_budget_summary(record)`
flattens this. Steps are not FLOPs; RSS is a process high-water mark.

### 4. Experiment configurations
`ControlledConfig.as_dict()` = `{schema_version, architecture (JepaConfig minus
schedule fields), schedule (TrainingSchedule)}`; `run_fingerprint` includes the
seed, `recipe_fingerprint` excludes it. TCN/linear configs are recorded under
`record['config']` with the same two fingerprints. No schedule field has a
default; proposed V2.1 values are never embedded in code.

### 5. Dataset and split identities
Records carry `spec_fingerprint`, `training_fingerprint` (P1
`TrainingSlice.fingerprint`), `training_dataset_fingerprint`,
`normalization_fingerprint`, `train_windows.fingerprint` (selected starts and
issue times) and `validation.origin_fingerprint`. The runner binds the dataset
fingerprint, train/validation split fingerprints and a **declared** test
identity (P1 `WindowedPartition.split_fingerprint`) at plan creation.

### 6. Checkpoint provenance
`QuantileForecaster.save` → weights-only Torch payload with model kind/id,
canonical record JSON, normalization JSON, per-tensor SHA-256 weights
fingerprint, Torch version; `load_forecaster` rejects unknown kinds, mismatched
record/config/arm/normalization/spec identities and weight tampering.
`PretrainingArtifact` stores one seed's post-SSL state with an identity
(architecture, SSL epochs, spec, normalization, training support, window subset)
that must match exactly before reuse by fine-tuned or frozen arms; on reuse the
seeded initial state is recomputed and the loaded weights must equal the recorded
post-SSL module fingerprints. Loading a checkpoint also requires the weights to
equal the record's selected-weight fingerprints, so one arm's record cannot carry
another arm's weights. `controlled.check_paired_cohort(records)` is the
enforcement point for pairing and budget matching across independently
configured arms (shared initial state, windows, support, normalization,
downstream order and schedule; B replays J's SSL order and step count; frozen
JEPA reuses J's SSL artifact).

### 7. Statistical evaluation inputs
`experiments.v2_interfaces.evaluation_identity_fields(record, *, experiment_id,
code_fingerprint, data_provenance_fingerprint, split_fingerprint,
protocol_fingerprint)` returns keyword arguments whose names and order equal
`EvaluationIdentity` on `fd7203b`. `config_fingerprint` is the seed-free recipe
fingerprint, so one paired cohort shares a configuration identity. Fields the
model owner cannot know are caller declarations.

**OBSERVED compatibility check (scratch only, not committed):** `git archive
fd7203b src` was extracted to a scratch directory, this branch's new modules were
overlaid, and six synthetic model outputs (J and S × seeds 3/4/5, multi-day
synthetic fixture) were wrapped in Neal's `EvaluationIdentity` and
`EvaluationRecord`, JSON round-tripped, converted with `loss_panel_from_records`
and compared with `paired_comparison` (block 1 day, 200 replicates). All calls
succeeded. The V1 training/contract/probabilistic modules are identical on both
refs. This is interface compatibility on synthetic inputs, not approval of the
mapping or of any statistical setting.

### 8. Test-release state
`experiments.v2_runner.StagedRun` ledger: stages `CREATED → A_VALIDATED →
B_FITTED → C_SELECTED → D_LOCKED → E_TEST_RELEASED → F_PUBLISHED`; lock
manifest and `lock_fingerprint`; single release record. Release requires
`allow_test_release=True`, a plan `approval_status == 'APPROVED'`, and a
`TestReleaseAuthorization` naming the exact config and lock fingerprints and the
declared test identity. Hooks (`register_hook(stage, fn)`) receive a read-only
ledger snapshot and return `{hook_id, version, passed, details}`; a failure
blocks the transition — this is where independent validators plug in.

## Classical acceptance policy contract (for the oracle owner)

```python
class FitAcceptancePolicy(Protocol):
    policy_id: str
    policy_version: str
    approval_status: str  # 'PROPOSED_REQUIRES_APPROVAL' | 'APPROVED' | 'TEST_DOUBLE'
    parameters: dict      # optional; enters the policy fingerprint
    def evaluate(self, candidate: FitCandidate) -> AcceptanceDecision: ...
```
Usage: `AcceptedVolatility(vol, dist, simulations, sim_seed, policy=..., retry_budget=RetryBudget(...))`
and `AcceptedARIMA(order, ..., policy=..., retry_budget=...)`. No production
policy exists on this branch; tests use test doubles only.

Decisions requiring the oracle owner's agreement: retries run in order only
when no initial attempt is accepted and stop at the first accepted one; a
candidate with an error or non-finite likelihood/parameters is never selectable
regardless of the policy; a malformed decision raises `PolicyContractError`
(a `TypeError`, stopping the run) rather than being recorded as a model failure;
the policy fingerprint (and hence the `accepted-…` model name) excludes
`approval_status` and the policy class, although both are recorded, and no
production code requires an APPROVED policy; volatility `converged` is
arch's optimizer success report and ARIMA keeps V1's "missing means not
converged"; settings are limited to `maxiter` (+ `ftol` for volatility); the
forecast-time variance check of the proposed protocol is not yet covered (only
in-sample conditional variance is recorded).

## Safeguards: technically enforced vs procedural

Enforced by code on this branch: runner stage order; release disabled by
default, single-shot per run and per declared test identity within one results
root (exclusive-create registry), gated on approved plan + matching authorization +
declared test identity; artifact SHA-256 verification at resume/select/lock/
release; resume rejects changed config/dataset/split/test/job identities and a changed
provenance declaration;
write-once artifacts and quarantine (never deletion) of interrupted jobs;
no-replace publication; fitting APIs accept only `TrainingSlice` + validation
windows; checkpoint/artifact identity checks.

Procedural only: the release registry covers one results root; job records are
opaque to the runner (a hook must compare them with declared identities); a crash
during release leaves the run at D_LOCKED permanently with unsealed partial test
outputs (fail-closed, by design); test files can be read outside the runner; identity strings
and approval statuses are unauthenticated declarations; no signing or access
control; callables passed to the runner are trusted; concurrent processes on one
run directory are not prevented; RSS is checked between jobs only.

## Not claimed

Compatibility beyond the synthetic check above; agreement on any proposed value
(seeds, budgets, λ grid, TCN architecture, acceptance thresholds, block length);
that equal inputs/steps make comparators fair in capacity or compute.
