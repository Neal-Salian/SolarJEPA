"""Fresh supervised Protocol v1 worker; fitting needs separate external approval.

Import and configuration inspection perform no scientific I/O or model building.
The CLI has no standalone fitting mode, retries, implicit SSL recomputation or
resume route. Results become usable only after the parent supervisor seals them.
"""
import argparse
from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import time


def _json(path):
    from .config import read_finite_json
    return read_finite_json(path)


def _fingerprint(value):
    from solar_flare_jepa.forecasting.contracts import fingerprint_payload
    return fingerprint_payload(value)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{label} requires every exact configuration field')


def parse_job_config(job):
    """Parse explicit register configurations without filling scientific defaults."""
    if (not isinstance(job, dict) or 'model_config' not in job
            or job.get('model_config_fingerprint') != _fingerprint(job['model_config'])):
        raise ValueError('Exact model configuration fingerprint is required')
    record, kind = job['model_config'], job.get('kind')
    from solar_flare_jepa.training.controlled import ControlledConfig, TrainingSchedule
    from solar_flare_jepa.training.jepa import JepaConfig
    from solar_flare_jepa.training.comparators import ComparatorSchedule, QuantileLinearConfig, TcnConfig
    try:
        if kind in ('ssl_phase', 'neural_downstream'):
            _keys(record, ('schema_version', 'architecture', 'schedule'), 'Controlled config')
            ignored = {'pretrain_epochs', 'finetune_epochs', 'patience', 'jepa_weight_during_finetune'}
            _keys(record['architecture'], {f.name for f in fields(JepaConfig)} - ignored, 'JEPA architecture')
            _keys(record['schedule'], {f.name for f in fields(TrainingSchedule)}, 'Controlled schedule')
            config = ControlledConfig.from_dict(record)
            normalized, schedule = config.as_dict(), None
        elif kind == 'tcn':
            _keys(record, ('tcn', 'schedule'), 'TCN config')
            _keys(record['tcn'], {f.name for f in fields(TcnConfig)}, 'TCN architecture')
            _keys(record['schedule'], {f.name for f in fields(ComparatorSchedule)}, 'TCN schedule')
            config, schedule = TcnConfig(**record['tcn']), ComparatorSchedule(**record['schedule'])
            normalized = dict(tcn=config.as_dict(), schedule=schedule.as_dict())
        elif kind == 'quantile_linear':
            _keys(record, ('linear',), 'Linear config')
            _keys(record['linear'], {f.name for f in fields(QuantileLinearConfig)}, 'Linear path')
            config, schedule = QuantileLinearConfig(**record['linear']), None
            normalized = dict(linear=config.as_dict())
        else:
            raise ValueError('Unsupported Protocol v1 worker job kind')
    except (KeyError, TypeError) as error:
        raise ValueError('Malformed explicit model configuration') from error
    if normalized != record or config.seed != job.get('seed'):
        raise ValueError('Typed configuration changes exact protocol semantics or seed')
    return config, schedule


def _supervisor_ledger(context, supervisor_directory):
    directory = Path(supervisor_directory).absolute()
    expected = Path(context['approval']['output_root']) / 'supervisor'
    if directory.resolve() != directory or directory != expected:
        raise ValueError('Worker supervisor must be the reserved symlink-free output directory')
    ledger = _json(directory / 'supervisor.json')
    plan = ledger.get('plan', {})
    if (plan.get('code_fingerprint') != context['runtime']['source_fingerprint']
            or plan.get('config_fingerprint') != context['binding_fingerprint']
            or ledger.get('plan_fingerprint') != _fingerprint(plan)
            or ledger.get('execution_order') != [j['job_id'] for j in context['design']['jobs']]
            or set(ledger.get('jobs', {})) != set(ledger['execution_order'])):
        raise ValueError('Supervisor source/environment/configuration/job binding differs')
    resources = context['design']['resources']
    expected_limits = {name: resources[name] for name in ('threads', 'max_rss_bytes', 'total_wall_seconds',
                                                          'max_retries', 'poll_interval_seconds')}
    jobs = plan.get('jobs', [])
    expected_jobs = context['design']['jobs']
    if (plan.get('resources') != expected_limits or not isinstance(jobs, list) or len(jobs) != len(expected_jobs)
            or any(row.get('job_id') != expected_job['job_id']
                   or row.get('timeout_seconds') != expected_job['timeout_seconds']
                   for row, expected_job in zip(jobs, expected_jobs))):
        raise ValueError('Supervisor job/resource ceilings differ from the frozen protocol')
    for attempt in ledger.get('attempts', []):
        declaration = [row for row in jobs if row['job_id'] == attempt.get('job_id')]
        if len(declaration) != 1 or attempt.get('job_fingerprint') != _fingerprint(declaration[0]):
            raise ValueError('Supervisor attempt declaration fingerprint differs')
    return directory, ledger


def _artifact_binding(context, job, name, digest, fingerprint):
    return dict(schema_version=1, job_id=job['job_id'],
                design_fingerprint=context['protocol']['design_fingerprint'],
                binding_fingerprint=context['binding_fingerprint'],
                model_config_fingerprint=job['model_config_fingerprint'],
                artifact_name=name, artifact_sha256=digest, artifact_fingerprint=fingerprint)


def load_dependency(context, job, supervisor_directory):
    """Read a successful sealed SSL dependency; never recompute a missing one."""
    dependencies = job.get('dependencies')
    if dependencies == []:
        return None
    if not isinstance(dependencies, list) or len(dependencies) != 1:
        raise ValueError('JEPA requires exactly one declared SSL dependency')
    matches = [item for item in context['design']['jobs'] if item['job_id'] == dependencies[0]]
    if len(matches) != 1 or matches[0]['kind'] != 'ssl_phase' or matches[0]['seed'] != job['seed']:
        raise ValueError('SSL dependency is not this seed\'s declared shared artifact')
    dependency = matches[0]
    directory, ledger = _supervisor_ledger(context, supervisor_directory)
    entry = ledger['jobs'][dependency['job_id']]
    expected = f"attempts/{dependency['job_id']}-1/artifacts"
    attempts = [a for a in ledger.get('attempts', []) if a.get('job_id') == dependency['job_id']]
    if (entry.get('status') != 'succeeded' or entry.get('artifact_path') != expected
            or len(attempts) != 1 or attempts[0].get('number') != 1
            or attempts[0].get('status') != 'succeeded' or attempts[0].get('returncode') != 0):
        raise ValueError('SSL dependency is missing, failed, retried or unsealed')
    artifact_directory = directory / expected
    if artifact_directory.resolve() != artifact_directory:
        raise ValueError('SSL artifact path redirects through a symlink')
    from .v2_runner import _verify_sealed
    _verify_sealed(artifact_directory, entry['artifacts'], dependency['job_id'])
    binding, result = _json(artifact_directory / 'binding.json'), _json(artifact_directory / 'result.json')
    _keys(result, ('pretraining_record', 'artifact_fingerprint'), 'SSL result')
    expected_binding = _artifact_binding(context, dependency, 'ssl.pt', _sha256(artifact_directory / 'ssl.pt'),
                                         result['artifact_fingerprint'])
    if binding != expected_binding or {p.name for p in artifact_directory.iterdir()} != {
            'ssl.pt', 'binding.json', 'result.json', 'worker.json', 'artifacts.json'}:
        raise ValueError('SSL dependency source/environment/configuration/artifact binding differs')
    from solar_flare_jepa.training.controlled import PretrainingArtifact
    artifact = PretrainingArtifact.load(artifact_directory / 'ssl.pt')
    if artifact.fingerprint != result['artifact_fingerprint'] or artifact.record != result['pretraining_record']:
        raise ValueError('SSL dependency actual weights/record identity differs')
    _assert_state_runtime(artifact.state)
    return artifact


def _load_inputs(root, context):
    from solar_flare_jepa.data.goes_v2_development import load_development
    data, normalization = context['design']['data'], context['design']['data']['normalization']
    splits = [dict(name=name, start_utc=bounds[0], end_utc=bounds[1])
              for name, bounds in data['splits_utc_half_open'].items()]
    # Canonical role order, independent of JSON mapping ordering.
    splits.sort(key=lambda item: ('train', 'validation').index(item['name']))
    bundle = load_development(context['approval']['data_root'], manifests=[m['path'] for m in data['allowed_manifests']],
        forecast=data['forecast'], splits=splits,
        dataset_fingerprint=normalization['historical_expected_dataset_fingerprint'],
        split_fingerprint=normalization['historical_expected_split_fingerprint'],
        max_train_windows=context['design']['training']['max_train_windows'])
    _check_inputs(bundle, context)
    return bundle


def _check_inputs(bundle, context):
    expected = context['design']['data']['normalization']
    evidence = bundle.evidence
    observed = dict(dataset=bundle.dataset.fingerprint, split=evidence['split_fingerprint'],
                    training=bundle.training.fingerprint, normalization=bundle.normalization.fingerprint)
    pins = dict(dataset=expected['historical_expected_dataset_fingerprint'],
                split=expected['historical_expected_split_fingerprint'],
                training=expected['historical_expected_training_fingerprint'],
                normalization=expected['historical_expected_fingerprint'])
    if observed != pins or any(evidence[f'{key}_fingerprint'] != value for key, value in observed.items()):
        raise ValueError('Observed development input/normalization identities differ from protocol')
    from .v2_pilot_protocol import validate_data_identity
    validate_data_identity(context, bundle)
    if (evidence.get('test_windows_built') is not False or evidence.get('test_partition_constructed') is not False
            or evidence.get('manifest_identities') != context['design']['data']['allowed_manifests']):
        raise ValueError('Development loader scope differs from the approved manifest-only inputs')


def _establish_runtime(context, config):
    training, resources = context['design']['training'], context['design']['resources']
    if (training['device'] != 'cpu' or training['dtype'] != 'float32'
            or config.threads != 4 or resources['threads'] != 4
            or any(os.environ.get(name) != '4' for name in resources['thread_environment'])):
        raise ValueError('CPU float32/four native-library threads must be established before building')
    import torch
    from solar_flare_jepa.training.jepa import _setup
    torch.set_default_device('cpu')
    torch.set_default_dtype(torch.float32)
    _setup(config)
    if (torch.get_default_dtype() != torch.float32 or torch.get_default_device().type != 'cpu'
            or torch.get_num_threads() != 4 or not torch.are_deterministic_algorithms_enabled()):
        raise ValueError('Worker device/dtype/thread/determinism assertions failed')


def _assert_state_runtime(state):
    import torch
    if (not state or any(not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                         or (value.is_floating_point() and value.dtype != torch.float32)
                         for value in state.values())):
        raise ValueError('Every model/artifact tensor must remain on CPU with float32 floating weights')


def _fit(bundle, job, config, schedule, dependency):
    if job['kind'] == 'ssl_phase':
        from solar_flare_jepa.training.controlled import pretrain_controlled
        return pretrain_controlled(bundle.training, config)
    if job['kind'] == 'neural_downstream':
        from solar_flare_jepa.training.controlled import SSL_ARMS, fit_controlled
        if (config.schedule.arm in SSL_ARMS) != (dependency is not None):
            raise ValueError('No automatic SSL fallback or unexpected SSL reuse is permitted')
        return fit_controlled(bundle.training, bundle.validation, config, pretraining=dependency)
    if job['kind'] == 'tcn':
        from solar_flare_jepa.training.comparators import fit_tcn
        return fit_tcn(bundle.training, bundle.validation, config, schedule)
    if job['kind'] == 'quantile_linear':
        from solar_flare_jepa.training.comparators import fit_quantile_linear
        return fit_quantile_linear(bundle.training, bundle.validation, config)
    raise ValueError('Unsupported worker job')


def _write_json(path, value):
    from solar_flare_jepa.forecasting.contracts import canonical_json
    with Path(path).open('x') as stream:
        stream.write(canonical_json(value) + '\n')


def execute_job(root, approval, job, directory, supervisor_directory):
    """Execute only one externally approved job in its first supervised attempt."""
    if approval is None:
        raise ValueError('Separate G3 reservation/G4 execution approval is required')
    from .v2_pilot_protocol import validate_execution
    context = validate_execution(root, approval)
    matches = [j for j in context['design']['jobs'] if j['job_id'] == job.get('job_id')]
    if len(matches) != 1 or matches[0] != job:
        raise ValueError('Job differs from the exact approved Protocol v1 declaration')
    supervisor, ledger = _supervisor_ledger(context, supervisor_directory)
    output = Path(directory).absolute()
    expected = supervisor / f"attempts/{job['job_id']}-1/artifacts"
    attempts = [a for a in ledger.get('attempts', []) if a.get('job_id') == job['job_id']]
    if (output != expected or output.resolve() != output or not output.is_dir() or any(output.iterdir())
            or ledger.get('stop_reason') is not None or ledger['jobs'][job['job_id']]['status'] != 'pending'
            or len(attempts) != 1 or attempts[0].get('number') != 1
            or attempts[0].get('status') != 'running' or attempts[0].get('pid') not in (None, os.getpid())):
        raise ValueError('Worker requires a new empty active first-attempt supervisor artifact directory')
    config, schedule = parse_job_config(job)
    settings = config.architecture if hasattr(config, 'architecture') else config
    _establish_runtime(context, settings)
    dependency = load_dependency(context, job, supervisor_directory)
    began = time.perf_counter()
    bundle = _load_inputs(root, context)
    # Identity validation happens again at the consumer boundary, including supplied SSL support.
    _check_inputs(bundle, context)
    if dependency is not None:
        from solar_flare_jepa.training.controlled import _pretraining_identity
        expected_ssl = _pretraining_identity(bundle.training, bundle.normalization,
                                              bundle.evidence['train_windows'], config)
        if dependency.record['identity'] != expected_ssl:
            raise ValueError('Sealed SSL support/configuration differs before downstream fitting')
    selected = _fit(bundle, job, config, schedule, dependency)
    if job['kind'] == 'ssl_phase':
        from solar_flare_jepa.training.controlled import _pretraining_identity
        if selected.record['identity'] != _pretraining_identity(
                bundle.training, bundle.normalization, bundle.evidence['train_windows'], config):
            raise ValueError('Produced SSL configuration/support differs from the exact job')
        _assert_state_runtime(selected.state)
        path = output / 'ssl.pt'
        selected.save(path)
        from solar_flare_jepa.training.controlled import PretrainingArtifact
        reloaded = PretrainingArtifact.load(path)
        if reloaded.fingerprint != selected.fingerprint or reloaded.record != selected.record:
            raise ValueError('SSL weights-only reload identity differs')
        result = dict(pretraining_record=selected.record, artifact_fingerprint=selected.fingerprint)
        artifact_fingerprint = selected.fingerprint
    else:
        from .v2_evaluation_adapters import build_evaluation_record
        from .v2_pilot_protocol import evaluation_identity
        from solar_flare_jepa.training.controlled import load_forecaster
        if selected.record.get('config') != job['model_config'] or selected.record.get('seed') != job['seed']:
            raise ValueError('Selected model configuration/seed differs from the exact job')
        _assert_state_runtime(selected.model.state_dict())
        if selected.record['train_windows'] != bundle.evidence['train_windows']:
            raise ValueError('Selected model training subset differs from verified loader support')
        identity = evaluation_identity(context, bundle)
        before = build_evaluation_record(selected, bundle.validation, identity)
        path = output / 'selected.pt'
        selected.save(path)
        reloaded = load_forecaster(path)
        after = build_evaluation_record(reloaded, bundle.validation, identity)
        if selected.record != reloaded.record or before.to_json() != after.to_json():
            raise ValueError('Exact validation predictions/records differ after weights-only reload')
        result = dict(model_record=selected.record, evaluation_record=after.as_dict())
        artifact_fingerprint = after.fingerprint
    # Reject source/environment/approval drift during preparation, fitting or reload.
    final_context = validate_execution(root, approval)
    if final_context['binding_fingerprint'] != context['binding_fingerprint']:
        raise ValueError('Execution identity changed during worker execution')
    _write_json(output / 'result.json', result)
    _write_json(output / 'binding.json', _artifact_binding(context, job, path.name, _sha256(path),
                                                         artifact_fingerprint))
    _write_json(output / 'worker.json', dict(schema_version=1, job_id=job['job_id'],
        preparation_fit_and_validation_seconds=time.perf_counter() - began,
        input_evidence=bundle.evidence, exact_weights_only_reload_parity=True,
        scientific_status='NO_VALIDATED_REPLACEMENT', device='cpu', dtype='float32', threads=4))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--approval', required=True, type=Path)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--supervisor-directory', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        from .v2_pilot_protocol import validate_execution
        context = validate_execution(args.root, args.approval)
        jobs = [j for j in context['design']['jobs'] if j['job_id'] == args.job_id]
        if len(jobs) != 1:
            raise ValueError('Unknown exact Protocol v1 job id')
        execute_job(args.root, args.approval, jobs[0], Path.cwd(), args.supervisor_directory)
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps(dict(status='WORKER_REFUSED_OR_FAILED', reason=str(error))))
        return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
