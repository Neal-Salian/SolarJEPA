"""Authorized GOES development restoration: plan, inventory, idempotent restore (offline, artificial bytes)."""
import hashlib
import importlib
import json
from pathlib import Path
from urllib.error import URLError

import pytest

PRODUCT = 'xrsf-l2-avg1m_science'
DIRECTORY = f'data/raw/noaa/history/goes16/{PRODUCT}/v2-2-1/'
BASE = f'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/{PRODUCT}/'


def api():
    return importlib.import_module('solar_flare_jepa.data.goes_restoration')


def acquisition():
    return importlib.import_module('solar_flare_jepa.data.goes_acquisition')


def payload(day):
    return b'CDF\x01' + f'artificial-{day}'.encode()


class Response:
    def __init__(self, body):
        self.body, self.headers = body, {'Content-Length': str(len(body))}

    def __enter__(self):
        import io
        self.stream = io.BytesIO(self.body)
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        return self.stream.read(size)


def serve(url, timeout):
    return Response(payload(url.rsplit('_d', 1)[1][:8]))


def no_network(*args, **kwargs):
    raise AssertionError('This operation must not use the network')


def make_selection(root, month='2024-07', days=2, name='history'):
    """A pinned, complete manifest whose files are absent (the restoration starting state)."""
    year, mon = month.split('-')
    files, rows = [], []
    for day in range(1, days + 1):
        stamp = f'{year}{mon}{day:02d}'
        filename = f'sci_xrsf-l2-avg1m_g16_d{stamp}_v2-2-1.nc'
        entry = dict(nominal_date=f'{year}-{mon}-{day:02d}', url=f'{BASE}{year}/{mon}/{filename}',
                     path=f'{DIRECTORY}{year}/{mon}/{filename}', max_bytes=128)
        files.append(entry)
        body = payload(stamp)
        rows.append(dict(entry, platform='GOES-16', product=PRODUCT, version='2-2-1', bytes=len(body),
                         sha256=hashlib.sha256(body).hexdigest(), acquired_utc='2026-10-08T00:00:00+00:00',
                         registered_utc='2026-10-08T00:00:01+00:00', lineage={'method': 'download_official_noaa'}))
    interval = dict(start=f'{year}-{mon}-01', end_exclusive=f'{year}-{mon}-{days + 1:02d}', basis='a priori')
    config = dict(schema_version=1, dataset_id=f'artificial-{name}', platform='GOES-16', product=PRODUCT,
                  version='2-2-1', selected_interval=interval, manifest_path=f'data/manifests/{name}.json',
                  max_total_bytes=days * 128, timeout_seconds=30, max_attempts=3, retry_delay_seconds=0,
                  files=files)
    config_path = root / f'configs/data/{name}.json'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config))
    manifest = dict(schema_version=1, dataset_id=config['dataset_id'], platform='GOES-16', product=PRODUCT,
                    version='2-2-1', selected_interval=interval, config_path=f'configs/data/{name}.json',
                    config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    max_total_bytes=config['max_total_bytes'], selected_file_count=days, complete=True,
                    total_bytes=sum(r['bytes'] for r in rows), files=rows)
    manifest_path = root / config['manifest_path']
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return f'data/manifests/{name}.json'


def make_plan(root, manifests, **changes):
    plan = dict(schema_version=1, plan_id='artificial-plan', purpose='test', authorization_basis=['test'],
                platform='GOES-16', product=PRODUCT, version='2-2-1',
                authorized_interval=dict(start='2024-05-01', end_exclusive='2024-09-01'),
                max_total_bytes=4096, disk_margin_bytes=0,
                manifests=[dict(path=m, role='development_exposed', v1_role='test') for m in manifests],
                forbidden=['outside interval'])
    plan.update(changes)
    path = root / 'configs/data/plan.json'
    path.write_text(json.dumps(plan))
    return path


# ------------------------------------------------------------------ plan / authorization


def test_plan_parses_manifests_and_lists_every_pinned_identity(tmp_path):
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path, days=3)]), tmp_path)
    assert [r['nominal_date'] for r in plan['files']] == ['2024-07-01', '2024-07-02', '2024-07-03']
    assert plan['required_bytes'] == sum(r['bytes'] for r in plan['files'])
    assert {r['role'] for r in plan['files']} == {'development_exposed'}


@pytest.mark.parametrize('month', ['2025-01', '2024-04', '2024-09'])
def test_identities_outside_the_authorized_interval_are_rejected_before_any_access(tmp_path, month, monkeypatch):
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    with pytest.raises(api().UnauthorizedSelection, match='authorized interval'):
        api().load_plan(make_plan(tmp_path, [make_selection(tmp_path, month=month)]), tmp_path)


@pytest.mark.parametrize('change', [dict(version='2-2-0'), dict(product='xrsf-l2-flx1s_science'),
                                    dict(platform='GOES-18')])
def test_plan_with_other_product_identity_is_rejected(tmp_path, change):
    with pytest.raises(api().UnauthorizedSelection, match='product'):
        api().load_plan(make_plan(tmp_path, [make_selection(tmp_path)], **change), tmp_path)


def test_manifest_with_wrong_product_version_is_rejected(tmp_path):
    name = make_selection(tmp_path)
    path = tmp_path / name
    value = json.loads(path.read_text())
    value['files'][0]['version'] = '2-2-0'
    path.write_text(json.dumps(value, indent=2) + '\n')
    with pytest.raises(ValueError):
        api().load_plan(make_plan(tmp_path, [name]), tmp_path)


@pytest.mark.parametrize('defect', ['role', 'duplicate', 'outside_manifests', 'budget', 'incomplete'])
def test_malformed_or_unauthorized_plans_fail_closed(tmp_path, defect):
    name = make_selection(tmp_path)
    changes = {}
    manifests = [name]
    if defect == 'role':
        plan = make_plan(tmp_path, manifests)
        value = json.loads(plan.read_text())
        value['manifests'][0]['role'] = 'sealed_test'
        plan.write_text(json.dumps(value))
    else:
        if defect == 'duplicate':
            manifests = [name, name]
        elif defect == 'outside_manifests':
            manifests = ['configs/data/history.json']
        elif defect == 'budget':
            changes = dict(max_total_bytes=10)
        elif defect == 'incomplete':
            path = tmp_path / name
            value = json.loads(path.read_text())
            value['complete'] = False
            path.write_text(json.dumps(value, indent=2) + '\n')
        plan = make_plan(tmp_path, manifests, **changes)
    with pytest.raises(ValueError):
        api().load_plan(plan, tmp_path)


def test_split_boundaries_must_stay_inside_the_authorized_interval(tmp_path):
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path)]), tmp_path)
    good = [dict(name='train', start_utc='2024-05-01T00:00:00Z', end_utc='2024-07-22T00:00:00Z'),
            dict(name='validation', start_utc='2024-07-22T00:00:00Z', end_utc='2024-08-01T00:00:00Z'),
            dict(name='test', start_utc='2024-08-01T00:00:00Z', end_utc='2024-09-01T00:00:00Z')]
    assert api().check_split_authorization(good, plan) == dict(
        train='development_exposed', validation='development_exposed', test='development_exposed')
    beyond = [dict(s) for s in good]
    beyond[-1]['end_utc'] = '2024-09-02T00:00:00Z'
    with pytest.raises(api().UnauthorizedSelection, match='authorized interval'):
        api().check_split_authorization(beyond, plan)


# ------------------------------------------------------------------ inventory


def test_inventory_classifies_missing_verified_mismatch_partial_and_unexpected(tmp_path, monkeypatch):
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    name = make_selection(tmp_path, days=4)
    plan = api().load_plan(make_plan(tmp_path, [name]), tmp_path)
    rows = plan['files']
    (tmp_path / rows[0]['path']).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rows[0]['path']).write_bytes(payload('20240701'))                    # verified
    (tmp_path / rows[1]['path']).write_bytes(b'CDF\x01' + b'y' * 19)                 # same size, other hash
    (tmp_path / rows[2]['path']).write_bytes(b'CDF\x01short')                        # truncated
    stale = tmp_path / rows[0]['path'].replace('.nc', '.nc.abc.part')
    stale.write_bytes(b'CDF')
    (tmp_path / DIRECTORY / '2024/07/notes.txt').write_text('unexpected')
    before = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    report = api().inventory(plan, tmp_path)
    assert [r['status'] for r in report['files']] == ['present_verified', 'mismatch', 'mismatch', 'missing']
    assert report['counts'] == dict(required=4, present_verified=1, missing=1, mismatch=2, partial=1, unexpected=1)
    assert report['partial'] == [stale.relative_to(tmp_path).as_posix()]
    assert report['unexpected'] == [f'{DIRECTORY}2024/07/notes.txt']
    assert {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before  # read-only


# ------------------------------------------------------------------ restore


def test_restore_downloads_only_missing_files_and_is_idempotent(tmp_path, monkeypatch):
    name = make_selection(tmp_path, days=3)
    plan = api().load_plan(make_plan(tmp_path, [name]), tmp_path)
    first = plan['files'][0]
    (tmp_path / first['path']).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / first['path']).write_bytes(payload('20240701'))   # valid copy is reused, not re-downloaded
    requested = []
    monkeypatch.setattr(acquisition(), 'open_history_url', lambda url, timeout: (requested.append(url), serve(url, timeout))[1])
    manifest_before = (tmp_path / name).read_bytes()
    result = api().restore(plan, tmp_path)
    assert [u.rsplit('/', 1)[1] for u in requested] == [Path(r['path']).name for r in plan['files'][1:]]
    assert result['after']['counts']['present_verified'] == 3 and result['after']['counts']['missing'] == 0
    assert result['stats']['downloaded_files'] == 2 and result['stats']['downloaded_bytes'] == sum(
        r['bytes'] for r in plan['files'][1:])
    assert (tmp_path / name).read_bytes() == manifest_before   # tracked manifest untouched
    inode = (tmp_path / first['path']).stat().st_ino
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    again = api().restore(plan, tmp_path)
    assert again['stats']['attempts'] == 0 and again['after'] == result['after']
    assert (tmp_path / first['path']).stat().st_ino == inode    # never rewritten
    assert not list(tmp_path.rglob('*.part'))


def test_restore_refuses_mismatched_files_before_any_network_access(tmp_path, monkeypatch):
    name = make_selection(tmp_path, days=2)
    plan = api().load_plan(make_plan(tmp_path, [name]), tmp_path)
    target = tmp_path / plan['files'][0]['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'CDF\x01' + b'z' * 15)
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    with pytest.raises(api().IntegrityError, match='mismatch'):
        api().restore(plan, tmp_path)
    assert target.read_bytes() == b'CDF\x01' + b'z' * 15   # never overwritten


def test_wrong_hash_download_is_never_installed(tmp_path, monkeypatch):
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path, days=1)]), tmp_path)
    monkeypatch.setattr(acquisition(), 'open_history_url', lambda url, timeout: Response(b'CDF\x01' + b'o' * 19))
    with pytest.raises(ValueError, match='SHA-256'):
        api().restore(plan, tmp_path)
    assert not (tmp_path / plan['files'][0]['path']).exists()
    assert not list(tmp_path.rglob('*.part'))


def test_transient_failures_are_retried_counted_and_partial_download_resumes(tmp_path, monkeypatch):
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path, days=2)]), tmp_path)
    calls = []
    def outage_on_second(url, timeout):
        calls.append(url)
        if 'd20240702' in url:
            raise URLError('outage')
        return serve(url, timeout)
    monkeypatch.setattr(acquisition(), 'open_history_url', outage_on_second)
    with pytest.raises(URLError):
        api().restore(plan, tmp_path)
    partial = api().inventory(plan, tmp_path)
    assert partial['counts']['present_verified'] == 1 and partial['counts']['missing'] == 1
    monkeypatch.setattr(acquisition(), 'open_history_url', outage_on_second)
    stats = {}
    with pytest.raises(URLError):
        api().restore(plan, tmp_path, stats=stats)   # review F4: counters survive the failure
    assert stats['attempts'] == 3 and stats['retries'] == 2 and stats['downloaded_files'] == 0
    assert [f['attempt'] for f in stats['failures']] == [1, 2, 3]
    monkeypatch.setattr(acquisition(), 'open_history_url', serve)
    result = api().restore(plan, tmp_path)
    assert result['before']['counts']['missing'] == 1 and result['after']['counts']['present_verified'] == 2
    assert result['stats']['downloaded_files'] == 1 and result['stats']['retries'] == 0


def test_restore_stops_when_disk_space_is_insufficient(tmp_path, monkeypatch):
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path)], disk_margin_bytes=10**6), tmp_path)
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    with pytest.raises(api().InsufficientSpace, match='requires'):
        api().restore(plan, tmp_path, free_bytes=lambda path: 10)


def listing_html(names, size='1K'):
    rows = ''.join(f'<tr><td><a href="{n}">{n}</a></td><td align="right">2025-12-05 18:43  </td>'
                   f'<td align="right">{size}</td></tr>\n' for n in names)
    return f'<html><body><table>{rows}</table></body></html>'


def test_official_listing_comparison_detects_missing_extra_and_version_changes(tmp_path):
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path, days=2)]), tmp_path)
    names = [Path(r['path']).name for r in plan['files']]
    assert [r['name'] for r in api().parse_listing(listing_html(names))] == names
    good = api().compare_official_listing(plan, lambda url: listing_html(names))
    assert good['consistent'] is True and good['months']['2024-07']['last_modified_dates'] == ['2025-12-05']
    extra = names + [names[0].replace('d20240701', 'd20240703')]
    for listed, field in ((names[:1], 'missing_from_listing'), (extra, 'listed_not_pinned'),
                          ([n.replace('v2-2-1', 'v2-2-2') for n in names], 'listed_not_pinned')):
        result = api().compare_official_listing(plan, lambda url, listed=listed: listing_html(listed))
        assert result['consistent'] is False and result['months']['2024-07'][field]
    assert api().compare_official_listing(plan, lambda url: listing_html(names, '9K'))['consistent'] is False


def test_manifest_changed_after_plan_load_is_refused_before_network(tmp_path, monkeypatch):
    # Review F5: tracked manifests are re-checked against the plan before any acquisition.
    name = make_selection(tmp_path)
    plan = api().load_plan(make_plan(tmp_path, [name]), tmp_path)
    path = tmp_path / name
    path.write_text(path.read_text() + '\n')
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    with pytest.raises(api().IntegrityError, match='since the plan was loaded'):
        api().restore(plan, tmp_path)


@pytest.mark.parametrize('dangling', [False, True])
def test_symlink_at_a_pinned_path_is_classified_as_mismatch_and_never_followed(tmp_path, monkeypatch, dangling):
    # Review F6: inventory classifies instead of crashing; restore then refuses before network.
    plan = api().load_plan(make_plan(tmp_path, [make_selection(tmp_path, days=1)]), tmp_path)
    target = tmp_path / plan['files'][0]['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    source = tmp_path / 'elsewhere.nc'
    if not dangling:
        source.write_bytes(payload('20240701'))
    target.symlink_to(source)
    report = api().inventory(plan, tmp_path)
    assert report['files'][0]['status'] == 'mismatch' and 'Symlink' in report['files'][0]['reason']
    monkeypatch.setattr(acquisition(), 'open_history_url', no_network)
    with pytest.raises(api().IntegrityError):
        api().restore(plan, tmp_path)
    assert target.is_symlink()
