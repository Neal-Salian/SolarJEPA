"""M4A proposed V2 training/pilot configurations: annotated, internally consistent, executable by the code."""
import hashlib
import importlib
import json
from pathlib import Path

import pytest

torch = pytest.importorskip('torch')

from solar_flare_jepa.forecasting.contracts import ForecastSpec  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / 'configs' / 'v2_proposed'
STATUSES = {'INHERITED_V1', 'INHERITED_V2_PROPOSAL', 'NEWLY_PROPOSED_M4A', 'CODE_INVARIANT'}


def load(name):
    return json.loads((ROOT / name).read_text())


def controlled():
    return importlib.import_module('solar_flare_jepa.training.controlled')


def comparators():
    return importlib.import_module('solar_flare_jepa.training.comparators')


def protocol_spec():
    return ForecastSpec(60, 120, 30, ('a', 'b'), ('a', 'b'), ('W/m2', 'W/m2'), ('W/m2', 'W/m2'), stride_steps=30,
                        transform='log10', feature_reference=(1., 1.), target_reference=(1., 1.))


def derived_seeds(count):
    seeds, i = [], 0
    while len(seeds) < count:
        digest = hashlib.sha256(f'SolarJEPA-V2.1-paired-seed-{i}'.encode('ascii')).digest()
        seed = int.from_bytes(digest[:4], 'big') % 2**31
        if seed not in seeds and seed not in (17, 29, 43):
            seeds.append(seed)
        i += 1
    return seeds


@pytest.mark.parametrize('name', ['training_protocol_proposal.json', 'feasibility_pilot_proposal.json'])
def test_proposals_are_marked_unapproved_unless_an_approval_is_recorded(name):
    proposal = load(name)
    if not proposal['approved']:
        assert proposal['status'] == 'PROPOSED_REQUIRES_APPROVAL'
        assert set(proposal['approval'].values()) == {None}
    else:  # an approval must name who, when and where
        assert all(proposal['approval'].values())


def test_every_setting_records_value_source_status_and_approval():
    for name, setting in load('training_protocol_proposal.json')['settings'].items():
        assert {'value', 'source', 'status', 'approval_required'} <= set(setting), name
        assert setting['status'] in STATUSES, name
        assert type(setting['approval_required']) is bool, name


def test_seed_list_reproduces_its_documented_derivation_and_pilot_uses_the_first_two():
    seeds = load('training_protocol_proposal.json')['settings']['seeds']['value']
    assert seeds == derived_seeds(20)
    pilot = load('feasibility_pilot_proposal.json')
    assert pilot['seeds'] == seeds[:2] and pilot['executed'] is False


def test_proposed_arms_and_schedules_construct_valid_controlled_configs():
    module, proposal = controlled(), load('training_protocol_proposal.json')
    s = {name: value['value'] for name, value in proposal['settings'].items()}
    assert set(proposal['arms']) == set(module.ARMS)
    assert s['supervised_warmup_epochs'] == s['ssl_epochs']
    jepa = importlib.import_module('solar_flare_jepa.training.jepa')
    architecture = jepa.JepaConfig(**s['architecture'], **s['jepa_objective'], quantiles=tuple(s['quantiles']),
                                   batch_size=s['batch_size'], lr=s['optimizer']['lr'],
                                   weight_decay=s['optimizer']['weight_decay'], gradient_clip=s['gradient_clip_norm'],
                                   max_train_windows=s['max_train_windows'], seed=s['seeds'][0],
                                   threads=s['precision_and_device']['torch_threads'])
    recipes = set()
    for arm, plan in proposal['arms'].items():
        schedule = module.TrainingSchedule(
            arm=arm, pretrain_epochs=plan['pretrain_epochs'], warmup_epochs=plan['warmup_epochs'],
            downstream_epochs=s['downstream_epochs'], early_stopping_patience=s['early_stopping'],
            train_loss=s['train_loss'], selection_metric=s['checkpoint_selection']['metric'],
            diagnostic_metrics=tuple(s['diagnostic_metrics']))
        recipes.add(module.ControlledConfig(architecture, schedule).recipe_fingerprint)
    assert len(recipes) == len(module.ARMS)  # arms are distinct recipes sharing one architecture


def test_proposed_comparators_construct_and_match_the_verified_tcn_arithmetic():
    module, s = comparators(), load('training_protocol_proposal.json')['settings']
    tcn, linear = s['tcn']['value'], s['quantile_linear']['value']
    config = module.TcnConfig(width=tcn['width'], kernel_size=tcn['kernel_size'], dilations=tuple(tcn['dilations']),
                              dropout=tcn['dropout'], seed=s['seeds']['value'][0], threads=4,
                              batch_size=tcn['batch_size'], lr=tcn['lr'], weight_decay=tcn['weight_decay'],
                              gradient_clip=tcn['gradient_clip'], quantiles=tuple(s['quantiles']['value']),
                              max_train_windows=tcn['max_train_windows'])
    model = module.build_tcn(protocol_spec(), config)
    assert sum(p.numel() for p in model.parameters()) == s['tcn']['verified']['parameters'] == 44620
    assert module.receptive_field(config) == s['tcn']['verified']['receptive_field_bins'] == 253
    grid = linear['lambdas']
    assert grid == sorted(grid) and grid[0] == 0.0 and len(set(grid)) == len(grid)
    module.QuantileLinearConfig(lambdas=tuple(grid), lr=linear['lr'], batch_size=linear['batch_size'],
                                epochs=linear['epochs'], seed=s['seeds']['value'][0], threads=4,
                                gradient_clip=linear['gradient_clip'], quantiles=tuple(s['quantiles']['value']),
                                max_train_windows=linear['max_train_windows'],
                                train_loss=s['train_loss']['value'],
                                selection_metric=s['checkpoint_selection']['value']['metric'])


def test_pilot_never_releases_test_data_and_has_bounded_resources():
    pilot = load('feasibility_pilot_proposal.json')
    assert any('release_test' in item for item in pilot['forbidden'])
    assert 'never calls release_test' in pilot['data']['test_handling']
    ceilings = pilot['resource_ceilings']
    assert 0 < ceilings['process_peak_rss_bytes'] <= 4 * 2**30 and ceilings['one_job_per_process'] is True
    assert all(0 < v <= 3600 for v in ceilings['per_job_timeout_seconds'].values())


def benchmark():
    import importlib.util
    path = Path(__file__).resolve().parents[1] / 'scripts' / 'benchmark_v2_feasibility.py'
    spec = importlib.util.spec_from_file_location('benchmark_v2_feasibility', path)
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    return bench


def test_benchmark_schedule_is_read_from_the_proposal():
    s = load('training_protocol_proposal.json')['settings']
    assert benchmark().PROPOSED == dict(
        ssl_epochs=s['ssl_epochs']['value'], warmup_epochs=s['supervised_warmup_epochs']['value'],
        downstream_epochs=s['downstream_epochs']['value'], linear_epochs=s['quantile_linear']['value']['epochs'],
        linear_lambdas=len(s['quantile_linear']['value']['lambdas']))


def test_benchmark_ssl_job_output_feeds_the_ssl_projection(tmp_path):
    # Review F1: the real ssl job output (not a hand-built dict) must yield an ssl_phase projection.
    import argparse
    bench = benchmark()
    args = argparse.Namespace(train_days=2, validation_days=1, max_train_windows=64, threads=1, ssl_epochs=1,
                              downstream_epochs=1, linear_epochs=1)
    result = bench.run_job('ssl', args, tmp_path)
    assert [e['phase'] for e in result['epochs']] == ['pretrain'] and result['artifact_bytes'] > 0
    seconds = bench.project(dict(ssl=result))['seconds']
    assert seconds['ssl_phase'] == pytest.approx(result['epochs'][0]['wall_seconds'] * bench.PROPOSED['ssl_epochs'])


def test_benchmark_projection_counts_warmup_once_and_uses_per_lambda_times():
    bench = benchmark()
    epochs = lambda phase, *values: [dict(phase=phase, epoch=i + 1, wall_seconds=v) for i, v in enumerate(values)]
    results = dict(
        ssl=dict(data_seconds=5., epochs=epochs('pretrain', 3.)),
        supervised=dict(data_seconds=5., epochs=epochs('downstream', 4., 2.)),
        supervised_extra_updates=dict(data_seconds=5., epochs=epochs('supervised_warmup', 3.)
                                      + epochs('downstream', 4., 2.)),
        quantile_linear=dict(data_seconds=5., epochs_per_lambda=2,
                             lambda_candidates=[dict(wall_seconds=0.5), dict(wall_seconds=0.1)]))
    seconds = bench.project(results)['seconds']
    assert seconds['ssl_phase'] == 3. * 8
    assert seconds['supervised_job_excluding_ssl'] == 5. + 4. + 14 * 2.
    assert seconds['supervised_extra_updates_job_excluding_ssl'] == 5. + 4. + 14 * 2. + 3. * 8
    assert seconds['quantile_linear_per_lambda'] == pytest.approx(0.1 * 50)
    lambdas = bench.PROPOSED['linear_lambdas']
    assert seconds['quantile_linear_proposed_lambdas'] == pytest.approx(5. + 0.4 + lambdas * 5.)
