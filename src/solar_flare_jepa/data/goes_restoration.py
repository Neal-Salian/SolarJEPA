"""Authorized, idempotent restoration and integrity inventory of pinned GOES development data.

Composes, and does not replace, ``goes_acquisition`` (bounded, pinned, no-replace
downloads from the recorded official NOAA URLs). Adds:

* an explicit authorization plan: only listed manifests, only one platform,
  product and version, only nominal dates inside an authorized interval;
* a read-only inventory (present_verified / missing / mismatch, plus stray
  partial downloads and unexpected files under the managed raw tree);
* a restore step that refuses mismatched files before any network access,
  checks disk space and leaves tracked manifests byte-identical.

A matching manifest hash proves only that bytes equal the repository's pin.
Native product identity is checked separately (``native_identity``).
"""

from pathlib import Path, PurePosixPath
import re
import shutil

from . import goes_acquisition as acquisition
from .download import sha256_file

MANAGED_ROOT = f'data/raw/noaa/history/goes16/{acquisition.PRODUCT}/'
ROLES = ('development_exposed',)
COUNT_KEYS = ('required', 'present_verified', 'missing', 'mismatch', 'partial', 'unexpected')


class UnauthorizedSelection(ValueError):
    """A requested identity lies outside the explicit authorization plan."""


class IntegrityError(ValueError):
    """Local bytes contradict a pinned identity; nothing is replaced."""


class InsufficientSpace(OSError):
    """Free disk space is below the restoration requirement."""


def _interval(value):
    start, end = acquisition._date(value['start']), acquisition._date(value['end_exclusive'])
    if start >= end:
        raise ValueError('Authorized interval must be ordered')
    return start, end


def _inside(day, interval):
    return interval[0] <= day < interval[1]


def load_plan(plan_path, root):
    """Validate the plan and every listed manifest; return the authorized pinned identities."""
    root = Path(root).resolve()
    plan_path = Path(plan_path)
    plan_path = plan_path if plan_path.is_absolute() else root / plan_path
    plan = acquisition._json(acquisition._path(plan_path.relative_to(root).as_posix(), root))
    try:
        plan_id = plan['plan_id']
        if not isinstance(plan_id, str) or not plan_id:
            raise ValueError('Plan requires a nonempty plan_id')
        if type(plan['schema_version']) is not int or plan['schema_version'] != 1:
            raise ValueError('Unsupported restoration plan schema')
        if (plan['platform'], plan['product'], plan['version']) != (
                acquisition.PLATFORM, acquisition.PRODUCT, acquisition.VERSION):
            raise UnauthorizedSelection('Plan platform/product/version differs from the supported product identity')
        interval = _interval(plan['authorized_interval'])
        budget, margin = plan['max_total_bytes'], plan['disk_margin_bytes']
        if type(budget) is not int or budget <= 0 or type(margin) is not int or margin < 0:
            raise ValueError('Plan byte budget/margin must be explicit nonnegative integers')
        entries = plan['manifests']
        if not isinstance(entries, list) or not entries:
            raise ValueError('Plan must list at least one manifest')
        paths = [entry['path'] for entry in entries]
        if len(set(paths)) != len(paths):
            raise ValueError('Duplicate manifest in plan')
        files, manifests = [], []
        for entry in entries:
            if entry['role'] not in ROLES:
                raise UnauthorizedSelection(f"Role {entry['role']!r} is not authorized for development restoration")
            relative = entry['path']
            if not relative.startswith('data/manifests/') or not relative.endswith('.json'):
                raise ValueError('Plan manifests must be JSON under data/manifests')
            manifest_path = acquisition._path(relative, root)
            inventory = acquisition._json(manifest_path)
            if (inventory['platform'], inventory['product'], inventory['version']) != (
                    plan['platform'], plan['product'], plan['version']):
                raise UnauthorizedSelection('Manifest platform/product/version differs from the plan')
            selected = _interval(inventory['selected_interval'])
            if not (interval[0] <= selected[0] and selected[1] <= interval[1]):
                raise UnauthorizedSelection(f'{relative}: selection lies outside the authorized interval')
            spec, config_relative, digest, output = acquisition._config(inventory['config_path'], root)
            if output != manifest_path:
                raise ValueError('Manifest location differs from its pinned config')
            acquisition._ledger(inventory, spec, config_relative, digest)
            if inventory['complete'] is not True:
                raise ValueError(f'{relative}: only complete pinned manifests can be restored')
            for row in inventory['files']:
                day = acquisition._date(row['nominal_date'])
                if not _inside(day, interval):
                    raise UnauthorizedSelection(f"{row['path']}: nominal date outside the authorized interval")
                if row != dict(row, **acquisition._canonical(day)) or not row['path'].startswith(MANAGED_ROOT):
                    raise UnauthorizedSelection(f"{row['path']}: not the official product identity for its date")
                files.append(dict(path=row['path'], url=row['url'], nominal_date=row['nominal_date'],
                                  bytes=row['bytes'], sha256=row['sha256'], max_bytes=row['max_bytes'],
                                  manifest=relative, role=entry['role'], lineage=row['lineage']['method']))
            manifests.append(dict(path=relative, config_path=config_relative, role=entry['role'],
                                  sha256=sha256_file(manifest_path), file_count=len(inventory['files'])))
        if len({f['path'] for f in files}) != len(files):
            raise ValueError('Duplicate file identity across manifests')
        required = sum(f['bytes'] for f in files)
        if required > budget:
            raise ValueError(f'Pinned selection ({required} B) exceeds the plan budget ({budget} B)')
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Malformed restoration plan or manifest') from error
    return dict(plan_id=plan_id, path=plan_path.relative_to(root).as_posix(),
                sha256=sha256_file(plan_path), interval=interval, max_total_bytes=budget,
                disk_margin_bytes=margin, manifests=manifests, files=files, required_bytes=required)


def check_split_authorization(splits, plan):
    """Every split boundary must lie inside the authorized interval; returns each split's data role."""
    from solar_flare_jepa.experiments.config import utc_ns
    lower, upper = (utc_ns(f'{day.isoformat()}T00:00:00Z') for day in plan['interval'])
    roles = {}
    for split in splits:
        start, end = utc_ns(split['start_utc']), utc_ns(split['end_utc'])
        if not lower <= start < end <= upper:
            raise UnauthorizedSelection(f"Split {split['name']!r} lies outside the authorized interval")
        roles[split['name']] = 'development_exposed'
    return roles


def _status(root, row):
    try:
        target = acquisition._path(row['path'], root)
    except ValueError as error:  # e.g. a symlink at or above the pinned path: never followed or adopted
        return 'mismatch', str(error)
    if not target.exists():
        return 'missing', None
    try:
        acquisition._check(target, row)
    except ValueError as error:
        return 'mismatch', str(error)
    return 'present_verified', None


def inventory(plan, root):
    """Classify every authorized identity and scan the managed raw tree; never mutates files."""
    root = Path(root).resolve()
    rows, expected = [], set()
    for row in plan['files']:
        expected.add(row['path'])
        status, reason = _status(root, row)
        rows.append(dict(path=row['path'], nominal_date=row['nominal_date'], manifest=row['manifest'],
                         bytes=row['bytes'], sha256=row['sha256'], status=status, reason=reason))
    partial, unexpected = [], []
    managed = root / MANAGED_ROOT
    if managed.exists():
        for path in sorted(p for p in managed.rglob('*') if p.is_file() or p.is_symlink()):
            relative = path.relative_to(root).as_posix()
            if relative in expected:
                continue
            (partial if PurePosixPath(relative).suffix == '.part' else unexpected).append(relative)
    counts = dict(required=len(rows), present_verified=0, missing=0, mismatch=0, partial=len(partial),
                  unexpected=len(unexpected))
    for row in rows:
        counts[row['status']] += 1
    return dict(counts=counts, files=rows, partial=partial, unexpected=unexpected)


def _check_manifests(plan, root, when):
    for manifest in plan['manifests']:
        if sha256_file(root / manifest['path']) != manifest['sha256']:
            raise IntegrityError(f"Tracked manifest {manifest['path']} changed {when}")


def restore(plan, root, *, free_bytes=lambda path: shutil.disk_usage(path).free, stats=None):
    """Download only missing authorized identities; refuse mismatches; idempotent.

    ``stats`` (caller-owned) receives attempt/retry/byte/failure counters and keeps
    them even when acquisition raises.
    """
    root = Path(root).resolve()
    stats = acquisition._new_stats({} if stats is None else stats)
    _check_manifests(plan, root, 'since the plan was loaded')
    before = inventory(plan, root)
    mismatched = [r['path'] for r in before['files'] if r['status'] == 'mismatch']
    if mismatched:
        raise IntegrityError(f'{len(mismatched)} local file(s) mismatch their pins; nothing is replaced: '
                             + ', '.join(mismatched))
    missing = [r for r in before['files'] if r['status'] == 'missing']
    needed = sum(r['bytes'] for r in missing) + plan['disk_margin_bytes']
    free = free_bytes(root)
    if missing and free < needed:
        raise InsufficientSpace(f'Restoration requires {needed} free bytes (missing data plus margin); {free} available')
    manifests = {m['path']: m for m in plan['manifests']}
    for relative in sorted({r['manifest'] for r in missing}, key=list(manifests).index):
        acquisition.acquire_history(manifests[relative]['config_path'], root, stats=stats)
    _check_manifests(plan, root, 'during restoration')
    after = inventory(plan, root)
    if after['counts']['present_verified'] != after['counts']['required']:
        raise IntegrityError('Restoration finished without verifying every authorized identity')
    return dict(before=before, after=after, stats=stats, free_bytes_before=free, required_free_bytes=needed)


_LISTING_ROW = re.compile(r'<a href="(sci_xrsf-l2-avg1m_g16_d\d{8}_v[0-9-]+\.nc)">[^<]*</a></td>\s*'
                          r'<td[^>]*>\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*</td>\s*<td[^>]*>\s*([0-9.]+)([KM]?)\s*</td>')


def parse_listing(html):
    """Rows (filename, last_modified, approximate bytes) of an official NOAA directory index page."""
    scale = {'': 1, 'K': 1024, 'M': 1024 ** 2}
    return [dict(name=name, last_modified=modified, approx_bytes=float(size) * scale[unit])
            for name, modified, size, unit in _LISTING_ROW.findall(html)]


def compare_official_listing(plan, fetch):
    """Compare pinned identities with the official monthly listings returned by ``fetch(url) -> html``.

    The listing gives names, version suffixes, modification times and size labels
    rounded to KiB; it carries no checksum, so it corroborates rather than proves bytes.
    """
    by_directory = {}
    for row in plan['files']:
        by_directory.setdefault(row['url'].rsplit('/', 1)[0] + '/', []).append(row)
    months = {}
    for directory, rows in sorted(by_directory.items()):
        listed = {entry['name']: entry for entry in parse_listing(fetch(directory))}
        expected = {Path(row['path']).name: row for row in rows}
        months[directory.rstrip('/').rsplit('/', 2)[-2] + '-' + directory.rstrip('/').rsplit('/', 1)[-1]] = dict(
            listed=len(listed), expected=len(expected), missing_from_listing=sorted(set(expected) - set(listed)),
            listed_not_pinned=sorted(set(listed) - set(expected)),
            versions=sorted({n.rsplit('_v', 1)[1][:-3] for n in listed}),
            last_modified_dates=sorted({e['last_modified'][:10] for e in listed.values()}),
            size_labels_within_1kib=all(abs(listed[n]['approx_bytes'] - r['bytes']) <= 1024
                                        for n, r in expected.items() if n in listed))
    consistent = all(not m['missing_from_listing'] and not m['listed_not_pinned'] and m['size_labels_within_1kib']
                     and m['versions'] == [acquisition.VERSION] for m in months.values())
    return dict(consistent=consistent, months=months,
                note='Official listings carry no checksums; byte identity rests on the pinned SHA-256 of downloads')
