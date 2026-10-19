# Stable Baseline v0.1 independent scientific review

Review date: **2026-10-18, Asia/Kolkata**. Reviewed the combined integration
working tree based on `main=1a4991da4dda`, prediction merge `4356611`, and
time-series commits `7dea4fc`/`e92efdd`, including the new reference verifier,
release preflight, regression tests and scientific/release documentation.
The reviewer previously authored the audit/plan but did not implement the new
replay tooling, dependency checker or dashboard composition. Independent review
used read-only source/artifact inspection and inference-only execution; no model
fitting, pilot execution, acquisition or original artifact writes occurred.

**Verdict: scientific preservation passes for the bounded historical baseline.**
No unresolved release-blocking scientific finding remains in the inspected
tree. This is a software/checkpoint reproducibility verdict for the frozen V1
experiment, subject to final technical/integration checks and publication of the
reviewed tree. It does not establish prospective skill, calibrated uncertainty,
pretraining superiority, physical SoLEXS validity or permission to merge main.

## Independently observed evidence

The following checks were executed by this reviewer, rather than inferred from
the implementer's report:

| Check | Observed result |
|---|---|
| Core training, forecasting, data and experiment source versus `v1` | No differences; frozen configs/manifests also preserved |
| Prediction service, page, charts and two registries versus `a495151` | Five inspected files byte-identical |
| Prediction registry artifacts | All 20 recorded artifact SHA-256 values matched; its 13 pinned core source modules also matched V1 bytes |
| Original bundle custody | Nine copied checkpoints plus summary, per-origin JSON and NPZ matched primary original bytes |
| Time-series preservation | All 26 scientific source identities matched; five scientific/report files matched selected `5618bc4` bytes |
| `scripts/verify_v1_reference.py --root "$PWD"` | PASS: nine models, 1,436 origins, 31 August files/44,640 native rows; all points and quantiles bitwise exact, maximum absolute and relative differences zero |
| Native support in full replay | Contexts, context masks, targets, target masks, exact minute coordinates and every saved temporal-support record matched |
| `scripts/verify_presentation.py` | PASS: 52 identities, 123 native files, 12 independently reconstructed stationarity statistics, 422 saved-score checks; maximum score discrepancy zero and stationarity discrepancy `2.2815527245256817e-11` |
| `tests/test_flux_prediction.py`, `test_flux_prediction_replay.py`, `test_v1_reference_replay.py` | 31 passed, one existing NumPy/netCDF warning, 27.61 seconds |
| `tests/test_stable_baseline.py` plus three focused integration UI tests | 10 passed, one existing NumPy/netCDF warning, 10.99 seconds |
| Updated reference preflight | PASS: 222 distinct artifact records, 123 native files, all nine original checkpoints; checkpoint constants equal the full replay contract |

The three focused UI checks exercised the four-page fresh-process boundary, the
fifth page and comparator/time controls, and richer time-series views plus the
saved-parameter inference button with fitting/network denied. Original artifacts
were not modified to obtain passing checks. The final all-test count, application
health, packaging/platform checks and feature-branch publication remain the
responsibility of the technical/release report.

## Scientific implementation assessment

The all-nine replay verifies pinned checkpoint identities before loading them,
compares stored model records with the original summary, checks every saved
origin/model inventory and support boundary, and independently reconstructs raw
contexts and realized targets from authenticated August NetCDF products. It
passes only context and future coordinates into `TrainedJepa.predict`; actual
future observations never enter neural inference. It restores no model from
newly fitted parameters and rechecks checkpoint/summary/archive bytes afterward.

The preserved checkpoint loader uses weights-only deserialization, strict state
loading and internal weight/config/normalization identities. Inference is CPU
float32 with the original batch size 256/four threads. All nine checkpoints
carry normalization fingerprint
`848623009ce048a14e32c50b7c70d9c9728cdd77391f10115ec1c8fd46d039a9`.
The source applies stored train-only means/scales after the dimensioned log10
transform and inverses predictions to W/m². Nothing is refitted on August.

The frozen QC adapter retains native timestamps and channel-specific rejection,
checks encoded units/flag schemas/count fields and preserves rejected bins as
gaps. Context is exactly `[issue−120 min, issue)`; lead 1 starts at issue and ends
one minute later; lead 30 ends at issue+30 minutes. The issue is a historical
bin-end availability assumption, distinct from measured delivery latency.
Complete-case benchmark eligibility and overlapping contexts are disclosed.

The verifier's acceptance remains `rtol=1e-6`, `atol=1e-15 W/m²`; observed full
batch replay achieved exact equality. This tolerance is a numerical criterion,
not a forecast uncertainty estimate. Five marginal quantiles produce nominal
central 50%/90% bands; neither calibration nor joint trajectory coverage follows.
The new nine-model verifier deliberately does not regenerate the 13 classical
forecast arrays; the independent presentation verifier reconciles all 22 saved
models' recorded scores with the original NPZ and per-origin losses. These are
different checks and are documented separately.

The four presentation pages may hash the exact tracked August manifest while
loading the saved May–August time-series report. That metadata-only exception is
appropriate composition: the fresh-process test still forbids August raw-file
reads, checkpoints, archived prediction arrays, torch/training/prediction imports
and network access, and still observes exactly 61 May/June native inputs.

## Findings raised and resolved

| Priority | Finding | Resolution and evidence |
|---|---|---|
| P1 | Reference preflight initially checked only the two registry seed17 checkpoints; seven missing reference checkpoints could leave preflight passing while full replay skipped. | `scripts/check_stable_baseline.py` now authenticates all nine pinned originals under `--references`. Independent inspection/execution observed nine checkpoint records. `test_reference_mode_detects_missing_and_changed_nonprimary_checkpoint` passed for missing/altered frozen seed29 bytes in a temporary fixture. |
| P2 | Release draft mislabeled marginal bands as 80%/90%. | Corrected to central 50%/90%, consistent with q05/q25/q50/q75/q95 and the unchanged UI. Direct final-text inspection confirmed. |
| P2 | Release scope draft described all presentation evidence as May/June. | Corrected to distinguish May/June native plots and the separately pinned saved May–August report. Direct final-text inspection confirmed. |
| Availability | Original per-origin JSON was initially absent from the new checkout. | Restored exact original hash `133025c6921bcd575b727287b504550ff15e6e1d3ade8bcc39a5ff432056aa7f`; reviewer confirmed primary byte equality and reran the 422-score verifier successfully. |

The full-reference pytest test explicitly skips when the ignored original bundle
is incomplete. That is acceptable only alongside the mandatory release
`--references` preflight and explicit verifier, which fail closed on missing or
mismatched originals. A skipped test is not numerical reproduction evidence.

## Scientific limits and remaining merge requirements

The scientific and release documents correctly retain seed sensitivity,
restricted temporal/satellite/complete-case support, normalized-versus-dex
selection differences, historical variance-fit convergence limitations,
uncalibrated marginal quantiles and unavailable operational timing. The original
experiment's producer SHA is distinguished from its later V1 audit tip. Existing
reports remain historical evidence and are not rewritten as fresh conclusions.

V2 pilot, V3 research, live/NRT inference, later event/external-evaluation work and
scientifically blocked SoLEXS forecasting remain excluded. Main's native SoLEXS
inspection infrastructure does not clear time, exposure, quality, calibration,
physical-quantity or cross-instrument gates. No new labels or instrument
semantics are inferred. The recurring NumPy/netCDF binary warning remains
disclosed; exact replay does not diagnose its cause or establish every native
execution path is unaffected. Other platforms/GPU, prospective science and new
training were not tested here.

Before main integration, finish final technical/full integration verification,
retain exact ignored artifact custody, publish only the reviewed integration
branch, recheck main/origin and obtain the user's explicit merge approval.
Any push to main requires separately explicit authorization. The final release
report must replace its pending completion language with actual results before
claiming release readiness; this review does not authorize a PR or main change.
