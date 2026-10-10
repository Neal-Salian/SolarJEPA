# M2 independent statistical reliability validation plan

Date: 2026-10-10 (Asia/Kolkata). Base: `fd7203bf9a2e1e3dd78d9750a948b823ab100d36`.
Branch: `research/v2-m2-statistical-validation`. This task-specific synthetic
milestone supersedes the older execution plan's *exposed-data feasibility* M2
for this branch only. Historical protocols remain proposals and are preserved.

**Goal:** Falsify incorrect evaluation behavior using known synthetic truth;
measure reliability without favoring any model or accessing solar observations.
**Architecture:** Add UI-independent synthetic generators and independent
reference calculations under `evaluation/stress/`. Reuse M1 public APIs. A
bounded CLI records aggregate evidence through existing exclusive publication.
**Tech stack:** Python/NumPy/pytest and standard library; no new dependency.
**Spec:** The task-specific M2 instructions in this chat; M1 executable contracts
and `V2_M1_DESIGN.md` define the interfaces under audit.

## Verified discovery and constraints

OBSERVED: fetched refs; M1 local and origin agree at the full SHA above; main
local/origin agree at `1a4991da4dda9676caeb1d7e35a03408528c3188` (no main worktree).
Original presentation checkout and its two untracked items are preserved.
No M2 or teammate model branch existed remotely at discovery. Managed isolated
worktree created from origin/M1; requested M2 branch published before edits.

Source inspection confirms strict `LossPanel`, canonical `EvaluationRecord`,
complete-support dex adapter, seed/fold/influence summaries, circular calendar
bootstrap, calibration and recomputed train normalizer audits. Existing tests
verify deterministic arithmetic, not empirical bootstrap coverage. Fixed folds,
independent representative seeds, approximately stationary weakly dependent
blocks, honest provenance and complete run cohorts remain assumptions.

No scientific inputs, ignored historical results, holdout, acquisition, JEPA fit,
V2 model experiment, V1 artifact/config/model edit, PR, merge or non-M2 push.
Full regression tests may execute existing tiny synthetic training fixtures;
these are software tests, not scientific retraining. Only reproduced validator
defects justify minimal M1 changes. No shared protocol parameter is frozen.

## Questions, hypotheses and estimands

Let d[s,f,t] = loss_A − loss_B. Negative means A is better. The M1 point
estimand is the equally weighted mean of fixed-fold origin means and seeds.
H0: E(d)=0; alternatives include E(d)=−0.4 and heterogeneous effects that cancel.
Test whether null signed estimates are symmetric, known effects are recovered,
and percentile intervals contain the stated truth. Rejection is *interval excludes
zero*, a simulation operating characteristic, not M1's bootstrap fraction as a
p-value. Power is rejection under the predeclared alternative; report direction.

Separate three targets: (i) expected loss over new training seeds conditional on
the realized calendar, (ii) expected calendar path conditional on supplied seeds,
(iii) joint seed/path expectation within the named fixed periods. No method here
infers generalization to a population of independently selected solar periods.
M1 joint intervals are assessed for (iii). Independent seed-only/time-only
resampling are attribution diagnostics with their corresponding conditional truths.

## Data generating processes and ground truth

Primary additive DGP: d=delta_f + sigma_s Z_s + sigma_t X_ft + sigma_e E_sft.
Z and E are independent standard normals; Z_s is shared across fixed folds.
Each X_f is a separate stationary Gaussian AR(1), initialized N(0,1), innovations
sqrt(1−rho²)N(0,1), covariance rho^|t−u|. B=1+abs(d), A=B+d ensure nonnegative
losses without clipping d. Units are artificial loss units, never solar metrics.
One origin/day by default; origin counts/empty days are explicit in special cases.
Truth is mean_f(delta_f). Known Gaussian variance of the equal-fold mean is
sigma_s²/S + sigma_t² sum_f(w_f' R_f w_f)/F²
+ sigma_e² sum_f(sum(w_f²))/(S F²), with w the normalized origin counts.
An oracle normal interval uses this *known DGP* variance; it is not an available
estimator for real losses. Include fold-dependent variance where configured.

| Scenario | Construction and expected behavior |
|---|---|
| Null | delta=0; independent cells and additive crossed factors separately; no preferred sign |
| Consistent advantage | delta=−0.4; estimate centered at truth, higher negative rejection |
| Seed-sensitive | explicit seed shifts (−1.2, +0.2, +0.2); leave-one-seed sign reverses |
| Serial dependence | rho=0, .6, .95; blocks 1/3/7, plus whole-period blocks; inadequate blocks may undercover |
| Unequal support | unequal origins between models must reject; unequal counts between fixed folds retain equal-fold weighting |
| Missing | NaN/Inf losses, partial masks, omitted run, sparse calendars; reject/unavailable, never drop/redraw |
| Heavy tails | standardized t3 finite variance and t1.5 finite mean/infinite variance; truth delta; no Gaussian oracle for non-Gaussian DGP |
| Heteroskedastic | independent Gaussian time factor with scale increasing .25→2; truth known, oracle variance uses scales |
| Calendar heterogeneity | fixed fold shifts (−.8, 0, +.8), unequal fold lengths; overall zero must not hide fold signs |
| Cross-seed dependence | legitimate shared Z_s across folds; additional shared latent seed shock corr=.8 violates independent seeds and should expose undercoverage |
| Interactions | pure iid cell noise; crossed product resampling may be conservative, not assumed exact |

For correlated seed effects replace Z_s by sqrt(c)Z0+sqrt(1−c)Z_s; seed variance
is sigma_s²[c+(1−c)/S]. The oracle knows c. For t draws, t3 uses scale sqrt(1/3);
t1.5 is unstandardized (variance undefined), and its mean exists. Finite simulated
means never establish finite population variance.

## Monte Carlo design, tolerances and failure criteria

Pilot: 5 independent datasets/case, 99 bootstrap draws; measure runtime before
scaling. Main bounded study: 300 datasets/case, 399 bootstrap draws, 95% linear
percentile intervals. Stable per-case SHA-256 seed streams, independent dataset
and bootstrap streams; no global RNG. Use paired simulated datasets for block
sensitivities. Matrix includes S=3/10/20, T=12/30/90 and F=1/3; targeted one-factor
sensitivities, not a full factorial. Maximum 32 cases, 4 million bootstrap draws,
15 minutes wall budget; reduce or stop only for budget, recording any change.
No optional stopping based on effect/sign/coverage. Repeated runs compare
deterministic scientific payload hashes, excluding timing metadata.

Report coverage, both null rejection directions, power, CI width, estimate bias,
RMSE, missing interval fraction and binomial Monte Carlo SE sqrt(p(1−p)/R).
Also Wilson 95% Monte Carlo intervals; zero counts do not imply zero uncertainty.
Report denominator for every rate; unavailable intervals are not silently omitted
and get separate conditional and unconditional coverage rates. Empirical nominal
coverage is INCONCLUSIVE at this budget; severe undercoverage is a limitation.
For each DGP report empirical estimator SD against oracle SD where applicable.

Independent direct-origin resampler must match M1's draws at atol=1e−12,
rtol=1e−12 on non-extreme fixtures with unequal counts, empty days and two folds.
Literal calibration/weighting arithmetic atol=1e−12. Large calibration
reductions use error/max(1, abs(reference)) <=1e−12: 20,000-cell constant
width sums exhibited about 2e−12 absolute rounding, so this scale-aware check
uses an independent math.fsum reference rather than asserting exact sums.
Coverage inclusion allows 1e−12*max(1,abs(truth)) rounding for degenerate truths. Gaussian calibration coverage
must agree with analytic probabilities within 5 binomial SE per cell plus 1e−12;
this is a deterministic seeded smoke criterion, not a simultaneous formal test.
Use 20,000 calibration origins, two leads, one artificial channel. Compare
normal forecasts: calibrated, scale .5/2, bias +.75, tail-only scale .5 at .05/.95,
and a rare-regime conditional failure with exact marginal calibration via a
stratified Uniform mixture. Report empirical counts, widths, interval scores,
per-lead and per-regime behavior; crossing must reject at the contract boundary.

Failure criteria: incorrect deterministic references, hidden sample deletion,
nonfinite output without explicit rejection, wrong sign/weighting, acceptance of
observable invalid temporal support, nondeterministic payload or artifact
replacement. Test statistical pathologies without requiring every CI to work.
Do not fix assumptions by silently changing the inference procedure.

## Adversarial and numerical review focus

Probe train/test overlap, embargo one-nanosecond boundaries, target/maturity
crossings, future-fitted normalization, duplicate/out-of-order origins, dataset,
horizon, support and provenance conflicts, invalid fitting ranges, target/prediction
identity. Test legitimate equality boundaries too. Classify DETECTED LEAKAGE,
DETECTED CONTRACT VIOLATION, UNDETECTABLE FROM AVAILABLE METADATA. Standalone
records cannot authenticate fit success, planned missing seeds or secret future
features; fitting audit lacks evaluation partition bounds, so builder evidence
is required for within-evaluation split containment.

Numerical probes: empty/single/tiny support, constant differences/zero variance,
extreme finite values, NaN/Inf, duplicate/reordered identifiers, units, quantile
levels, missing/failed runs, provenance omissions, repeated seeds and sparse days.
No Hypothesis dependency is installed; bounded parameterized/property loops suffice.
Inspect memory allocations for large calendar spans and enforce a justified
explicit guard if a reproducible unbounded-allocation path exists.

## Implementation tasks and verification

1. **Synthetic/reference utilities** — create `evaluation/stress/synthetic.py`,
   `reference.py`, `study.py`; tests in `tests/test_m2_statistics.py`. Public
   `Scenario`, `generate_panels`, `oracle_variance`, `reference_bootstrap`,
   `run_case` carry DGP/config/truth explicitly. Write reference/determinism/shape
   tests first, run RED for missing APIs, implement, run GREEN.
2. **Adversarial/calibration/numerical evidence** — create reusable
   `evaluation/stress/contracts.py`, `calibration.py`; new dedicated M2 tests.
   Reproduce failures before minimal production fixes; rerun all M1 tests.
3. **Reproducible CLI/study** — create `scripts/run_m2_validation.py` and
   `configs/validation/m2_synthetic.json`. Reuse `code_provenance`,
   `atomic_record`, `verify_artifacts`; output under ignored results with
   config/source hash + UUID, no replacement. Test CLI and payload repeatability.
   Commit executable study before main runs so Git SHA identifies clean source.
4. **Independent review/report/publication** — statistical and software subagents
   review whole M2 source; fix reproduced HIGH/BLOCKER defects with regressions.
   Run targeted/full tests, normal installed import outside checkout, pip check,
   artifact replay/hash, diff/check/status/protected-path/index/ignore audits.
   Create `V2_M2_STATISTICAL_RELIABILITY_REPORT.md`, include all results/limits,
   explicit readiness gate. Push M2 only, verify remote SHA. No PR or merge.

## Scope classification and readiness

**IMPLEMENTABLE_NOW:** bounded synthetic evidence and independent references,
adversarial fixtures, strict reproducibility, minimal justified validation fixes.
**REQUIRES_SHARED_APPROVAL:** real V2 seed/calendar/embargo/multiplicity/block
choices, planned-run manifests/fit acceptance interface, model-owner adapters,
period-population estimand, candidate access and exposed-data feasibility.
**OUT_OF_SCOPE:** JEPA architectures/training, scientific V2 runs, confirmatory
data, future acquisitions, real solar conclusions, UI, model/runner refactors.

Readiness concerns only infrastructure. PARTIALLY_READY if arithmetic/contracts
pass but empirical assumptions or integration metadata remain unresolved;
NOT_READY for unresolved reproduced severe defects; READY_FOR_INTERFACE_INTEGRATION
only with explicit documented limitations and adequate contract evidence.
No verdict authorizes confirmation or the next milestone.

Methodological context: [Owen and Eckles](https://arxiv.org/abs/1106.2125)
describe crossed-array bootstrap limitations; [Politis and White](https://mathweb.ucsd.edu/~politis/SBblock-revER.pdf)
show why block choice matters; [Gneiting and Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)
motivate proper quantile/interval scores. None proves nominal coverage of M1's hybrid.
