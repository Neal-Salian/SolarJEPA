"""Offline artificial-byte tests: no network or scientific validity claims."""
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
from urllib.error import URLError

import pytest


PAYLOAD = b'CDF\x01' + b'artificial-test-data'
BASE = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2024/07/'
DIRECTORY = 'data/raw/noaa/history/goes16/xrsf-l2-avg1m_science/v2-2-1/2024/07/'


def load_api():
    name = 'solar_flare_jepa.data.goes_acquisition'
    assert importlib.util.find_spec(name) is not None, 'Historical acquisition is not implemented'
    return importlib.import_module(name)


class Response(io.BytesIO):
    def __init__(self, body=PAYLOAD, length='actual'):
        super().__init__(body)
        self.headers = {} if length is None else {'Content-Length': str(len(body) if length == 'actual' else length)}


def config(root, days=2, **changes):
    files = []
    for day in range(1, days + 1):
        name = f'sci_xrsf-l2-avg1m_g16_d202407{day:02d}_v2-2-1.nc'
        files.append(dict(nominal_date=f'2024-07-{day:02d}', url=BASE + name,
                          path=DIRECTORY + name, max_bytes=128))
    value = dict(schema_version=1, dataset_id='artificial-offline-history', platform='GOES-16',
                 product='xrsf-l2-avg1m_science', version='2-2-1',
                 selected_interval=dict(start='2024-07-01', end_exclusive=f'2024-07-{days + 1:02d}',
                                        basis='a priori calendar selection'),
                 manifest_path='data/manifests/history.json', max_total_bytes=days * 128,
                 timeout_seconds=30, max_attempts=3, retry_delay_seconds=0, files=files)
    value.update(changes)
    path = root / 'configs/data/history.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path, value


def write_config(path, value):
    path.write_text(json.dumps(value))


def no_network(*args, **kwargs):
    raise AssertionError('This operation must not use the network')


def test_acquire_and_resume_complete_pinned_inventory(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    acquired = api.acquire_history(path, tmp_path)
    assert acquired['complete'] is True
    assert [f['nominal_date'] for f in acquired['files']] == ['2024-07-01', '2024-07-02']
    assert [f['bytes'] for f in acquired['files']] == [24, 24]
    assert all(f['sha256'] == hashlib.sha256(PAYLOAD).hexdigest() for f in acquired['files'])
    manifest = tmp_path / value['manifest_path']
    before = manifest.read_bytes()
    monkeypatch.setattr(api, 'open_history_url', no_network)
    assert api.acquire_history(path, tmp_path) == acquired
    assert manifest.read_bytes() == before
    assert api.verify_history(manifest, tmp_path) == [tmp_path / f['path'] for f in value['files']]


def test_retry_transient_connection_failure_is_bounded(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    count = 0
    def flaky(url, timeout):
        nonlocal count
        count += 1
        if count < 3:
            raise URLError('temporary outage')
        return Response()
    monkeypatch.setattr(api, 'open_history_url', flaky)
    assert api.acquire_history(path, tmp_path)['complete'] is True
    assert count == 3


def test_failure_keeps_verified_prefix_for_pinned_resume(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path)
    count = 0
    def interrupted(url, timeout):
        nonlocal count
        if 'd20240702' in url:
            count += 1
            raise URLError('outage')
        return Response()
    monkeypatch.setattr(api, 'open_history_url', interrupted)
    with pytest.raises(URLError):
        api.acquire_history(path, tmp_path)
    manifest = tmp_path / value['manifest_path']
    prefix = json.loads(manifest.read_text())
    assert prefix['complete'] is False
    assert len(prefix['files']) == 1
    assert count == 3
    with pytest.raises(ValueError, match='complete'):
        api.verify_history(manifest, tmp_path)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    complete = api.acquire_history(path, tmp_path)
    assert complete['files'][0] == prefix['files'][0]
    assert len(api.verify_history(manifest, tmp_path)) == 2
    assert not list(tmp_path.rglob('*.part'))


@pytest.mark.parametrize('body,length', [(b'<html>error</html>', 'actual'), (PAYLOAD, 99),
                                          (b'CDF\x01' + b'x' * 125, None), (PAYLOAD, -1)])
def test_bad_response_never_installs_raw_or_partial(tmp_path, monkeypatch, body, length):
    api = load_api()
    path, value = config(tmp_path, days=1)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response(body, length))
    with pytest.raises(ValueError):
        api.acquire_history(path, tmp_path)
    assert not (tmp_path / value['files'][0]['path']).exists()
    assert not list(tmp_path.rglob('*.part'))


@pytest.mark.parametrize('defect', ['host', 'http', 'query', 'platform', 'version', 'date', 'path', 'budget', 'filecap', 'missing_date', 'duplicate'])
def test_invalid_selection_fails_before_network(tmp_path, monkeypatch, defect):
    api = load_api()
    path, value = config(tmp_path)
    first = value['files'][0]
    if defect == 'host': first['url'] = first['url'].replace('data.ngdc.noaa.gov', 'example.org')
    elif defect == 'http': first['url'] = first['url'].replace('https:', 'http:')
    elif defect == 'query': first['url'] += '?token=x'
    elif defect == 'platform': first['url'] = first['url'].replace('g16_', 'g18_')
    elif defect == 'version': first['url'] = first['url'].replace('v2-2-1', 'v2-2-0')
    elif defect == 'date': first['nominal_date'] = '2024-07-03'
    elif defect == 'path': first['path'] = '../escaped.nc'
    elif defect == 'budget': value['max_total_bytes'] = 128
    elif defect == 'filecap': first['max_bytes'] = 1048577
    elif defect == 'missing_date': value['files'].pop()
    elif defect == 'duplicate': value['files'][1] = dict(first)
    write_config(path, value)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    with pytest.raises(ValueError):
        api.acquire_history(path, tmp_path)
    assert not (tmp_path / value['manifest_path']).exists()


def test_escaping_raw_directory_symlink_fails_before_network(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    outside = tmp_path.parent / (tmp_path.name + '-outside')
    outside.mkdir()
    raw = tmp_path / 'data/raw/noaa'
    raw.mkdir(parents=True)
    (raw / 'history').symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    with pytest.raises(ValueError, match='[Pp]ath|[Ss]ymlink'):
        api.acquire_history(path, tmp_path)
    assert list(outside.iterdir()) == []


def test_existing_unpinned_file_is_never_adopted(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    target = tmp_path / value['files'][0]['path']
    target.parent.mkdir(parents=True)
    target.write_bytes(PAYLOAD)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    with pytest.raises(ValueError, match='pinned'):
        api.acquire_history(path, tmp_path)
    assert target.read_bytes() == PAYLOAD


def test_corrupt_resumed_bytes_are_not_replaced(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    api.acquire_history(path, tmp_path)
    target = tmp_path / value['files'][0]['path']
    changed = b'CDF\x01' + b'?' * 20
    target.write_bytes(changed)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    with pytest.raises(ValueError, match='SHA-256'):
        api.acquire_history(path, tmp_path)
    assert target.read_bytes() == changed
    with pytest.raises(ValueError, match='SHA-256'):
        api.verify_history(tmp_path / value['manifest_path'], tmp_path)


def test_reference_copy_preserves_original_and_records_pinned_lineage(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    original = tmp_path / 'data/raw/noaa' / Path(value['files'][0]['path']).name
    original.parent.mkdir(parents=True)
    original.write_bytes(PAYLOAD)
    reuse = dict(path=original.relative_to(tmp_path).as_posix(), bytes=24,
                 sha256=hashlib.sha256(PAYLOAD).hexdigest(), checked_utc='2026-09-29T09:29:07+00:00')
    value['files'][0]['reuse'] = reuse
    write_config(path, value)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    result = api.acquire_history(path, tmp_path)
    row = result['files'][0]
    assert row['lineage'] == dict(method='copy_pinned_reference', parent=reuse)
    assert row['acquired_utc'] is None
    target = tmp_path / row['path']
    assert target.stat().st_ino != original.stat().st_ino
    target.write_bytes(b'changed history copy')
    assert original.read_bytes() == PAYLOAD


@pytest.mark.parametrize('defect', ['url', 'date', 'platform', 'bytes', 'hash', 'missing_record', 'config_hash'])
def test_verifier_rejects_manifest_identity_tampering(tmp_path, monkeypatch, defect):
    api = load_api()
    path, value = config(tmp_path)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    result = api.acquire_history(path, tmp_path)
    row = result['files'][0]
    if defect == 'url': row['url'] = row['url'].replace('g16_', 'g18_')
    elif defect == 'date': row['nominal_date'] = '2024-07-02'
    elif defect == 'platform': row['platform'] = 'GOES-18'
    elif defect == 'bytes': row['bytes'] = 25
    elif defect == 'hash': row['sha256'] = '0' * 64
    elif defect == 'missing_record': result['files'].pop()
    elif defect == 'config_hash': result['config_sha256'] = '0' * 64
    manifest = tmp_path / value['manifest_path']
    manifest.write_text(json.dumps(result))
    with pytest.raises(ValueError):
        api.verify_history(manifest, tmp_path)


def test_changed_config_cannot_silently_replace_existing_ledger(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    api.acquire_history(path, tmp_path)
    manifest = tmp_path / value['manifest_path']
    before = manifest.read_bytes()
    value['dataset_id'] = 'changed-selection'
    write_config(path, value)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    with pytest.raises(ValueError, match='config|identity'):
        api.acquire_history(path, tmp_path)
    assert manifest.read_bytes() == before


def test_duplicate_json_keys_fail_before_any_download(tmp_path, monkeypatch):
    api = load_api()
    path, _ = config(tmp_path, days=1)
    path.write_text(path.read_text().replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'))
    monkeypatch.setattr(api, 'open_history_url', no_network)
    with pytest.raises(ValueError, match='Duplicate'):
        api.acquire_history(path, tmp_path)


@pytest.mark.parametrize('defect', ['boolean_schema', 'download_time_removed'])
def test_verifier_preserves_strict_schema_and_acquisition_facts(tmp_path, monkeypatch, defect):
    api = load_api()
    path, value = config(tmp_path, days=1)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    result = api.acquire_history(path, tmp_path)
    if defect == 'boolean_schema':
        result['schema_version'] = True
    else:
        result['files'][0]['acquired_utc'] = None
    manifest = tmp_path / value['manifest_path']
    manifest.write_text(json.dumps(result))
    with pytest.raises(ValueError):
        api.verify_history(manifest, tmp_path)


def test_wrong_hash_response_does_not_install_selected_file(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    value['files'][0].update(bytes=24, sha256='0' * 64)
    write_config(path, value)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    with pytest.raises(ValueError, match='SHA-256'):
        api.acquire_history(path, tmp_path)
    assert not (tmp_path / value['files'][0]['path']).exists()
    assert not list(tmp_path.rglob('*.part'))


def test_partial_read_retry_restarts_stream_and_preserves_integrity(tmp_path, monkeypatch):
    api = load_api()
    path, value = config(tmp_path, days=1)
    count = 0
    class InterruptedResponse(Response):
        def read(self, size):
            if self.tell():
                raise ConnectionError('interrupted stream')
            return super().read(8)
    def resumed(url, timeout):
        nonlocal count
        count += 1
        assert timeout == 30
        return InterruptedResponse() if count == 1 else Response()
    monkeypatch.setattr(api, 'open_history_url', resumed)
    result = api.acquire_history(path, tmp_path)
    assert (tmp_path / result['files'][0]['path']).read_bytes() == PAYLOAD
    assert count == 2
    assert not list(tmp_path.rglob('*.part'))


def test_complete_pins_verify_after_repository_relocation(tmp_path, monkeypatch):
    api = load_api()
    import shutil
    first = tmp_path / 'first'
    first.mkdir()
    path, value = config(first)
    monkeypatch.setattr(api, 'open_history_url', lambda url, timeout: Response())
    api.acquire_history(path, first)
    moved = tmp_path / 'moved'
    shutil.copytree(first, moved)
    monkeypatch.setattr(api, 'open_history_url', no_network)
    paths = api.verify_history(moved / value['manifest_path'], moved)
    assert paths == [moved / e['path'] for e in value['files']]
    assert all(p.read_bytes() == PAYLOAD for p in paths)


def test_optional_stats_record_attempts_retries_bytes_and_failures(tmp_path, monkeypatch):
    # V2 restoration: retry counts and downloaded bytes must be observable without changing behaviour.
    api = load_api()
    path, value = config(tmp_path, days=2)
    calls = []
    def flaky(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise URLError('temporary outage')
        return Response()
    monkeypatch.setattr(api, 'open_history_url', flaky)
    stats = {}
    assert api.acquire_history(path, tmp_path, stats=stats)['complete'] is True
    assert stats == dict(attempts=3, retries=1, downloaded_files=2, downloaded_bytes=2 * len(PAYLOAD),
                         reused_reference_files=0, failures=[dict(url=value['files'][0]['url'], attempt=1,
                                                                  error='URLError: <urlopen error temporary outage>')])
    monkeypatch.setattr(api, 'open_history_url', no_network)
    again = {}
    api.acquire_history(path, tmp_path, stats=again)  # idempotent: nothing requested, nothing counted
    assert again == dict(attempts=0, retries=0, downloaded_files=0, downloaded_bytes=0, reused_reference_files=0,
                         failures=[])
