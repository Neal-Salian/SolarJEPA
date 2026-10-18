"""Retrospective inference boundaries; all artificial inputs stay in tests."""
from importlib import import_module, util
from pathlib import Path
import copy
import json

import numpy as np
import pandas as pd
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastPrediction, ForecastSpec, validate_alignment

ROOT = Path(__file__).resolve().parents[1]


def service():
    assert util.find_spec('solar_flare_jepa.dashboard.prediction') is not None, 'Prediction service is missing'
    return import_module('solar_flare_jepa.dashboard.prediction')


def spec():
    return ForecastSpec(**json.loads((ROOT/'configs/experiments/v1_goes_2024.json').read_text())['forecast'])


def frame():
    ix = pd.date_range('2024-08-01', periods=151, freq='min', tz='UTC')
    return pd.DataFrame({'xrsa_flux': np.arange(1,152)*1e-8, 'xrsb_flux': np.arange(1,152)*1e-6,
                         'observed': True, 'xrsa_valid': True, 'xrsb_valid': True}, index=ix)


def inputs(f=None, issue='2024-08-01T02:00Z'):
    return service().prepare_forecast(frame() if f is None else f, issue, spec())


def test_context_and_lead_one_use_completed_bins_without_time_shift():
    selected = inputs()
    assert selected.context.values.shape == (1,120,2)
    assert selected.context.mask.all()
    np.testing.assert_array_equal(selected.context.values[0,0], [1e-8,1e-6])
    np.testing.assert_allclose(selected.context.values[0,-1], [120e-8,120e-6])
    assert selected.context.starts_ns[0,0] == pd.Timestamp('2024-08-01T00:00Z').value
    assert selected.context.ends_ns[0,-1] == pd.Timestamp('2024-08-01T02:00Z').value
    assert selected.grid.starts_ns[0,0] == pd.Timestamp('2024-08-01T02:00Z').value
    assert selected.grid.ends_ns[0,0] == pd.Timestamp('2024-08-01T02:01Z').value
    assert selected.grid.ends_ns[0,-1] == pd.Timestamp('2024-08-01T02:30Z').value
    assert selected.context.spec.stride_steps == 30
    assert selected.context.spec.fingerprint == '094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94'
    assert selected.quality['context']['xrsa']['valid'] == 120
    assert selected.quality['future']['xrsa']['valid'] == 30


@pytest.mark.parametrize('issue', ['2024-08-01T01:59Z','2024-07-31T23:59Z','2024-08-31T23:31Z',
                                   '2024-09-01T00:00Z','2024-08-01T02:00:01Z','NaT',
                                   '2024-08-01T02:00','2024-08-01T02:00+01:00'])
def test_issue_time_rejects_partition_edges_subminute_and_non_utc(issue):
    with pytest.raises(ValueError): inputs(issue=issue)


def test_last_allowed_issue_and_additional_minute_origins():
    f = frame(); f.index = pd.date_range('2024-08-31T21:30Z', periods=151, freq='min')
    last = inputs(f, '2024-08-31T23:30Z')
    assert last.grid.ends_ns[0,-1] == pd.Timestamp('2024-09-01T00:00Z').value
    additional = inputs(frame(), '2024-08-01T02:01Z')
    assert additional.context.starts_ns[0,0] == pd.Timestamp('2024-08-01T00:01Z').value
    assert additional.grid.starts_ns[0,0] == pd.Timestamp('2024-08-01T02:01Z').value


@pytest.mark.parametrize('defect', ['mask','observed','zero','negative','nan','inf','missing','duplicate','offgrid'])
def test_incomplete_or_invalid_context_is_rejected_without_filling(defect):
    f = frame(); t=f.index[60]
    if defect=='mask': f.loc[t,'xrsa_valid']=False
    elif defect=='observed': f.loc[t,'observed']=False
    elif defect in ('zero','negative','nan','inf'):
        f.loc[t,'xrsa_flux']={'zero':0.,'negative':-1.,'nan':np.nan,'inf':np.inf}[defect]
    elif defect=='missing': f=f.drop(t)
    elif defect=='duplicate': f=pd.concat([f, f.loc[[t]]]).sort_index()
    else:
        ix=list(f.index); ix[60]=t+pd.Timedelta(seconds=1); f.index=pd.DatetimeIndex(ix)
    with pytest.raises(ValueError): inputs(f)


def test_future_is_optional_masked_and_cannot_change_context_or_grid():
    first=inputs(); f=frame(); f.loc[f.index[120]:,'xrsa_flux']=1e7
    f.loc[f.index[121],'xrsa_valid']=False
    f.loc[f.index[122],'xrsb_flux']=np.inf
    f=f.drop(f.index[123]); changed=inputs(f)
    np.testing.assert_array_equal(first.context.values, changed.context.values)
    np.testing.assert_array_equal(first.grid.starts_ns,changed.grid.starts_ns)
    assert np.isnan(changed.actual_future[1,0])
    assert np.isnan(changed.actual_future[2,1])
    assert np.isnan(changed.actual_future[3]).all()
    assert changed.quality['future']['xrsa'] == {'valid':28,'masked':2,'missing':1}
    absent=inputs(frame().iloc[:120])
    assert np.isnan(absent.actual_future).all()
    assert absent.quality['future']['xrsb']=={'valid':0,'masked':30,'missing':30}


def test_changed_spec_cannot_relax_full_valid_input_contract():
    altered=spec().as_dict(); altered['eligibility_policy']='masked'
    with pytest.raises(ValueError): service().prepare_forecast(frame(), '2024-08-01T02:00Z', ForecastSpec(**altered))


def test_registry_missing_corrupt_code_checkpoint_and_path_escape_fail_closed(tmp_path):
    p=service(); registry=p.load_prediction_registry(ROOT)
    with pytest.raises(ValueError): p.load_prediction_registry(tmp_path)
    manifest=tmp_path/p.REGISTRY_PATH; manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_bytes((ROOT/p.REGISTRY_PATH).read_bytes())
    for key in ('august_manifest','inference','jepa_checkpoint'):
        relative=registry['artifacts'][key]['path']; dest=tmp_path/relative
        dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text('corrupt')
        with pytest.raises(ValueError): p.verify_artifacts(tmp_path,registry, (key,))
    bad=copy.deepcopy(registry); bad['artifacts']['jepa_checkpoint']['path']='../outside.pt'
    with pytest.raises(ValueError): p.verify_artifacts(ROOT,bad,('jepa_checkpoint',))


def test_real_seed17_forecasts_preserve_future_causality_and_comparator_alignment(monkeypatch):
    p=service(); registry=p.load_prediction_registry(ROOT)
    f=p.load_august_observations(ROOT,registry)
    selected=p.prepare_forecast(f,'2024-08-01T02:00Z',spec())
    from solar_flare_jepa.training.jepa import TrainedJepa
    original=TrainedJepa.predict; calls=[]
    def predict(model, context, grid):
        calls.append((context,grid))
        return original(model,context,grid)
    monkeypatch.setattr(TrainedJepa,'predict',predict)
    result=p.predict_prepared(ROOT,registry,selected,include_supervised=True)
    np.testing.assert_allclose(result.jepa.values[0,0], [1.9218717283e-7,5.8635282473e-6],rtol=1e-6)
    np.testing.assert_allclose(result.jepa.values[0,-1], [1.8625988929e-7,5.1371215310e-6],rtol=1e-6)
    assert len(calls)==2 and all(context is selected.context and grid is selected.grid for context,grid in calls)
    validate_alignment(result.jepa.grid,result.supervised.grid)
    validate_alignment(result.jepa.grid,selected.grid)
    f.loc[f.index>=pd.Timestamp('2024-08-01T02:00Z'), ['xrsa_flux','xrsb_flux']]=np.nan
    changed=p.prepare_forecast(f,'2024-08-01T02:00Z',spec())
    second=p.predict_prepared(ROOT,registry,changed,include_supervised=False)
    np.testing.assert_array_equal(result.jepa.values,second.jepa.values)
    assert second.supervised is None
    assert np.isnan(second.inputs.actual_future).all()


def test_production_inference_is_offline_and_does_not_open_archive_or_unused_comparator(monkeypatch):
    import builtins,io,socket
    p=service()
    def guard(original):
        def checked(file,*args,**kwargs):
            if isinstance(file,(str,bytes,Path)):
                name=str(file)
                assert not any(item in name for item in ('test_predictions.npz','summary.json','supervised_seed17.pt')),name
            return original(file,*args,**kwargs)
        return checked
    monkeypatch.setattr(builtins,'open',guard(builtins.open))
    monkeypatch.setattr(io,'open',guard(io.open))
    def denied(*args,**kwargs):raise AssertionError('Network or fitting attempted')
    monkeypatch.setattr(socket.socket,'connect',denied)
    from solar_flare_jepa.training import jepa
    from solar_flare_jepa.data import goes_acquisition
    monkeypatch.setattr(jepa,'fit_forecaster',denied)
    monkeypatch.setattr(jepa,'pretrain_jepa',denied)
    monkeypatch.setattr(goes_acquisition,'acquire_history',denied)
    result=p.forecast(ROOT,'2024-08-01T02:00Z')
    assert result.jepa.values.shape==(1,30,2) and result.supervised is None


def test_normal_installed_service_accepts_pinned_identical_code_with_configurable_root(tmp_path):
    import subprocess,sys
    code=('from solar_flare_jepa.dashboard.prediction import forecast; '
          f'result=forecast({str(ROOT)!r},"2024-08-01T02:00Z"); '
          'assert result.jepa.values.shape==(1,30,2); print("PASS")')
    run=subprocess.run([sys.executable,'-I','-c',code],cwd=tmp_path,capture_output=True,text=True,timeout=90)
    assert run.returncode==0,run.stdout+run.stderr
    assert run.stdout.strip()=='PASS'


@pytest.mark.parametrize('other_loader',['prediction','legacy'])
def test_overlapping_reruns_serialize_complete_native_file_lifetimes(other_loader):
    # Native-library faults must be isolated from pytest's interpreter. This
    # previously exited139 with two threads in NetCDF open/close operations.
    import os,subprocess,sys
    code='''
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
from solar_flare_jepa.dashboard import prediction as p, data
root=Path.cwd();registry=p.load_prediction_registry(root)
legacy=data.load_registry(root);barrier=Barrier(2)
def read(worker):
    barrier.wait()
    for iteration in range(3):
        if worker==0 or OTHER=='prediction':
            frame=p.load_august_observations(root,registry)
            assert len(frame)==44640
        else:
            frame=data.load_observations(root,legacy)
            assert len(frame)==87840
    return len(frame)
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(read,range(2)))
assert results==([44640,44640] if OTHER=='prediction' else [44640,87840])
print('PASS')
'''.replace('OTHER',repr(other_loader))
    result=subprocess.run([sys.executable,'-X','faulthandler','-c',code],cwd=ROOT,
        capture_output=True,text=True,timeout=120,env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
    assert result.returncode==0,result.stdout+result.stderr
    assert result.stdout.strip()=='PASS'
