"""Bounded, reproducible foundation runs; no SoLEXS or neural training entry point."""
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

import numpy as np

from solar_flare_jepa.data.storage import repository_relative_path
from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.contracts import (
    ForecastSpec, fingerprint_payload, logical_array, validate_alignment,
)
from solar_flare_jepa.forecasting.splitting import chronological_partitions
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.evaluation import evaluate_trajectory
from solar_flare_jepa.evaluation.trajectory import prediction_snapshot
from .config import config_fingerprint, load_config, utc_ns
from .fixtures import synthetic_fixture
from .provenance import (atomic_record, code_provenance, dataset_fingerprint,
                         split_fingerprint, verify_source_identities, _destination, _source_path)


ROLE = 'foundation_smoke_not_scientific_skill'
PHASE_E = 'BLOCKED_FOR_PHASE_E'


def _dataset(config, root):
    if config['dataset']['kind'] == 'synthetic_fixture':
        return synthetic_fixture(config)
    # Optional scientific readers are never imported by a synthetic run.
    from .reference import goes_reference
    return goes_reference(config, root)


def _dataset_manifest(dataset):
    return dict(schema_version=1, fingerprint=dataset_fingerprint(dataset),
        name=dataset.name, role=dataset.role, rows=len(dataset.starts_ns),
        starts_ns=int(dataset.starts_ns[0]), ends_ns=int(dataset.ends_ns[-1]),
        cadence_seconds=dataset.cadence_seconds, feature_names=list(dataset.feature_names),
        target_names=list(dataset.target_names), feature_units=list(dataset.feature_units),
        target_units=list(dataset.target_units),
        feature_valid_counts=dataset.feature_mask.sum(axis=0).tolist(),
        target_valid_counts=dataset.target_mask.sum(axis=0).tolist(),
        availability_policy=dataset.availability_policy,
        actual_availability_known=dataset.availability_ns is not None,
        time_policy=dataset.time_policy, quality_policy=dataset.quality_policy,
        metadata=json.loads(dataset.metadata_json))


def _coordinates(window):
    grid = window.targets.grid
    return dict(origin_ids=list(grid.origin_ids), issue_times_ns=grid.issue_times_ns.tolist(),
        starts_ns=grid.starts_ns.tolist(), ends_ns=grid.ends_ns.tolist(),
        target_names=list(grid.spec.target_names), target_units=list(grid.spec.target_units),
        target_mask=window.targets.mask.tolist(), targets=logical_array(window.targets.values),
        dataset_fingerprint=grid.dataset_fingerprint, spec_fingerprint=grid.spec.fingerprint)


def _failure(seed, name, partition, window, stage, error):
    return dict(seed=seed, model=name, partition=partition, stage=stage,
        reason=str(error), error_type=type(error).__name__,
        attempted_origin_ids=list(window.context.origin_ids),
        common_target_valid_count=int(window.targets.mask.sum()))


def run_experiment(config_path, root, *, output_dir=None):
    """Run fixed baselines and publish one immutable, indexed execution directory.

    Configuration/source/data contract violations fail before publication. Once
    the validated dataset and splits exist, baseline fit/predict/score failures
    are explicit records on the common origins; no clipping or row dropping.
    Model seeds are identity tags here: these six deterministic comparators
    consume no RNG and receive no held-out values in their fit interface.
    """
    root = _source_path(root)
    config_path = Path(config_path)
    if not config_path.is_absolute():
        config_path = root/config_path
    config = load_config(config_path)
    started = datetime.now(timezone.utc).isoformat()
    execution_id = uuid.uuid4().hex
    destination = output_dir or root/'results'/'experiments'/execution_id
    # Refuse unsafe/existing destinations before doing any fits or writes.
    destination = _destination(root, destination)
    provenance = code_provenance(root)
    dataset = _dataset(config, root)
    spec = ForecastSpec(**config['forecast'])
    boundaries = [dict(name=x['name'], start_ns=utc_ns(x['start_utc']), end_ns=utc_ns(x['end_utc']))
                  for x in config['splits']]
    # Partition raw support FIRST; supervised windows never define partitions.
    partitions = chronological_partitions(dataset, boundaries)
    windows = {p.name:build_partition_windows(dataset, spec, p) for p in partitions}
    training = windows['train'].training_slice
    manifests = dict(schema_version=1, partitions=[windows[p.name].manifest() for p in partitions])
    identities = dict(config=config_fingerprint(config), dataset=dataset_fingerprint(dataset),
                      split=split_fingerprint(manifests), source=provenance['source']['fingerprint'],
                      training=training.fingerprint)
    experiment_ids = [dict(seed=seed, fingerprint=fingerprint_payload(dict(**identities, seed=seed)))
                      for seed in config['seeds']]
    parameters, predictions, metrics, failures = [], [], [], []
    attempted = 0
    succeeded = 0
    model_errors = (ValueError, ArithmeticError, np.linalg.LinAlgError)
    for seed in config['seeds']:
        definitions = list(config['baselines'])
        if not any(item['name'] == 'persistence' for item in definitions):
            definitions.insert(0, dict(name='persistence', parameters={}))
        fitted, fit_errors = {}, {}
        for definition in definitions:
            name = definition['name']
            reference_only = name == 'persistence' and not any(
                x['name'] == name for x in config['baselines'])
            model = make_baseline(name, definition['parameters'])
            try:
                if not len(training.context.origin_ids):
                    raise ValueError('No eligible training origins; fitting is not attempted')
                model.fit(training)
                fitted[name] = model
                parameters.append(dict(seed=seed, model=name, reference_only=reference_only,
                                       status='fitted', parameters=model.parameters))
            except model_errors as error:
                fit_errors[name] = error
                parameters.append(dict(seed=seed, model=name, reference_only=reference_only,
                    status='failed', parameters=None, reason=str(error), error_type=type(error).__name__))
        for partition in partitions:
            name, window = partition.name, windows[partition.name]
            outputs, prediction_errors = {}, {}
            for definition in definitions:
                model_name = definition['name']
                if model_name in fit_errors:
                    continue
                try:
                    if not len(window.context.origin_ids):
                        raise ValueError('No eligible origins in this partition')
                    prediction = prediction_snapshot(
                        fitted[model_name].predict(window.context, window.targets.grid))
                    validate_alignment(window.targets.grid, prediction.grid)
                    if prediction.model_id != model_name:
                        raise ValueError('Prediction model identity differs from the requested baseline')
                    outputs[model_name] = prediction
                except model_errors as error:
                    prediction_errors[model_name] = error
            for definition in definitions:
                model_name = definition['name']
                reference_only = model_name == 'persistence' and not any(
                    x['name'] == model_name for x in config['baselines'])
                record = dict(seed=seed, model=model_name, partition=name, reference_only=reference_only,
                              **_coordinates(window))
                error = fit_errors.get(model_name, prediction_errors.get(model_name))
                if error is not None:
                    stage = 'fit' if model_name in fit_errors else 'predict'
                    failure = _failure(seed, model_name, name, window, stage, error)
                    failures.append(failure)
                    predictions.append(dict(**record, status='failed', values=None, reason=str(error)))
                    if not reference_only:
                        attempted += 1
                        metrics.append(dict(seed=seed, model=model_name, partition=name,
                            status='failed', metrics=None, **{k:v for k,v in failure.items()
                                                            if k not in ('seed','model','partition')}))
                    continue
                prediction = outputs[model_name]
                predictions.append(dict(**record, status='predicted', values=prediction.values.tolist(),
                    point_interpretation=prediction.point_interpretation,
                    quantile_levels=list(prediction.quantile_levels),
                    quantiles=None if prediction.quantiles is None else prediction.quantiles.tolist()))
                if reference_only:
                    continue
                attempted += 1
                try:
                    scores = evaluate_trajectory(window.targets, prediction, training,
                        persistence=outputs.get('persistence'),
                        lead_weights=config['metrics']['lead_weights'],
                        target_weights=config['metrics']['target_weights'])
                    metrics.append(dict(seed=seed, model=model_name, partition=name,
                        status='scored', metrics=scores,
                        persistence_reference_status='predicted' if 'persistence' in outputs else 'failed',
                        persistence_reference_reason=None if 'persistence' in outputs else str(
                            fit_errors.get('persistence', prediction_errors.get('persistence')))))
                    succeeded += 1
                except model_errors as error:
                    failure = _failure(seed, model_name, name, window, 'evaluate', error)
                    failures.append(failure)
                    metrics.append(dict(seed=seed, model=model_name, partition=name,
                        status='failed', metrics=None, **{k:v for k,v in failure.items()
                                                        if k not in ('seed','model','partition')}))
    # Recheck code identity after execution. A changing checkout cannot publish a
    # result carrying the earlier source fingerprint or Git commit.
    verify_source_identities(root, provenance['source']['files'])
    final_provenance = code_provenance(root)
    if (final_provenance['git_commit'] != provenance['git_commit']
            or final_provenance['git_branch'] != provenance['git_branch']
            or final_provenance['source']['fingerprint'] != identities['source']):
        raise ValueError('Git/source state changed during execution')
    # This also records actual loaded adapter modules after lazy data loading.
    provenance = final_provenance
    status = 'failed' if not succeeded else 'complete_with_model_failures' if failures else 'complete'
    result = dict(schema_version=1, role=ROLE, phase_e=PHASE_E, status=status,
        execution_id=execution_id, experiment_ids=experiment_ids, fingerprints=identities,
        started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
        output=repository_relative_path(destination, root),
        dataset_role=dataset.role, code_commit=provenance['git_commit'],
        code_branch=provenance['git_branch'], seeds=config['seeds'],
        seed_policy=dict(fixture_seed=config['dataset'].get('fixture_seed'),
                         model_seeds_used_for_randomness=False,
                         explanation='Fixed deterministic baselines; separate fixture RNG; seeds tag identities'),
        models=config['baselines'], attempted_model_partition_scores=attempted,
        successful_model_partition_scores=succeeded, failure_count=len(failures),
        evaluation=dict(trajectory='native_units_common_target_mask', schema_version=1,
                        events='not_constructed_real_event_definitions_gated'),
        deferred=dict(arch_garch='deferred_pending_residual_diagnostics',
                      solexs=PHASE_E, neural_training='not_implemented', novelty='UNKNOWN'),
        artifacts=['resolved_config.json','dataset_manifest.json','split_manifest.json',
                   'provenance.json','model_parameters.json','predictions.json','metrics.json','failures.json'])
    contents = {'result.json':result, 'resolved_config.json':config,
        'dataset_manifest.json':_dataset_manifest(dataset), 'split_manifest.json':manifests,
        'provenance.json':provenance, 'model_parameters.json':parameters,
        'predictions.json':predictions, 'metrics.json':metrics, 'failures.json':failures}
    return atomic_record(root, destination, contents)
