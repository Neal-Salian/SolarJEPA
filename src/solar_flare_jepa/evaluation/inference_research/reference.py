"""Independent small-array mathematical references, never production fallback."""
import math
import numpy as np


def _values(values):
    x=np.asarray(values,float)
    if x.ndim!=1 or not 2<=len(x)<=512 or not np.isfinite(x).all():
        raise ValueError('Finite reference vector of length 2..512 required')
    return x


def hac_matrix_variance(values,lag_days):
    x=_values(values);n=len(x)
    if type(lag_days) is not int or not 0<=lag_days<n: raise ValueError('Invalid lag')
    distances=np.abs(np.arange(n)[:,None]-np.arange(n))
    kernel=np.maximum(0.,1-distances/(lag_days+1))
    e=x-x.mean()
    return float(e@kernel@e)/(n*(n-1))


def stationary_exact_variance(values,mean_block_days):
    x=_values(values);n=len(x)
    if type(mean_block_days) is not int or mean_block_days<1: raise ValueError('Invalid mean block')
    e=x-x.mean();p=1/mean_block_days
    covariance=[math.fsum(float(e[t]*e[(t+k)%n]) for t in range(n))/n for k in range(n)]
    return (covariance[0]+2*math.fsum((1-k/n)*(1-p)**k*covariance[k] for k in range(1,n)))/n
