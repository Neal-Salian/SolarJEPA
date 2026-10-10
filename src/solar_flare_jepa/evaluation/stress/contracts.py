"""Adversarial public-API probes; accepted dishonest metadata is an evidence limit."""
from copy import deepcopy
from dataclasses import replace

import numpy as np

from ...forecasting.contracts import ForecastSpec, TimeSeriesDataset, ForecastPrediction, ForecastTargets
from ...forecasting.splitting import TemporalPartition, chronological_partitions
from ...forecasting.windows import build_partition_windows
from ...training.normalization import Normalization
from ..comparison import paired_comparison, loss_panel_from_records
from ..diagnostics import calibration_diagnostics
from ..records import EvaluationIdentity, EvaluationRecord, validate_fitting_artifacts
from .synthetic import Scenario, generate_panels

NS = 1_000_000_000


def temporal_fixture():
    ticks = np.arange(40, dtype=np.int64)
    values = (ticks.astype(float)+1)[:, None]
    data = TimeSeriesDataset('M2', 'synthetic_fixture', ticks*NS, (ticks+1)*NS,
        values, np.ones_like(values, bool), values, np.ones_like(values, bool),
        ('x',), ('x',), ('unit',), ('unit',), 1, availability_ns=(ticks+1)[:, None]*NS)
    spec = ForecastSpec(1, 3, 2, ('x',), ('x',), ('unit',), ('unit',),
                        target_reference=(1.,), feature_reference=(1.,))
    parts = (TemporalPartition('train', 0, 16*NS), TemporalPartition('validation', 18*NS, 28*NS),
             TemporalPartition('test', 30*NS, 40*NS))
    windows = {p.name: build_partition_windows(data, spec, p) for p in parts}
    return data, spec, parts, windows


def contract_probes():
    data, spec, parts, windows = temporal_fixture()
    train = windows['train'].training_slice
    norm = Normalization.fit(train)
    validation = windows['validation']
    identity = EvaluationIdentity('synthetic', 'M2', 0, 'declared-code', 'declared-config',
        'declared-source', 'declared-split', train.fingerprint, norm.fingerprint, 'declared-protocol')
    y = validation.targets
    quantiles = y.values[..., None]*np.array([.5, 1., 2.])
    prediction = ForecastPrediction(y.values, y.grid, 'M2', (.25, .5, .75), quantiles)
    record = EvaluationRecord(identity, y, prediction)
    a, b, _ = generate_panels(Scenario('contracts', seeds=3, days=(4,)), 1)
    panel = a['f0']
    rows = []

    def probe(name, expected, category, operation, note=''):
        try:
            result = operation()
        except ValueError as error:
            observed, reason = 'rejected', str(error)
        else:
            observed = 'excluded' if result is False else 'accepted'
            reason = note
        if observed != expected:
            raise AssertionError(f'{name}: expected {expected}, observed {observed}')
        rows.append(dict(case=name, expected=expected, observed=observed, classification=category,
                         matched_expected=True, evidence=reason))

    leakage, contract, valid, limit = ('DETECTED LEAKAGE', 'DETECTED CONTRACT VIOLATION',
                                    'VALID BOUNDARY', 'UNDETECTABLE FROM AVAILABLE METADATA')
    def fitting(context=validation.context, targets=y, normalization=norm, training=train, **kwargs):
        return validate_fitting_artifacts(training, normalization, context, targets, **kwargs)
    def compare(left=panel, right=b['f0'], **kwargs):
        return paired_comparison({'f': left}, {'f': right}, **(dict(block_days=1, replicates=19,
                                 rng_seed=4, confidence=.95)|kwargs))
    probe('overlapping_partitions', 'rejected', leakage, lambda: chronological_partitions(data,
          (parts[0], replace(parts[1], start_ns=15*NS), parts[2])))
    probe('embargo_one_ns_short', 'rejected', leakage,
          lambda: chronological_partitions(data, parts, embargo_ns=2*NS+1))
    probe('exact_embargo_boundary', 'accepted', valid,
          lambda: chronological_partitions(data, parts, embargo_ns=2*NS))
    probe('train_support_reused', 'rejected', leakage,
          lambda: fitting(context=windows['train'].context, targets=windows['train'].targets))
    excluded = validation.excluded_origins
    probe('target_crossing_boundary', 'excluded', leakage,
          lambda: not any(r['issue_time_ns'] == 27*NS and 'support_after_partition' in r['reasons'] for r in excluded),
          'Builder records support_after_partition at the late origin')
    probe('exact_target_boundary', 'accepted', valid,
          lambda: max(r['end_ns'] for r in validation.support_manifest) == parts[1].end_ns,
          'Builder accepts target support ending exactly at supplied partition end')
    future_train = build_partition_windows(data, spec, TemporalPartition('train', 18*NS, 28*NS)).training_slice
    bad_norm = replace(Normalization.fit(future_train), raw_support_fingerprint=norm.raw_support_fingerprint)
    probe('future_fitted_normalization', 'rejected', leakage, lambda: fitting(normalization=bad_norm))
    probe('normalization_provenance', 'rejected', contract,
          lambda: fitting(normalization=replace(norm, raw_support_fingerprint='conflict')))
    probe('conflicting_normalization_identity', 'rejected', contract,
          lambda: fitting(identity=replace(identity, normalization_fingerprint='conflict')))
    probe('incorrect_fitting_range', 'rejected', leakage,
          lambda: fitting(training=replace(train, partition_end_ns=24*NS)))
    probe('failed_fitting_identity', 'rejected', contract,
          lambda: fitting(identity=replace(identity, training_fingerprint='failed')))
    probe('duplicate_origins', 'rejected', contract,
          lambda: replace(y.grid, origin_ids=(y.grid.origin_ids[0],)*len(y.grid.origin_ids)))
    probe('out_of_order_timestamps', 'rejected', contract,
          lambda: replace(y.grid, issue_times_ns=y.grid.issue_times_ns[::-1]))
    probe('dataset_identity', 'rejected', contract,
          lambda: fitting(context=replace(validation.context, dataset_fingerprint='different'),
                          targets=replace(y, grid=replace(y.grid, dataset_fingerprint='different'))))
    probe('wrong_horizon', 'rejected', contract, lambda: replace(y.grid, spec=replace(spec, horizon_steps=3)))
    serialized = record.as_dict()
    serialized['support_fingerprint'] = 'wrong'
    probe('invalid_support_metadata', 'rejected', contract, lambda: EvaluationRecord.from_dict(serialized))
    probe('prediction_target_identity', 'rejected', contract,
          lambda: replace(record, prediction=replace(prediction, grid=replace(y.grid, dataset_fingerprint='wrong'))))
    probe('incomplete_provenance', 'rejected', contract, lambda: replace(identity, code_fingerprint=''))
    for name, changes in (
        ('unequal_origin_support', dict(origin_ids=tuple('other:'+x for x in panel.origin_ids))),
        ('incompatible_units', dict(unit='another-unit')), ('mismatched_metric', dict(metric='another-metric')),
        ('reordered_seeds', dict(seed_ids=panel.seed_ids[::-1])),
        ('asymmetric_missing_run', dict(seed_ids=panel.seed_ids[:-1], losses=panel.losses[:-1]))):
        probe(name, 'rejected', contract, lambda changes=changes: compare(right=replace(b['f0'], **changes)))
    for name, changes in (
        ('nan_loss', dict(losses=np.full_like(panel.losses, np.nan))),
        ('infinite_loss', dict(losses=np.full_like(panel.losses, np.inf))),
        ('broadcast_loss', dict(losses=np.ones((3, 1)))), ('repeated_seeds', dict(seed_ids=(0, 0, 1))),
        ('empty_origins', dict(origin_ids=(), issue_times_ns=np.array([], np.int64), losses=np.empty((3, 0)))),
        ('unsorted_issue_times', dict(issue_times_ns=panel.issue_times_ns[::-1]))):
        probe(name, 'rejected', contract, lambda changes=changes: replace(panel, **changes))
    probe('single_seed', 'rejected', contract,
          lambda: compare(left=replace(panel, seed_ids=(0,), losses=panel.losses[:1]),
                          right=replace(b['f0'], seed_ids=(0,), losses=b['f0'].losses[:1])))
    probe('single_observation', 'accepted', valid,
          lambda: compare(left=replace(panel, origin_ids=panel.origin_ids[:1], issue_times_ns=panel.issue_times_ns[:1], losses=panel.losses[:, :1]),
                          right=replace(b['f0'], origin_ids=panel.origin_ids[:1], issue_times_ns=panel.issue_times_ns[:1], losses=b['f0'].losses[:, :1])))
    probe('zero_variance', 'accepted', valid, lambda: compare(left=panel, right=panel))
    probe('zero_reference', 'accepted', valid,
          lambda: compare(right=replace(b['f0'], losses=np.zeros_like(panel.losses)))['relative_interval'] is None,
          'Relative interval explicitly unavailable for nonpositive reference')
    probe('extreme_arithmetic_overflow', 'rejected', contract,
          lambda: compare(left=replace(panel, losses=np.full_like(panel.losses, 1e308))))
    probe('quantile_crossing', 'rejected', contract, lambda: replace(prediction, quantiles=quantiles[..., ::-1]))
    masked = replace(y, mask=np.zeros_like(y.mask), values=np.full_like(y.values, np.nan))
    probe('partial_target_mask', 'rejected', contract,
          lambda: loss_panel_from_records([replace(record, targets=masked)], calendar_start_ns=0, calendar_end_ns=86400*NS))
    probe('masked_nan_is_inert', 'accepted', valid,
          lambda: calibration_diagnostics(masked, prediction, space='native')['aggregate_mean_pinball'] is None)
    probe('unmasked_nan', 'rejected', contract, lambda: replace(y, values=np.full_like(y.values, np.nan)))
    probe('quantile_level_mismatch', 'rejected', contract,
          lambda: replace(prediction, quantile_levels=(.25, .5)))
    common_a, common_b = {}, {}
    for source, destination in ((a, common_a), (b, common_b)):
        destination['f'] = replace(source['f0'], seed_ids=(0, 1), losses=source['f0'].losses[:2])
    probe('common_missing_run', 'accepted', limit,
          lambda: paired_comparison(common_a, common_b, block_days=1, replicates=19, rng_seed=4, confidence=.95),
          'No planned cohort supplied: a seed missing from both arms is invisible')
    probe('standalone_failed_fit_label', 'accepted', limit,
          lambda: replace(record, identity=replace(identity, training_fingerprint='failed')),
          'Standalone record has declarations but no authenticated fit result')
    extended = build_partition_windows(data, spec, TemporalPartition('validation', 18*NS, 35*NS))
    probe('unknown_evaluation_partition_end', 'accepted', limit,
          lambda: fitting(context=extended.context, targets=extended.targets),
          'Fitting audit receives no original evaluation partition end; builder enforces supplied bounds only')
    hidden = replace(data, features=np.roll(data.features, -1, axis=0))
    probe('secret_future_feature', 'accepted', limit,
          lambda: build_partition_windows(hidden, spec, parts[1]),
          'Future-derived arrays with falsely causal availability/lineage cannot be authenticated')
    return rows
