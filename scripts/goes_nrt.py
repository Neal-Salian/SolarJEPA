"""Explicit NOAA snapshot intake, offline diagnostics and historical V1 replay.

No background refresh or model training. Fetch/assess success does not mean a
live forecast is eligible. Live inference is intentionally unavailable.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from solar_flare_jepa.data import goes_nrt as intake
from solar_flare_jepa.forecasting.nrt import forecast_snapshot, replay_v1, NrtForecastUnavailable


def _offline(event, arguments):
    if event.startswith('socket.connect') or event == 'socket.getaddrinfo':
        raise RuntimeError('Offline mode forbids network access')


def main(argv=None):
    """CLI entry; permanent network denial is installed only in its own process."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fetch = commands.add_parser('fetch', help='One explicit NOAA download and assessment; no inference')
    fetch.add_argument('--product', choices=tuple(intake.PRODUCTS), default='primary')
    for name in ('assess', 'forecast'):
        sub = commands.add_parser(name, help='Offline saved snapshot ' + name)
        sub.add_argument('--receipt', required=True, help='Receipt path relative to cache root')
        sub.add_argument('--now-utc', help='Explicit UTC assessment reference time for deterministic replay')
        sub.add_argument('--max-age-seconds', type=int, default=300)
        sub.add_argument('--cache-root', type=Path, default=ROOT/intake.DEFAULT_CACHE_ROOT)
    fetch.add_argument('--cache-root', type=Path, default=ROOT/intake.DEFAULT_CACHE_ROOT)
    replay = commands.add_parser('replay', help='Offline pinned GOES-16 science/checkpoint replay only')
    replay.add_argument('--root', type=Path, default=ROOT)
    replay.add_argument('--issue-utc', required=True, help='Historical August 2024 forecast origin, explicit UTC')
    replay.add_argument('--include-supervised', action='store_true')
    args = parser.parse_args(argv)
    offline = args.command != 'fetch'
    network_blocked = offline and __name__ == '__main__'
    if network_blocked:
        sys.addaudithook(_offline)
    try:
        if args.command == 'replay':
            report = replay_v1(args.root.resolve(), args.issue_utc, include_supervised=args.include_supervised)
            report['offline_network_blocked'] = network_blocked
        else:
            snapshot = (intake.fetch_snapshot(args.cache_root, product=args.product) if args.command == 'fetch'
                        else intake.load_snapshot(args.cache_root, args.receipt))
            now = getattr(args, 'now_utc', None) or datetime.now(timezone.utc).isoformat()
            assessment = intake.assess_snapshot(snapshot, now_utc=now,
                                                max_age_seconds=getattr(args, 'max_age_seconds', 300))
            report = dict(status='ACQUIRED' if args.command == 'fetch' else 'ASSESSED',
                          receipt_path=snapshot.provenance['receipt_path'], assessment=assessment,
                          offline_network_blocked=network_blocked)
            if args.command == 'forecast':
                try:
                    forecast_snapshot(snapshot)
                except NrtForecastUnavailable as exc:
                    report.update(status='FORECAST_UNAVAILABLE', error=str(exc))
                    print(json.dumps(report, indent=2, allow_nan=False))
                    return 2
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as exc:
        print(json.dumps(dict(status='FAIL', error=str(exc)), allow_nan=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
