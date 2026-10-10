# SolarJEPA V2.1 publication strategy

Date: 2026-10-10, Asia/Kolkata. Base origin/v1 644648f7d555fcbcb3eed4495d37fecffdd1863a. **PROPOSED — REQUIRES APPROVAL.** This is a research direction, not evidence that V2 has run or a venue will accept it.

## Recommended positioning and alternatives

Recommend **C with B as the central experimental question**: rigorous probabilistic solar X-ray forecasting across separated historical periods, testing whether latent pretraining adds value under limited data/compute. A useful negative result can be a contribution if comparisons, precision and artifact availability are strong. Three selected months do not constitute a solar-cycle benchmark.

| Position | Potential contribution | Required evidence / feasibility | Unsupported-claim risk |
|---|---|---|---|
| A: JEPA representations for solar forecasting | Domain-specific representation value, if real | Stable 20-seed improvement; budget controls; frozen/random transfer evidence; pretext ablation if objective specificity claimed; perhaps more temporal scope | High: standard EMA/patch/mask components are prior art; a single backbone or tiny conditional gain is weak methodological novelty |
| B: controlled SSL versus supervision under limited data | Reproducible conditional or negative evidence about when pretraining helps | Exact matched architecture/data/forecast objectives; update/cost controls; failed/negative runs; uncertainty and bounded claim | Moderate: no global claim about all JEPA/backbones; finite precision can leave an informative but inconclusive study |
| C: probabilistic flux forecasts with temporal validation | A transparent scientific/application benchmark and calibration/quality analysis | Common-origin comparators, independent chronological folds, honest marginal/conditional calibration, reproducible artifacts | Moderate: continuous flux continuation is not flare-onset warning or prospective deployment |

A possible working title is “Does latent pretraining improve probabilistic solar X-ray forecasts? A controlled temporal validation study.” This is a proposed title, not a first-in-field claim.

## Related-work evidence and novelty limits

Targeted primary-source reconnaissance was performed on 2026-10-10. Paperclip arXiv search/readouts supplied discovery and text, with primary arXiv/official sources checked separately; it is not comprehensive solar-physics coverage. Abstract/preview access is identified below; no prior score was independently reproduced or transferred into a leaderboard.

| Primary source | What it establishes for positioning |
|---|---|
| [Assran et al., I-JEPA (2023)](https://arxiv.org/abs/2301.08243) | Non-generative latent target prediction predates SolarJEPA |
| [Verdenius et al., LaT-PFN (2024)](https://arxiv.org/abs/2405.10093) | JEPA/PFN time-series forecasting is prior work; relevant text read through Paperclip |
| [Ennadir et al., Joint Embeddings Go Temporal](https://arxiv.org/abs/2509.25449) | Temporal JEPA classification/forecasting is established; record notes a NeurIPS 2024 workshop and 2025 arXiv posting |
| [Feng et al., JEPA pretraining for time-series forecasting (2026 preprint)](https://arxiv.org/abs/2609.31680) | Abstract reports backbone-dependent gains/degradation; SolarJEPA must isolate its particular domain/recipe rather than repeat general superiority |
| [Nie et al., PatchTST](https://arxiv.org/abs/2211.14730) | Patched supervised/SSL temporal forecasting is prior art; a relevant stronger comparator family |
| [Huang et al., short-term X-ray flux forecasting (2026)](https://www.sciencedirect.com/science/article/pii/S2213133726001083) | Publisher search preview identifies GOES forecasting comparisons; full paper access was unavailable, so detailed novelty overlap remains unassessed |
| [Barnes et al., All-Clear comparison (2016)](https://arxiv.org/abs/1608.06319) | Common data/event definitions/verification matter; its event task differs from continuous flux loss |
| [Nie et al., Phys-JEPA (June 2026 preliminary preprint)](https://arxiv.org/abs/2606.16076) | Explicit latent physical/residual constraints are already being studied elsewhere; text read via Paperclip. This does not supply a validated solar physical constraint |
| [Gneiting and Raftery (2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf) | Proper scoring/calibration/sharpness principles justify probabilistic evaluation |

Paperclip's Phys-JEPA index gives June 16 while the primary arXiv history gives June 15; cite the primary record/year, not an invented reconciliation. Do not rely on citation counts or unreviewed preprint claims as validated performance. A broader solar/space-weather literature search and detailed reading of directly overlapping papers remain required before a first-application/novelty assertion.

## Minimum evidence before a submission decision

Complete the [protocol](V2_EXPERIMENTAL_PROTOCOL.md) and [execution-plan](V2_RESEARCH_EXECUTION_PLAN.md) gates: approved access ledger, versioned task/data definition, exact matched controls, all primary seeds, multiple fixed periods, accepted classical fits and useful simple/TCN comparators. Show uncertainty from seeds and time, practical-margin interpretation, all horizons/channels, conditional support, failures and limitations. Supply code/config/data hashes and a reachable immutable artifact archive with independent metric/inference replay and one declared training repeat.

Do not equate an interval excluding zero with publication readiness. Judge effect size, reproducibility, distinct contribution and generalization. If the practical criterion fails, accurately frame negligible, negative, seed-dependent or inconclusive pretraining value. No model must win to be reported. If precision is insufficient, explicitly state which effects remain compatible; additional studies require a new protocol, not selective extension.

## Proposed paper structure

1. Scientific problem: one-minute two-channel irradiance forecasting and the limits of translating it into flare-warning utility.
2. Related work: solar X-ray/event forecasting, probabilistic verification, temporal SSL/JEPA and limited-data controls.
3. Data/protocol: instrument semantics, quality exclusions, exposure ledger, separate chronology and immutable artifact provenance.
4. Methods: JEPA and matched controls, comparator/fit acceptance, exact budgets and selection loss.
5. Statistical plan: fixed-period estimand, paired seeds/time blocks, multiplicity, assumptions and practical threshold.
6. Results: prespecified primary/secondary tables, seed/fold heterogeneity, calibration/lead/extreme diagnostics and resources, including failed runs.
7. Reproduction/limitations: inference versus training, finite regimes, complete-case selection, retrospective latency and catalog dependence.
8. Discussion: what the result supports about this recipe; conditional conclusions and bounded future hypotheses.

Exclude “physics-informed,” “generative,” “first temporal JEPA,” “state of the art,” “operational early warning,” “validated Aditya-L1” and “cycle-wide generalization” unless separate implemented/validated evidence supports each. Units/log transforms/positive quantiles are not physical dynamics; five quantiles are not joint event probabilities or exact CRPS.

Venue selection is deliberately deferred until evidence exists. An honest application/benchmark paper or negative-result study is more defensible than an architectural breakthrough claim. Peer review cannot be predicted from implementation/test success.
