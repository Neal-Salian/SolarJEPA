# Recovery guide

Verified **2026-10-18**. Start with [status](PROJECT_STATUS.md), [branch map and
checks](DEVELOPMENT_HANDOFF.md), [decisions](DECISION_LOG.md) and `AGENTS.md`.
Commands below are from the relevant checkout root on a POSIX shell. Windows
needs activation/path equivalents; cross-platform numerical identity is untested.
No ChatGPT subscription is required for Git, Python, Streamlit or local tests.
GitHub access, data rights and scientific/compute approval remain separate.

## 1. Recover an interrupted checkout before changing it

Preserve every existing worktree and ignored artifact. Do not start by pulling,
resetting, cleaning, stashing everything, pruning worktrees or rerunning jobs.
Inspect privately (diffs/process arguments may contain sensitive information):

```bash
git status --short --branch
git branch -avv
git worktree list --porcelain
git log --all --graph --decorate --oneline -40
git diff --stat
git diff --cached --stat
git ls-files --others --exclude-standard
git reflog -15
```

At this audit the primary EDA checkout has two untracked files, named in the
handoff. Everything in the 13 other pre-existing linked worktrees is tracked-clean;
ignored inputs/results still differ by worktree. Do not overwrite a changed state
just because this snapshot was clean.

Make a private backup outside the repository before resolving interruptions:

```bash
umask 077
RECOVERY_DIR=$(mktemp -d "${TMPDIR:-/tmp}/solarjepa-recovery.XXXXXX")
git diff --binary > "$RECOVERY_DIR/unstaged.patch"
git diff --cached --binary > "$RECOVERY_DIR/staged.patch"
git status --porcelain=v1 > "$RECOVERY_DIR/status.txt"
git ls-files --others --exclude-standard > "$RECOVERY_DIR/untracked-names.txt"
git bundle create "$RECOVERY_DIR/refs.bundle" --all
```

These commands **do not back up untracked files or ignored data/results**. Copy
reviewed untracked source/documents separately, and securely back up immutable
science inputs and completed result bundles with their relative paths and hashes.
Keep credentials, approval evidence and patches private. A temporary directory is
only interruption protection; move backups to durable approved storage.

For an incomplete merge/rebase/cherry-pick, read `git status`, preserve index,
conflicts and patches, then inspect the intended operation before choosing its
`--continue` or `--abort`. Neither operation is an automatic recovery step. A
failed push may have succeeded remotely: `git fetch origin`, then compare
`git rev-parse HEAD` and `git rev-parse '@{upstream}'` and inspect
`git log --left-right --oneline 'HEAD...@{upstream}'` where upstream exists.
Do not force-push. For a Git lock, first establish that no live Git process owns
it; do not delete locks blindly. A partial worktree setup requires checking
`git worktree list --porcelain` and the target directory before recreating it.
Use `git worktree repair <existing-path>` for an intentionally moved checkout
only after confirming its original identity. Never prune an unexplained entry.

For interrupted experiment outputs, inspect supervisor/run manifests and terminal
state before any restart. Preserve partial directories/logs. Original data are
immutable; existing output names are not overwrite targets. An atomic temporary
file is not a completed record. A failed/interrupted run is not a completed run.

## 2. Clone and recover the correct branch

```bash
git clone https://github.com/Neal-Salian/SolarJEPA.git
cd SolarJEPA
git fetch origin
git switch --track origin/codex/developer-handoff-recovery
git status --short --branch
git rev-parse origin/main
git worktree list --porcelain
```

The recorded main checkpoint is `1a4991da4dda9676caeb1d7e35a03408528c3188`.
If refs have advanced, investigate the diff rather than resetting. In an existing
clone use `git switch codex/developer-handoff-recovery` only in a clean checkout
where that branch is not already checked out elsewhere; otherwise read it with
`git show origin/codex/developer-handoff-recovery:docs/DEVELOPMENT_HANDOFF.md`.

Keep the documentation checkout open and create a workstream checkout outside it.
For a new clone with no local prediction branch:

```bash
git worktree add --track -b codex/solar-flux-prediction \
  ../SolarJEPA-prediction origin/codex/solar-flux-prediction
git -C ../SolarJEPA-prediction rev-parse HEAD
```

Expected prediction tip: `a4951516dc2094ceb246b016700d1483a808212b`.
Repeat with the **exact existing branch** from the handoff for V2, science or
research. If a local branch already exists without a worktree, use
`git worktree add ../SolarJEPA-prediction codex/solar-flux-prediction`.
If already attached, use that existing worktree. Do not use `-B`, recreate an
existing branch or switch another developer's checkout. Detached forensic access
is possible with `git worktree add --detach ../SolarJEPA-inspect <recorded-sha>`;
do not commit there accidentally. New milestone work starts from verified clean
main on its own branch and is published before edits, per `AGENTS.md`; resuming
an existing authorized workstream uses its existing branch.

## 3. Configure an isolated environment

Use one environment per worktree/lock family. Verify Python first; the inspected
host used **CPython 3.13.3/macOS arm64**. `pyproject.toml` allows Python >=3.11,
but the locks are historical, platform-dependent pins. The V1 lock header names
a Windows 3.13.11 environment; that is not the actual audit host. Do not silently
upgrade pins, share conflicting dashboard/research environments, or assume a
Linux/GPU/Windows reproduction has been tested.

```bash
python3.13 --version
python3.13 -m venv .venv
```

Then choose **one** install row for the checked-out branch:

| Checkout | Exact dependency command |
|---|---|
| Main / handoff / basic native SoLEXS | `.venv/bin/python -m pip install -r requirements-lock.txt` |
| V1 / V2 / external research / provisional modelling | `.venv/bin/python -m pip install -r requirements-v1-lock.txt` |
| Original four-page dashboard | `.venv/bin/python -m pip install -r requirements-dashboard-lock.txt` |
| JEPA prediction extension | `.venv/bin/python -m pip install -r requirements-dashboard-prediction-lock.txt` |
| Classical time-series presentation | `.venv/bin/python -m pip install -r requirements-dashboard-lock.txt` |

```bash
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m pip check
.venv/bin/python -c 'import solar_flare_jepa; print("installed import OK")'
```

Use a normal install for strict source/provenance checks; reinstall after source
changes. Pytest's configured `src` injection alone does not verify installation.
The main lock includes Astropy/cdflib; the V1 lock recursively includes training
and base dependencies. Existing SoLEXS runtime is under ignored
`results/solexs_integration_runtime/`, not `.venv`; it is machine-specific.
A new environment changes runtime identity: never replace the currently bound
G4 environment or reuse its approval after dependency changes without rebinding.

## 4. Restore inputs and run the matching verification

Restore only the selected workstream's inputs to the manifest-relative paths.
Compare bytes/SHA-256 before loading a checkpoint, and use only trusted bundles.
A matching filename or date is insufficient. `.gitignore` is not a backup.

### Main foundation

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/register_aditya.py --help
.venv/bin/python scripts/register_aditya.py \
  --config configs/data/solexs_storage.json --verify
```

The last command requires both original ZIPs. Without local data, synthetic/unit
checks remain possible; do not fabricate inputs. Public reference-only acquisition
syntax, if separately intended: `.venv/bin/python scripts/download_data.py --manifest configs/data/noaa_sample.json`.
It downloads pinned NOAA samples; it is not a PRADAN client or a V1 restoration.

### V1 and EDA

On `v1` or its appropriate descendants, provision all four manifest selections
(May–August, 123 files, 36,535,474 bytes) and the original run bundle.
Read-only identities:

```bash
.venv/bin/python scripts/acquire_goes_history.py --config configs/data/v1_goes_202405.json --verify
.venv/bin/python scripts/acquire_goes_history.py --config configs/data/v1_goes_202406.json --verify
.venv/bin/python scripts/acquire_goes_history.py --config configs/data/p2_goes_july2024.json --verify
.venv/bin/python scripts/acquire_goes_history.py --config configs/data/v1_goes_202408.json --verify
.venv/bin/python -m pytest -q tests/test_v1_foundation.py tests/test_statistical.py tests/test_jepa.py tests/test_v1_runner.py
```

Full historical regression command: `.venv/bin/python -m pytest -q` on the V1
branch. It includes bounded fit tests; it is **not** the V2 nonfitting gate check.
On the EDA branch, `.venv/bin/python scripts/verify_presentation.py` checks
committed figures/notebook identities and original run/raw-data alignment.

A separately authorized **new** V1 comparison uses
`.venv/bin/python scripts/run_v1_comparison.py --root "$PWD" --output-dir results/experiments/v1-new-authorized-run`.
This performs fitting and scoring; do not include it in interruption recovery or
reuse `v1-full-20261009`. Retraining cannot recreate the original bytes by fiat.

### Dashboard and prediction

On `presentation/solarjepa-streamlit-dashboard`, restore May/June raw inputs:

```bash
.venv/bin/python scripts/verify_dashboard.py
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

On `codex/solar-flux-prediction`, restore the 31 August files and pinned seed17
JEPA checkpoint; supervised overlay requires its matching seed17 checkpoint.
The app does not read archived prediction arrays. Explicit replay also needs
`summary.json` and `test_predictions.npz`:

```bash
.venv/bin/python scripts/verify_flux_prediction.py --root "$PWD"
.venv/bin/python -m pytest -q tests/test_flux_prediction.py tests/test_flux_prediction_replay.py tests/test_flux_prediction_ui.py tests/test_dashboard.py tests/test_dashboard_ui.py
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

Open [local dashboard](http://127.0.0.1:8501). Launch from checkout root so
`.streamlit/config.toml` applies (loopback, telemetry off, watcher disabled).
Default replay issue is `2024-08-01T02:00:00Z`, 120-minute context/30-minute horizon.
Unavailable or altered artifacts must fail closed. Old dashboard status is a
frozen presentation snapshot, not current V2 authority.

### V2: nonfitting recovery only

Use `codex/v2-experimental-validation-readiness` at `8e9ce06407d5`, read
`docs/protocols/PHASE2_V2_DEVELOPMENT_PROTOCOL_V1.md`,
`docs/PHASE2_V2_G4_EXECUTION_PREPARATION.md` and the superseding
`docs/PHASE2_V2_G4_LIFECYCLE_SAFETY.md`. Restore May–July inputs and private
reservation artifacts; preserve historical V1 checkpoints without model use.

```bash
.venv/bin/python scripts/run_v2_goes_pilot.py --root "$PWD"
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
NUMEXPR_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4 BLIS_NUM_THREADS=4 \
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_v2_pilot_protocol.py tests/test_v2_pilot_reporting.py \
  tests/test_v2_pilot_guard_bridge.py tests/test_v2_descriptive.py
```

First command is metadata-only: 20 processes/18 selected models, no fitting or
inference. Do not append execution flags. The historical M5
`preflight_v2_goes_pilot.py` deliberately returns exit **3** for a blocked pilot,
even when data are ready; do not interpret that as permission or a broken test.
Older V2 checkpoints have these exact scoped checks, verified against source
but **not rerun** as part of this documentation review. Use each branch's own
normal installation. They do not execute the full scientific study:

| Branch / checkpoint | Nonfitting check |
|---|---|
| `feat/v2-m0-m1-validation-foundation` / `fd7203bf9a2e` | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_independent_records.py tests/test_independent_diagnostics.py tests/test_independent_integrity.py` |
| `research/v2-m2-statistical-validation` / `94cae59398e5` | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_m2_contracts.py` |
| `research/v2-m3-inference-remediation` / `5e88f3a71092` | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_m3_inference.py -k test_invalid_method_configuration_rejects` |
| `feat/v2-training-protocol-feasibility` / `ac3428f910b3` | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_v2_losses.py` |
| `feat/v2-model-evaluation-integration` / `2e3f87111ab7` | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_v2_descriptive.py` |

M3's check validates six invalid configurations only. M2 includes bounded
synthetic contract/bootstrap checks; M4A checks loss/autograd arithmetic. Broader
interface/proposal suites contain synthetic fits. Do not import M3's experimental
inference into latest V2: latest reporting is descriptive-only.

**Current G4 state:** pending approval, inactive reservation; approved file and
pilot output absent. Local `results/v2-g4-mba-m2-20261017/` is under primary
storage, outside the execution checkout. Its path bindings are machine-specific.
Recover privately, revalidate and rebind against the intended source/runtime.
Neither this guide nor a copied JSON can manufacture owner authorization.

If a future authorized pilot is interrupted: zero retries/resume are allowed.
There is no shipped `--recover` CLI. Supported **stop-only** API is
`PilotSupervisor.cleanup_orphan()` after reconstructing the exact original
plan/limits/code/config identities and inspecting existing
`OUTPUT/supervisor/supervisor.json`. It authenticates durable ownership tokens,
PID/group/session/UID/birth and takes the lock. Do not call `.run()` to recover,
kill bare saved PIDs, erase `.pilot-started`, or invent a recovery flag. Ambiguous
ownership/live descendants/active locks require investigation and may fail closed.
INT/TERM/HUP cleanup is implemented; SIGKILL/host loss cannot be caught. No current
pilot output exists, so no orphan recovery is currently needed.

### Independent scientific/research tracks

SoLEXS integration (`codex/solexs-scientific-integration`):

```bash
.venv/bin/python -m pytest -q tests/test_solexs_interface.py tests/test_solexs_integration.py tests/test_solexs_reference.py
.venv/bin/python scripts/validate_solexs_reference.py --help
.venv/bin/python scripts/prepare_solexs_native.py --help
```

Restore original archives plus the tools/CALDB/reference assets named by
`data/manifests/solexs_reference_validation.json` and the historical evidence
manifests. Native evidence generation needs fresh output identities and explicit
scope; it does not approve UTC conversion or calibration. Phase E and provisional
branches are listed in the handoff. **Original provisional run bundle was not
found**; locate it from its custodian before claiming a fresh reproduction.
`run_solexs_provisional.py` trains and is not a safe recovery check.

External preparation (`research/goes-external-validation`):

```bash
.venv/bin/python -m pytest -q tests/test_external_preparation.py tests/test_external_config.py tests/test_event_matching_external.py tests/test_external_validation.py tests/test_external_flux.py
```

Restore January's 31 raw files/catalog inputs and the 13-file preparation bundle
at `results/experiments/goes-external-january2025-acceptance-d/`, authenticated by
`data/manifests/datasets/goes_external_january2025.json`.

External model evaluation (`research/goes-external-model-evaluation`): set
`V1_ARTIFACT_ROOT` and `GOES_PREPARATION_ROOT` to the restored repository roots
that own these immutable bundles (not to the bundle directories themselves):

```bash
.venv/bin/python -m pytest -q tests/test_external_model_inputs.py tests/test_external_model_metrics.py tests/test_external_model_pairing.py tests/test_external_model_runner.py
.venv/bin/python scripts/evaluate_external_models.py \
  --root "$PWD" --config configs/evaluation/goes_v1_external_january2025.json \
  --v1-dir "$V1_ARTIFACT_ROOT/results/experiments/v1-full-20261009" \
  --preparation-dir "$GOES_PREPARATION_ROOT/results/experiments/goes-external-january2025-acceptance-d" \
  --output-dir results/experiments/handoff-read-only-preflight-new
```

This is a nonfitting/noninference preflight, not another evaluation. Do **not**
append `--execute` or reuse the historical approval reference. The completed
six-file evaluation bundle is `results/experiments/goes-v1-external-january2025-approved-run/`;
its identity authority is `data/manifests/phase1_goes_external_execution.json`.
January was previously inspected and evaluated; confirmatory status is unavailable.

Classical time-series presentation (`presentation/time-series-requirements-completion`):
restore raw data and `results/presentation_time_series/diagnostics.json`, then:

```bash
.venv/bin/python -m pytest -q tests/test_presentation_classical.py tests/test_time_series_presentation.py tests/test_time_series_ui.py
.venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

Final deck (`presentation/final-time-series-presentation`): PPTX/PDF, images and
verification are already on GitHub. `python scripts/presentation/verify_deck.py`
requires document dependencies including `pypdf`, `python-pptx` and Pillow;
use `presentations/README.md` and an appropriate document runtime. Audit used
bundled document Python; the research environment lacked `pypdf`. Rebuilding
charts additionally needs the time-series source checkout/data/ignored payload.
Do not install dashboard/model dependencies into the older deck branch by guess.

## 5. What GitHub cannot restore

| Asset / current local home | GitHub? / recovery requirement |
|---|---|
| Source, tests, configs, lockfiles, small identity manifests, reports | Yes, **on their own branches**; main alone is insufficient. |
| Final PPTX/PDF, committed figures/captures/notebook | Yes, on presentation branches. |
| Primary `data/raw/`, `data/processed/`, original SoLEXS ZIPs/tools/CALDB | No. Secure owner backup or authorized source reacquisition; verify manifests; preserve originals. |
| Primary `results/experiments/v1-full-20261009/` | No. Full strict bundle + all 9 checkpoints available locally. Prediction worktree has only seed17 JEPA/supervised + summary/NPZ. |
| External raw/catalog/preparation bundle | No. Preparation worktree owns raw/prepared bytes; external evaluation uses supplied locators. |
| External evaluation six-file bundle / SoLEXS reference/native bundles | No. Present in their corresponding worktrees and hash-matched during audit. |
| `results/experiments/solexs-provisional-v1-20261009/` | No; absent from all inspected worktrees. Expected `best.pt`, `predictions.npz`, `report.json`, `selection_frozen.json`, `artifacts.json`; recover from custodian/backups. |
| V2 reservation, pending approval, runtime/execution bindings | No; primary `results/v2-g4-mba-m2-20261017/`. Private, machine-bound, **not authorization**. Approved file absent. |
| `.venv/`, `.cache/`, SoLEXS runtime, installation state | No. Rebuild matching lock family; current G4 bindings become stale if runtime changes. |
| Untracked files, session/chat context, approval conversations, OS processes/locks | No. Preserve locally; request original owner evidence where required; never infer approval from Git messages. |

Before backing up, inspect the exact manifest paths rather than broad copying
entire result trees (the primary results tree alone exceeds 1.6 GB). Do not put
any ignored science/checkpoint/authorization asset into Git or use `git add -f`.

Useful fixed V1 SHA-256 identities (all under the strict bundle):

| File | SHA-256 |
|---|---|
| `summary.json` | `80eae588a706e4b4d84df0daa7e03dcfc54c53ee408d2d6aed30e4bcb9988daf` |
| `per_origin.json` | `133025c6921bcd575b727287b504550ff15e6e1d3ade8bcc39a5ff432056aa7f` |
| `test_predictions.npz` | `59bcd596fefd6b10edeec93a69d7172343d4ffb7dc120f98a5185c1e35a3da82` |
| `jepa_finetune_seed17.pt` | `3d18e1067b7eeaf2b64ea572ff48831559f5171b82e765bf56841f2903fdaf48` |
| `supervised_seed17.pt` | `973f784e2adecd5183bd11bd3f6d47f49c5a8786e603cac82c15e2854858273b` |

All nine checkpoint names follow `{jepa_finetune,jepa_frozen,supervised}_seed{17,29,43}.pt`;
remaining hashes are pinned in external-execution/preservation manifests. Expected
missing provisional `best.pt` SHA-256:
`619e0410bfe74f81a163fc1a00533c9ad5c74686a4c69bc4e53a31326b6ec449`.
Time-series diagnostics SHA-256:
`69935892e311ef4aacd00a7e9e6ccb055aac8abb1cda7ee988195d6f2fcc5675`.

After any authorized continuation, update the handoff with branch/revision,
actual checks, artifact identities, failures and the exact next gate. Before a
commit/push use `git diff --check`, `git diff --cached --name-status`,
`git check-ignore -v <actual-local-artifact-path>` and inspect staged file types.
Stage only intended code/docs/manifests. Push only the corresponding feature
branch. Merge/push-to-main remain separate explicit actions; this handoff has no PR.
