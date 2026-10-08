# Phase E implementation and verification report

Evidence date: **2026-10-09, Asia/Kolkata**. Base:
`656e540162c635d4c2274b4469ae11247290f986`. Branch:
`research/phase-e-solexs-validation`. Scientific verdict remains
`BLOCKED_FOR_PHASE_E`; see the [scientific report](SOLEXS_PHASE_E_SCIENTIFIC_VALIDATION.md)
and [evidence matrix](SOLEXS_PHASE_E_EVIDENCE_MATRIX.md).

## Actual changes and scope

**No executable source, tests, dependencies, scientific definitions, acquisition
inventory, model, baseline or split was changed.** Existing native access,
inspection, response diagnostics, source identities and fail-closed training
checks already cover the authorized numerical investigation. No reproduced
repository defect justified a new utility or test. Test-driven development would
apply to a justified code defect; no artificial code change was introduced to
exercise that workflow.

The requirements manifest gained only an additive `phase_e_validation` record.
Its prior fields remain equal to the P2 versions, including dated requirements,
provenance and blocked gate. Four current identity notes clarify that the official
tools bundle and its three CALDB members are present and byte-verified. Those
notes supersede older acquisition/byte-equivalence unknowns without accepting
scientific compatibility. No existing gate consumer or config pin was weakened.

Complete milestone changed-file inventory:

| File | Purpose |
|---|---|
| `docs/SOLEXS_PHASE_E_SCIENTIFIC_VALIDATION.md` | Scientific investigation, readiness decision, dependencies and integration recommendations. |
| `docs/SOLEXS_PHASE_E_EVIDENCE_MATRIX.md` | Original source versions/locators, claim-specific observed evidence and uncertainty. |
| `docs/SOLEXS_PHASE_E_IMPLEMENTATION_REPORT.md` | Changes, executed checks, preservation and limitations. |
| `data/manifests/solexs_phase_e_evidence.json` | Compact portable identities, observed diagnostics, software versions and six gate decisions. |
| `data/manifests/solexs_phase_e_requirements.json` | Additive current record; historical fields preserved. |
| `docs/superpowers/plans/2026-10-08-phase-e-solexs-validation.md` | Authorized research/verification plan and completed checklist. |

Full diagnostic outputs and research scratch are ignored. A newly retrieved
versioned literature PDF was preserved under ignored
`data/raw/aditya/documentation/phase-e-reference/2509.26292v2.pdf`; 10,575,871 bytes,
SHA-256 `dc6db1cc6a1a2b9c8d348c12a212818616e025566f17adb141c9b364475c309e`.
This is literature, not a re-download of either scientific archive. No original
resource was overwritten or deleted, and no credentials were read or staged.

## Runtime and reproducibility

Existing environment: Python3.13.3, NumPy2.2.6, Astropy8.0.1, pandas2.3.3,
pytest9.1.1, netCDF4 1.7.2, xarray2026.7.0, Matplotlib3.11.2, Torch2.6.0.
No dependency install/reconfiguration occurred. Bundled pypdf was used read-only
for original manual/paper pages; it is not a project dependency. All significant
inputs and executed native source files are hash-pinned in the Phase E record.

Because raw inputs are in the untouched original checkout, actual diagnostics
ran the isolated worktree's scripts with its `src` explicitly on PYTHONPATH and
the original data root supplied through the existing configurable `--root`.
Five normally installed scientific modules were also imported without that
override and verified byte-identical to worktree sources. This checks the modules
used here; it is not a new whole-package installation certification.

The following are reproduction commands; use a new output name if one already
exists. A fresh clone must independently obtain the immutable real inputs and
reference resources; tests' artificial FITS fixtures are not substitutes.

```bash
# Run from the Phase E worktree/checkout; choose actual local storage/runtime.
SOLEXS_DATA_ROOT=/Users/nealsalian/Desktop/SolarJEPA
SOLEXS_PYTHON="$SOLEXS_DATA_ROOT/.venv/bin/python"
export PYTHONPATH="$PWD/src"
mkdir "$SOLEXS_DATA_ROOT/results/phase_e_reproduction"
"$SOLEXS_PYTHON" scripts/validate_solexs.py --root "$SOLEXS_DATA_ROOT" \
  --output results/phase_e_reproduction/native_report.json
"$SOLEXS_PYTHON" scripts/probe_solexs_readiness.py --root "$SOLEXS_DATA_ROOT" \
  > "$SOLEXS_DATA_ROOT/results/phase_e_reproduction/readiness_probe.json"
"$SOLEXS_PYTHON" scripts/explore_solexs.py --root "$SOLEXS_DATA_ROOT" \
  --output results/p2_solexs/phase_e_reproduction
"$SOLEXS_PYTHON" -m pytest -q tests/test_solexs.py \
  tests/test_solexs_readiness_probe.py tests/test_solexs_exploration.py
"$SOLEXS_PYTHON" -m pytest -q
```

Actual output paths (new, preserving previous runs):

| Artifact | Observed bytes / SHA-256 |
|---|---|
| `results/phase_e_20261008/native_report.json` | 100,275 / `70241bdde078c8e0986bb23117c6543a262fe1846bfd81e64d4b49380f43eb8a` |
| `results/phase_e_20261008/readiness_probe.json` | 22,739 / `3df12394d6e9f4f4fe94b7adb787c9a8cb9af41bb460b7dbe21cd2436f4df174` |
| `results/p2_solexs/phase_e_20261008/report.json` | 215,218 / `9ebc539d09d5c681f906a59e0600ddd33290a11f0cd8d18bb01aad213de97868` |

Four bounded native plots and the local-identity/research records remain in ignored
results. Artifact hashes prove preserved outputs, not accepted UTC/flux semantics.
The exploration JSON retains OBSERVED_NATIVE, EXPERIMENTAL_UNCALIBRATED plots,
`calibration.applied=false` and `training.executed=false`. No forecasting
experiment or metric was produced.

For local source-pin reproduction, read `sources` from
`solexs_guidance_sources.json`, `solexs_phase_d_sources.json` and
`solexs_phase_d1_evidence.json`; for each entry compare actual file size and full
SHA-256 against recorded values. For the official TAR, compare all45 outer member
names/sizes and all35 regular-member SHA-256 values with D.1's
`official_archive.members`, using read-only `tarfile.extractfile`, never extraction
paths. This verification ran successfully; the11 selected D.1 members were also
independently checked by the calibration reviewer.

## Executed verification

| Check | Actual result / scope |
|---|---|
| Untouched inherited full suite | **1,084 passed, zero failed**, one existing warning, 83.15s. |
| Final full suite after reports/manifests | **1,084 passed, zero failed**, same warning, 79.20s. |
| Native loader/readiness/exploration subset | **109 passed**, zero warnings, 7.33s; existing tests unchanged. |
| Actual archives/native CLI | Two archives/eight products; CRC/gzip/FITS integrity and16 DATASUM checks passed; CHECKSUM absent. |
| Actual response/readiness CLI | Deterministic native-only output; candidate mappings/applicability not approved. |
| Gated exploration CLI | Two archives/four plots; training not executed; conversion/calibration not applied. |
| P2 regression comparison | New native `archives` summaries exactly equal preserved P2 native-02 summaries; both response comparison records exactly equal Phase D observations. |
| Independent direct-array audit | Separate ZIP→gzip→FITS inspection reproduced native LC/PI/GTI/missingness relationships; numerical probe comparison agreed. |
| Local resource provenance |39 distinct source pins, both science ZIP hashes, all45 tools outer-member sizes and35 regular hashes match. |
| Normal scientific imports | Five installed scientific module hashes match worktree; no reinstall. |
| Previous scientific/output preservation |109 source/scientific hashes and290 prior output hashes rechecked;32 indexed experiment directories pass `verify_artifacts`, including all original P2 executions. |
| Strict-warning diagnostic | **1 failed**, intentionally promoting the inherited RuntimeWarning to error; no acceptance rule or suppression changed. |

Strict-warning command actually executed:

```bash
/Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -m pytest -q \
  tests/test_experiment_reference.py::test_adapter_preserves_selected_quality_mask_and_unknown_actual_availability \
  -W error::RuntimeWarning
```

The stack reaches xarray fixture writing and `netCDF4._netCDF4` import:
`numpy.ndarray size changed, may indicate binary incompatibility. Expected 16
from C header, got 96 from PyObject`. A normal fresh `import netCDF4` succeeded;
the targeted warnings-as-errors test reproduces the warning. The inherited P2
report recorded the same issue. No ABI-safety claim is made; dependency repair
and new GOES acceptance are outside this milestone. Normal suite success does
not erase this limitation.

Final manifest checks confirm that removing `phase_e_validation` restores exact
P2 requirement values, all six statuses agree between manifests, every pinned
input/source/artifact identity matches, and new evidence is repository-relative.
All local Markdown targets resolve. All 80 original raw-file snapshot hashes and
the original untracked skill/audit hashes remain unchanged. `git diff --check`
passes; tracked bulk-data directories contain only their original `.gitkeep`
files. Source/tests/configs/scripts/dependency/instruction diffs against P2 are
empty. Main/P1/P2 refs remain exactly as recorded in the scientific report; P3
is absent from observed refs and was not modified.

## Independent reviews and scientific assumptions

Three read-only investigators covered literature/GOES, timing/exposure/quality
and calibration. Their original source reads and independent array observations
were compared with coordinator execution rather than trusted by summary alone.
No investigator edited repository files. Initial subagent execution hit an account
usage limit; after the user's continuation request, all three completed and
preserved their reports. A fresh final reviewer found **no actionable findings**.
It independently checked 22 pinned identities, all eight expanded FITS hashes,
16 DATASUM results, full-day coordinate/missingness equality, GTI membership and
the three channel-sum comparisons. It also verified the additive manifest
preserves historical requirements. It did not independently revalidate every
literature claim, rerun the full suite or authenticate portal provenance; those
limits remain explicit. Coordinator execution supplies the full-suite evidence.
The review and independent research/audit traces are retained in ignored results,
with hashes in the Phase E evidence record.

No scientific acceptance criteria were relaxed. No zero error, UTC epoch repair,
fixed clock shift, continuous exposure formula, PI energy mapping, correction
coefficients, health flag, flare label or cross-source target was invented.
Instrument capabilities are not measured sample coverage; scientific papers do
not validate a particular response file. Native summaries are deterministic in
the inspected runtime. Cross-version bitwise plot reproducibility is not claimed.

## External dependencies and integration recommendation

Obtain an applicable mission answer/erratum for release1.1 clock/bin/GTI,
exposure/quality/correction and PI/response/gain compatibility. Request exact
resources and reference outputs after that policy is identified; HK is required
only for a workflow that uses it. Portal-wide July2 availability, compatible HK
names and a mission-approved alternate release remain UNKNOWN. Existing user
reports of a sent clarification email are historical supporting context, not a
current reply or authority. No message was sent to mission staff.

Only after the scientific contract is validated should a future phase select
bounded historical coverage, define source-separated targets/masks/uncertainties,
establish causal availability and independent chronological evaluation support,
then consider approved common-response comparisons. These are recommendations,
not implemented model/training work or permission to change P3. No branch is merged.
