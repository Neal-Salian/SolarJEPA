# Independent code and scientific review

Review date: 2026-10-18. Worktree: `codex/flare-onset-diagnostics` from `16b975f`.
Reviewer performed no implementation edits, training, inference, acquisition,
V2 pilot, protocol changes, commits, pushes, PR creation or integration.

## Verdict

**Code/specification: PASS for the authorized diagnostic and prospective-audit scope.**
No unresolved P0/P1/P2 correctness or scientific-integrity findings identified in
current source and final scientific documents. This verdict does not certify the
historical V1 split, empirical onset-rule validity or model skill.

**Scientific rule readiness: BLOCKED, appropriately.** The missing verified
full-cohort development forecast/catalog bundle is a scientific stop condition.
The readiness JSON freezes that blocker/provenance, with null numeric parameters
and no selected model; it does not pretend to be an executable onset rule.

## Review coverage

Read design, plan, initial review diff, split implementation report, diagnostics,
prospective split auditor, CLI, their tests, preserved frozen evaluator/matcher,
rule specification/readiness JSON, final error analysis and exposure audit.
Inspected the current uncommitted diagnostic reporting delta after coordinator
correction. Read original V1 runner/config in solar-flux-prediction to independently
check validation/test generation and persistence claims.

No full suite was rerun by this reviewer: coordinator owns final full verification,
installed import/CLI replay, preservation, index/ignore and remote checks.

## Resolved reporting finding

Initial generated model records omitted actual matching leads, false alarms per
eligible day, warning fraction and an explicit paired model comparison, despite
the design's reporting contract. Coordinator added preserved `matched_events`,
legacy false-alarm/warning rates and paired persistence event-hit/miss ID sets.
Reviewed the correction: same eligible event populations are checked before
pairing, all four paired cells are explicit, and paired uncertainty remains
`NOT_ESTIMATED`. Focused updated tests pass. No remaining action on this finding.

## Executed independent verification

1. Current `PYTHONPATH=src .../.venv/bin/python -m pytest tests/test_event_diagnostics.py -q`:
   **8 passed in 0.38s**. No training or inference test was invoked.
2. Independently inspected generated January JSON across all **22 models**:
   M+ qualified/eligible counts are **43/36**; X+ **3/3**. Every threshold-grid
   row retains baseline event denominator and eligible days. Five distinct M+
   event-hit sets exist across the full cohort; X+ has one common (empty) hit set.
   This check used the existing source diagnostic JSON before the final reporting
   field additions; coordinator must regenerate final source/installed reports.
3. Direct boundary probe of `_evaluation`: zero lead includes an onset at issue,
   horizon end is excluded, and an early event censors its whole origin under
   positive minimum lead, including any later event in that same origin. This is
   conservative and matches the explicitly preserved evaluator semantics.
4. **300 randomized synthetic split probes passed** input-permutation invariance,
   retained full-support partition containment, and cross-partition event-group
   disjointness. No real historical split was certified.
5. `git diff --cached --check`: passed for the staged snapshot examined.

## Scientific and implementation assessment

- Eventual catalog class and onset are retained when the class-defining peak is
  outside the horizon. Forecast/observed max-bin starts are labeled separately
  from catalog onset and peak. Native XRS-B values remain W/m2; errors are log10
  flux errors, with no invented physical-onset estimate.
- Threshold sensitivity moves decisions only, retaining native class truth,
  eligibility and exposure. Lead sensitivity explicitly changes eligibility,
  rematches and reports its denominators. Neither code nor documents select a
  winning threshold/model or feed exposed January statistics into a rule.
- False-alarm flux/background/catalog flags overlap and remain descriptive.
  Unknown prior ends do not become asserted ongoing physical events. Zero/short
  lead, QC-excluded opportunities and out-of-exposure events remain explicit.
- Auditor validates exact signed integer coordinates, causal declared feature
  availability, maturity >= horizon, full context-to-maturity support, explicit
  catalog envelope, transitive overlapping groups and full group coverage.
  Half-open touching intervals remain distinct. Cross-partition support/shared
  groups and explicit window/group embargo intersections are purged.
- A complete selected-catalog declaration is a caller assertion, fingerprinted
  but not independently proven. Certification is explicitly limited to retained
  selected-catalog support; it never establishes physical completeness,
  active-region independence, actual delivery causality or V1 training exposure.
  A declared empty negative envelope can certify only this narrow support scope;
  a bare empty event list cannot. Unknown event bounds reject the audit.
- Source identities are byte-pinned and semantically validated through the
  preserved evaluator before diagnostics. CLI refuses overwrite, confines output
  to this worktree's results tree and records executed source/config/runtime
  identities. Existing evaluator and V1/V2 processing are not changed.
- Window bootstrap summaries stay window summaries; event and paired uncertainty
  are not estimated. Scarce X support, exposed period selection and operational
  availability limits are explicit. No calibrated probability is inferred from
  marginal flux quantities.

## Independent document/source checks

Original V1 source computes both held-out prediction sets but serializes only
`predictions['test']` into `test_predictions.npz`; config dates match the exposure
audit. This supports the bounded missing-development-artifact finding without
claiming universal absence. P2's limited development cohort is not relabeled the
full V1 JEPA cohort. No historical interval is called unseen from missing files.

Checked the cited [NOAA SWPC page](https://www.spaceweather.gov/products/goes-x-ray-flux):
it distinguishes begin, peak and decay-based end. Documents appropriately avoid
substituting this operational definition for the NCEI science catalog algorithm.
Checked primary abstracts for [Ahmadzadeh et al.](https://arxiv.org/abs/2103.07542)
and [Bloomfield et al.](https://arxiv.org/abs/1202.5995): their temporal-dependence,
imbalance and verification-metric topics support the qualitative safeguards;
foreign class ratios/performance are not transferred to SolarJEPA.

## Remaining limitations and completion dependency

This review is not an independent reconstruction of raw January science products,
a full filesystem inventory, an instrument calibration audit, installed-runtime
certification, or evidence of physical catalog completeness. Scientific detector
algorithm details remain a documented inherited limitation. The proposed November
2026 interval is only a future-outcome candidate, with source/coverage/power and
permission unresolved. Final regenerated deterministic reports and coordinator's
full suite/preservation/installed smoke are still required before milestone
completion. None of these limits authorizes another milestone or integration.
