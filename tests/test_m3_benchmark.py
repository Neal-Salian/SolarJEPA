"""Known truths, frozen designs and independent benchmark bookkeeping."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from solar_flare_jepa.evaluation.inference_research.benchmark import run_benchmark, validate_config, null_status, gate_eligible, adversarial_checks
from solar_flare_jepa.evaluation.inference_research.synthetic import generate_case
from solar_flare_jepa.forecasting.contracts import fingerprint_payload


ROOT=Path(__file__).resolve().parents[1]


def tiny_config():
    config=json.loads((ROOT/'configs/validation/m3_development.json').read_text())
    config.update(replications=2,bootstrap_replicates=99)
    config['cases']=config['cases'][:2]
    return config


def test_benchmark_is_deterministic_and_keeps_timing_separate():
    config=tiny_config()
    a,pa=run_benchmark(config); b,pb=run_benchmark(config)
    assert a==b and fingerprint_payload(a)==fingerprint_payload(b)
    assert 'runtime_seconds' not in a and 'method_seconds' not in a
    assert all('method_seconds' not in case for case in a['cases'])
    assert pa['method_seconds'] and pb['method_seconds']
    for case in a['cases']:
        assert case['methods']['m1_joint']['estimand']=='joint'
        assert case['methods']['seed_t']['estimand']=='seed_conditional'
        assert case['methods']['seed_t']['zero_null_type1'] is None
        assert case['methods']['seed_t']['directional_power'] is None
        assert case['methods']['seed_t']['coverage']['denominator']==2


def test_conditional_null_and_power_classification_uses_latent_truth():
    case=tiny_config()['cases'][0]
    assert null_status(case,'seed_conditional')=='varying'
    assert null_status(case,'calendar_conditional')=='varying'
    assert null_status(case,'joint')=='null'
    case=deepcopy(case);case['scenario']['sigma_time']=0.
    assert null_status(case,'seed_conditional')=='null'
    case['scenario']['delta']=[.35]
    assert null_status(case,'seed_conditional')=='positive_alternative'


def test_callbacks_cannot_mutate_frozen_effects_or_replication_count():
    config=tiny_config()
    expected,_=run_benchmark(config)
    def mutate(*_):
        config['replications']=3
        config['cases'][1]['scenario']['delta']=[99.]
        config['methods'][0]['label']='changed'
    actual,_=run_benchmark(config,progress=mutate)
    assert actual==expected


def test_overlap_law_matches_fixed_seed_and_calendar_truths():
    config=json.loads((ROOT/'configs/validation/m3_evaluation.json').read_text())
    case=deepcopy(next(x for x in config['cases'] if x['law']=='overlap_ma'))
    case['scenario'].update(sigma_seed=0.,sigma_cell=0.)
    a,b,truths=generate_case(case,93)
    difference=np.mean([float((a[f].losses-b[f].losses).mean()) for f in a])
    assert difference==pytest.approx(truths['seed_conditional'],abs=1e-12)
    assert truths['calendar_conditional']==pytest.approx(0.)
    assert truths['joint']==0.
    a2,b2,t2=generate_case(case,93)
    np.testing.assert_array_equal(a['f0'].losses,a2['f0'].losses)
    assert truths==t2


def test_gate_eligibility_is_predeclared_and_respects_estimand_and_support():
    config=json.loads((ROOT/'configs/validation/m3_evaluation.json').read_text())
    cases={x['scenario']['name']:x for x in config['cases']}
    methods={m['label']:m for m in config['methods']}
    assert gate_eligible(cases['eval_seed_null'],methods['seed_t'])
    assert not gate_eligible(cases['eval_correlated_seeds'],methods['seed_t'])
    assert not gate_eligible(cases['eval_t1_5'],methods['seed_t'])
    assert not gate_eligible(cases['eval_unequal_counts'],methods['hac_l3'])
    assert not gate_eligible(cases['eval_ar_short'],methods['hac_l7'])
    assert gate_eligible(cases['eval_ar_short'],methods['stationary_l7'])


@pytest.mark.parametrize('changes',[dict(replications=True),dict(replications=1001),
    dict(bootstrap_replicates=1000000),dict(cases=[]),dict(confidence=float('nan')),dict(unknown=1)])
def test_invalid_or_unbounded_study_config_rejects(changes):
    with pytest.raises(ValueError):validate_config(tiny_config()|changes)


def test_config_is_detached_and_duplicate_case_rejects():
    config=tiny_config(); snapshot=validate_config(config)
    config['cases'][0]['scenario']['delta']=[17.]
    assert snapshot['cases'][0]['scenario']['delta']==[0.]
    config['cases'][1]=deepcopy(config['cases'][0])
    with pytest.raises(ValueError):validate_config(config)


def test_missing_and_failed_run_catalog_never_drops_runs():
    results=adversarial_checks(validate_config(tiny_config()))
    assert len(results)==15
    assert all(x['rejected'] for x in results)
    assert {x['violation'] for x in results}=={'one_model_missing','both_models_missing','failed_fitting_record'}


@pytest.mark.parametrize('drift',['git_commit','git_branch','source'])
def test_cli_rechecks_complete_final_provenance_before_publication(tmp_path,monkeypatch,drift):
    spec=importlib.util.spec_from_file_location('m3_cli_test',ROOT/'scripts/run_m3_inference.py')
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    before=dict(git_commit='before',git_branch='M3',source=dict(files=[],fingerprint='source'))
    after=deepcopy(before)
    if drift=='source':after['source']['fingerprint']='changed'
    else:after[drift]='changed'
    snapshots=iter([before,after])
    monkeypatch.setattr(sys,'argv',['run_m3_inference.py','--root',str(tmp_path)])
    monkeypatch.setattr(cli,'read_finite_json',lambda _:tiny_config())
    monkeypatch.setattr(cli,'code_provenance',lambda _:next(snapshots))
    monkeypatch.setattr(cli,'run_benchmark',lambda *args,**kwargs:({'synthetic':True},{}))
    monkeypatch.setattr(cli,'verify_source_identities',lambda *args:None)
    published=[]
    monkeypatch.setattr(cli,'atomic_record',lambda *args:published.append(args) or tmp_path)
    with pytest.raises(ValueError,match='state changed'):cli.main()
    assert not published
