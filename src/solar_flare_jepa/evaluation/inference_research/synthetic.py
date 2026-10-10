"""Unchanged M2 laws plus an explicitly separate horizon-overlap MA law."""
from dataclasses import replace
import math
import numpy as np

from ..comparison import DAY_NS
from ..stress.synthetic import Scenario, generate_panels, stream_seed


def generate_case(case:dict, rng_seed:int):
    cfg=Scenario(**case['scenario'])
    if case['law']=='m2':
        a,b,truth=generate_panels(cfg,rng_seed)
        return a,b,dict(joint=truth['joint'],seed_conditional=truth['seed_only'],calendar_conditional=truth['time_only'])
    q=case['overlap_days']
    if case['law']!='overlap_ma' or type(q) is not int or not 2<=q<=min(cfg.days) or cfg.distribution!='normal' or cfg.rho!=0 or cfg.heteroskedastic:
        raise ValueError('Unsupported explicit overlap law')
    a,b,truth=generate_panels(replace(cfg,sigma_time=0.),rng_seed)
    rng=np.random.default_rng(stream_seed('m3:overlap-calendar',rng_seed))
    shifts=[]
    for f in sorted(a):
        p=a[f];days=(p.calendar_end_ns-p.calendar_start_ns)//DAY_NS
        innovations=rng.normal(size=days+q-1)
        x=np.convolve(innovations,np.ones(q)/math.sqrt(q),mode='valid')
        indices=np.array([(int(t)-p.calendar_start_ns)//DAY_NS for t in p.issue_times_ns],np.int64)
        added=cfg.sigma_time*x[indices]
        d=(a[f].losses-b[f].losses)+added[None,:]
        base=1+np.abs(d)
        if np.any((d!=0)&((base+d)-base==0)):
            raise ValueError('Synthetic overlap effect below loss representation resolution')
        a[f]=replace(a[f],losses=base+d);b[f]=replace(b[f],losses=base)
        shifts.append(float(added.mean()))
    return a,b,dict(joint=truth['joint'],seed_conditional=truth['joint']+float(np.mean(shifts)),
                    calendar_conditional=truth['time_only'])
