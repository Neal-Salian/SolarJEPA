"""Offline bounded professor-requirements build; no download or neural training."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    from solar_flare_jepa.presentation.time_series import build_evidence
    report=build_evidence(args.root)
    print(json.dumps({'status':'PASS','dataset':report['dataset'],
                      'deployment':report['deployment'],'payload':report['payload']},indent=2))
