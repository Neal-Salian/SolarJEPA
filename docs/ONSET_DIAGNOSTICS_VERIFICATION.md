# Onset diagnostics verification and readiness

Executed 2026-10-18 on isolated branch `codex/flare-onset-diagnostics`, based on
verified local/remote forecasting checkpoint `16b975f`. Main and origin/main
matched `1a4991d` after fetch. The primary checkout's pre-existing untracked
`.agents/` and `docs/P1_FINAL_INTEGRATION_REAUDIT.md` were preserved.

## Executed evidence

| Check | Observed result |
|---|---|
| Clean checkpoint baseline | 270 passed, one existing warning, 38.49 s |
| Final full suite | **388 passed**, one existing warning, 37.48 s |
| Prospective split tests | 110 passed; includes test-first maturity, group-coverage and event-embargo regressions |
| Diagnostic tests | 8 passed; missing module/fields failed first, then passed |
| Installed package | Wheel built/installed with `pip install --no-deps --no-build-isolation --target .cache/onset-final-install .` |
| Imports outside checkout | All six executed event-module byte identities equal the installed snapshot |
| Installed CLI outside checkout | Real pinned January artifacts, all 22 models and 1007 retained origins; no inference/fitting |
| Source/installed determinism | Entire regenerated diagnostic JSON equal; bytes and SHA-256 identical |
| Preserved scores | All 66 class/model counts, matches/leads, opportunity scores/intervals and false-alarm rates equal the historical installed report |
| Model/science preservation | All 16 V1 artifacts in the prior checkpoint audit rehashed unchanged, including nine checkpoints and August forecasts |
| Independent review | No unresolved P0/P1/P2 code or scientific reporting findings within scope |
| Storage/index/compile | Actual report/cache/raw/checkpoint ignore checks, index policy audit, compileall and whitespace checks passed |
| Scientific rule freeze | **BLOCKED**, no numeric parameters or model selected |

Final ignored diagnostic artifact:
`results/events/january2025-diagnostics-installed.json`, 5,229,868 bytes,
SHA-256 `a3357d259b465248eea1404c8d49889009c4f1fdfe986a2c51f5a84d1bdb07ae`.
The source replay has exactly the same identity. The JSON records executed code
hashes, config identity, runtime and all eight pinned source identities. These
are reproducibility identities, not authenticity or independent raw-data attestations.

Python 3.13.3 and NumPy 2.2.6 were used in the existing project virtual environment.
The warning is the baseline NetCDF-related `numpy.ndarray size changed` warning
in `tests/test_goes.py::test_cf_clock_bin_end_quality_and_source_retention`.
No dependency upgrade was attempted. An initial system-Python invocation lacked
xarray/astropy and failed collection; the existing project environment then ran
the full suite without skips. Its default installed package is a different
snapshot, so plain imports initially did not resolve this new events package.
The isolated installation, imported outside the checkout, resolved and verified
that issue without modifying the shared environment.

## Independent research and review

Separate Superpowers subagents audited real event errors and development/exposure
support; another implemented/tested the prospective split auditor. A fresh code
and scientific reviewer inspected the implementation and final scientific reports,
ran 8 focused tests and 300 randomized synthetic split property probes, checked
threshold denominator invariance for all 22 models, and tested half-open/short-lead
matching semantics. Coordinator review caught insufficient maturity validation
and incomplete full-group coverage; both received failing regression tests and
fixes before final verification.

The independent reviewer identified missing lead/rate/paired reporting fields;
these were added test-first and reviewed. No important findings remain open.
The reviewer’s [record](ONSET_INDEPENDENT_REVIEW.md) precedes final coordinator
verification; its stated replay/install/preservation dependencies are satisfied
by the checks above. No real historical split was certified by the new auditor.

## Preserved scope and remaining limits

The four inherited event modules and January frozen config remain byte-unchanged.
No datasets, checkpoints, existing experiment output or V1/V2 protocol were edited.
No model was loaded for prediction, retrained, recalibrated, selected or rerun;
no V2 pilot, new data acquisition, PR, merge or main push was performed.
All generated reports, installation files and scratch evidence remain ignored.
Scientific source bytes were validated through the inherited pinned adapter;
the milestone does not independently reconstruct the entire raw preprocessing.

The split utility validates caller-declared selected-catalog support only. Unknown
physical completeness, activity dependence, actual delivery latency and reprocessing
causality remain unknown. Event/paired uncertainty is explicitly not estimated;
window descriptive intervals are not substituted. Neither historical unseen
evaluation nor operational flare prediction is established.

**Readiness:** diagnostic/audit implementation verified; development-only onset
rule freeze blocked. See [error analysis](FLARE_EVENT_ERROR_ANALYSIS.md),
[exposure audit](ONSET_EXPOSURE_AUDIT.md) and the [blocked specification and exact
next milestone](ONSET_RULE_SPECIFICATION.md).
