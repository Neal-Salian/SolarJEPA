# V2 M5.0 Integration and Readiness Report

## Verdict

**READY_FOR_PROTOCOL_APPROVAL.** M5.0 infrastructure is integrated and verified. The active development data are ready. The pilot is **PILOT_NOT_AUTHORIZED**: all 17 decisions remain unresolved, classical policy lacks evidence, and the M5.0 entrypoint cannot train. This verdict invites explicit protocol review; it grants no experimental approval.

No real GOES model training, scientific test windows/scoring, locked-test release, automatic download or confirmatory inference occurred. The separate Claude Code protocol review was not incorporated or represented as approval.

## Git and integration

The milestone branch is `feat/v2-m5-pilot-readiness`, based exactly on M4B `2e3f87111ab7c3a881064aaad9dbd6d6298c69cd`. GOES restoration `8a9c98db66eca545eeaf062f5fb07e47ec6bdc63` was normally merged as `c8da8d7ff0412584be1d2a5b648ea41140e923b4`; both descend from M4A `ac3428f910b36b7f10cc0fbb0740ce6de62df5a7`, and their post-M4A changed paths do not overlap. The verified implementation commit is `18b5528666e4d9112db816c852e74ce16829bbcf`. Later documentation commits record its evidence without changing executable source.

The branch was published and given upstream tracking before implementation. Only the milestone branch is committed/pushed. No PR or protected-branch integration is performed. The final Git HEAD and remote equality are reported in the completion response, avoiding a self-referential document-commit hash. [Protected-state evidence](evidence/v2_m5_0_protected_state.json) verifies local/live remote refs, all four manifest identities, all 92 ignore rules and 13 preserved historical report roots. Original worktree HEADs and unrelated untracked desktop work remain intact.

The 14-path GOES integration includes restoration, native validation, pinned plan, acquisition counters and tests. M3.1 experimental inference code was not merged; M4B already retains its no-replacement report and guards. M1 defaults are unchanged. The private shared GOES assembly extraction preserves V1 behavior. See [the verified integration plan](V2_M5_0_INTEGRATION_PLAN.md).

## Data readiness

**OBSERVED:** 92/92 required May–July files, 27,280,082 raw bytes, exact sizes/SHA-256 and 92 passing native identities. Measured coverage is `[2024-05-01T00:00:00Z,2024-08-01T00:00:00Z)`:132,480 one-minute bins, zero missing/duplicate/off-grid timestamps. Existing valid copies were reused by explicit pinned paths; no file was downloaded, deleted or overwritten. Raw data remain ignored and absent from Git.

**DOCUMENTED historical evidence:** 123 May–August files, 36,535,474 bytes and 177,120 observations were reported by restoration. M5.0 does not reopen August; its 31 files are outside the active selection, not missing required pilot inputs. August is development-exposed from V1 scoring and cannot be an untouched holdout. January 2025/sealed sources remain isolated.

The restricted loader verifies all metadata before native reads and repeats raw/pin/source attribution checks at completion. Product is GOES-16 `xrsf-l2-avg1m_science` version `2-2-1`; channels are XRS-A/XRS-B flux in W/m², ordered `xrsa_flux`,`xrsb_flux`. Cadence, native units/status/electron/count semantics and normalization are inherited. No new preprocessing/quality rule or embargo was introduced. Actual operational latency remains UNKNOWN. See [the loader audit](V2_M5_0_GOES_LOADER_AUDIT.md).

| Development role | Exact UTC half-open bounds | Retained / excluded stride 30 windows |
|---|---|---|
| train | May1 to July22,2024 | 3609 /327 |
| validation | July22 to August1,2024 | 412 /68 |

The raw training partition has 118,080 unique rows. Lazy V2 preparation finds 108,199 eligible complete stride 1 windows and describes the proposed deterministic 20,000-window subset. Validation context/target shapes are `[412,120,2]` and `[412,30,2]`. Normalization is fitted only on unique valid raw training cells; the native smoke succeeded with Torch unavailable. These checks produced no model outcome.

## Deterministic preflight

The normally installed CLI ran twice from outside the checkout with immutable publication to separate ignored execution directories. Both exited 3 and reported DATA_READY/PILOT_NOT_AUTHORIZED; canonical report bytes matched exactly. The records identify code commit/source, configuration, dataset, split, seeds, normalization, jobs, proposed resources and unresolved approvals. The CLI has no training, scoring, confirmatory or release mode. Missing/malformed approvals, stale fingerprints, unsupported selections and changed source attribution fail closed.

Canonical preflight SHA-256: `c858905ebdbff7122a84a3201cbb3db90cb022e13c13c37bd17e242887aa4487`.

| Identity | Fingerprint |
|---|---|
| Configuration | `2f095fbef7ae1e4de714110dd379a88fcc864f2caeb3eef4b1c295faf9a26b9c` |
| Dataset | `080d6128a398259e2112ce812b13d599b2131f9992bccced9720fe215e05cb72` |
| Aggregate development splits | `69fac8443c0740b7504acbca31720ec5c52cd39a678999e0024debf6344987a4` |
| Train window split | `e79a5074c3323f771a8cc40c3dde7a1c8f61747f5ed90f827c450fbb9b6f0c9d` |
| Validation window split | `707588906ec567b711d60f53fcd7ec81934755a3cb3df24d9df6837e67a68677` |
| Seed cohort | `5329a52b07e8211d7d9a8fbebdf98afd23caeb09306e70b6ee53d2086982785c` |
| Training support | `8e5f200f701c73d37191009d66246cd3bd50b5c3da7bb290d4fc28612fff38fb` |
| Normalization | `848623009ce048a14e32c50b7c70d9c9728cdd77391f10115ec1c8fd46d039a9` |

Reducing the dataset changes dataset/window split identities. Training support and normalization remain exactly equal to the historical full-dataset evidence because their fitting inputs are unchanged. The loader audit records this correction to historical prose without rewriting it.

The unapproved concrete plan contains 20 specified process jobs: 2 shared SSL phases, 10 primary controlled arms, 2 TCN jobs, 2 quantile-linear full paths and 4 separate loss-comparison jobs. Each linear path has 7 lambdas, giving 14 candidate fits. Historical proposal files are preserved unchanged; the amendment records the M4B per-seed requirement. Classical jobs remain unresolved and excluded from the count.

## Resource safeguards

The reusable supervisor executes only explicitly supplied shell-free argv jobs. It has no model/data policy or pilot launcher, and preflight never invokes it. It enforces per-attempt timeouts, cumulative active wall time including validation/sealing/bookkeeping, persistent conservative crash accounting, sampled worker-tree RSS, deterministic job ordering, native-library thread settings and at most one identical infrastructure retry. Ordinary/numerical exits are terminal. Logs/failures are retained; failed partials are quarantined; successful artifacts are sealed and hash-checked on resume. Changed identities, symlink storage, conflicting initializers and live/unknown orphan states fail closed.

Proposals remain 4 GiB RSS, 4 library threads, SSL 300 s, neural 600 s, TCN/linear 1800 s, 7200 s total and one infrastructure retry. Synthetic tests verify actual termination, failure classification, retry provenance, total overhead accounting, RSS descendants, artifact immutability, recovery and concurrent initialization.

Limits: macOS/Linux `ps` support is required; only macOS was executed here. Sampled RSS can miss brief peaks and is not a hard allocation cap. Environment settings do not enforce OS thread counts. Workers must not daemonize/leave their session; code/config identities are caller declarations. Unknown spawn state requires manual investigation before any separate recovery decision. No real model workload was used to validate resource scaling.

## Approvals and scientific restrictions

Every required decision and its policy/evidence/approver/fingerprint/dependency is in [the approval register](V2_M5_0_APPROVAL_REGISTER.md) and its machine record. Unresolved IDs: D09, D10, D11, DATA_ACCESS, AUGUST, QUALITY, SEEDS, BUDGETS, LOSSES, CHECKPOINT, TCN, LINEAR, CLASSICAL, FAILURE_RETRY, STATISTICS, TEST_PROHIBITION, REPRODUCIBILITY.

D09 verifies inherited touching boundaries but remains unapproved. D10 must reconcile the independent scientific protocol review, complete job policy and per-seed linear amendment. D11 must approve ceilings/operational limits. CLASSICAL is BLOCKED_ON_EVIDENCE pending fit-acceptance policy or explicit exclusion. No approval has been invented.

M3.1 remains NO_VALIDATED_REPLACEMENT. M4B restrictions remain DESCRIPTIVE_ONLY/INFERENCE_UNAVAILABLE: no validated confidence intervals, confirmatory p-values, significance/superiority claims or new acceptance thresholds. Quality acceptance of partial-count minutes is pending. May–August are exposed development data; no result can be promoted into independent confirmation.

## Verification and independent review

| Check actually executed | Result |
|---|---|
| Fresh unchanged M4B full baseline | 1583 passed, 1 warning, 120.77s |
| Independent new-test trio | 84 passed, 114.42s |
| Resource targeted suite | 40 passed, 4.61s |
| Final installed M5 full regression | 1705 passed, 1 warning, 304.22s |
| Native installed preflight twice | DATA_READY/PILOT_NOT_AUTHORIZED; both exit3; byte-identical |
| Native preprocessing with Torch unavailable | Passed; no model/optimizer |
| Normal installed imports/metadata CLI from /tmp | Passed; metadata-only NOT_CHECKED and blocked exit3 |
| Whitespace, manifest/history/index/ignore/ref checks | Passed |

The existing warning is a NumPy ndarray-size RuntimeWarning at the netCDF boundary. It was reported, not suppressed. The initial shared-environment baseline had 1581 passes/2 failures: an older installed distribution and a concurrent merge invalidated source identity. A separate venv and unchanged M4B rerun resolved both. An earlier M5 suite passed 1703 before final resource cases; an intermediate recheck was deliberately interrupted after the crash-recovery repair and superseded by the complete 1705 run. Tests were not weakened.

Fresh independent review covered provenance, scientific integrity, leakage/exposure, loader/authorization/resource safety, statistics, isolation, reproducibility and compatibility. Confirmed repairs: HIGH ambiguous spawn recovery; MEDIUM initializer races, raw attribution, and final code/config attribution; LOW malformed approval strictness. Final review reports no remaining BLOCKER/HIGH/MEDIUM. [Review evidence](evidence/v2_m5_0_independent_review.json) and [verification evidence](evidence/v2_m5_0_verification.json) record the exact results. The separate Claude protocol review is outside this implementation review.

## Recommendation and stopping point

Proceed to explicit experimental-protocol review and resolve all 17 registered decisions, including the classical scope, embargo, quality policy, per-seed baseline amendment and resource limitations. Before any real fitting, freeze reviewed code/config/data/split identities and explicitly authorize a separately reviewed pilot execution pathway that connects the existing model APIs and supervisor. M5.0 supplies a preflight-only boundary; changing an approval flag cannot make it train.

No real GOES training run has started. No sealed data or release is needed to complete M5.0. Keep reporting descriptive; statistical confirmation remains unavailable.

Machine evidence: [canonical native preflight](evidence/v2_m5_0_native_preflight.json), [verification](evidence/v2_m5_0_verification.json), [protected state](evidence/v2_m5_0_protected_state.json), [independent review](evidence/v2_m5_0_independent_review.json).
