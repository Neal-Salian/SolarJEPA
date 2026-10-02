"""Small artificial FITS products; no real solar observations are fixtures."""
import gzip
import hashlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import weakref
import zipfile

import numpy as np
import pytest
from astropy.io import fits

from solar_flare_jepa.data.storage import register_archives

ARCHIVE = 'data/raw/aditya/solexs/l1/v1.1/archives/2024/07/AL1_SLX_L1_20240701_v1.1.zip'
PREFIX = 'AL1_SLX_L1_20240701_v1.1'


def science():
    assert importlib.util.find_spec('solar_flare_jepa.data.solexs'), 'SoLEXS scientific API is missing'
    return importlib.import_module('solar_flare_jepa.data.solexs')


def product_bytes(kind='lc', detector='SDD2', *, units=None, missing_clock=False,
                  invalid_gti=False, pi_width=3, instrument='SoLEXS'):
    primary = fits.PrimaryHDU()
    primary.header['INSTRUME'] = instrument
    primary.header['CREATOR'] = 'solexs_pipeline-1.1'
    primary.header['CONTENT'] = {'lc': 'LIGHT CURVE', 'gti': 'GOOD TIME INTERVAL',
                                 'pi': 'Type II PHA file'}[kind]
    if kind == 'lc':
        columns = [fits.Column(name='TIME', format='D', unit=units, array=[100., 101., 102.]),
                   fits.Column(name='COUNTS', format='D', array=[7., np.nan, -3.])]
        table = fits.BinTableHDU.from_columns(columns, name='RATE')
        if not missing_clock:
            for key, value in {'TIMEUNIT': 's', 'TIMEDEL': 1, 'MJDREFI': 40587,
                               'MJDREFF': 0.22916666651, 'TIMESYS': 'UTC',
                               'TIMEREF': 'LOCAL', 'TIMZERO': 0}.items():
                table.header[key] = value
    elif kind == 'gti':
        starts, stops = ([100., 106.], [102., 104.]) if invalid_gti else ([100.], [102.])
        if detector == 'SDD1':
            starts, stops = np.array([], dtype=np.int16), np.array([], dtype=np.int16)
        fmt = 'I' if detector == 'SDD1' else 'D'
        table = fits.BinTableHDU.from_columns([
            fits.Column(name='START', format=fmt, array=starts),
            fits.Column(name='STOP', format=fmt, array=stops)], name='GTI')
    else:
        data = np.array([[1., 2., 3.], [np.nan]*3, [2.5, 0., -1.]])[:, :pi_width]
        table = fits.BinTableHDU.from_columns([
            fits.Column(name='TSTART', format='D', unit='s', array=[100., 101., 102.]),
            fits.Column(name='TELAPSE', format='D', unit='s', array=[1., 1., 1.]),
            fits.Column(name='SPEC_NUM', format='J', array=[1, 2, 3]),
            fits.Column(name='CHANNEL', format='3K', array=np.tile([0, 1, 2], (3, 1))),
            fits.Column(name='COUNTS', format=f'{pi_width}D', array=data),
            fits.Column(name='EXPOSURE', format='D', unit='s', array=[1., 0., 1.])], name='SPECTRUM')
        table.header['DETCHANS'] = 3
        table.header['CHANTYPE'] = 'PI'
        table.header['HDUCLAS4'] = 'TYPE:II'
    if detector == 'SDD2':
        table.header['FILTER'] = 'SDD2'
    stream = io.BytesIO()
    fits.HDUList([primary, table]).writeto(stream, checksum=True)
    return stream.getvalue()


def archive_fixture(root, products=None):
    products = products or [('lc', 'SDD2', product_bytes())]
    path = root / ARCHIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    members = []
    with zipfile.ZipFile(path, 'w') as z:
        for kind, detector, payload in products:
            member = f'{PREFIX}/{detector}/AL1_SOLEXS_20240701_{detector}_L1.{kind}.gz'
            z.writestr(member, gzip.compress(payload, mtime=0))
            members.append(member)
    record = register_archives(root, [ARCHIVE])['files'][0]
    return record, members


def test_lc_loading_preserves_native_values_units_clock_and_source(tmp_path):
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes(units='ms'))])
    before = (tmp_path / ARCHIVE).read_bytes()
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        native = api.load_light_curve(product)
        assert product.kind == 'lc'
        assert product.detector == {'value': 'SDD2', 'evidence': 'OBSERVED', 'source': 'FILTER'}
        np.testing.assert_array_equal(native.columns['TIME'], [100., 101., 102.])
        np.testing.assert_array_equal(native.columns['COUNTS'], [7., np.nan, -3.])
        assert native.units == {'TIME': 'ms', 'COUNTS': None}
        assert native.time_metadata['MJDREFF'] == 0.22916666651
        assert native.time_metadata['TIMZERO'] == 0
        assert native.time_metadata['TIMEZERO'] is None
        assert native.provenance['archive_sha256'] == record['sha256']
        assert native.provenance['member'] == members[0]
        assert native.provenance['kind'] == 'lc'
        assert native.provenance['detector'] == product.detector
        assert native.warnings == product.warnings
        assert not native.columns['COUNTS'].flags.writeable
        assert 'TIME_REFERENCE_CONFLICT' in product.warnings
        assert 'TIME_COLUMN_UNIT_CONFLICT' in product.warnings
        assert product.expanded_bytes == 8640
    assert (tmp_path / ARCHIVE).read_bytes() == before
    assert not list((tmp_path / '.cache/aditya/solexs').rglob('*.fits'))
    np.testing.assert_array_equal(native.columns['TIME'], [100., 101., 102.])


def test_missing_clock_cards_remain_unknown(tmp_path):
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes(missing_clock=True))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        native = api.load_light_curve(product)
        assert native.time_metadata['MJDREFI'] is None
        assert native.time_metadata['TIMEUNIT'] is None
        assert native.time_metadata['TIMESYS'] is None
        assert 'TIME_REFERENCE_MISSING' in product.warnings


def test_gti_preserves_invalid_intervals_without_filtering(tmp_path):
    record, members = archive_fixture(tmp_path, [('gti', 'SDD2', product_bytes('gti', invalid_gti=True))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        native = api.load_gti(product)
        np.testing.assert_array_equal(native.columns['START'], [100., 106.])
        np.testing.assert_array_equal(native.columns['STOP'], [102., 104.])
        assert native.units == {'START': None, 'STOP': None}


def test_empty_sdd1_is_inferred_and_never_zero_solar_observations(tmp_path):
    record, members = archive_fixture(tmp_path, [('gti', 'SDD1', product_bytes('gti', 'SDD1'))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        native = api.load_gti(product)
        assert len(native.columns['START']) == 0
        assert native.columns['START'].dtype.kind == 'i'
        assert native.columns['START'].dtype.itemsize == 2
        assert product.detector == {'value': 'SDD1', 'evidence': 'INFERRED', 'source': 'member_name'}


@pytest.mark.parametrize('stage', ['gzip', 'fits', 'checksum'])
def test_malformed_payload_fails_and_cleans_scratch(tmp_path, stage):
    payload = product_bytes()
    if stage == 'fits':
        payload = b'not a FITS file'
    elif stage == 'checksum':
        payload = payload[:5760] + bytes([payload[5760] ^ 1]) + payload[5761:]
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', payload)])
    if stage == 'gzip':
        path = tmp_path / ARCHIVE
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr(members[0], b'not gzip')
        # Independent registration of this malformed fixture proves the science
        # layer checks payload integrity beyond the central-directory foundation.
        (tmp_path / 'data/manifests/aditya_inventory.json').unlink()
        record = register_archives(tmp_path, [ARCHIVE])['files'][0]
    api = science()
    with pytest.raises(ValueError):
        with api.open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Malformed scientific payload was accepted')
    assert not list((tmp_path / '.cache/aditya/solexs').rglob('*.fits'))


@pytest.mark.parametrize('limit', ['member', 'expanded'])
def test_expansion_limits_fail_before_returning_a_product(tmp_path, limit):
    record, members = archive_fixture(tmp_path)
    api = science()
    limits = api.AccessLimits(max_member_bytes=1) if limit == 'member' else api.AccessLimits(max_fits_bytes=4096)
    with pytest.raises(ValueError, match='limit'):
        with api.open_solexs_product(tmp_path, record, members[0], limits=limits):
            pytest.fail('Oversized input was accepted')
    assert not list((tmp_path / '.cache/aditya/solexs').rglob('*.fits'))


def test_changed_registered_source_is_rejected(tmp_path):
    record, members = archive_fixture(tmp_path)
    with (tmp_path / ARCHIVE).open('ab') as f:
        f.write(b'changed')
    with pytest.raises(ValueError, match='identity|changed'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Changed registered bytes were accepted')


def test_cache_symlink_escape_is_rejected(tmp_path):
    record, members = archive_fixture(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + '-outside')
    outside.mkdir()
    (tmp_path / '.cache').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='root'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Escaping cache symlink was accepted')
    assert list(outside.iterdir()) == []


def test_caller_failure_cleans_product_scratch(tmp_path):
    record, members = archive_fixture(tmp_path)
    with pytest.raises(RuntimeError, match='caller'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            raise RuntimeError('caller failed')
    assert not list((tmp_path / '.cache/aditya/solexs').rglob('*.fits'))


def test_different_instrument_metadata_fails(tmp_path):
    payload = product_bytes(instrument='OtherInstrument')
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', payload)])
    with pytest.raises(ValueError, match='instrument'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Different instrument was accepted')


def edit_fits(payload, edit):
    with fits.open(io.BytesIO(payload)) as hdus:
        edit(hdus)
        stream = io.BytesIO()
        hdus.writeto(stream, checksum=True)
        return stream.getvalue()


def test_pi_chunks_preserve_vectors_units_missingness_and_exposure(tmp_path):
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', product_bytes('pi'))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        chunks = list(api.iter_spectra(product, chunk_rows=2))
        assert [len(c.columns['TSTART']) for c in chunks] == [2, 1]
        assert chunks[0].units['TSTART'] == 's'
        assert chunks[0].units['COUNTS'] is None
        np.testing.assert_array_equal(chunks[0].columns['CHANNEL'], [[0, 1, 2]]*2)
        np.testing.assert_array_equal(chunks[0].columns['COUNTS'][1], [np.nan]*3)
        np.testing.assert_array_equal(chunks[1].columns['COUNTS'][0], [2.5, 0., -1.])
        np.testing.assert_array_equal(chunks[0].columns['EXPOSURE'], [1., 0.])
        assert not chunks[0].columns['COUNTS'].flags.writeable
        assert 'CALIBRATION_NOT_APPLIED' in product.warnings
    np.testing.assert_array_equal(chunks[0].columns['COUNTS'][0], [1., 2., 3.])
    with pytest.raises(ValueError, match='closed'):
        next(api.iter_spectra(product))


@pytest.mark.parametrize('change', ['width', 'detchans', 'type', 'channel_type', 'column', 'detector'])
def test_pi_incompatible_schema_is_rejected(tmp_path, change):
    payload = product_bytes('pi', pi_width=2 if change == 'width' else 3)
    def edit(hdus):
        table = hdus[1]
        if change == 'detchans':
            table.header['DETCHANS'] = 4
        elif change == 'type':
            table.header['HDUCLAS4'] = 'TYPE:I'
        elif change == 'channel_type':
            table.header['CHANTYPE'] = 'PHA'
        elif change == 'column':
            table.header['TTYPE2'] = 'UNRECOGNIZED'
        elif change == 'detector':
            table.header['FILTER'] = 'SDD1'
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', edit_fits(payload, edit))])
    with pytest.raises(ValueError):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Incompatible PI schema was accepted')


@pytest.mark.parametrize('value', [0, -1, 1.5, True])
def test_invalid_pi_chunk_bound_is_rejected(tmp_path, value):
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', product_bytes('pi'))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        with pytest.raises(ValueError, match='positive integer'):
            next(api.iter_spectra(product, chunk_rows=value))


def test_closed_context_and_wrong_loader_are_rejected(tmp_path):
    record, members = archive_fixture(tmp_path)
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        with pytest.raises(ValueError, match='kind'):
            api.load_gti(product)
    with pytest.raises(ValueError, match='closed'):
        api.load_light_curve(product)


def test_eager_row_limit_does_not_truncate_data(tmp_path):
    record, members = archive_fixture(tmp_path)
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0],
                                  limits=api.AccessLimits(max_eager_rows=2)) as product:
        with pytest.raises(ValueError, match='limit'):
            api.load_light_curve(product)


def test_archive_inspection_is_portable_deterministic_and_keeps_anomalies(tmp_path):
    products = [('lc', 'SDD2', product_bytes()), ('gti', 'SDD2', product_bytes('gti', invalid_gti=True)),
                ('pi', 'SDD2', product_bytes('pi')), ('gti', 'SDD1', product_bytes('gti', 'SDD1'))]
    record, _ = archive_fixture(tmp_path, products)
    api = science()
    report = api.inspect_solexs_archive(tmp_path, record, chunk_rows=2)
    assert report == api.inspect_solexs_archive(tmp_path, record, chunk_rows=1)
    serialized = json.dumps(report, allow_nan=False, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert 'UTC_CONVERSION_NOT_APPLIED' in serialized
    lc = next(p for p in report['products'] if p['kind'] == 'lc')
    assert lc['numeric']['COUNTS']['nan'] == 1
    assert lc['numeric']['COUNTS']['negative'] == 1
    assert lc['time']['duplicate_values'] == 0
    assert lc['time']['step_min'] == lc['time']['step_max'] == 1
    assert lc['time']['converted_utc'] is None
    assert lc['hdus'][1]['columns'][0]['unit'] is None
    assert lc['hdus'][1]['datasum'] == 'verified'
    gti = next(p for p in report['products'] if p['kind'] == 'gti' and p['detector']['value'] == 'SDD2')
    assert gti['gti']['invalid_intervals'] == 1
    assert gti['gti']['intervals_native'] == [[100., 102.], [106., 104.]]
    pi = next(p for p in report['products'] if p['kind'] == 'pi')
    assert pi['spectra']['all_nan_rows'] == 1
    assert pi['spectra']['channel_axis_constant'] is True
    assert pi['spectra']['channel_min'] == 0
    assert pi['spectra']['channel_max'] == 2
    assert pi['numeric']['COUNTS']['noninteger_finite'] == 1
    assert pi['table_bytes'] == 228
    assert pi['hdus'][1]['columns'][3]['shape'] == [3, 3]
    assert report['zip_integrity'] == 'verified'
    assert report['identity_evidence']['nominal_observation_date'] == 'INFERRED'
    assert report['identity_evidence']['product_version'] == 'INFERRED'


def test_time_diagnostics_cover_nonfinite_unordered_duplicate_and_gapped_values(tmp_path):
    def edit(hdus):
        # Adjacent finite steps -1 and +1, with a duplicate separated by a NaN.
        hdus[1] = fits.BinTableHDU.from_columns([
            fits.Column(name='TIME', format='D', array=[100., 105., 104., np.nan, 105., np.inf]),
            fits.Column(name='COUNTS', format='D', array=np.arange(6.))], name='RATE')
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', edit_fits(product_bytes(), edit))])
    lc = science().inspect_solexs_archive(tmp_path, record)['products'][0]
    assert lc['time']['duplicate_values'] == 1
    assert lc['time']['nonmonotonic_steps'] == 1
    assert lc['time']['step_min'] == -1
    assert lc['time']['step_max'] == 5
    assert lc['numeric']['TIME']['nan'] == 1
    assert lc['numeric']['TIME']['positive_infinity'] == 1
    assert lc['time']['positive_steps_not_one'] == 1


def test_missing_fits_checksum_is_reported_as_absent_not_verified(tmp_path):
    def edit(hdus):
        for hdu in hdus:
            del hdu.header['DATASUM']
            del hdu.header['CHECKSUM']
    with fits.open(io.BytesIO(product_bytes())) as hdus:
        edit(hdus)
        stream = io.BytesIO()
        hdus.writeto(stream)
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', stream.getvalue())])
    report = science().inspect_solexs_archive(tmp_path, record)
    assert all(h['datasum'] == h['checksum'] == 'absent' for h in report['products'][0]['hdus'])


def test_truncated_gzip_trailer_is_rejected(tmp_path):
    record, members = archive_fixture(tmp_path)
    with zipfile.ZipFile(tmp_path / ARCHIVE, 'w') as z:
        z.writestr(members[0], gzip.compress(product_bytes(), mtime=0)[:-4])
    (tmp_path / 'data/manifests/aditya_inventory.json').unlink()
    record = register_archives(tmp_path, [ARCHIVE])['files'][0]
    with pytest.raises(ValueError, match='Corrupt'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Missing gzip trailer was accepted')


@pytest.mark.parametrize('change', ['detector', 'column', 'duplicate_hdu', 'vector'])
def test_light_curve_schema_conflicts_fail(tmp_path, change):
    def edit(hdus):
        if change == 'detector':
            hdus[1].header['FILTER'] = 'SDD1'
        elif change == 'column':
            hdus[1].header['TTYPE1'] = 'UNKNOWN_TIME'
        elif change == 'duplicate_hdu':
            hdus.append(hdus[1].copy())
        else:
            hdus[1] = fits.BinTableHDU.from_columns([
                fits.Column(name='TIME', format='2D', array=[[1, 2]]),
                fits.Column(name='COUNTS', format='D', array=[3])], name='RATE')
    record, members = archive_fixture(tmp_path, [('lc', 'SDD2', edit_fits(product_bytes(), edit))])
    with pytest.raises(ValueError):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Incompatible LC schema accepted')


def test_spectrum_iterator_cannot_resume_after_context_closes(tmp_path):
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', product_bytes('pi'))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        iterator = api.iter_spectra(product, chunk_rows=1)
        first = next(iterator)
    with pytest.raises(ValueError, match='closed'):
        next(iterator)
    assert first.columns['COUNTS'][0, 0] == 1


def test_native_cross_product_diagnostics_do_not_impose_filtering_or_equality(tmp_path):
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes()),
                                          ('gti', 'SDD2', product_bytes('gti')),
                                          ('pi', 'SDD2', product_bytes('pi'))])
    report = science().inspect_solexs_archive(tmp_path, record)
    lc = next(p for p in report['products'] if p['kind'] == 'lc')
    pi = next(p for p in report['products'] if p['kind'] == 'pi')
    assert lc['gti_comparison']['finite_inside'] == 2
    assert lc['gti_comparison']['nan_inside'] == 1
    assert lc['gti_comparison']['filter_applied'] is False
    assert pi['lc_comparison']['time_rows_equal'] is True
    assert pi['lc_comparison']['nan_masks_equal'] is True
    assert pi['lc_comparison']['equal_sum_rows'] == 0
    assert pi['lc_comparison']['maximum_absolute_sum_difference'] == 4.5
    assert pi['lc_comparison']['quantity_equivalence'] == 'UNKNOWN'


def test_mismatched_pi_and_lc_coordinates_are_not_compared_as_aligned(tmp_path):
    def edit(hdus):
        hdus[1].data['TSTART'] += 100
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', product_bytes()),
                                          ('pi', 'SDD2', edit_fits(product_bytes('pi'), edit))])
    pi = next(p for p in science().inspect_solexs_archive(tmp_path, record)['products'] if p['kind'] == 'pi')
    assert pi['lc_comparison']['time_rows_equal'] is False
    assert pi['lc_comparison']['equal_sum_rows'] is None
    assert pi['lc_comparison']['nan_masks_equal'] is None


@pytest.mark.parametrize('field', ['max_member_bytes', 'max_fits_bytes', 'max_eager_rows', 'max_archive_members'])
def test_access_bounds_require_positive_integers(field):
    with pytest.raises(ValueError, match='positive integers'):
        science().AccessLimits(**{field: 0})


def test_zip_payload_crc_corruption_is_detected_beyond_registration(tmp_path):
    record, members = archive_fixture(tmp_path)
    path = tmp_path / ARCHIVE
    with zipfile.ZipFile(path) as z:
        info = z.getinfo(members[0])
        offset = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
    raw = bytearray(path.read_bytes())
    raw[offset + 12] ^= 1
    path.write_bytes(raw)
    (tmp_path / 'data/manifests/aditya_inventory.json').unlink()
    record = register_archives(tmp_path, [ARCHIVE])['files'][0]
    with pytest.raises(ValueError, match='Corrupt'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Corrupt ZIP CRC payload accepted')


def test_unregistered_and_unsupported_members_are_rejected(tmp_path):
    record, _ = archive_fixture(tmp_path)
    with pytest.raises(ValueError, match='registered'):
        with science().open_solexs_product(tmp_path, record, '../unknown.gz'):
            pytest.fail('Unregistered member accepted')
    path = tmp_path / ARCHIVE
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr(f'{PREFIX}/SDD2/unknown.gz', gzip.compress(product_bytes()))
    (tmp_path / 'data/manifests/aditya_inventory.json').unlink()
    record = register_archives(tmp_path, [ARCHIVE])['files'][0]
    with pytest.raises(ValueError, match='Unsupported'):
        science().inspect_solexs_archive(tmp_path, record)


def cli(root, output, cwd, chunk_rows=2):
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    return subprocess.run([sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'scripts/validate_solexs.py'),
                           '--root', str(root), '--config', 'config.json', '--output', output,
                           '--chunk-rows', str(chunk_rows)], cwd=cwd, env=env, text=True, capture_output=True)


def test_installed_science_cli_relocates_without_host_paths_or_raw_writes(tmp_path):
    root, moved, outside = [tmp_path / p for p in ['first', 'moved', 'outside']]
    outside.mkdir()
    archive_fixture(root, [('lc', 'SDD2', product_bytes()), ('pi', 'SDD2', product_bytes('pi'))])
    (root / 'config.json').write_text(json.dumps({'inventory_path': 'data/manifests/aditya_inventory.json',
                                                'archives': [ARCHIVE]}))
    before = hashlib.sha256((root / ARCHIVE).read_bytes()).hexdigest()
    first = cli(root, 'results/native.json', outside)
    assert first.returncode == 0, first.stderr
    shutil.copytree(root, moved, ignore=shutil.ignore_patterns('.cache', 'results'))
    relocated = cli(moved, 'results/native.json', outside, chunk_rows=1)
    assert relocated.returncode == 0, relocated.stderr
    assert (root / 'results/native.json').read_bytes() == (moved / 'results/native.json').read_bytes()
    assert str(root) not in (root / 'results/native.json').read_text()
    assert hashlib.sha256((root / ARCHIVE).read_bytes()).hexdigest() == before
    report = json.loads((root / 'results/native.json').read_text())
    assert report['schema_version'] == 1 and len(report['archives']) == 1
    assert report['policies']['utc_conversion'] == 'UNKNOWN_NOT_APPLIED'
    assert not list((root / '.cache').rglob('*.fits'))


def test_science_cli_rejects_raw_output_and_preserves_previous_report_on_failure(tmp_path):
    archive_fixture(tmp_path)
    (tmp_path / 'config.json').write_text(json.dumps({'inventory_path': 'data/manifests/aditya_inventory.json',
                                                    'archives': [ARCHIVE]}))
    before = (tmp_path / ARCHIVE).read_bytes()
    blocked = cli(tmp_path, ARCHIVE, tmp_path)
    assert blocked.returncode != 0
    assert (tmp_path / ARCHIVE).read_bytes() == before
    output = tmp_path / 'results/native.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text('previous report')
    (tmp_path / ARCHIVE).write_bytes(before + b'identity conflict')
    failed = cli(tmp_path, 'results/native.json', tmp_path)
    assert failed.returncode != 0
    assert output.read_text() == 'previous report'


def test_context_releases_owned_fits_columns_instead_of_retaining_table_copies(tmp_path):
    # Astropy retains full copies on FITS_rec destruction when cached HDU
    # columns still own references. Weak references test the actual lifetime,
    # without a platform-dependent RSS threshold or retaining an HDU data view.
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', product_bytes('pi'))])
    api = science()
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        native = next(api.iter_spectra(product, chunk_rows=1))
        column = weakref.ref(product.hdus['SPECTRUM'].columns['COUNTS'])
        assert column() is not None
    assert column() is None
    np.testing.assert_array_equal(native.columns['COUNTS'], [[1., 2., 3.]])


@pytest.mark.parametrize('kind', ['lc', 'pi'])
@pytest.mark.parametrize('card', ['extension_instrument', 'primary_detector'])
def test_conflicting_primary_and_extension_identity_is_rejected(tmp_path, kind, card):
    def edit(hdus):
        if card == 'extension_instrument':
            hdus[1].header['INSTRUME'] = 'OtherInstrument'
        else:
            hdus[0].header['FILTER'] = 'SDD1'
    record, members = archive_fixture(tmp_path, [(kind, 'SDD2', edit_fits(product_bytes(kind), edit))])
    with pytest.raises(ValueError, match='instrument|Detector'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Contradictory scientific identity accepted')


def test_variable_length_columns_are_rejected_before_shallow_chunk_copy(tmp_path):
    def edit(hdus):
        extra = fits.Column(name='EXTRA', format='PJ()',
                            array=np.array([np.array([1, 2]), np.array([3]), np.array([4, 5])], dtype=object))
        hdus[1] = fits.BinTableHDU.from_columns(hdus[1].columns + fits.ColDefs([extra]),
                                               header=hdus[1].header, name='SPECTRUM')
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', edit_fits(product_bytes('pi'), edit))])
    with pytest.raises(ValueError, match='Variable-length'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('Unsafe object-array scientific schema accepted')


@pytest.mark.parametrize('fmt,values,expected_min,expected_max', [
    ('B', [100, 99, 100], -1, 1), ('I', [32767, -32768], -65535, -65535),
    ('K', [2**63-1, -2**63], -(2**64-1), -(2**64-1)),
])
def test_integer_time_diagnostics_do_not_overflow(tmp_path, fmt, values, expected_min, expected_max):
    def edit(hdus):
        hdus[1] = fits.BinTableHDU.from_columns([
            fits.Column(name='TIME', format=fmt, array=values),
            fits.Column(name='COUNTS', format='D', array=np.arange(len(values)))], name='RATE')
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', edit_fits(product_bytes(), edit))])
    time = science().inspect_solexs_archive(tmp_path, record)['products'][0]['time']
    assert time['nonmonotonic_steps'] == 1
    assert time['step_min'] == expected_min
    assert time['step_max'] == expected_max


def test_integer_gti_duration_and_order_diagnostics_do_not_overflow(tmp_path):
    def edit(hdus):
        hdus[1] = fits.BinTableHDU.from_columns([
            fits.Column(name='START', format='I', array=[-32768]),
            fits.Column(name='STOP', format='I', array=[32767])], name='GTI')
    record, _ = archive_fixture(tmp_path, [('gti', 'SDD2', edit_fits(product_bytes('gti'), edit))])
    gti = science().inspect_solexs_archive(tmp_path, record)['products'][0]['gti']
    assert gti['sum_stop_minus_start_native'] == 65535
    def unsigned_edit(hdus):
        hdus[1] = fits.BinTableHDU.from_columns([
            fits.Column(name='START', format='B', array=[100, 90]),
            fits.Column(name='STOP', format='B', array=[101, 95])], name='GTI')
    unsigned = tmp_path / 'unsigned'
    record, _ = archive_fixture(unsigned, [('gti', 'SDD2', edit_fits(product_bytes('gti'), unsigned_edit))])
    assert science().inspect_solexs_archive(unsigned, record)['products'][0]['gti']['unordered_starts'] == 1


def test_unsupported_archive_processing_level_cannot_contain_an_accepted_l1_member(tmp_path):
    _, members = archive_fixture(tmp_path)
    l2 = ARCHIVE.replace('/l1/', '/l2/').replace('_L1_', '_L2_')
    path = tmp_path / l2
    path.parent.mkdir(parents=True)
    (tmp_path / ARCHIVE).rename(path)
    (tmp_path / 'data/manifests/aditya_inventory.json').unlink()
    record = register_archives(tmp_path, [l2])['files'][0]
    with pytest.raises(ValueError, match='L1'):
        with science().open_solexs_product(tmp_path, record, members[0]):
            pytest.fail('L2 archive with L1 scientific member accepted')


def test_integer_spectral_sum_comparison_does_not_overflow_or_round(tmp_path):
    def lc_edit(hdus):
        hdus[1] = fits.BinTableHDU.from_columns([
            fits.Column(name='TIME', format='D', array=[100., 101., 102.]),
            fits.Column(name='COUNTS', format='K', array=[1, 2, 3])], name='RATE')
    def pi_edit(hdus):
        columns = [c if c.name != 'COUNTS' else fits.Column(
            name='COUNTS', format='3K', array=[[2**62]*3, [0, 0, 0], [1, 2, 3]])
                   for c in hdus[1].columns]
        hdus[1] = fits.BinTableHDU.from_columns(columns, header=hdus[1].header, name='SPECTRUM')
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', edit_fits(product_bytes(), lc_edit)),
                                          ('pi', 'SDD2', edit_fits(product_bytes('pi'), pi_edit))])
    pi = next(p for p in science().inspect_solexs_archive(tmp_path, record)['products'] if p['kind'] == 'pi')
    assert pi['lc_comparison']['maximum_absolute_sum_difference'] == 3 * 2**62 - 1


@pytest.mark.parametrize('coordinate', [False, True])
def test_mixed_float_integer_pi_lc_comparisons_preserve_distinct_values(tmp_path, coordinate):
    def lc_edit(hdus):
        hdus[1].data['COUNTS'] = [float(2**53), 0., 0.]
        if coordinate:
            hdus[1].data['TIME'] = [float(2**53), float(2**53+2), float(2**53+4)]
    def pi_edit(hdus):
        columns = [fits.Column(name='COUNTS', format='3K', array=[[2**53+1, 0, 0], [0, 0, 0], [0, 0, 0]])
                   if c.name == 'COUNTS' else fits.Column(
                       name='TSTART', format='K', array=[2**53+1, 2**53+2, 2**53+4])
                   if c.name == 'TSTART' and coordinate else c for c in hdus[1].columns]
        hdus[1] = fits.BinTableHDU.from_columns(columns, header=hdus[1].header, name='SPECTRUM')
    record, _ = archive_fixture(tmp_path, [('lc', 'SDD2', edit_fits(product_bytes(), lc_edit)),
                                          ('pi', 'SDD2', edit_fits(product_bytes('pi'), pi_edit))])
    pi = next(p for p in science().inspect_solexs_archive(tmp_path, record)['products'] if p['kind'] == 'pi')
    if coordinate:
        assert pi['lc_comparison']['time_rows_equal'] is False
        assert pi['lc_comparison']['equal_sum_rows'] is None
    else:
        assert pi['lc_comparison']['equal_sum_rows'] == 2
        assert pi['lc_comparison']['maximum_absolute_sum_difference'] == 1


def test_mixed_gti_endpoints_keep_exact_values_and_invalid_span(tmp_path):
    def edit(hdus):
        hdus[1] = fits.BinTableHDU.from_columns([
            fits.Column(name='START', format='K', array=[2**53+1]),
            fits.Column(name='STOP', format='D', array=[float(2**53)])], name='GTI')
    record, _ = archive_fixture(tmp_path, [('gti', 'SDD2', edit_fits(product_bytes('gti'), edit))])
    gti = science().inspect_solexs_archive(tmp_path, record)['products'][0]['gti']
    assert gti['invalid_intervals'] == 1
    assert gti['sum_stop_minus_start_native'] == -1
    assert gti['intervals_native'] == [[2**53+1, float(2**53)]]


def test_mixed_exposure_elapsed_values_are_not_falsely_equal(tmp_path):
    def edit(hdus):
        columns = [fits.Column(name='TELAPSE', format='K', array=[2**53+1, 1, 1])
                   if c.name == 'TELAPSE' else c for c in hdus[1].columns]
        hdus[1] = fits.BinTableHDU.from_columns(columns, header=hdus[1].header, name='SPECTRUM')
        hdus[1].data['EXPOSURE'] = [float(2**53), 1., 1.]
    record, _ = archive_fixture(tmp_path, [('pi', 'SDD2', edit_fits(product_bytes('pi'), edit))])
    assert science().inspect_solexs_archive(tmp_path, record)['products'][0]['spectra']['exposure_equals_telapse_rows'] == 2


def test_spectral_partial_missingness_varying_channels_and_duplicate_ids_remain_visible(tmp_path):
    def edit(hdus):
        hdus[1].data['COUNTS'][0, 0] = np.nan
        hdus[1].data['CHANNEL'][2] += 1
        hdus[1].data['SPEC_NUM'][1] = 1
    record, members = archive_fixture(tmp_path, [('pi', 'SDD2', edit_fits(product_bytes('pi'), edit))])
    api = science()
    summary = api.inspect_solexs_archive(tmp_path, record)['products'][0]['spectra']
    assert summary['all_nan_rows'] == summary['partially_nan_rows'] == 1
    assert summary['channel_axis_constant'] is False
    assert summary['spec_num_duplicate_values'] == 1
    with api.open_solexs_product(tmp_path, record, members[0]) as product:
        native = next(api.iter_spectra(product))
        assert np.isnan(native.columns['COUNTS'][0, 0])
        np.testing.assert_array_equal(native.columns['CHANNEL'][2], [1, 2, 3])
        np.testing.assert_array_equal(native.columns['SPEC_NUM'], [1, 1, 3])


def test_science_cli_report_hardlink_cannot_modify_the_original_archive(tmp_path):
    archive_fixture(tmp_path)
    (tmp_path / 'config.json').write_text(json.dumps({'inventory_path': 'data/manifests/aditya_inventory.json',
                                                    'archives': [ARCHIVE]}))
    original = tmp_path / ARCHIVE
    before = original.read_bytes()
    output = tmp_path / 'results/native.json'
    output.parent.mkdir()
    os.link(original, output)
    result = cli(tmp_path, 'results/native.json', tmp_path)
    assert result.returncode == 0, result.stderr
    assert original.read_bytes() == before
    assert json.loads(output.read_text())['schema_version'] == 1
