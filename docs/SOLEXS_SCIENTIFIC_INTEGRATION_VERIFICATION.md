# SoLEXS native integration verification

Executed 2026-10-16, Asia/Kolkata. Scientific scope and limitations are in
[the milestone report](SOLEXS_SCIENTIFIC_INTEGRATION.md). Exact input/output,
source and supporting-log identities are in
[`solexs_scientific_integration.json`](../data/manifests/solexs_scientific_integration.json).

## Outcome

**NATIVE_INTERFACE_READY_SCIENCE_BLOCKED.** Native integrity, portable
preparation and guarded publication passed. No scientific gate was promoted.
No real-data model training, checkpoint replacement, physical conversion,
GOES alignment, PR or merge occurred. Existing full-suite tests include small
artificial training fixtures; they do not retrain the real pilot or V1/V2.

Implementation execution commit:
`32cc4b28aae5408b2dbee7992284f5ba6ab2eac8`. Subsequent changes contain only
documentation and evidence manifests; their Git commit identity differs while
the verified executable source stays the same.

## Executed checks

| Check | Observed result |
|---|---|
| Isolated inherited full suite | **1,149 passed**, one inherited warning, 89.63 s. |
| First implementation full suite | **1,200 passed**, same warning, 81.01 s. |
| Final corrected full suite | **1,211 passed**, same warning, 76.93 s. |
| New native quality/interface/integration tests | **62 passed**; independent code reviewer also ran all 62 successfully. |
| Existing native loader/readiness/exploration plus initial new tests | **160 passed** before review regressions were added. |
| Independent scientific review | Approved native scope and scientific report; required reproduction wording precision was corrected. No scientific clearance inferred. |
| Independent implementation review | Approved after PI structure, inventory snapshot, diagnostic fingerprint, empty-stream and GTI-selection regression fixes. |
| Normal isolated package installation | `pip install --no-deps --no-build-isolation .` succeeded in the new worktree's ignored runtime; shared environments were not reinstalled. |
| Normal imports and CLI help from `/tmp` | Imported the new worktree's normally installed distribution; help succeeded. No test `src` injection used for CLI execution. |
| Real native CLI from `/tmp` | Two archives/eight FITS products verified; 39 documentary/calibration/tool source identities matched. All 57 executable/configuration provenance entries were captured; installed/checkout source matches. |
| Real reproduction and relocated data-root run | Both reports and artifact indexes verify; all three report files are byte-identical. |
| Existing output publication | Rejected with `FileExistsError`; prior artifact identities stayed unchanged. |
| Existing calibration/readiness probe | Succeeded; response labels 1–340, native PI 0–339, applicability still unapproved. |
| Original tools TAR.GZ | 45 outer members; all 35 regular-member hashes match D.1 pins; no package installation/execution. |
| Frozen SoLEXS pilot | All 26 pinned pilot/reproduction/supporting artifacts matched, including checkpoints and predictions. No pilot rerun. |
| Original indexed experiments | 32 indexes and 319 artifact/index identities verified, including the indexed original checkpoint. |
| Original raw/user files | All 52 snapshot identities match; includes original Aditya inputs and the pre-existing untracked user files. |
| Git scope/data policy | All milestone files are additions relative to the chosen checkpoint. Actual raw/results paths match ignore rules; no prohibited data paths in index/reachable history. Whitespace checks pass. |

The inherited warning is:

```text
RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility.
Expected 16 from C header, got 96 from PyObject
```

It occurs on netCDF4 import in
`test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability`.
It was neither suppressed nor repaired; these runs do not establish ABI safety.

The ignored acceptance runtime is
`results/solexs_integration_runtime/bin/python`, with a normal local package
installation and a `.pth` reference to existing dependency libraries. This helper
is machine-specific; portable dependencies remain in `pyproject.toml`/existing
lock files. No new dependency or dependency-file change was needed.

## Real-input numerical findings

| Nominal archive date | LC/PI rows each | Finite LC / fully finite PI rows | Closed GTI points | Half-open GTI points |
|---|---:|---:|---:|---:|
| 2024-07-01 | 86,400 | 86,272 | 86,272 | 86,268 |
| 2024-07-03 | 86,400 | 86,398 | 86,398 | 86,395 |

Both products on both days have one initial numerical run boundary and no
internal coordinate-step breaks at the requested numerical step of one.
Missing count entries remain NaN; positive finite exposure flags remain true
on missing PI rows. Those flags do not establish live exposure or valid science.
All finite PI/LC counts are nonnegative integers in this sample. No detector
health/saturation clearance or uncertainty is inferred.

The normal CLI reports live under ignored:

```text
results/experiments/solexs-native-integration-20261016/
results/experiments/solexs-native-integration-20261016-reproduction/
results/experiments/solexs-native-integration-20261016-relocated/
```

Shared report SHA-256:
`5517b8d6a7b22f4b1eb784054363a1988cecb84d632e7c5b6423f802d5fb06d5`.
Bitwise equality is established for these native metadata audits in the recorded
runtime/configuration, not arbitrary future software/calibration releases.

## Review and regression fixes

New functions were preceded by failing tests. Independent review then found
five boundary issues, reproduced before fixing:

- Direct PI preparation accepted missing/fractional/mismatched channel/counter
  fields. Loader-equivalent structural validation now rejects them without
  assuming channel numbering.
- The audit discarded its pinned inventory snapshot and reread the pathname.
  Consumption now validates the retained exact JSON snapshot.
- Batch identity omitted diagnostic masks; different predecessor/GTI
  diagnostics could share a fingerprint. Every derived mask now participates.
- Empty science products skipped step/detector validation. These checks now
  run regardless of row count.
- Multiple GTIs for one detector silently selected the last entry. The audit
  now rejects ambiguity and records the selected GTI's full provenance.

The independent scientific review also corrected documentation that grouped
package setup/full tests with the offline native audit: pip can fetch build
tooling and tests train small artificial models. Only the native audit/probe
provide the no-network/no-training assurance.

## Concurrent work and publication boundary

`main` and `origin/main` remain
`1a4991da4dda9676caeb1d7e35a03408528c3188`. During this run, a concurrent task
advanced `codex/v2-experimental-validation-readiness` from `5d2f0b1` to
`b0157f2` (`fix(experiments): hard-stop pilot workers during cleanup interruptions`).
That ref update was recorded, not performed by this milestone; its worktree was
left alone. Other-ref immutability is therefore not claimed. No changes were
reset, merged or imported from that concurrent work.

Publication is restricted to `codex/solexs-scientific-integration`; no PR,
merge, main push, force push or branch deletion is authorized. The final handoff
records verified local/upstream/remote equality after push. The managed worktree
is retained for review and the next explicitly authorized milestone.
