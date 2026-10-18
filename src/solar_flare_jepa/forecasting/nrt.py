"""Conservative NRT boundary and explicit immutable GOES-16 science replay.

Live SWPC snapshots have no established V1 time/QC/satellite compatibility
contract. Only the existing pinned historical science service may forecast.
This module imports no model code until historical replay is explicitly called.
"""
from datetime import datetime, timezone


class NrtForecastUnavailable(ValueError):
    """A live snapshot does not satisfy an established model input contract."""


def forecast_snapshot(snapshot, **kwargs):
    """Reject every live snapshot, including caller-supplied override arguments.

    Numerical completeness or a caller's compatibility assertion cannot establish
    science-product time semantics, quality parity or cross-satellite validity.
    No snapshot inspection, checkpoint loading or historical fallback occurs.
    """
    raise NrtForecastUnavailable(
        'scientific contract unavailable: SWPC timestamp/bin semantics, science-quality parity '
        'and GOES-16 checkpoint compatibility are not established; live inference is blocked'
    )


def replay_v1(root, issue_utc, *, executed_utc=None, include_supervised=False):
    """Replay only pinned August 2024 GOES-16 science inputs and saved models.

    ``root`` locates the existing immutable V1 contract, not arbitrary science
    files. The historical service rechecks source/checkpoint identities, complete
    120x2 context, saved train-only normalization and the unchanged forecast spec.
    ``executed_utc`` permits an explicit recorded execution time for reproducible
    reports; it never replaces the retrospective forecast origin or supplies an
    unknown historical publication time. No operational validity is asserted.
    """
    import pandas as pd

    try:
        executed = pd.Timestamp(datetime.now(timezone.utc) if executed_utc is None else executed_utc)
        if pd.isna(executed) or executed.tzinfo is None or executed.utcoffset().total_seconds() != 0:
            raise ValueError('Expected explicit UTC execution time')
        origin = pd.Timestamp(issue_utc)
        if origin.tzinfo is not None and executed < origin:
            raise ValueError('Replay execution cannot precede its forecast origin')
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Invalid replay execution time: ' + str(exc)) from exc

    from solar_flare_jepa.dashboard.prediction import forecast
    result = forecast(root, issue_utc, include_supervised=include_supervised)
    context, grid = result.inputs.context, result.inputs.grid
    origin = pd.Timestamp(grid.issue_times_ns[0], tz='UTC')
    end = pd.Timestamp(grid.ends_ns[0, -1], tz='UTC')
    predictions = [result.jepa] + ([result.supervised] if result.supervised is not None else [])
    return {
        'status': 'PASS',
        'mode': 'historical_science_replay',
        'operationally_validated': False,
        'timing': {
            'observation_start_utc': pd.Timestamp(context.starts_ns[0, 0], tz='UTC').isoformat(),
            'observation_end_utc': pd.Timestamp(context.ends_ns[0, -1], tz='UTC').isoformat(),
            'publication_utc': None,
            'forecast_origin_utc': origin.isoformat(),
            'horizon_minutes': int((end - origin).total_seconds() / 60),
            'forecast_end_utc': end.isoformat(),
            'execution_utc': executed.tz_convert('UTC').isoformat(),
        },
        'context': {
            'values': context.values[0].tolist(),
            'mask': context.mask[0].tolist(),
            'feature_names': list(context.spec.feature_names),
            'feature_units': list(context.spec.feature_units),
        },
        'future_grid': {
            'starts_utc': [value.isoformat() for value in pd.to_datetime(grid.starts_ns[0], utc=True)],
            'ends_utc': [value.isoformat() for value in pd.to_datetime(grid.ends_ns[0], utc=True)],
        },
        'predictions': [{
            'model_id': prediction.model_id,
            'values': prediction.values[0].tolist(),
            'quantile_levels': list(prediction.quantile_levels),
            'quantiles': prediction.quantiles[0].tolist(),
            'point_interpretation': prediction.point_interpretation,
        } for prediction in predictions],
        'quality': result.inputs.quality,
        'provenance': result.provenance,
    }
