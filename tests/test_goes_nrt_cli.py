"""CLI modes keep acquisition success separate from inference eligibility."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys

import pytest

from solar_flare_jepa.data import goes_nrt as nrt
from test_goes_nrt import NOW, Response, payload, save

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/goes_nrt.py'


def cli():
    assert SCRIPT.exists(), 'Explicit NOAA CLI is missing'
    spec=spec_from_file_location('goes_nrt_cli',SCRIPT)
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_fetch_publishes_observations_without_claiming_forecast(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(nrt,'_transport',lambda url,timeout:Response(payload()))
    assert cli().main(['fetch','--cache-root',str(tmp_path)])==0
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='ACQUIRED'
    assert result['assessment']['model_input_ready'] is False
    assert (tmp_path/result['receipt_path']).is_file()
    assert result['assessment']['source']['publication_utc'] is None


def test_cli_offline_assessment_keeps_old_receipt_and_reports_staleness(tmp_path,capsys):
    saved=save(tmp_path)
    assert cli().main(['assess','--cache-root',str(tmp_path),'--receipt',saved.provenance['receipt_path'],
                       '--now-utc','2026-10-18T09:00Z'])==0
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='ASSESSED'
    assert result['assessment']['freshness']['stale']
    assert result['assessment']['source']['received_utc']=='2026-10-18T08:02:00+00:00'
    # A library call must not install irreversible process-global audit hooks.
    assert not result['offline_network_blocked']


def test_cli_forecast_reports_unavailable_with_no_fallback(tmp_path,capsys):
    saved=save(tmp_path)
    assert cli().main(['forecast','--cache-root',str(tmp_path),'--receipt',saved.provenance['receipt_path'],
                       '--now-utc',NOW])==2
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='FORECAST_UNAVAILABLE'
    assert result['assessment']['model_input_ready'] is False
    assert 'predictions' not in result


def test_cli_invalid_receipt_returns_json_failure(tmp_path,capsys):
    assert cli().main(['assess','--cache-root',str(tmp_path),'--receipt','receipts/absent.json'])==1
    assert json.loads(capsys.readouterr().out)['status']=='FAIL'


def test_cli_saved_science_replay_runs_from_another_directory_offline(tmp_path):
    assert SCRIPT.exists(), 'Explicit NOAA CLI is missing'
    if not (ROOT/'results/experiments/v1-full-20261009/jepa_finetune_seed17.pt').is_file():
        pytest.skip('Pinned ignored V1 artifacts required for integration replay')
    result=subprocess.run([sys.executable,str(SCRIPT),'replay','--root',str(ROOT),
                           '--issue-utc','2024-08-01T02:00Z'],cwd=tmp_path,
                          capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads(result.stdout)
    assert report['mode']=='historical_science_replay'
    assert report['offline_network_blocked']
    assert report['operationally_validated'] is False
    assert report['timing']['forecast_origin_utc']=='2024-08-01T02:00:00+00:00'
    assert len(report['predictions'][0]['values'])==30


def test_cli_missing_replay_artifacts_fails_without_network(tmp_path):
    assert SCRIPT.exists(), 'Explicit NOAA CLI is missing'
    result=subprocess.run([sys.executable,str(SCRIPT),'replay','--root',str(tmp_path),
                           '--issue-utc','2024-08-01T02:00Z'],cwd=tmp_path,
                          capture_output=True,text=True,timeout=30)
    assert result.returncode==1
    assert json.loads(result.stdout)['status']=='FAIL'
