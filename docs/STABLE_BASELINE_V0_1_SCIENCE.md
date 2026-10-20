# Stable Baseline v0.1 scientific preservation and replay

Audit date: **2026-10-18, Asia/Kolkata**. Scope: the existing retrospective
GOES-16 V1 software, observations, saved model outputs and dashboard. This report
records fresh independent inspection and inference checks; original scientific
reports remain unchanged.

**Scientific replay verdict: PASS for the frozen retrospective baseline.** All
nine original neural checkpoints reproduce every saved August forecast exactly
in the fresh integration environment. This establishes numerical preservation of
the inspected experiment, not prospective scientific performance, publication
readiness, operational validity or new JEPA superiority. The overall release
verdict also requires the technical, dashboard and integration checks recorded
in the release-readiness report.

Evidence labels follow the repository policy: **DOCUMENTED** refers to
authoritative instrument/data documentation, **OBSERVED** to direct source,
file or execution evidence, **INFERRED** to a derived interpretation, and
**UNKNOWN** to an unestablished quantity. Earlier repository reports are
historical evidence; their reported checks are not silently counted as freshly
executed checks here.

## Frozen identities and retained scientific behavior

**OBSERVED:** the required implementation is the existing ancestry
P1 forecasting/contracts → P2 GOES/training foundation → V1 → presentation EDA
→ four-page dashboard → fifth prediction page. The prediction tip is
`a4951516dc2094ceb246b016700d1483a808212b`. Comparison of the integration
worktree against that tip found no differences in `data/`, `forecasting/`,
`training/` or `experiments/` under `src/solar_flare_jepa/`, or in either frozen
V1 experiment/model configuration. The scientific inference dependencies also
pass the existing immutable byte guards before replay.

| Identity | Value |
|---|---|
| Original strict experiment | `v1-full-20261009` |
| Actual source executed by that experiment | `4a3f88227ce28dea0e885e68987282285963f38e` |
| Historical V1 audit branch tip | `644648f7d555` (distinct from experiment producer) |
| Dataset fingerprint | `d21b81b42643777f68855d8e02fc17cb7fb326805763117f8e5863233d68ba12` |
| Forecast-spec fingerprint | `094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94` |
| Train-only normalization fingerprint | `848623009ce048a14e32c50b7c70d9c9728cdd77391f10115ec1c8fd46d039a9` |
| Original `summary.json` SHA-256 | `80eae588a706e4b4d84df0daa7e03dcfc54c53ee408d2d6aed30e4bcb9988daf` |
| Original `test_predictions.npz` SHA-256 | `59bcd596fefd6b10edeec93a69d7172343d4ffb7dc120f98a5185c1e35a3da82` |

**OBSERVED source behavior:** XRS-A/XRS-B primary corrected irradiances remain in
W/m². The preserved adapter checks the native time convention, record-start
semantics, measured file coverage, cadence, units and status/electron flag
schemas. Its channel-specific quality rule requires finite positive flux,
status zero, accepted electron bits, sample count 1–60 and encoded valid bounds.
Observed timestamps, valid channel cells and independent events are different
counts. An average containing one measurement is eligible under this existing
policy; the integration does not invent a stronger quality threshold.

**OBSERVED source behavior:** the forecast uses exactly 120 consecutive completed
one-minute bins × two channels and emits 30 one-minute forecast bins × two
channels. The context is `[issue−120 min, issue)`; the future grid is
`[issue, issue+30 min)`. The original benchmark stride remains 30 minutes.
`retrospective_bin_end` availability remains explicit. Missing or rejected
context cells are never filled. Optional future observations are a separate
display payload and do not enter prediction.

**OBSERVED source/checkpoint behavior:** the original transform is
`log10(F / [1 W/m²])`, followed by means and population scales fitted on unique
raw training support. Every replayed checkpoint carries the same stored
normalization fingerprint; nothing is refitted on August. Safe weights-only
checkpoint loading, strict state keys, weight fingerprints, model variant,
seed, original record and forecast specification are checked. Inference uses
CPU, batch size 256 and four Torch threads, matching the original recipe.

**OBSERVED:** the model outputs five ordered marginal quantiles
`q05/q25/q50/q75/q95`. The displayed point forecast is q50. Central 50%/90%
bands are nominal and uncalibrated. They are not simultaneous trajectory
coverage guarantees, an exact joint predictive density or uncertainty about a
model-comparison effect.

## Fresh execution evidence

Four explicit manifest verifications checked **123 native files / 36,535,474
bytes**, with each file matching its frozen manifest identity:

| Manifest | Files | Bytes |
|---|---:|---:|
| `goes_v1_202405.json` | 31 | 9,169,020 |
| `goes_v1_202406.json` | 30 | 8,910,715 |
| `goes_p2_july2024.json` | 31 | 9,200,347 |
| `goes_v1_202408.json` | 31 | 9,255,392 |

**OBSERVED:** the new [complete reference verifier](../scripts/verify_v1_reference.py)
was run with the fresh integration `.venv` and the copied original artifact
bundle. It first verifies the frozen source/manifest/checkpoint/summary/archive
identities. It then reconstructs all contexts and targets independently from
the 31 August NetCDF files, before loading a checkpoint. All 1,436 saved origin
IDs, measured minute coordinates, contexts, context masks, actual future values,
target masks and saved temporal support agree exactly.

| Original model | Origins | Point arrays | Five-quantile arrays | Maximum absolute / relative difference |
|---|---:|---|---|---|
| `jepa_finetune_seed17` | 1,436 | Exact | Exact | 0 / 0 |
| `jepa_finetune_seed29` | 1,436 | Exact | Exact | 0 / 0 |
| `jepa_finetune_seed43` | 1,436 | Exact | Exact | 0 / 0 |
| `jepa_frozen_seed17` | 1,436 | Exact | Exact | 0 / 0 |
| `jepa_frozen_seed29` | 1,436 | Exact | Exact | 0 / 0 |
| `jepa_frozen_seed43` | 1,436 | Exact | Exact | 0 / 0 |
| `supervised_seed17` | 1,436 | Exact | Exact | 0 / 0 |
| `supervised_seed29` | 1,436 | Exact | Exact | 0 / 0 |
| `supervised_seed43` | 1,436 | Exact | Exact | 0 / 0 |

That is **775,440 point values and 3,877,200 quantile values** checked. Checkpoint
hashes, summary bytes and archive bytes were checked again after inference and
were unchanged. All nine checkpoint SHA-256 identities are pinned in the
verifier and recorded in the generated report.

The acceptance tolerance is the pre-existing single-origin verifier's
`rtol=1e-6`, `atol=1e-15 W/m²`; the full original batch shape achieved exact
equality without using that allowance. The tolerance is a numerical replay
criterion, not a scientific uncertainty value or forecast metric. The earlier
single-origin command was also independently run on the preserved prediction
worktree: its first saved origin passed, with maximum quantile relative
differences `6.3050053e-7` for JEPA and `7.8812510e-7` for supervised.
Shape-dependent float32 differences explain why the report distinguishes exact
full-batch replay from tolerated single-origin replay.

Fresh integration runtime: CPython 3.13.3, NumPy 2.2.6, Torch 2.6.0,
macOS 26.3 arm64, CPU/four threads/batch 256. The recorded complete verifier
execution took **9.188 seconds** on this host. Timing is an observation, not a
performance guarantee. Detailed new evidence is in the ignored
`results/release/scientific_reference_audit.json`; the command recreates it.

The new subprocess regression tests were observed failing before the verifier
existed and then passing. They exercise the full original bundle and a
structured failure for an absent repository/bundle. A source clone without
the ignored bundle skips only the full-bundle test with an explicit reason;
existing mismatched artifacts are not skipped. The release checker and verifier
themselves fail when required artifacts are missing. The complete integration
suite result belongs to the release report, rather than being inferred from
these targeted tests.

The archive contains 22 original model identities. This new command replays all
nine neural checkpoints; **it does not restore/refit the 13 point/statistical
comparators or recompute their performance metrics**. Existing baseline
implementation/tests and historical comparison artifacts remain available. No
model retraining, V2 pilot, new scientific evaluation, acquisition or network
request was executed by this verifier.

## Reproduction commands

After following the release setup/restore instructions and installing source
normally, run from the integration checkout:

```bash
# Explicit --manifest matters: the historical --verify CLI does not use --config.
.venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --verify --manifest data/manifests/goes_v1_202405.json
.venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --verify --manifest data/manifests/goes_v1_202406.json
.venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --verify --manifest data/manifests/goes_p2_july2024.json
.venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --verify --manifest data/manifests/goes_v1_202408.json

.venv/bin/python scripts/verify_v1_reference.py --root "$PWD"
.venv/bin/python scripts/verify_flux_prediction.py --root "$PWD"
.venv/bin/python -m pytest -q tests/test_v1_reference_replay.py
```

The full command requires the original nine `.pt` files, `summary.json` and
`test_predictions.npz` under `results/experiments/v1-full-20261009/`, plus all
31 pinned August native files. All of these are intentionally ignored by Git.
The app's prediction page needs its approved seed17 checkpoint(s) and August
observations; it does not open the archived prediction arrays or summary.

## Scientific limits retained from the original evidence

- **OBSERVED:** the original frozen training interval is May 1–July 22 2024,
  validation July 22–August 1, and test August 1–September 1, UTC half-open.
  These are one satellite and four months. Repeated August inspection makes it
  historical evidence, not a new untouched holdout for subsequent research.
- **OBSERVED:** the retained benchmark is a complete-case population with
  overlapping contexts and 1,436 August origins. A forecast origin is not an
  independent flare. Additional one-minute dashboard issue times supplement
  retrospective examples and do not extend the original benchmark metrics.
- **UNKNOWN:** historical acquisition/delivery time, as-issued product revisions,
  prospective performance, other-satellite compatibility and calibration under
  deployment shift. A 30-bin model horizon does not establish 30 minutes of
  useful operational warning.
- **OBSERVED in the retained V1 audit, not recalculated here:** the fine-tuned
  JEPA/control aggregate pinball difference is approximately 0.646% for three
  fitted seeds. Removing one seed reverses the difference. **INFERRED:** a
  stable JEPA pretraining advantage across training randomness remains
  inconclusive. The historical conditional daily-block intervals omit training
  and model-selection uncertainty; integration does not upgrade their status.
- **OBSERVED in retained source/reports:** neural selection minimizes normalized
  pinball while final/classical comparison uses equal-channel dex pinball.
  Classical variance selection admits finite fits with unsuccessful convergence
  flags, and some retained fits have near-unit persistence. These historical
  limitations are preserved rather than silently changing the experiment.
- **OBSERVED in retained source/reports:** five quantiles yield a quantile score,
  not exact CRPS. Historical sharp-peak examples can be missed despite improved
  aggregate losses. The V1 path has no validated flare-event labels, event/onset
  probabilities, joint trajectory model or physical dynamical constraint.
- **UNKNOWN:** GPU/MPS and other-platform numerical equivalence. The fresh
  integration checks here establish the named CPU environment only. The retained
  NumPy/netCDF ndarray-size warning is disclosed in technical verification;
  exact replay does not diagnose its underlying cause or guarantee all native
  execution paths.

## Explicitly excluded workstreams and gates

**OBSERVED from preserved branch source/reports:** none of the following is a
release component or permission to execute another milestone:

| Workstream inspected | Exclusion and unresolved gate |
|---|---|
| V2 latest readiness, `8e9ce06` | Protocol/guard/lifecycle infrastructure, with no authorized real-data pilot or trained replacement result. G4 owner authorization, current runtime/input binding and its prerequisites remain separate. No V2 fitting or pilot was executed. |
| V3 research, `3692c5b` | Evidence/design/literature work only. It neither implements nor validates a V3 model. Fresh evaluation-data eligibility, event/fold support, controls and scientific promotion rules remain research work. |
| Near-real-time foundation, `eacdb2c` | Live inference deliberately refuses before checkpoint use. SWPC JSON minute-tag support, full quality/calibration parity, per-row availability and cross-satellite validity remain UNKNOWN. Numerical completeness or matching wavelength bands cannot establish scientific equivalence to frozen GOES-16 science v2-2-1 inputs. |
| SoLEXS scientific integration, `df88009` | Native preparation/reference witnesses do not clear physical forecasting. Absolute clock precedence, bin support/availability, effective live exposure, response-channel correspondence, correction/calibration applicability and release-specific physical units remain unresolved. No timestamp shift, channel relabeling, flux conversion, flare label or cross-instrument model input is invented. |

The user-reported PRADAN acquisition remains explicitly user-reported. Hash
identity does not authenticate acquisition or resolve instrument semantics.
Inherited fail-closed diagnostic foundations are retained for compatibility;
their presence is not scientific clearance for SoLEXS model functionality.

**Remaining scientific requirements before a bounded-baseline merge:** preserve
the frozen identities/results, make the original bundle available to release
verification, retain these limitations/exclusions in user-facing documentation,
and finish independent scientific/technical and dashboard integration review.
Fresh model science, live operation, SoLEXS physical forecasting and V2/V3
execution each require their own scoped decision and evidence; they are not
prerequisites to honestly shipping this historical baseline. Any merge into
`main` still requires the user's explicit approval, and pushing `main` requires
separate authorization.
