"""Installed-package P2 historical data preparation."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.data.foundation import prepare_foundation


def main():
    parser = argparse.ArgumentParser(description='Validate pinned GOES and prepare leakage-safe P1 splits')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', default='configs/experiments/p2_goes_july2024.json')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        summary = prepare_foundation(args.config, args.root, args.output_dir)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'GOES preparation failed: {exc}\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
