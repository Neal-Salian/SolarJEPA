"""Known-truth loss panels, with explicit independent RNG streams."""
from dataclasses import asdict, dataclass
import hashlib
import math

import numpy as np

from ..comparison import DAY_NS, LossPanel


def stream_seed(label, master_seed):
    if type(label) is not str or type(master_seed) is not int or master_seed < 0:
        raise ValueError('Explicit label and nonnegative integer seed required')
    return int.from_bytes(hashlib.sha256(f'M2:{master_seed}:{label}'.encode()).digest()[:8], 'big')


@dataclass(frozen=True)
class Scenario:
    name: str
    seeds: int = 10
    days: tuple[int, ...] = (30,)
    delta: tuple[float, ...] = (0.,)
    sigma_seed: float = .4
    sigma_time: float = .6
    sigma_cell: float = .3
    rho: float = 0.
    seed_correlation: float = 0.
    distribution: str = 'normal'
    heteroskedastic: bool = False
    counts: tuple[int, ...] = (1,)

    def __post_init__(self):
        if type(self.name) is not str or not self.name.strip():
            raise ValueError('Scenario requires a name')
        if type(self.seeds) is not int or not 2 <= self.seeds <= 100:
            raise ValueError('Synthetic seed count must be 2..100')
        for key in ('days', 'counts', 'delta'):
            raw = getattr(self, key)
            if not isinstance(raw, (tuple, list)) or not raw:
                raise ValueError('Explicit nonempty scenario sequences required')
            object.__setattr__(self, key, tuple(raw))
        if not 1 <= len(self.days) <= 4 or any(type(d) is not int or not 2 <= d <= 366 for d in self.days):
            raise ValueError('One to four synthetic periods of 2..366 days required')
        if len(self.delta) not in (1, len(self.days)):
            raise ValueError('One common effect or one effect per fold required')
        if any(type(c) is not int or not 0 <= c <= 4 for c in self.counts) or not any(self.counts):
            raise ValueError('Counts must be 0..4 with some support')
        for x in (*self.delta, self.sigma_seed, self.sigma_time, self.sigma_cell, self.rho, self.seed_correlation):
            if type(x) not in (int, float) or not math.isfinite(x):
                raise ValueError('Finite numerical scenario parameters required')
        if min(self.sigma_seed, self.sigma_time, self.sigma_cell) < 0 or abs(self.rho) >= 1 or not 0 <= self.seed_correlation <= 1:
            raise ValueError('Invalid variance, stationarity or correlation')
        if self.distribution not in ('normal', 't3', 't1.5') or type(self.heteroskedastic) is not bool:
            raise ValueError('Unsupported innovation distribution/variance pattern')
        if self.heteroskedastic and self.rho != 0:
            raise ValueError('Heteroskedastic case here uses independent calendar innovations')
        if any(sum(day_counts(self, i)) == 0 for i in range(len(self.days))):
            raise ValueError('Every fixed fold requires observed support')

    @property
    def effects(self):
        return self.delta * len(self.days) if len(self.delta) == 1 else self.delta

    def as_dict(self):
        return asdict(self)


def day_counts(cfg, fold):
    return np.resize(np.asarray(cfg.counts, dtype=np.int64), cfg.days[fold])


def _noise(rng, shape, distribution):
    if distribution == 'normal':
        return rng.normal(size=shape)
    if distribution == 't3':
        return rng.standard_t(3, size=shape) / np.sqrt(3.)  # variance one
    return rng.standard_t(1.5, size=shape)  # mean zero, infinite variance


def generate_panels(cfg, rng_seed):
    """Losses are artificial; multiple origins/day repeat the same day cell.

    Conditional truths fix only the stated latent effects: seed_only fixes the
    realized calendar factor, time_only fixes seed factors. Cell innovations are
    averaged out in both population truths, not treated as fixed observations.
    """
    if not isinstance(cfg, Scenario):
        raise ValueError('Expected Scenario')
    rng = np.random.default_rng(stream_seed('dataset', rng_seed))
    z = _noise(rng, cfg.seeds, cfg.distribution)
    shared = _noise(rng, (), cfg.distribution)
    z = math.sqrt(cfg.seed_correlation)*shared + math.sqrt(1-cfg.seed_correlation)*z
    folds_a, folds_b, calendar_mean = {}, {}, []
    start = 0
    for f, (days, effect) in enumerate(zip(cfg.days, cfg.effects)):
        x = np.empty(days)
        x[0] = _noise(rng, (), cfg.distribution)
        for t in range(1, days):
            x[t] = cfg.rho*x[t-1] + math.sqrt(1-cfg.rho**2)*_noise(rng, (), cfg.distribution)
        if cfg.heteroskedastic:
            x *= np.linspace(.25, 2., days)
        cell = _noise(rng, (cfg.seeds, days), cfg.distribution)
        d = effect + cfg.sigma_seed*z[:, None] + cfg.sigma_time*x[None, :] + cfg.sigma_cell*cell
        counts = day_counts(cfg, f)
        calendar_mean.append(float(np.dot(counts, x)/counts.sum()))
        origin_days = np.repeat(np.arange(days), counts)
        difference = d[:, origin_days]
        base = 1 + np.abs(difference)
        stored = (base+difference)-base
        if np.any((difference != 0) & (stored == 0)):
            raise ValueError('Synthetic paired effect is below loss representation resolution')
        times = np.array([start + int(day)*DAY_NS + (j+1)*(DAY_NS//8)
                          for day, count in enumerate(counts) for j in range(int(count))], np.int64)
        fields = dict(seed_ids=tuple(range(cfg.seeds)), origin_ids=tuple(f'f{f}:o{i}' for i in range(len(times))),
                      issue_times_ns=times, support_fingerprint=f'synthetic:{cfg.name}:f{f}',
                      metric='artificial_loss/v1', unit='artificial', calendar_start_ns=start,
                      calendar_end_ns=start+days*DAY_NS)
        folds_a[f'f{f}'] = LossPanel(losses=base+difference, **fields)
        folds_b[f'f{f}'] = LossPanel(losses=base, **fields)
        start += (days+2)*DAY_NS
    truth = float(np.mean(cfg.effects))
    return folds_a, folds_b, dict(joint=truth,
        seed_only=truth+cfg.sigma_time*float(np.mean(calendar_mean)),
        time_only=truth+cfg.sigma_seed*float(z.mean()))


def oracle_variance(cfg):
    """Exact unconditional variance for Gaussian known-DGP equal-fold mean."""
    if cfg.distribution != 'normal':
        return None
    variance = cfg.sigma_seed**2*(cfg.seed_correlation+(1-cfg.seed_correlation)/cfg.seeds)
    folds = len(cfg.days)
    for f, days in enumerate(cfg.days):
        counts = day_counts(cfg, f)
        w = counts/counts.sum()
        covariance = cfg.rho ** np.abs(np.arange(days)[:, None]-np.arange(days))
        if cfg.heteroskedastic:
            scales = np.linspace(.25, 2., days)
            covariance *= scales[:, None]*scales
        variance += (cfg.sigma_time**2*float(w@covariance@w) + cfg.sigma_cell**2*float(w@w)/cfg.seeds)/folds**2
    return float(variance)
