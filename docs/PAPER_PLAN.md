# Paper plan and minimum evidence

Working title: **Calibration-aware latent forecasting of solar X-ray dynamics
from Aditya-L1**. Retain “physics-informed” only if the physical constraint
survives validation; retain “generative” only with a tested stochastic decoder.
No venue or acceptance claim.

1. **Abstract:** task, data period, honest design, quantified findings when
   available, uncertainty and limitations. No invented results now.
2. **Introduction:** why forecast radiation trajectories and onset warnings;
   full-disk observability limits; precise hypotheses and contribution.
3. **Related work:** X-ray forecasting, calibration, latent SSL/TS-JEPA/Phys-JEPA,
   probabilistic numerical models and LLM counterevidence; distinguish adaptation.
4. **Dataset:** source/license/version; measured coverage, quality/exclusions,
   calibration and timestamps; catalogue construction and independent events.
5. **Method:** notation, masked patch encoder, EMA/predictor/decoder, uncertainty,
   physically justified observation model and its applicability limits.
6. **Experimental setup:** locked temporal partitions, support purging, event
   grouping, matched training/tuning budgets, common origins and compute.
7. **Results:** all eligible periods, baseline table, horizon/regime calibration,
   independent-event warning/lead time and paired uncertainty.
8. **Ablations:** latent versus supervised/reconstruction; resolution/physics
   factorial, conventional physical control; justified spectral/particle tests.
9. **Discussion:** practical warning lead time versus continuing events,
   failure cases, missingness, representation evidence and what it cannot mean.
10. **Limitations:** short mission interval, rare X events, full-disk ambiguity,
    calibration/label uncertainty, retrospective latency, domain shift, compute.
11. **Conclusion:** supported findings, including negative results; next tests.

Minimum evidence for a credible full study:

- Reproducible **real Aditya** extraction with response/quality/time audit, a
  versioned manifest, and sufficient independent evaluation events to make
  uncertainty informative. NOAA-only EDA is not this evidence.
- One untouched later period, plus development walk-forward/regime sensitivity.
- Persistence, linear/statistical, ARCH/GARCH adequacy results, and competitive
  small neural controls; matched supervised backbone for JEPA.
- At least three seeds for retained neural comparisons, paired dependent-data
  CIs, no superiority claim from one training run or a lucky period.
- Continuous and calibrated probabilistic results, with onset warning evaluated
  separately from flare evolution. Full confusion denominators and prevalence.
- Required 2×2 ablation only if physical constraint is scientifically supported;
  otherwise publish the narrower honest method, not empty “physics” experiments.
- Failure-case figures, data exclusions, compute totals, all trial configs,
  environment/commit hashes and accessible reproduction scripts.

Planned figures: coverage/quality calendar; spectral lightcurves with true
forecast issue boundaries; architecture; lead-time skill; reliability and
interval coverage by regime; paired effect-size plot; representative failures.
Planned tables: dataset inventory; target/split event counts; baseline results;
ablations; parameter/time/VRAM cost. A calibration or particle negative result
is part of the scientific record, not removed from the paper.

Approval decisions: narrow title/task; access to calibrated SoLEXS; whether
particle fusion warrants its cost; event sufficiency and exact split periods;
physical observation model; runtime caps; optional Qwen priority. Approval
authorizes a later implementation phase, never retroactively creates evidence.
