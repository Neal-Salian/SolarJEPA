"""Scientific validation and pipeline compatibility of restored GOES development data.

Read-only. Reuses the repository's own native contract (``validate_goes_files``,
``goes_training``) and preprocessing (P1 windows, train-only ``Normalization``);
nothing here changes quality rules, fills gaps, normalizes differently or trains.
``pipeline_smoke`` builds training and validation windows only: test windows are
never constructed, scored or released.
"""
from datetime import datetime, time, timedelta
from pathlib import Path

import numpy as np

from .foundation import GOES_INSTRUMENT, validate_goes_files
from .goes import TIME_UNITS
from . import goes_acquisition as acquisition

# Native attributes that tie a file to the pinned official product (observed on the restored archive).
EXPECTED_ATTRIBUTES = dict(platform='g16', instrument=GOES_INSTRUMENT, title='L2 XRS 1 minute average',
                           processing_level='Level 2', time_coverage_resolution='PT1M',
                           naming_authority='gov.nesdis.noaa')
PROVENANCE_ATTRIBUTES = ('date_created', 'algorithm', 'algorithm_version', 'algorithm_date',
                         'processing_parameters_file', 'instrument_id', 'L1b_production_site', 'git_commit_hash',
                         'publisher_institution')
DEVELOPMENT_SPLITS = ('train', 'validation')


def _utc_midnight(value):
    """The date of an exact UTC-midnight ISO timestamp, else None (offsets and other times are rejected)."""
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.utcoffset() != timedelta(0) or parsed.timetz().replace(tzinfo=None) != time(0):
        return None
    return parsed.date()


def native_identity(path, row):
    """Check native metadata against the pinned identity; return checks and provenance (no data decode)."""
    import netCDF4
    path = Path(path)
    day = acquisition._date(row['nominal_date'])
    with netCDF4.Dataset(path) as ds:
        attrs = {name: ds.getncattr(name) for name in ds.ncattrs()}
        units = {name: getattr(ds[name], 'units', None) for name in ('xrsa_flux', 'xrsb_flux', 'time')
                 if name in ds.variables}
    checks = {name: attrs.get(name) == value for name, value in EXPECTED_ATTRIBUTES.items()}
    checks.update(
        id_equals_filename=attrs.get('id') == path.name,
        filename_version=path.name.endswith(f'_v{acquisition.VERSION}.nc'),
        coverage_start_is_nominal_day=_utc_midnight(attrs.get('time_coverage_start')) == day,
        coverage_end_is_next_day=_utc_midnight(attrs.get('time_coverage_end')) == day + timedelta(days=1),
        flux_units_w_m2=units.get('xrsa_flux') == 'W/m2' and units.get('xrsb_flux') == 'W/m2',
        time_units=units.get('time') == TIME_UNITS)
    provenance = {name: (np.asarray(attrs[name]).tolist() if name in attrs else None) for name in PROVENANCE_ATTRIBUTES}
    return dict(path=row['path'], passed=all(checks.values()), checks=checks, provenance=provenance)


def quality_summary(frame):
    """Counts from the validated native grid frame; observations are counted, never altered."""
    observed = frame['observed'].to_numpy(bool)
    summary = dict(grid_bins=len(frame), observed_bins=int(observed.sum()), missing_bins=int((~observed).sum()))
    native = frame[observed]
    for ch in ('xrsa', 'xrsb'):
        raw = native[ch + '_flux_raw'].to_numpy(float)
        count = native[ch + '_num'].to_numpy(float)
        valid = native[ch + '_valid'].to_numpy(bool)
        summary[ch] = dict(
            units='W/m2', valid_bins=int(valid.sum()), invalid_observed_bins=int((~valid).sum()),
            valid_fraction_of_grid=float(valid.sum() / len(frame)) if len(frame) else None,
            status_flag_counts={str(int(k)) if np.isfinite(k) else 'nonfinite': int(v) for k, v in zip(
                *np.unique(native[ch + '_flag'].to_numpy(float), return_counts=True))},
            nonfinite_raw=int((~np.isfinite(raw)).sum()), nonpositive_raw=int((np.isfinite(raw) & (raw <= 0)).sum()),
            samples_full_60=int((count == 60).sum()), samples_1_to_59=int(((count > 0) & (count < 60)).sum()),
            valid_samples_1_to_59=int((valid & (count > 0) & (count < 60)).sum()),
            valid_samples_lt_30=int((valid & (count > 0) & (count < 30)).sum()),
            samples_zero_or_invalid=int((~np.isfinite(count) | (count <= 0) | (count > 60)).sum()),
            valid_log10_min=float(np.log10(raw[valid]).min()) if valid.any() else None,
            valid_log10_max=float(np.log10(raw[valid]).max()) if valid.any() else None)
    eflag = native['electron_correction_flag'].to_numpy(float)
    summary['electron_correction_flag_counts'] = {
        str(int(k)) if np.isfinite(k) else 'nonfinite': int(v) for k, v in zip(*np.unique(eflag, return_counts=True))}
    if 'xrs_primary_chan' in native:
        summary['primary_channel_counts'] = {str(int(k)) if np.isfinite(k) else 'nonfinite': int(v) for k, v in zip(
            *np.unique(native['xrs_primary_chan'].to_numpy(float), return_counts=True))}
    days = frame.index.floor('D')
    per_day = frame.groupby(days)['observed'].sum()
    summary['observed_bins_per_day'] = dict(min=int(per_day.min()), max=int(per_day.max()),
                                            days_below_1440=int((per_day < 1440).sum()))
    return summary


def validate_manifest_data(plan, manifest, root):
    """Native identity of every file plus the repository's native time-series contract for one manifest."""
    import pandas as pd
    root = Path(root).resolve()
    rows = [r for r in plan['files'] if r['manifest'] == manifest['path']]
    paths = acquisition.verify_history(root / manifest['path'], root)
    identities = [native_identity(path, row) for path, row in zip(paths, rows)]
    inventory = acquisition._json(root / manifest['path'])
    interval = inventory['selected_interval']
    frame, report = validate_goes_files(paths, start_utc=pd.Timestamp(interval['start'], tz='UTC').isoformat(),
                                        end_utc=pd.Timestamp(interval['end_exclusive'], tz='UTC').isoformat())
    return dict(manifest=manifest['path'], role=manifest['role'], files=len(paths),
                native_identity_passed=sum(i['passed'] for i in identities), identities=identities,
                contract=dict((k, report[k]) for k in (
                    'status', 'observed_start_utc', 'observed_end_utc', 'observed_rows', 'grid_rows', 'missing_bins',
                    'missing_intervals', 'cadence_seconds', 'chronological_order', 'duplicate_timestamps',
                    'imputation', 'normalization')),
                quality=quality_summary(frame))


def _containment(window, partition, spec):
    """Every retained origin's full context and target support lies inside its partition."""
    context_start = np.asarray(window.context.starts_ns).min(axis=1) if len(window.context.origin_ids) else []
    target_end = np.asarray(window.targets.grid.ends_ns).max(axis=1) if len(window.context.origin_ids) else []
    return dict(context_inside=bool(np.all(np.asarray(context_start) >= partition.start_ns)),
                targets_inside=bool(np.all(np.asarray(target_end) <= partition.end_ns)))


def _v2_preparation(train_window, validation_window, max_train_windows):
    """The V2 trainers' own data preparation (``training.controlled._prepare``) plus validation tensors.

    No model is built and no optimizer step runs. Requires the optional Torch extra.
    """
    from solar_flare_jepa.training.controlled import _prepare
    from solar_flare_jepa.training.jepa import JepaConfig, window_tensors
    _, _, normalization, windows, record = _prepare(train_window.training_slice, validation_window,
                                                    JepaConfig(max_train_windows=max_train_windows))
    batch = window_tensors(validation_window, normalization)
    features, mask, targets = windows.take(np.arange(min(len(windows), 4)))[:3]
    return dict(normalization_fingerprint=normalization.fingerprint, train_windows=record,
                train_window_shape=list(features.shape), train_target_shape=list(targets.shape),
                train_window_mask_complete=bool(mask.all()),
                validation_tensor_shapes={name: list(getattr(batch, name).shape)
                                          for name in ('features', 'feature_mask', 'targets', 'target_mask')},
                validation_tensors_finite=bool(np.isfinite(batch.features.numpy()).all()))


def pipeline_smoke_from_dataset(dataset, config, plan, *, max_train_windows=20000):
    """Build development windows and train-only normalization with the existing interfaces; no optimizer."""
    from solar_flare_jepa.experiments.config import utc_ns
    from solar_flare_jepa.forecasting.contracts import ForecastSpec
    from solar_flare_jepa.forecasting.splitting import chronological_partitions
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    from solar_flare_jepa.training.normalization import Normalization, training_snapshot
    from .goes_restoration import check_split_authorization
    roles = check_split_authorization(config['splits'], plan)
    spec = ForecastSpec(**config['forecast'])
    partitions = chronological_partitions(dataset, [dict(name=p['name'], start_ns=utc_ns(p['start_utc']),
                                                         end_ns=utc_ns(p['end_utc'])) for p in config['splits']])
    selected = {p.name: p for p in partitions if p.name in DEVELOPMENT_SPLITS}
    windows = {name: build_partition_windows(dataset, spec, partition) for name, partition in selected.items()}
    again = {name: build_partition_windows(dataset, spec, partition) for name, partition in selected.items()}
    training = training_snapshot(windows['train'].training_slice)
    normalization = Normalization.fit(training)
    # Independent recomputation: unique valid raw rows strictly inside the training partition.
    train = selected['train']
    rows = (dataset.starts_ns >= train.start_ns) & (dataset.ends_ns <= train.end_ns)
    independent, widened = [], []
    validation_end = selected['validation'].end_ns
    wide_rows = (dataset.starts_ns >= train.start_ns) & (dataset.ends_ns <= validation_end)
    for k in range(dataset.features.shape[1]):
        logs = np.log10(dataset.features[rows & dataset.feature_mask[:, k], k] / spec.feature_reference[k])
        independent.append((float(logs.mean()), float(logs.std())))
        wide = np.log10(dataset.features[wide_rows & dataset.feature_mask[:, k], k] / spec.feature_reference[k])
        widened.append((float(wide.mean()), float(wide.std())))
    fitted = list(zip(normalization.feature_mean, normalization.feature_scale))
    validation = windows['validation']
    result = dict(
        roles=roles, built_partitions=sorted(windows), test_windows_built='test' in windows,
        dataset=dict(rows=len(dataset.starts_ns), fingerprint=dataset.fingerprint, channels=list(dataset.feature_names),
                     units=list(dataset.feature_units), cadence_seconds=dataset.cadence_seconds),
        spec=spec.as_dict(),
        splits={name: dict(start_ns=p.start_ns, end_ns=p.end_ns, retained_origins=len(windows[name].retained_origins),
                           excluded_origins=len(windows[name].excluded_origins),
                           split_fingerprint=windows[name].split_fingerprint,
                           deterministic=windows[name].split_fingerprint == again[name].split_fingerprint
                           and windows[name].retained_origins == again[name].retained_origins,
                           **_containment(windows[name], p, spec)) for name, p in selected.items()},
        shapes=dict(validation_context=list(np.shape(validation.context.values)),
                    validation_targets=list(np.shape(validation.targets.values)),
                    train_context=list(np.shape(windows['train'].context.values)),
                    raw_training_rows=int(len(training.raw_starts_ns))),
        masks=dict(validation_context_complete=bool(np.asarray(validation.context.mask).all()),
                   validation_targets_complete=bool(np.asarray(validation.targets.mask).all()),
                   train_context_complete=bool(np.asarray(windows['train'].context.mask).all())),
        validation_starts_after_training=bool(np.asarray(validation.context.starts_ns).min() >= train.end_ns),
        normalization=dict(fitting_scope=normalization.as_dict()['fitting_scope'], fingerprint=normalization.fingerprint,
                           feature_mean=list(normalization.feature_mean), feature_scale=list(normalization.feature_scale),
                           feature_counts=list(normalization.feature_counts),
                           equals_independent_train_only=bool(np.allclose(fitted, independent, rtol=0, atol=1e-12)),
                           differs_from_train_plus_validation=bool(not np.allclose(fitted, widened, rtol=0, atol=1e-9))),
        training_fingerprint=training.fingerprint)
    result['v2_preparation'] = _v2_preparation(windows['train'], validation, max_train_windows)
    result['v2_preparation']['normalization_matches'] = (
        result['v2_preparation']['normalization_fingerprint'] == normalization.fingerprint)
    return result


def pipeline_smoke(plan, config_path, root):
    """Load the development data through ``goes_training`` and run ``pipeline_smoke_from_dataset``."""
    from solar_flare_jepa.experiments.config import load_config, read_finite_json
    from .foundation import goes_training
    from .goes_restoration import UnauthorizedSelection
    root = Path(root).resolve()
    config_path = Path(config_path)
    config_path = config_path if config_path.is_absolute() else root / config_path
    dataset = read_finite_json(config_path).get('dataset', {})
    requested = set(dataset.get('manifests', [dataset.get('manifest')]))
    if not requested <= {m['path'] for m in plan['manifests']}:  # decided before any data is read
        raise UnauthorizedSelection('Experiment config requests manifests outside the restoration plan')
    config = load_config(config_path)
    return pipeline_smoke_from_dataset(goes_training(config, root), config, plan)
