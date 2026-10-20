"""Rebuild presentation evidence and assets from local V1 inputs only."""
import csv
import importlib.metadata
import json
from pathlib import Path

import pandas as pd

from solar_flare_jepa.data.download import sha256_file
from .eda import V1_CONFIG, load_v1_frame, longest_complete_block, stationarity_analysis, dependence_analysis
from .comparison import V1_RUN, SEEDS, FAMILIES, verify_bundle
from .figures import eda_figures, comparison_figures, architecture_figure, LABELS, ORDER


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def package_versions(names):
    """Record absent optional tools without making figure generation depend on them."""
    result = {}
    for name in names:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def write_eda_evidence(root, evidence, block, stationarity, dependence):
    destination = Path(root) / 'docs/presentation'; destination.mkdir(parents=True, exist_ok=True)
    report = dict(evidence, diagnostic_block=dict(start_utc=block.index[0].isoformat(),
        end_exclusive_utc=(block.index[-1] + pd.Timedelta(minutes=1)).isoformat(), rows=len(block),
        selection='earliest longest jointly valid consecutive training run; no imputation'),
        stationarity=stationarity, dependence=dependence)
    write_json(destination / 'eda_evidence.json', report)
    fields = ['channel', 'transform', 'input_rows', 'adf_statistic', 'adf_p_value', 'adf_lags',
              'adf_nobs', 'kpss_statistic', 'kpss_p_relation', 'kpss_p_value', 'kpss_lags']
    with (destination / 'stationarity.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fields, extrasaction='ignore', lineterminator='\n'); writer.writeheader(); writer.writerows(stationarity)
    return report


def build_presentation(root):
    root = Path(root).resolve(); output = root / 'docs/figures/presentation'
    frame, data = load_v1_frame(root)
    config = json.loads((root / V1_CONFIG).read_text()); train = config['splits'][0]
    block = longest_complete_block(frame, train['start_utc'], train['end_utc'])
    stationarity, dependence = stationarity_analysis(block), dependence_analysis(block)
    write_eda_evidence(root, data, block, stationarity, dependence)
    summary, replay = verify_bundle(root, frame)
    write_json(root / 'docs/presentation/model_evidence.json', replay)
    columns = ['model_id', 'label', 'seeds', 'mean_pinball', 'log_mae', 'coverage_central_50',
               'coverage_central_90', 'width_central_50', 'width_central_90', 'mean_fit_seconds', 'mean_predict_seconds']
    table = []
    for model in ORDER + sorted(set(replay['grouped']) - set(ORDER)):
        if model not in replay['grouped']: continue
        scores = replay['grouped'][model]
        ids = [f'{model}_seed{s}' for s in SEEDS] if model in FAMILIES else [model]
        table.append(dict(model_id=model, label=LABELS.get(model, model), seeds='17,29,43' if model in FAMILIES else '',
            **{k: scores.get(k) for k in columns[3:9]},
            mean_fit_seconds=sum(summary['fits'][k]['fit_seconds'] for k in ids) / len(ids),
            mean_predict_seconds=sum(summary['scores']['test'][k]['predict_seconds'] for k in ids) / len(ids)))
    with (root / 'docs/presentation/model_metrics.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, columns, lineterminator='\n'); writer.writeheader(); writer.writerows(table)
    entries = eda_figures(frame, block, dependence, data, output)
    entries += comparison_figures(summary, replay, output)
    entries += architecture_figure(output)
    # Reuse without copying or altering historical images. Verify exact runner identities.
    reused = []
    for name, caption in [
        ('fig_lead_log_mae.png', 'Single validation-selected JEPA seed 43, GJR-t, ARIMA(2,1,0), and persistence. '
         'Not the neural seed-mean plot; prefer new comparison_lead_errors for the main slide.'),
        ('fig_fan_largest_rise.png', 'Retrospective largest XRS-B rise: August 8 19:00 UTC, ×21.0776. '
         'Validation-selected JEPA seed 43, GJR-t and ARIMA(2,1,0); all upper 90% bands miss the peak. '
         'Horizontal positive lead labels denote target-bin ends. This is a difficult selected example, not average skill.'),
        ('fig_coverage.png', 'All 16 probabilistic model/seed records; marginal 50%/90% coverage. Dense appendix asset.')]:
        path = root / 'docs/figures/v1' / name
        if sha256_file(path) != sha256_file(root / V1_RUN / name):
            raise ValueError('Historical figure identity mismatch: ' + name)
        reused.append(dict(files=['docs/figures/v1/' + name], caption=caption, source=[V1_RUN + '/' + name]))
    reused.append(dict(files=['docs/figures/v1/jepa_training_curves.png'],
        caption='Original 3×4 history/collapse-diagnostic grid; preserved, appendix only. Compact new histories figure preferred.',
        source=[V1_RUN + '/summary.json', 'docs/V1_RESULTS.md']))
    for entry in entries + reused:
        entry['identities'] = [dict(path=relative, bytes=(root / relative).stat().st_size,
                                   sha256=sha256_file(root / relative)) for relative in entry['files']]
    source_paths = [V1_CONFIG, 'configs/experiments/v1_models.json', 'requirements-v1-lock.txt',
        'requirements-presentation.txt', 'scripts/build_presentation.py',
        'scripts/verify_presentation.py', 'notebooks/presentation_goes_eda.ipynb',
        'src/solar_flare_jepa/training/jepa.py',
        'src/solar_flare_jepa/data/goes.py', 'src/solar_flare_jepa/data/foundation.py',
        'src/solar_flare_jepa/data/eda.py', 'src/solar_flare_jepa/data/goes_acquisition.py',
        'src/solar_flare_jepa/evaluation/probabilistic.py']
    source_paths += ['src/solar_flare_jepa/presentation/' + name for name in
                     ('__init__.py', 'eda.py', 'comparison.py', 'figures.py', 'pipeline.py')]
    environment = package_versions(
        ('numpy', 'pandas', 'xarray', 'netCDF4', 'matplotlib', 'statsmodels', 'scipy', 'torch', 'arch', 'nbclient', 'ipykernel'))
    write_json(root / 'docs/presentation/figure_manifest.json', dict(
        base_commit='644648f7d555fcbcb3eed4495d37fecffdd1863a',
        generated=entries, reused=reused, packages=environment,
        analysis_sources=[dict(path=p, sha256=sha256_file(root / p)) for p in source_paths]))
    return dict(eda_figures=8, new_figures=len(entries), reused_figures=len(reused),
                stationarity_rows=len(stationarity), model_count=replay['model_count'],
                numerical_checks=replay['numerical_checks'], max_absolute_discrepancy=replay['max_absolute_discrepancy'])
