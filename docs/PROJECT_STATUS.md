# SolarJEPA project status — canonical tracker

Current checkpoint: **2026-10-06** (Asia/Kolkata). Git fetch verifies D.1 merged
on synchronized main `1a4991da4dda9676caeb1d7e35a03408528c3188` (PR #4).
`research/experiment-evaluation-foundation` was created and published from that
main before milestone edits. Checkpoint `805f1c3` is frozen and unchanged.
The [P1 audit](P1_REPOSITORY_AUDIT.md),
[Paperclip reconnaissance](P1_LITERATURE_RECONNAISSANCE.md), and
[proposed design](P1_PROPOSED_DESIGN.md) are a research/design checkpoint;
approved P1 infrastructure is now implemented on the separate published
`feat/p1-experiment-evaluation-foundation` branch from `805f1c3`. The preserved
[integration audit](P1_INTEGRATION_READINESS_AUDIT.md) returned
**NOT_READY_FOR_INTEGRATION** at `11b72bb`: window values/masks could contradict
canonical raw TrainingSlice support. Focused [remediation](P1_TRAININGSLICE_REMEDIATION.md)
at code commit `8ba57aa58242facf7614e805695fe9e71406ea3c` validates this
relationship and records effective training identities. The preserved
[fresh re-audit](P1_INTEGRATION_READINESS_REAUDIT.md) of `0f587d9` then returned
**NOT_READY_FOR_INTEGRATION**: R1, copied/deserialized/subclassed contexts could
expose post-issue support to all six baseline prediction APIs. Focused
[prediction-context remediation](P1_PREDICTION_CONTEXT_REMEDIATION.md) at
`009547932e398edeef1bd2ede2ff3d10bc9e1862` reconstructs and validates detached
causal snapshots before consumption. That checkpoint passed 480 targeted / 646
total tests, but the preserved [final audit](P1_FINAL_INTEGRATION_READINESS_AUDIT.md)
of `8fa3877` returned **NOT_READY_FOR_INTEGRATION** for N1: non-string categorical
semantics and caller-owned metadata survived snapshots under colliding identities.
Focused [canonical-semantics remediation](P1_CANONICAL_SEMANTICS_REMEDIATION.md)
at `edea3df87c0b08fdc08e66fe1df597334270dad8` normalizes categories, captures owned
metadata/container content and canonical parameter keys before validation/use.
Verification: **659 P1 targeted / 825 total tests passed**, one existing warning;
179 new canonical-semantic cases, all 53 F1 and 185 R1 regressions pass.
All 22 modules import from the rebuilt installed distribution outside checkout
and match source. Fresh synthetic/GOES pairs each score all 54 combinations with
zero failures; stable-byte, artifact and corruption checks pass. All 109 starting
artifact/config/skill identities match after acceptance. A fresh independent
reviewer closed additional factory alias variants and found no surviving related
BLOCKER/HIGH in 686 bounded probes plus eight factory and six Mapping checks,
repeated against the installed package. Historical F3-F9 limitations and a
pre-existing malformed numeric-subtype edge remain documented. The historical
[P1 implementation checkpoint](P1_IMPLEMENTATION_REPORT.md) remains preserved.
Current state: **READY_FOR_P1_REAUDIT**. The next step is another fresh
integration-readiness audit; no integration or
next-phase work is authorized. Main and the research branch remain unchanged.
The Paperclip pointer remains untracked.

**Phase E remains BLOCKED_FOR_PHASE_E pending authoritative SoLEXS evidence.**
The official request is user-reported as sent; no reply is available. P1
implements instrument-independent mechanics on synthetic/existing GOES reference
data, while the scientific dataset/acquisition/training gates
remain in force. Historical D.1 manifests and reports retain their original
checkpoint states; their old integration wording does not override observed Git.

Previous update (before the D.1 PR merge): **2026-10-03**, Phase D.1 authoritative
evidence and
calibration acquisition on `data/solexs-authoritative-evidence`, created and
immediately published from clean synchronized main
`e1cfa8546b92d60aed5f187714a7aa304f3e1864`. Git verifies the user-managed Phase D
merge and its unchanged C/D foundation. The official PRADAN Tools-1.1 archive is
now obtained, hash/integrity checked and boundedly inspected; its selected source
and three CALDB products match pinned public candidates. This establishes source
identity, not compatibility with the generating pipeline. See the
[D.1 evidence report](SOLEXS_PHASE_D1_REPORT.md),
[fourteen-resource audit](../data/manifests/solexs_phase_d1_requirements.json),
[official source/member provenance](../data/manifests/solexs_phase_d1_evidence.json)
and [next exact clarification request](SOLEXS_PHASE_D1_AUTHORITY_REQUEST.md).
Phase E historical acquisition remains **BLOCKED** by pipeline-1.1 absolute
clock, LC bin/continuous-GTI/exposure policy and approved correction/HK/response
compatibility. D.1 is an evidence checkpoint awaiting authoritative clarification;
its main integration remains the user's decision.
No Aditya dataset, model, full alignment or UI work has started; GOES is preserved.

Previous storage update: **2026-10-01**, local `main`, after approved fast-forward
integration of `data/solexs-ingestion` at
`351482dc11aa75d2140d521828d0a24702765ad6`.
Pre-integration `main`: `278011ce27796781db873cd8d40578e1584e81d3`.
Archive foundation: `6b8eb17`; metadata portability: `510f890`.
Project root: `SolarJEPA` (formerly `isro`). Local integration was authorized;
remote approval was pending at that checkpoint. The October 2 fetch observes
that state and the user-managed AGENTS.md PR already integrated on origin/main.

This file owns stage status, blockers, completion criteria and task priority.
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) uses the same stages and
describes how to execute them. [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) owns
the proposed experimental protocol. [VALIDATION_REPORT.md](VALIDATION_REPORT.md)
is the historical foundation checkpoint. Current storage evidence is in
[SOLEXS_FOUNDATION_VALIDATION.md](SOLEXS_FOUNDATION_VALIDATION.md); it supersedes
the prior import failure and archive absence without rewriting past results.

Two user-acquired L1 v1.1 SoLEXS ZIPs for July 1 and 3, 2024 are registered by
local size/hash and central-directory listing. July 2 is missing from the obtained
collection, not asserted unavailable mission-wide. These are intake samples,
not the training dataset. Bounded Phase C inspection establishes all eight complete
gzip/FITS products, sixteen HDU DATASUM checks, native LC/PI cadence/missingness
and GTI correspondence. Official product/Unix definitions are documented;
absolute clock precedence, LC bin/GTI policy and correction/response applicability
remain unresolved. Phase D observes a 0-based PI / 1-based candidate RMF channel
discrepancy and residual LC-band differences; no candidate is approved or applied.
The user's July 2 authenticated catalogue search returned "File not found";
mission availability/reason remain UNKNOWN. The July 1 catalogue search returned
one AL1_SLX daily ZIP and no separate HK; its accompanying-downloads route shows
only tools/manual/updates, with no HK. These are attributed observations of those
searches/routes, not global HK absence or a clock repair policy. Normal installed
imports and seven CLI help checks pass; the original GOES files and saved artifacts
remain unchanged. A user-installed untracked Paperclip skill is preserved outside
the D.1 commit; it is not a scientific or milestone dependency.

## Status rules and audit boundary

- **NOT STARTED:** the research-stage outputs have not been implemented or run.
  A proposal, configuration, literature note or paper outline is not execution.
- **IN PROGRESS:** substantive partial outputs exist, but some completion
  criteria remain unmet. Partial NOAA work does not complete an Aditya stage.
- **BLOCKED:** the active stage cannot produce its required outputs until an
  identified access, evidence or authorization gate is resolved.
- **COMPLETE:** all mandatory outputs exist, appropriate tests pass, and a
  documented reproduction verifies them. Claims must match the tested scope.
  Optional experiments may be omitted only through a recorded scope decision.

No whole stage is COMPLETE. The existing reference-data functions
and artifacts have useful verified evidence, but they do not constitute the
proposed Aditya benchmark or an independently reproduced research pipeline.
Stages are research deliverables, not percentages of files written. Stage 9 is
cross-cutting and starts early; the Stage 7 development evaluator must be ready
before baseline tuning, even though final evaluation occurs later.

The preceding documentation-only audit read all tracked project files, the five-commit history, and relevant
ignored local data, metadata and EDA artifacts. Third-party virtual-environment
contents were excluded except for installation diagnostics. No archive access
was retested, no data were downloaded, and no models were trained. The recorded
PRADAN access check and literature screening remain dated **2026-09-29**.
Only this tracker, the implementation plan and README changed in that audit.
The subsequent approved storage milestone adds local registration, installation
repair, portable generated identifiers and tests; no member payloads are read,
no data are acquired, and no model work is performed.

## Stage table

| Stage | Research deliverable | Status | Evidence and remaining gate |
|---|---|---|---|
| 0 | Research question and scientific scope | IN PROGRESS | Research, literature, novelty and experiment proposals exist; scope/protocol approval and full-method review remain. |
| 1 | Data acquisition and validation | BLOCKED | Six verified NOAA files and two completely inspected SoLEXS ZIPs; official product definitions and native adapter verified, absolute timing/QC/calibration remain gated. |
| 2 | Dataset construction, preprocessing and leakage-safe splits | IN PROGRESS | P1 contracts, causal windows/support purging and split manifests tested on synthetic/reference data; final Aditya dataset, labels and benchmark splits remain gated. |
| 3 | Classical/statistical baselines | IN PROGRESS | Six fixed point comparators and training-only fits verified by P1 infrastructure smokes; real benchmark and ARCH/GARCH diagnostics remain deferred. |
| 4 | Supervised deep-learning baselines | NOT STARTED | LSTM/TCN/Transformer proposed; no implementations, profiles or trained controls. |
| 5 | SolarJEPA implementation | NOT STARTED | Proposal JSON and design only; no encoder, predictor, EMA target or decoder. |
| 6 | SolarJEPA pretraining/training | NOT STARTED | No training runner, checkpoints, run manifests or learning curves. |
| 7 | Forecasting evaluation and flare-warning evaluation | IN PROGRESS | P1 trajectory and supplied-label event metrics have hand-calculated tests; scientific labels, calibration and final benchmark evaluation remain gated. |
| 8 | Ablations, uncertainty and physics-informed experiments | NOT STARTED | Conditional protocols exist; no ablation runs, calibration or validated physical constraint. |
| 9 | Reproducibility and robustness validation | IN PROGRESS | P1 portable identities, code/package parity, deterministic reruns and exclusive atomic records verified; independent environment reproduction and dependency warning remain. |
| 10 | Paper-ready results, figures and documentation | NOT STARTED | Paper outline and reference EDA figures exist; no research results or result-backed manuscript. |

## CURRENT_STAGE, NEXT_STAGE, BLOCKERS, NEXT 3 TASKS

**CURRENT_STAGE = 1 — Data acquisition and validation (BLOCKED).** This is the
active scientific bottleneck after the initial reference foundation. Stage 0
still has open approval/review items; Stage 2 and Stage 9 have partial foundation
work. Nothing authorizes skipping those gates or proceeding to training.

**NEXT_STAGE = 2 — Dataset construction, preprocessing and leakage-safe splits.**
It can advance on Aditya only after the Stage 0 scope gate and Stage 1 validated
extraction gate. Immediate Stage 9 maintenance is a prerequisite for trusting
the documented workflow, rather than a move directly to model development.

**BLOCKERS**

| ID | Blocker | Affected work | Resolution evidence required |
|---|---|---|---|
| B1 | Samples, official guidance and pinned candidate RMF/ARF/correction resources exist; mission compatibility, HK, data-use review and holdings remain unresolved. | Stages 1–8, Aditya-specific parts of 9–10 | Approved tools/CALDB compatibility, channel-index rule and correction workflow; matching HK if required; separately reviewed historical acquisition. |
| B2 | Native structure/missingness is validated, but clock-card precedence, LC bins/NUMBAND, continuous GTI/exposure and physical quantities are unresolved. | Stages 1–2; physical/fusion extensions | Version-applicable timing/quality/exposure policies and numerical validation against approved corrected reference products. |
| B3 | Research scope, target definitions, acquisition expansion and training budget have not received the requested next approval; dates and event sufficiency cannot yet be frozen. | Completion of Stage 0; dataset/model/training gates | Recorded scope decision, coverage/event precision audit, exact split manifest and approved bounded pilot. |
| B4 (local symptom resolved) | Hidden editable `.pth` recurred; a normal non-editable installation removes that dependency. Its recurring flag origin remains unknown. | Local CLI gate resolved; independent reproduction remains Stage 9 work. | Installed imports and six CLI help tests pass without `PYTHONPATH`; fresh independent environment still required. |

Conditional gates are not blockers to a narrower SoLEXS-only study: ASPEX overlap,
valid response-based physics, X+ event sufficiency and a Qwen compute profile are
all missing. Drop or defer those claims if their evidence fails. The provenance
transition and dependency warning below are reproducibility gaps to resolve,
not evidence of corrupted telemetry.

**NEXT 3 TASKS — current scientific decisions and separately gated future work**

Immediate checkpoint action: fresh integration-readiness audit of corrected P1
on its preserved feature branch.
Integration requires explicit authorization. The following scientific work
remains separately gated; P1 does not resolve its evidence requirements.

1. **Obtain version-applicable mission guidance and authenticated resource inventory.**
   Resolve 1.1 clock/date/MJD precedence, LC bin/NUMBAND and continuous GTI/exposure
   rules; identify an approved tools/CALDB and correction-state policy. Use the
   Phase D prerequisite plan; official sizes and legacy HK availability are UNKNOWN.
2. **Validate a bounded compatible correction/calibration pilot after that evidence.**
   If the approved workflow requires HK, obtain matching July 1/3 SDD2 HK and
   coefficients; resolve PI/response channel indexing, gain provenance, units,
   quality/missingness and numerical reference agreement. Do not substitute
   filename/date agreement for compatibility.
3. **Review subsequent acquisition separately after authoritative gates pass.**
   Historical acquisition is BLOCKED until the scientific gates pass. Then review
   a bounded paired selection, catalogue gaps, storage and a dataset contract.
   No July 2 filling, full alignment, final dataset or model work is authorized now.

The October 1 storage checkpoint stopped on local `main` after integration
verification, preserving `data/solexs-ingestion`, with remote approval pending
at that time. That is historical; Phase C is now merged and its science branch
is preserved. Phase D uses its own published milestone branch. Phase C's
authority-first decision and official-source reconciliation are recorded.
Remaining scientific policies and later acquisition/dataset/training
tasks and integration into main remain separately gated.

## Historical pre-storage audit evidence and discrepancies

The following audit describes revision
`0f1265c047f0c2c6b5749b17b396cea4caa3c6c8` before the storage milestone.
Its archive absence/import failures are historical; current evidence is linked
above. Original reference measurements and retrieval facts are preserved.

### Repository and history

| Commit | Verified scope |
|---|---|
| `3bc443e` | Repository scaffold, ignores, licensing and initial README. |
| `aeabb63` | Research/data/literature/novelty/experiment/paper plans. |
| `65a0fb8` | Bounded public NOAA downloader, sample manifest and retrieval record. |
| `5e3e7b5` | Metadata inventory, NOAA adapter/preparation/EDA and tests. |
| `0f1265c` | Validation checkpoint, dependency pins and proposal configurations. |

Local `main` and the cached `origin/main` reference point to the audited revision.
`origin` is configured for `Neal-Salian/SolarJEPA`. No fetch was used to establish
current server state, and no push is part of the audit. There are no model,
training or evaluation modules, train/evaluate entry points, checkpoints or
model weights in the inspected project. Empty data/result placeholders do not
prove stage execution. Raw data, processed data, generated results and `.venv`
are ignored; no science files or weights are Git-tracked.

### Real data and generated artifacts

The six files in [noaa_sample.json](../configs/data/noaa_sample.json) are official
GOES-16 XRS science L2 v2-2-1 external references over
`[2024-07-01T00:00:00Z, 2024-07-04T00:00:00Z)`.

| Local output | Measured audit evidence | Interpretation |
|---|---|---|
| Three `avg1m` raw NetCDF files | 874,906 bytes; 4,320 rows; 60-second cadence; no absent grid rows | Real reference extraction, not an Aditya corpus. |
| Three `flsum` raw NetCDF files | 127,679 bytes; 94 state rows; 28 IDs; 27 observed peaks (25 C, 2 M, 0 X); 21 complete start/peak/end groups | Descriptive catalogue grouping; no forecasting labels. |
| All six raw files | **1,002,585 bytes**; every size/hash matches both per-file manifests | Immutable local reference sample verified. |
| Aditya products | **0 files, 0 bytes** | No SoLEXS/ASPEX validation or overlap evidence. |
| `data/processed/noaa_reference.parquet` | 261,174 bytes; fresh in-memory extraction equals saved frame | No windows, normalization, imputation or partitions. |
| Parquet sidecar / `results/schema.json` | Current source/processed hashes match; all six saved schemas equal current inspections | Local provenance and schema checked. |
| `results/noaa_reference/summary.json` and four PNGs | Fresh descriptive summary matches; figures visually inspected | Reference EDA only, no forecasts or paper-result figures. |

XRS-A has 2,267 valid rows and XRS-B 4,318 under channel-specific electron/status
quality masks. Longest unavailable runs are 254 and 2 minutes respectively;
these are quality exclusions rather than missing timestamps. Backward
log-derivative valid pairs are 2,170 and 4,316. No imputation, scaler fitting,
cross-instrument alignment or fitted statistical model has been performed.
The selected three days and two M peaks cannot support rare-event skill claims.

### Current verification

Read-only checks on the audited revision:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/preprocess.py --help
git ls-files '*.nc' '*.parquet' '*.fits' '*.cdf' '*.pt' '*.ckpt' '*.safetensors'
git check-ignore data/raw/noaa/sci_xrsf-l2-avg1m_g16_d20240701_v2-2-1.nc data/processed/noaa_reference.parquet results/noaa_reference/summary.json .venv/bin/python
```

- Pytest: **26 passed, 1 dependency RuntimeWarning**, 2.39 seconds. Tests use
  artificial I/O/schema fixtures, not artificial scientific results.
- `pip check`: **no broken requirements**. A sandbox pip-cache warning also
  appears; dependency consistency does not establish successful package imports.
- Normal `import solar_flare_jepa` and the displayed CLI help command:
  **FAIL**, `ModuleNotFoundError`. The editable `.pth` points to the correct
  existing `SolarJEPA/src` but has macOS `UF_HIDDEN` set. Python 3.13
  `site.addpackage` explicitly skips hidden `.pth` files. Pytest's
  `pythonpath = ["src"]` explains why unit tests pass. Why the flag is present
  again after the historical repair has not been established; nothing was fixed
  in this audit.
- With explicit `PYTHONPATH=src` **for diagnosis only**, verified manifest
  selection, `read_goes`, event reading, summary functions and all six schema
  inspections succeed. `pandas.testing.assert_frame_equal` verifies the saved
  Parquet's contents; normalized summary fields equal the saved JSON exactly.
  This proves component/data consistency, not normal CLI reproduction. No
  generated file was overwritten, and byte-identical regenerated Parquet/PNG
  output was not tested.
- Python 3.13.3/macOS 26.3 arm64 is the only environment checked here. The
  NetCDF4 `numpy.ndarray size changed` warning remains unresolved. No fresh
  environment install, CI, Linux/T4/Colab/Kaggle or GPU profile was performed.

### Provenance transition

The current acquisition config SHA-256 is
`b0552fa53ce837da4337fb2b355ab7ddbb87f27b77156acd9c9229d970e35101`.
[noaa_retrieval.json](../data/manifests/noaa_retrieval.json) records
`fd0253e0b15c4dadfb3384d28cc9d39849cd5a46bba99f82974dc9ce120dccda`.
Removing only each entry's `bytes` and `sha256`, then serializing with
`json.dumps(spec, indent=2) + "\n"`, reproduces the recorded digest exactly.
This establishes consistency with the manifest **before** measured values were
pinned; all individual raw hashes agree. That transition is not explicitly
versioned in the retrieval record. Preserve its original times/`fetched` fields
when clarifying provenance; do not overwrite it with a new fetch claim.
The processed sidecar already matches the current pinned manifest.

## Stage 0 — Research question and scientific scope

**Status: IN PROGRESS**

- **What already exists:** six falsifiable research questions, SoLEXS-first
  recommendation, continuous versus onset targets, skeptical novelty analysis,
  baseline/uncertainty/leakage design and proposed CPU/T4 budgets.
- **Evidence/files:** [RESEARCH_PLAN.md](RESEARCH_PLAN.md),
  [LITERATURE_NOTES.md](LITERATURE_NOTES.md), [NOVELTY.md](NOVELTY.md),
  [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md), [PAPER_PLAN.md](PAPER_PLAN.md),
  [core_proposal.json](../configs/experiments/core_proposal.json).
- **What is missing:** recorded next-phase scope approval, full-method/code
  review of the strongest JEPA/SSL/solar comparators, empirical event-sufficiency
  and calibration findings needed to freeze the protocol. Many literature entries
  explicitly report abstract-level screening, not reproduction.
- **Dependencies/blockers:** B1–B3; physical and generative terminology is
  conditional. Data-informed revisions may narrow targets or remove extensions.
- **Exact completion criteria:** an approved, versioned scope specifies primary
  task/estimand, RQs and falsifiers, conditional exclusions, baseline/tuning
  budgets, target definitions and go/no-go rules; full methods of mandatory
  comparators are reviewed; Stage 1 feasibility findings support that scope.
  Record the approval and resulting document/config revision. No unearned
  physics, MHD, generation or superiority claim remains.
- **Next actions:** approve the narrower study, complete comparator review and
  resolve data-dependent decisions after the first real sample. Keep exact split
  dates and physical loss conditional until evidence exists.

## Stage 1 — Data acquisition and validation

**Status: BLOCKED**

- **What already exists:** manual registered-acquisition instructions; bounded,
  tested public NOAA downloader; pinned six-file sample and retrieval record;
  NetCDF/FITS/CDF metadata inventory; real NOAA extraction and EDA; canonical
  SoLEXS archive storage and two locally verified ZIP identity/listing records.
  Phase C adds complete member inspection, native LC/GTI/PI access and official
  definition/release reconciliation, with explicit unresolved policy states.
- **Evidence/files:** [DATA_DOWNLOAD.md](DATA_DOWNLOAD.md),
  [DATASET_CARD.md](DATASET_CARD.md), [VALIDATION_REPORT.md](VALIDATION_REPORT.md),
  [download.py](../src/solar_flare_jepa/data/download.py),
  [inspect.py](../src/solar_flare_jepa/data/inspect.py),
  [storage.py](../src/solar_flare_jepa/data/storage.py),
  [solexs.py](../src/solar_flare_jepa/data/solexs.py),
  [SOLEXS_SCIENTIFIC_VALIDATION.md](SOLEXS_SCIENTIFIC_VALIDATION.md),
  [DATA_STORAGE.md](DATA_STORAGE.md),
  [aditya_inventory.json](../data/manifests/aditya_inventory.json),
  [test_download.py](../tests/test_download.py), pinned manifests and local
  artifacts enumerated above. FITS/CDF inspection is metadata-only.
- **What is missing:** product-compatible full responses/HK, accepted absolute
  clock/GTI/bin policy and calibrated adapter, authenticated broader holdings and
  data terms review; matching ASPEX products if retained. Native coverage/expanded
  bytes/cadence/gap statistics are now measured. No anonymous
  Aditya API or sample was verified in the previous investigation.
- **Dependencies/blockers:** B1 and B2; broad acquisition remains gated by B3.
  Authentication must be completed through the official route, never bypassed.
- **Exact completion criteria:** obtain a permitted modest real interval and
  official definitions/calibration; version a credential-free inventory with
  URLs/product IDs, hashes, sizes, times, levels/versions and rights; implement
  tested documented clock/quality/calibration extraction; verify numerical
  values against an official reference; report measured coverage/gaps/units and
  enumerate feasible larger holdings with estimated volume. Record ASPEX
  inclusion or evidence-based deferral. Reproduction from supplied raw products
  must succeed without guessing fields, clocks or counts-to-flux conversion.
- **Next actions:** review Phase C; resolve the explicit scientific policy and
  calibration requirements before separately authorizing dataset/acquisition work.

## Stage 2 — Dataset construction, preprocessing and leakage-safe splits

**Status: IN PROGRESS** — reference preprocessing and P1 mechanical contracts.

- **What already exists:** NOAA quality-aware Parquet preparation with masks,
  source identifiers, bin start/end, log flux and gap-aware backward derivative;
  sidecar hashes, descriptive event grouping, chronology/purge design; P1
  immutable contracts, raw-first partitions, causal windows/lookback/maturity
  support and synthetic supplied-group purging with retained/excluded manifests.
- **Evidence/files:** [goes.py](../src/solar_flare_jepa/data/goes.py),
  [preprocess.py](../scripts/preprocess.py), [test_goes.py](../tests/test_goes.py),
  [test_eda.py](../tests/test_eda.py), [noaa_eda.json](../configs/data/noaa_eda.json),
  local Parquet/sidecar; [P1 checkpoint](P1_IMPLEMENTATION_REPORT.md) and
  `forecasting/contracts.py`, `splitting.py`, `windows.py` with adversarial tests.
- **What is missing:** calibrated Aditya dataset, causal synchronization,
  approved real-data feature/label definitions, transformations and adapters,
  scientific event groups and frozen benchmark support/partition choices.
  `core_proposal.json` has `data_manifest: null` and `utc_boundaries: null`.
- **Dependencies/blockers:** Stage 0 protocol and Stage 1 extraction gates;
  B1–B3. Catalogue state readers do not implement warning labels.
- **Exact completion criteria:** a versioned Aditya dataset and source/feature
  metadata reproduce from raw files; freeze explicit chronological train/tune/
  calibration/test UTC boundaries, eligible origin IDs and independent-event
  counts. Full feature/history/target/label-maturity support stays in its
  partition; straddling/overlapping event clusters are purged. Tests verify
  future perturbations cannot change earlier features, causal bin joins,
  gap/unknown-target handling, train-only fitted transforms, no support/event
  leakage and deterministic manifest hashes. Publish coverage/exclusions and
  event-precision assessment without examining held-out model performance.
- **Next actions:** approve a real-data adapter/contract after authoritative validation; select
  primary history/horizon through cheap development-only screening, then freeze
  the benchmark before any learned model sees its data.

## Stage 3 — Classical/statistical baselines

**Status: IN PROGRESS** — P1 mechanics only.

- **What already exists:** fixed persistence, unique-training-period mean,
  causal trailing mean, drift, AR(1) with intercept and direct ridge; explicit
  transform/fit/predict contracts and matched synthetic/reference predictions.
- **Evidence/files:** [P1 checkpoint](P1_IMPLEMENTATION_REPORT.md),
  `forecasting/baselines.py`, `test_baselines.py`; baseline/volatility rationale
  remains in [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md). ARCH/GARCH has not been fit.
- **What is missing:** approved real benchmark, training-only adequacy/residual
  diagnostics, conditional-variance comparisons and probabilistic controls.
- **Dependencies/blockers:** Stage 2 frozen benchmark, approval of pilot compute,
  Stage 7 tested development metrics and Stage 9 run provenance.
- **Exact completion criteria:** all mandatory cheap baselines produce saved
  out-of-sample development forecasts from resolved configs with unit/transform/
  alignment tests and reproducible metrics. Diagnose mean dynamics and
  heteroskedasticity on training-only positive log differences/residuals; run
  constant-variance versus ARCH/GARCH where defensible, reporting convergence,
  parameter adequacy and path-based probabilistic scores. A documented failed
  applicability gate is acceptable evidence, not a forced flare-class fit.
  Record costs and chosen settings; leave final test sealed until Stage 7.
- **Next actions:** review P1, then approve benchmark/diagnostic decisions
  after the scientific data gates. ARCH/GARCH remains secondary variance work.

## Stage 4 — Supervised deep-learning baselines

**Status: NOT STARTED**

- **What already exists:** small LSTM, causal TCN and supervised patch
  Transformer design; optional GRU substitution and matched-budget policy.
- **Evidence/files:** [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md),
  [RESEARCH_PLAN.md](RESEARCH_PLAN.md); no neural source or executable config.
- **What is missing:** numerical-model implementations, masks/quantile heads,
  training/checkpoint harness, runnable configs, profiles and repeated controls.
- **Dependencies/blockers:** Stages 0–3 gates, development evaluator and run
  provenance; approved CPU/T4 pilot profile before substantive training.
- **Exact completion criteria:** the retained LSTM/TCN/Transformer subset
  implements a shared forecast API and passes causal/mask/shape/transform tests;
  measure actual parameters, peak memory and runtime. Complete bounded tuning
  on the fixed benchmark, then at least three seeds for retained neural controls,
  storing configs/RNG/checkpoints/per-origin predictions and tuning results.
  Include the exact supervised backbone used to compare JEPA; no test-based
  tuning. Record any evidence-based subset reduction explicitly.
- **Next actions:** build the reusable supervised harness after cheap controls
  and profile the smallest viable models before choosing repetitions.

## Stage 5 — SolarJEPA implementation

**Status: NOT STARTED**

- **What already exists:** masked temporal patch/context encoder, EMA target,
  latent predictor and ordered quantile decoder proposal: width 128, 3 layers,
  4 heads, 5-minute patches; target 1–3M parameters, not yet measured.
- **Evidence/files:** [jepa_proposal.json](../configs/model/jepa_proposal.json)
  says `proposal_only_not_executable`; architecture in research plan. No JEPA
  modules, loss implementation or learned representation exists.
- **What is missing:** encoder/predictor/decoder/EMA/loss code, runnable model
  configs, collapse diagnostics and inference/checkpoint tests.
- **Dependencies/blockers:** validated Stage 2 input/target contract, reusable
  Stage 4 backbone, full comparator review and explicit implementation approval.
- **Exact completion criteria:** implement the approved minimal JEPA; tests
  prove stop-gradient targets, correct EMA updates, train-only target support,
  no future inputs at inference, mask/shape handling, ordered quantiles,
  checkpoint round trips and logged latent variance/effective rank. A bounded
  approved smoke/profile verifies gradients, finite losses and measured memory/
  parameters. Plain JEPA must run without physical/fusion extensions. No trained
  research result is required for this implementation stage.
- **Next actions:** reuse the supervised patch backbone; isolate latent
  pretraining and forecasting heads before adding any optional loss.

## Stage 6 — SolarJEPA pretraining/training

**Status: NOT STARTED**

- **What already exists:** proposed train-only SSL, frozen/fine-tuned heads,
  reconstruction or TS2Vec control, seeds `[17,29,43]` and capped pilot schedule.
- **Evidence/files:** [core_proposal.json](../configs/experiments/core_proposal.json),
  [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md); no completed run artifacts.
- **What is missing:** approved runnable training/pretraining configs, optimizer/
  EMA/RNG resume support, profiles, checkpoints, learning curves and seeded runs.
- **Dependencies/blockers:** Stages 2, 4 and 5, approved runtime limits and Stage 9
  run manifests. No unlabeled calibration/test pretraining is permitted.
- **Exact completion criteria:** pass the approved short profile, log measured
  compute and freeze development-selected settings; train plain JEPA and required
  matched SSL/no-pretraining controls on train support only. Complete at least
  three retained-model seeds with resolved configs, complete state/checkpoints,
  convergence/collapse evidence, failure accounting and resume verification.
  Produce saved common-origin development predictions for Stage 7; an apparent
  gain on one seed is not a completion or superiority criterion.
- **Next actions:** authorize and execute only a bounded pilot after data/model
  gates; decide expansion from its measured runtime and stability.

## Stage 7 — Forecasting evaluation and flare-warning evaluation

**Status: IN PROGRESS** — P1 evaluators, scientific benchmark pending.

- **What already exists:** metric/estimand definitions, onset versus continuation
  distinction, common origins, event alarms, calibration-block and paired-block
  statistical protocol. P1 implements hand-checked native MAE/RMSE, persistence
  skill, training-scaled MASE, diagnostic correlation and actual-quantile pinball;
  separate supplied-label confusion/precision/POD/FAR/F1/TSS/HSS2/Brier scoring.
  EDA continues to count observed catalogue states/peaks only.
- **Evidence/files:** metric/split/inference sections of experiment plan,
  [DATASET_CARD.md](DATASET_CARD.md); [eda.py](../src/solar_flare_jepa/data/eda.py)
  explicitly performs no fitting, forecasting or training-label evaluation;
  [P1 checkpoint](P1_IMPLEMENTATION_REPORT.md) and tested `evaluation/` package.
- **What is missing:** scientific warning-label implementation and benchmark forecasts,
  calibration artifacts, locked thresholds, untouched-period/OOD scores, paired
  confidence intervals and reliable independent-event sample size.
- **Dependencies/blockers:** Stage 2 frozen labels/splits and saved predictions
  from Stages 3–6. The evaluator's development portion precedes training; final
  test scoring waits for the approved core/Stage 8 experiment selection to freeze.
- **Exact completion criteria:** hand-computed tests verify MAE/RMSE, pinball,
  interval coverage/width, Brier skill, TSS/HSS2, precision/recall/F1 and distinct
  FAR/FPR with undefined denominators handled as NA. Freeze alarm rules and
  tuning/calibration choices before final scoring. Produce auditable common-origin
  and event-level tables, confusion denominators/prevalence, lead time/false
  alarms per day, regime/horizon results, seed variability and paired dependent-
  data CIs. Evaluate the untouched later/OOD periods without tuning and state
  event-count limits. CRPS requires a declared distribution or suitable samples.
- **Next actions:** review the P1 mechanics; approve real definitions/protocol;
  after all protocol choices freeze, evaluate the final test once and save
  per-origin outputs sufficient to recompute every score.

## Stage 8 — Ablations, uncertainty and physics-informed experiments

**Status: NOT STARTED**

- **What already exists:** proposal for JEPA/no-pretraining/SSL controls,
  resolution/physics factorial, calibrated quantiles, optional particle/foundation-
  model/LLM tracks and response-consistent measurement model. Physics weight is
  zero in the current proposal; risk head is also gated.
- **Evidence/files:** research/experiment/novelty plans and JEPA proposal config.
  No actual constraint, calibrator, distribution, fusion model or ablation run.
- **What is missing:** supported physical loss and response residual validation,
  retained ablation implementations/runs, interval/probability calibration,
  temporal-dependence sensitivity, matched-capacity controls and measured costs.
- **Dependencies/blockers:** Stage 1 response/particle evidence, Stage 2 fixed
  dataset, stable Stages 4–6 models, development evaluator and separate approvals
  for extensions. Five marginal quantiles do not determine horizon-max risk.
- **Exact completion criteria:** run no-pretraining/SSL and equal-history/capacity
  multiresolution controls with repeated seeds; evaluate ordered quantiles and
  calibration on a separate chronological block, reporting conditional coverage
  and width. If physics passes, test documented units/exposure/response folding
  and applicable observation likelihood, then run plain/physics/resolution/both
  plus a conventional physical-model control. Otherwise record rejection and
  narrow the paper/title. Fusion requires identical eligible origins and causal
  particle arrival times. Qwen remains optional: matching task/tokenization,
  invalid-output accounting and memory/cost profile required if retained.
  Freeze all choices before final test use; make no exchangeable conformal
  guarantee under temporal shift or generative claim without trajectory samples.
- **Next actions:** validate baseline uncertainty first; isolate useful
  extensions one at a time on development data before committing the factorial.

## Stage 9 — Reproducibility and robustness validation

**Status: IN PROGRESS**

- **What already exists:** package metadata, macOS dependency pins, source hashes,
  bounded acquisition, tests, reproducible in-memory reference extraction,
  ignored artifacts and documented environment/known warning; installed import/
  CLI regressions, SoLEXS registration tests and relocated-root metadata checks;
  P1 finite configuration, dataset/config/split/source hashes, actual Git/package
  provenance, indexed atomic records and same-environment deterministic reruns.
- **Evidence/files:** [pyproject.toml](../pyproject.toml),
  [requirements-lock.txt](../requirements-lock.txt), [.gitignore](../.gitignore),
  all tests, manifests, sidecar and [P1 verification](P1_IMPLEMENTATION_REPORT.md).
  `experiments/` is an executable bounded registry; older proposal configs remain proposals.
- **What is missing:** clean independent environment reproduction/CI,
  neural optimizer/EMA/RNG/checkpoint resume provenance and approved robustness results.
  Historical sidecar identifiers remain machine-specific to preserve validated
  artifacts; future generated sidecars/EDA use repository-relative identifiers.
- **Dependencies/blockers:** B1–B3 for real-data/model robustness. The
  dependency RuntimeWarning needs assessment, not silent suppression. Linux/T4
  support and proposed VRAM/GPU-hour budgets are unmeasured.
- **Exact completion criteria:** from a fresh documented environment, normal
  imports and CLI tests plus pinned sample preparation/EDA succeed without
  implicit local state. Explain provenance transitions and warning disposition;
  verify immutable source/split/config identities, relative paths and source
  terms. For experiments, store revision/dirty diff, environment, all trials,
  seeds/RNG/optimizer/EMA states, checkpoints, predictions and logs; demonstrate
  checkpoint resume and metric reproduction. Complete at least one independent
  CPU reproduction and the chosen GPU platform profile; evaluate approved
  missingness, boundary/timing and temporally separated regime sensitivities
  without adapting on held-out outcomes. Exact bytes or numerical tolerances
  must be declared for each artifact; data and seeds alone do not guarantee
  bitwise GPU determinism.
- **Next actions:** retain the verified local CLI/provenance foundation; build
  integration/independent-environment checks before model experiments, then
  extend the same evidence contract to every run.

## Stage 10 — Paper-ready results, figures and documentation

**Status: NOT STARTED**

- **What already exists:** manuscript outline, minimum evidence list, novelty/
  limitations notes, dataset card draft and reference-data descriptive figures.
- **Evidence/files:** [PAPER_PLAN.md](PAPER_PLAN.md), [NOVELTY.md](NOVELTY.md),
  research/data docs; local NOAA EDA PNGs labelled as observations, not forecasts.
- **What is missing:** actual benchmark results/ablations/CIs, paper figures,
  finalized dataset/method reporting, result-backed manuscript and reproduction
  artifact review. No superiority, precursor or physics finding is established.
- **Dependencies/blockers:** mandatory Stage 0–9 deliverables; extension failures
  must lead to a documented narrower scope, not unsupported paper wording.
- **Exact completion criteria:** every table/figure regenerates from immutable
  predictions/metrics and identifies data period/model/settings; the manuscript
  includes fair baselines, at least three retained-model seeds, paired dependent-
  data CIs, uncertainty, onset/continuation separation, exclusions, compute,
  failure cases and all applicable ablations. An independent reproduction
  supports each numerical claim. Complete full-method related-work review and
  claim/rights audit; report negative/inconclusive findings. Label an underpowered
  study a pilot. Optional physics/LLM/fusion omissions are explicit. Submission,
  release and push remain separate user decisions.
- **Next actions:** retain the outline; draft result sections and create final
  figures only after evidence exists, then review claims against artifacts.

## Reconciliation and tracker maintenance

[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) now uses **Stages 0–10** exactly
as above. The former Phases 0–6 are historical labels, not a second execution
sequence. Its former “Phase 0 complete/stop” means only that the initial reference
foundation was built; it never completed Stage 1 Aditya validation, Stage 2 splits
or Stage 9 project-wide reproduction. The stale “no remote” initialization task
is retired because the repository and remote already exist.

Experiment-plan **Stages A–D** remain internal compute tiers (CPU screening,
single-seed tuning, repeated comparisons, sensitivity), not project stages.
Use “experiment tier A/B/C/D” when discussing them to avoid ambiguity.
Neither proposal JSON is an executable or approved training configuration.

For each future status change, record date/revision, passing verification,
artifact IDs/hashes, scope and unresolved failures here, and keep corresponding
implementation tasks aligned. Reopen a COMPLETE stage if later evidence breaks
its criteria. Do not infer progress from a commit message or an empty directory.
