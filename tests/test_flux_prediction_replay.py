"""The explicit offline archive verifier proves independent raw-context replay."""
from importlib import util
from pathlib import Path
import json
import os
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/verify_flux_prediction.py'


def test_explicit_offline_replay_matches_raw_context_and_both_saved_models():
    assert SCRIPT.exists(), 'Explicit offline prediction replay verifier missing'
    result=subprocess.run([sys.executable,str(SCRIPT),'--root',str(ROOT)],cwd=ROOT.parent,
                          env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads(result.stdout)
    assert report['status']=='PASS'
    assert report['issue_utc']=='2024-08-01T02:00:00+00:00'
    assert report['context_exact'] and report['context_mask_exact']
    assert report['future_grid_exact'] and report['offline_network_blocked']
    assert report['saved_origin_count']==1436 and report['seed']==17
    assert set(report['models'])=={'jepa_finetune','supervised_transformer'}
    assert report['rtol']==1e-6 and report['atol']==1e-15
    for model in report['models'].values():
        assert model['point_match'] and model['quantiles_match']


def test_replay_refuses_nonbenchmark_origin_instead_of_selecting_neighbor():
    assert SCRIPT.exists(), 'Explicit offline prediction replay verifier missing'
    result=subprocess.run([sys.executable,str(SCRIPT),'--root',str(ROOT),'--issue-utc','2024-08-01T02:01Z'],
                          capture_output=True,text=True,timeout=90)
    assert result.returncode != 0
    report=json.loads(result.stdout)
    assert report['status']=='FAIL' and 'saved benchmark origin' in report['error']
