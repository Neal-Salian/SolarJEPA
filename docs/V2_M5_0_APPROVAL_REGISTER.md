# V2 M5.0 Approval Register

All 17 experimental decisions remain unresolved. This register grants no approval; `approval` is null for every entry. M5.0 authorizes verification and implementation only. A future approved protocol needs a versioned, reviewed integration; flipping a JSON flag cannot authorize the preflight entrypoint.

Configuration fingerprint: `2f095fbef7ae1e4de714110dd379a88fcc864f2caeb3eef4b1c295faf9a26b9c`.

The machine-readable source is [m5_0_approval_register.json](../configs/v2_proposed/m5_0_approval_register.json). It records each proposed policy, evidence, status, required approver, configuration fingerprint, and implementation dependency. Both historical M4A proposal files remain unchanged; [the unapproved M5 amendment](../configs/v2_proposed/m5_0_preflight_amendment.json) pins their exact bytes.

| ID | Decision | Status | Required approver | Dependency |
|---|---|---|---|---|
| D09 | Embargo | REQUIRES_APPROVAL | project scientific owner | raw partition/window calendar |
| D10 | Experimental protocol | REQUIRES_APPROVAL | project scientific owner | all pilot execution |
| D11 | Resource ceilings | REQUIRES_APPROVAL | project scientific owner | process supervisor invocation |
| DATA_ACCESS | Dataset access | REQUIRES_APPROVAL | project scientific owner | future real-data fitting |
| AUGUST | August handling | REQUIRES_APPROVAL | project scientific owner | selection guard |
| QUALITY | Quality threshold | REQUIRES_APPROVAL | project scientific owner | scientific preprocessing |
| SEEDS | Seed selection | REQUIRES_APPROVAL | project scientific owner | paired job cohort |
| BUDGETS | Training budgets | REQUIRES_APPROVAL | project scientific owner | training schedules |
| LOSSES | Loss functions | REQUIRES_APPROVAL | project scientific owner | primary and secondary cohort recipes |
| CHECKPOINT | Checkpoint selection | REQUIRES_APPROVAL | project scientific owner | validation-only selection |
| TCN | TCN configuration | REQUIRES_APPROVAL | project scientific owner | TCN jobs |
| LINEAR | Quantile-linear regularization | REQUIRES_APPROVAL | project scientific owner | quantile-linear jobs |
| CLASSICAL | Classical baseline policy | BLOCKED_ON_EVIDENCE | project scientific owner and fit-acceptance owner | complete job plan and fit-acceptance evidence |
| FAILURE_RETRY | Failure and retry handling | REQUIRES_APPROVAL | project scientific owner | supervisor/retry ledger |
| STATISTICS | Statistical reporting | REQUIRES_APPROVAL | project scientific owner | all reporting; no CI/p-values/superiority |
| TEST_PROHIBITION | Test-release prohibition | REQUIRES_APPROVAL | project scientific owner | all execution interfaces |
| REPRODUCIBILITY | Execution provenance and freeze | REQUIRES_APPROVAL | project scientific owner | future approved pilot entrypoint |

D09 remains pending: the inherited half-open partitions touch, and window support is fully contained within each partition. M5.0 verifies that behavior without approving a zero embargo. Any changed embargo/calendar requires new split identities and reviewed preprocessing, rather than silent trimming.

D10 must reconcile the independently reviewed scientific protocol with the M4B requirements. The concrete unapproved plan has 20 specified process jobs: two SSL phases, ten primary arms, two TCN jobs, two quantile-linear paths, and four separate loss-comparison jobs. Each quantile-linear path has seven lambda candidates; the historical single-fit proposal is preserved and superseded only as a pending amendment. Classical job inclusion and fit-acceptance evidence remain BLOCKED_ON_EVIDENCE, so the count excludes unresolved classical jobs.

D11 retains the proposed 4 GiB sampled worker-tree RSS ceiling, four library threads, 300/600/1800-second attempt timeouts, 7200-second total active wall budget, and one identical infrastructure retry. Synthetic enforcement evidence does not approve these budgets for the pilot.

Quality rules remain inherited: status zero, channel-specific electron bits, finite positive flux within product bounds, positive native count no greater than 60. Valid partial-minute averages remain allowed; no new threshold is silently selected.

Statistical reporting remains DESCRIPTIVE_ONLY / INFERENCE_UNAVAILABLE because M3.1 concluded NO_VALIDATED_REPLACEMENT. There is no validated CI, confirmatory p-value, significance/superiority conclusion, or new acceptance threshold. Approval cannot resurrect an invalid inference method.

August 2024 is already development-exposed and scored in V1; it is excluded by this loader and cannot become an untouched holdout. January 2025 and sealed data remain isolated. The preflight has no fitting, scoring, confirmatory, or release mode.

The separate Claude Code protocol review is outside these implementation findings. No decisions or approvals are attributed to that review.
