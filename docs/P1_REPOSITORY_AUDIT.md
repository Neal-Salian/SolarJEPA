# P1 starting-state audit and checkpoint

Date: 2026-10-03 (Asia/Kolkata). Scope: independently inspect the repository,
perform required Paperclip reconnaissance, prepare a proposed P1 design, and
publish the research branch. **No P1 implementation has been authorized.**

## Git state observed before edits

- Branch/HEAD: `main` at `1a4991da4dda9676caeb1d7e35a03408528c3188`.
- `git fetch origin` succeeded; local main and origin/main resolve to that same
  commit, and `git diff --exit-code main origin/main` passed.
- Tracked working tree/index were clean. The sole untracked file was the
  user-mentioned `.agents/skills/paperclip/SKILL.md`; it was preserved.
- PR #4 merged D.1's `1abed0f` into main. The existing C, D, D.1, storage, and
  agent-instruction branches were inspected and preserved.
- `research/experiment-evaluation-foundation` was absent locally/remotely after
  fetch. It was created from that synchronized main and published with
  `git push -u origin research/experiment-evaluation-foundation` before edits.
  Only this feature branch is used. No merge or push to main occurred.

These are SolarJEPA `git` observations. No `paperclip git` command was used.

## Implemented state verified

| Area | OBSERVED evidence | Consequence for P1 |
|---|---|---|
| Source/config/dependencies | Source package contains the data modules only; no forecasting/model/evaluation/experiment implementation. Model and experiment JSON explicitly remain proposals. No torch/statsmodels/ARCH dependency is declared. | Add a small independent foundation after approval; do not reimplement data access or claim a trained model exists. |
| GOES | Pinned-path verification checks six local NetCDF files. Fresh `read_goes` output equals the saved Parquet, including dtypes/coordinates. Manifest/processed hashes match its sidecar. | Reuse the adapter and quality/time policies as an external reference smoke. |
| Reference coverage | 4,320 one-minute rows, July 1 through July 4 exclusive, 2024; 2,267 valid XRS-A and 4,318 valid XRS-B rows. | A fully observed multivariate sample is not implied. Prefer XRS-B for the initial real reference smoke. |
| Reference events | 94 catalogue state records, 28 IDs, 21 complete start/peak/end groups; 27 peaks, including two M peaks. | EDA counts are not forecast labels or adequate warning-performance evidence. |
| SoLEXS | Native loader preserves clock cards/units, copies LC/GTI arrays and streams PI chunks without UTC/GTI/calibration transformations. Tests exercise these boundaries. Both original registered ZIPs pass `verify_inventory`. | Native access is reusable, but cannot supply P1 scientific forecasting data while the gate is pending. |
| Existing C/D/D.1 artifacts | D.1 native-report and readiness-probe bytes equal their preserved D outputs and match D.1 manifest hashes. | Preserve this validated foundation. This audit did not rerun full real FITS/PI inspection or calibration diagnostics. |
| Experiment artifacts | `results/schema.json` is an ignored list of six file-metadata inspections, not an experiment result schema. No forecast/evaluation run registry or fitted baseline was found. | A reusable schema belongs outside ignored `results/`; descriptive EDA is not an experiment result. |

Inspected source includes download/storage/inspection, GOES, EDA, SoLEXS native
access, and readiness-probe entry points; test fixtures and cases cover their
existing contracts. Configs, inventories, scientific evidence/gate manifests,
recent branch history, relevant reports, and existing local artifacts were
checked. Normal installed copies of all six data modules hash-match checkout
source. No installation repair or dependency update was needed.

## Discrepancies resolved without rewriting scientific history

1. README and the status tracker still described D.1 as awaiting main integration.
   Actual Git shows it merged at `1a4991d`. Their current-status text is corrected;
   historical D.1 reports/base commits remain unchanged.
2. The saved GOES EDA summary says no SoLEXS/ASPEX files exist. All its numerical
   summary fields match a fresh read, but the current implementation correctly
   says the report contains GOES only. The old output is preserved as historical;
   its wording is not used as evidence of archive absence.
3. D.1 manifests retain their original `milestone_state: IN_PROGRESS`. The
   completed/merged evidence audit does not mean its scientific prerequisites
   were resolved. These historical manifests still correctly record the blocked
   gate and pending response; they are not rewritten to imply approval.

## Executed verification

| Check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | 166 passed, one NumPy ndarray binary-compatibility RuntimeWarning, 42.58 seconds. |
| Normal imports without `PYTHONPATH`; installed source identities | Imports passed; download/storage/inspect/GOES/SoLEXS/EDA module hashes equal checkout source. Existing CLI/outside-checkout tests passed within the full suite. |
| `.venv/bin/python -m pip check` | No broken requirements; pip also reported its unwritable user cache was disabled. |
| Read-only Python audit using `verified_manifest_paths`, `read_goes`, `assert_frame_equal`, `summarize`, `load_inventory`, `verify_inventory`, and SHA-256 | Six NOAA identities, Parquet equality, two SoLEXS archive identities, and preserved C/D/D.1 artifact identities passed; the one historical EDA prose difference is recorded above. |
| `git check-ignore -v` on actual NOAA/SoLEXS/processed/report paths | Raw inputs, Parquet, and generated reports remain protected by current ignore rules. The Paperclip pointer is not ignored. |
| `git ls-files` and `git log --all --name-only --format=` path scan | No prohibited science/model binaries or non-placeholder raw/interim/processed/results paths in index or inspected local/ref history. |
| Documentation checks and final fetch | Local Markdown links/gate declarations pass; all 14 numbered references have Paperclip line URLs; 11 exact searches are recorded. Protected source/tests/scripts/configs/manifests/dependencies/ignore rules/AGENTS.md remain equal to main. `git diff --check` passes; main and origin/main remain `1a4991d`. |

No new behavioural tests were written for documentation-only work. P1-specific
tests in the proposed design are planned, not executed. Neural forecasting,
new-environment portability, operational latency, ARCH/GARCH adequacy, and all
unresolved SoLEXS scientific semantics remain untested.

## Paperclip pointer recommendation

**OBSERVED:** the file is untracked, not ignored, credential-free, and has no
machine-specific project path. No `.agents`/`.codex` files are currently tracked;
the repository does version-control stable `AGENTS.md` instructions.

**DOCUMENTED/OBSERVED installation evidence:** `paperclip skill` describes
`paperclip install` as installing a lightweight agent-skill pointer.
`paperclip install --help` exposes a project-directory option. Inspection of
the installed `gxl_paperclip.cli.skill` implementation confirms that
`fetch_agent_skill` prefers the lightweight placeholder, `_write_codex` writes
`.agents/skills/paperclip/SKILL.md` under the selected target, and `install_skill`
registers installed paths for later refresh. This is agent configuration,
not scientific data, a Paperclip paper repository, or a requirement to commit it.
The installer does not establish the user's intended Git policy.

**Recommendation:** leave this installed file unchanged and untracked in the
P1 scientific/design commit; add no blanket ignore. It is suitable for a
separate reusable agent-configuration change if the project chooses to require
Paperclip across collaborators, with its dynamic `paperclip skill` instructions
retained. That separate choice is not inferred from installation alone.

## Scientific status and next decision

**OBSERVED:** scientific manifests set application/clock/calibration approval
false and record `BLOCKED_FOR_PHASE_E`. The request's sent status is explicitly
USER_REPORTED_ACTION, independently unverified, with no authoritative reply
available. No external message was sent by this agent.

**UNKNOWN/PENDING:** pipeline-1.1 TIME/MJD/date precedence; clock/UTC convention;
LC/PI bin timing; continuous GTI START/STOP and exposure semantics;
correction/HK compatibility; PI-to-response channel mapping; approved calibration
and real cross-instrument alignment. No correction, channel offset, HK
substitution, physical-flux interpretation, real chronology, final dataset,
historical acquisition, training, or novelty claim was introduced.

Review the [literature findings](P1_LITERATURE_RECONNAISSANCE.md) and
[proposed P1 design](P1_PROPOSED_DESIGN.md). The required next action is the
user's checkpoint decision before major implementation. Phase E remains
**BLOCKED pending authoritative SoLEXS evidence** regardless of P1 approval.
