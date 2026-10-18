# SolarJEPA — verified project status

Checkpoint: **2026-10-18 (Asia/Kolkata)**. Scope: recovery audit, no new science,
training, acquisition, integration or deployment. Read this with
[development handoff](DEVELOPMENT_HANDOFF.md), [recovery guide](RECOVERY_GUIDE.md)
and [decision log](DECISION_LOG.md).

**OBSERVED:** fetched origin; local `main` and `origin/main` both resolve to
`1a4991da4dda9676caeb1d7e35a03408528c3188`. Most development is published on
separate branches and is **not integrated into main**. The documentation branch
starts from that main and contains no forecasting/dashboard/V2 implementation.
The branch inventory in the handoff is the checkout map, not a merge plan.

Evidence labels: **DOCUMENTED** = authoritative documentation; **OBSERVED** =
files/code/execution inspected; **INFERRED** = interpretation; **UNKNOWN** = not
established. Historical test results are not fresh verification. No general
JEPA superiority, operational warning performance, calibrated SoLEXS flux,
physics-informed result or publication readiness is established.

## Verified workstreams

| Workstream | Implemented/completed checkpoint | Remaining scope or gate |
|---|---|---|
| Main / SoLEXS C–D.1 | Archive registration, bounded native FITS inspection, source/calibration identity manifests and offline readiness probes; D.1 merged through PR #4. | Scientific calibration/time-policy gates remain; main README/tracker predates the later branches. |
| P1 / P2 | Causal forecasting/split/evaluation/provenance mechanics; GOES training foundation and bounded neural smoke; dual-source contracts. | P2 does not establish a calibrated dual-source benchmark. |
| V1 | Completed retrospective GOES-16 May–August 2024 comparison; actual primary-storage bundle, 9 neural checkpoints and saved forecasts exist. `v1` tip `644648f7d555`; strict execution revision `4a3f88227ce28dea0e885e68987282285963f38e`. | Three fitted seeds, one test month, seed-sensitive JEPA/control difference, limited coverage/calibration and comparator qualifications; publication NOT_READY in historical scientific audit. |
| V2 M0–M4B | Separate model interfaces, statistical validation, inference remediation, protocol/feasibility and descriptive evaluation integration implemented on their branches. | M3 found NO_VALIDATED_REPLACEMENT; current V2 remains descriptive-only; experimental M3 methods stay on their research branch. Infrastructure is not a completed V2 experiment. |
| V2 M5 / latest experimental readiness | Restored May–July development input identities; nonfitting preflight/resource supervision and guarded pilot infrastructure. Latest `8e9ce06407d5`. | G1 protocol ratified; G2 implemented. G3 reservation/bindings prepared with owner reservation pending. **G4 NOT_AUTHORIZED**; no approved pilot execution or substantive V2 training result. |
| Research dashboard / prediction | Streamlit presentation branch; prediction branch `a4951516dc20` adds retrospective checkpoint-backed inference with reusable core logic. | Requires local raw files and authenticated artifact identities; missing inputs must produce explicit unavailable states. No live forecast service. |
| Presentations / time-series requirements | EDA/comparison, diagnostics/viva guide, and final PPTX/PDF exist on separate presentation branches. | Final deck branch descends from old main, not the newer dashboard/model code. Rebuild with its own tools only. |
| Independent GOES research | External data validation at `f309921d776c`; frozen January model evaluation at `a502d3fbf65f` completed bounded retrospective scoring. | Preserve frozen selection and reported negative/inconclusive evidence; no new fitting or additional period scoring implied. |
| Independent SoLEXS research | Phase E evidence, native sample-index pilot code/manifest and release-reference validation at `df88009ae87c`; original provisional pilot bundle not found locally. | Native numerical/reference agreement is not UTC, physical calibration or flare-warning validation. E1/E2/E3/E6 blocked; E4/E5 partially verified. |

## Scientific boundaries and next priorities

1. Preserve and securely back up local-only bytes listed in the recovery guide.
   A clone restores code/manifests, not the completed run or owner authorization.
2. Resume the intended branch at its recorded checkpoint, verify inputs and run
   the branch-specific nonfitting checks. Do not consolidate independent tracks.
3. V2: revalidate current runtime/source/config/data bindings, obtain the named
   owner's reservation and explicit bounded G4 authorization through the existing
   workflow. A pending template or a previous readiness result grants no approval.
4. SoLEXS: obtain authoritative evidence for UTC/bin/GTI policy, response/channel
   compatibility, quality/deadtime/live exposure, correction state and physical
   quantity/target/uncertainty definitions. Keep native sample indices and counts
   labelled as such; never substitute GOES classes or filename dates.
5. V1/research: use frozen saved evidence, report seed and temporal limits, and
   decide any additional controlled experiment separately. Physics, particle
   fusion, React/FastAPI, operational alerts and publication remain gated.

## Audit verification and historical context

Fresh base-tree suite (shared existing Python 3.13.3 environment, source tests in
new main-based worktree): **166 passed, 1 warning, 37.47 s**. Warning:
`numpy.ndarray size changed ... Expected 16 ... got 96`. Its cause/impact is
UNKNOWN; no environment repair was attempted. This is not a fresh installation
or a full test of every branch. Workstream checks are recorded in the handoff.

The previous 2026-10-03 stage tracker is preserved in
[main at the audit base](https://github.com/Neal-Salian/SolarJEPA/blob/1a4991da4dda9676caeb1d7e35a03408528c3188/docs/PROJECT_STATUS.md).
Its statements that model/UI work had not started describe that older scope,
not the verified multi-branch state above. Historical scientific reports and
plans are left intact; they require branch/revision context.
