"""Synthetic leakage, temporal support and fitting-artifact integrity."""
from copy import deepcopy
from dataclasses import replace
import importlib

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.splitting import TemporalPartition, chronological_partitions
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.training.normalization import Normalization

NS = 1_000_000_000


def fixture(*, omitted=(), future_scale=1., delayed=False):
    ticks = np.array([x for x in range(40) if x not in omitted], np.int64)
    values = (ticks.astype(float) + 1)[:, None]
    values[ticks >= 16] *= future_scale
    available = (ticks + 1)[:, None] * NS
    if delayed:
        available[ticks == 18] = 30 * NS
    data = TimeSeriesDataset('integrity', 'synthetic_fixture', ticks * NS,
        (ticks + 1) * NS, values, np.ones_like(values, bool), values,
        np.ones_like(values, bool), ('x',), ('x',), ('artificial',), ('artificial',),
        1, availability_ns=available)
    spec = ForecastSpec(1, 3, 2, ('x',), ('x',), ('artificial',), ('artificial',))
    partitions = (TemporalPartition('train', 0, 16 * NS),
                  TemporalPartition('validation', 18 * NS, 28 * NS),
                  TemporalPartition('test', 30 * NS, 40 * NS))
    windows = {p.name: build_partition_windows(data, spec, p) for p in partitions}
    return data, spec, partitions, windows


def validate(windows, normalization=None, **kwargs):
    train = windows['train'].training_slice
    normalization = Normalization.fit(train) if normalization is None else normalization
    evaluation = windows['validation']
    return importlib.import_module('solar_flare_jepa.evaluation.records').validate_fitting_artifacts(
        train, normalization, evaluation.context, evaluation.targets, **kwargs)


def test_embargo_checks_explicit_gaps_without_moving_any_boundary():
    data, _, partitions, _ = fixture()
    selected = chronological_partitions(data, partitions, embargo_ns=2 * NS)
    assert [(p.start_ns, p.end_ns) for p in selected] == [(0, 16 * NS), (18 * NS, 28 * NS), (30 * NS, 40 * NS)]
    with pytest.raises(ValueError, match='embargo'):
        chronological_partitions(data, partitions, embargo_ns=2 * NS + 1)


@pytest.mark.parametrize('embargo', [True, -1, 1., '1', 2**63])
def test_embargo_requires_nonnegative_int64_nanoseconds(embargo):
    data, _, partitions, _ = fixture()
    with pytest.raises(ValueError):
        chronological_partitions(data, partitions, embargo_ns=embargo)


def test_normalization_audit_recomputes_statistics_and_fitting_identity():
    _, _, _, windows = fixture()
    result = validate(windows, embargo_ns=2 * NS)
    assert result['status'] == 'VALIDATED_DECLARED_FITTING_ARTIFACTS'
    assert result['training_fingerprint'] == windows['train'].training_slice.fingerprint
    assert result['normalization_fingerprint'] == Normalization.fit(windows['train'].training_slice).fingerprint
    train = windows['train'].training_slice
    normalizer = Normalization.fit(train)
    # A real evaluation-fitted normalizer, relabeled with the train raw identity.
    evaluation_train = build_partition_windows(fixture()[0], train.spec,
        TemporalPartition('train', 18 * NS, 28 * NS)).training_slice
    contaminated = replace(Normalization.fit(evaluation_train),
                           raw_support_fingerprint=normalizer.raw_support_fingerprint)
    with pytest.raises(ValueError, match='normalization'):
        validate(windows, contaminated)
    with pytest.raises(ValueError, match='normalization'):
        validate(windows, replace(normalizer, raw_support_fingerprint='forged'))


def test_evaluation_reuse_of_training_support_is_rejected():
    _, _, _, windows = fixture()
    windows['validation'] = windows['train']
    with pytest.raises(ValueError, match='support'):
        validate(windows)


def test_fitting_audit_requires_actual_gap_and_complete_declared_dependency_support():
    data, spec, _, windows = fixture()
    windows['validation'] = build_partition_windows(data, spec, TemporalPartition('validation', 16 * NS, 28 * NS))
    with pytest.raises(ValueError, match='embargo'):
        validate(windows, embargo_ns=4 * NS)
    assert validate(windows, embargo_ns=0)['status'] == 'VALIDATED_DECLARED_FITTING_ARTIFACTS'
    # Mutating lookback after construction must be revalidated, not trusted.
    context = deepcopy(windows['validation'].context)
    targets = deepcopy(windows['validation'].targets)
    changed_spec = replace(context.spec, feature_lookback_steps=4)
    object.__setattr__(context, 'spec', changed_spec)
    object.__setattr__(targets.grid, 'spec', changed_spec)
    train = windows['train'].training_slice
    with pytest.raises(ValueError):
        importlib.import_module('solar_flare_jepa.evaluation.records').validate_fitting_artifacts(
            train, Normalization.fit(train), context, targets)


def test_future_only_perturbation_cannot_change_fitted_statistics_or_training_identity():
    _, _, _, original = fixture()
    _, _, _, changed = fixture(future_scale=1e6)
    one, two = [validate(w) for w in (original, changed)]
    assert one['training_fingerprint'] == two['training_fingerprint']
    assert one['normalization_fingerprint'] == two['normalization_fingerprint']
    assert one['support_fingerprint'] != two['support_fingerprint']


def test_window_boundary_gap_quality_and_future_availability_policies_are_preserved():
    data, spec, _, windows = fixture()
    support = windows['train'].support_manifest
    assert support[0]['start_ns'] == 0
    assert support[-1]['end_ns'] == 16 * NS
    reasons = {r['issue_time_ns']: r['reasons'] for r in windows['train'].excluded_origins}
    assert 'support_before_partition' in reasons[2 * NS]
    assert 'support_after_partition' in reasons[15 * NS]
    _, _, _, gaps = fixture(omitted=(20,))
    assert all(not (r['start_ns'] <= 20 * NS < r['end_ns']) for r in gaps['validation'].support_manifest)
    assert any('missing_cadence' in r['reasons'] for r in gaps['validation'].excluded_origins)
    _, _, _, late = fixture(delayed=True)
    assert all(r['issue_time_ns'] != 21 * NS for r in late['validation'].support_manifest)
    with pytest.raises(ValueError):
        replace(data, starts_ns=np.roll(data.starts_ns, 1))
    with pytest.raises(ValueError):
        replace(data, feature_mask=np.ones_like(data.features, int))
    mask = data.feature_mask.copy()
    mask[18] = False
    masked = build_partition_windows(replace(data, feature_mask=mask),
        replace(spec, eligibility_policy='masked'), TemporalPartition('validation', 18 * NS, 28 * NS))
    assert not masked.context.mask[0, 0, 0]
    assert np.isnan(masked.context.values[0, 0, 0])


def test_normalizer_subclass_hooks_cannot_hide_wrong_statistics():
    _, _, _, windows = fixture()
    class ForgedNormalizer(Normalization):
        def as_dict(self):
            return Normalization.fit(windows['train'].training_slice).as_dict()
    original = Normalization.fit(windows['train'].training_slice)
    forged = ForgedNormalizer(**{field: getattr(original, field) for field in original.__dataclass_fields__})
    object.__setattr__(forged, 'feature_mean', (900.,))
    with pytest.raises(ValueError, match='normalization'):
        validate(windows, forged)
