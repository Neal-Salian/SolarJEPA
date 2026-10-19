"""Read-only stable dependency and SHA-256 preflight; no science imports or fitting."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
# Integration trust anchors preserve the original reviewed registry bytes.
CONTRACTS = {
    'src/solar_flare_jepa/dashboard/registry.json': '26f31b31e21697502318916933617c931459f4e305e9891b12f7ae4b70cf0b49',
    'src/solar_flare_jepa/dashboard/prediction_registry.json': '66030fdca12524b8e661970e6540b118715103d1ffed44f14d8f7c7b236c0f4f',
    'docs/presentation/time_series_identity.json': '84615cf8389e8952567f6ef2676db7461144618c596f4e1361552225e9a091ce',
}
FIGURES = 'docs/presentation/figure_manifest.json'
FIGURES_SHA = 'cabfc33c4e1d6d700280de41b0126e16dfca5615d946371de56c0584013edd93'
# Original checkpoint SHA-256 values, shared with the reviewed numerical replay contract.
CHECKPOINTS = {
    "jepa_finetune_seed17": "3d18e1067b7eeaf2b64ea572ff48831559f5171b82e765bf56841f2903fdaf48",
    "jepa_finetune_seed29": "e1b97d4cc8587fd9fa9ff02da2cda2165e2bf5b8febb825b4b820af4ddf1540f",
    "jepa_finetune_seed43": "6e36849378836f83847ae275561c65460fe4eb129eb1703302bbead7b342e4d5",
    "jepa_frozen_seed17": "84772e256b7796978ca53154e4e5088b5b38e98f78a903b5cc33e51e76272c54",
    "jepa_frozen_seed29": "1da1e6f474e7cf0e96522e3e391f7f1dc2998974c436e143b2920b488159fe33",
    "jepa_frozen_seed43": "98ba8d6379100b2687b075754c15551d9960c8de175957bb6891fdd01ceaea4a",
    "supervised_seed17": "973f784e2adecd5183bd11bd3f6d47f49c5a8786e603cac82c15e2854858273b",
    "supervised_seed29": "0e77f5fd68a6972ca7f3335733fc873b109527a90e8e7758ab644ad3584c2585",
    "supervised_seed43": "6ef24954846756544957363433c1fe000101154e6c9c814aaedd5c8bc3c3a550"
}


def lock_versions(path, seen=None):
    """Resolve exact local lock includes; reject cycles, ranges and conflicting pins."""
    path = Path(path).resolve()
    seen = set() if seen is None else set(seen)
    if path in seen:
        raise ValueError('Dependency lock include cycle: ' + str(path))
    seen.add(path)
    pins = {}
    for line in path.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        if line.startswith('-r '):
            selected = lock_versions(path.parent / line[3:].strip(), seen)
        else:
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)', line)
            if not match:
                raise ValueError('Exact dependency pin required: ' + line)
            name, value = match.groups()
            selected = {re.sub(r'[-_.]+', '-', name).lower(): value}
        for name, value in selected.items():
            if name in pins and pins[name] != value:
                raise ValueError('Conflicting dependency pin: ' + name)
            pins[name] = value
    return pins


def check_dependencies(lock):
    result = {}
    for name, expected in lock_versions(lock).items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = None
        result[name] = dict(expected=expected, installed=installed, ok=installed == expected)
    return result


def local_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root) or '..' in Path(relative).parts:
        raise ValueError('Artifact path escapes checkout: ' + str(relative))
    return path


def verify_file(root, record):
    relative = record['path']
    result = dict(path=relative, ok=False)
    try:
        path = local_path(root, relative)
        if not path.is_file():
            raise ValueError('Required artifact missing: ' + relative)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != record['sha256']:
            raise ValueError('Artifact SHA-256 mismatch: ' + relative)
        if 'bytes' in record and path.stat().st_size != record['bytes']:
            raise ValueError('Artifact byte-size mismatch: ' + relative)
        result.update(ok=True, sha256=digest.hexdigest(), bytes=path.stat().st_size)
    except (OSError, ValueError) as error:
        result['error'] = str(error)
    return result


def check_artifacts(root, references=False):
    """Hash required original inputs without opening NetCDF, checkpoints or arrays."""
    checked = {}
    def check(record):
        relative = record['path']
        if relative in checked and checked[relative].get('sha256') == record['sha256']:
            return checked[relative]['ok']
        checked[relative] = verify_file(root, record)
        return checked[relative]['ok']
    def read(relative):
        return json.loads(local_path(root, relative).read_text())
    trusted = {}
    for relative, digest in CONTRACTS.items():
        if check(dict(path=relative, sha256=digest)):
            trusted[relative] = read(relative)
    legacy = trusted.get('src/solar_flare_jepa/dashboard/registry.json')
    prediction = trusted.get('src/solar_flare_jepa/dashboard/prediction_registry.json')
    identity = trusted.get('docs/presentation/time_series_identity.json')
    manifests = set()
    if legacy:
        for record in legacy['sources'].values():
            check(record)
        manifests.update(row['manifest'] for row in legacy['datasets'])
    if prediction:
        for key, record in prediction['artifacts'].items():
            if references or not key.startswith('replay_'):
                check(record)
        manifests.add(prediction['artifacts']['august_manifest']['path'])
    if identity:
        for record in identity['sources']:
            check(record)
            if references and record['path'].startswith('data/manifests/goes_'):
                manifests.add(record['path'])
        if check(identity['report']):
            check(read(identity['report']['path'])['payload'])
    if references:
        for name, digest in CHECKPOINTS.items():
            check(dict(path='results/experiments/v1-full-20261009/' + name + '.pt', sha256=digest))
        if check(dict(path=FIGURES, sha256=FIGURES_SHA)):
            figures = read(FIGURES)
            for record in figures['analysis_sources']:
                check(record)
            for figure in figures['generated'] + figures['reused']:
                for record in figure['identities']:
                    check(record)
        check(dict(path='results/experiments/v1-full-20261009/per_origin.json',
                   sha256='133025c6921bcd575b727287b504550ff15e6e1d3ade8bcc39a5ff432056aa7f'))
    native_files = 0
    for relative in sorted(manifests):
        if checked.get(relative, {}).get('ok'):
            for record in read(relative)['files']:
                native_files += 1
                check(record)
    return list(checked.values()), native_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Checkout with restored original ignored inputs')
    parser.add_argument('--references', action='store_true', help='Also require all 123 native products and V1 reference artifacts')
    args = parser.parse_args()
    report = dict(status='FAIL', references=args.references, dependencies={}, artifacts=[], errors=[],
                  native_files=0, python=platform.python_version(), platform=platform.platform())
    try:
        report['dependencies'] = check_dependencies(args.root / 'requirements-stable-lock.txt')
        report['errors'].extend('Dependency mismatch: ' + name for name, row in report['dependencies'].items() if not row['ok'])
        report['artifacts'], report['native_files'] = check_artifacts(args.root, args.references)
        report['errors'].extend(row['error'] for row in report['artifacts'] if not row['ok'])
    except (OSError, ValueError, KeyError, TypeError) as error:
        report['errors'].append(str(error))
    if not report['errors']:
        report['status'] = 'PASS'
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
