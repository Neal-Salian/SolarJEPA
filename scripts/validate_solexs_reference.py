"""Replay pinned tools on artificial inputs and verify selected native witnesses."""
import argparse
from pathlib import Path

from solar_flare_jepa.data.solexs_reference import run_reference_validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--manifest', type=Path, default=Path('data/manifests/solexs_reference_cases.json'))
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='New directory beneath results/experiments')
    parser.add_argument('--chunk-rows', type=int, default=1024)
    args = parser.parse_args()
    path = run_reference_validation(args.manifest, project_root=args.project_root,
        data_root=args.data_root or args.project_root, output_dir=args.output_dir,
        chunk_rows=args.chunk_rows)
    print(path)


if __name__ == '__main__':
    main()
