"""Restore verified classical V1 records and bind an explicit prediction dataset.

This loader checks record structure and declared identities; it cannot establish
that caller-supplied coefficients came from the historical run. Production must
supply records authenticated by ``load_frozen_inputs`` and bind its distinct
external dataset. Binding the original dataset is permitted for historical
replay. Original dataset/training/split records and baseline guards are retained.
No fit, optimizer, normalization estimation or fit-quality selection occurs.
"""
from copy import deepcopy
import json

import numpy as np

from .baselines import AR1, DirectRidge, TrainingMean, _finite, make_baseline
from .contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, FutureGrid, _canonical_fields, _canonical_strings,
    _string, canonical_json,
)
from .statistical import ARIMA, PersistenceEmpirical, QUANTILE_LEVELS, Volatility
from solar_flare_jepa.training.core import _context_grid

_STATE_POLICY = 'latest_valid_observed_bin; elapsed_cadence_to_future'


def _array(record, key, shape, *, integer=False):
    values = np.asarray(record[key])
    if (values.shape != shape or values.dtype.kind not in ('iu' if integer else 'fiu')
            or not np.isfinite(values).all()):
        raise ValueError(f'Invalid {key}: expected finite numeric shape {shape}')
    if integer and (values < 0).any():
        raise ValueError(f'{key} must contain nonnegative counts')
    return values.astype(np.int64 if integer else float, copy=True)


def _channels(record, key, k, kind):
    values = record[key]
    if (not isinstance(values, list) or len(values) != k
            or any(type(value) is not kind for value in values)):
        raise ValueError(f'Invalid per-target {key}')
    return values


def _restore_model(record, spec):
    name = _string(record['name'], 'Model name')
    if name.startswith(('arima(', 'sarima(')):
        model = ARIMA(record['order'], record['seasonal_order'], record['fit_last_steps'], record['maxiter'])
    elif name.startswith('ar1-'):
        model = Volatility(record['vol'], record['dist'], record['simulations'], record['sim_seed'])
        if model.simulations != 1000 or model.sim_seed != 0:
            raise ValueError('Frozen V1 requires simulations=1000 and sim_seed=0')
    elif name == 'persistence_empirical':
        model = PersistenceEmpirical()
    else:
        keys = {'persistence': (), 'training_mean': (), 'trailing_mean': ('lookback_steps',),
                'drift': ('lookback_steps',), 'ar1': (), 'direct_ridge': ('lag_steps', 'alpha')}
        if name not in keys:
            raise ValueError(f'Unknown frozen baseline name {name!r}')
        model = make_baseline(name, {key: record[key] for key in keys[name]})
    if model.name != name:
        raise ValueError('Recorded model name differs from its constructor recipe')
    steps = getattr(model, 'lookback_steps', getattr(model, 'lag_steps', None))
    if steps is not None and steps > spec.context_steps:
        raise ValueError('Recorded lag/lookback exceeds original forecast context')
    for key, value in model._constructor_parameters().items():
        if record[key] != value:
            raise ValueError(f'Recorded constructor {key} differs from model semantics')
    k, h = len(spec.target_names), spec.horizon_steps
    model._spec = spec
    if model.observed_counterparts:
        if record['state_policy'] != _STATE_POLICY:
            raise ValueError('Recorded observed state policy is incompatible')
        indices = []
        for name, unit in zip(spec.target_names, spec.target_units):
            if name not in spec.feature_names:
                raise ValueError('Target has no observed feature counterpart')
            index = spec.feature_names.index(name)
            if spec.feature_units[index] != unit:
                raise ValueError('Observed counterpart units differ')
            indices.append(index)
        model._indices = tuple(indices)
    if isinstance(model, TrainingMean):
        model._mean = _array(record, 'mean', (k,))
        if (_array(record, 'valid_sample_counts', (k,), integer=True) < 1).any():
            raise ValueError('Training means require recorded valid samples')
    elif isinstance(model, AR1):
        model._intercept = _array(record, 'intercept', (k,))
        model._coefficient = _array(record, 'coefficient', (k,))
        if (_array(record, 'valid_pair_counts', (k,), integer=True) < 2).any():
            raise ValueError('AR1 requires recorded training pairs')
    elif isinstance(model, DirectRidge):
        model._intercept = _array(record, 'intercept', (h*k,))
        model._coefficient = _array(record, 'coefficient', (model.lag_steps*len(spec.feature_names), h*k))
        if type(record['valid_window_count']) is not int or record['valid_window_count'] < 1:
            raise ValueError('Ridge requires a recorded valid window count')
    elif isinstance(model, PersistenceEmpirical):
        if record['quantile_levels'] != list(QUANTILE_LEVELS):
            raise ValueError('Empirical quantile levels differ from frozen recipe')
        if record['lead_policy'] != 'leads 1..context_steps+horizon_steps from latest valid bin':
            raise ValueError('Empirical lead policy differs from frozen recipe')
        shape = (spec.context_steps+h, k, len(QUANTILE_LEVELS))
        raw = np.asarray(record['increment_quantiles'], dtype=object)
        if raw.shape != shape:
            raise ValueError(f'Invalid increment_quantiles shape; expected {shape}')
        # Null is only the original explicit lack of pair support at a lead.
        counts = _array(record, 'valid_pair_counts', shape[:2], integer=True)
        for index in np.ndindex(shape[:2]):
            values = raw[index].tolist()
            if counts[index] == 0:
                if any(value is not None for value in values):
                    raise ValueError('Unsupported empirical leads require explicit nulls')
            elif any(type(value) not in (int, float) for value in values):
                raise ValueError('Supported empirical increments must be finite numeric values')
        table = np.asarray(raw, float)
        if (counts[:h] == 0).any() or (np.diff(table[counts > 0], axis=-1) < 0).any():
            raise ValueError('Invalid empirical support/quantile ordering')
        model._table = table
    elif isinstance(model, ARIMA):
        names = model._model(np.zeros(spec.context_steps)).param_names
        model._params = _named_parameters(record, names, k)
        _array(record, 'aic', (k,))
        _array(record, 'loglikelihood', (k,))
        _channels(record, 'converged', k, bool)
        _array(record, 'fit_grid_steps', (k,), integer=True)
        _array(record, 'valid_observation_counts', (k,), integer=True)
        _warnings(record, k)
    elif isinstance(model, Volatility):
        names = model._model(np.zeros(spec.context_steps), 0)._all_parameter_names()
        model._params = _named_parameters(record, names, k)
        model._scales = _array(record, 'scale', (k,))
        if (model._scales <= 0).any():
            raise ValueError('Recorded volatility scale must be positive')
        mean = _channels(record, 'mean', k, dict)
        model._means = []
        for value in mean:
            pair = (_array(value, 'const', ()), _array(value, 'phi', ()))
            if not abs(float(pair[1])) < 1:
                raise ValueError('Recorded AR(1) difference mean is not stationary')
            model._means.append(tuple(float(x) for x in pair))
        _array(record, 'loglikelihood', (k,))
        _array(record, 'persistence', (k,))  # Near/above-unit states are retained.
        _array(record, 'convergence_flag', (k,), integer=True)  # No convergence gate.
        _array(record, 'valid_pair_counts', (k,), integer=True)
        _warnings(record, k)
        _channels(record, 'starts', k, list)
        if (record['estimator'] != 'two-stage: OLS AR(1) mean, then zero-mean variance MLE on residuals'
                or record['pair_policy'] != 'consecutive valid differences; residuals concatenated across gaps'):
            raise ValueError('Recorded volatility estimator/pair semantics differ')
    model._dataset_fingerprint = record['dataset_fingerprint']
    model._record = deepcopy(record)
    return model


def _named_parameters(record, names, k):
    if _channels(record, 'param_names', k, list) != [list(names)]*k:
        raise ValueError('Recorded parameter names/order differ from fixed model')
    return list(_array(record, 'params', (k, len(names))))


def _warnings(record, k):
    if any(any(type(warning) is not str for warning in values)
           for values in _channels(record, 'fit_warnings', k, list)):
        raise ValueError('Recorded fit warnings must be per-target strings')


class FrozenBaseline:
    """Fixed classical equations with original fit identity and bound input identity.

    ``parameters`` remains the detached original fitted record, including fit
    warnings/flags. Only the explicit prediction dataset is permitted here;
    the underlying baseline's original dataset guard is never changed.
    """
    def __init__(self, model, external_dataset_fingerprint):
        self._model = model
        self._external_dataset_fingerprint = external_dataset_fingerprint

    @property
    def parameters(self):
        return self._model.parameters

    @property
    def name(self):
        return self._model.name

    @property
    def training_fingerprint(self):
        return self._model._record['training_fingerprint']

    @property
    def dataset_fingerprint(self):
        return self._model._record['dataset_fingerprint']

    @property
    def external_dataset_fingerprint(self):
        return self._external_dataset_fingerprint

    def predict(self, context, future_grid):
        if (not isinstance(context, ForecastContext) or not isinstance(future_grid, FutureGrid)
                or not isinstance(context.spec, ForecastSpec)
                or not isinstance(future_grid.spec, ForecastSpec)):
            raise ValueError('Prediction requires context/grid with explicit forecast specs')
        context, grid = _context_grid(context, future_grid)
        model, spec = self._model, self._model._spec
        if (context.dataset_fingerprint != self.external_dataset_fingerprint
                or context.spec.fingerprint != spec.fingerprint):
            raise ValueError('Prediction dataset/spec differs from explicitly bound frozen inputs')
        model._quantiles = None
        try:
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                transformed = model._predict(context, grid)
            values = spec.inverse_targets(_finite(transformed, 'frozen forecast'))
            transformed_quantiles = model._quantiles
        finally:
            model._quantiles = None
        quantiles = None
        levels = ()
        if transformed_quantiles is not None:
            levels = QUANTILE_LEVELS
            quantiles = np.stack([spec.inverse_targets(transformed_quantiles[..., j])
                                  for j in range(len(levels))], axis=-1)
            quantiles = np.maximum.accumulate(_finite(quantiles, 'native frozen quantiles'), axis=-1)
            if not np.array_equal(quantiles[..., levels.index(.5)], values):
                raise ValueError('Frozen point must equal the predictive median')
        return ForecastPrediction(values, grid, model.name, levels, quantiles,
                                  'native_point' if spec.transform == 'identity' else 'inverse_transformed_point')


def load_frozen_baseline(record: dict, spec: ForecastSpec, *,
                         expected_training_fingerprint: str,
                         external_dataset_fingerprint: str) -> FrozenBaseline:
    """Restore authenticated saved parameters without fitting or reselection.

    ``expected_training_fingerprint`` is the verified original TrainingSlice
    fingerprint, not an external fit. Record authenticity is established by the
    input manifest loader before this structural adapter is called.
    """
    if not isinstance(record, dict) or not isinstance(spec, ForecastSpec):
        raise ValueError('Frozen restoration requires a fitted record and ForecastSpec')
    spec = ForecastSpec(**_canonical_fields(spec, ForecastSpec))
    expected = _string(expected_training_fingerprint, 'Expected training fingerprint')
    external = _string(external_dataset_fingerprint, 'Bound prediction dataset fingerprint')
    try:
        record = json.loads(canonical_json(_canonical_strings(record)))
        for key in ('dataset_fingerprint', 'training_fingerprint', 'split_fingerprint', 'spec_fingerprint'):
            _string(record[key], key)
        if record['training_fingerprint'] != expected or record['spec_fingerprint'] != spec.fingerprint:
            raise ValueError('Recorded training/spec identity differs from verified original')
        if (record['transform'] != spec.transform
                or record['feature_reference'] != list(spec.feature_reference)
                or record['target_reference'] != list(spec.target_reference)):
            raise ValueError('Recorded transform/reference semantics differ from original spec')
        model = _restore_model(record, spec)
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError(f'Malformed frozen fit record: {error}') from error
    return FrozenBaseline(model, external)
