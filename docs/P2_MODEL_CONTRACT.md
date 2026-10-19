# P2 training and future model contract

P2 implements a bounded optional PyTorch training foundation. The registered
model is `TRAINING_INFRASTRUCTURE_SMOKE_TEST`: a small linear network, **never
SolarJEPA**. Its purpose is to verify data, optimizer, masks, checkpoints and
native-unit evaluation. Scores from its bounded selections do not establish
scientific forecast skill, event classification, calibration or uncertainty.
The SoLEXS gate remains `BLOCKED_FOR_PHASE_E`.

## Implemented boundary

The UI-independent package `solar_flare_jepa.training` consumes existing P1
contracts; it does not acquire, resample, interpolate or relabel observations.

| Interface | Meaning |
|---|---|
| `Normalization.fit(training_slice)` | Fit dimensioned transforms/statistics on independently eligible, unique raw train rows. |
| `tensor_batch(window, normalization, indices, device=...)` | Explicit normalized float32 features/targets and boolean feature/target masks. |
| `build_smoke_model(spec)` | `forward(features, feature_mask)` returns `[batch, horizon_steps, target_channels]`. |
| `masked_mse(prediction, targets, target_mask)` | Reduce only declared valid target cells; reject empty support and any nonfinite output. |
| `fit_smoke(training_slice, validation_window, ...)` | Bounded seeded Adam steps, validation monitoring and earliest minimum-loss epoch selection. |
| `TrainedSmoke.predict(context, future_grid)` | Accept only causal P1 context and coordinate-only future grid; return native-unit `ForecastPrediction`. |
| `save_checkpoint(path)` / `load_checkpoint(path, expected_identities=...)` | Exclusive save; safe weights-only CPU deserialization with complete provenance checks. |
| `run_training_smoke(config_path, root, ...)` | Existing dataset adapter, chronological raw splits/windows, training/reload and bounded P1 trajectory scores. |

Package import does not import Torch. Install the optional training extra to use
tensor/optimizer/checkpoint operations. CPU is the default; MPS must be requested
explicitly and must be built and available. CUDA and implicit device fallback
are unsupported. CPU inference from a matching checkpoint is tested for bitwise
repeatability in the same runtime; equality across devices or library versions
is not established.

## Scientific and normalization semantics

The July 2024 experiment configuration declares native `xrsa_flux` and
`xrsb_flux`, in `W/m2`, one-minute cadence, 120 context steps, 30 future steps
and stride 30. Its explicit log transform is `log10(flux / reference)`, where
both dimensional reference values are **1 W/m2**. References, channel order,
units, masks, availability and interval coordinates come from the P1 spec and
historical adapter; the training layer invents none of these facts.

For each channel, the normalizer uses only valid cells from `raw_features` or
`raw_targets` of the canonical `TrainingSlice`. Population standard deviation
(`ddof=0`) is fitted after the declared transform. A constant training channel
uses scale 1.0 to avoid division by zero. Raw-row counts, statistics, transform,
references and raw support identity are recorded. Repeated appearances in
context/target windows do not weight those statistics. Validation, calibration
and test data never fit statistics. Supervised train targets are legitimate
training information; future targets are never passed to `predict`.

Raw and P1 window missingness remain NaN with false masks. Only the temporary
normalized tensors fill false cells with zero, and masks stay separate. The
smoke network concatenates feature values and the feature mask so that a
missing cell remains distinguishable from an observed value at the training
mean. Target masks govern the loss and P1 scoring support. No interpolation,
mask upgrading, origin exclusion based on model output or inverse-transform
clipping is performed.

The model predicts points in standardized transformed space. Inference undoes
standardization and then the spec transform; P1 labels log outputs
`inverse_transformed_point`. These are not asserted to be physical conditional
means. The returned shape and physical units are those declared by the future
grid. Invalid/nonpositive valid log input, inverse-transform overflow or
underflow, nonfinite tensors, loss, gradients, parameters or optimizer state
abort the run.

## Fixed smoke budget and selections

`configs/training/p2_smoke.json` predeclares seed 17, two epochs, batch size 16,
four train batches, two validation batches, 32 evaluation origins per partition,
Adam learning rate 0.001 and gradient norm cap 1.0. The selected train and
validation origins are the first chronological eligible origins, determined
before model initialization. There is no shuffle, sampling, early stopping,
test-based hyperparameter tuning or expensive full-model training. The model
parameter budget is capped at two million; configuration integers and numeric
hyperparameters also have hard bounds.

Each epoch records train and validation masked normalized MSE pooled by valid
cell counts. Validation alone selects the checkpoint; ties retain the earliest
epoch. The checkpoint includes weights and Adam state from that selected epoch.
The training record separately reports total optimizer steps and the final
training weights identity, which can differ from the selected checkpoint.

Scoring happens after checkpoint selection on a separately bounded first
chronological subset of each partition, using `evaluate_trajectory` and a fitted
P1 persistence reference. Coverage records eligible, selected and omitted
origin counts, selected IDs and valid/total target cells. Full P1 retained,
excluded and raw support manifests are preserved alongside this subset record.
Overlapping horizons and bounded selection do not imply independent samples or
month-wide model performance.

## Checkpoint and artifact identity

A checkpoint binds executable/configuration source, dataset, forecast spec,
full split manifest, effective training slice, normalization and training config
fingerprints. It records the spec, normalizer, seed, all configured bounds,
weights fingerprint, selected training record, optimizer kind/state and Torch
version. Loading requires the complete externally expected identities and
recomputes the spec, normalization, config and weights identities. Unknown model
kinds, malformed payloads and nonfinite state fail. `weights_only=True` avoids
unrestricted pickle deserialization; load maps tensors to CPU before explicit
device selection. This is consistency/integrity verification, not a digital
signature or authentication against an adversary able to replace every trusted
identity.

The runner requires clean tracked source and matching executed/installed source
through the existing P1 provenance guard. It verifies source/configuration bytes
again before publication. Its custom binary-plus-JSON publisher keeps P1's
single-directory output restrictions and exclusive atomic rename; it does not
weaken the JSON-only P1 publisher. Generated `best.pt` and JSON reports remain
ignored under `results/experiments/`; only code, configuration and small human
contracts belong in Git. Existing output directories and checkpoint files are
never overwritten. Any run failure leaves no published completed execution.

```bash
python -m pip install '.[training]'
python scripts/train_smoke.py \
  --config configs/experiments/p2_goes_july2024.json \
  --root "$PWD" \
  --output-dir results/experiments/p2-goes-training-smoke \
  --device cpu
```

The root must contain the already verified historical acquisition manifest and
raw data. Reinstall a normal package after source changes before running this
CLI. The output includes checkpoint, immutable identity index, dataset/split and
code/config provenance, normalization/training records, native predictions and
scores. The runner serializes/reloads the selected model and verifies identical
predictions before publishing.

## Future SolarJEPA integration: planned, not implemented

A future model should consume the same normalized `[B, context, features]`
values and boolean feature mask, and return `[B, horizon, targets]` finite
normalized point predictions. Scientific feature construction and target
semantics remain outside Torch modules and outside frontend callbacks. Keep
`predict(context, future_grid)` free of future labels; use the P1 output adapter
and evaluator after inverse transformation. Probabilistic outputs require a
separate explicit quantile/distribution contract and scientific validation.

To add SolarJEPA, implement and register its architecture, then extend the
currently smoke-only model construction and checkpoint dispatch with an explicit
architecture/version/parameter identity. Reuse normalization, tensorization,
masked loss, provenance, selection and prediction boundaries. Add independent
causality, mask, numerical, shape, checkpoint compatibility and scientific
validation tests before using its new identity. The current checkpoint loader
intentionally accepts only `masked_linear`; pretrained downloads, JEPA losses,
large training, uncertainty estimation, event labels and SoLEXS model-ready
conversion are future work requiring their own authorized milestone.

## Evidence scope

The implementation tests use explicitly artificial fixtures to verify optimizer
updates, masks, unique-raw normalization, validation-only selection, native-unit
scoring, incompatible identity rejection and deterministic checkpoint reload.
Actual historical GOES run counts/results belong in the P2 execution report,
not this reusable contract. Instrument semantics are documented/verified by the
source-specific adapter and acquisition evidence; this contract supplies no new
scientific observations. MPS capability selection is tested, while actual P2
acceptance training uses CPU. SoLEXS calibrated time/flux and operational GOES
delivery latency remain UNKNOWN or BLOCKED as stated in the main P2 handoff.
