"""Bounded retrospective GOES inference. No training, acquisition or archive reads.

The parent dataset fingerprint identifies the frozen V1 dataset lineage; only its
explicitly pinned August partition is opened here. Future observations are a
separate display payload and never reach ``TrainedJepa.predict``.
"""
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

from solar_flare_jepa.dashboard.data import DashboardUnavailable, _NATIVE_IO_LOCK, _path, _sha, read_json
from solar_flare_jepa.forecasting.contracts import ForecastContext, ForecastSpec, FutureGrid

REGISTRY_PATH = 'src/solar_flare_jepa/dashboard/prediction_registry.json'
REGISTRY_SHA256 = '66030fdca12524b8e661970e6540b118715103d1ffed44f14d8f7c7b236c0f4f'
SPEC_FINGERPRINT = '094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94'
DATASET_FINGERPRINT = 'd21b81b42643777f68855d8e02fc17cb7fb326805763117f8e5863233d68ba12'
START = pd.Timestamp('2024-08-01T00:00:00Z')
END = pd.Timestamp('2024-09-01T00:00:00Z')
MINUTE_NS = 60_000_000_000
CODE_KEYS = ('inference', 'training_core', 'normalization', 'contracts', 'windows',
             'goes_adapter', 'goes_foundation', 'goes_verification', 'data_storage',
             'data_download', 'experiment_config', 'source_capture', 'package')
SOURCE_KEYS = ('august_manifest', 'august_config', 'forecast_config') + CODE_KEYS


@dataclass(frozen=True)
class ForecastInputs:
    context: ForecastContext
    grid: FutureGrid
    actual_future: np.ndarray
    quality: dict


@dataclass(frozen=True)
class PredictionResult:
    inputs: ForecastInputs
    jepa: object
    supervised: object | None
    provenance: dict


def load_prediction_registry(root):
    """A separate immutable contract; legacy dashboard registry stays unchanged."""
    try:
        path = _path(root, REGISTRY_PATH)
        if _sha(path) != REGISTRY_SHA256:
            raise DashboardUnavailable('Prediction registry identity mismatch')
        return read_json(path)
    except OSError as exc:
        raise DashboardUnavailable('Prediction registry is unavailable') from exc


def verify_artifacts(root, registry, keys):
    """Verify pinned bytes and executed project source, before native/model access."""
    approved = load_prediction_registry(root)
    if registry != approved:
        raise DashboardUnavailable('Prediction contract differs from the pinned registry')
    from solar_flare_jepa._executed_source import verify_loaded_source
    for key in keys:
        try:
            artifact = approved['artifacts'][key]
            path = _path(root, artifact['path'])
            if _sha(path) != artifact['sha256']:
                raise DashboardUnavailable('Prediction artifact identity mismatch: ' + artifact['path'])
            if 'module' in artifact:
                module = import_module(artifact['module'])
                loaded_path = Path(module.__file__)
                if _sha(loaded_path) != artifact['sha256']:
                    raise DashboardUnavailable('Imported prediction code identity mismatch: ' + artifact['module'])
                verify_loaded_source(artifact['module'], str(loaded_path.absolute()), artifact['sha256'])
        except (OSError, KeyError, TypeError, ImportError) as exc:
            raise DashboardUnavailable('Required prediction artifact is unavailable: ' + str(key)) from exc


def load_august_observations(root, registry):
    """Validate exactly 31 immutable August science products, entirely offline."""
    verify_artifacts(root, registry, SOURCE_KEYS)
    from solar_flare_jepa.data.goes_acquisition import verify_history
    from solar_flare_jepa.data.foundation import validate_goes_files
    try:
        path = _path(root, registry['artifacts']['august_manifest']['path'])
        manifest = read_json(path)
        if (manifest['dataset_id'] != 'v1-goes16-202408-science-avg1m-v2-2-1'
                or manifest['selected_interval']['start'] != '2024-08-01'
                or manifest['selected_interval']['end_exclusive'] != '2024-09-01'):
            raise DashboardUnavailable('Unapproved prediction observation partition')
        for row in manifest['files']:
            if not row['path'].startswith('data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/08/'):
                raise DashboardUnavailable('Unapproved prediction native source')
            _path(root, row['path'])
        paths = verify_history(path, Path(root).resolve())
        if len(paths) != 31:
            raise DashboardUnavailable('Incomplete August source selection')
        with _NATIVE_IO_LOCK:
            frame, _ = validate_goes_files(paths, start_utc=START.isoformat(), end_utc=END.isoformat())
        return frame[['xrsa_flux', 'xrsb_flux', 'observed', 'xrsa_valid', 'xrsb_valid']].copy()
    except (OSError, KeyError, TypeError, RuntimeError, ValueError) as exc:
        raise DashboardUnavailable('August GOES observations could not be verified: ' + str(exc)) from exc


def _issue_time(value):
    try:
        issue = pd.Timestamp(value)
        if (pd.isna(issue) or issue.tzinfo is None or issue.utcoffset().total_seconds() != 0
                or issue.value % MINUTE_NS):
            raise ValueError('Expected a whole UTC minute with explicit UTC timezone')
        issue = issue.tz_convert('UTC')
        if issue - pd.Timedelta(minutes=120) < START or issue + pd.Timedelta(minutes=30) > END:
            raise ValueError('Full context and forecast must lie within the August 2024 held-out partition')
        return issue
    except (TypeError, OverflowError) as exc:
        raise DashboardUnavailable('Invalid UTC issue time') from exc


def prepare_forecast(frame, issue_time, spec):
    """Select completed, fully valid 120x2 context bins; mask optional actuals.

    Minute origins supplement retrospective inference only. The original spec's
    stride30 and fingerprint are preserved; this does not extend the benchmark.
    """
    if not isinstance(spec, ForecastSpec) or spec.fingerprint != SPEC_FINGERPRINT:
        raise DashboardUnavailable('Prediction requires the unchanged frozen V1 forecast spec')
    issue = _issue_time(issue_time)
    if (not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None
            or frame.index.has_duplicates or not frame.index.is_monotonic_increasing
            or (frame.index.asi8 % MINUTE_NS != 0).any()):
        raise DashboardUnavailable('Observation index must contain unique ordered UTC minute bins')
    required = ['observed', 'xrsa_valid', 'xrsb_valid', 'xrsa_flux', 'xrsb_flux']
    if any(key not in frame for key in required):
        raise DashboardUnavailable('Missing context channels or quality masks')
    for key in required[:3]:
        if frame[key].dtype.kind != 'b':
            raise DashboardUnavailable('Observation quality masks must be boolean')
    past_index = pd.date_range(issue-pd.Timedelta(minutes=120), issue, freq='min', inclusive='left')
    future_index = pd.date_range(issue, issue+pd.Timedelta(minutes=30), freq='min', inclusive='left')
    # Reindex exposes missing bins without creating observations or filling values.
    past = frame.reindex(past_index)
    future = frame.reindex(future_index)
    quality = {}
    arrays = []
    for label, selected in (('context', past), ('future', future)):
        observed = selected['observed'].eq(True)
        channels = []
        quality[label] = {}
        for channel in ('xrsa', 'xrsb'):
            valid = selected[channel+'_valid'].eq(True) & observed
            values = selected[channel+'_flux'].astype(float)
            valid &= np.isfinite(values) & (values > 0)
            channels.append(values.where(valid).to_numpy(float))
            quality[label][channel] = {'valid': int(valid.sum()), 'masked': int((~valid).sum()),
                                       'missing': int((~observed).sum())}
        arrays.append(np.column_stack(channels))
    context_values, actual = arrays
    if not np.isfinite(context_values).all():
        raise DashboardUnavailable('All 120 context bins must be positive, finite and quality-valid in both channels; no filling')
    issues = np.array([issue.value], dtype=np.int64)
    origin_ids = ('origin:' + str(issue.value),)
    context = ForecastContext(context_values[None], np.ones((1,120,2), dtype=bool),
        past_index.asi8[None], past_index.asi8[None]+MINUTE_NS, issues, origin_ids, spec, DATASET_FINGERPRINT)
    grid = FutureGrid(future_index.asi8[None], future_index.asi8[None]+MINUTE_NS,
                      issues, origin_ids, spec, DATASET_FINGERPRINT)
    actual.setflags(write=False)
    return ForecastInputs(context, grid, actual, quality)


def predict_prepared(root, registry, inputs, *, include_supervised=False):
    """Both models receive the same context object and future grid; no actuals."""
    keys = SOURCE_KEYS + ('jepa_checkpoint',) + (('supervised_checkpoint',) if include_supervised else ())
    verify_artifacts(root, registry, keys)
    from solar_flare_jepa.training.jepa import TrainedJepa
    predictions = []
    for variant in (('jepa_finetune', 'jepa_checkpoint'), ('supervised', 'supervised_checkpoint'))[:2 if include_supervised else 1]:
        name, key = variant
        model = TrainedJepa.load(_path(root, registry['artifacts'][key]['path']))
        if (model.variant != name or model.record['seed'] != 17
                or model.normalization.fingerprint != registry['normalization_fingerprint']
                or model.normalization.spec.fingerprint != registry['spec_fingerprint']
                or inputs.context.spec.fingerprint != registry['spec_fingerprint']
                or not inputs.context.mask.all()):
            raise DashboardUnavailable('Checkpoint seed, normalization, spec or input eligibility differs')
        prediction = model.predict(inputs.context, inputs.grid)
        if (prediction.quantile_levels != (0.05, 0.25, 0.5, 0.75, 0.95)
                or (prediction.values <= 0).any() or (prediction.quantiles <= 0).any()):
            raise DashboardUnavailable('Invalid prediction quantiles or positive flux domain')
        predictions.append(prediction)
    return PredictionResult(inputs, predictions[0], predictions[1] if include_supervised else None,
        {'experiment_id': registry['experiment_id'], 'executed_commit': registry['executed_commit'],
         'seed': 17, 'normalization_fingerprint': registry['normalization_fingerprint'],
         'spec_fingerprint': registry['spec_fingerprint'],
         'dataset_fingerprint': registry['dataset_fingerprint'],
         'artifacts': {key: registry['artifacts'][key] for key in keys}})


def forecast(root, issue_time, *, include_supervised=False):
    registry = load_prediction_registry(root)
    observations = load_august_observations(root, registry)
    inputs = prepare_forecast(observations, issue_time, ForecastSpec(**registry['forecast_spec']))
    return predict_prepared(root, registry, inputs, include_supervised=include_supervised)
