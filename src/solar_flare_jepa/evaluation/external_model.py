"""Frozen external point/quantile scores without constructing fitting support.

Reuses ``external_flux`` from external-validation f309921 and ``diagnostics``
from V2 M4B 2e3f871. Both kernels and their public APIs are preserved unchanged.
This wrapper neither executes a model nor estimates scientific parameters.
"""
import json

import numpy as np

from ..forecasting.contracts import (
    ForecastTargets, _canonical_strings, canonical_json, fingerprint_payload,
    logical_array, validate_alignment,
)
from .diagnostics import _mean, calibration_diagnostics
from .external_flux import _cell, _losses, evaluate_external_flux
from .trajectory import _forecast_snapshot, _prediction_content, prediction_snapshot


QUANTILE_LEVELS = (.05, .25, .50, .75, .95)
INTERVAL_FORMULA = 'IS_alpha=(U-L)+(2/alpha)*max(L-z,0)+(2/alpha)*max(z-U,0)'


def validate_external_score(score):
    """Detach finite JSON and reject changes to a published score's content.

    Returns a plain dict independent of the caller's buffers and container hooks.
    This checksum detects accidental mutation, not dishonest self-signed scores;
    the input fingerprint likewise describes the scorer's consumed declarations.
    Pairing must independently validate its cohort and exact support contract.
    """
    if not isinstance(score, dict):
        raise ValueError('Expected external score dictionary')
    try:
        detached = json.loads(canonical_json(_canonical_strings(score)))
        expected = detached.pop('score_content_fingerprint')
        if expected != fingerprint_payload(detached):
            raise ValueError('External score content fingerprint differs from actual content')
        if detached.get('schema_version') != 1 or detached.get('adapter') != 'external_model_v1':
            raise ValueError('Unsupported external score schema')
        detached['score_content_fingerprint'] = expected
        return detached
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError('Malformed external score content fingerprint') from error


def _point_metrics(signed, mask, reference):
    result = _losses(signed, mask, reference)
    result['mse'] = _cell(_mean(np.square(signed), mask), int(mask.sum()),
                          None if mask.any() else 'empty_mask')
    return result


def _pooled_detail(values, counts, selection):
    """Pool kernel channel/lead means by their original valid-cell counts."""
    values = np.asarray(values, dtype=float)
    counts = np.asarray(counts, dtype=np.int64)[selection]
    values = values[selection]
    valid = counts > 0
    total = int(counts.sum())
    if not total:
        return None if values.ndim == counts.ndim else [None]*values.shape[-1]
    # Normalize before multiplying to avoid artificial overflow in count*mean.
    weights = counts[valid].astype(float)/total
    selected = values[valid]
    result = np.sum(selected*weights.reshape((-1,)+(1,)*(selected.ndim-1)), axis=0)
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite pooled diagnostic')
    return float(result) if np.ndim(result) == 0 else result.tolist()


def _quantile_metrics(diagnostics, selection, *, space):
    if diagnostics is None:
        return dict(mean_pinball=None, pinball_by_quantile=None,
                    quantile_reliability=None, intervals=None)
    counts = diagnostics['counts']
    count = int(np.asarray(counts)[selection].sum())
    mean_pinball = _pooled_detail(diagnostics['mean_pinball'], counts, selection)
    result = dict(mean_pinball=_cell(mean_pinball, count, None if count else 'empty_mask'),
        pinball_by_quantile=_pooled_detail(diagnostics['pinball_by_quantile'], counts, selection),
        quantile_reliability=_pooled_detail(diagnostics['quantile_reliability'], counts, selection),
        intervals={})
    for interval in diagnostics['intervals']:
        label = 'central_50' if interval['low'] == .25 else 'central_90'
        result['intervals'][label] = dict(low=interval['low'], high=interval['high'],
            nominal_coverage=interval['nominal_coverage'], alpha=2*interval['low'],
            space=space, unit='dex' if space == 'dex' else 'W/m2', count=count,
            formula=INTERVAL_FORMULA,
            **{key: _pooled_detail(interval[key], counts, selection)
               for key in ('coverage', 'width', 'interval_score')})
    return result


def _space_scores(signed, mask, reference, diagnostics, grid, *, space):
    h = mask.shape[1]
    unit = 'dex' if space == 'dex' else 'W/m2'
    def metric(index, detail):
        return dict(**_point_metrics(signed[index], mask[index],
                    None if reference is None else reference[index]),
                    **_quantile_metrics(diagnostics, detail, space=space))
    by_target, by_target_lead = {}, {}
    for channel, name in enumerate(grid.spec.target_names):
        by_target[name] = metric((slice(None), slice(None), channel), (slice(None), channel))
        by_target_lead[name] = [dict(lead_step=lead+1,
            lead_end_seconds=(lead+1)*grid.spec.cadence_seconds,
            **metric((slice(None), lead, channel), (slice(lead, lead+1), slice(channel, channel+1))))
            for lead in range(h)]
    by_lead = [dict(lead_step=lead+1, lead_end_seconds=(lead+1)*grid.spec.cadence_seconds,
        **metric((slice(None), lead, slice(None)), (lead, slice(None)))) for lead in range(h)]
    return dict(space=space, unit=unit,
        units=dict(mae=unit, mse='dex^2' if space == 'dex' else '(W/m2)^2',
            rmse=unit, mean_pinball=unit, pinball_by_quantile=unit,
            width=unit, interval_score=unit, coverage='dimensionless',
            quantile_reliability='dimensionless', persistence_mae_skill='dimensionless',
            persistence_mse_skill='dimensionless'),
        aggregate=metric((slice(None), slice(None), slice(None)), (slice(None), slice(None))),
        by_target=by_target, by_lead=by_lead, by_target_lead=by_target_lead)


def _coverage_detail(mask, names):
    def counts(selected):
        valid, total = int(selected.sum()), int(selected.size)
        return dict(valid_count=valid, total_count=total, prediction_count=total,
                    excluded_count=total-valid)
    return dict(by_target={name: counts(mask[:, :, channel]) for channel, name in enumerate(names)},
        by_lead=[dict(lead_step=lead+1, **counts(mask[:, lead, :])) for lead in range(mask.shape[1])],
        by_target_lead={name: [dict(lead_step=lead+1, **counts(mask[:, lead, channel]))
            for lead in range(mask.shape[1])] for channel, name in enumerate(names)})


def score_external_prediction(targets, prediction, *, persistence=None) -> dict:
    """Score a complete frozen native flux forecast on observation-only masks.

    Native and dimensioned dex point losses pool equal valid cells. Quantile
    arms require the five protocol levels and native point equal to saved q.5.
    Point-only arms receive null quantile outputs, never synthetic uncertainty.
    Per-origin scalar rows use equal valid leads/channels and quantiles, retain
    origin order/issue time/mask/count, and provide MAE, MSE and mean pinball in
    both spaces. Empty observation support returns JSON null without deleting
    origins. MASE is unavailable without independently bound training scales.
    """
    if not isinstance(targets, ForecastTargets):
        raise ValueError('Expected ForecastTargets')
    targets = _forecast_snapshot(targets, ForecastTargets)
    # Unscored payload has no observed meaning and is inert in score identities.
    targets = ForecastTargets(np.where(targets.mask, targets.values, np.nan), targets.mask, targets.grid)
    prediction = prediction_snapshot(prediction)
    persistence = None if persistence is None else prediction_snapshot(persistence)
    grid, mask = targets.grid, targets.mask
    validate_alignment(grid, prediction.grid)
    if persistence is not None:
        validate_alignment(grid, persistence.grid)
    if (grid.spec.transform != 'log10' or len(grid.spec.target_reference) != len(grid.spec.target_names)
            or set(grid.spec.target_units) != {'W/m2'}):
        raise ValueError('External flux scores require dimensioned log10 W/m2 target references')
    if (targets.values[mask] <= 0).any():
        raise ValueError('Dex scores require positive observed flux')
    for forecast in (prediction, persistence):
        if forecast is None:
            continue
        if (forecast.values <= 0).any() or (forecast.quantiles is not None and (forecast.quantiles <= 0).any()):
            raise ValueError('Dex scores require positive forecasts on the full fixed grid')
        if forecast.quantiles is not None:
            if forecast.quantile_levels != QUANTILE_LEVELS:
                raise ValueError('External quantile levels must equal the five protocol levels')
            if not np.array_equal(forecast.values, forecast.quantiles[..., 2]):
                raise ValueError('Quantile forecast point must equal the saved native median')
    # Invoke the original adapter as well as reuse its strict _losses kernel.
    native_base = evaluate_external_flux(targets, prediction, persistence)
    diagnostics = dict(native=None, dex=None)
    if prediction.quantiles is not None:
        diagnostics['native'] = calibration_diagnostics(targets, prediction, space='native')
        diagnostics['dex'] = calibration_diagnostics(targets, prediction, space='log10')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            observed = np.where(mask, targets.values, 1.)
            signed_native = np.where(mask, prediction.values-observed, 0.)
            # Log subtraction keeps dimensioned finite extremes out of F/r overflow.
            log_reference = np.log10(np.asarray(grid.spec.target_reference))
            observed_dex = np.log10(observed)-log_reference
            point_dex = np.log10(prediction.values)-log_reference
            signed_dex = np.where(mask, point_dex-observed_dex, 0.)
            ref_native = ref_dex = None
            if persistence is not None:
                ref_native = np.where(mask, persistence.values-observed, 0.)
                ref_dex = np.where(mask, np.log10(persistence.values)-log_reference-observed_dex, 0.)
            native = _space_scores(signed_native, mask, ref_native, diagnostics['native'], grid, space='native')
            dex = _space_scores(signed_dex, mask, ref_dex, diagnostics['dex'], grid, space='dex')
            per_origin = []
            for i, origin in enumerate(grid.origin_ids):
                row = dict(origin_id=origin, issue_time_ns=int(grid.issue_times_ns[i]),
                           valid_mask=mask[i].tolist(), valid_count=int(mask[i].sum()))
                for space, signed in (('native', signed_native), ('dex', signed_dex)):
                    row[f'{space}_mae'] = _mean(np.abs(signed[i]), mask[i])
                    row[f'{space}_mse'] = _mean(np.square(signed[i]), mask[i])
                    row[f'{space}_mean_pinball'] = (None if diagnostics[space] is None else
                        diagnostics[space]['per_origin_mean_pinball'][i])
                per_origin.append(row)
    except FloatingPointError as error:
        raise ValueError('Nonfinite external evaluation arithmetic') from error
    support = dict(schema_version=1, dataset_fingerprint=grid.dataset_fingerprint,
        spec=grid.spec.as_dict(), origin_ids=list(grid.origin_ids),
        issue_times_ns=logical_array(grid.issue_times_ns), starts_ns=logical_array(grid.starts_ns),
        ends_ns=logical_array(grid.ends_ns), targets=logical_array(targets.values), mask=logical_array(mask))
    result = dict(schema_version=1, adapter='external_model_v1', fit_performed=False,
        model_id=prediction.model_id, point_interpretation=prediction.point_interpretation,
        quantile_point_interpretation=None if prediction.quantiles is None else 'saved_native_median',
        dataset_fingerprint=grid.dataset_fingerprint, spec_fingerprint=grid.spec.fingerprint,
        support_fingerprint=fingerprint_payload(support),
        evaluation_input_fingerprint=fingerprint_payload(dict(adapter='external_model_v1',
            support=support, prediction=_prediction_content(prediction), persistence=_prediction_content(persistence),
            weights=dict(lead=[1]*mask.shape[1], target=[1]*mask.shape[2]))),
        origin_ids=list(grid.origin_ids), issue_times_ns=logical_array(grid.issue_times_ns),
        starts_ns=logical_array(grid.starts_ns), ends_ns=logical_array(grid.ends_ns),
        observation_mask=logical_array(mask), observation_values=logical_array(targets.values),
        target_names=list(grid.spec.target_names), target_units=list(grid.spec.target_units),
        target_reference=list(grid.spec.target_reference), quantile_levels=list(prediction.quantile_levels),
        weights=dict(lead=[1]*mask.shape[1], target=[1]*mask.shape[2]),
        coverage=dict(**native_base['coverage'], excluded_count=int(mask.size-mask.sum()),
            **_coverage_detail(mask, grid.spec.target_names),
            valid_by_target_lead={name: mask[:, :, channel].sum(axis=0).tolist()
                                 for channel, name in enumerate(grid.spec.target_names)},
            valid_by_origin=mask.sum(axis=(1, 2)).tolist()),
        reduction=dict(mask='fixed observation mask; full finite positive forecast grid required',
            weighting='equal valid cells; equal five quantiles within each cell',
            per_origin='equal observed cells and quantiles within each retained origin',
            primary='equal retained-origin means, then equal means of three frozen seeds',
            rmse='sqrt(pooled mean squared error); never average origin/lead/seed RMSE',
            reliability='mean(observed <= predicted quantile); inclusive, dimensionless',
            coverage='inclusive central marginal intervals; invariant to monotone log10',
            interval_score=INTERVAL_FORMULA, log_transform='log10(F)-log10(dimensioned target reference)',
            uncertainty='five quantiles do not define exact CRPS, joint calibration or event probability'),
        native=native, dex=dex, per_origin=per_origin, mase=native_base['mase'])
    result['score_content_fingerprint'] = fingerprint_payload(result)
    return result


_COHORT_VARIANTS = ('jepa_finetune', 'jepa_frozen', 'supervised')
_COHORT_SEEDS = (17, 29, 43)
_CLASSICAL_NAMES = ('persistence', 'training_mean', 'trailing_mean', 'drift', 'ar1', 'direct_ridge',
    'persistence_empirical', 'arima(2,1,0)', 'ar1-constant-normal', 'ar1-arch(1)-normal',
    'ar1-garch(1,1)-normal', 'ar1-garch(1,1)-t', 'ar1-gjr-garch(1,1)-t')
_COHORT_LOSSES = tuple(f'{space}_{loss}' for space in ('native', 'dex')
                       for loss in ('mae', 'mse', 'mean_pinball'))


def _pairing_settings(settings):
    # Validate scientific declarations using the same frozen-input boundary.
    # This reads declarations only: no filesystem, model construction or fit.
    from ..experiments.external_inputs import _protocol
    try:
        if not isinstance(settings, dict):
            raise ValueError('Expected full approved protocol dictionary')
        # Runtime locators are not scientific settings. Read base dictionary
        # content so a caller's items/access hooks cannot spoof frozen fields.
        declarations = _canonical_strings({key: value for key, value in dict.items(settings)
            if key not in ('code_root', 'historical_code_root', 'preparation_code_root')})
        frozen, _, spec = _protocol(declarations)
    except (KeyError, TypeError, OverflowError, ValueError) as error:
        raise ValueError(f'Invalid frozen pairing settings: {error}') from error
    return frozen, spec


def _validated_pairing_score(raw, model_id, spec, *, quantiles_required):
    """Validate actual coordinates/rows independently of a self-signed checksum."""
    from ..forecasting.contracts import FutureGrid, _times
    score = validate_external_score(raw)
    try:
        issues = _times(score['issue_times_ns'], ndim=1)
        n = len(issues)
        if not n or any(int(b) <= int(a) for a, b in zip(issues, issues[1:])):
            raise ValueError('Scores require unique chronological origin times')
        ids = [f'origin:{int(t)}' for t in issues]
        starts = _times(score['starts_ns'], ndim=2)
        ends = _times(score['ends_ns'], ndim=2)
        expected_starts = issues[:, None]+np.arange(spec.horizon_steps)[None, :]*spec.cadence_ns
        mask = np.asarray(score['observation_mask'])
        if (score['model_id'] != model_id or score['fit_performed'] is not False
                or score['spec_fingerprint'] != spec.fingerprint or score['origin_ids'] != ids
                or score['target_names'] != list(spec.target_names)
                or score['target_units'] != list(spec.target_units)
                or score['target_reference'] != list(spec.target_reference)
                or score['weights'] != dict(lead=[1]*spec.horizon_steps, target=[1]*len(spec.target_names))
                or not np.array_equal(starts, expected_starts)
                or not np.array_equal(ends, expected_starts+spec.cadence_ns)
                or mask.dtype.kind != 'b'):
            raise ValueError('Score model, spec, origin, mask or grid declarations differ')
        grid = FutureGrid(starts, ends, issues, tuple(ids), spec, score['dataset_fingerprint'])
        targets = ForecastTargets(score['observation_values'], mask, grid)
        if (targets.values[mask] <= 0).any():
            raise ValueError('Scores require positive observed native flux')
        support = dict(schema_version=1, dataset_fingerprint=grid.dataset_fingerprint,
            spec=spec.as_dict(), origin_ids=ids, issue_times_ns=logical_array(issues),
            starts_ns=logical_array(starts), ends_ns=logical_array(ends),
            targets=logical_array(targets.values), mask=logical_array(mask))
        if score['support_fingerprint'] != fingerprint_payload(support):
            raise ValueError('Score support fingerprint differs from actual support')
        levels = score['quantile_levels']
        if levels not in ([], list(QUANTILE_LEVELS)) or (quantiles_required and not levels):
            raise ValueError('Score requires the planned five quantiles')
        counts = mask.sum(axis=(1, 2)).astype(np.int64)
        coverage = score['coverage']
        if (coverage['valid_count'] != int(counts.sum()) or coverage['total_count'] != mask.size
                or coverage['valid_by_origin'] != counts.tolist()):
            raise ValueError('Score coverage differs from actual observation support')
        rows = score['per_origin']
        if len(rows) != n:
            raise ValueError('Score rows must retain every origin')
        losses = {name: [] for name in _COHORT_LOSSES}
        for index, row in enumerate(rows):
            count = int(counts[index])
            if (row['origin_id'] != ids[index] or type(row['issue_time_ns']) is not int
                    or row['issue_time_ns'] != int(issues[index])
                    or type(row['valid_count']) is not int or row['valid_count'] != count
                    or np.asarray(row['valid_mask']).dtype.kind != 'b'
                    or row['valid_mask'] != mask[index].tolist()):
                raise ValueError('Score row identity or observation mask/count differs')
            for name in losses:
                value = row[name]
                unavailable = not count or (name.endswith('mean_pinball') and not levels)
                if unavailable:
                    if value is not None:
                        raise ValueError('Unobserved/unavailable loss must be null')
                elif (type(value) not in (int, float) or not np.isfinite(value) or value < 0):
                    raise ValueError('Model failure cannot become missing per-origin loss')
                losses[name].append(np.nan if value is None else float(value))
        return score, support, issues, counts, {k: np.asarray(v) for k, v in losses.items()}
    except (KeyError, TypeError, IndexError, OverflowError) as error:
        raise ValueError('Malformed external score pairing contract') from error


def _cohort_loss_summary(loss_arrays, counts):
    """Equal origin loss means and separately valid-cell pooled squared error."""
    observed = counts > 0
    total = int(counts.sum())
    means = {}
    for name, values in loss_arrays.items():
        means[name] = (None if not observed.any() or np.isnan(values[observed]).all()
                       else float(np.mean(values[observed])))
    pooled = {space: (None if not total else float(np.sum(
        loss_arrays[f'{space}_mse'][observed]*(counts[observed]/total))))
        for space in ('native', 'dex')}
    if any(value is not None and not np.isfinite(value) for value in (*means.values(), *pooled.values())):
        raise ValueError('Nonfinite external cohort loss reduction')
    return dict(loss_means=means, pooled_mse=pooled,
                rmse={space: None if value is None else float(np.sqrt(value)) for space, value in pooled.items()})


def _full_axis_losses(losses, axis, retained_indices):
    full = {}
    for name, values in losses.items():
        vector = np.full(len(axis), np.nan)
        vector[retained_indices] = values
        full[name] = vector
    return full


def _mean_seed_diagnostics(values):
    """Average saved score diagnostics; reconstruct every RMSE from mean MSE."""
    first = values[0]
    if all(value == first for value in values):
        return first
    if type(first) is dict and all(type(value) is dict and value.keys() == first.keys() for value in values):
        result = {key: _mean_seed_diagnostics([value[key] for value in values]) for key in first}
        if 'mse' in result and 'rmse' in result:
            mse = result['mse']['value']
            result['rmse'] = _cell(None if mse is None else float(np.sqrt(mse)),
                result['mse']['count'], result['mse']['reason'])
        return result
    if type(first) is list and all(type(value) is list and len(value) == len(first) for value in values):
        return [_mean_seed_diagnostics([value[index] for value in values]) for index in range(len(first))]
    if all(type(value) in (int, float) for value in values):
        return float(np.mean(values))
    raise ValueError('Seed diagnostic structure or availability differs')


def _seed_paired_comparison(model, reference, axis, settings, *, role, classical=False):
    from .uncertainty import paired_block_bootstrap
    result = dict(role=role, direction='model_loss - reference_loss; negative favors model',
        reference_seed_interpretation=('one_fixed_classical_fit_replicated_across_seeds' if classical
                                       else 'matched_frozen_checkpoint_seeds'),
        uncertainty_condition='fixed nine checkpoints and fixed fitted classical references; calendar sensitivity only')
    for name in ('dex_mean_pinball', 'dex_mae'):
        if np.isnan(reference['full'][name]).all():
            result[name] = None
            continue
        model_loss, reference_loss = model['full'][name], reference['full'][name]
        if not np.array_equal(np.isnan(model_loss), np.isnan(reference_loss)):
            raise ValueError('Paired loss support differs; model failures cannot shrink support')
        effects, relative, relative_reasons = {}, {}, {}
        for seed in _COHORT_SEEDS:
            left = model['seed_losses'][seed][name]
            right = reference['seed_losses'][seed][name]
            observed = np.isfinite(left)
            if not np.array_equal(observed, np.isfinite(right)) or not observed.any():
                raise ValueError('Paired seed losses require common observed origin support')
            effects[str(seed)] = float(np.mean(left[observed]-right[observed]))
            reference_mean = float(np.mean(right[observed]))
            relative[str(seed)] = None if reference_mean == 0 else 1-float(np.mean(left[observed]))/reference_mean
            relative_reasons[str(seed)] = 'zero_reference_loss' if reference_mean == 0 else None
        values = np.array(list(effects.values()))
        reference_mean = float(np.mean(reference_loss[np.isfinite(reference_loss)]))
        model_mean = float(np.mean(model_loss[np.isfinite(model_loss)]))
        uncertainty = settings['uncertainty']
        calendars = [paired_block_bootstrap(axis, model_loss, reference_loss, day*86400,
            replicates=uncertainty['replicates'], seed=uncertainty['seed'], confidence=uncertainty['confidence'],
            minimum_block_seconds=uncertainty['minimum_support_seconds']) for day in uncertainty['block_days']]
        for calendar in calendars:
            calendar['loss_units'] = 'dex'
            calendar['fixed_checkpoint_conditioning'] = True
            calendar['seed_resampling_performed'] = False
        result[name] = dict(seed_effects=effects, mean_difference=float(np.mean(values)),
            relative_reduction=None if reference_mean == 0 else 1-model_mean/reference_mean,
            relative_reduction_reason='zero_reference_loss' if reference_mean == 0 else None,
            seed_relative_reductions=relative, seed_relative_reduction_reasons=relative_reasons,
            sample_standard_deviation=float(np.std(values, ddof=1)),
            model_win_count=int((values < 0).sum()), reference_win_count=int((values > 0).sum()),
            model_win_fraction=float(np.mean(values < 0)),
            tie_count=int((values == 0).sum()),
            leave_one_seed_out_mean={str(seed): float(np.mean(np.delete(values, index)))
                                    for index, seed in enumerate(_COHORT_SEEDS)},
            per_origin_mean_differences=logical_array(model_loss-reference_loss),
            calendar_sensitivity=calendars)
    return result


def summarize_external_cohort(scores_by_variant_seed, candidate_issue_times_ns, exclusions,
                              *, settings, classical_scores=None) -> dict:
    """Pair all nine frozen checkpoint scores on the complete January candidate axis.

    ``settings`` is the approved full protocol. ``classical_scores`` optionally
    supplies all thirteen name-to-score fixed classical fits, each replicated
    over the matched checkpoint seeds. All scores are detached and checked for
    exact target/grid/row support before any reduction. Exclusions are Task1's
    ordered reason-bearing candidate list. Only observation exclusions can
    create common missing positions; per-model failures raise.

    Losses average within each retained origin before equal origins/seeds.
    RMSE instead takes the square root of valid-cell pooled squared losses.
    Calendar draws condition on fixed checkpoints, never resample three seeds,
    and provide no significance or joint training-population uncertainty claim.
    """
    from ..forecasting.contracts import _times
    frozen, spec = _pairing_settings(settings)
    if type(scores_by_variant_seed) is not dict or set(scores_by_variant_seed) != set(_COHORT_VARIANTS):
        raise ValueError('Complete cohort requires exactly three planned variants')
    axis = _times(candidate_issue_times_ns, ndim=1)
    start, end, cadence = 1735689600000000000, 1738368000000000000, 1800*10**9
    if not np.array_equal(axis, np.arange(start, end, cadence, dtype=np.int64)):
        raise ValueError('Full regular January 30-minute candidate axis is required')
    detached_exclusions = json.loads(canonical_json(_canonical_strings(exclusions)))
    if type(detached_exclusions) is not list:
        raise ValueError('Ordered reason-bearing candidate exclusions are required')
    excluded = []
    for item in detached_exclusions:
        if (type(item) is not dict or type(item.get('issue_time_ns')) is not int
                or item.get('origin_id') != f"origin:{item.get('issue_time_ns')}"
                or type(item.get('reasons')) is not list or not item['reasons']
                or any(type(reason) is not str or not reason for reason in item['reasons'])):
            raise ValueError('Invalid candidate observation exclusion')
        excluded.append(item['issue_time_ns'])
    if excluded != sorted(set(excluded)):
        raise ValueError('Candidate exclusions must be unique and chronological')
    records, common = {}, None
    for variant in _COHORT_VARIANTS:
        seeds = scores_by_variant_seed[variant]
        if (type(seeds) is not dict or any(type(seed) is not int for seed in seeds)
                or set(seeds) != set(_COHORT_SEEDS)):
            raise ValueError('Complete cohort requires integer seeds17,29,43 for every variant')
        records[variant] = {}
        for seed in _COHORT_SEEDS:
            record = _validated_pairing_score(seeds[seed], f'{variant}_seed{seed}', spec, quantiles_required=True)
            if common is None:
                common = record[1]
            elif record[1] != common:
                raise ValueError('All nine scores require identical ordered target/grid/observation support')
            records[variant][seed] = record
    reference = records['supervised'][17]
    _, _, issues, counts, _ = reference
    combined = list(map(int, issues))+excluded
    if len(set(combined)) != len(combined) or sorted(combined) != axis.tolist():
        raise ValueError('Retained and excluded candidate support must be exhaustive and disjoint')
    indices = np.searchsorted(axis, issues)
    if not counts.any():
        raise ValueError('Cohort requires observed target support')
    classical = {}
    if classical_scores is not None:
        if type(classical_scores) is not dict or set(classical_scores) != set(_CLASSICAL_NAMES):
            raise ValueError('Supplied classical cohort requires all thirteen fixed models')
        for name in _CLASSICAL_NAMES:
            quantiles_required = name not in _CLASSICAL_NAMES[:6]
            record = _validated_pairing_score(classical_scores[name], name, spec,
                                             quantiles_required=quantiles_required)
            if not quantiles_required and record[0]['quantile_levels']:
                raise ValueError('Point-only classical references cannot acquire fabricated quantiles')
            if record[1] != common:
                raise ValueError('Classical scores require identical checkpoint observation support')
            classical[name] = record
    variants, working = {}, {}
    for variant, seeds in records.items():
        losses = {seed: record[4] for seed, record in seeds.items()}
        average = {name: np.mean([losses[seed][name] for seed in _COHORT_SEEDS], axis=0)
                   for name in _COHORT_LOSSES}
        full = _full_axis_losses(average, axis, indices)
        variants[variant] = dict(**_cohort_loss_summary(average, counts),
            seed_mean_diagnostics={space: _mean_seed_diagnostics([seeds[seed][0][space]
                for seed in _COHORT_SEEDS]) for space in ('native', 'dex')},
            seeds={str(seed): dict(**_cohort_loss_summary(losses[seed], counts),
                model_id=seeds[seed][0]['model_id'], score_content_fingerprint=seeds[seed][0]['score_content_fingerprint'])
                for seed in _COHORT_SEEDS},
            per_origin=[dict(origin_id=origin, issue_time_ns=int(issue), valid_count=int(count),
                **{name: None if np.isnan(average[name][i]) else float(average[name][i]) for name in _COHORT_LOSSES})
                for i, (origin, issue, count) in enumerate(zip(common['origin_ids'], issues, counts))],
            full_axis_losses={name: logical_array(vector) for name, vector in full.items()},
            forecast_ensemble_created=False)
        working[variant] = dict(seed_losses=losses, full=full)
    comparisons = {f'{variant}_minus_supervised': _seed_paired_comparison(working[variant], working['supervised'],
        axis, frozen, role=role) for variant, role in (('jepa_finetune', 'primary'), ('jepa_frozen', 'secondary'))}
    classical_results = {}
    for name, record in classical.items():
        losses = record[4]
        full = _full_axis_losses(losses, axis, indices)
        classical_results[name] = dict(**_cohort_loss_summary(losses, counts),
            score_content_fingerprint=record[0]['score_content_fingerprint'],
            full_axis_losses={key: logical_array(vector) for key, vector in full.items()},
            seed_interpretation='one_fixed_classical_fit_replicated_across_seeds')
        replicated = dict(seed_losses={seed: losses for seed in _COHORT_SEEDS}, full=full)
        for variant in _COHORT_VARIANTS:
            comparisons[f'{variant}_minus_{name}'] = _seed_paired_comparison(working[variant], replicated,
                axis, frozen, role='descriptive_classical_reference', classical=True)
    result = dict(schema_version=1, adapter='external_model_cohort_v1', fit_performed=False,
        protocol_fingerprint=fingerprint_payload(frozen), seeds=list(_COHORT_SEEDS),
        support=dict(support_fingerprint=reference[0]['support_fingerprint'], candidate_origin_count=len(axis),
            retained_origin_count=len(issues), observed_origin_count=int((counts > 0).sum()),
            excluded_candidate_count=len(excluded), candidate_issue_times_ns=logical_array(axis),
            retained_candidate_indices=indices.tolist(), candidate_exclusions=detached_exclusions,
            valid_target_cell_count=int(counts.sum()), origin_ids=common['origin_ids']),
        variants=variants, classical_models=classical_results, comparisons=comparisons,
        reduction=dict(loss_means='equal observed per-origin loss means, then equal three frozen seeds',
            rmse='sqrt(valid-cell pooled squared loss across equal three seeds)',
            paired='matched seed differences before equal seed reduction; negative favors model',
            forecast_ensemble_created=False),
        uncertainty=dict(**frozen['uncertainty'], fixed_checkpoint_conditioning=True,
            joint_seed_population_uncertainty_estimated=False, seed_resampling_performed=False,
            validated_replacement='NO_VALIDATED_REPLACEMENT', significance_claim=False,
            limitations=['Three fixed seeds do not identify training-population uncertainty.',
                'Calendar block intervals condition on frozen checkpoint and classical fit state.',
                'Descriptive1/3/7-day sensitivity is not a validated V2 uncertainty replacement.',
                'No p-values, significance claims or joint seed/calendar population intervals.']))
    # Reject arithmetic overflow and guarantee a detached finite JSON artifact.
    result = json.loads(canonical_json(result))
    result['cohort_content_fingerprint'] = fingerprint_payload(result)
    return result
