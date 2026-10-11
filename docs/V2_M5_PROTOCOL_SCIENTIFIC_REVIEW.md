# SolarJEPA V2 M5.0 — independent scientific and experimental protocol review

Date: 2026-10-11. Branch `research/v2-m5-protocol-review`, base `8a9c98d` (GOES restoration, which contains M4A).
This is a **review, not an approval**. No protocol value, split, embargo, preprocessing rule or configuration was changed.
No model was trained. No GOES file outside May–July 2024 was opened. No test or external data was accessed.

Companion documents: [decision register](V2_M5_EXPERIMENTAL_DECISION_REGISTER.md),
[resource and fairness review](V2_M5_RESOURCE_AND_FAIRNESS_REVIEW.md), [handoff](V2_M5_INDEPENDENT_REVIEW_HANDOFF.md).
Evidence: [`docs/evidence/v2_m5_protocol_review_evidence.json`](evidence/v2_m5_protocol_review_evidence.json).

## 1. Verdict

**PROTOCOL_RECOMMENDATIONS_READY.** Every requested area was reviewed with executed or source evidence. The decision
register gives a recommended option for each decision.

**The pilot itself is not ready to execute.** It needs:
- owner decisions (D09, D10, D11, M5-AUG, M5-QC);
- three engineering prerequisites that do not exist yet:
  - a development-only May–July loader with a behavioural no-August test;
  - an enforcing job driver for timeouts, per-job RSS, one job per process and retry caps;
  - an amended, versioned pilot proposal with per-seed linear fits.

## 2. Method

Four independent review passes were run in separate agent contexts. Superpowers is not installed in this
environment, so equivalent structured review was used. Each pass was read-only on the repository and wrote evidence to scratch.
The coordinator spot-checked the highest-impact claims (timeouts absent from the runner, SSL fingerprint contents, the August loader path).

| Pass | Scope | Data |
|---|---|---|
| A — temporal science | Boundaries, embargo evidence, quality-control thresholds, loader gap | Restored **May–July 2024 only** (92 files); August never opened |
| B — experiment design | Seeds, fairness counts, losses, selection, λ grid, classical models | Synthetic data only; M4B code via `git archive` |
| C — compute | Resource totals with per-seed linear, 8 GB host risk, enforcement audit, M4B test count | Synthetic benchmarks plus committed real-data evidence; M4B in a temporary detached worktree (removed) |
| D — statistics, provenance, isolation | M3.1 consequences, reporting, provenance, test isolation | Static reading plus synthetic probes against archived M4B code |

**Verified starting claims:**

| Claim | Result |
|---|---|
| M4B 1,583 tests | **1,583 collected, 1,582 passed, 1 failed** at `2e3f871` in this environment. The failure is the installed-vs-checkout source identity test (the shared venv holds another branch's non-editable install). M4B documents 1,583 passed in its own isolated install; matching it here is INFERRED, not reproduced |
| GOES restoration: 123/123 verified, 177,120 rows, V1 windows reproduced | Consistent. Pass A reproduced the May–July subset exactly (132,480 rows, 0 missing or duplicate; train 3,609/327, validation 412/68; identical normalization) |
| M3.1 verdict | NO_VALIDATED_REPLACEMENT (`5e88f3a:docs/V2_M3_INFERENCE_REMEDIATION_REPORT.md:10`); M4B maps it to `INFERENCE_UNAVAILABLE` |

## 3. Temporal eligibility and leakage

**Splits.** Splits are UTC half-open intervals:

| Split | Interval | Nanosecond bounds |
|---|---|---|
| Train | [2024-05-01, 2024-07-22) | 1714521600e9 → 1721606400e9 |
| Validation | [2024-07-22, 2024-08-01) | → 1722470400e9 |

The partitions touch. The first retained origin of each partition is at 02:00, because the context must fit inside the partition.
The last origin's targets end exactly at the partition end (OBSERVED).

**Leakage checks:**

| Check | Finding |
|---|---|
| Input-context overlap across the boundary | None. Every context lies inside its partition |
| Forecast-target overlap | None. Stride 30 = horizon 30 gives disjoint targets; contexts overlap by 90 min within a partition |
| Boundary-crossing windows | None |
| Label availability | Retrospective bin end (`bin_end_earliest`, no actual-delivery array). Operational latency UNKNOWN; not an operational forecast |
| Normalization | Unique valid training bins only. Identical when recomputed from a May–July-only dataset |
| Validation selection reuse | Each of 412 validation origins scores 15 epochs per neural arm and 8 λ per linear seed. Reuse of a selection set, not leakage, but it makes selected values optimistic |
| Dependence | Real (§4). The INFERRED effective validation sample is about 100–110 of 412 origins |

**Training-window overlap.** 108,199 eligible stride-1 windows. The 20,000-window subset has mean spacing of 5.9 rows and about 96% adjacent overlap.
This is many dependent presentations, not 20,000 independent examples.

**August and January 2025.** August loads in the historical all-manifest route. January 2025 is unreachable from HEAD, M4B or M5 code paths:
its configs exist only on `origin/research/goes-external-validation`. Its exclusion is procedural, not technical (evidence D).
The M4A pilot proposal and the GOES readiness document (§6.1–6.2) relied on the all-manifest loader. This is **the review's one BLOCKER
for execution**: see M5-AUG and M5-LOADER in the register.

## 4. Embargo (D09)

Containment already prevents shared bins. The question is dependence across the boundary.

Training-only autocorrelation of raw log10 flux (XRS-A / XRS-B):

| Lag | Autocorrelation |
|---|---|
| 2 h | 0.50 / 0.59 |
| 1 d | 0.31 / 0.38 |
| 2 d | 0.25 / 0.32 |
| 5 d | 0.09 / 0.11 |

After 1-day detrending the fast component decorrelates within about 2 h (e-fold about 48 / 61 min).

**Therefore:**
- Short embargoes (150 min) remove the fast dependence almost free.
- One day matches the protocol's proposal for new folds, at 1.3% training cost when the training end is truncated.
- No tested length removes the multi-day level persistence.

Option costs are in the register. **Recommendation:** E_1d by truncating training to 2024-07-21, with E0 as a defensible alternative
for V1 comparability. **Owner decision.**

## 5. GOES quality-control policy

**Valid rule.** The V1 rule treats a minute bin as valid if 0 < sample count ≤ 60, among other checks.
In May–July, 6.54% of valid XRS-A and 1.52% of valid XRS-B bins are partial-minute averages.

**Character of partial bins:**
- Most have exactly 59 samples, carry the native particle-spike exclusion indication and are isolated.
- Bins with fewer than 45 samples sit at the edges of bad-data and instrument-mode episodes.
- The repository ignores `xrs?_flag_excluded`.

**Effect of a stricter threshold.** Normalization barely changes (≤ 0.04% for thresholds up to 59). Window support falls sharply:

| Threshold | Training origins |
|---|---|
| ≥ 30 | 3,309 |
| ≥ 59 | 2,254 |
| = 60 | 0 |

The restoration documents' wording that a threshold "would change support and normalization" overstated the normalization effect.

**Recommendation:** Policy C. Keep the V1 rule primary for comparability, add a predeclared count ≥ 30 sensitivity,
and disclose the partial-minute limitation.

## 6. Seeds, fairness, losses, selection, baselines

Detail is in the [resource and fairness review](V2_M5_RESOURCE_AND_FAIRNESS_REVIEW.md) and the register.

**Seeds:**
- The seeds are deterministic and reproducible, and every stochastic component is seeded.
- Thread count changes JEPA-family weights bitwise.
- Two seeds measure optimisation variance on one data sample (1 degree of freedom).

**Fairness.** Step counts are verified:

| Arm | Encoder+predictor updates | Head updates |
|---|---|---|
| J | 1,817 | 1,185 |
| B | 1,817 | **1,817** |
| S | 1,185 | 1,185 |

Data, normalization, windows and validation content are identical across all arms. M4B's content fingerprint catches value
changes that M4A's origin-only identity missed. Equal compute is not claimed.

**SSL artifact identity includes wall time.** A recomputed SSL artifact cannot pass the paired-cohort check. Persist one artifact per seed;
an SSL retry invalidates J and frozen J (MEDIUM).

**Loss and selection:**
- The loss is correct in dex, mask-safe and gradient-checked.
- Earliest-minimum selection is deterministic but sensitive at the 1e-12 level.
- Selected values are post-selection.

**Baselines:**
- TCN: re-verified at 44,620 parameters and a 253-bin receptive field.
- Quantile-linear: must be **per seed** (seeded shuffling changes the fit). The M4A grid lacks values below 1, so the recommended grid adds 0.01 and 0.1 and drops 10⁵.
- Classical: persistence only; ARIMA and volatility excluded while acceptance is `POLICY_UNAVAILABLE`.

## 7. Resources, failure handling and provenance

**Updated pilot totals** on the M4 host, with 2 per-seed linear fits and 20 real-data preparations:

| Scenario | Total |
|---|---|
| Optimistic | 24 min |
| Expected | 29 min |
| Conservative | 74 min |

The 7,200 s budget holds, except under the conservative case with every job retried (8,900 s).

**Enforcement gaps (HIGH, OBSERVED).** None of the following are enforced: per-job timeouts, the total budget, per-job RSS and
one job per process. Crashed jobs re-run on resume without an attempt cap.

**Provenance.** The following are recomputed or checked by code: plan dataset/split fingerprints, normalization, validation content,
the job matrix and containment. Code, data-provenance, evaluation-split and protocol fingerprints and approval status are caller-declared strings.
The minimum M5 provenance set is in the handoff.

## 8. Statistical restrictions

M3.1's verdict makes all pilot statistics **descriptive**:
- M4B's `descriptive_comparison` complies.
- `paired_comparison` remains callable, emits percentile CIs and accepts 2 seeds. In a synthetic null with 2 seeds × 10 days, it covered the nominal 95% level only 52.7% of the time.
- Pilot reporting must avoid `paired_comparison`, `run_v1` and `block_bootstrap`.
- The mandatory header and forbidden-phrase list are in M5-STATS.
- Seed-conditional, calendar-conditional and joint inference are all unsupported by 2 seeds × 1 fold × 10 days.

## 9. Findings by severity

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| R1 | **BLOCKER** (execution) | The proposed pilot route loads August via the all-manifest loader, contrary to the M4B no-test-read requirement. The GOES readiness §6.1–6.2 recommendation is superseded | D; `foundation.py:189-190`; `docs/V2_GOES_M5_READINESS.md:78-82` |
| R2 | HIGH | Guards cannot detect an all-manifest or mislabelled-calendar load. Provenance fields are unverified strings | D probes; M4B `v2_evaluation_safety.py` |
| R3 | HIGH | No per-job timeout, total budget or per-job RSS enforcement; no one-job-per-process | C; grep of M4B runner and safety modules |
| R4 | MEDIUM | Retry semantics: unlimited crash re-runs on resume; no timeout ledger outcome | C |
| R5 | MEDIUM | SSL artifact fingerprint includes wall time, so a recomputed SSL fails the cohort check | B; `controlled.py:418` |
| R6 | MEDIUM | Proposal JSONs contradict per-seed linear (`quantile_linear_fits: 1`); stale linear timeout | B, C, D |
| R7 | MEDIUM | Thread count is part of the numerical result; cross-host reproducibility UNKNOWN; comparator checks do not bind threads | B |
| R8 | MEDIUM | λ grid lacks values below 1; 10⁵ redundant; weak-range λ choice within seed noise | B |
| R9 | MEDIUM | `paired_comparison` and `run_v1` CIs remain callable; `publish_development` accepts any JSON; protocol §7 still prescribes percentile CIs | D |
| R10 | MEDIUM | A development-only loader cannot use `validate_config` or `chronological_partitions` as they stand | A |
| R11 | MEDIUM | Exposed August is called "sealed" or "untouched" in proposal and readiness text | D |
| R12 | MEDIUM | Post-selection validation values are not labelled as such in planned outputs | D |
| R13 | MEDIUM | Restoration docs overstated the normalization effect of a stricter quality threshold | A |
| R14 | LOW | Stale numbers: 117,931 eligible windows (real 108,199); ×1.25 rationale cites a 29-day validation; M4A optimistic estimates 6–18% light; linear benchmark used 5 λ | A, C |
| R15 | LOW | `PCG64(seed)` equals the SSL/warmup stream; frozen-arm `trainable_total` reports 136,332 rather than 67,948; TCN zero-width intervals; no torch version in `code_provenance`; thread defaults (`JepaConfig.threads = 8`) | B, C, D |

No finding was fixed in code here: this is a review milestone, and the fixes belong to the M5.0 implementation and an
approved amendment. Historical documents are not rewritten; supersessions are recorded in this review.

## 10. Limitations of this review

- **Host.** Measurements come from an Apple M4 with 16 GiB, not the owner's possible 8 GB host.
- **Contention.** Some synthetic timings overlapped another review pass: evidence C's first pass and evidence B's linear timings, which are marked as such. Evidence C reran the key jobs on a quieter host.
- **Synthetic evidence.** The λ-grid and fairness evidence is synthetic and cannot establish real-data optima.
- **Scripts.** Review scripts embed host-specific paths and are not committed. Their hashes are in the evidence file.
- **Exposure attestations** (D03) and the custodian (D04) are outside this review and remain unresolved.
