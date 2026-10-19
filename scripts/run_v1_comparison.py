"""Run the v1 JEPA vs ARIMA/SARIMA vs ARCH/GARCH comparison and write figures.

Strict mode (default) requires clean tracked source and a normal installation,
like the P2 acceptance CLIs. `--dev` records the relaxed provenance explicitly
and is for iteration only; report numbers from strict runs.
"""
import argparse
from pathlib import Path

from solar_flare_jepa.experiments.v1 import run_v1
from solar_flare_jepa.experiments.v1_report import write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path, default=Path('configs/experiments/v1_goes_2024.json'))
    parser.add_argument('--models', type=Path, default=Path('configs/experiments/v1_models.json'))
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--dev', action='store_true', help='relaxed provenance for iteration only')
    parser.add_argument('--quick', action='store_true', help='one seed and reduced JEPA epochs')
    args = parser.parse_args()
    destination = run_v1(args.config, args.models, args.root, output_dir=args.output_dir,
                         dev=args.dev, quick=args.quick)
    write_report(destination)


if __name__ == '__main__':
    main()
