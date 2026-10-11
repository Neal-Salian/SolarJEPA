"""M4B adapters preserve the exact validation scientific contracts."""
from dataclasses import replace
import importlib
import json

import numpy as np
import pytest

from m4b_helpers import development_windows, fit_model, LEVELS, LOSS
from solar_flare_jepa.evaluation.records import EvaluationRecord
from solar_flare_jepa.forecasting.contracts import ForecastTargets
from solar_flare_jepa.training.controlled import _validation_identity


def adapters():
    return importlib.import_module('solar_flare_jepa.experiments.v2_evaluation_adapters')


def declarations(windows):
    return dict(experiment_id='m4b', code_fingerprint='code', data_provenance_fingerprint='synthetic',
        split_fingerprint=adapters().split_identity(windows['train'].split_fingerprint,
            windows['validation'].split_fingerprint, 'UNRELEASED_SYNTHETIC_ID', fold_id='fold-1'),
        protocol_fingerprint='synthetic-development-only')


def test_selection_identity_changes_when_values_masks_change_at_same_origins():
    window = development_windows()['validation']
    targets = window.targets
    changed = replace(window, targets=ForecastTargets(targets.values * 2, targets.mask, targets.grid))
    assert _validation_identity(window) != _validation_identity(changed)


def test_selection_identity_preserves_declared_feature_availability():
    window = development_windows()['validation']
    availability = np.broadcast_to(window.context.ends_ns[..., None], window.context.values.shape).copy()
    changed = replace(window, context=replace(window.context, availability_ns=availability))
    assert _validation_identity(window) != _validation_identity(changed)


def test_masked_record_canonicalizes_unscored_values_and_panel_refuses_partial_support():
    from solar_flare_jepa.evaluation.comparison import loss_panel_from_records
    w = development_windows(masked=True)
    model = fit_model('supervised', 5, w)
    record = adapters().build_evaluation_record(model, w['validation'], declarations(w))
    assert not record.targets.mask.all()
    assert np.isnan(record.targets.values[~record.targets.mask]).all()
    assert EvaluationRecord.from_json(record.to_json()).to_json() == record.to_json()
    with pytest.raises(ValueError, match='complete common target support'):
        loss_panel_from_records([record], calendar_start_ns=0, calendar_end_ns=86_400_000_000_000)


@pytest.mark.parametrize('arm', ['jepa_finetune', 'supervised', 'supervised_extra_updates',
                                'jepa_frozen', 'random_frozen', 'tcn', 'quantile_linear'])
def test_record_round_trip_all_model_kinds(arm):
    w = development_windows()
    model = fit_model(arm, 5, w)
    record = adapters().build_evaluation_record(model, w['validation'], declarations(w))
    assert EvaluationRecord.from_json(record.to_json()).to_json() == record.to_json()
    assert record.identity.config_fingerprint == model.record['recipe_fingerprint']
    assert record.prediction.grid.spec.target_names == ('a', 'b')
    assert record.prediction.quantile_levels == LEVELS
    assert record.prediction.quantiles.shape[1:] == (5, 2, 5)


def test_record_rejects_other_selection_values_and_nonvalidation_partition():
    w = development_windows()
    model = fit_model('supervised', 5, w)
    window = w['validation']
    targets = window.targets
    changed = replace(window, targets=ForecastTargets(targets.values * 2, targets.mask, targets.grid))
    with pytest.raises(ValueError, match='validation|selection'):
        adapters().build_evaluation_record(model, changed, declarations(w))
    with pytest.raises(ValueError, match='validation'):
        adapters().build_evaluation_record(model, w['train'], declarations(w))


@pytest.mark.parametrize('mutation', ['levels', 'weights', 'rearrange'])
def test_record_refuses_mutated_selected_predictor(mutation):
    torch = pytest.importorskip('torch')
    w = development_windows()
    model = fit_model('supervised', 5, w)
    if mutation == 'levels':
        model.quantiles = (.01, .1, .5, .9, .99)
    elif mutation == 'weights':
        with torch.no_grad():
            next(model.model.parameters()).add_(.01)
    else:
        model.rearrange = True
    with pytest.raises(ValueError, match='selected|quantile|predictor'):
        adapters().build_evaluation_record(model, w['validation'], declarations(w))


def test_seed_invariant_split_identity_and_exact_prefix_subset():
    w = development_windows()
    records = [adapters().build_evaluation_record(fit_model('supervised', s, w), w['validation'], declarations(w))
               for s in (5, 6)]
    assert records[0].identity.config_fingerprint == records[1].identity.config_fingerprint
    assert records[0].identity.split_fingerprint == records[1].identity.split_fingerprint
    assert adapters().subset_records(records, (5,)) == (records[0],)
    for bad in ((6,), (6, 5), (5, 5), (7,)):
        with pytest.raises(ValueError):
            adapters().subset_records(records, bad)
    with pytest.raises(ValueError):
        adapters().split_identity('train', 'validation', w['validation'], fold_id='f')


@pytest.mark.parametrize('field', ['training_fingerprint', 'normalization_fingerprint'])
def test_primary_two_seed_panels_reject_one_seed_fitting_identity_change(field):
    from solar_flare_jepa.evaluation.comparison import loss_panel_from_records
    w = development_windows()
    calendar = dict(calendar_start_ns=0, calendar_end_ns=86_400_000_000_000)
    for arm in ('jepa_finetune', 'supervised'):
        records = [adapters().build_evaluation_record(fit_model(arm, seed, w),
                   w['validation'], declarations(w)) for seed in (5, 6)]
        panel = loss_panel_from_records(records, **calendar)
        assert tuple(panel.seed_ids) == (5, 6)
        changed = replace(records[1], identity=replace(records[1].identity, **{field: 'changed'}))
        with pytest.raises(ValueError, match='recipe|identity|fingerprint'):
            loss_panel_from_records([records[0], changed], **calendar)


def test_calendar_uses_half_open_partition_bounds_and_checks_actual_origins():
    w = development_windows()['validation']
    start, end = adapters().calendar_bounds(w)
    assert start == 0 and end == 86_400_000_000_000
    manifest = w.as_dict()
    manifest['partition']['end_ns'] = int(w.context.issue_times_ns[-1])
    bad = replace(w, _manifest_json=json.dumps(manifest))
    with pytest.raises(ValueError, match='partition'):
        adapters().calendar_bounds(bad)


def test_deterministic_replication_requires_attestation_and_preserves_source_identity():
    w = development_windows()
    source = adapters().build_evaluation_record(fit_model('supervised', 5, w), w['validation'], declarations(w))
    with pytest.raises(ValueError, match='deterministic'):
        adapters().replicate_deterministic_record(source, (5, 6), deterministic=False, source_execution_id='fixed-fit')
    records, metadata = adapters().replicate_deterministic_record(
        source, (5, 6), deterministic=True, source_execution_id='fixed-fit')
    assert tuple(r.identity.seed for r in records) == (5, 6)
    np.testing.assert_array_equal(records[0].prediction.quantiles, records[1].prediction.quantiles)
    assert metadata['replicated'] is True and metadata['source_seed'] == 5
    assert metadata['source_record_fingerprint'] == source.fingerprint


def test_three_way_float64_metric_agreement():
    torch = pytest.importorskip('torch')
    from solar_flare_jepa.evaluation.probabilistic import log_scores
    from solar_flare_jepa.evaluation.diagnostics import calibration_diagnostics
    from solar_flare_jepa.training.losses import MetricAccumulator
    w = development_windows()
    model = fit_model('supervised', 5, w)
    record = adapters().build_evaluation_record(model, w['validation'], declarations(w))
    normalization = model.normalization
    y = normalization.normalize(record.targets.values, record.targets.mask, 'target')
    log_q = np.log10(record.prediction.quantiles)
    q = (log_q - np.asarray(normalization.target_mean)[None, None, :, None]) / np.asarray(
        normalization.target_scale)[None, None, :, None]
    metric = MetricAccumulator(LOSS, LEVELS, normalization.target_scale)
    metric.add(torch.tensor(q), torch.tensor(y), torch.tensor(record.targets.mask.copy()))
    native = log_scores(record.targets, record.prediction, record.targets.grid.spec)['mean_pinball']
    diagnostic = calibration_diagnostics(record.targets, record.prediction, space='log10', intervals=())['aggregate_mean_pinball']
    assert metric.value() == pytest.approx(native, abs=1e-12, rel=0)
    assert diagnostic == pytest.approx(native, abs=1e-12, rel=0)


def test_actual_float32_checkpoint_metric_matches_native_with_declared_numeric_tolerance():
    from solar_flare_jepa.evaluation.probabilistic import log_scores
    w = development_windows()
    model = fit_model('supervised', 5, w)
    record = adapters().build_evaluation_record(model, w['validation'], declarations(w))
    native = log_scores(record.targets, record.prediction, record.targets.grid.spec)['mean_pinball']
    # Training rounds standardized targets/forecasts to float32. This numerical
    # regression tolerance follows the existing model-side parity check; it is
    # not a scientific acceptance margin or model superiority criterion.
    assert model.record['selection']['value'] == pytest.approx(native, rel=2e-5, abs=2e-7)


def test_classical_policy_and_inference_remain_explicitly_unavailable():
    status = adapters().integration_status()
    assert status['status'] == 'DESCRIPTIVE_ONLY'
    assert status['inference_status'] == 'INFERENCE_UNAVAILABLE'
    assert status['classical_acceptance_status'] == 'POLICY_UNAVAILABLE'
    assert status['m3_verdict'] == 'NO_VALIDATED_REPLACEMENT'


def test_budget_table_preserves_measured_cost_without_acceptance_threshold():
    w = development_windows()
    j = fit_model('jepa_finetune', 5, w).record
    b = fit_model('supervised_extra_updates', 5, w).record
    result = adapters().descriptive_budget_table({'fold-1': [j, b]})
    assert len(result['jobs']) == 2
    assert result['median_j_over_b_wall_ratio'] > 0
    assert result['acceptance'] is None
    assert result['jobs'][0]['fold_id'] == 'fold-1'


@pytest.mark.parametrize('mutation', ['support', 'overflow'])
def test_budget_ratio_rejects_unpaired_support_and_nonfinite_arithmetic(mutation):
    w = development_windows()
    j = fit_model('jepa_finetune', 5, w).record
    b = fit_model('supervised_extra_updates', 5, w).record
    if mutation == 'support':
        b['training_fingerprint'] = 'other-training'
    else:
        j['wall_seconds']['this_call_training'] = 1e308
        j['wall_seconds']['attributed_training'] = 1e308
        b['wall_seconds']['this_call_training'] = 1e-308
    with pytest.raises(ValueError):
        adapters().descriptive_budget_table({'fold-1': [j, b]})
