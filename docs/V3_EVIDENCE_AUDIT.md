# V3 repository and scientific evidence audit

Date: 2026-10-18. Read alongside [the proposed design](V3_RESEARCH_DESIGN.md).
Full commit and file SHA-256 pins are in
[the research manifest](../data/manifests/v3_research_evidence.json).

## Repository state and method

**OBSERVED:** `main` and fetched `origin/main` both resolved to
`1a4991da4dda9676caeb1d7e35a03408528c3188`; main was not checked out in another
worktree. The original checkout was `presentation/eda-model-comparison` at
`660f469`, with untracked `.agents/` and `docs/P1_FINAL_INTEGRATION_REAUDIT.md`.
Those items were preserved. A managed isolated worktree was created from
`origin/main`; `codex/v3-research-design` was pushed with upstream tracking before
research edits. No milestone branch was merged or copied into main.

Main has the earlier data foundation, not the later model/evaluation modules.
Audit used read-only `git show <pinned-ref>:<path>` across the preserved milestone
branches, actual source/configuration/tests, small tracked verification records,
and two saved result summaries. No model was loaded, fit or invoked, no original
observations or full prediction arrays were decoded, and no new metric was
computed from held-out predictions. Arithmetic means of already stored seed
metrics below are retrospective evidence extraction only, not V3 model selection.

## Architecture and protocol evidence

| Ref (short SHA) / source | Observed implementation and limits |
|---|---|
| V1 `644648f`, `training/jepa.py:242–382` | Five-minute value+mask patches; joint two-channel width 32/depth 3/heads 4 Transformer; predictor depth 2; EMA target encoder; target LayerNorm; future queries; full-context+future teacher during training; optional contiguous context masking; monotone quantile head width 128. Forecast path accepts context only. |
| V1 saved `summary.json`, `/models_config/jepa/config` | Batch 256, eight pretraining epochs, up to 15 fine-tuning epochs, patience 3, 20k training-window cap, five quantiles, lr .001, EMA .996→1, four threads; these are the executed recipe settings, not guessed defaults. |
| V1 `training/jepa.py:507–526` and `training/normalization.py:81–108` | Unique raw-training-bin scaling; historical checkpoint selection in standardized units. This differs from final equal-channel dex score. Different early-stop histories also mean J/S are not equal-update controls. |
| V2 readiness `8e9ce06`, `training/controlled.py`, `training/losses.py` | Reuses V1 builder; provides paired initialization, phase-specific shuffle accounting, J/S/extra-supervised-update/frozen-JEPA/frozen-random controls and versioned equal-channel dex pinball. Matching encoder/predictor update opportunities does not match head updates or teacher FLOPs. |
| V2 readiness, `training/comparators.py` | Existing quantile-linear and TCN comparators; TCN width 32, six residual blocks through dilation 32, RF 253, 44,620 parameters. Full-context linear C120/H30 has 72,300 parameters and rejects incomplete contexts; raw linear outputs can cross and are rearranged under a declared policy. |
| V2 readiness, `forecasting/windows.py`, `evaluation/records.py`, `experiments/v2_descriptive.py` | Raw-support partitioning, canonical identities, exact paired support and descriptive effects. Sampling inference fields are null with reason `NO_VALIDATED_REPLACEMENT`. |
| V2 readiness, `forecasting/statistical.py:285–307` | Volatility starts record convergence flags, but the winner is highest finite likelihood/parameters irrespective of convergence. V3 needs an explicit accepted-fit contract before classical superiority claims. |
| V2 readiness, `evaluation/events.py`, `evaluation/diagnostics.py` | Binary-event scoring accepts supplied labels/probabilities; it does not establish catalogs or event probabilities. Reliability/coverage is marginal, not simultaneous trajectory validity. |

**OBSERVED source arithmetic:** existing trainable total 136,332; EMA encoder 39,808.
The M4 evidence corroborates these counts but does not measure V3 memory on M2.
The same source already contains latent diversity diagnostics; reuse before adding
another implementation. Exact file hashes permit checking line references if
branches move.

## Saved V1 activity evidence

Saved strict run: `results/experiments/v1-full-20261009/summary.json`, SHA-256
`80eae588a706e4b4d84df0daa7e03dcfc54c53ee408d2d6aed30e4bcb9988daf`,
15,674,689 bytes. Source execution commit in provenance:
`4a3f88227ce28dea0e885e68987282285963f38e`. The final V1 branch tip is later;
distinguish artifact producer from audited source tip.

The following are **OBSERVED stored values / INFERRED arithmetic seed means**.
MAE/pinball are pooled across **both channels and all 30 leads**, in dex. The
stratum definition uses future XRS-B only. Neural entries average seeds 17/29/43,
not ensemble predictions. Counts are retained forecast origins, not independent
events. Quiet-below-C has zero test origins and cannot support quiet-regime skill.

| Model | All 1436 MAE / pinball | Rising 112 MAE / pinball | M+ 193 MAE / pinball |
|---|---|---|---|
| JEPA fine-tuned | .11659323 / .03924509 | .35923454 / .12700599 | .26115065 / .09102530 |
| Supervised | .11798546 / .03950022 | .36327943 / .12768568 | .25910921 / .08992262 |
| Persistence | .13385546 / unavailable | .34804115 / unavailable | .30166073 / unavailable |
| Direct ridge | .12431181 / unavailable | .33525695 / unavailable | .26073108 / unavailable |

Source paths: `/scores/test/<model>/log/{log_mae,mean_pinball}` and
`/scores/test/<model>/strata/<stratum>/{origins,log_mae,mean_pinball}`.
`experiments/v1.py:33–53` defines future max B≥2×last as rising and ≥10⁻⁵ W/m²
as M+; these are retrospective threshold windows. `evaluation/probabilistic.py`
averages over channel/lead cells. No raw target was inspected to create new strata.

**INFERRED:** JEPA's global pinball is about 0.646% below supervised for these
fitted seeds. Its rising MAE trails persistence/ridge; its M+ MAE/pinball trail
supervised. Global improvement therefore does not imply robust flare skill.
**UNKNOWN:** event-specific peak amplitude/timing, underprediction direction,
onset skill, causes of errors and future-period generalization. An event catalog
and an independently frozen diagnostic rule are required to address those questions.

## Training results, validation and exposure

**OBSERVED:** the strict V1 saved summary records complete status, zero failures,
three seeds per neural variant and test 1436 origins. Its dataset fingerprint is
`d21b81b42643777f68855d8e02fc17cb7fb326805763117f8e5863233d68ba12`.
Train was May 1–July 22 2024; validation July 22–August 1; test August 1–September 1,
UTC half-open. The historical report's conditional intervals are not rerun or
promoted to validated joint inference in V3.

**OBSERVED:** January's tracked execution manifest and local saved summary agree
on `fit_performed=false`, complete status and 1007 retained origins; the local
summary hash matches the tracked artifact identity
`f87c2825829763ad250e574806165d4f2ac778c0108e7dc786bfde6e5cab2917`.
Its exposure record says `confirmatory_status=UNAVAILABLE` and prior inspection
OBSERVED. Dataset fingerprint:
`b4ff51eff9d8a3d85f30375c07b7623915cd09be9c8f82e26ca17dca13dfcd7c`.
No January model was rerun and no January performance ranking was used here.

**OBSERVED stored evidence:** M2/M3 synthetic reliability investigations did not
qualify a replacement inference method. M3's durable summary and current V2
descriptive code preserve this outcome. No synthetic coverage number establishes
real-solar confidence validity. No additional simulation was necessary for this
research-only audit.

**OBSERVED:** latest V2 G4 lifecycle verification records `pilot_executed=false`,
`real_data_model_constructed=false`, `real_data_validation_predictions=false`
and fitting/execution authorization false. Thus readiness code is not a trained
V2 result. The inspected V2 protocol has May–July development only, explicitly
excludes August/January/candidate years, and is descriptive rather than confirmatory.
Absence of results in inspected records is not proof of no private/unrecorded run;
that remains UNKNOWN and must enter the future exposure audit.

## Discrepancies retained rather than rewritten

- **OBSERVED:** main is substantially earlier than model branches. Research pins
  cross-branch sources; it does not pretend those modules are available on main.
- **OBSERVED:** the older V2 design JSON retains
  `storage_gate_implemented=false`; current `v2_pilot.py:check_storage` and
  supervisor code implement storage gates, as later reservation evidence records.
  The older annotation is historical bookkeeping, not a present missing feature.
- **OBSERVED:** an older G4 SIGTERM/SIGHUP orphan finding is followed by lifecycle
  cancellation/cleanup fixes and synthetic verification. It is not repeated as
  an unresolved current bug. No lifecycle code was changed here.
- **OBSERVED:** benchmark host Mac16,12/Apple M4/16 GiB differs from actual current
  Mac14,2/Apple M2/8 GiB. The M4 projection says `EXTRAPOLATED_NOT_MEASURED`.
  Current M2 identity does not establish V3 training feasibility or historical
  sustained throughput. Scientific training was not benchmarked in this task.
- **OBSERVED/DOCUMENTED:** retrospective bin-end coordinates and science-quality
  product processing do not establish historical arrival timestamps or complete
  per-value upstream causality. Actual delivery remains UNKNOWN.

## Verification scope

The research branch changes documentation and a small provenance manifest only;
no reusable utility was justified. The existing main-based suite was executed in
the new worktree: **166 passed, one warning, 35.79 seconds**. The warning concerns
NumPy binary-size compatibility in `test_cf_clock_bin_end_quality_and_source_retention`;
it was retained, not suppressed or resolved by changing dependencies. Pytest uses
this worktree's `src` through the existing configuration. This verifies the
unchanged data foundation, not the later V1/V2 branch suites or V3 scientific skill.

Independent design/scientific review, file/source identity checks, Markdown link
checks, manifest consistency and final Git publication checks are recorded in
[the review and verification record](V3_INDEPENDENT_REVIEW.md). No full V1/V2 suite
was invoked: some of its fixtures fit models, and no V1/V2 code was changed.
