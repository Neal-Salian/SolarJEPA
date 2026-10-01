"""Bounded public NOAA acquisition. No authentication or archive scraping."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
import certifi


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused; review and pin the new public URL')


def open_public(url):
    context = ssl.create_default_context(cafile=certifi.where())
    return build_opener(NoRedirect, HTTPSHandler(context=context)).open(
        Request(url, headers={'User-Agent': 'solar-flare-jepa-research/0.1'}), timeout=30)


def sha256_file(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _validate(entry, root):
    url = urlsplit(entry['url'])
    if (url.scheme != 'https' or url.netloc != 'data.ngdc.noaa.gov'
            or url.query or url.fragment or not url.path.startswith('/platforms/')):
        raise ValueError('Only unsigned public NOAA platform HTTPS URLs are supported')
    target = (root / entry['path']).resolve()
    if not target.is_relative_to((root / 'data/raw/noaa').resolve()):
        raise ValueError('Destination must be inside data/raw/noaa')
    if target.suffix != '.nc' or not 0 < entry['max_bytes'] <= 4 * 1024**2:
        raise ValueError('Expected a NetCDF file with a positive limit <=4 MiB')
    digest = entry.get('sha256')
    if digest is not None and (len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest)):
        raise ValueError('Invalid SHA-256')
    return target


def _check(path, entry):
    size = path.stat().st_size
    if size > entry['max_bytes'] or (entry.get('bytes') is not None and size != entry['bytes']):
        raise ValueError('File size differs from manifest or exceeds cap')
    with path.open('rb') as stream:
        magic = stream.read(8)
    if not (magic.startswith((b'CDF\x01', b'CDF\x02', b'CDF\x05'))
            or magic == b'\x89HDF\r\n\x1a\n'):
        raise ValueError('Response is not NetCDF/HDF5; possible error or login page')
    digest = sha256_file(path)
    if entry.get('sha256') and digest != entry['sha256']:
        raise ValueError('SHA-256 mismatch; existing/raw data are never silently replaced')
    return size, digest


def verified_manifest_paths(manifest_path: Path, root: Path, product: str) -> list[Path]:
    """Select immutable local reference files; never scan or download extra dates."""
    if product not in {'avg1m', 'flsum'}:
        raise ValueError('Unsupported reference product')
    root = Path(root).resolve()
    spec = json.loads(Path(manifest_path).read_text())
    entries = [e for e in spec['files']
               if f'/xrsf-l2-{product}_science/' in urlsplit(e['url']).path]
    if not entries:
        raise ValueError(f'No {product} files in pinned manifest')
    paths = []
    for entry in entries:
        if not entry.get('sha256') or entry.get('bytes') is None:
            raise ValueError('Reference preparation requires pinned hashes and byte sizes')
        path = _validate(entry, root)
        _check(path, entry)
        paths.append(path)
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate reference files in manifest')
    return paths


def download_manifest(manifest_path: Path, root: Path) -> list[dict]:
    manifest_path, root = Path(manifest_path), Path(root).resolve()
    spec = json.loads(manifest_path.read_text())
    entries = spec['files']
    budget = spec['max_total_bytes']
    if not entries or not 0 < budget <= 16 * 1024**2:
        raise ValueError('Empty manifest or total cap outside (0,16 MiB]')
    targets = [_validate(entry, root) for entry in entries]
    if len(set(targets)) != len(targets) or sum(e['max_bytes'] for e in entries) > budget:
        raise ValueError('Duplicate destinations or combined per-file limits exceed total budget')
    records = []
    for entry, target in zip(entries, targets):
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not entry.get('sha256'):
                raise ValueError('Existing file requires a pinned hash')
            size, digest = _check(target, entry)
            fetched = False
        else:
            tmp = None
            try:
                with open_public(entry['url']) as response:
                    length = response.headers.get('Content-Length')
                    expected = int(length) if length is not None else None
                    if expected is not None and expected > entry['max_bytes']:
                        raise ValueError('Content-Length exceeds per-file cap')
                    with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.part', delete=False) as out:
                        tmp = Path(out.name)
                        total = 0
                        while chunk := response.read(65536):
                            total += len(chunk)
                            if total > entry['max_bytes']:
                                raise ValueError('Stream exceeds per-file cap')
                            out.write(chunk)
                    if expected is not None and total != expected:
                        raise ValueError('Truncated response: Content-Length mismatch')
                size, digest = _check(tmp, entry)
                # Link creation is atomic and refuses replacement if another process won.
                target.hardlink_to(tmp)
                fetched = True
            finally:
                if tmp is not None:
                    tmp.unlink(missing_ok=True)
        records.append(dict(path=entry['path'], url=entry['url'], bytes=size, sha256=digest,
                            fetched=fetched, checked_utc=datetime.now(timezone.utc).isoformat()))
    provenance = root / 'data/manifests/noaa_retrieval.json'
    provenance.parent.mkdir(parents=True, exist_ok=True)
    provenance.write_text(json.dumps({'manifest_sha256': sha256_file(manifest_path),
                                      'files': records}, indent=2) + '\n')
    return records
