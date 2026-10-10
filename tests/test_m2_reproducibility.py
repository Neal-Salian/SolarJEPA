"""Clean-source CLI publication and deterministic payload identities."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.evaluation.stress.runner import validate_config, scientific_payload
from solar_flare_jepa.forecasting.contracts import fingerprint_payload
from solar_flare_jepa.evaluation.stress.synthetic import Scenario, generate_panels
from solar_flare_jepa.evaluation.comparison import paired_comparison


def tiny_config():
    return dict(schema_version=1, master_seed=71, replications=2, bootstrap_replicates=9,
        confidence=.95, calibration_origins=20, max_runtime_seconds=60,
        cases=[dict(scenario=dict(name='tiny', seeds=3, days=[4]), block_days=1, attribution=True)])


def test_payload_repeatability_excludes_timing_and_machine_paths():
    config = tiny_config()
    a, b = scientific_payload(config), scientific_payload(config)
    assert a == b
    assert fingerprint_payload(a) == fingerprint_payload(b)
    assert len(a['contracts']) >= 35
    assert a['references']['maximum_absolute_interval_error'] < 1e-12
    assert a['seed_sensitive']['mean_difference'] < 0
    assert a['seed_sensitive']['leave_one_seed_out_difference'][0] > 0
    assert a['seed_sensitive']['seed_win_fraction'] == pytest.approx(1/3)
    assert 'runtime' not in json.dumps(a)


@pytest.mark.parametrize('changes', [dict(replications=1001), dict(master_seed=True), dict(cases=[]),
    dict(bootstrap_replicates=10000), dict(calibration_origins=0), dict(max_runtime_seconds=100000)])
def test_runner_rejects_excessive_or_ambiguous_budgets(changes):
    with pytest.raises(ValueError):
        validate_config(tiny_config() | changes)


def test_config_strict_schema_and_source_payload_identity():
    with pytest.raises(ValueError):
        validate_config(tiny_config() | {'unknown': 1})
    config = tiny_config()
    config['cases'][0]['block_days'] = 5
    with pytest.raises(ValueError):
        validate_config(config)


def test_arm_swap_sign_equivariance_with_finite_samples():
    for seed in range(5):
        a, b, _ = generate_panels(Scenario('swap', seeds=3, days=(7, 9), counts=(1, 3, 0)), seed)
        args = dict(block_days=3, replicates=31, rng_seed=seed, confidence=.95)
        forward, reverse = paired_comparison(a, b, **args), paired_comparison(b, a, **args)
        assert forward['mean_difference'] == -reverse['mean_difference']
        np.testing.assert_allclose(forward['difference_interval'], -np.array(reverse['difference_interval'])[::-1], atol=1e-12)


def test_progress_callback_cannot_mutate_validated_scientific_design():
    config = tiny_config()
    config['cases'].append(dict(scenario=dict(name='tiny-two', seeds=3, days=[4]), block_days=1, attribution=False))
    def mutate(*_):
        config['replications'] = 3
        config['cases'][1]['scenario']['delta'] = [99.]
    result = scientific_payload(config, progress=mutate)
    assert [case['replications'] for case in result['cases']] == [2, 2]
    assert [case['truth'] for case in result['cases']] == [0., 0.]


@pytest.mark.parametrize('scenario', [[], {'name': 'bad', 'unknown': 1}])
def test_malformed_scenario_configuration_uses_value_error(scenario):
    config = tiny_config()
    config['cases'][0]['scenario'] = scenario
    with pytest.raises(ValueError):
        validate_config(config)


@pytest.mark.parametrize('drift', ['git_commit', 'git_branch', 'source'])
def test_cli_rechecks_complete_git_and_source_identity_before_publication(tmp_path, monkeypatch, drift):
    from copy import deepcopy
    import importlib.util
    from pathlib import Path
    import sys
    module_spec = importlib.util.spec_from_file_location('m2_cli_test', Path(__file__).resolve().parents[1]/'scripts/run_m2_validation.py')
    cli = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(cli)
    before = dict(git_commit='before', git_branch='M2', source=dict(files=[], fingerprint='source'))
    after = deepcopy(before)
    if drift == 'source':
        after['source']['fingerprint'] = 'newly-added-source'
    else:
        after[drift] = 'changed'
    snapshots = iter([before, after])
    monkeypatch.setattr(sys, 'argv', ['run_m2_validation.py', '--root', str(tmp_path)])
    monkeypatch.setattr(cli, 'read_finite_json', lambda _: tiny_config())
    monkeypatch.setattr(cli, 'code_provenance', lambda _: next(snapshots))
    monkeypatch.setattr(cli, 'scientific_payload', lambda *args, **kwargs: {'synthetic': True})
    monkeypatch.setattr(cli, 'verify_source_identities', lambda *args: None)
    published = []
    monkeypatch.setattr(cli, 'atomic_record', lambda *args: published.append(args) or tmp_path)
    monkeypatch.setattr(cli, 'verify_artifacts', lambda *args: None)
    with pytest.raises(ValueError, match='state changed'):
        cli.main()
    assert not published
