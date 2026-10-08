"""Bounded offline native diagnostics, with the existing scientific gate intact.

No training dataset, UTC coordinate, rate/flux conversion or calibration is
constructed here. Existing SoLEXS access owns archive/FITS parsing and integrity.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil

import numpy as np

from .download import sha256_file
from .inspect import write_json
from .solexs import inspect_solexs_archive, iter_spectra, load_light_curve, open_solexs_product
from .storage import ROLE, load_inventory, repository_relative_path, verify_inventory


GATE = 'BLOCKED_FOR_PHASE_E'


@dataclass(frozen=True)
class ExplorationLimits:
    max_archives: int = 4
    max_plot_points: int = 2048
    max_plot_spectra: int = 4
    max_plot_channels: int = 1024
    chunk_rows: int = 1024

    def __post_init__(self):
        ceilings = dict(max_archives=4, max_plot_points=65536, max_plot_spectra=32,
                        max_plot_channels=4096, chunk_rows=8192)
        for name, value in asdict(self).items():
            if type(value) is not int or value <= 0:
                raise ValueError('Exploration limits must be positive integers')
            if value > ceilings[name]:
                raise ValueError(f'{name} exceeds the bounded exploration limit')


def validate_request(*, representation='native', train=False):
    """Fail closed at the exploration boundary; native semantics remain native."""
    if representation != 'native':
        raise ValueError('Only native diagnostics are supported; semantic conversion is unresolved')
    if type(train) is not bool or train:
        raise ValueError(f'SoLEXS sequence training is {GATE}')


def _identity(root, path):
    relative = repository_relative_path(path, root)
    source = root / relative
    if not source.is_file():
        raise ValueError(f'Missing exploration input: {relative}')
    return dict(path=relative, bytes=source.stat().st_size, sha256=sha256_file(source))


def _verify_identity(root, expected):
    if _identity(root, expected['path']) != expected:
        raise ValueError('Exploration input identity changed before publication')


def _source_identity(archive, product):
    kind = product['kind']
    table_name = {'lc': 'RATE', 'pi': 'SPECTRUM', 'gti': 'GTI'}[kind]
    table = next(h for h in product['hdus'] if h['name'] == table_name)
    units = {c['name']: c['unit'] for c in table['columns']}
    return dict(
        mission='Aditya-L1', platform='Aditya-L1', instrument='SoLEXS',
        channels=list(units), native_units=[u if u is not None else 'UNKNOWN' for u in units.values()],
        time_basis='NATIVE_NUMERIC_COORDINATES; absolute UTC/bin support UNKNOWN_NOT_APPLIED',
        sampling='Native coordinate diagnostics only; completed-bin availability UNKNOWN',
        measurement_type='native_counts' if kind in ('lc', 'pi') else 'native_gti_intervals',
        quality_status='OBSERVED native numeric diagnostics; scientific QC/GTI policy UNKNOWN_NOT_APPLIED',
        preprocessing='Native values/missingness preserved; UTC/calibration/GTI/rate conversion NOT_APPLIED',
        column_units=units,
        native_details=dict(
            time_basis=dict(type='native_numeric_coordinates', metadata=product['time_metadata'],
                            warnings=product['warnings'], converted_utc=None,
                            absolute_clock_policy='UNKNOWN_NOT_APPLIED',
                            bin_position='UNKNOWN' if kind == 'lc' else 'NOT_ESTABLISHED_FOR_TRAINING'),
            sampling=product.get('time', dict(intervals=product['rows'], continuous_exposure=None)),
            quality=dict(numeric_diagnostics=product['numeric'], scientific_qc='UNKNOWN_NOT_APPLIED',
                         gti_filtering='UNKNOWN_NOT_APPLIED'),
            preprocessing=dict(utc_conversion=False, calibration=False, gap_filling=False,
                               rate_conversion=False, missing_values='PRESERVED')),
        validation_status='OBSERVED_NATIVE', target_definition='UNDEFINED_FOR_TRAINING',
        training_gate=GATE, dataset_role=ROLE, product_kind=kind,
        detector=product['detector'], provenance=product['provenance'],
        nominal_observation_date=archive['nominal_observation_date'],
        nominal_date_evidence=archive['identity_evidence']['nominal_observation_date'])


def _detectors(archives):
    grouped = {}
    for archive in archives:
        for product in archive['products']:
            entry = grouped.setdefault(product['detector']['value'], dict(kinds=set(), evidence=set()))
            entry['kinds'].add(product['kind'])
            entry['evidence'].add(product['detector']['evidence'])
    return [dict(value=value, product_kinds=sorted(entry['kinds']),
                 association_evidence=sorted(entry['evidence']),
                 native_sequence_available=bool({'lc', 'pi'} & entry['kinds']),
                 absence_reason='UNKNOWN' if not {'lc', 'pi'} & entry['kinds'] else None)
            for value, entry in sorted(grouped.items())]


def _candidate_tasks(detectors, remaining):
    """Candidate definitions are future research proposals, never executed tasks."""
    candidates = [
        ('native_lc_forecast', 'Native LC COUNTS; encoded units retained, correction state UNKNOWN',
         'Future native COUNTS on the same detector',
         'LC TIME is native; absolute clock, bin position and completed-bin availability UNKNOWN',
         'Preserve NaNs; scientific quality and GTI/exposure policy unresolved',
         'Establish quantity/correction comparability and chronological causal support first',
         'Future masked MAE/RMSE in native encoded units, detector-separated chronological holdout'),
        ('native_pi_forecast', 'Native Type-II CHANNEL/COUNTS vectors and TSTART/TELAPSE/EXPOSURE',
         'Future raw COUNTS vectors on unchanged native CHANNEL labels',
         'Native TSTART only; integration availability and absolute clock require mission policy',
         'Preserve all/partial NaN rows and native exposure; no correction or GTI filter',
         'Stable detector/channel semantics, approved timing/exposure and correction representation required',
         'Future per-channel masked native errors on chronological holdout; no flux interpretation'),
        ('native_pi_reconstruction', 'Native CHANNEL/COUNTS vectors',
         'Artificially hidden native channel entries; no physical incident spectrum target',
         'No time conversion; chronological independence would still be required for split design',
         'Artificial masks must remain distinct from native missingness/quality masks',
         'Scientific semantics and training permission required even for an artificial reconstruction task',
         'Future held-out-channel native errors; cannot establish forecast or physical spectrum skill'),
        ('calibrated_irradiance_forecast', 'Incident irradiance is UNKNOWN; only native counts observed',
         'UNDEFINED until approved response/correction chain and physical units are established',
         'Absolute UTC and completed-bin availability UNKNOWN',
         'Approved HK/correction, response/indexing, gain and quality/background provenance required',
         'Native counts cannot be relabelled as calibrated irradiance',
         'UNDEFINED until physical targets, uncertainty and quality reference exist'),
        ('solexs_goes_alignment', 'Distinct SoLEXS counts and GOES irradiance quantities',
         'UNDEFINED; no cross-instrument equivalent quantity is assumed',
         'Clock precedence, bin support and observer/light-time convention unresolved',
         'Source-specific quality, missingness and calibration must survive alignment',
         'Resolve timing and distinct energy/response semantics; no nominal-date alignment',
         'UNDEFINED until approved alignment/target contract and independent chronological holdout'),
        ('flare_event_forecast', 'No SoLEXS flare event labels established by this exploration',
         'UNDEFINED event onset/class labels',
         'Absolute event chronology and observation availability UNKNOWN',
         'A finite/NaN count mask is not a flare label',
         'Require authoritative event definitions/labels and source-applicable quality/timing',
         'UNDEFINED; native plots and continuous error cannot establish event classification skill'),
    ]
    return [dict(id=ident, status='EXPERIMENTAL_UNCALIBRATED', measured_quantity=measured,
                 target_definition=target, timing=timing, quality=quality, assumptions=assumptions,
                 evaluation=evaluation, evaluation_executed=False, training_allowed=False,
                 gate_disposition=GATE, required_evidence=remaining or ['Mission-approved scientific contract'],
                 available_detectors=[d['value'] for d in detectors if d['native_sequence_available']])
            for ident, measured, target, timing, quality, assumptions, evaluation in candidates]


def _indices(rows, cap):
    return np.linspace(0, rows - 1, min(rows, cap), dtype=np.int64) if rows else np.array([], dtype=np.int64)


def _plot(root, record, product_summary, output, limits):
    """Copy a bounded display subset through the existing native loaders."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    kind = product_summary['kind']
    if kind not in ('lc', 'pi'):
        return None
    member = product_summary['provenance']['member']
    detector = product_summary['detector']['value']
    row_indices = _indices(product_summary['rows'],
                           limits.max_plot_points if kind == 'lc' else limits.max_plot_spectra)
    rows = []
    with open_solexs_product(root, record, member) as product:
        if kind == 'lc':
            native = load_light_curve(product)
            x, y = native.columns['TIME'][row_indices], native.columns['COUNTS'][row_indices]
            units = native.units
        else:
            offset = 0
            for chunk in iter_spectra(product, chunk_rows=limits.chunk_rows):
                if chunk.columns['COUNTS'].shape[1] > limits.max_plot_channels:
                    raise ValueError('Native plot channel-count limit exceeded')
                selected = row_indices[(row_indices >= offset) & (row_indices < offset + len(chunk.columns['TSTART']))]
                for index in selected:
                    local = int(index - offset)
                    rows.append((chunk.columns['CHANNEL'][local].copy(), chunk.columns['COUNTS'][local].copy(),
                                 chunk.columns['TSTART'][local].item(), int(index)))
                offset += len(chunk.columns['TSTART'])
            units = {c.name: c.unit for c in product.hdus[product.table_name].columns}
    filename = f"{record['sha256']}_{detector}_{kind}.png"
    destination = output / filename
    fig, ax = plt.subplots(figsize=(11, 4.5), constrained_layout=True)
    try:
        if kind == 'lc':
            ax.scatter(x, y, s=3)
            ax.set_xlabel(f"Native TIME (encoded unit: {units.get('TIME') or 'unset'}); UTC UNKNOWN")
        else:
            for channel, counts, start, index in rows:
                ax.plot(channel, counts, linewidth=.8, label=f'row {index}; native TSTART {start}')
            ax.set_xlabel('Native CHANNEL label; energy mapping UNKNOWN')
            if rows:
                ax.legend(fontsize=7)
        ax.set_ylabel(f"Native COUNTS (encoded unit: {units.get('COUNTS') or 'unset'})")
        ax.set_title(f"EXPERIMENTAL_UNCALIBRATED | {detector} {kind.upper()}\n"
                     f"Nominal filename date {record['nominal_observation_date']} | calibration not applied\n"
                     'Bounded native row subset; full missingness and coverage diagnostics in JSON', fontsize=10)
        ax.grid(alpha=.2)
        fig.savefig(destination, dpi=120, metadata={'Software': 'SolarJEPA native exploration'})
    finally:
        plt.close(fig)
    return dict(path=repository_relative_path(destination, root), sha256=sha256_file(destination),
                bytes=destination.stat().st_size, status='EXPERIMENTAL_UNCALIBRATED',
                product_kind=kind, detector=product_summary['detector'],
                provenance=product_summary['provenance'], displayed_rows=len(row_indices),
                displayed_row_indices=row_indices.tolist(), total_native_rows=product_summary['rows'],
                selection='uniform_native_row_indices_no_aggregation',
                axis_semantics=dict(timing='Native coordinates only; UTC UNKNOWN_NOT_APPLIED',
                                    quantity='Native COUNTS; calibration UNKNOWN_NOT_APPLIED',
                                    channels='Native CHANNEL; energy mapping UNKNOWN_NOT_APPLIED'))


def explore_solexs(config_path, root, output_dir, *, representation='native', train=False):
    """Verify selected archives, then publish to one new ignored directory.

    Config/input/output paths are root-contained and provenance is portable.
    Existing directories (including symlinks) are rejected before reading science.
    Failure removes only the newly created run directory, preserving all inputs.
    """
    validate_request(representation=representation, train=train)
    root = Path(root).resolve()
    output_path = repository_relative_path(output_dir, root)
    if not output_path.startswith('results/p2_solexs/'):
        raise ValueError('Output must be a unique directory under results/p2_solexs/')
    destination = root / output_path
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Exploration output directory already exists; choose a unique path')
    config_identity = _identity(root, config_path)
    config = json.loads((root / config_identity['path']).read_text())
    if config.get('schema_version') != 1:
        raise ValueError('Unsupported native exploration config schema')
    try:
        limits = ExplorationLimits(**config.get('limits', {}))
    except TypeError as exc:
        raise ValueError('Unsupported exploration limits') from exc
    requested = [repository_relative_path(p, root) for p in config['archives']]
    if len(requested) > limits.max_archives:
        raise ValueError('Selected archive-count limit exceeded')
    if not requested or len({p.casefold() for p in requested}) != len(requested):
        raise ValueError('Select distinct explicit registered native archives')
    inventory_identity = _identity(root, config['inventory_path'])
    gate_identity = _identity(root, config['gate_path'])
    if gate_identity['sha256'] != config['gate_sha256']:
        raise ValueError('Scientific gate identity differs from pinned config')
    gate = json.loads((root / gate_identity['path']).read_text())
    if gate.get('gate') != GATE:
        raise ValueError('Unexpected scientific gate; this native-only milestone requires review')
    remaining = gate.get('minimum_remaining_evidence', gate.get('gate_requirements', []))
    inventory = load_inventory(root / inventory_identity['path'])
    registered = {r['path']: r for r in inventory['files']}
    if not set(requested).issubset(registered):
        raise ValueError('Config selects an archive absent from registered inventory')
    records = [registered[p] for p in sorted(requested)]
    # The existing API verifies SHA/size/listing, every ZIP member CRC, nested
    # gzip integrity, FITS structure/checksums, and summarizes all native rows.
    archives = [inspect_solexs_archive(root, record, chunk_rows=limits.chunk_rows) for record in records]
    detectors = _detectors(archives)
    report = dict(schema_version=1, status='OBSERVED_NATIVE', dataset_role=ROLE,
                  representation='native_values_and_encoded_metadata',
                  gate=dict(status=GATE, provenance=gate_identity, remaining_evidence=remaining),
                  limits=asdict(limits), provenance=dict(
                      config=config_identity, inventory=inventory_identity,
                      runtime_sources={
                          'solar_flare_jepa.data.solexs_exploration': dict(sha256=sha256_file(Path(__file__))),
                          'solar_flare_jepa.data.solexs': dict(
                              sha256=sha256_file(Path(inspect_solexs_archive.__code__.co_filename)))}),
                  policies=dict(utc_conversion='UNKNOWN_NOT_APPLIED', calibration='UNKNOWN_NOT_APPLIED',
                                gti_filtering='UNKNOWN_NOT_APPLIED', gap_filling='NOT_APPLIED',
                                cross_source_alignment='NOT_APPLIED', scientific_validation='NOT_ESTABLISHED'),
                  archives=archives, detectors=detectors,
                  source_identities=[_source_identity(a, p) for a in archives for p in a['products']],
                  housekeeping=dict(present_in_selected_archives=any(m['path'].endswith('.hk.gz')
                          for a in archives for m in a['members']),
                                    mission_availability='UNKNOWN', compatibility='UNKNOWN'),
                  calibration=dict(applied=False, compatibility='UNKNOWN',
                                   policy='Prior official/CALDB identity does not establish applicability'),
                  candidate_tasks=_candidate_tasks(detectors, remaining),
                  training=dict(allowed=False, executed=False, metrics=None, reason=GATE), plots=[])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # Exclusive reservation prevents another run overwriting this one.
    try:
        for record, archive in zip(records, archives):
            for product in archive['products']:
                plot = _plot(root, record, product, destination, limits)
                if plot is not None:
                    report['plots'].append(plot)
        verify_inventory(dict(inventory, files=records, missing_coverage=[]), root)
        for identity in (config_identity, inventory_identity, gate_identity):
            _verify_identity(root, identity)
        write_json(destination / 'report.json', report)
    except BaseException:
        shutil.rmtree(destination)
        raise
    return report
