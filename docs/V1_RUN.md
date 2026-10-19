# v1: how to run the comparison (Mac M4, 16 GB) + Claude Code prompt

Status when pushed (2026-10-09): code complete and unit-tested on Windows
(Python 3.13.11, CPU). New-module tests pass. **The full end-to-end run has
NOT completed yet**: the 8 GB Windows laptop ran out of memory during the
smoke run, so the first successful run will happen on the Mac. Treat every
number as unproduced until `summary.md` exists.

## What v1 contains

| Piece | File |
|---|---|
| Plan and protocol | `docs/V1_PLAN.md` |
| May/June/August 2024 pinned acquisition configs + manifests | `configs/data/v1_goes_2024{05,06,08}.json`, `data/manifests/goes_v1_*.json` |
| Contiguous multi-manifest GOES dataset kind | `data/foundation.py`, `experiments/config.py` (`goes_historical_multi`) |
| Experiment (train May 1–Jul 22, val Jul 22–Aug 1, test Aug 2024) | `configs/experiments/v1_goes_2024.json` |
| Model list fixed before results | `configs/experiments/v1_models.json` |
| ARIMA grid, AR(1)+constant/ARCH/GARCH/GJR-GARCH (Normal/t), empirical persistence | `forecasting/statistical.py` |
| Temporal JEPA (EMA target encoder, latent predictor, quantile head) + supervised control | `training/jepa.py` |
| Log-space pinball/coverage/width + daily block bootstrap | `evaluation/probabilistic.py` |
| Runner and report/figures | `experiments/v1.py`, `experiments/v1_report.py`, `scripts/run_v1_comparison.py` |
| Tests | `tests/test_v1_foundation.py`, `tests/test_statistical.py`, `tests/test_jepa.py` |

Notable decisions, all made before any v1 result was observed:

- **GARCH estimation is two-stage.** The joint AR-GARCH MLE converged to an
  explosive mean (AR coefficient 10.4 on XRS-B) on these heavy-tailed data
  (residual kurtosis 74 / 306). v1 fits the AR(1) mean by OLS, then each
  variance model on the residuals with a multi-start MLE (the default single
  start stopped near its initial values). All variance models share one mean.
- **SARIMA is supported but excluded from the run.** Log-difference ACF shows
  no 60-minute or daily periodicity (|ACF| ≈ 0.01), and an s=60 fit did not
  finish in 28 minutes. It is reported as a justified exclusion, not a result.
- JEPA is width 32, 20,000 evenly spaced training windows, 3 seeds, selected
  on validation pinball only. `supervised` is the identical architecture
  without JEPA pretraining (the ablation that isolates JEPA's contribution).

## Exact commands (macOS, from a fresh clone)

```bash
git clone https://github.com/Neal-Salian/SolarJEPA.git && cd SolarJEPA
git fetch --all && git switch v1
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-v1-lock.txt
.venv/bin/python -m pip install --no-deps .      # normal install: the provenance guard needs it

# Data: ~37 MB from NOAA/NCEI, pinned by SHA-256 (July uses the P2 config)
for c in configs/data/p2_goes_july2024.json configs/data/v1_goes_202405.json \
         configs/data/v1_goes_202406.json configs/data/v1_goes_202408.json; do
  .venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --config "$c"
done
for m in goes_p2_july2024 goes_v1_202405 goes_v1_202406 goes_v1_202408; do
  .venv/bin/python scripts/acquire_goes_history.py --root "$PWD" --verify --manifest data/manifests/$m.json
done

# Tests (expect the full suite plus the new tests to pass on macOS)
.venv/bin/python -m pytest -q tests/test_v1_foundation.py tests/test_statistical.py tests/test_jepa.py
.venv/bin/python -m pytest -q

# 1) Integration smoke (~15 min): relaxed provenance, 1 seed, tiny JEPA budget
.venv/bin/python scripts/run_v1_comparison.py --root "$PWD" \
  --output-dir results/experiments/v1-smoke --dev --quick

# 2) Reportable strict run (~2–3 h on CPU): clean tree + normal install required
.venv/bin/python scripts/run_v1_comparison.py --root "$PWD" \
  --output-dir results/experiments/v1-full-$(date +%Y%m%d)
```

Outputs (git-ignored): `summary.md`, `summary.json`, `per_origin.json`,
`test_predictions.npz`, three PNG figures and JEPA checkpoints `*.pt`.

## Prompt for Claude Code on the Mac

Paste this into Claude Code from the repository root:

```text
You are continuing the SolarJEPA v1 milestone on branch `v1` (based on P2 commit
656e540). Read AGENTS.md, docs/V1_PLAN.md and docs/V1_RUN.md first, and follow
AGENTS.md's scientific-integrity and Git rules. Use Superpowers skills where they
help (verification-before-completion, systematic-debugging for any failure).

Goal: produce the first complete, reproducible v1 comparison of temporal JEPA vs
ARIMA vs AR(1)+constant/ARCH/GARCH/GJR-GARCH vs the six P2 baselines on GOES-16
XRS (train May 1–Jul 22 2024, validation Jul 22–Aug 1, test August 2024).

Steps:
1. Verify you are on `v1`, the tree is clean and `git log -1` matches origin/v1.
   Create the venv and install exactly as docs/V1_RUN.md says (normal install,
   not editable). Acquire and --verify all four monthly GOES manifests.
2. Run the new tests, then the full test suite. Report counts. If anything fails,
   debug the root cause before changing code; do not weaken tests or checks.
3. Run the --dev --quick smoke. If it fails, fix the bug with a regression test,
   commit it on `v1`, reinstall normally, and rerun the smoke.
4. Run the strict full comparison (no --dev). Do not change
   configs/experiments/v1_models.json or v1_goes_2024.json after seeing any
   result; if a change is unavoidable, record why in the results doc and treat
   the August test as no longer untouched.
5. Read summary.md. Write docs/V1_RESULTS.md with: the test and validation
   tables, strata table, bootstrap comparisons, model failures, the train-only
   diagnostics (ACF, ARCH-LM), the GARCH fitted parameters and persistence, and
   the JEPA training curves and collapse statistics. State plainly whether JEPA
   beat the supervised control and the GARCH family, with the bootstrap CIs.
   Use DOCUMENTED/OBSERVED/INFERRED/UNKNOWN labels, list the limitations (four
   months, one satellite, overlapping origins, no event labels, five quantiles
   not exact CRPS), and never round away a negative result.
6. Copy the three figures into docs/figures/v1/ only if each is under 500 KB.
   Never commit data, results/, checkpoints or .npz files (check git status and
   `git check-ignore -v`).
7. Commit with Conventional Commits and push only to origin/v1. Do not merge,
   do not push main or any other branch, and do not force-push. Stop and
   summarize for human review.

Hardware note: Mac M4 16 GB. Keep JEPA on CPU (threads=4 as configured) so the
run matches the declared config; MPS is untested in this repo.
```

## Known limitations

Four months of one satellite near solar maximum; overlapping contexts, so
origins are not independent; retrospective archive data with unknown
operational latency; no flare-event labels; five quantiles give a quantile
score, not exact CRPS; CPU budgets limit model size. SoLEXS remains
`BLOCKED_FOR_PHASE_E` and is not used.
