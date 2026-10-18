"""Artificial multivariate values with explicit invented-fixture semantics."""
import json

import numpy as np

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from .config import validate_config, utc_ns


def synthetic_fixture(config):
    cfg = validate_config(config)
    ds = cfg['dataset']
    if ds['kind'] != 'synthetic_fixture':
        raise ValueError('Synthetic generator cannot reinterpret scientific observations')
    spec = ForecastSpec(**cfg['forecast'])
    names = tuple(dict.fromkeys(spec.feature_names+spec.target_names))
    rng = np.random.default_rng(ds['fixture_seed'])
    t = np.arange(ds['rows'], dtype=float)
    # Artificial positive channels. No solar chronology, flux or events implied.
    values = np.column_stack([2.+k+.015*t+.3*np.sin(t/(7.+k))+
                              rng.normal(0,.01,len(t)) for k in range(len(names))])
    start = utc_ns(ds['start_utc'])
    last = start + ds['rows']*spec.cadence_ns
    if last > np.iinfo(np.int64).max:
        raise ValueError('Synthetic interval coordinates overflow')
    starts = start+np.arange(ds['rows'],dtype=np.int64)*spec.cadence_ns
    features = values[:,[names.index(x) for x in spec.feature_names]]
    targets = values[:,[names.index(x) for x in spec.target_names]]
    return TimeSeriesDataset('p1_artificial_multivariate','synthetic_fixture',starts,
        starts+spec.cadence_ns,features,np.ones_like(features,dtype=bool),targets,
        np.ones_like(targets,dtype=bool),spec.feature_names,spec.target_names,
        spec.feature_units,spec.target_units,spec.cadence_seconds,
        np.broadcast_to(starts[:,None]+spec.cadence_ns,features.shape),
        metadata_json=json.dumps(dict(generator='p1_artificial_v1',fixture_seed=ds['fixture_seed'],
            interpretation='foundation_smoke_not_scientific_skill')))
