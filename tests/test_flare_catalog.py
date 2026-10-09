"""Synthetic offline catalog fixtures; these do not validate solar observations."""
import csv
from dataclasses import FrozenInstanceError
import hashlib
import importlib
import importlib.util
import io
import json

import pytest


FIELDS = ('time,start_time,end_time,flare_id,xrsb_irrad,flare_class,xrsb_irrad_source,'
          'background_irrad,integrated_irrad_peak,integrated_irrad_end,'
          'flare_loc_swpc_hgs_lon,flare_loc_swpc_hgs_lat,flare_loc_swpc_source,'
          'flare_loc_xrs_hgs_lon,flare_loc_xrs_hgs_lat,flare_loc_xrs_hpc_x,'
          'flare_loc_xrs_hpc_y,flare_loc_xrs_source,sequential_flare_num,'
          'event_id_swpc,peak_saturated,active_region').split(',')
BASE = ('https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/'
        'goes/multi/l2/data/xrsf-l2-flrpt_science/csv/')
CATALOG_NAME = 'sci_xrsf-l2-flrpt_geo_y2025_v1-0-1.csv'
META_NAME = 'sci_xrsf-l2-flrpt_geo_metadata.json'


def api():
    name = 'solar_flare_jepa.data.flare_catalog'
    assert importlib.util.find_spec(name) is not None, 'Flare catalog is not implemented'
    return importlib.import_module(name)


def row(**changes):
    result = dict.fromkeys(FIELDS, '')
    result.update(time='2025-01-01 00:05:00', start_time='2025-01-01 00:00:00',
                  end_time='2025-01-01 00:10:00', flare_id='202501010000',
                  xrsb_irrad='1.136e-05', flare_class='M1.1',
                  xrsb_irrad_source='GOES-16', sequential_flare_num='1', peak_saturated='0')
    result.update(changes)
    return result


def payload(*rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def fixture(tmp_path, *rows):
    path = tmp_path / 'catalog.csv'
    path.write_bytes(payload(*rows))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_parse_preserves_utc_provenance_and_truncated_class(tmp_path):
    path, digest = fixture(tmp_path, row())
    event, = api().parse_flare_report(path, 'synthetic-v1', digest)
    assert (event.start_ns, event.peak_ns, event.end_ns) == (
        1735689600000000000, 1735689900000000000, 1735690200000000000)
    assert (event.catalog_id, event.catalog_sha256, event.event_id, event.source) == (
        'synthetic-v1', digest, '202501010000', 'GOES-16')
    assert event.flare_class == 'M1.1' and event.peak_flux == 1.136e-5
    assert event.original_row == 2 and event.flags == ()
    with pytest.raises(FrozenInstanceError):
        event.peak_flux = 0.0


def test_missing_end_and_sequential_saturation_remain_explicit(tmp_path):
    path, digest = fixture(tmp_path, row(end_time='', sequential_flare_num='3', peak_saturated='1'))
    event, = api().parse_flare_report(path, 'synthetic-v1', digest)
    assert event.end_ns is None
    assert set(event.flags) == {'missing_end', 'sequential_flare', 'peak_saturated'}
    assert event.sequential_number == 3 and event.peak_saturated


def test_exact_duplicate_deduplicated_but_conflict_rejected(tmp_path):
    path, digest = fixture(tmp_path, row(), row())
    event, = api().parse_flare_report(path, 'synthetic-v1', digest)
    assert event.original_row == 2 and 'exact_duplicate' in event.flags
    path, digest = fixture(tmp_path, row(), row(flare_class='M1.2'))
    with pytest.raises(ValueError, match='Conflicting'):
        api().parse_flare_report(path, 'synthetic-v1', digest)


def test_cross_midnight_times_are_explicit_not_guessed(tmp_path):
    path, digest = fixture(tmp_path, row(start_time='2024-12-31 23:59:00', flare_id='202412312359'))
    event, = api().parse_flare_report(path, 'synthetic-v1', digest)
    assert event.start_ns == 1735689540000000000


@pytest.mark.parametrize('changes', [
    {'time': '2025-01-01 00:05:01'}, {'time': '2025-01-01T00:05:00'},
    {'time': ''}, {'start_time': '2025-01-01 00:06:00'},
    {'end_time': '2025-01-01 00:04:00'}, {'flare_id': '202501010001'},
    {'xrsb_irrad': 'nan'}, {'xrsb_irrad': '-1'}, {'flare_class': 'Q1.0'},
    {'flare_class': 'M0.0'}, {'xrsb_irrad_source': 'mystery'},
    {'sequential_flare_num': '1.5'}, {'sequential_flare_num': '0'},
    {'peak_saturated': '2'},
])
def test_invalid_scientific_fields_fail_closed(tmp_path, changes):
    path, digest = fixture(tmp_path, row(**changes))
    with pytest.raises(ValueError):
        api().parse_flare_report(path, 'synthetic-v1', digest)


def test_hash_mismatch_rejects_label_provenance(tmp_path):
    path, _ = fixture(tmp_path, row())
    with pytest.raises(ValueError, match='SHA-256'):
        api().parse_flare_report(path, 'synthetic-v1', '0' * 64)


def test_missing_duplicate_or_unknown_header_rejected(tmp_path):
    for header in ['time,start_time', ','.join(FIELDS + ['time']), ','.join(FIELDS + ['new_column'])]:
        path = tmp_path / 'bad.csv'
        path.write_text(header + '\n')
        with pytest.raises(ValueError):
            api().parse_flare_report(path, 'synthetic-v1', hashlib.sha256(path.read_bytes()).hexdigest())


def test_zero_events_valid_header_and_deterministic_order(tmp_path):
    path, digest = fixture(tmp_path)
    assert api().parse_flare_report(path, 'synthetic-v1', digest) == ()
    later = row(time='2025-01-01 01:05:00', start_time='2025-01-01 01:00:00',
                end_time='2025-01-01 01:10:00', flare_id='202501010100')
    path, digest = fixture(tmp_path, later, row())
    events = api().parse_flare_report(path, 'synthetic-v1', digest)
    assert [e.original_row for e in events] == [3, 2]


@pytest.mark.parametrize('value,want', [('C1.0', 1e-6), ('M2.5', 2.5e-5), ('X11.2', 11.2e-4)])
def test_class_threshold_uses_catalog_magnitude(value, want):
    assert api().class_threshold(value) == pytest.approx(want)


@pytest.mark.parametrize('value', ['C10.0', 'M1', 'M1.00', 'C0.9', 'X' + '9' * 400 + '.0'])
def test_class_threshold_rejects_malformed_or_nonfinite_magnitudes(value):
    with pytest.raises(ValueError):
        api().class_threshold(value)


class Response(io.BytesIO):
    def __init__(self, body):
        super().__init__(body)
        self.headers = {'Content-Length': str(len(body))}


def config(tmp_path):
    content = payload(row())
    metadata = json.dumps({'global_attributes': {'flrpt_algorithm_version': '1-0-1',
                           'title': 'L2 XRS flare report', 'time_coverage_resolution': 'PT1M'},
                           'variable_attributes': {'time': {}, 'start_time': {}, 'end_time': {},
                           'flare_class': {}, 'xrsb_irrad_source': {},
                           'xrsb_irrad': {'units': 'W/m2'}}}).encode()
    bodies = {'catalog': content, 'metadata': metadata}
    resources = []
    for role, name in [('catalog', CATALOG_NAME), ('metadata', META_NAME)]:
        data = bodies[role]
        resources.append(dict(role=role, url=BASE + name,
                              path='data/raw/external/goes_flare_catalog_2025/' + name,
                              max_bytes=1024**2, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    value = dict(schema_version=1, catalog_id='noaa-ncei-science-flrpt-2025-v1-0-1',
                 product='xrsf-l2-flrpt_science', version='1-0-1', year=2025,
                 manifest_path='data/manifests/flare_catalog_2025.json',
                 timeout_seconds=30, resources=resources)
    path = tmp_path / 'configs/data/flare_catalog_2025.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value))
    return path, value, bodies


def test_acquisition_verifies_and_resumes_without_overwriting(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    monkeypatch.setattr(module, 'open_history_url', lambda url, timeout: Response(
        bodies['catalog' if url.endswith('.csv') else 'metadata']))
    ledger = module.acquire_catalog(path, tmp_path)
    assert ledger['complete'] and ledger['event_count'] == 1
    manifest = tmp_path / spec['manifest_path']
    original = manifest.read_bytes()
    def no_network(*args):
        raise AssertionError('Verified local catalog must not download')
    monkeypatch.setattr(module, 'open_history_url', no_network)
    assert module.acquire_catalog(path, tmp_path) == ledger
    assert manifest.read_bytes() == original
    resources = module.verify_catalog(manifest, tmp_path)
    assert set(resources) == {'catalog', 'metadata'}
    resources['catalog'].write_text('corrupt')
    with pytest.raises(ValueError):
        module.acquire_catalog(path, tmp_path)
    assert resources['catalog'].read_text() == 'corrupt'


@pytest.mark.parametrize('change', ['host', 'version', 'path_escape', 'unbounded', 'hash'])
def test_acquisition_rejects_bad_identity_before_network(tmp_path, monkeypatch, change):
    module = api()
    path, spec, bodies = config(tmp_path)
    if change == 'host':
        spec['resources'][0]['url'] = 'https://example.com/' + CATALOG_NAME
    elif change == 'version':
        spec['version'] = '9-0-0'
    elif change == 'path_escape':
        spec['resources'][0]['path'] = '../escaped.csv'
    elif change == 'unbounded':
        spec['resources'][0]['max_bytes'] = 10**10
    else:
        spec['resources'][0]['sha256'] = 'invalid'
    path.write_text(json.dumps(spec))
    monkeypatch.setattr(module, 'open_history_url', lambda *args: pytest.fail('Unexpected network'))
    with pytest.raises(ValueError):
        module.acquire_catalog(path, tmp_path)


def test_changed_response_bytes_never_installed(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    monkeypatch.setattr(module, 'open_history_url', lambda *args: Response(b'wrong'))
    with pytest.raises(ValueError):
        module.acquire_catalog(path, tmp_path)
    assert not (tmp_path / spec['resources'][0]['path']).exists()


def repin(path, spec, bodies, role, content):
    bodies[role] = content
    entry = next(e for e in spec['resources'] if e['role'] == role)
    entry.update(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    path.write_text(json.dumps(spec))


def test_annual_product_rejects_event_peak_outside_named_year(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    content = payload(row(time='2024-12-31 23:55:00', start_time='2024-12-31 23:50:00',
                          end_time='2025-01-01 00:00:00', flare_id='202412312350'))
    repin(path, spec, bodies, 'catalog', content)
    monkeypatch.setattr(module, 'open_history_url', lambda url, timeout: Response(
        bodies['catalog' if url.endswith('.csv') else 'metadata']))
    with pytest.raises(ValueError, match='year'):
        module.acquire_catalog(path, tmp_path)
    assert not (tmp_path / spec['manifest_path']).exists()


def test_metadata_cannot_change_physical_irradiance_units(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    metadata = json.loads(bodies['metadata'])
    metadata['variable_attributes']['xrsb_irrad']['units'] = 'counts'
    repin(path, spec, bodies, 'metadata', json.dumps(metadata).encode())
    monkeypatch.setattr(module, 'open_history_url', lambda url, timeout: Response(
        bodies['catalog' if url.endswith('.csv') else 'metadata']))
    with pytest.raises(ValueError):
        module.acquire_catalog(path, tmp_path)


def test_ledger_cannot_promote_unknown_catalog_completeness(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    monkeypatch.setattr(module, 'open_history_url', lambda url, timeout: Response(
        bodies['catalog' if url.endswith('.csv') else 'metadata']))
    ledger = module.acquire_catalog(path, tmp_path)
    ledger['scientific_completeness'] = 'VERIFIED'
    manifest = tmp_path / spec['manifest_path']
    manifest.write_text(json.dumps(ledger))
    with pytest.raises(ValueError):
        module.verify_catalog(manifest, tmp_path)


def test_transfer_without_length_header_still_checks_hash(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    def response(url, timeout):
        result = Response(bodies['catalog' if url.endswith('.csv') else 'metadata'])
        result.headers.clear()
        return result
    monkeypatch.setattr(module, 'open_history_url', response)
    assert module.acquire_catalog(path, tmp_path)['event_count'] == 1


def test_raw_symlink_identity_rejected(tmp_path, monkeypatch):
    module = api()
    path, spec, bodies = config(tmp_path)
    target = tmp_path / spec['resources'][0]['path']
    target.parent.mkdir(parents=True)
    other = tmp_path / 'other.csv'
    other.write_bytes(bodies['catalog'])
    target.symlink_to(other)
    monkeypatch.setattr(module, 'open_history_url', lambda *args: pytest.fail('Unexpected network'))
    with pytest.raises(ValueError):
        module.acquire_catalog(path, tmp_path)
    assert target.is_symlink()


def cloned_ledger(tmp_path,monkeypatch):
    module=api()
    source=tmp_path/'source'
    source.mkdir()
    config_path,spec,bodies=config(source)
    monkeypatch.setattr(module,'open_history_url',lambda url,timeout:Response(bodies['catalog' if url.endswith('.csv') else 'metadata']))
    module.acquire_catalog(config_path,source)
    clone=tmp_path/'clone'
    for rel in ('configs/data/flare_catalog_2025.json',spec['manifest_path']):
        target=clone/rel;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((source/rel).read_bytes())
    return module,source,clone,spec,bodies


@pytest.mark.parametrize('missing',['catalog','metadata','both'])
def test_committed_ledger_restores_missing_pinned_resources_without_rewriting(tmp_path,monkeypatch,missing):
    module,source,clone,spec,bodies=cloned_ledger(tmp_path,monkeypatch)
    for entry in spec['resources']:
        if missing not in (entry['role'],'both'):
            target=clone/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((source/entry['path']).read_bytes())
    manifest=clone/spec['manifest_path'];before=manifest.read_bytes()
    with pytest.raises(ValueError):module.verify_catalog(manifest,clone)
    requested=[]
    def download(url,timeout):
        requested.append(url)
        return Response(bodies['catalog' if url.endswith('.csv') else 'metadata'])
    monkeypatch.setattr(module,'open_history_url',download)
    result=module.acquire_catalog('configs/data/flare_catalog_2025.json',clone)
    assert manifest.read_bytes()==before
    assert result==json.loads(before)
    assert set(requested)=={entry['url'] for entry in spec['resources'] if missing in (entry['role'],'both')}
    assert set(module.verify_catalog(manifest,clone))=={'catalog','metadata'}


def test_missing_resource_recovery_rejects_existing_corruption_before_network(tmp_path,monkeypatch):
    module,source,clone,spec,bodies=cloned_ledger(tmp_path,monkeypatch)
    metadata=spec['resources'][1]
    target=clone/metadata['path'];target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(b'corrupt')
    monkeypatch.setattr(module,'open_history_url',lambda *args:pytest.fail('Unexpected network'))
    with pytest.raises(ValueError):module.acquire_catalog('configs/data/flare_catalog_2025.json',clone)
    assert not (clone/spec['resources'][0]['path']).exists()


def test_missing_resource_recovery_never_accepts_changed_remote_snapshot(tmp_path,monkeypatch):
    module,source,clone,spec,bodies=cloned_ledger(tmp_path,monkeypatch)
    manifest=clone/spec['manifest_path'];before=manifest.read_bytes()
    monkeypatch.setattr(module,'open_history_url',lambda *args:Response(b'changed'))
    with pytest.raises(ValueError):module.acquire_catalog('configs/data/flare_catalog_2025.json',clone)
    assert manifest.read_bytes()==before
    assert not (clone/spec['resources'][0]['path']).exists()
