"""Deterministic, development-only M5 planning. There is no training entrypoint.

The historical proposal is preserved verbatim. An unapproved amendment records
the per-seed linear requirement and restricted data selection. No approval flag
can make this module execute an optimizer, release data, or run inference.
"""
from pathlib import Path

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.forecasting.contracts import fingerprint_payload
from .config import read_finite_json

CONFIG = 'configs/v2_proposed/'
DECISIONS = ('D09', 'D10', 'D11', 'DATA_ACCESS', 'AUGUST', 'QUALITY', 'SEEDS',
             'BUDGETS', 'LOSSES', 'CHECKPOINT', 'TCN', 'LINEAR', 'CLASSICAL',
             'FAILURE_RETRY', 'STATISTICS', 'TEST_PROHIBITION', 'REPRODUCIBILITY')
# Pin original M4A proposals and the M5 amendment/decision policies. A future
# approved protocol requires a new reviewed integration; changing a JSON flag
# is deliberately insufficient to authorize any execution in M5.0.
POLICY_STATUSES = {'PROPOSED', 'REQUIRES_APPROVAL', 'BLOCKED_ON_EVIDENCE'}


def _inputs(root):
    root = Path(root)
    proposal = read_finite_json(root / CONFIG / 'feasibility_pilot_proposal.json')
    protocol = read_finite_json(root / CONFIG / 'training_protocol_proposal.json')
    amendment = read_finite_json(root / CONFIG / 'm5_0_preflight_amendment.json')
    for name, expected in amendment['source_sha256'].items():
        if name not in ('feasibility_pilot_proposal.json', 'training_protocol_proposal.json'):
            raise ValueError('Unsupported source proposal')
        if sha256_file(root / CONFIG / name) != expected:
            raise ValueError('Historical proposal identity differs; new protocol review required')
    if set(amendment['source_sha256']) != {'feasibility_pilot_proposal.json', 'training_protocol_proposal.json'}:
        raise ValueError('Missing original proposal identity')
    if (proposal['approved'] is not False or protocol['approved'] is not False
            or amendment['approved'] is not False or amendment['execution_scope'] != 'PREFLIGHT_ONLY'
            or amendment['test_release_permitted'] is not False
            or amendment['statistical_reporting'] != ['DESCRIPTIVE_ONLY', 'INFERENCE_UNAVAILABLE']):
        raise ValueError('M5.0 accepts only unapproved preflight proposals')
    return proposal, protocol, amendment


def build_plan(root):
    proposal, protocol, amendment = _inputs(root)
    seeds = proposal['seeds']
    if seeds != protocol['settings']['seeds']['value'][:2] or len(set(seeds)) != 2:
        raise ValueError('Two proposed paired seeds required')
    fingerprint = fingerprint_payload(dict(proposal=proposal, protocol=protocol, amendment=amendment))
    jobs = []
    def add(seed, arm, kind, cohort, dependencies=()):
        job_id = f'{len(jobs):02d}-{seed}-{cohort}-{arm}'
        jobs.append(dict(job_id=job_id, seed=seed, arm=arm, kind=kind, cohort=cohort,
                         dependencies=list(dependencies),
                         proposed_timeout_seconds=proposal['resource_ceilings']['per_job_timeout_seconds'][kind]))
        return job_id
    for seed in seeds:
        ssl = add(seed, 'ssl', 'ssl_phase', 'shared_ssl')
        for arm in protocol['arms']:
            add(seed, arm, 'neural_downstream', 'primary', [ssl] if arm.startswith('jepa') else [])
        add(seed, 'tcn', 'tcn', 'baseline')
        add(seed, 'quantile_linear', 'quantile_linear', 'baseline')
        for arm in ('jepa_finetune', 'supervised'):
            add(seed, arm, 'neural_downstream', 'normalized_pinball_v1', [ssl] if arm.startswith('jepa') else [])
    return dict(schema_version=1, experiment_id='solarjepa-v2-m5-two-seed-goes-feasibility-proposed',
                configuration_fingerprint=fingerprint, seeds=seeds,
                seed_cohort_identity=fingerprint_payload(dict(seeds=seeds, configuration_fingerprint=fingerprint)),
                planned_model_arms=list(protocol['arms']), jobs=jobs, estimated_job_count=len(jobs),
                quantile_linear_candidate_fits=len(seeds) * len(protocol['settings']['quantile_linear']['value']['lambdas']),
                classical_jobs_status=amendment['classical_policy'],
                job_count_scope='20 specified process jobs; classical jobs unresolved, 14 linear candidates nested in 2 jobs',
                proposed_resource_ceilings=amendment['resource_ceilings'],
                data_selection=amendment['development_manifests'], splits=amendment['splits_utc_half_open'])


def check_approvals(register, configuration_fingerprint):
    if (not isinstance(register, dict) or type(register.get('schema_version')) is not int
            or register.get('schema_version') != 1
            or register.get('kind') != 'solarjepa_v2_m5_0_approval_register'
            or register.get('authorization_scope') != 'M5_0_PREFLIGHT_ONLY'
            or register.get('configuration_fingerprint') != configuration_fingerprint):
        raise ValueError('Invalid approval register/configuration fingerprint')
    decisions = register.get('decisions')
    if (not isinstance(decisions, list) or len(decisions) != len(DECISIONS)
            or any(not isinstance(d, dict) or type(d.get('identifier')) is not str for d in decisions)
            or {d.get('identifier') for d in decisions} != set(DECISIONS)):
        raise ValueError('Approval register must cover each required decision exactly once')
    required = {'identifier', 'title', 'proposed_policy', 'evidence', 'status', 'required_approver',
                'configuration_fingerprint', 'implementation_dependency', 'approval'}
    for d in decisions:
        if (set(d) != required or d['configuration_fingerprint'] != configuration_fingerprint
                or type(d['status']) is not str or d['status'] not in POLICY_STATUSES or d['approval'] is not None
                or not isinstance(d['evidence'], list) or not d['evidence']
                or any(not isinstance(d[k], str) or not d[k].strip() for k in (
                    'title', 'required_approver', 'implementation_dependency'))):
            raise ValueError('Invalid or unrecognized approval; M5.0 has no authorized experimental decisions')
    if fingerprint_payload(decisions) != DECISION_POLICIES_FINGERPRINT:
        raise ValueError('Approval decision policies changed; reviewed amendment required')
    return sorted(DECISIONS)


def load_approval_register(root, configuration_fingerprint):
    register = read_finite_json(Path(root) / CONFIG / 'm5_0_approval_register.json')
    check_approvals(register, configuration_fingerprint)
    return register


def inspect_data(root):
    from solar_flare_jepa.data.goes_v2_development import load_development, MANIFEST_PINS, _metadata
    from solar_flare_jepa.data import goes_acquisition
    # Enumerate explicit pins only; restoration.inventory scans the entire tree.
    try:
        _metadata(Path(root).resolve())
        missing = []
        for relative, _ in MANIFEST_PINS:
            manifest = read_finite_json(Path(root) / relative)
            missing.extend(r['path'] for r in manifest['files']
                           if not goes_acquisition._path(r['path'], Path(root).resolve()).is_file())
        if missing:
            return dict(status='DATA_NOT_READY', missing_files=len(missing), missing_paths=missing,
                        dataset_fingerprint=None, split_fingerprint=None, test_windows_built=False)
        bundle = load_development(root)
    except (ValueError, OSError) as error:
        return dict(status='DATA_NOT_READY', reason=str(error), dataset_fingerprint=None,
                    split_fingerprint=None, test_windows_built=False)
    return {**bundle.evidence, 'status': 'DATA_READY', 'test_windows_built': False}


def preflight(root, *, verify_data=True):
    from .provenance import code_provenance
    root = Path(root).resolve()
    plan = build_plan(root)
    register = load_approval_register(root, plan['configuration_fingerprint'])
    approvals = check_approvals(register, plan['configuration_fingerprint'])
    provenance = code_provenance(root, require_clean=False)
    # Select stable provenance fields: the list of already-imported modules can
    # differ between otherwise identical in-process calls.
    code = {k: provenance[k] for k in ('git_commit', 'git_branch', 'tracked_dirty', 'packages', 'python', 'platform')}
    code['source_fingerprint'] = provenance['source']['fingerprint']
    data = inspect_data(root) if verify_data else dict(status='NOT_CHECKED', dataset_fingerprint=None,
                                                      split_fingerprint=None, test_windows_built=False)
    after = code_provenance(root, require_clean=False)
    if (any(after[k] != code[k] for k in ('git_commit', 'git_branch', 'tracked_dirty', 'packages', 'python', 'platform'))
            or after['source']['fingerprint'] != code['source_fingerprint']
            or build_plan(root) != plan
            or load_approval_register(root, plan['configuration_fingerprint']) != register):
        raise ValueError('Code/configuration/approval identities changed during preflight')
    return dict(kind='solarjepa_v2_m5_0_preflight', schema_version=1, plan=plan, code=code,
                experiment_identity=fingerprint_payload(dict(plan=plan, code=code, data=data)),
                data_readiness=data, outstanding_approvals=approvals,
                approval_register_fingerprint=fingerprint_payload(register),
                execution_readiness='PILOT_NOT_AUTHORIZED', execution_scope='M5_0_PREFLIGHT_ONLY',
                statistical_reporting=['DESCRIPTIVE_ONLY', 'INFERENCE_UNAVAILABLE'],
                test_release_permitted=False, training_executed=False,
                readiness_reason='All experimental decisions remain unapproved; this entrypoint cannot train')


# Generated from the initial, unapproved, reviewed-in-code register. This pins
# policy content as well as configuration; it conveys no experimental approval.
DECISION_POLICIES_FINGERPRINT = 'e368e2ac4ec9c583b82b27d808b974a1883931303e357371104ec2a9d8959c7b'
