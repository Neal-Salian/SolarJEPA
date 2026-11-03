# V2 pilot — M4 host preparation (2026-10-19)

**Verdict: PREPARED, NOT AUTHORIZED.** All non-fitting gates pass on this MacBook (Apple M4, 16 GiB). The M4 reservation is
inactive and the pilot is not authorized for this changed execution environment. No model was fitted, no prediction made,
no test partition built, and no pilot output exists. This is a proposed replacement for the M2 environment, not a second pilot.

Machine record: [`evidence/phase2_v2_m4_host_preparation_20261019.json`](evidence/phase2_v2_m4_host_preparation_20261019.json).
Base: `codex/v2-experimental-validation-readiness` @ `1c5b699` (verified; contains checkpoint `8e9ce06`). Execution must run from that
branch at a clean tree: the validator hard-codes it. This record lives on a separate branch so the executing commit does not change.

## Host and environment (OBSERVED)

| | M4 (this host) | M2 reference |
|---|---|---|
| Model / chip | Mac16,12 / Apple M4 | Mac14,2 / Apple M2 |
| CPUs / RAM | 10 logical (4P+6E) / 16 GiB | 8 / 8 GiB |
| macOS / Python | 27.0.1 / 3.13.7 | 26.3 / 3.13.3 |
| Host fingerprint | `7911860b…eeb` | `58c5a228…e77dd` |
| Runtime fingerprint at `1c5b699` | `df978386…6b5` (recomputed twice, byte-identical) | `08e6f763…57ae4` |

Worktree `.venv` built offline from the repository locks. All 43 relevant installed packages equal the M2 versions. The 50 packages
absent are Jupyter/dev tooling and `psutil`, never imported by source or scripts. Torch 2.6.0, NumPy 2.2.6, NetCDF4 1.7.2. MPS exists
but is unused (CPU float32). The M2 binding was not reused: it is denied by the validator on this host.

## Verified readiness

- **Protocol:** design `ec104daa…`, 17 decisions, 20 jobs, configuration `a7ce7119…`, executable source `fbb17789…` all match the ratified values; 24 source pins match.
- **Data (92 May–July files, 27,280,082 B):** 92/92 native identities, 132,480 bins, 0 missing/duplicate; train/validation retain 3,609/412 and exclude 327/68; normalization from 118,080 unique training rows. All eight approval data-identity fields equal the M2 evidence. Native preflight took 9.7 s, 512 MB peak, Torch never imported.
- **Tests on this machine:** 301 (pilot, driver, worker, lifecycle, guards, descriptive, loader) + 357 (resource controls, GOES, contracts, provenance) passed. The full project suite was not run (it includes fitting).
- **Gate behaviour:** the pending file, a missing approval, the M2 runtime+host binding, and an M4 runtime with the M2 host are all denied. An in-memory dry run (never saved, not used to launch) shows the M4 binding is consistent once an owner supplies authority. The output directory remains absent. The CLI refuses without approval before scientific I/O.
- **Limits retained unchanged:** CPU float32, 4 threads, 2 GiB sampled RSS, 7,200 s total, zero retries/resume, ≥1 GiB free output (15 GiB free), attempt ceilings 300/600/1,800/600 s.

## Differences the owner must accept

macOS 27.0.1 and Python 3.13.7 (the lock was validated on 3.13.3), a different CPU. JEPA-family weights depend on thread count and CPU, so results are not expected to be bitwise equal to any M2 run. The strict NumPy-first NetCDF4 import exits 0 here, whereas M2 reproduced the warning; the cause is unknown and no suppression was added. The host was on battery (31%); the run needs AC power and an uninterrupted session.

## Runtime estimate (INFERRED, wide uncertainty)

From synthetic benchmarks on this Mac under macOS 26.3.1 plus measured real-data preparation: about **26 / 32 / 81 min** (optimistic / expected / conservative) against the 120-min budget; plausible 25–90 min. TCN is the largest cost (about 4–5 min per seed). Excluded or unmeasured: macOS 27 behaviour, reload parity, guarded publication and report overhead. No real-data fitting benchmark exists; completion of all 20 jobs is UNKNOWN. Any single failure leaves the pilot INCOMPLETE.

## Remaining blockers and next steps

1. Owner activates the M4 reservation (`SolarJEPA-G4-M4-20261019-01`) for one immediate window and accepts the differences above.
2. Owner separately authorizes one bounded 20-job pilot for this changed environment.
3. External files (outside Git) are prepared as PENDING: `owner-approval.pending.json`, `reservation.json`, `execution-binding.json`, `runtime-final.json`. After authority, change exactly the approval fields the validator documents, then re-verify the runtime on the final clean commit immediately before launching, with AC power connected.
