# Development handoff

Snapshot **2026-10-18 (Asia/Kolkata)**; verified against fetched origin, worktree
status, source trees, commit graph, manifests and available local artifacts.
Use [status](PROJECT_STATUS.md) for scientific scope and [recovery](RECOVERY_GUIDE.md)
for commands. This handoff does not authorize another milestone.

## Branch/worktree checkpoint inventory

All listed non-handoff tips were equal to fetched origin at audit. Short SHAs
are exact 12-character unique commit prefixes in this repository; recover using
`git rev-parse origin/<branch>` and compare before acting. Local branch names
exist except the three rows marked remote-only. No branch was removed or merged.
`—` means no checked-out worktree, not lost work. Worktree labels are directory
basenames; the portable command `git worktree list --porcelain` supplies actual
locations without embedding personal paths here.

The checkpoint column records inspected branch contents, not a claim that every
branch suite was rerun. Most development descendants are absent from main.

| Branch (GitHub `origin/`) | Verified tip | Existing worktree label | Checkpoint / purpose |
|---|---|---|---|
| `chore/agent-instructions` | `7ce7f02cf3ad` | `—` | Historical agent guidelines; integrated ancestor of main. |
| `codex/developer-handoff-recovery` | `1a4991da4dda` | `developer-handoff-recovery` | This documentation-only worktree; base main `1a4991da4dda`; final delivery SHA is Git HEAD. |
| `codex/solar-flux-prediction` | `a4951516dc20` | `solar-flux-prediction` | Retrospective seed17 inference/replay + prediction page atop dashboard. |
| `codex/solexs-scientific-integration` | `df88009ae87c` | `solexs-scientific-integration` | Native preparation/readiness + pinned release reference cases; gates remain. |
| `codex/v2-experimental-validation-readiness` | `8e9ce06407d5` | `v2-experimental-validation-readiness` | Latest protocol/pilot guard/lifecycle fixes; G4 blocked on owner authorization. |
| `data/solexs-authoritative-evidence` | `1abed0f86c1c` | `—` | Official bundle/member identity manifests; integrated ancestor. |
| `data/solexs-ingestion` | `351482dc11aa` | `—` | Immutable archive registration/provenance; integrated ancestor. |
| `data/solexs-science-validation` | `bc364dca5b0c` | `—` | Native LC/GTI/PI inspection and tests; integrated ancestor. |
| `data/solexs-timing-calibration` | `cd6f9c5dd29f` | `—` | Offline timing/CALDB probes; integrated ancestor. |
| `data/v2-goes-development-restoration` | `8a9c98db66ec` | `—` | Restoration validator and pinned May–July data evidence; remote-only local ref. |
| `feat/p1-experiment-evaluation-foundation` | `595371190177` | `—` | Forecasting contracts/windows/baselines/evaluation and provenance tests. |
| `feat/p2-dual-source-training-foundation` | `656e540162c6` | `—` | GOES training foundation + bounded smoke; provisional SoLEXS gate. |
| `feat/v2-controlled-model-development` | `1826400ca9ca` | `—` | V2 model factory/interface source + contract tests; remote-only local ref. |
| `feat/v2-m0-m1-validation-foundation` | `fd7203bf9a2e` | `v2-m0-m1-validation` | Leakage/data/model controls and M0/M1 validation harness. |
| `feat/v2-m5-pilot-readiness` | `60718686f016` | `v2-m5-pilot-readiness` | M5 guarded preflight/supervision; historical unresolved decision register. |
| `feat/v2-model-evaluation-integration` | `2e3f87111ab7` | `v2-m4b-integration` | M4B guarded descriptive model/evaluation integration. |
| `feat/v2-training-protocol-feasibility` | `ac3428f910b3` | `—` | M4A protocol + synthetic feasibility tooling; not real training approval. |
| `main` | `1a4991da4dda` | `—` | Merged SoLEXS foundation; `data/solexs.py`, native-inspection tests; no later forecasting code. |
| `presentation/eda-model-comparison` | `660f46968355` | `primary` | EDA/comparison assets + executed notebook; primary hosts full V1 artifacts. |
| `presentation/final-time-series-presentation` | `a41c3dd803ea` | `final-time-series-presentation` | 20-slide final PPTX/PDF/assets/verification; old-main lineage. |
| `presentation/solarjepa-streamlit-dashboard` | `d718177a9a41` | `solarjepa-dashboard` | Offline research Streamlit app; reusable data/chart core. |
| `presentation/time-series-requirements-completion` | `abe4b79d2fe7` | `time-series-requirements` | Diagnostics/viva requirements and deployment inference replay. |
| `research/experiment-evaluation-foundation` | `805f1c3f8bc0` | `—` | P1 research/design proposal; no extra execution inferred. |
| `research/goes-external-model-evaluation` | `a502d3fbf65f` | `goes-external-model-evaluation` | Frozen January external evaluation runner/results; completed bounded scoring. |
| `research/goes-external-validation` | `f309921d776c` | `goes-external-validation` | Independent external dataset inspection and scientific research outputs. |
| `research/phase-e-solexs-validation` | `83b54435c163` | `—` | Phase E documentary/native scientific gate validation. |
| `research/solexs-provisional-sequence-modeling` | `3baad2bc2f8c` | `—` | Frozen native sample-index pilot code/manifest; original local bundle missing. |
| `research/v2-independent-validation` | `90571dfe1444` | `—` | Independent protocol design; superseded details need latest protocol reconciliation. |
| `research/v2-m2-statistical-validation` | `94cae59398e5` | `v2-m2-statistical-validation` | Reliability/statistical evaluator + local result evidence. |
| `research/v2-m3-inference-remediation` | `5e88f3a71092` | `v2-m3-inference-remediation` | Frozen inference reliability results; no V1 replacement. |
| `research/v2-m5-protocol-review` | `c872e4a2b8ea` | `—` | Independent protocol review/decision register; remote-only local ref. |
| `v1` | `644648f7d555` | `—` | Frozen V1 comparison and scientific audit; artifacts remain in primary storage. |

The handoff branch row records its creation base to avoid a self-referential
commit ID. Its delivery commit is `git rev-parse origin/codex/developer-handoff-recovery`.
The prior 14 worktrees are retained; the new handoff worktree is the fifteenth.
All prior linked worktrees were clean. The primary EDA checkout had exactly two
pre-existing untracked items: `.agents/skills/paperclip/SKILL.md` and
`docs/P1_FINAL_INTEGRATION_REAUDIT.md`. Neither belongs to this delivery or can be
restored from GitHub; preserve before any cleanup. No tracked changes were found.

## Ownership and exact continuation boundary

| Track | Completed at checkpoint | Next action; do not skip prerequisite |
|---|---|---|
| V1 / dashboard | Historical full run; current artifact identity/numerical checks; prediction replay. | Restore matching data/checkpoints, verify registry and replay, then launch locally. New training/comparisons require separate scope. |
| V2 latest | Ratified development protocol, guarded worker/supervisor, nonfitting reservation/bindings; interrupt/cancellation cleanup fixes. | Read `docs/PHASE2_V2_G4_EXECUTION_PREPARATION.md` and its superseding `docs/PHASE2_V2_G4_LIFECYCLE_SAFETY.md`. Revalidate inputs/runtime and obtain owner approval. Do not run a pilot from a pending file. |
| SoLEXS | Native sample/reference evidence and explicit fail-closed gates. | Resolve authoritative time/exposure/response/quality/quantity evidence; no UTC/flux/label fabrication. |
| External GOES | Data-validation track plus completed frozen January model evaluation. | Recover external and V1 bundles, verify frozen manifests; decide any new scientific period/fit separately. |
| Provisional SoLEXS | Frozen native-index numerical pilot manifest/code exists; original bundle not found. | Recover the original bundle from its custodian; report metrics as historical until verified. Never relabel it as physical forecasting. |
| Presentation | EDA, diagnostic/replay guide and final deck are separately published. | Use the branch for the intended deliverable; verify existing assets before rebuilding. |

No independent track is automatically approved for integration. The final-deck
branch is **not** a superset of prediction/V1 code: its parent is old main.
A handoff clone on default main will not contain the dashboard or V2 packages.

## Fresh verification performed for this handoff

- Base main-derived tree: `python -m pytest -q` — 166 passed, 1 existing warning.
- Normal installed core import and `register_aditya.py --help` /
  `probe_solexs_readiness.py --help` — exit 0 using existing primary environment.
  This is installed-environment availability, not a fresh install of each branch.
- V1: targeted foundation/statistical/JEPA/runner tests — 87 passed; all 123 raw
  daily files matched manifest bytes/SHA-256. Actual full-run summary, per-origin
  JSON, prediction NPZ and nine checkpoint identities remain present.
- Presentation verifier — PASS, 52 identities, 123 native files, 12 independently
  recomputed ADF/KPSS statistics (maximum discrepancy 2.282e-11), 422 score checks
  (maximum discrepancy 0), native context/target alignment and 8 saved executed
  notebook cells. Notebook execution itself was not rerun.
- Dashboard/prediction tests — 58 passed; dashboard verifier PASS (61 native
  May/June files, 87,840 rows, 17 pinned sources). Seed17 inference replay matched
  saved forecasts within `rtol=1e-6`, `atol=1e-15`.
- V2 nonfitting protocol/reporting/guard/bridge/descriptive tests — 113 passed.
  All 92 May–July files matched (27,280,082 bytes); 32 lifecycle evidence identities
  and nine historical V1 checkpoint hashes matched. No V2 fitting executed.
- SoLEXS — both registered original ZIPs and eight release/native report outputs
  hash matched; 93 interface/integration/reference tests passed. Scientific
  readiness remained blocked. Original provisional pilot bundle was not found.
- External research: preparation tests 55 passed (1 warning); frozen model
  adapter/metrics/pairing/runner tests 134 passed. All 31 January raw files, 13
  preparation files and six evaluation files matched their manifests; nonfitting
  preflight passed without inference or creating its output directory.
- Classical time-series tests: 53 passed (1 warning), deployment replay passed.
  Final-deck verifier passed with bundled document Python: 20 slides/notes/pages,
  nine scientific figures and two embedded actual dashboard captures. The research
  environment attempt lacked `pypdf`; no fresh visual/PowerPoint review was done.

The existing NumPy/netCDF ndarray-size warning appeared in base and some branch
checks. No clean-environment rebuild, GPU test, full all-branch suite, retraining,
new acquisition, calibrated SoLEXS derivation or operational service test was
performed. Exact branch commands and remaining local dependencies follow in the
recovery guide. Historical branch reports contain broader prior checks; those
are historical evidence, not rerun claims.

Delivery validation: all 32 branch checkpoint entries matched fetched refs;
all local branch counterparts matched origin. Markdown local links, shell-block
syntax, private-path/token-pattern scan and `git diff --check` passed. Independent
whole-handoff review approved; focused V2 review corrected M3 lineage wording and
older checkpoint test paths. New-branch tree/history and staged-path checks must
remain documentation-only at publication.
