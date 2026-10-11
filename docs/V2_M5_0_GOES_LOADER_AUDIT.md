# V2 M5.0 GOES Loader Audit

The dedicated loader verifies only the exposed May–July 2024 development selection. It preserves V1 scientific policies and constructs exactly the train and validation partitions. No test partition, August windows, external validation, model, optimizer or inference is invoked.

## Verified inputs

**OBSERVED:** all 92 pinned local files (27,280,082 bytes) were reused from the existing desktop checkout, copied by explicit manifest paths into the isolated M5 worktree without overwriting sources, and verified again. The M5 audit reads only those paths. Original archive and manifest bytes remain unchanged. Raw files remain ignored.

| Manifest | Files | Bytes | SHA-256 |
|---|---:|---:|---|
| `data/manifests/goes_v1_202405.json` | 31 | 9169020 | `9828b714ecb4545af2711f2760d110b9d0dd963a67e1f3d1d1f711af0aeb2240` |
| `data/manifests/goes_v1_202406.json` | 30 | 8910715 | `91e45449c61918c52786c4d4f45d4d9311ef313bbc8baace314a40bf135ecc79` |
| `data/manifests/goes_p2_july2024.json` | 31 | 9200347 | `581a3c4b8cfba6b9b21ed1fdb0b2277e728e9bf329a8da1ddcc0bd49c3cc4b3d` |

**OBSERVED:** 132,480 minute observations, zero missing bins, zero duplicate timestamps; coverage `[2024-05-01T00:00:00Z, 2024-08-01T00:00:00Z)`. All 92 native identities pass the restoration validator (g16, EXIS, Level 2, PT1M, product filename/version, nominal-day coverage, W/m² flux and documented UTC time units). Native provenance is retained in machine evidence. Native production dates are not acquisition times.

**DOCUMENTED:** restoration history reports 123 files/36,535,474 bytes/177,120 observations across May–August. M5.0 intentionally does not reread the 31 August files; that full-period observation count is historical evidence, not a fresh M5 measurement. August was scored in V1 and is development-exposed. The fourth tracked manifest is preserved but excluded by the M5 selection guard.

## Scientific contracts

Channels are ordered `xrsa_flux`, `xrsb_flux`, in W/m². Existing `validate_goes_files`, `read_goes`, restoration `native_identity`, `quality_summary`, and acquisition manifest/config/hash checks are reused. Bins are 60 seconds, UTC record start, half-open. Actual operational delivery latency remains **UNKNOWN**; only retrospective bin-end availability is supported. No resampling, interpolation, imputation, unit conversion or new flare labels are introduced.

Quality remains strict status zero, channel-specific electron-quality bits, finite positive flux inside native bounds, and positive native counts <=60. Channel A contamination does not automatically mask B. Valid partial-minute counts remain accepted; their proposed acceptance threshold requires QUALITY approval. Invalid cells retain false masks/NaNs. Current valid bins are A 128,098 / B 130,297.

| Role | UTC half-open support | Retained stride 30 origins | Excluded origins |
|---|---|---:|---:|
| train | `[2024-05-01T00:00:00Z, 2024-07-22T00:00:00Z)` | 3609 | 327 |
| validation | `[2024-07-22T00:00:00Z, 2024-08-01T00:00:00Z)` | 412 | 68 |

Full context/target support stays within its partition. Context 120 steps, horizon 30, stride 30, complete eligibility and log10(F/(1 W/m²)) match V1. D09 is pending: the touching partitions are observed inherited behavior, not approval of zero embargo.

## Preprocessing and identities

**OBSERVED:** Normalization fits unique valid raw training observations only (118,080 raw minute rows), not overlapping windows or validation data. The preprocessing provenance includes channel-specific counts, mean/scale, raw-support hash and full forecast definition. V2 lazy training-window preparation finds 108,199 complete stride 1 windows and a deterministic chronological subset of 20,000 under the unapproved budget; only normalized row arrays and start indices are constructed, avoiding an expanded stride 1 training tensor. Validation context/target array shapes are `[412,120,2]`/`[412,30,2]`.

The native smoke ran with `sys.modules["torch"] = None` and succeeded, which provides executable evidence that no Torch model/optimizer or real-data fitting was needed. Synthetic loader tests also forbid `_torch()` calls. Dataset preparation is permitted verification; these are no model outcomes.

| Identity | Observed fingerprint |
|---|---|
| dataset_fingerprint | `080d6128a398259e2112ce812b13d599b2131f9992bccced9720fe215e05cb72` |
| forecast_fingerprint | `094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94` |
| split_fingerprint | `69fac8443c0740b7504acbca31720ec5c52cd39a678999e0024debf6344987a4` |
| training_fingerprint | `8e5f200f701c73d37191009d66246cd3bd50b5c3da7bb290d4fc28612fff38fb` |
| normalization_fingerprint | `848623009ce048a14e32c50b7c70d9c9728cdd77391f10115ec1c8fd46d039a9` |
| train window split | `e79a5074c3323f771a8cc40c3dde7a1c8f61747f5ed90f827c450fbb9b6f0c9d` |
| validation window split | `707588906ec567b711d60f53fcd7ec81934755a3cb3df24d9df6837e67a68677` |

**OBSERVED discrepancy in historical prose:** `V2_GOES_SCIENTIFIC_VALIDATION.md` said a May–July-only dataset changes every identity. The executable contracts and this audit show that the dataset and window split hashes change, while training-support hash `8e5f200f…38fb` and normalization hash `84862300…39a9` remain equal to the historical evidence because fitting support is unchanged. The historical document is preserved, and this later correction is recorded here.

## Boundary verification

The loader rejects test/confirmatory/training modes, changed/extra/reordered manifests, August/January selections, wrong product/config pins, changed calendar/test roles, forecast/quality-policy changes and symlink redirection before scientific reads. Measured dataset/split expectations are compared after verified construction. The loader accepts no caller-supplied arbitrary dataset.

The generic V1 loader still requires a test split and reads every declared manifest. Its behavior is preserved. A shared private assembly helper avoids duplicating its identity construction; M5 constructs two explicit TemporalPartitions without inventing a pseudo-test. Stock restoration and validation CLI defaults still include August and restoration inventory scans the managed tree. They are excluded from the M5 command.

Remaining limitations: operational availability is unknown; partial-count quality threshold and temporal embargo remain unapproved; classical fit-acceptance policy is unavailable; no full-May–August data re-audit was performed; no statistical inference is validated. The loader cannot make the pilot authorized.
