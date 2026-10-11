"""Integrity, scientific and pipeline validation of the restored GOES development data (read-only).

    python scripts/validate_goes_development.py --out docs/evidence/v2_goes_development_integrity.json
    python scripts/validate_goes_development.py --official-listing --out ...   # also query NOAA listings

Never downloads data, trains, or builds/scores test windows. Writes one compact
machine-readable report and refuses to overwrite an existing one.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from solar_flare_jepa.data import goes_acquisition as acquisition
from solar_flare_jepa.data.goes_development_validation import pipeline_smoke, validate_manifest_data
from solar_flare_jepa.data.goes_restoration import compare_official_listing, inventory, load_plan

DEFAULT_PLAN = Path('configs/data/v2_goes_development_restoration.json')
DEFAULT_EXPERIMENT = Path('configs/experiments/v1_goes_2024.json')


def _fetch(url):
    with acquisition.open_history_url(url, 30) as response:
        return response.read(4 * 1024 ** 2).decode('utf-8', 'replace')


def _code_identity(root):
    def git(*command):
        try:
            return subprocess.run(['git', *command], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    return dict(git_head=git('rev-parse', 'HEAD'),
                git_dirty=bool(git('status', '--porcelain', '--', 'src', 'scripts', 'configs', 'data/manifests')),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def _sum_quality(parts):
    total = dict(grid_bins=0, observed_bins=0, missing_bins=0)
    for key in total:
        total[key] = sum(p[key] for p in parts)
    for ch in ('xrsa', 'xrsb'):
        merged = {}
        for p in parts:
            for key, value in p[ch].items():
                if key in ('valid_bins', 'invalid_observed_bins', 'nonfinite_raw', 'nonpositive_raw', 'samples_full_60',
                           'samples_1_to_59', 'samples_zero_or_invalid', 'valid_samples_1_to_59',
                           'valid_samples_lt_30'):
                    merged[key] = merged.get(key, 0) + value
                elif key == 'status_flag_counts':
                    flags = merged.setdefault(key, {})
                    for flag, count in value.items():
                        flags[flag] = flags.get(flag, 0) + count
        merged['valid_fraction_of_grid'] = merged['valid_bins'] / total['grid_bins']
        total[ch] = merged
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--plan', type=Path, default=DEFAULT_PLAN)
    parser.add_argument('--experiment', type=Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument('--official-listing', action='store_true', help='compare with official NOAA listings (network)')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    if out.exists():
        parser.error(f'{out} exists; reports are never overwritten')
    began, timings = time.perf_counter(), {}
    plan = load_plan(args.plan, root)
    tick = time.perf_counter()
    files = inventory(plan, root)
    timings['inventory_hash_verification'] = time.perf_counter() - tick
    if files['counts']['present_verified'] != files['counts']['required']:
        print(json.dumps(files['counts']))
        return 2
    tick = time.perf_counter()
    manifests = [validate_manifest_data(plan, manifest, root) for manifest in plan['manifests']]
    timings['native_identity_and_time_series'] = time.perf_counter() - tick
    tick = time.perf_counter()
    smoke = pipeline_smoke(plan, args.experiment, root)
    timings['pipeline_smoke'] = time.perf_counter() - tick
    listing = compare_official_listing(plan, _fetch) if args.official_listing else None
    identities = {i['path']: i for m in manifests for i in m.pop('identities')}
    provenance = {}
    for identity in identities.values():
        for key, value in identity['provenance'].items():
            provenance.setdefault(key, set()).add(json.dumps(value))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = dict(
        kind='solarjepa_goes_development_integrity', schema_version=1,
        generated_utc=datetime.now(timezone.utc).isoformat(), code=_code_identity(root),
        evidence_scope='OBSERVED on the restoring host; read-only; no training; no test windows built or scored',
        plan=dict(plan_id=plan['plan_id'], path=plan['path'], sha256=plan['sha256'],
                  authorized_interval=[d.isoformat() for d in plan['interval']], manifests=plan['manifests']),
        inventory_counts=files['counts'], partial=files['partial'], unexpected=files['unexpected'],
        files=[dict(path=r['path'], nominal_date=r['nominal_date'], bytes=r['bytes'], sha256=r['sha256'],
                    status=r['status'], native_identity_passed=identities[r['path']]['passed'],
                    failed_native_checks=sorted(k for k, v in identities[r['path']]['checks'].items() if not v))
               for r in files['files']],
        native_provenance_values={k: [json.loads(v) for v in sorted(values)]
                                  for k, values in provenance.items() if k != 'date_created'},
        native_date_created_range=[min(json.loads(v) for v in provenance['date_created']),
                                   max(json.loads(v) for v in provenance['date_created'])],
        manifests=manifests, quality_total=_sum_quality([m['quality'] for m in manifests]),
        official_listing=listing, pipeline_smoke=smoke,
        experiment_config=dict(path=args.experiment.as_posix(), sha256=hashlib.sha256(
            (args.experiment if args.experiment.is_absolute() else root / args.experiment).read_bytes()).hexdigest()),
        resources=dict(wall_seconds=time.perf_counter() - began, phase_seconds=timings,
                       peak_rss_bytes=int(peak if sys.platform == 'darwin' else peak * 1024),
                       raw_bytes_on_disk=sum(r['bytes'] for r in files['files'])))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as stream:
        json.dump(report, stream, indent=1, sort_keys=True, default=str)
    native_ok = all(f['native_identity_passed'] for f in report['files'])
    print(json.dumps(dict(out=str(out), inventory=files['counts'], native_identity_all_passed=native_ok,
                          listing_consistent=None if listing is None else listing['consistent'],
                          wall_seconds=round(report['resources']['wall_seconds'], 1)), indent=1))
    return 0 if native_ok and (listing is None or listing['consistent']) else 3


if __name__ == '__main__':
    sys.exit(main())
