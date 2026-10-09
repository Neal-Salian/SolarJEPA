"""Pinned external-only GOES data and unchanged P1 causal test windows.

No TrainingSlice, learned normalization or model selection is exposed here.
Catalog annotations are separate artifacts and never become dataset features.
"""
import hashlib
import json
import stat
from pathlib import Path

import pandas as pd
import xarray as xr

from .foundation import GOES_QUALITY, GOES_TIME, SourceIdentity, validate_goes_files
from .goes_acquisition import _path, verify_history
from ..experiments.config import _object, _reject_constant, utc_ns
from ..forecasting.contracts import (ForecastSpec, TimeSeriesDataset, _canonical_fields,
                                     canonical_json)
from ..forecasting.splitting import TemporalPartition
from ..forecasting.windows import build_partition_windows

FROZEN_MANIFEST = 'data/manifests/goes_p2_july2024.json'
FROZEN_SHA256 = '581a3c4b8cfba6b9b21ed1fdb0b2277e728e9bf329a8da1ddcc0bd49c3cc4b3d'


def _json_snapshot(path, root):
    """Parse exactly the finite JSON bytes whose identity is recorded."""
    path = _path(Path(path).relative_to(root).as_posix(), root)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > 4*1024**2:
        raise ValueError('Expected a bounded regular JSON input')
    data = path.read_bytes()
    after = path.stat()
    fields = ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    if any(getattr(before,key) != getattr(after,key) for key in fields):
        raise ValueError('JSON input changed while being read')
    value = json.loads(data,object_pairs_hook=_object,parse_constant=_reject_constant)
    identity = dict(path=path.relative_to(root).as_posix(),bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest())
    return value, identity


def load_external_dataset(manifest_path, root):
    """Verify source bytes and scientific schema; reject frozen July overlap.

    Returns (TimeSeriesDataset, observed_native_validation_report). The frozen
    ledger is checked by its exact P2 hash; its raw files need not be copied to
    this external workspace. Native processing metadata is retained as evidence,
    without inferring contemporaneous availability from science-file timestamps.
    """
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    if manifest_path.is_absolute():
        try:
            manifest_path = manifest_path.relative_to(root)
        except ValueError as exc:
            raise ValueError('External manifest must stay inside root') from exc
    manifest_path = _path(manifest_path.as_posix(), root)
    frozen_path = _path(FROZEN_MANIFEST, root)
    frozen, frozen_snapshot = _json_snapshot(frozen_path,root)
    if frozen_snapshot['sha256'] != FROZEN_SHA256:
        raise ValueError('Frozen July benchmark manifest identity changed')
    inventory, manifest_snapshot = _json_snapshot(manifest_path,root)
    _, acquisition_snapshot = _json_snapshot(_path(inventory['config_path'],root),root)
    paths = verify_history(manifest_path, root)
    interval = inventory['selected_interval']
    start = pd.Timestamp(interval['start'], tz='UTC')
    end = pd.Timestamp(interval['end_exclusive'], tz='UTC')
    frozen_start = pd.Timestamp(frozen['selected_interval']['start'], tz='UTC')
    frozen_end = pd.Timestamp(frozen['selected_interval']['end_exclusive'], tz='UTC')
    if start < frozen_end and frozen_start < end:
        raise ValueError('External interval overlaps frozen July benchmark raw support')
    if inventory['dataset_id'] == frozen['dataset_id']:
        raise ValueError('External dataset must have a distinct identity')
    frame, report = validate_goes_files(paths, start_utc=start.isoformat(), end_utc=end.isoformat())
    channels = ('xrsa_flux','xrsb_flux')
    identity = SourceIdentity('NOAA GOES-R','GOES-16','EXIS/XRS',channels,('W/m2','W/m2'),
        GOES_TIME,'60 s record-start half-open bins','irradiance',GOES_QUALITY,'none',
        'OBSERVED_NATIVE','external future electron-corrected primary XRS-A and XRS-B flux bins')
    processing = []
    for path in paths:
        with xr.open_dataset(path, decode_times=False, engine='netcdf4') as ds:
            fields = ('id','platform','instrument','instrument_id','processing_level','date_created',
                      'time_coverage_start','time_coverage_end','time_coverage_resolution',
                      'algorithm','algorithm_version','algorithm_date','processing_parameters_file',
                      'input_files_first','input_files_last','input_files_total','git_commit_hash','git_commit_date')
            attrs = {name:ds.attrs.get(name) for name in fields}
            for name,value in attrs.items():
                if hasattr(value,'tolist'):
                    attrs[name] = value.tolist()
            processing.append(attrs)
    metadata = dict(adapter='external_goes16_native_v1',evaluation_only=True,
        source_identity=identity.as_dict(),sources=inventory['files'],
        acquisition_manifest_path=manifest_path.relative_to(root).as_posix(),
        acquisition_manifest_sha256=manifest_snapshot['sha256'],raw_validation=report,
        native_processing=processing,channel_bands_nm={'xrsa_flux':[.05,.4],'xrsb_flux':[.1,.8]},
        frozen_benchmark=dict(path=FROZEN_MANIFEST,sha256=FROZEN_SHA256,dataset_id=frozen['dataset_id'],
            exclusion_start_utc=frozen_start.isoformat(),exclusion_end_utc=frozen_end.isoformat()),
        preprocessing=dict(fit_performed=False,normalization='none',imputation='none'),
        catalog_features='prohibited; separate retrospective label artifacts only',
        actual_operational_delivery='UNKNOWN',
        native_preprocessing_causality='UNKNOWN; reprocessed science files may list adjacent-day inputs',
        operational_benchmark_status='BLOCKED_EXTERNAL_EVIDENCE')
    values = frame[list(channels)].to_numpy(float)
    masks = frame[['xrsa_valid','xrsb_valid']].to_numpy(bool)
    dataset = TimeSeriesDataset(inventory['dataset_id'],'goes_historical',frame.index.asi8,
        pd.DatetimeIndex(frame.time_end).asi8,values,masks,values,masks,channels,channels,
        ('W/m2','W/m2'),('W/m2','W/m2'),60,availability_policy='bin_end_earliest',
        time_policy=GOES_TIME,quality_policy=GOES_QUALITY,metadata_json=canonical_json(metadata))
    from ..experiments.provenance import verify_source_identities
    inputs = [frozen_snapshot,manifest_snapshot,acquisition_snapshot]
    inputs += [{key:row[key] for key in ('path','bytes','sha256')} for row in inventory['files']]
    verify_source_identities(root,inputs)
    return dataset, report


def build_external_windows(dataset, spec):
    """Use one entire external test partition; never construct fitting support."""
    if not isinstance(dataset,TimeSeriesDataset) or not isinstance(spec,ForecastSpec):
        raise ValueError('Expected canonical dataset and forecast spec')
    dataset = TimeSeriesDataset(**_canonical_fields(dataset,TimeSeriesDataset))
    spec = ForecastSpec(**_canonical_fields(spec,ForecastSpec))
    metadata = json.loads(dataset.metadata_json)
    if (metadata.get('evaluation_only') is not True
            or metadata.get('preprocessing',{}).get('fit_performed') is not False):
        raise ValueError('An explicitly external-only dataset is required')
    partition = TemporalPartition('test',int(dataset.starts_ns[0]),int(dataset.ends_ns[-1]))
    result = build_partition_windows(dataset,spec,partition)
    if result.training_slice is not None:
        raise ValueError('External construction must never expose a training slice')
    return result


def validate_external_config(config):
    """Resolve a finite, explicit evaluation-only configuration, with no tuning."""
    cfg = json.loads(canonical_json(config))
    required = {'schema_version','evaluation_id','goes_manifest','catalog_manifest','forecast',
                'catalog_interval','minimum_classes','policy'}
    if (not isinstance(cfg,dict) or set(cfg) != required
            or type(cfg['schema_version']) is not int or cfg['schema_version'] != 1
            or cfg['policy'] != 'external_evaluation_only_no_fitting_or_tuning'
            or not isinstance(cfg['evaluation_id'],str) or not cfg['evaluation_id'].strip()):
        raise ValueError('Unsupported external evaluation-only configuration')
    for key in ('goes_manifest','catalog_manifest'):
        # Validate lexical portability without touching an arbitrary current root.
        from pathlib import PurePosixPath
        value = cfg[key]
        if (not isinstance(value,str) or not value.startswith('data/manifests/')
                or not value.endswith('.json') or '\\' in value or ':' in value
                or '..' in PurePosixPath(value).parts or PurePosixPath(value).as_posix() != value):
            raise ValueError('Manifest identity must be canonical repository-relative JSON')
    try:
        spec = ForecastSpec(**cfg['forecast'])
    except (TypeError, ValueError) as exc:
        raise ValueError('Unsupported forecast configuration') from exc
    if spec.availability_mode != 'retrospective_bin_end':
        raise ValueError('Science archive has no established operational availability')
    bounds = cfg['catalog_interval']
    if not isinstance(bounds,list) or len(bounds) != 2 or utc_ns(bounds[0]) >= utc_ns(bounds[1]):
        raise ValueError('Explicit ordered UTC catalog selection interval required')
    classes = cfg['minimum_classes']
    if (not isinstance(classes,list) or not classes or any(type(value) is not str for value in classes)
            or len(set(classes)) != len(classes)
            or any(value not in ('C1.0','M1.0','X1.0') for value in classes)):
        raise ValueError('Use explicit distinct a priori C1.0, M1.0, X1.0 onset tasks')
    return cfg


def prepare_external_validation(config_path, root, output_dir):
    """Publish immutable preparation artifacts; no predictions or model scores.

    Requires a clean implementation and a matching installed package, following
    the existing P1 publication/source-provenance checks. Run in a newly named
    ignored results directory. Repeated runs use distinct output directories.
    """
    from collections import Counter
    from .flare_catalog import parse_flare_report, verify_catalog
    from ..evaluation.flare_alignment import align_events, label_onsets
    from ..experiments.provenance import atomic_record, code_provenance, verify_source_identities
    from ..forecasting.contracts import fingerprint_payload, logical_array
    root = Path(root).resolve()
    config_path = Path(config_path)
    if config_path.is_absolute():
        config_path = config_path.relative_to(root)
    config_path = _path(config_path.as_posix(),root)
    config_value, config_snapshot = _json_snapshot(config_path,root)
    cfg = validate_external_config(config_value)
    goes_inventory, goes_snapshot = _json_snapshot(_path(cfg['goes_manifest'],root),root)
    catalog, catalog_snapshot = _json_snapshot(_path(cfg['catalog_manifest'],root),root)
    inputs = [config_snapshot,goes_snapshot,catalog_snapshot]
    for inventory in (goes_inventory,catalog):
        _, snapshot = _json_snapshot(_path(inventory['config_path'],root),root)
        inputs.append(snapshot)
    inputs += [{key:row[key] for key in ('path','bytes','sha256')}
               for row in goes_inventory['files']+catalog['resources']]
    provenance = code_provenance(root)
    dataset, native = load_external_dataset(cfg['goes_manifest'],root)
    spec = ForecastSpec(**cfg['forecast'])
    windows = build_external_windows(dataset,spec)
    paths = verify_catalog(cfg['catalog_manifest'],root)
    catalog_file = next(row for row in catalog['resources'] if row['role'] == 'catalog')
    events = parse_flare_report(paths['catalog'],catalog['catalog_id'],catalog_file['sha256'])
    alignment = align_events(events,dataset)
    bounds = tuple(utc_ns(value) for value in cfg['catalog_interval'])
    labels = {threshold:label_onsets(events,dataset,windows.targets.grid,
        minimum_class=threshold,catalog_interval=bounds,
        catalog_provenance=({'catalog_id':catalog['catalog_id'],'sha256':catalog_file['sha256']},))
        for threshold in cfg['minimum_classes']}
    start, end = int(dataset.starts_ns[0]), int(dataset.ends_ns[-1])
    by_start = [event for event in events if start <= event.start_ns < end]
    by_peak = [event for event in events if start <= event.peak_ns < end]
    label_summary = {}
    for threshold,value in labels.items():
        scored = [valid and mature for valid,mature in zip(value['valid_mask'],value['mature_mask'])]
        label_summary[threshold] = dict(definition_id=value['definition_id'],
            candidate_origins=len(scored),valid_mature_origins=sum(scored),
            catalog_positive_origins=sum(value['outcomes']),
            valid_mature_positive_origins=sum(y and good for y,good in zip(value['outcomes'],scored)),
            exclusion_reasons=dict(Counter(reason for row in value['origin_provenance'] for reason in row['reasons'])),
            catalog_completeness=value['catalog_completeness'])
    summary = dict(schema_version=1,status='PARTIALLY_VERIFIED',
        verified_scope='pinned retrospective observations, catalog parsing and deterministic candidate labels',
        evaluation_id=cfg['evaluation_id'],dataset_id=dataset.name,dataset_fingerprint=dataset.fingerprint,
        config_path=config_path.relative_to(root).as_posix(),config_sha256=config_snapshot['sha256'],
        native_validation=native,forecast=spec.as_dict(),spec_fingerprint=spec.fingerprint,
        split_fingerprint=windows.split_fingerprint,partition='external_test_only',
        retained_origins=len(windows.retained_origins),excluded_origins=len(windows.excluded_origins),
        valid_target_cells=int(windows.targets.mask.sum()),
        source_manifest=dict(path=cfg['goes_manifest'],sha256=goes_snapshot['sha256']),
        catalog_manifest=dict(path=cfg['catalog_manifest'],sha256=catalog_snapshot['sha256']),
        catalog_id=catalog['catalog_id'],annual_catalog_records=len(events),
        selected_event_counts=dict(onset=dict(Counter(event.flare_class[0] for event in by_start)),
                                   peak=dict(Counter(event.flare_class[0] for event in by_peak))),
        selected_events_by_source=dict(Counter(event.source for event in by_start)),
        missing_event_ends=sum(event.end_ns is None for event in by_start),
        saturated_events=sum(event.peak_saturated for event in by_start),
        aligned_events=len(alignment),labels=label_summary,fit_performed=False,
        model_predictions='NOT_RUN',model_metrics='NOT_COMPUTED',
        operational_benchmark_status='BLOCKED_EXTERNAL_EVIDENCE',
        physical_flare_completeness='UNKNOWN',event_decision_validation='BLOCKED_IMPLEMENTATION',
        frozen_benchmark=json.loads(dataset.metadata_json)['frozen_benchmark'])
    summary['preparation_fingerprint'] = fingerprint_payload(summary)
    context, target = windows.context, windows.targets
    grid = target.grid
    grid_record = dict(dataset_fingerprint=grid.dataset_fingerprint,spec=spec.as_dict(),
        origin_ids=list(grid.origin_ids),issue_times_ns=logical_array(grid.issue_times_ns),
        starts_ns=logical_array(grid.starts_ns),ends_ns=logical_array(grid.ends_ns))
    contents = {'summary.json':summary,'resolved_config.json':cfg,'provenance.json':provenance,
        'dataset_manifest.json':json.loads(dataset.metadata_json),'window_manifest.json':windows.manifest(),
        'event_alignment.json':alignment,'future_grid.json':grid_record,
        'contexts.json':dict(dataset_fingerprint=context.dataset_fingerprint,spec=spec.as_dict(),
            origin_ids=list(context.origin_ids),issue_times_ns=logical_array(context.issue_times_ns),
            starts_ns=logical_array(context.starts_ns),ends_ns=logical_array(context.ends_ns),
            values=logical_array(context.values),mask=logical_array(context.mask),availability_ns=None),
        'targets.json':dict(grid=grid_record,values=logical_array(target.values),mask=logical_array(target.mask)),
        **{f'onset_labels_{key[0]}.json':value for key,value in labels.items()}}
    verify_source_identities(root,provenance['source']['files'])
    verify_source_identities(root,inputs)
    verify_history(cfg['goes_manifest'],root)
    verify_catalog(cfg['catalog_manifest'],root)
    atomic_record(root,output_dir,contents)
    return summary
