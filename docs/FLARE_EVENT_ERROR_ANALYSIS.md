# Exposed January event-error analysis

Executed 2026-10-18 from `16b975f`, without fitting, inference, source changes or
rule selection. **OBSERVED** results below come from the immutable inputs pinned
in `configs/events/january2025_frozen.json`, validated by the unchanged frozen
evaluator before diagnostics. January is already exposed. This is error analysis,
not evidence of independent or operational flare prediction.

## What the 4/36 result means

The three finetuned JEPA seeds and persistence hit exactly the same four eligible
M+ onsets. Those issue times already have last-context flux above M1.0. Hits are
clustered on January 3–4 and have nominal issue-to-onset leads of 2, 14, 20 and
4 minutes. These are not four independent demonstrations of precursor learning.
All three seeds have 32 misses; all 32 originate below M level and have forecast
maxima below M. Of these, **22** have observed M-level flux within the horizon;
**16** have the class-defining catalog peak outside it. These subsets overlap.
The remaining ten misses never attain M-level flux inside that horizon.

**INFERRED:** the point trajectories often continue recent flux rather than
anticipating a sharp rise. This is a behavior of these frozen outputs; it does
not identify whether representation, loss, training event imbalance, or capacity
caused it. No retraining/ablation was performed. Training on flux pinball and
selecting flux checkpoints does not establish onset discrimination.

| Model | Hits / eligible | Misses | Onset false alarms | False alarms with real future M flux | False alarms already above M at issue |
|---|---:|---:|---:|---:|---:|
| Persistence | 4 / 36 | 32 | 23 | 23 | 23 |
| JEPA seed17 | 4 / 36 | 32 | 26 | 24 | 23 |
| JEPA seed29 | 4 / 36 | 32 | 23 | 22 | 22 |
| JEPA seed43 | 4 / 36 | 32 | 22 | 21 | 21 |

Most onset false alarms therefore coincide with real flux exceedance. They are
not all spurious flux predictions: a continuation/decay forecast can be correct
for flux and false for **new catalog onset**. Known catalog evolution accompanies
15/13/12 of the JEPA false alarms. Every JEPA false alarm also has some unresolved
prior catalog end in the selected history. Those flags overlap; neither proves
continuous physical activity. Unknown ends must not be silently filled.

JEPA false alarms per eligible exposure day are 1.286, 1.138 and 1.088 for
seeds17/29/43; issued-horizon warning fractions are 2.99%, 2.69% and 2.59%.
These use the preserved eligible exposure definition, not 31 calendar days.
Paired event comparisons against persistence show four both-hit and 32
both-miss events, with zero model-only or persistence-only hits for every
finetuned seed. These are paired descriptive outcomes without significance
or independent-event uncertainty claims.

## The three X events

All are missed at the X threshold. The X1.1 event is nevertheless an M+ hit;
"missed X" must not be interpreted as "no lower-class alarm."

| Catalog onset UTC | Class | Issue-to-onset | Catalog peak after issue | Observed horizon maximum W/m² | JEPA forecast maximum range W/m² | Diagnosis |
|---|---|---:|---:|---:|---:|---|
| Jan 3 11:29 | X1.2 | 29 min | 39 min | 2.939e-6 | 2.884–2.918e-6 | Onset is inside the horizon, class attainment/peak outside; even observed horizon flux never reaches X |
| Jan 3 22:32 | X1.1 | 2 min | 11 min | 1.144e-4 | 1.130–1.209e-5 | Within-horizon amplitude underprediction, roughly one tenth of observed maximum |
| Jan 4 12:35 | X1.8 | 5 min | 18 min | 1.864e-4 | 2.411–2.471e-6 | Within-horizon amplitude underprediction, roughly 1.3% of observed maximum |

A horizon-max alarm cannot solve the eventual-class onset task by construction
when class attainment is outside the horizon. Conversely, the latter two events
show genuine horizon forecast errors. Extending a horizon after seeing January
would define another experiment, not correct the preserved protocol.

## Matching, exposure and lead sensitivity

The preserved matcher maximizes one-to-one hit cardinality. There are **zero**
duplicate eligible M+ alarms for these finetuned seeds. In this nonoverlapping
30-minute issuance selection, repeat matching is therefore not the explanation
for the 22–26 false alarms. Adding suppression now would change the decision
policy; it cannot be presented as a correction to the old score.

There are 43 aligned M+ catalog events. Four lack any retained onset-containing
forecast; three start exactly at issue and are censored from 60-second advance
scoring. The 36 eligible events are the score population. Excluded future-QC
windows are not valid negative forecasts or deployment availability evidence.

Post hoc lead sensitivity at the original M threshold, identical hit counts
across JEPA seeds (false alarms remain 26/23/22 respectively):

| Minimum nominal lead | Eligible events | Hits | Misses | Eligible origins |
|---:|---:|---:|---:|---:|
| 0 min | 39 | 4 | 35 | 1007 |
| 1 min | 36 | 4 | 32 | 1004 |
| 5 min | 31 | 2 | 29 | 999 |
| 10 min | 22 | 2 | 20 | 990 |
| 15 min | 12 | 1 | 11 | 980 |

Eligibility changes with the lead constraint. A falling miss count here does
not establish better prediction. All leads are nominal catalog timestamps minus
issue; physical timing uncertainty and historical delivery latency are UNKNOWN.

## Threshold sensitivity without selection

Factors multiply the **decision flux threshold** only. Event truth remains M+,
and all 36 eligible events remain in every row. Every predeclared diagnostic grid
point is reported; none is selected or proposed for deployment.

| Factor × M1.0 | seed17 hits / false alarms | seed29 hits / false alarms | seed43 hits / false alarms |
|---:|---:|---:|---:|
| 0.50 | 8 / 96 | 10 / 94 | 10 / 101 |
| 0.75 | 5 / 46 | 6 / 45 | 4 / 42 |
| 1.00 | 4 / 26 | 4 / 23 | 4 / 22 |
| 1.25 | 2 / 21 | 2 / 19 | 2 / 16 |
| 1.50 | 2 / 16 | 2 / 15 | 2 / 12 |
| 2.00 | 2 / 9 | 2 / 11 | 1 / 9 |

**INFERRED:** threshold movement trades sensitivity for an already large alarm
burden and cannot by itself reconcile onset and exceedance. This is not a
development comparison. No claim is made about thresholds outside this grid.

## Reproduction and uncertainty

`scripts/diagnose_flare_events.py` consumes the same two explicit immutable
artifact roots as the existing evaluator. It verifies all eight resource byte
identities, semantic fingerprints, catalog/source/coordinate/QC lineage and all
22 models; it refuses output overwrite. It performs no downloads or inference.

```bash
python scripts/diagnose_flare_events.py \
  --forecast-root "$FORECAST_ROOT" --label-root "$LABEL_ROOT" \
  --output results/events/january2025-diagnostics.json
```

Use an installed snapshot of this branch in the documented dependency environment.
The JSON contains all models' legacy counts and window uncertainty, M/X event
identities with every retained onset opportunity, onset/peak/maximum timing,
log-flux errors, every false alarm's evidence, and full threshold/lead tables.
Max-bin timing uses the first tied native **bin start**, not a physical onset.
Catalog peak values and observed forecast-bin maxima are separate quantities.

Existing UTC-day block intervals describe binary opportunity metrics. They are
not event uncertainty bounds. Event intervals are explicitly `NOT_ESTIMATED`;
event dependence, rematching and boundary handling need a frozen design. No
calibrated onset probability, reliable X skill, or operational performance is
established. See [the blocked rule specification](ONSET_RULE_SPECIFICATION.md)
and [exposure audit](ONSET_EXPOSURE_AUDIT.md).

## Event ledger

All aligned M+ events follow, including the X events and events outside exposure.
The forecast column uses seed17 solely as an identifiable diagnostic trajectory;
the JSON includes all 22 models and no model is selected. All three finetuned
seeds have the same event hit/miss set. Flux columns are in **10⁻⁶ W/m²**;
onset and peak lags are minutes. An absent opportunity is not a model miss.

| Event ID (catalog prefix omitted) | Onset UTC | Class | Result | Onset lead | Peak minus onset | Last context | Predicted max | Observed max | Peak in horizon |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 202501010435 | 01-01 04:35 | M1.1 | miss | 5 | 10 | 4.518 | 4.470 | 11.358 | yes |
| 202501011512 | 01-01 15:12 | M1.0 | miss | 12 | 12 | 3.227 | 3.322 | 10.249 | yes |
| 202501011805 | 01-01 18:05 | M1.2 | miss | 5 | 12 | 6.727 | 6.403 | 12.511 | yes |
| 202501012132 | 01-01 21:32 | M1.1 | miss | 2 | 9 | 6.702 | 7.119 | 11.644 | yes |
| 202501021718 | 01-02 17:18 | M1.1 | miss | 18 | 22 | 2.871 | 3.066 | 6.627 | no |
| 202501031129 | 01-03 11:29 | X1.2 | miss | 29 | 10 | 2.812 | 2.918 | 2.939 | no |
| 202501032154 | 01-03 21:54 | M2.3 | miss | 24 | 18 | 4.283 | 4.005 | 4.218 | no |
| 202501032232 | 01-03 22:32 | X1.1 | hit | 2 | 9 | 12.068 | 11.383 | 114.413 | yes |
| 202501032314 | 01-03 23:14 | M1.9 | hit | 14 | 10 | 27.434 | 23.898 | 25.531 | yes |
| 202501032350 | 01-03 23:50 | M5.9 | hit | 20 | 6 | 17.924 | 20.872 | 59.609 | yes |
| 202501040034 | 01-04 00:34 | M1.5 | hit | 4 | 2 | 10.949 | 10.020 | 15.998 | yes |
| 202501040458 | 01-04 04:58 | M7.7 | miss | 28 | 20 | 3.325 | 3.088 | 3.260 | no |
| 202501041235 | 01-04 12:35 | X1.8 | miss | 5 | 13 | 2.332 | 2.457 | 186.400 | yes |
| 202501042308 | 01-04 23:08 | M2.1 | miss | 8 | 18 | 3.071 | 2.858 | 21.688 | yes |
| 202501050214 | 01-05 02:14 | M4.1 | miss | 14 | 25 | 2.712 | 2.867 | 17.049 | no |
| 202501050704 | 01-05 07:04 | M2.1 | miss | 4 | 14 | 6.781 | 4.479 | 21.337 | yes |
| 202501050908 | 01-05 09:08 | M4.1 | miss | 8 | 28 | 3.284 | 3.381 | 26.342 | no |
| 202501051519 | 01-05 15:19 | M2.5 | outside_evaluated_exposure | — | — | — | — | — | — |
| 202501060130 | 01-06 01:30 | M3.1 | outside_evaluated_exposure | 0 | 22 | 1.424 | 1.498 | 31.808 | yes |
| 202501060335 | 01-06 03:35 | M1.4 | miss | 5 | 15 | 1.537 | 1.620 | 14.564 | yes |
| 202501061612 | 01-06 16:12 | M4.9 | outside_evaluated_exposure | — | — | — | — | — | — |
| 202501072235 | 01-07 22:35 | M1.1 | outside_evaluated_exposure | — | — | — | — | — | — |
| 202501090018 | 01-09 00:18 | M1.1 | outside_evaluated_exposure | — | — | — | — | — | — |
| 202501170201 | 01-17 02:01 | M1.3 | miss | 1 | 10 | 4.422 | 4.861 | 13.046 | yes |
| 202501170308 | 01-17 03:08 | M1.1 | miss | 8 | 12 | 6.544 | 5.399 | 11.620 | yes |
| 202501170910 | 01-17 09:10 | M2.0 | miss | 10 | 9 | 1.982 | 2.042 | 20.581 | yes |
| 202501171119 | 01-17 11:19 | M1.5 | miss | 19 | 18 | 2.236 | 2.429 | 3.519 | no |
| 202501171324 | 01-17 13:24 | M7.4 | miss | 24 | 11 | 4.031 | 4.384 | 4.319 | no |
| 202501171842 | 01-17 18:42 | M2.1 | miss | 12 | 8 | 4.730 | 3.656 | 21.038 | yes |
| 202501171944 | 01-17 19:44 | M1.8 | miss | 14 | 5 | 6.006 | 7.737 | 18.684 | yes |
| 202501172200 | 01-17 22:00 | M1.0 | outside_evaluated_exposure | 0 | 5 | 3.077 | 2.914 | 10.814 | yes |
| 202501180044 | 01-18 00:44 | M1.7 | miss | 14 | 14 | 2.989 | 3.025 | 17.343 | yes |
| 202501180300 | 01-18 03:00 | M1.1 | outside_evaluated_exposure | 0 | 7 | 7.493 | 6.892 | 11.669 | yes |
| 202501190328 | 01-19 03:28 | M2.4 | miss | 28 | 4 | 1.673 | 1.701 | 2.761 | no |
| 202501211008 | 01-21 10:08 | M3.3 | miss | 8 | 31 | 2.209 | 2.287 | 26.940 | no |
| 202501221045 | 01-22 10:45 | M1.3 | miss | 15 | 23 | 3.322 | 3.407 | 10.944 | no |
| 202501242048 | 01-24 20:48 | M2.7 | miss | 18 | 16 | 2.761 | 2.981 | 17.339 | no |
| 202501270752 | 01-27 07:52 | M2.6 | miss | 22 | 20 | 4.233 | 4.516 | 4.307 | no |
| 202501281941 | 01-28 19:41 | M1.7 | miss | 11 | 4 | 2.187 | 2.177 | 17.091 | yes |
| 202501290336 | 01-29 03:36 | M1.0 | miss | 6 | 32 | 1.755 | 1.826 | 5.569 | no |
| 202501310548 | 01-31 05:48 | M1.0 | miss | 18 | 22 | 2.794 | 2.619 | 6.701 | no |
| 202501311340 | 01-31 13:40 | M6.7 | miss | 10 | 26 | 2.249 | 2.133 | 56.232 | no |
| 202501312014 | 01-31 20:14 | M1.8 | miss | 14 | 9 | 1.968 | 2.095 | 18.376 | yes |

Catalog prefix: `noaa-ncei-science-flrpt-2025-v1-0-1`. The three outside-exposure rows with onset lead zero are advance-censored; the other four have no retained onset-containing origin. No missing observation is synthesized.
