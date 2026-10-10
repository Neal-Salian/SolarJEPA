"""Presentation-specific scientific safeguards, independent of model fitting."""
import numpy as np
import pandas as pd
import pytest

from solar_flare_jepa.presentation.eda import longest_complete_block, stationarity_analysis
from solar_flare_jepa.presentation.comparison import independent_scores, mean_seed_scores, verify_bundle


def test_contiguous_training_block_never_bridges_absent_or_rejected_bins():
    ix = pd.date_range('2024-05-01', periods=12, freq='min', tz='UTC').delete(4)
    f = pd.DataFrame({'xrsa_flux': 1., 'xrsb_flux': 2.}, index=ix)
    f.loc[ix[1], 'xrsa_flux'] = np.nan
    # Long held-out tail must not extend the diagnostic block.
    b = longest_complete_block(f, '2024-05-01', '2024-05-01T00:09Z')
    assert b.index.equals(ix[4:8])
    assert len(b) == 4
    assert (np.diff(b.index.asi8) == 60_000_000_000).all()


def test_block_uses_earliest_tie_and_rejects_nonpositive_values():
    ix = pd.date_range('2024-05-01', periods=7, freq='min', tz='UTC')
    f = pd.DataFrame({'xrsa_flux': [1, 1, 0, 1, 1, np.inf, 1], 'xrsb_flux': 2.}, index=ix)
    assert longest_complete_block(f, '2024-05-01', '2024-05-02').index.equals(ix[:2])


def test_stationarity_analysis_refuses_gaps_and_reports_actual_test_parameters():
    rng = np.random.default_rng(8)
    ix = pd.date_range('2024-05-01', periods=800, freq='min', tz='UTC')
    f = pd.DataFrame({'xrsa_flux': 10 ** rng.normal(-7, .1, 800),
                      'xrsb_flux': 10 ** rng.normal(-6, .1, 800)}, index=ix)
    with pytest.raises(ValueError, match='contiguous'):
        stationarity_analysis(f.drop(ix[4]))
    rows = stationarity_analysis(f)
    assert len(rows) == 6
    for r in rows:
        assert r['adf_lags'] == 30 and r['adf_regression'] == 'c'
        assert r['adf_autolag'] is None and 0 <= r['adf_p_value'] <= 1
        assert r['adf_p_interpretation'] == ('lower_approximation_cutoff_returned_zero'
                                           if r['adf_p_value'] == 0 else 'MacKinnon_approximation')
        assert r['kpss_regression'] == 'c' and r['kpss_p_relation'] in ('=', '<', '>')
        assert r['input_rows'] == (799 if r['transform'] == 'log_difference' else 800)


def test_independent_log_scores_have_hand_calculated_pinball_and_coverage():
    # y=0 dex, forecast=[-1,-.5,0,.5,1] dex: mean pinball=(.05+.125+0+.125+.05)/5=.07
    y = np.ones((2, 3, 2))
    q = np.broadcast_to(10. ** np.array([-1, -.5, 0, .5, 1]), (*y.shape, 5)).copy()
    mask = np.ones_like(y, bool)
    scores, losses = independent_scores(y, mask, y, q)
    assert scores['mean_pinball'] == pytest.approx(.07)
    assert scores['log_mae'] == 0 and scores['coverage_central_90'] == 1
    assert scores['width_central_50'] == 1 and scores['width_central_90'] == 2
    assert losses['mean_pinball'] == pytest.approx([.07, .07])
    assert scores['by_lead']['mean_pinball'] == pytest.approx([.07] * 3)


def test_scores_ignore_masked_cells_but_reject_invalid_scored_predictions():
    y = np.ones((1, 2, 1)); mask = np.array([[[True], [False]]])
    point = y.copy(); point[0, 1, 0] = np.nan
    s, _ = independent_scores(y, mask, point)
    assert s['log_mae'] == 0 and 'mean_pinball' not in s
    point[0, 0, 0] = 0
    with pytest.raises(ValueError, match='positive'):
        independent_scores(y, mask, point)


def test_quantile_order_and_shapes_cannot_silently_change_comparison():
    y = np.ones((1, 2, 1)); m = np.ones_like(y, bool)
    with pytest.raises(ValueError, match='shape'):
        independent_scores(y, m, np.ones((2, 1, 1)))
    q = np.broadcast_to([1., 2., 3., 4., 5.], (*y.shape, 5)).copy()
    q[0, 0, 0] = q[0, 0, 0, ::-1]
    with pytest.raises(ValueError, match='ordered'):
        independent_scores(y, m, y, q)


def test_seed_aggregation_averages_losses_not_forecasts_and_requires_all_seeds():
    rows = {f'supervised_seed{s}': {'log_mae': v, 'mean_pinball': v / 2,
                                   'by_lead': {'log_mae': [v, v]}}
            for s, v in zip((17, 29, 43), (1., 2., 6.))}
    avg = mean_seed_scores(rows, 'supervised')
    assert avg['log_mae'] == 3 and avg['mean_pinball'] == 1.5
    assert avg['by_lead']['log_mae'] == [3., 3.]
    del rows['supervised_seed43']
    with pytest.raises(ValueError, match='seed'):
        mean_seed_scores(rows, 'supervised')


@pytest.mark.parametrize('mismatch', ['model', 'origin'])
def test_bundle_refuses_incompatible_model_or_origin_support(tmp_path, mismatch):
    import json
    from pathlib import Path
    from solar_flare_jepa.experiments.config import load_config
    from solar_flare_jepa.presentation.comparison import V1_RUN
    run = tmp_path / V1_RUN; run.mkdir(parents=True)
    configs = tmp_path / 'configs/experiments'; configs.mkdir(parents=True)
    source_config = Path(__file__).resolve().parents[1] / 'configs/experiments/v1_goes_2024.json'
    (configs / 'v1_goes_2024.json').write_bytes(source_config.read_bytes())
    (configs / 'v1_models.json').write_text('{}')
    (run / 'summary.json').write_text(json.dumps(dict(dev_mode=False, quick=False, status='complete',
        config=load_config(source_config), models_config={}, scores={'test': {'m': {}}})))
    (run / 'per_origin.json').write_text(json.dumps({'test': dict(losses={'m': {}}, origin_ids=['a'])}))
    np.savez(run / 'test_predictions.npz', model_ids=['bad' if mismatch == 'model' else 'm'],
             origin_ids=['bad'], targets=np.ones((1, 30, 2)), target_mask=np.ones((1, 30, 2), bool))
    with pytest.raises(ValueError, match='support mismatch'):
        verify_bundle(tmp_path)


def test_figure_generation_metadata_does_not_require_optional_notebook_tools(monkeypatch):
    from solar_flare_jepa.presentation import pipeline
    real_version = pipeline.importlib.metadata.version
    def version(name):
        if name in ('nbclient', 'ipykernel'):
            raise pipeline.importlib.metadata.PackageNotFoundError(name)
        return real_version(name)
    monkeypatch.setattr(pipeline.importlib.metadata, 'version', version)
    versions = pipeline.package_versions(('numpy', 'nbclient', 'ipykernel'))
    assert versions['numpy'] == np.__version__
    assert versions['nbclient'] is None and versions['ipykernel'] is None
