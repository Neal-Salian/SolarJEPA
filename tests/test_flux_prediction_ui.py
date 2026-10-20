"""New renderer contracts and strict legacy-page access isolation."""
from importlib import import_module, util
from datetime import time
from pathlib import Path
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from test_flux_prediction import frame, inputs, ROOT
from solar_flare_jepa.forecasting.contracts import ForecastPrediction

APP=ROOT/'streamlit_app.py'


def chart_result():
    p=import_module('solar_flare_jepa.dashboard.prediction')
    f=frame(); f.loc[f.index[121],'xrsa_valid']=False
    selected=inputs(f)
    q=np.broadcast_to(np.array([1e-8,2e-8,3e-8,4e-8,5e-8]),(1,30,2,5)).copy()
    q[:,:,1,:]*=100
    prediction=ForecastPrediction(q[...,2],selected.grid,'jepa_finetune',(.05,.25,.5,.75,.95),q)
    comparator=ForecastPrediction(q[...,2]*2,selected.grid,'supervised_transformer',(.05,.25,.5,.75,.95),q*2)
    return p.PredictionResult(selected,prediction,comparator,{'seed':17})


def test_forecast_chart_has_native_channels_quantile_intervals_and_exact_time_boundaries():
    assert util.find_spec('solar_flare_jepa.dashboard.prediction_charts') is not None, 'Prediction charts missing'
    chart=import_module('solar_flare_jepa.dashboard.prediction_charts').prediction_figure(chart_result())
    assert chart.layout.yaxis.type==chart.layout.yaxis2.type=='log'
    assert 'W/m²' in chart.layout.yaxis.title.text
    assert 'UTC' in chart.layout.xaxis2.title.text
    assert '0.05–0.4 nm' in chart.layout.annotations[0].text
    assert '0.1–0.8 nm' in chart.layout.annotations[1].text
    traces={trace.name:trace for trace in chart.data}
    assert traces['XRS-A · context'].x[0]==pd.Timestamp('2024-08-01T00:00Z').to_pydatetime()
    assert traces['XRS-A · JEPA median'].x[0]==pd.Timestamp('2024-08-01T02:00Z').to_pydatetime()
    assert traces['XRS-A · JEPA median'].x[-1]==pd.Timestamp('2024-08-01T02:29Z').to_pydatetime()
    np.testing.assert_array_equal(traces['XRS-A · central 90%'].y,np.full(30,5e-8))
    np.testing.assert_array_equal(traces['XRS-A · central 50%'].y,np.full(30,4e-8))
    assert traces['XRS-A · central 90%'].fill=='tonexty'
    assert traces['XRS-A · central 50%'].fill=='tonexty'
    assert np.isnan(traces['XRS-A · actual future'].y[1])
    assert all(trace.connectgaps is False for trace in chart.data)
    assert 'XRS-A · supervised median' in traces
    boundaries={pd.Timestamp(shape.x0) for shape in chart.layout.shapes}
    assert boundaries=={pd.Timestamp('2024-08-01T00:00Z'),pd.Timestamp('2024-08-01T02:00Z'),pd.Timestamp('2024-08-01T02:30Z')}


def test_fifth_page_renders_forecast_and_controls_and_preserves_scope_labels():
    app=AppTest.from_file(str(APP),default_timeout=60).run()
    assert 'Solar Flux Prediction' in app.sidebar.radio[0].options, 'Fifth page route missing'
    assert any('Stable Baseline v0.1' in caption.value for caption in app.caption)
    app.sidebar.radio[0].set_value('Solar Flux Prediction').run()
    assert not app.exception and not app.error
    assert len(app.get('plotly_chart'))==1
    assert app.date_input[0].value.isoformat()=='2024-08-01'
    assert app.time_input[0].value.isoformat()=='02:00:00'
    captions=' '.join(x.value for x in app.caption)
    assert 'uncalibrated' in captions and 'latency' in captions and 'UTC' in captions
    assert '1,436' in captions and 'seed 17' in captions
    assert app.checkbox[0].value is False
    app.checkbox[0].check().run()
    assert not app.exception and not app.error and len(app.get('plotly_chart'))==1
    app.time_input[0].set_value(time(2,1)).run()
    assert not app.exception and not app.error
    app.time_input[0].set_value(time(1,59)).run()
    assert not app.exception and app.error and len(app.get('plotly_chart'))==0


def test_fifth_page_missing_artifacts_has_no_fallback(monkeypatch):
    assert util.find_spec('solar_flare_jepa.dashboard.prediction_page') is not None, 'Prediction page missing'
    p=import_module('solar_flare_jepa.dashboard.prediction')
    def unavailable(*args,**kwargs):
        raise ValueError('Pinned checkpoint is missing')
    monkeypatch.setattr(p,'forecast',unavailable)
    app=AppTest.from_file(str(APP),default_timeout=60).run()
    app.sidebar.radio[0].set_value('Solar Flux Prediction').run()
    assert not app.exception and len(app.get('plotly_chart'))==0
    assert any('unavailable' in msg.value.lower() for msg in app.error)
    assert any('Pinned checkpoint is missing' in msg.value for msg in app.caption)


def run_legacy_boundary():
    """Fresh process: full-suite training imports cannot weaken this assertion."""
    import builtins, importlib.abc, io, socket
    import streamlit as st
    import xarray as xr
    forbidden=('2024/08/','goes_v1_202408','test_predictions','results/experiments','.pt')
    class NoPrediction(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname.startswith(('torch','solar_flare_jepa.training','solar_flare_jepa.dashboard.prediction')):
                raise AssertionError('Legacy page attempted model import: '+fullname)
    sys.meta_path.insert(0,NoPrediction())
    def reject(*args,**kwargs): raise AssertionError('Network attempted')
    socket.socket.connect=reject
    opened=[]
    def guard(original):
        def checked(file,*args,**kwargs):
            if isinstance(file,(str,bytes,Path)):
                name=str(file)
                # The TS identity verifies tracked August metadata without opening August science products.
                metadata=Path(file).resolve()==ROOT/'data/manifests/goes_v1_202408.json'
                assert metadata or not any(x in name for x in forbidden),name
                opened.append(name)
            return original(file,*args,**kwargs)
        return checked
    builtins.open=guard(builtins.open); io.open=guard(io.open)
    native=[]; original=xr.open_dataset
    def open_dataset(path,*args,**kwargs):
        assert '/2024/05/' in str(path) or '/2024/06/' in str(path)
        native.append(str(path));return original(path,*args,**kwargs)
    xr.open_dataset=open_dataset
    st.cache_data.clear()
    app=AppTest.from_file(str(APP),default_timeout=60).run()
    assert not app.exception and not app.error and len(app.metric)==3
    assert app.metric[1].value=='87,840'
    for page,count in [('Overview',1),('Data Explorer',4),('Time-Series Analysis',2),('Model Results',2)]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception and not app.error,page
        assert len(app.get('plotly_chart'))==count,page
        if page=='Time-Series Analysis':
            before=app.dataframe[0].value.copy()
            app.selectbox[0].set_value('XRS-B').run()
            assert not app.dataframe[0].value.equals(before)
            app.selectbox[1].set_value('First log₁₀ difference').run()
            assert not app.error and not app.exception
            assert any('First log₁₀ difference' in str(node.value) for node in app.selectbox)
        if page=='Model Results': assert len(app.dataframe[0].value)==5
    assert len(set(native))==61
    assert not any(n.startswith(('torch','solar_flare_jepa.training','solar_flare_jepa.dashboard.prediction')) for n in sys.modules)
    print(json.dumps({'status':'PASS','native_files':len(set(native)),'charts':[1,4,2,2]}))


def test_all_legacy_pages_render_without_models_august_or_prediction_arrays():
    code="import sys; sys.path.insert(0,'tests'); from test_flux_prediction_ui import run_legacy_boundary; run_legacy_boundary()"
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,timeout=120,
                          env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
    assert result.returncode==0,result.stdout+result.stderr
    assert json.loads(result.stdout.splitlines()[-1])=={'status':'PASS','native_files':61,'charts':[1,4,2,2]}
