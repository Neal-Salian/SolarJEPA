"""Immutable P2 smoke artifacts using the P1 data/split/evaluation contracts."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

import numpy as np

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.evaluation import evaluate_trajectory
from solar_flare_jepa.experiments.config import config_fingerprint, load_config, read_finite_json, utc_ns
from solar_flare_jepa.experiments.provenance import (
    _destination, _rename_no_replace, _source_identity, _source_path, code_provenance,
    split_fingerprint, verify_artifacts, verify_source_identities,
)
from solar_flare_jepa.experiments.runner import _coordinates, _dataset, _dataset_manifest
from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastSpec, ForecastTargets, FutureGrid, canonical_json,
    fingerprint_payload, logical_array,
)
from solar_flare_jepa.forecasting.splitting import chronological_partitions
from solar_flare_jepa.forecasting.windows import WindowedPartition, build_partition_windows
from .core import MODEL_ID, TrainingConfig, _selection, fit_smoke, load_checkpoint, window_snapshot


def load_training_config(path):
    content = read_finite_json(Path(path))
    if not isinstance(content, dict) or set(content) != set(TrainingConfig().as_dict()):
        raise ValueError('Training config must explicitly declare every hyperparameter and bound')
    return TrainingConfig(**content)


def bounded_window(window, maximum):
    """A recorded chronological subset; original partition manifests remain intact."""
    window = window_snapshot(window)
    selection = _selection(window, maximum)
    n = selection['selected_count']
    old = window.context
    context = ForecastContext(old.values[:n], old.mask[:n], old.starts_ns[:n], old.ends_ns[:n],
        old.issue_times_ns[:n], old.origin_ids[:n], old.spec, old.dataset_fingerprint,
        None if old.availability_ns is None else old.availability_ns[:n])
    old = window.targets.grid
    grid = FutureGrid(old.starts_ns[:n], old.ends_ns[:n], old.issue_times_ns[:n], old.origin_ids[:n],
                      old.spec, old.dataset_fingerprint)
    targets = ForecastTargets(window.targets.values[:n], window.targets.mask[:n], grid)
    return WindowedPartition(context, targets, None, '{}'), selection


def _publish(root, destination, model, contents):
    destination = _destination(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=destination.parent))
    try:
        model.save_checkpoint(stage / 'best.pt')
        for name, content in sorted(contents.items()):
            if '/' in name or not name.endswith('.json') or name == 'artifacts.json':
                raise ValueError('Unsafe training artifact identifier')
            encoded = (canonical_json(content) + '\n').encode('utf-8')
            with (stage / name).open('xb') as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        files = [dict(path=path.name, bytes=path.stat().st_size, sha256=sha256_file(path))
                 for path in sorted(stage.iterdir())]
        with (stage / 'artifacts.json').open('xb') as stream:
            stream.write((canonical_json(dict(schema_version=1, files=files)) + '\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        verify_artifacts(stage)
        # Reopen the actual serialized checkpoint before publication. Weight
        # deserialization is CPU-only and restricted to tensors/primitive state.
        restored = load_checkpoint(stage / 'best.pt', expected_identities=model.identities, device='cpu')
        if restored.record != model.record:
            raise ValueError('Serialized checkpoint training record differs')
        _rename_no_replace(stage, destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return destination


def run_training_smoke(config_path, root, *, output_dir=None, training_config_path=None, device='cpu'):
    """Run fixed smoke training, reload and bounded native evaluation.

    Any numeric or identity failure aborts publication. Test targets are read
    for scoring only after the selected validation checkpoint has been frozen.
    """
    root = _source_path(root)
    config_path = Path(config_path)
    config_path = _source_path(config_path if config_path.is_absolute() else root / config_path)
    training_path = Path(training_config_path or 'configs/training/p2_smoke.json')
    training_path = _source_path(training_path if training_path.is_absolute() else root / training_path)
    config = load_config(config_path)
    settings = load_training_config(training_path)
    if settings.seed not in config['seeds']:
        raise ValueError('Training seed must be predeclared by the experiment configuration')
    execution_id = uuid.uuid4().hex
    destination = _destination(root, output_dir or root / 'results' / 'experiments' / f'p2-training-{execution_id}')
    started = datetime.now(timezone.utc).isoformat()
    provenance = code_provenance(root)
    configuration_sources = []
    for path in (config_path, training_path):
        if not path.is_relative_to(root):
            raise ValueError('Reproducible training config must be within the repository root')
        configuration_sources.append(dict(path=path.relative_to(root).as_posix(), **_source_identity(path)))
    # P1's executable-source inventory already includes all new src/scripts.
    # Explicit P2 config bytes additionally bind these new input definitions.
    source_identity = fingerprint_payload(dict(executable_source=provenance['source']['fingerprint'],
                                               configuration_sources=configuration_sources))
    dataset = _dataset(config, root)
    spec = ForecastSpec(**config['forecast'])
    boundaries = [dict(name=part['name'], start_ns=utc_ns(part['start_utc']), end_ns=utc_ns(part['end_utc']))
                  for part in config['splits']]
    partitions = chronological_partitions(dataset, boundaries)
    windows = {part.name: build_partition_windows(dataset, spec, part) for part in partitions}
    split_manifest = dict(schema_version=1, partitions=[windows[part.name].manifest() for part in partitions])
    training = windows['train'].training_slice
    model = fit_smoke(training, windows['validation'], config=settings, source_identity=source_identity,
                      split_identity=split_fingerprint(split_manifest), device=device)
    predictions, metrics, coverage = [], [], {}
    persistence = make_baseline('persistence', {}).fit(training)
    reload_equal = True
    # Use a temporary file only to verify inference from actual serialization;
    # the published best.pt is written independently with the same content.
    with tempfile.TemporaryDirectory(prefix='p2-reload-') as temporary:
        checkpoint = Path(temporary).resolve() / 'best.pt'
        model.save_checkpoint(checkpoint)
        restored = load_checkpoint(checkpoint, expected_identities=model.identities, device=device)
        for partition in partitions:
            window, coverage[partition.name] = bounded_window(windows[partition.name], settings.max_eval_origins)
            prediction = model.predict(window.context, window.targets.grid)
            reloaded = restored.predict(window.context, window.targets.grid)
            if not np.array_equal(prediction.values, reloaded.values):
                reload_equal = False
                raise ValueError('Checkpoint reload inference differs from selected model')
            reference = persistence.predict(window.context, window.targets.grid)
            score = evaluate_trajectory(window.targets, prediction, training, persistence=reference,
                lead_weights=config['metrics']['lead_weights'], target_weights=config['metrics']['target_weights'])
            predictions.append(dict(partition=partition.name, **_coordinates(window),
                                    model_id=MODEL_ID, values=logical_array(prediction.values),
                                    point_interpretation=prediction.point_interpretation))
            metrics.append(dict(partition=partition.name, metrics=score))
    verify_source_identities(root, provenance['source']['files'])
    verify_source_identities(root, configuration_sources)
    result = dict(schema_version=1, status='complete', model_id=MODEL_ID,
        scientific_status='TRAINING_INFRASTRUCTURE_SMOKE_TEST', phase_e='BLOCKED_FOR_PHASE_E',
        execution_id=execution_id, started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
        output=destination.relative_to(root).as_posix(), identities=model.identities,
        experiment_config_fingerprint=config_fingerprint(config), coverage=coverage,
        reload_verification=dict(bitwise_equal=reload_equal, partitions=[part.name for part in partitions], device=device),
        limitations=['bounded first chronological origins, not full-month model fitting/evaluation',
                     'masked normalized MSE trains a point smoke model; no physical conditional-mean claim',
                     'no SolarJEPA architecture, event labels, uncertainty estimates or forecast skill claim',
                     'operational delivery latency and SoLEXS calibrated timing/flux remain unresolved'])
    contents = {'result.json': result, 'config.json': config, 'training_config.json': settings.as_dict(),
        'provenance.json': dict(code=provenance, configuration_sources=configuration_sources,
                               source_identity=source_identity),
        'dataset_manifest.json': _dataset_manifest(dataset), 'split_manifest.json': split_manifest,
        'normalization.json': model.normalization.as_dict(), 'training_record.json': model.record,
        'predictions.json': predictions, 'metrics.json': metrics}
    return _publish(root, destination, model, contents)
