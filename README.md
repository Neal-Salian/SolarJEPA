# solar-flare-jepa

Research feasibility and data foundation for **Physics-Informed Joint-Embedding
Generative Forecasting of Solar Flare Dynamics Using Aditya-L1 Telemetry**.
The title is provisional: JEPA is a representation-learning method, not by
itself a generative trajectory model; physics and generation claims require
additional validated components.

**Status (2026-09-29): investigation and small-data validation only. No models
trained. Aditya-L1 files require registered PRADAN access and have not been
obtained. NOAA GOES samples are external reference data, not substitute Aditya
telemetry.** See [validation report](docs/VALIDATION_REPORT.md) for measured
sample sizes, evidence, and remaining blockers.

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

Python 3.11+; the recorded environment is in `requirements-lock.txt` (Python
version and validation commands in the report). No GPU required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
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

## Layout and scope

`src/solar_flare_jepa/data/` contains only acquisition, inspection, and reference
data preparation. `scripts/` contains command-line entry points; `configs/`
contains data and proposed experiment configurations. `data/manifests/` keeps
small provenance records. Raw/interim/processed data and generated `results/`
are ignored. Notebooks are reserved for exploration, never the sole pipeline.
Model/training/evaluation packages will be added only after design approval;
there are deliberately no misleading train/evaluate stubs.

MIT applies to original code and documentation. Mission data retain their own
terms. No remote repository or public release has been created.
