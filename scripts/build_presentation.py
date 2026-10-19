"""Rebuild GOES presentation assets from existing pinned V1 data; never download/train."""
import argparse
import json
import os
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    os.environ.setdefault('MPLCONFIGDIR', str(args.root.resolve() / '.cache/matplotlib'))
    from solar_flare_jepa.presentation.pipeline import build_presentation
    print(json.dumps(build_presentation(args.root), indent=2))
