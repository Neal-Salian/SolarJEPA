"""Exact Protocol v1 identities and fail-closed, external execution declarations.

A declaration is an owner claim recorded locally, not an authenticated signature.
Ratification/infrastructure approval never supplies host or fitting authorization.
This module inspects source/configuration metadata only; it opens no science file.
"""
from collections.abc import Mapping
from datetime import datetime, timezone
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
import sys

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .config import read_finite_json
from .provenance import code_provenance

PROTOCOL_PATH = 'docs/protocols/phase2_v2_development_v1.json'
DESIGN_FINGERPRINT = 'ec104daac15f45fe1c0cee9de44b72e2ed67e2bc42de1bc69edb99ffbec55624'
PROTOCOL_ID = 'solarjepa.phase2.v2.development.v1'
EXPERIMENT_ID = 'solarjepa-phase2-v2-development-v1'
SCOPE = 'EXPOSED_DEVELOPMENT_FEASIBILITY_ONLY'
_APPROVAL_KEYS = {'schema_version', 'kind', 'approval_status', 'authorized_by', 'approved_utc',
    'protocol_id', 'design_fingerprint', 'execution_authorized', 'data_fitting_authorized',
    'test_release_authorized', 'scope', 'source_root', 'data_root', 'output_root',
    'runtime_fingerprint', 'configuration_fingerprint', 'host_reservation', 'data_identity'}


def configuration_fingerprint(design):
    return fingerprint_payload(design['jobs'])


def load_protocol(root):
    """Recompute the complete ratified design and every historical source pin."""
    root = Path(root).resolve()
    register = read_finite_json(root / PROTOCOL_PATH)
    design = register.get('design')
    if (not isinstance(design, dict) or register.get('design_fingerprint') != DESIGN_FINGERPRINT
            or fingerprint_payload(design) != DESIGN_FINGERPRINT
            or register.get('protocol_id') != PROTOCOL_ID or design.get('protocol_id') != PROTOCOL_ID):
        raise ValueError('Protocol design fingerprint changed; renewed owner approval required')
    if (len(design['decisions']) != 17 or len({d['id'] for d in design['decisions']}) != 17
            or len(design['jobs']) != 20 or len({j['job_id'] for j in design['jobs']}) != 20):
        raise ValueError('Protocol decision/job matrix is inconsistent')
    seen = set()
    for job in design['jobs']:
        if (fingerprint_payload(job['model_config']) != job['model_config_fingerprint']
                or any(dependency not in seen for dependency in job['dependencies'])
                or job['timeout_seconds'] != design['resources']['per_job_timeout_seconds'][job['kind']]):
            raise ValueError('Protocol configuration or dependency graph is inconsistent')
        seen.add(job['job_id'])
    for relative, identity in design['source_files'].items():
        path = root / relative
        if path.stat().st_size != identity['bytes'] or sha256_file(path) != identity['sha256']:
            raise ValueError(f'Protocol historical source identity changed: {relative}')
    return register


def _memory():
    if sys.platform == 'darwin':
        result = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    return int(os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE'))


def runtime_identity(root):
    """Bind clean actual executing source, Python, installed packages and host."""
    root = Path(root).resolve()
    provenance = code_provenance(root, require_clean=True, require_installed_match=True)
    if provenance['git_branch'] != 'codex/v2-experimental-validation-readiness':
        raise PermissionError('Pilot execution requires the isolated authorized V2 feature branch')
    packages = {d.metadata['Name'].lower().replace('_', '-'): d.version for d in distributions()
                if d.metadata.get('Name')}
    locks = {name: sha256_file(root / name) for name in
             ('requirements-lock.txt', 'requirements-training-lock.txt', 'requirements-v1-lock.txt', 'pyproject.toml')}
    environment = dict(python=sys.version, executable=str(Path(sys.executable).absolute()),
                       packages=dict(sorted(packages.items())), lock_files=locks)
    host = dict(hostname=socket.gethostname(), platform=platform.platform(), machine=platform.machine(),
                processor=platform.processor(), logical_cpus=os.cpu_count(), physical_memory_bytes=_memory())
    identity = dict(git_commit=provenance['git_commit'], git_branch=provenance['git_branch'],
        source_fingerprint=provenance['source']['fingerprint'], source_files=provenance['source']['files'],
        environment=environment, host=host, host_fingerprint=fingerprint_payload(host))
    return dict(identity, fingerprint=fingerprint_payload(identity))


def _path(value, label):
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise PermissionError(f'{label} must be an explicit absolute path')
    path = Path(value)
    if path.resolve() != path:
        raise PermissionError(f'{label} must not redirect through symlinks')
    return path


def validate_execution(root, approval):
    """Require separate G3/G4 claims before loader/output access; never create one.

    ``approval`` is a finite JSON mapping or an external file containing that
    mapping. File bytes themselves are bound by the canonical approval payload.
    Existing output is intentionally allowed here for supervised workers; the
    driver separately requires an absent output directory before creating it.
    """
    if approval is None:
        raise PermissionError('Separate host reservation and execution approval are required')
    root = Path(root).resolve()
    if not isinstance(approval, Mapping):
        path = _path(str(Path(approval).absolute()), 'approval file')
        if path.is_relative_to(root):
            raise PermissionError('Execution approval must be an external owner-supplied file')
        try:
            approval = read_finite_json(path)
        except (OSError, ValueError) as error:
            raise PermissionError(f'Invalid execution approval: {error}') from error
    else:
        approval = json.loads(canonical_json(dict(approval)))
    if not isinstance(approval, dict) or set(approval) != _APPROVAL_KEYS:
        raise PermissionError('Execution approval has missing or unrecognized fields')
    expected = dict(schema_version=1, kind='solarjepa_v2_pilot_execution_approval', approval_status='APPROVED',
        protocol_id=PROTOCOL_ID, design_fingerprint=DESIGN_FINGERPRINT, execution_authorized=True,
        data_fitting_authorized=True, test_release_authorized=False, scope=SCOPE)
    if any(type(approval[k]) is not type(v) or approval[k] != v for k, v in expected.items()):
        raise PermissionError('Execution approval must explicitly authorize only this bounded protocol and fitting scope')
    if not isinstance(approval['authorized_by'], str) or not approval['authorized_by'].strip():
        raise PermissionError('Execution approval requires a named owner')
    try:
        approved = datetime.fromisoformat(approval['approved_utc'].replace('Z', '+00:00'))
        if approved.utcoffset() is None or approved.utcoffset().total_seconds() != 0 or approved > datetime.now(timezone.utc):
            raise ValueError('UTC approval in past or present required')
    except (AttributeError, TypeError, ValueError) as error:
        raise PermissionError('Execution approval timestamp must be valid UTC') from error
    if _path(approval['source_root'], 'source_root') != root:
        raise PermissionError('Execution source root differs from the isolated implementation')
    data_root = _path(approval['data_root'], 'data_root')
    output = _path(approval['output_root'], 'output_root')
    if (output == root or output == data_root or output.is_relative_to(data_root / 'data')
            or output.is_relative_to(root / 'data') or output.is_relative_to(root / 'checkpoints')):
        raise PermissionError('Output reservation overlaps protected source/data/checkpoint storage')
    reservation = approval['host_reservation']
    if (not isinstance(reservation, dict) or set(reservation) != {'reserved', 'host_fingerprint', 'rationale'}
            or reservation['reserved'] is not True or not isinstance(reservation['rationale'], str)
            or not reservation['rationale'].strip()):
        raise PermissionError('Explicit named host reservation is required')
    protocol = load_protocol(root)
    ratification = protocol.get('owner_ratification') or {}
    implementation = protocol.get('implementation_approval') or {}
    if (ratification.get('approval_status') != 'APPROVED'
            or ratification.get('design_fingerprint') != DESIGN_FINGERPRINT
            or set(ratification.get('decision_ids', [])) != {d['id'] for d in protocol['design']['decisions']}
            or protocol.get('implementation_authorized') is not True
            or implementation.get('approval_status') != 'APPROVED'
            or implementation.get('design_fingerprint') != DESIGN_FINGERPRINT):
        raise PermissionError('G1 ratification and G2 implementation approval are required')
    data_identity = approval['data_identity']
    keys = {'dataset_fingerprint', 'forecast_fingerprint', 'split_fingerprint', 'split_fingerprints',
            'training_fingerprint', 'normalization_fingerprint', 'train_windows', 'validation_content_fingerprint'}
    if not isinstance(data_identity, dict) or set(data_identity) != keys:
        raise PermissionError('Execution approval requires exact data identity fields')
    history = protocol['design']['data']['normalization']
    for key in ('dataset_fingerprint', 'split_fingerprint', 'training_fingerprint', 'normalization_fingerprint'):
        historic = 'historical_expected_fingerprint' if key == 'normalization_fingerprint' else 'historical_expected_' + key
        if data_identity[key] != history[historic]:
            raise PermissionError('Execution approval data identity differs from frozen historical support')
    splits, subset = data_identity['split_fingerprints'], data_identity['train_windows']
    digest = lambda value: isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None
    if (not isinstance(splits, dict) or set(splits) != {'train', 'validation'}
            or not all(digest(value) for value in splits.values())
            or fingerprint_payload(splits) != data_identity['split_fingerprint']
            or not digest(data_identity['validation_content_fingerprint'])
            or not isinstance(subset, dict) or set(subset) != {
                'eligible', 'used', 'stride', 'cap', 'policy', 'subsample', 'fingerprint'}
            or any(type(subset[key]) is not int for key in ('eligible', 'used', 'stride', 'cap'))
            or not 0 < subset['used'] <= subset['eligible'] or subset['used'] != min(subset['eligible'], 20000)
            or subset['stride'] != 1 or subset['cap'] != 20000
            or subset['policy'] != 'complete_consecutive_raw_training_rows'
            or subset['subsample'] != ('evenly_spaced_chronological' if subset['eligible'] > 20000 else 'none')
            or not digest(subset['fingerprint'])):
        raise PermissionError('Execution approval data identity must bind complete support and validation content')
    from solar_flare_jepa.forecasting.contracts import ForecastSpec
    if data_identity['forecast_fingerprint'] != ForecastSpec(**protocol['design']['data']['forecast']).fingerprint:
        raise PermissionError('Execution approval forecast identity differs from the frozen protocol')
    runtime = runtime_identity(root)
    if approval['runtime_fingerprint'] != runtime['fingerprint']:
        raise PermissionError('Execution approval runtime identity differs from actual clean source/environment')
    if reservation['host_fingerprint'] != runtime['host_fingerprint']:
        raise PermissionError('Execution approval host reservation differs from actual host')
    if approval['configuration_fingerprint'] != configuration_fingerprint(protocol['design']):
        raise PermissionError('Execution approval configuration fingerprint differs')
    binding = fingerprint_payload(dict(approval=approval, runtime=runtime))
    return dict(protocol=protocol, design=protocol['design'], approval=approval, runtime=runtime,
                binding_fingerprint=binding)


def evaluation_identity(context, bundle):
    return dict(experiment_id=EXPERIMENT_ID, code_fingerprint=context['runtime']['source_fingerprint'],
        data_provenance_fingerprint=bundle.dataset.fingerprint,
        split_fingerprint=fingerprint_payload(bundle.evidence['split_fingerprints']),
        protocol_fingerprint=DESIGN_FINGERPRINT)


def validate_data_identity(context, bundle):
    """Recompute actual prepared support against separately approved identities."""
    from solar_flare_jepa.training.controlled import _validation_identity
    evidence = bundle.evidence
    actual = {key: evidence[key] for key in ('dataset_fingerprint', 'forecast_fingerprint',
        'split_fingerprint', 'split_fingerprints', 'training_fingerprint', 'normalization_fingerprint', 'train_windows')}
    actual['validation_content_fingerprint'] = _validation_identity(bundle.validation)['content_fingerprint']
    if actual != context['approval']['data_identity']:
        raise ValueError('Actual development data/support/normalization/validation identity differs from approval')
    return actual
