"""Bounded classical demonstration: training-only selection and causal replay."""
from copy import deepcopy
import importlib
import json

import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa.statespace.sarimax import SARIMAX


def classical_module():
    try:
        return importlib.import_module('solar_flare_jepa.presentation.classical')
    except ModuleNotFoundError:
        pytest.fail('The classical presentation inference module is missing')


def flux_frame(start, rows, seed):
    rng = np.random.default_rng(seed)
    log = np.full((rows, 2), -6.)
    for i in range(1, rows):
        log[i] = -6 + .7 * (log[i - 1] + 6) + rng.normal(0, .04, 2)
    return pd.DataFrame(10 ** log, index=pd.date_range(start, periods=rows, freq='min', tz='UTC'),
                        columns=['xrsa_flux', 'xrsb_flux'])


@pytest.fixture(scope='module')
def inputs():
    train = flux_frame('2024-06-11T16:38Z', 3100, 81)
    test = flux_frame('2024-08-01', 360, 82)
    test.iloc[3, 0] = np.nan
    return train, test


@pytest.fixture(scope='module')
def bundle(inputs):
    return classical_module().build_classical(*inputs)


def test_classical_module_exposes_causal_inference():
    assert callable(classical_module().infer)


def test_demo_selects_earliest_eligible_window_and_strict_finite_json(bundle):
    deployment = bundle['deployment']
    assert deployment['issue_utc'] == '2024-08-01T02:04:00+00:00'
    assert deployment['context']['time_utc'][0] == '2024-08-01T00:04:00+00:00'
    assert len(deployment['actual']['time_utc']) == 30
    assert deployment['forecast']['time_utc'] == deployment['actual']['time_utc']
    assert bundle['classical']['training']['rows'] == 2880
    assert bundle['classical']['training']['end_exclusive_utc'] == '2024-06-13T16:38:00+00:00'
    assert len(bundle['classical']['candidates']) == 14
    assert bundle['classical']['sarima_status'] == 'NOT_APPLICABLE'
    json.dumps(bundle, allow_nan=False)


def test_information_criteria_match_same_training_response_and_likelihood(bundle, inputs):
    training = inputs[0].iloc[:2880]
    for row in bundle['classical']['candidates']:
        if row['fit_status'] == 'failed':
            continue
        y = np.log10(training[row['channel'] + '_flux'].to_numpy())
        result = SARIMAX(y, order=row['order'], trend=row['trend']).filter(row['params'])
        assert row['llf'] == pytest.approx(result.llf, abs=1e-8)
        assert row['aic'] == pytest.approx(result.aic, abs=1e-8)
        assert row['bic'] == pytest.approx(result.bic, abs=1e-8)
        assert row['nobs_effective'] == result.nobs_effective
        assert row['df_model'] == result.df_model
        assert row['burn'] == result.loglikelihood_burn
    for channel, row in bundle['classical']['selected'].items():
        eligible = [r for r in bundle['classical']['candidates']
                    if r['channel'] == channel and r['order'][1] == 1 and r['fit_status'] == 'converged']
        assert row['bic'] == min(r['bic'] for r in eligible)


def test_selection_and_parameters_ignore_test_targets_and_unused_training_tail(bundle, inputs):
    train, test = inputs
    changed_train, changed_test = train.copy(), test.copy()
    changed_train.iloc[2880:] *= 100
    changed_test.iloc[124:] *= 1000
    changed = classical_module().build_classical(changed_train, changed_test)
    assert changed['classical']['selected'] == bundle['classical']['selected']
    assert changed['deployment']['forecast'] == bundle['deployment']['forecast']
    assert changed['deployment']['metrics'] != bundle['deployment']['metrics']


def replay_context(bundle):
    content = bundle['deployment']['context']
    return pd.DataFrame({ch: content[ch] for ch in ('xrsa_flux', 'xrsb_flux')},
                        index=pd.to_datetime(content['time_utc'], utc=True))


def test_inference_replays_saved_parameters_without_fit(bundle, monkeypatch):
    from solar_flare_jepa.forecasting.statistical import ARIMA
    def forbidden(*args, **kwargs):
        raise AssertionError('Inference must never fit a model')
    monkeypatch.setattr(ARIMA, 'fit', forbidden)
    context = replay_context(bundle)
    output = classical_module().infer(bundle['classical']['selected'], context, bundle['deployment']['issue_utc'])
    assert output.shape == (30, 2)
    assert str(output.index.tz) == 'UTC'
    np.testing.assert_allclose(output.to_numpy(), np.column_stack([
        bundle['deployment']['forecast'][ch] for ch in ('xrsa_flux', 'xrsb_flux')]), rtol=0, atol=0)


@pytest.mark.parametrize('defect', ['naive', 'duplicate', 'gap', 'reverse', 'future', 'short', 'zero', 'nan', 'channel'])
def test_inference_rejects_invalid_context(bundle, defect):
    context = replay_context(bundle)
    if defect == 'naive':
        context.index = context.index.tz_localize(None)
    elif defect == 'duplicate':
        context.index = pd.DatetimeIndex([context.index[0], *context.index[:-1]])
    elif defect == 'gap':
        context.index = context.index.where(np.arange(120) != 4, context.index[4] + pd.Timedelta(seconds=1))
    elif defect == 'reverse':
        context = context.iloc[::-1]
    elif defect == 'future':
        context.index += pd.Timedelta(minutes=1)
    elif defect == 'short':
        context = context.iloc[1:]
    elif defect == 'channel':
        context = context.rename(columns={'xrsa_flux': 'unknown'})
    else:
        context.iloc[4, 0] = 0 if defect == 'zero' else np.nan
    with pytest.raises(ValueError):
        classical_module().infer(bundle['classical']['selected'], context, bundle['deployment']['issue_utc'])


@pytest.mark.parametrize('field,value', [('channel', 'xrsb'), ('units', 'counts'), ('transform', 'identity'),
    ('context_steps', 119), ('horizon_steps', 31), ('params', [float('nan')]),
    ('param_names', ['wrong']), ('order', [1, 1, True]), ('trend', 'c'),
    ('train_end_utc', '2024-08-02T00:00Z')])
def test_inference_rejects_corrupt_saved_schema(bundle, field, value):
    selected = deepcopy(bundle['classical']['selected'])
    selected['xrsa'][field] = value
    with pytest.raises(ValueError):
        classical_module().infer(selected, replay_context(bundle), bundle['deployment']['issue_utc'])


def test_log_metrics_use_identical_observed_forecast_timestamps(bundle):
    deployment = bundle['deployment']
    for channel in ('xrsa', 'xrsb'):
        residual = np.log10(deployment['actual'][channel + '_flux']) - np.log10(deployment['forecast'][channel + '_flux'])
        assert deployment['metrics'][channel]['log_mae'] == pytest.approx(np.abs(residual).mean())
        assert deployment['metrics'][channel]['log_rmse'] == pytest.approx(np.sqrt(np.mean(residual ** 2)))


def test_finite_flux_with_explicit_false_qc_mask_is_ineligible(inputs):
    train, test = inputs
    test = test.fillna(1e-6)
    test['xrsa_valid'] = True
    test['xrsb_valid'] = True
    test['observed'] = True
    test.loc[test.index[3], 'xrsa_valid'] = False
    result = classical_module().build_classical(train, test)
    assert result['deployment']['issue_utc'] == '2024-08-01T02:04:00+00:00'


@pytest.mark.parametrize('mask', ['xrsa_valid', 'xrsb_valid', 'observed'])
def test_complete_training_support_refuses_explicit_rejected_observation(inputs, mask):
    train, test = inputs
    train = train.copy()
    train[mask] = True
    train.loc[train.index[3], mask] = False
    with pytest.raises(ValueError, match='positive|finite|valid'):
        classical_module().build_classical(train, test)
