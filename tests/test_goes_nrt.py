"""Synthetic saved HTTP observations exercise ingestion, never scientific truth."""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from solar_flare_jepa.data import goes_nrt as nrt


NOW = '2026-10-18T08:02:00Z'


def payload(count=120, **changes):
    rows = []
    for stamp in pd.date_range('2026-10-18T06:00Z', periods=count, freq='min'):
        for band, flux in [('0.05-0.4nm', 1e-7), ('0.1-0.8nm', 1e-6)]:
            rows.append(dict(time_tag=stamp.isoformat().replace('+00:00', 'Z'), satellite=18,
                             energy=band, flux=flux, observed_flux=flux,
                             electron_correction=0.0, electron_contaminaton=False))
    if changes:
        rows[-1].update(changes)
    return json.dumps(rows).encode()


class Response:
    def __init__(self, body, url=None):
        from io import BytesIO
        self.body = BytesIO(body)
        self.url = url or nrt.PRODUCTS['primary']
        self.headers = {'Date': 'Sun, 18 Oct 2026 08:02:00 GMT',
                        'Last-Modified': 'Sun, 18 Oct 2026 08:01:00 GMT',
                        'Content-Length': str(len(body))}
        self.status = 200
    def read(self, size):
        return self.body.read(size)
    def geturl(self):
        return self.url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.body.close()


def save(tmp_path, body=None, received=NOW):
    return nrt.fetch_snapshot(tmp_path, now_utc=received,
                              transport=lambda url, timeout: Response(payload() if body is None else body))


def test_saved_observations_replay_exactly_without_network_or_new_receipt(tmp_path):
    saved = save(tmp_path)
    loaded = nrt.load_snapshot(tmp_path, saved.provenance['receipt_path'])
    assert loaded.payload == payload()
    assert loaded.provenance['payload_sha256'] == hashlib.sha256(payload()).hexdigest()
    report = nrt.assess_snapshot(loaded, now_utc=NOW)
    assert report['observation']['sample_count'] == 120
    assert report['freshness']['age_seconds'] == 180
    assert report['continuity']['complete_context']
    assert report['source']['publication_utc'] is None
    assert report['source']['received_utc'] == '2026-10-18T08:02:00+00:00'
    assert not report['model_input_ready']
    assert 'SCIENCE_QC_PARITY_UNKNOWN' in report['compatibility']['blockers']
    assert 'SATELLITE_OUTSIDE_V1_DOMAIN' in report['compatibility']['blockers']


def test_same_payload_retains_each_receipt_and_original_age(tmp_path):
    first = save(tmp_path)
    second = save(tmp_path, received='2026-10-18T08:03Z')
    assert first.provenance['receipt_path'] != second.provenance['receipt_path']
    assert len(list((tmp_path/'objects').iterdir())) == 1
    old = nrt.load_snapshot(tmp_path, first.provenance['receipt_path'])
    report = nrt.assess_snapshot(old, now_utc='2026-10-18T09:00Z')
    assert report['freshness']['stale']
    assert report['source']['received_utc'] == first.provenance['received_utc']


@pytest.mark.parametrize('mutation,blocker', [
    ({'flux': 0}, 'INVALID_FLUX'),
    ({'flux': None}, 'INVALID_FLUX'),
    ({'electron_contaminaton': True}, 'ELECTRON_CONTAMINATION'),
    ({'satellite': 19}, 'SATELLITE_SWITCH'),
])
def test_unsafe_observations_are_preserved_but_never_eligible(tmp_path, mutation, blocker):
    body = payload(**mutation)
    saved = save(tmp_path, body)
    assert saved.payload == body
    report = nrt.assess_snapshot(saved, now_utc=NOW)
    assert blocker in report['compatibility']['blockers']
    assert not report['continuity']['complete_context']
    assert not report['model_input_ready']


def test_gaps_and_missing_channels_are_never_filled(tmp_path):
    rows = json.loads(payload())
    del rows[60:62]
    del rows[-1]
    report = nrt.assess_snapshot(save(tmp_path, json.dumps(rows).encode()), now_utc=NOW)
    assert report['continuity']['missing_minutes'] == 1
    assert report['continuity']['unpaired_minutes'] == 1
    assert not report['continuity']['complete_context']


@pytest.mark.parametrize('body', [b'[]', b'{}', b'[{"x":1,"x":2}]', b'[NaN]', b'invalid'])
def test_malformed_json_is_not_published(tmp_path, body):
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path, body)
    assert not list(tmp_path.glob('receipts/*.json'))


@pytest.mark.parametrize('mutation', [{'time_tag':'2026-10-18T06:00:01Z'},
                                    {'time_tag':'2026-10-18T06:00:00'},
                                    {'energy':'1-8A'}, {'electron_contaminaton':0}])
def test_unknown_schema_and_time_are_rejected(tmp_path, mutation):
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path, payload(**mutation))


def test_duplicate_and_reordered_records_fail_closed(tmp_path):
    rows=json.loads(payload())
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path, json.dumps(rows+[rows[0]]).encode())
    rows[0],rows[2]=rows[2],rows[0]
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path, json.dumps(rows).encode())


def test_future_tags_and_clock_rollback_are_blockers(tmp_path):
    saved=save(tmp_path, received='2026-10-18T07:58Z')
    report=nrt.assess_snapshot(saved, now_utc='2026-10-18T07:57Z')
    assert report['freshness']['clock_error']
    assert 'OBSERVATION_AFTER_RECEIPT' in report['compatibility']['blockers']


def test_tampered_cache_provenance_and_traversal_are_rejected(tmp_path):
    saved=save(tmp_path)
    receipt=tmp_path/saved.provenance['receipt_path']
    record=json.loads(receipt.read_text())
    record['url']='https://example.org/data.json'
    receipt.write_text(json.dumps(record))
    with pytest.raises(nrt.NoaaNrtError):
        nrt.load_snapshot(tmp_path, saved.provenance['receipt_path'])
    with pytest.raises(nrt.NoaaNrtError):
        nrt.load_snapshot(tmp_path, '../outside.json')


def test_tampered_bytes_and_symlink_cache_are_rejected(tmp_path):
    saved=save(tmp_path/'cache')
    path=tmp_path/'cache'/'objects'/(saved.provenance['payload_sha256']+'.json')
    path.write_bytes(b'[]')
    with pytest.raises(nrt.NoaaNrtError):
        nrt.load_snapshot(tmp_path/'cache',saved.provenance['receipt_path'])
    (tmp_path/'alias').symlink_to(tmp_path/'cache',target_is_directory=True)
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path/'alias')


def test_bounds_redirect_and_failure_do_not_publish_or_fallback(tmp_path):
    with pytest.raises(nrt.NoaaNrtError):
        nrt.fetch_snapshot(tmp_path, now_utc=NOW, max_bytes=100,
                           transport=lambda url, timeout:Response(payload()))
    with pytest.raises(nrt.NoaaNrtError):
        nrt.fetch_snapshot(tmp_path, now_utc=NOW,
                           transport=lambda url, timeout:Response(payload(),'https://example.org'))
    def timeout(url, seconds):
        raise TimeoutError('timeout')
    with pytest.raises(nrt.NoaaNrtError):
        nrt.fetch_snapshot(tmp_path, now_utc=NOW, transport=timeout)
    assert not list(tmp_path.glob('receipts/*.json'))
    with pytest.raises(nrt.NoaaNrtError):
        nrt.fetch_snapshot(tmp_path, product='https://example.org', now_utc=NOW)


def test_corrupt_existing_object_size_is_checked_before_read(tmp_path,monkeypatch):
    saved=save(tmp_path)
    path=tmp_path/'objects'/(saved.provenance['payload_sha256']+'.json')
    path.write_bytes(b'x'*(nrt.MAX_BYTES+100))
    original=Path.read_bytes
    def bounded_read(selected):
        if selected==path:
            pytest.fail('Oversized corrupt cache object was read into memory')
        return original(selected)
    monkeypatch.setattr(Path,'read_bytes',bounded_read)
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path)


def test_extreme_json_number_fails_as_domain_error(tmp_path):
    rows=json.loads(payload())
    rows[0]['flux']=10**400
    with pytest.raises(nrt.NoaaNrtError):
        save(tmp_path,json.dumps(rows).encode())


@pytest.mark.parametrize('chunked',[False,True])
def test_body_deadline_interrupts_dripping_response(tmp_path,chunked):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread, Event
    import time
    from urllib.request import urlopen
    requested=Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_GET(self):
            requested.set()
            self.send_response(200)
            self.send_header('Transfer-Encoding','chunked') if chunked else self.send_header('Content-Length','20')
            self.end_headers()
            try:
                body=(b'0'*24+b'1\r\nx\r\n0\r\n\r\n') if chunked else b'x'*20
                for value in body:
                    self.wfile.write(bytes([value]))
                    self.wfile.flush()
                    time.sleep(.025)
            except (BrokenPipeError,ConnectionResetError):
                pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    def transport(url,timeout):
        response=urlopen('http://127.0.0.1:'+str(server.server_port),timeout=timeout)
        response.geturl=lambda:nrt.PRODUCTS['primary']
        return response
    try:
        start=time.monotonic()
        with pytest.raises(nrt.NoaaNrtError):
            nrt.fetch_snapshot(tmp_path,now_utc=NOW,timeout_seconds=.08,transport=transport)
        elapsed=time.monotonic()-start
        assert requested.is_set(), 'Transfer must reach the server to test its deadline'
        assert elapsed<.3, f'Body read exceeded its budget: {elapsed}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert not list(tmp_path.glob('receipts/*.json'))


@pytest.mark.parametrize('kind',['receipt','object'])
def test_fifo_cache_files_are_rejected_without_blocking(tmp_path,kind):
    import os
    import subprocess
    import sys
    saved=save(tmp_path)
    path=(tmp_path/saved.provenance['receipt_path'] if kind=='receipt' else
          tmp_path/'objects'/(saved.provenance['payload_sha256']+'.json'))
    path.unlink()
    os.mkfifo(path)
    program=('from solar_flare_jepa.data.goes_nrt import load_snapshot, NoaaNrtError\n'
             'import sys\n'
             'try: load_snapshot(sys.argv[1],sys.argv[2])\n'
             'except NoaaNrtError: print("REFUSED")\n')
    completed=subprocess.run([sys.executable,'-c',program,str(tmp_path),saved.provenance['receipt_path']],
                             capture_output=True,text=True,timeout=2,
                             env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')})
    assert completed.returncode==0,completed.stderr
    assert completed.stdout.strip()=='REFUSED'


@pytest.mark.parametrize('header,value',[('Content-Length',None),('Content-Length','-1'),
                                         ('Content-Length','9999999'),('Transfer-Encoding','chunked')])
def test_unbounded_or_chunked_http_framing_is_not_accepted(tmp_path,header,value):
    def transport(url,timeout):
        response=Response(payload())
        if value is None:
            response.headers.pop(header,None)
        else:
            response.headers[header]=value
        return response
    with pytest.raises(nrt.NoaaNrtError):
        nrt.fetch_snapshot(tmp_path,now_utc=NOW,transport=transport)
    assert not list(tmp_path.glob('receipts/*.json'))
