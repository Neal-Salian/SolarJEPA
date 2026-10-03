"""Read the existing GOES reference only; bin end is no delivery-time claim."""
from pathlib import Path

import pandas as pd

from solar_flare_jepa.data.download import sha256_file, verified_manifest_paths
from solar_flare_jepa.data.goes import read_goes
from solar_flare_jepa.data.storage import repository_relative_path
from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset, canonical_json
from .config import read_finite_json, validate_config


TIME_POLICY = ('GOES documented UTC convention neglecting leap seconds; index=bin start, '
               'available at time_end at earliest; operational latency unknown')
QUALITY_POLICY = 'strict_status_zero_and_channel_specific_electron_bits'
REFERENCE_ROLE = 'external_reference_validation_not_aditya'


def goes_reference(config, root):
    """Verify pinned local preparation and expose native XRS-B intervals.

    Legacy absolute source paths are association evidence only; never dereference
    them. An unambiguous filename/hash/size match ties them to verified manifest
    sources. The original artifacts are read only and semantic identity omits
    machine-specific prefixes, sidecar serialization, and Parquet serialization.
    """
    cfg = validate_config(config)
    if cfg['dataset']['kind'] != 'goes_reference':
        raise ValueError('GOES adapter requires goes_reference mode')
    root = Path(root).resolve()
    settings = cfg['dataset']
    manifest = root / repository_relative_path(settings['manifest'], root)
    preparation = read_finite_json(root / repository_relative_path(settings['prepared_config'], root))
    sidecar = read_finite_json(root / repository_relative_path(settings['sidecar'], root))
    expected_preparation = dict(dataset_role=REFERENCE_ROLE, manifest=settings['manifest'],
        processed_path='data/processed/noaa_reference.parquet', results_dir='results/noaa_reference',
        quality_policy=QUALITY_POLICY, cadence_seconds=60, imputation='none', normalization='none')
    if preparation != expected_preparation or type(preparation.get('cadence_seconds')) is not int:
        raise ValueError('Unsupported pinned GOES preparation configuration')
    if (not isinstance(sidecar, dict) or sidecar.get('config') != preparation
            or sidecar.get('role') != REFERENCE_ROLE or sidecar.get('time_policy') != TIME_POLICY
            or sidecar.get('units') != {'flux':'W/m2', 'log10_flux':'log10(F / (1 W/m2))', 'dlog10_dt':'s^-1'}):
        raise ValueError('GOES preparation sidecar policy/configuration mismatch')
    manifest_hash = sha256_file(manifest)
    if sidecar.get('manifest_sha256') != manifest_hash:
        raise ValueError('GOES sidecar manifest SHA-256 mismatch')
    paths = verified_manifest_paths(manifest, root, 'avg1m')
    sources = [dict(id=repository_relative_path(path, root), sha256=sha256_file(path),
                    bytes=path.stat().st_size) for path in paths]
    recorded = sidecar.get('sources')
    if not isinstance(recorded, list) or len(recorded) != len(sources):
        raise ValueError('GOES sidecar raw source set mismatch')
    matched = set()
    for source in recorded:
        if (not isinstance(source, dict) or set(source) != {'path', 'sha256', 'bytes'}
                or not isinstance(source['path'], str) or type(source['bytes']) is not int):
            raise ValueError('Malformed GOES sidecar raw source')
        historic = Path(source['path'])
        candidates = [s for s in sources if Path(s['id']).name == historic.name
                      and s['sha256'] == source['sha256'] and s['bytes'] == source['bytes']
                      and (historic.is_absolute() or source['path'] == s['id'])]
        if len(candidates) != 1 or candidates[0]['id'] in matched:
            raise ValueError('GOES sidecar raw source identity mismatch or ambiguity')
        matched.add(candidates[0]['id'])
    processed = root / repository_relative_path(preparation['processed_path'], root)
    if sidecar.get('processed_sha256') != sha256_file(processed):
        raise ValueError('GOES processed Parquet SHA-256 mismatch')
    frame = pd.read_parquet(processed)
    if type(sidecar.get('rows')) is not int or sidecar['rows'] != len(frame):
        raise ValueError('GOES sidecar prepared row count mismatch')
    # Re-execute documented time/unit/quality checks and compare ALL prepared
    # content, so even a newly declared Parquet hash cannot hide stale processing.
    fresh = read_goes(paths)
    try:
        pd.testing.assert_frame_equal(frame, fresh, check_exact=True, check_freq=False)
    except AssertionError as exc:
        raise ValueError('Prepared GOES content differs from verified raw preparation') from exc
    spec = ForecastSpec(**cfg['forecast'])
    values = frame[['xrsb_flux']].to_numpy(dtype=float)
    mask = frame[['xrsb_valid']].to_numpy(dtype=bool)
    metadata = dict(adapter='p1_existing_goes_xrsb_v1', sources=sources,
                    manifest_sha256=manifest_hash,
                    interpretation='reference_validation_not_aditya', operational_latency='UNKNOWN',
                    imputation='none', normalization='none')
    return TimeSeriesDataset('p1_goes_xrsb_reference', 'goes_reference', frame.index.asi8,
        pd.DatetimeIndex(frame['time_end']).asi8, values, mask, values, mask,
        spec.feature_names, spec.target_names, spec.feature_units, spec.target_units,
        60, availability_policy='bin_end_earliest', time_policy=sidecar['time_policy'],
        quality_policy=preparation['quality_policy'], metadata_json=canonical_json(metadata))
