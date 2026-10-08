"""Deterministic numerical comparators without P1's physical-time assumptions."""
from dataclasses import dataclass
import json

import numpy as np

from solar_flare_jepa.forecasting.contracts import canonical_json
from .sequences import LABEL, UNIT, array_hash


@dataclass(frozen=True)
class NumericalBaseline:
    name: str
    context: int
    horizon: int
    mean: float
    scale: float
    parameters_json: str
    coefficients: np.ndarray | None = None

    @property
    def parameters(self):
        return json.loads(self.parameters_json)

    def predict(self, values, mask):
        """No future targets enter this API; unsupported contexts fail explicitly."""
        x, mask = np.asarray(values, float), np.asarray(mask)
        if (x.ndim != 3 or x.shape[1:] != (self.context,1) or mask.shape != x.shape
                or mask.dtype != bool or not np.isfinite(x[mask]).all()
                or np.isinf(x).any() or not mask.any(axis=1).all()):
            raise ValueError('Invalid/unsupported numerical baseline context')
        out = np.empty((len(x),self.horizon,1))
        if self.name == 'direct_ridge':
            if not mask.all():
                raise ValueError('Direct Ridge requires complete context; no hidden padding')
            z = (x[:,:,0]-self.mean)/self.scale
            out[:,:,0] = (np.c_[np.ones(len(x)),z] @ self.coefficients)*self.scale+self.mean
        else:
            for i in range(len(x)):
                valid = np.flatnonzero(mask[i,:,0])
                if self.name == 'persistence':
                    out[i,:,0] = x[i,valid[-1],0]
                elif self.name == 'training_mean':
                    out[i,:,0] = self.mean
                elif self.name == 'trailing_mean':
                    recent = valid[valid >= max(0,self.context-16)]
                    if not len(recent):
                        raise ValueError('Trailing mean has no recent valid support')
                    out[i,:,0] = x[i,recent,0].mean()
                elif self.name == 'fixed_ar1':
                    leads = self.context-valid[-1]+np.arange(self.horizon)
                    out[i,:,0] = self.mean + .9**leads*(x[i,valid[-1],0]-self.mean)
                else:
                    raise ValueError('Unsupported numerical comparator')
        if not np.isfinite(out).all():
            raise ValueError('Nonfinite baseline output')
        return out


def fit_baselines(training, normalization):
    """Only train windows/statistics are accepted. No model-specific origin drops."""
    x,y = training.x,training.y
    if not training.x_mask.all() or not training.y_mask.all():
        raise ValueError('Pilot baseline fit requires complete train windows')
    mean,scale = normalization['mean'],normalization['scale']
    if not np.isfinite([mean,scale]).all() or scale <= 0:
        raise ValueError('Invalid train-only statistics')
    z=(x[:,:,0]-mean)/scale
    design=np.c_[np.ones(len(x)),z]
    penalty=np.eye(design.shape[1]); penalty[0,0]=0
    coefficients=np.linalg.solve(design.T@design+penalty,design.T@((y[:,:,0]-mean)/scale))
    if not np.isfinite(coefficients).all():
        raise ValueError('Nonfinite Ridge fit')
    coefficients=np.frombuffer(coefficients.tobytes(),dtype=float).reshape(coefficients.shape)
    fitted={}
    for name in ('persistence','training_mean','trailing_mean','fixed_ar1','direct_ridge'):
        parameters=dict(name=name,scientific_label=LABEL,unit=UNIT,
                        fit_support='train_windows_only' if name=='direct_ridge' else 'unique_raw_train_statistics',
                        train_window_fingerprint=training.fingerprint,
                        normalization=normalization,lookback=min(16,x.shape[1]) if name=='trailing_mean' else None,
                        phi=.9 if name=='fixed_ar1' else None,
                        ar1_policy='fixed_mean_reverting_comparator_not_fitted_AR1' if name=='fixed_ar1' else None,
                        ridge_alpha=1. if name=='direct_ridge' else None,
                        coefficient_hash=array_hash(coefficients) if name=='direct_ridge' else None)
        fitted[name]=NumericalBaseline(name,x.shape[1],y.shape[1],mean,scale,canonical_json(parameters),
                                      coefficients if name=='direct_ridge' else None)
    return fitted


def evaluate(targets, predictions, mask, persistence=None):
    """Same numerical target support for every model; invalid output aborts."""
    y,p,m = np.asarray(targets,float),np.asarray(predictions,float),np.asarray(mask)
    if (y.shape != p.shape or y.shape != m.shape or y.ndim != 3 or m.dtype != bool
            or not m.any() or not np.isfinite(y[m]).all() or not np.isfinite(p).all()):
        raise ValueError('Invalid numerical evaluation support or predictions')
    err=p[m]-y[m]
    mae,rmse=float(np.abs(err).mean()),float(np.sqrt(np.square(err).mean()))
    if not np.isfinite([mae,rmse]).all():
        raise ValueError('Numerical metric overflow')
    result=dict(scientific_label=LABEL,unit=UNIT,mae=mae,rmse=rmse,
                valid_target_cells=int(m.sum()),total_target_cells=int(m.size),
                valid_prediction_cells=int(p.size),prediction_coverage=1.,
                target_coverage=float(m.mean()),scored_coverage=float(m.mean()))
    if persistence is not None:
        ref=evaluate(y,persistence,m)
        for metric in ('mae','rmse'):
            loss=ref[metric]
            result[metric+'_skill_vs_persistence']=None if loss==0 else float(1-result[metric]/loss)
        result['skill_definition']='1 - model_error / persistence_error; same target mask'
    return result
