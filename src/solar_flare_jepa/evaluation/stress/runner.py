"""Validated budgets and deterministic synthetic-only scientific payloads."""
from dataclasses import replace
import time

import numpy as np

from ...forecasting.contracts import canonical_json
from ..comparison import paired_comparison
from .calibration import calibration_study
from .contracts import contract_probes
from .reference import reference_bootstrap
from .study import run_case
from .synthetic import Scenario, generate_panels


def validate_config(config):
    required = {'schema_version', 'master_seed', 'replications', 'bootstrap_replicates', 'confidence',
                'calibration_origins', 'max_runtime_seconds', 'cases'}
    if type(config) is not dict or set(config) != required or type(config['schema_version']) is not int or config['schema_version'] != 1:
        raise ValueError('Malformed M2 configuration')
    canonical_json(config)
    for name, minimum, maximum in (('master_seed', 0, 2**63-1), ('replications', 2, 1000),
        ('bootstrap_replicates', 2, 5000), ('calibration_origins', 1, 100000), ('max_runtime_seconds', 1, 900)):
        if type(config[name]) is not int or not minimum <= config[name] <= maximum:
            raise ValueError(f'{name} outside bounded integer budget')
    if type(config['confidence']) not in (int, float) or not 0 < config['confidence'] < 1:
        raise ValueError('Confidence must be within (0,1)')
    if type(config['cases']) is not list or not 1 <= len(config['cases']) <= 32:
        raise ValueError('One to 32 explicit cases required')
    keys, workload = set(), 0
    for case in config['cases']:
        if type(case) is not dict or set(case) != {'scenario', 'block_days', 'attribution'} or type(case['attribution']) is not bool:
            raise ValueError('Malformed case configuration')
        cfg = Scenario(**case['scenario'])
        block = case['block_days']
        if type(block) is not int or not 1 <= block <= min(cfg.days):
            raise ValueError('Block must fit every fixed fold')
        key = (cfg.name, block)
        if key in keys:
            raise ValueError('Duplicate case identity')
        keys.add(key)
        workload += (1+2*case['attribution'])*config['replications']*config['bootstrap_replicates']
    if workload > 4_000_000:
        raise ValueError('Total study exceeds four million bootstrap draws')
    return config


def independent_reference_checks():
    maximum = 0.
    for days, counts, block in (((7,), (1,), 1), ((7, 5), (1, 3, 0), 3), ((4, 4), (1,), 4)):
        a, b, _ = generate_panels(Scenario('independent-reference', seeds=3, days=days, counts=counts), 123)
        args = dict(block_days=block, replicates=101, rng_seed=8, confidence=.95)
        actual = paired_comparison(a, b, **args)
        reference = reference_bootstrap(a, b, **args)
        if actual['difference_interval'] is None or reference['interval'] is None:
            raise AssertionError('Reference fixture unexpectedly unavailable')
        maximum = max(maximum, float(np.max(np.abs(np.array(actual['difference_interval'])-reference['interval']))))
    if maximum > 1e-12:
        raise AssertionError('M1 disagrees with direct-origin reference')
    return dict(fixtures=3, draws_per_fixture=101, maximum_absolute_interval_error=maximum,
                iid_interaction_variance_factor='3 - 2/S - 2/T + 1/(S*T) for block=1 and one fold')


def scientific_payload(config, *, progress=None):
    """No timing/path metadata in scientific payload; runtime guard is external.

    Budget checked between cases (a single case cannot be interrupted here).
    Any budget overrun raises before publication, never drops remaining cases.
    """
    config = validate_config(config)
    started = time.monotonic()
    cases = []
    for i, case in enumerate(config['cases']):
        if time.monotonic()-started > config['max_runtime_seconds']:
            raise TimeoutError('M2 runtime budget exceeded; incomplete study is not published')
        cfg = Scenario(**case['scenario'])
        result = run_case(cfg, block_days=case['block_days'], attribution=case['attribution'],
                          replications=config['replications'], bootstrap_replicates=config['bootstrap_replicates'],
                          confidence=config['confidence'], master_seed=config['master_seed'])
        cases.append(result)
        if progress is not None:
            progress(i+1, len(config['cases']), cfg.name, case['block_days'])
    a, b, _ = generate_panels(Scenario('seed-sensitive', seeds=3, days=(4,), sigma_seed=0., sigma_time=0., sigma_cell=0.), 1)
    shifts = np.array([-1.2, .2, .2])[:, None]
    b['f0'] = replace(b['f0'], losses=np.full((3, 4), 2.))
    a['f0'] = replace(a['f0'], losses=b['f0'].losses+shifts)
    seed_sensitive = paired_comparison(a, b, block_days=1, replicates=99, rng_seed=1, confidence=.95)
    calibration = calibration_study(origins=config['calibration_origins'], rng_seed=config['master_seed'])
    if any(row['arithmetic']['max_scaled_error'] > 1e-12 for row in calibration['normal']):
        raise AssertionError('Calibration arithmetic disagrees with literal reference')
    if time.monotonic()-started > config['max_runtime_seconds']:
        raise TimeoutError('M2 runtime budget exceeded; incomplete study is not published')
    return dict(schema_version=1, synthetic_only=True, cases=cases, contracts=contract_probes(),
                calibration=calibration, references=independent_reference_checks(), seed_sensitive=seed_sensitive,
                interpretation='Synthetic method assessment only; no real-data validity or nominal-coverage certification')
