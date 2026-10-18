# V3 independent review and verification

Date: 2026-10-18. Scope: [research design](V3_RESEARCH_DESIGN.md),
[evidence audit](V3_EVIDENCE_AUDIT.md), [literature](V3_LITERATURE.md), and
[compact provenance](../data/manifests/v3_research_evidence.json).

## Research and independent review

Superpowers parallel-agent, brainstorming/design, worktree, code-review and
verification guidance was used intentionally for this research milestone.
Separate agent contexts investigated literature, actual V1/V2 architecture and
scientific protocol. The coordinator inspected source and saved summaries and
authored the resulting design. Two agents then independently reviewed the actual
draft, returned corrections, and rechecked the corrected text. They had contributed
domain research but did not author the design; this is internal independent
review, not external peer review or a formal scientific validation.

| Review | Important findings resolved | Final verdict and scope |
|---|---|---|
| Scientific protocol/statistics | Fixed promotion estimand across unequal folds/seeds; per-channel calibration gates; unavailable promotion mean for any incomplete planned fit; interval-only CQR nesting; version-bound literature | **PASS for research-branch publication**, no remaining blocking/important findings. Independently matched 11 ref pins, 22 source-file identities, V1 summary identity and 28 aggregate metric values to stored evidence. |
| Literature/objective/uncertainty | Fixed-lead across-origin teacher/prediction diversity and content/position probes; explicit variance/covariance objective; point-only tuning metric; raw versus calibrated promotion; disjoint calibration wording and source-version caveats | **PASS for research-only publication**, no unresolved important findings. Checked mechanism/scoring assumptions, literature limitations, update counts, resource arithmetic and TCN receptive fields. |

The positional shortcut check matters: a local teacher sees one patch token, so
position differences can create apparent diversity without flux information.
The document now requires sensitivity across origins at each fixed lead, not
pooled across leads. Likewise, calibrated interval endpoints do not become an
ordered five-quantile forecast and do not enter the primary pinball gate.

Neither reviewer authorizes data access, fitting, model implementation, test
release or integration. The literature reviewer did not verify Git hashes or
pytest execution; the protocol reviewer did verify the listed identities and
stored aggregate arithmetic. The architecture research agent supplied source and
saved-aggregate findings before its final turn hit a usage limit; it is not counted
as a completed final review. The coordinator and protocol reviewer independently
checked the evidence used in the package.

## Executed checks

| Check | Observed result | What it does not establish |
|---|---|---|
| Main-based suite before research edits | 166 passed, 1 warning, 35.79s | No V1/V2 model-suite qualification or V3 scientific performance |
| Same suite after document preparation | 166 passed, 1 warning, 35.19s | No training, validation predictions or model resource benchmark |
| Normal imports with this worktree's `src` explicitly on `PYTHONPATH` | Package and `data.goes` imported from this isolated worktree | No normal-install qualification of later milestone branches |
| Coordinator manifest consistency | 45 ref/file/summary/aggregate/preservation checks passed | Hash identity does not establish original scientific correctness or freshness |
| Independent protocol evidence check | 11 refs, 22 file byte/hash identities, V1 summary identity and 28 stored aggregate values matched | No independent replay of original fitting or held-out scoring |
| `git check-ignore -v` | Actual local NOAA NetCDF, SoLEXS ZIP and saved result summary protected; representative interim/processed/checkpoint paths protected | No bulk data was staged or uploaded |

Test command, run from the isolated research worktree:

```sh
/Users/nealsalian/Desktop/SolarJEPA/.venv/bin/python -m pytest -q
```

Pytest's existing configuration selects this worktree's `src`. The retained warning
is `RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility`
in `test_cf_clock_bin_end_quality_and_source_retention`. No dependency pin, source
or protocol was changed to suppress it. The identical 166-test rerun is the final
test result; no broader V1/V2 suite with fitting fixtures was launched.

The 45 coordinator checks comprise 11 refs, 22 source files, two saved summaries,
eight neural stratum rows and two original untracked-item identity records. Each
row check includes its stored count and both metrics. These assertion counts are
software/provenance checks, not independent scientific observations. One-off
standard-library inspection snippets were used; no duplicate reusable research
utility or tests that merely mirror the document were added.

## Publication boundary and remaining work

Only four research Markdown files and the small JSON manifest are intended for
the commit. Before publication, inspect staged names/content, `git diff --check`,
history since main, ignore rules and status; afterward verify the remote research
head equals local HEAD and main remains pinned. No PR or merge is requested.
Original scientific inputs, model artifacts and V1/V2 source/configurations are
unchanged. Original presentation-branch status and the two untracked-item content
identities were checked after the research audit.

Remaining unknowns are explicit: eligible fresh evaluation data and prior private
exposure, sufficient independent event/fold support, current authoritative L2
documentation, upstream/as-issued causality, acceptable local-teacher diversity,
calibration under shift, sustained M2 training cost and V3 effectiveness.
The next proposed V3-M0 milestone implements synthetic-only contracts and
diagnostics after scope review; actual scientific experiments remain separate.
