# Onset rule: scientific freeze blocked

Recorded 2026-10-18 from checkpoint `16b975f`. The preserved machine-readable
[readiness record](../configs/events/onset_rule_readiness.json) freezes the
decision **not to freeze numeric alarm parameters**. It is not executable alarm
configuration. No onset rule, selected model, calibration, rise threshold,
refractory duration or probability has been fitted or frozen in this milestone.

**OBSERVED:** the bounded inventory found saved August test predictions and
January external predictions, but no verified retained development
forecast/catalog-label bundle. V1 computed validation forecasts transiently and
persisted test forecasts. Its validation was also used for flux checkpoint
selection. Its historical event-group declarations do not establish event
separation. See the [exposure audit](ONSET_EXPOSURE_AUDIT.md).

This is a scientific blocker: substituting exposed January/August outcomes for
development support would violate the requested selection boundary. No new rule
is applied to either period. The January threshold and lead grids are explicitly
post hoc error descriptions; there is no objective optimizer or best-row output.

## Development-only design brief

The intended target is a **new catalog onset** with eventual M+ (and separately
X+) peak class, within a declared future interval. Final class may mature after
that interval. A forecast crossing of M/X irradiance within the interval is a
different target and remains a comparator. Labels must preserve native UTC
half-open coordinates, class maturity, source/calibration, quality and selection
coverage. Retrospective labels may be used for supervision/evaluation only.

Two development candidates deserve comparison, without a present preference:

- A deterministic transition rule using causal context background/rise and
  predicted change, with explicit handling of elevated/ongoing flux. Background
  above M does **not** establish an ongoing physical event or exclude a new
  catalog onset. A hard below-M gate is therefore not justified by these data.
- A separately development-calibrated onset occurrence model. This requires a
  distinct approved fitting milestone; marginal flux quantiles alone cannot
  identify a joint horizon-event probability.

The family, features, context summary length, rise criteria, model cohort,
lead interval, episode definition, suppression/rearming, thresholds, latency
assumptions and selection objective remain **UNSELECTED**. A generic rise
formula would still be an unvalidated proxy for catalog onset. No synthetic
example or January result can supply its scientific parameter provenance.

Before numeric freezing, a development-only artifact must contain immutable
forecast values, explicit issue/future grids, causal context and availability,
complete retained/excluded origins, source hashes, authoritative event labels,
class maturity and event/group supports. Preserve raw sources/checkpoints and
bind every derivation to code/config identities. If forecasts must be generated,
obtain separate authorization for inference; this milestone performs none.

## Chronology and leakage contract

Predeclare chronological development-selection, calibration (if needed) and
evaluation partitions. Include **all** known events, including subthreshold
events, when forming connected overlapping event-support groups. Associate an
origin using its full context through horizon/class-maturity support. Purge
cross-boundary support, shared groups and declared embargoes; unresolved event
ends prevent certification. Record every exclusion and group assignment.

`events.evaluation.audit_chronological_split` implements this prospective audit.
Certification concerns declared selected-catalog support only. It cannot prove
physical catalog completeness, recover unknown ends, establish active-region
independence, or erase V1's historical training/selection exposure. If auditing
the fixed checkpoint reveals a boundary event it already learned from, purging
only the new table cannot make its training event-disjoint. Report that limit;
retraining is outside this milestone.

## Imbalance, matching and uncertainty contract

Keep the natural chronological prevalence in calibration/evaluation. Report
M+/X+ event counts and per-class recall, precision, CSI, alarm count, false alarms
per eligible day, warning time and actual lead distribution. Keep window
TP/FP/FN/TN, TSS/HSS and balanced accuracy separate from event metrics, which
have no defined TN. Accuracy alone is unsuitable as a selection target. Do not
oversample/resample test events or tune a class weight on held-out outcomes.
Any development weighting/cost or alert budget must be justified and frozen
before evaluation; none is selected here.

Freeze opportunity eligibility, partial-event censoring, class-maturity support,
lead semantics, episode/rearming policy, one-to-one matching/tie policy and
exposure denominators together. Debouncing repeated alarms changes the
estimand and cannot be introduced after evaluation. A future decision should
also identify which issue time begins an episode; later issues cannot extend
its warning retrospectively without an explicitly frozen policy.

Report undefined denominators as null. Existing seed17, 1,000-replicate UTC-day
block percentiles are **window-opportunity descriptive intervals**, not event
confidence or prediction intervals. The diagnostic report labels event
uncertainty `NOT_ESTIMATED`; do not reuse the window intervals for event CSI.
Before confirmatory testing, freeze dependence-aware event/block resampling,
rematching within replicated cohorts, block-edge handling, paired model
comparisons and counts of undefined replicates. Block length must reflect
event evolution and other dependence, not only the 150-minute window length.
Three X events cannot establish stable X skill or generalization.

## Scientific readiness and exact next milestone

**READY:** deterministic error analysis of existing exposed forecasts and a
validated prospective selected-catalog split auditor.

**BLOCKED:** development-only onset rule freeze, calibrated onset probabilities,
historically unseen confirmatory evaluation, and operational prediction claims.

Next milestone: **development evidence recovery and onset-rule feasibility**.
Recover saved development predictions if they exist elsewhere; otherwise seek
separate authorization to materialize forecasts from the fixed checkpoints
without retraining. Obtain and byte-pin authoritative development event coverage;
audit model exposure, full event groups, chronology and causal availability.
Only then select an onset family/parameters on development support, freeze its
provenance and uncertainty design, and register a sealed evaluation cohort.
Do not execute the V2 pilot or alter its protocols as a shortcut.

A genuinely future candidate, 2026-11-01T00:00Z through 2026-12-01T00:00Z, has
no realized outcomes on this audit date. This identifies an unseen **outcome
period**, not an acquired/validated evaluation dataset. Source compatibility,
catalog delivery, coverage, M/X support and evaluation permission remain unknown.
Freeze any extension/stopping policy before outcomes exist; never extend only
until desired events or favorable scores appear. No historical period is
certified unseen from absence in this inventory.
