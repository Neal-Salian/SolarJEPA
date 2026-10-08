"""Run the explicit numerical SoLEXS pilot; never calibrated forecasting."""
import argparse
import json
from pathlib import Path

from solar_flare_jepa.provisional.experiment import run_experiment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/experiments/solexs_provisional_v1.json')
    parser.add_argument('--data-root',required=True,help='Workspace containing immutable registered ZIPs')
    parser.add_argument('--output-dir',required=True,help='New results/experiments/<identity> under code checkout')
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[1]
    config=Path(args.config)
    if not config.is_absolute():config=project/config
    report=run_experiment(config,project_root=project,data_root=args.data_root,output_dir=args.output_dir)
    print(json.dumps(dict(scientific_label=report['scientific_label'],stages=[report[k] for k in ('stage_a','stage_b','stage_c')],
                          output_dir=args.output_dir,selected_epoch=report['neural']['selected_epoch']),indent=2))


if __name__=='__main__':main()
