# Bounded onset exposure and development-support audit

Audit date: 2026-10-18. Read-only scientific/artifact audit; no training, inference,
acquisition, catalog-outcome inspection from a new period, or protocol change.
Paths use configurable checkout roots: PRIMARY_ROOT is the existing primary
checkout, FLUX_ROOT the preserved solar-flux-prediction checkout, and EXTERNAL_ROOT
the preserved goes-external-validation checkout. These are evidence locators;
scientific identities come from the pinned files, not the root names.

## Verdict

**OBSERVED:** the saved frozen 22-model V1 development forecast cohort is not
available in the bounded inventory examined. Existing P2 development forecasts
are a different, limited cohort. **INFERRED:** numeric onset thresholds, gates,
alert suppression parameters or a probability calibrator cannot be selected and
frozen for the full V1 cohort from the presently established development support.
The current deliverable can specify a conceptual family and executable contracts,
but selection/readiness must remain **BLOCKED**. No candidate rule was applied
to January in this audit.

**UNKNOWN:** whether additional suitable preserved forecasts/catalogs exist in
unpublished locations or another human's records. The search is evidence of the
examined locations, never proof of universal absence.

## Actual development artifacts

**OBSERVED:**
`$FLUX_ROOT/configs/experiments/v1_goes_2024.json`
fixes train `[2024-05-01,2024-07-22)`, validation `[2024-07-22,2024-08-01)`,
and test `[2024-08-01,2024-09-01)`. Forecast support is 120 context minutes,
30 future minutes and stride 30; future starts at issue, native bin completion
is one minute later, and availability is retrospective bin-end assumption.

**OBSERVED:** the V1 runner (`src/solar_flare_jepa/experiments/v1.py`, lines
114–133 and 253–263 in that worktree) computes validation and test predictions,
but writes only `test_predictions.npz`. Its `per_origin.json` contains losses and
coordinates, not recoverable trajectories. The existing canonical output
`$PRIMARY_ROOT/results/experiments/v1-full-20261009/`
contains the test NPZ, nine checkpoints, summary/per-origin reports and plots;
no development trajectory file appears in its direct inventory. The corresponding
V1 output directories in solar-flux-prediction, goes-near-real-time and
primary checkout were inspected by filenames. No checkpoint was loaded or run.

**OBSERVED:** useful but non-equivalent historical artifacts exist at
`$PRIMARY_ROOT/results/experiments/p2-goes-baselines-20261008/predictions.json`.
This is an explicit list of 18 records: persistence, training mean, trailing mean,
drift, AR1 and direct ridge for each of train/validation/test. Train has 855
origins from July 1 02:00 UTC to July 21 23:30; validation has 199 from July 22
02:00 to July 26 23:30; test has 209. Configuration is
`$FLUX_ROOT/configs/experiments/p2_goes_july2024.json`.
Its entire July dataset is development relative to V1's later August test, but
these models were fitted under a different July training protocol and do not
supply the missing V1 JEPA forecasts. Training-origin classical predictions are
in-sample for their fitted models and cannot be relabeled independent calibration.

**OBSERVED:**
`$PRIMARY_ROOT/results/experiments/p2-goes-training-smoke-20261008/predictions.json`
is explicitly `TRAINING_INFRASTRUCTURE_SMOKE_TEST`, only 32 origins per partition;
its training config limits two epochs, four training batches and two validation
batches. It is not the three-seed V1 finetuned/frozen/supervised cohort.

**OBSERVED:** primary raw files include only three development flare-state
files, `data/raw/noaa/sci_xrsf-l2-flsum_g16_d2024070{1,2,3}_v2-2-1.nc`.
The inherited event milestone reconstructed 28 IDs and preserved an incomplete
boundary event and unknown ends; source is `docs/FLARE_EVENT_FORECASTING.md`
and actual `events.labels` reconstruction/validation code. This is not a verified
May–July event catalog with complete onset-to-peak support. The local annual
catalog at
`$EXTERNAL_ROOT/data/raw/external/goes_flare_catalog_2025/`
is a 2025 CSV/metadata identity supporting the January lineage. Its outcomes
outside January were not inspected here. No 2024 annual report appeared in the
bounded raw inventories.

Inventory scope: `git worktree list` (16 checkouts including current), top-level
results/experiments inventories, raw file names, relevant tracked configs/source,
existing development JSON coordinate/model metadata. Historical temporary pytest
fixtures and arbitrary personal/external locations were not exhaustively audited.

## Chronology, event grouping and exposed periods

**OBSERVED:** V1/P2 splitting enforces ordered raw-axis partitions and complete
context/target support. `forecasting/splitting.py` accepts caller-supplied event
groups; real P2 split manifests examined contain `event_groups: []`. Inherited
V1 audit also records empty groups. `events.labels.label_events` enforces context,
horizon, all candidate onset-to-peak class support, maturity and feature
availability, but explicitly does not certify event-disjoint training.

**INFERRED:** chronological row containment alone does not establish distinct
flare/active-region episodes across development partitions. A future onset
selection milestone needs an explicit group definition, boundary-crossing purge,
class-maturity support and conservative handling of unknown event ends. Multiple
windows/alarm issues referring to one event must not become independent positives.
Any group or minimum-gap choice is a prospective analysis choice, not an observed
property of existing experiments.

**OBSERVED:** May–July 2024 is already development/training/EDA support. August
2024 has saved V1 forecasts, repeated scoring, scientific audits, figures and
presentations (actual test NPZ plus V1 source and `docs/V1_SCIENTIFIC_AUDIT.md`).
January 2025 has complete external preparation, saved 22-model predictions and
published retrospective event results (`configs/events/january2025_frozen.json`
and `docs/FLARE_EVENT_FORECASTING.md`). Both August and January are exposed for
future design; neither is a fresh confirmatory holdout.

**OBSERVED supporting record:** external-validation research reports a filename
listing survey for additional 2023/2024 months and January 2025, with only January
acquired there. **UNKNOWN:** complete human/agent exposure history for any other
historical period. Filename survey, lack of a local artifact, or lack of a result
in this checkout does not establish unseen outcomes. No historical candidate is
certified genuinely unseen by this audit.

**INFERRED proposal:** `[2026-11-01T00:00:00Z,2026-12-01T00:00:00Z)` is a genuinely
not-yet-occurred outcome interval as of 2026-10-18 and can be named prospectively
without reading its outcomes. It is only a proposed period. **UNKNOWN:** usable
instrument/source continuity with historical GOES-16, actual archive/catalog
availability/version/latency, quality, forecast exposure, M/X counts, suitability
and statistical power. Future month length guarantees none of those. It is not
approved acquisition or evaluation, and no evaluation rule is frozen yet.

## Authoritative semantics and external research

**DOCUMENTED:** NOAA SWPC distinguishes catalog begin, peak and end; its public
operational begin description uses four rising minutes, while peak is a maximum
minute and end is a background-relative decay criterion. Thus catalog onset time
is distinct from the time at which later observations establish/recognize it.
This operational description must not replace the separate NCEI science-report
algorithm. [NOAA SWPC GOES X-ray Flux](https://www.spaceweather.gov/products/goes-x-ray-flux).
The current inherited label package consumes pinned science catalog records and
keeps operational availability/completeness unknown. The audit did not independently
revalidate all science-detector details; the Machol DOI endpoint was inaccessible
through the browser in this pass.

**DOCUMENTED:** Ahmadzadeh et al. identify temporal coherence, rare-event imbalance,
normalization and cross-validation as sources of misleading flare performance.
Their active-region dataset and class ratios are not SolarJEPA's population and
are not transferred numerically. [Primary paper](https://arxiv.org/abs/2103.07542).
Bloomfield et al. compare TSS/HSS under flare forecast verification and thresholding;
this supports reporting support counts and multiple decision metrics, not a
single accuracy score or transferred numerical expectation.
[Primary paper](https://arxiv.org/abs/1202.5995).

**INFERRED:** use independent event/episode units and chronological development
roles, freeze all selection before evaluation, retain original prevalence for
scoring, and report event hits/misses, repeated alarms, false alarms per exposed
time and uncertain small-event denominators. Dependent-origin resampling needs
prespecified blocks/group units; one-day bootstrap intervals alone do not prove
independence or population generalization. These are proposed design safeguards,
not evidence that a new rule has skill.

## Exact next milestone and gates

1. **Development support recovery and registration:** locate preserved full-cohort
   development forecasts and an authoritative development catalog; verify bytes,
   source/model/config lineage, dates, coordinates, QC, complete candidate axis and
   onset-to-peak support. If preserved forecasts cannot be recovered, request a
   separately scoped authorization for inference from unchanged checkpoints on
   development only; existing authorization prohibits running it now. No retraining
   is implied. Catalog acquisition, if needed, is a separate explicit action.
2. **Development-only selection:** after support is verified, define chronological
   fit/tune/calibration roles with event-disjoint grouping and purge/maturity rules;
   compare a bounded conceptual onset family using contextual rise/background and
   predicted excess/rise, with explicit episode/reset logic. Numeric parameters,
   cohort, alert objective, multiplicity and uncertainty remain unresolved now.
   Do not optimize or choose using August or January. Freeze and hash the entire
   rule/protocol only after development adequacy and independent review.
3. **Prospective evaluation decision:** separately authorize an evaluation period
   and source-continuity/acquisition/inference plan. November 2026 is a proposal,
   with adequacy unknown; preregister an exposure-based continuation rule if needed
   before outcomes, rather than choosing months after viewing M/X counts. Keep
   development selection separate from that evaluation and leave V1/V2 unchanged.

No new-period outcome was used to choose a historical test interval. No numeric
onset parameter, rule winner, probability calibration, operational-skill claim,
PR or integration action is established by this audit.
