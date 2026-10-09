# Provisional SoLEXS implementation and verification

**EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED**

Evidence date: 2026-10-09, Asia/Kolkata. Base
`83b54435c1634f7de0a3ec6494439c023a4d0296`; branch
`research/solexs-provisional-sequence-modeling`. Frozen execution commit:
`2f5b3b3cb66ea489ca8527dbdd6bd5fb5762b75b`. Stage A passed for numerical
recorded-value prediction only; baselines and limited neural training completed.
See [the self-contained scientific report](SOLEXS_PROVISIONAL_MODELING_REPORT.md)
and [new provenance manifest](../data/manifests/solexs_provisional_v1.json).

## Complete changed-file inventory

All milestone paths below are additions. No pre-existing source, tests, scientific
identity, benchmark, Phase E document/requirement, GOES config or instruction file
was changed.

| Path | Purpose |
|---|---|
| `src/solar_flare_jepa/provisional/__init__.py` | Separate numerical task namespace. |
| `src/solar_flare_jepa/provisional/sequences.py` | Native identities/masks, row ordering, finite-run windows and unique raw train statistics. |
| `src/solar_flare_jepa/provisional/baselines.py` | Five sample-index numerical comparators and identical-mask metrics/coverage. |
| `src/solar_flare_jepa/provisional/neural.py` | Generic affine CPU predictor, masked loss, validation-only selection and verified checkpoints. |
| `src/solar_flare_jepa/provisional/experiment.py` | Frozen config/input/code identities, staged execution and exclusive artifact publication. |
| `scripts/run_solexs_provisional.py` | Offline CLI with configurable immutable-data root and new output identity. |
| `configs/experiments/solexs_provisional_v1.json` | Exact two-product pins and frozen sample/optimizer settings. |
| `tests/test_solexs_provisional_sequences.py` | 16 order/missing/gap/split/provenance/normalization cases. |
| `tests/test_solexs_provisional_baselines.py` | Four prediction/causality/target-mask/coverage cases. |
| `tests/test_solexs_provisional_neural.py` | 27 training/mask/numerical/determinism/checkpoint cases. |
| `tests/test_solexs_provisional_experiment.py` | 18 config/identity/portability/exclusive-publication cases. |
| `data/manifests/solexs_provisional_v1.json` | Compact exact experimental provenance, metrics and ignored artifact identities. |
| `docs/SOLEXS_PROVISIONAL_MODELING_REPORT.md` | Scientific feasibility, experiments, limitations, sources and reproduction. |
| `docs/SOLEXS_PROVISIONAL_IMPLEMENTATION_REPORT.md` | This inventory and verification/handoff. |
| `docs/superpowers/specs/2026-10-09-solexs-provisional-design.md` | User-authorized design and scientific boundaries. |
| `docs/superpowers/plans/2026-10-09-solexs-provisional-modeling.md` | Execution/review ledger and completed tasks. |

## Executed verification and warnings

| Check | Observed result |
|---|---|
| Untouched inherited full suite | 1,084 passed, one inherited warning, 77.54 s. |
| Final frozen implementation full suite | 1,149 passed, same warning, 75.71 s. |
| New provisional suite | 65 passed, 2.52 s; independent reviewer also 65 passed. |
| Native loader/readiness/exploration subset | 109 passed, no warnings, 5.70 s. |
| Native validator / direct independent audit | Two ZIPs/eight FITS products; all gzip/CRC/structure and 16 DATASUM checks pass; CHECKSUM absent. |
| Existing readiness probe | Candidate RMF labels 1–340, PI 0–339; applicability remains false. |
| Normal isolated package installation | Succeeded with existing dependencies, no shared P2 install changes. |
| Normal CLI help/source guard | Passed; 53 source entries, clean tracked source and installed/executed source equality. |
| Real frozen experiment | All stages completed; selected epoch 4, 1,032 parameters, 472 total optimizer steps. |
| Same-config reproduction | Every indexed artifact byte identical, including checkpoint; all arrays/metrics/history/identities equal. |
| Independent numerical review | 300 randomized window cases and synthetic training/reload passed; real metrics and prediction hashes independently recomputed. |
| Independent scientific review | Real source/window/normalization/prediction/selection/metric checks reproduced; physical gates preserved. |
| Original-file and experiment preservation | 436 prior file hashes match; 32 prior indexed experiments verify. |
| Git scope and data protections | Protected local/fetched refs unchanged; main remote unchanged; no P3 ref observed; ignore/index/history checks pass. |
| Whitespace/final diff | `git diff --check` passes; exact changed inventory is additive. |

The existing warning is
`RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject`, from netCDF4 import during
`test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability`.
It was not suppressed or repaired; no ABI-safety claim is made.

Intermediate verification failures are preserved, not hidden:

- An implementer's original-environment full run had **1,130 passed, one failed**:
  `test_installed_synthetic_run_does_not_require_optional_aditya_imports`.
  The installed snapshot did not contain the newly added provisional module.
  The existing provenance guard correctly refused it. A separate normal install
  resolved the setup mismatch without changing P2's shared environment.
- A subsequent full run had **1,134 passed, one failed**:
  `test_runner_publishes_verified_checkpoint_and_reproducible_bounded_native_scores`.
  The coordinator edited the runner while that verification interpreter was active.
  Existing executed-source guards detected the changed module. After source was
  frozen, a fresh full run passed all 1,149 tests. No guard was weakened.
- Expected TDD RED runs preceded implementation: 16 sequence, four baseline,
  27 neural and four runner cases; ten frozen-config regression cases, two
  config/runtime provenance cases and two publication-redirect cases then failed
  before their fixes. All final 65 provisional cases pass.

Review fixed three concrete safeguard defects before real execution: frozen v1
configuration accepted alternate settings; runtime provenance incorrectly required
optional pytest; a redirected stage could write an artifact index outside results.
Single-byte-snapshot config parsing/hash also removes separate-read ambiguity.
Independent final review found no remaining required code/scientific defect.
Code review was temporarily interrupted by an account limit, then completed after
the user's continuation. These are engineering review outcomes, not mission
approval of time, exposure, calibration, uncertainty or forecasting readiness.

## Results and artifact locations

| Item | Ignored location |
|---|---|
| Main experiment | `results/experiments/solexs-provisional-v1-20261009/` |
| Consistency execution | `results/experiments/solexs-provisional-v1-20261009-reproduction/` |
| Direct native integrity CLI output | Original data root: `results/solexs_provisional_feasibility_20261009/native_report.json` |
| Independent audits/literature/reviews/tests/preservation snapshots | Worktree: `results/solexs_provisional_20261009_research/` |
| Isolated local runtime | Worktree: `results/solexs_provisional_runtime/` |

Each experiment contains `report.json`, `selection_frozen.json`, `predictions.npz`,
`best.pt`, and labeled `artifacts.json`. The compact tracked manifest records
exact hashes and sizes. Predictions NPZ includes source-relative row origins,
recorded targets/masks, model predictions and explicit scientific/unit labels.
Source masks/native metadata/provenance remain in the sequence/derivation records;
no hidden imputed measurement or science-quality mask was created. No full arrays
or checkpoints are committed, even when small.

Main selected-checkpoint train MAE/RMSE: **4.598365/8.061419**; validation:
**4.607214/6.014515**; held-out test: **4.972369/7.355389**, on the unencoded recorded
numerical scale. Persistence test: **6.222016/8.924128**; trailing mean:
**4.603606/6.824853**; Ridge: **4.814436/6.811153**. Neural training establishes no
advantage over these simple baselines. All original results remain preserved.

## Reproduction

Use a clean checkout of the feature branch and a normal installation with the
existing required dependencies plus Astropy and Torch. A fresh environment may
install `'.[aditya,training,test]'`; the actual run reused installed dependencies.
Set `SOLEXS_DATA_ROOT` to the root containing the immutable relative archive paths.
It can differ from the code checkout. Never overwrite an existing output identity.

```bash
python -m pip install --no-deps .
python scripts/run_solexs_provisional.py --help
python -m pytest -q tests/test_solexs_provisional_sequences.py \
  tests/test_solexs_provisional_baselines.py \
  tests/test_solexs_provisional_neural.py \
  tests/test_solexs_provisional_experiment.py
python -m pytest -q tests/test_solexs.py tests/test_solexs_readiness_probe.py \
  tests/test_solexs_exploration.py
python -m pytest -q
python scripts/run_solexs_provisional.py \
  --data-root "$SOLEXS_DATA_ROOT" \
  --output-dir results/experiments/solexs-provisional-new-reproduction
python -c 'from solar_flare_jepa.provisional.experiment import verify_outputs; verify_outputs("results/experiments/solexs-provisional-new-reproduction")'
```

The local acceptance runtime is
`results/solexs_provisional_runtime/bin/python`. It is a dedicated venv with a
normal milestone package install and a local `.pth` reference to the original
runtime's dependency directory. This machine-specific ignored helper is not a
portable dependency specification; project extras/lock files remain unchanged.
The CLI uses its own checkout as code/config root and `--data-root` only for data.
No network access or new scientific-data download occurs in the runner. Running
from another current directory is supported by the script's checkout root and
absolute `--config`/data paths; outputs remain relative to the code checkout.

A later documentation-only commit changes reported Git commit identity, while
frozen source/config hashes and numerical outputs remain the comparison basis.
Bitwise reproduction is established only for the recorded CPU/runtime, not future
Torch/NumPy/Astropy versions, other devices or a differently calibrated product.
Checkpoint hashes are consistency checks, not external signatures/authentication.

## Preservation and publishing boundary

The original preservation snapshot covers all 89 original raw files, 32 indexed
experiments, Phase E/P2 SoLEXS results and the two originally untracked user files:
436 full identities. Temporary legacy test scratch was excluded from the snapshot;
it was not deleted. Broad traversal encountered blocking legacy test fixtures,
so read-only snapshot processes were stopped and hashing was limited to immutable
raw files and explicit indexed scientific artifacts. No original file was modified.

Before publication, actual archive/checkpoint/result paths match `.gitignore`;
no ZIP/FITS/gzip/science arrays/checkpoints occur in the index or reachable Git
path history. Prior manifests, scientific identities, results and original source
remain byte-identical. No forced staging, reset, rebase, force push, branch deletion,
P3 operation, main push, merge or PR creation occurred.

Focused commits and final publication are restricted to
`research/solexs-provisional-sequence-modeling`. Final local/upstream/independent
remote SHA equality and clean status are reported in the human handoff after push.
No text here supplies integration permission. Work stops for human review.
