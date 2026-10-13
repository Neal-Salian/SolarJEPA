# Phase 1 verification and review record

Date: 2026-10-13, Asia/Kolkata. This records executed readiness checks, not a
completed external experiment. The [audit](PHASE1_GOES_READINESS_AUDIT.md)
contains the verdict and scientific limitations. The
[portable evidence ledger](../data/manifests/phase1_goes_model_readiness.json)
contains exact input/checkpoint hashes and measured audit results.

## Executed checks

| Check | Observed result |
|---|---|
| Fetch/ref/worktree audit | Main equals origin/main; 13 worktrees inventoried; requested branch based on V1 and published with upstream |
| V1 data/contracts/scoring/provenance tests | 690 passed, 1 warning, 52.57 s |
| Existing external preparation/scoring/uncertainty tests | 67 passed, 1 warning, 2.54 s, on pinned external branch |
| Normal package installation | Task-local `.venv`; no-deps normal install; `pip check` passed |
| Installed-source provenance guard | Clean V1 executable source and installed distribution match; source fingerprint matches original strict run |
| CLI smoke checks | `run_v1_comparison.py --help` and `prepare_goes_training.py --help` exit 0; no run initiated |
| Checkpoint safety/integrity | Nine safe loads; expected shapes/dtypes, finite state and internal weight identities pass |
| Neural internal replay | First original 256-origin batch bitwise for all nine checkpoints; no target-encoder inference and no changed weights |
| Original normalization | Direct arithmetic on unique raw training support exactly matches saved statistics, counts and support identity |
| Classical internal replay | Saved state restored for 16 candidates without fit; 13 archived test arms checked on two origins, 12 bitwise, ridge within 1.78e-15 dex |
| Raw/prepared identity and temporal audit | 123 V1 + 31 January files verified; both 13-file acceptance outputs verified; zero raw overlap |
| January V1 window reconstruction | Saved native contexts/targets/grid/manifests and dataset/split identities reproduced exactly |

The inherited warning in both test runs is:
`RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility. Expected 16 from C header, got 96 from PyObject`.
It was not suppressed. Its cause and numerical impact remain UNKNOWN.

The task-local environment reads existing dependencies through a local `.pth`
file and installs this branch's package into its own site-packages. The original
environment is unmodified. Source tests inject this checkout's `src`, as configured
by pytest; the separate normal-import/installed-source check does not rely on that
injection. No declaration or lockfile changed. Historical exact SciPy,
statsmodels and arch versions are absent from the saved V1 envelope: available
host versions are not promoted into original training/runtime facts.

## Commands and audit methods

From the new worktree, with its qualified local environment:

```bash
.venv/bin/python -m pip install --no-deps --no-build-isolation --ignore-installed .
.venv/bin/python -m pip check
.venv/bin/python scripts/run_v1_comparison.py --help
.venv/bin/python scripts/prepare_goes_training.py --help
.venv/bin/python -m pytest -q tests/test_goes.py tests/test_goes_acquisition.py tests/test_forecasting_contract.py tests/test_forecasting_splits.py tests/test_forecasting_windows.py tests/test_prediction_context_causality.py tests/test_prediction_publication.py tests/test_evaluation_boundary.py tests/test_canonical_semantics.py tests/test_trajectory_metrics.py tests/test_v1_foundation.py tests/test_experiment_provenance.py tests/test_executable_source_provenance.py tests/test_loaded_source_provenance.py
```

From the existing external worktree at `f309921`, using its retained environment:

```bash
.venv/bin/python -m pytest -q tests/test_external_validation.py tests/test_external_config.py tests/test_external_preparation.py tests/test_external_flux.py tests/test_uncertainty.py
```

These are focused non-training suites. They do not include the neural training
tests or invoke the historical full comparison runner. The external tests prove
the sibling implementation's behavior, not integration into this new branch.
The complete repository suite was not run in this milestone.

Read-only Python audits additionally executed safe `TrainedJepa.load`,
`code_provenance(require_clean=True, require_installed_match=True)`, native
manifest SHA-256/size checks, unchanged V1 dataset/window construction, direct
log mean/std/count arithmetic and training-window enumeration. Neural replay
used only original internal-test contexts. Classical reconstruction populated
saved fitted fields in memory and forbade `fit`; no supported restore API is
claimed. Byte rechecks were repeated after these audits. Source/native
field references and exact results are preserved in the ledger.

To independently reproduce the input identity checks, supply separate V1 and
external storage roots, resolve each ledger's logical paths inside its declared
root, stream SHA-256 and compare byte lengths. Do not symlink external files
outside a root to bypass storage guards or relabel acquisition lineage. For
window reproduction, use the unchanged V1 `ForecastSpec` and raw-axis test-window
builder; compare contexts, targets, masks and grid to the pinned acceptance
artifacts. No fitting or model inference is needed for that comparison.

## Independent review

A fresh read-only reviewer checked the audit, ledger, protocol and plan against
actual source and retained inputs. The reviewer independently verified 200 byte
identities, all nine safe-load states and checkpoint/summary records, original
training normalization, and January context/target/grid/window reconstruction.
The reviewer did not invoke fitting, prediction or scoring and did not repeat
the specialist's bounded prediction replays or the 690/67-test suites; their
retained logs support those results.

Review identified and resolved three issues: a plan step could have begun code
before its readiness gate; deterministic points were described as medians; and
interval score lacked an exact formula/space declaration. The revised plan has
an explicit non-code scope/authorization gate and the protocol pins both point
interpretations and interval arithmetic. The reviewer rechecked the fixes and
returned no unresolved Critical, Important or Minor finding. The deliverables
are suitable for feature-branch publication; phase readiness remains
PARTIALLY_READY.

Direct NOAA PDF retrieval failed through the final reviewer's web tool, so the
reviewer did not independently reverify the specialist's official release-date
source check. The specialist's successful method opened NOAA's documentation
directory and followed its ReadMe link: the six-page document dated October 6,
2026, printed page 5, section 5, Table 4 directly lists releases 2-2-2 on October
6, 2026 and 2-2-1 on December 15, 2025. No current PDF bytes were saved, so the
older research-snapshot checksum is not attributed to that web response.
Operational validity, blindness, future adapter correctness and
external performance were explicitly left unqualified: no external results
exist to review. Descriptive bootstrap formulas are not empirical proof of
inferential coverage.

## Final preservation and publication

After the audits and review corrections, a fresh before/after SHA-256 comparison
found all 259 inventoried existing files unchanged, all pre-existing local/remote
refs unchanged, and all other 12 worktree statuses unchanged. A new fetch found
no unexpected remote divergence. The original two untracked items remain in
the original presentation checkout. This bounded preservation check does not
claim to hash every ignored file.

`git check-ignore -v` was executed in each owning storage root for actual
checkpoint/NPZ, native NetCDF and external context paths, plus this worktree's
audit scratch and environment. All are ignored by the expected rules. The new
ledger contains hashes, configuration, audit counts and compact provenance;
it contains no weights, scientific payload arrays or absolute user paths.
JSON semantic checks and local document-link validation passed.

Final staged whitespace and index/current-branch-history inspection passed.
Exactly four new documents and one provenance ledger are staged; no prohibited
raw/science/checkpoint payload is in the index or current branch history.
An explicit push to `research/goes-external-model-evaluation` follows the
verified commit. The final response reports the observed commit and remote equality
after those commands run, rather than embedding a self-referential commit hash
in this report. No PR or merge is authorized. The worktree, scratch audit evidence
and existing source artifacts are retained.
