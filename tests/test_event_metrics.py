"""Supplied synthetic binary outcomes only; no physical event labels are derived."""
import json

import numpy as np
import pytest


def evaluate(outcomes, decisions=None, probabilities=None, valid_mask=None,
             mature_mask=None, origin_ids=None, **changes):
    from solar_flare_jepa.evaluation import evaluate_events
    n=len(outcomes)
    kwargs=dict(outcomes=outcomes,valid_mask=np.ones(n,bool) if valid_mask is None else valid_mask,
                mature_mask=np.ones(n,bool) if mature_mask is None else mature_mask,
                origin_ids=tuple(f'o{i}' for i in range(n)) if origin_ids is None else origin_ids,
                event_definition='synthetic_binary_fixture',horizon_seconds=60,
                decisions=decisions,probabilities=probabilities)
    kwargs.update(changes)
    return evaluate_events(**kwargs)


def value(cell):
    assert cell['reason'] is None
    return cell['value']


def test_complete_confusion_table_and_hand_derived_metrics_far_differs_from_fpr():
    # TP=2, FP=1, FN=1, TN=4.
    result=evaluate([1,1,1,0,0,0,0,0],[1,1,0,1,0,0,0,0],
                    [.9,.8,.4,.7,.2,.1,.3,.0])
    assert result['confusion'] == {'tp':2,'fp':1,'fn':1,'tn':4}
    metrics=result['metrics']
    assert value(metrics['precision']) == pytest.approx(2/3)
    assert value(metrics['recall']) == pytest.approx(2/3)
    assert value(metrics['pod']) == pytest.approx(2/3)
    assert value(metrics['far']) == pytest.approx(1/3)
    assert value(metrics['fpr']) == .2
    assert value(metrics['f1']) == pytest.approx(2/3)
    assert value(metrics['tss']) == pytest.approx(7/15)
    assert value(metrics['hss2']) == pytest.approx(7/15) # 2*(8-1)/(3*5+3*5)
    assert value(metrics['brier']) == pytest.approx(.13) # squared loss sum 1.04 / 8
    assert metrics['brier']['count'] == 8
    assert result['per_origin'][2]['brier_loss'] == .36
    assert result['event_definition'] == 'synthetic_binary_fixture'
    assert result['horizon_seconds'] == 60
    json.dumps(result,allow_nan=False)


def test_probability_only_scores_brier_without_threshold_or_confusion():
    result=evaluate([0,1],probabilities=[.2,.7])
    assert value(result['metrics']['brier']) == pytest.approx(.065)
    assert result['confusion'] is None
    assert result['metrics']['precision'] == {'value':None,'reason':'decisions_not_supplied','count':2}
    assert result['per_origin'][0]['decision'] is None


def test_invalid_and_immature_outcomes_are_excluded_with_ordered_ids_and_losses():
    result=evaluate([1,np.nan,1,0],[1,np.nan,0,1],[.8,np.nan,.2,.3],
                    valid_mask=np.array([True,False,True,True]),
                    mature_mask=np.array([True,True,False,True]),
                    origin_ids=('b','a','d','c'))
    assert result['origin_ids'] == ['b','a','d','c']
    assert result['coverage'] == {'total_count':4,'valid_count':3,'mature_count':3,
                                  'scored_count':2,'fraction':.5}
    assert result['confusion'] == {'tp':1,'fp':1,'fn':0,'tn':0}
    assert value(result['metrics']['brier']) == pytest.approx(.065)
    assert result['per_origin'][1]['outcome'] is None
    assert result['per_origin'][2]['brier_loss'] is None


@pytest.mark.parametrize('outcomes,decisions,undefined', [
    ([0,0],[0,0],['precision','recall','pod','far','f1','tss','hss2']),
    ([1,1],[1,1],['fpr','tss','hss2']),
    ([1,1],[0,0],['precision','far','fpr','tss']),
    ([0,0],[1,1],['recall','pod','tss']),
])
def test_zero_denominators_have_explicit_reasons(outcomes,decisions,undefined):
    result=evaluate(outcomes,decisions)
    for name in undefined:
        assert result['metrics'][name]['value'] is None
        assert result['metrics'][name]['reason'] == 'zero_denominator'
        assert result['metrics'][name]['count'] == 2
    assert result['metrics']['brier']['reason'] == 'probabilities_not_supplied'
    json.dumps(result,allow_nan=False)


def test_empty_or_no_mature_label_mask_is_undefined_not_zero_skill():
    for args in (dict(outcomes=[],decisions=[]),
                 dict(outcomes=[1,0],decisions=[1,0],mature_mask=np.zeros(2,bool))):
        result=evaluate(**args)
        assert result['coverage']['scored_count'] == 0
        assert result['metrics']['f1'] == {'value':None,'reason':'empty_mask','count':0}


@pytest.mark.parametrize('changes', [
    {'outcomes':[[0],[1]]}, {'outcomes':[0,np.nan]}, {'outcomes':[0,2]},
    {'decisions':[0]}, {'decisions':[0,2]}, {'decisions':[0,np.inf]},
    {'probabilities':[.5]}, {'probabilities':[.2,1.1]},
    {'probabilities':[-.1,.2]}, {'probabilities':[np.nan,.2]},
    {'valid_mask':[1,1]}, {'mature_mask':[True]},
    {'origin_ids':['same','same']}, {'origin_ids':['only']},
    {'origin_ids':['','two']}, {'event_definition':''},
    {'horizon_seconds':0}, {'horizon_seconds':True}, {'horizon_seconds':1.5},
])
def test_malformed_shapes_range_identity_and_masks_rejected(changes):
    with pytest.raises(ValueError):
        _changed(changes)


def _changed(changes):
    kwargs=dict(outcomes=[0,1],decisions=[0,1])
    kwargs.update(changes)
    return evaluate(**kwargs)


def test_missing_observation_needs_explicit_mask_and_no_prediction_input_rejected():
    with pytest.raises(ValueError):
        evaluate([0,1])
    masked=evaluate([0,np.nan],decisions=[0,np.nan],valid_mask=np.array([True,False]))
    assert masked['coverage']['scored_count'] == 1
