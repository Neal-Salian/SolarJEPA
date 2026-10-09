"""v1 comparison: temporal JEPA versus ARIMA/SARIMA and ARCH/GARCH families.

Every model is fitted on the training partition only. ARIMA order and JEPA
checkpoints are selected on validation only; the test partition is scored once
after all selections are frozen. All models are scored on the identical P1
retained origins and valid target cells. Strata use observed future targets as
retrospective evaluation annotations only; they never enter any model input.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import uuid

import numpy as np

from solar_flare_jepa.evaluation import evaluate_trajectory
from solar_flare_jepa.evaluation.probabilistic import block_bootstrap, log_scores
from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.contracts import ForecastSpec, canonical_json
from solar_flare_jepa.forecasting.splitting import chronological_partitions
from solar_flare_jepa.forecasting.statistical import make_probabilistic
from solar_flare_jepa.forecasting.windows import build_partition_windows
from .config import config_fingerprint, load_config, read_finite_json, utc_ns
from .provenance import code_provenance, _destination, _source_identity, _source_path
from .runner import _dataset, _dataset_manifest

M_CLASS = 1e-5   # W/m2, GOES 0.1-0.8 nm M1 threshold (SWPC definition)
C_CLASS = 1e-6
DAY_NS = 86_400 * 10**9


def _strata(window, spec):
    """Retrospective per-origin annotations from observed XRS-B targets."""
    b = spec.target_names.index('xrsb_flux')
    fb = spec.feature_names.index('xrsb_flux')
    targets = np.where(window.targets.mask[..., b], window.targets.values[..., b], np.nan)
    future_max = np.nanmax(np.where(np.isnan(targets), -np.inf, targets), axis=1)
    context = window.context
    last = np.array([context.values[n, np.flatnonzero(context.mask[n, :, fb])[-1], fb]
                     for n in range(len(context.origin_ids))])
    return dict(flaring_m_plus=future_max >= M_CLASS, quiet_below_c=future_max < C_CLASS,
                rising_x2=future_max >= 2 * last, all=np.ones(len(last), bool))


def _stratified(scores, strata):
    result = {}
    for name, selected in strata.items():
        entry = dict(origins=int(selected.sum()))
        for key, values in scores['per_origin'].items():
            values = np.asarray(values, float)[selected]
            entry[key] = float(np.nanmean(values)) if len(values) else None
        result[name] = entry
    return result


def _train_diagnostics(training, spec):
    """ACF of log differences and squared differences plus Engle's ARCH-LM, train only.

    Only adjacent valid pairs enter; concatenating valid pairs across gaps is an
    approximation recorded with the counts. Evidence for or against seasonality
    and conditional heteroskedasticity, not a model-adequacy proof.
    """
    from statsmodels.stats.diagnostic import het_arch
    adjacent = np.diff(np.asarray(training.raw_starts_ns, np.int64)) == spec.cadence_ns
    result = {}
    for k, name in enumerate(spec.target_names):
        valid = training.raw_target_mask[:, k]
        pairs = adjacent & valid[1:] & valid[:-1]
        y = np.log10(np.where(valid, training.raw_targets[:, k], 1.) / spec.target_reference[k])
        r = (y[1:] - y[:-1])[pairs]
        r = r - r.mean()
        def acf(x, lag):
            return float((x[lag:] * x[:-lag]).sum() / (x * x).sum())
        lags = (1, 2, 5, 10, 30, 60, 120, 1440)
        lm, lm_p, _, _ = het_arch(r, nlags=10)
        result[name] = dict(valid_difference_pairs=int(pairs.sum()), std=float(r.std()),
                            excess_kurtosis=float(((r / r.std())**4).mean() - 3),
                            acf_diff={str(l): acf(r, l) for l in lags},
                            acf_squared_diff={str(l): acf(r**2 - (r**2).mean(), l) for l in lags},
                            arch_lm_10=dict(statistic=float(lm), p_value=float(lm_p)))
    return result


def _score(model_id, prediction, window, training, persistence, spec, metrics_cfg):
    native = evaluate_trajectory(window.targets, prediction, training, persistence=persistence,
                                 lead_weights=metrics_cfg['lead_weights'],
                                 target_weights=metrics_cfg['target_weights'])
    native.pop('per_origin')
    native.pop('by_target_lead')
    logs = log_scores(window.targets, prediction, spec)
    return dict(model_id=model_id, native=native, log=logs)


def run_v1(config_path, models_path, root, *, output_dir=None, dev=False, quick=False):
    root = _source_path(root)
    config_path = Path(config_path) if Path(config_path).is_absolute() else root / config_path
    models_path = Path(models_path) if Path(models_path).is_absolute() else root / models_path
    provenance = code_provenance(root, require_clean=not dev, require_installed_match=not dev)
    config = load_config(config_path)
    models = read_finite_json(models_path)
    destination = _destination(root, output_dir or root / 'results' / 'experiments' / f'v1-{uuid.uuid4().hex[:8]}')
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing v1 output directory')
    started = datetime.now(timezone.utc).isoformat()
    log = lambda message: print(f'[{datetime.now():%H:%M:%S}] {message}', flush=True)

    dataset = _dataset(config, root)
    spec = ForecastSpec(**config['forecast'])
    boundaries = [dict(name=p['name'], start_ns=utc_ns(p['start_utc']), end_ns=utc_ns(p['end_utc']))
                  for p in config['splits']]
    partitions = chronological_partitions(dataset, boundaries)
    windows = {p.name: build_partition_windows(dataset, spec, p) for p in partitions}
    training = windows['train'].training_slice
    held_out = ('validation', 'test')
    log(f"windows: {({k: len(w.context.origin_ids) for k, w in windows.items()})}")
    diagnostics = _train_diagnostics(training, spec)
    persistence = make_baseline('persistence', {}).fit(training)
    reference = {name: persistence.predict(windows[name].context, windows[name].targets.grid) for name in held_out}
    strata = {name: _strata(windows[name], spec) for name in held_out}
    blocks = {name: np.asarray(windows[name].targets.grid.issue_times_ns) // DAY_NS for name in held_out}

    results, predictions, fits = {name: {} for name in held_out}, {name: {} for name in held_out}, {}

    def evaluate(model_id, predict, family, record=None, partitions=held_out):
        for name in partitions:
            began = time.perf_counter()
            prediction = predict(windows[name].context, windows[name].targets.grid)
            entry = _score(model_id, prediction, windows[name], training, reference[name], spec, config['metrics'])
            entry.update(family=family, predict_seconds=time.perf_counter() - began,
                         strata=_stratified(entry['log'], strata[name]))
            results[name][model_id] = entry
            predictions[name][model_id] = prediction
        if record is not None:
            fits[model_id] = record

    # 1. Existing deterministic P1 point comparators (fixed parameters).
    for item in config['baselines']:
        began = time.perf_counter()
        model = make_baseline(item['name'], item['parameters']).fit(training)
        evaluate(model.name, model.predict, 'p1_point_baseline',
                 dict(parameters=model.parameters, fit_seconds=time.perf_counter() - began))
        log(f'baseline {model.name} done')

    # 2. Classical probabilistic comparators. Candidates in a selection group
    #    are compared on validation mean pinball; only the winner is tested.
    groups, failures, checkpoints = {}, [], {}
    for item in models['statistical']:
        began = time.perf_counter()
        try:
            model = make_probabilistic(item['name'], item['parameters']).fit(training)
            model_id = model.name
            fit_record = dict(parameters=model.parameters, fit_seconds=time.perf_counter() - began,
                              selection_group=item.get('selection_group'))
            evaluate(model_id, model.predict, item.get('family', item['name']), fit_record,
                     partitions=('validation',))
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as error:
            # A model failure is reported, never converted into origin dropping.
            failures.append(dict(model=item, stage='fit_or_validation', error_type=type(error).__name__,
                                 reason=str(error)))
            log(f'statistical {item} FAILED: {error}')
            continue
        groups.setdefault(item.get('selection_group') or model_id, []).append((model_id, model))
        log(f'statistical {model_id} fitted and validated ({fit_record["fit_seconds"]:.1f}s)')
    selections = {}
    for group, members in groups.items():
        chosen = min(members, key=lambda m: results['validation'][m[0]]['log']['mean_pinball'])
        selections[group] = dict(selected=chosen[0], criterion='validation log mean pinball',
                                 candidates={m[0]: results['validation'][m[0]]['log']['mean_pinball'] for m in members})
        for model_id, model in members:
            if model_id == chosen[0] or len(members) == 1:
                try:
                    evaluate(model_id, model.predict, results['validation'][model_id]['family'],
                             partitions=('test',))
                except (ValueError, FloatingPointError, np.linalg.LinAlgError) as error:
                    failures.append(dict(model=model_id, stage='test', error_type=type(error).__name__,
                                         reason=str(error)))
                    log(f'statistical {model_id} FAILED on test: {error}')
                    continue
                log(f'statistical {model_id} tested')

    # 3. Temporal JEPA variants and the identical supervised architecture.
    jepa_cfg = models.get('jepa')
    if jepa_cfg:
        from solar_flare_jepa.training.jepa import JepaConfig, fit_forecaster
        settings = dict(jepa_cfg['config'])
        if quick:
            settings.update(jepa_cfg.get('quick_overrides', {}))
        for variant in jepa_cfg['variants']:
            for seed in jepa_cfg['seeds'][:1 if quick else None]:
                began = time.perf_counter()
                config_obj = JepaConfig(**dict(settings, seed=seed))
                model_id = f'{variant}_seed{seed}'
                try:
                    trained = fit_forecaster(training, windows['validation'], config_obj, variant, seed)
                    evaluate(model_id, trained.predict, variant,
                             dict(record=trained.record, fit_seconds=time.perf_counter() - began, seed=seed))
                except (ValueError, FloatingPointError, RuntimeError) as error:
                    failures.append(dict(model=model_id, stage='fit_or_evaluation', error_type=type(error).__name__,
                                         reason=str(error)))
                    log(f'jepa {model_id} FAILED: {error}')
                    continue
                checkpoints[model_id] = trained
                log(f'jepa {model_id} done ({time.perf_counter() - began:.0f}s)')

    # 4. Paired daily-block bootstrap on test against fixed references.
    comparisons = []
    test = results['test']
    # Reference models are chosen on validation, never on test.
    validation = results['validation']
    best = lambda prefix: min((k for k in test if k.startswith(prefix) and k in validation),
                              key=lambda k: validation[k]['log']['mean_pinball'], default=None)
    references = [k for k in ('persistence_empirical', best('ar1-garch'), best('ar1-gjr'), best('arima'))
                  if k in test]
    for model_id, entry in test.items():
        if 'mean_pinball' not in entry['log']['per_origin']:
            continue
        for ref in references:
            if ref == model_id:
                continue
            for metric in ('mean_pinball', 'log_mae'):
                comparisons.append(dict(model=model_id, reference=ref, metric=metric, partition='test',
                    **block_bootstrap(entry['log']['per_origin'][metric], test[ref]['log']['per_origin'][metric],
                                      blocks['test'], replicates=2000, seed=17)))

    destination.mkdir(parents=True)
    for model_id, trained in checkpoints.items():
        trained.save(destination / f'{model_id}.pt')
    summary = dict(schema_version=1, status='complete', started_utc=started,
                   finished_utc=datetime.now(timezone.utc).isoformat(), dev_mode=dev, quick=quick,
                   config=config, config_fingerprint=config_fingerprint(config),
                   models_config=models, models_config_identity=_source_identity(models_path),
                   dataset=_dataset_manifest(dataset),
                   split_manifest=[windows[p.name].manifest() for p in partitions],
                   provenance=dict(git=provenance.get('git'), source_fingerprint=provenance['source']['fingerprint']),
                   selections=selections, fits=fits, failures=failures, diagnostics=diagnostics, comparisons=comparisons,
                   limitations=['four months of one satellite (GOES-16, May-Aug 2024); not cycle-wide generalization',
                                'overlapping contexts; origins are not independent samples',
                                'retrospective science-archive data; operational latency UNKNOWN',
                                'five quantiles: mean pinball is a quantile score, not exact CRPS',
                                'no flare-event labels; strata are retrospective evaluation annotations'])
    scores = {name: {k: {kk: vv for kk, vv in v.items()} for k, v in results[name].items()} for name in held_out}
    for name in held_out:
        for entry in scores[name].values():
            entry['log'] = {k: v for k, v in entry['log'].items() if k != 'per_origin'}
    (destination / 'summary.json').write_text(canonical_json(dict(summary, scores=scores)) + '\n')
    (destination / 'per_origin.json').write_text(canonical_json({
        name: dict(origin_ids=list(windows[name].targets.grid.origin_ids),
                   issue_times_ns=np.asarray(windows[name].targets.grid.issue_times_ns).tolist(),
                   strata={k: v.tolist() for k, v in strata[name].items()},
                   losses={m: e['log']['per_origin'] for m, e in results[name].items()})
        for name in held_out}) + '\n')
    test_window = windows['test']
    arrays = dict(origin_ids=np.asarray(test_window.targets.grid.origin_ids),
                  issue_times_ns=np.asarray(test_window.targets.grid.issue_times_ns),
                  targets=test_window.targets.values, target_mask=test_window.targets.mask,
                  context=test_window.context.values, context_mask=test_window.context.mask,
                  model_ids=np.asarray(list(predictions['test'])))
    for i, prediction in enumerate(predictions['test'].values()):
        arrays[f'point_{i}'] = prediction.values
        if prediction.quantiles is not None:
            arrays[f'quantiles_{i}'] = prediction.quantiles
    np.savez_compressed(destination / 'test_predictions.npz', **arrays)
    log(f'wrote {destination}')
    return destination
