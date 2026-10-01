# solar-flare-jepa

Research feasibility and data foundation for **Physics-Informed Joint-Embedding
Generative Forecasting of Solar Flare Dynamics Using Aditya-L1 Telemetry**.
The title is provisional: JEPA is a representation-learning method, not by
itself a generative trajectory model; physics and generation claims require
additional validated components.

**Status (2026-10-01): investigation and small-data validation only. No models
trained. Aditya-L1 files require registered PRADAN access and have not been
obtained. NOAA GOES samples are external reference data, not substitute Aditya
telemetry.** See the [canonical project tracker](docs/PROJECT_STATUS.md) for
current stages, blockers and next tasks, and the
[validation report](docs/VALIDATION_REPORT.md) for the historical foundation
checkpoint and measured sample sizes.

The current audit found that normal package/CLI imports fail in the existing
local virtual environment while the 26 unit tests pass through pytest's `src`
path configuration. The tracker records the installation cause and reproduction
gate; no environment repair was performed during the documentation-only audit.

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
terms. An origin remote is configured; this session has not pushed or published.
