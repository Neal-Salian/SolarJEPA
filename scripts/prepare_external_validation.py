"""Prepare pinned external observations and separate catalog labels; no model run."""
import argparse
import json
from pathlib import Path
from solar_flare_jepa.data.external_validation import prepare_external_validation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config',default='configs/evaluation/goes_external_january2025.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    try:
        summary=prepare_external_validation(args.config,args.root,args.output_dir)
    except (ValueError,OSError,KeyError) as exc:
        parser.exit(2,f'External preparation failed: {exc}\n')
    print(json.dumps(summary,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
