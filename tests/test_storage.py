"""Artificial ZIPs exercise intake contracts; none contain satellite observations."""
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIRST = 'data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240701_v1.1.zip'
SECOND = 'data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240703_v1.1.zip'
INVENTORY = 'data/manifests/aditya_inventory.json'


def storage():
    assert importlib.util.find_spec('solar_flare_jepa.data.storage') is not None, 'Archive registration API is missing'
    return importlib.import_module('solar_flare_jepa.data.storage')


def artificial_archive(root, relative=FIRST, members=None):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as archive:
        for name, payload in (members or [('fixture/', b''), ('fixture/test.FITS', b'artificial bytes only')]):
            info = zipfile.ZipInfo(name, date_time=(2024, 7, 1, 0, 0, 0))
            archive.writestr(info, payload)
    return path


def test_registration_measures_identity_without_extracting_or_guessing(tmp_path):
    archive = artificial_archive(tmp_path)
    before = archive.read_bytes()
    manifest = storage().register_archives(tmp_path, [FIRST], missing_dates=['2024-07-02'])
    record = manifest['files'][0]
    assert record['path'] == FIRST
    assert record['original_filename'] == 'AL1_SLX_L1_20240701_v1.1.zip'
    assert record['bytes'] == len(before)
    assert record['sha256'] == hashlib.sha256(before).hexdigest()
    assert (record['mission'], record['instrument'], record['processing_level'], record['product_version']) == ('Aditya-L1', 'SoLEXS', 'L1', 'v1.1')
    assert record['nominal_observation_date'] == '2024-07-01'
    assert record['metadata_evidence']['nominal_observation_date'] == 'INFERRED'
    assert record['metadata_evidence']['sha256'] == 'OBSERVED'
    assert record['detector'] is None and record['observed_coverage'] is None
    assert record['acquired_utc'] is None
    assert record['registered_utc'].endswith('+00:00')
    assert record['processing_status'] == 'archived'
    assert record['scientific_validation_status'] == 'not_validated'
    assert manifest['dataset_role'] == 'initial_ingestion_validation_sample_not_training_dataset'
    assert json.loads((tmp_path / INVENTORY).read_text()) == manifest
    assert archive.read_bytes() == before
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*') if p.is_file()) == [INVENTORY, FIRST]


def test_central_directory_listing_is_distinct_from_member_content_validation(tmp_path):
    artificial_archive(tmp_path)
    listing = storage().register_archives(tmp_path, [FIRST])['files'][0]['archive']
    assert listing['member_count'] == 2 and listing['file_count'] == 1
    assert listing['declared_uncompressed_bytes'] == 21
    assert [m['path'] for m in listing['members']] == ['fixture/', 'fixture/test.FITS']
    assert listing['member_payloads_read'] is False
    assert listing['member_crc_verified'] is False


def test_absolute_inputs_record_relative_identifiers(tmp_path):
    archive = artificial_archive(tmp_path)
    record = storage().register_archives(tmp_path, [archive])['files'][0]
    assert record['path'] == FIRST
    assert storage().repository_relative_path(archive, tmp_path) == FIRST
    assert str(tmp_path) not in json.dumps(record)


def test_repeat_registration_preserves_manifest_bytes_and_timestamps(tmp_path):
    artificial_archive(tmp_path)
    first = storage().register_archives(tmp_path, [FIRST], acquired_utc='2026-10-01T00:00:00Z', missing_dates=['2024-07-02'])
    before = (tmp_path / INVENTORY).read_bytes()
    second = storage().register_archives(tmp_path, [FIRST])
    assert second == first
    assert (tmp_path / INVENTORY).read_bytes() == before


def test_partial_registration_preserves_other_product_facts(tmp_path):
    artificial_archive(tmp_path)
    first = storage().register_archives(tmp_path, [FIRST], acquired_utc='2026-10-01T00:00:00Z')
    artificial_archive(tmp_path, SECOND)
    combined = storage().register_archives(tmp_path, [SECOND])
    assert len(combined['files']) == 2
    assert combined['files'][0] == first['files'][0]
    assert combined['files'][1]['acquired_utc'] is None


def test_changed_bytes_cannot_rewrite_registered_identity(tmp_path):
    artificial_archive(tmp_path)
    storage().register_archives(tmp_path, [FIRST])
    before = (tmp_path / INVENTORY).read_bytes()
    artificial_archive(tmp_path, members=[('different.txt', b'changed artificial bytes')])
    with pytest.raises(ValueError, match='conflict|changed'):
        storage().register_archives(tmp_path, [FIRST])
    assert (tmp_path / INVENTORY).read_bytes() == before


@pytest.mark.parametrize('changes', [
    {'acquired_utc': '2026-10-01T01:00:00Z'},
    {'source_url': 'https://pradan1.issdc.gov.in/al1/'},
])
def test_repeat_cannot_silently_rewrite_acquisition_facts(tmp_path, changes):
    artificial_archive(tmp_path)
    storage().register_archives(tmp_path, [FIRST], acquired_utc='2026-10-01T00:00:00Z')
    before = (tmp_path / INVENTORY).read_bytes()
    with pytest.raises(ValueError, match='conflict'):
        storage().register_archives(tmp_path, [FIRST], **changes)
    assert (tmp_path / INVENTORY).read_bytes() == before


@pytest.mark.parametrize('relative', [
    '../AL1_SLX_L1_20240701_v1.1.zip',
    'data/raw/aditya/solexs/l1/v1.1/archives/2024/08/AL1_SLX_L1_20240701_v1.1.zip',
    'data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240230_v1.1.zip',
])
def test_noncanonical_or_invalid_date_paths_fail_before_writing(tmp_path, relative):
    artificial_archive(tmp_path, relative)
    with pytest.raises(ValueError):
        storage().register_archives(tmp_path, [relative])
    assert not (tmp_path / INVENTORY).exists()


def test_symlink_escape_is_rejected(tmp_path):
    root = tmp_path / 'root'
    outside = artificial_archive(tmp_path / 'outside')
    alias = root / FIRST
    alias.parent.mkdir(parents=True)
    alias.symlink_to(outside)
    with pytest.raises(ValueError):
        storage().register_archives(root, [FIRST])
    assert not (root / INVENTORY).exists()


@pytest.mark.parametrize('member', ['../escape.fits', '/absolute.fits', 'C:/drive.fits', 'folder\\escape.fits'])
def test_unsafe_member_names_fail_without_extracting(tmp_path, member):
    artificial_archive(tmp_path, members=[(member, b'artificial bytes')])
    with pytest.raises(ValueError, match='member'):
        storage().register_archives(tmp_path, [FIRST])
    assert not (tmp_path / INVENTORY).exists()


@pytest.mark.parametrize('defect', ['hash', 'date', 'path', 'member_size', 'missing_conflict'])
def test_inconsistent_manifest_is_rejected_without_overwrite(tmp_path, defect):
    artificial_archive(tmp_path)
    manifest = storage().register_archives(tmp_path, [FIRST])
    damaged = copy.deepcopy(manifest)
    record = damaged['files'][0]
    if defect == 'hash':
        record['sha256'] = 'invalid'
    elif defect == 'date':
        record['nominal_observation_date'] = '2024-07-03'
    elif defect == 'path':
        record['path'] = '/absolute/archive.zip'
    elif defect == 'member_size':
        record['archive']['declared_uncompressed_bytes'] += 1
    else:
        damaged['missing_coverage'] = [{'instrument': 'SoLEXS', 'nominal_observation_date': '2024-07-01', 'status': 'missing_from_obtained_collection', 'evidence': 'DOCUMENTED', 'statement': 'Missing from obtained collection; not a mission-wide availability claim.'}]
    target = tmp_path / INVENTORY
    target.write_text(json.dumps(damaged))
    before = target.read_bytes()
    with pytest.raises(ValueError):
        storage().register_archives(tmp_path, [FIRST])
    assert target.read_bytes() == before


def test_missing_coverage_refers_only_to_obtained_collection(tmp_path):
    artificial_archive(tmp_path)
    manifest = storage().register_archives(tmp_path, [FIRST], missing_dates=['2024-07-02'])
    missing = manifest['missing_coverage'][0]
    assert missing['nominal_observation_date'] == '2024-07-02'
    assert missing['status'] == 'missing_from_obtained_collection'
    assert missing['evidence'] == 'DOCUMENTED'
    assert len(manifest['files']) == 1
    with pytest.raises(ValueError, match='missing'):
        storage().register_archives(tmp_path, [FIRST], missing_dates=['2024-07-01'])


def test_verification_detects_changed_archives_without_updating_manifest(tmp_path):
    artificial_archive(tmp_path)
    manifest = storage().register_archives(tmp_path, [FIRST])
    storage().verify_inventory(manifest, tmp_path)
    before = (tmp_path / INVENTORY).read_bytes()
    artificial_archive(tmp_path, members=[('new.txt', b'changed')])
    with pytest.raises(ValueError, match='changed|conflict'):
        storage().verify_inventory(manifest, tmp_path)
    assert (tmp_path / INVENTORY).read_bytes() == before


@pytest.mark.parametrize('options', [
    {'source_url': 'https://pradan.issdc.gov.in/al1/?token=private'},
    {'source_url': 'https://user:password@pradan.issdc.gov.in/al1/'},
    {'acquired_utc': '2026-10-01'},
    {'inventory_path': FIRST},
])
def test_invalid_provenance_or_output_cannot_write_files(tmp_path, options):
    artificial_archive(tmp_path)
    with pytest.raises(ValueError):
        storage().register_archives(tmp_path, [FIRST], **options)
    assert not (tmp_path / INVENTORY).exists()


def test_raw_directory_and_extension_protection(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'config', 'core.ignorecase', 'false'], check=True)
    (tmp_path / '.gitignore').write_text((ROOT / '.gitignore').read_text())
    protected = [FIRST, SECOND, 'data/interim/aditya/solexs/cache/product.fits',
                 'data/interim/aditya/solexs/cache/product.FITS',
                 'accidental.ZIP', 'accidental.FITS', 'accidental.FIT', 'accidental.FTS']
    for relative in protected:
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b'artificial ignore-policy fixture')
    result = subprocess.run(['git', '-C', str(tmp_path), 'check-ignore', '--stdin'],
                            input='\n'.join(protected)+'\n', capture_output=True, text=True)
    assert set(result.stdout.splitlines()) == set(protected)
    status = subprocess.check_output(['git', '-C', str(tmp_path), 'status', '--porcelain', '--untracked-files=all'], text=True)
    assert status.strip() == '?? .gitignore'


@pytest.mark.parametrize('defect', ['evidence', 'acquisition_evidence', 'registered_time'])
def test_evidence_categories_and_registration_time_are_validated(tmp_path, defect):
    artificial_archive(tmp_path)
    manifest = storage().register_archives(tmp_path, [FIRST])
    if defect == 'evidence':
        manifest['files'][0]['metadata_evidence']['nominal_observation_date'] = 'OBSERVED'
    elif defect == 'acquisition_evidence':
        manifest['files'][0]['metadata_evidence']['acquired_utc'] = 'OBSERVED'
    else:
        manifest['files'][0]['registered_utc'] = None
    with pytest.raises(ValueError):
        storage().validate_inventory(manifest)


def test_registration_cli_from_other_directory_and_read_only_verification(tmp_path):
    from test_cli import clean_environment
    archive = artificial_archive(tmp_path)
    config = tmp_path / 'sample.json'
    config.write_text(json.dumps({'inventory_path': INVENTORY, 'source_url': 'https://pradan.issdc.gov.in/al1/',
                                 'archives': [FIRST], 'missing_dates': ['2024-07-02']}))
    invocation = [sys.executable, '-B', str(ROOT / 'scripts/register_aditya.py'),
                  '--root', str(tmp_path), '--config', str(config)]
    before = archive.read_bytes()
    registered = subprocess.run(invocation, cwd=tmp_path.parent, env=clean_environment(), capture_output=True, text=True)
    assert registered.returncode == 0, registered.stderr
    assert json.loads(registered.stdout)['inventory'] == INVENTORY
    receipt = (tmp_path / INVENTORY).read_bytes()
    verified = subprocess.run(invocation + ['--verify'], cwd=tmp_path.parent, env=clean_environment(), capture_output=True, text=True)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)['action'] == 'verified'
    assert (tmp_path / INVENTORY).read_bytes() == receipt
    assert archive.read_bytes() == before
