# Research design and feasibility

Date: 2026-09-29. Status: proposed research; foundation implementation authorized.
Training and broad acquisition require the user's next approval. Links to primary
sources and evidence scope are in [LITERATURE_NOTES.md](LITERATURE_NOTES.md).

## Scientific decision

Proceed with a **SoLEXS-first probabilistic forecasting study**, conditional on
calibrated data access. Particle fusion is optional and must earn inclusion.
Do not promise physics-informed or generative novelty before data validation.

Three plausible approaches:

1. Recommended: forecast SoLEXS spectral/band evolution, with GOES used only
   for external labels and an explicitly declared auxiliary target. This retains
   the mission-specific question and has a manageable compute budget.
2. Joint SoLEXS–ASPEX forecasting: potentially useful for solar-wind/SEP science,
   but particle transport and sparse overlap make it a riskier first paper.
3. GOES-only methodological study: accessible and mature, but different scope
   with weaker Aditya novelty. Do not silently adopt it if PRADAN is unavailable.

## Refined research questions and falsifiers

| RQ | Controlled comparison | What would weaken the claim? |
|---|---|---|
| 1 | JEPA pretraining versus identical supervised backbone and masked reconstruction/TS2Vec control | Gain disappears after equalizing parameters, training steps, or tuning |
| 2 | Validated measurement/physical constraint versus no constraint, on JEPA and conventional model | Only generic positivity helps, or spectral fit residuals show misspecification |
| 3 | Multi-resolution versus single-resolution with equal context and comparable capacity | Gain comes only from more history or extra parameters |
| 4 | Qwen text forecasting versus native numerical models on the same reduced task | Formatting errors, cost, or calibration dominate any accuracy gain |
| 5 | AR/ARIMA and conditional variance models versus neural probabilistic forecasts | No residual heteroskedasticity or unstable conditional variance |
| 6 | Later unseen periods and naturally occurring missingness/quality regimes | Gains confined to continuing flares or one active interval |

## Data feasibility and interpretation

Official sources establish that mission products exist, but a public release
announcement is not a per-file inventory. Current registered holdings, exact
overlap, file sizes, SoLEXS product schema, calibration dependencies and gap
statistics remain unverified. The public Access Data link was tested and
redirected to sign-in. No authentication workaround is attempted.

SoLEXS is disk-integrated radiation; ASPEX observes local particles. Solar-wind
material propagates much more slowly than photons; energetic-particle timing
depends on energy, transport and magnetic connection. A correlation can reflect
past eruptions or persistent activity, not a precursor of the next flare.
Only past **arrival-time** particle measurements may be features. Never move
future particle arrivals backwards to construct a predictive input. An event
association study using propagated times must be separate from forecasting.

GOES 0.1–0.8 nm irradiance defines standard flare classes. The SoLEXS passband
differs and counts also depend on response, exposure, gain and detector. A
train-only empirical cross-calibration is not an exact physical equivalence.
Prefer calibrated mission bands; if only counts can be defended, name the task
count-rate forecasting and narrow the paper accordingly.

## Proposed architecture (not implemented)

Input: calibrated channels, validity masks, observation age, and documented
instrument state; timestamps available by forecast issue time only. Start with
1-minute SoLEXS aggregates if exposure and quality permit. Preserve native
data for checking impulsive peaks. STEPS remains a separate 10-minute stream,
with causal joins and staleness masks, not artificial 1-minute interpolation.

Patch the past into nonoverlapping 5-minute tokens. Use a 3-layer, width-128,
4-head context Transformer (target total 1–3M parameters; measure actual count).
An EMA target encoder sees future training patches with stop-gradient. A
2-layer predictor receives context latents, relative horizon positions and
masks, and predicts future latents. No future target encoder at inference.
Use normalized latent regression, monitor representation variance/effective
rank, and investigate collapse before adding variance regularization.

Decode predicted latents into ordered 0.05/0.25/0.5/0.75/0.95 quantiles for
future log band flux. Decoder receives no future observations. Pretrain only on
training-period windows, then compare frozen and fine-tuned heads with the same
supervised backbone. EMA, latent patching and decoder choices are adaptations.

Optional multiresolution: causally aggregate the same past at 1/5/15-minute
scales with separate projections and shared encoder/fusion. Aggregates must
end by issue time. Use 10-minute native particle patches if included. Compare
against conventional multiresolution models with matching history and capacity.

Objective candidate:

`L = λlatent Llatent + λforecast Lpinball + λmeasurement Lmeasurement + λrisk LBCE`.

Start with `λmeasurement = 0`. Tune weights on validation only, log component
magnitudes/gradient norms, and share tuning budgets. Risk heads estimate nested
M+/X+ probabilities on external GOES labels, with X+ ≤ M+ by parameterization.
Do not claim marginal trajectory quantiles define the probability of a maximum:
that requires a temporal joint distribution. A future coherent stochastic
decoder can support trajectory samples and threshold-consistent horizon risks;
it is a separate experiment, not assumed to follow from JEPA.

## Defensible physical additions and rejected shortcuts

The strongest candidate is **instrument-response consistency**: predict a
nonnegative photon spectrum S(E), fold it through a versioned response R and
exposure τ to expected counts μ_i = τ Σ_j R_ij S_j ΔE_j + background_i, and
compare with valid observed counts. Use Poisson likelihood only when detector
processing/dead time and bin statistics justify it; corrected flux requires its
own error model. Response units, effective area inclusion, energy widths,
background uncertainty, aperture selection and pile-up exclusions must be
verified. This is a measurement model, not conservation of total flare energy.
Integrated bands from a shared nonnegative spectrum enforce additivity.

A stronger thermal option, after spectral validation: nonnegative emission
measure distribution and an optically thin emissivity response using documented
atomic data, abundance and temperature assumptions. Evaluate residuals and
nonthermal events; do not enforce an isothermal interpretation globally.

Positivity, nested risks and band additivity are useful constraints but weak
novelty. Generic smoothness can erase real flare impulses and is not physics.
Do not impose MHD/PDE conservation on unresolved full-disk flux without spatial
fields and boundary conditions. Do not substitute STEPS ions for hard X-rays
in a Neupert loss. Neupert-type constraints need appropriate hard X-rays and
an explicitly validated event regime; exclude from the initial scope.

## Features, uncertainty, and preprocessing contract

Primary: calibrated bands and masks; log10 positive flux for dynamic range.
Nonpositive corrected values remain flagged, not silently clipped into events.
Explore trailing means/variance and backward first differences as activity and
rise-rate summaries. Compute derivatives per elapsed time only across valid
adjacent samples. Second derivatives are noise-sensitive and deferred. Hardness
ratios require compatible calibrated bands and denominator quality checks.
Avoid a large indicator library. Each feature has a removal ablation.

Retain native epoch/time scale, bin start/end, exposure, UTC conversion method,
detector, quality bits, units and calibration version. Never infer epoch from
filename. Resample with bins whose right edges are no later than issue time.
No backward fill or centered filters. Keep gaps as masks; short forward fill,
if eventually allowed, has an explicit maximum age and is never used for labels.
Fit scalers and imputation values on training data only. Store Parquet with
metadata sidecars and source hashes; never globally normalize before splitting.

Quantile forecasts are the first uncertainty method. Evaluate interval width,
coverage and pinball loss by horizon and activity regime. Calibrate on a separate
chronological calibration block. Ordinary exchangeable conformal coverage is
not guaranteed under solar temporal dependence; blocked/adaptive conformal is
an empirical extension, with residual updates delayed until outcomes mature.
Use ensembles only if repeated training fits the budget.

## Go/no-go gates

1. Obtain manuals and matched real SoLEXS/ASPEX samples; verify time scales,
   quality, calibration and rights. No scientific Aditya parser is validated yet.
2. Inventory available months without selecting only flare days. Count usable
   independent events, not overlapping windows. Freeze eligible periods.
3. Demonstrate reproducible calibrated extraction and honest common-sample
   comparisons. If particle overlap is inadequate, drop fusion explicitly.
4. Agree on target definition, purge policy, compute budget and final untouched
   period. If fewer than 30 independent M+ events in evaluation, report a pilot
   rather than a stable M+ skill claim; X+ is exploratory unless similarly powered.
   These are planning heuristics, not a statistical power guarantee. Simulate CI
   widths using development-period event rates before freezing the full protocol.
5. Approve baseline/JEPA pilot; advance only with acceptable memory/time profile.
6. Approve physical constraint only after calibration residual audit. If no
   defensible constraint survives, revise the title and report the simpler study.
