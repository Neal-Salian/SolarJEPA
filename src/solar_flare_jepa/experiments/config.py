"""Strict, resolved P1 configurations with no implicit scientific defaults."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from solar_flare_jepa.forecasting.contracts import ForecastSpec, canonical_json, fingerprint_payload


def _object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON field: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f'Nonfinite JSON constant: {value}')


def read_finite_json(path: Path):
    return json.loads(Path(path).read_text(), object_pairs_hook=_object,
                      parse_constant=_reject_constant)


def _keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value)-set(required)-set(optional) or set(required)-set(value):
        raise ValueError(f'Expected required fields {sorted(required)} and optional {sorted(optional)}')


def utc_ns(value):
    if not isinstance(value, str):
        raise ValueError('UTC coordinates must be explicit timezone-bearing strings')
    try:
        stamp = pd.Timestamp(value)
        if stamp.tz is None or stamp.utcoffset() != pd.Timedelta(0) or pd.isna(stamp):
            raise ValueError('An explicit UTC timestamp is required')
        return int(stamp.value)
    except (TypeError, OverflowError, ValueError) as exc:
        raise ValueError('Invalid explicit UTC coordinate') from exc


def _positive_int(value, *, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError('Expected integer configuration value')
    return value


def _weights(value, count):
    if not isinstance(value, list) or len(value) != count or any(type(x) not in (float,int) for x in value):
        raise ValueError('Metric weights must be explicit numeric lists of matching length')
    array = np.asarray(value, dtype=float)
    with np.errstate(over='ignore'):
        total = array.sum()
    if not np.isfinite(array).all() or (array < 0).any() or not np.isfinite(total) or total <= 0:
        raise ValueError('Invalid metric weights')
    return array.tolist()


def validate_config(config):
    """Return a fully resolved finite copy; unsupported scientific inputs fail."""
    try:
        canonical_json(config)
    except (TypeError,ValueError) as exc:
        raise ValueError('Configuration must be finite JSON') from exc
    cfg = deepcopy(config)
    _keys(cfg, ('schema_version','dataset','forecast','splits','baselines','metrics','seeds'))
    if type(cfg['schema_version']) is not int or cfg['schema_version'] != 1:
        raise ValueError('Unsupported schema version')
    dataset = cfg['dataset']
    if not isinstance(dataset,dict) or dataset.get('kind') not in ('synthetic_fixture','goes_reference'):
        raise ValueError('Unsupported scientific input; Phase E remains BLOCKED_FOR_PHASE_E')
    if dataset['kind'] == 'synthetic_fixture':
        _keys(dataset, ('kind','rows','start_utc','fixture_seed'))
        _positive_int(dataset['rows'])
        _positive_int(dataset['fixture_seed'], minimum=0)
        dataset['start_utc'] = pd.Timestamp(utc_ns(dataset['start_utc']),tz='UTC').isoformat()
    else:
        _keys(dataset, ('kind','manifest','prepared_config','sidecar'))
        expected = dict(manifest='configs/data/noaa_sample.json', prepared_config='configs/data/noaa_eda.json',
                        sidecar='data/processed/noaa_reference.metadata.json')
        if any(dataset[k] != v for k,v in expected.items()):
            raise ValueError('Only the existing pinned GOES reference is supported')
    if not isinstance(cfg['forecast'],dict):
        raise ValueError('Forecast definition must be an object')
    try:
        spec = ForecastSpec(**cfg['forecast'])
    except (TypeError,ValueError) as exc:
        raise ValueError('Invalid forecast specification') from exc
    cfg['forecast'] = json.loads(canonical_json(spec.as_dict()))
    if dataset['kind'] == 'goes_reference':
        if (spec.feature_names != ('xrsb_flux',) or spec.target_names != ('xrsb_flux',)
                or spec.feature_units != ('W/m2',) or spec.target_units != ('W/m2',)
                or spec.availability_mode != 'retrospective_bin_end'
                or spec.eligibility_policy != 'complete' or spec.cadence_seconds != 60
                or spec.feature_lookback_steps != 0):
            raise ValueError('Unsupported pinned GOES smoke representation/policy')
    elif any(unit != 'synthetic_unit' for unit in spec.feature_units+spec.target_units):
        raise ValueError('Artificial fixture units must be explicitly synthetic_unit')
    if not isinstance(cfg['splits'],list) or len(cfg['splits']) not in (3,4):
        raise ValueError('Explicit chronological splits are required')
    names = ['train','validation','test'] if len(cfg['splits']) == 3 else ['train','validation','calibration','test']
    previous = None
    for item,name in zip(cfg['splits'],names):
        _keys(item, ('name','start_utc','end_utc'))
        start,end = utc_ns(item['start_utc']),utc_ns(item['end_utc'])
        if item['name'] != name or start >= end or previous is not None and start < previous:
            raise ValueError('Splits must be nonoverlapping chronological train/validation/(calibration)/test')
        item['start_utc'],item['end_utc'] = [pd.Timestamp(x,tz='UTC').isoformat() for x in (start,end)]
        previous = end
    if not isinstance(cfg['baselines'],list) or not cfg['baselines']:
        raise ValueError('At least one declared baseline required')
    allowed = {'persistence':(), 'training_mean':(), 'ar1':(),
               'trailing_mean':('lookback_steps',), 'drift':('lookback_steps',),
               'direct_ridge':('lag_steps','alpha')}
    seen = set()
    for model in cfg['baselines']:
        _keys(model, ('name','parameters'))
        name,parameters = model['name'],model['parameters']
        if not isinstance(name,str) or name not in allowed or name in seen:
            raise ValueError('Unsupported or duplicate baseline; ARCH/GARCH fitting is deferred')
        seen.add(name)
        _keys(parameters, allowed[name])
        if 'lookback_steps' in parameters:
            length = _positive_int(parameters['lookback_steps'], minimum=2 if name == 'drift' else 1)
            if length > spec.context_steps:
                raise ValueError('Baseline lookback exceeds available context')
        if 'lag_steps' in parameters:
            if _positive_int(parameters['lag_steps']) > spec.context_steps:
                raise ValueError('Ridge lag exceeds context')
            alpha = parameters['alpha']
            if type(alpha) not in (float,int) or not np.isfinite(alpha) or alpha < 0:
                raise ValueError('Ridge alpha must be finite and nonnegative')
            parameters['alpha'] = float(alpha)
    _keys(cfg['metrics'], ('lead_weights','target_weights'))
    cfg['metrics']['lead_weights'] = _weights(cfg['metrics']['lead_weights'],spec.horizon_steps)
    cfg['metrics']['target_weights'] = _weights(cfg['metrics']['target_weights'],len(spec.target_names))
    if not isinstance(cfg['seeds'],list) or not cfg['seeds']:
        raise ValueError('Seeds must be a nonempty unique list')
    for seed in cfg['seeds']:
        _positive_int(seed, minimum=0)
    if len(set(cfg['seeds'])) != len(cfg['seeds']):
        raise ValueError('Seeds must be a nonempty unique list')
    return cfg


def load_config(path):
    return validate_config(read_finite_json(Path(path)))


def config_fingerprint(config):
    return fingerprint_payload(validate_config(config))
