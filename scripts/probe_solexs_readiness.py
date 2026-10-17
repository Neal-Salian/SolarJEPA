"""Offline native comparisons of validation samples and unapproved CALDB candidates.

This research probe establishes numerical relationships, never clock precedence,
GTI filtering, exposure correction, a physical energy mapping or flux conversion.
It uses the existing Phase C loader; mission policy remains in the gate report.
"""
from pathlib import Path
import argparse
import json
import re
import warnings

import numpy as np
from astropy.io import fits

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.data.solexs import (
    TIME_CARDS, iter_spectra, load_light_curve, open_solexs_product,
)
from solar_flare_jepa.data.storage import load_inventory, repository_relative_path


from solar_flare_jepa.data.solexs_comparison import candidate_slice, compare_native_rows


def inspect_candidate_response(paths, *, max_bytes=16 * 1024**2):
    """Bounded FITS metadata/grid diagnostics; return channel labels for comparison."""
    hdus, tables = {}, {}
    for name in ('rmf', 'arf', 'arf_pi'):
        path = Path(paths[name])
        if path.stat().st_size > max_bytes:
            raise ValueError('Candidate response byte limit exceeded')
        # Astropy accepts compressed FITS transparently. Restrict this probe to
        # standard uncompressed FITS so stat size also bounds the payload read.
        with path.open('rb') as stream:
            if not stream.read(80).startswith(b'SIMPLE  ='):
                raise ValueError('Candidate must be an uncompressed FITS file')
        with warnings.catch_warnings():
            warnings.simplefilter('error', fits.verify.VerifyWarning)
            with fits.open(path, mode='readonly', memmap=True, lazy_load_hdus=False) as opened:
                opened.verify('exception')
                if any(re.match(r'\d*[PQ]', str(c.format)) for h in opened
                       for c in getattr(h, 'columns', [])):
                    raise ValueError('Variable-length candidate response is unsupported')
                hdus[name] = {}
                for hdu in opened:
                    for key, verify in [('DATASUM', hdu.verify_datasum),
                                        ('CHECKSUM', hdu.verify_checksum)]:
                        if key in hdu.header and verify() != 1:
                            raise ValueError(f'Candidate FITS {key} failed')
                    columns = list(getattr(hdu, 'columns', []))
                    hdus[name][hdu.name] = dict(
                        rows=hdu.header.get('NAXIS2'),
                        units={c.name: c.unit for c in columns},
                        cards={k: hdu.header.get(k) for k in
                               ('CREATOR', 'FILTER', 'DETCHANS', 'CHANTYPE', 'TLMIN1')})
                    if columns:
                        tables[(name, hdu.name)] = {
                            c.name: np.array(hdu.data[c.name], copy=True) for c in columns}

    def grid(left, low, high, right, rlow, rhigh):
        lu, ru = hdus[left[0]][left[1]]['units'], hdus[right[0]][right[1]]['units']
        if lu[low] is None or lu[high] is None or (lu[low], lu[high]) != (ru[rlow], ru[rhigh]):
            return 'NOT_COMPARABLE_ENCODED_UNITS'
        l, r = tables[left], tables[right]
        if np.array_equal(l[low], r[rlow]) and np.array_equal(l[high], r[rhigh]):
            return 'EXACT_VALUES_AND_ENCODED_UNITS'
        return 'DIFFERENT_NATIVE_VALUES'

    eb, matrix = tables[('rmf', 'EBOUNDS')], tables[('rmf', 'MATRIX')]
    channels = eb['CHANNEL']
    response = matrix['MATRIX']
    summary = dict(
        accepted_for_application=False, hdus=hdus,
        response_channel_first_last=[int(channels[0]), int(channels[-1])],
        matrix_shape=list(response.shape), matrix_array_bytes=response.nbytes,
        matrix_nonfinite_cells=int((~np.isfinite(response)).sum()),
        matrix_negative_cells=int((response < 0).sum()),
        arf_incident_grid_comparison=grid(('arf', 'SPECRESP'), 'ENERG_LO', 'ENERG_HI',
                                         ('rmf', 'MATRIX'), 'ENERG_LO', 'ENERG_HI'),
        arf_pi_channel_grid_comparison=grid(('arf_pi', 'SPECRESP'), 'ENERG_LO', 'ENERG_HI',
                                           ('rmf', 'EBOUNDS'), 'E_MIN', 'E_MAX'))
    return summary, channels


def verified_inputs(root, manifest):
    """Resolve only explicitly pinned diagnostic inputs; never download resources."""
    previous = json.loads((root / repository_relative_path(
        manifest['previous_manifest'], root)).read_text())
    sources = previous['sources'] + manifest['sources']
    inputs = {}
    for name, relative in manifest['inputs'].items():
        relative = repository_relative_path(relative, root)
        records = [s for s in sources if s['path'] == relative]
        if len(records) != 1:
            raise ValueError('Missing or ambiguous candidate source identity')
        path, record = root / relative, records[0]
        if path.stat().st_size > 16 * 1024**2:
            raise ValueError('Candidate input byte limit exceeded')
        if path.stat().st_size != record['bytes'] or sha256_file(path) != record['sha256']:
            raise ValueError('Candidate source identity changed')
        inputs[name] = path
    return inputs


def build_probe(root, records, inputs):
    """Metadata-only sample comparison; the native loader owns archive safety."""
    root = Path(root).resolve()
    calibration, channels = inspect_candidate_response(inputs)
    bounds = np.loadtxt(inputs['bounds'])
    band = candidate_slice(bounds)
    cards = (*TIME_CARDS, 'TIMEPIXR', 'TREFPOS', 'TREFDIR', 'TIMEOFFS', 'TIMSYER',
             'TIMRDER', 'TIERABSO', 'TIERRELA', 'OBSORBIT', 'PLEPHEM',
             'DTCORR', 'GAINAPP', 'RESPFILE', 'ANCRFILE', 'NUMBAND', 'EXPOSURE')
    archives = []
    for record in sorted(records, key=lambda r: r['path']):
        names = [m['path'] for m in record['archive']['members'] if not m['is_directory']]
        members = {}
        for kind in ('gti', 'lc', 'pi'):
            matches = [name for name in names if name.endswith(f'SDD2_L1.{kind}.gz')]
            if len(matches) != 1:
                raise ValueError('This bounded diagnostic requires one SDD2 GTI/LC/PI sample')
            members[kind] = matches[0]
        clocks, lineage = {}, {}
        for kind in ('gti', 'lc'):
            with open_solexs_product(root, record, members[kind]) as product:
                clocks[kind] = {h.name: {k: h.header.get(k) for k in cards} for h in product.hdus}
                lineage[kind] = product.provenance
                if kind == 'lc':
                    light_curve = load_light_curve(product)
        with open_solexs_product(root, record, members['pi']) as product:
            clocks['pi'] = {h.name: {k: h.header.get(k) for k in cards} for h in product.hdus}
            lineage['pi'] = product.provenance
            comparison = compare_native_rows(
                light_curve.columns, (chunk.columns for chunk in iter_spectra(product, chunk_rows=1024)),
                band, channels)
        archives.append(dict(archive=record['path'], archive_sha256=record['sha256'],
                             clocks=clocks, source_lineage=lineage, comparison=comparison))
    return dict(
        schema_version=1, evidence='OBSERVED', representation='native_diagnostics_only',
        policies=dict(absolute_utc_conversion='UNKNOWN_NOT_APPLIED',
                      gti_filtering='UNKNOWN_NOT_APPLIED', exposure_correction='UNKNOWN_NOT_APPLIED',
                      calibration='UNKNOWN_NOT_APPLIED', gap_filling='NOT_APPLIED',
                      instrument_alignment='NOT_PERFORMED'),
        inputs={k: dict(path=repository_relative_path(p, root), bytes=p.stat().st_size,
                        sha256=sha256_file(p)) for k, p in sorted(inputs.items())},
        candidate_calibration=calibration,
        band_hypothesis=dict(
            tool_slice_start_inclusive_stop_exclusive=list(band),
            control_slice_start_inclusive_stop_exclusive=[band[0], band[1] + 1],
            nominal_thresholds_from_manual=[2, 22], text_table_encoded_unit=None,
            mapping_validated=False), archives=archives)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path, default=Path('configs/data/solexs_storage.json'))
    parser.add_argument('--sources', type=Path, default=Path('data/manifests/solexs_phase_d_sources.json'))
    args = parser.parse_args()
    root = args.root.resolve()
    config = json.loads((root / repository_relative_path(args.config, root)).read_text())
    sources = json.loads((root / repository_relative_path(args.sources, root)).read_text())
    inputs = verified_inputs(root, sources)
    inventory = load_inventory(root / repository_relative_path(config['inventory_path'], root))
    selected = [repository_relative_path(p, root) for p in config['archives']]
    if not selected or len(set(selected)) != len(selected):
        raise ValueError('Select distinct explicit registered archives')
    records = {r['path']: r for r in inventory['files']}
    report = build_probe(root, [records[p] for p in selected], inputs)
    verified_inputs(root, sources)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
