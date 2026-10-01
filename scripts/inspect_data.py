"""Inventory local NetCDF/FITS/CDF metadata without guessing calibration."""
import argparse
from pathlib import Path
from solar_flare_jepa.data.inspect import inspect_file, write_json

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('files', nargs='+', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    write_json(args.output, [inspect_file(path) for path in args.files])
