"""Verify offline dashboard sources without fitting, downloads, or test-array reads."""
import importlib.abc
import json
from pathlib import Path
import resource
import socket
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from solar_flare_jepa.dashboard import data


def main():
    registry=data.load_registry(ROOT)
    allowed=set()
    for relative in data.DATASETS:
        allowed.update((ROOT/row['path']).resolve() for row in data.read_json(ROOT/relative)['files'])
    opened=set()
    def audit(event,args):
        if event.startswith('socket.connect') or event=='socket.getaddrinfo':
            raise RuntimeError('Offline verification forbids network access')
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
            if 'test_predictions' in str(p) or p.is_relative_to(ROOT/'results'):
                raise RuntimeError('Experiment arrays are outside dashboard access')
            if p.suffix=='.nc':
                if p not in allowed: raise RuntimeError('Native file outside permitted May/June selection')
                opened.add(p)
    class NoTraining(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname.startswith(('torch','solar_flare_jepa.training','solar_flare_jepa.experiments.v1',
                                    'solar_flare_jepa.experiments.runner')):
                raise RuntimeError('Dashboard cannot import training or experiment execution')
    sys.addaudithook(audit); sys.meta_path.insert(0,NoTraining())
    import xarray as xr
    native_open=xr.open_dataset
    def open_dataset(path,*args,**kwargs):
        p=Path(path).resolve()
        if p not in allowed: raise RuntimeError('Unapproved native dataset')
        opened.add(p)
        return native_open(path,*args,**kwargs)
    xr.open_dataset=open_dataset
    start=time.perf_counter()
    for key in registry['visualizations']: data.verify_sources(ROOT,registry,key)
    frame=data.load_observations(ROOT,registry)
    summary=data.dataset_summary(frame)
    diagnostic=data.load_diagnostics(ROOT,registry)
    models=data.load_model_comparison(ROOT,registry)
    distribution=data.histogram(frame)
    render={}
    for ch in ('xrsa','xrsb'):
        reduced=data.envelope(frame[ch+'_flux'])
        assert len(reduced)<=2400
        assert reduced.max()==frame[ch+'_flux'].max()
        assert int(distribution[ch]['counts'].sum())==summary[ch+'_valid_rows']
        render[ch]={'drawn_points':len(reduced),'gap_markers':int(reduced.isna().sum()),
                    'peak_preserved':True,'histogram_total':int(distribution[ch]['counts'].sum())}
    assert opened==allowed and len(opened)==61
    result={'status':'PASS','native_files_verified':len(opened),'source_identities':len(registry['sources']),
        'summary':summary,'rendering':render,'diagnostic_rows':diagnostic['diagnostic_block']['rows'],
        'models':models.to_dict('records'),'elapsed_seconds':round(time.perf_counter()-start,3),
        'peak_process_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(2**20 if sys.platform=='darwin' else 1024),1),
        'frame_mib':round(frame.memory_usage(deep=True).sum()/2**20,2),
        'offline_sockets_blocked':True,'training_imports_blocked':True,
        'native_access_allowlist':'May/June 2024 only; no experiment arrays'}
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__': main()
