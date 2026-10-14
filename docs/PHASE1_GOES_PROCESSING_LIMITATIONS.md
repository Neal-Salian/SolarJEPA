# Phase 1 GOES processing and exposure follow-up

Audit date: 2026-10-13. This supplement supports the approved bounded,
previously inspected retrospective replication. It records no January model
predictions or performance results and adds no new approval requirement to
that scope. Original audit and preparation reports remain historical records.
**DOCUMENTED** means primary-source documentation; **OBSERVED** means inspected
Git/file evidence; **INFERRED** means interpretation; **UNKNOWN** is unresolved.

## Recorded exposure and its limits

**OBSERVED:** The retained source ledger at external-validation revision
`f309921d776cf2deb632a886e8426e42bac1a050`,
`data/manifests/goes_external_january2025.json`, records acquisition of the 31
January native files from `2026-10-09T13:21:01.058506+00:00` through
`2026-10-09T13:22:59.059045+00:00`. Fresh hashing reproduced every recorded
source SHA-256. These are ledger acquisition declarations, distinct from
native creation dates and observation coverage; filesystem times were not used.

**OBSERVED:** Reachable history records:

| Evidence | Exact recorded location |
|---|---|
| Acquisition and annual 2025 catalog pinning | `28e222ba042b32c84dad49a446f0849c677af4b9`; source/catalog manifests and configs |
| Native QC, preparation and catalog inspection results | `bd128295c8529e064473e483751ca747de2f57a5`; `docs/GOES_EXTERNAL_VALIDATION_IMPLEMENTATION.md` and `data/manifests/datasets/goes_external_january2025.json` |
| Explicit subsequent exposure acknowledgement | `a03281d226e5b609d2e769fb7c506cf67db2800e:docs/V2_M0_RESOLUTION.md`, exposure table; also `fd7203bf9a2e1e3dd78d9750a948b823ab100d36:docs/V2_EXPERIMENTAL_PROTOCOL.md`, section 3 |

**OBSERVED:** The external-validation worktree retains acceptance directories
`results/experiments/goes-external-january2025-acceptance-{a,b,c,d}`. Their
summaries declare `fit_performed=false`, `model_predictions=NOT_RUN` and
`model_metrics=NOT_COMPUTED`. Their member inventories contain preparation,
contexts/targets, grids, catalog alignment, labels and provenance, with no
prediction/checkpoint files. C/D record executed source
`8f41ab2f7fac59fc12152040af32e10c69563091`; A/B record
`6c8a6e99a9711ed887a82531f1110d4a07276453`. These observations corroborate
preparation exposure; summary declarations alone cannot rule out separate runs.

**OBSERVED:** January acquisition and its recorded inspection predate the V1
strict run's `started_utc=2026-10-09T15:21:39.239319+00:00`, read from the
retained `results/experiments/v1-full-20261009/summary.json`, whose provenance
identifies source `4a3f88227ce28dea0e885e68987282285963f38e`. The acquisition
and inspection commits record 19:24:39 and 19:34:54 +05:30 respectively,
before that source commit's recorded 20:45:41 +05:30 time. Git times and run
declarations establish recorded chronology, not an independently authenticated
human-decision history.

**UNKNOWN:** Whether January exposure influenced V1 architecture, recipe,
selection or other human decisions; all private/manual/teammate accesses and
unrecorded runs. The read-only search covered 54 local and remote-tracking refs
in tracked docs/configs/manifests/source/scripts, relevant path history, and
experiment-directory names across 13 registered worktrees. It was not an
exhaustive forensic search of every ignored artifact, deleted object, private
machine or remote ref. No January model run was established in the inspected
evidence. Absence elsewhere remains unknown.

**INFERRED:** January is appropriate for the approved temporally external
retrospective replication, with exposure disclosed. Freezing the existing V1
cohort now prevents new January-based selection but cannot make historical
access blind or establish an untouched confirmatory holdout.

## Native metadata and authoritative processing evidence

**OBSERVED:** All 31 immutable January files identify `xrs04_avg.py`,
`algorithm_version=[2,4]`, `algorithm_date=2025-08-13`, and
`processing_parameters_file=g16_xrs-avg-electron-contam-lut_v3.h5`. All record
December 5, 2025 creation and six inputs spanning previous/current/next-day
SEISS MPS-HI minute products and XRS one-second products. For January 1 the
first/last inputs are December 31/January 2; for January 31 they are
January 30/February 1. File-level input declarations do not specify which
samples influenced each retained value. Algorithm, LUT and product versions
are separate identifiers.

**DOCUMENTED:** The current [NOAA XRS L2 ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf),
dated October 6, 2026, sections 3/5 and Table 4, distinguishes reprocessed
science products from operational data. Table 4 dates pinned `v2-2-1` to
December 15, 2025, with calibration/spike and interpolation changes, and newer
`v2-2-2` to October 6, 2026, with updated electron coefficients and gap handling.
Generic archive latency statements are not historical per-bin delivery logs.
**OBSERVED:** The current document was read through NOAA's documentation index;
no new science version was downloaded, compared across versions or repinned.
Hash verification above used the existing pinned science files.

**DOCUMENTED:** The retained [NOAA L2 User's Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf),
pages 7-8, describes fit-derived electron corrections, retrospective interpolation
over short missing-SEISS gaps and separate interpolation/decay flags.
The byte-verified retained guide is identified by SHA-256
`5736ef81e8a34aef8a0672c14193ed641f846f4d8008c66ee80ec12e243f3cee`
in external revision `f309921`'s
`data/manifests/goes_external_research_sources.json`. Its original acquisition
time is null; registration does not supply a missing acquisition time.
**OBSERVED:** Existing `data/goes.py:read_goes` rejects nonzero flux-status flags
and electron invalid/interpolation/decay bits through its frozen mask. Those
checks do not authenticate all upstream calibration or quality dependencies.

**DOCUMENTED:** The NOAA-linked instrument paper
[Machol et al. (2026)](https://doi.org/10.1029/2026JA035181), sections 3.3,
4.1.1 and 4.1.2, specifies a **centered** five-point median in one-second spike
flagging, exclusion of spikes when forming minute means, on-orbit dark
calibration and fit-derived electron corrections. **INFERRED:** Neighboring-time
quality selection can affect a minute mean even when its final interpolation
flag is clear. This gives a specific dependency to investigate; it does not
prove which retained January values depend on post-issuance measurements.

**DOCUMENTED:** The [NOAA L1b ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l1b/docs/GOES-R_EXIS_XRS_L1b_Data_ReadMe.pdf),
Table 2 and caveat 12, identifies the time-dependent science dark correction
introduced with L1b `v0-0-2` in December 2025. The official
[EXIS algorithm design document](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l1b/docs/GOES-R_EXIS_L1b_Algorithms_CDRL80.pdf),
109620revH, Figure 5 and Appendix C, documents calibration/LUT dependencies.
These documents describe algorithms and calibration concepts, not the complete
version-matched `xrs04_avg.py` execution or the named LUT's training support.

## Preserved unknowns and the approved claim

**UNKNOWN:** The named LUT's coefficient-estimation calendar, exact calibration
inputs and immutable bytes; complete version-matched upstream code; each
retained value/flag's actual dependency support; historical January delivery
and as-issued values. Bounded searches for the exact processor/LUT filenames,
NOAA documentation and the [official-linked code examples](https://cires-stp.github.io/goesr-spwx-examples/examples/index.html)
did not locate the required production code or LUT provenance. This is a
search limitation, not a claim that such evidence does not exist.

Coordinate-level context/target separation remains the existing verified
contract. Operational causality and live availability remain unestablished;
adjacent-day inputs alone prove neither leakage of every value nor its absence.
The approved claim is frozen-model prediction of a previously inspected,
reprocessed January archived science product. No operational-causal,
population-generalization or untouched-confirmatory claim follows from it.
Pinned `v2-2-1`, historical QC and all selected checkpoints remain unchanged.
The ignored `results/phase1_adapter_audit/scientific_followup.json` records
fresh source identities, native attributes, preparation evidence and chronology.
