"""Synthetic NOAA CLI regression: portability must not change scientific values."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import xarray as xr

from test_cli import clean_environment
from test_goes import write_fixture


ROOT = Path(__file__).resolve().parents[1]


def synthetic_reference(tmp_path):
    root = tmp_path / 'original'
    raw = root / 'data/raw/noaa'
    raw.mkdir(parents=True)
    flux = raw / 'sci_xrsf-l2-avg1m_g16_d20240701_v2-2-1.nc'
    events = raw / 'sci_xrsf-l2-flsum_g16_d20240701_v2-2-1.nc'
    write_fixture(flux)
    ds = xr.Dataset({
        'time': ('record', np.array([0, 60, 180], dtype=float)),
        'status': ('record', ['EVENT_START', 'EVENT_PEAK', 'EVENT_END']),
        'flare_id': ('record', [11, 11, 11]),
        'flare_class': ('record', ['', 'M1.0', '']),
        'xrsb_flux': ('record', [1e-6, 1e-5, 5e-6]),
    })
    ds.time.attrs['units'] = 'seconds since 2000-01-01 12:00:00 UTC'
    ds.to_netcdf(events)
    entries = []
    for path, product in [(flux, 'avg1m'), (events, 'flsum')]:
        entries.append(dict(path=path.relative_to(root).as_posix(), bytes=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), max_bytes=1048576,
                            url=f'https://data.ngdc.noaa.gov/platforms/goes/l2/data/xrsf-l2-{product}_science/2024/07/{path.name}'))
    (root / 'manifest.json').write_text(json.dumps(dict(files=entries, max_total_bytes=2097152)))
    config = dict(manifest='manifest.json', processed_path='data/processed/reference.parquet',
                  results_dir='results/reference', quality_policy='strict_status_zero_and_channel_specific_electron_bits',
                  cadence_seconds=60, imputation='none', normalization='none')
    (root / 'config.json').write_text(json.dumps(config))
    return root, flux, events


def run_script(directory, script):
    result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts' / script), '--config', 'config.json'],
                            cwd=directory, env=clean_environment(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_preprocess_and_eda_metadata_survive_repository_relocation(tmp_path):
    root, flux, events = synthetic_reference(tmp_path)

    def prepare_and_report(directory):
        for script in ['preprocess.py', 'eda.py']:
            run_script(directory, script)
        sidecar = json.loads((directory / 'data/processed/reference.metadata.json').read_text())
        report = json.loads((directory / 'results/reference/summary.json').read_text())
        assert sidecar['sources'][0]['path'] == 'data/raw/noaa/' + flux.name
        assert report['event_sources'][0]['path'] == 'data/raw/noaa/' + events.name
        assert str(tmp_path) not in json.dumps([sidecar, report])
        return sidecar, report

    first_metadata = prepare_and_report(root)
    parquet = root / 'data/processed/reference.parquet'
    original_frame = pd.read_parquet(parquet)
    original_bytes = parquet.read_bytes()
    assert original_frame.xrsb_flux_raw.tolist() == [1e-6, 1e-5, -1, 1e-4]
    assert original_frame.xrsb_valid.tolist() == [True, False, False, True]
    moved = tmp_path / 'relocated'
    root.rename(moved)
    second_metadata = prepare_and_report(moved)
    pd.testing.assert_frame_equal(original_frame, pd.read_parquet(moved / 'data/processed/reference.parquet'))
    assert (moved / 'data/processed/reference.parquet').read_bytes() == original_bytes
    assert second_metadata == first_metadata


def test_eda_normalizes_historical_paths_without_overwriting_sidecar(tmp_path):
    root, flux, _ = synthetic_reference(tmp_path)
    run_script(root, 'preprocess.py')
    metadata_path = root / 'data/processed/reference.metadata.json'
    metadata = json.loads(metadata_path.read_text())
    metadata['sources'][0]['path'] = str(flux.resolve())
    metadata_path.write_text(json.dumps(metadata))
    before = metadata_path.read_bytes()
    scientific_bytes = (root / 'data/processed/reference.parquet').read_bytes()
    moved = tmp_path / 'relocated'
    root.rename(moved)
    run_script(moved, 'eda.py')
    report = json.loads((moved / 'results/reference/summary.json').read_text())
    assert report['preprocessing_metadata']['sources'][0]['path'] == 'data/raw/noaa/' + flux.name
    assert str(tmp_path) not in json.dumps(report)
    assert (moved / 'data/processed/reference.metadata.json').read_bytes() == before
    assert (moved / 'data/processed/reference.parquet').read_bytes() == scientific_bytes
