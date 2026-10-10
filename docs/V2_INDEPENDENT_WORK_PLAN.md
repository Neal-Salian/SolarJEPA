# SolarJEPA V2.1 independent work and coordination plan

Date: 2026-10-10, Asia/Kolkata. **PROPOSED — REQUIRES APPROVAL** for future execution/ownership. Current delivery is four research documents only.

## Isolation and immutable V1 identity

Repository: https://github.com/Neal-Salian/SolarJEPA.git. Local root: /Users/nealsalian/Desktop/SolarJEPA.

Fetched remote references and verified origin/v1 at **644648f7d555fcbcb3eed4495d37fecffdd1863a**. Created research/v2-independent-validation directly from that ref and published it with upstream origin/research/v2-independent-validation before writing documents. No merge/rebase/reset/history rewrite is part of this work. V1's executed strict source is 4a3f88227ce28dea0e885e68987282285963f38e; its audit checkpoint and existing configs/results remain immutable.

A 419-file pre-change SHA-256 snapshot covers tracked/untracked files, scientific-data directories and existing V1 outputs. Preserve pre-existing .agents/skills/paperclip/SKILL.md and docs/P1_FINAL_INTEGRATION_REAUDIT.md. The only delivery paths are the four documents linked below.

At final continuation the temporary directory was absent. This task's cached output retained 377 complete original hashes, all of which still matched, including existing untracked work and V1 artifacts. All 123 GOES files independently matched committed manifests (36,535,474 bytes); those manifests covered the remaining 42 entries, giving 419 existing files checked by the two evidence sources. The complete original 419-entry snapshot was not recoverable, so 42 checks establish manifest identity rather than a direct pre-change comparison. All 13 pre-existing local branch refs remained unchanged. This limitation is disclosed rather than claiming the temporary record is durable.

This branch is for independent research design. Never push this work to v1/main, merge another branch, force-push, delete branches or create a PR without explicit authorization. Before every push verify branch/upstream/destination and remote parent. If the research remote advances unexpectedly, stop; preserve local work and request a safe reconciliation decision. If v1 advances, record it without absorbing new code into this frozen-base design.

The checkout is shared among tools/subagents. Their read-only assignments do not provide separate filesystem isolation. For later simultaneous implementation, use independently authorized checkouts/worktrees and immutable artifact namespaces; do not let two agents switch the same checkout concurrently.

## Independent tasks versus shared decisions

| Work | Can proceed independently after authorization | Coordination required |
|---|---|---|
| Repository/source verification | Read this pinned base, inspect causal inputs, configs and tests; preserve evidence | Agree new base only through a separate integration decision |
| Statistical tooling | Develop synthetic/exposed-data paired loss/bootstrap checks and reproducible summaries | Freeze estimand, seed count, block lengths, secondary family and practical margin before tests |
| Data/provenance | Prepare bounded acquisition specifications and validate known schemas | Both contributors attest prior exposure; custodian owns hidden test bytes, QC outputs and access log |
| Models/optimization | Develop V2 loss/stage-count/control/fit-acceptance tests on synthetic/exposed data | Agree exact control budgets, search lists, failure/retry policy and validation-selection contract |
| Compute/artifacts | Measure permitted pilot RSS/time, stream immutable arrays, construct dependency/hash index | Fix resource ceiling, job schedule, retention and external artifact archive |
| Event/physics research | Read authoritative instrument/catalog papers without candidate event outcomes | Approve any new labels, event-warning contract, physical hypothesis or SoLEXS gate separately |
| Writing/review | Maintain claim/evidence maps and independent literature notes | Jointly approve claim scope from all outcomes, including negative results; choose venue after evidence |

No message has been sent to the teammate. The following split is suggested ownership, not an assertion about their current tasks or consent.

**Contributor A / independent validation lead:** exposure/data cards, calendar/QC contracts, statistical implementation, convergence acceptance, analysis/reproduction, publication claim limits. Can implement validation tooling against this pinned base after separate authorization, without editing teammate model work.

**Contributor B / ML lead:** versioned forecasting loss, controlled JEPA/supervised schedules, two cheap comparators, artifact streaming, profiling and reproducible model records. This assignment requires coordination with the teammate's actual branch/interfaces; do not duplicate or overwrite unknown work.

Cross-review A's masks/analysis with B and B's initial states/losses/predictions with A. Share frozen schema/config/seed/artifact contracts, not mutable output directories. No contributor learns one candidate test's scores and tunes another.

## Likely integration conflicts and avoidance

Likely future shared paths are training/jepa.py, forecasting/statistical.py, experiments/v1.py/provenance.py, requirements locks, forecast contracts and runner/output schemas. These are risks inferred from the design, not changes made here. V2 should have versioned entry points/configurations and preserve V1 defaults; exact file allocation awaits a separately approved implementation plan and knowledge of teammate work.

Before parallel coding, compare current branches and proposed path ownership; agree API/schema, dependency and test contracts. Avoid global changes to V1 loss, quality or acceptance semantics. Never copy a new model into V1 or reinterpret historical reports as if V2 checks had existed then. Cross-branch integration and destination pushes require explicit authorization and independent verification.

## Review checkpoints and unresolved decisions

1. **Design review:** both contributors approve/resolve the protocol decision register, one-month fold scope, holdout exposure and resources. This documentation commit is not that approval.
2. **Foundation review:** independently test closed support, train-only normalization, exact dex loss, paired stage/RNG counts, failure preservation and statistical arithmetic before acquisition.
3. **Freeze review:** sign code/config/environment/data/access hashes and artifact locations; all fold selection rules fixed before test access.
4. **Pre-unseal review:** custodian verifies every primary model is complete and frozen; no unauthorized test exposure. A failed gate pauses release.
5. **Scientific review:** inspect all primary/secondary results, sensitivity/negative evidence, assumptions and measured compute; choose the claim the evidence actually supports.
6. **Reproduction review:** fresh-environment metric/inference replay and one approved training repeat; document discrepancies rather than suppress them.

Unresolved decisions are enumerated in the [experimental protocol](V2_EXPERIMENTAL_PROTOCOL.md), with compute gates in the [execution plan](V2_RESEARCH_EXECUTION_PLAN.md). Candidate freshness, actual data quality/activity, practical thresholds, RAM and inference validity remain unknown/proposed. No new scientific data was downloaded, no model trained and no V2 implementation made during this design.

## Independent design review record

Three read-only reviewers independently examined actual source/artifacts: temporal/instrument methodology, seed/statistical design, and model/budget fairness. The coordinator independently recomputed V1 seed effects and checked primary literature; prior audit conclusions were challenged rather than accepted automatically. Review corrections and unresolved limitations are incorporated into the four documents, not historical V1 reports.

Review focus includes falsifiability, possible hidden holdout exposure, seed-power limitations, shared bootstrap draws, fixed-period inference, nonsmooth calibration statistics, matched update opportunities, strict variance acceptance, weak TCN receptive fields, and realistic memory/storage. Any unresolved substantive criticism blocks the affected execution/claim until approved; it does not justify fabricating certainty.

Final review corrected pooled M+ weighting and all-endpoint empty-resample handling, made the calibration-band transformation explicit, separated observed runtime gates from loss inference, fixed the linear shuffle schedule and bounded Monte Carlo checks to development. It also clarified annual 2025 catalog acquisition and catalog-assigned start times. All three reviewers rechecked the revisions and found no remaining material correction. This is qualified review of document coherence, not approval to execute or evidence of achieved precision, fresh holdouts or valid bootstrap coverage.

Deliverables: [experimental protocol](V2_EXPERIMENTAL_PROTOCOL.md), [execution plan](V2_RESEARCH_EXECUTION_PLAN.md), [publication strategy](V2_PUBLICATION_STRATEGY.md), and this independent work plan. Publish only this research checkpoint, then stop for review.
