# SolarJEPA implementation plan

Reconciled with the storage-foundation update on **2026-10-01**.
[PROJECT_STATUS.md](PROJECT_STATUS.md) is the canonical tracker for status,
blockers, completion criteria and the next three tasks. This document describes
execution using the **same Stages 0–10**. It does not authorize further work.
[RESEARCH_PLAN.md](RESEARCH_PLAN.md) supplies scientific hypotheses;
[EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) supplies the proposed protocol.

**Goal:** validate real Aditya data, construct a frozen benchmark, then perform
fair, bounded forecasting experiments after the required approvals.
**Architecture:** separate source acquisition/inspection/calibration, causal
preparation, immutable windows/splits, model APIs, training and evaluation.
**Current stack:** Python 3.11+ declaration; Python 3.13.3/macOS arm64 dependency
pins; NumPy/pandas/xarray/NetCDF4/Parquet/matplotlib, optional Astropy/CDF.
No torch, statistical-model fitting or LLM runtime is implemented in the
foundation. Other environments and all training budgets remain unprofiled.

## Existing work to preserve

The existing repository/history, remote, research documents, bounded NOAA downloader,
six pinned reference files, metadata inventory, NOAA preparation/EDA and tests
already exist. Do not reinitialize Git, recreate this foundation, revert completed
work, or treat generated NOAA artifacts as an Aditya corpus. Existing files are
listed and verified in the tracker.

The approved `data/solexs-ingestion` milestone adds two locally registered ZIPs,
normal installed import/CLI checks and portable future source identifiers.
It preserves the stable `main` revision, raw files and saved GOES outputs. See
[DATA_STORAGE.md](DATA_STORAGE.md) and
[SOLEXS_FOUNDATION_VALIDATION.md](SOLEXS_FOUNDATION_VALIDATION.md) for evidence.
A normal installation avoids the recurring hidden editable `.pth`; the origin
of the repeated filesystem flag remains unknown. Source changes require reinstall.
The original retrieval digest also corresponds to the pre-checksum manifest;
preserve that historical transition. Independent environment reproduction and
the known NetCDF4 warning remain Stage 9 gaps.

## Global constraints and gates

- The current authorization covers only the storage foundation on its feature
  branch. Scientific extraction, acquisition expansion, model work, integration
  and pushing require their own approvals. Passing checks do not authorize merge.
- No random time splits, future-fill, guessed instrument epochs or raw-data Git.
  Missing/bad/saturated targets are unknown, never zero or negative flare labels.
- Source hashes, finite acquisition caps, exact calibration versions and source
  rights are mandatory. Authentication uses the official registered route.
- NOAA reference validation cannot be reported as Aditya validation. Counts
  cannot receive GOES physical-flux classes without a justified separate mapping.
- Baselines share the benchmark, information, eligible origins and tuning policy.
  Self-supervised pretraining uses training support only, including future targets.
- Evaluation development tests and run provenance are implemented early as
  portions of Stages 7 and 9. Final test scoring waits for all chosen experiments,
  thresholds and calibration decisions to freeze. Stage numbers are deliverables,
  not a requirement to postpone cross-cutting infrastructure.
- Profile an approved short pilot before repeated neural/LLM runs. The proposed
  30 core/6 LLM GPU-hour ceilings and VRAM targets are caps, not measurements.
- Do not add arbitrary smoothness/MHD/Neupert constraints. Physics, fusion and
  generative terminology require the corresponding evidence gates.

## Stage 0 — Research question and scientific scope

Preserve existing research, novelty, literature, paper and experiment documents.
Complete full-method review of mandatory JEPA/SSL and solar forecasting controls.
Record approval of the SoLEXS-first continuous task, separate M+ onset warning,
scope exclusions, event precision criteria and bounded pilot policy. Use real
Stage 1 findings to finalize feasible channels, targets and claims.

Outputs: versioned scope/approval record and aligned research/experiment configs.
Gate: the tracker's Stage 0 completion criteria; a provisional architecture or
an abstract-level citation does not freeze the scientific design.

## Stage 1 — Data acquisition and validation

Preserve the two registered intake archives; use [DATA_DOWNLOAD.md](DATA_DOWNLOAD.md)
for future approved manuals and matching calibration through registered access.
Record actual archive
holdings/levels/versions/bytes without selecting only flare-rich periods. Preserve
raw files outside Git; extend the existing credential-free inventory only for an
approved selection. July 2 remains missing from the obtained collection. Assess STEPS
and SWIS independently and record fusion inclusion or deferral.

Only after reading actual metadata, add source-specific adapters under
`src/solar_flare_jepa/data/solexs.py` and, if justified, `aspex.py`.
Proposed common long-form schema:

```text
time_start_utc, time_end_utc, instrument, detector, channel, value, unit,
valid, quality, exposure, calibration_id, source_sha256
```

Retain native clock/time-scale metadata, energy edges, uncertainty and documented
availability. Fixtures must derive from permitted real metadata. Test clock/bin
conversion, fill/quality flags, detector changes, response units, exposure/dead
time and excluded channels. Compare a calibrated lightcurve against an official
quicklook or documented numerical reference. Generic FITS/CDF inventory is not a
science adapter. Report cadence, gaps, numerical ranges and unavailable fields.

Outputs: reviewed adapter, small calibrated Parquet/metadata, real-file validation
report, acquisition inventory and feasible coverage/volume estimate.
Gate: Stage 1 tested extraction and calibration criteria; broader acquisition
requires the recorded approval and data-use review.

## Stage 2 — Dataset construction, preprocessing and leakage-safe splits

Build on the existing reference preparation contract, with separate Aditya
adapters. Planned modules: `features/causal.py`, `data/windows.py`,
`data/splits.py`, `data/labels.py` under `src/solar_flare_jepa/`.
Do not add hundreds of unexplained indicators. Start with calibrated bands,
masks, observation age, log flux and justified trailing/rise-rate summaries.
Use native particle cadence and causal joins if fusion survives Stage 1.

Each window records origin, full feature/history/target support interval, source
hashes, masks, event IDs and label-availability/maturity time. Separate maximum
threshold exceedance from new-onset labels whose eventual class may mature after
the forecast horizon. Incomplete catalogue coverage cannot create negatives.
Partition construction accepts explicit UTC boundaries and produces immutable
IDs, never random splits. Freeze the primary history/horizon before formal model
comparison; retain other combinations as development or sensitivity tasks.

Tests must verify no cross-partition support/event-cluster overlap; future-value
perturbations leave past features unchanged; training-only scaler/imputation/
response fitting; backward joins never consume later bins; gaps remain unknown;
label maturity is purged; calibration versions are compatible; IDs/hashes are
deterministic. Inspect event clusters and exclusions before freezing cutoffs.

Outputs: versioned dataset/features, train/tune/calibration/test and window/event
manifests, coverage/exclusion/event-count report and precision assessment.
Gate: Stage 2 criteria; proposal `null` dates/manifest must become evidence-backed
values. A three-day engineering sample cannot be the full research benchmark.

## Stage 3 — Classical/statistical baselines

Implement the shared forecast/data/run contract and the development portion of
Stage 7 before tuning. Planned package: `models/statistical/`. Start with last
valid persistence, trailing mean/EWMA and direct linear/ridge, then a small AR/
ARIMA grid. Add climatology/activity/logistic warning controls on the same past
information. Compare against persistence in physical and log units.

Shared interface:

```text
predict(history, mask, horizon) -> Forecast
Forecast: timestamps, units, quantiles or declared joint samples,
          optional separately defined nested warning probabilities
```

For ARCH/GARCH, inspect training-only positive log-flux differences or mean-model
residuals: ACF/PACF, stationarity with cautions, tails, residual/squared-residual
autocorrelation, Ljung–Box and ARCH-LM. Fit the mean first. Compare AR+constant
variance with ARCH and GARCH(1,1) only where meaningful; check parameters,
convergence and regime sensitivity. Simulate conditional paths and invert the
transform correctly for probabilistic flux scores. Variance is neither mean
flux nor a flare probability; do not fit volatility models to integer classes.
Document inadequacy rather than force an interpretation.

Test known forecasts, transform inversion, aligned origins and metric fixtures.
Save development forecasts, diagnostics, costs and selected settings. No final
test inspection during tuning. Gate: Stage 3 reproducible baseline/adequacy
criteria, including an evidence-based applicability decision for ARCH/GARCH.

## Stage 4 — Supervised deep-learning baselines

Planned modules: `models/deep_learning/`, shared `training/`, runnable model/
experiment configs, `scripts/train.py` and the development evaluator. Implement
small LSTM, causal TCN and supervised patch Transformer; GRU is optional or a
recorded substitution if resource evidence warrants it.

Reuse the forecast/mask/decoder contract. Test causality, missing-input behavior,
output shapes, quantile order, transform inversion, fixed-seed behavior and
checkpoint round trips. Profile parameters, memory and seconds/step on the chosen
hardware before training. Use the bounded tuning policy and retain at least three
seeds for selected controls. Store Stage 9 provenance and failures for every run.
The supervised Transformer must supply the matched backbone for Stage 5/6.

Outputs: trained retained controls, configs/checkpoints, common-origin development
predictions and compute logs. Gate: Stage 4 criteria and approved measured budget.

## Stage 5 — SolarJEPA implementation

Planned modules: `models/jepa/encoder.py`, `predictor.py`, `heads.py` and reusable
EMA/latent-loss utilities. Reuse the supervised patch backbone. Starting design:
5-minute patches, width 128, 3 layers, 4 heads, 2-layer predictor; verify actual
parameter count rather than asserting the target 1–3M range. Target encoder sees
future training patches with stop-gradient; inference receives past context only.
Decode predicted latents into ordered log-flux quantiles. A deterministic latent
predictor with marginal quantiles is not a stochastic trajectory generator.

Tests: target stop-gradient, correct EMA updates, train-only support, future-input
absence at inference, mask/output shapes, ordered quantiles, serialization and
latent-collapse diagnostic logging. Keep physics/risk weights off unless their
own gates pass. Use only an approved bounded smoke/profile for verification.

Outputs: runnable/tested plain JEPA, config and measured small profile.
Gate: Stage 5 correctness criteria; full scientific training belongs to Stage 6.

## Stage 6 — SolarJEPA pretraining/training

Planned runner: `training/pretrain.py` plus the shared supervised/fine-tuning
harness. Complete an approved profile of at most 200 optimizer steps before
larger runs. Record RAM/VRAM, seconds/step and estimated total budget. T4 FP16 is
the starting precision; do not assume BF16 support or CUDA quantization on Apple.

Use training-period windows only. Compare no-pretraining, latent JEPA, frozen/
fine-tuned heads and one retained reconstruction/TS2Vec control, with disclosed
pretraining and tuning budgets. Complete the chosen single-seed tuning tier,
freeze hyperparameters and then repeat retained comparisons with seeds
`17,29,43` (five only if affordable). Track variance/effective rank, finite losses,
convergence and all failed runs. Checkpoints include optimizer/EMA/RNG states and
must resume correctly. Produce saved development predictions; keep test sealed.

Outputs: run registry, checkpoints, resolved configs, learning/collapse plots,
predictions and compute totals. Gate: Stage 6 stable repeated-training criteria;
neither a pilot checkpoint nor one favorable score completes the stage.

## Stage 7 — Forecasting evaluation and flare-warning evaluation

Build `evaluation/` and `scripts/evaluate.py` in two parts: tested development
metrics before Stages 3/4 tuning, and locked final evaluation after the retained
Stage 8 choices are fixed. Tests use hand-computed forecast/label fixtures,
including zero-event/undefined denominators and correct origin/units alignment.

Implement MAE/RMSE, persistence skill, pinball, coverage/width, Brier/climatology
skill, reliability, TSS/HSS2, precision/recall/F1, PR-AUC, confusion matrices,
distinct FAR/FPR and event-level alarms/lead time. Use CRPS only for a declared
distribution or adequate trajectory samples, not five quantiles presented as an
exact full CDF. Keep onset and ongoing-event estimands separate.

Lock thresholds on tuning and calibrators on a separate chronological block.
Use identical origins for paired error comparisons; block/event-cluster CIs,
per-seed scores and development-chosen dependence sensitivity. Do not bootstrap
overlapping windows IID. Report exclusions, prevalence and independent events.
Evaluate the untouched later/OOD periods only after protocol/model choices
freeze; do not reuse final-test findings for tuning.

Outputs: reproducible forecast/warning/probabilistic tables and figures with
per-origin predictions, alarm records, paired CIs and complete denominators.
Gate: Stage 7 accuracy/calibration/statistical reporting criteria, not superiority.

## Stage 8 — Ablations, uncertainty and physics-informed experiments

Integrate baseline quantile uncertainty from the start; this stage evaluates its
calibration and the retained extensions. Run common-history/capacity controls
for no-pretraining/SSL and multiresolution before claiming latent benefit. Fit
any interval/probability calibration only on the chronological calibration block;
adaptive updates wait for target/label maturity. Temporal dependence makes
exchangeable conformal guarantees inapplicable without additional assumptions.

Add a response-based measurement module only after Stage 1 calibration review.
Hand-calculate folded counts from a documented response fixture; test response
units, exposure, energy-bin widths, background and nonnegative spectra. Validate
the appropriate observation likelihood and residuals, including dead-time/pile-up
regimes. If defensible, run plain/physics/multiresolution/both and the same physical
constraint on a strong conventional model. If not, record rejection and remove
unsupported physical claims instead of inventing a loss.

Fusion requires matched-origin quality/overlap audit and past particle arrival
features; no shifting future arrivals backward. Marginal trajectory quantiles do
not define `P(max flux > threshold)`. Use a separately tested risk head or, if
approved, a coherent stochastic decoder before threshold-consistent sampled risks.

Optional Qwen experiment: isolated `models/llm/` dependencies; pinned checkpoint/
tokenizer/license; tested serialization/round trips, tokenizer lengths, malformed
outputs and no label-text leakage; 4-bit LoRA only after hardware/runtime profile.
Match a reduced numerical task and report invalid generations, calibration and
sampling costs. It is not the default forecaster or a required core completion
gate if scope explicitly defers it.

Outputs: retained ablation/uncertainty results, physical applicability/residual
report, inclusion/deferral decisions and costs. Freeze choices on development
data before Stage 7 final scoring. Gate: Stage 8 evidence and fairness criteria.

## Stage 9 — Reproducibility and robustness validation

Local import/CLI checks, registration and metadata portability now have regression
coverage. Preserve those checks, then independently reproduce pinned reference
preparation/EDA in a fresh documented environment. Record warning disposition
and prevent tests' `src` injection from being mistaken for installation success.
Preserve historical retrieval facts rather than overwriting them with new times.

For all later data and model runs, record resolved configs, source/split/window
hashes, environment, Git revision/dirty diff, seeds/RNG state, checkpoints and
per-origin predictions/logs. Use portable relative identifiers and declare exact
bytes versus numerical tolerance. Verify resume and independent metric/figure
reproduction. Add meaningful integration/CI checks and profile the selected T4/
Colab/Kaggle environment before claiming platform support.

Complete approved missingness/quality, timing, purge-buffer and temporally
separated regime checks using frozen development-selected rules. Audit all tried
configs/failures and final-test isolation. Output the reproduction/robustness
record required by Stage 9; pins and passing unit tests alone are insufficient.

## Stage 10 — Paper-ready results, figures and documentation

Use [PAPER_PLAN.md](PAPER_PLAN.md); do not prewrite result claims. Generate final
tables/figures from immutable Stage 7/8 outputs and uncertainty estimates, not
hand-edited scores. Link every claim to a run/artifact and reviewed source. Report
coverage/exclusions, independent-event limits, onset versus continuation, all
mandatory controls, seed/block uncertainty, failures and measured compute.

Finish dataset/method/reproduction documentation, full-method literature/novelty
review and claim/data-rights checks. Narrow the title if physics or generation
is unsupported; label underpowered findings a pilot. Outputs are a result-backed
manuscript, regenerable figures/tables and independent reproduction evidence.
Gate: Stage 10 minimum scientific evidence, with no venue/acceptance claim.
Publishing, repository release and pushing require a separate user decision.

## Historical numbering reconciliation

| Former label | Current deliverables |
|---|---|
| Phase 0 — repository/reference foundation | Partial Stages 0, 1, 2, 9 and paper planning only; preserve existing work. |
| Phase 1 — Aditya access/calibration | Stage 1. |
| Phase 2 — causal benchmark | Stage 2. |
| Phase 3 — baseline/evaluation harness | Stages 3–4; early development portion of Stage 7 and run provenance in 9. |
| Phase 4 — JEPA/SSL | Stages 5–6; comparisons evaluated through 7–8. |
| Phase 5 — physical/resolution/fusion additions | Stage 8, conditional on real-data gates. |
| Phase 6 — optional LLM/paper artifacts | Optional Stage 8 experiment; Stage 10 paper outputs. |

The old foundation stop remains a limit on work authorization, not evidence of
global-stage completion. Experiment-plan labels A–D are **compute tiers** inside
these deliverables; they do not compete with project Stages 0–10. All new status
changes and priorities are recorded only in PROJECT_STATUS.md, with this plan
kept aligned.
