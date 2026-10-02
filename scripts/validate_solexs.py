"""Inspect explicit registered SoLEXS samples offline; retain native scientific values."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.data.inspect import write_json
from solar_flare_jepa.data.solexs import AccessLimits, inspect_solexs_archive
from solar_flare_jepa.data.storage import ROLE, load_inventory, repository_relative_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Storage/repository root; scientific paths must stay inside it')
    parser.add_argument('--config', type=Path, default=Path('configs/data/solexs_storage.json'))
    parser.add_argument('--output', type=Path, default=Path('results/solexs_science_validation/native_report.json'),
                        help='JSON report under results/; raw/inventory paths cannot be output targets')
    parser.add_argument('--chunk-rows', type=int, default=1024)
    parser.add_argument('--max-fits-bytes', type=int, default=512 * 1024**2)
    args = parser.parse_args()
    root = args.root.resolve()
    output = repository_relative_path(args.output, root)
    if not output.startswith('results/') or not output.endswith('.json'):
        parser.error('Output must be a JSON file under results/')
    if args.chunk_rows <= 0:
        parser.error('--chunk-rows must be a positive integer')
    limits = AccessLimits(max_fits_bytes=args.max_fits_bytes)
    config_path = args.config if args.config.is_absolute() else root / args.config
    config = json.loads(config_path.read_text())
    inventory = load_inventory(root / repository_relative_path(config['inventory_path'], root))
    requested = [repository_relative_path(p, root) for p in config['archives']]
    if not requested or len(set(requested)) != len(requested):
        parser.error('Config must select distinct explicit registered archives')
    records = {r['path']: r for r in inventory['files']}
    if not set(requested).issubset(records):
        parser.error('Config selects an archive absent from the registered inventory')
    report = dict(schema_version=1, dataset_role=ROLE,
                  representation='native_values_and_encoded_metadata',
                  policies=dict(utc_conversion='UNKNOWN_NOT_APPLIED', gti_filtering='UNKNOWN_NOT_APPLIED',
                                calibration='UNKNOWN_NOT_APPLIED', gap_filling='NOT_APPLIED'),
                  archives=[inspect_solexs_archive(root, records[p], limits=limits,
                                                  chunk_rows=args.chunk_rows) for p in sorted(requested)])
    # Build/verify every member before publishing a complete metadata-only report.
    write_json(root / output, report)
    print(json.dumps(dict(report=output, archives=len(report['archives']),
                          products=sum(len(a['products']) for a in report['archives']))))
