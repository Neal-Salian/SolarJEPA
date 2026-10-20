"""Verify generated presentation identities and independently check stationarity algebra."""
import json
from pathlib import Path

import numpy as np
from statsmodels.tsa.adfvalues import mackinnonp

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.presentation.eda import load_v1_frame, longest_complete_block
from solar_flare_jepa.presentation.comparison import verify_bundle, V1_RUN

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'docs/presentation/figure_manifest.json').read_text())
    identities = manifest['analysis_sources'] + [i for f in manifest['generated'] + manifest['reused'] for i in f['identities']]
    for row in identities:
        assert sha256_file(root / row['path']) == row['sha256'], row['path']
    expected = {
        'summary.json': '80eae588a706e4b4d84df0daa7e03dcfc54c53ee408d2d6aed30e4bcb9988daf',
        'per_origin.json': '133025c6921bcd575b727287b504550ff15e6e1d3ade8bcc39a5ff432056aa7f',
        'test_predictions.npz': '59bcd596fefd6b10edeec93a69d7172343d4ffb7dc120f98a5185c1e35a3da82'}
    for name, digest in expected.items():
        assert sha256_file(root / V1_RUN / name) == digest, name
    frame, evidence = load_v1_frame(root)
    saved = json.loads((root / 'docs/presentation/eda_evidence.json').read_text())
    assert evidence == {k: saved[k] for k in evidence}
    block = longest_complete_block(frame, '2024-05-01', '2024-07-22')
    differences = []
    for row in saved['stationarity']:
        raw = block[row['channel'] + '_flux'].to_numpy(float)
        values = {'raw_scaled': raw / raw.mean(), 'log_level': np.log10(raw),
                  'log_difference': np.diff(np.log10(raw))}[row['transform']]
        # Independently reconstruct the ADF OLS regression and its level coefficient t-statistic.
        p = row['adf_lags']; dy = np.diff(values)
        design = np.column_stack([values[p:-1], *[dy[p-j:-j] for j in range(1, p+1)], np.ones(len(dy)-p)])
        response = dy[p:]; beta = np.linalg.lstsq(design, response, rcond=None)[0]
        residual = response - design @ beta
        variance = residual @ residual / (len(response) - design.shape[1])
        standard_error = np.sqrt(variance * np.linalg.inv(design.T @ design)[0, 0])
        statistic = beta[0] / standard_error
        np.testing.assert_allclose(statistic, row['adf_statistic'], rtol=0, atol=2e-8)
        np.testing.assert_allclose(mackinnonp(statistic, regression='c', N=1), row['adf_p_value'], rtol=1e-6, atol=1e-35)
        # Independently reconstruct level-KPSS cumulative-residual and Bartlett HAC algebra.
        res = values - values.mean(); n = len(values); lags = row['kpss_lags']
        long_run = res @ res / n
        for lag in range(1, lags + 1):
            long_run += 2 * (1 - lag / (lags + 1)) * (res[lag:] @ res[:-lag]) / n
        kpss = np.sum(np.cumsum(res)**2) / n**2 / long_run
        np.testing.assert_allclose(kpss, row['kpss_statistic'], rtol=0, atol=2e-10)
        differences.extend([abs(float(statistic) - row['adf_statistic']), abs(float(kpss) - row['kpss_statistic'])])
    _, replay = verify_bundle(root, frame)
    stored = json.loads((root / 'docs/presentation/model_evidence.json').read_text())
    assert replay == stored
    notebook = json.loads((root / 'notebooks/presentation_goes_eda.ipynb').read_text())
    cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert all(c['execution_count'] is not None for c in cells)
    assert not any(o['output_type'] == 'error' for c in cells for o in c['outputs'])
    assert '/Users/' not in json.dumps(notebook)
    result = dict(status='PASS', manifest_identities=len(identities), native_files=evidence['source_files'],
        stationarity_independent_statistics=12, max_stationarity_absolute_discrepancy=max(differences),
        score_checks=replay['numerical_checks'], max_score_absolute_discrepancy=replay['max_absolute_discrepancy'],
        native_context_target_alignment=True, executed_notebook_cells=len(cells),
        v1_audited_artifact_hashes_unchanged=True)
    print(json.dumps(result, indent=2))
