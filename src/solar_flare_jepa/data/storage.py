"""Local immutable archive registration, not extraction or scientific validation."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from urllib.parse import urlsplit
import zipfile

from .download import sha256_file


ROLE = 'initial_ingestion_validation_sample_not_training_dataset'
PORTAL = 'https://pradan.issdc.gov.in/al1/'
ARCHIVE_NAME = re.compile(r'AL1_SLX_(L[1-9][0-9]*)_([0-9]{8})_(v[0-9]+(?:\.[0-9]+)*)\.zip', re.IGNORECASE)


def repository_relative_path(path: Path, root: Path) -> str:
    """Resolve a local path and reject escape; serialize without a host prefix."""
    root = Path(root).resolve()
    path = Path(path)
    target = (path if path.is_absolute() else root / path).resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError('Path must remain inside the repository root') from exc


def _identity(filename):
    match = ARCHIVE_NAME.fullmatch(filename)
    if match is None:
        raise ValueError('Unsupported SoLEXS archive filename; review its product naming')
    level, date, version = match.groups()
    day = datetime.strptime(date, '%Y%m%d').date()
    level, version = level.upper(), version.lower()
    path = f'data/raw/aditya/solexs/{level.lower()}/{version}/archives/{day:%Y/%m}/{filename}'
    return dict(path=path, original_filename=filename, mission='Aditya-L1', instrument='SoLEXS',
                processing_level=level, product_version=version, nominal_observation_date=day.isoformat())


def _utc(value):
    if not isinstance(value, str) or 'T' not in value:
        raise ValueError('Timestamp must include a UTC time and timezone')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError('Timestamp must explicitly use UTC')
    return parsed.isoformat()


def _source(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.netloc not in {'pradan.issdc.gov.in', 'pradan1.issdc.gov.in'}
            or parts.path != '/al1/' or parts.query or parts.fragment):
        raise ValueError('Use a credential-free official PRADAN portal URL')
    return dict(portal='ISRO PRADAN', url=url, acquisition_method='manual', evidence='DOCUMENTED',
                statement='User-reported official-portal acquisition; portal authenticity not independently checked.')


def _safe_member(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
            or '\x00' in name):
        raise ValueError('Unsafe archive member name; no extraction was performed')


def _archive_listing(path):
    """Read central-directory declarations only; never open/decompress members."""
    members = []
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                _safe_member(info.filename)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError('Symbolic-link archive member is unsupported')
                members.append(dict(path=info.filename, compressed_bytes=info.compress_size,
                                    uncompressed_bytes=info.file_size, crc32=f'{info.CRC:08x}',
                                    is_directory=info.is_dir()))
    except zipfile.BadZipFile as exc:
        raise ValueError('Invalid ZIP central directory') from exc
    if not members or len({m['path'] for m in members}) != len(members):
        raise ValueError('Empty or duplicate archive members')
    return dict(member_count=len(members), file_count=sum(not m['is_directory'] for m in members),
                declared_uncompressed_bytes=sum(m['uncompressed_bytes'] for m in members),
                member_payloads_read=False, member_crc_verified=False, members=members)


def _missing(dates):
    records = []
    for value in sorted(set(dates)):
        if datetime.strptime(value, '%Y-%m-%d').date().isoformat() != value:
            raise ValueError('Missing coverage date must use YYYY-MM-DD')
        records.append(dict(instrument='SoLEXS', nominal_observation_date=value,
                            status='missing_from_obtained_collection', evidence='DOCUMENTED',
                            statement='User reports this date missing from the obtained collection; not a mission-wide availability claim.'))
    return records


def _evidence(acquired):
    return dict(mission='DOCUMENTED', instrument='DOCUMENTED', processing_level='INFERRED',
                product_version='INFERRED', nominal_observation_date='INFERRED',
                original_filename='OBSERVED', bytes='OBSERVED', sha256='OBSERVED',
                detector='UNKNOWN', observed_coverage='UNKNOWN',
                acquired_utc='UNKNOWN' if acquired is None else 'DOCUMENTED',
                registered_utc='OBSERVED', archive='OBSERVED')


def validate_inventory(inventory: dict) -> None:
    """Check metadata consistency without claiming raw/member/science validity."""
    try:
        if inventory['schema_version'] != 1 or inventory['dataset_role'] != ROLE:
            raise ValueError('Unsupported inventory schema or dataset role')
        records, missing = inventory['files'], inventory['missing_coverage']
        if not isinstance(records, list) or not isinstance(missing, list):
            raise ValueError('Inventory collections must be lists')
        paths = []
        for record in records:
            identity = _identity(record['original_filename'])
            if any(record[key] != value for key, value in identity.items()):
                raise ValueError('Archive identity conflicts with canonical path/filename')
            paths.append(record['path'])
            if (not isinstance(record['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', record['sha256'])
                    or type(record['bytes']) is not int or record['bytes'] <= 0):
                raise ValueError('Invalid archive hash or byte size')
            if record['source'] != _source(record['source']['url']):
                raise ValueError('Inconsistent source provenance')
            _utc(record['registered_utc'])
            if record['acquired_utc'] is not None:
                _utc(record['acquired_utc'])
            if record['metadata_evidence'] != _evidence(record['acquired_utc']):
                raise ValueError('Inconsistent metadata evidence categories')
            if (record['detector'] is not None or record['observed_coverage'] is not None
                    or record['processing_status'] != 'archived'
                    or record['scientific_validation_status'] != 'not_validated'):
                raise ValueError('Registration schema cannot assert scientific validation')
            listing = record['archive']
            members = listing['members']
            names = []
            for member in members:
                _safe_member(member['path'])
                names.append(member['path'])
                if (type(member['is_directory']) is not bool
                        or any(type(member[k]) is not int or member[k] < 0 for k in ['compressed_bytes', 'uncompressed_bytes'])
                        or not re.fullmatch('[0-9a-f]{8}', member['crc32'])):
                    raise ValueError('Invalid archive member declarations')
            if (not members or len(set(names)) != len(names)
                    or listing['member_count'] != len(members)
                    or listing['file_count'] != sum(not m['is_directory'] for m in members)
                    or listing['declared_uncompressed_bytes'] != sum(m['uncompressed_bytes'] for m in members)
                    or listing['member_payloads_read'] is not False or listing['member_crc_verified'] is not False):
                raise ValueError('Inconsistent archive listing')
        if len(set(paths)) != len(paths):
            raise ValueError('Duplicate archive identities')
        dates = []
        present = {r['nominal_observation_date'] for r in records}
        for row in missing:
            day = row['nominal_observation_date']
            _missing([day])
            if (row['instrument'] != 'SoLEXS' or row['status'] != 'missing_from_obtained_collection'
                    or row['evidence'] != 'DOCUMENTED' or not row['statement'] or day in present):
                raise ValueError('Inconsistent missing coverage record')
            dates.append(day)
        if len(set(dates)) != len(dates):
            raise ValueError('Duplicate missing coverage dates')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed inventory metadata') from exc


def _observed(root, relative):
    path = root / relative
    identity = _identity(path.name)
    if relative != identity['path']:
        raise ValueError('Archive path is not canonical for its filename')
    if not path.is_file():
        raise ValueError('Archive is not an available local file')
    before = path.stat()
    digest = sha256_file(path)
    listing = _archive_listing(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('Archive changed during registration')
    return dict(identity, bytes=after.st_size, sha256=digest, archive=listing)


def verify_inventory(inventory: dict, root: Path) -> None:
    """Recheck every registered archive, without changing any provenance file."""
    validate_inventory(inventory)
    root = Path(root).resolve()
    for record in inventory['files']:
        relative = repository_relative_path(record['path'], root)
        observed = _observed(root, relative)
        if any(record[k] != v for k, v in observed.items()):
            raise ValueError(f"Archive identity conflict/changed bytes: {record['path']}")


def register_archives(root: Path, paths: list, *, inventory_path=Path('data/manifests/aditya_inventory.json'),
                      acquired_utc=None, source_url=PORTAL, missing_dates=None) -> dict:
    """Register explicit local inputs atomically; never download or write raw data."""
    root = Path(root).resolve()
    relative_output = repository_relative_path(inventory_path, root)
    if not relative_output.startswith('data/manifests/') or not relative_output.endswith('.json'):
        raise ValueError('Inventory must be a JSON file under data/manifests')
    output = root / relative_output
    source = _source(source_url)
    acquired = _utc(acquired_utc) if acquired_utc is not None else None
    relative_inputs = [repository_relative_path(p, root) for p in paths]
    if not relative_inputs or len(set(relative_inputs)) != len(relative_inputs):
        raise ValueError('Supply distinct explicit archive paths')
    inventory = (json.loads(output.read_text()) if output.exists() else
                 dict(schema_version=1, dataset_role=ROLE, files=[], missing_coverage=[]))
    validate_inventory(inventory)
    records = {r['path']: r for r in inventory['files']}
    for relative in relative_inputs:
        observed = _observed(root, relative)
        if relative in records:
            old = records[relative]
            if (any(old[k] != v for k, v in observed.items()) or old['source'] != source
                    or (acquired is not None and old['acquired_utc'] != acquired)):
                raise ValueError(f'Archive identity or acquisition conflict: {relative}')
            continue
        records[relative] = dict(observed, source=source, acquired_utc=acquired,
                                 registered_utc=datetime.now(timezone.utc).isoformat(), detector=None,
                                 observed_coverage=None, metadata_evidence=_evidence(acquired),
                                 processing_status='archived', scientific_validation_status='not_validated')
    inventory['files'] = [records[k] for k in sorted(records)]
    if missing_dates is not None:
        inventory['missing_coverage'] = _missing(missing_dates)
    validate_inventory(inventory)
    serialized = json.dumps(inventory, indent=2, allow_nan=False) + '\n'
    if output.exists() and output.read_text() == serialized:
        return inventory
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(serialized)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return inventory
