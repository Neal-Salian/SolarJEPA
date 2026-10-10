# SolarJEPA V2 baseline and loss audit (M4A)

Date: 2026-10-10. Branch `feat/v2-training-protocol-feasibility`, based on
`feat/v2-controlled-model-development` @ `1826400`. Companion documents:
[training protocol](V2_TRAINING_PROTOCOL.md), [compute feasibility](V2_COMPUTE_FEASIBILITY.md),
[M4B handoff](V2_M4_INTEGRATION_HANDOFF.md).

Evidence labels follow `AGENTS.md`: **OBSERVED** (executed in this milestone),
**INFERRED** (derived, not executed), **DOCUMENTED** (stated in an earlier report;
not re-established here). The earlier [implementation report](V2_MODEL_IMPLEMENTATION_REPORT.md)
was treated as a claim to verify, not as evidence.

## 1. Method

- An independent read-only audit pass (separate agent context, no write access to
  source or tests) recomputed every number by hand from the layer definitions,
  then confirmed it with `sum(p.numel())`, autograd probes and perturbation
  scripts. Scratch probes were not committed. Their findings were re-checked by the
  coordinator before any fix.
- Regression tests were written first for each confirmed defect, observed failing,
  then fixed with the smallest change (§6).
- All inputs were synthetic. No GOES data exists on this host (see
  [training protocol §9](V2_TRAINING_PROTOCOL.md#9-goes-development-data-eligibility)).

## 2. TCN comparator (`training/comparators.py`)

Proposed configuration (PROPOSED, `docs/V2_EXPERIMENTAL_PROTOCOL.md` on
`research/v2-independent-validation`): width 32, kernel 3, dilations 1/2/4/8/16/32,
two convolutions per residual block, GELU, dropout 0, 60 s cadence, 120-bin context,
30-bin horizon, two channels, five quantiles.

### Parameter count — OBSERVED 44,620 (matches the report)

Input channels = 2 values + 2 validity masks = 4. Convolution parameters = in·out·k + out.

| Layer | Arithmetic | Parameters |
|---|---|---|
| Block 1 conv 1 (4→32, k=3) | 4·32·3 + 32 | 416 |
| Block 1 conv 2 (32→32, k=3) | 32·32·3 + 32 | 3,104 |
| Block 1 skip, 1×1 (4→32) | 4·32 + 32 | 160 |
| Blocks 2–6, two 32→32 convs each, identity skip | 5 · 2 · 3,104 | 31,040 |
| Head (32→300 = 30 leads · 2 channels · 5 levels) | 32·300 + 300 | 9,900 |
| **Total** | | **44,620** |

### Receptive field — OBSERVED 253 bins (matches the report)

RF = 1 + Σ_blocks 2·(k−1)·d = 1 + 2·2·(1+2+4+8+16+32) = 1 + 4·63 = **253**
(`receptive_field`, `comparators.py:137-139`). It was checked empirically on a
400-bin input: the earliest bin with nonzero gradient on the final state is
index 147, and 400 − 147 = 253.

**Interpretation.** 253 > 120, so the final state sees every bin of the
120-minute context: bin 0 has a nonzero gradient (OBSERVED). About 133 bins of the field
fall in the causal zero padding, so the dilation-16/32 taps mostly read padding.
This is not extra information. Padding (value 0, mask 0) is indistinguishable
from a masked observation, which is consistent with how masks are encoded.

### Other checks

| Property | Result | Evidence |
|---|---|---|
| Causal padding | Left padding 2·dilation for each kernel-3 conv. Perturbing every t∈[0,120) in both value and mask channels left all outputs at positions < t bit-identical (0 violations) | OBSERVED |
| Residual connections | 1×1 biased projection in block 1 (4→32), identity in blocks 2–6 | OBSERVED |
| Horizon alignment | Only the final state feeds `Linear(32,300)`, reshaped `[B,30,2,5]`, index = h·10 + k·5 + q. A gradient probe on cell (h=3,k=1,q=2) reached only (3,1,0..2) | OBSERVED |
| Quantile semantics | q₀ plus cumulative Softplus increments, so outputs are non-decreasing by construction. Config requires strictly increasing levels in (0,1) including 0.5 | OBSERVED |
| Input normalization | Shared train-only `Normalization` (unique raw training bins). Masked entries become 0 and mask channels are concatenated | OBSERVED |
| Training/validation | Shared `train_downstream` (AdamW reset, fixed or patience schedule, earliest-minimum validation selection) | OBSERVED (code) |
| Test-partition invariance | `fit_tcn` accepts no test partition. The existing test checks that weights are unchanged when the held-out partition is scaled | OBSERVED (existing test passes) |

## 3. Full-context quantile-linear comparator

| Property | Result | Evidence |
|---|---|---|
| Context usage | `Linear(120·2, 300)` on `features[:, :120].flatten(1)`: the full 120-minute context, with no future rows | OBSERVED |
| Parameters | 240·300 + 300 = **72,300** (matches the report) | OBSERVED |
| Mask handling | No mask input. `forecast` raises on any invalid context cell, so validation/test contexts must be complete | OBSERVED |
| Quantile ordering | Training uses raw (possibly crossing) outputs. Validation scoring and `QuantileForecaster(rearrange=True)` sort per cell. The raw crossing fraction is recorded | OBSERVED |
| Regularization | `λ · mean(W²)` over the 72,000 weights. Biases excluded. Zero initialization | OBSERVED |
| Selection | Each λ trained for fixed epochs with an identical PCG64(seed) shuffle stream (1 unique stream fingerprint across 5 λ). Final epoch kept. λ chosen by validation metric, exact ties to the smallest λ (`{1:.5,0:.5,2:.4}`→2, `{0:.5,1:.4,2:.4}`→1) | OBSERVED |
| Leakage | Normalization from training rows only. `_validate_inputs` requires validation to start at or after the training end. Weights are bit-identical when the test partition is multiplied by 10³ | OBSERVED |

### λ-scale finding (MEDIUM, protocol rather than code)

Because the penalty is a **mean** over 72,000 coefficients, its gradient is
2λW/72,000. The previously proposed grid λ∈{0, 0.001, 0.01, 0.1, 1} is therefore
almost unregularized at production size.

On the 1,000-weight test fixture, the mean squared coefficient was:

| λ | Mean squared coefficient |
|---|---|
| 0 | 0.00661 |
| 1 | 0.00610 |
| 100 | 7.1×10⁻⁵ |
| ≥10⁴ | ~1.4×10⁻⁵ |

These values are OBSERVED. At 72,000 weights the per-λ effect is about 72× weaker still (INFERRED).
Validation would then select the smallest λ by default, and the "regularization
grid" would carry no information. The code is internally consistent, so it is not changed. The
replacement grid is a protocol proposal in
[training protocol §5.4](V2_TRAINING_PROTOCOL.md#54-quantile-linear-regularization-grid).

## 4. Losses (`training/losses.py`, V1 `training/jepa.py:pinball_loss`)

Pinball: ρ_τ(u) = max(τu, (τ−1)u), u = y − q.

| Version | Definition (masked) | Channel weight in dex |
|---|---|---|
| `normalized_pinball_v1` | Mean of ρ over every valid standardized cell and level (cells pooled across channels) | 1/σ_k (implicit). With σ_A, σ_B from training this gave B/A weight 1.68107 in V1 (DOCUMENTED, V1 audit F05) |
| `dex_pinball_equal_channel_v2` | (1/K) Σ_k σ_k · mean_{valid cells of k}(ρ) | Equal. By positive homogeneity σρ(e) = ρ(σe), this is mean dex pinball per channel |

OBSERVED checks against an independent NumPy reference:

- **Literal values.** V1 0.3506566915435323 and V2 0.30238383360861487, identical to the reference.
- **Hand cases.** y=1, q=0, τ=0.9 → 0.9; y=0, q=1, τ=0.9 → 0.1.
- **Gradients.** `torch.autograd.gradcheck` (float64) passes for both versions.
- **Masking.** NaN placed in masked target cells leaves the loss and gradient finite, and the gradient is exactly 0 at masked positions.
- **Reduction.** With unequal per-channel support, V1 pools cells (0.33489) and V2 averages channel means (0.18494). This is intended, and the two coincide only when channel scales and counts are equal.
- **Training versus evaluation units.** V2 equals the plain mean pinball computed directly on dex-scaled quantiles and targets. `MetricAccumulator` (float64, uneven batches) matches the one-shot loss. The float32 versus float64 gap was 6.5×10⁻⁹.
- **Empty support.** An all-false mask raises. For V2, a batch with one channel entirely masked raises. Training windows are complete-case (`complete_consecutive_raw_training_rows`), so this cannot occur in training. Validation batches with no valid cells are skipped by the accumulator.

Analytic comparison (INFERRED). The two losses rank models identically only when
σ_A = σ_B. Otherwise the V1 loss puts 1/σ_k weight on channel k in dex. The V1
gradient on channel k is σ_k⁻¹ times the V2 gradient up to the 1/K factor. This was
pinned by the existing test `test_dex_gradient_ratio_equals_train_std_ratio`. No
claim is made that either loss improves forecasts. That is an empirical
question for the pilot ([protocol §6](V2_TRAINING_PROTOCOL.md#6-loss-comparison-protocol-development-only)).

**Duplication note.** Dex pinball is now computed in three places:

- `training/losses.py` (model side)
- V1 `evaluation/probabilistic.py` `log_scores`
- `evaluation/diagnostics.calibration_diagnostics(space='log10')` on the M0/M1 branch

They agree on complete support. Under masked support, the training metric averages per channel while the evaluation side rejects masked records. No cross-branch numerical agreement test exists yet. That is an M4B integration test ([handoff §6](V2_M4_INTEGRATION_HANDOFF.md#6-required-integration-tests)).

## 5. JEPA/supervised arms (parameter capacity)

OBSERVED with the V1 confirmatory architecture (width 32, depth 3, head 128):
136,332 trainable parameters (encoder + predictor + head) for the full fine-tuning arms.
Head-only arms (`jepa_frozen`, `random_frozen`) train 67,948 head parameters. The
136,332 figure matches the V1 audit (DOCUMENTED there, OBSERVED here via the
benchmark microbench `trainable_parameters`).

Capacity is not matched across model families: JEPA arms 136,332, TCN 44,620,
linear 72,300. The comparators are reference models, not capacity-matched controls.

## 6. Findings and corrections

| ID | Severity | Finding | Status |
|---|---|---|---|
| B1 | MEDIUM | λ penalty is a mean over 72,000 weights, so the proposed grid {0…1} is near-unregularized | Protocol change proposed (§3). Code unchanged |
| B2 | MEDIUM (cost/fairness) | `train_downstream` applies AdamW weight decay to all trainable parameters, including biases and head. The linear model uses Adam with no decay. This is inherited from V1 and identical across J/S/B/TCN | Documented. Not changed, because changing it would break V1 bitwise parity |
| B3 | LOW | `forecast_loss`/`MetricAccumulator` accepted unsorted, duplicate, NaN or out-of-(0,1) quantile levels and returned finite values. Example: levels (0.5, 0.25, 0.05, 0.75, 0.95) gave 0.4582 | **Fixed**: `check_levels` in `losses.py`. Regression test `test_quantile_levels_must_be_strictly_increasing_inside_the_unit_interval` (7 cases × 2 versions, both entry points) |
| B4 | LOW | `fit_controlled`, `fit_tcn` and `fit_quantile_linear` with `validation_window=None` crashed with `AttributeError` inside `window_tensors`, rather than refusing explicitly | **Fixed**: `_prepare(..., require_validation=True)`. Only `pretrain_controlled` opts out. Regression tests in `test_v2_controlled.py` and `test_v2_comparators.py` |
| B5 | LOW | Under extreme head weights in float32, Softplus underflow can give exactly tied adjacent quantiles. `predict` permits ties because it rejects only crossings | Documented. Irrelevant at normal weights (INFERRED) |
| B6 | LOW | `channel_weights` rejects NumPy-typed scales. This fails closed, and `Normalization` stores Python floats | Documented |
| B7 | LOW (design) | Quantile-linear refuses incomplete contexts, while the TCN and JEPA arms accept masks. Under the proposed complete-case support this never triggers | Documented as a fairness boundary |

No BLOCKER or HIGH defects were found in the baselines or losses.

## 7. Regression-test evidence

| Run | Result |
|---|---|
| Baseline full suite at `1826400` (before any change) | **1290 passed**, 1 warning, 65.2 s (OBSERVED) |
| `tests/test_v2_comparators.py` + `tests/test_v2_losses.py` at baseline | 21 passed (OBSERVED) |
| New regression tests before the fix | 9 failed (7 level cases + 2 missing-validation cases), as intended (OBSERVED) |
| `test_v2_losses.py`, `test_v2_comparators.py`, `test_v2_controlled.py` after the fix | 55 passed (OBSERVED) |
| Final full suite | 1310 passed, 1 warning ([handoff §8](V2_M4_INTEGRATION_HANDOFF.md#8-verification-evidence)) |

The single warning is the pre-existing NumPy binary-compatibility `RuntimeWarning`
in `tests/test_experiment_reference.py`.
