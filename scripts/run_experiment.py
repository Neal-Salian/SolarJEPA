"""Run a P1 synthetic or already pinned GOES foundation smoke (no acquisition)."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.experiments.runner import run_experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path, help='Strict P1 JSON configuration')
    parser.add_argument('--root', required=True, type=Path, help='Clean Git repository root')
    parser.add_argument('--output-dir', type=Path, help='New results/experiments/<execution> directory')
    args = parser.parse_args()
    try:
        output = run_experiment(args.config, args.root, output_dir=args.output_dir)
    except (ValueError, OSError) as error:
        parser.exit(2, f'P1 execution refused: {error}\n')
    result = json.loads((output/'result.json').read_text())
    print(json.dumps({k:result[k] for k in ('output','status','execution_id')}, sort_keys=True))
    return 0 if result['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
