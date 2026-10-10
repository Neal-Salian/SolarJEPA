"""Explicit, bounded NOAA GOES-16 science history acquisition.

The inventory pins local bytes, not a NOAA-issued checksum or science validation.
Writers must be serialized; raw files are installed without replacement.
"""
from datetime import date, datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import ssl
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request, build_opener

import certifi

from .download import NoRedirect, sha256_file


PLATFORM = 'GOES-16'
PRODUCT = 'xrsf-l2-avg1m_science'
VERSION = '2-2-1'
BASE = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/'
MAX_FILE_BYTES = 1024**2
MAX_TOTAL_BYTES = 31 * MAX_FILE_BYTES


def open_history_url(url: str, timeout: float):
    """Open a pinned public URL with TLS verification and no redirects."""
    context = ssl.create_default_context(cafile=certifi.where())
    return build_opener(NoRedirect, HTTPSHandler(context=context)).open(
        Request(url, headers={'User-Agent': 'solar-flare-jepa-research/0.1'}), timeout=timeout)


def _json(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    value = json.loads(path.read_text(), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    return value


def _path(relative: str, root: Path) -> Path:
    if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative
            or '\x00' in relative or PurePosixPath(relative).is_absolute()
            or '..' in PurePosixPath(relative).parts or PurePosixPath(relative).as_posix() != relative):
        raise ValueError('Path must be a canonical repository-relative path')
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError('Path escapes repository root')
    current = root
    for part in PurePosixPath(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError('Symlink paths are not supported for acquisition identities')
    return target


def _date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError('Nominal dates must use YYYY-MM-DD')
    return parsed


def _pin(entry, required=False):
    digest, size = entry.get('sha256'), entry.get('bytes')
    if digest is None and size is None and not required:
        return
    if (not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)
            or type(size) is not int or not 0 < size <= entry.get('max_bytes', MAX_FILE_BYTES)):
        raise ValueError('A pinned identity requires a valid SHA-256 and bounded byte size')


def _utc(value):
    if not isinstance(value, str) or 'T' not in value:
        raise ValueError('Provenance timestamp must explicitly use UTC')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.utcoffset() != timedelta(0):
        raise ValueError('Provenance timestamp must explicitly use UTC')
    return parsed


def _canonical(day: date):
    name = f'sci_xrsf-l2-avg1m_g16_d{day:%Y%m%d}_v{VERSION}.nc'
    return dict(nominal_date=day.isoformat(),
                url=f'{BASE}{PRODUCT}/{day:%Y/%m}/{name}',
                path=f'data/raw/noaa/history/goes16/{PRODUCT}/v{VERSION}/{day:%Y/%m}/{name}')


def _config(config_path, root):
    config_path = Path(config_path)
    config_path = config_path if config_path.is_absolute() else root / config_path
    try:
        relative = config_path.relative_to(root).as_posix()
        config_path = _path(relative, root)
        spec = _json(config_path)
        if (type(spec['schema_version']) is not int or spec['schema_version'] != 1 or spec['platform'] != PLATFORM
                or spec['product'] != PRODUCT or spec['version'] != VERSION
                or not isinstance(spec['dataset_id'], str) or not spec['dataset_id']):
            raise ValueError('Unsupported historical source identity')
        interval = spec['selected_interval']
        start, end = _date(interval['start']), _date(interval['end_exclusive'])
        count = (end - start).days
        if not 0 < count <= 31 or not isinstance(interval['basis'], str) or not interval['basis']:
            raise ValueError('Select an explicit a priori interval of at most 31 nominal dates')
        files = spec['files']
        if not isinstance(files, list) or len(files) != count:
            raise ValueError('Selection must contain every nominal date exactly once')
        for i, entry in enumerate(files):
            identity = _canonical(start + timedelta(days=i))
            if any(entry[key] != value for key, value in identity.items()):
                raise ValueError('Official URL, path, nominal date, platform or version conflict')
            _path(entry['path'], root)
            if type(entry['max_bytes']) is not int or not 0 < entry['max_bytes'] <= MAX_FILE_BYTES:
                raise ValueError('Per-file cap must be a positive integer <=1 MiB')
            _pin(entry)
            if 'reuse' in entry:
                reuse = entry['reuse']
                if reuse['path'] != 'data/raw/noaa/' + Path(identity['path']).name:
                    raise ValueError('Reference lineage must retain the matching original filename')
                _path(reuse['path'], root)
                _pin(reuse, required=True)
                if reuse.get('checked_utc') is not None:
                    _utc(reuse['checked_utc'])
        budget = spec['max_total_bytes']
        if (type(budget) is not int or not 0 < budget <= MAX_TOTAL_BYTES
                or sum(e['max_bytes'] for e in files) > budget):
            raise ValueError('Selected per-file caps exceed the total budget (maximum 31 MiB)')
        for key, ceiling in [('timeout_seconds', 30), ('retry_delay_seconds', 5)]:
            value = spec[key]
            if (type(value) not in {int, float} or not math.isfinite(value)
                    or not 0 <= value <= ceiling or (key == 'timeout_seconds' and value == 0)):
                raise ValueError('Timeout/retry delay outside bounded acquisition limits')
        if type(spec['max_attempts']) is not int or not 1 <= spec['max_attempts'] <= 3:
            raise ValueError('Acquisition allows at most three attempts per file')
        manifest = _path(spec['manifest_path'], root)
        if not spec['manifest_path'].startswith('data/manifests/') or manifest.suffix != '.json':
            raise ValueError('History ledger must be JSON under data/manifests')
        return spec, relative, sha256_file(config_path), manifest
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed acquisition config') from exc


def _base(spec, relative, digest):
    return dict(schema_version=1, dataset_id=spec['dataset_id'], platform=PLATFORM,
                product=PRODUCT, version=VERSION, selected_interval=spec['selected_interval'],
                config_path=relative, config_sha256=digest, max_total_bytes=spec['max_total_bytes'],
                selected_file_count=len(spec['files']))


def _ledger(value, spec, relative, digest):
    try:
        if (type(value.get('schema_version')) is not int
                or any(value.get(key) != expected for key, expected in _base(spec, relative, digest).items())):
            raise ValueError('Ledger config/source identity mismatch')
        records = value['files']
        if not isinstance(records, list) or type(value['complete']) is not bool:
            raise ValueError('Malformed completion inventory')
        selected = {entry['path']: entry for entry in spec['files']}
        seen = set()
        for row in records:
            entry = selected.get(row['path'])
            if entry is None or row['path'] in seen:
                raise ValueError('Unselected or duplicate inventory identity')
            seen.add(row['path'])
            for key in ['path', 'url', 'nominal_date', 'max_bytes']:
                if row[key] != entry[key]:
                    raise ValueError('Inventory nominal/source identity conflict')
            if row['platform'] != PLATFORM or row['product'] != PRODUCT or row['version'] != VERSION:
                raise ValueError('Inventory satellite/product/version conflict')
            _pin(row, required=True)
            if entry.get('sha256') is not None and (row['sha256'], row['bytes']) != (entry['sha256'], entry['bytes']):
                raise ValueError('Inventory/config pinned identity conflict')
            registered = _utc(row['registered_utc'])
            if row['acquired_utc'] is not None and _utc(row['acquired_utc']) > registered:
                raise ValueError('Acquisition time cannot follow registration')
            lineage = row['lineage']
            if lineage == dict(method='copy_pinned_reference', parent=entry.get('reuse')):
                if row['acquired_utc'] is not None or row['sha256'] != entry['reuse']['sha256'] or row['bytes'] != entry['reuse']['bytes']:
                    raise ValueError('Reference lineage identity conflict')
            elif lineage == {'method': 'download_official_noaa'}:
                if row['acquired_utc'] is None:
                    raise ValueError('Observed download acquisition time must be retained')
            elif lineage == {'method': 'existing_config_pinned'}:
                if row['acquired_utc'] is not None:
                    raise ValueError('Pinned local bytes do not establish an acquisition time')
            else:
                raise ValueError('Unknown acquisition lineage')
        if records != sorted(records, key=lambda row: row['nominal_date']):
            raise ValueError('Inventory must preserve nominal chronological order')
        if (value['complete'] != (len(records) == len(selected))
                or value['total_bytes'] != sum(row['bytes'] for row in records)
                or value['total_bytes'] > spec['max_total_bytes']):
            raise ValueError('Inconsistent complete inventory or total budget')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed history ledger') from exc


def _check(path, entry):
    if not path.is_file():
        raise ValueError(f'Pinned raw file is unavailable: {path.name}')
    before = path.stat()
    size = before.st_size
    if not 0 < size <= entry['max_bytes'] or (entry.get('bytes') is not None and size != entry['bytes']):
        raise ValueError('Raw byte size differs from pinned identity or cap')
    with path.open('rb') as stream:
        magic = stream.read(8)
    if not (magic.startswith((b'CDF\x01', b'CDF\x02', b'CDF\x05')) or magic == b'\x89HDF\r\n\x1a\n'):
        raise ValueError('Raw response is not NetCDF/HDF5')
    digest = sha256_file(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('Raw file changed during integrity verification')
    if entry.get('sha256') is not None and digest != entry['sha256']:
        raise ValueError('SHA-256 mismatch; immutable raw files are never replaced')
    return size, digest


def _write_ledger(path, value):
    serialized = json.dumps(value, indent=2, allow_nan=False) + '\n'
    if path.exists() and path.read_text() == serialized:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _new_stats(stats):
    """Initialise an optional caller-owned counter mapping (observability only)."""
    if stats is not None:
        for key, value in dict(attempts=0, retries=0, downloaded_files=0, downloaded_bytes=0,
                               reused_reference_files=0, failures=[]).items():
            stats.setdefault(key, value)
    return stats


def _download(entry, temporary, spec, stats=None):
    for attempt in range(spec['max_attempts']):
        if stats is not None:
            stats['attempts'] += 1
            stats['retries'] += attempt > 0
        try:
            with open_history_url(entry['url'], spec['timeout_seconds']) as response:
                declared = response.headers.get('Content-Length')
                expected = int(declared) if declared is not None else None
                if expected is not None and not 0 < expected <= entry['max_bytes']:
                    raise ValueError('Content-Length exceeds cap or is invalid')
                total = 0
                with temporary.open('wb') as stream:
                    while chunk := response.read(65536):
                        total += len(chunk)
                        if total > entry['max_bytes']:
                            raise ValueError('Stream exceeds per-file cap')
                        stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                if expected is not None and total != expected:
                    raise ValueError('Truncated response: Content-Length mismatch')
            return _check(temporary, entry)
        except (URLError, TimeoutError, ConnectionError, OSError, ValueError) as error:
            if stats is not None:
                stats['failures'].append(dict(url=entry['url'], attempt=attempt + 1,
                                              error=f'{type(error).__name__}: {error}'))
            if isinstance(error, ValueError):
                raise
            if isinstance(error, HTTPError) and error.code not in {408, 429, 500, 502, 503, 504}:
                raise
            if attempt + 1 == spec['max_attempts']:
                raise
            time.sleep(spec['retry_delay_seconds'])
    raise RuntimeError('Unreachable bounded download state')


def acquire_history(config_path: Path, root: Path, *, stats: dict | None = None) -> dict:
    """Acquire only explicit daily flux files; resume solely from pinned identities.

    ``stats``, when supplied, receives attempt/retry/byte/failure counters; it never
    changes acquisition behaviour.
    """
    root = Path(root).resolve()
    _new_stats(stats)
    spec, relative, digest, output = _config(config_path, root)
    inventory = (_json(output) if output.exists() else
                 dict(_base(spec, relative, digest), complete=False, total_bytes=0, files=[]))
    _ledger(inventory, spec, relative, digest)
    records = {row['path']: row for row in inventory['files']}
    # Fail on all existing identity defects before requesting any missing date.
    for entry in spec['files']:
        target = _path(entry['path'], root)
        if target.exists():
            pinned = records.get(entry['path'], entry)
            _pin(pinned, required=True)
            _check(target, pinned)
    for entry in spec['files']:
        target = _path(entry['path'], root)
        previous = records.get(entry['path'])
        if target.exists() and previous is not None:
            continue
        expected = dict(entry)
        if previous is not None:
            expected.update(bytes=previous['bytes'], sha256=previous['sha256'])
        temporary = None
        acquired = None
        lineage = dict(method='existing_config_pinned')
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                size, checksum = _check(target, expected)
            else:
                with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.part', delete=False) as stream:
                    temporary = Path(stream.name)
                reuse = entry.get('reuse')
                original = _path(reuse['path'], root) if reuse is not None else None
                if original is not None and original.exists():
                    size, checksum = _check(original, dict(reuse, max_bytes=entry['max_bytes']))
                    shutil.copyfile(original, temporary)
                    _check(temporary, dict(expected, bytes=size, sha256=checksum))
                    lineage = dict(method='copy_pinned_reference', parent=reuse)
                    if stats is not None:
                        stats['reused_reference_files'] += 1
                else:
                    size, checksum = _download(expected, temporary, spec, stats)
                    acquired = datetime.now(timezone.utc).isoformat()
                    if stats is not None:
                        stats['downloaded_files'] += 1
                        stats['downloaded_bytes'] += size
                    lineage = dict(method='download_official_noaa')
                # Atomic no-replace publication; copies never alias reference inodes.
                target.hardlink_to(temporary)
            if previous is None:
                records[entry['path']] = dict(
                    **{key: entry[key] for key in ['path', 'url', 'nominal_date', 'max_bytes']},
                    platform=PLATFORM, product=PRODUCT, version=VERSION, bytes=size, sha256=checksum,
                    acquired_utc=acquired, registered_utc=datetime.now(timezone.utc).isoformat(), lineage=lineage)
            inventory['files'] = sorted(records.values(), key=lambda row: row['nominal_date'])
            inventory['total_bytes'] = sum(row['bytes'] for row in inventory['files'])
            inventory['complete'] = len(records) == len(spec['files'])
            _ledger(inventory, spec, relative, digest)
            _write_ledger(output, inventory)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return inventory


def verify_history(manifest_path: Path, root: Path) -> list[Path]:
    """Recheck a complete pinned flux-only inventory without mutation or network."""
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    manifest_path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        manifest_path = _path(manifest_path.relative_to(root).as_posix(), root)
        inventory = _json(manifest_path)
        spec, relative, digest, output = _config(inventory['config_path'], root)
        if manifest_path != output:
            raise ValueError('Manifest location differs from pinned config')
        _ledger(inventory, spec, relative, digest)
        if inventory['complete'] is not True:
            raise ValueError('Historical flux inventory is not complete')
        paths = []
        for row in inventory['files']:
            target = _path(row['path'], root)
            _check(target, row)
            paths.append(target)
        return paths
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed historical inventory') from exc
