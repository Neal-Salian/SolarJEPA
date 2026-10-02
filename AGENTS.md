# SolarJEPA agent guidelines

These are stable repository-wide rules. Task-specific user instructions override
default workflows; approvals are action-specific. Stay within the authorized milestone.

## Verify real state before editing

- Inspect source, tests, configuration, scripts/CLIs and Git status, branches,
  refs, history and diffs. Check runtime behavior, generated artifacts and
  scientific inputs/manifests where relevant. Preserve validated existing work.
- README, status documents, TODOs, plans, comments, validation reports, commit
  messages and previous agent summaries are supporting context, not proof of
  implementation state. Surface discrepancies and prefer verified code/executable
  evidence. Do not reimplement functionality because documentation says it is
  missing, or assume it works because documentation says it is complete.

## Git milestone workflow

- Verify clean `main` and relevant remote state before work; fetch when appropriate.
  Stop on unexpected changes or divergence rather than resetting user work.
- Create one meaningful branch for the active milestone from verified `main`.
  Publish it to GitHub and configure upstream tracking before milestone work.
  Make changes only on that branch; do not create future milestone branches early.
- Use focused Conventional Commits and push milestone commits only to their
  corresponding feature branch. Preserve meaningful branches for traceability.
- Integration into `main` requires explicit user authorization or a user-managed
  PR. Any agent-performed merge or push to `main` requires explicit authorization
  for that action; merge approval is not automatically push approval.
- "Phase complete", passing tests and "ready" are never integration permission.
  Never force-push, rewrite shared history or delete milestone branches without
  explicit authorization.

## Scientific integrity

- Never silently invent or assume missing observations, timestamps, calibration,
  units, physical quantities, detector semantics, quality rules, flare labels,
  scientific metadata, model metrics or uncertainty values.
- For scientific conclusions, distinguish **DOCUMENTED** (authoritative
  documentation), **OBSERVED** (direct file/execution evidence), **INFERRED**
  (derived but not directly documented) and **UNKNOWN** (not established).
  Attribute user reports explicitly; do not promote inference into documented fact.
- Keep unknowns unknown. Prefer authoritative instrument/data documentation for
  scientific semantics. Distinguish nominal filename dates, measured coverage,
  acquisition time and registration time; filesystem timestamps are not substitutes.

## Scientific data and provenance

- Follow the actual `.gitignore` and [storage policy](docs/DATA_STORAGE.md).
  Never commit raw scientific data: downloaded archives, extracted FITS/science
  products, large intermediate arrays, temporary extraction artifacts or
  intentionally ignored bulk datasets. Keep credentials out of Git.
- Never use `git add -f` to bypass data protections. Before completion or push,
  verify ignore rules against actual paths and check the index/history for
  prohibited data; use `git check-ignore -v` and appropriate Git inspection.
- Treat original source archives as immutable unless an explicitly approved
  workflow permits otherwise. Track reproducibility code, configuration,
  manifests, provenance and checksums; use repository-relative/configurable paths.

## Architecture and implementation

- Use **Streamlit** for the initial frontend when frontend work is authorized.
  Keep it a thin presentation layer. Scientific processing, data loading,
  preprocessing, forecasting, evaluation, model and explanation logic belong in
  reusable UI-independent core modules, not Streamlit pages/callbacks.
- Preserve core independence so a later **React + FastAPI** frontend does not
  require rewriting the scientific/model pipeline. This is not permission to
  build React/FastAPI now.
- Understand existing architecture and reuse functionality before adding
  abstractions. Avoid unnecessary dependencies, speculative abstractions and
  unrelated refactors. Preserve backward compatibility where appropriate.
- Test meaningful behavior changes. Reproduce bugs before fixing them when
  practical; prefer root-cause fixes over symptom patches.

## Superpowers and verification

- Use available Superpowers skills intentionally when they improve the task:
  planning, appropriate brainstorming, TDD, systematic debugging, verification
  and code review. Do not invoke them mechanically. Workflows never override
  user approval gates, Git restrictions, scientific integrity or scope boundaries.
- Verify the final implementation after fixes with checks appropriate to scope:
  targeted/full tests, normal imports, CLI/runtime smoke checks, scientific and
  regression validation, artifact identities, portability and final review.
  Inspect `git diff`, `git diff --check`, status and relevant history before completion.
- Writing code is not evidence of success. Report only checks actually executed
  and their results; explicitly identify untested behavior and remaining limitations.

## Documentation and scope

- Documentation should reflect verified state without becoming the source of
  truth for implementation state. Preserve historical reports; do not rewrite
  them to imply later findings were known earlier.
- Keep phase results, plans, status and temporary findings in appropriate docs,
  reports or artifacts, not here. Keep this file stable and concise.
- For a material scope change, stop and report the discovery, evidence, impact,
  proposed approach, alternatives and decision required. Do not silently expand
  scope or begin another milestone without authorization.
