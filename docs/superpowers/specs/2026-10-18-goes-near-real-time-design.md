# GOES near-real-time foundation design

## Authorized outcome and boundaries

Build a provenance-preserving NOAA XRS ingestion/cache and V1 inference foundation.
The user explicitly selected Superpowers architecture, implementation and independent
review subagents, authorized branch-only commits/pushes, and requested continued
execution. Preserve all five Streamlit pages and the historical prediction page;
leave V2, models, normalization, training and benchmark definitions unchanged.
The baseline is verified published `codex/solar-flux-prediction` at `a495151`,
not `main`: this follows the task-specific request. Local `main` and `origin/main`
were equal after fetch. Unrelated untracked files in the original checkout remain
untouched. New branch: `codex/goes-near-real-time-foundation`.

## Selected approach and alternatives

Use a separate UI-independent ingestion module and explicit CLI. Keep raw HTTP
responses and receipt manifests in ignored local storage. Validate saved snapshots
without network. A separate inference service accepts only the existing immutable
GOES-16 science replay contract; live SWPC input is rejected before model loading.
This gives a useful foundation without assuming scientific equivalence.

Reusing the historical dashboard directly for live data would bypass its August,
GOES-16, source identity and retrospective availability contracts. An autonomous
polling service or new dashboard mode would add operational/UI scope before the
input contract is established. Neither is part of this milestone.

## Data and provenance contract

Support only explicit allowlisted NOAA SWPC primary/secondary six-hour JSON URLs.
Use bounded downloads, finite timeout, no redirected source, strict JSON decoding,
content-addressed immutable raw bytes and atomic receipt manifests. Each acquisition
has its own receipt time even for unchanged bytes. Store URL, product role, SHA256,
bytes, HTTP Date/Last-Modified as transport metadata, and local receipt UTC.
Publication time is UNKNOWN/null: receipt time and HTTP headers do not establish
per-row publication time. Cache reads recheck identities and never reset freshness.
No implicit cache fallback or polling. Serialize writers; retention is explicit
manual maintenance outside this milestone.

Validate explicit UTC minute tags, unique ordered paired A/B samples, satellite
identity, declared energy bands, finite positive flux eligibility, contamination,
minute continuity, future tags, age and a complete 120-minute context. Missing or
invalid values remain unusable; never interpolate, forward-fill, zero-fill, rename
quality flags to science masks, or substitute another satellite silently.
Energy compatibility alone is insufficient for checkpoint eligibility.

## Inference and time contract

SWPC JSON time-tag bin placement and science-quality parity are not established;
V1 is a GOES-16 science-product model, not a validated GOES-18/19 operational model.
Therefore every SWPC assessment reports model_input_ready=false with blockers.
No override or user-supplied compatibility assertion enables a live forecast.

The supported bounded adapter replays the pinned saved GOES-16 science inputs and
checkpoint. Reuse the exact V1 120x2 context, positive complete masks, trained
normalization, spec fingerprint, weights-only checkpoint loader and 30-bin future
grid. Never retrain or call lower-level normalized prediction to bypass contracts.
Observation start/end, publication time (unknown), retrospective forecast origin,
execution UTC, grid interval and model horizon are separate fields. The 30-bin
model horizon is not a 30-minute warning capability. Delayed replay is not an
operational forecast. Receipt/execution time must never be relabeled as the old
forecast origin or inferred historical publication time.

## Verification and failure behavior

Tests cover immutable cache/replay, malformed and oversized responses, invalid
provenance, stale/clock-skewed observations, missing channels/bins, contamination,
nonpositive flux and satellite changes. Offline deterministic replay compares the
existing saved observations and archived point/quantile predictions with fixed
rtol=1e-6 and atol=1e-15 W/m2. Network is blocked during replay.
Run baseline/full suite, normal installed imports/CLI, existing five-page UI tests,
independent scientific/code review, diff/ignore/index checks and final branch push.
Live feed availability and a snapshot's observed age are samples, not latency SLAs.

## Readiness boundary and next milestone

Ready for explicit acquisition, diagnostics and offline research replay after
verification; not ready for live V1 forecasts, alerts, operational use or calibrated
uncertainty claims. Next milestone: authoritative time/QC mapping and matched
operational/science cross-satellite comparison with a prospective shadow-capture
latency/gap study. No training or model replacement is authorized by this design.
