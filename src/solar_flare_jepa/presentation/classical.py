"""Small, training-only classical demonstration and saved-parameter replay.

This experiment is separate from the archived V1 benchmark. Its orders, 2,880
training-minute budget and first eligible August example are fixed in advance.
All estimation and forecast state filtering reuse the research SARIMAX adapter.
"""
from copy import deepcopy
import hashlib
import warnings

import numpy as np
import pandas as pd
import statsmodels

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset, canonical_json
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.statistical import ARIMA
from solar_flare_jepa.forecasting.windows import build_partition_windows

CHANNELS = ('xrsa', 'xrsb')
COLUMNS = tuple(ch + '_flux' for ch in CHANNELS)
CONTEXT_STEPS, HORIZON_STEPS, FIT_STEPS, MAXITER = 120, 30, 2880, 100
MINUTE = pd.Timedelta(minutes=1)
ORDERS = (('AR', (1, 0, 0)), ('AR', (2, 0, 0)),
          ('MA', (0, 0, 1)), ('MA', (0, 0, 2)), ('ARMA', (1, 0, 1)),
          ('ARIMA', (1, 1, 0)), ('ARIMA', (2, 1, 0)))


def _utc(value, label):
    try:
        stamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f'{label} requires a UTC minute timestamp') from error
    if (pd.isna(stamp) or stamp.tzinfo is None or stamp.utcoffset() != pd.Timedelta(0)
            or stamp.value % MINUTE.value):
        raise ValueError(f'{label} requires an aware UTC minute timestamp')
    return stamp.tz_convert('UTC')


def _frame(frame, *, complete, contiguous, exact_columns=False):
    if not isinstance(frame, pd.DataFrame) or not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError('Expected a DataFrame with an aware UTC minute index')
    if (not len(frame) or frame.columns.has_duplicates or not set(COLUMNS).issubset(frame.columns)
            or (exact_columns and set(frame.columns) != set(COLUMNS))):
        raise ValueError('Expected the two named GOES flux channels')
    index = frame.index
    if (index.tz is None or index.hasnans or index.has_duplicates or not index.is_monotonic_increasing
            or any(t.utcoffset() != pd.Timedelta(0) for t in (index[0], index[-1]))):
        raise ValueError('Expected sorted unique aware UTC timestamps')
    index = index.tz_convert('UTC').as_unit('ns')
    if (index.asi8 % MINUTE.value).any() or (contiguous and not (np.diff(index.asi8) == MINUTE.value).all()):
        raise ValueError('Expected contiguous minute-aligned UTC timestamps')
    try:
        result = frame.loc[:, COLUMNS].astype(float).copy()
    except (TypeError, ValueError) as error:
        raise ValueError('Flux channels require numeric observations') from error
    result.index = index
    for channel in CHANNELS:
        for mask_name in (channel + '_valid', 'observed'):
            if mask_name in frame.columns:
                mask = frame[mask_name].to_numpy()
                if not all(isinstance(value, (bool, np.bool_)) for value in mask):
                    raise ValueError('Explicit validity masks require nonmissing booleans')
                result.loc[~np.asarray(mask, bool), channel + '_flux'] = np.nan
    values = result.to_numpy()
    if complete and (not np.isfinite(values).all() or (values <= 0).any()):
        raise ValueError('Flux observations must be positive and finite')
    return result


def _training_slice(frame, channel):
    """Canonical unique raw training support, independent of retained windows."""
    name = channel + '_flux'
    values = frame[[name]].to_numpy(float)
    starts = frame.index.asi8
    ends = starts + MINUTE.value
    dataset = TimeSeriesDataset(name='presentation_classical_' + channel, role='goes_historical',
        starts_ns=starts, ends_ns=ends, features=values, targets=values,
        feature_mask=np.ones_like(values, bool), target_mask=np.ones_like(values, bool),
        feature_names=(name,), target_names=(name,), feature_units=('W/m2',), target_units=('W/m2',),
        cadence_seconds=60, availability_policy='bin_end_earliest',
        metadata_json=canonical_json({'purpose': 'bounded presentation demonstration; not V1 benchmark'}))
    spec = ForecastSpec(cadence_seconds=60, context_steps=CONTEXT_STEPS, horizon_steps=HORIZON_STEPS,
        stride_steps=30, feature_names=(name,), target_names=(name,),
        feature_units=('W/m2',), target_units=('W/m2',), transform='log10',
        feature_reference=(1.,), target_reference=(1.,), target_minimum=(0.,),
        availability_mode='retrospective_bin_end')
    partition = TemporalPartition('train', int(starts[0]), int(ends[-1]))
    return build_partition_windows(dataset, spec, partition).training_slice


def _saved_record(record, channel, issue):
    """Validate the serialized replay contract before constructing any filter."""
    required = {'schema_version', 'channel', 'order', 'params', 'param_names', 'trend', 'train_end_utc',
                'context_steps', 'horizon_steps', 'units', 'transform', 'fit_status'}
    if not isinstance(record, dict) or not required.issubset(record):
        raise ValueError('Saved model record is missing required schema fields')
    if (type(record['schema_version']) is not int or record['schema_version'] != 1
            or record['channel'] != channel or record['units'] != 'W/m2' or record['transform'] != 'log10'
            or type(record['context_steps']) is not int or record['context_steps'] != CONTEXT_STEPS
            or type(record['horizon_steps']) is not int or record['horizon_steps'] != HORIZON_STEPS
            or record['fit_status'] != 'converged'):
        raise ValueError('Saved model schema, channel, units or fit status is incompatible')
    order = record['order']
    if (not isinstance(order, (list, tuple)) or len(order) != 3
            or any(type(v) is not int for v in order) or tuple(order) not in {o for _, o in ORDERS}):
        raise ValueError('Saved model order is invalid')
    if record['trend'] != ('n' if order[1] else 'c'):
        raise ValueError('Saved model deterministic trend is incompatible')
    if _utc(record['train_end_utc'], 'Training end') > issue:
        raise ValueError('Issue time precedes the end of fitted training support')
    try:
        parameters = np.asarray(record['params'], float)
    except (TypeError, ValueError) as error:
        raise ValueError('Saved parameters require finite numbers') from error
    if parameters.ndim != 1 or not np.isfinite(parameters).all():
        raise ValueError('Saved parameters require a finite vector')
    return parameters


def _forecast_record(record, context, issue):
    channel = record['channel']
    params = _saved_record(record, channel, issue)
    adapter = ARIMA(order=record['order'], maxiter=MAXITER)
    model = adapter._model(np.log10(context[channel + '_flux'].to_numpy(float)))
    if (record['param_names'] != list(model.param_names) or len(params) != len(model.param_names)
            or params[list(model.param_names).index('sigma2')] <= 0):
        raise ValueError('Saved parameter names, dimensions or innovation variance are invalid')
    with warnings.catch_warnings():
        # Match the existing adapter's fixed-parameter, fresh-context state policy.
        warnings.simplefilter('ignore')
        mean = model.filter(params).get_forecast(HORIZON_STEPS).predicted_mean
    with np.errstate(over='ignore', invalid='ignore', under='ignore'):
        native = np.power(10., np.asarray(mean, float))
    if native.shape != (HORIZON_STEPS,) or not np.isfinite(native).all() or (native <= 0).any():
        raise ValueError('Saved model produced invalid native flux predictions')
    return native


def infer(selected: dict, context: pd.DataFrame, issue_utc: str) -> pd.DataFrame:
    """Replay fitted parameters using exactly 120 completed past UTC minute bins.

    Returns 30 positive native-unit predictive medians on target-bin START
    timestamps. No fitting, target observations or future data enter this API.
    """
    if not isinstance(selected, dict) or set(selected) != set(CHANNELS):
        raise ValueError('Saved selection must contain exactly xrsa and xrsb records')
    issue = _utc(issue_utc, 'Issue time')
    context = _frame(context, complete=True, contiguous=True, exact_columns=True)
    expected = pd.date_range(issue - CONTEXT_STEPS * MINUTE, periods=CONTEXT_STEPS, freq='min')
    if len(context) != CONTEXT_STEPS or not context.index.equals(expected):
        raise ValueError('Context must contain exactly 120 completed past bins ending at issue time')
    for channel in CHANNELS:
        _saved_record(selected[channel], channel, issue)
    output = {channel + '_flux': _forecast_record(selected[channel], context, issue) for channel in CHANNELS}
    return pd.DataFrame(output, index=pd.date_range(issue, periods=HORIZON_STEPS, freq='min', name='time_utc'))


def _first_test_window(test_frame, train_end):
    """Select solely by chronology, cadence and observed QC validity, not activity."""
    frame = _frame(test_frame, complete=False, contiguous=False)
    if frame.index[0] < train_end:
        raise ValueError('Held-out observations overlap fitted training support')
    valid = np.isfinite(frame.to_numpy()).all(axis=1) & (frame.to_numpy() > 0).all(axis=1)
    run = 0
    for i, good in enumerate(valid):
        consecutive = i == 0 or frame.index[i] - frame.index[i - 1] == MINUTE
        run = (run + 1 if consecutive else 1) if good else 0
        if run == CONTEXT_STEPS + HORIZON_STEPS:
            start = i + 1 - run
            return (frame.iloc[start:start + CONTEXT_STEPS].copy(),
                    frame.iloc[start + CONTEXT_STEPS:i + 1].copy())
    raise ValueError('No eligible contiguous 120-context/30-target held-out window')


def _metrics(actual, forecast):
    residual = np.log10(np.asarray(actual, float)) - np.log10(np.asarray(forecast, float))
    return {'log_mae': float(np.abs(residual).mean()), 'log_rmse': float(np.sqrt(np.mean(residual ** 2)))}


def _content(frame):
    return dict(time_utc=[t.isoformat() for t in frame.index],
                **{column: frame[column].to_list() for column in COLUMNS})


def build_classical(training_block: pd.DataFrame, test_frame: pd.DataFrame) -> dict:
    """Fit seven fixed orders, select training BIC within d=1, then show one origin."""
    full_train = _frame(training_block, complete=True, contiguous=True)
    if len(full_train) < FIT_STEPS:
        raise ValueError('Classical demonstration requires at least 2880 contiguous training rows')
    train = full_train.iloc[:FIT_STEPS].copy()
    train_end = train.index[-1] + MINUTE
    support_hash = hashlib.sha256(canonical_json(_content(train)).encode()).hexdigest()
    candidates = []
    for channel in CHANNELS:
        training = _training_slice(train, channel)
        for family, order in ORDERS:
            row = dict(schema_version=1, channel=channel, family=family, order=list(order),
                trend='n' if order[1] else 'c', train_end_utc=train_end.isoformat(),
                context_steps=CONTEXT_STEPS, horizon_steps=HORIZON_STEPS, units='W/m2', transform='log10',
                target_reference=1., training_sha256=support_hash, training_fingerprint=training.fingerprint,
                statsmodels_version=statsmodels.__version__,
                optimizer='lbfgs', maxiter=MAXITER, low_memory=True,
                log_mae=None, log_rmse=None, aic=None, bic=None, llf=None, params=None, param_names=None,
                nobs=None, nobs_effective=None, df_model=None, burn=None, comparison_group=None,
                fit_status='failed', warnings=[], error=None)
            try:
                adapter = ARIMA(order, maxiter=MAXITER).fit(training)
                fitted = adapter.parameters
                endog = np.log10(train[channel + '_flux'].to_numpy(float))
                model = adapter._model(endog)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    result = model.filter(fitted['params'][0])
                np.testing.assert_allclose([result.llf, result.aic],
                    [fitted['loglikelihood'][0], fitted['aic'][0]], rtol=0, atol=1e-8)
                if not np.isfinite([result.llf, result.aic, result.bic]).all():
                    raise ValueError('Nonfinite training information criteria')
                row.update(params=fitted['params'][0], param_names=fitted['param_names'][0],
                    aic=float(result.aic), bic=float(result.bic), llf=float(result.llf),
                    nobs=int(result.nobs), nobs_effective=int(result.nobs_effective),
                    df_model=int(result.df_model), burn=int(result.loglikelihood_burn),
                    simple_differencing=bool(model.simple_differencing),
                    use_exact_diffuse=bool(model.use_exact_diffuse),
                    initialization='approximate diffuse integrated states; stationary ARMA states',
                    enforce_stationarity=bool(model.enforce_stationarity), enforce_invertibility=bool(model.enforce_invertibility),
                    fit_status='converged' if fitted['converged'][0] else 'nonconverged',
                    warnings=sorted(set(fitted['fit_warnings'][0] + [str(w.message) for w in caught])),
                    comparison_group=f'{channel}|log10|d={order[1]}|trend={row["trend"]}|burn={result.loglikelihood_burn}')
            except (ValueError, FloatingPointError, np.linalg.LinAlgError) as error:
                row['error'] = f'{type(error).__name__}: {error}'
            candidates.append(row)
    # Freeze selection before accessing even the held-out frame's timestamps or QC.
    selected = {}
    for channel in CHANNELS:
        eligible = [row for row in candidates if row['channel'] == channel
                    and row['order'][1] == 1 and row['fit_status'] == 'converged']
        if not eligible:
            raise ValueError(f'No converged training-only d=1 candidate for {channel}')
        chosen = min(eligible, key=lambda row: (row['bic'], row['order']))
        selected[channel] = deepcopy({key: value for key, value in chosen.items() if key not in ('log_mae', 'log_rmse')})
    context, actual = _first_test_window(test_frame, train_end)
    issue = actual.index[0]
    forecast = infer(selected, context, issue.isoformat())
    for row in candidates:
        if row['fit_status'] == 'converged':
            values = _forecast_record(row, context, issue)
            row.update(_metrics(actual[row['channel'] + '_flux'], values))
    payload = dict(classical=dict(
        training=dict(start_utc=train.index[0].isoformat(), end_exclusive_utc=train_end.isoformat(), rows=len(train)),
        candidates=candidates, selected=selected,
        selection='training BIC within d=1 group; no test selection',
        sarima_status='NOT_APPLICABLE',
        sarima_reason='No stable seasonal period is established by the contiguous training evidence; '
                      'an imposed STL period does not justify SARIMA seasonal differencing or seasonal lags.',
        interpretation='Small prespecified classical demonstration; separate from archived V1 results. '
                       'AIC/BIC are comparable only within each channel/d/trend/burn group.'),
        deployment=dict(context=_content(context), actual=_content(actual), forecast=_content(forecast),
            issue_utc=issue.isoformat(), context_steps=CONTEXT_STEPS, horizon_steps=HORIZON_STEPS,
            metrics={channel: _metrics(actual[channel + '_flux'], forecast[channel + '_flux']) for channel in CHANNELS},
            origin_selection='first chronological jointly valid contiguous 120-context/30-target window',
            interpretation='One held-out forecast illustration; not an estimate of average skill or calibration. '
                           'Native predictions are inverse-log predictive medians, conditional on fitted parameters.'))
    canonical_json(payload)  # Reject nonfinite JSON rather than exporting invalid scientific evidence.
    return payload
