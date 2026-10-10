"""Classical fit-acceptance integration layer: contracts, opt-in accepted fits, test doubles.

Every policy here is a TEST DOUBLE. No scientific acceptance threshold is
chosen or tested; the oracle and its thresholds are owned elsewhere.
"""
from pathlib import Path
import json
import math
import subprocess
import sys

import numpy as np
import pytest

from test_statistical import TRAIN, WINDOWS, context_grid
from solar_flare_jepa.forecasting import statistical
from solar_flare_jepa.forecasting.acceptance import (
    APPROVAL_STATUSES, AcceptanceDecision, AcceptedARIMA, AcceptedVolatility, FitCandidate,
    FitRejected, PolicyContractError, RetryAttempt, RetryBudget, evaluate_candidate, policy_identity,
)
from solar_flare_jepa.forecasting.contracts import canonical_json
from solar_flare_jepa.forecasting.statistical import ARIMA, Volatility

ROOT = Path(__file__).resolve().parents[1]


class _Double:
    policy_version = '0-test'
    approval_status = 'TEST_DOUBLE'

    def __init__(self, policy_id, rule, parameters=None):
        self.policy_id, self.rule, self.calls = policy_id, rule, []
        if parameters is not None:
            self.parameters = parameters

    def evaluate(self, candidate):
        self.calls.append(candidate)
        reasons = self.rule(candidate)
        return AcceptanceDecision(not reasons, tuple(reasons), self.policy_id, self.policy_version)


def accept_all():
    return _Double('accept-all', lambda c: [])


def accept_all_finite():
    return _Double('accept-all-finite', lambda c: [] if c.likelihood_finite and c.all_parameters_finite
                   else ['nonfinite'])


def reject_all():
    return _Double('reject-all', lambda c: ['scripted rejection'])


def scripted(rejected):
    """Reject (channel, attempt_kind, attempt_index) keys listed in `rejected`."""
    return _Double('scripted', lambda c: ['scripted'] if (c.channel, c.attempt_kind, c.attempt_index) in rejected
                   else [])


def converged_only():
    return _Double('converged-only', lambda c: [] if c.converged and c.likelihood_finite and c.all_parameters_finite
                   else [f'not converged (flag={c.convergence_flag}, converged={c.converged})'])


def retry_only():
    return _Double('retry-only', lambda c: [] if c.attempt_kind == 'retry' else ['initial attempts rejected'])


def _predict(m):
    return m.predict(*context_grid(WINDOWS)).quantiles


VOL = dict(vol='arch', dist='normal', simulations=200)


@pytest.fixture(scope='module')
def v1_vol():
    return Volatility(**VOL).fit(TRAIN)


@pytest.fixture(scope='module')
def v1_arima():
    return ARIMA([1, 0, 0]).fit(TRAIN)


# ---------------------------------------------------------------- V1 invariance

def test_v1_classes_and_registry_are_untouched_by_import():
    assert Volatility.__dict__['_multistart'].__module__ == statistical.__name__
    assert Volatility.__dict__['_multistart'].__qualname__ == 'Volatility._multistart'
    assert ARIMA.__dict__['_fit'].__qualname__ == 'ARIMA._fit'
    assert sorted(statistical._PROBABILISTIC) == ['arima', 'persistence_empirical', 'volatility']
    assert statistical._PROBABILISTIC['volatility'] is Volatility


def test_v1_records_and_predictions_identical_without_acceptance_module(v1_vol, v1_arima):
    script = (
        "import sys; sys.path[:0] = ['src', 'tests']\n"
        "from test_statistical import TRAIN, WINDOWS, context_grid\n"
        "from solar_flare_jepa.forecasting.statistical import ARIMA, Volatility\n"
        "from solar_flare_jepa.forecasting.contracts import canonical_json\n"
        "out = {}\n"
        f"for key, m in (('vol', Volatility(**{VOL!r})), ('arima', ARIMA([1, 0, 0]))):\n"
        "    m.fit(TRAIN)\n"
        "    out[key] = dict(record=m.parameters, quantiles=m.predict(*context_grid(WINDOWS)).quantiles.tolist())\n"
        "assert 'solar_flare_jepa.forecasting.acceptance' not in sys.modules\n"
        "print(canonical_json(out))\n")
    done = subprocess.run([sys.executable, '-c', script], cwd=ROOT, capture_output=True, text=True, check=True)
    before = json.loads(done.stdout)
    for key, m in (('vol', v1_vol), ('arima', v1_arima)):
        assert json.loads(canonical_json(m.parameters)) == before[key]['record']
        assert _predict(m).tolist() == before[key]['quantiles']


def test_accept_all_finite_reproduces_v1_volatility_selection_and_predictions(v1_vol):
    policy = accept_all_finite()
    m = AcceptedVolatility(**VOL, policy=policy).fit(TRAIN)
    v1, rec = v1_vol.parameters, m.parameters
    for key in ('params', 'param_names', 'loglikelihood', 'convergence_flag', 'persistence', 'mean', 'scale',
                'fit_warnings', 'valid_pair_counts'):
        assert rec[key] == v1[key]
    # Same V1 default+fixed start grid, same per-start outcomes.
    for v1_starts, entries in zip(v1['starts'], rec['starts']):
        assert [s['start'] for s in v1_starts] == [e['candidate']['start'] for e in entries]
        assert [s.get('loglikelihood') for s in v1_starts] == [e['candidate']['loglikelihood'] for e in entries]
    np.testing.assert_array_equal(_predict(m), _predict(v1_vol))
    assert len(policy.calls) == sum(len(s) for s in v1['starts'])


def test_accept_all_reproduces_v1_arima(v1_arima):
    m = AcceptedARIMA([1, 0, 0], policy=accept_all()).fit(TRAIN)
    for key in ('params', 'param_names', 'aic', 'loglikelihood', 'converged', 'fit_grid_steps',
                'valid_observation_counts', 'fit_warnings'):
        assert m.parameters[key] == v1_arima.parameters[key]
    np.testing.assert_array_equal(_predict(m), _predict(v1_arima))


def test_accepted_names_never_collide_with_v1_and_encode_policy():
    a = AcceptedVolatility(**VOL, policy=accept_all())
    b = AcceptedVolatility(**VOL, policy=reject_all())
    c = AcceptedVolatility(**VOL, policy=accept_all(), retry_budget=RetryBudget([RetryAttempt({'maxiter': 9})]))
    v1 = Volatility(**VOL).name
    assert a.name.startswith('accepted-') and v1 in a.name and a.name != v1
    assert len({a.name, b.name, c.name}) == 3
    assert AcceptedARIMA([1, 0, 0], policy=accept_all()).name.startswith('accepted-arima(1,0,0)')


# ---------------------------------------------------------------- selection semantics

def test_policy_called_once_per_candidate_and_identity_recorded():
    policy = accept_all_finite()
    m = AcceptedVolatility(**VOL, policy=policy).fit(TRAIN)
    rec = m.parameters
    entries = [e for channel in rec['starts'] for e in channel]
    assert len(policy.calls) == len(entries) == 2 * 4
    assert len({id(c) for c in policy.calls}) == len(policy.calls)
    identity = rec['acceptance_policy']
    assert identity['policy_id'] == 'accept-all-finite' and identity['policy_version'] == '0-test'
    assert identity['approval_status'] == 'TEST_DOUBLE' and len(identity['fingerprint']) == 64
    assert identity == policy_identity(policy)
    for e in entries:
        assert e['decision']['policy_id'] == 'accept-all-finite' and e['decision']['policy_version'] == '0-test'
        assert e['candidate']['attempt_kind'] == 'initial' and e['candidate']['settings'] == {'maxiter': 500}
    assert [s['selected'] for s in rec['acceptance']] == [
        next(i for i, e in enumerate(ch) if e['selected']) for ch in rec['starts']]
    canonical_json(rec)


def test_rejected_higher_likelihood_start_is_never_selected(v1_vol):
    v1 = v1_vol.parameters
    best = [int(np.nanargmax([np.nan if s.get('loglikelihood') is None else s['loglikelihood'] for s in ch]))
            for ch in v1['starts']]
    m = AcceptedVolatility(**VOL, policy=scripted({(k, 'initial', i) for k, i in enumerate(best)})).fit(TRAIN)
    rec = m.parameters
    for k, entries in enumerate(rec['starts']):
        chosen = [e for e in entries if e['selected']]
        assert len(chosen) == 1 and chosen[0]['decision']['accepted'] and chosen[0]['candidate']['attempt_index'] != best[k]
        assert not entries[best[k]]['decision']['accepted'] and not entries[best[k]]['selected']
        accepted = [e['candidate']['loglikelihood'] for e in entries if e['decision']['accepted']]
        assert rec['loglikelihood'][k] == max(accepted) <= v1['loglikelihood'][k]


def test_all_rejected_raises_fit_rejected_with_every_candidate():
    with pytest.raises(FitRejected) as caught:
        AcceptedVolatility(**VOL, policy=reject_all()).fit(TRAIN)
    error = caught.value
    assert isinstance(error, ValueError)
    d = error.diagnostics
    assert d['channel'] == 0 and d['family'] == 'volatility' and d['policy']['policy_id'] == 'reject-all'
    assert len(d['candidates']) == 4 and all(not e['decision']['accepted'] for e in d['candidates'])
    assert all(e['decision']['reasons'] == ['scripted rejection'] for e in d['candidates'])
    json.loads(canonical_json(d))


def test_retries_run_only_when_needed_bounded_and_recorded():
    budget = RetryBudget([RetryAttempt({'maxiter': 2000, 'ftol': 1e-10},
                                       {'omega_fraction': 0.9, 'alpha': 0.1}),
                          RetryAttempt({'maxiter': 300})])
    # Not needed: no retry candidate exists.
    calls = accept_all_finite()
    rec = AcceptedVolatility(**VOL, policy=calls, retry_budget=budget).fit(TRAIN).parameters
    assert all(e['candidate']['attempt_kind'] == 'initial' for ch in rec['starts'] for e in ch)
    assert rec['retry_budget'] == budget.as_dict()
    # Needed and bounded: reject-all runs exactly the budget, in order, then fails.
    with pytest.raises(FitRejected) as caught:
        AcceptedVolatility(**VOL, policy=reject_all(), retry_budget=budget).fit(TRAIN)
    retries = [e['candidate'] for e in caught.value.diagnostics['candidates'] if e['candidate']['attempt_kind'] == 'retry']
    assert [r['attempt_index'] for r in retries] == [0, 1]
    assert [r['settings'] for r in retries] == [{'ftol': 1e-10, 'maxiter': 2000}, {'maxiter': 300}]
    assert retries[1]['start'] is None
    residual_variance = caught.value.diagnostics['residual_variance']
    assert retries[0]['start'] == pytest.approx([0.9 * residual_variance, 0.1])
    # Retries stop at the first accepted retry.
    policy = retry_only()
    rec = AcceptedVolatility(**VOL, policy=policy, retry_budget=budget).fit(TRAIN).parameters
    for ch in rec['starts']:
        assert [e['candidate']['attempt_kind'] for e in ch] == ['initial'] * 4 + ['retry']
        assert ch[-1]['selected']
    assert [s['retry_attempts_run'] for s in rec['acceptance']] == [1, 1]


def test_nonconverged_start_is_recorded_and_rejected_by_converged_only_double():
    vol = dict(vol='garch', dist='normal', simulations=200)
    with pytest.raises(FitRejected) as caught:
        AcceptedVolatility(**vol, policy=converged_only(), initial_settings={'maxiter': 1}).fit(TRAIN)
    entries = caught.value.diagnostics['candidates']
    assert all(e['candidate']['settings'] == {'maxiter': 1} for e in entries)
    assert any(e['candidate']['convergence_flag'] not in (None, 0) and e['candidate']['converged'] is False
               and e['candidate']['likelihood_finite'] and not e['decision']['accepted'] for e in entries)
    # A recorded interior retry with a larger budget is used only after rejection.
    budget = RetryBudget([RetryAttempt({'maxiter': 2000, 'ftol': 1e-10},
                                       lambda context: [0.15 * context['residual_variance'], 0.05, 0.8])])
    m = AcceptedVolatility(**vol, policy=converged_only(), initial_settings={'maxiter': 1},
                           retry_budget=budget).fit(TRAIN)
    rec = m.parameters
    for k, ch in enumerate(rec['starts']):
        assert ch[-1]['candidate']['attempt_kind'] == 'retry' and ch[-1]['selected']
        assert ch[-1]['candidate']['convergence_flag'] == 0 == rec['convergence_flag'][k]
        assert rec['loglikelihood'][k] == ch[-1]['candidate']['loglikelihood']
    assert 'callable' in rec['retry_budget']['attempts'][0]['start']
    assert np.isfinite(_predict(m)).all()
    canonical_json(rec)


def test_candidate_diagnostics_are_factual():
    rec = AcceptedVolatility(vol='gjr', dist='t', simulations=200, policy=accept_all_finite()).fit(TRAIN).parameters
    for k, ch in enumerate(rec['starts']):
        for e in ch:
            c = e['candidate']
            if c['error'] is not None:
                continue
            p = c['parameters']
            persistence = p['alpha[1]'] + p['beta[1]'] + p['gamma[1]'] / 2
            assert c['persistence'] == pytest.approx(persistence)
            assert c['slacks']['persistence'] == pytest.approx(1 - persistence)
            assert c['slacks']['nu_minus_2'] == pytest.approx(p['nu'] - 2)
            assert c['slacks']['alpha_plus_gamma'] == pytest.approx(p['alpha[1]'] + p['gamma[1]'])
            assert c['slacks']['mean_phi'] == pytest.approx(1 - abs(rec['mean'][k]['phi']))
            assert c['min_conditional_variance'] > 0 and c['variance_positive_finite']
            assert c['family'] == 'volatility' and c['model'].startswith('accepted-') and c['channel'] == k
            assert isinstance(c['warnings'], list)


# ---------------------------------------------------------------- ARIMA

def test_arima_retry_path_uses_accepted_parameters_only():
    reference = ARIMA([1, 0, 1]).fit(TRAIN)
    m = AcceptedARIMA([1, 0, 1], maxiter=1, policy=converged_only(),
                      retry_budget=RetryBudget([RetryAttempt({'maxiter': 200})])).fit(TRAIN)
    rec = m.parameters
    for k, ch in enumerate(rec['candidates']):
        first, retry = ch
        assert first['candidate']['attempt_kind'] == 'initial' and first['candidate']['settings'] == {'maxiter': 1}
        assert first['candidate']['converged'] is False and not first['decision']['accepted'] and not first['selected']
        assert retry['candidate']['attempt_kind'] == 'retry' and retry['selected'] and retry['candidate']['converged']
        assert retry['candidate']['ar_root_min_modulus'] > 0 and retry['candidate']['ma_root_min_modulus'] > 0
        assert rec['params'][k] == reference.parameters['params'][k] == list(retry['candidate']['parameters'].values())
    np.testing.assert_array_equal(_predict(m), _predict(reference))
    canonical_json(rec)


def test_arima_all_rejected_raises_with_candidates():
    with pytest.raises(FitRejected) as caught:
        AcceptedARIMA([1, 0, 0], maxiter=1, policy=reject_all(),
                      retry_budget=RetryBudget([RetryAttempt({'maxiter': 5})])).fit(TRAIN)
    d = caught.value.diagnostics
    assert d['family'] == 'arima' and [e['candidate']['attempt_kind'] for e in d['candidates']] == ['initial', 'retry']
    json.loads(canonical_json(d))


# ---------------------------------------------------------------- contracts

def _candidate(**changes):
    values = dict(family='volatility', model='m', channel=0, attempt_kind='initial', attempt_index=0, start=None,
                  settings={'maxiter': 1}, converged=True, convergence_flag=0, loglikelihood=-1.0,
                  parameters={'omega': 0.5}, min_conditional_variance=0.25, variance_positive_finite=True,
                  persistence=0.0, slacks={'persistence': 1.0})
    values.update(changes)
    return FitCandidate(**values)


def test_nonfinite_diagnostics_serialize_as_null_with_explicit_flags():
    c = _candidate(loglikelihood=float('nan'), parameters={'omega': float('inf'), 'alpha[1]': 0.1},
                   min_conditional_variance=float('nan'), variance_positive_finite=False,
                   slacks={'persistence': float('-inf')})
    assert not c.likelihood_finite and not c.all_parameters_finite
    d = c.as_dict()
    assert d['loglikelihood'] is None and d['parameters']['omega'] is None and d['parameters']['alpha[1]'] == 0.1
    assert d['min_conditional_variance'] is None and d['slacks']['persistence'] is None
    assert d['nonfinite_fields'] == ['loglikelihood', 'min_conditional_variance', 'parameters.omega',
                                     'slacks.persistence']
    assert d['likelihood_finite'] is False and d['all_parameters_finite'] is False
    json.loads(canonical_json(d))
    assert _candidate().as_dict()['nonfinite_fields'] == []
    assert math.isnan(c.loglikelihood)  # the raw value is preserved on the object


@pytest.mark.parametrize('changes', [
    dict(family='egarch'), dict(attempt_kind='final'), dict(channel=-1), dict(channel=True),
    dict(convergence_flag=True), dict(converged=1), dict(settings={'maxiter': 1.5}), dict(model=''),
    dict(start=[1.0, 'a']), dict(error=''), dict(variance_positive_finite='yes'),
])
def test_candidate_validation(changes):
    with pytest.raises(ValueError):
        _candidate(**changes)


def test_decision_validation():
    assert AcceptanceDecision(True, (), 'p', '1').as_dict() == dict(accepted=True, reasons=[], policy_id='p',
                                                                     policy_version='1')
    for args in [(False, (), 'p', '1'), (1, (), 'p', '1'), (False, ('',), 'p', '1'), (True, (), '', '1'),
                 (False, 'reason', 'p', '1')]:
        with pytest.raises(ValueError):
            AcceptanceDecision(*args)


class _Malformed(_Double):
    def __init__(self, result):
        super().__init__('malformed', None)
        self.result = result

    def evaluate(self, candidate):
        return self.result


@pytest.mark.parametrize('result', [{'accepted': True}, True, None,
                                    AcceptanceDecision(True, (), 'other', '0-test'),
                                    AcceptanceDecision(True, (), 'malformed', '9')])
def test_malformed_policy_decisions_are_rejected(result):
    policy = _Malformed(result)
    with pytest.raises(PolicyContractError):
        evaluate_candidate(policy, _candidate())
    with pytest.raises(PolicyContractError):
        AcceptedVolatility(**VOL, policy=policy).fit(TRAIN)
    assert not issubclass(PolicyContractError, ValueError)


def test_policy_identity_validation_and_parameters_fingerprint():
    a = policy_identity(_Double('p', None, parameters={'margin': 1e-6}))
    b = policy_identity(_Double('p', None, parameters={'margin': 1e-5}))
    assert a['parameters'] == {'margin': 1e-6} and a['fingerprint'] != b['fingerprint']
    assert set(APPROVAL_STATUSES) == {'PROPOSED_REQUIRES_APPROVAL', 'APPROVED', 'TEST_DOUBLE'}
    bad = _Double('p', None)
    bad.approval_status = 'approved-ish'
    with pytest.raises(ValueError):
        policy_identity(bad)
    with pytest.raises(ValueError):
        AcceptedVolatility(**VOL, policy=bad)
    with pytest.raises(ValueError):
        AcceptedVolatility(**VOL, policy=object())


def test_retry_budget_has_no_default_attempts_and_validates():
    assert RetryBudget().attempts == () and RetryBudget().as_dict() == {'attempts': []}
    assert AcceptedVolatility(**VOL, policy=accept_all()).parameters['retry_budget'] == {'attempts': []}
    for settings in [{}, {'maxiter': 0}, {'maxiter': True}, {'ftol': 1e-9}, {'maxiter': 5, 'ftol': -1.0},
                     {'maxiter': 5, 'ftol': float('nan')}, {'maxiter': 5, 'gtol': 1.0}, [('maxiter', 5)]]:
        with pytest.raises(ValueError):
            RetryAttempt(settings)
    with pytest.raises(ValueError):
        RetryAttempt({'maxiter': 5}, [1.0, float('nan')])
    with pytest.raises(ValueError):
        RetryBudget([{'maxiter': 5}])
    # Family-specific validation happens at model construction, before fitting.
    with pytest.raises(ValueError):
        AcceptedARIMA([1, 0, 0], policy=accept_all(), retry_budget=RetryBudget([RetryAttempt({'maxiter': 5, 'ftol': 1e-9})]))
    with pytest.raises(ValueError):
        AcceptedARIMA([1, 0, 0], policy=accept_all(),
                      retry_budget=RetryBudget([RetryAttempt({'maxiter': 5}, {'omega_fraction': 1.0})]))
    with pytest.raises(ValueError):  # GARCH declarative start needs beta
        AcceptedVolatility(vol='garch', policy=accept_all(),
                           retry_budget=RetryBudget([RetryAttempt({'maxiter': 5}, {'omega_fraction': 1., 'alpha': .1})]))
    with pytest.raises(ValueError):  # unknown key
        AcceptedVolatility(**VOL, policy=accept_all(), start_grid=[{'omega_fraction': 1., 'alpha': .1, 'zeta': 1.}])


def test_start_grid_override_replaces_v1_grid():
    grid = [None, {'omega_fraction': 0.9, 'alpha': 0.1}, [0.5, 0.2]]
    rec = AcceptedVolatility(**VOL, policy=accept_all_finite(), start_grid=grid).fit(TRAIN).parameters
    for ch in rec['starts']:
        assert len(ch) == 3 and ch[0]['candidate']['start'] is None and ch[2]['candidate']['start'] == [0.5, 0.2]
    assert rec['start_grid'][0] is None and rec['start_grid'][2] == {'values': [0.5, 0.2]}
