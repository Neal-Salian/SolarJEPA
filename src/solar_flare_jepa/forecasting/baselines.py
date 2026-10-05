"""Deterministic point comparators fitted only on an explicit TrainingSlice.

Values remain in native units at the boundary. Log-space comparators return
inverse-transformed points, without claiming physical conditional means.
Masked prediction support is never turned into model-specific origin dropping.
"""
from copy import deepcopy
from collections.abc import Mapping

import numpy as np

from .contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, FutureGrid, TrainingSlice,
    _canonical_fields, _category, validate_alignment,
)


def _steps(value, name, minimum=1):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
            or value < minimum):
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def _finite(values, label):
    if not np.isfinite(values).all():
        raise ValueError(f'Nonfinite {label}; numeric overflow or insufficient fit')
    return values


def _target_column(spec, values, k):
    """Transform only selected valid observations, in a target's native units."""
    values = np.asarray(values, float)
    if spec.transform == 'identity':
        return _finite(values.copy(), 'target values')
    if (values <= 0).any():
        raise ValueError('Log transform requires positive valid target observations')
    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
        result = np.log10(values / spec.target_reference[k])
    return _finite(result, 'log transform')


class _Baseline:
    name = ''
    observed_counterparts = False

    def __init__(self):
        self._spec = None
        self._record = {'name': self.name}

    @property
    def parameters(self):
        """Detached, finite JSON-compatible constructor and fitted parameter record."""
        return deepcopy(self._record)

    def fit(self, training: TrainingSlice):
        if not isinstance(training, TrainingSlice):
            raise ValueError('fit requires a TrainingSlice')
        self._spec = None
        # Fit and record identity from the same validated immutable snapshot,
        # including reconstructed nested windows; no model-specific bypass.
        training = TrainingSlice(**_canonical_fields(training, TrainingSlice))
        spec = training.spec
        steps = getattr(self, 'lookback_steps', getattr(self, 'lag_steps', None))
        if steps is not None and steps > spec.context_steps:
            raise ValueError('Requested lag/lookback exceeds declared context length')
        if self.observed_counterparts:
            indices = []
            for name, unit in zip(spec.target_names, spec.target_units):
                if name not in spec.feature_names:
                    raise ValueError(f'Target {name!r} has no observed feature counterpart')
                index = spec.feature_names.index(name)
                if spec.feature_units[index] != unit:
                    raise ValueError(f'Target {name!r} counterpart units are incompatible')
                indices.append(index)
            self._indices = tuple(indices)
        # Do not make any training identity available to prediction until fit succeeds.
        fitted = self._fit(training)
        self._dataset_fingerprint = training.context.dataset_fingerprint
        record = dict(name=self.name, **self._constructor_parameters(), **fitted,
                      dataset_fingerprint=self._dataset_fingerprint,
                      spec_fingerprint=spec.fingerprint,
                      split_fingerprint=training.split_fingerprint,
                      training_fingerprint=training.fingerprint,
                      transform=spec.transform,
                      feature_reference=list(spec.feature_reference),
                      target_reference=list(spec.target_reference))
        if self.observed_counterparts:
            record['state_policy'] = 'latest_valid_observed_bin; elapsed_cadence_to_future'
        self._record = record
        self._spec = spec
        return self

    def _constructor_parameters(self):
        return {}

    def _fit(self, training):
        return {}

    def predict(self, context: ForecastContext, future_grid: FutureGrid):
        if self._spec is None:
            raise ValueError('Model must be successfully fitted before prediction')
        if not isinstance(context, ForecastContext) or not isinstance(future_grid, FutureGrid):
            raise ValueError('predict requires ForecastContext and FutureGrid')
        if (not isinstance(context.spec, ForecastSpec)
                or not isinstance(future_grid.spec, ForecastSpec)):
            raise ValueError('Prediction inputs require explicit forecast specs')
        # Copies, deserialization and subclasses need not preserve constructor
        # invariants. Validate and consume the same detached exact-base snapshot.
        # Reconstruct each declared spec independently; do not substitute the fit
        # spec, repair future support or invoke caller-supplied subtype methods.
        context_fields = _canonical_fields(context, ForecastContext)
        context_fields['spec'] = ForecastSpec(**_canonical_fields(context.spec, ForecastSpec))
        grid_fields = _canonical_fields(future_grid, FutureGrid)
        grid_fields['spec'] = ForecastSpec(**_canonical_fields(future_grid.spec, ForecastSpec))
        context = ForecastContext(**context_fields)
        future_grid = FutureGrid(**grid_fields)
        validate_alignment(context, future_grid)
        if (context.dataset_fingerprint != self._dataset_fingerprint
                or context.spec.fingerprint != self._spec.fingerprint):
            raise ValueError('Prediction dataset/spec identity differs from fitted identity')
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            transformed = self._predict(context, future_grid)
        values = self._spec.inverse_targets(_finite(transformed, 'forecast'))
        return ForecastPrediction(values, future_grid, self.name,
                                  point_interpretation=('native_point' if self._spec.transform == 'identity'
                                                        else 'inverse_transformed_point'))

    def _support(self, context, n, k, steps):
        feature = self._indices[k]
        valid = np.flatnonzero(context.mask[n, -steps:, feature]) + self._spec.context_steps - steps
        if len(valid) == 0:
            raise ValueError(f'Insufficient valid context support for origin {context.origin_ids[n]!r}')
        values = _target_column(self._spec, context.values[n, valid, feature], k)
        return valid, values

    def _shape(self, context):
        return (len(context.origin_ids), self._spec.horizon_steps, len(self._spec.target_names))


class Persistence(_Baseline):
    """Repeat the latest valid observed counterpart, even when earlier than issue."""
    name = 'persistence'
    observed_counterparts = True

    def _predict(self, context, grid):
        output = np.empty(self._shape(context))
        for n in range(len(context.origin_ids)):
            for k in range(len(self._indices)):
                _, values = self._support(context, n, k, self._spec.context_steps)
                output[n, :, k] = values[-1]
        return output


class TrainingMean(_Baseline):
    """Per-target mean of valid unique unwindowed training observations."""
    name = 'training_mean'

    def _fit(self, training):
        means, counts = [], []
        for k in range(len(training.spec.target_names)):
            selected = training.raw_targets[training.raw_target_mask[:, k], k]
            if len(selected) == 0:
                raise ValueError('Training mean requires valid raw samples for every target')
            with np.errstate(over='ignore', invalid='ignore'):
                means.append(float(_target_column(training.spec, selected, k).mean()))
            counts.append(len(selected))
        self._mean = _finite(np.array(means), 'training mean')
        return dict(mean=self._mean.tolist(), valid_sample_counts=counts)

    def _predict(self, context, grid):
        return np.broadcast_to(self._mean, self._shape(context)).copy()


class TrailingMean(_Baseline):
    """Mean of valid counterpart values in the last fixed lookback bins."""
    name = 'trailing_mean'
    observed_counterparts = True

    def __init__(self, lookback_steps):
        super().__init__()
        self.lookback_steps = _steps(lookback_steps, 'lookback_steps')
        self._record.update(self._constructor_parameters())

    def _constructor_parameters(self):
        return dict(lookback_steps=self.lookback_steps)

    def _predict(self, context, grid):
        output = np.empty(self._shape(context))
        for n in range(len(context.origin_ids)):
            for k in range(len(self._indices)):
                _, values = self._support(context, n, k, self.lookback_steps)
                output[n, :, k] = values.mean()
        return output


class Drift(TrailingMean):
    """Slope between first/last valid bins in fixed support, using elapsed time."""
    name = 'drift'

    def __init__(self, lookback_steps):
        super().__init__(_steps(lookback_steps, 'lookback_steps', minimum=2))

    def _predict(self, context, grid):
        output = np.empty(self._shape(context))
        for n in range(len(context.origin_ids)):
            for k in range(len(self._indices)):
                indices, values = self._support(context, n, k, self.lookback_steps)
                if len(indices) < 2:
                    raise ValueError('Drift requires at least two valid context support points')
                first = int(context.ends_ns[n, indices[0]])
                last = int(context.ends_ns[n, indices[-1]])
                elapsed = np.array([int(end)-last for end in grid.ends_ns[n]], float)
                output[n, :, k] = values[-1] + (values[-1]-values[0]) * (elapsed / (last-first))
        return output


class AR1(_Baseline):
    """Fixed per-target least-squares AR(1) with intercept; no gap bridging."""
    name = 'ar1'
    observed_counterparts = True

    def _fit(self, training):
        intercepts, coefficients, counts = [], [], []
        adjacent = np.array([int(b)-int(a) == training.spec.cadence_ns
                             for a, b in zip(training.raw_starts_ns, training.raw_starts_ns[1:])], bool)
        for k in range(len(training.spec.target_names)):
            mask = training.raw_target_mask[:, k]
            pairs = adjacent & mask[:-1] & mask[1:]
            if pairs.sum() < 2:
                raise ValueError('AR1 requires at least two adjacent valid training pairs per target')
            x = _target_column(training.spec, training.raw_targets[:-1, k][pairs], k)
            y = _target_column(training.spec, training.raw_targets[1:, k][pairs], k)
            try:
                with np.errstate(over='ignore', invalid='ignore'):
                    coefficients_pair = np.linalg.lstsq(np.column_stack((np.ones(len(x)), x)), y, rcond=None)[0]
            except np.linalg.LinAlgError as error:
                raise ValueError('AR1 training least-squares fit failed') from error
            _finite(coefficients_pair, 'AR1 fit')
            intercepts.append(float(coefficients_pair[0]))
            coefficients.append(float(coefficients_pair[1]))
            counts.append(int(pairs.sum()))
        self._intercept, self._coefficient = np.array(intercepts), np.array(coefficients)
        return dict(intercept=intercepts, coefficient=coefficients, valid_pair_counts=counts)

    def _predict(self, context, grid):
        output = np.empty(self._shape(context))
        for n in range(len(context.origin_ids)):
            for k in range(len(self._indices)):
                indices, values = self._support(context, n, k, self._spec.context_steps)
                state = values[-1]
                last_end = int(context.ends_ns[n, indices[-1]])
                steps = (int(grid.ends_ns[n, 0]) - last_end) // self._spec.cadence_ns
                for _ in range(steps):
                    state = self._intercept[k] + self._coefficient[k]*state
                output[n, 0, k] = state
                for lead in range(1, self._spec.horizon_steps):
                    state = self._intercept[k] + self._coefficient[k]*state
                    output[n, lead, k] = state
        return output


class DirectRidge(_Baseline):
    """Map fixed recent feature lags jointly to all future leads/targets.

    Minimize ||Y - intercept - X B||² + alpha ||B||². The intercept is
    unpenalized. Alpha zero uses the deterministic minimum-norm least-squares
    solution when lags are collinear. Only complete training rows enter fit;
    every prediction row must have complete declared lags.
    """
    name = 'direct_ridge'

    def __init__(self, lag_steps, alpha):
        super().__init__()
        self.lag_steps = _steps(lag_steps, 'lag_steps')
        if (isinstance(alpha, (bool, np.bool_)) or not isinstance(alpha, (int, float, np.integer, np.floating))
                or not np.isfinite(alpha) or alpha < 0):
            raise ValueError('alpha must be a finite nonnegative number')
        self.alpha = float(alpha)
        self._record.update(self._constructor_parameters())

    def _constructor_parameters(self):
        return dict(lag_steps=self.lag_steps, alpha=self.alpha)

    def _fit(self, training):
        selected = (training.context.mask[:, -self.lag_steps:, :].all(axis=(1, 2))
                    & training.targets.mask.all(axis=(1, 2)))
        if selected.sum() < 1:
            raise ValueError('Direct ridge requires complete valid training windows')
        x = training.spec.transform_features(training.context.values[selected, -self.lag_steps:, :]).reshape(int(selected.sum()), -1)
        y = training.spec.transform_targets(training.targets.values[selected]).reshape(int(selected.sum()), -1)
        with np.errstate(over='ignore', invalid='ignore'):
            xmean, ymean = x.mean(axis=0), y.mean(axis=0)
            xc, yc = x-xmean, y-ymean
        _finite(xc, 'centered ridge features')
        _finite(yc, 'centered ridge targets')
        # Augmented least squares avoids squaring X's condition number.
        design = np.vstack((xc, np.sqrt(self.alpha)*np.eye(x.shape[1])))
        response = np.vstack((yc, np.zeros((x.shape[1], y.shape[1]))))
        try:
            coefficient = np.linalg.lstsq(design, response, rcond=None)[0]
        except np.linalg.LinAlgError as error:
            raise ValueError('Direct ridge training least-squares fit failed') from error
        with np.errstate(over='ignore', invalid='ignore'):
            intercept = ymean-xmean@coefficient
        self._coefficient = _finite(coefficient, 'ridge coefficients')
        self._intercept = _finite(intercept, 'ridge intercept')
        return dict(coefficient=coefficient.tolist(), intercept=intercept.tolist(),
                    valid_window_count=int(selected.sum()))

    def _predict(self, context, grid):
        if not context.mask[:, -self.lag_steps:, :].all():
            raise ValueError('Direct ridge requires fully valid declared context lags for every origin')
        x = self._spec.transform_features(context.values[:, -self.lag_steps:, :])
        x = x.reshape(len(context.origin_ids), self.lag_steps*len(self._spec.feature_names))
        return (x@self._coefficient + self._intercept).reshape(self._shape(context))


_BASELINES = {'persistence': Persistence, 'training_mean': TrainingMean,
              'trailing_mean': TrailingMean, 'drift': Drift, 'ar1': AR1,
              'direct_ridge': DirectRidge}


def make_baseline(name, parameters):
    """Construct one fixed baseline; unknown names/parameters fail clearly."""
    name = _category(name, tuple(_BASELINES), 'baseline name')
    if not isinstance(parameters, Mapping):
        raise ValueError('Baseline parameters must be a mapping')
    try:
        return _BASELINES[name](**parameters)
    except TypeError as error:
        raise ValueError(f'Invalid parameters for baseline {name!r}: {error}') from error
