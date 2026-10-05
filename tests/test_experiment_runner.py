"""Exercise the complete pipeline and installed boundary in isolated Git roots."""
from copy import deepcopy
from dataclasses import replace
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest

from test_experiment_provenance import config as prototype

ROOT = Path(__file__).resolve().parents[1]


def runner():
    return importlib.import_module('solar_flare_jepa.experiments.runner')


def commit(root):
    for args in [('add','.'),('-c','user.name=P1 test fixture','-c','user.email=p1@example.invalid',
                              'commit','-qm','test fixture')]:
        subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)


def repository(tmp_path,cfg=None):
    root=tmp_path/'repository'
    root.mkdir()
    for directory in ('src','scripts','schemas'):
        shutil.copytree(ROOT/directory,root/directory)
    for file in ('pyproject.toml','requirements-lock.txt','.gitignore'):
        shutil.copyfile(ROOT/file,root/file)
    path=root/'configs'/'experiments'/'p1_test.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(cfg or prototype()))
    subprocess.run(['git','-C',str(root),'init','-q'],check=True,capture_output=True)
    commit(root)
    return root,path


def clean_environment():
    env=os.environ.copy()
    env.pop('PYTHONPATH',None)
    env['PYTHONDONTWRITEBYTECODE']='1'
    return env


def test_deterministic_semantic_reruns_have_distinct_execution_ids(tmp_path):
    module=runner()
    root,path=repository(tmp_path)
    a=module.run_experiment(path,root)
    b=module.run_experiment(path,root)
    first,second=[json.loads((p/'result.json').read_text()) for p in (a,b)]
    assert first['execution_id'] != second['execution_id']
    assert first['experiment_ids'] == second['experiment_ids']
    for file in ('predictions.json','metrics.json','model_parameters.json','split_manifest.json'):
        assert (a/file).read_bytes() == (b/file).read_bytes()
    assert first['role'] == 'foundation_smoke_not_scientific_skill'
    assert first['phase_e'] == 'BLOCKED_FOR_PHASE_E'
    assert first['status'] == 'complete'
    assert len(first['experiment_ids']) == 3
    assert first['deferred']['arch_garch'] == 'deferred_pending_residual_diagnostics'


def test_semantic_experiment_ids_and_models_record_effective_training_identity(tmp_path):
    from solar_flare_jepa.experiments.fixtures import synthetic_fixture
    from solar_flare_jepa.experiments.config import utc_ns
    from solar_flare_jepa.forecasting.contracts import ForecastSpec, fingerprint_payload
    from solar_flare_jepa.forecasting.splitting import TemporalPartition
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    cfg = prototype()
    root, path = repository(tmp_path, cfg)
    output = runner().run_experiment(path, root)
    result = json.loads((output / 'result.json').read_text())
    assert isinstance(result['fingerprints'].get('training'), str)
    boundary = cfg['splits'][0]
    train = build_partition_windows(synthetic_fixture(cfg), ForecastSpec(**cfg['forecast']),
        TemporalPartition('train', utc_ns(boundary['start_utc']), utc_ns(boundary['end_utc']))).training_slice
    assert result['fingerprints']['training'] == train.fingerprint
    for record in json.loads((output / 'model_parameters.json').read_text()):
        assert record['parameters']['training_fingerprint'] == train.fingerprint
    for experiment in result['experiment_ids']:
        payload = dict(**result['fingerprints'], seed=experiment['seed'])
        assert experiment['fingerprint'] == fingerprint_payload(payload)
        payload['training'] = 'changed-effective-training-data'
        assert experiment['fingerprint'] != fingerprint_payload(payload)


def test_full_window_fit_prediction_chain_is_invariant_to_huge_future_changes():
    module=runner()
    from solar_flare_jepa.experiments.fixtures import synthetic_fixture
    from solar_flare_jepa.experiments.config import utc_ns
    from solar_flare_jepa.forecasting.contracts import ForecastSpec
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    from solar_flare_jepa.forecasting.splitting import TemporalPartition
    from solar_flare_jepa.forecasting.baselines import make_baseline
    cfg=prototype()
    data=synthetic_fixture(cfg)
    spec=ForecastSpec(**cfg['forecast'])
    cut=utc_ns('2024-01-01T00:40:00Z')
    values,targets=np.array(data.features),np.array(data.targets)
    values[data.starts_ns >= cut] = 1e100
    targets[data.starts_ns >= cut] = -1e100
    changed=replace(data,features=values,targets=targets)
    partition=TemporalPartition('train',int(data.starts_ns[0]),cut)
    one,two=[build_partition_windows(d,spec,partition) for d in (data,changed)]
    for name,params in [('persistence',{}),('training_mean',{}),('trailing_mean',{'lookback_steps':2}),
                        ('drift',{'lookback_steps':2}),('ar1',{}),('direct_ridge',{'lag_steps':2,'alpha':.1})]:
        models=[make_baseline(name,params).fit(w.training_slice) for w in (one,two)]
        for key,value in models[0].parameters.items():
            if key not in ('dataset_fingerprint','split_fingerprint'):
                assert value == models[1].parameters[key]
        predictions=[m.predict(w.context,w.targets.grid).values for m,w in zip(models,(one,two))]
        np.testing.assert_array_equal(*predictions)
    assert one.context.origin_ids == two.context.origin_ids


def test_actual_drift_domain_failures_are_recorded_without_origin_dropping(tmp_path):
    module=runner()
    cfg=prototype()
    cfg['dataset']['rows']=800
    cfg['forecast'].update(horizon_steps=220,target_minimum=[0.,0.])
    cfg['splits']=[dict(name=name,start_utc=start,end_utc=end) for name,start,end in [
        ('train','2024-01-01T00:00:00Z','2024-01-01T03:50:00Z'),
        ('validation','2024-01-01T03:50:00Z','2024-01-01T08:20:00Z'),
        ('test','2024-01-01T08:20:00Z','2024-01-01T13:20:00Z')]]
    cfg['metrics']['lead_weights']=[1]*220
    cfg['baselines']=[dict(name='drift',parameters={'lookback_steps':2})]
    cfg['seeds']=[17]
    root,path=repository(tmp_path,cfg)
    out=module.run_experiment(path,root)
    result=json.loads((out/'result.json').read_text())
    failures=json.loads((out/'failures.json').read_text())
    assert result['status'] == 'complete_with_model_failures'
    assert failures and any('domain' in failure['reason'] for failure in failures)
    for failure in failures:
        assert failure['attempted_origin_ids']
        assert failure['common_target_valid_count'] > 0
    metric_records=json.loads((out/'metrics.json').read_text())
    failed=[item for item in metric_records if item['status']=='failed']
    assert failed and all(item['metrics'] is None and item['reason'] for item in failed)


def test_invalid_prediction_context_records_failures_without_scoring_future_values(tmp_path, monkeypatch):
    module = runner()
    cfg = prototype()
    cfg['baselines'] = [dict(name=name, parameters=params) for name, params in [
        ('persistence', {}), ('training_mean', {}),
        ('trailing_mean', {'lookback_steps': 2}), ('drift', {'lookback_steps': 2}),
        ('ar1', {}), ('direct_ridge', {'lag_steps': 2, 'alpha': .1})]]
    cfg['seeds'] = [17]
    root, path = repository(tmp_path, cfg)
    build = module.build_partition_windows

    def malformed_test_context(dataset, spec, partition):
        window = build(dataset, spec, partition)
        if partition.name == 'test':
            context = deepcopy(window.context)
            context.availability_ns[:, -1, :] = context.issue_times_ns[:, None] + 1
            context.values[:, -1, :] = window.targets.values[:, 0, :]
            return replace(window, context=context)
        return window

    monkeypatch.setattr(module, 'build_partition_windows', malformed_test_context)
    output = module.run_experiment(path, root)
    result = json.loads((output / 'result.json').read_text())
    failures = json.loads((output / 'failures.json').read_text())
    predictions = json.loads((output / 'predictions.json').read_text())
    metrics = json.loads((output / 'metrics.json').read_text())
    assert result['status'] == 'complete_with_model_failures'
    assert result['failure_count'] == 6
    assert len(failures) == 6 and {f['model'] for f in failures} == {b['name'] for b in cfg['baselines']}
    assert all(f['partition'] == 'test' and f['stage'] == 'predict' and
               f['error_type'] == 'ValueError' and f['attempted_origin_ids'] and
               f['common_target_valid_count'] > 0 and f['reason'] for f in failures)
    for record in predictions:
        if record['partition'] == 'test':
            assert record['status'] == 'failed' and record['values'] is None
    for record in metrics:
        if record['partition'] == 'test':
            assert record['status'] == 'failed' and record['metrics'] is None
    assert result['successful_model_partition_scores'] == 12


def test_runner_refuses_unsafe_output_and_dirty_or_mismatched_code(tmp_path):
    module=runner()
    root,path=repository(tmp_path)
    with pytest.raises(ValueError):
        module.run_experiment(path,root,output_dir=root/'data'/'raw'/'bad')
    source=root/'src'/'solar_flare_jepa'/'forecasting'/'contracts.py'
    source.write_text(source.read_text()+'\n# dirty source\n')
    with pytest.raises(ValueError,match='clean'):
        module.run_experiment(path,root)
    commit(root)
    with pytest.raises(ValueError,match='identity mismatch'):
        module.run_experiment(path,root)
    assert not list((root/'results'/'experiments').glob('*'))


def test_runner_rejects_scientifically_gated_dataset_mode(tmp_path):
    module=runner()
    cfg=prototype()
    cfg['dataset']={'kind':'solexs'}
    path=tmp_path/'blocked.json'
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='BLOCKED'):
        module.run_experiment(path,ROOT)


@pytest.mark.parametrize('mutation', ['new_source','tracked_edit','branch_switch'])
def test_execution_cannot_publish_stale_code_provenance(tmp_path, monkeypatch, mutation):
    module=runner()
    root,path=repository(tmp_path)
    original=module._dataset
    def changing_dataset(config, worktree):
        data=original(config,worktree)
        if mutation=='new_source':
            (root/'src/solar_flare_jepa/added_during_run.py').write_text('value = 1\n')
        elif mutation=='tracked_edit':
            (root/'.gitignore').write_text((root/'.gitignore').read_text()+'\n# changed during execution\n')
        else:
            subprocess.run(['git','-C',str(root),'checkout','-qb','switched-during-run'],
                           check=True,capture_output=True)
        return data
    monkeypatch.setattr(module,'_dataset',changing_dataset)
    with pytest.raises(ValueError, match='clean|changed during execution'):
        module.run_experiment(path,root)
    assert not list((root/'results/experiments').glob('*/result.json'))


def test_installed_cli_help_and_import_work_outside_checkout(tmp_path):
    result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/'run_experiment.py'),'--help'],
                          cwd=tmp_path,env=clean_environment(),capture_output=True,text=True)
    assert result.returncode == 0,result.stderr
    assert '--config' in result.stdout and '--root' in result.stdout
    result=subprocess.run([sys.executable,'-B','-c',
        'from solar_flare_jepa.experiments.runner import run_experiment; '
        'from solar_flare_jepa.evaluation import evaluate_events; '
        'from solar_flare_jepa.forecasting.baselines import Persistence'],
        cwd=tmp_path,env=clean_environment(),capture_output=True,text=True)
    assert result.returncode == 0,result.stderr


def test_installed_synthetic_run_does_not_require_optional_aditya_imports(tmp_path):
    module=runner()
    root,path=repository(tmp_path)
    program="""
import importlib.abc,sys
class NoAditya(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='astropy' or fullname.startswith('astropy.'):
            raise ImportError('optional Aditya dependency deliberately unavailable')
sys.meta_path.insert(0,NoAditya())
from solar_flare_jepa.experiments.runner import run_experiment
print(run_experiment(sys.argv[1],sys.argv[2]))
"""
    result=subprocess.run([sys.executable,'-B','-c',program,str(path),str(root)],
                          cwd=tmp_path,env=clean_environment(),capture_output=True,text=True)
    assert result.returncode == 0,result.stderr
    assert list((root/'results'/'experiments').glob('*/result.json'))
