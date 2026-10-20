"""Classical probabilistic comparators fitted only on an explicit TrainingSlice.

Each target channel is modelled separately as a univariate series in the
spec's transformed space (log10 of flux over the declared reference for GOES
XRS). Only the canonical raw training arrays enter fitting; validation/test
data are never seen. Fitted parameters are fixed at prediction time: each
origin's own context sets the forecast state, without refitting.

Point values are the predictive MEDIAN in transformed space, inverse
transformed. Because the inverse transform is monotone, inverse-transformed
transformed-space quantiles are native-unit quantiles of the same predictive
distribution; the median maps to the native median, never to a native mean.
Predictive distributions are conditional on point-estimated parameters and
omit parameter uncertainty.
"""
from collections.abc import Mapping
import warnings

import numpy as np

from .baselines import _Baseline, _finite, _steps, _target_column
from .contracts import ForecastPrediction, _category, _canonical_strings, logical_array

QUANTILE_LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
_MEDIAN = QUANTILE_LEVELS.index(0.5)


def _grid_series(training, k):
    """Transformed target k on the regular raw cadence grid; NaN marks absent or invalid bins."""
    starts = training.raw_starts_ns
    if not len(starts):
        raise ValueError('Statistical fits require nonempty raw training support')
    cadence = training.spec.cadence_ns
    offsets = np.array([(int(s) - int(starts[0])) // cadence for s in starts], np.int64)
    series = np.full(int(offsets[-1]) + 1, np.nan)
    mask = training.raw_target_mask[:, k]
    if mask.any():
        series[offsets[mask]] = _target_column(training.spec, training.raw_targets[mask, k], k)
    return series


def _context_series(model, context, n, k):
    """Latest-valid support plus the full context grid (NaN where invalid)."""
    indices, values = model._support(context, n, k, model._spec.context_steps)
    series = np.full(model._spec.context_steps, np.nan)
    series[indices] = values
    return indices, values, series


def _gap(model, context, grid, n, last_index):
    """One-step advances from the latest valid context bin to the first future bin."""
    return (int(grid.ends_ns[n, 0]) - int(context.ends_ns[n, last_index])) // model._spec.cadence_ns


def _warnings_record(caught):
    return sorted({f'{w.category.__name__}: {w.message}'[:300] for w in caught})


class _ProbabilisticBaseline(_Baseline):
    """Quantile-forecasting base. `_predict` returns the transformed median [N,H,K]
    and sets transformed quantiles [N,H,K,Q] on `self._quantiles`."""
    observed_counterparts = True

    def __init__(self):
        super().__init__()
        self._quantiles = None

    def _store(self, quantiles):
        quantiles = np.maximum.accumulate(_finite(quantiles, 'forecast quantiles'), axis=-1)
        self._quantiles = quantiles
        return quantiles[..., _MEDIAN].copy()

    def predict(self, context, future_grid):
        self._quantiles = None
        try:
            point = super().predict(context, future_grid)
            transformed = self._quantiles
        finally:
            self._quantiles = None
        native = np.stack([self._spec.inverse_targets(transformed[..., j])
                           for j in range(len(QUANTILE_LEVELS))], axis=-1)
        native = np.maximum.accumulate(_finite(native, 'native forecast quantiles'), axis=-1)
        if not np.array_equal(native[..., _MEDIAN], point.values):
            raise ValueError('Point forecast must equal the predictive median quantile')
        return ForecastPrediction(values=point.values, grid=point.grid, model_id=self.name,
                                  quantile_levels=QUANTILE_LEVELS, quantiles=native,
                                  point_interpretation=point.point_interpretation)


class PersistenceEmpirical(_ProbabilisticBaseline):
    """Latest valid value plus per-lead empirical training increment quantiles.

    For lead h, increments y[t+h] - y[t] are taken over all training grid
    pairs whose two bins are both valid (no bin or gap is bridged by
    imputation; pairs are defined by elapsed cadence). Leads are counted from
    the latest valid context bin, so a stale context uses longer-lead
    increments. The point is the median (latest value + median increment),
    which is not exactly the latest value. Quantiles use numpy's default
    linear interpolation. Increments pool all training conditions.
    """
    name = 'persistence_empirical'

    def _fit(self, training):
        spec = training.spec
        leads = spec.context_steps + spec.horizon_steps
        table = np.full((leads, len(spec.target_names), len(QUANTILE_LEVELS)), np.nan)
        counts = np.zeros((leads, len(spec.target_names)), int)
        for k in range(len(spec.target_names)):
            y = _grid_series(training, k)
            for h in range(1, leads + 1):
                d = y[h:] - y[:-h] if h < len(y) else np.empty(0)
                d = d[np.isfinite(d)]
                counts[h - 1, k] = len(d)
                if len(d):
                    table[h - 1, k] = np.quantile(d, QUANTILE_LEVELS)
        if (counts[:spec.horizon_steps] == 0).any():
            raise ValueError('Empirical persistence requires valid training pairs at every horizon lead')
        self._table = table
        return dict(quantile_levels=list(QUANTILE_LEVELS), increment_quantiles=logical_array(table),
                    valid_pair_counts=counts.tolist(),
                    lead_policy='leads 1..context_steps+horizon_steps from latest valid bin')

    def _predict(self, context, grid):
        n_, h_, k_ = self._shape(context)
        quantiles = np.empty((n_, h_, k_, len(QUANTILE_LEVELS)))
        for n in range(n_):
            for k in range(k_):
                indices, values = self._support(context, n, k, self._spec.context_steps)
                gap = _gap(self, context, grid, n, indices[-1])
                increments = self._table[gap - 1:gap - 1 + h_, k]
                if not np.isfinite(increments).all():
                    raise ValueError('No training increment support for this stale-context lead')
                quantiles[n, :, k] = values[-1] + increments
        return self._store(quantiles)


def _int_tuple(value, length, label):
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise ValueError(f'{label} must be a list of {length} integers')
    return tuple(_steps(x, label, minimum=0) for x in value)


class ARIMA(_ProbabilisticBaseline):
    """Per-channel (S)ARIMA via statsmodels SARIMAX with Gaussian predictive quantiles.

    Fitted by maximum likelihood on the full regular training grid (or its
    last `fit_last_steps` grid steps when given) with invalid/absent bins as
    NaN; the Kalman filter skips them, without imputation. Trend is a constant
    only without differencing ('c'), otherwise none ('n'). Prediction filters
    each origin's context (NaN where invalid) at the fixed fitted parameters
    with a fresh default initialization, equivalent to `results.apply(context)`
    without refit, so trailing invalid bins are forecast through, not skipped.
    Quantiles are mean + se_mean * Phi^-1(level): Gaussian in log space,
    conditional on fitted parameters.
    """

    def __init__(self, order, seasonal_order=(0, 0, 0, 0), fit_last_steps=None, maxiter=200):
        self.order = _int_tuple(order, 3, 'order')
        self.seasonal_order = _int_tuple(seasonal_order, 4, 'seasonal_order')
        if any(self.seasonal_order[:3]) and self.seasonal_order[3] < 2:
            raise ValueError('Seasonal components require seasonal period >= 2')
        if not any(self.seasonal_order[:3]) and self.seasonal_order[3] != 0:
            raise ValueError('A seasonal period without seasonal components is ambiguous')
        self.fit_last_steps = None if fit_last_steps is None else _steps(fit_last_steps, 'fit_last_steps', minimum=2)
        self.maxiter = _steps(maxiter, 'maxiter')
        p, d, q = self.order
        P, D, Q, s = self.seasonal_order
        name = f'arima({p},{d},{q})' if not s else f'sarima({p},{d},{q})({P},{D},{Q},{s})'
        self.name = name + ('' if self.fit_last_steps is None else f'-last{self.fit_last_steps}')
        self._trend = 'n' if d or D else 'c'
        super().__init__()
        self._record.update(self._constructor_parameters())

    def _constructor_parameters(self):
        return dict(order=list(self.order), seasonal_order=list(self.seasonal_order),
                    fit_last_steps=self.fit_last_steps, maxiter=self.maxiter, trend=self._trend)

    def _model(self, endog):
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        seasonal = self.seasonal_order if self.seasonal_order[3] else (0, 0, 0, 0)
        return SARIMAX(endog, order=self.order, seasonal_order=seasonal, trend=self._trend)

    def _fit(self, training):
        p, d, q = self.order
        P, D, Q, s = self.seasonal_order
        minimum = p + q + P + Q + (self._trend == 'c') + 1 + d + D * s
        params, record = [], dict(params=[], param_names=[], aic=[], loglikelihood=[], converged=[],
                                  fit_grid_steps=[], valid_observation_counts=[], fit_warnings=[])
        for k in range(len(training.spec.target_names)):
            y = _grid_series(training, k)
            if self.fit_last_steps is not None:
                y = y[-self.fit_last_steps:]
            if np.isfinite(y).sum() <= minimum:
                raise ValueError('ARIMA requires more valid training observations than parameters')
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                # low_memory skips storing O(n * states^2) filter output after fitting.
                result = self._model(y).fit(disp=False, maxiter=self.maxiter, low_memory=True)
            values = _finite(np.asarray(result.params, float), 'ARIMA parameters')
            _finite(np.array([result.aic, result.llf]), 'ARIMA likelihood')
            params.append(values)
            record['params'].append(values.tolist())
            record['param_names'].append(list(result.model.param_names))
            record['aic'].append(float(result.aic))
            record['loglikelihood'].append(float(result.llf))
            record['converged'].append(bool(result.mle_retvals.get('converged', False)))
            record['fit_grid_steps'].append(len(y))
            record['valid_observation_counts'].append(int(np.isfinite(y).sum()))
            record['fit_warnings'].append(_warnings_record(caught))
        self._params = params
        return record

    def _predict(self, context, grid):
        from scipy.stats import norm
        n_, h_, k_ = self._shape(context)
        z = norm.ppf(QUANTILE_LEVELS)
        quantiles = np.empty((n_, h_, k_, len(QUANTILE_LEVELS)))
        for n in range(n_):
            for k in range(k_):
                _, _, series = _context_series(self, context, n, k)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    forecast = self._model(series).filter(self._params[k]).get_forecast(h_)
                mean = np.asarray(forecast.predicted_mean, float)
                se = np.asarray(forecast.se_mean, float)
                quantiles[n, :, k] = mean[:, None] + se[:, None] * z[None, :]
        return self._store(quantiles)


_VOL_NAMES = {'constant': 'constant', 'arch': 'arch(1)', 'garch': 'garch(1,1)', 'gjr': 'gjr-garch(1,1)'}


class Volatility(_ProbabilisticBaseline):
    """Two-stage AR(1) mean plus (G)ARCH variance for one-step log-differences.

    r_t = y_t - y_{t-1} uses adjacent valid grid pairs. Stage 1 fits the AR(1)
    mean r_t = c + phi r_{t-1} + e_t by least squares on consecutive valid
    differences. Stage 2 fits the variance process (constant, ARCH(1),
    GARCH(1,1), GJR-GARCH(1,1)) and innovation law to the residuals e_t with a
    zero-mean arch model. Joint AR-GARCH maximum likelihood was observed to
    converge to an explosive mean (|phi| > 1) on heavy-tailed flare data, so the
    stable two-stage estimator is used; every variance model therefore shares
    one mean and differs only in its predictive distribution. Residuals are
    concatenated across gaps (an approximation recorded with counts) and scaled
    by a fixed training factor (1/std of r) for optimizer conditioning.
    Prediction filters the fixed variance parameters over the context's
    residuals, simulates innovation paths, propagates them through the AR(1)
    recursion from the latest valid difference, unscales and cumulatively sums
    them onto the latest valid y. Draws are seeded from (sim_seed, issue time,
    channel) so output is independent of origin batching. Parameter
    uncertainty is not represented.
    """

    def __init__(self, vol, dist='normal', simulations=1000, sim_seed=0):
        self.vol = _category(vol, tuple(_VOL_NAMES), 'volatility process')
        self.dist = _category(dist, ('normal', 't'), 'innovation distribution')
        self.simulations = _steps(simulations, 'simulations', minimum=2)
        self.sim_seed = _steps(sim_seed, 'sim_seed', minimum=0)
        self.name = (f'ar1-{_VOL_NAMES[self.vol]}-{self.dist}'
                     + ('' if self.simulations == 1000 else f'-sim{self.simulations}')
                     + ('' if self.sim_seed == 0 else f'-seed{self.sim_seed}'))
        super().__init__()
        self._record.update(self._constructor_parameters())

    def _constructor_parameters(self):
        return dict(vol=self.vol, dist=self.dist, simulations=self.simulations, sim_seed=self.sim_seed)

    def _model(self, residuals, seed):
        from arch.univariate import ARCH, GARCH, ConstantVariance, Normal, StudentsT, ZeroMean
        volatility = {'constant': lambda: ConstantVariance(), 'arch': lambda: ARCH(p=1),
                      'garch': lambda: GARCH(p=1, o=0, q=1), 'gjr': lambda: GARCH(p=1, o=1, q=1)}[self.vol]()
        distribution = (Normal if self.dist == 'normal' else StudentsT)(seed=seed)
        return ZeroMean(residuals, volatility=volatility, distribution=distribution, rescale=False)

    def _multistart(self, residuals):
        """Maximum likelihood over arch's default start plus a fixed start grid.

        A single default SLSQP start was observed to stop near its starting
        values on these heavy-tailed residuals; the highest finite
        log-likelihood is kept and every start's outcome is recorded.
        """
        variance = float(np.var(residuals))
        grids = {'constant': [()], 'arch': [(a,) for a in (0.1, 0.5, 0.9)],
                 'garch': [(a, b) for a in (0.05, 0.15, 0.3) for b in (0.5, 0.8, 0.93) if a + b < 0.999],
                 'gjr': [(a, 0.05, b) for a in (0.05, 0.15) for b in (0.5, 0.8, 0.9)]}
        starts = [None]
        for terms in grids[self.vol]:
            persistence = sum(terms) - (terms[1] / 2 if self.vol == 'gjr' else 0)
            values = ([variance * max(1 - persistence, 0.01)] + list(terms) if self.vol != 'constant'
                      else [variance])
            starts.append(values + ([5.0] if self.dist == 't' else []))
        best, outcomes = None, []
        for start in starts:
            try:
                result = self._model(residuals, 0).fit(
                    disp='off', options=dict(maxiter=500),
                    starting_values=None if start is None else np.asarray(start, float))
                likelihood = float(result.loglikelihood)
            except (ValueError, np.linalg.LinAlgError) as error:
                outcomes.append(dict(start=start, error=str(error)))
                continue
            finite = np.isfinite(likelihood) and np.isfinite(np.asarray(result.params, float)).all()
            outcomes.append(dict(start=start, loglikelihood=likelihood if finite else None,
                                 convergence_flag=int(result.convergence_flag)))
            if finite and (best is None or likelihood > best.loglikelihood):
                best = result
        if best is None:
            raise ValueError('No variance-model start produced a finite likelihood')
        return best, outcomes

    @staticmethod
    def _differences(series):
        """Consecutive valid difference pairs (r_{t-1}, r_t) and the valid r sequence."""
        r = np.diff(series)
        pairs = np.isfinite(r[:-1]) & np.isfinite(r[1:])
        return r[:-1][pairs], r[1:][pairs], r[np.isfinite(r)]

    def _fit(self, training):
        record = dict(mean=[], params=[], param_names=[], loglikelihood=[], persistence=[], convergence_flag=[],
                      scale=[], valid_pair_counts=[], fit_warnings=[],
                      estimator='two-stage: OLS AR(1) mean, then zero-mean variance MLE on residuals',
                      pair_policy='consecutive valid differences; residuals concatenated across gaps')
        self._params, self._scales, self._means = [], [], []
        for k in range(len(training.spec.target_names)):
            lagged, current, r = self._differences(_grid_series(training, k))
            if len(current) < 10:
                raise ValueError('Volatility model requires at least 10 consecutive valid training differences')
            std = float(r.std())
            if not np.isfinite(std) or std <= 0:
                raise ValueError('Volatility model requires nonconstant training log-differences')
            scale = 1.0 / std
            x, y = lagged * scale, current * scale
            design = np.column_stack((np.ones(len(x)), x))
            const, phi = _finite(np.linalg.lstsq(design, y, rcond=None)[0], 'AR(1) mean')
            if not abs(phi) < 1:
                raise ValueError('AR(1) mean of log-differences is not stationary')
            residuals = y - const - phi * x
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                result, starts = self._multistart(residuals)
            record.setdefault('starts', []).append(starts)
            values = _finite(np.asarray(result.params, float), 'volatility parameters')
            named = dict(zip(result.params.index, values))
            _finite(np.array([result.loglikelihood]), 'volatility likelihood')
            # GJR asymmetry may be negative provided alpha + gamma >= 0.
            tolerance = -1e-8
            if (named.get('omega', 1.) <= 0 or named.get('alpha[1]', 0.) < tolerance
                    or named.get('beta[1]', 0.) < tolerance
                    or named.get('alpha[1]', 0.) + named.get('gamma[1]', 0.) < tolerance):
                raise ValueError('Variance parameters violate omega > 0, alpha, beta, alpha + gamma >= 0')
            persistence = (named.get('alpha[1]', 0.) + named.get('beta[1]', 0.)
                           + named.get('gamma[1]', 0.) / 2)
            self._params.append(values)
            self._scales.append(scale)
            self._means.append((float(const), float(phi)))
            record['mean'].append(dict(const=float(const), phi=float(phi)))
            record['params'].append(values.tolist())
            record['param_names'].append(list(result.params.index))
            record['loglikelihood'].append(float(result.loglikelihood))
            record['persistence'].append(float(persistence))
            record['convergence_flag'].append(int(result.convergence_flag))
            record['scale'].append(scale)
            record['valid_pair_counts'].append(int(len(current)))
            record['fit_warnings'].append(_warnings_record(caught))
        return record

    def _predict(self, context, grid):
        n_, h_, k_ = self._shape(context)
        quantiles = np.empty((n_, h_, k_, len(QUANTILE_LEVELS)))
        for n in range(n_):
            for k in range(k_):
                indices, values, series = _context_series(self, context, n, k)
                lagged, current, r = self._differences(series)
                if len(current) < 2:
                    raise ValueError(f'Insufficient valid context differences for origin {context.origin_ids[n]!r}')
                const, phi = self._means[k]
                scale = self._scales[k]
                residuals = (current - phi * lagged) * scale - const
                gap = _gap(self, context, grid, n, indices[-1])
                seed = np.random.default_rng([self.sim_seed, int(context.issue_times_ns[n]) % 2**64, k])
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    fixed = self._model(residuals, seed).fix(self._params[k])
                    forecast = fixed.forecast(horizon=gap - 1 + h_, method='simulation',
                                              simulations=self.simulations, reindex=False)
                shocks = np.asarray(forecast.simulations.values, float)[-1]
                state = np.full(self.simulations, r[-1] * scale)
                paths = np.empty_like(shocks)
                for step in range(shocks.shape[1]):
                    state = const + phi * state + shocks[:, step]
                    paths[:, step] = state
                levels = values[-1] + np.cumsum(paths / scale, axis=1)[:, gap - 1:]
                quantiles[n, :, k] = np.quantile(levels, QUANTILE_LEVELS, axis=0).T
        return self._store(quantiles)


_PROBABILISTIC = {'persistence_empirical': PersistenceEmpirical, 'arima': ARIMA, 'volatility': Volatility}


def make_probabilistic(name, parameters):
    """Construct one fixed probabilistic comparator; unknown names/parameters fail clearly."""
    name = _category(name, tuple(_PROBABILISTIC), 'probabilistic model name')
    if not isinstance(parameters, Mapping):
        raise ValueError('Probabilistic model parameters must be a mapping')
    try:
        parameters = _canonical_strings(parameters if isinstance(parameters, dict) else dict(parameters))
        return _PROBABILISTIC[name](**parameters)
    except TypeError as error:
        raise ValueError(f'Invalid parameters for probabilistic model {name!r}: {error}') from error
