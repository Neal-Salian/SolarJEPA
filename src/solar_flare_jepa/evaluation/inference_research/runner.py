#!/usr/bin/env python3
"""Publish synthetic-only M3 inference evidence with complete source attestation."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import resource
import uuid

from .benchmark import run_benchmark, validate_config
from solar_flare_jepa.experiments.config import read_finite_json
from solar_flare_jepa.experiments.provenance import atomic_record, code_provenance, verify_artifacts, verify_source_identities
from solar_flare_jepa.forecasting.contracts import fingerprint_payload


def main(*,default_root:Path|None=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=default_root,required=default_root is None)
    parser.add_argument('--config',default='configs/validation/m3_development.json')
    parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    config=read_finite_json(root/args.config)
    if args.pilot:
        if config['stage']!='development': raise ValueError('Pilot cannot inspect frozen evaluation scenarios')
        config=config|dict(replications=5,bootstrap_replicates=99)
    config=validate_config(config)
    before=code_provenance(root);started=datetime.now(timezone.utc).isoformat()
    scientific,performance=run_benchmark(config,progress=lambda i,n,name:print(f'{i}/{n}: {name}',flush=True))
    verify_source_identities(root,before['source']['files'])
    after=code_provenance(root)
    if (before['git_commit']!=after['git_commit'] or before['git_branch']!=after['git_branch']
            or before['source']['fingerprint']!=after['source']['fingerprint']):
        raise ValueError('Git/source state changed during execution')
    identity=fingerprint_payload(dict(config=config,source=after['source']['fingerprint']))
    destination='results/experiments/m3-'+config['stage']+'-'+identity[:12]+'-'+uuid.uuid4().hex[:12]
    metadata=dict(schema_version=1,config=config,config_fingerprint=fingerprint_payload(config),
        scientific_payload_sha256=fingerprint_payload(scientific),provenance=after,
        dependencies={name:version(name) for name in ('numpy','scipy','pytest')},started_utc=started,
        peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,peak_rss_unit='bytes on macOS, KiB on Linux',
        tolerances=dict(reference_atol=1e-12,reference_rtol=1e-12,coverage_scaled_atol=1e-12))
    directory=atomic_record(root,destination,{'scientific.json':scientific,'metadata.json':metadata,'performance.json':performance})
    verify_artifacts(directory)
    print(f'Published: {destination}\nPayload SHA-256: {metadata["scientific_payload_sha256"]}\nRuntime: {performance["runtime_seconds"]:.3f} s')


if __name__=='__main__':main()
