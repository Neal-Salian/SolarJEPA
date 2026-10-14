"""Guarded frozen external replication: preflight never constructs predictors.

Execution consumes authenticated snapshots without fitting. A caller-supplied
approval reference records an external human decision; code cannot authenticate
that decision. Full scientific execution remains subject to the protocol gate.
"""
from copy import deepcopy
import hashlib
import importlib
import io
import json
from pathlib import Path
import tempfile

from solar_flare_jepa.evaluation.external_model import score_external_prediction, validate_external_score
# Cohort pairing imports this dependency lazily. Load it before the strict
# baseline provenance snapshot so its inspection/executed-source state is stable.
from solar_flare_jepa.evaluation import uncertainty as _calendar_dependency
from solar_flare_jepa.evaluation.trajectory import prediction_snapshot, _prediction_content
from solar_flare_jepa.forecasting.contracts import ForecastPrediction, canonical_json, fingerprint_payload, logical_array
from solar_flare_jepa.forecasting.frozen import load_frozen_baseline
from solar_flare_jepa.training.jepa import TrainedJepa
from .config import _object, _reject_constant
from .external_inputs import load_frozen_inputs, reverify_frozen_inputs
from .provenance import code_provenance, atomic_record, _destination, _source_identity


def _protocol(config_path, root):
    path = Path(config_path)
    if not path.is_absolute():
        path = root/path
    identity = _source_identity(path)
    payload = path.read_bytes()
    if dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()) != identity:
        raise ValueError('Protocol bytes changed during consumption')
    protocol = json.loads(payload, object_pairs_hook=_object, parse_constant=_reject_constant)
    if not isinstance(protocol, dict):
        raise ValueError('Protocol must be a finite JSON object')
    canonical_json(protocol)
    protocol['code_root'] = str(root)
    return path, identity, protocol


def _runtime(root):
    packages = {}
    for name in ('torch', 'numpy', 'pandas', 'scipy', 'statsmodels', 'arch'):
        module = importlib.import_module(name)
        packages[name] = str(module.__version__)
    # Every tracked runtime lock at the repository root, distinct from pinned
    # historical lock bytes carried by the authenticated input provenance.
    lockfiles = [dict(path=p.name, **_source_identity(p)) for p in sorted(root.glob('*lock*'))
                 if p.is_file()]
    return dict(packages=packages, lockfiles=lockfiles)


def _metadata(frozen, source, runtime):
    import torch
    protocol = frozen['protocol']
    historical_packages = frozen['historical_source'].get('packages', {})
    saved_torch = {}
    for item in frozen['checkpoint_records']:
        payload = torch.load(io.BytesIO(item['checkpoint_bytes']), map_location='cpu', weights_only=True)
        if type(payload['torch_version']) is not str or not payload['torch_version']:
            raise ValueError('Saved checkpoint must declare its recorded torch version')
        saved_torch[item['model']] = payload['torch_version']
    return dict(schema_version=1, evaluation_id=protocol['evaluation_id'],
        scope=protocol['scope'], claim=protocol['claim'], fit_performed=False,
        fitting_policy=protocol['fitting_policy'], limitations=deepcopy(protocol['limitations']),
        exposure=deepcopy(protocol['exposure']), historical_source=deepcopy(frozen['historical_source']),
        inference_source=source, inference_runtime=runtime,
        historical_runtime=dict(interpretation='recorded_historical_declarations_not_recreated_execution',
            package_versions={name: historical_packages.get(name) for name in
                              ('torch','scipy','statsmodels','arch','numpy','pandas')},
            unavailable_version_status='UNKNOWN', checkpoint_torch_versions=saved_torch),
        historical_runtime_lockfiles=[deepcopy(x) for x in protocol['historical_input_files']
                                     if 'lock' in x['path']],
        input_fingerprint=frozen['input_fingerprint'], protocol_fingerprint=frozen['protocol_fingerprint'],
        input_identities=deepcopy(frozen['input_identities']),
        external_dataset_fingerprint=frozen['context'].dataset_fingerprint,
        checkpoints=[{key: deepcopy(value) for key,value in item.items() if key != 'checkpoint_bytes'}
                     for item in frozen['checkpoint_records']],
        classical_models=list(frozen['classical_fit_records']),
        classical_fit_records=deepcopy(frozen['classical_fit_records']),
        candidate_count=len(frozen['candidate_issue_times_ns']), retained_origin_count=len(frozen['context'].origin_ids))


def _preflight(config_path, root, v1_dir, preparation_dir, output_dir):
    root = Path(root).resolve()
    if output_dir is not None:
        _destination(root, output_dir)  # Reject occupied/redirected output before inference.
    path, identity, protocol = _protocol(config_path, root)
    source = code_provenance(root, require_clean=True, require_installed_match=True)
    frozen = load_frozen_inputs(Path(v1_dir), Path(preparation_dir), protocol)
    runtime = _runtime(root)
    if frozen['context'].dataset_fingerprint == frozen['v1_summary']['dataset']['fingerprint']:
        raise ValueError('External prediction requires a distinct bound dataset identity')
    return root, path, identity, protocol, source, runtime, frozen


def preflight_external_evaluation(config_path: Path, root: Path, *, v1_dir: Path,
                                  preparation_dir: Path, output_dir: Path | None = None) -> dict:
    """Authenticate metadata/artifact bytes without model loading or inference."""
    root, path, identity, protocol, source, runtime, frozen = _preflight(
        config_path, root, v1_dir, preparation_dir, output_dir)
    reverify_frozen_inputs(frozen, Path(v1_dir), Path(preparation_dir), protocol)
    if _source_identity(path) != identity or _runtime(root) != runtime:
        raise ValueError('Protocol/runtime changed during preflight')
    final_source = code_provenance(root, require_clean=True, require_installed_match=True)
    if final_source != source:
        raise ValueError('Inference source changed during preflight')
    result = _metadata(frozen, source, runtime)
    result['protocol_file_identity'] = identity
    result.update(status='preflight_verified', inference_performed=False,
                  full_external_execution='requires_explicit_user_approval')
    return result


def _publication_inputs(frozen):
    context, targets = frozen['context'], frozen['targets']
    grid = targets.grid
    common = dict(spec=context.spec.as_dict(), dataset_fingerprint=context.dataset_fingerprint,
                  issue_times_ns=context.issue_times_ns.tolist(), origin_ids=list(context.origin_ids))
    return dict(input_identities=deepcopy(frozen['input_identities']),
        input_fingerprint=frozen['input_fingerprint'],
        candidate_issue_times_ns=frozen['candidate_issue_times_ns'].tolist(),
        retained_candidate_indices=frozen['retained_candidate_indices'].tolist(),
        candidate_exclusions=deepcopy(frozen['candidate_exclusions']),
        window_manifest=deepcopy(frozen['window_manifest']),
        dataset_manifest=deepcopy(frozen['dataset_manifest']),
        preparation_summary=deepcopy(frozen['preparation_summary']),
        context=dict(**common, values=logical_array(context.values), mask=context.mask.tolist(),
            starts_ns=context.starts_ns.tolist(), ends_ns=context.ends_ns.tolist(),
            availability_ns=None if context.availability_ns is None else context.availability_ns.tolist()),
        future_grid=dict(**common, starts_ns=grid.starts_ns.tolist(), ends_ns=grid.ends_ns.tolist()),
        targets=dict(values=logical_array(targets.values), mask=targets.mask.tolist()))


def _checkpoint_predictions(frozen, root):
    import torch
    context, grid = frozen['context'], frozen['targets'].grid
    previous_threads = torch.get_num_threads()
    previous_deterministic = torch.are_deterministic_algorithms_enabled()
    previous_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    outputs, execution = {}, {}
    parent = root/'results/experiments'
    parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='.checkpoint-consumption-', dir=parent) as temporary:
            for item in frozen['checkpoint_records']:
                path = Path(temporary)/item['path']
                with path.open('xb') as stream:
                    stream.write(item['checkpoint_bytes'])
                if _source_identity(path) != item['identity']:
                    raise ValueError('Checkpoint snapshot identity differs before safe loading')
                model = TrainedJepa.load(path)
                if (model.record != item['record'] or canonical_json(model.normalization.as_dict()) != canonical_json(item['normalization'])
                        or canonical_json(model.config.as_dict()) != canonical_json(item['record']['config'])):
                    raise ValueError('Loaded checkpoint identity differs from frozen record')
                torch.set_num_threads(model.config.threads)
                torch.use_deterministic_algorithms(True)
                prediction = prediction_snapshot(model.predict(context, grid))
                # The public JEPA ID identifies variant only; scoring/publication
                # additionally preserves the original saved cohort seed identity.
                prediction = ForecastPrediction(prediction.values, prediction.grid, item['model'],
                    prediction.quantile_levels, prediction.quantiles, prediction.point_interpretation)
                outputs[item['model']] = prediction
                execution[item['model']] = dict(device='cpu', batch_size=model.config.batch_size,
                    torch_threads=model.config.threads, deterministic_algorithms=True,
                    saved_record=deepcopy(item['record']))
                path.unlink()
    finally:
        torch.set_num_threads(previous_threads)
        torch.use_deterministic_algorithms(previous_deterministic, warn_only=previous_warn_only)
    return outputs, execution


def run_external_evaluation(config_path: Path, root: Path, *, v1_dir: Path,
                            preparation_dir: Path, output_dir: Path,
                            approval_reference: str | None = None) -> Path:
    """Execute all frozen arms after a caller records explicit human approval.

    The nonempty reference is a traceability assertion, not authorization proof.
    Failed arms abort the complete comparison; no surviving-seed reduction or
    observation-support change can be published.
    """
    if type(approval_reference) is not str or not approval_reference.strip():
        raise ValueError('Explicit execution approval reference is required')
    root, path, identity, protocol, source, runtime, frozen = _preflight(
        config_path, root, v1_dir, preparation_dir, output_dir)
    predictions, checkpoint_execution = _checkpoint_predictions(frozen, root)
    context, targets = frozen['context'], frozen['targets']
    for name, record in frozen['classical_fit_records'].items():
        model = load_frozen_baseline(record, context.spec,
            expected_training_fingerprint=record['training_fingerprint'],
            external_dataset_fingerprint=context.dataset_fingerprint)
        predictions[name] = prediction_snapshot(model.predict(context, targets.grid))
    planned = {x['model'] for x in protocol['checkpoint_cohort']} | set(protocol['classical_models'])
    if set(predictions) != planned or len(predictions) != 22:
        raise ValueError('Complete frozen 22-arm cohort is required')
    persistence = predictions['persistence']
    scores = {name: validate_external_score(score_external_prediction(targets, prediction,
                    persistence=persistence)) for name,prediction in predictions.items()}
    nested = {}
    for item in frozen['checkpoint_records']:
        nested.setdefault(item['variant'], {})[item['seed']] = scores[item['model']]
    from solar_flare_jepa.evaluation.external_model import summarize_external_cohort
    cohort = summarize_external_cohort(nested, frozen['candidate_issue_times_ns'],
        frozen['candidate_exclusions'], settings=protocol,
        classical_scores={name: scores[name] for name in protocol['classical_models']})
    summary = _metadata(frozen, source, runtime)
    summary['protocol_file_identity'] = identity
    summary.update(status='complete', inference_performed=True,
        execution_approval=dict(reference=approval_reference, authenticated_by_code=False,
                                meaning='caller_supplied_reference_to_external_human_approval'),
        checkpoint_execution=checkpoint_execution, cohort=cohort)
    prediction_records = {name: _prediction_content(prediction) for name,prediction in predictions.items()}
    prediction_identity = fingerprint_payload(prediction_records)
    # Publication repeats every consumed-input/source/runtime boundary, and
    # integrity validation of the actual score/prediction payloads.
    reverify_frozen_inputs(frozen, Path(v1_dir), Path(preparation_dir), protocol)
    if _source_identity(path) != identity or _runtime(root) != runtime:
        raise ValueError('Protocol/runtime changed before publication')
    if code_provenance(root, require_clean=True, require_installed_match=True) != source:
        raise ValueError('Inference source changed before publication')
    scores = {name: validate_external_score(score) for name,score in scores.items()}
    if fingerprint_payload({name: _prediction_content(prediction_snapshot(prediction))
                            for name,prediction in predictions.items()}) != prediction_identity:
        raise ValueError('Prediction state changed before publication')
    summary['prediction_content_fingerprint'] = prediction_identity
    return atomic_record(root, output_dir, {'summary.json': summary,
        'resolved_protocol.json': frozen['protocol'], 'predictions.json': prediction_records,
        'scores.json': scores, 'inputs.json': _publication_inputs(frozen)})
