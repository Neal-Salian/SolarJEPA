# solar-flare-jepa

Research feasibility and data foundation for **Physics-Informed Joint-Embedding
Generative Forecasting of Solar Flare Dynamics Using Aditya-L1 Telemetry**.
The title is provisional: JEPA is a representation-learning method, not by
itself a generative trajectory model; physics and generation claims require
additional validated components.

**Status (2026-10-02): Phase C native scientific foundation verified. Both
SoLEXS L1 v1.1 samples (July 1 and 3, 2024) have complete FITS/integrity, structure,
native timing and quality inspection. Clock-card precedence, LC bins, GTI filtering
and compatible calibration remain scientific gates. July 2 is missing from the
obtained collection. These are validation samples, not a training dataset. No
models trained. NOAA GOES samples remain external reference data.** See the
[SoLEXS scientific findings](docs/SOLEXS_SCIENTIFIC_VALIDATION.md),
[canonical project tracker](docs/PROJECT_STATUS.md) for
current stages, blockers and next tasks, and the
[validation report](docs/VALIDATION_REPORT.md) for the historical foundation
checkpoint and measured sample sizes.

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
