"""Prepare strict-quality NOAA reference Parquet; no imputation or scaling."""
import argparse
import json
from pathlib import Path
from solar_flare_jepa.data.goes import read_goes
from solar_flare_jepa.data.inspect import write_json
from solar_flare_jepa.data.download import sha256_file, verified_manifest_paths

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True, type=Path)
    args = p.parse_args()
    config = json.loads(args.config.read_text())
    if (config['quality_policy'] != 'strict_status_zero_and_channel_specific_electron_bits'
            or config['cadence_seconds'] != 60 or config['imputation'] != 'none'
            or config['normalization'] != 'none'):
        raise ValueError('Unsupported preparation policy; review before extending')
    paths = verified_manifest_paths(Path(config['manifest']), Path.cwd(), 'avg1m')
    frame = read_goes(paths)
    out = Path(config['processed_path'])
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out)
    write_json(out.with_suffix('.metadata.json'), dict(config=config,
        role='external_reference_validation_not_aditya', rows=len(frame),
        manifest_sha256=sha256_file(Path(config['manifest'])),
        units={'flux':'W/m2', 'log10_flux':'log10(F / (1 W/m2))', 'dlog10_dt':'s^-1'},
        time_policy='GOES documented UTC convention neglecting leap seconds; index=bin start, available at time_end at earliest; operational latency unknown',
        sources=[dict(path=str(p), sha256=sha256_file(p), bytes=p.stat().st_size) for p in paths],
        processed_sha256=sha256_file(out)))
    print(f'Wrote {len(frame)} reference rows to {out}')
