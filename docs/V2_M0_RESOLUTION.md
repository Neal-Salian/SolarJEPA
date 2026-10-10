# V2 M0 evidence audit and decision register

Date: 2026-10-10 (Asia/Kolkata). This completes the **documentation** scope of
M0 requested in this milestone; it does not approve the proposed research study.
The earlier [experimental protocol](V2_EXPERIMENTAL_PROTOCOL.md),
[execution plan](V2_RESEARCH_EXECUTION_PLAN.md), [publication strategy](V2_PUBLICATION_STRATEGY.md)
and [coordination plan](V2_INDEPENDENT_WORK_PLAN.md) remain historical proposals.
This supplement resolves their relationship to subsequent presentation exposure
and defines the currently authorized, model-independent M1 scope.

## Repository and implementation audit

**OBSERVED:** Starting checkout was `presentation/eda-model-comparison`, commit
`660f469683557a0f3134f72ec69b174a5bcdd917`, tracking the identical origin ref.
`git fetch --all --prune` succeeded. Local/main and origin/main both pointed to
`1a4991d`; their left/right divergence count was 0/0. There was no main worktree
and no tracked checkout change. Existing untracked `.agents/` and
`docs/P1_FINAL_INTEGRATION_REAUDIT.md` were preserved in the original checkout.

**OBSERVED:** V2 checkpoint `90571df` and presentation `660f469` are siblings
whose parent is V1 `644648f7d555fcbcb3eed4495d37fecffdd1863a`.
V2 adds four documents only: no implementation, tests or experiment configs.
No M0/M1 branch or worktree existed in the initial branch/worktree inventory.
Other worktrees were GOES external validation (`f309921`), Phase E SoLEXS
(`83b5443`) and provisional SoLEXS numerical modeling (`3baad2b`).
They were audited read-only; none was switched, merged or edited.

**OBSERVED:** The new managed worktree is based on `origin/research/v2-independent-validation`
and uses `feat/v2-m0-m1-validation-foundation`. Its upstream was published before
milestone edits. This follows the task-specific instruction to use the V2
checkpoint rather than the older main. Presentation evidence was read at its
separate pinned ref; presentation code/assets were not copied or merged.

| Stage | Executable evidence inspected | Established state |
|---|---|---|
| P1 | `forecasting/{contracts,splitting,windows,baselines}.py`, `evaluation/{trajectory,events}.py`, `experiments/{runner,provenance}.py`, associated tests | Implemented immutable canonical contracts, partition-local causal support, baseline scoring, manifests and executed-source provenance; do not rebuild |
| P2 | `data/{foundation,goes,goes_acquisition,solexs_exploration}.py`, `training/{normalization,core,runner}.py`, P2 tests/configs/manifests | Implemented historical GOES adapter, train-only normalization and bounded synthetic training foundation; scientifically usable SoLEXS forecasting remains gated |
| V1 | `training/jepa.py`, `forecasting/statistical.py`, `experiments/v1.py`, `evaluation/probabilistic.py`, V1 tests/configs; presentation tracked replay records | Implemented JEPA/supervised/classical comparison. Existing numerical results are historical records, not new experiments in this milestone |
| V2 | `git diff 644648f..90571df` and four V2 documents | Proposed protocol only before this branch; model-independent M1 is the current implementation authorization |

Three independent read-only subagents audited scientific/statistical methodology,
data/provenance, and architecture. No auditor read raw/processed scientific data
or ignored result arrays. Current executable test outcomes belong in the
[M1 verification report](V2_M1_VERIFICATION.md); historical test counts are not
presented as current execution evidence.

## Exposure ledger and holdout assessment

Bounds below are UTC half-open. **OBSERVED** source/configuration evidence
establishes software inputs and tracked reports; it cannot establish every
human decision or private access. **UNKNOWN** is not equivalent to untouched.

| Period/source | Training exposure | Validation/selection exposure | Test exposure | Exploratory inspection and decision influence |
|---|---|---|---|---|
| GOES July 1–4 2024 | P1 July 1–2 | P1 July 2–3 | P1 July 3–4 | Reference processing/EDA; subsequently included in V1 training |
| GOES July 2024 | P2 July 1–22 | P2 July 22–27 | P2 July 27–Aug 1 | P2 development; former P2 test becomes V1 validation |
| GOES May 1–July 22 2024 | V1 gradient/SSL/classical fitting | Not a separate validation interval | Not a separate V1 test | Full-period presentation EDA; architecture/design influence beyond tracked execution UNKNOWN |
| GOES July 22–Aug 1 2024 | Excluded from configured V1 fitting | V1 statistical selection and neural checkpoint selection | Earlier P2 includes July 27–Aug 1 | Full-period EDA; clearly model-selection exposed |
| GOES Aug 1–Sep 1 2024 | Excluded from configured V1 fitting | No automated test-loss selector identified | V1 smoke, strict comparison, subsequent audit/replay and presentation comparison | Presentation full-frame EDA; later V2 design is informed by reported test behavior; complete private decision history UNKNOWN |
| GOES Jan 2025 | No fitting established by inspected tracked evidence | UNKNOWN private access | No model scoring established by external report | Sibling research config/manifest proves acquisition; source/native preparation documented; not a fresh default |
| Annual 2025 flare catalog | Not established | UNKNOWN | Not established | Whole-year acquisition/pinning; extent of human inspection UNKNOWN |
| SoLEXS nominal July 1/3 2024 | Sibling provisional numerical modeling reported, not calibrated science forecasting | Separate provisional pilot | Separate provisional pilot | Native diagnostics and Phase E investigation; nominal dates are not verified UTC coverage |
| Candidate May–July 2020/2022/2023 | UNKNOWN prior access | UNKNOWN prior access | UNKNOWN prior access | Proposed dates only; no data access or suitability statistics in this milestone |

Evidence: `configs/experiments/{p1_goes_reference,p2_goes_july2024,v1_goes_2024}.json`;
`experiments/v1.py:118–204`; presentation ref `presentation/{eda,pipeline,figures}.py`
and `docs/presentation/{eda_evidence,model_evidence}.json`;
external-validation ref `configs/data/{goes_external_january2025,flare_catalog_2025}.json`
and `docs/GOES_EXTERNAL_VALIDATION_RESEARCH.md`; `data/manifests/aditya_inventory.json`;
Phase E and provisional reports on their existing research refs.

**OBSERVED:** Presentation loads all four May–August manifests and makes
raw/log/distribution/rolling/daily/QC plots from the full frame. ACF/PACF and
stationarity use a training-only contiguous block. The narrower diagnostic scope
does not undo broader exposure. **INFERRED:** All May–August is appropriate only
as exposed development or explicitly retrospective evaluation for new decisions.
No period is certified independent by this audit. Candidate independence requires
both contributors' YES/NO/UNKNOWN access attestations (raw, quality, plots,
catalogs, fitting, scores, tools/dates and decision influence) and a custodian.

## Discrepancies and scientific limits

* V1 runner's once-after-all-selection wording conflicts with actual baseline
  test scoring before later selections, and sequential neural test scoring.
  No automated test selector was found; manual influence remains UNKNOWN.
* Neural checkpoint selection uses standardized pinball, while reported losses
  use equal-cell dex pinball (`jepa.py:507–550`, `probabilistic.py:58–70`).
  Future aligned loss/selection needs a versioned model change; V1 is preserved.
* V1 bootstrap keeps fitted seeds fixed, resamples observed days independently
  and silently filters nonfinite pairs (`probabilistic.py:84–105`). Its interval
  cannot establish training-seed robustness or arbitrary inter-day dependence.
  The tracked presentation record shows its small mean JEPA advantage reverses
  when seed 43 is omitted. This audit did not recompute ignored V1 arrays.
* Finite maximum volatility likelihood need not be a converged accepted fit
  (`statistical.py:275–322`). Future strict fit policy requires model-owner work.
* Hardware is OBSERVED Mac14,2, 8 GiB, Python 3.13.3; the older M4/16 GB run-guide
  assumption does not describe this host. MPS suitability remains UNKNOWN.
* GOES masks require finite positive native-range flux, status zero,
  channel-specific electron bits and integer counts 1–60. Missing cadence is
  explicit, never imputed. Record-start UTC and earliest bin-end availability
  are implemented; actual historical delivery latency is UNKNOWN.
* The external source audit documents adjacent-day processing inputs for revised
  GOES science products. No local window check proves upstream causal processing
  or historical as-issued availability. Claims are retrospective prediction of
  the archived product until authoritative evidence resolves that limitation.
* SoLEXS clock reference, bin placement, GTI endpoint/exposure and calibration
  gates remain unresolved. Existing native/provisional success is not scientific
  clearance. No UTC conversion, new quality rule or physical target is invented.

## Protocol and compute proposal

Retain the detailed V2.1 proposal rather than replacing it with conflicting
defaults. Proposed task: one-minute GOES XRS-A/B native flux; log10(F / 1 W/m²)
evaluation; 120-minute context, leads 1–30, 30-minute issue stride; complete
common target support, no filling or origin removal after model failure.
Primary endpoint: equal-channel/lead/quantile dex pinball; primary contrast
fine-tuned JEPA minus matched supervised, equal weighting of three named folds.
Secondary: median log MAE, native MAE/RMSE, reliability, 50%/90% coverage/width
and proper interval score; lead/channel/stratum summaries are exploratory unless
frozen otherwise. Five quantiles imply neither exact CRPS nor event probabilities.

Proposed candidate folds are separate May–July 2020/2022/2023 datasets, with
one-day train/validation and validation/test gaps. Full context, lookback,
forecast, maturity and declared group support must fit inside its partition.
No future-fold initialization or pooled normalizer; unique raw train fitting.
Explicit temporal gaps prevent support overlap but do not prove active-region
independence. Same timestamps, target masks, units, quantiles and metric version
must be used by all paired models; model failure preserves an unavailable result.

The earlier proposal §6 specifies 20 fresh paired primary seeds generated from
SHA-256 labels, explicitly excluding V1 seeds 17/29/43; use its exact recorded
list, with the first five for diagnostic neural arms. It proposes fixed bounded
grids, no adaptive test-driven search,
8 SSL/warmup and 15 downstream epochs, no early stopping for primary controlled
arms, validation-only fixed-epoch checkpoint selection, and deterministic
20,000-window training caps. These remain PROPOSED. Exact learning-rate/optimizer
and comparator grids remain in the earlier protocol; inspect and freeze its
configuration before any execution. No experiments are authorized here.

Budget proposal remains serial CPU, four Torch threads, process RSS ≤4 GiB,
main-study reservation 8–16 CPU hours (24-hour ceiling), 5 GiB outputs and
10 GiB free workspace. This is not a measured M1 benchmark. Run counts in the
earlier plan (225 downstream neural jobs plus shared phases) are substantial;
feasibility must be established on separately authorized exposed-data M2.
Do not silently reduce seeds after outcomes. Reconsider scope before unsealing
if infeasible. Current M1 adds no dependency or training job.

Proposed inference preserves paired seeds and contiguous calendar blocks within
each fixed fold, equal-fold losses and shared resampling across arms/seeds.
Retain empty calendar days and sums/counts. A required empty replicate invalidates
the interval; no redrawing or silent dropping. Block length, repetitions,
confidence, multiplicity and scientific margin require freeze. The V2.1 proposal
uses 3-day blocks with 1/7-day sensitivity and 50,000 draws, one primary comparison
and seven secondary slots. Arithmetic verification does not prove coverage under
nonstationary solar activity. No bootstrap of the three purposively chosen folds
supports a population-of-periods claim; no lower mean alone establishes superiority.

Methodological primary sources: [Bouthillier et al.](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf),
[Owen and Eckles](https://arxiv.org/abs/1106.2125),
[Politis and White](https://mathweb.ucsd.edu/~politis/SBblock-revER.pdf),
[Gneiting and Raftery](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).
They motivate uncertainty and proper scores, not guaranteed coverage for this study.

## Decision register

Status is a workflow classification; evidence labels above distinguish direct
observation from documentation/inference. Proposed values are not approved.

| ID / item | Status | Why / missing evidence / resolver | Can safe M1 proceed? |
|---|---|---|---|
| D01 existing P1/P2/V1 APIs and V2 documentation | VERIFIED | Source/config/ref audit above; current tests separately reported | Yes, reuse |
| D02 May–Aug 2024 exposure and presentation implications | VERIFIED | Tracked source/evidence establish exposure; never independent V2 default | Yes, synthetic inputs |
| D03 private access and model-selection history | REQUIRES_TEAMMATE_AGREEMENT | Both contributors must attest; repository absence cannot establish freshness | Yes; confirmatory access blocked |
| D04 independent candidate calendar and custodian/access log | REQUIRES_TEAMMATE_AGREEMENT | 2020/2022/2023 are proposals; owner/freshness unestablished | Yes; no candidate access |
| D05 candidate bytes/QC/activity/adequate statistical support | BLOCKED | No approved access or measured candidate support; custodian and domain lead | Yes; do not inspect to resolve |
| D06 archived-product versus operational causality | BLOCKED | Authoritative upstream processing/availability evidence missing; instrument/domain lead | Yes, retrospective contract only |
| D07 shared model/experiment/prediction schema | REQUIRES_TEAMMATE_AGREEMENT | Proposed additive contract in M1 design; model owner must accept adapter/schema | Yes; no teammate branch edits |
| D08 primary target/context/horizon/quality/common support | PROPOSED | Retain V2.1 recipe above pending joint freeze | Yes, configurable utilities |
| D09 embargo/dependency and normalization policies | PROPOSED | One day is not scientific independence; domain lead approves; provenance must be honest | Yes, explicit parameter and tests |
| D10 seed cohort/search/stages/selection/failure policies | REQUIRES_TEAMMATE_AGREEMENT | Model owner must implement aligned dex selection, pairing and strict fit acceptance | Yes; no model changes |
| D11 CPU/RAM/runtime/storage reservation | PROPOSED | Host verified; feasibility unmeasured; owner approves after authorized M2 | Yes |
| D12 primary/secondary estimands/multiplicity and 1% margin | REQUIRES_TEAMMATE_AGREEMENT | Statistical/domain leads approve relevance and family before release | Yes, no significance claims |
| D13 block length/replicates/confidence/assumptions | PROPOSED | Statistical lead validates development dependence and freezes choices | Yes; explicit caller settings |
| D14 calibration and robustness arithmetic | VERIFIED | Proper score definitions; implemented behavior requires M1 tests | Yes; formal calibration inference deferred |
| D15 complete V2 runner/model loss/schedules/streaming | BLOCKED | Broader earlier M1 scope belongs to model-owner coordination, outside current foundation | Yes, document deferred integration |
| D16 SoLEXS scientific forecasting/physical labels | BLOCKED | Timing/calibration/GTI gates; instrument authority/domain lead | Yes, no new SoLEXS processing |
| D17 event alarms/Brier score/trajectory coverage | NOT_APPLICABLE | Current continuous marginal-flux foundation does not define these estimands | Yes |
| D18 acquisition/fitting/unsealing/integration | BLOCKED | Outside current authorization; fresh explicit approval and protocol freeze required | Yes; no training/confirmation/merge/PR |

M0 documentation is complete with unresolved decisions recorded. The original
execution plan's stronger M0 gate (all decisions signed) is **not** satisfied.
This distinction and the narrower current M1 scope must accompany readiness claims.
