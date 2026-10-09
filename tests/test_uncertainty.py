"""Synthetic paired losses, not observational confidence claims."""
import json

import numpy as np
import pytest

SECOND = 1_000_000_000


def bootstrap(times, model, reference, **kwargs):
    from solar_flare_jepa.evaluation.uncertainty import paired_block_bootstrap
    return paired_block_bootstrap(np.asarray(times), np.asarray(model), np.asarray(reference), **kwargs)


def test_paired_constant_difference_preserves_pairing_and_is_deterministic():
    args = ([0,SECOND,2*SECOND,3*SECOND], [2.,4.,8.,10.], [1.,3.,7.,9.])
    result = bootstrap(*args, block_seconds=2, replicates=100, seed=17)
    assert result == bootstrap(*args, block_seconds=2, replicates=100, seed=17)
    assert result['mean_difference'] == 1.
    assert result['confidence_interval'] == [1.,1.]
    assert result['block_count'] == 2
    assert result['scored_pair_count'] == 4
    assert result['method'] == 'paired_nonoverlapping_UTC_calendar_block_percentile_v1'
    assert result['significance_claim'] is False
    json.dumps(result, allow_nan=False)


def test_unequal_calendar_block_sizes_pool_origin_sums_not_block_means():
    # UTC-epoch blocks [0,2), [2,4), [4,6): sizes 1,2,1.
    result = bootstrap([SECOND,2*SECOND,3*SECOND,4*SECOND],
                       [0.,2.,4.,10.], [0.,0.,0.,0.], block_seconds=2, replicates=20, seed=1)
    assert result['mean_difference'] == 4. # not mean([0,3,10]) = 13/3
    assert [b['origin_count'] for b in result['blocks']] == [1,2,1]
    assert [b['start_ns'] for b in result['blocks']] == [0,2*SECOND,4*SECOND]
    assert [b['paired_count'] for b in result['blocks']] == [1,2,1]
    assert result['edge_blocks_partial'] is True


def test_nan_pairs_are_excluded_jointly_but_regular_axis_and_empty_blocks_remain():
    result = bootstrap(np.arange(6,dtype=np.int64)*SECOND,
                       [2.,np.nan,np.nan,np.nan,8.,10.],
                       [1.,np.nan,np.nan,np.nan,7.,9.], block_seconds=2, replicates=200, seed=4)
    assert result['mean_difference'] == 1.
    assert result['scored_pair_count'] == 3
    assert result['excluded_pair_count'] == 3
    assert result['model_missing_count'] == 3
    assert result['reference_missing_count'] == 3
    assert result['blocks'][1]['paired_count'] == 0
    assert result['undefined_replicate_count'] > 0
    assert result['defined_replicate_count'] + result['undefined_replicate_count'] == 200
    assert result['confidence_interval'] == [1.,1.]


def test_zero_losses_are_valid_but_no_independence_or_significance_is_asserted():
    result = bootstrap(np.arange(4,dtype=np.int64)*SECOND, np.zeros(4), np.zeros(4),
                       block_seconds=2,replicates=20)
    assert result['mean_difference'] == 0.
    assert result['confidence_interval'] == [0.,0.]
    assert result['limitations']
    assert result['seed'] == 17


@pytest.mark.parametrize('times,model,reference', [
    ([0,SECOND,3*SECOND],[1.,1.,1.],[1.,1.,1.]),
    ([0,SECOND,SECOND],[1.,1.,1.],[1.,1.,1.]),
    ([SECOND,0],[1.,1.],[1.,1.]),
    ([0.,float(SECOND)],[1.,1.],[1.,1.]),
    ([0,SECOND],[np.inf,1.],[np.nan,1.]),
    ([0,SECOND],[-1.,1.],[1.,1.]),
    ([0,SECOND],[1.],[1.,1.]),
    ([0,SECOND],[[1.],[1.]],[1.,1.]),
    ([0,SECOND],[np.nan,np.nan],[1.,1.]),
])
def test_invalid_gapped_unordered_or_nonfinite_loss_inputs_are_rejected(times,model,reference):
    with pytest.raises(ValueError):
        bootstrap(times,model,reference,block_seconds=1,replicates=20)


@pytest.mark.parametrize('kwargs', [
    {'block_seconds':0}, {'block_seconds':True}, {'block_seconds':1.5},
    {'block_seconds':10}, {'block_seconds':1,'minimum_block_seconds':2},
    {'block_seconds':1,'replicates':0}, {'block_seconds':1,'replicates':True},
    {'block_seconds':1,'seed':-1}, {'block_seconds':1,'confidence':1.},
    {'block_seconds':1,'confidence':float('nan')},
])
def test_invalid_resampling_design_and_too_few_blocks_fail(kwargs):
    with pytest.raises(ValueError):
        bootstrap([0,SECOND,2*SECOND,3*SECOND], [1.,2.,3.,4.],[0.,0.,0.,0.],**kwargs)


def test_sparse_pairs_need_two_informative_blocks():
    with pytest.raises(ValueError):
        bootstrap([0,SECOND,2*SECOND,3*SECOND], [1.,1.,np.nan,np.nan], [0.,0.,np.nan,np.nan],
                  block_seconds=2,replicates=20)


def test_fingerprint_binds_explicit_resampling_design_and_input_losses():
    a = bootstrap([0,SECOND,2*SECOND,3*SECOND], [1.,2.,3.,4.],[0.,0.,0.,0.],
                  block_seconds=1,replicates=20)
    b = bootstrap([0,SECOND,2*SECOND,3*SECOND], [1.,2.,3.,4.],[0.,0.,0.,0.],
                  block_seconds=2,replicates=20)
    assert a['input_fingerprint'] != b['input_fingerprint']
    assert a['origin_cadence_ns'] == SECOND


def test_resampled_unequal_blocks_use_ratio_of_sums_in_the_interval():
    # Two UTC blocks contain respectively 1 zero and 3 tens. Drawing two
    # blocks gives only means {0, 7.5, 10}, probabilities {1/4, 1/2, 1/4}.
    # A central20% interval sits in the7.5 mass; equal block means yield5.
    result = bootstrap([2*SECOND,3*SECOND,4*SECOND,5*SECOND],
                       [0.,10.,10.,10.],[0.,0.,0.,0.],
                       block_seconds=3,replicates=1000,seed=17,confidence=.2)
    assert result['mean_difference'] == 7.5
    assert result['confidence_interval'] == [7.5,7.5]


def test_large_finite_losses_do_not_overflow_pooled_block_means():
    result = bootstrap([0,SECOND,2*SECOND,3*SECOND],
                       [1e308]*4,[0.]*4,block_seconds=2,replicates=20)
    assert result['mean_difference'] == 1e308
    assert result['confidence_interval'] == [1e308,1e308]


def test_partial_pair_bootstrap_declares_interval_conditioning():
    result = bootstrap(np.arange(6,dtype=np.int64)*SECOND,
                       [1.,1.,np.nan,np.nan,2.,2.],[0.,0.,np.nan,np.nan,0.,0.],
                       block_seconds=2,replicates=50,seed=4)
    assert result['undefined_replicate_count'] > 0
    assert result['interval_condition'] == 'draws_with_at_least_one_valid_paired_origin'


def test_model_specific_missing_loss_cannot_disappear_from_paired_comparison():
    with pytest.raises(ValueError,match='identical'):
        bootstrap(np.arange(4,dtype=np.int64)*SECOND,
                  [np.nan,0.,0.,0.],[100.,1.,1.,1.],block_seconds=1,replicates=20)
