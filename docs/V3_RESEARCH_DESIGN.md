# SolarJEPA V3 research and experimental design

Date: 2026-10-18 (Asia/Kolkata). Status: **proposed research design, not an execution protocol**.

## Decision and scope

Recommend **V3 compact temporal JEPA with a supervised fallback**, testing local
future-block representation prediction first, then a causal fine/coarse context
extension. Preserve joint GOES XRS-A/B inputs, a small width-32 encoder, an EMA
teacher used only in training, and direct ordered quantile forecasts. Pretraining
must earn its additional cost against the same supervised architecture and an
extra-update supervised control. Do not presume that JEPA is the winning recipe.

The immediate next milestone is **V3-M0: exposure-safe contracts, synthetic
diagnostics and resource accounting**. It implements no scientific fitting and
does not release a holdout. Model experiments require a later, separately frozen
protocol and authorization. This document does not authorize acquisition, training,
calibration fitting, inference on scientific observations, V1/V2 changes or integration.

The user's intended outcome is a defensible, affordable experimental programme,
including transition/peak error diagnosis and uncertainty, on a MacBook Air M2
with 8 GB RAM. This milestone delivers research documents and small provenance
records only. Existing audit facilities suffice; a new executable utility would
duplicate functionality before the V3 contracts are reviewed.

Evidence labels throughout: **DOCUMENTED** = authoritative method/instrument
documentation; **OBSERVED** = source or saved-file evidence inspected here;
**INFERRED** = derived interpretation or proposed application; **UNKNOWN** = not
established. All V3 benefits and resource throughput are UNKNOWN. See the
[evidence audit](V3_EVIDENCE_AUDIT.md), [literature](V3_LITERATURE.md) and
[source pins](../data/manifests/v3_research_evidence.json).

## 1. What V1/V2 establish

**OBSERVED:** V1 already has five-minute patches, future latent queries, EMA and
stop-gradient targets, optional contiguous context masking and monotone quantiles.
V2 reuses that backbone, adding dex loss alignment, controlled optimization arms,
compact comparators, canonical evaluation and guarded experimental infrastructure.
These are foundations, not V3 novelty. The inspected V2 readiness evidence records
no real-data pilot execution. No V2 accuracy or M2 training-throughput result is
available from that evidence.

**OBSERVED/INFERRED:** Saved V1 test aggregates show substantially larger errors
on future-defined rising and M+ windows. JEPA's small global advantage over the
supervised control does not persist uniformly within those strata. No saved
stratum establishes event peak timing, peak underprediction, precursor skill or
causes of error. V3 therefore needs a diagnostic protocol before a flare loss.

**OBSERVED:** M3 returned `NO_VALIDATED_REPLACEMENT`; current V2 descriptive
summaries deliberately provide no sampling intervals, p-values or significance.
V3 carries this restriction forward until a separately reviewed inference method
is qualified for its actual estimand. More bootstrap draws or more overlapping
origins do not fix an unidentified independent-sample structure.

## 2. Candidate architecture and alternatives

### A. Recommended first candidate: compact local-target JEPA

- Two jointly encoded channels, one-minute cadence, dimensioned
  `log10(F / (1 W/m²))`; invalid/nonpositive observations remain masked/rejected by
  the declared eligibility rule. Fit center/scale on unique raw training bins only.
- Anchor context C=120 minutes, horizon H=30 minutes, patches of five raw minutes,
  width 32, three encoder layers, four heads, predictor depth two, head width 128.
  Start with the existing five quantiles `{.05,.25,.5,.75,.95}` and float32 CPU.
- A context-only student predicts six future patch embeddings. The candidate EMA
  teacher encodes **each five-minute target block separately**, without attending
  to other future blocks. Reuse teacher weights across blocks; include target lead
  positions. This isolates local temporal content from the existing full-sequence
  teacher, whose target embeddings can depend on the entire training horizon.
  Neither recipe has future inputs at forecast time. This is an objective hypothesis,
  not evidence that the existing training teacher leaks test data.
  Each local block is one patch token, so its teacher attention has no temporal
  mixing across tokens. Lead-position embeddings can also create a shortcut.
  Require training-only content-shuffle/constant-content probes at fixed positions,
  and position-shuffle probes at fixed content; measure representation sensitivity
  and diversity **across origins at each fixed lead**, separately for teacher
  targets and predictions. Pooling across leads could hide a position-only solution.
  Locality trades contextual representations for patch content; it does not
  guarantee a better forecasting target. Low latent loss alone cannot pass E1. Exact
  constant/content-insensitive representations fail the mechanism check; a
  prospective tolerance and nondegeneracy rule must be fixed in M0, without
  choosing it from solar evaluation outcomes.
- Equal mean Smooth-L1 latent loss over future blocks/dimensions; EMA schedule
  `.996 → 1`, stop gradient through teacher. Compare future-only targets first;
  contiguous context masking is a separate ablation with separately normalized
  context and future terms, so changing target count does not silently change loss.
- Use a direct horizon head conditioned on pooled context and predicted future
  latents, with a context-last-value residual anchor in log space. Ordered offsets
  use a base plus positive cumulative increments. **Anchor on/off must also be
  tested in the supervised arm**; it is not a JEPA-specific advantage. The initial
  isolated objective contrast keeps the existing unanchored head fixed.
- Downstream optimization and checkpoint selection use the same unweighted,
  equal-channel/equal-lead/equal-quantile pinball loss in **dex**. Training-space
  normalization must be inverted or explicitly scale-corrected for this loss.
  Report raw and calibrated outputs separately.

### B. Conditional extension: fine/coarse history

Only after A is mechanically sound, compare C=120 against C=360 at H=30. Preserve
the newest 120 minutes as 24 five-minute raw-value patches. Summarize the earlier
240 minutes into 16 nonoverlapping 15-minute blocks; each channel supplies its
mean log flux and last-minus-first log flux, with validity/count information.
Project the coarse view separately, add explicit scale/relative-time embeddings,
and share the compact encoder across the resulting 40 context tokens.

All constituent bins must end by issue time and pass the declared rule. These
summaries are derived modeling features, not new instrument measurements; no
centered smoothing or cross-gap interpolation. Complete-support first keeps
comparison semantics simple. Compare with a single-scale C=360/p=5 control
(72 context tokens) on exactly the same origins. This separates longer history
from aggregation. Coarse summary choices are frozen before outcomes, not searched.

This extension may capture evolving background while preserving recent changes;
that mechanism is **INFERRED**. Whether it helps flare transitions is UNKNOWN.
Five- and ten-minute future representation targets, with equal loss weight per
scale, are a subsequent objective ablation, not bundled with longer context.

### C. Affordable alternative and stop rule

A supervised compact TCN plus a full-context linear quantile model may be a better
cost/accuracy choice. Start with width 32, kernel 3, two convolutions per residual
block, dilations 1/2/4/8/16: receptive field `1+4*(1+2+4+8+16)=125` minutes.
It covers C=120; **it does not cover C=360**. For the long-context contrast, extend
dilations through 64 (RF=509) or declare the comparator limited; do not claim equal
history access with RF=125. The full-context linear model is joint-channel,
regularized and assessed for raw quantile crossing. Preserve each method's
rearrangement policy in both tuning and evaluation.

Do not add codebooks, large pretrained foundation models, generative diffusion,
React/FastAPI, new modalities or SoLEXS fusion in this milestone. The current
scientific/provenance readiness does not justify those costs or semantics.

## 3. Exposure firewall and future data contract

**No new scientific data are read or acquired for this design.** Historical saved
aggregates inform the research question only. They cannot rank V3 configurations,
set thresholds adaptively, calibrate uncertainty or choose a deployment model.

| Period/source | V3 treatment |
|---|---|
| GOES May 1–July 22, 2024, previously training support | Candidate historical development pool only after exposure audit; any newly found evaluation/selection exposure is excluded from V3 tuning |
| GOES July 22–August 1, 2024, V1/V2 validation | Exposed; exclude from V3 selection and calibration |
| GOES August 2024, V1 test | Exposed; historical diagnosis only, no V3 selection/calibration/confirmation |
| GOES January 2025, external evaluation | Exposed; explicitly unavailable as a confirmatory holdout; same prohibition |
| Candidate 2020/2022/2023 periods, other dates | Suitability, prior access and coverage UNKNOWN; no automatic fresh designation or access permission |
| SoLEXS collection | Not a substitute for calibrated GOES flux or a ready multimodal input; exclude until independent scientific gates pass |

Before any V3 experiment, an owner-reviewed inventory must distinguish prior
training, tuning, calibration, tests, EDA, presentations and unrecorded exposure.
Audit all relevant branches/results, including provisional SoLEXS/GOES pilots.
Uncertain exposure fails closed for confirmation. No calendar is nominated as
fresh merely because it is absent from a particular report. Source product,
satellite, version, time semantics, units, flags, coverage and content hashes
must be frozen; file timestamps cannot establish observation or availability time.

For an audited eligible development pool, use three fixed expanding chronological
folds where volume permits, each with distinct train, tune, calibration and
development-evaluation intervals. Declare actual UTC half-open dates **before
opening outcomes**. If support is insufficient, report that blocker and reduce
the claim rather than filling dates or treating cells as independent samples.
The small historical training pool alone does not establish three adequate folds.

The final confirmation interval must be separately acquired/qualified and sealed
after the exposure review; its dates and event support remain UNKNOWN now. Freeze
one chosen recipe and all comparisons before release. A later forward-collected
as-issued series is preferable for operational claims, but is outside this task.
Development-evaluation outcomes may rank V3 candidates only within that new,
explicitly authorized development protocol; the historical exposed evaluations
above remain prohibited. Once a period has been used for selection it is not a
confirmatory period.

Every window's full dependency support includes context, targets, derived-feature
lookback, label maturity, catalog construction, calibration residuals and upstream
processing. Purge overlap at boundaries using that support, not just origin labels;
for C≤360/H≤60 require at least 420 minutes between adjacent partition origin
ranges **plus any additional known dependency**. This mechanical separation is
not a proof of temporal independence or of causal science-product processing.
UNKNOWN upstream support blocks operational claims even with a large embargo.

Pretraining, normalization, training-based quantile residuals and sampling weights
are training-only. Pretraining is repeated within each fold; no SSL checkpoint
trained on a later fold can enter an earlier fold. Do not cache any teacher that
has seen tuning/calibration/evaluation targets. Tuning chooses checkpoints and
hyperparameters; calibration is used only by the predeclared calibration rule,
not to select architecture. Record exclusions and support counts without opening
sealed outcome amplitudes for coverage-driven dataset selection.

## 4. Prioritized hypothesis matrix

These are proposed contrasts, not launched jobs. Run in order; a failed gate stops
promotion. Do not execute a full context × horizon × objective × loss grid.

| Priority / ID | Hypothesis and isolated comparison | Primary readout | Promotion criterion |
|---|---|---|---|
| 0 / G0 | Exposure-safe supports and context-only inference can be enforced | Synthetic boundary, teacher and provenance checks | All mechanical gates in §9; otherwise stop |
| 1 / E1 | Local future-target JEPA helps beyond additional optimization | Existing full-sequence teacher vs local teacher; each paired to S and S-extra | §8 accuracy/resource gate; publish failure/null outcomes |
| 1 / E2 | Useful learned representations, not just head optimization | Frozen JEPA encoder+predictor vs frozen random encoder+predictor; same trainable head | Consistent descriptive skill gain; a diagnostic, not replacement for E1 |
| 2 / E3 | Latest-value anchoring improves transitions | Anchor off/on in J and S, no objective change | §8 guardrails, no JEPA attribution if S gains equally |
| 2 / E4 | Older background context helps beyond recent history | C120 vs C360 single-scale vs C360 fine/coarse; J and S, fixed H30 | §8 gate on common support; extra cost justified |
| 3 / E5 | Temporal scales/objectives matter | Five-minute-only vs equal-weight five/ten-minute local targets; then future-only vs context masking | One change at a time, §8 guardrails; no new backbone |
| 3 / E6 | Collapse safeguards help | EMA alone vs EMA + online variance/covariance penalty | Train-only diversity checks plus §8, not latent loss alone |
| 3 / E7 | Tail focus improves rare high-flux forecasts without unacceptable global cost | Uniform vs fixed quantile-level tail weights; optional separate median increment loss | Transition/peak diagnostics and §8 guardrails |
| 4 / E8 | Calibration helps under shift | Raw vs fixed static CQR; delayed online ACI only as a separate protocol | Coverage and width together; no distribution-free solar guarantee |
| 4 / E9 | H60 remains useful | Fixed C architecture, H30 vs H60; report first30 on shared support and leads31–60 separately | Resource gate and horizon-specific skill vs persistence; no best-horizon claim |

E1 minimal screening cohort: three paired seeds `{17,29,43}`, two separately
trained teacher recipes J-existing/J-local (1,000 SSL + 2,000 downstream updates),
S (2,000 supervised), S-extra (3,000 supervised), and masked-value reconstruction
R (1,000 pretraining + 2,000 downstream). That is **15 fitted recipe outcomes and
42,000 optimizer updates** before frozen probes/classical controls. One update
means effective batch 64, microbatch 16 × accumulation 4; use the same sampled
origins/order when objectives allow. R reconstructs masked training patches and
is discarded after pretraining, then uses the same downstream head. This tests
latent prediction against non-JEPA pretraining. These ceilings are proposals,
not proven adequate optimization or measured feasibility. No adaptive retries.

Use three fixed chronological folds only after data/support and compute gates;
that multiplies the E1 update budget by three. Screening on one eligible fold is
engineering/development evidence only. Promote at most one objective and one
context extension, then repeat with five predeclared paired seeds and all approved
folds if affordable. Sharing SSL across frozen probes is allowed within identical
seed/fold/objective identities; report actual shared cost and full standalone
recipe cost separately. Distinct objectives need distinct SSL jobs.

## 5. Objectives, flare sensitivity and calibration

Keep the unweighted dex pinball primary. For level τ and error `e=y−qτ`,
`ρτ(e)=max(τe,(τ−1)e)`; average equally over fixed quantiles, target channels,
leads and paired origins. Report channel-specific results so XRS-A variability
cannot hide XRS-B degradation. Native-space MAE/RMSE are additional diagnostics.

E7 first uses fixed quantile-level weights
`wτ = 1 + 4*I(τ≥.9)`, normalized to mean one. Positive fixed quantile weights
retain each quantile's target; this emphasizes upper quantiles, not observed
flare frequency. Outcome-weighted pinball, inverse-event sampling without
correction and focal regression can change the target distribution and damage
calibration; do not silently describe those as proper marginal probability
training. A separate median increment auxiliary Smooth-L1 term may be tested at
`λ∈{0,.1}` only after fixing its dex normalization; evaluate bias and tail coverage.
No classification focal loss until a separate flare-event label contract exists.

E6 proposal: retain the stated latent prediction loss and use
`L = Llatent + λ*(Lvariance + Lcovariance)` on online predicted target embeddings.
At each fixed lead, center across distinct training origins, apply the variance
floor across origins for each dimension, and penalize off-diagonal dimension
covariances; average over dimensions/leads after explicit normalization. Fix the
variance-floor scale and finite-batch estimator in M0; no present/future-invariance
term is added. Normalize the variance and covariance penalty terms explicitly;
compare `λ=0` and `.1` for the combined online regularizer only. Measure dimension
standard deviations, covariance spectrum/effective rank and correlation across
distinct training origins, with origin separation disclosed. LayerNorm within
each vector is not an anti-collapse proof. Constant inputs and identical-origin
batches are software stress tests; do not invent a solar rank threshold.

Static CQR uses a disjoint chronological calibration interval: per lead/channel
and central 50%/90% interval, compute nonconformity
`s=max(qlo−y,y−qhi)` and its finite-sample order-statistic correction, with exact
sample count/order rule recorded. Report unadjusted and adjusted intervals; allow
negative corrections only with a predeclared no-inversion rule. Insufficient
support produces UNKNOWN calibration, not borrowed tuning/test residuals.
Treat CQR as **interval-only calibration**, not a replacement ordered five-quantile
forecast; do not insert its endpoints into primary pinball scoring. If publishing
both intervals together, freeze the nesting rule: retain the adjusted 50% interval
and expand the adjusted 90% endpoints as needed to contain it. Measure coverage,
width and interval score after this deterministic rule, and record each expansion.
Coherent full-quantile recalibration would be a separate method.
Exchangeability of solar residuals is not established, so classical CQR coverage
theorems do not become a solar guarantee. Avoid flare-conditioned calibration
until independent event counts justify a separate protocol.

Online ACI is secondary only: issue first, update solely with residuals whose
full target horizon has matured by the next issue. Freeze update rate and policy
using eligible development data; do not replay test targets early or select a
rate from final outcomes. Its long-run coverage objective is not flare-conditional
or simultaneous trajectory validity. Model and preprocessing stay frozen.

## 6. Diagnostics for transitions and peaks

Use context-observable and retrospective strata separately. Context strata may
use fixed past log-slope/variability bins (edges fitted on training only).
Retrospective strata may use XRS-B future max ≥2×last context and flux thresholds
C1/M1/X1. NOAA defines class from peak 0.1–0.8 nm flux; a threshold crossing is
not itself a catalogued event. Missingness is never a quiet or negative label.

Before peak claims, freeze an authoritative catalog/version and an event/window
association rule, including overlapping events, boundaries, gaps and repeated
origins. Proposed report: one fixed issue at 10 minutes before catalog peak for
events with fully observed ±required support (explicitly retrospective, not an
operational trigger), with a second context-only-triggered cohort if separately
approved. At fixed H30, report:

- XRS-B median-path peak amplitude error `max_h(q.5,h) − max_h(yh)` in dex;
  native relative/absolute errors with valid nonzero denominators; signed bias
  and underprediction fraction, not only absolute error.
- Peak timing error `argmax_h(q.5,h) − argmax_h(yh)` in minutes, earliest tie rule,
  observed-vs-predicted maximum at horizon boundaries flagged/censored separately.
- Per-lead errors and interval coverage before/during/after a catalog peak;
  report onset-before-issue versus onset-after-issue cohorts separately.
- Median increment/derivative error, rise/decay bias and false high-flux forecasts
  on all eligible background windows, not only event-centered examples.

`max` of marginal medians is a deterministic path diagnostic, **not** a median
or quantile of the random peak. Marginal quantiles provide neither probability
of any flare within H nor simultaneous path bands. Brier score, reliability and
PR-AUC for “any M+ in H” require a separately trained/predeclared event-probability
head or joint forecast distribution; do not derive them from five marginal
quantiles. If added later, include climatology, prevalence, TSS/HSS at a
development-frozen threshold and event-level deduplication. No such head is
recommended for the first V3 experiment.

## 7. Fair comparisons and statistical reporting

Minimum roster: persistence; train-only empirical residual quantile persistence;
train-only drift/trailing mean; AR(1); direct ridge; full-context quantile linear;
one compact supervised TCN; identical-architecture S and S-extra; J and R.
ARIMA order grid `{(1,1,0),(1,1,1),(2,1,0),(2,1,1)}` and AR/GARCH/GJR with normal/t
innovations are secondary classical references, contingent on fit qualification.

All receive the same declared source product, usable context, forecast origins,
channels, lead grid, training chronology and calibration access. Fit statistical
parameters on training only; updating state using observations already available
at issue is allowed under a frozen rule and is not parameter refitting. If rolling
refits are permitted, specify their schedule and give all families equivalent
data availability; report compute separately. Use the same validation dex score
for probabilistic hyperparameter/checkpoint selection; disclose the different
search counts. Point-only models use development dex MAE for their point-only
choices and enter point metrics only; no invented pinball for a point.

Before AR/GARCH claims, V3 must reject nonconverged/nonfinite fits, validate
parameter admissibility/stability and forecast finiteness, record all starts,
and specify failure handling before evaluation. Current finite-likelihood-only
selection is insufficient. Do not edit the historical fitter in this milestone.
Failures remain visible: no model-dependent dropping of hard origins, best-start
cherry-picking on evaluation or silent substitution of a weaker baseline.

For promotion, average cells/quantiles equally within each origin, origins equally
within each fold, then the **planned seeds equally and the fixed folds equally**.
Use individual fitted-run losses, not ensemble predictions. Keep all planned arms,
seeds and folds in the completeness check; an unfinished/failed cohort cannot be
rescored as a smaller successful experiment. Also show pooled-cell and individual
fold results descriptively, with their different weighting made explicit.
Require complete finite predictions from **every planned fit** for each promotion
contrast. One unresolved fit/resource stop makes its promotion mean unavailable;
four successful seeds plus one failed seed cannot satisfy the 4/5 rule.
Successful-pair descriptions can still be published, explicitly incomplete and
ineligible for promotion. Classical references use the identical origin/fold
reduction; deterministic reference scores are reused in paired seed contrasts,
not treated as independent repeated fits.

Report skill `1 − loss_model/loss_reference` on exact common support (UNKNOWN for
zero reference loss), raw differences, per-seed/per-fold results, seed SD, daily
loss traces and leave-one-seed/fold-out descriptions. Mean per-seed losses are a
different estimand from losses of ensemble predictions; never interchange them.
Paired seeds reduce some variation but do not establish independent solar samples.
Origins/channels/leads overlap; do not use iid-cell intervals or ordinary binomial
coverage error bars. No p-values, confidence claims or multiplicity-adjusted
significance until a separate inference qualification covers dependence, seed
cohort effects, rare events and selection. Predeclare one primary J-vs-S-extra
contrast; remaining contrasts are secondary. Published V1 intervals stay historical
and do not supply a validated V3 test.

## 8. Acceptance criteria and stopping decisions

The following **design targets** are chosen for prospective development screening,
not estimates of detectable effect, confidence levels or scientifically justified
equivalence margins. Freeze them with the future data protocol before outcomes.

1. **Mechanical:** all §9 tests pass; zero sealed/exposed-selection access; identical
   paired support and provenance. Any violation invalidates that experiment.
2. **Resource:** one worker; sampled worker RSS <2 GiB, process tree <3 GiB; no
   sustained macOS memory-pressure warning or >256 MiB swap growth from baseline.
   Stop on violation; sampling can miss peaks and cannot provide an OS hard cap.
3. **Global accuracy:** candidate's **raw, uncalibrated** mean unweighted dex pinball improves by ≥2%
   versus both S and S-extra, and is no worse than the development-selected
   probabilistic persistence/linear reference. Require the improvement direction
   in each approved fold and at least 4/5 paired seeds for promotion, not just an
   average driven by one seed. Three-seed screening can only warrant replication.
4. **Activity guardrails:** rising/M+ log-MAE and pinball do not degrade by >2%
   versus S; aim for ≥5% improvement in XRS-B peak-amplitude MAE and absolute
   rise/decay bias versus S. A relative error on a zero denominator is UNKNOWN.
   Report counts and all counterexamples. <30 distinct supported M+ events or
   <10 X events means event-specific acceptance is **insufficient evidence**;
   these counts are reporting floors, not statistical power/independence claims.
5. **Calibration:** empirical 90% coverage within [.87,.93] and 50% within
   [.45,.55] **for each channel** (and pooled), width inflation ≤20% relative to
   that same recipe's raw intervals, and no >3 percentage point degradation in
   supported M+ coverage relative to S under a matched policy. Compare raw with
   raw and CQR with CQR fitted on the same disjoint calibration interval for each
   model; never choose a favorable policy after outcomes. The predeclared CQR
   interval-only outputs must satisfy these coverage/width gates for promotion;
   raw interval performance remains mandatory disclosure. Report interval scores
   as well as coverage/width, every channel/lead/regime, and sparse support as
   unavailable. These are engineering tolerances, not coverage guarantees; low
   event support blocks a flare-calibration claim. Calibrated interval scores are secondary
   and cannot rescue the raw accuracy gate.
6. **Value for cost:** disclose total pretraining+downstream+search+calibration
   time, updates, sampled RSS and failures. A JEPA standalone recipe taking >2×
   S-extra wall time needs a separately justified scientific benefit; otherwise
   prefer the strongest affordable supervised recipe. No claim of equal FLOPs,
   energy or wall time from matching update counts.

If JEPA fails, publish the result and recommend S/TCN/linear according to the
frozen development ranking. A design recommendation is not a deployment decision.
Only a final locked, fresh evaluation can support a later out-of-period claim;
without qualified inference report conditional observed performance only.

## 9. MacBook Air M2 feasibility and next milestone

**OBSERVED here:** `sysctl` reports Mac14,2 / Apple M2 / 8,589,934,592 bytes RAM.
V1's saved provenance records this model/8 GiB host; V1 training runtimes are
historical recipe costs, not V3 benchmarks. The inspected M4/16-GiB V2 timings
and extrapolations are not measurements on this M2. V3 throughput, sustained
thermal performance, MPS correctness and achievable completion time are UNKNOWN.

Analytic float32 estimates, excluding allocator/runtime/OS/workspace overhead:

| Item | Calculation / estimate | Interpretation |
|---|---|---|
| Existing full trainable model | 136,332 parameters; EMA encoder 39,808 | Source arithmetic; existing V1 architecture |
| Proposed V3 parameter ceiling | ≤250,000 trainable | Design budget, exact count verified in M0 |
| Parameters + gradients + Adam moments at ceiling | `16*250000` = 3.81 MiB, plus teacher weights | Excludes optimizer overhead/copies/activations |
| One attention matrix, B16/4 heads, N30 | `16*4*30²*4` = .220 MiB per layer | C120+H30 patch tokens |
| Same matrix, fine/coarse N46 | .517 MiB per layer | 40 context + 6 target tokens |
| Same matrix, long single-scale N78 | 1.485 MiB per layer | 72 context + 6 target tokens; 6.76× N30 |
| 20k materialized windows, C360/H60/two channels | `20000*420*2*4` = 64.1 MiB values + 16.0 MiB boolean masks | Plus targets, indices and copies; streaming preferred |

Small weights do not bound peak RSS: attention backward, EMA forward, Python,
Torch, preparation, serialization and other apps matter. Use lazy window indices,
microbatch16/accumulation4, one process, no data-loader subprocesses, CPU/float32
first, and one fixed thread policy. Separate MPS qualification may follow; no
silent device fallback or mixed-precision change within a contrast.

**Scheduling estimates are ceilings/formulas, not observed durations.** Later,
after explicit experiment authorization, a 100-update disposable feasibility
profile must measure preparation, warmup and sustained update times and sampled
memory on the actual host. Predict each job as `setup + SSL_updates*tSSL +
downstream_updates*tDS + validation + sealing`, conservatively using sustained
p90 and disclosing uncertainty. The E1 42k-update total takes 70 minutes at an
assumed .1 s/update or 5 h 50 min at .5 s/update, before overhead; these are
sensitivity scenarios, not M2 estimates. A proposed two-hour session budget
cannot guarantee completion. Hard stop after the budget, no retries or post-hoc
seed dropping; defer the remaining fixed jobs to a separately approved reservation.
Reserve ≥5 GiB scratch plus measured immutable input size; check free storage
before launch and each job. Stream forecasts to ignored artifacts rather than
building large JSON bundles in memory. Persist hashes and compact summaries.

### V3-M0 deliverables (next implementation milestone)

Create only after its scope/design is approved; do not create its branch now.

1. Resolve source reuse deliberately: current main lacks the V1/V2 model modules.
   Pin the audited implementations and propose the minimal compatible import/copy
   or integration approach; no implicit merging of whole milestone branches.
2. Add UI-independent V3 exposure/support contracts, prospective config validation
   and pure resource arithmetic. Fail closed on UNKNOWN exposure for selection,
   disallowed periods, unsatisfied support/availability and mismatched identities.
3. Add synthetic-only tests for full-support purges; train-only scaling/SSL;
   coarse-bin causality and support; local teacher target isolation/stop-gradient;
   context-only forecasts; head shape/quantile ordering; raw-vs-dex loss invariance;
   classical convergence acceptance; calibration maturity/no inversion; peak
   amplitude/timing tie/censoring semantics; exact paired-support failure handling.
4. Count parameters/attention/state allocations without scientific fitting.
   Exercise resource-stop/atomic-output logic with synthetic process fixtures,
   including cancellation, no retries and accounting for shared SSL. Synthetic
   tensors and forward-only software tests are not solar performance evidence.
5. Obtain independent software and scientific review; record passes/failures and
   unresolved data/inference questions. Publish only that milestone branch.

M0 acceptance: all specified software invariants pass, zero scientific fit calls,
zero evaluation-data decoding, no V1/V2 edits, exact dependency/source pins and
a reviewed future data-access protocol. M0 does not include the later 100-update
profile, a training run, holdout release, model selection or a PR/merge.
