"""Pinned NOAA NCEI science flare reports, independent of model predictions.

Calendar timestamps in this product are documented UTC minute labels. Missing
ends remain unknown. A successfully parsed catalog is not proof of completeness.
"""
import csv
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import tempfile

from .download import sha256_file
from .goes_acquisition import _json, _path, _utc, open_history_url


FIELDS = tuple(('time,start_time,end_time,flare_id,xrsb_irrad,flare_class,xrsb_irrad_source,'
                'background_irrad,integrated_irrad_peak,integrated_irrad_end,'
                'flare_loc_swpc_hgs_lon,flare_loc_swpc_hgs_lat,flare_loc_swpc_source,'
                'flare_loc_xrs_hgs_lon,flare_loc_xrs_hgs_lat,flare_loc_xrs_hpc_x,'
                'flare_loc_xrs_hpc_y,flare_loc_xrs_source,sequential_flare_num,'
                'event_id_swpc,peak_saturated,active_region').split(','))
BASE = ('https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/'
        'goes/multi/l2/data/xrsf-l2-flrpt_science/csv/')
NAMES = {'catalog': 'sci_xrsf-l2-flrpt_geo_y2025_v1-0-1.csv',
         'metadata': 'sci_xrsf-l2-flrpt_geo_metadata.json'}
MAX_BYTES = 1024**2


@dataclass(frozen=True)
class FlareEvent:
    catalog_id: str
    catalog_sha256: str
    event_id: str
    start_ns: int
    peak_ns: int
    end_ns: int | None
    flare_class: str
    peak_flux: float
    source: str
    sequential_number: int
    peak_saturated: bool
    original_row: int
    flags: tuple[str, ...]


def class_threshold(flare_class: str) -> float:
    """Magnitude represented by NOAA's class string in W/m²; never relabel flux."""
    if not isinstance(flare_class, str) or not re.fullmatch(r'[ABCMX][1-9][0-9]*\.[0-9]', flare_class):
        raise ValueError('Malformed NOAA flare classification')
    magnitude = float(flare_class[1:])
    if not math.isfinite(magnitude):
        raise ValueError('Flare class magnitude must be finite')
    if flare_class[0] != 'X' and magnitude >= 10:
        raise ValueError('Non-X class magnitude must be less than ten')
    return magnitude * {'A': 1e-8, 'B': 1e-7, 'C': 1e-6, 'M': 1e-5, 'X': 1e-4}[flare_class[0]]


def _timestamp(value: str) -> int:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:00', value):
        raise ValueError('Flare timestamps must be explicit documented UTC minute labels')
    instant = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    delta = instant - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 10**9


def parse_flare_report(path, catalog_id: str, catalog_sha256: str) -> tuple[FlareEvent, ...]:
    """Parse a verified full CSV; preserve class/source and missing end times.

    Exact duplicate rows are flagged and collapsed. Conflicting reuse of an
    event identifier fails closed. Rows are returned in peak/start/ID order;
    ``original_row`` is the one-based physical CSV row, including the header.
    """
    if not isinstance(catalog_id, str) or not catalog_id.strip():
        raise ValueError('A catalog identity is required')
    if not isinstance(catalog_sha256, str) or not re.fullmatch('[0-9a-f]{64}', catalog_sha256):
        raise ValueError('A valid SHA-256 catalog identity is required')
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Catalog exceeds the bounded annual-file size')
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != catalog_sha256:
        raise ValueError('SHA-256 mismatch for catalog label provenance')
    reader = csv.DictReader(io.StringIO(content.decode('utf-8'), newline=''))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError('Unsupported or ambiguous flare-report header')
    events, original = {}, {}
    for row in reader:
        line = reader.line_num
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Wrong CSV field count')
            event_id = row['flare_id']
            if event_id in original:
                if row != original[event_id]:
                    raise ValueError(f'Conflicting catalog event ID: {event_id}')
                event = events[event_id]
                events[event_id] = replace(event, flags=tuple(sorted(set(event.flags + ('exact_duplicate',)))))
                continue
            start, peak = _timestamp(row['start_time']), _timestamp(row['time'])
            end = _timestamp(row['end_time']) if row['end_time'] else None
            if peak < start or (end is not None and end < peak):
                raise ValueError('Event timestamps are not chronologically ordered')
            expected_id = row['start_time'].replace('-', '').replace(' ', '').replace(':', '')[:12]
            if event_id != expected_id:
                raise ValueError('Flare ID does not match its documented UTC start')
            class_threshold(row['flare_class'])
            flux = float(row['xrsb_irrad'])
            if not math.isfinite(flux) or flux <= 0:
                raise ValueError('Flare peak irradiance must be finite and positive')
            source = row['xrsb_irrad_source']
            if not re.fullmatch(r'GOES-([1-9]|1[0-9])', source):
                raise ValueError('Unknown irradiance source spacecraft')
            sequence = row['sequential_flare_num']
            if not re.fullmatch(r'[1-9][0-9]*', sequence):
                raise ValueError('Sequence number must be a positive integer')
            if row['peak_saturated'] not in {'0', '1'}:
                raise ValueError('Unknown peak saturation flag')
            saturated = row['peak_saturated'] == '1'
            flags = tuple(name for name, condition in [('missing_end', end is None),
                          ('sequential_flare', int(sequence) > 1), ('peak_saturated', saturated)] if condition)
            events[event_id] = FlareEvent(catalog_id, catalog_sha256, event_id, start, peak, end,
                                         row['flare_class'], flux, source, int(sequence), saturated, line, flags)
            original[event_id] = row
        except (ValueError, TypeError) as exc:
            raise ValueError(f'Invalid flare-report row {line}: {exc}') from exc
    return tuple(sorted(events.values(), key=lambda event: (event.peak_ns, event.start_ns, event.event_id)))


def _config(config_path, root):
    path = Path(config_path)
    path = path if path.is_absolute() else root / path
    try:
        relative = path.relative_to(root).as_posix()
        path = _path(relative, root)
        spec = _json(path)
        if (spec['schema_version'] != 1 or type(spec['schema_version']) is not int
                or spec['product'] != 'xrsf-l2-flrpt_science' or spec['version'] != '1-0-1'
                or type(spec['year']) is not int or spec['year'] != 2025
                or spec['catalog_id'] != 'noaa-ncei-science-flrpt-2025-v1-0-1'):
            raise ValueError('Unsupported official flare-report identity/version')
        timeout = spec['timeout_seconds']
        if type(timeout) not in {float, int} or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ValueError('Catalog timeout must be bounded by 30 seconds')
        resources = spec['resources']
        if not isinstance(resources, list) or [entry['role'] for entry in resources] != ['catalog', 'metadata']:
            raise ValueError('Catalog and metadata resources must each occur exactly once')
        for entry in resources:
            name = NAMES[entry['role']]
            if (entry['url'] != BASE + name or
                    entry['path'] != 'data/raw/external/goes_flare_catalog_2025/' + name):
                raise ValueError('Official catalog URL or raw path identity conflict')
            _path(entry['path'], root)
            if (type(entry['max_bytes']) is not int or not 0 < entry['max_bytes'] <= MAX_BYTES
                    or type(entry['bytes']) is not int or not 0 < entry['bytes'] <= entry['max_bytes']
                    or not isinstance(entry['sha256'], str)
                    or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])):
                raise ValueError('Every resource requires bounded bytes and a pinned SHA-256')
        manifest = _path(spec['manifest_path'], root)
        if spec['manifest_path'] != 'data/manifests/flare_catalog_2025.json':
            raise ValueError('Unexpected flare-report manifest location')
        return spec, relative, sha256_file(path), manifest
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed flare-report acquisition config') from exc


def _check(path, entry):
    if (not path.is_file() or path.stat().st_size != entry['bytes']
            or sha256_file(path) != entry['sha256']):
        raise ValueError('Pinned catalog resource byte size or SHA-256 differs; never overwrite')


def _validate_content(paths, spec):
    metadata = _json(paths['metadata'])
    try:
        attributes = metadata['global_attributes']
        if (attributes['flrpt_algorithm_version'] != spec['version']
                or attributes['title'] != 'L2 XRS flare report'
                or attributes['time_coverage_resolution'] != 'PT1M'
                or metadata['variable_attributes']['xrsb_irrad']['units'] != 'W/m2'
                or not {'time', 'start_time', 'end_time', 'flare_class', 'xrsb_irrad_source'}
                       .issubset(metadata['variable_attributes'])):
            raise ValueError('Unsupported NOAA catalog metadata')
    except (KeyError, TypeError) as exc:
        raise ValueError('Malformed NOAA catalog metadata') from exc
    events = parse_flare_report(paths['catalog'], spec['catalog_id'], spec['resources'][0]['sha256'])
    lower = _timestamp(f"{spec['year']}-01-01 00:00:00")
    upper = _timestamp(f"{spec['year'] + 1}-01-01 00:00:00")
    if any(not lower <= event.peak_ns < upper for event in events):
        raise ValueError('Catalog event peak lies outside its named aggregation year')
    return events


def verify_catalog(manifest_path, root) -> dict[str, Path]:
    """Verify config, immutable ledger, bytes and semantics; return resource paths."""
    root = Path(root).resolve()
    path = Path(manifest_path)
    path = path if path.is_absolute() else root / path
    ledger = _json(_path(path.relative_to(root).as_posix(), root))
    try:
        spec, relative, digest, expected_path = _config(ledger['config_path'], root)
        if (path != expected_path or ledger['config_path'] != relative or ledger['config_sha256'] != digest
                or ledger['catalog_id'] != spec['catalog_id'] or ledger['complete'] is not True
                or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
                or ledger['scientific_completeness'] != 'UNKNOWN'
                or ledger['status'] != 'VERIFIED_RAW_IDENTITIES_AND_PARSE'
                or type(ledger['event_count']) is not int or ledger['product'] != spec['product']
                or ledger['version'] != spec['version'] or ledger['year'] != spec['year']
                or len(ledger['resources']) != 2):
            raise ValueError('Catalog ledger/config identity mismatch')
        paths = {}
        for entry, record in zip(spec['resources'], ledger['resources']):
            if any(record[key] != value for key, value in entry.items()):
                raise ValueError('Catalog ledger resource identity conflict')
            _utc(record['registered_utc'])
            acquired = record['acquired_utc']
            if acquired is not None:
                if _utc(acquired) > _utc(record['registered_utc']):
                    raise ValueError('Catalog acquisition follows registration')
                if record['lineage'] != 'download_official_noaa':
                    raise ValueError('Catalog acquisition lineage conflict')
            elif record['lineage'] != 'existing_pinned_bytes_acquisition_time_unknown':
                raise ValueError('Unknown existing catalog acquisition lineage')
            local = _path(record['path'], root)
            _check(local, entry)
            paths[entry['role']] = local
        events = _validate_content(paths, spec)
        if ledger['event_count'] != len(events) or ledger['total_bytes'] != sum(e['bytes'] for e in spec['resources']):
            raise ValueError('Catalog ledger event/byte count conflict')
        return paths
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed flare-report ledger') from exc


def acquire_catalog(config_path, root) -> dict:
    """Acquire exactly two pinned public resources, without redirects/replacement.

    Existing files must match the config. Existing ledgers are verified and
    returned unchanged. A changed remote snapshot fails rather than repinning.
    """
    root = Path(root).resolve()
    spec, relative, digest, manifest = _config(config_path, root)
    if manifest.exists():
        verify_catalog(manifest, root)
        return _json(manifest)
    records, paths = [], {}
    for entry in spec['resources']:
        path = _path(entry['path'], root)
        acquired = None
        lineage = 'existing_pinned_bytes_acquisition_time_unknown'
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    with open_history_url(entry['url'], spec['timeout_seconds']) as response:
                        length = response.headers.get('Content-Length')
                        if length is not None and int(length) != entry['bytes']:
                            raise ValueError('Remote catalog Content-Length differs from pinned size')
                        count = 0
                        while chunk := response.read(65536):
                            count += len(chunk)
                            if count > entry['max_bytes'] or count > entry['bytes']:
                                raise ValueError('Remote catalog exceeds pinned byte budget')
                            stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                _check(temporary, entry)
                os.link(temporary, path)
                acquired = datetime.now(timezone.utc).isoformat()
                lineage = 'download_official_noaa'
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        _check(path, entry)
        paths[entry['role']] = path
        records.append(dict(entry, acquired_utc=acquired, registered_utc=datetime.now(timezone.utc).isoformat(),
                            lineage=lineage))
    events = _validate_content(paths, spec)
    ledger = dict(schema_version=1, catalog_id=spec['catalog_id'], product=spec['product'],
                  version=spec['version'], year=spec['year'], config_path=relative, config_sha256=digest,
                  complete=True, resources=records, total_bytes=sum(e['bytes'] for e in records),
                  event_count=len(events), status='VERIFIED_RAW_IDENTITIES_AND_PARSE',
                  scientific_completeness='UNKNOWN',
                  metadata_caveat='Unversioned metadata snapshot is pinned by bytes; later remote changes fail verification.')
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(ledger, indent=2, allow_nan=False) + '\n')
    verify_catalog(manifest, root)
    return ledger
