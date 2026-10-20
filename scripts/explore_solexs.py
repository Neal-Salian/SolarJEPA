"""Explore explicit real SoLEXS inputs offline in native instrument coordinates."""
import argparse
import json
from pathlib import Path
import uuid

from solar_flare_jepa.data.solexs_exploration import explore_solexs
from solar_flare_jepa.data.storage import repository_relative_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path, default=Path('configs/data/p2_solexs_exploration.json'))
    parser.add_argument('--output', type=Path, default=None,
                        help='New run directory under results/p2_solexs/; existing outputs are refused')
    parser.add_argument('--representation', default='native',
                        help='Only native is accepted; UTC/flux conversions remain scientifically gated')
    parser.add_argument('--train', action='store_true', help='Rejected while BLOCKED_FOR_PHASE_E')
    args = parser.parse_args()
    output = args.output or Path('results/p2_solexs') / uuid.uuid4().hex
    try:
        report = explore_solexs(args.config, args.root, output,
                               representation=args.representation, train=args.train)
    except (ValueError, FileExistsError, KeyError) as exc:
        parser.error(str(exc))
    relative = repository_relative_path(output, args.root)
    print(json.dumps(dict(report=f'{relative}/report.json', status=report['status'],
                          gate=report['gate']['status'], archives=len(report['archives']),
                          plots=len(report['plots']), training_executed=report['training']['executed'])))


if __name__ == '__main__':
    main()
