# Phase 1: external GOES model evaluation readiness audit

Audit date: 2026-10-13, Asia/Kolkata. **Verdict: PARTIALLY_READY.**

The frozen V1 neural models and January 2025 data have compatible numerical
contracts. Retraining and new normalization are unnecessary. The complete phase
is not yet qualified: an explicit no-refit external adapter is missing, native
science-product causality/as-issued availability remain unknown, and January
has already been inspected. No January model inference, scoring, fitting,
selection, calibration or full experiment was performed in this milestone.

This verdict separates a usable retrospective flux dataset from proof of a
causal operational forecast. It reports unresolved requirements rather than
silently weakening them. The proposed analysis is in
[the scientific protocol](PHASE1_GOES_EVALUATION_PROTOCOL.md); exact future work
and approval gates are in [the implementation plan](superpowers/plans/2026-10-13-goes-external-model-evaluation.md).

## Evidence and repository audit

**OBSERVED** denotes fresh file/code/execution evidence. **DOCUMENTED** denotes
authoritative instrument documentation. **INFERRED** denotes interpretation.
**UNKNOWN** remains unresolved. Earlier project reports are supporting claims,
not fresh verification. Specialist audits covered checkpoints/preprocessing,
native data/scientific compatibility, and evaluation planning. An independent
final review is recorded in [the verification report](PHASE1_GOES_VERIFICATION.md).

| Item | Observed identity / decision |
|---|---|
| Repository | `Neal-Salian/SolarJEPA` |
| Verified main and origin/main | `1a4991da4dda9676caeb1d7e35a03408528c3188`, ahead/behind 0/0 after fetch |
| New branch | `research/goes-external-model-evaluation`, published with upstream before changes |
| Base | V1 / origin/v1 `644648f7d555fcbcb3eed4495d37fecffdd1863a` |
| Isolated worktree | Codex managed `goes-external-model-evaluation/SolarJEPA` |
| V1 executed strict-run source | `4a3f88227ce28dea0e885e68987282285963f38e` |
| Reusable external branch | `research/goes-external-validation`, `f309921d776cf2deb632a886e8426e42bac1a050` |
| Existing V1 artifacts | `results/experiments/v1-full-20261009` in original checkout |
| Existing January artifacts | `results/experiments/goes-external-january2025-acceptance-c` and `-d` in external-validation worktree |

The user explicitly requested an appropriate existing base and this exact branch
name, overriding the repository's default main base. V1 preserves the trained
model implementation without bringing unrelated V2 or presentation changes into
this milestone. External preparation is a sibling branch, not inherited code.
No merge/cherry-pick is needed for this audit. A future implementation should
reuse the reviewed external-only files at their pinned revision and retain their
tests, rather than rebuilding preprocessing or importing another checkout at
runtime. V2 provides statistical-contract lessons; its validation-only model
adapter is not an external V1 runner.

All 13 worktrees were inventoried. The original checkout stayed on
`presentation/eda-model-comparison`; its pre-existing `.agents/` and
`docs/P1_FINAL_INTEGRATION_REAUDIT.md` remained untracked and were preserved.
A bounded before/after SHA-256 inventory covers 259 existing raw, V1-run,
external-acceptance and untracked files (265,951,467 bytes), not every ignored
scratch artifact. Final preservation/ref/storage checks are in the verification
report. No existing experiment, report, checkpoint or dataset was replaced.

## Checkpoints and preprocessing

**OBSERVED:** All nine strict-run checkpoints exist: fine-tuned JEPA, frozen
JEPA with trained forecasting head, and matched supervised Transformer, each at
seeds 17, 29 and 43. Smoke-run weights are separate and are not candidates.
The compact [evidence ledger](../data/manifests/phase1_goes_model_readiness.json)
pins actual checkpoint bytes, weight fingerprints, normalization and run/config
identities. Checkpoint qualification details are recorded there and in the
verification report; no newly fitted model replaces a missing artifact.

Relevant unchanged code:

| Contract | Implementation |
|---|---|
| Neural model/configuration | `training/jepa.py:49,242`, `configs/experiments/v1_models.json` |
| Safe checkpoint read and identity checks | `TrainedJepa.load`, `training/jepa.py:711` |
| Context-only inference and inverse transform | `TrainedJepa.predict`, `training/jepa.py:664` |
| Unique raw training normalization | `training/normalization.py:80` |
| Native quality policy | `data/goes.py`, `read_goes` |
| Chronological raw support/windows | `forecasting/splitting.py`, `forecasting/windows.py` |

The model uses 5-minute patches of the two flux channels plus masks, width 32,
depth 3, four attention heads, a depth-2 latent predictor, and a head with 128
hidden units. It returns 30 leads × two channels × five ordered marginal
quantiles: 0.05, 0.25, 0.50, 0.75, 0.95. The point is the inverse-transformed
median, not a physical conditional mean. The EMA target encoder supplies
training targets; forecasting consumes observed context only. Frozen JEPA means
its pretrained encoder/predictor remain frozen during head training; all three
variants are fully frozen for this external experiment.

Saved normalization transforms `log10(F / 1 W/m2)` and standardizes each channel
using unique raw training observations only. The independent numerical audit
checks the saved means/scales/counts against those observations without calling
`Normalization.fit` or replacing any statistics. Approximate means are
(-6.9751727621, -5.4752957945), scales (0.5742480619, 0.3415974219) dex and counts
(113,926, 116,125); full precision and fingerprints are in the evidence ledger.
Prepared January values remain in W/m² until the checkpoint's own transform.

**OBSERVED:** Current V1 source and the recorded strict-run source have the same
53-file executable inventory and fingerprint
`e4418cd34a326e9e429df87214182253ca2b050f7d6fba593ead54e7bd2467d2`.
Different reporting commits do not imply different executed model code.
A normal task-local installation passed installed/source identity guards.
Checkpoint SHA-256 values establish newly measured byte identities; they are
not an independent cryptographic signature of the original training execution.

All nine safe weights-only loads passed state shape/dtype, finite-value, record
and internal weight-identity checks. On the first 256 original August test
origins, using the original batch size 256, every saved point and quantile
replayed bitwise. A two-origin batch changed outputs by at most
`4.1073422085702305e-7` dex on this host; preserve the configured batch size and
do not infer cross-platform bitwise reproducibility. Forecasting called the EMA
target encoder zero times and did not change model weights. Direct raw-support
recalculation reproduced 108,199 eligible stride-one training windows and the
20,000-window cap. These are bounded internal replay checks, not a new full
internal or external experiment.

## External dataset compatibility

**OBSERVED:** The committed January source and dataset ledgers match retained
bytes. Each of 31 native files has 1,440 measured minute bins. Both acceptance
runs' 13 artifacts match the committed preparation ledger. Reconstructing
windows with the unchanged V1 builder reproduces the saved contexts, targets,
grid, dataset fingerprint and split fingerprint.

| Quantity | Fresh observation |
|---|---|
| Dataset | `external-goes16-january2025-science-avg1m-v2-2-1` |
| Spacecraft / instrument | GOES-16 / EXIS-XRS FM1 |
| Interval | `[2025-01-01T00:00:00Z, 2025-02-01T00:00:00Z)` |
| Raw files / bytes / rows | 31 / 9,119,470 / 44,640 |
| Duplicate / missing / off-grid bins | 0 / 0 / 0 |
| Ordered features and targets | `xrsa_flux`, `xrsb_flux`, both W/m² |
| Cadence / context / horizon / stride | 60 seconds / 120 / 30 / 30 steps |
| Availability / eligibility | `retrospective_bin_end` / `complete` |
| V1/external ForecastSpec equality | Exact, fingerprint `094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94` |
| Valid A / B minute bins | 39,170 / 44,317 |
| Rejected A / B minute bins | 5,470 / 323 |
| Raw nonfinite A / B | 313 / 313 |
| Candidate / retained / excluded origins | 1,488 / 1,007 / 481 |
| Retention | 67.6747% of candidate origins |
| Retained context / target shapes | `(1007,120,2)` / `(1007,30,2)` |
| Valid target cells | 60,420; every retained target mask is true |
| First / last retained issue | January 1 02:00 / January 31 23:30 UTC |
| Dataset fingerprint | `b4ff51eff9d8a3d85f30375c07b7623915cd09be9c8f82e26ca17dca13dfcd7c` |
| Split fingerprint | `8018d4c47c06250d988f992a261131e3ca25fd57a0039da4a1be1247a9506dcb` |

The unchanged QC accepts finite positive selected primary flux, status zero,
valid averaged sample counts and the existing channel-specific electron rules.
It performs no local fill, interpolation or spacecraft substitution. Retained
partial-minute averages can have 1–59 contributing samples: 2,325 valid A bins
and 593 valid B bins have fewer than 60. No new sample-count cutoff was invented.
The exact policy remains frozen for comparison with V1.

Of 481 excluded origins, four lack support before the January boundary, 180
fail feature quality alone, 35 fail target quality alone and 262 fail both.
These disjoint patterns sum to 481; reason totals overlap. Future-target QC
defines an offline complete-case scoring population and must never be described
as a deployable origin-selection rule. No unobserved data or flare labels are
invented to fill exclusions.

## Temporal isolation, causality and exposure

**OBSERVED:** All 123 V1 May–August native source identities were verified.
Their measured raw axis contains 177,120 bins ending at 2024-09-01 00:00 UTC.
January begins 122 days later; there is zero raw-bin overlap. Frozen splits are
training `[2024-05-01,2024-07-22)`, validation `[2024-07-22,2024-08-01)`, and
internal test `[2024-08-01,2024-09-01)`, all UTC. Every January context ends
by issuance and each target begins at or after issuance. January windows expose
no TrainingSlice, learned statistics, event labels or future observations as
predictor inputs. The existing external loader checks only July overlap; future
integration must enforce all V1 development and test support explicitly.

**DOCUMENTED:** NOAA distinguishes retrospectively corrected/calibrated science
products from operational products; it describes electron-contamination
correction limitations and short-gap interpolation in the XRS processing.
See the [NOAA XRS L2 guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf)
and [NOAA science-product readme](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf).
Current flags exclude the relevant interpolated/invalid bins; that does not
prove every retained native value was generated with causal upstream processing.

**OBSERVED:** January files were created on December 5, 2025, by
`xrs04_avg.py`, algorithm version `[2,4]`, with previous/current/next-day XRS and
SEISS inputs. Product version `2-2-1` is distinct from algorithm version.
These are native creation/provenance metadata, not acquisition timestamps.
Acquisition times remain those in the immutable source ledger; filesystem
times are not used as acquisition or coverage evidence.

**DOCUMENTED:** The NOAA readme inspected for this audit lists a newer science
product `v2-2-2`, released October 6, 2026; the retained `v2-2-1` release is
December 15, 2025. This is a version limitation, not permission to repin or
replace inputs. Generic archive latencies in the readme do not establish
historical per-bin as-issued availability for January 2025.

**UNKNOWN:** Per-value influence of later observations and actual January 2025
delivery latency. Adjacent-day inputs are evidence requiring investigation,
not proof that each retained value leaks. Coordinate causality passes; native
preprocessing causality and as-issued operational availability are unestablished.
An operational causal claim is therefore `BLOCKED_EXTERNAL_EVIDENCE`.

**OBSERVED:** January data, QC and catalog summaries were inspected on the
external branch before this task. V2's exposure register also records this
history (`docs/V2_EXPERIMENTAL_PROTOCOL.md:47` at `fd7203b`). **UNKNOWN:** All
private/teammate access and any unrecorded selection. January is temporally
external to training, but cannot be called a genuinely uninspected confirmatory
test. This audit found no authorized January model run; absence of unrecorded
runs is not established. All nine V1 checkpoints must be retained without
selection using January scores.

## Reuse, exact gaps and readiness gate

| Requirement | Verdict | Evidence / resolution |
|---|---|---|
| Native channels, units, cadence and windows | PASS | Exact V1 spec and reconstructed prepared artifacts |
| Frozen neural checkpoint availability and normalization | PASS within audited host | Nine saved states; no retraining/refitting required |
| Raw train/validation/internal-test/external separation | PASS for these files | All 154 native input files checked; zero overlap |
| Context-only neural inference | PASS in inspected path | `TrainedJepa.predict`; frozen normalizer/spec checks |
| Native preprocessing causal / live delivery evidence | UNKNOWN | Obtain authoritative algorithm/dependency and delivery evidence, or explicitly bound the claim to retrospective science products |
| Completely blind external test | NOT ESTABLISHED | Record known exposure; do not assert untouched or population-wide confirmatory evidence |
| No-refit classical replay | INCOMPLETE integration | Saved fitted records exist; no supported external restore API |
| External scoring and provenance orchestration | INCOMPLETE integration | Reuse external flux scorer and V1 log scorer through qualified wrapper; preserve identities |
| Joint seed/temporal uncertainty validity | LIMITED | Three fixed fitted seeds and one month; descriptive intervals only |

V1 `run_v1` is a training/comparison runner and must not be used for this task.
It calls baseline fits, neural training and validation selection. Its docstring
says all test scoring occurs after selection; the execution order interleaves
some internal test scoring and later fits. Preserve this historical discrepancy;
it is not evidence of January-based selection.

V1 `_Baseline.predict` (`forecasting/baselines.py:119`) and
`evaluate_trajectory` (`evaluation/trajectory.py:183`) require the original
dataset fingerprint. Do not relabel January as training, mutate those guards,
construct an external TrainingSlice, or call fit to satisfy them. Saved classical
fit records provide a basis for an explicit restore/transfer wrapper; not every
family's restoration has yet been qualified. Failed restoration must remain a
reported missing arm, not trigger a new fit.

An audit-only reconstruction restored all 16 saved classical candidates from
JSON fitted parameters without invoking fit. First-two-origin internal-test
replay was available for 13 archived test arms: 12 reproduced bitwise and direct
ridge differed by at most `1.7763568394002505e-15` dex. The three other ARIMA
candidates were validation-only. This establishes that saved state is available;
private field reconstruction is not a supported external restore implementation
or full-horizon/month qualification. Existing convergence/fit-quality limitations
must remain attached to the original fits.

The sibling external branch already implements `load_external_dataset`,
`build_external_windows`, `evaluate_external_flux` and `paired_block_bootstrap`.
The flux scorer's coverage field means observation/prediction support, not
prediction-interval calibration. V1 `log_scores` supplies pinball and 50/90%
marginal coverage, but its per-channel output only supplies log MAE. A qualified
wrapper must add channel/lead pinball, RMSE and interval summaries and bind
quantile arrays in evaluation identities. Train-scaled MASE is omitted.
V2 M4B `build_evaluation_record` is validation-only and cannot be passed January
as if it were V2 validation. M2/M3 evidence does not establish a universally
reliable significance procedure; it does not justify upgrading bootstrap output
to a p-value or joint seed/calendar uncertainty.

The task-local environment uses Python 3.13.3, torch 2.6.0, NumPy 2.2.6,
pandas 2.3.3, netCDF4 1.7.2, statsmodels 0.14.5 and arch 7.2.0. Required packages
are available on this host; a fresh machine needs the existing optional training
and stats dependencies and retained ignored inputs/checkpoints. No dependency
declaration was changed. Cross-host/accelerator equivalence is untested.

## Exact next action

Resolve the scientific scope first: explicitly accept a retrospective,
previously inspected, continuous-flux external replication with the recorded
native-processing limits, or provide the missing authoritative causal/as-issued
evidence if a causal operational claim is required. Neither choice makes January
blind. While PARTIALLY_READY, obtain explicit authorization for the bounded
no-refit restore/transfer and scoring adapters before writing that code, as set
out in plan Task 0. Alternatively, proceed under the standing conditional
instruction only after a supported READY determination. After adapter
qualification, re-audit the mandatory gates for the chosen claim. The full external
experiment still requires explicit user approval of the frozen
protocol and exact execution manifest after infrastructure tests/review pass.

No event detection, catalog completeness claim, model selection using January,
new training, V2 development, PR, merge or push to a protected branch belongs
to this milestone. The delivered audit/protocol/plan are the completed work;
full external performance remains unknown.

## Dated implementation follow-up — 2026-10-14

The preceding October 13 audit and PARTIALLY_READY determination remain
historical. The user subsequently approved the bounded retrospective scope and
adapter implementation. The [implementation/verification report](PHASE1_GOES_ADAPTER_IMPLEMENTATION.md)
records the current **READY** verdict for that scope, unchanged frozen inputs,
1,417-test regression, normal installed preflight and bounded historical replay.
The [processing/exposure supplement](PHASE1_GOES_PROCESSING_LIMITATIONS.md)
records observed prior exposure and unresolved upstream causality. Neither this
follow-up nor infrastructure readiness authorizes the full January experiment.
No new January model predictions or metrics have been computed.
