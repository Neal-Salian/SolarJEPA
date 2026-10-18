# Retrospective flare-event forecasting design

User-approved scope, 2026-10-18: implement, verify, independently review and
publish this milestone without further design-stage pauses. No training, V2
pilot, operational claim, PR, merge, or changes to historical artifacts.

## Architecture and existing evidence

Branch `codex/solar-flare-event-forecasting` starts at verified main `1a4991d`.
Main contains GOES readers but no forecasting package. Historical V1 and external
validation branches remain intact. Add a small UI-independent `events` package;
consume byte-pinned frozen artifacts without importing training/model code.
Reuse the external-validation maximum-cardinality matcher and onset label
support/maturity rules through narrow adapters, documenting their source.
Do not merge the entire external forecasting implementation into this milestone.

Three distinct quantities are supported: catalog onset occurrence, catalog peak
occurrence, and forecast XRS-B trajectory threshold exceedance. Thresholds C+,
M+, X+ are 1e-6, 1e-5, 1e-4 W/m2 in the 0.1–0.8 nm band. Final catalog class
depends on future peak information and is truth only, never a predictor input.
Threshold exceedance is a candidate alarm rule, not a reconstructed NOAA event.

## Coordinates and labels

Preserve existing native half-open `[issue, horizon_end)` catalog timestamp
semantics rather than silently changing historical labels. A catalog onset at
issue has zero nominal lead and cannot count as advance warning. Matching uses
an explicit minimum lead of 60 seconds by default; min=0 is descriptive detection.
No timing tolerance or timestamp snapping is implicit. The first V1 future bin
starts at issue and completes at issue+60s; the last completes at issue+1800s.

Normalize daily flsum states by declared source and flare ID, preserving partial
events and missing ends. Never derive missing start/peak/end times from IDs.
Require explicit catalog identity, satellite and calibration convention. Reject
conflicting duplicate states; retain cross-day events. Catalog labels require
explicit UTC nanosecond coordinates, full XRS-B horizon QC and candidate
start-through-peak support, including subthreshold events. Label maturity is at
least horizon end and every candidate peak-bin end. Incomplete/unsupported or
saturated candidates invalidate the opportunity instead of certifying negatives.
Known missing ends do not invalidate onset or peak occurrence by themselves.
Catalog coverage is a declared selection envelope; physical completeness remains
UNKNOWN. Retrospective labels and ongoing-event strata stay separate from inputs.

Chronological validation requires context start >= partition start, features
available <= issue, horizon end <= partition end and label maturity <= partition
end. Event start-through-peak support crossing a partition boundary is censored;
an event-disjoint study additionally needs complete event-support groups. This
milestone does not retrospectively certify V1 splits as event-disjoint.

## Decisions, matching and evaluation

An immutable protocol declares native XRS-B point-trajectory max >= threshold,
all three class thresholds, all available models, and no fitting/calibration or
selection. A predicted first threshold bin is reported as an interval and bin
completion lead, not an exact flare onset. No suppression/refractory tuning is
performed: every issued positive is an alarm; unmatched repeats count as false
alarms, with duplicate-opportunity diagnostics. This policy remains explicit.

Match alarms and catalog onsets one-to-one, maximize cardinality first and break
ties deterministically by issue/alarm ID then onset/event ID. Score only events
with a valid, mature eligible forecast opportunity under the declared lead rule;
report events outside this evaluated exposure separately. Event lists have no
true negatives. Opportunity scores separately report TP/FP/FN/TN, prevalence,
precision, recall, FAR, FPR, CSI, TSS, HSS and balanced accuracy. Undefined
denominators remain null. Report coverage, already-above-threshold context,
zero-lead onsets, missed events and nominal matching leads.

Resample whole UTC calendar blocks for descriptive opportunity-score uncertainty,
preserving missing origin positions/coverage and undefined bootstrap replicates.
Require at least two informative blocks; default 1-day blocks exceed the 150-min
context+horizon support but do not establish independence. Do not present marginal
quantiles as a joint event probability, or bootstrap intervals as predictive
uncertainty. Brier/reliability analysis awaits calibrated event probabilities.

## Artifact binding and readiness

Pin input paths, bytes and SHA-256 in a small portable config; locator roots are
CLI arguments. Reject path escapes, changed bytes, duplicate JSON keys, bad
coordinates, source/fingerprint/spec mismatches, reordered origin IDs and masks.
Bind predictions to explicit grid coordinates and labels, including class
definition, support, maturity, native timing and catalog identities. Preserve
historical label definitions in output. New report output refuses overwrite.

January's frozen 1007-origin forecasts and candidate catalog labels already exist;
use them for an exploratory, no-inference demonstration. January and August were
previously inspected. Confirmatory status and operational readiness are UNAVAILABLE.
Class scarcity, selection on future QC, catalog completeness, native reprocessing
causality, publication latency, and absence of joint event probabilities remain
limitations. Next milestone: freeze decisions on development-only support, obtain
and verify a genuinely unseen temporally/event-disjoint period, then evaluate
without adapting the rule to its labels. No data acquisition is required here.
