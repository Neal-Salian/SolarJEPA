"""Bounded SWPC snapshot intake and diagnostics, not science-product validation.

The JSON time tags are retained as supplied. They are not promoted to science bin
starts or publication times. No function here constructs eligible model inputs.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import ssl
import stat
import tempfile
import time
from types import MappingProxyType
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler
from uuid import uuid4

import certifi
import pandas as pd

PRODUCTS = {role: f'https://services.swpc.noaa.gov/json/goes/{role}/xrays-6-hour.json'
            for role in ('primary', 'secondary')}
DEFAULT_CACHE_ROOT = '.cache/noaa/goes_nrt'
BANDS = {'0.05-0.4nm': 'xrsa', '0.1-0.8nm': 'xrsb'}
MAX_BYTES = 2_000_000
MAX_ROWS = 1500
MINUTE_NS = 60_000_000_000


class NoaaNrtError(ValueError):
    """Acquisition or cache integrity is unavailable; never silently fall back."""


def _utc(value, *, minute=False):
    try:
        stamp = pd.Timestamp(value)
        if (pd.isna(stamp) or stamp.tzinfo is None
                or stamp.utcoffset().total_seconds() != 0
                or (minute and stamp.value % MINUTE_NS)):
            raise ValueError('Expected explicit UTC' + (' whole minute' if minute else ''))
        return stamp.tz_convert('UTC')
    except (TypeError, ValueError, OverflowError) as exc:
        raise NoaaNrtError('Invalid UTC timestamp') from exc


def _now():
    return datetime.now(timezone.utc).isoformat()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise NoaaNrtError('Duplicate JSON key')
        result[key] = value
    return result


def _decode(payload):
    try:
        return json.loads(payload, object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(NoaaNrtError('Nonfinite JSON')))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise NoaaNrtError('Malformed JSON') from exc


def _rows(payload):
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_BYTES:
        raise NoaaNrtError('Snapshot bytes exceed bounds or are empty')
    rows = _decode(payload)
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
        raise NoaaNrtError('Expected bounded nonempty observation list')
    required = {'time_tag', 'satellite', 'flux', 'observed_flux', 'electron_correction',
                'electron_contaminaton', 'energy'}
    seen, latest = set(), {}
    for row in rows:
        if not isinstance(row, dict) or not required <= row.keys():
            raise NoaaNrtError('Missing SWPC observation fields')
        if (type(row['time_tag']) is not str or type(row['energy']) is not str or row['energy'] not in BANDS
                or type(row['satellite']) is not int or not 16 <= row['satellite'] <= 19
                or type(row['electron_contaminaton']) is not bool):
            raise NoaaNrtError('Unsupported channel, satellite or quality schema')
        stamp = _utc(row['time_tag'], minute=True)
        key = (stamp.value, row['energy'])
        if key in seen or stamp.value <= latest.get(row['energy'], -2**63):
            raise NoaaNrtError('Duplicate or unordered channel/time identity')
        seen.add(key)
        latest[row['energy']] = stamp.value
        for name in ('flux', 'observed_flux', 'electron_correction'):
            value = row[name]
            try:
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                    raise NoaaNrtError('Unsupported numeric field')
            except OverflowError as exc:
                raise NoaaNrtError('Numeric field exceeds finite float domain') from exc
    return rows


def _safe_root(value):
    root = Path(value).absolute()
    if '..' in root.parts or any(p.is_symlink() for p in (root, *root.parents)):
        raise NoaaNrtError('Cache must not traverse symlinks or parent components')
    return root


def _inside(root, relative):
    if type(relative) is not str or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise NoaaNrtError('Cache path must be relative and contained')
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root.resolve()):
        raise NoaaNrtError('Cache path escapes root or traverses symlink')
    return path


@dataclass(frozen=True)
class Snapshot:
    payload: bytes
    provenance: dict

    def __post_init__(self):
        object.__setattr__(self, 'provenance', MappingProxyType(dict(self.provenance)))


def _verify(snapshot):
    p = snapshot.provenance
    required = {'schema_version', 'product', 'url', 'payload_sha256', 'payload_bytes',
                'received_utc', 'publication_utc', 'http_date', 'http_last_modified', 'receipt_path'}
    if (set(p) != required or type(p['schema_version']) is not int or p['schema_version'] != 1
            or p['product'] not in PRODUCTS or p['url'] != PRODUCTS[p['product']]
            or p['publication_utc'] is not None
            or type(p['payload_bytes']) is not int or p['payload_bytes'] != len(snapshot.payload)
            or p['payload_sha256'] != sha256(snapshot.payload).hexdigest()
            or any(p[name] is not None and type(p[name]) is not str
                   for name in ('http_date', 'http_last_modified'))):
        raise NoaaNrtError('Invalid snapshot provenance or payload identity')
    _utc(p['received_utc'])
    if (type(p['receipt_path']) is not str or len(Path(p['receipt_path']).parts) != 2
            or Path(p['receipt_path']).parts[0] != 'receipts'
            or not Path(p['receipt_path']).name.endswith('.json')):
        raise NoaaNrtError('Invalid receipt identity')
    return _rows(snapshot.payload)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise NoaaNrtError('NOAA source redirect refused')


def _transport(url, timeout):
    opener = build_opener(_NoRedirect(), HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    return opener.open(Request(url, headers={'User-Agent': 'SolarJEPA-research/0.1',
                                           'Accept': 'application/json', 'Accept-Encoding': 'identity'}),
                       timeout=timeout)


def _publish(path, body):
    """Publish without overwriting an existing immutable object (single writer)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.partial-', delete=False) as stream:
        temp = Path(stream.name)
        try:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
            try:
                os.link(temp, path)
            except FileExistsError:
                if not path.is_file() or path.stat().st_size != len(body):
                    raise NoaaNrtError('Immutable cache size or file type differs')
                with path.open('rb') as existing:
                    identical = existing.read(len(body) + 1) == body
                if not identical:
                    raise NoaaNrtError('Immutable cache collision or changed bytes')
        finally:
            temp.unlink(missing_ok=True)


def _read_file(path, limit):
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
        raise NoaaNrtError('Cache entry must be a bounded regular file')
    with path.open('rb') as stream:
        body = stream.read(limit + 1)
    if len(body) > limit or len(body) != info.st_size:
        raise NoaaNrtError('Cache size changed or exceeds bounds')
    return body


def fetch_snapshot(cache_root=DEFAULT_CACHE_ROOT, *, product='primary', now_utc=None,
                   timeout_seconds=15, max_bytes=MAX_BYTES, transport=None):
    """One explicit fetch; record receipt after body completion, never on failure.

    ``now_utc`` and ``transport`` provide deterministic replay/test boundaries.
    No polling, retry, cache fallback, source fallback or automatic retention.
    Socket operations have finite timeouts; the body has a remaining-budget
    deadline. DNS/TLS/header setup is not a hard whole-call wall-clock guarantee.
    Injected transports must return promptly from read/read1; arbitrary Python
    transport code cannot be preempted by this service.
    Require Content-Length and refuse chunked/unknown framing: the chunk parser
    can otherwise wait inside one read for slowly delivered framing metadata.
    """
    if (type(product) is not str or product not in PRODUCTS
            or type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 60 or type(max_bytes) is not int
            or not 1 <= max_bytes <= MAX_BYTES):
        raise NoaaNrtError('Unsupported product or transfer bounds')
    root = _safe_root(cache_root)
    if now_utc is not None:
        _utc(now_utc)
    try:
        deadline = time.monotonic() + timeout_seconds
        with (transport or _transport)(PRODUCTS[product], timeout_seconds) as response:
            if response.status != 200 or response.geturl() != PRODUCTS[product]:
                raise NoaaNrtError('Unexpected HTTP status or source')
            length = response.headers.get('Content-Length')
            if (response.headers.get('Transfer-Encoding') is not None
                    or getattr(response, 'chunked', False) or type(length) is not str
                    or not length.isascii() or not length.isdigit()
                    or not 1 <= int(length) <= max_bytes):
                raise NoaaNrtError('Expected bounded Content-Length without transfer encoding')
            declared_size = int(length)
            parts, size = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise NoaaNrtError('Transfer exceeded deadline')
                # HTTPResponse.read(size) can wait for a full buffer under a
                # drip stream. read1 performs at most one underlying raw read.
                reader = getattr(response, 'read1', response.read)
                raw = getattr(getattr(response, 'fp', None), 'raw', None)
                sock = getattr(raw, '_sock', None)
                if sock is not None:
                    sock.settimeout(remaining)
                chunk = reader(min(65536, max_bytes + 1 - size))
                if time.monotonic() > deadline:
                    raise NoaaNrtError('Transfer exceeded deadline')
                size += len(chunk)
                if size > max_bytes:
                    raise NoaaNrtError('Response exceeds byte limit')
                if not chunk:
                    break
                parts.append(chunk)
            body = b''.join(parts)
            if len(body) != declared_size:
                raise NoaaNrtError('Response body differs from declared size')
            received = _utc(now_utc if now_utc is not None else _now()).isoformat()
            headers = {key: response.headers.get(key) for key in ('Date', 'Last-Modified')}
        _rows(body)  # Validate shape before publishing even raw cache bytes.
        digest = sha256(body).hexdigest()
        relative = 'receipts/' + uuid4().hex + '.json'
        provenance = dict(schema_version=1, product=product, url=PRODUCTS[product],
                          payload_sha256=digest, payload_bytes=len(body), received_utc=received,
                          publication_utc=None, http_date=headers['Date'],
                          http_last_modified=headers['Last-Modified'], receipt_path=relative)
        snapshot = Snapshot(body, provenance)
        _verify(snapshot)
        _publish(_inside(root, 'objects/' + digest + '.json'), body)
        _publish(_inside(root, relative), json.dumps(provenance, sort_keys=True, allow_nan=False).encode())
        return snapshot
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        raise NoaaNrtError('NOAA acquisition failed: ' + str(exc)) from exc


def load_snapshot(cache_root, receipt_path):
    """Offline read verifies bytes; it never changes receipt or observation age."""
    root = _safe_root(cache_root)
    try:
        manifest = _inside(root, receipt_path)
        record = _decode(_read_file(manifest, 8192))
        if not isinstance(record, dict) or record.get('receipt_path') != receipt_path:
            raise NoaaNrtError('Receipt identity differs')
        digest = record.get('payload_sha256')
        if type(digest) is not str or len(digest) != 64 or any(ch not in '0123456789abcdef' for ch in digest):
            raise NoaaNrtError('Invalid payload digest')
        path = _inside(root, 'objects/' + digest + '.json')
        snapshot = Snapshot(_read_file(path, MAX_BYTES), record)
        _verify(snapshot)
        return snapshot
    except (OSError, ValueError, TypeError) as exc:
        raise NoaaNrtError('Cached snapshot unavailable: ' + str(exc)) from exc


def assess_snapshot(snapshot, *, now_utc, max_age_seconds=300):
    """Structural diagnostics, never a certification of science-quality parity.

    The five-minute default is a local conservative diagnostic policy, not NOAA's
    latency guarantee. A time-tag age is not a publication or delivery latency.
    """
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 3600:
        raise NoaaNrtError('Freshness bound must be 1..3600 seconds')
    rows = _verify(snapshot)
    now, received = _utc(now_utc), _utc(snapshot.provenance['received_utc'])
    samples, satellites = {}, set()
    invalid, contaminated = 0, 0
    for row in rows:
        stamp = _utc(row['time_tag'], minute=True)
        samples.setdefault(stamp.value, {})[BANDS[row['energy']]] = row
        satellites.add(row['satellite'])
        invalid += row['flux'] is None or row['flux'] <= 0
        contaminated += row['electron_contaminaton']
    times = sorted(samples)
    first, last = pd.Timestamp(times[0], tz='UTC'), pd.Timestamp(times[-1], tz='UTC')
    gaps = [{'after':pd.Timestamp(a, tz='UTC').isoformat(),
             'before':pd.Timestamp(b, tz='UTC').isoformat(),
             'missing_minutes':int((b-a)//MINUTE_NS-1)}
            for a,b in zip(times,times[1:]) if b-a != MINUTE_NS]
    unpaired = sum(set(pair) != {'xrsa', 'xrsb'} for pair in samples.values())
    tail = [samples.get(last.value - offset*MINUTE_NS) for offset in range(120)]
    complete = len(satellites) == 1 and all(
        pair is not None and set(pair) == {'xrsa','xrsb'}
        and all(r['flux'] is not None and r['flux'] > 0 and not r['electron_contaminaton']
                for r in pair.values()) for pair in tail)
    age = (now-last).total_seconds()
    clock_error = now < received or now < last
    blockers = ['TIME_TAG_BIN_SEMANTICS_UNKNOWN', 'SCIENCE_QC_PARITY_UNKNOWN',
                'PUBLICATION_TIME_UNKNOWN', 'OPERATIONAL_VALIDATION_ABSENT']
    for condition, code in ((16 not in satellites or satellites != {16}, 'SATELLITE_OUTSIDE_V1_DOMAIN'),
                            (len(satellites)>1,'SATELLITE_SWITCH'), (invalid,'INVALID_FLUX'),
                            (contaminated,'ELECTRON_CONTAMINATION'), (unpaired,'MISSING_CHANNEL'),
                            (bool(gaps),'MISSING_MINUTES'), (not complete,'INCOMPLETE_120_MINUTE_CONTEXT'),
                            (age>max_age_seconds,'STALE_OBSERVATIONS'),
                            (clock_error,'CLOCK_ERROR'), (last>received,'OBSERVATION_AFTER_RECEIPT')):
        if condition:
            blockers.append(code)
    return dict(schema_version=1, source=dict(snapshot.provenance),
                observation=dict(first_time_tag=first.isoformat(),last_time_tag=last.isoformat(),
                                 row_count=len(rows),sample_count=len(samples),satellites=sorted(satellites),
                                 channels=sorted({BANDS[r['energy']] for r in rows}),
                                 flux_units='W/m2',time_tag_semantics='UNKNOWN'),
                freshness=dict(now_utc=now.isoformat(),age_seconds=age,max_age_seconds=max_age_seconds,
                               stale=age>max_age_seconds,clock_error=clock_error),
                continuity=dict(expected_cadence_seconds=60,missing_minutes=sum(g['missing_minutes'] for g in gaps),
                                gaps=gaps,unpaired_minutes=unpaired,contiguous=not gaps and not unpaired,
                                complete_context=bool(complete)),
                quality=dict(invalid_flux_rows=invalid,electron_contaminaton_true_rows=contaminated,
                             science_qc_mapping='UNKNOWN'),
                compatibility=dict(model_input_ready=False,blockers=blockers),model_input_ready=False)
