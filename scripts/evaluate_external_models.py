"""Verify frozen external inputs; inference requires a recorded explicit approval.

Default preflight authenticates artifacts without constructing predictors.
--execute and --approval-reference record a caller's human-approval assertion;
this CLI does not authenticate human authorization. Never fits or acquires data.
"""
import argparse
from pathlib import Path

from solar_flare_jepa.experiments.external_evaluation import (
    preflight_external_evaluation, run_external_evaluation,
)
from solar_flare_jepa.forecasting.contracts import canonical_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--v1-dir', type=Path, required=True)
    parser.add_argument('--preparation-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='Fresh results/experiments directory')
    parser.add_argument('--execute', action='store_true', help='Execute only after explicit human approval')
    parser.add_argument('--approval-reference', help='Caller-supplied reference; not authenticated by code')
    args = parser.parse_args(argv)
    if args.execute and not (args.approval_reference and args.approval_reference.strip()):
        parser.error('--execute requires a nonempty --approval-reference')
    if args.approval_reference and not args.execute:
        parser.error('--approval-reference requires --execute')
    locators = dict(v1_dir=args.v1_dir, preparation_dir=args.preparation_dir, output_dir=args.output_dir)
    if args.execute:
        destination = run_external_evaluation(args.config, args.root, **locators,
                                             approval_reference=args.approval_reference)
        print(destination)
    else:
        print(canonical_json(preflight_external_evaluation(args.config, args.root, **locators)))


if __name__ == '__main__':
    main()
