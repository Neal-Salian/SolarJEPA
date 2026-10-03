# solar-flare-jepa

Research feasibility and data foundation for **Physics-Informed Joint-Embedding
Generative Forecasting of Solar Flare Dynamics Using Aditya-L1 Telemetry**.
The title is provisional: JEPA is a representation-learning method, not by
itself a generative trajectory model; physics and generation claims require
additional validated components.

**Status (2026-10-03): Phase D is merged into verified main `e1cfa85`.
Phase D.1 authoritative evidence/acquisition is on
`data/solexs-authoritative-evidence`. The original official Tools-1.1 bundle is
verified; its compatibility with pipeline-1.1 samples remains unresolved.
Historical acquisition remains BLOCKED by clock/bin/GTI/exposure policy and
approved correction/HK/response compatibility.** The July 1/3, 2024
L1 v1.1 products remain native validation samples; July 2 availability is UNKNOWN.
No final dataset or models exist. NOAA GOES remains external reference data.
See the [D.1 evidence checkpoint](docs/SOLEXS_PHASE_D1_REPORT.md),
[fourteen-resource audit](data/manifests/solexs_phase_d1_requirements.json),
[next authoritative clarification](docs/SOLEXS_PHASE_D1_AUTHORITY_REQUEST.md),
[historical Phase D gate report](docs/SOLEXS_PHASE_D_GATE_REPORT.md),
[Phase C findings](docs/SOLEXS_SCIENTIFIC_VALIDATION.md), and
[canonical project tracker](docs/PROJECT_STATUS.md).

The local editable installation's hidden `.pth` flag recurred between commands.
A normal package installation now passes import/CLI checks without `PYTHONPATH`;
the process reapplying the hidden flag remains unknown. See
[storage/provenance policy](docs/DATA_STORAGE.md) and
[foundation verification](docs/SOLEXS_FOUNDATION_VALIDATION.md).

## Research decisions

- Prioritize continuous SoLEXS signal forecasting and calibrated M+ warning.
- Test a small temporal JEPA against persistence, statistical, LSTM, TCN,
  supervised Transformer and linear baselines on identical time periods.
- Gate particle fusion, physical constraints, and LLM experiments on evidence.
- Separate ongoing-flare continuation from genuinely pre-onset warnings.
- Use chronological, purged partitions and event/block uncertainty estimates.
- Never equate SoLEXS counts or its 2–22 keV band with GOES flare-class flux.

Read [research design](docs/RESEARCH_PLAN.md), [experiments](docs/EXPERIMENT_PLAN.md),
[implementation plan](docs/IMPLEMENTATION_PLAN.md), [novelty](docs/NOVELTY.md),
[literature](docs/LITERATURE_NOTES.md), [dataset card](docs/DATASET_CARD.md),
[download instructions](docs/DATA_DOWNLOAD.md), and [paper plan](docs/PAPER_PLAN.md).

## Reproduce the foundation

The dependency ranges target Python 3.11+, while the recorded environment and
`requirements-lock.txt` were validated on Python 3.13.3/macOS arm64. Use that
Python version for the pinned reproduction below; other platforms remain
unverified. No GPU required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps .
python -m pytest
python scripts/download_data.py --manifest configs/data/noaa_sample.json
python scripts/inspect_data.py data/raw/noaa/*.nc --output results/schema.json
python scripts/preprocess.py --config configs/data/noaa_eda.json
python scripts/eda.py --config configs/data/noaa_eda.json
```

The downloader is an allowlisted public NOAA downloader, **not an authenticated
PRADAN client**. It enforces sample size limits, verifies pinned SHA-256 hashes,
refuses changed existing files, and records provenance. Run from repository root.
For manually acquired Aditya files, `inspect_data.py` inventories FITS/CDF
metadata without guessing units, calibration, quality definitions, or epochs.
An inventory is not a validated instrument parser.

Register and verify the explicitly configured local SoLEXS ZIPs without extraction:

```bash
python scripts/register_aditya.py --config configs/data/solexs_storage.json
python scripts/register_aditya.py --config configs/data/solexs_storage.json --verify
```

Original ZIPs live under
`data/raw/aditya/solexs/<level>/<version>/archives/<YYYY>/<MM>/`.
The current compressed member suffixes are `.gti.gz`, `.lc.gz`, and `.pi.gz`;
the existing FITS/CDF inspector does not automatically unpack or interpret them.
Use the separate UI-independent SoLEXS science layer for bounded native inspection:

```bash
python scripts/validate_solexs.py --config configs/data/solexs_storage.json
```

This offline CLI verifies registered bytes and every compressed scientific member,
stages one temporary FITS product at a time, and writes portable metadata under
ignored `results/solexs_science_validation/`. It applies no clock conversion,
GTI filtering or calibration. The [access contract](docs/SOLEXS_SCIENCE_CONTRACT.md)
describes readonly native LC/GTI copies and chunked PI access.
Phase D adds an offline diagnostic probe for explicitly pinned, unapproved
calibration candidates and exact native row comparisons:

```bash
mkdir -p results/solexs_timing_calibration
python scripts/probe_solexs_readiness.py \
  > results/solexs_timing_calibration/readiness_probe.json
```

Place the identity-matching candidate inputs at the ignored relative paths in the
[source manifest](data/manifests/solexs_phase_d_sources.json) first; the probe does
not download them. Equality or a valid FITS structure does not approve UTC, GTI,
correction or physical flux policies. The gate report explains the evidence and
unsupported interpretations. The shown output target is an ignored report;
never redirect output to source data.
D.1 pins the user-supplied official tools archive and its selected-member byte
equivalence in a separate [evidence manifest](data/manifests/solexs_phase_d1_evidence.json).
Read-only bundle verification is reproduced in the checkpoint report; no external
tools installation, HK substitution or timestamp/channel repair is performed.
After package-source edits, reinstall the package before checking installed CLIs;
pytest's source-path configuration alone does not establish installation success.

## Layout and scope

`src/solar_flare_jepa/data/` contains only acquisition, inspection, and reference
data preparation. `scripts/` contains command-line entry points; `configs/`
contains data and proposed experiment configurations. `data/manifests/` keeps
small provenance records. Raw/interim/processed data and generated `results/`
are ignored. Notebooks are reserved for exploration, never the sole pipeline.
Model/training/evaluation packages will be added only after design approval;
there are deliberately no misleading train/evaluate stubs.

MIT applies to original code and documentation. Mission data retain their own
terms. Milestone branches are published to origin. Main integration and the next
scientific milestone require the user's separate decision.
