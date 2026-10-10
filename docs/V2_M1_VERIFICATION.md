# V2 M1 verification and integration readiness

Date: 2026-10-10, Asia/Kolkata. Scope: the model-independent foundation in
[M1 design](V2_M1_DESIGN.md), following [M0 resolution](V2_M0_RESOLUTION.md).
This report records current execution separately from historical V1 evidence.
Tested implementation content is committed at `b92caa2`; subsequent changes
are documentation only. The final published tip is available through
`origin/feat/v2-m0-m1-validation-foundation` and the repository Git log.

## Delivered implementation

* Reused canonical P1 forecasting contracts, partition-local support/mask/gap
  validation and P2 unique-raw-train normalization. No replacement framework.
* Added explicit minimum chronological embargo without moving partition bounds.
* Added canonical versioned evaluation identity/record serialization, content
  support identity and recomputed normalization/fitting-support audits.
* Added strict native/dex marginal quantile reliability, pinball, coverage,
  width and proper symmetric interval scores. Empty support is null; incompatible
  native units have no pooled unit-sensitive score.
* Added complete-record dex loss extraction, paired seed aggregation, equal
  fixed-fold effects, relative reduction, seed/fold/influence summaries and
  crossed circular calendar-block intervals. Seeds and day draws are shared
  correctly; zero-count days stay in the calendar; empty required draws invalidate
  intervals. Metric identity includes quantiles and the experimental spec.

No change to scientific readers, training/model logic, V1 scoring, acquisition,
configurations, data manifests or existing artifacts. No new dependency, UI,
runner, model fit policy or research experiment was added.

## Tests and executed checks

Commands run in the isolated worktree with `.venv/bin/python`. The environment
was cloned from the existing dependency environment without changing the original,
then the package was normally installed with
`-m pip install --no-deps --no-build-isolation .` before baseline and final runs.

| Check | Observed outcome |
|---|---|
| Baseline full `-m pytest -q` at V2 base | 1,171 passed, one warning, 139.87 s |
| Final targeted five new modules | 121 passed, no warnings, 0.82 s |
| Final full `-m pytest -q` after normal reinstall | 1,292 passed, one existing warning, 142.90 s |
| Installed `python -I` imports and deterministic comparison from `/tmp` | PASS; no Torch imported; installed worktree venv confirmed |
| `-m pip check` after installation | No broken requirements found |
| `git diff --check` and staged whitespace checks | PASS |
| Protected-path diff against `90571df` | Empty for data/configs/scientific readers/training/experiments/V1 scorers and historical V1/V2 documents |
| Branch/ref snapshot comparison before final push | Only the new feature branch advanced; all other existing local/remote refs unchanged |
| Storage ignore checks | Raw NetCDF, processed Parquet, result NPZ and checkpoints ignored by actual rules |
| Science/result path inventory in new worktree | Only four `.gitkeep` files under raw/interim/processed/results; no scientific holdout present |

The baseline warning is the existing
`test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability`
NumPy extension warning: `numpy.ndarray size changed, may indicate binary incompatibility`.
It was not suppressed or addressed through dependency changes.

New tests: `test_independent_records.py` (46),
`test_independent_integrity.py` (12), `test_independent_comparison.py` (37),
`test_independent_diagnostics.py` (15), `test_independent_integration.py` (11).
They cover schemas, masks, serialization, copies/subclasses, exact support,
normalization reuse, temporal boundaries, embargo, missing/duplicate/invalid time
support through P1 checks, future availability, deterministic resampling,
unequal calendar counts, empty draws, seed/fold pairing, physical units and
synthetic end-to-end record replay. Existing tests were not weakened or rewritten.

## Test-first development and failure record

Expected RED checks preceded implementation: missing comparison/diagnostic
modules and record-to-panel adapter produced collection/import failures; Task 2
had 43 missing-API/embargo failures and one existing-invariant pass. Tests passed
after the corresponding APIs were implemented.

Systematic inspection of initial diagnostics found missing explicit logarithmic
references; a dedicated test reproduced acceptance before correction. The draft
literal pinball fixture also had an incorrect hand-calculated expectation and
a duplicate keyword in test construction; these test defects were corrected
from the literal score arithmetic, not by weakening production checks.
Finite-loss arithmetic overflow and full-int64-span timestamp subtraction had
two reproduced failures; explicit finite-arithmetic guards and Python integer
calendar differences resolved them. Overlapping fold calendars had one reproduced
failure and are now rejected before independent fold day draws.

Independent review corrections all have tests:

| Finding | Reproduction and correction |
|---|---|
| Native loss/width/interval score pooled incompatible units | Mixed W/m²/K example reproduced; pooled unit-sensitive outputs now null |
| Extreme asymmetric quantile tails accepted as central | Tiny lower-tail / nextafter(1,0) example failed before fix; compare tail masses relatively, use alpha=2×lower tail |
| Raw panels rely on caller labels | Added canonical-record loss adapter; altered observations/masks/quantiles/recipe and partial/point-only inputs fail |
| Within-panel actual model ID/point interpretation omitted | Two failing integration cases; now require matching prediction declarations |
| Cross-fold metric did not bind full experimental spec | Failing metric-identity test; full spec now included in metric identity |
| JSON loader coerced numeric strings/booleans | Seven reproduced failures among 12 malformed-cell cases; exact JSON numeric cell types required before conversion |
| Empty-origin record serialized but failed reload | Two failing point/quantile record cases; restore only declared empty shapes/dtypes; nonempty validators preserved |

No unresolved reproduced implementation defect remains after the final checks;
scientific/provenance limitations below remain explicitly unresolved.

## Independent review evidence

Three read-only audits covered scientific/statistical methodology,
data/provenance, and reusable architecture. The architecture auditor subsequently
implemented only assigned records/splitting/tests; it did not review its own work
as the independent acceptance reviewer.

A separate statistical reviewer executed 50 then-current synthetic tests and
matched the calendar bootstrap to an independent direct-origin reference across
31 draws, nonconstant seeds/days, unequal counts, two folds and truncated blocks.
A fresh whole-branch code reviewer executed 104 then-current tests, checked the
diff and reproduced the model/schema/empty-record boundaries above. Later fixes
were verified by RED→GREEN regressions and the final suite; their final written
reviews contain earlier findings, not an assertion that the later tree was
independently re-reviewed. All review work used synthetic inputs only.

Reviewer-declined topics are retained as limitations: authentic unseen training
history, candidate independence/suitability, nominal CI coverage and operational
causality are not established by code review. The split fingerprint in an
identity may refer to a complete split design, while TrainingSlice stores one
partition manifest; the fitting audit does not conflate those labels or claim
to authenticate them. None of these limits authorizes confirmatory access.

## Scientific integrity and readiness

No sealed/candidate V2 observations were read, summarized or scored. Source and
tracked provenance/presentation records established historical exposure without
opening raw/processed data or ignored historical result arrays. The new worktree
contains no such science products and has no link to the original data storage.
Original source archives and V1 outputs were neither opened nor modified;
this is an isolation/action record, not a claimed bytewise replay of those artifacts.

No new scientific JEPA model, exposed-data feasibility fit or confirmatory
experiment ran. Full baseline/regression suites execute existing tiny synthetic
neural training fixtures in temporary directories; those software tests are
explicitly distinguished from scientific model training and produce no research
result. No acquisition, test-driven tuning, teammate branch modification, merge,
main push or PR occurred.

**PARTIALLY_READY** for integration: the safe model-independent foundation is
implemented and reviewed. M0 documentation is complete under the current task,
while original M0 signed-decision/access gates remain unresolved. Interface
adoption and the broader original V2 M1 model/loss/schedule/runner/streaming work
require teammate coordination. Confirmatory V2 execution is **BLOCKED**.

Before confirmation, obtain both exposure attestations, approve candidate calendar
and custodian, freeze targets/masks/interfaces/seed cohorts/search/selection/failure
rules/compute limits/estimands/multiplicity/interval settings, implement model-owner
adapters and aligned dex selection, run separately authorized exposed-data M2
feasibility/dependence checks, and authorize later acquisition/fitting/unsealing.
Archived-product upstream causality, practical relevance, precision, block
adequacy and SoLEXS timing/calibration gates remain research risks.

Provenance labels and honest availability/dependency declarations are necessary
but cannot expose arbitrary dishonest future-derived arrays or identical
externally fitted normalizer statistics. The kernel assumes representative
paired seeds and adequate approximately stationary blocks; temporal errors are
not treated as independent, but arithmetic correctness is not proof of coverage.
No general JEPA superiority or event-warning claim follows from this milestone.
