# Skeptical novelty assessment

Search date: 2026-09-29. This is a scoped literature investigation, not proof
that no similar work exists. Repeat citation/backward/forward searches before
submission; distinguish preprints, code repositories, and peer-reviewed papers.

## Established / existing work (A)

- I-JEPA latent prediction and EMA targets [Assran et al.](https://arxiv.org/abs/2301.08243).
- Time-series JEPA [Girgis et al.](https://arxiv.org/abs/2406.04853),
  [Ennadir et al.](https://arxiv.org/abs/2509.25449), and
  [CF-JEPA author repository](https://github.com/WDSLab/CF-JEPA).
- Physics-informed multivariate JEPA explicitly exists:
  [Phys-JEPA, preliminary June 2026 manuscript](https://arxiv.org/abs/2606.16076).
  Its proposed physical/residual latent decomposition rules out claiming this
  broad combination as new. We have not reproduced its results.
- Hierarchical self-supervision (TS2Vec), temporal patching (PatchTST), quantile
  forecasts, conformal calibration, chronological splits and model ensembles.
- GOES-only flare forecasting and ongoing-flare duration prediction; see
  [Landa & Reuveni](https://arxiv.org/abs/2101.12550) and
  [Reep & Barnes](https://arxiv.org/abs/2103.03957).
- Solar X-ray heteroskedastic models, including ARFIMA–GARCH
  [Stanislavsky et al.](https://doi.org/10.1093/mnras/stz656).

## Adaptations (B), not stand-alone novelty

SoLEXS patch encoder; masked multivariate channels; log flux; multiple
resolutions; Qwen QLoRA baseline; nonnegative flux; nested M+/X+ outputs;
response folding as a known measurement operation. Combining them is not a
new physical discovery. A latent feature is not an identified MHD precursor.
The mission name and a new acronym cannot support a contribution claim.

## Candidate contribution (C), contingent on experiments

An auditable, calibration-aware Aditya telemetry benchmark that tests whether
spectral latent prediction improves **pre-onset** warning and uncertainty under
temporal shift, separately from the easy task of extrapolating an ongoing flare.
The methodological addition, if viable, is response-consistent probabilistic
forecasting with an explicit measurement model, validated against a matching
supervised physical model and current time-series SSL methods.

Support would require: common-period controls, matched backbone/training
budgets, no event leakage, repeated seeds, paired block confidence intervals,
useful lead time, calibration conditional on activity, and credible response
residuals. A negative result that cleanly bounds particle/JEPA benefit can still
be scientifically useful; do not prewrite superiority claims.

Cross-instrument predictive learning may be interesting for SEP/solar-wind
evolution, but is a different target if local particle observations follow the
solar event. Require transport-informed hypotheses and controls for prior
eruptions and missingness before including it in the flare-warning paper.

## Claims currently unsupported

“First physics-informed JEPA”; “MHD precursor representation”; “generative
world model” from deterministic latent regression; cross-cycle generalization
from a short mission interval; causal precursor detection from shifted
correlations; stronger forecasting than conventional models; reliable X-class
warning from a few events. All must be avoided.
