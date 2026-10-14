"""Synthetic complete-cohort pairing; no January model inference or fitted state."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.evaluation.external_model import score_external_prediction
from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid, fingerprint_payload,
)

SEEDS = (17, 29, 43)
VARIANTS = ('jepa_finetune', 'jepa_frozen', 'supervised')
SECOND = 10**9


def summarize(*args, **kwargs):
    from solar_flare_jepa.evaluation.external_model import summarize_external_cohort
    return summarize_external_cohort(*args, **kwargs)


@pytest.fixture
def cohort():
    settings = json.loads(Path('configs/evaluation/goes_v1_external_january2025.json').read_text())
    spec = ForecastSpec(**settings['forecast'])
    axis = np.arange(1735689600000000000, 1738368000000000000, 1800*SECOND, dtype=np.int64)
    indices = [4, 5, 484, 1000]
    issues = axis[indices]
    starts = issues[:, None]+np.arange(30)[None, :]*60*SECOND
    grid = FutureGrid(starts, starts+60*SECOND, issues,
        tuple(f'origin:{i}' for i in issues), spec, 'synthetic-january')
    target = ForecastTargets(np.ones((4, 30, 2)), np.ones((4, 30, 2), bool), grid)
    scores = {}
    for variant, errors in zip(VARIANTS, [(1., 2., 3.), (2., 2., 2.), (4., 4., 4.)]):
        scores[variant] = {}
        for seed, error in zip(SEEDS, errors):
            values = np.full(target.values.shape, 10.**error)
            quantiles = np.repeat(values[..., None], 5, axis=-1)
            prediction = ForecastPrediction(values, grid, f'{variant}_seed{seed}',
                (.05, .25, .5, .75, .95), quantiles)
            scores[variant][seed] = score_external_prediction(target, prediction)
    exclusions = [dict(origin_id=f'origin:{int(t)}', issue_time_ns=int(t), reasons=['synthetic_missing_context'])
                  for i, t in enumerate(axis) if i not in indices]
    return scores, axis, exclusions, settings


def run(cohort, **kwargs):
    scores, axis, exclusions, settings = cohort
    return summarize(scores, axis, exclusions, settings=settings, **kwargs)


def resign(score):
    score.pop('score_content_fingerprint')
    score['score_content_fingerprint'] = fingerprint_payload(score)


def test_exact_seed_origin_support_pairing(cohort):
    result = run(cohort)
    assert result['support']['retained_origin_count'] == 4
    assert result['support']['candidate_origin_count'] == 1488
    paired = result['comparisons']['jepa_finetune_minus_supervised']['dex_mae']
    assert paired['seed_effects'] == {'17': -3., '29': -2., '43': -1.}
    assert paired['mean_difference'] == -2.
    assert paired['sample_standard_deviation'] == 1.
    assert paired['model_win_count'] == 3
    assert paired['leave_one_seed_out_mean'] == {'17': -1.5, '29': -2., '43': -2.5}
    assert result['comparisons']['jepa_finetune_minus_supervised']['role'] == 'primary'
    assert result['comparisons']['jepa_frozen_minus_supervised']['role'] == 'secondary'


def test_common_missing_seed_rejected(cohort):
    for variant in VARIANTS:
        del cohort[0][variant][43]
    with pytest.raises(ValueError, match='seed'):
        run(cohort)


@pytest.mark.parametrize('mutation', ['reorder', 'duplicate', 'mask', 'row_mask', 'time', 'grid', 'support', 'model_id', 'null_loss'])
def test_incompatible_score_contracts_rejected_even_when_resigned(cohort, mutation):
    score = cohort[0]['jepa_finetune'][17]
    if mutation == 'reorder':
        score['origin_ids'].reverse()
    elif mutation == 'duplicate':
        score['origin_ids'][1] = score['origin_ids'][0]
    elif mutation == 'mask':
        score['observation_mask'][0][0][0] = False
    elif mutation == 'row_mask':
        score['per_origin'][0]['valid_mask'][0][0] = False
    elif mutation == 'time':
        score['per_origin'][0]['issue_time_ns'] += 1
    elif mutation == 'grid':
        score['ends_ns'][0][0] += 1
    elif mutation == 'support':
        score['support_fingerprint'] = 'different'
    elif mutation == 'model_id':
        score['model_id'] = 'jepa_finetune_seed29'
    else:
        score['per_origin'][0]['dex_mae'] = None
    resign(score)
    with pytest.raises(ValueError):
        run(cohort)


def test_seed_mean_is_loss_mean_not_forecast_ensemble(cohort):
    # Point errors1/2/3 dex => MAE2, degenerate quantile pinball1.
    # Mean native predictions gives log10((10+100+1000)/3)=2.568..., a different estimand.
    result = run(cohort)
    assert result['variants']['jepa_finetune']['loss_means']['dex_mae'] == 2.
    assert result['variants']['jepa_finetune']['loss_means']['dex_mean_pinball'] == 1.
    assert result['variants']['jepa_finetune']['per_origin'][0]['dex_mae'] == 2.
    assert result['variants']['jepa_finetune']['forecast_ensemble_created'] is False


def test_seed_rmse_uses_pooled_mse(cohort):
    result = run(cohort)
    assert result['variants']['jepa_finetune']['loss_means']['dex_mse'] == pytest.approx(14/3)
    assert result['variants']['jepa_finetune']['rmse']['dex'] == pytest.approx(np.sqrt(14/3))
    assert result['variants']['jepa_finetune']['rmse']['dex'] != 2.


def test_missing_origins_preserve_full_axis(cohort):
    result = run(cohort)
    full = result['variants']['jepa_finetune']['full_axis_losses']['dex_mae']
    assert len(full) == 1488
    assert full[:4] == [None]*4
    assert full[4:6] == [2., 2.]
    assert result['support']['candidate_exclusions'] == cohort[2]
    assert result['support']['excluded_candidate_count'] == 1484
    json.dumps(result, allow_nan=False)


def test_utc_epoch_edges_and_empty_blocks(cohort):
    result = run(cohort)
    bootstraps = result['comparisons']['jepa_finetune_minus_supervised']['dex_mae']['calendar_sensitivity']
    assert [b['block_seconds'] for b in bootstraps] == [86400, 259200, 604800]
    assert bootstraps[0]['block_count'] == 31
    assert bootstraps[0]['blocks'][1]['paired_count'] == 0
    seven = bootstraps[2]
    assert seven['blocks'][0]['start_ns'] == 1735171200000000000
    assert seven['blocks'][0]['origin_count'] == 48
    assert seven['edge_blocks_partial'] is True
    assert seven['undefined_replicate_count'] > 0


def test_bootstrap_metadata_and_repeatability(cohort):
    a, b = run(cohort), run(cohort)
    assert a == b
    for comparison in a['comparisons'].values():
        for loss in ('dex_mae', 'dex_mean_pinball'):
            for boot in comparison[loss]['calendar_sensitivity']:
                assert boot['replicates'] == 2000
                assert boot['seed'] == 17
                assert boot['minimum_block_seconds'] == 9000
                assert boot['defined_replicate_count']+boot['undefined_replicate_count'] == 2000
                assert boot['interval_condition'] == 'draws_with_at_least_one_valid_paired_origin'
                assert boot['significance_claim'] is False
        assert 'native_mae' not in comparison
        assert 'dex_mse' not in comparison
    assert a['uncertainty']['joint_seed_population_uncertainty_estimated'] is False
    assert a['uncertainty']['validated_replacement'] == 'NO_VALIDATED_REPLACEMENT'


@pytest.mark.parametrize('mutation', ['gap', 'reorder', 'not_int', 'excluded_missing', 'excluded_duplicate', 'excluded_reason', 'excluded_overlap'])
def test_candidate_axis_and_exclusions_are_exhaustive_ordered_and_reason_bearing(cohort, mutation):
    scores, axis, exclusions, settings = cohort
    if mutation == 'gap':
        axis = np.delete(axis, 100)
    elif mutation == 'reorder':
        axis = axis[::-1]
    elif mutation == 'not_int':
        axis = axis.astype(float)
    elif mutation == 'excluded_missing':
        exclusions.pop()
    elif mutation == 'excluded_duplicate':
        exclusions[1] = deepcopy(exclusions[0])
    elif mutation == 'excluded_reason':
        exclusions[0]['reasons'] = []
    else:
        exclusions[0]['issue_time_ns'] = int(axis[4])
        exclusions[0]['origin_id'] = f'origin:{int(axis[4])}'
    with pytest.raises(ValueError):
        summarize(scores, axis, exclusions, settings=settings)


@pytest.mark.parametrize('field,value', [('replicates', 1999), ('seed', 29), ('block_days', [1, 3]), ('minimum_support_seconds', 8999)])
def test_changed_prespecified_settings_rejected(cohort, field, value):
    cohort[3]['uncertainty'][field] = value
    with pytest.raises(ValueError, match='settings'):
        run(cohort)


def classics(cohort):
    scores, _, _, settings = cohort
    sample = scores['supervised'][17]
    result = {}
    for name in settings['classical_models']:
        score = deepcopy(sample)
        score['model_id'] = name
        if name in settings['classical_models'][:6]:
            score['quantile_levels'] = []
            for space in ('dex', 'native'):
                score[space]['aggregate']['mean_pinball'] = None
                for row in score['per_origin']:
                    row[f'{space}_mean_pinball'] = None
        resign(score)
        result[name] = score
    return result


def test_classical_fixed_fit_replication_and_point_only_quantile_unavailability(cohort):
    result = run(cohort, classical_scores=classics(cohort))
    assert len(result['classical_models']) == 13
    comparison = result['comparisons']['jepa_finetune_minus_persistence']
    assert comparison['reference_seed_interpretation'] == 'one_fixed_classical_fit_replicated_across_seeds'
    assert comparison['dex_mae']['seed_effects'] == {'17': -3., '29': -2., '43': -1.}
    assert comparison['dex_mean_pinball'] is None
    assert result['comparisons']['jepa_finetune_minus_persistence_empirical']['dex_mean_pinball']['mean_difference'] == -1.


@pytest.mark.parametrize('mutation', ['missing', 'different_support', 'wrong_name'])
def test_supplied_classical_cohort_must_include_all13_common_support(cohort, mutation):
    classical = classics(cohort)
    if mutation == 'missing':
        classical.pop('persistence')
    elif mutation == 'different_support':
        classical['persistence']['support_fingerprint'] = 'other'
        resign(classical['persistence'])
    else:
        classical['persistence']['model_id'] = 'wrong'
        resign(classical['persistence'])
    with pytest.raises(ValueError):
        run(cohort, classical_scores=classical)


def test_relative_reductions_and_seed_win_fraction(cohort):
    result = run(cohort)
    paired = result['comparisons']['jepa_finetune_minus_supervised']['dex_mae']
    assert paired['relative_reduction'] == .5
    assert paired['seed_relative_reductions'] == {'17': .75, '29': .5, '43': .25}
    assert paired['relative_reduction_reason'] is None
    assert paired['model_win_fraction'] == 1.


def test_zero_reference_loss_relative_reduction_is_unavailable(cohort):
    scores, _, _, settings = cohort
    sample = scores['supervised'][17]
    spec = ForecastSpec(**settings['forecast'])
    grid = FutureGrid(sample['starts_ns'], sample['ends_ns'], sample['issue_times_ns'],
                      tuple(sample['origin_ids']), spec, sample['dataset_fingerprint'])
    target = ForecastTargets(np.ones((4, 30, 2)), np.ones((4, 30, 2), bool), grid)
    for seed in SEEDS:
        values = np.ones((4, 30, 2))
        prediction = ForecastPrediction(values, grid, f'supervised_seed{seed}', (.05, .25, .5, .75, .95),
                                        np.repeat(values[..., None], 5, axis=-1))
        scores['supervised'][seed] = score_external_prediction(target, prediction)
    result = run(cohort)
    paired = result['comparisons']['jepa_finetune_minus_supervised']['dex_mae']
    assert paired['relative_reduction'] is None
    assert paired['relative_reduction_reason'] == 'zero_reference_loss'
    assert paired['seed_relative_reductions'] == {'17': None, '29': None, '43': None}
    assert paired['seed_relative_reduction_reasons'] == {str(seed): 'zero_reference_loss' for seed in SEEDS}
    assert paired['model_win_fraction'] == 0.


def test_seed_diagnostics_are_mean_diagnostics_not_forecast_ensemble(cohort):
    averaged = run(cohort)['variants']['jepa_finetune']['seed_mean_diagnostics']['dex']
    assert averaged['aggregate']['pinball_by_quantile'] == pytest.approx([1.9, 1.5, 1., .5, .1])
    assert averaged['by_target']['xrsa_flux']['pinball_by_quantile'] == pytest.approx([1.9, 1.5, 1., .5, .1])
    assert averaged['by_target_lead']['xrsb_flux'][29]['mean_pinball']['value'] == 1.
    assert averaged['aggregate']['rmse']['value'] == pytest.approx(np.sqrt(14/3))


def test_unequal_origin_counts_keep_equal_origin_losses_and_cell_pooled_rmse(cohort):
    scores, _, _, settings = cohort
    sample = scores['supervised'][17]
    spec = ForecastSpec(**settings['forecast'])
    grid = FutureGrid(sample['starts_ns'], sample['ends_ns'], sample['issue_times_ns'],
                      tuple(sample['origin_ids']), spec, sample['dataset_fingerprint'])
    mask = np.ones((4, 30, 2), bool)
    mask[0] = False
    mask[0, 0, 0] = True
    target = ForecastTargets(np.ones((4, 30, 2)), mask, grid)
    for variant in VARIANTS:
        for seed in SEEDS:
            values = np.full((4, 30, 2), 10.)
            values[0] = 1000.
            prediction = ForecastPrediction(values, grid, f'{variant}_seed{seed}', (.05, .25, .5, .75, .95),
                np.repeat(values[..., None], 5, axis=-1))
            scores[variant][seed] = score_external_prediction(target, prediction)
    averaged = run(cohort)['variants']['jepa_finetune']
    assert averaged['loss_means']['dex_mae'] == 1.5
    assert averaged['loss_means']['dex_mse'] == 3.
    assert averaged['pooled_mse']['dex'] == pytest.approx(189/181)
    assert averaged['rmse']['dex'] == pytest.approx(np.sqrt(189/181))
    assert averaged['seed_mean_diagnostics']['dex']['aggregate']['mae']['value'] == pytest.approx(183/181)


@pytest.mark.parametrize('name', ['persistence', 'persistence_empirical'])
def test_classical_quantile_availability_matches_frozen_arm(cohort, name):
    classical = classics(cohort)
    classical[name]['quantile_levels'] = ([] if name == 'persistence_empirical' else [.05, .25, .5, .75, .95])
    if name == 'persistence_empirical':
        for row in classical[name]['per_origin']:
            row['dex_mean_pinball'] = row['native_mean_pinball'] = None
    else:
        for row in classical[name]['per_origin']:
            row['dex_mean_pinball'] = row['native_mean_pinball'] = 1.
    resign(classical[name])
    with pytest.raises(ValueError):
        run(cohort, classical_scores=classical)


def test_settings_container_hook_cannot_disguise_changed_bootstrap(cohort):
    original = deepcopy(cohort[3])
    changed = deepcopy(original)
    changed['uncertainty']['replicates'] = 1999

    class SettingsSpoof(dict):
        def items(self):
            return original.items()

    with pytest.raises(ValueError, match='settings'):
        summarize(cohort[0], cohort[1], cohort[2], settings=SettingsSpoof(changed))


def test_row_mask_requires_actual_boolean_support(cohort):
    score = cohort[0]['jepa_finetune'][17]
    score['per_origin'][0]['valid_mask'][0][0] = 1
    resign(score)
    with pytest.raises(ValueError):
        run(cohort)
