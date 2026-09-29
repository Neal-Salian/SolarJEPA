"""Fixtures here are artificial bytes for I/O tests, never scientific data."""
import hashlib
import io
import json
from pathlib import Path

import pytest

from solar_flare_jepa.data.download import download_manifest


PAYLOAD = b'CDF\x01' + b'unit-test-only' * 3
URL = 'https://data.ngdc.noaa.gov/platforms/test/sample.nc'


class Response(io.BytesIO):
    def __init__(self, body=PAYLOAD, length=None):
        super().__init__(body)
        self.headers = {'Content-Length': str(len(body) if length is None else length)}


def manifest(tmp_path, **changes):
    entry = dict(url=URL, path='data/raw/noaa/sample.nc', max_bytes=1024,
                 sha256=hashlib.sha256(PAYLOAD).hexdigest())
    entry.update(changes)
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps({'max_total_bytes': 2048, 'files': [entry]}))
    return path


def test_records_bytes_and_detects_corrupt_cache(tmp_path, monkeypatch):
    monkeypatch.setattr('solar_flare_jepa.data.download.open_public', lambda url: Response())
    path = manifest(tmp_path)
    records = download_manifest(path, tmp_path)
    assert records[0]['bytes'] == 46  # 4-byte magic plus three 14-byte strings
    target = tmp_path / 'data/raw/noaa/sample.nc'
    assert target.read_bytes() == PAYLOAD
    target.write_bytes(b'corrupt')
    with pytest.raises(ValueError):
        download_manifest(path, tmp_path)


@pytest.mark.parametrize('change', [
    {'url': 'https://example.org/sample.nc'},
    {'url': 'http://data.ngdc.noaa.gov/sample.nc'},
    {'url': URL + '?token=secret'},
    {'path': '../escape.nc'},
    {'path': 'README.md'},
    {'max_bytes': 0},
])
def test_rejects_invalid_source_or_destination_before_network(tmp_path, change):
    with pytest.raises(ValueError):
        download_manifest(manifest(tmp_path, **change), tmp_path)


@pytest.mark.parametrize('body,length,limit', [
    (b'<html>login</html>', None, 1024),
    (PAYLOAD, 500, 1024),
    (PAYLOAD, None, 10),
])
def test_no_partial_file_on_bad_response(tmp_path, monkeypatch, body, length, limit):
    monkeypatch.setattr('solar_flare_jepa.data.download.open_public',
                        lambda url: Response(body, length))
    with pytest.raises(ValueError):
        download_manifest(manifest(tmp_path, max_bytes=limit), tmp_path)
    assert not (tmp_path / 'data/raw/noaa/sample.nc').exists()
    assert not list(tmp_path.rglob('*.part'))


def test_hash_mismatch_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr('solar_flare_jepa.data.download.open_public', lambda url: Response())
    with pytest.raises(ValueError):
        download_manifest(manifest(tmp_path, sha256='0' * 64), tmp_path)
    assert not (tmp_path / 'data/raw/noaa/sample.nc').exists()
