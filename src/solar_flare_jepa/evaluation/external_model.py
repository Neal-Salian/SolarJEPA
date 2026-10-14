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
