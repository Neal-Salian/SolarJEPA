# Presentation checkpoint verification

Verification date: 2026-10-10. This record describes checks actually executed
for the presentation milestone. The small machine-readable result is
[verification.json](presentation/verification.json); the installed package
versions are in [environment.txt](presentation/environment.txt).

## Repository and scope

The remote was fetched before work. `origin/v1` matched the requested scientific
audit commit `644648f7d555fcbcb3eed4495d37fecffdd1863a`. The presentation branch
`presentation/eda-model-comparison` was created from that commit and published
with upstream tracking before implementation. Initial `main` / `origin/main`
were `1a4991da4dda9676caeb1d7e35a03408528c3188`; the original V2 checkout was
`research/v2-independent-validation` at
`90571dfe144434bbbd681c410dcdf2c389eab409`.

Pre-existing untracked `.agents/` and
`docs/P1_FINAL_INTEGRATION_REAUDIT.md` were preserved and excluded from the
checkpoint. Presentation changes add files; existing V1 implementation,
configuration, benchmark artifacts and figures remain unchanged. Only the four
explicit V1 May–August manifests, their native inputs, the strict V1 experiment
bundle and existing V1/reference presentation assets were read. No confirmatory
V2 holdout was accessed. No scientific data were downloaded, no model was
trained or tuned, and no SARIMA experiment was run. No PR, merge or push to
another branch is authorized by this checkpoint.

## Executed checks

| Check | Observed result |
|---|---|
| Presentation utility tests | **10 passed in 2.25 s**; gap-safe block selection, invalid values, stationarity settings/p-value disclosure, hand-calculated losses, masking, seed aggregation, mismatched support rejection and optional notebook metadata |
| Full suite after final regeneration | **1,181 passed, 1 warning in 90.97 s** |
| Dependency consistency | `pip check`: no broken requirements |
| Normal installed imports | EDA, comparison, figures and pipeline modules import; installed source hashes match the checkout |
| CLI portability smoke | Full build launched from `/tmp` using the normally installed package: exit 0; 8 EDA figures, 15 new figures, 4 reused references, 6 stationarity rows, 22 saved models |
| Notebook execution | All **8 code cells** executed without errors; 17 total cells; compact 18,178-byte notebook, no embedded dataset or machine-specific path |
| Native provenance and quality | **123 files** rehashed and natively validated; fresh coverage/QC evidence agrees with the saved evidence |
| Figure/source identity verification | **52 SHA-256 identities** match, including PNG/SVG assets, reused V1 figures and implementation/notebook sources |
| Independent stationarity algebra | **12 statistics** reconstructed: ADF OLS coefficient t statistics and KPSS cumulative-residual/Bartlett HAC statistics; maximum absolute discrepancy **2.2815527245256817e-11** |
| Saved-prediction score replay | **422 checks**, maximum absolute discrepancy **0.0** against saved summaries/per-origin/lead/quantile metrics |
| Native forecast support | Saved contexts and targets match native V1 data, timestamps, channel order and masks |
| Historical result preservation | Audited summary, per-origin and prediction bundle hashes remain unchanged |
| Final staging review | **53 presentation-only additions**, no existing tracked file changes, no raw data/checkpoints in the index; `git diff --cached --check` passes |
| Actual-path ignore checks | All **133** native/prediction/checkpoint paths exist and match the existing ignore rules |

The full-suite warning is in
`tests/test_experiment_reference.py::test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability`:
`RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject`. It is an existing runtime warning;
the test passed. It is disclosed rather than counted as a failure or hidden.

The audited artifact hashes are pinned in
[the verification script](../scripts/verify_presentation.py). Full local logs
are under ignored `results/presentation/`; small durable results are committed
under `docs/presentation/`. Bulk native files, prediction arrays, checkpoints,
runtime kernelspecs and logs are excluded by the existing storage policy.

## Independent review and corrections

Two read-only reviewers inspected V1 evidence and the final presentation science,
source and images. The final reviewer viewed all 15 generated PNGs and separately
recomputed saved model metrics and stationarity statistics. Confirmed issues
were corrected before final regeneration and verification:

- Architecture labels were shortened/wrapped to fit their boxes.
- Extreme ADF p-values reported as zero are explicitly described as the
  statsmodels MacKinnon approximation cutoff, rather than numerical underflow
  or an exactly zero probability.
- Missing optional notebook-tool metadata no longer prevents CLI figure
  generation; a regression test covers this behavior.
- The teacher/EMA implementation and independent verification script were added
  to source hashes in the figure manifest.
- Final staging caught trailing spaces emitted by Matplotlib's SVG writer;
  the exporter now removes them and writes CSVs with consistent LF endings.
  The executed notebook is also included in source identities.

No confirmed review finding remains deferred. Review did not include retraining,
new observations or independent replication of training on another platform.

## Reproduction

Use the existing V1 environment and local manifest-pinned data/artifacts.
These commands do not fetch scientific data:

```sh
.venv/bin/python -m pip install --no-deps .
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/build_presentation.py
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/verify_presentation.py
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

Notebook execution additionally uses the optional tools in
[requirements-presentation.txt](../requirements-presentation.txt). The notebook
uses repository-aware relative paths and the same reusable presentation package.
The executed notebook was run through `nbclient` with a project-environment
`ipykernel`, a 180-second cell timeout and the working directory `notebooks/`.
The local kernelspec was installed under ignored `results/presentation/runtime`;
it is not a required absolute path in the notebook. Register an equivalent kernel
for the chosen environment when reproducing elsewhere. Missing pinned native
data or saved V1 artifacts must be supplied by the authorized data custodian;
the workflow does not silently substitute observations or download replacements.
Execute the notebook before the full CLI build, which records its final hash
and the identities of all regenerated figures.

## Interpretation and completeness limits

All required EDA figures, the executed notebook, asset inventory, verified model
comparison, architecture explanation and ten-slide guide are supplied. Fifteen
new figures have both PNG and SVG outputs; four existing V1 figures are reused
by reference. No assembled PowerPoint/PDF deck was requested or created.

SARIMA is deliberately omitted because the training-only analysis did not
establish a defensible stable seasonal period for a fair addition. No LSTM,
TCN or PatchTST scores exist in this V1 bundle; the supervised comparison is the
matched Transformer control. Neither omission is replaced with invented scores.

Stationarity results concern one contiguous training block and have mixed
ADF/KPSS evidence for log levels. The JEPA improvement over the matched control
is small and seed-sensitive; excluding seed 43 reverses its direction. Bootstrap
intervals condition on the fitted seeds. Quality exclusions, repeated historical
test access, classical fit diagnostics, channel calibration differences and
unknown operational data latency limit interpretation. These outputs support a
transparent retrospective pilot, not robust general superiority or operational
flare warnings. Detailed limitations remain in the
[EDA report](PRESENTATION_EDA_REPORT.md) and
[model comparison](PRESENTATION_MODEL_COMPARISON.md).
