"""Inventory (default, read-only) or restore the authorized GOES development data.

    python scripts/restore_goes_development.py                    # read-only inventory
    python scripts/restore_goes_development.py --restore          # download only missing pinned files

Writes a machine-readable report (never overwriting one). Raw data stay under
the ignored ``data/raw`` tree; only pinned manifest identities are requested.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import sys
import time

from solar_flare_jepa.data.goes_restoration import inventory, load_plan, restore

DEFAULT_PLAN = Path('configs/data/v2_goes_development_restoration.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--plan', type=Path, default=DEFAULT_PLAN)
    parser.add_argument('--restore', action='store_true', help='download missing authorized files')
    parser.add_argument('--out', type=Path, help='report path (default under ignored results/)')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    began, started = time.perf_counter(), datetime.now(timezone.utc)
    plan = load_plan(args.plan, root)
    result = restore(plan, root) if args.restore else dict(before=inventory(plan, root), after=None, stats=None)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = dict(kind='solarjepa_goes_development_restoration', schema_version=1,
                  mode='restore' if args.restore else 'inventory', started_utc=started.isoformat(),
                  plan=dict(plan_id=plan['plan_id'], path=plan['path'], sha256=plan['sha256'],
                            interval=[d.isoformat() for d in plan['interval']], manifests=plan['manifests']),
                  required_files=len(plan['files']), required_bytes=plan['required_bytes'],
                  wall_seconds=time.perf_counter() - began,
                  peak_rss_bytes=int(peak if sys.platform == 'darwin' else peak * 1024), **result)
    out = args.out or root / 'results' / 'v2_goes_restoration' / f"{report['mode']}-{started:%Y%m%dT%H%M%SZ}.json"
    out = out if out.is_absolute() else root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as stream:
        json.dump(report, stream, indent=1, sort_keys=True)
    final = result['after'] or result['before']
    print(json.dumps(dict(out=str(out), mode=report['mode'], counts=final['counts'], stats=result['stats']),
                     indent=1))
    return 0 if final['counts']['present_verified'] == final['counts']['required'] else 2


if __name__ == '__main__':
    sys.exit(main())
