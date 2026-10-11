# V2 M4B controlled model–evaluation integration report

Date: 2026-10-11 (Asia/Kolkata). Branch:
`feat/v2-model-evaluation-integration`.

## Verdict and scope

**READY_FOR_M5_INTEGRATION** describes the synthetic model/evaluation integration
boundary. It is conditional infrastructure readiness, not authorization or
immediate readiness to execute a GOES pilot. The [M5 handoff](V2_M4B_M5_HANDOFF.md)
lists the outstanding data-loader, protocol, resource and access decisions.
Inference remains **INFERENCE_UNAVAILABLE**; comparisons are **DESCRIPTIVE_ONLY**.
Classical acceptance remains **POLICY_UNAVAILABLE**.

M4B performed no real-data training, GOES downloads, confirmatory evaluation,
scientific test release or January 2025 access. All new execution used bounded
synthetic fixtures. Generic runner release tests use synthetic callbacks only.
No PR or protected-branch integration is part of this milestone.

Evidence labels: **OBSERVED** means inspected code or executed checks;
**DOCUMENTED** means preserved historical evidence; **INFERRED** means a derived
consequence; **UNKNOWN** means not established. No synthetic result establishes
scientific model superiority, independent seeds or future-period performance.

## Verified integration decisions

**OBSERVED:** M4B starts from verified M4A HEAD
`ac3428f910b36b7f10cc0fbb0740ce6de62df5a7`, in an isolated managed worktree.
The dedicated branch was published with upstream tracking before edits. The
original presentation checkout and its untracked files were preserved.

Git ancestry and changed-path audits found a common V1 ancestor, disjoint M4A
and evaluation changes and a conflict-free read-only merge simulation. M2
`94cae59398e52a65074ec66c73ad94bd47ca8867` was merged into M4B only, yielding
`6712ede91a804344db865ef0bd93ea64d7329bf1`. This brings M0/M1 records, diagnostics,
fitting checks, numerical corrections and M2 reliability infrastructure.
The [plan](V2_M4B_INTEGRATION_PLAN.md) records the complete verified ancestry.

M3.1 `5e88f3a7109296c9475378b77be0257a4f9363ab` contains experimental inference
methods. Its production records/comparison/diagnostics/splitting match M2;
merging those experiments would unnecessarily expose unvalidated methods.
Instead its report, research plan, aggregate evidence and referenced figure
are preserved byte-for-byte. The original source branch remains the executable
research reproduction location. No historical finding or M1 default was changed.

## Actual implementation

| Change | Purpose / observed boundary |
|---|---|
| `experiments/v2_evaluation_adapters.py` | Canonical validation-record construction; selected-weight/options checks; seed-free fold/split identity; whole-day calendar envelopes; explicit deterministic replication metadata; exact secondary seed prefix; descriptive cost tables. |
| `experiments/v2_descriptive.py` | Reuses canonical loss panels and diagnostics for paired equal-fixed-fold/equal-seed effects, per-fold/per-seed records, SD/win fraction/leave-one-out diagnostics. Pairs losses before reduction, validates cross-arm provenance and stable per-arm recipes across folds. No inference call or opt-in parameter. |
| `experiments/v2_evaluation_safety.py` | Mandatory actual-fitting and complete-planned-job guards; comparator support matching; development-only wrapper with release refused; immutable descriptive publication at D_LOCKED; complete-study lock/release hooks. Full job-payload D seals are checked on publication and locked resume. |
| `training/controlled.py::_validation_identity` | Binds exact scored context/target content, masks, availability, bin times, split/spec/dataset identities as well as origin ids/times. Prevents a different validation set at unchanged origin labels from impersonating checkpoint-selection support. |
| `experiments/v2_interfaces.py` | Corrects the historical module description after integration; mapping API and interface version remain compatible. |
| Synthetic fixtures and four integration test modules | Exercise all five controlled arms, TCN, quantile-linear and classical persistence, scientific negative cases, publication and reproducibility. |

No architecture, experimental budget, optimizer default, manifest, temporal split,
M4A proposal or classical acceptance threshold was changed. Evaluation kernels
were reused, rather than copied into the adapters. Existing ARIMA/volatility
interfaces and historical research functionality remain available with their
original contracts; they are not used for unapproved acceptance or inference.

The [interface reconciliation](V2_M4B_INTERFACE_RECONCILIATION.md) supplies exact
source/target meanings, A1–A10 status and named executable traceability for all
eleven M4A tests. A8 is deliberately unavailable: implementing an invented
scientific acceptance oracle would violate this milestone.

## Bounded synthetic end-to-end evidence

`test_synthetic_two_fold_all_models_descriptive_publication_without_test_access`
constructs two nonoverlapping fixed calendars and two seeds. Each fold fits
JEPA fine-tuning, supervised, supervised extra updates, frozen JEPA, frozen random,
TCN and quantile-linear. Caps are 24 training windows and one epoch per phase;
the linear fixture uses two regularization candidates. SSL artifacts are shared
explicitly by compatible arms, with attribution retained. Persistence is fitted
once and explicitly replicated with source provenance; linear is fitted per seed.

The test runs the full workflow twice: 28 downstream/comparator fits per execution,
56 across the reproducibility check. It verifies actual common fitting support,
validation-only selection, all planned jobs, native units/channel/horizon/quantile
identity, checkpoint save/reload parity, canonical records, paired descriptive
reports, code identity, immutable publication and identical scientific record
fingerprints/report values across executions. Wall times and lock/publication
metadata are execution measurements and are not asserted identical.
It also pairs each frozen arm, TCN, quantile-linear and extra-update control
against the exact declared JEPA seed prefix; these secondary reports remain
descriptive even when the tiny fixture supplies one seed.

Synthetic generation includes a time gap and missing feature/target cells.
Complete-window eligibility excludes invalid primary support; separate masked
tests preserve null/unscored cells and reject incomplete primary loss panels.
The end-to-end test poisons test-window/release and historical bootstrap entry
points. Only train/validation windows exist and both runs remain D_LOCKED.

## Verification results

Full-suite commands use the isolated Python 3.13 environment, Torch 2.6.0 and
pytest 9.1.1. It shares read-only dependency paths with the original environment
but has its own non-editable project installation. Reinstallation after source
edits preserves the installed-source/checkout provenance check.

| Check | OBSERVED result |
|---|---|
| Exact M4A before integration | **1,310 passed**, 1 pre-existing NumPy warning, 99.68 s |
| Audited M2 merge before M4B implementation | **1,477 passed**, same warning, 100.23 s |
| Final adapter/descriptive/safety/end-to-end suite | **106 passed**, 23.09 s |
| Final full regression | **1,583 passed**, 1 pre-existing NumPy warning, 125.47 s |
| Independent cross-fold/global-identity checks after fix | **12 passed** |
| Independent post-lock payload regressions | **6 passed** |
| Independent publication/resume/drift checks | **11 passed**, 32 deselected |
| Historical runner approval/identity/provenance subset | **13 passed**, 22 deselected |

These branch counts are separate observations, not sums of the historical 1,310
and 1,391 reports. The M3.1 suite was not merged or rerun. The current complete
suite includes V1 bitwise fit parity and checkpoint/native-unit regression checks.
The warning is `numpy.ndarray size changed` during the existing
`test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability`;
it was present on both baseline runs. No failing tests were suppressed.

TDD reproduced missing adapters and origin-only selection identity, then fixed
them. Later confirmed review defects were reproduced before fixes: mutable
predictor options/weights, unpaired/nonfinite budget arithmetic, cross-fold recipe
changes, nondevelopment plan labels and post-lock payload drift. Final checks
were rerun after corrections; tests were not relaxed to permit mismatches.

## Independent review and disposition

Independent read-only agents audited Git architecture, training/model contracts
and evaluation/statistical contracts before implementation. Separate final
contract and safety reviewers inspected the resulting integration, reproduced
defects and verified their fixes. No reviewer concurrently edited source files.

| Severity | Confirmed finding | Disposition / regression evidence |
|---|---|---|
| MEDIUM | Mutable selected predictor options/weights could affect A1 forecasts after fitting. | Fixed: validate options and selected weights before prediction; `test_record_refuses_mutated_selected_predictor`. |
| MEDIUM | Cost ratios could pair different fitting support or emit nonfinite arithmetic. | Fixed: reuse controlled cohort checks and finite canonical serialization; `test_budget_ratio_rejects_unpaired_support_and_nonfinite_arithmetic`. |
| MEDIUM | A fixed-fold comparison could change either model's recipe between folds. | Fixed: stable model/configuration/model-id/point interpretation per side; eight negative cases in `test_each_model_recipe_is_stable_across_fixed_folds`. Independent original reproduction now rejects. |
| HIGH | A development plan could retain a confirmatory execution label. | Fixed: explicit nondevelopment modes reject before construction; four negative cases in `test_development_rejects_non_development_execution_mode_in_plan`. Release remains disabled regardless of plan approval. |
| LOW | Classical acceptance publication metadata used an inconsistent key/status. | Fixed: `classical_acceptance_status=POLICY_UNAVAILABLE`; publication metadata regression. |
| MEDIUM | Post-D prediction/accounting payload drift could publish under the old lock. | Fixed: D guard records full per-job payload fingerprints; publication and locked resume compare seals and reject missing seals. Six live/persisted drift cases; independent synthetic reproduction now raises `ArtifactIntegrityError`. |

Final scoped reviewers report no remaining BLOCKER/HIGH or same-scope finding.
The payload seal is a consistency check in an unauthenticated ledger. It is not
protection against a user deliberately rewriting both payloads and seals.

Normal installed-package imports for all three new modules, strict
installed-source/checkout provenance equality and `scripts/run_experiment.py
--help` also passed. Required-document links and all 31 explicit named test
references resolve; `git diff --check` and staged whitespace checks passed.
Ignore/index/history audits excluded scientific bulk data, generated results,
checkpoints and environment files. M3.1 evidence equality was rechecked by Git
blob comparison and SHA-256. M4A proposals, manifests and acceptance source
remain unchanged. A final fetch observed the separate developer's
`data/v2-goes-development-restoration` branch; M4B did not merge it or inspect
its scientific files.

## Scientific safeguards and limitations

- **Inference:** outputs always declare DESCRIPTIVE_ONLY / INFERENCE_UNAVAILABLE
  with NO_VALIDATED_REPLACEMENT. CI, standard error, p-value, significance and
  bootstrap fields are null. No inference settings can enable them. Seed SD and
  win fraction are descriptive diagnostics only.
- **Test isolation:** DevelopmentRun refuses release, permits only development
  execution labels and requires actual-artifact guards on construction/resume.
  Generic StagedRun retains explicit enablement, approved plan/authorization,
  exact configuration/lock/test identities, code provenance and single-shot
  registry checks. StudyLock supplies complete-fold consistency, no approval.
- **Publication:** existing atomic no-replace publication primitives and sealed
  artifact checks are reused. Changed records, artifacts or locks reject. A
  previously published destination cannot be replaced.
- **Provenance:** actual fitting/normalization/support and recipe/run/seed
  identities are checked against supplied artifacts and declared plans. Caller
  attestations, approval strings, external access history and custody are not
  authenticated by this software; the registry is scoped to one results root.
- **Compatibility:** old V2 origin-only validation records cannot prove current
  exact support and are not silently upgraded. V1 behavior is preserved. A1 is
  validation-only; test records require a future separately authorized workflow.
- **Fairness:** intended support and model-side accounting are verified, while
  optimizer steps, examples, exposure, wall time and RSS stay distinct. No
  equal-compute or superiority claim follows.
- **Data readiness:** the real GOES development loader needs an approved route
  that reads train/validation only. Historical all-manifest loading is not made
  safe by stopping at D_LOCKED. M4B does not duplicate restoration work.
- **Experimental readiness:** SHA-derived seed counts, schedules, objectives,
  regularization grid, resources and retries remain proposals. Quantile-linear
  minibatch order is seeded; its historical one-fit cost proposal needs an
  approved per-seed amendment. A8 and confirmatory inference remain unavailable.

## Publication and M5 recommendation

Only the dedicated M4B branch is committed/pushed. The final response records its
exact publication commit and remote synchronization; the branch history retains
the audited merge and focused implementation/documentation commits. No PR is
created. Protected main/v1 and the original M4A branch must match the verified
refs in the plan at final verification.

Verified implementation commit:
`31910f6609bca10f3b469f2b5c0ad7b6b2489a2a`. The final full suite above includes
the expanded secondary-comparison assertions. Only documentation and preserved
historical aggregate evidence are added after this source/test commit.

Proceed to a **separately authorized development-only** GOES feasibility milestone
only after the [M5 handoff](V2_M4B_M5_HANDOFF.md) prerequisites: verified restored
development inputs and exact data semantics; no-test loader behavior; resolved
D07/D09/D10/D11 and exposure/custody/access decisions; approved complete per-seed
recipes/job matrix; revised linear resource budgets and enforceable host limits.
No confirmatory evaluation is ready under the current inference verdict.
