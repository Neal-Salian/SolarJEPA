# Presentation checkpoint plan

Authorized scope: the user's 16-phase presentation brief, implemented on
`presentation/eda-model-comparison` from audited `origin/v1`
`644648f7d555fcbcb3eed4495d37fecffdd1863a`. No training, new scientific downloads,
V1 changes, V2 data access, merge or PR.

## Design and file boundaries

Reuse `verify_history`, `validate_goes_files`, `read_goes`, the descriptive EDA
summary and `block_bootstrap`. Add a presentation package with separate EDA,
saved-prediction arithmetic and plotting modules; one CLI and one notebook call
these functions. Read exactly the four V1 manifests and the strict V1 bundle.
All new assets live under `docs/figures/presentation/`; small numerical evidence
and figure lineage live under `docs/presentation/`. Bulk inputs remain ignored.

## Execution checklist

- [x] Fetch/record refs; preserve pre-existing untracked work; create/publish branch.
- [x] Inspect V1 source/configurations, native inputs, artifacts and prior figures.
- [x] Test gap-safe block selection, invalid-value handling, stationarity settings,
  independent metric arithmetic, common support and artifact mismatch rejection.
- [x] Implement reusable analysis and figure generation; run on pinned V1 inputs.
- [x] Execute the notebook; retain compact numerical outputs, no embedded datasets.
- [x] Write inventory, EDA report, comparison report and ten-slide guide with captions.
- [x] Independently review science/code/figures; correct confirmed errors.
- [x] Run full tests, imports, CLI and numerical/source checks; record exact results.

Publication gate: review storage/Git scope, then commit and push exclusively to
the presentation branch. The final response records the published commit and
remote synchronization; this plan records the work before that Git checkpoint.

## Scientific choices fixed before analysis

- Descriptive coverage/distributions: all May–August V1 data with native QC masks.
- ADF/KPSS/ACF/PACF: longest jointly valid contiguous **training** block, earliest
  tie; no gap concatenation or imputation. Tests on log levels and first log
  differences; ADF intercept, fixed 30 lags, sensitivity 10/60; KPSS intercept,
  automatic HAC bandwidth with bounded p-values disclosed. Raw-level ADF/KPSS
  also supplied for transformation comparison; raw flux scaled by its mean for
  numerical conditioning (a positive constant, not a log transform).
- ACF/PACF descriptive, without misleading iid significance bands; inspect
  differences and squared differences for volatility. Seasonal-lag evidence on
  this one contiguous block cannot establish stable solar seasonality. SARIMA is
  omitted unless a defensible training-only period emerges; it must not delay
  the core deliverables.
- Scores: independently recompute every saved test model's dex losses and
  verify against summary/per-origin/lead/quantile records. Family rows average
  losses for seeds 17/29/43, never average predictions. Point-only methods have
  no invented pinball or intervals. All probabilistic figures share support.
- Retain seed 43 influence, poor frozen transfer, channel calibration imbalance,
  classical optimization caveats, normalized-selection/dex-evaluation mismatch,
  dependence, retrospective availability and repeated August access.
- Existing figures are reused by reference when correct. New comparison figures
  show seed means and paired seed differences; no result-favouring tuning.

## Review focus

Missing bins versus rejected measurements; timestamps versus bin-end lead labels;
float64 log arithmetic and equal-channel weights; seed losses versus ensembles;
point-only versus quantile forecasts; untouched V1 and excluded V2 inputs;
bounded stationarity p-values versus claims of global stationarity; reproducible
figure lineage and relative paths. The detailed brief is the specification;
this plan records implementation choices within that authorization.
