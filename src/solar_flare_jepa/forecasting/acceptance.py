"""Opt-in classical fit acceptance: per-attempt facts, a versioned policy hook, explicit retries.

V1 `Volatility._multistart` keeps the highest finite likelihood whether or not
the optimizer converged, and V1 ARIMA forecasts from whatever the optimizer
returned. This module leaves both untouched and adds subclasses that pass
every optimizer outcome (`FitCandidate`) to a caller-supplied
`FitAcceptancePolicy`, select only among accepted outcomes, run caller-declared
retries only when nothing was accepted, and record every attempt and decision.

No acceptance threshold, start grid or retry budget is chosen here: candidates
carry threshold-free facts, decisions come from the policy (whose approval
status is recorded), and retries default to none. Volatility keeps V1's start
grid and first-pass settings unless the caller overrides them.
"""
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, runtime_checkable
import json
import math
import warnings

import numpy as np

from .baselines import _finite, _steps
from .contracts import _category, _string, canonical_json, fingerprint_payload
from .statistical import ARIMA, Volatility, _grid_series, _warnings_record

APPROVAL_STATUSES = ('PROPOSED_REQUIRES_APPROVAL', 'APPROVED', 'TEST_DOUBLE')
FAMILIES = ('arima', 'volatility')
ATTEMPT_KINDS = ('initial', 'retry')
_SETTINGS = {'arima': ('maxiter',), 'volatility': ('maxiter', 'ftol')}
# Declarative volatility start keys in arch parameter order; omega_fraction
# multiplies the training residual variance (sigma2 for constant variance).
_START_KEYS = {'constant': ('omega_fraction',), 'arch': ('omega_fraction', 'alpha'),
               'garch': ('omega_fraction', 'alpha', 'beta'), 'gjr': ('omega_fraction', 'alpha', 'gamma', 'beta')}
_FIT_ERRORS = (ValueError, np.linalg.LinAlgError)


class FitRejected(ValueError):
    """No candidate for a model/channel was accepted. `diagnostics` holds every attempt."""

    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = json.loads(canonical_json(diagnostics))


class PolicyContractError(TypeError):
    """A policy broke its contract; an infrastructure error, never a model failure."""


def _real(value, label, finite=True):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f'{label} must be a real number')
    value = float(value)
    if finite and not math.isfinite(value):
        raise ValueError(f'{label} must be finite')
    return value


def _optional(value, check):
    return None if value is None else check(value)


def _bool(value, label):
    if not isinstance(value, bool):
        raise ValueError(f'{label} must be a bool')
    return value


def _settings(value, allowed=('maxiter', 'ftol')):
    """Explicit optimizer settings; maxiter is always required."""
    if not isinstance(value, Mapping) or not value:
        raise ValueError('Optimizer settings must be a nonempty mapping')
    result = {}
    for key, part in value.items():
        if key not in allowed:
            raise ValueError(f'Unsupported optimizer setting {key!r}; allowed {allowed}')
        if key == 'maxiter':
            result[key] = _steps(part, 'maxiter')
        elif (part := _real(part, key)) <= 0:
            raise ValueError(f'{key} must be positive')
        else:
            result[key] = part
    if 'maxiter' not in result:
        raise ValueError('Optimizer settings require an explicit maxiter')
    return dict(sorted(result.items()))


def _start_spec(value):
    """None (library default), literal values, a declarative mapping, or a callable(context)."""
    if value is None or callable(value):
        return value
    if isinstance(value, Mapping):
        return MappingProxyType({_string(k, 'start key'): _real(v, f'start {k}') for k, v in value.items()})
    if isinstance(value, (list, tuple, np.ndarray)):
        return tuple(_real(v, 'start value') for v in value)
    raise ValueError('Start must be None, a sequence of numbers, a mapping or a callable')


def _describe_start(spec):
    if spec is None:
        return None
    if isinstance(spec, tuple):
        return {'values': list(spec)}
    if isinstance(spec, Mapping):
        return {'spec': dict(spec)}
    return {'callable': f'{getattr(spec, "__module__", "?")}.{getattr(spec, "__qualname__", type(spec).__qualname__)}'}


def _resolve_start(spec, context):
    if spec is None or isinstance(spec, tuple):
        return spec
    if isinstance(spec, Mapping):
        keys = _START_KEYS[context['vol']]
        values = [context['residual_variance'] * spec['omega_fraction']] + [spec[k] for k in keys[1:]]
        return tuple(values + ([spec['nu']] if context['dist'] == 't' else []))
    return tuple(_real(v, 'callable start value') for v in spec(dict(context)))


def _sanitize(value, path, flagged):
    """Non-finite floats become None, and their paths are recorded."""
    if isinstance(value, float) and not math.isfinite(value):
        flagged.append(path)
        return None
    if isinstance(value, Mapping):
        return {k: _sanitize(v, f'{path}.{k}' if path else k, flagged) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v, f'{path}[{i}]', flagged) for i, v in enumerate(value)]
    return value


def _scalar(value, label):
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (np.integer, int)):
        return int(value)
    return _real(value, label, finite=False)


@dataclass(frozen=True)
class FitCandidate:
    """One optimizer outcome with threshold-free facts; non-finite values are kept raw.

    `converged` is the library's own report (ARIMA `mle_retvals['converged']`,
    arch `optimization_result.success`); `convergence_flag` is arch's
    `convergence_flag` (None for ARIMA, whose `warnflag` is in `details`).
    `min_conditional_variance` is in the fitted (scaled) space. `slacks` are
    plain numbers such as 1 - persistence, 1 - |phi| and nu - 2.
    """
    family: str
    model: str
    channel: int
    attempt_kind: str
    attempt_index: int
    start: tuple | None
    settings: Mapping
    converged: bool | None
    convergence_flag: int | None
    loglikelihood: float | None
    parameters: Mapping
    min_conditional_variance: float | None = None
    variance_positive_finite: bool | None = None
    persistence: float | None = None
    slacks: Mapping = field(default_factory=dict)
    ar_root_min_modulus: float | None = None
    ma_root_min_modulus: float | None = None
    details: Mapping = field(default_factory=dict)
    warnings: tuple = ()
    error: str | None = None

    def __post_init__(self):
        number = lambda label: lambda v: _real(v, label, finite=False)
        values = dict(
            family=_category(self.family, FAMILIES, 'model family'),
            model=_string(self.model, 'model name'),
            channel=_steps(self.channel, 'channel', minimum=0),
            attempt_kind=_category(self.attempt_kind, ATTEMPT_KINDS, 'attempt kind'),
            attempt_index=_steps(self.attempt_index, 'attempt index', minimum=0),
            start=_optional(self.start, lambda s: tuple(_real(v, 'start value', finite=False) for v in s)),
            settings=MappingProxyType(_settings(self.settings)),
            converged=_optional(self.converged, lambda v: _bool(v, 'converged')),
            convergence_flag=_optional(self.convergence_flag, lambda v: _steps(v, 'convergence flag', minimum=-2**31)),
            loglikelihood=_optional(self.loglikelihood, number('loglikelihood')),
            parameters=MappingProxyType({_string(k, 'parameter name'): _real(v, k, finite=False)
                                         for k, v in self.parameters.items()}),
            min_conditional_variance=_optional(self.min_conditional_variance, number('conditional variance')),
            variance_positive_finite=_optional(self.variance_positive_finite,
                                               lambda v: _bool(v, 'variance_positive_finite')),
            persistence=_optional(self.persistence, number('persistence')),
            slacks=MappingProxyType({_string(k, 'slack name'): _real(v, k, finite=False)
                                     for k, v in self.slacks.items()}),
            ar_root_min_modulus=_optional(self.ar_root_min_modulus, number('AR root modulus')),
            ma_root_min_modulus=_optional(self.ma_root_min_modulus, number('MA root modulus')),
            details=MappingProxyType({_string(k, 'detail name'): _scalar(v, k) for k, v in self.details.items()}),
            warnings=tuple(_string(w, 'warning') for w in self.warnings),
            error=_optional(self.error, lambda v: _string(v, 'error')))
        if values['error'] is not None and (values['parameters'] or values['loglikelihood'] is not None):
            raise ValueError('A failed attempt cannot carry fitted parameters or likelihood')
        for key, value in values.items():
            object.__setattr__(self, key, value)

    @property
    def likelihood_finite(self):
        return self.loglikelihood is not None and math.isfinite(self.loglikelihood)

    @property
    def all_parameters_finite(self):
        return bool(self.parameters) and all(math.isfinite(v) for v in self.parameters.values())

    def as_dict(self):
        """Canonical-JSON-safe record; `nonfinite_fields` lists every value nulled here."""
        raw = dict(family=self.family, model=self.model, channel=self.channel, attempt_kind=self.attempt_kind,
                   attempt_index=self.attempt_index, start=None if self.start is None else list(self.start),
                   settings=dict(self.settings), converged=self.converged, convergence_flag=self.convergence_flag,
                   loglikelihood=self.loglikelihood, parameters=dict(self.parameters),
                   min_conditional_variance=self.min_conditional_variance,
                   variance_positive_finite=self.variance_positive_finite, persistence=self.persistence,
                   slacks=dict(self.slacks), ar_root_min_modulus=self.ar_root_min_modulus,
                   ma_root_min_modulus=self.ma_root_min_modulus, details=dict(self.details),
                   warnings=list(self.warnings), error=self.error)
        flagged = []
        record = _sanitize(raw, '', flagged)
        record.update(likelihood_finite=self.likelihood_finite, all_parameters_finite=self.all_parameters_finite,
                      nonfinite_fields=sorted(flagged))
        return record


@dataclass(frozen=True)
class AcceptanceDecision:
    """A policy verdict; a rejection must state at least one reason."""
    accepted: bool
    reasons: tuple
    policy_id: str
    policy_version: str

    def __post_init__(self):
        _bool(self.accepted, 'accepted')
        if isinstance(self.reasons, str) or not isinstance(self.reasons, (list, tuple)):
            raise ValueError('Decision reasons must be a sequence of strings')
        object.__setattr__(self, 'reasons', tuple(_string(r, 'decision reason') for r in self.reasons))
        if not self.accepted and not self.reasons:
            raise ValueError('A rejection requires at least one reason')
        object.__setattr__(self, 'policy_id', _string(self.policy_id, 'policy_id'))
        object.__setattr__(self, 'policy_version', _string(self.policy_version, 'policy_version'))

    def as_dict(self):
        return dict(accepted=self.accepted, reasons=list(self.reasons), policy_id=self.policy_id,
                    policy_version=self.policy_version)


@runtime_checkable
class FitAcceptancePolicy(Protocol):
    """Versioned acceptance oracle. Optional `parameters` (JSON mapping) enter its fingerprint."""
    policy_id: str
    policy_version: str
    approval_status: str

    def evaluate(self, candidate: FitCandidate) -> AcceptanceDecision: ...


def policy_identity(policy):
    """Validated identity; the fingerprint covers id, version and declared parameters."""
    if not callable(getattr(policy, 'evaluate', None)):
        raise ValueError('Acceptance policy requires an evaluate(candidate) method')
    core = dict(policy_id=_string(getattr(policy, 'policy_id', None), 'policy_id'),
                policy_version=_string(getattr(policy, 'policy_version', None), 'policy_version'))
    try:
        core['parameters'] = json.loads(canonical_json(getattr(policy, 'parameters', None)))
    except (TypeError, ValueError) as error:
        raise ValueError(f'Policy parameters must be canonical JSON: {error}') from error
    status = _category(getattr(policy, 'approval_status', None), APPROVAL_STATUSES, 'policy approval status')
    return dict(core, approval_status=status, policy_class=f'{type(policy).__module__}.{type(policy).__qualname__}',
                fingerprint=fingerprint_payload(core))


def evaluate_candidate(policy, candidate, identity=None):
    """Call the policy once and validate its decision type and declared identity."""
    if not isinstance(candidate, FitCandidate):
        raise TypeError('evaluate_candidate requires a FitCandidate')
    identity = policy_identity(policy) if identity is None else identity
    decision = policy.evaluate(candidate)
    if type(decision) is not AcceptanceDecision:
        raise PolicyContractError(f'Policy returned {type(decision).__name__}, not AcceptanceDecision')
    if (decision.policy_id, decision.policy_version) != (identity['policy_id'], identity['policy_version']):
        raise PolicyContractError('Decision policy id/version differs from the evaluating policy')
    return decision


@dataclass(frozen=True)
class RetryAttempt:
    """One explicit retry: optimizer settings plus a start (None = library default)."""
    settings: Mapping
    start: object = None

    def __post_init__(self):
        object.__setattr__(self, 'settings', MappingProxyType(_settings(self.settings)))
        object.__setattr__(self, 'start', _start_spec(self.start))

    def as_dict(self):
        return dict(settings=dict(self.settings), start=_describe_start(self.start))


@dataclass(frozen=True)
class RetryBudget:
    """Ordered retries run only when no initial attempt is accepted; none by default."""
    attempts: tuple = ()

    def __post_init__(self):
        attempts = tuple(self.attempts)
        if not all(isinstance(a, RetryAttempt) for a in attempts):
            raise ValueError('RetryBudget attempts must be RetryAttempt instances')
        object.__setattr__(self, 'attempts', attempts)

    def as_dict(self):
        return {'attempts': [a.as_dict() for a in self.attempts]}


def _check_family(family, settings, starts, vol=None, dist=None):
    for s in settings:
        _settings(s, _SETTINGS[family])
    for spec in starts:
        if family == 'arima' and isinstance(spec, Mapping):
            raise ValueError('ARIMA starts must be None, literal values or a callable')
        if family == 'volatility' and isinstance(spec, Mapping):
            keys = set(_START_KEYS[vol]) | ({'nu'} if dist == 't' else set())
            if set(spec) != keys:
                raise ValueError(f'Declarative {vol}/{dist} start requires exactly the keys {sorted(keys)}')
        if family == 'volatility' and isinstance(spec, tuple):
            if len(spec) != len(_START_KEYS[vol]) + (dist == 't'):
                raise ValueError(f'Literal {vol}/{dist} start has the wrong number of values')


def _v1_starts(vol, dist, variance):
    """V1 `Volatility._multistart` default + fixed start grid, reproduced verbatim (parity-tested)."""
    grids = {'constant': [()], 'arch': [(a,) for a in (0.1, 0.5, 0.9)],
             'garch': [(a, b) for a in (0.05, 0.15, 0.3) for b in (0.5, 0.8, 0.93) if a + b < 0.999],
             'gjr': [(a, 0.05, b) for a in (0.05, 0.15) for b in (0.5, 0.8, 0.9)]}
    starts = [None]
    for terms in grids[vol]:
        persistence = sum(terms) - (terms[1] / 2 if vol == 'gjr' else 0)
        values = [variance * max(1 - persistence, 0.01)] + list(terms) if vol != 'constant' else [variance]
        starts.append(values + ([5.0] if dist == 't' else []))
    return starts


class _Accepted:
    """Shared policy/retry bookkeeping for accepted-fit subclasses."""
    _family = ''

    def _setup(self, policy, retry_budget):
        self.policy = policy
        self._policy_identity = policy_identity(policy)
        if retry_budget is None:
            retry_budget = RetryBudget()
        if not isinstance(retry_budget, RetryBudget):
            raise ValueError('retry_budget must be a RetryBudget')
        self.retry_budget = retry_budget

    def _rename(self, base):
        identity = {k: v for k, v in self._constructor_parameters().items()
                    if k in ('retry_budget', 'start_grid', 'initial_settings')}
        identity['policy'] = self._policy_identity['fingerprint']
        self.name = f'accepted-{base}-{fingerprint_payload(identity)[:12]}'
        self._record = dict(name=self.name, **self._constructor_parameters())

    def _accepted_parameters(self):
        return dict(acceptance_policy=dict(self._policy_identity), retry_budget=self.retry_budget.as_dict())

    def _judge(self, candidate, result, entries):
        decision = evaluate_candidate(self.policy, candidate, self._policy_identity)
        selectable = (decision.accepted and candidate.error is None and candidate.likelihood_finite
                      and candidate.all_parameters_finite)
        entries.append(dict(candidate=candidate.as_dict(), decision=decision.as_dict(),
                            selectable=selectable, selected=False))
        return (candidate.loglikelihood, result) if selectable else None

    def _attempts(self, run, entries, initial):
        """Run initial attempts, then retries in order until one is selectable; return best index."""
        options = [(i, run('initial', i, settings, start)) for i, (settings, start) in enumerate(initial)]
        retries = 0
        for j, attempt in enumerate(self.retry_budget.attempts):
            if any(o for _, o in options):
                break
            retries += 1
            options.append((len(options), run('retry', j, dict(attempt.settings), attempt.start)))
        best = None
        for index, option in options:
            if option and (best is None or option[0] > options[best][1][0]):
                best = index
        return best, options, retries

    def _reject(self, channel, entries, **extra):
        policy = self._policy_identity
        raise FitRejected(f'No accepted {self._family} fit for channel {channel} under policy '
                          f'{policy["policy_id"]}@{policy["policy_version"]} ({len(entries)} candidates)',
                          dict(family=self._family, model=self.name, channel=channel, policy=policy,
                               retry_budget=self.retry_budget.as_dict(), candidates=entries, **extra))


class AcceptedVolatility(_Accepted, Volatility):
    """V1 two-stage AR(1)+(G)ARCH whose multistart selects only policy-accepted starts.

    Every start (V1 grid unless `start_grid` is given; settings V1's maxiter=500
    unless `initial_settings` is given) is fitted, recorded and judged; the
    highest likelihood among accepted, finite outcomes is kept (first on ties,
    as V1). Retries run in order only when nothing was accepted and stop at the
    first accepted one. V1's post-selection sign check still applies.
    """
    _family = 'volatility'

    def __init__(self, vol, dist='normal', simulations=1000, sim_seed=0, *, policy, retry_budget=None,
                 start_grid=None, initial_settings=None):
        self._setup(policy, retry_budget)
        self.start_grid = None if start_grid is None else tuple(_start_spec(s) for s in start_grid)
        self.initial_settings = _settings({'maxiter': 500} if initial_settings is None else initial_settings,
                                          _SETTINGS['volatility'])
        super().__init__(vol, dist, simulations, sim_seed)
        _check_family('volatility', [a.settings for a in self.retry_budget.attempts],
                      [a.start for a in self.retry_budget.attempts] + list(self.start_grid or ()), self.vol, self.dist)
        self._rename(self.name)

    def _constructor_parameters(self):
        grid = 'v1_default_plus_fixed_grid' if self.start_grid is None else [_describe_start(s) for s in self.start_grid]
        return dict(super()._constructor_parameters(), **self._accepted_parameters(), start_grid=grid,
                    initial_settings=dict(self.initial_settings))

    def _prefit(self, training, k):
        """V1's stage-1 mean, recomputed only to bind channel facts (verified against V1 after fit)."""
        lagged, current, r = self._differences(_grid_series(training, k))
        std = float(r.std()) if len(r) else math.nan
        if len(current) < 10 or not np.isfinite(std) or std <= 0:
            return None
        x, y = lagged * (1.0 / std), current * (1.0 / std)
        const, phi = np.linalg.lstsq(np.column_stack((np.ones(len(x)), x)), y, rcond=None)[0]
        return float(phi), y - const - phi * x

    def _fit(self, training):
        self._channels = [self._prefit(training, k) for k in range(len(training.spec.target_names))]
        self._acceptance = []
        record = super()._fit(training)
        if (len(self._acceptance) != len(record['mean'])
                or any(m['phi'] != c[0] for m, c in zip(record['mean'], self._channels))):
            raise RuntimeError('Accepted-fit channel facts differ from the V1 fit')
        record['acceptance'] = self._acceptance
        return record

    def _candidate(self, k, kind, index, start, settings, phi, result, error, caught):
        common = dict(family='volatility', model=self.name, channel=k, attempt_kind=kind, attempt_index=index,
                      start=start, settings=settings, warnings=_warnings_record(caught))
        slacks = {'mean_phi': 1 - abs(phi)}
        if result is None:
            return FitCandidate(**common, converged=None, convergence_flag=None, loglikelihood=None,
                                parameters={}, slacks=slacks, error=error)
        params = dict(zip(map(str, result.params.index), np.asarray(result.params, float).tolist()))
        persistence = params.get('alpha[1]', 0.) + params.get('beta[1]', 0.) + params.get('gamma[1]', 0.) / 2
        slacks['persistence'] = 1 - persistence
        if 'nu' in params:
            slacks['nu_minus_2'] = params['nu'] - 2
        if 'gamma[1]' in params:
            slacks['alpha_plus_gamma'] = params['alpha[1]'] + params['gamma[1]']
        with np.errstate(over='ignore', invalid='ignore'):
            variance = np.asarray(result.conditional_volatility, float) ** 2
        optimum = getattr(result, 'optimization_result', None)
        details = {} if optimum is None else dict(optimizer_message=str(optimum.get('message', '')),
                                                  optimizer_iterations=optimum.get('nit'))
        return FitCandidate(**common, converged=None if optimum is None else bool(optimum.success),
                            convergence_flag=int(result.convergence_flag),
                            loglikelihood=float(result.loglikelihood), parameters=params,
                            min_conditional_variance=float(np.min(variance)) if variance.size else None,
                            variance_positive_finite=bool(variance.size and np.isfinite(variance).all()
                                                          and (variance > 0).all()),
                            persistence=persistence, slacks=slacks, details=details)

    def _multistart(self, residuals):
        k = len(self._acceptance)
        channel = self._channels[k] if k < len(self._channels) else None
        if channel is None or not np.array_equal(channel[1], residuals):
            raise RuntimeError('Accepted volatility fit could not bind residuals to a channel')
        phi, variance = channel[0], float(np.var(residuals))
        context = dict(family='volatility', channel=k, vol=self.vol, dist=self.dist, residual_variance=variance)
        starts = (_v1_starts(self.vol, self.dist, variance) if self.start_grid is None
                  else [_resolve_start(s, context) for s in self.start_grid])
        entries = []

        def run(kind, index, settings, spec):
            start = _resolve_start(_start_spec(spec), context)
            result = error = None
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                try:
                    result = self._model(residuals, 0).fit(
                        disp='off', options=dict(settings),
                        starting_values=None if start is None else np.asarray(start, float))
                except _FIT_ERRORS as exc:
                    error = f'{type(exc).__name__}: {exc}'
            for w in caught:  # Keep V1's channel-level fit_warnings complete.
                warnings.warn_explicit(w.message, w.category, w.filename, w.lineno)
            candidate = self._candidate(k, kind, index, start, settings, phi, result, error, caught)
            return self._judge(candidate, result, entries)

        best, options, retries = self._attempts(run, entries, [(self.initial_settings, s) for s in starts])
        if best is None:
            self._reject(k, entries, residual_variance=variance)
        entries[best]['selected'] = True
        self._acceptance.append(dict(channel=k, selected=best, initial_candidates=len(starts),
                                     retry_attempts_run=retries, residual_variance=variance))
        return options[best][1][1], entries


def _min_modulus(result, attribute):
    try:
        roots = np.asarray(getattr(result, attribute), complex)
    except (AttributeError, ValueError, np.linalg.LinAlgError):
        return None
    return float(np.abs(roots).min()) if roots.size else None


class AcceptedARIMA(_Accepted, ARIMA):
    """V1 per-channel (S)ARIMA whose forecasts use only a policy-accepted fit.

    Each channel is fitted once with `maxiter` (V1's call), judged, then retried
    in budget order until one attempt is accepted; an all-rejected channel
    raises FitRejected. Every attempt is recorded under `candidates`.
    """
    _family = 'arima'

    def __init__(self, order, seasonal_order=(0, 0, 0, 0), fit_last_steps=None, maxiter=200, *, policy,
                 retry_budget=None):
        self._setup(policy, retry_budget)
        super().__init__(order, seasonal_order, fit_last_steps, maxiter)
        _check_family('arima', [a.settings for a in self.retry_budget.attempts],
                      [a.start for a in self.retry_budget.attempts])
        self._rename(self.name)

    def _constructor_parameters(self):
        return dict(super()._constructor_parameters(), **self._accepted_parameters(),
                    initial_settings={'maxiter': self.maxiter})

    def _candidate(self, k, kind, index, start, settings, result, error, caught):
        common = dict(family='arima', model=self.name, channel=k, attempt_kind=kind, attempt_index=index,
                      start=start, settings=settings, convergence_flag=None, warnings=_warnings_record(caught))
        if result is None:
            return FitCandidate(**common, converged=None, loglikelihood=None, parameters={}, error=error)
        params = dict(zip(result.model.param_names, np.asarray(result.params, float).tolist()))
        retvals = result.mle_retvals or {}
        sigma2 = params.get('sigma2')
        return FitCandidate(**common, converged=bool(retvals.get('converged', False)),
                            loglikelihood=float(result.llf), parameters=params,
                            variance_positive_finite=None if sigma2 is None else bool(math.isfinite(sigma2) and sigma2 > 0),
                            ar_root_min_modulus=_min_modulus(result, 'arroots'),
                            ma_root_min_modulus=_min_modulus(result, 'maroots'),
                            details=dict(aic=float(result.aic), iterations=retvals.get('iterations'),
                                         fcalls=retvals.get('fcalls'), warnflag=retvals.get('warnflag')))

    def _fit(self, training):
        p, d, q = self.order
        P, D, Q, s = self.seasonal_order
        minimum = p + q + P + Q + (self._trend == 'c') + 1 + d + D * s
        params, record = [], dict(params=[], param_names=[], aic=[], loglikelihood=[], converged=[],
                                  fit_grid_steps=[], valid_observation_counts=[], fit_warnings=[],
                                  candidates=[], acceptance=[])
        for k in range(len(training.spec.target_names)):
            y = _grid_series(training, k)
            if self.fit_last_steps is not None:
                y = y[-self.fit_last_steps:]
            if np.isfinite(y).sum() <= minimum:
                raise ValueError('ARIMA requires more valid training observations than parameters')
            context = dict(family='arima', channel=k, series=y.copy())
            entries = []

            def run(kind, index, settings, spec):
                start = _resolve_start(_start_spec(spec), context)
                result = error = None
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    try:
                        result = self._model(y).fit(disp=False, maxiter=settings['maxiter'], low_memory=True,
                                                    **({} if start is None else {'start_params': np.asarray(start)}))
                    except _FIT_ERRORS as exc:
                        error = f'{type(exc).__name__}: {exc}'
                return self._judge(self._candidate(k, kind, index, start, settings, result, error, caught),
                                   result, entries)

            best, options, retries = self._attempts(run, entries, [({'maxiter': self.maxiter}, None)])
            if best is None:
                self._reject(k, entries)
            entries[best]['selected'] = True
            result = options[best][1][1]
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
            record['fit_warnings'].append(entries[best]['candidate']['warnings'])
            record['candidates'].append(entries)
            record['acceptance'].append(dict(channel=k, selected=best, initial_candidates=1,
                                             retry_attempts_run=retries))
        self._params = params
        return record
