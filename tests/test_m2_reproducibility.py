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
