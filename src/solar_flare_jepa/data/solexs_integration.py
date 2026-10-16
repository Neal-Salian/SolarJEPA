"""Pinned offline SoLEXS native preparation/readiness audit, without model use."""
import hashlib
import json
from pathlib import Path
import re

from solar_flare_jepa.experiments.config import _object, _reject_constant
from solar_flare_jepa.experiments.provenance import (
    atomic_record, code_provenance, verify_source_identities,
)
from .solexs import inspect_solexs_archive
from .solexs_interface import iter_native_batches, require_native_request
from .storage import repository_relative_path, validate_inventory, verify_inventory


GATES = {'E1': 'BLOCKED_EXTERNAL_EVIDENCE', 'E2': 'BLOCKED_EXTERNAL_EVIDENCE',
         'E3': 'BLOCKED_EXTERNAL_EVIDENCE', 'E4': 'PARTIALLY_VERIFIED',
         'E5': 'PARTIALLY_VERIFIED', 'E6': 'BLOCKED_EXTERNAL_EVIDENCE'}
CONFIG_KEYS = {'schema_version', 'representation', 'inventory', 'phase_e',
               'source_manifests', 'archives', 'chunk_rows', 'expected_native_step'}


def _snapshot(root, path):
    relative = repository_relative_path(path, root)
    with (root/relative).open('rb') as stream:
        data = stream.read(2*1024**2+1)
    if len(data) > 2*1024**2:
        raise ValueError('Native audit JSON byte limit exceeded')
    identity = dict(path=relative, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    verify_source_identities(root, [identity])
    return json.loads(data, object_pairs_hook=_object, parse_constant=_reject_constant), identity


def _pin(value):
    if (not isinstance(value, dict) or set(value) != {'path', 'bytes', 'sha256'}
            or type(value['path']) is not str or type(value['bytes']) is not int or value['bytes'] < 0
            or type(value['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}', value['sha256'])):
        raise ValueError('Expected complete portable input identity')
    return value


def _pinned_json(root, pin):
    _pin(pin)
    payload, observed = _snapshot(root, pin['path'])
    if observed != pin:
        raise ValueError('Pinned manifest identity differs')
    return payload


def _config(value):
    if (not isinstance(value, dict) or set(value) != CONFIG_KEYS
            or type(value['schema_version']) is not int or value['schema_version'] != 1):
        raise ValueError('Unsupported native audit configuration/schema')
    require_native_request(value['representation'])
    if (type(value['chunk_rows']) is not int or not 1 <= value['chunk_rows'] <= 8192
            or type(value['expected_native_step']) is not int or value['expected_native_step'] != 1):
        raise ValueError('Audit uses bounded chunks and one native numerical step only')
    for key, cap in [('archives', 4), ('source_manifests', 8)]:
        if not isinstance(value[key], list) or not 1 <= len(value[key]) <= cap:
            raise ValueError('Expected bounded explicit archive/evidence selection')
    _pin(value['inventory']); _pin(value['phase_e'])
    for pin in value['source_manifests']:
        _pin(pin)
    return value


def _gate(value):
    if (not isinstance(value, dict) or type(value.get('schema_version')) is not int
            or value['schema_version'] != 1 or value.get('gate') != 'BLOCKED_FOR_PHASE_E'
            or value.get('forecast_training_allowed') is not False
            or value.get('physical_analysis_allowed') is not False):
        raise ValueError('Unsupported Phase E gate; independent scientific review required')
    gates = value.get('gates')
    if (not isinstance(gates, list) or len(gates) != len(GATES)
            or any(not isinstance(g, dict) or type(g.get('id')) is not str for g in gates)
            or len({g['id'] for g in gates}) != len(GATES)
            or {g['id']: g.get('status') for g in gates} != GATES):
        raise ValueError('Phase E gates changed, duplicated or unknown; review required')
    return gates


def _documentary_sources(root, manifests):
    sources = {}
    for pin in manifests:
        manifest = _pinned_json(root, pin)
        entries = manifest.get('sources') if isinstance(manifest, dict) else None
        if not isinstance(entries, list) or not 1 <= len(entries) <= 64:
            raise ValueError('Unsupported documentary source manifest')
        for entry in entries:
            if not isinstance(entry, dict) or not {'path', 'bytes', 'sha256'} <= set(entry):
                raise ValueError('Missing documentary source identity')
            identity = _pin({k: entry[k] for k in ('path', 'bytes', 'sha256')})
            key = identity['path'].casefold()
            if key in sources and sources[key] != identity:
                raise ValueError('Conflicting documentary source identities')
            sources[key] = identity
    result = sorted(sources.values(), key=lambda s: s['path'])
    verify_source_identities(root, result)
    return result


def _prepared(root, record, summary, chunk_rows):
    members, gti_provenance = {}, {}
    for product in summary['products']:
        if product['kind'] != 'gti':
            continue
        detector = product['detector']['value']
        if detector in members:
            raise ValueError('Ambiguous GTI selection for one detector; explicit source review required')
        members[detector] = product['provenance']['member']
        gti_provenance[detector] = product['provenance']
    prepared = []
    for product in summary['products']:
        if product['kind'] not in ('lc', 'pi'):
            continue
        counts, flags, rows, batches = {}, {}, 0, 0
        digest = hashlib.sha256()
        gti_counts = dict(closed_points=0, half_open_points=0, endpoint_disagreements=0)
        has_gti = product['detector']['value'] in members
        for batch in iter_native_batches(root, record, product['provenance']['member'],
                chunk_rows=chunk_rows, gti_member=members.get(product['detector']['value'])):
            q = batch.quality.summary()
            rows += q['rows']; batches += 1
            for name, number in q['counts'].items():
                counts[name] = counts.get(name, 0) + number
            for name, number in q['row_flags'].items():
                flags[name] = flags.get(name, 0) + number
            if batch.gti is not None:
                diagnostics = batch.gti.summary()
                for name in gti_counts:
                    gti_counts[name] += diagnostics[name]
            digest.update(batch.fingerprint.encode('ascii'))
        if rows != product['rows']:
            raise ValueError('Native preparation did not conserve source rows')
        prepared.append(dict(kind=product['kind'], detector=product['detector'],
            provenance=product['provenance'], rows=rows, batches=batches,
            column_units={c['name']: c['unit'] for h in product['hdus'] for c in h['columns']},
            native_time_metadata=product['time_metadata'], warnings=product['warnings'],
            batch_sequence_sha256=digest.hexdigest(),
            numerical_quality=dict(counts=counts, row_flags=flags,
                scientific_quality='UNKNOWN_NOT_APPLIED', filter_applied=False),
            gti_provenance=gti_provenance.get(product['detector']['value']),
            gti=dict(**gti_counts, clock_compatibility='UNKNOWN',
                endpoint_policy='UNKNOWN_NOT_APPLIED', continuous_exposure=None,
                filter_applied=False) if has_gti else None))
    return prepared


def audit_native_inputs(config_path, root):
    """Rebuild facts from explicit immutable inputs; publish no files or arrays.

    As with existing readers, temporary bounded FITS scratch is created beneath
    root/.cache and removed. Config/manifests are parsed from single snapshots;
    every selected input is reverified before returning the complete report.
    """
    root = Path(root).resolve()
    config, config_identity = _snapshot(root, config_path)
    config = _config(config)
    phase_e = _pinned_json(root, config['phase_e'])
    gates = _gate(phase_e)
    inventory = _pinned_json(root, config['inventory'])
    validate_inventory(inventory)
    documentary = _documentary_sources(root, config['source_manifests'])
    requested = [repository_relative_path(p, root) for p in config['archives']]
    if len({p.casefold() for p in requested}) != len(requested):
        raise ValueError('Archive selection must be distinct')
    registered = {r['path']: r for r in inventory['files']}
    if not set(requested) <= set(registered):
        raise ValueError('Unregistered native archive selection')
    records = [registered[p] for p in sorted(requested)]
    archives = []
    for record in records:
        summary = inspect_solexs_archive(root, record, chunk_rows=config['chunk_rows'])
        prepared = _prepared(root, record, summary, config['chunk_rows'])
        archives.append(dict(archive=record['path'], archive_sha256=record['sha256'],
                             native_integrity=summary, prepared_products=prepared))
    pins = [config_identity, config['inventory'], config['phase_e'], *config['source_manifests']]
    verify_source_identities(root, [*pins, *documentary])
    verify_inventory(dict(inventory, files=records, missing_coverage=[]), root)
    return dict(schema_version=1, evidence='OBSERVED', scope='Explicit registered native pilot only',
        representation='native_values_and_encoded_metadata',
        inputs=dict(config=config_identity, inventory=config['inventory'], phase_e=config['phase_e'],
                    source_manifests=config['source_manifests'], verified_documentary_sources=documentary),
        readiness=dict(verdict='NATIVE_INTERFACE_READY_SCIENCE_BLOCKED',
            native_preparation='VERIFIED_FOR_SELECTED_INPUTS', gates=gates,
            jepa_training_allowed=False, physical_analysis_allowed=False,
            required_next_evidence=['Applicable clock/bin/availability contract',
                'Detector/pipeline/epoch response and channel correspondence',
                'GTI/exposure/deadtime/HK quality reference',
                'Scientific quantity, target, uncertainty and unit contract']),
        policies=dict(utc_conversion=False, local_calibration=False, unit_conversion=False,
            gti_filtering=False, gap_filling=False, sorting=False, normalization=False,
            channel_mapping=False, cross_source_alignment=False, training_executed=False,
            upstream_calibration_and_correction_state='UNKNOWN'), archives=archives)


def run_native_audit(config_path, *, project_root, data_root, output_dir):
    """Capture executed/installed source and exclusively publish a JSON audit.

    Publication reuses the repository's atomic, no-replacement artifact writer.
    Source must be clean and normally installed; no models are imported or run.
    """
    project_root = Path(project_root).resolve()
    code = code_provenance(project_root)
    report = audit_native_inputs(config_path, data_root)
    after = code_provenance(project_root)
    if code['source'] != after['source'] or code['git_commit'] != after['git_commit']:
        raise ValueError('Executed project source changed during native audit')
    report['code'] = after
    return atomic_record(project_root, output_dir, {'report.json': report})
