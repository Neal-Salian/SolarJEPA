"""Offline source replay and native witnesses, never a science-readiness gate.

The reviewed official TAR is the only executable external source. Its functions
run on artificial FITS in fresh timezone subprocesses, outside the native reader.
"""
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

import numpy as np
from astropy.io import fits

from .solexs import TIME_CARDS, iter_spectra, load_light_curve, open_solexs_product
from .solexs_comparison import candidate_slice, compare_native_rows
from .solexs_integration import _gate, _pin, _snapshot
from .storage import repository_relative_path, validate_inventory, verify_inventory
from solar_flare_jepa.experiments.provenance import (
    _destination, atomic_record, code_provenance, verify_source_identities,
)

REVIEWED_ARCHIVE_SHA256 = '348014aefa50ade556ec4a160a3cfe0b08095bde84b4650a27d6b5d3bf7fa2d3'
# This bounded milestone supports only the reviewed release metadata, native
# witnesses and fixed artificial oracle. Prevent contradictory release claims
# and partial/empty expectations from producing PASS.
REVIEWED_WITNESSES_SHA256 = 'd0207367e838162d52d8d12f3170c7b1dc86820fa61e4a379f6c29e6a2bb855e'
PREFIX = 'solexs_tools-1.1/'
SELECTED_MEMBERS = (
    'solexs_tools/__init__.py', 'solexs_tools/time_utils.py',
    'solexs_tools/solexs_genlc.py', 'solexs_tools/solexs_genspec.py',
    'CALDB/ebounds/energy_bins_out_SDD2_v1.dat',
    'CALDB/arf/solexs_arf_SDD2_v1.arf',
    'CALDB/response/rmf/solexs_gaussian_SDD2_v1.rmf',
)
REVIEWED_MEMBERS = {'solexs_tools-1.1/CALDB/arf/solexs_arf_SDD2_v1.arf': {'bytes': 34560,
                                                       'sha256': '0f08199b3ef2f346979c58e0df83451fa23ae72a39fcaaa3d85bfe66b4b5bdc7'},
 'solexs_tools-1.1/CALDB/ebounds/energy_bins_out_SDD2_v1.dat': {'bytes': 6423,
                                                                'sha256': '684f916612003706062d509ab805ae2cda763f99a83f85ce81028a94aea0949e'},
 'solexs_tools-1.1/CALDB/response/rmf/solexs_gaussian_SDD2_v1.rmf': {'bytes': 6168960,
                                                                     'sha256': 'fc8ab03f15bb21ff066426cd6047519d57ffe017bb776bb88a5a65136deb63db'},
 'solexs_tools-1.1/solexs_tools/__init__.py': {'bytes': 345,
                                               'sha256': '6a4c02d1818a1cc6f91e8c223d41636c60ecac3f95a1d5ae49f6af22fbcde453'},
 'solexs_tools-1.1/solexs_tools/solexs_genlc.py': {'bytes': 7181,
                                                   'sha256': 'f6a3dd900e482fb88283189c9cb40aa60eddb50583cba7cabe364b591b38bb92'},
 'solexs_tools-1.1/solexs_tools/solexs_genspec.py': {'bytes': 13924,
                                                     'sha256': '265b0741e2aa902ff5df208d2ba1aabf58861b23778ae31d647722882d90ee7f'},
 'solexs_tools-1.1/solexs_tools/time_utils.py': {'bytes': 2135,
                                                 'sha256': '8d4ce3352aadd9cd9cf38a70b59369dac51c9b298a52e130421d1c45bdd7ca10'}}
# The only local adapter. The copied source is otherwise byte-for-byte unchanged.
CALDB_ADAPTER = "from pathlib import Path\nCALDB_BASE_DIR = str(Path(__file__).resolve().parents[1] / 'CALDB')\n"
CLOCK_CARDS = (*TIME_CARDS, 'TIMEPIXR', 'TREFPOS', 'TREFDIR', 'TIMEOFFS', 'TIMSYER',
    'TIMRDER', 'TIERABSO', 'TIERRELA', 'OBSORBIT', 'PLEPHEM', 'DTCORR', 'GAINAPP',
    'RESPFILE', 'ANCRFILE', 'NUMBAND', 'EXPOSURE')


def _member_path(name):
    if (type(name) is not str or '\\' in name or ':' in name
            or not name.startswith(PREFIX) or '..' in PurePosixPath(name).parts
            or str(PurePosixPath(name)) != name):
        raise ValueError('Unsafe selected TAR member path')
    return name


def read_selected_members(path, pins, *, max_member_bytes=8*1024**2,
                          max_total_bytes=16*1024**2, max_members=128):
    """Read bounded selected regular members; no extraction paths or setup code.

    Unselected payloads are never materialized. gzip expansion is bounded by the
    aggregate declared TAR payload/header extent (including unselected members).
    The archive itself must be verified separately before calling this helper.
    """
    if not isinstance(pins, dict) or not pins or len(pins) > 16:
        raise ValueError('Expected a bounded explicit selected-member mapping')
    for name, pin in pins.items():
        _member_path(name)
        if not isinstance(pin, dict) or set(pin) != {'bytes', 'sha256'}:
            raise ValueError('Malformed selected-member pin')
        _pin(dict(path=name, **pin))
        if pin['bytes'] > max_member_bytes:
            raise ValueError('Selected TAR member byte limit exceeded')
    result, seen, extent = {}, set(), 0
    with tarfile.open(path, 'r|gz') as archive:
        for index, member in enumerate(archive):
            extent = member.offset_data + ((member.size + 511)//512)*512
            if index >= max_members or extent > 64*1024**2:
                raise ValueError('TAR member-count or expanded extent limit exceeded')
            if member.name not in pins:
                continue
            if member.name in seen or not member.isfile():
                raise ValueError('Selected TAR member is duplicate or non-regular')
            seen.add(member.name)
            pin = pins[member.name]
            if member.size != pin['bytes'] or member.size > max_member_bytes:
                raise ValueError('Selected TAR member size changed')
            with archive.extractfile(member) as stream:
                payload = stream.read(max_member_bytes + 1)
            if len(payload) != member.size or hashlib.sha256(payload).hexdigest() != pin['sha256']:
                raise ValueError('Selected TAR member identity changed')
            result[member.name] = payload
            if sum(map(len, result.values())) > max_total_bytes:
                raise ValueError('Selected TAR total byte limit exceeded')
    if set(result) != set(pins):
        raise ValueError('Missing selected TAR member')
    return result


def assert_expected(observed, expected, locator):
    """Match every declared witness; allow additional diagnostic output fields."""
    if isinstance(expected, dict):
        if not isinstance(observed, dict) or not set(expected) <= set(observed):
            raise ValueError(f'Reference disagreement at {locator}: missing fields')
        for key, value in expected.items():
            assert_expected(observed[key], value, f'{locator}.{key}')
    elif isinstance(expected, list):
        if not isinstance(observed, list) or len(observed) != len(expected):
            raise ValueError(f'Reference disagreement at {locator}: list length')
        for index, value in enumerate(expected):
            assert_expected(observed[index], value, f'{locator}[{index}]')
    elif (isinstance(expected, bool) != isinstance(observed, bool)
            or observed != expected):
        raise ValueError(f'Reference disagreement at {locator}: {observed!r} != {expected!r}')


def load_reference_manifest(root, path):
    """Parse one finite duplicate-free snapshot and validate the replay boundary."""
    value, identity = _snapshot(Path(root).resolve(), path)
    keys = {'schema_version', 'tools_release', 'native_release', 'tools_archive',
            'members', 'inventory', 'sources', 'native', 'tool_expected', 'source_locators'}
    if (not isinstance(value, dict) or set(value) != keys
            or type(value['schema_version']) is not int or value['schema_version'] != 1):
        raise ValueError('Unsupported reference manifest/schema')
    _pin(value['tools_archive']); _pin(value['inventory'])
    if value['tools_archive']['sha256'] != REVIEWED_ARCHIVE_SHA256:
        raise ValueError('Only the reviewed official tools1.1 archive may be replayed')
    if not isinstance(value['members'], dict) or set(value['members']) != {PREFIX+n for n in SELECTED_MEMBERS}:
        raise ValueError('Reference requires exactly the reviewed source/CALDB members')
    if value['members'] != REVIEWED_MEMBERS:
        raise ValueError('Member pins differ from reviewed tools1.1 source/CALDB identities')
    for field in ('sources', 'native'):
        if not isinstance(value[field], list) or not 1 <= len(value[field]) <= 8:
            raise ValueError('Expected bounded reference input selection')
    for source in value['sources']:
        _pin(source)
    paths = []
    for entry in value['native']:
        if (not isinstance(entry, dict) or set(entry) != {'archive', 'expected', 'rows', 'source_locator'}
                or not isinstance(entry['expected'], dict) or not isinstance(entry['rows'], list)
                or not 1 <= len(entry['rows']) <= 16
                or any(type(i) is not int or i < 0 for i in entry['rows'])
                or len(set(entry['rows'])) != len(entry['rows'])):
            raise ValueError('Malformed native witness selection')
        paths.append(repository_relative_path(entry['archive'], root))
    if len(set(p.casefold() for p in paths)) != len(paths):
        raise ValueError('Duplicate native archive selection')
    if (not isinstance(value['tool_expected'], dict)
            or set(value['tool_expected']) != {'UTC', 'Asia/Kolkata'}
            or not isinstance(value['source_locators'], dict)):
        raise ValueError('Missing explicit timezone/source reference expectations')
    for expected in value['tool_expected'].values():
        if (not isinstance(expected, dict) or not {'epoch', 'genlc', 'rebin', 'fractional_writer', 'genspec'} <= set(expected)
                or not isinstance(expected['genlc'], dict)
                or not isinstance(expected['genspec'], dict)
                or not {'none', 'explicit_one', 'even_two', 'odd_three'} <= set(expected['genlc'])
                or not {'request_half_open', 'closed_gti_endpoint', 'clamped_stop'} <= set(expected['genspec'])):
            raise ValueError('Missing required executable reference witnesses')
    witnesses = dict(native=[{k: entry[k] for k in ('archive', 'rows', 'expected')}
                             for entry in value['native']], tool_expected=value['tool_expected'],
                     tools_release=value['tools_release'], native_release=value['native_release'])
    digest = hashlib.sha256(json.dumps(witnesses, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if digest != REVIEWED_WITNESSES_SHA256:
        raise ValueError('Reference release/witness identity differs; review the complete expected contract')
    return value, identity


def replay_tools(payloads):
    """Run pinned package functions in isolated temporary subprocesses, offline.

    Only artificial files enter the reviewed tools. No native data paths or
    scientific pipeline objects are passed to those subprocesses.
    """
    if set(payloads) != {PREFIX+n for n in SELECTED_MEMBERS}:
        raise ValueError('Incomplete reviewed replay payload')
    for name, payload in payloads.items():
        if (not isinstance(payload, bytes) or len(payload) != REVIEWED_MEMBERS[name]['bytes']
                or hashlib.sha256(payload).hexdigest() != REVIEWED_MEMBERS[name]['sha256']):
            raise ValueError('Replay payload differs from reviewed source/CALDB identity')
    results = {}
    with tempfile.TemporaryDirectory(prefix='solexs-reference-') as temporary:
        stage = Path(temporary)
        for name, payload in payloads.items():
            relative = _member_path(name)[len(PREFIX):]
            target = stage/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        (stage/'solexs_tools/caldb_config.py').write_text(CALDB_ADAPTER)
        worker = Path(__file__).with_name('_solexs_reference_worker.py')
        for zone in ('UTC', 'Asia/Kolkata'):
            output = stage/(zone.replace('/', '_')+'.json')
            env = dict(os.environ, TZ=zone, PYTHONDONTWRITEBYTECODE='1')
            # -I ignores ambient Python injection and user site-packages. The
            # worker adds only this selected temporary package directory.
            subprocess.run([sys.executable, '-I', '-B', str(worker), str(stage), str(output)],
                cwd=stage, env=env, capture_output=True, text=True, timeout=60, check=True)
            if output.stat().st_size > 256*1024:
                raise ValueError('Replay result byte limit exceeded')
            results[zone] = json.loads(output.read_text())
    return results


def native_witness(root, record, band, response_channels, rows, *, chunk_rows=1024):
    """Compare native arrays without transforming clocks, channels or quantities."""
    if type(chunk_rows) is not int or not 1 <= chunk_rows <= 8192:
        raise ValueError('Native reference chunk_rows must be in 1..8192')
    members, clocks, lineage, units = {}, {}, {}, {}
    for kind in ('gti', 'lc', 'pi'):
        names = [m['path'] for m in record['archive']['members']
                 if not m['is_directory'] and m['path'].endswith(f'SDD2_L1.{kind}.gz')]
        if len(names) != 1:
            raise ValueError('Native witness requires one SDD2 LC/PI/GTI')
        members[kind] = names[0]
        with open_solexs_product(root, record, names[0]) as product:
            clocks[kind] = {h.name: {k: h.header.get(k) for k in CLOCK_CARDS} for h in product.hdus}
            units[kind] = {c.name: c.unit for c in product.hdus[product.table_name].columns}
            lineage[kind] = product.provenance
            if kind == 'lc':
                lc = load_light_curve(product).columns
    cases = {}
    with open_solexs_product(root, record, members['pi']) as product:
        def chunks():
            offset = 0
            for chunk in iter_spectra(product, chunk_rows=chunk_rows):
                columns = chunk.columns
                for row in rows:
                    if offset <= row < offset+len(columns['TSTART']):
                        index = row-offset
                        counts = columns['COUNTS'][index]
                        def number(value):
                            return float(value) if np.isfinite(value) else None
                        cases[row] = dict(row=row, native_coordinate=float(columns['TSTART'][index]),
                            spec_num=int(columns['SPEC_NUM'][index]), lc=number(lc['COUNTS'][row]),
                            tool_41_313=number(counts[band[0]:band[1]].sum()),
                            control_41_314=number(counts[band[0]:band[1]+1].sum()),
                            all_sum=number(counts.sum()),
                            counts_big_endian_float64_sha256=hashlib.sha256(
                                np.asarray(counts, dtype='>f8').tobytes()).hexdigest())
                offset += len(columns['TSTART'])
                yield columns
        comparison = compare_native_rows(lc, chunks(), band, response_channels)
    if set(cases) != set(rows):
        raise ValueError('Native reference row outside product')
    return dict(archive=record['path'], archive_sha256=record['sha256'], comparison=comparison,
                clocks=clocks, units=units, source_lineage=lineage,
                cases=[cases[row] for row in rows])


def _caldb_facts(payloads):
    """Only structural metadata of the exact tools bundle, never application."""
    import io
    result = {}
    channels = None
    grids = {}
    for kind, name in [('rmf', SELECTED_MEMBERS[-1]), ('arf', SELECTED_MEMBERS[-2])]:
        with fits.open(io.BytesIO(payloads[PREFIX+name]), memmap=False) as hdus:
            hdus.verify('exception')
            result[kind] = {h.name: dict(rows=h.header.get('NAXIS2'),
                units={c.name: c.unit for c in getattr(h, 'columns', [])},
                creator=h.header.get('CREATOR')) for h in hdus}
            if kind == 'rmf':
                channels = np.array(hdus['EBOUNDS'].data['CHANNEL'], copy=True)
                data = hdus['MATRIX'].data
                result['matrix_shape'] = list(data['MATRIX'].shape)
                result['matrix_nonfinite_cells'] = int((~np.isfinite(data['MATRIX'])).sum())
                result['matrix_negative_cells'] = int((data['MATRIX'] < 0).sum())
                grids[kind] = tuple(np.array(data[k], copy=True) for k in ('ENERG_LO', 'ENERG_HI'))
            else:
                grids[kind] = tuple(np.array(hdus['SPECRESP'].data[k], copy=True) for k in ('ENERG_LO', 'ENERG_HI'))
    result['response_channel_first_last'] = [int(channels[0]), int(channels[-1])]
    result['arf_incident_grid_values_equal_rmf'] = all(np.array_equal(a, b) for a, b in zip(grids['arf'], grids['rmf']))
    result['accepted_for_science_application'] = False
    return result, channels


def audit_reference(manifest_path, root, *, chunk_rows=1024):
    """Rebuild pinned tool behavior and release facts; disagreement aborts report."""
    import io
    root = Path(root).resolve()
    manifest, identity = load_reference_manifest(root, manifest_path)
    pins = [identity, manifest['tools_archive'], manifest['inventory'], *manifest['sources']]
    verify_source_identities(root, pins)
    phase_e = [pin for pin in manifest['sources']
               if pin['path'] == 'data/manifests/solexs_phase_e_evidence.json']
    if len(phase_e) != 1:
        raise ValueError('Expected one pinned inherited Phase E gate')
    gate, gate_identity = _snapshot(root, phase_e[0]['path'])
    if gate_identity != phase_e[0]:
        raise ValueError('Pinned Phase E gate changed')
    gates = _gate(gate)
    inventory, inventory_identity = _snapshot(root, manifest['inventory']['path'])
    if inventory_identity != manifest['inventory']:
        raise ValueError('Pinned inventory changed')
    validate_inventory(inventory)
    records = {r['path']: r for r in inventory['files']}
    if any(e['archive'] not in records for e in manifest['native']):
        raise ValueError('Native reference archive is unregistered')
    selected = [records[e['archive']] for e in manifest['native']]
    verify_inventory(dict(inventory, files=selected, missing_coverage=[]), root)
    payloads = read_selected_members(root/manifest['tools_archive']['path'], manifest['members'])
    tools = replay_tools(payloads)
    assert_expected(tools, manifest['tool_expected'], 'tools')
    calibration, channels = _caldb_facts(payloads)
    band = candidate_slice(np.loadtxt(io.BytesIO(payloads[PREFIX+SELECTED_MEMBERS[4]])))
    native = []
    for entry in manifest['native']:
        observed = native_witness(root, records[entry['archive']], band, channels,
                                  entry['rows'], chunk_rows=chunk_rows)
        assert_expected(observed, entry['expected'], 'native.'+entry['archive'])
        observed['case_result'] = 'PASS'
        native.append(observed)
    verify_source_identities(root, pins)
    verify_inventory(dict(inventory, files=selected, missing_coverage=[]), root)
    return dict(schema_version=1, evidence='OBSERVED', verdict='REFERENCE_AGREEMENT_SCIENCE_BLOCKED',
        input_identities=dict(manifest=identity, tools_archive=manifest['tools_archive'],
            members=manifest['members'], inventory=manifest['inventory'], sources=manifest['sources']),
        release_identities=dict(tools=manifest['tools_release'], native=manifest['native_release']),
        replay=dict(case_result='PASS', mission_policy_accepted=False,
            cases={zone: {case: 'PASS' for case in ('epoch', 'genlc', 'rebin',
                'fractional_writer', 'genspec')} for zone in tools},
            scope='artificial fixtures only; tool behavior', zones=tools,
            adapter=dict(path='solexs_tools/caldb_config.py', source=CALDB_ADAPTER,
                sha256=hashlib.sha256(CALDB_ADAPTER.encode()).hexdigest()),
            volatile_fields_excluded=['PRIMARY.DATE', 'temporary output/CALDB paths']),
        runtime=dict(python=sys.version, numpy=np.__version__, astropy=version('astropy')),
        tools_bundle_caldb=calibration, source_locators=manifest['source_locators'],
        band_diagnostic=dict(tool_slice=list(band), inclusive_upper_control=[band[0], band[1]+1],
            encoded_bounds_unit=None, mapping_validated=False), native=native,
        readiness=dict(jepa_training_allowed=False, physical_analysis_allowed=False,
            clock_conversion_allowed=False, calibration_application_allowed=False,
            inherited_phase_e_gate='BLOCKED_FOR_PHASE_E', gates=gates,
            unknowns=['Absolute UTC/card precedence and bin availability',
                'Detector/pipeline/epoch response and channel correspondence',
                'GTI/quality/health/deadtime and continuous effective exposure',
                'COUNTS quantity and correction state; units remain encoded null',
                'Physical target, uncertainty, labels and chronological forecast validity']),
        policies=dict(native_utc_conversion=False, native_gti_filtering=False,
            native_channel_mapping=False, native_exposure_division=False,
            native_calibration=False, native_gap_filling=False, training_executed=False,
            correction_state='UNKNOWN'))


def run_reference_validation(manifest_path, *, project_root, data_root, output_dir, chunk_rows=1024):
    """Use existing provenance and atomic exclusive publication safeguards."""
    project_root = Path(project_root).resolve()
    _destination(project_root, output_dir)  # Refuse existing/unsafe outputs before replay.
    before = code_provenance(project_root)
    report = audit_reference(manifest_path, data_root, chunk_rows=chunk_rows)
    after = code_provenance(project_root)
    if before['source'] != after['source'] or before['git_commit'] != after['git_commit']:
        raise ValueError('Executed source changed during reference validation')
    report['code'] = after
    return atomic_record(project_root, output_dir, {'report.json': report})
