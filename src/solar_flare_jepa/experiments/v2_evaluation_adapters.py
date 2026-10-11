"""Thin M4B validation adapters. No protocol approval or inference is supplied.

The split convention is versioned for development integration; adopting it for
an approved experiment is a separate decision. All test input is a declaration
string. No data loaders or test-release routines are imported here.
"""
from collections.abc import Mapping
from dataclasses import replace
import math
import statistics

from solar_flare_jepa.evaluation.comparison import DAY_NS
from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from solar_flare_jepa.training.core import window_snapshot
from .v2_interfaces import evaluation_identity_fields, training_budget_summary


def _label(value, name):
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f'{name} requires an explicit nonempty identity string')
    return value


def _seeds(seeds):
    if not isinstance(seeds, (tuple, list)) or not seeds:
        raise ValueError('An explicit ordered seed cohort is required')
    result = tuple(seeds)
    if any(type(s) is not int or not 0 <= s < 2**32 for s in result) or len(set(result)) != len(result):
        raise ValueError('Seeds must be unique uint32 integers')
    return result


def integration_status():
    """Scientific availability, independent of configuration approval status."""
    return dict(status='DESCRIPTIVE_ONLY', inference_status='INFERENCE_UNAVAILABLE',
        m3_verdict='NO_VALIDATED_REPLACEMENT',
        inference_reason='No confirmatory inference method has passed the separately required validation.',
        classical_acceptance_status='POLICY_UNAVAILABLE',
        classical_acceptance_reason='Versioned wrappers exist; no approved acceptance oracle is supplied.')


def split_identity(training_split, validation_split, declared_test_identity, *, fold_id):
    """Seed-free declaration hash; never takes a test partition or observations."""
    payload = dict(schema_version=1, convention='M4B_DEVELOPMENT_SPLIT_V1',
        fold_id=_label(fold_id, 'fold_id'), train=_label(training_split, 'training_split'),
        validation=_label(validation_split, 'validation_split'),
        declared_test_identity=_label(declared_test_identity, 'declared_test_identity'))
    if len({payload['train'], payload['validation'], payload['declared_test_identity']}) != 3:
        raise ValueError('Train, validation and declared test identities must differ')
    return fingerprint_payload(payload)


def calendar_bounds(window):
    """Outward UTC-day envelope of the declared half-open partition, not samples."""
    window = window_snapshot(window)
    partition = window.as_dict()['partition']
    start, end = partition['start_ns'], partition['end_ns']
    if type(start) is not int or type(end) is not int or start >= end:
        raise ValueError('Invalid half-open partition bounds')
    if not len(window.context.origin_ids) or any(
            not start <= int(t) < end for t in window.context.issue_times_ns):
        raise ValueError('Every issue time must be inside the declared half-open partition')
    # Python integer arithmetic retains exact endpoint and negative-epoch semantics.
    return (start // DAY_NS) * DAY_NS, -((-end) // DAY_NS) * DAY_NS


def build_evaluation_record(forecaster, windowed_partition, identity_kwargs):
    """Adapt a selected V2 model on its exact validation selection support.

    Native units, channel order, forecast grid, mask and quantiles are preserved
    by canonical contracts. Test partitions must use the historical authorized
    release workflow; this development adapter refuses them.
    """
    from solar_flare_jepa.training.controlled import (
        ControlledConfig, MODEL_KIND, _validation_identity, _verify_selected_weights)
    from solar_flare_jepa.training.comparators import LINEAR_KIND, TCN_KIND
    window = window_snapshot(windowed_partition)
    if window.as_dict()['partition']['name'] != 'validation':
        raise ValueError('M4B record construction accepts validation partitions only')
    if not isinstance(identity_kwargs, Mapping):
        raise ValueError('Explicit evaluation identity declarations are required')
    record = forecaster.record
    if record['model_kind'] == MODEL_KIND:
        config = ControlledConfig.from_dict(record['config'])
        options = config.architecture
        if record['run_fingerprint'] != config.run_fingerprint or record['recipe_fingerprint'] != config.recipe_fingerprint:
            raise ValueError('Selected predictor configuration identity differs')
    elif record['model_kind'] in (TCN_KIND, LINEAR_KIND):
        name = 'tcn' if record['model_kind'] == TCN_KIND else 'linear'
        from types import SimpleNamespace
        options = SimpleNamespace(**record['config'][name])
        if record['run_fingerprint'] != fingerprint_payload(record['config']):
            raise ValueError('Selected predictor configuration identity differs')
    else:
        raise ValueError('Unsupported selected V2 predictor kind')
    if (tuple(forecaster.quantiles) != tuple(options.quantiles)
            or forecaster.batch_size != options.batch_size
            or forecaster.rearrange != (record['model_kind'] == LINEAR_KIND)):
        raise ValueError('Selected predictor options/quantile semantics differ from configuration')
    _verify_selected_weights(forecaster.model, record)
    expected = dict(spec_fingerprint=window.context.spec.fingerprint,
        training_dataset_fingerprint=window.context.dataset_fingerprint,
        normalization_fingerprint=forecaster.normalization.fingerprint,
        validation=_validation_identity(window))
    if any(record.get(k) != v for k, v in expected.items()):
        raise ValueError('Model and validation selection support/spec/dataset/normalization differ')
    identity = EvaluationIdentity(**evaluation_identity_fields(record, **dict(identity_kwargs)))
    prediction = forecaster.predict(window.context, window.targets.grid)
    if prediction.model_id != record['model_id'] or prediction.quantile_levels != tuple(forecaster.quantiles):
        raise ValueError('Model prediction identity or quantile semantics differ')
    return EvaluationRecord(identity, window.targets, prediction)


def subset_records(records, seeds):
    """Select an exact predeclared prefix, preserving cohort order and records."""
    seeds = _seeds(seeds)
    if not isinstance(records, (list, tuple)) or not records or any(
            not isinstance(r, EvaluationRecord) for r in records):
        raise ValueError('Canonical evaluation records are required')
    actual = _seeds(tuple(r.identity.seed for r in records))
    if seeds != actual[:len(seeds)]:
        raise ValueError('Secondary seeds must be the exact ordered prefix of the primary cohort')
    return tuple(records[:len(seeds)])


def replicate_deterministic_record(record, seeds, *, deterministic, source_execution_id):
    """Relabel one declared deterministic forecast; retain its source provenance.

    This is a caller attestation, not a test of determinism. Replicated labels
    are not independent fitting runs. Never infer determinism from architecture
    or zero initialization; quantile-linear is fitted separately per seed in
    the M4B synthetic workflow.
    """
    seeds = _seeds(seeds)
    if deterministic is not True:
        raise ValueError('Explicit deterministic forecast attestation is required')
    _label(source_execution_id, 'source_execution_id')
    if not isinstance(record, EvaluationRecord):
        raise ValueError('Expected EvaluationRecord')
    source = EvaluationRecord.from_json(record.to_json())
    records = tuple(EvaluationRecord(replace(source.identity, seed=s), source.targets, source.prediction)
                    for s in seeds)
    metadata = dict(replicated=True, independent_seed_runs=False, source_seed=source.identity.seed,
        source_execution_id=source_execution_id, source_record_fingerprint=source.fingerprint,
        source_identity=source.identity.as_dict(), seed_labels=list(seeds),
        basis='CALLER_ATTESTED_DETERMINISTIC_FORECAST')
    return records, metadata


def descriptive_budget_table(folds):
    """Report measured jobs and matched J/B wall ratios, without H5 inference."""
    if not isinstance(folds, Mapping) or not folds:
        raise ValueError('Named folds with actual model records are required')
    from solar_flare_jepa.training.controlled import check_paired_cohort
    jobs, ratios = [], []
    for fold, records in sorted(folds.items()):
        _label(fold, 'fold_id')
        seen, paired = set(), {}
        if not isinstance(records, (tuple, list)) or not records:
            raise ValueError('Nonempty per-fold model records required')
        for record in records:
            summary = training_budget_summary(record)
            key = (summary['model_id'], summary['seed'])
            if key in seen:
                raise ValueError('Duplicate model/seed budget record')
            seen.add(key)
            wall = record.get('wall_seconds', {})
            value = wall.get('attributed_training', wall.get('this_call_training'))
            if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
                raise ValueError('A finite nonnegative measured training wall time is required')
            jobs.append(dict(fold_id=fold, **summary, measured_training_wall_seconds=value,
                **{k: record[k] for k in ('training_fingerprint', 'normalization_fingerprint',
                                          'validation')}))
            arm = record.get('arm')
            if arm in ('jepa_finetune', 'supervised_extra_updates'):
                paired.setdefault(summary['seed'], {})[arm] = (value, record)
        for seed, pair in sorted(paired.items()):
            if set(pair) != {'jepa_finetune', 'supervised_extra_updates'}:
                continue  # unpaired costs are still reported, never fabricated
            check_paired_cohort([item[1] for item in pair.values()])
            denominator = pair['supervised_extra_updates'][0]
            ratios.append(dict(fold_id=fold, seed=seed,
                j_over_b_wall_ratio=None if denominator <= 0 else pair['jepa_finetune'][0] / denominator))
    available = [r['j_over_b_wall_ratio'] for r in ratios if r['j_over_b_wall_ratio'] is not None]
    result = dict(**integration_status(), jobs=jobs, paired_wall_ratios=ratios,
        median_j_over_b_wall_ratio=statistics.median(available) if available else None,
        acceptance=None, notes='Steps, examples, exposure, wall time and RSS differ; no equal-compute claim. '
        'Attributed SSL time is shared and must not be summed across arms. No cost inference is defined.')
    canonical_json(result)
    return result
