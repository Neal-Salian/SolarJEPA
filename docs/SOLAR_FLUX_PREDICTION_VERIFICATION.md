# Solar Flux Prediction verification

This record describes the bounded fifth-page implementation on
`codex/solar-flux-prediction`, based on `d718177`. Existing historical dashboard
verification reports and the original source registry were preserved.

## Verified scope

The UI-independent service opens the explicitly pinned August 2024 GOES manifest
and its 31 immutable native products. The runtime page uses the existing
`TrainedJepa.load` / `predict(context, future_grid)` APIs with the full-run seed
17 JEPA checkpoint and optional supervised checkpoint. Models, normalization,
forecasting contracts, native scientific adapters and experiment code were not
modified. No real-data training, acquisition, evaluation rerun, pilot or G4
activation was performed. Tiny synthetic fits belong only to existing tests.

The source/checkpoint contract is separate from the legacy registry. It pins
native manifest/config identities, executed inference dependencies, the frozen
forecast spec, saved train-only normalization, both approved checkpoints and
explicit verifier-only replay artifacts. Runtime checks verify repository bytes
and captured imported source bytes, including a byte-identical normal package
installation. The page does not open the saved archive or summary.

August is the historical V1 test partition and has already been evaluated. Its
use here does not make it an untouched holdout for future evaluation. Extra
minute origins preserve the frozen stride-30 specification and do not extend
archived benchmark metrics or establish new forecast skill.

## Behavioral verification

New tests exercise completed-bin timing, partition edges, explicit UTC minute
alignment, 120×2 full-valid context eligibility, missing cadence, duplicate and
off-grid timestamps, nonfinite/nonpositive inputs, rejected context masks,
optional future gaps and future perturbation invariance. Comparator calls receive
identical context/grid objects; the existing inference API canonicalizes the
returned grids, whose identities and coordinates are also checked.

The chart tests independently assert channel wavelengths, physical units,
logarithmic axes, quantile bounds, masked gaps, exact UTC starts and all three
boundaries. Streamlit AppTest selects all five pages, changes issue minute and
comparator controls, and verifies explicit unavailable states. A fresh-process
legacy regression blocks Torch/model imports, networking, August data and
prediction artifacts while rendering the original page chart counts 1/2/1/1,
87,840 observed records and working channel/transformation controls.

A normal installed-package inference test runs with `python -I` outside the
checkout. A separate guarded production call blocks acquisition/fitting/network
access, saved archive/summary reads and the unused optional comparator checkpoint.

## Native concurrency failure and regression

Browser review found a server exit 139 during rapid widget changes. A minimal
isolated reproduction with two concurrent August loads also exited 139, with
faulthandler traces showing overlapping xarray/NetCDF metadata opening and file
closing. Additional isolated regressions for August↔August and August↔legacy
loads failed with native HDF errors before the fix.

A single process-wide dashboard `RLock` now spans the complete
`validate_goes_files` lifetime in both dashboard native loaders. Hash verification
uses ordinary byte reads and remains outside the native critical section.
Original scientific adapters and registry identities remain unchanged. Both
concurrency regressions passed, and the original two-thread reproduction
completed ten successful native loads. This serializes simultaneous native
reads, so a second active rerun/session may wait for the first read to finish.

## Explicit archive replay

`python scripts/verify_flux_prediction.py --root /path/to/SolarJEPA` passed for
the deterministic first saved origin, `2024-08-01T02:00:00Z`. Network calls were
blocked. Raw context values, masks, context/future coordinates and QC-valid actual
future values matched the archive exactly before both checkpoint outputs were
compared. All 1,436 saved origin identities were checked against the pinned
summary; this command replays the selected example, not all-origin evaluation.
A requested unsaved minute origin is rejected without neighbor substitution.

Single-origin predictions use `rtol=1e-6` and `atol=1e-15 W/m²`. Float32 results
differ slightly from the archived original batch shape. Observed maximum
relative differences for the default example were:

| Checkpoint | Point | Quantiles |
|---|---:|---:|
| JEPA fine-tuned seed 17 | 4.7287536e-7 | 6.3050053e-7 |
| Supervised seed 17 | 3.9406263e-7 | 7.8812510e-7 |

These differences are replay tolerances, not uncertainty estimates or forecast
metrics. The absolute floor is negligible relative to the archived positive
flux values. Quantile coverage remains nominal and uncalibrated.

## Environment and checks

The observed environment is CPython 3.13.3, Torch 2.6.0 and the existing dashboard
lock, plus the repository's science/test extras for the full suite. The optional
prediction runtime/lock are separate; the older dashboard lock was not changed.
`pip check` passed, normal package imports were verified after
`pip install --no-deps .`, and the legacy offline verifier passed with 61 native
files, 17 source identities and 87,840 observed records.

The first full run passed 1,237 tests before the two concurrency regressions were
added. The final post-fix `.venv/bin/python -m pytest` run passed **1,239 tests**
with **1 existing warning** in **119.89 seconds**, including both native
concurrency regressions.
Both runs expose the existing NumPy/netCDF runtime warning rather than hiding it:
`numpy.ndarray size changed, may indicate binary incompatibility. Expected 16
from C header, got 96 from PyObject`.

The controller's initial pre-implementation baseline had 1,189 passes and 17
failures because the new isolated environment lacked a normal package
installation. All 17 were isolated CLI/import `ModuleNotFoundError` failures;
normal installation resolved them. They were not fixed by changing research code.

Raw data, checkpoints and replay arrays remain ignored; only reproducibility
code, tests, manifests and documentation are committed. Operational delivery
latency and real-time behavior are UNKNOWN. Cross-platform native concurrency,
GPU behavior and calibrated coverage have not been established by these checks.

The controller reported an independent browser check against a fresh server:
all four legacy pages retained their headings/charts/units; rapid comparator and
actual-observation toggles, followed by 02:00→02:01 and immediate toggle actions,
completed without a native fault. The displayed additional-minute support was
00:01–02:01 context and 02:01–02:31 forecast, with both supervised medians. This
browser evidence is attributed to the controller; the implementer independently
ran the automated Streamlit and native concurrency tests above.
