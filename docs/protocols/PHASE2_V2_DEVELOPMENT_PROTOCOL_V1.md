# SolarJEPA Phase 2 development protocol — version 1

Date: **2026-10-15, Asia/Kolkata**. Identifier: `solarjepa.phase2.v2.development.v1`.

Design fingerprint: `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624`.

**2026-10-16 authorization addendum:** the owner explicitly ratified this exact version/fingerprint and all17 decisions, and authorized Phase2 pilot infrastructure implementation, synthetic/non-training validation, and feature-branch commit/push. Independent recomputation and consistency inspection confirmed the design. G1 is satisfied; G2 implementation is authorized, subject to verification/review. G3 host/data/output reservation and G4 fitting/execution approval remain absent. No defaults or historical design/verification evidence are changed; `design.decisions` retains its original design-time bookkeeping. The register’s outer authorization fields record the new authority. The dated finalization narrative below remains historical.

**FINALIZED DEVELOPMENT DEFAULTS — READY FOR OWNER RATIFICATION — EXECUTION BLOCKED.** All 17 design decisions now have concrete defaults, rationale and risks. The user's authorization covers this documentation milestone. It does not approve implementation, fitting access, resource reservation, a pilot or test release. No owner signature or historical approval has been invented.

The normative [design and decision register](phase2_v2_development_v1.json) contains exact per-job configurations, source/environment/data pins and all 17 decisions. Its `design_fingerprint` hashes canonical JSON of `design`; outer review/approval bookkeeping is excluded. Ratification must identify this version and exact fingerprint. The [verification record](../evidence/phase2_v2_protocol_v1_verification.json) records checks and independent review. If prose and register disagree, **stop and amend/review before ratification**, rather than choose a convenient interpretation.

## Purpose, evidence and authority

This is an exposed-data engineering feasibility design: establish that the existing V2 controls, baselines, checkpointing, guarded evaluation and resource interfaces can be connected reproducibly. It does not test JEPA value or authorize the prospective multi-fold/20-seed study. The [readiness audit](../PHASE2_V2_VALIDATION_READINESS.md) and M0–M5 reports remain historical evidence; their original proposals, null approval register and preflight are unchanged.

**OBSERVED:** M5 `6071868` already integrates controlled models, TCN, quantile-linear, M4B evaluation and the restricted loader/supervisor. This version is finalized on readiness checkpoint `8b4bc50f754c4a48921d993568760e8d7c7e056c`, with the same executable fingerprint `271e9f14caeb3bc5c984f4513ffdae598aa1e6fdc51c0a97e4ec4e9c955dd7c2`. **DOCUMENTED:** prior native M5 validation and synthetic model tests support reuse. **INFERRED:** preserving their task/calendar/recipe minimizes changes for feasibility. **UNKNOWN:** private exposure, future host feasibility, independent solar loss units and actual operational delivery/upstream causality.

January 2025 is model-outcome-exposed after the completed [V1 retrospective evaluation](https://github.com/Neal-Salian/SolarJEPA/blob/a502d3fbf65f57c795b087491d216cc37922071f/docs/PHASE1_GOES_EXTERNAL_EVALUATION.md). It is excluded from this design and cannot be untouched confirmation. These defaults follow existing implementations and feasibility constraints; no January results are used to select a model, grid, seed or reporting method. Unrecorded historical decision influence remains UNKNOWN. The nine original V1 checkpoints and saved external results remain immutable.

## Data, temporal support and QC

Only the existing pinned May, June and July 2024 manifests may enter a later authorized pilot. The register lists their full SHA-256/config identities. Within `allowed_manifests`, `sha256` identifies the manifest bytes; `files` and `bytes` describe the referenced native NetCDF count/volume, matching existing loader evidence. No acquisition, broad file glob, catalog, August/January data, candidate 2020/2022/2023 periods, test partition or inner pseudo-test is permitted.

| Role | UTC half-open interval |
|---|---|
| Training | `[2024-05-01T00:00:00Z, 2024-07-22T00:00:00Z)` |
| Validation/selection | `[2024-07-22T00:00:00Z, 2024-08-01T00:00:00Z)` |

Choose **zero embargo**, `embargo_ns=0`, with full partition-local context/target/dependency containment. It preserves the frozen loader and V1 fitting support. Touching intervals do not establish independence. A one-day truncation is a defensible future amendment, but changes support/normalization/loader and does not enable sampling inference. No upstream causality guarantee follows from local containment.

The fixed task is GOES-16 `xrsf-l2-avg1m_science` version `2-2-1`, ordered `xrsa_flux`,`xrsb_flux`, native `W/m2`, 60-second cadence, 120 observed context bins, 30 future one-minute target bins and a 30-minute issue stride. Use dimensioned `log10(F/(1 W/m²))`, complete eligibility, explicit missing bins and no imputation. Availability remains `retrospective_bin_end`; actual delivery is UNKNOWN.

Retain native QC: finite positive flux within supplied native bounds; status zero; integer-coded quality/count fields; electron flag 0–511 with excluded bits `(7|8)` for A and `(7|16)` for B; `0 < count <= 60`. **No QC sensitivity cohort in version 1.** Partial-minute averages are treated as observations, a disclosed limitation. Count≥30 sensitivity is deferred rather than silently added to the job budget.

Normalization uses each valid unique raw training cell once, population SD and existing zero-SD handling. No validation/test fitting or post-outcome calibration is permitted. Future authorized preparation must recompute and verify actual support/statistics against the historical pinned identities; a stored expected hash is not permission to skip those checks. No scientific decoding or normalization fitting occurs in this finalization.

## Exact model, seed and job design

Use the ordered seeds **1261866429, 1291916211** for every stochastic arm and linear path. They are the first two previously derived SHA-256 protocol seeds. Never redraw, replace, omit or favor a seed. Fix CPU float32, four Torch/native-library threads and deterministic algorithms; future fresh workers must establish/assert device/dtype explicitly before building.

Controlled architecture: patch5, width32, depth3, heads4, predictor depth2, MLP ratio4, head128, dropout0; quantiles `[.05,.25,.5,.75,.95]`. JEPA uses Smooth-L1, block context masking of four patches, EMA `.996→1`, and zero auxiliary JEPA loss during fine-tuning. AdamW has lr`.001`, weight decay`.0001` on all trainable parameters including biases, clip norm1, no LR schedule and a fresh optimizer per phase. Use batch256, the same deterministic evenly spaced chronological cap of20,000 complete stride-one training windows, and `monitor_windows=2048`. Full emitted configurations are in the register: **do not substitute `JepaConfig()` defaults**.

| Model family | SSL epochs | Supervised warmup | Downstream epochs | Downstream trainable modules |
|---|---:|---:|---:|---|
| Fine-tuned JEPA (J) | 8, shared artifact | 0 | 15 | Encoder, predictor, head |
| Supervised (S) | 0 | 0 | 15 | Encoder, predictor, head |
| Extra-update supervised (B) | 0 | 8 | 15 | Encoder, predictor, head |
| Frozen JEPA | 8, reuse same artifact | 0 | 15 | Head only |
| Random-frozen | 0 | 0 | 15 | Head only |

All 15 downstream epochs execute; there is no early stopping. Select the exact earliest validation minimum among downstream epochs only, retaining curves and selected epoch. The internal compatibility `patience=1` field does not override schedule `early_stopping_patience=null`.

TCN uses width32, kernel3, dilations `[1,2,4,8,16,32]`, dropout0, the same optimizer/batch/clip/cap/seeds and 15 fixed epochs. Its 253-bin receptive field includes padding around only120 observed bins. Quantile-linear uses flattened context **values**, with complete-mask enforcement, zero initialization and seven λ values `{0,1,10,100,1000,10000,100000}`. For each seed fit every λ for100 fixed epochs with Adam lr`.01`, batch256, no clipping/additional weight decay and penalty `λ mean(W²)` excluding bias. Reset identical PCG64(seed) permutations for each λ. Train raw quantiles; sort for validation/prediction. Keep the final-epoch candidate, choose the lowest validation loss and smallest λ on exact ties. Record final per-λ metric/objective/coefficient norm/crossings/steps/weights/order, selected λ and `BOUNDARY_SELECTED` at the maximum. There is **no grid extension** or promised dual per-epoch linear history.

Primary train **and** selection loss is `dex_pinball_equal_channel_v2`, with normalized V1 loss as neural diagnostic. Separate alternate J/S runs train **and** select on `normalized_pinball_v1`, recording dex diagnostics. This is a bundled objective/selection comparison, not an isolated causal training-loss experiment. The alternate J reuses the same per-seed SSL artifact: existing identity checks exclude downstream loss settings, but source/environment bindings must additionally be supplied externally.

| Descriptor prefixes, first/second seed | Job | Count | Future development run |
|---|---|---:|---|
| 00 /10 | Shared SSL | 2 | Supervisor only |
| 01–05 /11–15 | J,S,B,frozen JEPA,random-frozen | 10 | Primary |
| 06 /16 | TCN | 2 | Primary |
| 07 /17 | Full seven-λ linear path | 2 processes;14 candidates | Primary |
| 08–09 /18–19 | Alternate-loss J,S | 4 | Separate alternate-loss |

Total: **20 process jobs,18 selected model jobs,14 nested linear candidates**. Preserve complete ordered jobs and explicit successful sealed-SSL dependencies. Exactly one SSL artifact per seed serves primary J/frozen J and alternate J. No SSL recomputation or changed artifact is permitted under this version. All classical references, including persistence/empirical persistence and ARIMA/volatility, are **explicitly excluded** (`classical_job_count=0`). This resolves CLASSICAL without an unavailable acceptance oracle or new guard route; it supplies no V2-versus-classical conclusion. Their future inclusion requires a separately scoped amendment.

## All 17 decisions resolved for development design

Every register item is `DECIDED_FOR_DEVELOPMENT_DESIGN`, with a selected-default pointer, evidence, rationale, risks and rejected alternatives. This status is **not** `APPROVED` and grants no action authorization.

| ID | Version 1 decision | Main tradeoff/remaining approval |
|---|---|---|
| D09 | Zero gap; fixed May–July intervals; contained support | Comparability over changed calendar; dependence retained |
| D10 | Fixed two-seed20-job matrix above | Feasibility only; owner must ratify exact fingerprint |
| D11 | 2 GiB sampled RSS,serial/four threads,7200s total,job limits below | Conservative design limits; named host/storage not reserved |
| DATA_ACCESS | Three pinned May–July manifests only | Actual fitting access needs later explicit approval |
| AUGUST | No August loading, arrays, scoring or reporting | Already exposed; no pilot test endpoint |
| QUALITY | Existing masks/counts1–60; no sensitivity cohort | Partial-minute means and QC-conditioned retention disclosed |
| SEEDS | Ordered fixed pair for every stochastic fit | Limited optimization spread; no replacement |
| BUDGETS | 8SSL/8B-warmup/15downstream;batch256/cap20k;no stopping | Budgets transparent,not equal hardware compute |
| LOSSES | Dex primary;normalized alternate J/S cohort | Bundled train/selection recipe comparison |
| CHECKPOINT | Validation-only exact earliest minimum;linear finalλ path | Post-selection scores; unequal search opportunities |
| TCN | Fixed causal CPU recipe,two seeds | Capacity/padding differ from Transformer |
| LINEAR | Seven λ values,two actual seeded paths,no extension | Sparse weak-penalty range; boundary results retained |
| CLASSICAL | Exclude every classical fit/reference in v1 | No classical baseline conclusion; scope remains20jobs |
| FAILURE_RETRY | Zero automatic retries;terminal first failure | Infrastructure glitches can leave pilot incomplete |
| STATISTICS | Canonical paired descriptive reporting only | `NO_VALIDATED_REPLACEMENT`;no nominal inference |
| TEST_PROHIBITION | No test objects/release;end at `D_LOCKED` | January and candidates never become fresh by relabelling |
| REPRODUCIBILITY | Exact source/environment/data/config/job/report freeze | Caller declarations/private history have limits |

## Resource, failure and compute policy

| Design stop/reservation parameter | Value |
|---|---:|
| Sampled live worker+descendant RSS | 2,147,483,648 bytes (2 GiB) |
| SSL attempt timeout,including preparation | 300s |
| Controlled downstream attempt,including B warmup/preparation | 600s |
| TCN attempt | 1800s |
| Full linear path attempt | 600s |
| Cumulative wall limit | 7200s |
| Automatic retries | 0 |
| Supervisor polling | .05s |
| Minimum free output storage before launch and each job | 1,073,741,824 bytes (1 GiB) |

These deliberately supersede older4GiB/linear1800s/one-retry proposals **for this design only**. Prior resource evidence supports selecting conservative limits; no actual workload under these limits has been measured here. The observed reference host is Mac14,2/arm64/8GiB, not a reservation. Free-space checks/reservation are not implemented by the supervisor and need future integration. Sampling can miss brief peaks; these are not hard OS memory/thread limits. Six native-library thread variables and Torch are set to4; OS thread count is not guaranteed.

The20 first-attempt timeout ceilings sum to13,800s, **exceeding** the7200s total. The total overrides them and includes preparation, monitoring, validation, sealing/bookkeeping and conservatively charged crash downtime. Completion is not guaranteed; never extend limits or alter settings to rescue a run.

Timeout/RSS/numerical/ordinary/integrity/spawn/interruption failures stop the planned pilot on the first attempt; monitoring failure and total exhaustion stop immediately. Preserve failed and pending jobs, logs and quarantined partials. The existing supervisor uses pending/succeeded/failed and stop reasons; a future driver must derive `INCOMPLETE`. Do not shrink support/seed cohorts or publish a partial run as the completed comparison. Failure reports may expose engineering diagnostics through an explicit incomplete-report route, never bypass the complete-job scientific publication guard. Any recovery requires owner investigation/approval and unchanged identities; additional fit attempts require a reviewed amendment and explicit authorization.

J versus B matches **encoder/predictor update opportunities**, not FLOPs/runtime/head updates/energy. B's head additionally trains in warmup; SSL has teacher computation. Record per-module optimizer steps/examples, phase/preparation/validation time, actual pilot elapsed time, sampled RSS, device/threads/environment and storage. Actual pilot costs count each SSL once. Standalone JEPA recipe costs attribute full SSL plus its own downstream work; never sum those duplicated attributed costs as actual pilot time. No runtime ratio, skill margin or adaptive compute-matching acceptance threshold is selected.

## Paired evaluation and reporting

Principal development contrast: J−S. Predeclared secondary contrasts: J−B,frozen JEPA−random-frozen,J−frozen JEPA,B−S,J−TCN,J−linear. Report all, plus the separate alternate-cohort J−S and within-arm bundled loss-recipe differences. No favorable comparison/channel/seed selection.

Require identical valid timestamps, observed targets, grids, masks, quantiles, calendars and declared complete cohorts; never remove failed-model origins. Pair losses before reduction. Average equal five-quantile×30-lead×two-channel dex pinball per origin, then equal origins within each fixed fold, then equal folds/seeds. This design has one exposed fold and two seeds. Report A−B (negative favorsA); relative reduction is `−mean_difference/mean_B` only when the reference is positive, never a mean of percentages.

For every arm/seed retain aggregate/A/B pinball, all lead×channel×quantile losses/reliability and support counts. Report inclusive central50%/90% **marginal predictive** coverage,width and interval score in dex and channel-specific nativeW/m²; supplementary saved median-point MAE/MSE/RMSE in both spaces. Derive pooled RMSE from pooled squared errors. Report full neural curves/selections, linear final-λ path, raw crossings/boundary flags and collapsed predictive intervals. Model predictive intervals are permitted diagnostics; they are not sampling intervals or a calibration guarantee.

Publish each seed's scores/effect, two-seed mean, descriptive sample SD, strict-negative win fraction(ties nonwins) and leave-one-seed-out differences. Leads/channels/quantiles, correlated origins and seeds sharing data are not independent experimental replications. All selected validation metrics are post-selection on exposed data, not unbiased generalization estimates. Neural15-epoch versus linear7-λ selection opportunities differ.

Mandatory header: **DEVELOPMENT FEASIBILITY ONLY — EXPOSED MAY–JULY2024 — POST-SELECTION VALIDATION — ONE FOLD/TWO SEEDS — DESCRIPTIVE_ONLY — INFERENCE_UNAVAILABLE — NO_VALIDATED_REPLACEMENT.** The six comparison fields `difference_interval`,`relative_interval`,`standard_error`,`p_value`,`significance`,`bootstrap_negative_fraction` must be JSON null. Their three existing reason fields equal `NO_VALIDATED_REPLACEMENT`. Reject sampling inference under aliases, nominal comparison confidence/credible intervals, bootstrap/calendar ranges/sign probabilities, seed tests, superiority/equivalence/noninferiority/acceptance/power/population win claims and operational/fresh-test/generalization claims. Do not use legacy interval-producing APIs as a fallback, even as sensitivity.

Future driver/report schemas must enforce this policy: generic `publish_development` accepts arbitrary JSON and status labels alone do not validate every report. M2/M3's negative inference evidence remains in force; no alternative method or larger bootstrap draw count is silently selected.

## Execution gates and remaining owner approvals

There are **zero unresolved design choices and four pending action/resource gates**. Owner ratification can accept this complete package; no need to rediscover17 defaults.

1. **G1 — Owner ratification:** explicitly accept version1 and its exact design fingerprint, including zero embargo/partial-minute QC/no classical references/resource limits/no retries and the descriptive/post-selection risks. This signature is currently absent.
2. **G2 — Implementation authorization/review:** separately authorize only the missing integration; no driver is implemented here. Reuse two supervisor-only SSL jobs, one primary14-model `DevelopmentRun`, and a separate alternate4-model run. Bind every exact `JobSpec.parameters.model_config`, sealed SSL/source/environment identities, CPUfloat32/thread assertions, complete guards, validation reload parity, free-space checks and descriptive-only schemas. One20-job `DevelopmentRun` is invalid. Nontraining verification and independent review must pass.
3. **G3 — Named host/environment/data/output reservation:** owner/operator must approve the actual host and resources, verify data/output roots,manifest/raw identities,normalizer/support/environment and budget feasibility before launch. This document does not approve fitting microbenchmarks or claim measured workload feasibility. Unresolved local cloud `main` readability/fetch limitations remain documented; implemented-source identity must be verifiable without protected-ref repair.
4. **G4 — Bounded execution/fitting approval:** only afterG1–G3, obtain a separate explicit approval for one pilot with frozen implemented source/config/design identities and May–July fitting scope. No approval for real fits or experiments exists now.

Any later test/candidate access, January reuse, operational qualification or inferential/confirmatory study is **G5, outside this protocol** and requires a separate design/access/methodology authorization. Passing checks, protocol publication or ratifying design grants none of those actions. Changing the old approval flags cannot enable training: existing M5 preflight remains unchanged, rejects invented approval and reports17 outstanding legacy decisions because it does not consume this new documentation register.

## Verification and review

Fresh existing non-fitting checks: **102 passed, one SSL-fitting benchmark deliberately deselected, no warnings,7.93s**. The proposal unit test constructed one TCN solely for parameter-count/receptive-field checks, without a forward pass, prediction or fit. The retained read-only consistency helper passed **257 checks**, including all17 decision pointers, exact20 typed job configurations, seeds/dependencies,13800/7200s arithmetic, source/manifest pins, null authorizations and unchanged legacy policy. It constructed no model and performed no fit/prediction/scientific decoding. A helper-only wrapper-comparison mistake was corrected without changing any protocol/source values; both helper versions are preserved in ignored evidence.

Two normally installed metadata-only preflights from outside the checkout returned expected exit3 and byte-identical records:17 legacy approvals outstanding,PILOT_NOT_AUTHORIZED,no training/release/data decoding. All nine V1 checkpoint hashes,13 other worktree statuses and29 remote branch heads remained unchanged before commit; current source identity is unchanged. Historical native/data/model validation is cited rather than rerun as a new scientific experiment.

Scientific, statistical and implementation subagents reviewed the defaults and source contracts. The fresh independent reviewer returned **specification PASS, scientific-quality PASS, feature-only publication ready after one evidence-wording correction**. The corrected record now distinguishes unit-test-only TCN construction from the helper’s zero model builds and from the absence of fits/predictions/experiments. The reviewer independently matched the four staged documents, design/config/source/verification identities, manifest/config volumes, V1 evidence, all17 decisions and the14+4 grouping/resource arithmetic, without rerunning tests or models. The corrected evidence and clarification were independently rechecked: **specification PASS, scientific-quality PASS, feature-only publication ready; no new issue**. Unknown exposure, processing/availability, future host feasibility and confirmatory inference remain unestablished. Full logs/helpers remain ignored with their hashes in the verification record; only documentation is committed. No driver, fitting access, host reservation or pilot authorization is created.
