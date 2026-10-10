# M3.1 statistical inference research and implementation plan

Date: 2026-10-10. Base: `94cae59398e52a65074ec66c73ad94bd47ca8867`.
Branch: `research/v2-m3-inference-remediation`.

**Goal:** Investigate M2 failures and benchmark a bounded set of conditional
inference candidates without changing M1 defaults or the shared V2 protocol.
**Architecture:** Separate experimental `evaluation/inference_research/` modules
consume existing paired `LossPanel` objects. Reuse unchanged M2 generators and
publication/provenance utilities; add one explicit moving-average overlap law.
**Stack:** NumPy, standard library and existing optional SciPy for t quantiles.
**Spec:** The task-specific M3.1 request; M0/M1/M2 executable contracts and the
historical proposed V2 protocol, whose approval/access decisions remain open.
Implementation is inline with independent read-only statistical/software reviews.

## 1. Verified discovery and M2 evidence

Fetched all refs. M2 local/origin match the full base SHA above. Original
presentation checkout and its two untracked items are preserved. M3 did not
exist; a new managed worktree was created from origin/M2 and its requested
branch published with upstream before edits. No protected branch is changed.

OBSERVED before M3 implementation: full M2 CLI rerun, 25 cases ×300 datasets
×399 draws, reproduced scientific payload
`0c4ee722a0c287774c277928342fe548648dee81e5cb137ed3238297d3d53a1e`
in 235.886 s. Baseline suite: 1,338 passed, one existing NumPy warning, 218.06 s.
Source/evidence inspection identifies `evaluation/comparison.py:paired_comparison`
and `evaluation/stress/study.py:run_case` as the producing kernels.

M1 draws one paired seed vector across all fixed folds; circular day blocks are
independent by fold and shared across models/seeds. Means use equal fixed-fold
weights and origin counts; required empty draws invalidate the whole interval.
NumPy linear percentiles construct CIs; bootstrap sign fractions are not p-values.
RNGs are explicit; M2 SHA-derived streams and all original DGPs are preserved.
M2 fixed paired arithmetic defects were already corrected in the base.

Recorded/reproduced additive-null coverage 90.3%, null exclusion 9.67%, known
negative-advantage power 82.67%; strong AR coverage 13–29%, correlated-seed 19.3%,
iid-cell 99.7%. Different mechanisms are hypotheses to examine, not one diagnosis:
finite-seed percentile error; insufficient temporal information/short blocks;
invisible common seed shocks; and interaction variance inflation.

## 2. Questions and estimands

For paired losses d[s,f,o], let r_s=mean_f(mean_o d[s,f,o]) and theta_hat=mean_s r_s.
Origins average identical horizon/channel/quantile support; horizons are not
independent replicates. Named folds remain fixed and equally weighted.

| Target | Random units and conditioning | Identifiability |
|---|---|---|
| seed_conditional | New independent training seeds; fixed realized evaluation calendar, training data and selection recipe | Possible with representative independent runs and a declared seed-score law |
| calendar_conditional | New within-fold calendar paths; supplied seed effects fixed; independent disjoint fold paths | Requires adequate weak dependence/stable mean and explicit time units |
| joint | New seeds and within-fold paths, same fixed named periods | M1 comparator only; no validated replacement presumed |
| future-period population | Independently selected datasets/periods | Not identified by three purposively chosen folds; no fold bootstrap |

In the M2 additive law, seed_conditional truth is delta_bar plus the realized
weighted calendar factor; calendar_conditional truth is delta_bar plus the
realized seed factor. Cell noise is integrated out. Conditional truths often
differ from zero when joint delta is zero. Their zero-exclusion rates MUST NOT
be called Type-I error. Report size at the true conditional parameter separately;
zero-null size/power only where the corresponding truth is constant zero/nonzero
by DGP construction. Do not rank methods with different estimands as substitutes.

## 3. Literature and candidate screening

Primary sources browsed; bibliography links preserve access depth. No new tool
or research dependency is installed. These theories do not certify solar data.

| Candidate | Units/assumptions, cost, finite-sample limits and decision |
|---|---|
| Moving blocks | Overlapping fixed contiguous blocks; weakly dependent approximately stationary path, growing block/count asymptotics; O(BT). Boundary weighting differs from circular blocks. Researched, not separately implemented. |
| Circular blocks | Existing M1 crossed method; paired seed and day units, O(BSTF), finite S and T, artificial wrap; whole-period blocks collapse time variation. Retain comparator. |
| Stationary blocks | Geometric run lengths, restart p=1/ell; stationary weakly dependent finite-variance calendar scores. O(BT), bounded arrays. Implement basic intervals conditional on fixed seeds, ell=3/7 prespecified. |
| Hierarchical bootstrap | Appropriate for nested sampling, not a seed×calendar cross; cannot manufacture independent periods or runs. Do not implement a wrong nesting. |
| Two-way cluster variance | Independent clusters in each crossed dimension, many clusters in both, overlap subtraction; serial dependence needs a justified time grouping. Small/unknown effective time clusters and arbitrary seed correlation remain unresolved. Research only. |
| Bartlett HAC / DM style | Mean paired daily scores, explicit lag L=3/7, finite moments and weak dependence with stable mean; asymptotic normal critical value, O(TL). Independent fixed folds combine with 1/F². Implement calendar-conditional only. No arbitrary h−1 truncation for serial solar losses. |
| Studentized blocks | Potential refinement, but requires reliable variance/studentizer inside every draw; small/zero variance and strong persistence remain problematic, extra O(BTL). Research only; no invalid-draw filtering. |
| Cluster wild bootstrap | Independent clusters, appropriate restricted-null construction, many/enough informative clusters; few-cluster discreteness/imbalance cannot be cured by B. O(BN). Research only. |
| Seed Student t | Per-seed equal-fold mean, S independent common-mean Gaussian scores, df=S−1; exact iid Gaussian, conservative independent Gaussian heterogeneity/normal scale mixtures at confidence≥.95. O(SN), S≥2 and nonzero observed dispersion. Implement conditional on fixed calendar. |
| Joint additive variance | Sum of seed and time components requires independent additive factors. Interaction enters both naive components; serial HAC has no justified T−1 chi-square df. No implementation without a defensible correction and independent validation. |

References: [Newey–West working-paper abstract; full PDF inaccessible](https://www.nber.org/papers/t0055),
[Politis–Romano publisher abstract](https://www.tandfonline.com/doi/abs/10.1080/01621459.1994.10476870),
[Cameron–Gelbach–Miller author manuscript](https://cameron.econ.ucdavis.edu/research/JBESpaper2009version.pdf),
[Cameron–Miller author survey](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf),
[Diebold–Mariano original paper](https://www.ssc.wisc.edu/~bhansen/718/DieboldMariano1995.pdf),
[Ibragimov–Müller §2.1](https://www.princeton.edu/~umueller/tstat.pdf),
[Owen–Eckles](https://arxiv.org/abs/1106.2125),
[corrected block-length methodology](https://public.econ.duke.edu/~ap172/Patton_Politis_White_2009.pdf).
Stationary/HAC asymptotic requirements are not a finite T guarantee. No universal
minimum cluster count exists; the resource/design guards below are necessary
conditions only. Arbitrary common seed shocks cannot be estimated from one cohort.

## 4. Selected interfaces, restrictions and failure behavior

Typed frozen `Design`, `MethodConfig`, `InferenceResult` and `RunState` dataclasses.
`infer(a, b, *, design, config)` requires explicit estimand, sampling unit,
independence/calendar/law declarations, planned seed IDs and complete per-model,
fold, seed fit-status ledger; missing/failed runs reject, including common omissions.
Declarations do not authenticate actual fitting history or prove independence.

seed_t requires independent seed IDs, fixed calendar, Gaussian or symmetric
normal-scale-mixture seed scores and confidence≥.95. No calendar inference is
claimed. Calendar candidates condition on arbitrary fixed seeds, require separate
independent fold paths and finite-variance weak dependence. HAC permits declared
heteroskedastic weak dependence; stationary bootstrap requires stationarity.
Both initially require complete equal positive origin counts per calendar day
within each fold; unequal fold lengths are allowed. Unequal/missing day counts
reject rather than silently changing weights or deleting days.

HAC: V_f=[sum e_t²+2 sum_(k=1)^L (1−k/(L+1))sum e_t e_(t−k)]/T²,
explicit T/(T−1) correction; combined V=sum_f V_f/F², normal critical value.
Require T≥4(L+1) and at least eight days. Stationary basic CI is
[2 theta_hat−q_(1−alpha/2)(theta*), 2 theta_hat−q_(alpha/2)(theta*)]; uniform first
day, geometric restart, circular continuation, shared across fixed seeds/models.
Require T/ell≥4, T≥8. These guard thresholds are research settings, not proof of
four independent blocks. S=1 is supported for calendar-only if its ledger is valid.

Nonfinite arithmetic rejects; constant/zero dispersion gives an explicit
INSUFFICIENT_INDEPENDENT_INFORMATION result, never an apparently valid point CI.
Bound calendar cells≤1,000,000 and bootstrap day-index cells≤1,000,000. Unsupported
assumptions/designs have explicit unavailable reasons; malformed contracts raise
ValueError. No method fallback and no loss/run/origin omission.

## 5. Development and frozen evaluation

Create separate `configs/validation/m3_development.json` and `m3_evaluation.json`
before production code or evaluation results. Commit both and this plan first.
Development reuses 13 selected M2 DGPs unchanged,
R=100, B=199, master seed 20261011. Pilot uses only development, R=5, B=99.
Final evaluation uses 16 new prespecified laws, R=400, B=399, seed 20261117:
Gaussian seed null/positive effect, mixed null/negative effect, pure calendar
null/positive effect, iid cells, rho=.97 short and rho=.9 long paths, correlated
seed shock c=.65, unequal fixed-fold effects/lengths, heteroskedasticity, t3/t1.5,
overlap MA(4), and unequal/missing day support. Exact parameters live in frozen JSON.
The MA law adds a five-innovation normalized moving average to a time-zero M2
base; its overlap and conditional truths are explicit. Original M2 laws are not edited.

All methods see exactly the same generated panels within each replication.
Method settings remain seed_t, HAC L=3/7, stationary ell=3/7, M1 joint block=3.
SHA-derived namespace distinguishes stage/case/replicate; block variants use
common RNG labels. No final-result tuning or setting selection. Any revision
after evaluation is logged and makes that evaluation development evidence;
use a separately frozen fresh seed/config for any new selection claim.

Metrics: unconditional/available-only truth coverage with Wilson95/MCSE,
availability/failure reasons, true-parameter size, genuine zero-null Type-I rate,
directional power where truth is a fixed alternative, zero-exclusion otherwise,
width, bias/MCSE (finite variance only), paired method coverage-disagreement
uncertainty only within the same estimand, runtime and process RSS. Rates retain
all denominators. Conditional estimands are never pooled with joint estimates.

## 6. Acceptance, budget and reproducibility

Gate eligible cases by declared DGP/support before observing results. Exact
Gaussian seed-t assessment requires independent seeds and nonzero seed-score
variance. Conservative scale-mixture claims are reported separately. Calendar
gates require supported law/counts/length and nonzero calendar variance. For each
eligible final case: availability=100%, Wilson95 coverage lower≥.90 and upper≤.99,
and for genuine zero-null cases Wilson95 Type-I upper≤.10. All numerical/reference,
contract and repeatability checks must pass. These are bounded research screening
criteria, not nominal coverage certification or a real-data confirmation gate.
Power is reported, never the selection criterion. A primary joint replacement
requires a correct joint candidate; conditional success cannot satisfy it.

One final run: ≤8,000,000 resampling draws, ≤900 s, RSS planning cap 1 GiB;
pilot runtime determines feasibility only, not method tuning. Repeat final once
for deterministic scientific bytes (not extra independent R). Keep timing/RSS
outside the scientific hash. Total typical reservation under one hour including
M2 replay, baseline/final tests and reviews; stop/reassess budget overruns.
No global RNG, raw synthetic arrays in Git, scientific data discovery, acquisition
or training. Unique source/config-hash+UUID outputs; existing artifacts immutable.
Record clean commit/source/config, versions, tolerances, platform, seeds, budgets,
counts, elapsed time and checksums; recheck final executed-source/package parity.
Numerical references atol/rtol 1e−12; true-parameter coverage tolerance 1e−12
scaled by max(1,|truth|). Do not let that tolerance fabricate valid zero-variance CIs.

## 7. Implementation tasks and independent checks

- [x] Task 1: `evaluation/inference_research/{contracts,methods}.py` and
  `tests/test_m3_inference.py`. RED absent API; GREEN literal seed t with df=2
  critical value 4.302652729749464, independent HAC Toeplitz quadratic form,
  exact three-day stationary transition enumeration, mismatched/failed ledger,
  degenerate/small/nonfinite/large-offset and deterministic sampling checks.
- [x] Task 2: `evaluation/inference_research/{benchmark,synthetic}.py`,
  `scripts/run_m3_inference.py`, `tests/test_m3_benchmark.py`. RED missing API;
  GREEN frozen config, conditional-null attribution, overlap covariance/truth,
  common data/draw labels, unsupported-method reasons, callback mutation and
  budget/publication/provenance rejection. Reuse M2 rate summaries unchanged.
- [ ] Task 3: Commit executable source, normal install, pilot/development then
  frozen evaluation/repeat. Preserve aggregate evidence under docs, bulk outputs
  ignored. Independent reviewers challenge estimands, units, formulas, Monte
  Carlo, benchmark overfitting and software/provenance. Reproduced severe defects
  require RED→GREEN regressions and final checks.
- [ ] Task 4: Full tests/import/pip/artifact/scope/history/ignore audits;
  `docs/V2_M3_INFERENCE_REMEDIATION_REPORT.md`, tables/figure, explicit selection
  and restricted integration proposal. Commit/push M3 only, verify remote SHA.

## 8. Scope and unresolved risks

IMPLEMENTABLE_NOW: synthetic-only experimental candidates, strict run ledger,
references, controlled comparison, failure diagnosis and scientific reporting.
REQUIRES_PROTOCOL_APPROVAL: official estimand/method, independent run design,
calendar/access/selection/fit policy, multiplicity, real-loss dependence checks,
model-owner integration and any production conditional-for-joint substitution.
OUT_OF_SCOPE: JEPA training/model edits, confirmatory/holdout access, new solar
data, shared V2 decisions, UI, M3.2, protected-branch integration or PR.

No method recovers arbitrary unseen common shocks from one cohort. Short highly
persistent records may contain INSUFFICIENT INDEPENDENT INFORMATION. Overlap
length is not the whole dependence length; heterogeneous fixed folds do not
identify future-period generalization. Symmetric heavy-tail theory is not a
license for arbitrary skewed/infinite-mean losses. Real seed-score distribution,
operational causality, training-data/search uncertainty and effective block
independence remain UNKNOWN. No forced numerical CI or favorable-method selection.

## Execution rulings

The initial literal df=2 critical value was an inaccurate tabulation. Before
benchmark execution, independent 60-digit Decimal inversion of
F(t)=1/2+t/(2 sqrt(t²+2)) gave 4.30265272974946385…, agreeing with SciPy to
2e−15. The literal test/plan were corrected from this mathematical evidence;
no expected simulation value, scientific tolerance or frozen configuration changed.

Before simulations, adversarial regressions reproduced floating-point point
intervals at subnormal and large-offset scales. The candidate returns
INSUFFICIENT_NUMERICAL_RESOLUTION after rescaling rather than publishing them.
Independent review also distinguished the scale-mixture location theorem from
mean inference: the experimental Design now requires explicit finite_mean;
undefined means are unsupported. All frozen DGPs, including t1.5, have finite
means. Neither change modifies frozen scenarios, seeds, budgets or thresholds.

Pilot/development completed at 64629f6 (R5/B99: 1.313 s; R100/B199: 11.940 s).
Before final evaluation, review reproduced two out-of-preset contract issues:
integer assumptions passed JSON validation before later rejection, and tiny
nonzero effects were labeled a zero null. Explicit Boolean checks and exact-null
classification fix them. No candidate settings were tuned from development.
HAC L7 has no eligible development DGP because those periods are shorter than
its 32-day guard; its first eligible Monte Carlo assessment is frozen evaluation.
Fixed lag/block settings have no general growing-bandwidth/block asymptotic
guarantee. These restrictions are retained rather than tuned after development.

Software review reproduced a driver-attestation gap: a stale external copy could
call valid package functions while provenance hashed the checkout driver. The
meaningful CLI logic now lives in captured `inference_research/runner.py`; the
script only supplies its repository root and invokes it. Shared provenance/M1/M2
code is untouched. The exporter also rejects counting one execution as a repeat.
Both fixes precede final evaluation; no scientific settings changed. The earlier
development artifacts remain preserved and are not claimed to have stronger
driver attestation retroactively. This is not an interpreter security sandbox.
