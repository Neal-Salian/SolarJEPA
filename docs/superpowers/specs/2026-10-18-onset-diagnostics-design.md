# Onset diagnostics and freeze-readiness design

The user authorizes research, implementation, testing and independent review from
`16b975fa945daaf4ce2601af444f923f311878d8`, on a new isolated branch, with no PR
or integration. This milestone diagnoses existing forecasts; it cannot train,
rerun inference, execute the V2 pilot, or change V1/V2 protocols.

## Scientific contract

January 2025 and August 2024 are exposed research periods. January threshold,
lead and matching sensitivity is descriptive only: enumerate a declared grid,
report every result, select no winner and feed no January statistic into a rule.
Preserve all frozen source identities and the existing evaluator unchanged.
Retrospective catalog onset, class attainment, peak and publication are distinct.
No forecast-bin crossing is presented as a catalog onset prediction.

Keep development evidence separate from diagnostic evidence. A usable onset rule
requires verified development forecasts, catalog coverage, event-disjoint support,
causal feature/label maturity, and a predeclared selection objective. If these are
missing, freeze the **blocked specification and provenance**, not unsupported
numeric parameters. Never fill a scientific unknown with an assumed value.

## Implementation

1. Add `events/diagnostics.py` and a read-only CLI. Reuse the existing frozen
   evaluator for byte/semantic validation. Report all models, event IDs and
   exposed/unexposed eligibility, each M+/X+ opportunity's predicted/observed
   maxima and timing, onset-to-peak lag, issue-to-onset lead, last-context flux,
   error and descriptive catalog evolution. Explain false alarms by observed
   flux exceedance, background and catalog state with overlapping flags.
   Decompose misses into below-threshold trajectories, onset/class attainment
   outside horizon, and matching/exposure limitations without causal overclaims.
   Threshold and lead sweeps retain native labels and cannot select a rule.
2. Add `events/evaluation.py` for prospective chronological event-disjoint split
   auditing. Validate exact integer support, unique IDs, causal feature
   availability and label maturity. Purge windows crossing a partition, optional
   explicit embargo, and shared event support/groups. Unknown event support must
   prevent certification; empty group declarations are not evidence of safety.
   This utility does not alter or retrospectively certify V1 splits.
3. Add synthetic boundary/regression tests before implementation; execute the
   real immutable January artifacts deterministically and validate legacy counts.
   Add provenance, installed import/CLI smoke, preservation and storage checks.
4. Publish error analysis, exposure ledger, blocked or defensible rule spec,
   verification evidence and exact next milestone. A genuinely unseen test
   period needs positive exposure/provenance evidence; no such period is asserted
   merely because a file or report is absent.

## Rule design boundary

Compare candidate onset-specific formulations using development evidence only:
causal rise/transition discrimination with an explicit ongoing-event policy,
episode formation, lead range and class-occurrence label; alternatively a
development-calibrated onset classifier. Flux exceedance remains a comparator.
No default rise threshold, refractory duration, event probability or selected
model is invented here. A candidate family is not a frozen empirical rule.

## Evaluation and uncertainty

Keep natural test prevalence, event recall/precision/CSI and false alarms per
eligible day; window TN metrics are a separate estimand. Report M and X counts,
missed events, all censoring, paired model comparisons and null denominators.
Existing UTC-block percentiles describe window sampling uncertainty only. Event
uncertainty requires dependence-aware event/block resampling with rematching and
boundary handling; do not relabel window intervals as event confidence bounds.
No independence or calibrated-probability claim follows from marginal quantiles.

## Alternatives and choice

Replacing the old threshold after looking at January would contaminate selection.
Retraining an onset model would exceed scope. Add deterministic diagnostics and
prospective safeguards now; stop rule freezing if development provenance fails.
The user's explicit execution instruction supersedes repeated skill approval
handoffs. Existing scientific approval gates and preservation rules still apply.
