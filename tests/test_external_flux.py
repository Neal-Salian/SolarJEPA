"""Synthetic, hand-derived external-adapter checks; no observational skill claims."""
from copy import deepcopy
from dataclasses import replace
import json
import numpy as np
import pytest
from solar_flare_jepa.forecasting.contracts import ForecastSpec, FutureGrid, ForecastTargets, ForecastPrediction


def fixture(mask=None, units=('W/m2',)):
    n,h,k=2,2,len(units)
    names=tuple(f'x{i}' for i in range(k))
    spec=ForecastSpec(60,1,h,names,names,units,units,availability_mode='retrospective_bin_end',eligibility_policy='masked')
    issue=np.array([120,240],dtype=np.int64)*10**9
    start=issue[:,None]+np.array([0,60],dtype=np.int64)*10**9
    grid=FutureGrid(start,start+60*10**9,issue,('one','two'),spec,'external-fixture')
    observed=np.tile(np.array([[[2.],[4.]],[[6.],[8.]]]),(1,1,k))
    points=np.tile(np.array([[[1.],[1.]],[[5.],[3.]]]),(1,1,k))
    target=ForecastTargets(observed,np.ones_like(observed,bool) if mask is None else mask,grid)
    return target,ForecastPrediction(points,grid,'synthetic-model'),ForecastPrediction(np.zeros_like(points),grid,'persistence')


def evaluate(*args,**kwargs):
    from solar_flare_jepa.evaluation.external_flux import evaluate_external_flux
    return evaluate_external_flux(*args,**kwargs)


def test_external_errors_skills_and_leads_need_no_external_training_slice():
    result=evaluate(*fixture())
    assert result['by_target']['x0']['mae']['value']==2.5
    assert result['by_target']['x0']['rmse']['value']==3.
    assert result['by_target']['x0']['persistence_mae_skill']['value']==.5
    assert result['by_target']['x0']['persistence_mse_skill']['value']==.7
    assert result['by_target_lead']['x0'][0]['mae']['value']==1.
    assert result['by_target_lead']['x0'][1]['rmse']['value']==pytest.approx(4.123105625617661)
    assert result['coverage']=={'valid_count':4,'total_count':4,'prediction_count':4,'scored_count':4,'fraction':1.,'prediction_fraction':1.}
    assert result['per_origin'][1]['absolute_error']==[[1.],[5.]]
    assert result['dataset_fingerprint']=='external-fixture'
    assert result['fit_performed'] is False
    json.dumps(result,allow_nan=False)


def test_missing_targets_not_failed_predictions_determine_score_support():
    mask=np.array([[[True],[False]],[[True],[True]]])
    t,p,r=fixture(mask)
    result=evaluate(t,p,r)
    assert result['by_target']['x0']['mae']['value']==pytest.approx(7/3)
    assert result['coverage']['fraction']==.75
    assert result['coverage']['prediction_fraction']==1.
    bad=deepcopy(p)
    object.__setattr__(bad,'values',np.array([[[1.],[np.nan]],[[5.],[3.]]]))
    with pytest.raises(ValueError): evaluate(t,bad,r)


def test_external_prediction_identity_cannot_be_spoofed_by_equal_shape():
    t,p,r=fixture()
    with pytest.raises(ValueError,match='align'):
        evaluate(t,replace(p,grid=replace(p.grid,dataset_fingerprint='july-frozen')),r)
    with pytest.raises(ValueError,match='align'):
        evaluate(t,p,replace(r,grid=replace(r.grid,origin_ids=('two','one'))))


def test_copied_mutated_grid_and_target_revalidated():
    t,p,r=fixture()
    malformed=deepcopy(t)
    object.__setattr__(malformed.grid,'starts_ns',malformed.grid.starts_ns+10**9)
    with pytest.raises(ValueError): evaluate(malformed,p,r)
    malformed=deepcopy(t)
    object.__setattr__(malformed,'mask',np.ones((2,1,1),bool))
    with pytest.raises(ValueError): evaluate(malformed,p,r)


def test_empty_support_and_zero_reference_skill_are_undefined():
    t,p,r=fixture(np.zeros((2,2,1),bool))
    result=evaluate(t,p,r)
    assert result['aggregate']['mae']=={'value':None,'count':0,'reason':'empty_mask'}
    t,p,_=fixture()
    result=evaluate(t,p,ForecastPrediction(t.values,t.grid,'perfect-reference'))
    assert result['by_target']['x0']['persistence_mae_skill']['value'] is None
    assert result['by_target']['x0']['persistence_mae_skill']['reason']=='zero_persistence_loss'
    result=evaluate(t,p)
    assert result['by_target']['x0']['persistence_mae_skill']['reason']=='persistence_not_supplied'


def test_differing_units_do_not_produce_pooled_physical_error():
    result=evaluate(*fixture(units=('W/m2','synthetic-counts')))
    assert result['aggregate']['mae']['reason']=='incompatible_target_units'
    assert result['by_target']['x0']['mae']['value']==2.5
    assert result['by_target']['x1']['mae']['value']==2.5


def test_metric_identity_is_deterministic_and_binds_values_and_mask():
    t,p,r=fixture()
    result=evaluate(t,p,r)
    assert result==evaluate(t,p,r)
    changed=evaluate(t,replace(p,values=p.values+.1),r)
    assert result['evaluation_input_fingerprint']!=changed['evaluation_input_fingerprint']


def test_nonfinite_loss_is_failure_not_silent_overflow():
    t,p,r=fixture()
    with pytest.raises(ValueError,match='Nonfinite'):
        evaluate(t,replace(p,values=np.full_like(p.values,1e308)),r)


def test_nonzero_residual_squared_underflow_cannot_report_perfect_forecast():
    t,p,_=fixture()
    t=replace(t,values=np.zeros_like(t.values))
    p=replace(p,values=np.full_like(p.values,1e-200))
    with pytest.raises(ValueError,match='underflow'):
        evaluate(t,p)


@pytest.mark.parametrize('reference',[False,True])
def test_nonzero_squared_reduction_underflow_is_not_perfect_error(reference):
    t,p,_=fixture()
    t=replace(t,values=np.zeros_like(t.values))
    points=np.zeros_like(p.values)
    points[0,0,0]=np.sqrt(np.nextafter(0.,1.))
    tiny=replace(p,values=points)
    with pytest.raises(ValueError,match='underflow'):
        evaluate(t,replace(p,values=np.ones_like(p.values)),tiny) if reference else evaluate(t,tiny)
