"""Run bounded P2 TRAINING_INFRASTRUCTURE_SMOKE_TEST; never SolarJEPA training."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.training.runner import run_training_smoke


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path, help='Strict experiment JSON configuration')
    parser.add_argument('--root', required=True, type=Path, help='Clean Git repository/storage root')
    parser.add_argument('--output-dir', type=Path, help='New results/experiments/<execution> directory')
    parser.add_argument('--training-config', type=Path, help='Explicit bounds/hyperparameters (default: configs/training/p2_smoke.json)')
    parser.add_argument('--device', choices=('cpu', 'mps'), default='cpu', help='CPU default; MPS requires explicit capability')
    args = parser.parse_args()
    try:
        output = run_training_smoke(args.config, args.root, output_dir=args.output_dir,
                                   training_config_path=args.training_config, device=args.device)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(2, f'P2 training execution refused: {error}\n')
    result = json.loads((output / 'result.json').read_text())
    print(json.dumps({key: result[key] for key in ('output', 'status', 'model_id', 'execution_id')}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
