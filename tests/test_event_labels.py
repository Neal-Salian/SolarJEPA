"""Behavioral regression cases for retrospective labels, never synthetic results."""
import numpy as np
import pandas as pd
import pytest

from solar_flare_jepa.events import labels

MIN = 60_000_000_000
DIGEST = 'a' * 64


def event(**changes):
    values = dict(event_id='e', source='GOES-16', catalog_id='c',
                  catalog_sha256=DIGEST, start_ns=10*MIN, peak_ns=20*MIN,
                  end_ns=None, flare_class='M1.0', peak_flux=1e-5)
    values['calibration']=labels.CALIBRATION
    values.update(changes)
    return labels.CatalogEvent(**values)


def call(events, **changes):
    kwargs = dict(issues_ns=np.array([5*MIN, 35*MIN], dtype=np.int64),
                  starts_ns=np.arange(100, dtype=np.int64)*MIN,
                  valid_b=np.ones(100, bool), coverage=(0, 100*MIN),
                  partition=(0, 100*MIN), context_seconds=300,
                  source='GOES-16',calibration=labels.CALIBRATION,
                  catalog_identities=(('c', DIGEST),))
    kwargs.update(changes)
    return labels.label_events(events, **kwargs)


def test_onset_and_peak_are_distinct_and_missing_end_is_not_fabricated():
    onset = call([event(start_ns=4*MIN, peak_ns=10*MIN)])
    peak = call([event(start_ns=4*MIN, peak_ns=10*MIN)], target='peak')
    assert onset['outcomes'] == [False, False]
    assert peak['outcomes'] == [True, False]
    assert peak['valid_mask'] == [True, True]


def test_maturity_includes_subthreshold_peak_after_horizon():
    result = call([event(peak_ns=70*MIN, flare_class='C2.0', peak_flux=2e-6)],
                  partition=(0, 60*MIN))
    assert result['outcomes'][0] is False
    assert result['maturity_ns'][0] == 71*MIN
    assert not result['valid_mask'][0]
    assert 'maturity_outside_partition' in result['reasons'][0]


def test_zero_lead_is_explicit_and_right_boundary_is_exclusive():
    result = call([event(start_ns=5*MIN), event(event_id='edge', start_ns=35*MIN,
                                               peak_ns=40*MIN)])
    assert result['event_ids'] == [['e'], ['edge']]
    assert result['zero_lead_mask'] == [True, True]


def test_missing_bin_and_quality_gaps_prevent_certifying_negative():
    starts = np.delete(np.arange(100, dtype=np.int64)*MIN, 12)
    assert call([], starts_ns=starts, valid_b=np.ones(99, bool))['valid_mask'] == [False, True]
    valid = np.ones(100, bool); valid[12] = False
    assert call([], valid_b=valid)['valid_mask'] == [False, True]


def test_incomplete_catalog_cannot_certify_negatives():
    result = call([event(peak_ns=None, flare_class=None, peak_flux=None)])
    assert not any(result['valid_mask'])
    assert all('incomplete_catalog_event' in row for row in result['reasons'])


def test_foreign_source_saturation_and_duplicate_id_are_rejected_or_censored():
    assert not call([event(source='GOES-18')])['valid_mask'][0]
    assert not call([event(peak_saturated=True)])['valid_mask'][0]
    with pytest.raises(ValueError, match='Duplicate'):
        call([event(), event()])


def test_chronological_support_and_feature_availability():
    result = call([], context_seconds=600)
    assert not result['valid_mask'][0]
    result = call([], feature_available_ns=np.array([6*MIN, 35*MIN], dtype=np.int64))
    assert result['valid_mask'] == [False, True]
    assert 'feature_not_available' in result['reasons'][0]


@pytest.mark.parametrize('name,value', [('issues_ns',[True]), ('valid_b',np.ones(100)),
                                      ('horizon_seconds',True)])
def test_declared_coordinates_and_masks_are_not_silently_coerced(name, value):
    with pytest.raises(ValueError):
        call([], **{name:value})


def test_state_reconstruction_cross_day_duplicates_and_partial_events():
    states = pd.DataFrame([
        dict(flare_id=1., status='EVENT_START', time=pd.Timestamp('2024-07-01T23:59Z'),
             flare_class='nan', xrsb_flux=1e-6, source_file='d1'),
        dict(flare_id=1., status='EVENT_PEAK', time=pd.Timestamp('2024-07-02T00:10Z'),
             flare_class='M1.0', xrsb_flux=1e-5, source_file='d2'),
        dict(flare_id=2., status='POST_EVENT', time=pd.Timestamp('2024-07-02T00:20Z'),
             flare_class='nan', xrsb_flux=1e-6, source_file='d2')])
    result = labels.states_to_events(states, source='GOES-16', catalog_id='days',
                                    source_hashes={'d1':DIGEST,'d2':'b'*64},calibration=labels.CALIBRATION)
    assert result[0].end_ns is None
    assert result[0].start_ns < result[0].peak_ns
    assert result[1].start_ns is None
    bad = pd.concat([states,states.iloc[[1]].assign(xrsb_flux=2e-5)],ignore_index=True)
    with pytest.raises(ValueError, match='Conflicting'):
        labels.states_to_events(bad, source='GOES-16', catalog_id='days',
                                source_hashes={'d1':DIGEST,'d2':'b'*64},calibration=labels.CALIBRATION)


def test_class_threshold_boundaries():
    assert labels.class_threshold('C1.0') == 1e-6
    assert labels.class_threshold('M1.0') == 1e-5
    assert labels.class_threshold('X1.0') == 1e-4
    for value in ['M0.0','M0.5','Q1.0','Mnan',None]:
        with pytest.raises(ValueError):
            labels.class_threshold(value)


def test_calibration_and_mixed_boolean_times_must_be_explicit():
    with pytest.raises(ValueError,match='calibration'): event(calibration='operational_scaled')
    with pytest.raises(ValueError): call([],issues_ns=[True,35*MIN])


def test_one_catalog_name_cannot_name_conflicting_bytes_even_if_empty():
    with pytest.raises(ValueError,match='Conflicting'):
        call([],catalog_identities=(('c',DIGEST),('c','b'*64)))


def test_empty_catalog_still_requires_explicit_scientific_declarations():
    with pytest.raises(ValueError): call([],calibration='unknown')
    with pytest.raises(ValueError): call([],source=None)
    empty=pd.DataFrame(columns=['flare_id','status','time','flare_class','xrsb_flux','source_file'])
    with pytest.raises(ValueError):
        labels.states_to_events(empty,source=None,catalog_id='c',source_hashes={'d':DIGEST},
                                calibration='unknown')


def test_generator_cannot_be_exhausted_into_a_false_negative_catalog():
    with pytest.raises(ValueError,match='list or tuple'):
        call(iter([event()]))
