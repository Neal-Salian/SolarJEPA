# V2 M4B to M5 handoff

Date: 2026-10-11 (Asia/Kolkata). Source milestone branch:
`feat/v2-model-evaluation-integration`.

**M4B delivers a development-only descriptive pipeline. M5 is not authorized.**
No real-data training, GOES feasibility pilot, acquisition, January 2025 access,
confirmatory evaluation or scientific test release follows from completing this
integration. No inference method has been selected:
`NO_VALIDATED_REPLACEMENT` → `INFERENCE_UNAVAILABLE`. Classical fit acceptance
remains `POLICY_UNAVAILABLE`.

Read the [integration report](V2_M4B_INTEGRATION_REPORT.md) for executed verification,
review and Git publication, and the
[interface reconciliation](V2_M4B_INTERFACE_RECONCILIATION.md) for A1–A10 and all
eleven M4A test requirements. Historical proposals remain intact:
[training protocol](V2_TRAINING_PROTOCOL.md),
[compute feasibility](V2_COMPUTE_FEASIBILITY.md),
[M4A handoff](V2_M4_INTEGRATION_HANDOFF.md),
[training proposal JSON](../configs/v2_proposed/training_protocol_proposal.json)
and [pilot proposal JSON](../configs/v2_proposed/feasibility_pilot_proposal.json).
Their values are proposals, not defaults newly approved by M4B.

Evidence labels are **OBSERVED** (direct source/execution), **DOCUMENTED**
(historical cited evidence), **INFERRED** (derived consequence) and **UNKNOWN**
(not established). The historical reports are not rewritten to imply current
findings were known earlier.

## Available implementation

| Capability | Entry point / boundary |
|---|---|
| Validation forecasts → canonical records | `experiments.v2_evaluation_adapters.build_evaluation_record` for selected five-arm/TCN/linear predictors; exact schema-1 records and native units |
| Seed-free fold/split declaration | `split_identity(..., fold_id=...)`; train/validation fingerprints and declared test identity only |
| Complete-support loss panels / diagnostics | Existing `loss_panel_from_records`, `calibration_diagnostics`; no duplicated statistical kernels |
| Paired descriptive reports | `experiments.v2_descriptive.descriptive_comparison`; equal fixed-fold/equal-seed weighting, per-fold/per-seed effects, explicit unavailable inference |
| Actual-fitting and planned-run checks | `experiments.v2_evaluation_safety.DevelopmentRun` and `register_fitting_guard`; every planned controlled/TCN/linear job succeeds and stays selected |
| Comparator/support matching | `check_comparator_cohort` plus existing controlled `check_paired_cohort` |
| Whole-study lock infrastructure | `StudyLock`; complete fold mapping and rechecked persisted locks; grants no release authorization |
| Development publication | `DevelopmentRun.publish_development`; checks artifact locks and D-recorded full job-payload fingerprints, then creates a no-replace JSON artifact package at `D_LOCKED`, no transition to test release |
| Descriptive costs | `descriptive_budget_table`; phase/step/example/time/RSS records and matched J/B wall ratios, `acceptance=None` |

M2 records, provenance/reliability infrastructure and numerical fixes are retained.
M3.1 experimental inference methods are not merged. Its report, plan, small
aggregate synthetic evidence and figure are preserved from
`5e88f3a7109296c9475378b77be0257a4f9363ab`; reproduce that research using its own
source branch and frozen executable commit. Its negative verdict is not permission
to select a favorable conditional method or call the historical bootstrap reliable.

The bounded synthetic integration exercises two folds × two seeds × seven fitted
model kinds, explicit classical persistence replication, exact checkpoint reload,
canonical record/panel conversion, repeatable scientific fingerprints and
descriptive publication without constructing test windows. This validates the
integration on software fixtures. It supplies no real-data performance or
statistical-independence evidence. Final counts and warnings are recorded in the
integration report, separately from M4A and post-merge baselines.

## Decisions and approvals needed before new work

IDs are from the historical [M0 decision register](V2_M0_RESOLUTION.md#decision-register).
M4B implements configurable development contracts; it does not change the
approval status of these decisions.

| Decision | Required explicit resolution | Blocking implication |
|---|---|---|
| **D07 shared schema / split identity** | Joint adoption/versioning of canonical records, the model identity mapping and `M4B_DEVELOPMENT_SPLIT_V1` convention for the intended scientific study | Working development adapters are not scientific protocol approval. |
| **D09 embargo / dependency / normalization** | Approve the actual temporal exclusion rule and `embargo_ns`, fitting scope, availability interpretation and dependence rationale | An explicit zero in a synthetic test is not an approved real-data embargo; one day is not proof of independence. |
| **D10 training / seeds / search / selection / failures** | Approve complete seed cohorts, schedules, objective/selection metric, TCN recipe/optimizer, linear grid and **per-seed linear execution**, complete run ledger, numerical-failure/retry rules and any classical oracle | No pilot or model-value study may silently adopt the proposed recipe. No seed dropping/replacement or changed-setting retry. |
| **D11 compute / RAM / runtime / storage** | Reserve the execution host and approve measured/revised ceilings, process model, threads, timeouts, total budget, checkpoint/prediction storage and linear per-seed cost revision | M4A extrapolations on synthetic data are host-specific; remeasurement is required before executing an approved pilot. |
| **D02 / D03 exposure and access history** | Preserve May–August 2024 development-only classification; record both contributors' exposure/model-selection/private-run attestations | Absence of a local result cannot establish freshness. August 2024 cannot become an untouched holdout. |
| **D04 / D05 candidate calendar, custodian and scientific support** | Approve explicit candidate periods, an access custodian/log, byte identities, permitted QC/eligibility inspection and sufficient support before any fresh-data use | Candidate 2020/2022/2023 periods are proposals, not available approved folds; do not inspect them to resolve the gate. |
| **D06 / D08 task and availability semantics** | Approve target/context/horizon/quality/common-support rules and archived-product versus operational-causality interpretation from authoritative evidence | Retrospective bin-end declarations do not prove upstream operational availability. |
| **D12 / D13 inference and estimands** | Separate protocol decision on fixed-period target, independent units, margins, multiplicity and a validated inferential method/settings, or explicit rescoping to descriptive development reporting | Current status is `INFERENCE_UNAVAILABLE`; no CI/p-value/acceptance gate may be enabled from M4B outputs. |
| **D18 milestone / restoration / acquisition / unsealing** | Action-specific authorization for the next milestone and data-access workflow; later distinct authorization for any test release or protected-branch integration | Branch publication, passing tests and M4B completion grant none of these actions. |

A5 deterministic replication requires an explicit source execution and attestation
even after protocol approval. It marks forecasts reused under seed labels;
replicated labels must never be counted as independent classical training runs.
A8 additionally requires an accountable acceptance-policy owner, exact versioned
candidate/forecast checks, approved thresholds and failure/retry behavior. Existing
ARIMA/volatility wrappers and test doubles are integration interfaces, not the
production scientific oracle.

## Required proposal amendments

### Quantile-linear is a per-seed comparator

**OBSERVED:** `fit_quantile_linear` uses seeded minibatch shuffling and Adam. Zero
initial weights do not make fits seed-invariant. M4B therefore fits quantile-linear
separately for every declared seed; deterministic replication is demonstrated
with persistence only.

**DOCUMENTED discrepancy:** the historical pilot JSON declares
`quantile_linear_fits: 1` for a two-seed pilot, and M4A compute totals/storage use
one linear fit per fold (three for the proposed main study). The M4A A5 wording
also groups linear with deterministic models. These historical statements remain
preserved, but cannot be used to justify replicated linear results in M5.

Before any pilot, prepare and approve a **new versioned proposal amendment** that
defines the linear seed cohort and complete job matrix, fits it per seed, and
revises runtime/RSS/storage projections and total reservation. A two-seed pilot
requires two linear fitting jobs, each containing the full approved λ grid.
The future study's linear cohort size is a decision; do not silently choose
20 seeds, five seeds or one fit. Recompute budgets from the approved choice and
remeasure on the execution host. Do not edit historical evidence to make its
old totals appear to include these fits.

### A development-only GOES loader is a prerequisite

**OBSERVED source / DOCUMENTED proposal conflict:** the existing pilot proposal
says the loader requires a test split and reads every manifest, while its stop
conditions forbid any attempt to read or score the test partition. Stopping a
runner at `D_LOCKED` gates test scoring/release; it cannot undo input reads that
already happened in the loader.

Before an approved GOES pilot, implement or select a route that loads **only the
approved train/validation inputs**, and behaviorally verify that test manifests,
files, arrays, windows and targets are never read or constructed. Use explicit
input selection, train-only normalization and current fitting guards. Keep test
identity as a declaration string; never open test data to compute it within a
development run. The M4B fixture constructs only train and validation windows;
it is evidence for that synthetic route, not for the current GOES loader.

Any changed split calendar, pseudo-test, manifest selection/content or data
identity needs an approved versioned amendment. Do not silently create an inner
pseudo-test, change the V1 splits or edit manifests to make the loader convenient.
Do not run the historical all-manifest loader and describe August as safely
unread merely because no release method was called.

## Data restoration and exposure boundary

**DOCUMENTED:** all May–August 2024 is exposed; May–July contributed to V1
fitting/selection and August was scored. These periods support development-only
feasibility, never confirmatory claims. Historical “sealed”/“untouched” phrasing
does not reverse exposure. January 2025 access is prohibited for this handoff;
it is not a fresh-test default. Private inspection and teammate exposure beyond
tracked evidence remain **UNKNOWN** pending attestations.

The user assigns restoration to a separate developer. Coordinate with that
owner and consume only approved, verified restored inputs; do **not** start a
duplicate download or acquisition. The historical M4A host statement that raw
data was absent is a dated observation, not proof of current execution-host
availability. Verify approved file presence and actual per-file hashes against
the selected manifests only after access is authorized. Preserve immutable source
archives and acquisition facts; do not replace missing acquisition times with
filesystem timestamps or invent NOAA-issued checksums.

Follow [storage policy](DATA_STORAGE.md) and actual `.gitignore`: raw NetCDF,
archives/FITS, arrays, checkpoints, caches and generated bulk results stay outside
Git. Track only small approved configs/manifests, reproducibility code and
portable aggregate evidence. Verify actual paths with `git check-ignore -v`;
never use forced staging to bypass protections. Restoring approved development
inputs does not authorize accessing candidate folds or January 2025.

### Concrete GOES restoration and loading contract

The following is **OBSERVED from source/config/manifest inspection only**; no real
GOES raw file was opened in M4B. It specifies checks for the separately authorized
restoration/loading owner, not a claim that restored bytes already passed them.
Implementation sources are
[`goes_acquisition.verify_history`](../src/solar_flare_jepa/data/goes_acquisition.py),
[`foundation.goes_training` / `validate_goes_files`](../src/solar_flare_jepa/data/foundation.py),
[`read_goes`](../src/solar_flare_jepa/data/goes.py),
[`build_partition_windows`](../src/solar_flare_jepa/forecasting/windows.py),
[`TimeSeriesDataset` / `ForecastSpec`](../src/solar_flare_jepa/forecasting/contracts.py),
[`Normalization.fit`](../src/solar_flare_jepa/training/normalization.py) and
[`validate_fitting_artifacts`](../src/solar_flare_jepa/evaluation/records.py).

| Contract | Exact existing requirement and handoff action |
|---|---|
| Manifest and byte identity | Historical manifests use schema 1, platform `GOES-16`, product `xrsf-l2-avg1m_science`, version `2-2-1`; each names its config and `config_sha256`, dataset id, half-open selected calendar interval, complete file count/byte total, and ordered per-file relative path/URL/nominal date/bytes/SHA-256/acquisition/registration/lineage. `verify_history` validates config/ledger equality, completeness, unique selected paths, budget, lineage and timestamps, then checks actual NetCDF/HDF5 signature, size and SHA-256 without network/mutation. Preserve existing pins; they are local byte identities, not NOAA-issued checksums. For approved train/validation restoration, the historical May/June/July manifests are `goes_v1_202405.json`, `goes_v1_202406.json`, `goes_p2_july2024.json` (31/30/31 files). Using a different input selection requires the versioned loader amendment above. |
| Dataset identity and provenance | The loader verifies each selected manifest before reading native files. Multi-manifest selections must be chronologically contiguous and share a platform; the dataset name joins their dataset ids and metadata records ordered manifest hashes plus every raw source path/hash/size. `TimeSeriesDataset.fingerprint` hashes semantic content including exact times, values/masks, names/units, quality/time/availability policies and metadata. Preserve dataset/spec/training/window/normalization identities and exact validation-content identity through fit, checkpoint, evaluation record and publication; a human-readable dataset name alone is insufficient. |
| Time bins, gaps and coverage | The native reader requires `time.units == 'seconds since 2000-01-01 12:00:00 UTC'` and `long_name` beginning `Record start time`; code declares leap-second-neglecting UTC, not TT/J2000. Bins are `[start,start+60 s)`, with coverage attributes checked when present. Native timestamps must be finite, sorted, unique, minute-grid aligned and within the selected interval/nominal source day. Duplicate, overlapping/off-grid or sub-minute rows fail. Missing grid bins are represented as absent with false validity and NaNs, never filled observations; record measured coverage/gap reports separately from nominal filename dates. Do not move timestamps or substitute filesystem times. |
| Channels, units and calibration boundary | Feature and target order is exactly `('xrsa_flux','xrsb_flux')`, each in native `W/m2`; window selection checks exact names and units. The foundation requires native `g16`, the exact EXIS instrument string, matching file id/version and scalar time-series variables. Existing `SourceIdentity` declares `EXIS/XRS`, irradiance, primary electron-corrected flux, `OBSERVED_NATIVE`, and no preprocessing/unit conversion. Preserve these declarations and native metadata; no new calibration, detector conversion, AU correction or Aditya/SoLEXS substitution is implemented. Physical calibration validity beyond the pinned product contract is **not re-established in M4B** and requires authoritative product evidence/domain approval where needed. |
| Native quality and masks | Required quality/count fields are scalar time series; their finite entries must be integer-coded. Channel flux must be finite, positive, within supplied `valid_min`/`valid_max`, status flag 0 and `0 < *_num <= 60`. Status schema is exactly meanings `good_data eclipse bad_data interpolated`, values `[0,1,2,4]`, masks `[3,1,2,4]`. Electron schema masks `[1,1,6,6,8,16,32,64,128,256]` and values `[0,1,2,4,8,16,32,64,128,256]` are checked; nonfinite/out-of-range electron flags make cells invalid, and code masks `(7|8)` for A, `(7|16)` for B. Preserve channel-specific validity and quality diagnostics. Accepting count 1 is existing behavior, not a new full-minute-quality approval; revised gates require protocol/version approval. |
| Availability and operational claims | The GOES dataset uses `availability_policy='bin_end_earliest'`, no measured actual-delivery array, and `availability_mode='retrospective_bin_end'`. Bin end is an earliest retrospective bound; metadata explicitly says operational latency/delivery **UNKNOWN**. Do not fabricate arrival timestamps or promote this to an operational forecast. Operational windows require explicit actual availability; any supplied actual availability is still enforced by issue time. |
| Train/validation support and embargo | Historical config declares train `[2024-05-01,2024-07-22)` and validation `[2024-07-22,2024-08-01)` in UTC. Only approved train/validation inputs may be loaded. Windows are constructed after partitioning; the full context, target, lookback/maturity and any explicitly supplied group support must be contained, with boundary-end equality allowed and origin end excluded. Guard checks earliest validation context/lookback against raw training end plus explicit nonnegative `embargo_ns`. Touching historical partitions do not approve embargo 0 or establish independence; D09 must choose the actual policy without silent split changes. |
| Horizon, completeness and normalization | Historical GOES spec is 60 s cadence, 120 context bins, 30 target bins, stride 30; target bins start at issue time and span `[issue,issue+30 min)`, not one 30-minute aggregate. Native targets/point predictions are `[origin,30,2]`, with a separate quantile axis. `complete` eligibility excludes invalid context/target cells; `masked` preserves false masks/NaNs without filling, and primary panels reject partial target support. `Normalization.fit` uses each valid unique raw training bin once, `log10(F/(1 W/m2))`, channel means/population SD (zero SD→1), and `fitting_scope='UNIQUE_RAW_TRAINING_PARTITION'`; validation/test values never fit it. The guard recomputes the normalizer and exact raw-support identity. |
| No test or January 2025 access | The historical config lists August as `test` and the all-manifest loader reads it; that route is unsuitable for the promised pilot. The new approved route must reject reads/construction of test manifests/files/arrays/windows/targets and use only a declared test identity string. January 2025 remains prohibited; no broad glob, fallback loader, catalog access, candidate-period inspection or duplicate acquisition is authorized. Verify this behavior before a GOES pilot, independently of the `D_LOCKED` release gate. |

The reader's hard-coded product semantics are **OBSERVED implementation
requirements**. Their scientific motivation is **DOCUMENTED** in historical
source/report context, not newly externally validated by this integration.
Actual restored coverage, mask counts, raw schema conformance and file checksums
remain **UNKNOWN until authorized execution**. Proposed policy changes remain
subject to D07/D08/D09/D10 and a versioned amendment.

## Resource proposal carried forward, still unapproved

These exact historical values remain **PROPOSED_REQUIRES_APPROVAL** under D10/D11:

| Item | Historical proposed value |
|---|---|
| Primary / secondary seed cohorts | 20 SHA-256-derived seeds / first five for specified secondary arms; pilot uses first two |
| SSL / extra-update warmup / downstream schedule | 8 / 8 / 15 fixed epochs; explicit selection rules |
| Train windows / batch | 20,000 chronological subset / 256 |
| Optimizer | AdamW `lr=1e-3`, `weight_decay=1e-4`, reset per phase, clip 1.0; no learning-rate schedule; linear Adam `lr=0.01` |
| Training / selection objective | `dex_pinball_equal_channel_v2`; separate loss-comparison cohort proposed with V1 normalized objective |
| Linear grid | `{0,1,10,100,1000,10000,100000}`, 100 epochs per λ; revised **per-seed** execution must be proposed |
| Precision / threads | CPU float32, four Torch threads, deterministic algorithms |
| Memory | 4 GiB process peak RSS; historical runner checks between jobs |
| Timeouts | SSL 300 s; neural downstream 600 s; TCN and quantile-linear 1,800 s each |
| Pilot total wall budget | 7,200 s |
| Process model | One job per process |
| Infrastructure retry | At most one logged retry with identical seed/config/code; numerical failures recorded without changed-setting retries |

The original M4A pilot projections are about 19 minutes optimistic, 24 minutes
expected and 57 minutes conservative on its host. Main-study projections are
about 4.0–4.1 / 5.1 / 11.9–12.3 hours. These are **DOCUMENTED historical
extrapolations**, exclude classical/analysis cost and use the old one-linear-fit
count. They are not revised M5 estimates or proof that approved resource limits
will hold. Per-process high-water RSS, optimizer steps, examples, unique support,
data exposure and wall time are different measurements; report all distinctly.
J/B step matching supplies no equal-FLOP/equal-compute guarantee, and shared SSL
attribution must not be double-counted.

## Safe continuation after separate authorization

1. Verify the exact M4B branch/commit and report, clean relevant Git state and
   remote state. Preserve protected `main`/`v1`, teammate branches, historical
   evidence and existing work. Create/publish only the authorized next milestone
   branch from the user-approved base; do not infer a main integration action.
2. Resolve/freeze D07/D09/D10/D11, data/exposure/custody decisions and the versioned
   linear/loader amendments. Name the complete planned job matrix and code,
   configuration, data, split, normalization, protocol and seed identities.
3. Coordinate restoration with its developer, verify only approved development
   inputs, and prove the selected loader has no test-read path. No duplicate
   acquisition, January 2025 access or unapproved manifest/split change.
4. Execute a separately approved bounded feasibility pilot with the mandatory
   `DevelopmentRun` guards and exact planned jobs. Retain failure records; stop
   on temporal/provenance/support/reload failures, unauthorized data access,
   nonfinite outputs or approved resource-limit breaches. Keep the V1-loss
   comparison in its separate cohort; do not mix objectives in a primary pairing.
5. Inspect validation histories, λ paths, measured time/RSS/storage, native-unit
   reload parity, complete-run ledger and canonical records. Publish only
   descriptive outputs at `D_LOCKED`. Any scientific decision change gets a new
   versioned protocol before later execution; do not tune to a pilot advantage.
6. A confirmatory M5 requires its own scope/inference decision, fresh approved
   data/custody and exact release authorization. With the current M3.1 verdict,
   retain `INFERENCE_UNAVAILABLE`; either separately validate an inference design
   or explicitly rescope to descriptive development work. M4B does neither.

`StudyLock` enforces declared complete-fold locks in one results root and preserves
the historical `StagedRun` release gates: explicit enablement, an approved plan,
matching configuration/lock authorization and declared test identity. Approval
strings and provenance are unauthenticated. Same-user code can read files outside
the runner, alter permissions, use another root or remove a registry; process-local
hooks are not system access control. A release crash is fail-closed and can leave
unsealed partial output. Signed custody, honest exposure declarations, access logs
and action-specific human authorization remain procedural responsibilities.
`DevelopmentRun` always refuses test release and reinstalls its fitting guards on
resume. Locked resume/publication compare full job payloads, including prediction
and accounting metadata, with the successful D-hook fingerprints; changed payloads
or missing seals fail. This detects ordinary drift, not deliberate rewriting of
both ledger payloads and unauthenticated seals. Generic raw `StagedRun` users must
explicitly reinstall required hooks.
