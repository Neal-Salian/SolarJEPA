"""Generate descriptive plots and diagnostics for the prepared NOAA sample."""
import argparse
import json
import os
from pathlib import Path
import pandas as pd
from solar_flare_jepa.data.goes import read_event_records
from solar_flare_jepa.data.eda import summarize, summarize_events, plot_reference
from solar_flare_jepa.data.inspect import write_json
from solar_flare_jepa.data.download import sha256_file, verified_manifest_paths
from solar_flare_jepa.data.storage import repository_relative_path

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    args = p.parse_args()
    config = json.loads(args.config.read_text())
    output = Path(config['results_dir'])
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(Path('.cache/matplotlib').resolve()))
    frame = pd.read_parquet(config['processed_path'])
    metadata = json.loads(Path(config['processed_path']).with_suffix('.metadata.json').read_text())
    if (metadata['config'] != config
            or metadata['manifest_sha256'] != sha256_file(Path(config['manifest']))
            or metadata['processed_sha256'] != sha256_file(Path(config['processed_path']))):
        raise ValueError('Stale or modified preparation output; rerun preprocess')
    flux_paths = verified_manifest_paths(Path(config['manifest']), Path.cwd(), 'avg1m')
    paths = verified_manifest_paths(Path(config['manifest']), Path.cwd(), 'flsum')
    events = read_event_records(paths)
    report = summarize(frame)
    report['catalogue'] = summarize_events(events)
    report['event_sources'] = [dict(path=repository_relative_path(s, Path.cwd()), sha256=sha256_file(s)) for s in paths]
    # Preserve historical sidecars while emitting current, portable source identities.
    report['preprocessing_metadata'] = dict(metadata, sources=[
        dict(path=repository_relative_path(s, Path.cwd()), sha256=sha256_file(s), bytes=s.stat().st_size)
        for s in flux_paths])
    write_json(output/'summary.json', report)
    plot_reference(frame, events, output)
    print(f'Wrote reference EDA to {output}')
