"""Small development-only scientific fixtures: no test partition exists."""
import numpy as np

from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows

NS = 1_000_000_000
LOSS = 'dex_pinball_equal_channel_v2'
LEVELS = (.05, .25, .5, .75, .95)


def development_windows(*, masked=False, offset_ns=0):
    ticks = np.array([i for i in range(160) if i != 35], dtype=np.int64)
    values = 10. ** np.column_stack((-6 + .3 * np.sin(ticks / 7), -5 + .2 * np.cos(ticks / 9)))
    mask = np.ones_like(values, bool)
    mask[ticks == 22, 0] = False
    mask[ticks == 135, 1] = False
    dataset = TimeSeriesDataset('m4b-development', 'synthetic_fixture', ticks * NS + offset_ns, (ticks + 1) * NS + offset_ns,
        values, mask, values, mask, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), 1,
        availability_policy='bin_end_earliest')
    spec = ForecastSpec(1, 10, 5, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'), ('W/m2', 'W/m2'),
        transform='log10', feature_reference=(1., 1.), target_reference=(1., 1.), target_minimum=(0., 0.),
        availability_mode='retrospective_bin_end', eligibility_policy='masked' if masked else 'complete')
    return {name: build_partition_windows(dataset, spec, TemporalPartition(name, start * NS + offset_ns, end * NS + offset_ns))
            for name, start, end in [('train', 0, 100), ('validation', 100, 160)]}


def controlled_config(arm, seed):
    from solar_flare_jepa.training import controlled as c
    from solar_flare_jepa.training.jepa import JepaConfig
    config = JepaConfig(patch_steps=5, width=8, depth=1, heads=2, predictor_depth=1,
        mlp_ratio=2, head_hidden=8, pretrain_epochs=1, finetune_epochs=1, batch_size=16,
        threads=1, patience=1, monitor_windows=24, max_train_windows=24, seed=seed)
    schedule = c.TrainingSchedule(arm=arm, pretrain_epochs=int(arm in c.SSL_ARMS),
        warmup_epochs=int(arm == 'supervised_extra_updates'), downstream_epochs=1,
        early_stopping_patience=None, train_loss=LOSS, selection_metric=LOSS)
    return c.ControlledConfig(config, schedule)


def fit_model(arm, seed, windows=None, *, pretraining=None):
    from solar_flare_jepa.training import controlled as c, comparators as b
    w = development_windows() if windows is None else windows
    training, validation = w['train'].training_slice, w['validation']
    if arm == 'tcn':
        return b.fit_tcn(training, validation,
            b.TcnConfig(width=4, kernel_size=3, dilations=(1, 2), dropout=0., seed=seed,
                threads=1, batch_size=16, lr=.001, weight_decay=.0001, gradient_clip=1.,
                quantiles=LEVELS, max_train_windows=24),
            b.ComparatorSchedule(downstream_epochs=1, early_stopping_patience=None,
                                 train_loss=LOSS, selection_metric=LOSS))
    if arm == 'quantile_linear':
        return b.fit_quantile_linear(training, validation,
            b.QuantileLinearConfig(seed=seed, epochs=1, batch_size=16, threads=1,
                lambdas=(0., 1.), max_train_windows=24, quantiles=LEVELS, lr=.01,
                gradient_clip=1., train_loss=LOSS, selection_metric=LOSS))
    return c.fit_controlled(training, validation, controlled_config(arm, seed), pretraining=pretraining)
