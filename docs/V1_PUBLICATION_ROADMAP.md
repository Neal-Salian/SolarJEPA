# SolarJEPA V1 publication roadmap and recommended V2 direction

Date: 2026-10-10 (Asia/Kolkata). Based on the independent audit of v1 at 3dbd67abad753c086dec51d0f8cf3b6382bfd10b. This is a research proposal, not authorization to implement V2 or alter V1 results/configurations. See [V1_SCIENTIFIC_AUDIT.md](V1_SCIENTIFIC_AUDIT.md) for source evidence, numerical checks and finding IDs.

## Publication target and minimum evidence

**Current verdict: NOT_READY.** The defensible starting question is: does a lightweight JEPA pretraining stage improve direct probabilistic GOES X-ray flux forecasts beyond a matched supervised architecture, across training seeds and separated solar-activity periods? Treat continuous flux prediction as the primary task. A flare-onset warning claim needs its own catalog-based causal evaluation; an Aditya-L1, physics-informed or generative claim is outside current evidence.

The recommended minimum evidence package for this proposed publication claim is R01–R07 below, scaled to the claim rather than a universal venue requirement. It comprises a frozen protocol, robust classical acceptance, additional paired seeds and targeted controls, multiple time regimes, two stronger inexpensive comparators, calibrated/disaggregated evaluation and an independently reproducible artifact package. No positive JEPA result is an acceptance requirement. If gains vanish, report a reproducible negative/conditional application study and reconsider the publication contribution rather than tune against August.

P0 are scientific-design/validity gates before new confirmatory runs. P1 are essential publication-strengthening studies. P2 are useful scope extensions after the core question is resolved. P3 are optional research paths. Computational estimates below are planning estimates, not executed benchmarks or guarantees.

## R01 — P0: Freeze a publication protocol and data/quality card

**Motivation and evidence:** F01/F02/F05/F06/F09/F10. The current primary-looking result is a supplementary three-fitted-seed average; selection uses normalized pinball while reporting uses equal-channel dex; August has been repeatedly inspected. Support/quality eligibility excludes 52 of 1,488 test candidates: four boundary-support and 48 unique quality exclusions.

**Proposed verification:** Before new modeling, specify the scientific target, primary contrast, target/channel/lead weights, seed/time estimand, calibration metrics, secondary multiplicity family, exclusion/missingness policy, and train/validation/test chronology. Align checkpoint and classical selection with the chosen metric, or explicitly justify different objectives. Mark August 2024 exploratory/spent for future design. Document valid measurement counts, flag semantics, sample support and archive-vs-operational availability.

**Deliverable:** Versioned protocol, data/quality card, new held-out-period access ledger and a reproducible analysis specification.

**Acceptance criteria:** An independent reader can identify exactly one primary claim/estimand and why its weights matter; all future preprocessing and selection use training/validation only; test access and all deviations are recorded. Verify and record new data identities, native units/time/flag schemas, measured coverage, gaps, validity counts and exclusions. Existing V1 reports/configs remain preserved. No invented latency or quality cutoff.

**Estimated compute:** Minutes for data-card/statistical checks; researcher effort dominates. **Additional data:** Not for design; fresh held-out periods are required by R04. **Before V2:** Yes, before implementing or selecting any V2 model and before new test inspection. **Owners:** Contributor A leads protocol/data; B reviews optimization/metric feasibility.

## R02 — P0: Classical optimization and fit-acceptance protocol

**Motivation and evidence:** F04. Two selected XRS-A GARCH fits have convergence flag 8 despite converged starts. Best GJR is nearly on a stationarity boundary; its finite-horizon forecasts are not shown invalid.

**Proposed experiment:** On training/validation only, require declared convergence and numerical constraint tolerances, retain every optimizer outcome, compare accepted converged starts and diagnose residuals/gap handling. Evaluate a segmented-gap treatment or document the approximation. Fix the policy before fresh tests. Check simulation stability with several fixed simulation seeds/path counts as a cheap sensitivity; do not optimize simulation seed on test.

**Deliverable:** Fit-acceptance specification and table of flags, likelihoods, positivity/stationarity slacks, residual diagnostics and simulation variability. Preserve failed fits as results rather than silently replacing V1 artifacts.

**Acceptance criteria:** Every reported accepted baseline meets the declared rule; otherwise label the failure and refrain from blanket family superiority. Show whether conclusions survive reasonable accepted-fit/simulation choices. No requirement to prove long-run stationarity for a deliberately nonstationary finite-horizon specification, but the claim and constraints must agree.

**Estimated compute:** Approximately 3–10 CPU minutes for targeted V1-sized classical refits and prediction sensitivities, extrapolating from observed fits of 2.1–5.0 seconds/model and test prediction/scoring of 8.8–12.0 seconds/model. Longer histories or harder optimizers may require hours; profile one channel/month first. **Additional data:** None for diagnosis; fresh periods needed for reportable comparisons. **Before V2:** Design/acceptance rule yes; future-protocol fitting follows authorization. **Owners:** A leads statistical fit review; B verifies common evaluation interfaces.

## R03 — P1: Paired seeds and minimal pretraining controls

**Motivation and evidence:** F01/F03. Seed43 drives the mean gain; dropping it reverses pinball. JEPA adds 632 pretraining updates. The frozen model loses to supervised; there is no random-frozen reference.

**Proposed experiment:** Use a prespecified set of at least 10 paired seeds as a practical first stage, not a power guarantee. Run the existing fine-tuned recipe and architecture-matched supervised arm on identical new train/validation protocols. Add a supervised optimization-budget control with comparable total updates. To retain a representation-transfer claim, include a frozen-random encoder/predictor plus the same trained head and the existing frozen-JEPA arm; these are useful low-cost diagnostics but not essential to a narrower forecasting-recipe comparison. If an objective-specific novelty claim remains important, add one equally budgeted masked-reconstruction pretext; do not launch a broad pretext sweep initially.

**Deliverable:** Paired per-seed/per-period predictions, training step/wall-time accounting, learning curves and an ablation table with seed/time-aware uncertainty. Distinguish equal downstream budget from equal total optimization budget; document which comparisons answer each question.

**Acceptance criteria:** Quantify seed variation and effect uncertainty relative to a prespecified meaningful margin; show whether one seed dominates and whether gain survives reasonable controls. Ten seeds do not automatically establish power. A null/negative outcome is acceptable if precise and honestly reported; expand seeds only under a predetermined precision rule and compute ceiling. No test-driven stopping to obtain significance.

**Estimated compute:** Current recorded neural training wall times were roughly 55–131 seconds each on Mac14,2/8 GiB, CPU4; all nine totaled 13.83 minutes. At the same cap/model size, about 1–3 CPU hours for 10-seed multi-arm screening on one protocol, then scale only the surviving scientific comparison. These are extrapolations; longer data or slower monitoring can change costs. **Additional data:** Not for exploratory control screening; yes for final confirmation through R04. **Before V2:** Agree design first; execute as the first authorized V2 research block, before architecture scaling. **Owners:** B leads training/controls; A independently checks estimand and paired analysis.

## R04 — P1: Temporal generalization before scaling

**Motivation and evidence:** F02/F10. One August test month cannot establish stability across activity levels, and quiet-stratum support is zero.

**Proposed experiment:** Select at least three separated chronological outer test blocks spanning lower and higher activity, with training/validation preceding each test and no shared target support. Prefer longer blocks and more independent solar regimes over a large random split. Select blocks from external calendar/activity criteria before inspecting model scores. Include at least one newly acquired, genuinely uninspected period. Do not choose dates because they improve JEPA. Keep preprocessing, selection budgets and analysis frozen. Lower-activity coverage must be demonstrated, not assumed from a month name.

**Deliverable:** A temporal-generalization matrix, per-block quality/event supports, common-origin predictions and period-level uncertainty/influence analysis. Retain August as a clearly marked historical pilot, not a new confirmatory fold.

**Acceptance criteria:** Report every prespecified block, failures and negative transfer; quantify both seed and temporal variation; ensure nonzero support for claimed activity regimes. Three blocks are a minimum diversity check, not cycle-wide representativeness or a statistical power guarantee. If the contribution remains narrow, state that scope.

**Estimated compute:** Additional GOES months are roughly 9 MB/month in this pinned V1 selection, before version differences. With the 20,000-window cap, small neural training remains laptop-friendly; classical fitting can dominate. Pilot one fold, then allow several CPU hours for minimum multi-fold runs and budget separately for R03. **Additional data:** Yes, pinned GOES periods; no need to acquire all 2017–2025 data initially. **Before V2:** Choose/freeze the held-out periods before model development; execute within authorized V2. **Owners:** A leads acquisition/chronology; B executes frozen models.

## R05 — P1: Two high-value stronger comparators

**Motivation and evidence:** F08. Ridge is a short-lag point baseline with fewer training windows; classical models are univariate. Most neural/classical gain is already produced by the supervised control.

**Proposed experiment:** Add (1) a full-120-minute, two-channel quantile-linear or regularized quantile-MLP comparator, and (2) one small quantile TCN or PatchTST-style temporal backbone. Choose one temporal family initially, not a full LSTM/TCN/Transformer/foundation-model sweep. Match training-window support, outputs, quality masks, selection metric and bounded validation budget; report parameter count, updates and wall time. A small multivariate VAR/difference model is a useful cheap sensitivity if the multichannel-information issue remains unresolved.

**Deliverable:** A comparator fairness matrix and common-origin loss/calibration table on R04 periods.

**Acceptance criteria:** No model receives held-out fitting information; stronger alternatives have a reasonable prespecified validation budget and the same forecast task. Report budget/capacity differences rather than claim perfect equality. Limit superiority claims to models actually evaluated.

**Estimated compute:** Quantile-linear/MLP or VAR: minutes to tens of minutes per fold depending on solver/features. Small TCN/patch model: tens of minutes to a few hours for seeds/folds on CPU; benchmark one seed first. No foundation model or GPU is a minimum requirement. **Additional data:** Same R04 data. **Before V2:** Specify during design; implement only after authorization, before broad novelty/performance claims. **Owners:** B leads comparators; A audits selection and data access.

## R06 — P1: Calibration, difficult cases and scientific utility

**Motivation and evidence:** F07/F09. Overall coverage hides channel deviations; achieved rising-target coverage is 63.22%; pretraining has no demonstrated M+ advantage. Complete accepted minute averages have variable sample support.

**Proposed experiment:** From fixed V1 predictions first, report channel/lead reliability, interval score/sharpness, influence and contributing-sample-count/missingness strata as exploratory diagnostics; use physical exposure terminology only where instrument documentation establishes it. For new runs, fit any calibration adjustment on validation only and evaluate once on fresh periods. If claiming flare warnings, obtain an authoritative event catalog, distinguish pre-onset issues from ongoing/post-peak continuation, and evaluate alert lead time, false alarms and event-level performance with a declared matching rule. Do not infer event probabilities or exact CRPS from five quantiles, or demand nominal marginal coverage in strata defined by realized future values. Use physically justified quality sensitivities and disclose changes in population.

**Deliverable:** Reliability/interval-score tables, activity/quality support counts and, where claimed, a catalog provenance/event matching card and event-level uncertainty. Prespecify a meaningful practical improvement margin or explicitly report that operational utility is unestablished.

**Acceptance criteria:** Every calibrated result uses validation-only fitting; uncertainty estimates for channel/lead evaluation metrics account for temporal dependence and follow R01's seed estimand and multiplicity plan; negative extremes are retained. Any warning claim has nontrivial pre-onset support and reports false alarms, not only loss on already active flux. Without an event study, title/claims remain continuous flux forecasting. No arbitrary new observation/flag semantics.

**Estimated compute:** Minutes for saved-prediction diagnostics/calibration; hours of scientific catalog/QC work and inexpensive evaluation, with no extra retraining initially. **Additional data:** Event catalog only if warning/onset claims are retained; raw count/flag variables already exist. New forecast confirmation uses R04 periods. **Before V2:** Define utility/events during protocol design; cheap V1 diagnostics are already partly supplied by the audit; execute prospective calibration/event work in authorized V2. **Owners:** A leads event/quality/statistics; B validates causal inputs and calibrated output interfaces.

## R07 — P1: Reproduction package and one independent training repeat

**Motivation and evidence:** F11. Nine saved predictions replay, but training was not replicated and the run envelope omits some dependency identities.

**Proposed verification:** Archive lockfile hashes, full package inventory, source/config/data manifests, checkpoint/NPZ hashes and analysis scripts in a versioned publication artifact store with appropriate data licensing. Keep bulk data/checkpoints out of Git. Have the other contributor reproduce metrics and saved CPU inference in a fresh environment, then repeat one preregistered small training seed/protocol from scratch without retuning. Record OS/hardware and acceptable numerical tolerance in advance.

**Deliverable:** Runnable reproduction instructions, an artifact index and an independent reproduction report that separates inference, training and conclusions.

**Acceptance criteria:** A clean environment can locate/verify dependencies and all required artifacts, recompute principal tables, and reproduce the designated training run within declared tolerance or document the discrepancy. Exact cross-platform bitwise training is not assumed. M4 reproduction is required only for an M4-specific claim; MPS is optional and must not silently replace CPU4.

**Estimated compute:** Minutes for hashes/score replay, minutes to tens of minutes for checkpoint inference and one small neural training repeat, plus installation/data-transfer time. Full classical refitting may take longer and should be separately budgeted. **Additional data:** No new scientific period solely for reproducibility; needs access to the pinned bytes/artifact store. **Before V2:** Design archive/replay requirements now; complete before submission and after the final authorized protocol freezes. **Owners:** A and B reproduce each other's result without sharing unpublished tuning decisions.

## R08 — P2: Horizon and second-satellite extension

**Motivation and evidence:** F02/F07/F12. JEPA loses to GJR at short leads despite overall gain; cross-satellite transfer is unmeasured.

**Proposed experiment:** First disaggregate existing 1/5/15/30-minute leads with clear multiplicity labels. Only after R01–R07 clarify the core result, add a small prespecified horizon comparison or one second-GOES transfer test with documented calibration/bandpass and overlap handling. Do not automatically test every horizon and satellite.

**Deliverable:** Horizon-specific skill/utility and, if pursued, a sensor-transfer data card and evaluation.

**Acceptance criteria:** Define which horizon/domain claim matters; use fresh tests and common supports. No unsupported calibration equivalence across instruments; every negative result retained.

**Estimated compute:** Minutes for existing-lead analysis; roughly proportional to additional runs for new horizons (hours rather than mandatory large GPU training). **Additional data:** Yes for satellite transfer; not for existing leads. **Before V2:** Not a prerequisite to start V2; only required before claims extending beyond its tested scope. **Owners:** A designs scientific target/transfer; B implements bounded runs after authorization.

## R09 — P3: Gated physics, generation and SoLEXS research

**Motivation and evidence:** F12. These are project ambitions, not implemented V1 capabilities. Distinct instrument semantics cannot be inferred from GOES performance.

**Proposed research:** Select one hypothesis only after the empirical benchmark is credible: an explicitly justified physical constraint, a stochastic joint-trajectory decoder, or SoLEXS transfer after timing/calibration/quality gates clear. Use ablations and independent physical/instrument evidence. Do not begin with speculative loss terms or count-to-flare-class conversion.

**Deliverable:** A separate scientific design with a validated physical/instrument contract, baseline, evaluation metric and feasibility budget.

**Acceptance criteria:** Physics has a documented measurable constraint and a valid ablation; generation demonstrates stochastic trajectories with appropriate joint/distributional evaluation; SoLEXS has approved time/exposure/calibration/response semantics before model claims. No assumed conversion between SoLEXS counts and GOES classes.

**Estimated compute:** UNKNOWN until hypothesis/data contracts are established; begin with small offline feasibility checks. A large generative model or multi-year pretraining is not an automatic next step. **Additional data:** Potentially calibrated SoLEXS and external physical measurements; depends on the chosen hypothesis. **Before V2:** No; it should not block the minimal GOES-first V2 empirical program or be represented as completed. **Owners:** A leads instrument/physics authority; B evaluates modeling feasibility only after gates clear.

## Compute-conscious execution order and stopping rules

1. Complete R01 and R02 design checks; organize a publication artifact index. No training is needed to decide the estimand, identify optimizer failures or accept the negative seed result.
2. Pilot one new temporal fold, two paired seeds and the cheap full-context comparator. Use training/validation only for sizing and feasibility decisions; keep outer test outcomes uninspected until the protocol and analysis are frozen. Measure actual RAM and wall time. Preserve CPU4 as the reference; do not allocate large jobs from optimistic estimates.
3. Run the prespecified paired-seed/control experiment on that fold, then the minimum separated periods. Reuse immutable pretrained checkpoints for frozen/head comparisons where identities and protocol permit; do not fit twice merely for convenience.
4. Add the one selected temporal comparator and calibrate using validation only. Analyze all declared outcomes, including failures; do not keep extending training until JEPA wins.
5. Complete independent replay/training reproduction, then assess whether a robust positive, conditional or negative contribution is publishable. R08/R09 are gated expansions, not default work.

Observed V1 context: all nine recorded neural training wall times totaled 829.67 seconds; the strict comparison's saved interval was 18.44 minutes on Mac14,2/8 GiB. These measurements include the actual capped protocol and are not performance guarantees for longer data, new algorithms, parallel jobs or another laptop. On an 8 GiB host, serialize training and memory-heavy classical fits; leave memory for loading arrays. Kaggle/GPU work is optional after the local scientific screening succeeds. A large pretrained model may have unknowable data overlap and would need its own contamination audit.

Use fixed compute ceilings and precision/coverage requirements chosen before tests. If additional seeds/time regimes leave JEPA's effect unstable, stop scaling and report that. Do not select a favorite seed, test period, horizon, quality threshold or pretext using August results.

## Suggested two-contributor division

| Work | Contributor A: data/statistics/scientific validity | Contributor B: ML/experiment engineering |
|---|---|---|
| Before experiments | Freeze chronology, instrument/QC/event definitions, primary estimand and uncertainty plan | Verify causal pipeline, objective alignment, budgets, seeds and comparator feasibility |
| Execution | Pinned GOES periods, classical acceptance/diagnostics, catalog provenance | JEPA/supervised/budget controls, frozen-random, chosen quantile comparators, artifact capture |
| Independent review | Recompute B's predictions/scores; inspect test access and inference scope | Reproduce A's masks/splits and baseline simulations; inspect fit acceptance and comparisons |
| Writing | Scientific motivation, limitations, literature and statistical interpretation | Architecture, objective, training resources and reproduction instructions |
| Final decision | Jointly approve claim scope based on all prespecified outcomes | Jointly preserve/report negative results and confirm publication artifact completeness |

Keep ownership explicit but reviews crossed. Neither contributor should accept the other's scientific conclusion merely because the pipeline runs. A static reference to the tested commit and immutable result bundles avoids accidental history rewriting.

## Recommended V2 direction and submission gate

Recommended V2 is a **GOES-first, controlled probabilistic temporal-generalization study**: align selection and evaluation, strengthen the matched supervised comparisons, quantify seed/period uncertainty, and separate flux continuation from genuine onset warnings where claimed. Prioritize resolving the incremental value of JEPA over broad model scaling or unvalidated instrument fusion.

For the proposed application paper, this audit recommends completing R01–R07 deliverables, independently checked tables/citations/artifact identities, honest treatment of all negative cases, and a contribution statement distinguishable from existing temporal JEPA and solar X-ray forecasting papers. A statistically significant but tiny average alone is insufficient; report effect size/uncertainty and the chosen scientific/practical relevance standard. If only a bounded pilot remains, submit or share it as that, without claiming methodological or operational breakthroughs.

No V2 implementation, model/configuration change, PR, merge or main integration is authorized or performed by this roadmap. New work requires the user's separate milestone authorization.
