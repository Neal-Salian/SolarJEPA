# Flare-event milestone verification

Executed 2026-10-18 on `codex/solar-flare-event-forecasting`, isolated from verified
main `1a4991d`. No PR, merge, main push, training, inference or V2 pilot was part
of this milestone. The original checkout's two untracked items were preserved.

## Executed checks

| Check | Observed result |
|---|---|
| Main baseline `python -m pytest -q` | 166 passed, one warning |
| Final feature `python -m pytest -q` | **270 passed**, one warning, 36.08 seconds |
| Test-first defect checks | Missing feature and specific scientific/provenance regressions failed before implementation/fixes, then passed |
| Installed wheel | Built and installed with `pip install --no-deps --no-build-isolation --target .cache/event-install .` |
| Installed imports outside checkout | All four events modules loaded from installed snapshot and matched source bytes |
| Installed CLI outside checkout | Verified all pinned inputs; 1007 origins, C194/M39/X3, 22 models; no fitting or inference |
| Deterministic real run | All class reports exactly equal between reviewed source and installed execution |
| Native flsum reconstruction | 28 IDs; one partial start/peak, seven unknown ends, no invented states |
| Preservation | Three finetuned checkpoint SHA-256 values rechecked against read-only audit; unchanged |
| Output refusal | Deterministic CLI test executes real evaluation and rejects overwriting its existing report |
| Storage/whitespace | `git check-ignore -v` protects reports, install cache and raw science paths; `git diff --check` clean |

The one warning is the pre-existing runtime warning that `numpy.ndarray` size
differs from the C header expectation during a NetCDF-related test. No tests
failed. No dependency upgrade was attempted as an unrelated environment change.

The installed run used Python 3.13.3, NumPy 2.2.6 and the existing dependencies.
The existing environment's default installed SolarJEPA snapshot lacks this new
package; new imports require installing this branch or selecting the verified
isolated installation. An early ad hoc import omitted that locator, failed with
ModuleNotFoundError, and was rerun successfully against the installed snapshot.
Pytest's configured source path alone was not used as installation evidence.

Local ignored report: `results/events/january2025-installed.json`, 9,307,457 bytes,
SHA-256 `73d47257ef5b648cf2d39ddb0ec6e5aa62fb005a79528f1b9b12fe919169e543`.
It records input identities, config/policy identities, runtime and executed module
source hashes. Generated reports and science/model artifacts are not committed.
The pinned config and documentation are the portable reproduction entry point.

## Independent reviews

Research subagents audited primary NOAA/instrument documentation and existing
code/artifacts. A subagent implemented scoring/matching and their tests. A fresh
scientific reviewer and a separate fresh code reviewer inspected the integrated
implementation, with focused adversarial probes and scoped re-review of fixes.
An earlier design reviewer hit a service usage limit; its incomplete attempt is
not counted as a successful review.

Resolved review findings include lead/denominator alignment, full label and
support binding, explicit calibration for empty catalogs, catalog-ID/hash conflicts,
canonical class magnitudes, preserved excluded candidate slots, exact model cohort,
historical prediction/protocol/input fingerprints, mandatory preparation lineage,
incomplete peak flux, mixed boolean values and exhausted event iterators. No
important code or blocking scientific findings remained in the final reviews.
The coordinator subsequently ran the complete suite and real installed CLI.

## Scientific interpretation and limits

This validates deterministic code and faithful adaptation of already inspected,
byte-pinned research artifacts. It is not a new independent reconstruction of
all original raw-data processing, a completeness certification, or an authenticity
attestation. V1 split event groups remain empty; this milestone does not claim
the old experiments were event-disjoint. The generic labeler enforces chronological
context/horizon/class-maturity support, but future experiments need full event
grouping and an unexposed test period.

**Verdict:** ready for exploratory retrospective event research, with weak fixed-rule
M-event discrimination, missed X events, and documented false alarms. Confirmatory
validation, operational delivery/processing causality, physical detection completeness
and calibrated event probabilities remain unestablished. See the scientific
[protocol, observed results and next milestone](FLARE_EVENT_FORECASTING.md).
