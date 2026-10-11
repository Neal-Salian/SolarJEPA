"""Read-only M5.0 plan/data verification; cannot fit or release test data."""
import argparse
from pathlib import Path

from solar_flare_jepa.experiments.provenance import atomic_record
from solar_flare_jepa.experiments.v2_m5_preflight import preflight
from solar_flare_jepa.forecasting.contracts import canonical_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--metadata-only', action='store_true', help='Skip raw data; readiness remains NOT_CHECKED')
    parser.add_argument('--output', help='New immutable directory under results/experiments')
    args = parser.parse_args()
    result = preflight(args.root, verify_data=not args.metadata_only)
    if args.output:
        atomic_record(args.root, args.output, {'preflight.json': result})
    print(canonical_json(result))
    # A blocked pilot is deliberately a nonzero shell result, even with ready data.
    return 3


if __name__ == '__main__':
    raise SystemExit(main())
