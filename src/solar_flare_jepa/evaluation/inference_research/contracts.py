"""Explicit research estimands, declared assumptions and planned-run evidence."""
from dataclasses import asdict, dataclass
from typing import Literal
import math


def integer(value, minimum, label):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{label} requires integer >= {minimum}')
    return value


@dataclass(frozen=True)
class RunState:
    fold: str
    model: Literal['a', 'b']
    seed: int
    status: Literal['ok', 'failed', 'missing']

    def __post_init__(self):
        if type(self.fold) is not str or not self.fold.strip() or self.model not in ('a','b'):
            raise ValueError('Invalid declared run identity')
        integer(self.seed,0,'Run seed')
        if self.status not in ('ok','failed','missing'):
            raise ValueError('Unknown declared run status')


@dataclass(frozen=True)
class Design:
    """Caller declarations, not authentication.

    ``gaussian`` asserts common-mean iid Gaussian seed scores;
    ``normal_scale_mixture`` asserts independent common-location symmetric
    normal scale mixtures. Both are conditional on the supplied fixed calendar.
    """
    estimand: Literal['seed_conditional', 'calendar_conditional']
    sampling_unit: Literal['paired_training_run', 'calendar_day']
    independent_seeds: bool
    seed_score_law: Literal['gaussian', 'normal_scale_mixture', 'unknown']
    calendar_dependence: Literal['fixed', 'stationary_weak', 'heteroskedastic_weak', 'unknown']
    finite_variance: bool
    independent_folds: bool
    planned_seed_ids: tuple[int, ...]
    run_states: tuple[RunState, ...]
    missing_runs: Literal['reject']

    def __post_init__(self):
        units={'seed_conditional':'paired_training_run','calendar_conditional':'calendar_day'}
        if self.estimand not in units or self.sampling_unit != units[self.estimand]:
            raise ValueError('Explicit estimand and sampling unit must match')
        if any(type(getattr(self,k)) is not bool for k in ('independent_seeds','finite_variance','independent_folds')):
            raise ValueError('Explicit Boolean dependence/moment declarations required')
        if self.seed_score_law not in ('gaussian','normal_scale_mixture','unknown') or self.calendar_dependence not in ('fixed','stationary_weak','heteroskedastic_weak','unknown'):
            raise ValueError('Unknown law declaration')
        if self.missing_runs != 'reject':
            raise ValueError('Research interface never drops missing runs')
        if not isinstance(self.planned_seed_ids,(tuple,list)) or not self.planned_seed_ids:
            raise ValueError('Explicit planned seed cohort required')
        seeds=tuple(self.planned_seed_ids)
        for seed in seeds: integer(seed,0,'Planned seed')
        if len(set(seeds)) != len(seeds):
            raise ValueError('Duplicate planned seed IDs')
        if not isinstance(self.run_states,(tuple,list)) or not all(type(x) is RunState for x in self.run_states):
            raise ValueError('Explicit immutable run status ledger required')
        object.__setattr__(self,'planned_seed_ids',seeds)
        object.__setattr__(self,'run_states',tuple(self.run_states))


@dataclass(frozen=True)
class MethodConfig:
    method: Literal['seed_t','hac','stationary_basic']
    confidence: float
    rng_seed: int
    lag_days: int | None
    mean_block_days: int | None
    replicates: int

    def __post_init__(self):
        if self.method not in ('seed_t','hac','stationary_basic'):
            raise ValueError('Unknown experimental method')
        if type(self.confidence) not in (float,int) or not math.isfinite(self.confidence) or not 0 < self.confidence < 1:
            raise ValueError('Finite confidence within (0,1) required')
        integer(self.rng_seed,0,'RNG seed')
        integer(self.replicates,0,'Replicates')
        if self.method=='stationary_basic':
            integer(self.mean_block_days,1,'Mean block days')
            if self.lag_days is not None or not 99 <= self.replicates <= 1999:
                raise ValueError('Stationary bootstrap needs 99..1999 draws, no HAC lag')
        elif self.replicates != 0 or self.mean_block_days is not None:
            raise ValueError('Analytical methods take no resampling configuration')
        if self.method=='hac':
            integer(self.lag_days,0,'HAC lag days')
        elif self.lag_days is not None:
            raise ValueError('Only HAC takes lag days')
        if self.method=='seed_t' and self.confidence < .95:
            raise ValueError('Declared conservative t guarantee requires confidence >= .95')


@dataclass(frozen=True)
class InferenceResult:
    method: str
    estimand: str
    sampling_unit: str
    estimate: float
    interval: tuple[float,float] | None
    standard_error: float | None
    reason: str | None
    details: dict
    schema_version: int = 1

    def as_dict(self):
        return asdict(self)
