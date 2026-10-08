import importlib
import importlib.util

import numpy as np
import pytest

from test_solexs_provisional_sequences import native
from solar_flare_jepa.provisional.sequences import sequence_from_native, make_windows, fit_normalization


def api():
    name='solar_flare_jepa.provisional.baselines'
    assert importlib.util.find_spec(name), 'numerical baselines missing'
    return importlib.import_module(name)


def fitted():
    s=sequence_from_native(native(np.arange(20,dtype=float)))
    w=make_windows(s,0,20,context=4,horizon=2,stride=2)
    return api().fit_baselines(w,fit_normalization(s,0,20))


def test_deterministic_baselines_use_only_context_at_prediction():
    models=fitted()
    x=np.array([[[1.],[2.],[3.],[4.]]])
    m=np.ones_like(x,dtype=bool)
    expected={'persistence':[4,4], 'training_mean':[9.5,9.5],
              'trailing_mean':[2.5,2.5], 'fixed_ar1':[4.55,5.045]}
    for name,values in expected.items():
        p=models[name].predict(x,m)
        np.testing.assert_allclose(p[0,:,0],values)
        np.testing.assert_array_equal(p,models[name].predict(x,m))
    ridge=models['direct_ridge'].predict(x,m)
    assert ridge.shape==(1,2,1) and np.isfinite(ridge).all()
    np.testing.assert_array_equal(ridge,fitted()['direct_ridge'].predict(x,m))
    assert models['direct_ridge'].parameters['fit_support']=='train_windows_only'


def test_masked_context_is_preserved_and_ridge_fails_unsupported_context():
    models=fitted()
    x=np.array([[[1.],[2.],[3.],[np.nan]]])
    m=np.array([[[True],[True],[True],[False]]])
    np.testing.assert_array_equal(models['persistence'].predict(x,m)[0,:,0],[3,3])
    with pytest.raises(ValueError): models['direct_ridge'].predict(x,m)
    with pytest.raises(ValueError): models['persistence'].predict(x,np.zeros_like(m))


def test_metrics_apply_target_mask_and_report_prediction_coverage():
    y=np.array([[[1.],[np.nan]],[[5.],[7.]]])
    p=np.array([[[2.],[999.]],[[3.],[8.]]])
    mask=np.isfinite(y)
    reference=np.array([[[0.],[0.]],[[0.],[0.]]])
    metrics=api().evaluate(y,p,mask,reference)
    assert metrics['mae']==pytest.approx(4/3)
    assert metrics['rmse']==pytest.approx(np.sqrt(2))
    assert metrics['mae_skill_vs_persistence']==pytest.approx(1-4/13)
    assert metrics['valid_target_cells']==3 and metrics['total_target_cells']==4
    assert metrics['prediction_coverage']==1
    assert metrics['target_coverage']==.75
    assert metrics['unit']=='UNKNOWN_UNENCODED_NATIVE_VALUE'
    assert metrics['scientific_label']=='EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED'


def test_invalid_output_cannot_hide_behind_mask_or_reduce_coverage():
    with pytest.raises(ValueError):
        api().evaluate(np.array([[[1.],[np.nan]]]),np.array([[[1.],[np.inf]]]),np.array([[[True],[False]]]))
    with pytest.raises(ValueError):
        api().evaluate(np.ones((1,2,1)),np.ones((1,2,1)),np.zeros((1,2,1),bool))
    m=api().evaluate(np.ones((1,2,1)),np.ones((1,2,1)),np.ones((1,2,1),bool),np.ones((1,2,1)))
    assert m['mae_skill_vs_persistence'] is None
