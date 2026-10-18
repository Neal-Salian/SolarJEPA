# GOES near-real-time forecasting foundation

Implementation date: 2026-10-18. Baseline: published prediction dashboard
`a495151` (`codex/solar-flux-prediction`). Feature branch:
`codex/goes-near-real-time-foundation`. This milestone adds a separate Python
core/CLI. All five Streamlit pages, their registries and the historical prediction
page are preserved. No V1 weights, train-fitted normalization, V2 or training
behavior changes.

**Readiness verdict:** usable for explicit NOAA acquisition, local diagnostics and
saved GOES-16 science replay. **Live V1 forecasting is unavailable.** Numerical
completeness does not establish scientific compatibility. Nothing here is
operationally validated; the model's 30-bin output is not evidence of a 30-minute
warning capability, event-detection performance or calibrated uncertainty.

## Official products and evidence

Research used NOAA sources accessed on 2026-10-18. These links are mutable;
operational roles and upstream product versions can change.

| Source | Evidence and availability | Support in this milestone |
|---|---|---|
| [SWPC GOES X-ray Flux](https://www.swpc.noaa.gov/products/goes-x-ray-flux) | **DOCUMENTED:** plots use one-minute averages in 0.05–0.4 nm and 0.1–0.8 nm bands and update each minute. Eclipse/calibration dropouts occur. | Product/channel documentation; a minute refresh is not a latency SLA. |
| [SWPC primary six-hour JSON](https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json) | **OBSERVED:** row satellite IDs, two energy bands and native tags. | Explicit bounded fetch/cache/assessment only. |
| [SWPC secondary six-hour JSON](https://services.swpc.noaa.gov/json/goes/secondary/xrays-6-hour.json) | **OBSERVED:** separate source with its own satellite/quality history. | Explicit selection; never automatic fallback or mixed with primary. |
| [SWPC instrument-sources mapping](https://services.swpc.noaa.gov/json/goes/instrument-sources.json) | **DOCUMENTED by the product page:** maps instrument primary/secondary roles to satellites. **OBSERVED:** XRS primary 18, secondary 19 on research date. | Research reference; row satellite identity is checked, roles never imply GOES-16. Not separately downloaded by intake. |
| [NCEI EXIS product catalog](https://www.ncei.noaa.gov/products/goes-r-extreme-ultraviolet-xray-irradiance) | **DOCUMENTED:** operational/science L1b/L2 NetCDF products, including one-second flux and one-minute averages. Recommends consulting product documentation and generally science-quality L2. | Existing pinned GOES-16 archive replay; no new NetCDF acquisition or product-version migration. |
| [NCEI XRS L2 Readme](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf) | **DOCUMENTED:** science processing incorporates revised calibration/algorithms and recovered data. Archive science latency described as three days or less, operational archive as one day. These are archive-product descriptions, not SWPC JSON delivery promises. | Establishes why archive and real-time products cannot silently substitute. |
| [NCEI XRS L2 User Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf) | Authoritative algorithm/time/quality reference. The existing V1 source reader validates explicit NetCDF schemas. The live guide download timed out in final research; no new JSON equivalence claim is based on it. | Further authoritative mapping is required before enabling live inference. |

**OBSERVED JSON fields:** `time_tag`, `satellite`, `energy`, `flux`,
`observed_flux`, `electron_correction`, and the upstream misspelling
`electron_contaminaton` (boolean). Preserve raw fields/bytes. `flux` is the
selected diagnostic value in W/m²; `observed_flux` and `electron_correction`
are retained, not combined into a new calibration or substituted for `flux`.
A true contamination boolean conservatively makes that row unusable for the
numerical context check. It is **UNKNOWN** whether this boolean is equivalent to
any particular V1 science electron/status flag. False is not a science-quality
certificate. Null/zero/negative flux remains unusable, never a quiet-Sun label.

**UNKNOWN:** exact SWPC JSON minute-tag placement within the averaging interval,
per-row publication times, full eclipse/interpolation/count/status flags,
calibration/quality parity with pinned science v2-2-1, cross-satellite V1 model
validity, guaranteed delivery latency, prospective forecast skill and uncertainty
calibration. Band agreement alone cannot resolve those unknowns.

**INFERRED:** receipt minus latest tag is an observed tag age at this client; it
is not pure instrument latency, publication latency, or the duration of a
completed forecast warning. No source guarantees inferred here.

## Architecture and scientific boundary

`data/goes_nrt.py` owns intake/cache/assessment and imports no model code.
`forecasting/nrt.py` owns the live refusal and saved science replay boundary.
`scripts/goes_nrt.py` provides explicit actions and structured JSON statuses.
The service reuses the existing UI-independent historical inference module
(`dashboard/prediction.py`, which imports no Streamlit), rather than duplicating
its model/source checks or changing its page.

Live `forecast_snapshot` always raises `NrtForecastUnavailable` before checkpoint
or historical-service access. There is no compatibility override. A successful
fetch, fresh tag, positive flux, paired channels or 120 consecutive tags cannot
turn SWPC JSON into a certified model input. Even GOES-16 rows would remain
blocked by unknown timing/quality parity.

Saved `replay_v1` accepts only a repository/storage root and historical origin.
It checks the immutable registry, 31 pinned August 2024 GOES-16 science files,
product/instrument semantics, source code and checkpoint SHA256. It reuses
`prepare_forecast` and `TrainedJepa.load/predict`, including safe weights-only
loading, seed 17, unchanged spec and normalization fingerprints. Inputs are
exactly 120 consecutive completed minutes × two positive finite quality-valid
channels. No missing, interpolated or invalid context is filled. The fitted V1
log10 transform and stored training means/scales are reused; nothing is refitted.
Future observations never enter model prediction. Arbitrary raw paths, contexts
and alternative checkpoints are not accepted by this adapter.

## Time fields

| Field | Meaning |
|---|---|
| Live `first_time_tag`, `last_time_tag` | Native NOAA observation tags; bin position remains UNKNOWN. No forecast origin is fabricated. |
| `received_utc` | Local UTC clock after the entire HTTP body arrived. Never reset by a cache read. |
| `http_date`, `http_last_modified` | Raw HTTP transport metadata. Neither is relabeled per-row publication time. |
| `publication_utc: null` | Observation publication time was not supplied/established. |
| Replay `observation_start_utc`, `observation_end_utc` | Validated science context interval `[origin−120 min, origin)`. |
| Replay `forecast_origin_utc` | Historical origin, distinct from execution time. Uses unchanged retrospective-bin-end V1 spec. |
| Replay `forecast_end_utc`, `horizon_minutes` | Grid `[origin, origin+30 min)`, one-minute bins. Model horizon only. |
| Replay `execution_utc` | Execution clock (or an explicitly injected reference in deterministic API tests). Does not imply historical data availability. |

Actual historical delivery/publication times are unknown. The unchanged V1 spec
is `retrospective_bin_end`, not an operational availability contract. Neither
receipt nor execution is backdated into model input availability.

## Explicit commands

Use the existing prediction environment/dependency pins; no new dependencies were
introduced. Install current source normally before installed-import/CLI checks:

```bash
python -m pip install --no-deps .
python scripts/goes_nrt.py fetch --product primary
python scripts/goes_nrt.py fetch --product secondary
python scripts/goes_nrt.py assess --receipt receipts/<receipt-id>.json
python scripts/goes_nrt.py forecast --receipt receipts/<receipt-id>.json
python scripts/goes_nrt.py replay --issue-utc 2024-08-01T02:00:00Z
python scripts/verify_flux_prediction.py
```

Paths default relative to the script's repository root, so commands work from
another directory. `--cache-root` selects a contained cache workspace; `--root`
locates the complete pinned science replay tree. `assess`/`forecast` accept
`--now-utc` as an explicit diagnostic replay reference and `--max-age-seconds`
(1–3600; default 300). That five-minute default is local policy, not NOAA's SLA.
Fetch records the measured receipt clock; the CLI cannot inject it.

Exit 0 with `ACQUIRED` or `ASSESSED` means that action succeeded; inspect
`assessment.compatibility.blockers` and `model_input_ready=false` separately.
`forecast` returns exit 2 / `FORECAST_UNAVAILABLE`, with no predictions or
historical fallback. `replay` returns exit 0 / `PASS` only when its pinned
contract passes; missing artifacts fail, never trigger downloads. Acquisition,
parsing, cache integrity and replay errors return exit 1 / `FAIL` as JSON.
Argparse usage errors use exit 2. Actual offline CLI processes install a network
audit denial; calling imported `main()` does not alter the host's global hooks
and reports `offline_network_blocked=false` accurately.

## Cache, validation and failure handling

Default ignored storage is `.cache/noaa/goes_nrt/`. This follows the repository's
[storage policy](DATA_STORAGE.md): no raw observations or weights are tracked.

- `objects/<sha256>.json`: exact immutable response bytes, shared by equal responses.
- `receipts/<uuid>.json`: separate acquisition record for each successful fetch,
  retaining URL/role, bytes/hash, measured receipt UTC and raw HTTP metadata.

The intake allowlists only the two HTTPS six-hour URLs, refuses redirects and
requires bounded Content-Length without Transfer-Encoding/chunked framing.
Default transfer/socket budget is 15 seconds, maximum 60; maximum body is
2,000,000 bytes and 1,500 rows. Real body reads use `read1` and the remaining
socket budget, preventing a full-buffer drip from resetting the body deadline.
DNS/TLS/header setup still depends on OS/socket-operation timeouts: this is not
a hard whole-call wall-clock guarantee. Chunked framing is refused because its
internal parser can otherwise wait for drip-fed framing inside one read.
An upstream framing change produces a clear failure, not permissive parsing.
Injected API transports must return promptly; arbitrary Python calls cannot be
preempted by the adapter.

Strict JSON rejects duplicate object keys, nonfinite numbers, overflow and unknown
required schema. Assessment checks UTC minute alignment, per-channel ordering,
duplicate time/channel identities, actual row satellite IDs, channel pairing,
whole-minute gaps, future tags/clock rollback and observation age. It separately
reports whole-snapshot gaps and the latest numerically complete 120-minute tail.
The tail check is a diagnostic only, not a science-quality eligibility mask.
Within-snapshot satellite changes, missing channels/minutes, contamination and
invalid flux are visible blockers. Role is retained as provenance; cross-receipt
role/satellite changes are not monitored. There is no resampling or implicit satellite switch.

Cache reads verify canonical identities, contained paths, symlink avoidance,
regular-file type, capped sizes and hashes. Files are staged and published
without overwriting an existing object. Equal bytes keep separate receipt
records; conflicting/corrupt bytes fail. A failed fetch never silently serves
old cache data or writes a successful receipt. Partial temporary files are
removed; an orphan object can remain if receipt publication fails, and is not a
successful acquisition. Local receipt records establish local integrity, not
cryptographically authenticated NOAA publication history.

Writers/maintenance must be serialized. Concurrent hostile file replacement is
not supported. Disk quotas, automatic cache pruning, scheduling, dashboards,
retries, fallback and alert delivery are not implemented. This is an explicit
command foundation, not an unattended service. Retain receipt/object pairs when
preserving provenance; perform storage retention as an explicit reviewed action.
No original science archives or existing caches are mutated by replay.

## Verification and remaining milestone

New tests create explicitly synthetic saved JSON in temporary directories. They
exercise offline cache replay and unsafe/malformed data without committing raw
science. Integration tests use existing ignored saved GOES-16 observations and
checkpoints; when absent those new integration tests skip explicitly, while the
CLI fails closed. Real replay compares context/masks/grid exactly and native
point/quantile outputs against saved V1 predictions with `rtol=1e-6`,
`atol=1e-15 W/m²`. Production replay never reads saved prediction arrays; they
are independent verification artifacts. Future-causality and source/checkpoint
corruption checks are covered. See [verification record](GOES_NRT_VERIFICATION.md)
for actual executed checks and independent review results.

Next milestone: establish authoritative SWPC time-bin and quality-field mapping,
record prospective publication/receipt histories, quantify latency/gaps, and
compare matched operational/science products and satellites. A reviewed scientific
input contract and prospective evaluation must precede live model inference.
This does not authorize retraining, V2 work, alerts or replacing historical pages.
