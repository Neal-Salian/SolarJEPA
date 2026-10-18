# Decision log

Verified **2026-10-18**. This is an index of implemented constraints, recorded
protocol decisions and unresolved choices, not fresh permission to execute them.
Evidence terms follow [project status](PROJECT_STATUS.md). Files named below
exist on the specified branch; they need not exist on main/the handoff branch.
Historical approvals authorize only their original bounded action. Human
identity, approval conversations and machine reservations cannot be authenticated
from a commit message or caller-supplied approval string.

| Decision / scope | Evidence and consequence |
|---|---|
| Preserve milestone branches; main integration is separately authorized | `AGENTS.md`, observed commit graph and origin refs. Current main `1a4991da4dda`; no automatic integration of V1/V2/dashboard/research. This delivery is documentation-only, feature-branch push, no PR/merge. |
| Store immutable raw science and large artifacts outside Git | `.gitignore`, `docs/DATA_STORAGE.md`, actual ignore checks. Commit reproducibility code/config/manifests, not ZIP/FITS/NetCDF/NPZ/PT, environments or credentials. Acquisition time is not registration time or filesystem mtime. |
| Keep Streamlit thin and scientific logic reusable | `AGENTS.md`; prediction branch `dashboard/prediction_page.py`, `dashboard/prediction.py`, `training/jepa.py`. Streamlit calls reusable loading/inference; future React/FastAPI is an architectural option, not authorized work. |
| V1 is retrospective continuous flux forecasting | `v1`: experiment/model configs, `forecasting/windows.py`, `training/jepa.py`, actual saved NPZ/summary. Two GOES channels; 120 one-minute context rows, 30 future leads, five marginal quantiles; complete-case quality support; train-only normalization and purged chronology. No live latency or flare-warning claim. |
| V1 original run remains frozen | Actual strict source `4a3f88227ce28dea0e885e68987282285963f38e`; `docs/V1_RESULTS.md` / scientific audit at `644648f7d555`. Nine checkpoints, seeds 17/29/43, saved August forecasts. New output names and distinct decisions for reruns; August is exposed, not an untouched holdout. |
| V1 superiority interpretation is limited | Fresh saved-loss replay: fine-tuned JEPA mean pinball 0.0392450927 dex vs supervised 0.0395002178; removing seed43 reverses difference. Arithmetic mean of seed losses, not an ensemble. Frozen JEPA worse here. Marginal quantiles are uncalibrated; no exact CRPS/joint generative distribution or physics result follows. |
| M2/M3 do not validate replacement inference | `research/v2-m2-statistical-validation`, `research/v2-m3-inference-remediation`; source/historical result payloads. M3 remains separate. Latest V2 code reports `DESCRIPTIVE_ONLY`, `INFERENCE_UNAVAILABLE`, `NO_VALIDATED_REPLACEMENT`; inferential fields null. |
| Latest V2 Protocol v1 resolves the older 17 decisions | `codex/v2-experimental-validation-readiness`: `docs/protocols/phase2_v2_development_v1.json`, accompanying Markdown, executable `experiments/v2_pilot_protocol.py`. G1 design ratified, G2 implementation done; old M5's unresolved register remains historical. G3 reservation pending activation, G4 **NOT_AUTHORIZED**, G5/test access outside scope. |
| A bounded G4 pilot has exact design/resource boundaries | Protocol pins 20 processes / 18 models, two seeds 1261866429/1291916211, shared SSL processes; May–July exposed development only. CPU float32, four threads, sampled worker+descendant RSS 2 GiB, total 7,200 s, zero retries/resume, at least 1 GiB free output space. Attempt ceilings sum to 13,800 s; completion within total budget is not guaranteed. Readiness is not approval. |
| Latest cancellation handling supersedes SIGINT-only instructions | Latest `8e9ce06407d5`, `docs/PHASE2_V2_G4_LIFECYCLE_SAFETY.md`, driver/lifecycle tests. INT/TERM/HUP cleanup; authenticated stop-only orphan recovery, no automatic resume or bare-PID recovery. SIGKILL/host loss remains uncatchable. Older bindings at `d07a407` are stale. |
| January external evaluation is retrospective and already exposed | `research/goes-external-model-evaluation`: frozen evaluation config, `data/manifests/phase1_goes_external_execution.json`, surviving six-file output bundle. One recorded bounded run at `26479e04f27bbd50fbe696cda7369c5074d2c0ee`; nine frozen neural checkpoints + 13 classical fits, no refit. Caller approval reference is a historical assertion, not reusable authorization. Confirmatory status UNAVAILABLE; primary sensitivity intervals include zero. |
| SoLEXS native agreement cannot clear scientific gates | `codex/solexs-scientific-integration`: `data/solexs_interface.py`, `solexs_integration.py`, `solexs_reference.py`, pinned release manifest. E1/E2/E3/E6 blocked; E4/E5 partial. `require_jepa_ready()` rejects scientific use. Tools/CALDB numerical reference agreement proves only the inspected relationships. |
| Provisional SoLEXS numerical pilot is not scientific JEPA | `research/solexs-provisional-sequence-modeling`: frozen config/code and manifest; inherited by current SoLEXS branch. `generic_masked_linear_not_JEPA`, unknown native units, 64 native-sample context/8 horizon/stride8, seed17/eight epochs. Original five-file bundle absent in inspected storage; recorded metrics are not freshly authenticated. |
| Presentation artifacts have separate scope | Prediction branch extends dashboard; classical time-series branch is separate. Final PPTX/PDF branch starts from old main and contains deliverables, not full app/model code. STL's imposed daily period is diagnostic; SARIMA has no fit/score, rubric requirement8 remains partial. |

## Unresolved decisions and required evidence

| Question | Required evidence / next decision |
|---|---|
| Activate G3 reservation and authorize G4? | Named owner's explicit bounded approval/window, exact current source/design/config/runtime/input identities and inactive-to-active reservation transition. Pending JSON has null owner/time and false execution/fitting/test release; approved file/output absent. Do not invent or infer consent. |
| Current G4 binding identity? | Audit at `8e9ce06407d5`: design `ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624`; config `a7ce71194dac05c7ac14e5a5fc09f478b7b6d88ad0744a97bc7c3c7af02a641b`; source `fbb17789683545fae55b8aa5c19085bd4dadf9cdb0d72922bdad37e8b6c567ee`; runtime `08e6f763ff8aa88d96a18ffcd076e996646b6546fcb5d69964d566b803c57ae4`. Recompute after relocation/environment/source changes; do not copy an old runtime as proof. |
| Which mission-approved SoLEXS clock/bin/response/exposure policy? | Applicable single-release authoritative reference: absolute UTC/card precedence, LC bin/GTI endpoints, causal availability, PI0..339 vs RMF1..340 mapping, detector/pipeline/epoch applicability, quality/deadtime/effective exposure and correction state. Physical quantity/targets/uncertainties/labels remain UNKNOWN. |
| Which additional SoLEXS products? | Matching July1/3 SDD2 HK only if required by the approved correction workflow; exact names/availability UNKNOWN. SDD1 LC/PI only if SDD1 science is requested. July2 missing from obtained collection does not prove mission-wide absence. Bulk acquisition and inferred timestamp/channel repair remain gated. |
| Recover provisional bundle or run a new pilot? | First ask its custodian/backups for the recorded five-file bundle and verify manifest hashes. New training needs separate scope and cannot be represented as recovering original evidence. |
| What constitutes next scientific confirmation? | A separately frozen temporal/model protocol, appropriate comparator/seed/statistical controls and approval. Neither reused August nor previously inspected January becomes blinded confirmation. No extra fitting/scoring follows automatically. |
| Operational warnings / calibration / physics / fusion? | Documented delivery timing and physical response/quality/labels, validated event decisions and uncertainty, supported physical losses and separate scope. No current operational warning or physics-informed result. |
| Portability and binary warning? | Fresh independent installation/platform checks and investigation of existing NumPy/netCDF ndarray-size warning. This audit did not repair it or establish numerical impact. |
| Broader integration/publication/frontend expansion? | User decision for each action after review of actual branch diffs/evidence. No authorization from readiness, status or this handoff. |

Historical reports remain unchanged. When a decision changes, record its date,
action-specific approval/evidence, exact revision and superseded scope here;
never rewrite older evidence as if the later decision existed then.
