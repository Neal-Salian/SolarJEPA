"""Explicit offline replay against the immutable V1 seed17 prediction archive.

This CLI is the only new runtime that opens saved prediction arrays. It never
fits models, recomputes evaluation metrics, downloads data or writes artifacts.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

import numpy as np
import pandas as pd
from solar_flare_jepa.dashboard import prediction as p
from solar_flare_jepa.dashboard.data import _path, read_json
from solar_flare_jepa.forecasting.contracts import ForecastSpec

RTOL=1e-6
ATOL=1e-15  # W/m²: tiny absolute floor, well below the archived positive flux.


def verify_replay(root, issue_utc=None):
    registry=p.load_prediction_registry(root)
    p.verify_artifacts(root,registry,p.SOURCE_KEYS+('replay_archive','replay_summary',
                                                'jepa_checkpoint','supervised_checkpoint'))
    summary=read_json(_path(root,registry['artifacts']['replay_summary']['path']))
    spec=ForecastSpec(**registry['forecast_spec'])
    if (summary['dataset']['fingerprint']!=registry['dataset_fingerprint']
            or ForecastSpec(**summary['config']['forecast']).fingerprint!=spec.fingerprint
            or summary['provenance']['git_commit']!=registry['executed_commit']):
        raise ValueError('Saved experiment lineage differs from the approved contract')
    issue=p._issue_time(issue_utc or registry['default_issue_utc'])
    with np.load(_path(root,registry['artifacts']['replay_archive']['path']),allow_pickle=False) as archive:
        issues=archive['issue_times_ns']; ids=archive['origin_ids']
        partitions=[row for row in summary['split_manifest'] if row['partition']['name']=='test']
        if len(partitions)!=1: raise ValueError('Missing unique saved test partition')
        partition=partitions[0]
        if (len(ids)!=1436 or list(ids)!=partition['retained_origins']
                or len(issues)!=1436 or len(np.unique(issues))!=1436
                or not np.array_equal(ids,np.array(['origin:'+str(int(value)) for value in issues]))):
            raise ValueError('Saved benchmark origin identities differ')
        match=np.flatnonzero(issues==issue.value)
        if len(match)!=1:
            raise ValueError('Issue time is not an exact saved benchmark origin; no neighboring-origin substitution')
        index=int(match[0]); origin=str(ids[index])
        supports=[row for row in partition['support_manifest'] if row['origin_id']==origin]
        if len(supports)!=1: raise ValueError('Missing unique saved temporal support')
        support=supports[0]
        observations=p.load_august_observations(root,registry)
        selected=p.prepare_forecast(observations,issue,spec)
        # Independent raw data are checked before comparing model predictions.
        np.testing.assert_array_equal(selected.context.values[0],archive['context'][index])
        np.testing.assert_array_equal(selected.context.mask[0],archive['context_mask'][index])
        np.testing.assert_array_equal(selected.context.starts_ns[0],np.arange(
            support['context_start_ns'],support['context_end_ns'],p.MINUTE_NS,dtype=np.int64))
        np.testing.assert_array_equal(selected.grid.starts_ns[0],np.arange(
            support['target_start_ns'],support['target_end_ns'],p.MINUTE_NS,dtype=np.int64))
        if (int(issues[index])!=int(selected.grid.issue_times_ns[0])
                or selected.grid.ends_ns[0,-1]!=support['target_end_ns']):
            raise ValueError('Saved forecast issue or end boundary differs')
        np.testing.assert_array_equal(np.isfinite(selected.actual_future),archive['target_mask'][index])
        np.testing.assert_allclose(selected.actual_future,archive['targets'][index],rtol=0,atol=0,equal_nan=True)
        result=p.predict_prepared(root,registry,selected,include_supervised=True)
        models={}
        for output,saved_name in ((result.jepa,'jepa_finetune_seed17'),(result.supervised,'supervised_seed17')):
            model_matches=np.flatnonzero(archive['model_ids']==saved_name)
            if len(model_matches)!=1: raise ValueError('Missing unique saved seed17 model identity')
            model_index=int(model_matches[0])
            point=archive['point_'+str(model_index)][index:index+1]
            quantiles=archive['quantiles_'+str(model_index)][index:index+1]
            np.testing.assert_allclose(output.values,point,rtol=RTOL,atol=ATOL)
            np.testing.assert_allclose(output.quantiles,quantiles,rtol=RTOL,atol=ATOL)
            models[output.model_id]={'saved_model_id':saved_name,'point_match':True,'quantiles_match':True,
                'max_point_relative_difference':float(np.max(np.abs(output.values-point)/np.abs(point))),
                'max_quantile_relative_difference':float(np.max(np.abs(output.quantiles-quantiles)/np.abs(quantiles)))}
    return {'status':'PASS','issue_utc':issue.isoformat(),'origin_id':origin,'seed':17,
            'saved_origin_count':1436,'context_exact':True,'context_mask_exact':True,
            'future_grid_exact':True,'actual_future_exact':True,'models':models,'rtol':RTOL,'atol':ATOL,
            'tolerance_reason':'Single-origin float32 shape differs from original batch; rtol1e-6, tiny1e-15 W/m² floor.',
            'offline_network_blocked':True,'experiment_id':registry['experiment_id'],
            'spec_fingerprint':spec.fingerprint,'normalization_fingerprint':registry['normalization_fingerprint']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT,help='Repository/storage root; sources must import from this root')
    parser.add_argument('--issue-utc',help='Exact saved August benchmark UTC origin; default first origin, independent of performance')
    args=parser.parse_args()
    def offline(event,arguments):
        if event.startswith('socket.connect') or event=='socket.getaddrinfo':
            raise RuntimeError('Replay forbids network access')
    sys.addaudithook(offline)
    try:
        report=verify_replay(args.root.resolve(),args.issue_utc)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,ImportError,AssertionError) as exc:
        print(json.dumps({'status':'FAIL','error':str(exc)},allow_nan=False))
        return 1
    print(json.dumps(report,indent=2,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
