"""Read-only, authenticated inputs for the bounded retrospective V1 replication.

No predictor, fit, optimizer or normalization fit is called here. Runtime roots
locate immutable inputs; portable byte identities describe scientific inputs.
Checkpoint byte snapshots are deliberately outside the JSON identity records.
"""
from copy import deepcopy
from dataclasses import fields
import hashlib
import io
import json
import os
from pathlib import Path
import stat

import numpy as np

from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastSpec, ForecastTargets, FutureGrid, canonical_json,
    _immutable, fingerprint_payload, validate_alignment,
)
from solar_flare_jepa.training.jepa import JepaConfig, MODEL_IDS, MODEL_KIND, SCHEMA_VERSION
from solar_flare_jepa.training.normalization import Normalization
from solar_flare_jepa.training.core import _torch, _weights_fingerprint
from .config import _keys, _object, _reject_constant, utc_ns
from .provenance import _relative, _source_path, source_fingerprint, verify_artifacts


_VARIANTS = ('jepa_finetune', 'jepa_frozen', 'supervised')
_SEEDS = (17, 29, 43)
_QUANTILES = [.05, .25, .5, .75, .95]
_SPEC_FINGERPRINT = '094df46d625380c4c812bb26c9320cff10e40a2de185cfcebfa5dfff04674d94'
_CLASSICAL = ('persistence', 'training_mean', 'trailing_mean', 'drift', 'ar1', 'direct_ridge',
              'persistence_empirical', 'arima(2,1,0)', 'ar1-constant-normal', 'ar1-arch(1)-normal',
              'ar1-garch(1,1)-normal', 'ar1-garch(1,1)-t', 'ar1-gjr-garch(1,1)-t')
_RUNTIME_KEYS = {'code_root', 'historical_code_root', 'preparation_code_root'}


def _root(value):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise ValueError('Runtime locators must not contain path traversal')
    result = _source_path(path)
    if not result.is_dir():
        raise ValueError('Input root must be a directory')
    return result


def _snapshot(path, expected=None):
    """Hash exactly the bytes parsed; reject redirects and concurrent changes."""
    path = _source_path(path)
    try:
        with path.open('rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError('Input identity requires a regular file')
            payload = stream.read()
            after = os.fstat(stream.fileno())
        _source_path(path)
        current = path.stat()
    except OSError as error:
        raise ValueError(f'Cannot read input identity: {path.name}') from error
    attrs = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    if any(getattr(before, key) != getattr(after, key) or
           getattr(after, key) != getattr(current, key) for key in attrs):
        raise ValueError(f'Input identity changed during snapshot: {path.name}')
    identity = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    if expected is not None and identity != {key: expected[key] for key in ('bytes', 'sha256')}:
        raise ValueError(f'Input identity mismatch: {path.name}')
    return payload, identity


def _json(payload):
    try:
        value = json.loads(payload, object_pairs_hook=_object, parse_constant=_reject_constant)
        # Also rejects overflowed finite-looking literals, such as 1e999.
        canonical_json(value)
        return value
    except (TypeError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError('Input snapshot must contain strict finite JSON') from error


def _member(root, name):
    return root / str(_relative(name))


def _inventory(directory, entries):
    if not isinstance(entries, list) or not entries:
        raise ValueError('A nonempty pinned input identity inventory is required')
    names = [str(_relative(item['path'])) for item in entries]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate input identity path')
    snapshots, identities = {}, []
    for name, item in zip(names, entries):
        payload, identity = _snapshot(_member(directory, name), item)
        snapshots[name] = payload
        identities.append(dict(path=name, **identity))
    return snapshots, sorted(identities, key=lambda x: x['path'])


def _protocol(protocol):
    if not isinstance(protocol, dict):
        raise ValueError('An explicit frozen protocol is required')
    runtime = {key: protocol[key] for key in _RUNTIME_KEYS if key in protocol}
    frozen = _json(canonical_json({key: value for key, value in protocol.items() if key not in _RUNTIME_KEYS}))
    _keys(frozen, ('schema_version', 'evaluation_id', 'scope', 'claim', 'fitting_policy',
        'full_external_execution', 'readiness_ledger', 'preparation_acceptance', 'forecast',
        'checkpoint_cohort', 'classical_models', 'point_reference_parameters', 'quantile_levels',
        'metrics', 'uncertainty', 'external_interval', 'v1_support', 'simulation', 'exposure',
        'limitations', 'historical_input_files', 'preparation_input_files'))
    spec = ForecastSpec(**frozen['forecast'])
    planned = [dict(model=f'{variant}_seed{seed}', variant=variant, seed=seed,
                    path=f'{variant}_seed{seed}.pt') for variant in _VARIANTS for seed in _SEEDS]
    if frozen.get('checkpoint_cohort') != planned:
        raise ValueError('Frozen checkpoint cohort requires all nine planned variant/seed pairs')
    if (spec.fingerprint != _SPEC_FINGERPRINT or frozen.get('quantile_levels') != _QUANTILES
            or frozen.get('classical_models') != list(_CLASSICAL)):
        raise ValueError('Frozen scientific spec/channel order or model cohort changed')
    if (frozen.get('schema_version') != 1
            or frozen.get('scope') != 'bounded_retrospective_continuous_flux_replication'
            or frozen.get('claim') != 'temporally_disjoint_external_replication'
            or frozen.get('fitting_policy') != 'no_training_refitting_normalization_fitting_calibration_or_selection'
            or frozen['full_external_execution'] != 'requires_explicit_user_approval'):
        raise ValueError('Unsupported external evaluation scope or fitting policy')
    expected_metrics = dict(primary_loss='equal_origin_seed_mean_log10_dex_pinball',
        secondary_paired_loss='log10_dex_mae', quantile_weights=[1]*5, lead_weights=[1]*30,
        channel_weights=[1, 1], rmse_reduction='sqrt_pooled_squared_error')
    if (frozen['metrics'] != expected_metrics
            or frozen['simulation'] != dict(simulations=1000, sim_seed=0)):
        raise ValueError('Frozen evaluation metrics/weights or simulation settings changed')
    expected_exposure = dict(acquisition_commit='28e222ba042b32c84dad49a446f0849c677af4b9',
        documentation_commit='bd128295c8529e064473e483751ca747de2f57a5',
        prior_january_inspection='OBSERVED', unrecorded_access='UNKNOWN', confirmatory_status='UNAVAILABLE')
    if frozen['exposure'] != expected_exposure:
        raise ValueError('Frozen exposure/confirmatory protocol changed')
    expected_uncertainty = dict(block_days=[1, 3, 7], replicates=2000, seed=17, confidence=.95,
        alignment='UTC_epoch_nonoverlapping_calendar', minimum_support_seconds=9000,
        interpretation='descriptive_fixed_checkpoint_calendar_sensitivity')
    if frozen['uncertainty'] != expected_uncertainty:
        raise ValueError('Frozen descriptive uncertainty settings changed')
    interval = frozen['external_interval']
    if (utc_ns(interval['start_utc']), utc_ns(interval['end_utc'])) != (
            1735689600000000000, 1738368000000000000):
        raise ValueError('Frozen external support must remain January 2025')
    return frozen, runtime, spec


def _canonical_preparation(prep):
    context_record = _json(prep['contexts.json'])
    context_record['spec'] = ForecastSpec(**context_record['spec'])
    context = ForecastContext(**context_record)
    grid_record = _json(prep['future_grid.json'])
    grid_record['spec'] = ForecastSpec(**grid_record['spec'])
    grid = FutureGrid(**grid_record)
    targets_record = _json(prep['targets.json'])
    target_grid = targets_record['grid']
    target_grid['spec'] = ForecastSpec(**target_grid['spec'])
    targets = ForecastTargets(targets_record['values'], targets_record['mask'], FutureGrid(**target_grid))
    validate_alignment(context, grid)
    validate_alignment(grid, targets.grid)
    if not context.mask.all() or not targets.mask.all():
        raise ValueError('Frozen retained grid requires complete observation masks')
    context.spec.transform_features(context.values)
    targets.grid.spec.transform_targets(targets.values)
    return context, targets


def _candidate_axis(window, context, targets, summary, protocol):
    spec = context.spec
    if (ForecastSpec(**window['spec']).fingerprint != spec.fingerprint
            or window['spec_fingerprint'] != spec.fingerprint
            or window['dataset_fingerprint'] != context.dataset_fingerprint
            or summary['split_fingerprint'] != fingerprint_payload(window)):
        raise ValueError('Frozen window spec/dataset/support identity differs')
    start = utc_ns(protocol['external_interval']['start_utc'])
    end = utc_ns(protocol['external_interval']['end_utc'])
    if window['partition'] != dict(name='test', start_ns=start, end_ns=end):
        raise ValueError('Frozen external partition support differs')
    if (window['origin_policy'] != 'dataset_origin_stride_grid_partition_issue_half_open'
            or window['raw_starts_ns'][0] != start):
        raise ValueError('Unsupported candidate-origin grid anchor or policy')
    axis = np.arange(start, end, spec.stride_steps*spec.cadence_ns, dtype=np.int64)
    retained = list(context.origin_ids)
    if window['retained_origins'] != retained:
        raise ValueError('Retained grid order differs from candidate manifest')
    support = window['support_manifest']
    if [item['origin_id'] for item in support] != retained:
        raise ValueError('Retained support manifest order differs')
    for index, item in enumerate(support):
        issue = int(context.issue_times_ns[index])
        a = issue-(spec.context_steps+spec.feature_lookback_steps)*spec.cadence_ns
        b = issue+(spec.horizon_steps+spec.label_maturity_steps)*spec.cadence_ns
        coordinates = dict(issue_time_ns=issue, feature_lookback_start_ns=a,
            context_start_ns=int(context.starts_ns[index, 0]), context_end_ns=issue,
            target_start_ns=issue, target_end_ns=int(targets.grid.ends_ns[index, -1]),
            label_maturity_ns=b, start_ns=a, end_ns=b)
        if (item['origin_id'] != f'origin:{issue}' or any(item.get(k) != v for k, v in coordinates.items())
                or a < start or b > end or item.get('event_group_ids')):
            raise ValueError('Retained full dependency support differs from canonical grid')
    exclusions = deepcopy(window['excluded_origins'])
    excluded_times = []
    for item in exclusions:
        issue = item['issue_time_ns']
        if (type(issue) is not int or item['origin_id'] != f'origin:{issue}'
                or not isinstance(item.get('reasons'), list) or not item['reasons']
                or any(not isinstance(reason, str) or not reason for reason in item['reasons'])):
            raise ValueError('Invalid candidate observation exclusion')
        excluded_times.append(issue)
    combined = list(map(int, context.issue_times_ns)) + excluded_times
    if len(set(combined)) != len(combined) or sorted(combined) != axis.tolist():
        raise ValueError('Retained/excluded candidate axis must be exhaustive and disjoint')
    if excluded_times != sorted(excluded_times):
        raise ValueError('Candidate exclusions must retain chronological order')
    if (summary['retained_origins'] != len(retained) or summary['excluded_origins'] != len(exclusions)
            or summary['valid_target_cells'] != int(targets.mask.sum())):
        raise ValueError('Preparation candidate/retained target count differs')
    axis = _immutable(axis, np.int64)
    indices = _immutable(np.searchsorted(axis, context.issue_times_ns), np.int64)
    return axis, exclusions, indices


def _separation(summary, context, targets, protocol):
    partitions = [item['partition'] for item in summary['split_manifest']]
    expected = [dict(name=row['name'], start_ns=utc_ns(row['start_utc']), end_ns=utc_ns(row['end_utc']))
                for row in protocol['v1_support']]
    if partitions != expected or [p['name'] for p in partitions] != ['train', 'validation', 'test']:
        raise ValueError('Full V1 train/validation/test support differs from frozen protocol')
    if (partitions[0]['start_ns'] != 1714521600000000000
            or partitions[-1]['end_ns'] != 1725148800000000000
            or summary['dataset']['starts_ns'] != partitions[0]['start_ns']
            or summary['dataset']['ends_ns'] != partitions[-1]['end_ns']):
        raise ValueError('Full V1 May-Aug support must remain frozen')
    spec = context.spec
    starts = context.starts_ns[:, 0] - spec.feature_lookback_steps*spec.cadence_ns
    ends = targets.grid.ends_ns[:, -1] + spec.label_maturity_steps*spec.cadence_ns
    for partition in partitions:
        if np.any((starts < partition['end_ns']) & (ends > partition['start_ns'])):
            raise ValueError('External full dependency support overlaps V1 support')
    if context.dataset_fingerprint == summary['dataset']['fingerprint']:
        raise ValueError('External dataset must retain a distinct input identity')


def _checkpoint_records(snapshots, summary, ledger, protocol, spec):
    jepa = summary['models_config']['jepa']
    if jepa['seeds'] != list(_SEEDS) or jepa['variants'] != list(_VARIANTS):
        raise ValueError('Original V1 model cohort differs from the planned seeds/variants')
    planned_names = [x['model'] for x in protocol['checkpoint_cohort']]
    actual = sorted(name for name, fit in summary['fits'].items() if 'record' in fit)
    if actual != sorted(planned_names):
        raise ValueError('Missing or additional original V1 checkpoint cohort record')
    normalizer = Normalization.from_dict(ledger['checkpoint_audit']['checks']['normalization']['record'])
    training_identity = ledger['checkpoint_audit']['checks']['reconstruction']['training_fingerprint']
    torch = _torch()
    records = []
    required = {'schema_version', 'model_kind', 'variant', 'model_id', 'config_json',
                'normalization_json', 'record_json', 'model_state', 'weights_fingerprint', 'torch_version'}
    for planned in protocol['checkpoint_cohort']:
        name, path = planned['model'], planned['path']
        if path not in snapshots:
            raise ValueError('Missing planned checkpoint identity')
        try:
            payload = torch.load(io.BytesIO(snapshots[path]), map_location='cpu', weights_only=True)
        except Exception as error:
            raise ValueError('Checkpoint safe snapshot deserialization failed') from error
        if (not isinstance(payload, dict) or set(payload) != required
                or payload['schema_version'] != SCHEMA_VERSION or payload['model_kind'] != MODEL_KIND
                or payload['variant'] != planned['variant'] or payload['model_id'] != MODEL_IDS[planned['variant']]):
            raise ValueError('Checkpoint kind/variant/schema differs from planned cohort')
        config = _json(payload['config_json'])
        resolved_config = JepaConfig(**config).as_dict()
        record = _json(payload['record_json'])
        norm = Normalization.from_dict(_json(payload['normalization_json']))
        if (config != resolved_config or record != summary['fits'][name]['record']
                or record['config'] != config or record['seed'] != planned['seed']
                or config['seed'] != planned['seed'] or record['variant'] != planned['variant']
                or record['model_id'] != payload['model_id'] or record['model_kind'] != MODEL_KIND
                or {k: v for k, v in config.items() if k != 'seed'} != jepa['config']
                or config['quantiles'] != protocol['quantile_levels']):
            raise ValueError('Checkpoint record/config/seed differs from frozen V1 cohort')
        if (norm.fingerprint != normalizer.fingerprint or norm.spec.fingerprint != spec.fingerprint
                or record['normalization_fingerprint'] != norm.fingerprint
                or record['spec_fingerprint'] != spec.fingerprint
                or record['training_fingerprint'] != training_identity
                or record['training_dataset_fingerprint'] != summary['dataset']['fingerprint']):
            raise ValueError('Checkpoint training/spec/normalization identity differs')
        if _weights_fingerprint(payload['model_state']) != payload['weights_fingerprint']:
            raise ValueError('Checkpoint internal weight identity differs')
        records.append(dict(**planned, record=record, normalization=_json(canonical_json(norm.as_dict())),
            weights_fingerprint=payload['weights_fingerprint'], checkpoint_bytes=snapshots[path],
            identity=deepcopy(ledger['checkpoint_audit']['artifacts'][path])))
    return records


def load_frozen_inputs(v1_dir: Path, preparation_dir: Path, protocol: dict) -> dict:
    """Authenticate and detach inputs without inference/fitting.

    ``code_root`` (default cwd), ``historical_code_root`` and
    ``preparation_code_root`` are runtime-only protocol overrides. The last two
    default to the corresponding artifact directory's repository ancestor.
    Scientific JSON identities never contain these roots. Publication must call
    :func:`reverify_frozen_inputs` against the original locators before writing.
    """
    frozen, runtime, spec = _protocol(protocol)
    code_root = _root(runtime.get('code_root', Path.cwd()))
    v1_dir, preparation_dir = _root(v1_dir), _root(preparation_dir)
    historical_root = _root(runtime.get('historical_code_root', v1_dir.parents[2]))
    preparation_root = _root(runtime.get('preparation_code_root', preparation_dir.parents[2]))
    ledger_identity = frozen['readiness_ledger']
    ledger_bytes, _ = _snapshot(_member(code_root, ledger_identity['path']), ledger_identity)
    ledger = _json(ledger_bytes)
    v1_entries = [dict(path=name, **identity) for name, identity in ledger['checkpoint_audit']['artifacts'].items()]
    v1, v1_identities = _inventory(v1_dir, v1_entries)
    expected_names = sorted(item['path'] for item in v1_entries)
    actual_names = sorted(p.relative_to(v1_dir).as_posix() for p in v1_dir.rglob('*') if p.is_file())
    if actual_names != expected_names:
        raise ValueError('V1 artifact identity file set differs')
    prep_entries = [dict(path=item['name'], bytes=item['bytes'], sha256=item['sha256'])
        for item in ledger['dataset_audit']['acceptance'][frozen['preparation_acceptance']]['artifacts']]
    prep, prep_identities = _inventory(preparation_dir, prep_entries)
    # Reuse the published manifest validator, then independently bind its exact
    # consumed snapshot to the ledger and every parsed member.
    verified_manifest = verify_artifacts(preparation_dir)
    pinned_manifest = _json(prep['artifacts.json'])
    if verified_manifest != pinned_manifest:
        raise ValueError('Preparation manifest identity changed during verification')
    manifest_entries = sorted(pinned_manifest['files'], key=lambda x: x['path'])
    if manifest_entries != [item for item in prep_identities if item['path'] != 'artifacts.json']:
        raise ValueError('Preparation manifest/member identities differ from readiness ledger')
    historical_bytes, historical_identities = _inventory(historical_root, frozen['historical_input_files'])
    if frozen['preparation_input_files']:
        preparation_source, preparation_source_identities = _inventory(preparation_root, frozen['preparation_input_files'])
    else:
        preparation_source, preparation_source_identities = {}, []
    summary = _json(v1['summary.json'])
    if summary['status'] != 'complete' or summary.get('quick') is not False or summary.get('failures'):
        raise ValueError('Original V1 run must remain the completed full run')
    original_config = _json(historical_bytes['configs/experiments/v1_goes_2024.json'])
    original_models = _json(historical_bytes['configs/experiments/v1_models.json'])
    if (ForecastSpec(**summary['config']['forecast']).fingerprint != spec.fingerprint
            or ForecastSpec(**original_config['forecast']).fingerprint != spec.fingerprint
            or original_models != summary['models_config']
            or original_config['dataset'] != summary['config']['dataset']):
        raise ValueError('Original configuration bytes/spec/model declarations differ')
    context, targets = _canonical_preparation(prep)
    prep_summary = _json(prep['summary.json'])
    dataset_manifest = _json(prep['dataset_manifest.json'])
    for declaration in (prep_summary, _json(prep['resolved_config.json'])):
        if ForecastSpec(**declaration['forecast']).fingerprint != spec.fingerprint:
            raise ValueError('Preparation forecast spec differs from frozen V1 spec')
    if (context.spec.fingerprint != spec.fingerprint or prep_summary['spec_fingerprint'] != spec.fingerprint
            or prep_summary['dataset_fingerprint'] != context.dataset_fingerprint
            or prep_summary['fit_performed'] is not False
            or dataset_manifest['preprocessing']['fit_performed'] is not False):
        raise ValueError('External input identity/spec or no-fitting declaration differs')
    window = _json(prep['window_manifest.json'])
    axis, exclusions, indices = _candidate_axis(window, context, targets, prep_summary, frozen)
    _separation(summary, context, targets, frozen)
    records = _checkpoint_records(v1, summary, ledger, frozen, spec)
    classical = {}
    training_identity = records[0]['record']['training_fingerprint']
    for name in frozen['classical_models']:
        parameters = deepcopy(summary['fits'][name]['parameters'])
        if (parameters['spec_fingerprint'] != spec.fingerprint
                or parameters['dataset_fingerprint'] != summary['dataset']['fingerprint']
                or parameters['training_fingerprint'] != training_identity):
            raise ValueError('Frozen classical fit training/spec/dataset identity differs')
        classical[name] = parameters
    if summary['selections']['arima']['selected'] != 'arima(2,1,0)':
        raise ValueError('Historical ARIMA selection differs from frozen reference')
    identities = dict(schema_version=1, readiness_ledger=deepcopy(ledger_identity),
        v1_artifacts=v1_identities, preparation_artifacts=prep_identities,
        historical_inputs=historical_identities, preparation_inputs=preparation_source_identities,
        protocol_fingerprint=fingerprint_payload(frozen), spec_fingerprint=spec.fingerprint,
        original_dataset_fingerprint=summary['dataset']['fingerprint'],
        external_dataset_fingerprint=context.dataset_fingerprint,
        external_split_fingerprint=prep_summary['split_fingerprint'])
    current_source = dict(source=source_fingerprint(code_root),
        loader_module=dict(path='src/solar_flare_jepa/experiments/external_inputs.py',
                           **_snapshot(Path(__file__))[1]))
    return dict(context=context, targets=targets, candidate_issue_times_ns=axis,
        candidate_exclusions=exclusions, retained_candidate_indices=indices,
        checkpoint_records=records, classical_fit_records=classical,
        input_identities=identities, input_fingerprint=fingerprint_payload(identities),
        protocol=frozen, protocol_fingerprint=identities['protocol_fingerprint'],
        v1_summary=summary, preparation_summary=prep_summary, window_manifest=window,
        dataset_manifest=dataset_manifest, historical_source=deepcopy(summary['provenance']),
        current_source=current_source)


def _consumption_binding(value):
    """Describe live payload content, independently of its claimed identities."""
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            raise ValueError('Frozen consumption arrays must have primitive content')
        return ['array', value.dtype.str, list(value.shape),
                hashlib.sha256(value.tobytes(order='C')).hexdigest()]
    if isinstance(value, bytes):
        return ['bytes', len(value), hashlib.sha256(value).hexdigest()]
    if type(value) in (ForecastContext, ForecastTargets, FutureGrid, ForecastSpec):
        return ['contract', type(value).__name__,
                {field.name: _consumption_binding(getattr(value, field.name))
                 for field in fields(type(value))}]
    if isinstance(value, dict):
        return ['mapping', {key: _consumption_binding(part) for key, part in dict.items(value)}]
    if isinstance(value, (list, tuple)):
        return ['sequence', [_consumption_binding(part) for part in value]]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise ValueError('Unsupported frozen consumption payload type')


def reverify_frozen_inputs(frozen: dict, v1_dir: Path, preparation_dir: Path, protocol: dict) -> None:
    """Bind live consumption state to freshly authenticated original snapshots.

    This checks every returned field, including byte snapshots, fitted state,
    canonical contracts, candidate mapping, exclusions and source declarations.
    Caller-supplied identity/fingerprint assertions are never proof of that state.
    """
    current = load_frozen_inputs(v1_dir, preparation_dir, protocol)
    if fingerprint_payload(_consumption_binding(current)) != fingerprint_payload(_consumption_binding(frozen)):
        raise ValueError('Frozen consumption/input/source identity changed before publication')
