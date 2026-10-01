"""Fixtures here are artificial bytes for I/O tests, never scientific data."""
import hashlib
import io
import json
from pathlib import Path

import pytest

from solar_flare_jepa.data.download import download_manifest, verified_manifest_paths


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


def test_manifest_selection_ignores_extra_files_and_verifies_pinned_bytes(tmp_path):
    directory = tmp_path / 'data/raw/noaa'
    directory.mkdir(parents=True)
    selected = directory / 'sci_xrsf-l2-avg1m_g16_d20240701_v2-2-1.nc'
    selected.write_bytes(PAYLOAD)
    (directory / 'sci_xrsf-l2-avg1m_g16_d20240704_v2-2-1.nc').write_bytes(PAYLOAD)
    url = 'https://data.ngdc.noaa.gov/platforms/goes/l2/data/xrsf-l2-avg1m_science/2024/07/' + selected.name
    p = manifest(tmp_path, path=str(selected.relative_to(tmp_path)), url=url, bytes=46)
    assert verified_manifest_paths(p, tmp_path, 'avg1m') == [selected]
    selected.write_bytes(b'CDF\x01' + b'x' * 42)
    with pytest.raises(ValueError, match='SHA-256'):
        verified_manifest_paths(p, tmp_path, 'avg1m')


def test_manifest_selection_requires_product_and_pinned_hash(tmp_path):
    p = manifest(tmp_path)
    with pytest.raises(ValueError):
        verified_manifest_paths(p, tmp_path, 'avg1m')
    with pytest.raises(ValueError):
        verified_manifest_paths(p, tmp_path, 'unknown')
