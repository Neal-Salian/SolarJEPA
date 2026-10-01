"""Register explicit local SoLEXS ZIPs, or verify an existing inventory; no extraction."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.data.storage import register_archives, repository_relative_path, verify_inventory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Repository root; paths in config are relative to it')
    parser.add_argument('--config', type=Path, default=Path('configs/data/solexs_storage.json'))
    parser.add_argument('--acquired-utc', help='Known original acquisition UTC timestamp; otherwise null')
    parser.add_argument('--verify', action='store_true', help='Read-only verification of every inventoried archive')
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.config if args.config.is_absolute() else root / args.config
    config = json.loads(config_path.read_text())
    inventory_path = root / repository_relative_path(config['inventory_path'], root)
    if args.verify:
        inventory = json.loads(inventory_path.read_text())
        verify_inventory(inventory, root)
    else:
        inventory = register_archives(root, config['archives'], inventory_path=inventory_path,
                                      acquired_utc=args.acquired_utc, source_url=config['source_url'],
                                      missing_dates=config.get('missing_dates'))
    print(json.dumps(dict(action='verified' if args.verify else 'registered', files=len(inventory['files']),
                          missing_dates=[r['nominal_observation_date'] for r in inventory['missing_coverage']],
                          inventory=repository_relative_path(inventory_path, root)), indent=2))
