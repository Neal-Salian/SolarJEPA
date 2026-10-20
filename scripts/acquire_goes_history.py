"""Acquire or verify an explicit bounded NOAA historical flux selection."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.data.goes_acquisition import acquire_history, verify_history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path, default=Path('configs/data/p2_goes_july2024.json'))
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--manifest', type=Path, default=Path('data/manifests/goes_p2_july2024.json'))
    args = parser.parse_args()
    if args.verify:
        paths = verify_history(args.manifest, args.root)
        print(json.dumps(dict(status='VERIFIED_RAW_IDENTITIES', file_count=len(paths),
                              paths=[p.relative_to(args.root.resolve()).as_posix() for p in paths]), indent=2))
    else:
        inventory = acquire_history(args.config, args.root)
        print(json.dumps(dict(status='ACQUIRED_RAW_IDENTITIES', complete=inventory['complete'],
                              file_count=len(inventory['files']), total_bytes=inventory['total_bytes'],
                              manifest=str(args.root.resolve() / json.loads(
                                  (args.config if args.config.is_absolute() else args.root / args.config).read_text())['manifest_path'])), indent=2))


if __name__ == '__main__':
    main()
