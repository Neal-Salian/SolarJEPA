# Stable Baseline v0.1 release-readiness report

Audit started **2026-10-18**; final verification/publication **2026-10-19 (Asia/Kolkata)**. Scope: a controlled, local,
retrospective GOES/V1 research baseline. Integration branch:
`codex/stable-baseline-v0.1`, based on fetched `main=origin/main`
`1a4991da4dda9676caeb1d7e35a03408528c3188`. The delivered commit is the branch's
published Git HEAD; no release tag, PR, main merge or main push is authorized.

## Scope and component selection

The [audit and dependency map](STABLE_BASELINE_V0_1_AUDIT.md) identifies the exact
branch tips and worktrees examined. The [plan](superpowers/plans/2026-10-18-stable-baseline-v0-1.md)
records execution and validation. One selected prediction lineage was integrated
from `a4951516dc2094ceb246b016700d1483a808212b` in merge `4356611`.
The sibling time-series extension is composed from `5618bc4042d4a88b019504768772880cc15d2fcd`
and `abe4b79d2fe7549552b0a1f467be1cd949b652a7`; this does not select unrelated research branches.

The baseline includes the existing pinned NOAA GOES-16 science-product acquisition
and QC adapters, train-only normalization and chronological forecasting contracts,
six deterministic baselines, existing statistical comparators, trained V1 JEPA
variants and supervised controls, existing comparison evidence, and five pages:
Overview, Data Explorer, Time-Series Analysis, Model Results, Solar Flux Prediction.
Historical prediction uses 120 one-minute context bins to forecast 30 bins for
XRS-A and XRS-B in W/m². Presentation pages load May/June raw plots alongside
the separately pinned saved May–August time-series report; the neural prediction
page uses historical August 2024 inputs.

Scientific processing remains outside Streamlit. Original scientific modules,
configs, manifests, registries and saved outputs are preserved byte for byte.
New work composes UI views and adds setup, dependency/artifact preflight,
reference-replay verification, integration regressions and release documentation.
Inherited guarded SoLEXS inspection code and historical P2 smoke tooling remain
in the selected ancestry for compatibility; they are not stable release features
or authorization to execute experimental work.

## Fresh verification evidence

These checks were executed in this task; historical reports are separately dated.

| Check | Observed result |
|---|---|
| Fetched local main vs origin/main | Equal at `1a4991d`; no main edits |
| Main baseline suite | 166 passed, one existing warning, 39.22 seconds |
| Prediction integration before time-series composition | 1,239 passed, one existing warning, 120.13 seconds |
| Fresh isolated environment | Clean venv installed prediction lock plus compatible Astropy/cdflib; `pip check` passed |
| Four explicit GOES manifest identity checks | 31 May + 30 June + 31 July + 31 August = 123 files matched |
| Dashboard verifier before time-series composition | PASS; 61 native files, 87,840 minute rows, 17 pinned sources; offline and training-import guards |
| Composed dashboard UI suite | 23 passed, one existing warning; all five routes and offline guards |
| Original presentation reconciliation | PASS; 52 identities, 123 native files, 12 stationarity statistics (max discrepancy 2.282e-11), 422 score checks (max discrepancy 0) |
| Full V1 replay in fresh integration environment | PASS; nine checkpoints × 1,436 origins; every point and all five quantiles bitwise exact (max difference 0); raw contexts/masks/targets/support exact |
| Full release preflight | PASS; 123 native files, 222 artifact identities, all nine checkpoints; dependency pins matched |
| Final frozen-source full suite | **1,301 passed, one existing warning, 138.41 seconds**; no skips or failures |
| Independent reviews | [Scientific review](STABLE_BASELINE_V0_1_SCIENTIFIC_REVIEW.md) PASS; [technical review](STABLE_BASELINE_V0_1_TECHNICAL_REVIEW.md) PASS; all findings addressed |
| Normal installed package and CLI smoke | Model/GOES imports, both packaged registry JSON resources, storage/probe help and pip check passed |
| Loopback Streamlit runtime | HTTP 200 `ok` on port 18501; page behavior separately exercised by AppTest |

The acquisition CLI's verification mode selects `--manifest`, independently of
`--config`. An initial setup attempt before installing the local package failed
with ModuleNotFoundError; normal installation fixed it. An initial verify command
using `--config` checked the default July manifest repeatedly; the four explicit
`--manifest` checks above replaced that insufficient evidence. Neither attempt
changed inputs or reference outputs. Initial presentation reconciliation detected
a missing original `per_origin.json`; restoring its source-identical bytes
enabled the successful 422-check reconciliation above. A smoke command initially
used a nonexistent import name; the corrected module/model import passed.

One combined-suite attempt recorded **1 failed / 1,300 passed**: the UI recovery
message was edited after its module had loaded, and the executed-source guard
correctly refused a stale source identity in
`test_runner_publishes_verified_checkpoint_and_reproducible_bounded_native_scores`.
That test passed alone in a fresh interpreter (2.62 seconds). No provenance guard
was weakened. The final suite was restarted with a saved source-hash snapshot
and no further source edits; its completed result is reported above/below.

## Reproducibility and artifact custody

See the [run guide](STABLE_BASELINE_V0_1_RUN.md) for the exact environment,
restoration, preflight, regression/replay and loopback Streamlit launch commands.
This task installed a new CPython 3.13.3/macOS arm64 environment; this is the
verified platform, not a claim of cross-platform numerical identity. Original
older research locks conflict with Streamlit's Pillow/packaging constraints.
The stable lock extends the preserved dashboard-prediction locks rather than
combining incompatible lock families. CPU inference uses Torch 2.6.0. A final reinstall includes the reviewed UI recovery correction; the loopback smoke server was stopped after verification.

Only exact copies were placed in ignored paths in the new worktree: 123 daily
raw files, all nine V1 checkpoints, original summary, per-origin scores and prediction archive,
required dashboard artifact(s), and the time-series diagnostic payload. Each
copy matched its source SHA-256. Original worktrees, inputs and experiment
outputs were not replaced. Raw science, checkpoints and arrays are deliberately
absent from GitHub; a source clone alone cannot reproduce predictions. Custodians
must retain and restore the original bundles at their pinned relative paths.
Outside-root symlinks fail containment checks. Missing/mismatched artifacts are
release blockers; retraining or creating substitute reference arrays is not a
restoration procedure.

## Scientific interpretation and exclusions

**OBSERVED:** The integrated source preserves native QC/masks, causal minute
coordinates, the original forecasting spec and train-only normalization. See the
[scientific evidence](STABLE_BASELINE_V0_1_SCIENCE.md) and independent scientific
review for exact numerical reproduction evidence.

**OBSERVED in frozen artifacts and retained reports:** The experiment covers four
months of GOES-16; its August test set has 1,436 complete-case origins with overlapping
contexts. Archived research reports describe this restricted experiment, not
population-wide or prospective validation.

**INFERRED:** Reproducing saved forecasts supports software/checkpoint compatibility
for this historical experiment. It does not establish forecast skill on an
unseen period, superiority of JEPA pretraining, calibrated uncertainty or useful
operational warning performance. Seed-removal sensitivity makes pretraining
superiority inconclusive. The five output quantiles are marginal and nominal;
50%/90% bands are uncalibrated, not joint trajectory probabilities.

**UNKNOWN:** Operational data latency/availability parity, cross-platform exactness,
prospective skill, deployment reliability, event/onset probabilities, and physical
SoLEXS forecasting readiness. There is no generated flare label or invented
scientific quantity in this release.

Explicit exclusions:

- **V2 pilot:** guarded development/protocol work remains on its own branches;
  no pilot or real-data training ran during integration.
- **V3 research:** design/research work remains separate and is not a trained model.
- **Live inference:** NOAA near-real-time research is not integrated; historical
  bin-end availability is not a verified operational availability clock.
- **SoLEXS physical forecasting:** native inspection inherited from main does not
  resolve authoritative timing, exposure, response/channel mapping, quality or
  calibration applicability. No calibrated flux, alignment, event labels or
  SoLEXS model inference is claimed.

The existing NumPy/netCDF ndarray-size runtime warning persists on both original
main and the new environment. Native reads and numerical/identity checks are the
verification evidence; the warning remains disclosed. No GPU, Windows/Linux,
new observational acquisition or full retraining verification is claimed.

## Final repository safety observations

The final fetched `main` and `origin/main` still match `1a4991d`; the selected
prediction, V1 and time-series refs retain their original identities. Inspection
of all 36 pre-existing branch tips found 35 unchanged. The excluded
`codex/flare-onset-diagnostics` branch advanced independently from `16b975f` to
`a8128e9e85d6c36b7ebcd15c78ec73ead160f449` during this session (three event/diagnostic
commits); its worktree is now clean and synchronized with origin. No command in
this integration changed that branch, and those commits were not imported.
The primary checkout still has its two preserved untracked entries. Existing
worktrees and ignored originals remain retained. History inspection found no
prohibited raw science, checkpoint or prediction-array paths.

## Main integration requirements

1. Review the published integration diff, independent reviews, limitations and
   exact baseline scope. Retain original data/checkpoint bundles outside Git.
2. Resolve any material findings recorded in the final verdict below; run the
   documented preflight/replay in the receiving environment after restoration.
3. Obtain the user's **explicit approval to merge this feature branch into main**.
   Passing tests or this report does not grant that approval.
4. Immediately before any authorized merge, fetch and verify clean main and
   origin/main, inspect new divergence and rerun affected checks if the base moved.
5. Any agent push to main requires **separately explicit push authorization**.
   No PR is created by this task. Keep milestone branches/worktrees for traceability.

## Final verdict

**READY_FOR_CONTROLLED_RETROSPECTIVE_BASELINE.** The final full suite, mandatory
artifact/dependency preflight, original-score reconciliation, numerical replay,
five-page runtime checks and independent scientific/technical reviews pass.
There is no unresolved blocker for the named local historical baseline on the
verified platform. Source hashes were unchanged throughout the successful final
suite. The known native-library warning, external artifact custody requirement
and unverified other-platform/GPU behavior remain explicit limitations.

This is not operational, prospective-science or publication readiness. V2, V3,
live inference and blocked SoLEXS capabilities remain excluded. The sole remaining
action gate for merging this reviewed baseline into unchanged main is the user's
explicit merge approval, followed by the clean-main/origin recheck above. Any
push to main requires separate explicit authorization. Feature-branch publication
does not authorize either action.
