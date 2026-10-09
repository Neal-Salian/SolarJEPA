"""Acquire or verify the pinned official NOAA 2025 science flare report."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.data.flare_catalog import acquire_catalog, verify_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path, default=Path('configs/data/flare_catalog_2025.json'))
    parser.add_argument('--manifest', type=Path, default=Path('data/manifests/flare_catalog_2025.json'))
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        paths = verify_catalog(args.manifest, args.root)
        print(json.dumps(dict(status='VERIFIED_RAW_IDENTITIES_AND_PARSE', resources={
            role: path.relative_to(args.root.resolve()).as_posix() for role, path in paths.items()}), indent=2))
    else:
        ledger = acquire_catalog(args.config, args.root)
        print(json.dumps({key: ledger[key] for key in ['catalog_id', 'status', 'event_count', 'total_bytes']}, indent=2))


if __name__ == '__main__':
    main()
