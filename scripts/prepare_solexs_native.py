"""Offline native SoLEXS preparation audit; scientific JEPA/training stays blocked."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.data.solexs_integration import run_native_audit


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=project)
    parser.add_argument('--config', type=Path, default=Path('configs/data/solexs_integration.json'),
                        help='Pinned configuration relative to data root')
    parser.add_argument('--output-dir', required=True,
                        help='New directory directly beneath results/experiments/')
    args = parser.parse_args()
    destination = run_native_audit(args.config, project_root=project, data_root=args.data_root,
                                  output_dir=args.output_dir)
    print(json.dumps(dict(report=str(destination.relative_to(project)/'report.json'),
                         verdict='NATIVE_INTERFACE_READY_SCIENCE_BLOCKED', training_executed=False)))


if __name__ == '__main__':
    main()
