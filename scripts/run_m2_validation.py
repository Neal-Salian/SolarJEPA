#!/usr/bin/env python3
"""Run bounded synthetic M2 evidence; never discovers scientific datasets."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import resource
import time
import uuid

from solar_flare_jepa.evaluation.stress.runner import scientific_payload, validate_config
from solar_flare_jepa.experiments.config import read_finite_json
from solar_flare_jepa.experiments.provenance import (
    atomic_record, code_provenance, verify_artifacts, verify_source_identities,
)
from solar_flare_jepa.forecasting.contracts import fingerprint_payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', default='configs/validation/m2_synthetic.json')
    parser.add_argument('--pilot', action='store_true', help='5 datasets/case, 99 draws, 1000 calibration origins')
    args = parser.parse_args()
    root = args.root.resolve()
    config = read_finite_json(root/args.config)
    if args.pilot:
        config = dict(config, replications=5, bootstrap_replicates=99, calibration_origins=1000)
    config = validate_config(config)
    provenance = code_provenance(root)  # clean tracked source, normal installed match
    started_utc = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    scientific = scientific_payload(config, progress=lambda i, n, name, block:
        print(f'{i}/{n}: {name}, block={block}', flush=True))
    elapsed = time.monotonic()-start
    verify_source_identities(root, provenance['source']['files'])
    payload_hash = fingerprint_payload(scientific)
    identity = fingerprint_payload(dict(config=config, source=provenance['source']['fingerprint']))
    destination = 'results/experiments/m2-'+identity[:12]+'-'+uuid.uuid4().hex[:12]
    metadata = dict(schema_version=1, config=config, config_fingerprint=fingerprint_payload(config),
                    scientific_payload_sha256=payload_hash, provenance=provenance,
                    dependencies={name: version(name) for name in ('numpy', 'pytest', 'scipy')},
                    started_utc=started_utc, runtime_seconds=elapsed,
                    peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    peak_rss_unit='bytes on macOS, KiB on Linux',
                    tolerances=dict(reference_atol=1e-12, reference_rtol=1e-12,
                                    calibration_scaled_arithmetic=1e-12, calibration_probability_binomial_se=5))
    directory = atomic_record(root, destination, {'scientific.json': scientific, 'metadata.json': metadata})
    verify_artifacts(directory)
    print(f'Published: {destination}\nPayload SHA-256: {payload_hash}\nRuntime: {elapsed:.3f} s')


if __name__ == '__main__':
    main()
