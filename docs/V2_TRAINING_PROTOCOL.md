# SolarJEPA V2 training protocol (M4A proposal)

**Status: PROPOSED — REQUIRES APPROVAL.** This document audits the implemented
training infrastructure and proposes reproducible configurations. It does not
approve any configuration. It authorizes no pilot, confirmatory training,
data acquisition or test release.

Date: 2026-10-10. Branch `feat/v2-training-protocol-feasibility`, based on
`feat/v2-controlled-model-development` @ `1826400`. Machine-readable proposals:
[`configs/v2_proposed/training_protocol_proposal.json`](../configs/v2_proposed/training_protocol_proposal.json)
and [`configs/v2_proposed/feasibility_pilot_proposal.json`](../configs/v2_proposed/feasibility_pilot_proposal.json).
Both are pinned to the code by `tests/test_v2_m4a_proposals.py`.

Companion documents: [baseline audit](V2_BASELINE_AUDIT.md),
[compute feasibility](V2_COMPUTE_FEASIBILITY.md), [M4B handoff](V2_M4_INTEGRATION_HANDOFF.md).

Evidence labels: **OBSERVED** (executed here), **INFERRED**, **DOCUMENTED**
(stated elsewhere, not re-established), **UNKNOWN**. Decision IDs (D01–D18) refer
to the register in `docs/V2_M0_RESOLUTION.md` on `origin/feat/v2-m0-m1-validation-foundation`.

## 1. Verified starting state

| Item | Observation |
|---|---|
| Base | `origin/feat/v2-controlled-model-development` = `1826400` (matches the reported HEAD) |
| Protected refs | `main` `1a4991d`, `origin/v1` `644648f`, `origin/feat/v2-m0-m1-validation-foundation` `fd7203b`, `origin/research/v2-m2-statistical-validation` `94cae59`, `origin/research/v2-m3-inference-remediation` `94cae59`, `origin/research/v2-independent-validation` `90571df` — read only, unchanged |
| M3.1 | The M3 remediation branch has **no unique pushed commit**: it points at the M2 tip. No M3.1 output exists to depend on |
| Baseline tests | `pytest -q` → **1290 passed**, 1 pre-existing warning, 65.2 s (OBSERVED) |
| Superpowers | Not installed in this environment. Equivalent structured workflows were used instead: independent read-only audit agents, TDD for every fix, and a separate final reviewer |
| Protocol text | `docs/V2_EXPERIMENTAL_PROTOCOL.md` is byte-identical on the design, M0/M1 and M2 branches (OBSERVED by `git diff`) |

## 2. The five controlled arms — audit

Code: `src/solar_flare_jepa/training/controlled.py`. Every row was checked by reading the code. Rows marked "test" are also covered by an existing test that passes at baseline. Rows marked "M4A" are new evidence from this milestone.

| Requirement | Implementation | Evidence |
|---|---|---|
| Identical starting weights | Every arm starts from `_seeded_model(spec, config)` with the same seed. SSL arms record the same initial fingerprint, and reuse verifies the artifact's initial state is this seed's | test `test_all_arms_share_initial_state_window_subset_and_downstream_order`; `test_forged_pretraining_artifact_with_other_seed_weights_is_rejected` |
| Seed handling | Recorded streams: init (`_setup(seed)`), SSL order `default_rng([seed,0])`, SSL context mask `torch.Generator(seed+2)`, warmup order = SSL order, downstream order `default_rng([seed,1])`. Torch is reseeded before downstream | `RNG_STREAMS`; `test_seed_determinism_and_sensitivity` |
| Window support and order | One deterministic evenly spaced chronological subset (`TrainWindows.subsample`) shared by all arms. Identical per-epoch permutations downstream | test (as above) |
| Pretraining reuse | `PretrainingArtifact` is immutable, weights-only loaded and identity-checked (seed, architecture, SSL epochs, window cap, training support, normalization). Reuse is bitwise equal to recomputation | `test_pretraining_artifact_reuse_equals_recomputation` |
| Optimizer reset | A fresh AdamW per phase (SSL, warmup, downstream). Frozen modules have `requires_grad=False` and are excluded from the optimizer, so they receive no weight decay | code `train_downstream`; `test_frozen_arms_never_change_encoder_or_predictor` |
| Explicit budgets | `TrainingSchedule` has no defaults. Arm structure is enforced (SSL only for JEPA arms; warmup only for the extra-update arm) | `test_schedule_requires_every_budget_and_enforces_arm_structure` |
| Step accounting | Downstream and warmup counts are read from AdamW state per module. SSL counts follow the V1 optimizer definition, cross-checked against real `step()` calls. EMA updates are counted separately | `test_optimizer_step_and_parameter_update_accounting`; `test_recorded_steps_equal_actual_optimizer_step_calls` |
| Validation-only selection | `fit_*` accepts no test argument. Selection uses the validation partition, downstream epochs only, earliest minimum | `test_fixed_schedule_executes_every_epoch_and_selects_earliest_minimum`; `test_held_out_values_cannot_change_any_arm` |
| Selection support identity | **Gap found (M4A):** `check_paired_cohort` did not compare the validation identity, so arms selected on different validation windows passed. **Fixed**; the identity is now required per seed | new `test_paired_cohort_rejects_arms_selected_on_different_validation_support` (failed before the fix, passes after) |
| Missing validation | **Gap found (M4A):** `validation_window=None` crashed with `AttributeError`. **Fixed** to raise an explicit `ValueError` | new `test_fit_controlled_requires_a_validation_partition_for_selection` |
| Checkpoint/config identity | `run_fingerprint` (with seed), `recipe_fingerprint` (seed-free), selected per-module weight fingerprints bound to the record, safe weights-only load | `test_configuration_identity_separates_recipe_from_seed`; `test_checkpoint_cannot_carry_another_arms_weights` |
| Teacher isolation | The target encoder gets no gradient, is unchanged outside SSL and does not affect predictions | `test_teacher_is_isolated_from_gradients_and_forecasting` |
| V1 compatibility | `v1_compatible_schedule` reproduces V1 `fit_forecaster` bitwise | `test_v1_compatibility_mode_reproduces_v1_fit_forecaster_bitwise` |
| Monitor RNG | `_monitor` runs in eval mode with `no_grad` on a fixed chronological subset and consumes no RNG, so it cannot desynchronize arms | code read (M4A) |

**Scope of enforcement.** `check_paired_cohort` covers the five controlled arms
only, because it requires `model_kind == temporal_jepa_quantile_controlled`. TCN and
linear records share the support/normalization/window machinery, but no
cohort checker binds them to the J/S cohort. M4B should verify their identities by
comparing records (see the [handoff](V2_M4_INTEGRATION_HANDOFF.md)).

## 3. What "equal budget" means — four different quantities

The table uses the proposed schedule: 20,000 windows, batch 256 ⇒ ⌈20000/256⌉ = **79 steps/epoch**,
8 SSL / 8 warmup / 15 downstream epochs. Counts are exact consequences of the code (INFERRED arithmetic,
matching the step accounting tested above).

| Arm | Optimizer steps (enc+pred / head) | Window presentations | Distinct training windows | Measured cost (synthetic, M4 host) |
|---|---|---|---|---|
| J `jepa_finetune` | 632 SSL (enc+pred) + 1,185 (all) = **1,817** / head 1,185 | 8·20k SSL + 15·20k = 460,000 | 20,000 | see [compute §4](V2_COMPUTE_FEASIBILITY.md#4-per-job-projections) |
| S `supervised` | 1,185 / 1,185 | 300,000 | 20,000 | |
| B `supervised_extra_updates` | 632 warmup + 1,185 = **1,817** / head **1,817** | 460,000 | 20,000 | |
| Frozen JEPA | shared 632 SSL + 1,185 head-only | 460,000 (SSL attributed) | 20,000 | |
| Frozen random | 1,185 head-only | 300,000 | 20,000 | |
| TCN | 1,185 (all) | 300,000 | 20,000 | |
| Quantile-linear | 100·79 = 7,900 per λ, 7 independent λ fits | 2,000,000 per λ | 20,000 | |

- **Equal optimizer steps.** J and B match encoder/predictor update opportunities.
  B's head receives 632 extra updates that J's head does not. S has fewer steps by design.
- **Equal training examples.** J and B see each window 23 times and S 15 times. SSL
  presentations use the 150-bin window (context + future) as the latent target. This is training-partition data only.
- **Equal window exposure.** All neural/linear arms use the identical 20,000-window
  subset. Classical models use all unique raw training bins, which is unequal by design and declared.
- **Equal compute.** Not claimed. SSL steps run the context encoder, EMA teacher and predictor.
  Head-only steps skip backpropagation into the encoder. The TCN is about 7.5× costlier per step than full fine-tuning
  (microbench, [compute §3](V2_COMPUTE_FEASIBILITY.md#3-measured-results)). The proposed H5 cost endpoint
  (J/B wall-time ratio ≤ 1.10) is a separately measured quantity, not implied by step equality.

## 4. Fairness guarantees and remaining limitations

**Guaranteed by code (OBSERVED via tests):**
- identical initial state, window subset, normalization and downstream order per seed
- identical downstream schedule and objective across arms
- identical validation (selection) support per seed (M4A fix)
- B replays J's SSL order and step count
- the frozen JEPA arm reuses J's SSL artifact
- AdamW is reset per phase
- validation-only, downstream-only, earliest-minimum selection
- no test argument on any fitting path

**Not guaranteed / limitations:**
1. Step-matched ≠ FLOP-matched ≠ objective-matched. B's head also trains during warmup.
2. The JEPA arm has an extra randomness source (the SSL context-mask generator). B has none. Pairing is
   on shared streams only.
3. A fixed schedule equalizes executed epochs. The *selected* epoch can still differ by
   arm, so selected models embody different update counts. The selected epoch must be reported and
   never treated as a budget.
4. Weight decay applies to biases and LayerNorm parameters (inherited V1 AdamW behaviour, identical across neural
   arms). The linear model uses Adam without decay.
5. Capacity differs across families: 136,332 (J/S/B), 67,948 head-only, 44,620 TCN, 72,300 linear.
6. Monitoring time differs. JEPA arms also run the target encoder in per-epoch diagnostics,
   and that time is included in their epoch wall time. The measured downstream epochs of J and S did not differ
   materially on the synthetic benchmark ([compute §3](V2_COMPUTE_FEASIBILITY.md#3-measured-results)). It still biases
   wall-time ratios slightly against J.
7. Determinism is verified within one host and process. Cross-host bitwise reproducibility is UNKNOWN.
8. The validation partition (V1: 10 days, 412 retained origins, DOCUMENTED) is small. Selection noise is
   part of the outcome and is not modelled by any proposed inference.

## 5. Proposed configuration

All values are **PROPOSED — REQUIRES APPROVAL**. "Status" says where each value comes from.

| Setting | Proposed value | Status / source | Scientific trade-off |
|---|---|---|---|
| Seeds | 20 SHA-256-derived seeds (§6 of the V2 protocol). First 5 for the secondary arms. **Recomputed and confirmed in M4A** | INHERITED_V2_PROPOSAL (D10) | 20 is an affordable precision compromise, not a power guarantee (protocol §6) |
| Architecture | patch 5, width 32, depth 3, heads 4, predictor depth 2, MLP ratio 4, head 128, dropout 0 | INHERITED_V1 | Changing it would break comparability with V1 and add search degrees of freedom |
| JEPA objective | Smooth-L1, context block mask (4 patches), EMA 0.996→1, no auxiliary JEPA loss during fine-tuning | INHERITED_V1 | Masking and pretraining-volume sweeps are deferred (protocol §5) |
| Optimizer | AdamW, lr 1e-3, weight decay 1e-4, no LR schedule, reset per phase | INHERITED_V1 | No per-arm tuning, which avoids a search confound. Untuned for the TCN |
| Batch / clip | 256 / global norm 1.0 | INHERITED_V1 | — |
| Training windows | 20,000 deterministic chronological subset | INHERITED_V1 | Bounds cost. Discards ≈83% of the 117,931 eligible stride-1 windows of the 82-day V1 train split (count OBSERVED on the synthetic dataset of identical dimensions) |
| SSL / warmup / downstream epochs | 8 / 8 / 15 | INHERITED_V1 (8, 15); INHERITED_V2_PROPOSAL (warmup = SSL) | Warmup must equal SSL for B's replay check |
| Early stopping | None (fixed 15 epochs). V1 patience 3 is the recorded alternative | INHERITED_V2_PROPOSAL | Fixed schedules make executed budgets arm-independent but cost about 1.6× V1's early-stopped runtime |
| Checkpoint selection | Validation `dex_pinball_equal_channel_v2`, downstream epochs only, earliest minimum | INHERITED_V2_PROPOSAL; tie and eligibility rules are code invariants | Aligns selection with the proposed primary estimand (equal-channel dex) |
| Training loss | `dex_pinball_equal_channel_v2` | **NEWLY_PROPOSED_M4A** | V1 trained on standardized pinball (B/A weight 1.68 in dex). Training on the selection objective removes a train/select mismatch. Whether it changes checkpoints is unmeasured (§6) |
| Diagnostic metric | `normalized_pinball_v1` recorded per epoch | **NEWLY_PROPOSED_M4A** | No training effect. Enables the development loss comparison |
| TCN | width 32, kernel 3, dilations 1…32, dropout 0, lr 1e-3, wd 1e-4, clip 1, 15 fixed epochs, first 5 seeds | INHERITED_V2_PROPOSAL; arithmetic verified (44,620 params, RF 253) | No architecture sweep. RF > context, so the extra RF only reads padding |
| Quantile-linear | Adam lr 0.01, batch 256, 100 fixed epochs, **λ ∈ {0, 1, 10, 10², 10³, 10⁴, 10⁵}**, ties → smallest | lr/epochs INHERITED_V2_PROPOSAL; **grid NEWLY_PROPOSED_M4A** (§5.4) | 7 fits instead of 5, which is cheap (compute §4) |
| Quantiles | {0.05, 0.25, 0.5, 0.75, 0.95} | INHERITED_V1 (D08) | — |
| Precision / device | CPU, float32, 4 Torch threads, deterministic algorithms on | INHERITED_V1; threads confirmed by the M4A benchmark (8 threads was slower for every model) | MPS/GPU not assumed. Results are host-specific |
| Memory ceiling | 4 GiB process peak RSS, checked between jobs. Run one job per process | INHERITED_V2_PROPOSAL (D11) | Measured jobs peak at ≤0.65 GiB on synthetic data, so there is ample headroom |
| Per-job timeout | neural downstream 600 s, SSL 300 s, TCN 1,800 s, linear 1,800 s | **NEWLY_PROPOSED_M4A** (D11) | About 5–8× the extrapolated per-job time. A timeout is an infrastructure failure |
| Failure/retry | ≤1 logged infrastructure retry per job at an identical seed/config/code. Numerical failures recorded, never retried with changed settings. Seeds never dropped or replaced | policy INHERITED_V2_PROPOSAL; count **NEWLY_PROPOSED_M4A** | Prevents a selective-rerun bias |

### 5.1 Fixed schedule versus early stopping

Fixed 15 epochs is proposed. Early stopping (V1, patience 3) makes the executed budget
depend on validation noise and on the arm, which undermines the step-matching
argument for B. A fixed schedule costs more but is fully specified in advance. Under both
rules the selected epoch remains validation-dependent (§4, item 3).

### 5.2 Checkpoint selection

Earliest minimum of validation equal-channel dex pinball among downstream epochs.
Warmup/SSL checkpoints are ineligible (code invariant). The `normalized_pinball_v1`
diagnostic is computed every epoch so the pilot can report whether the two
criteria select different epochs. It is never used for selection under this proposal.

### 5.3 Loss selection

Proposed: train **and** select on `dex_pinball_equal_channel_v2`. The alternative
(train on `normalized_pinball_v1`, the V1 objective) remains available, and the
pilot measures the difference (§6). Neither choice is claimed to improve forecasts.

### 5.4 Quantile-linear regularization grid

The implemented penalty is λ·mean(W²) over the 72,000 coefficients. Its per-coefficient
ridge strength is α = λ/72,000 ([baseline audit B1](V2_BASELINE_AUDIT.md#λ-scale-finding-medium-protocol-rather-than-code)).
The previous grid {0, 10⁻³, 10⁻², 10⁻¹, 1} spans α ≤ 1.4×10⁻⁵, which is effectively
unregularized.

A rough scale argument (INFERRED) runs as follows:

- The pinball gradient per coefficient is of order (1/300 outputs)·σ_k·E|x| ≈ 10⁻³.
- At coefficient magnitudes of about 0.05, the penalty gradient 2αW matters once α ≈ 10⁻² (λ ≈ 7×10²).

The proposed grid {0, 1, 10, 10², 10³, 10⁴, 10⁵} therefore brackets "no effect" through
"dominant" (α from 1.4×10⁻⁵ to 1.4) in decade steps. Selecting the largest λ is reported as
`BOUNDARY_SELECTED`. During development only, one documented decade extension is allowed before
freeze. After freeze there is no extension. The pilot must record the λ path (validation metric,
mean squared coefficient, crossing fraction) to replace this scale argument with evidence.
Redefining the penalty as a sum would be equivalent up to rescaling. It is not proposed, because it would change the
semantics of existing tested code for no scientific gain.

## 6. Loss comparison protocol (development only)

Purpose: measure whether training/selecting on `normalized_pinball_v1` versus
`dex_pinball_equal_channel_v2` changes selected checkpoints and validation behaviour.
This is not a claim about forecast skill.

- **Data.** The pilot's exposed development partitions only (§8). The test is never scored.
- **Runs.** For each pilot seed, J and S are each trained twice: (train=dex, select=dex, diagnostic=normalized) and
  (train=normalized, select=normalized, diagnostic=dex). The J runs reuse the seed's SSL artifact, because the loss affects downstream only.
- **Recorded.** Per-epoch validation curves of both metrics, the selected epoch under each criterion, per-channel
  validation dex pinball at the selected checkpoints, and B/A channel weight implied by σ_k.
- **Reported descriptively.** Whether selected epochs differ, and the change in per-channel dex pinball.
  No interval, test or decision is attached. With 2 seeds nothing can be inferred.
- **Decision use.** Informs the approval of D10 (training loss) before the protocol is frozen. Any change produces a new
  protocol version, never a silent switch.

## 7. Reproducibility controls

- Every job writes a model record containing:
  - `recipe_fingerprint` and `run_fingerprint`
  - training/normalization/window/validation identities
  - RNG stream descriptions
  - pairing fingerprints (initial state, SSL/warmup/downstream orders)
  - per-phase budgets read from optimizer state
  - per-epoch metrics, selection, environment, and selected weight fingerprints
- Checkpoints are weights-only and identity-bound (`load_forecaster`).
- Recommended for M4B: record the code commit and `requirements` lock hash in the run
  provenance. `StagedRun(provenance=...)` accepts it, but nothing populates it automatically.
- Run one job per process. The record's RSS field is a process high-water mark.

## 8. Two-seed feasibility pilot — prepared, **not executed**

Machine-readable plan: [`feasibility_pilot_proposal.json`](../configs/v2_proposed/feasibility_pilot_proposal.json).

| Item | Proposal |
|---|---|
| Purpose | Operability, runtime, memory, checkpoint selection behaviour, loss implementation behaviour, evaluation-interface compatibility, artifact reproducibility. **Not** JEPA value |
| Seeds | 1261866429, 1291916211 (first two proposed seeds) |
| Data support | V1 splits on exposed May–August 2024 data: train 05-01→07-22, validation 07-22→08-01. August stays sealed, and the run stops at `D_LOCKED` |
| Eligible folds | One development fold (the V1 calendar). The proposed 2020/2022/2023 folds are not touched (D04/D05) |
| Jobs | 2 SSL phases; J/S/B/frozen-J/frozen-random/TCN × 2 seeds = 12 downstream jobs; 1 linear fit (7 λ); 4 loss-comparison jobs (J and S with the V1 loss) |
| Schedules | §5 (8 SSL / 8 warmup / 15 downstream, fixed) |
| Resource ceilings | 4 GiB RSS, per-job timeouts as §5, total wall budget 2 h, 4 threads, one job per process |
| Expected outputs | Ledger to D_LOCKED; model records; `check_paired_cohort` summaries; checkpoints with reload parity; validation predictions accepted by the M4B `EvaluationRecord`/`LossPanel` adapters; measured time/RSS/storage; λ path |
| Stop conditions | RSS or timeout breach after one retry; any nonfinite loss/gradient/prediction or crossing; cohort check failure; reload parity failure; any test-partition access; total budget exceeded |
| Preconditions | M4B integration merged on a branch; protocol approval (D10, D11); data re-acquired with manifest hash verification (§9); custodian decision on August handling |

Estimated pilot cost on the M4 host: see [compute §5](V2_COMPUTE_FEASIBILITY.md#5-study-and-pilot-totals).

## 9. GOES development-data eligibility

Audited read-only from manifests, configs and code. **No GOES data file exists on this host**
(`data/raw`, `data/interim` and `data/processed` contain only `.gitkeep`). No external path is configured. File-level
integrity, continuity and duplicate checks could therefore not be executed here. The statements below are from
manifests and code (OBSERVED) or from earlier reports (DOCUMENTED).

| Aspect | Finding |
|---|---|
| Provenance | 4 manifests (May, June, July P2, August 2024). GOES-16 `xrsf-l2-avg1m_science` v2-2-1 from NOAA NGDC. 123 files, ~36.5 MB. Per-file bytes/sha256/acquisition/lineage recorded. Hashes are trust-on-first-use (not NOAA-issued). July 01–03 are `copy_pinned_reference` (OBSERVED) |
| Integrity | Manifests are complete and `config_sha256` matches the configs (OBSERVED). File hashes are not verifiable here. DOCUMENTED: all 123 passed on the original host |
| Continuity / duplicates | Code rejects within-file and cross-file duplicates and non-minute deltas, reindexes to the full minute grid (missing → masked), and requires contiguous multi-manifest selections (OBSERVED, code + 204 targeted synthetic tests passed). DOCUMENTED: 177,120 consecutive bins, no gaps or duplicates |
| Quality flags | Status flag 0, 0 < count ≤ 60, electron-correction mask, finite positive flux within valid range. Count ≥ 1 is accepted (weak; DOCUMENTED 11,237 XRS-A bins with < 60 samples) |
| Splits (V1) | train 2024-05-01→07-22 (3,609 retained origins), validation 07-22→08-01 (412), test August (1,436) (DOCUMENTED counts) |
| Embargo | **None on this branch.** Partitions touch, and only support containment applies. `embargo_ns` exists on the M0/M1 branch only (D09) |
| Windows | 60 s cadence, 120-min context, 30-min horizon, stride 30. Complete-case (no imputation). Full support must lie inside its partition |
| Normalization | Fit on unique raw training-partition bins only (`fitting_scope='UNIQUE_RAW_TRAINING_PARTITION'`). Validation must start at or after the training end (OBSERVED code) |
| Support identity | One `WindowedPartition` per partition shared by all models. `split_fingerprint`, ordered `origin_ids`, `validate_alignment`. V2 adds the validation `origin_fingerprint` |
| **Exposure** | **All of May–August 2024 is exposed.** May–July was used for V1 fitting and selection. August was scored in V1 (V1 audit F10; D02 VERIFIED). These data are development-only and can never support confirmatory claims |
| Eligibility for the pilot | Development use of the train/validation partitions is permitted by D02 as exposed data. August must not be scored by the pilot. Because the loader requires a test split and reads every manifest, the pilot either loads August sealed behind the runner gate (proposed) or uses a pilot-specific May–July config with an inner pseudo-test (changes identities) — **decision required** |

Leakage risks noted (no confirmed train-to-test leakage in code):

1. No embargo. Autocorrelation crosses the touching boundaries.
2. `v1.run_v1` scores the test during fitting by default. V2 `StagedRun` gates it, but the gate is procedural for files read outside the runner.
3. Stale "untouched" wording about August in the `v1.py` docstring and `tests/test_v1_foundation.py:24` contradicts the audit. These are historical V1 files and were not edited.

## 10. Decisions requiring approval

| # | Decision | Register | Blocking for |
|---|---|---|---|
| 1 | Seed cohort (20 + first 5 secondary) | D10 | pilot (first 2), M5 |
| 2 | Epoch budgets 8/8/15 and fixed schedule vs early stopping | D10 | pilot |
| 3 | Training loss (dex vs V1 normalized) and selection metric | D10 | pilot (primary run), freeze |
| 4 | Quantile-linear λ grid {0,…,10⁵} and boundary rule | D10 | pilot |
| 5 | TCN architecture/optimizer as proposed | D10 | pilot |
| 6 | Resource ceilings: RSS, per-job timeouts, total budget, threads | D11 | pilot |
| 7 | Retry policy (≤1 infrastructure retry) | D10 | pilot |
| 8 | August handling for the pilot (sealed in-run vs pseudo-test config) | D02/D18 | pilot |
| 9 | Re-acquisition of the 123 manifest files on the execution host | D18 | pilot |
| 10 | Embargo policy | D09 | M5 (and pilot, if adopted) |
| 11 | Inference method, block length, margins and multiplicity | D12/D13, M3.1 | M5 |
| 12 | Custodian and test-release authorization | D04/D18 | M5 |
