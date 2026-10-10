"""Synthetic contract→serialization→paired-statistics integration; no model fits."""
from dataclasses import replace
import json

import numpy as np
import pytest

from solar_flare_jepa.evaluation.comparison import loss_panel_from_records, paired_comparison
from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord, validate_fitting_artifacts
from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset, ForecastPrediction
from solar_flare_jepa.forecasting.splitting import TemporalPartition, chronological_partitions
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.training.normalization import Normalization

DAY = 86_400_000_000_000
HOUR = DAY // 24


def records(widths=(1., 2.), version='a'):
    ticks = np.arange(96, dtype=np.int64) * HOUR
    values = np.ones((96, 1))  # invented dimensioned software fixture
    mask = np.ones_like(values, bool)
    data = TimeSeriesDataset('artificial', 'synthetic_fixture', ticks, ticks + HOUR,
                             values, mask, values, mask, ('x',), ('x',), ('unit',), ('unit',),
                             3600, availability_policy='bin_end_earliest')
    task = ForecastSpec(3600, 2, 1, ('x',), ('x',), ('unit',), ('unit',),
                        availability_mode='retrospective_bin_end', transform='log10',
                        feature_reference=(1.,), target_reference=(1.,))
    partitions = chronological_partitions(data, (
        TemporalPartition('train', 0, DAY),
        TemporalPartition('validation', DAY + 6 * HOUR, 2 * DAY),
        TemporalPartition('test', 2 * DAY + 6 * HOUR, 4 * DAY)), embargo_ns=6 * HOUR)
    windows = {p.name: build_partition_windows(data, task, p) for p in partitions}
    train, test = windows['train'].training_slice, windows['test']
    normalizer = Normalization.fit(train)
    audit = validate_fitting_artifacts(train, normalizer, test.context, test.targets, embargo_ns=6 * HOUR)
    assert audit['training_fingerprint'] == train.fingerprint
    result = []
    for seed, width in zip((11, 22), widths):
        identity = EvaluationIdentity('synthetic-study', version, seed, 'code', 'config',
            'artificial-provenance', 'split', train.fingerprint, normalizer.fingerprint, 'protocol')
        quantiles = np.broadcast_to(np.array([10.**-width, 1., 10.**width]), test.targets.values.shape + (3,))
        prediction = ForecastPrediction(test.targets.values, test.targets.grid, version,
                                        (.25, .5, .75), quantiles)
        record = EvaluationRecord(identity, test.targets, prediction)
        result.append(EvaluationRecord.from_json(record.to_json()))
    return result


def test_reproducible_synthetic_records_to_common_support_comparison():
    a = loss_panel_from_records(records(), calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)
    b = loss_panel_from_records(records((2., 3.), 'b'), calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)
    assert a.support_fingerprint == b.support_fingerprint
    assert a.seed_ids == (11, 22)
    np.testing.assert_allclose(a.losses[:, 0], [1/6, 1/3])
    result = paired_comparison({'synthetic': a}, {'synthetic': b},
                               block_days=1, replicates=31, rng_seed=5, confidence=.95)
    assert result['mean_difference'] == pytest.approx(-1/6)
    np.testing.assert_allclose(result['difference_interval'], [-1/6, -1/6])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('damage', ['observations', 'mask', 'recipe', 'duplicate_seed',
                                  'point_only', 'quantiles', 'model_id', 'point_interpretation'])
def test_loss_extraction_rejects_invalid_common_support_or_recipe(damage):
    bundle = records()
    second = bundle[1]
    if damage == 'observations':
        second = replace(second, targets=replace(second.targets, values=second.targets.values * 2))
    elif damage == 'mask':
        second = replace(second, targets=replace(second.targets, mask=np.zeros_like(second.targets.mask)))
    elif damage == 'recipe':
        second = replace(second, identity=replace(second.identity, protocol_fingerprint='different'))
    elif damage == 'duplicate_seed':
        second = replace(second, identity=replace(second.identity, seed=11))
    elif damage == 'point_only':
        second = replace(second, prediction=replace(second.prediction, quantiles=None, quantile_levels=()))
    elif damage == 'quantiles':
        second = replace(second, prediction=replace(second.prediction, quantile_levels=(.2, .5, .8)))
    elif damage == 'model_id':
        second = replace(second, prediction=replace(second.prediction, model_id='different-family'))
    else:
        second = replace(second, prediction=replace(second.prediction, point_interpretation='inverse_transformed_point'))
    with pytest.raises(ValueError):
        loss_panel_from_records([bundle[0], second], calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)


def test_different_quantile_cohorts_cannot_be_paired_by_the_same_metric_name():
    bundle = records()
    changed = [replace(r, prediction=replace(r.prediction, quantile_levels=(.2, .5, .8))) for r in bundle]
    a = loss_panel_from_records(bundle, calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)
    b = loss_panel_from_records(changed, calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)
    with pytest.raises(ValueError, match='align'):
        paired_comparison({'f': a}, {'f': b}, block_days=1, replicates=2, rng_seed=0, confidence=.95)


def test_metric_definition_binds_the_experimental_spec_across_folds():
    original = records()
    changed = []
    for record in original:
        grid = replace(record.targets.grid, spec=replace(record.targets.grid.spec, target_reference=(2.,)))
        changed.append(replace(record, targets=replace(record.targets, grid=grid),
                               prediction=replace(record.prediction, grid=grid)))
    a = loss_panel_from_records(original, calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)
    b = loss_panel_from_records(changed, calendar_start_ns=2 * DAY, calendar_end_ns=4 * DAY)
    assert a.metric != b.metric
