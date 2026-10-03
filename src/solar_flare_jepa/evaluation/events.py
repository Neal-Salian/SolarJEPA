"""Binary scoring of explicitly supplied outcomes, never derived event labels."""
import numpy as np


def _cell(value,count,reason=None):
    return {'value':None if value is None else float(value),'reason':reason,'count':int(count)}


def _vector(value,n,name,mask=None,binary=False):
    raw = np.asarray(value)
    if raw.shape != (n,) or raw.dtype.kind not in 'biuf':
        raise ValueError(f'{name} must be a numeric vector of length {n}')
    array = raw.astype(float)
    selected = array if mask is None else array[mask]
    if not np.isfinite(selected).all():
        raise ValueError(f'{name} must be finite on scored origins')
    if binary and not np.isin(selected,[0.,1.]).all():
        raise ValueError(f'{name} must be binary on scored origins')
    if not binary and ((selected < 0).any() or (selected > 1).any()):
        raise ValueError(f'{name} must be in [0,1] on scored origins')
    return array


def evaluate_events(outcomes,valid_mask,mature_mask,origin_ids,event_definition,
                    horizon_seconds,decisions=None,probabilities=None):
    """Score supplied binary outcomes on ``valid_mask & mature_mask``.

    All arrays are one-dimensional and follow the explicitly ordered, unique
    origin IDs. Masked or immature entries may be missing. Available scores
    never define the mask. Probabilities alone yield Brier scores with no
    invented decision threshold. This function establishes no real event
    semantics, event-level alarm matching, operational calibration or skill.
    """
    if not isinstance(origin_ids, (list, tuple)):
        raise ValueError('origin_ids require an explicit ordered list or tuple')
    ids = tuple(origin_ids)
    n = len(ids)
    if (len(set(ids)) != n or any(not isinstance(x,str) or not x.strip() for x in ids)):
        raise ValueError('origin_ids must be explicit unique nonempty strings')
    if not isinstance(event_definition,str) or not event_definition.strip():
        raise ValueError('An explicit event_definition is required')
    if (isinstance(horizon_seconds,(bool,np.bool_))
            or not isinstance(horizon_seconds,(int,np.integer)) or horizon_seconds <= 0):
        raise ValueError('horizon_seconds must be a positive integer')
    if decisions is None and probabilities is None:
        raise ValueError('Supply decisions or probabilities')
    masks = []
    for values,name in ((valid_mask,'valid_mask'),(mature_mask,'mature_mask')):
        mask = np.asarray(values)
        if mask.shape != (n,) or mask.dtype.kind != 'b':
            raise ValueError(f'{name} must be a boolean vector of length {n}')
        masks.append(mask)
    valid,mature = masks
    mask = valid & mature
    outcome = _vector(outcomes,n,'outcomes',mask,binary=True)
    decision = None if decisions is None else _vector(decisions,n,'decisions',mask,binary=True)
    probability = None if probabilities is None else _vector(probabilities,n,'probabilities',mask)
    count = int(mask.sum())
    names = ('precision','recall','pod','far','fpr','f1','tss','hss2')
    confusion = None
    metrics = {}
    if decision is None:
        metrics.update({name:_cell(None,count,'decisions_not_supplied') for name in names})
    else:
        y,d = outcome[mask],decision[mask]
        tp = int(((y == 1) & (d == 1)).sum())
        fp = int(((y == 0) & (d == 1)).sum())
        fn = int(((y == 1) & (d == 0)).sum())
        tn = int(((y == 0) & (d == 0)).sum())
        confusion = dict(tp=tp,fp=fp,fn=fn,tn=tn)
        def ratio(numerator,denominator):
            if not count:
                return _cell(None,0,'empty_mask')
            return _cell(numerator/denominator,count) if denominator else _cell(None,count,'zero_denominator')
        metrics.update(precision=ratio(tp,tp+fp),recall=ratio(tp,tp+fn),
                       pod=ratio(tp,tp+fn),far=ratio(fp,tp+fp),fpr=ratio(fp,fp+tn),
                       f1=ratio(2*tp,2*tp+fp+fn),
                       tss=ratio(tp*tn-fp*fn,(tp+fn)*(fp+tn)),
                       hss2=ratio(2*(tp*tn-fp*fn),(tp+fn)*(fn+tn)+(tp+fp)*(fp+tn)))
    losses = None
    if probability is None:
        metrics['brier'] = _cell(None,count,'probabilities_not_supplied')
    else:
        losses = np.zeros(n)
        losses[mask] = (probability[mask]-outcome[mask])**2
        metrics['brier'] = _cell(float(losses[mask].mean()),count) if count else _cell(None,0,'empty_mask')
    per_origin = [dict(origin_id=ids[i],valid=bool(valid[i]),mature=bool(mature[i]),scored=bool(mask[i]),
        outcome=float(outcome[i]) if mask[i] else None,
        decision=float(decision[i]) if mask[i] and decision is not None else None,
        probability=float(probability[i]) if mask[i] and probability is not None else None,
        brier_loss=float(losses[i]) if mask[i] and losses is not None else None) for i in range(n)]
    return dict(schema_version=1,event_definition=event_definition,horizon_seconds=int(horizon_seconds),
                origin_ids=list(ids),confusion=confusion,metrics=metrics,
                units={name:'dimensionless' for name in (*names,'brier')},
                reduction=dict(mask='valid_mask & mature_mask',brier='mean((probability - outcome)^2)',
                               far='FP/(TP+FP)',fpr='FP/(FP+TN)',
                               tss='TP/(TP+FN) - FP/(FP+TN)',
                               hss2='2*(TP*TN-FP*FN)/((TP+FN)*(FN+TN)+(TP+FP)*(FP+TN))'),
                coverage=dict(total_count=n,valid_count=int(valid.sum()),mature_count=int(mature.sum()),
                              scored_count=count,fraction=count/n if n else None),per_origin=per_origin)
