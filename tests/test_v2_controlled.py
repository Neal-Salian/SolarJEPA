"""V2 controlled JEPA/supervised arms: pairing, budgets, schedules, selection, isolation, identity."""
import copy
from dataclasses import replace
import importlib
import json
import math

import numpy as np
import pytest

torch = pytest.importorskip('torch')

from test_jepa import fixture, tiny  # noqa: E402

EPOCHS = dict(pretrain=2, warmup=2, downstream=4)


def controlled():
    return importlib.import_module('solar_flare_jepa.training.controlled')


def schedule(arm, *, patience=None, train='dex_pinball_equal_channel_v2', select=None, diagnostics=None):
    module = controlled()
    ssl = arm in ('jepa_finetune', 'jepa_frozen')
    other = 'normalized_pinball_v1' if train != 'normalized_pinball_v1' else 'dex_pinball_equal_channel_v2'
    return module.TrainingSchedule(
        arm=arm, pretrain_epochs=EPOCHS['pretrain'] if ssl else 0,
        warmup_epochs=EPOCHS['warmup'] if arm == 'supervised_extra_updates' else 0,
        downstream_epochs=EPOCHS['downstream'], early_stopping_patience=patience,
        train_loss=train, selection_metric=select or train,
        diagnostic_metrics=(other,) if diagnostics is None else diagnostics)


def fit_arm(arm, windows=None, config=None, **kwargs):
    module = controlled()
    windows = fixture() if windows is None else windows
    cfg = module.ControlledConfig(config or tiny(), schedule(arm))
    return module.fit_controlled(windows['train'].training_slice, windows['validation'], cfg, **kwargs)


@pytest.fixture(scope='module')
def arms():
    windows = fixture()
    return {arm: fit_arm(arm, windows) for arm in controlled().ARMS}, windows


def _per_epoch(record):
    return math.ceil(record['train_windows']['used'] / record['config']['architecture']['batch_size'])


# ------------------------------------------------------------------ configuration


def test_schedule_requires_every_budget_and_enforces_arm_structure():
    module = controlled()
    with pytest.raises(TypeError):
        module.TrainingSchedule(arm='supervised')  # no implicit budgets
    base = dict(arm='supervised', pretrain_epochs=0, warmup_epochs=0, downstream_epochs=3,
                early_stopping_patience=None, train_loss='dex_pinball_equal_channel_v2',
                selection_metric='dex_pinball_equal_channel_v2')
    module.TrainingSchedule(**base)
    bad = [dict(arm='ensemble'), dict(pretrain_epochs=1), dict(warmup_epochs=1), dict(downstream_epochs=0),
           dict(early_stopping_patience=0), dict(train_loss='mse'), dict(selection_metric='mae'),
           dict(diagnostic_metrics=('dex_pinball_equal_channel_v2',)), dict(downstream_epochs=True),
           dict(arm='jepa_finetune'), dict(arm='supervised_extra_updates'), dict(diagnostic_metrics=['x'])]
    for change in bad:
        with pytest.raises(ValueError):
            module.TrainingSchedule(**dict(base, **change))
    with pytest.raises(ValueError, match='auxiliary'):
        module.ControlledConfig(tiny(jepa_weight_during_finetune=0.5), module.TrainingSchedule(**base))


def test_configuration_identity_separates_recipe_from_seed():
    module = controlled()
    one = module.ControlledConfig(tiny(seed=3), schedule('jepa_finetune'))
    two = module.ControlledConfig(tiny(seed=4), schedule('jepa_finetune'))
    assert one.recipe_fingerprint == two.recipe_fingerprint
    assert one.run_fingerprint != two.run_fingerprint
    assert module.ControlledConfig(tiny(seed=3), schedule('jepa_finetune')).run_fingerprint == one.run_fingerprint
    changed = [module.ControlledConfig(tiny(seed=3), schedule('jepa_frozen')),
               module.ControlledConfig(tiny(seed=3, width=32, heads=2), schedule('jepa_finetune')),
               module.ControlledConfig(tiny(seed=3), schedule('jepa_finetune', train='normalized_pinball_v1')),
               module.ControlledConfig(tiny(seed=3), replace(schedule('jepa_finetune'), downstream_epochs=5))]
    assert len({one.recipe_fingerprint, *(c.recipe_fingerprint for c in changed)}) == 5
    # The V1 schedule fields of JepaConfig are overridden, never silently mixed in.
    assert (module.ControlledConfig(tiny(seed=3, finetune_epochs=9, patience=7), schedule('jepa_finetune')).run_fingerprint
            == one.run_fingerprint)
    restored = module.ControlledConfig.from_dict(json.loads(json.dumps(one.as_dict())))
    assert restored.run_fingerprint == one.run_fingerprint


# --------------------------------------------------------------- V1 compatibility


@pytest.mark.parametrize('variant,dropout', [('jepa_finetune', 0.), ('jepa_frozen', 0.), ('supervised', 0.),
                                             ('jepa_finetune', .2), ('supervised', .2)])
def test_v1_compatibility_mode_reproduces_v1_fit_forecaster_bitwise(variant, dropout):
    # Dropout > 0 makes the Torch RNG matter, so this also pins the downstream reseed.
    module = controlled()
    jepa = importlib.import_module('solar_flare_jepa.training.jepa')
    windows = fixture()
    config = tiny(dropout=dropout)
    v1 = jepa.fit_forecaster(windows['train'].training_slice, windows['validation'], config, variant)
    v2 = module.fit_controlled(windows['train'].training_slice, windows['validation'],
                               module.ControlledConfig(config, module.v1_compatible_schedule(variant, config)))
    left, right = v1._model.state_dict(), v2.model.state_dict()
    assert left.keys() == right.keys() and all(torch.equal(left[k], right[k]) for k in left)
    assert v1.record['selection']['epoch'] == v2.record['selection']['epoch']
    assert ([e['validation_pinball'] for e in v1.record['finetune_history']]
            == [e['metrics']['normalized_pinball_v1'] for e in v2.record['history'] if e['phase'] == 'downstream'])
    grid = windows['test'].targets.grid
    a, b = v1.predict(windows['test'].context, grid), v2.predict(windows['test'].context, grid)
    assert np.array_equal(a.quantiles, b.quantiles) and np.array_equal(a.values, b.values)


# ------------------------------------------------------------ pairing and budgets


def test_all_arms_share_initial_state_window_subset_and_downstream_order(arms):
    fitted, _ = arms
    records = {arm: model.record for arm, model in fitted.items()}
    for key in ('initial_state', 'downstream_order', 'train_windows'):
        values = {json.dumps(r['pairing'][key] if key != 'train_windows' else r['train_windows'], sort_keys=True)
                  for r in records.values()}
        assert len(values) == 1, key
    # The extra-update control replays the exact SSL window order of the JEPA arm.
    assert (records['supervised_extra_updates']['pairing']['warmup_order']
            == records['jepa_finetune']['pairing']['pretrain_order'])
    assert records['supervised']['pairing']['pretrain_order'] is None


def test_optimizer_step_and_parameter_update_accounting(arms):
    fitted, _ = arms
    p, w, d = EPOCHS['pretrain'], EPOCHS['warmup'], EPOCHS['downstream']
    per = _per_epoch(fitted['supervised'].record)
    expected = {  # module -> (ssl, warmup, downstream) updates of every tensor
        'jepa_finetune': dict(encoder=(p, 0, d), predictor=(p, 0, d), head=(0, 0, d)),
        'supervised': dict(encoder=(0, 0, d), predictor=(0, 0, d), head=(0, 0, d)),
        'supervised_extra_updates': dict(encoder=(0, w, d), predictor=(0, w, d), head=(0, w, d)),
        'jepa_frozen': dict(encoder=(p, 0, 0), predictor=(p, 0, 0), head=(0, 0, d)),
        'random_frozen': dict(encoder=(0, 0, 0), predictor=(0, 0, 0), head=(0, 0, d)),
    }
    for arm, modules in expected.items():
        budget = fitted[arm].record['budget']
        phases = {phase['phase']: phase for phase in budget['phases']}
        for index, name in enumerate(('pretrain', 'supervised_warmup', 'downstream')):
            epochs = (p, w, d)[index] if any(v[index] for v in modules.values()) else 0
            if not epochs:
                assert name not in phases
                continue
            phase = phases[name]
            assert phase['epochs_executed'] == epochs and phase['optimizer_steps'] == epochs * per
            assert phase['examples_seen'] == epochs * fitted[arm].record['train_windows']['used']
            for module_name, counts in modules.items():
                updates = phase['parameter_updates'][module_name]
                assert updates['min'] == updates['max'] == counts[index] * per, (arm, name, module_name)
        totals = budget['totals']
        assert totals['optimizer_steps'] == sum(ph['optimizer_steps'] for ph in budget['phases'])
        for module_name, counts in modules.items():
            assert totals['parameter_updates'][module_name] == sum(counts) * per
        assert totals['parameter_updates']['target_encoder'] == 0  # EMA is not an optimizer update
        assert totals['ema_target_updates'] == (p * per if arm in ('jepa_finetune', 'jepa_frozen') else 0)
    jepa, extra = fitted['jepa_finetune'].record['budget'], fitted['supervised_extra_updates'].record['budget']
    assert jepa['totals']['optimizer_steps'] == extra['totals']['optimizer_steps']


def test_recorded_steps_equal_actual_optimizer_step_calls(monkeypatch):
    calls = []
    original = torch.optim.AdamW.step

    def counted(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(torch.optim.AdamW, 'step', counted)
    for arm in ('jepa_finetune', 'supervised_extra_updates'):
        calls.clear()
        model = fit_arm(arm)
        assert len(calls) == model.record['budget']['totals']['optimizer_steps'] > 0


def test_fixed_schedule_executes_every_epoch_and_selects_earliest_minimum(arms):
    fitted, _ = arms
    for arm, model in fitted.items():
        record = model.record
        downstream = [e for e in record['history'] if e['phase'] == 'downstream']
        assert [e['epoch'] for e in downstream] == list(range(1, EPOCHS['downstream'] + 1))
        values = [e['metrics'][record['selection']['metric']] for e in downstream]
        assert record['selection']['epoch'] == int(np.argmin(values)) + 1
        assert record['selection']['value'] == min(values)
        assert record['selection']['eligible_phase'] == 'downstream' and record['selection']['stopped_early'] is False
        warmups = [e for e in record['history'] if e['phase'] == 'supervised_warmup']
        assert len(warmups) == (EPOCHS['warmup'] if arm == 'supervised_extra_updates' else 0)
        assert all('metrics' not in e for e in warmups)


def test_earliest_epoch_wins_exact_ties():
    module = controlled()
    assert module._select_epoch([0.5, 0.4, 0.4, 0.6]) == 2
    assert module._select_epoch([0.3]) == 1
    with pytest.raises(ValueError):
        module._select_epoch([0.3, float('nan')])


def test_patience_mode_stops_after_stale_epochs():
    module = controlled()
    history = [0.5, 0.6, 0.7, 0.2]
    assert module._should_stop(history[:3], 2) is True
    assert module._should_stop(history[:2], 2) is False
    assert module._should_stop(history, None) is False


def test_selected_metric_reproduces_from_saved_model_and_matches_log_scores(arms):
    from solar_flare_jepa.evaluation.probabilistic import log_scores
    fitted, windows = arms
    valid = windows['validation']
    for arm in ('jepa_finetune', 'supervised'):
        model = fitted[arm]
        prediction = model.predict(valid.context, valid.targets.grid)
        dex = log_scores(valid.targets, prediction, valid.context.spec)['mean_pinball']
        assert model.record['selection']['metric'] == 'dex_pinball_equal_channel_v2'
        assert model.record['selection']['value'] == pytest.approx(dex, rel=2e-5)


# ------------------------------------------------------- freezing and teacher isolation


def test_frozen_arms_never_change_encoder_or_predictor(arms):
    fitted, _ = arms
    for arm, reference in (('jepa_frozen', 'after_pretrain'), ('random_frozen', 'initial')):
        fingerprints = fitted[arm].record['fingerprints']
        for module_name in ('encoder', 'predictor'):
            assert fingerprints['selected'][module_name] == fingerprints[reference][module_name]
        assert fingerprints['selected']['head'] != fingerprints[reference]['head']
    jepa, frozen = fitted['jepa_finetune'].record['fingerprints'], fitted['jepa_frozen'].record['fingerprints']
    assert jepa['after_pretrain'] == frozen['after_pretrain']
    assert fitted['jepa_finetune'].record['fingerprints']['selected']['encoder'] != jepa['after_pretrain']['encoder']


def test_teacher_is_isolated_from_gradients_and_forecasting(arms):
    fitted, windows = arms
    for arm, model in fitted.items():
        fingerprints = model.record['fingerprints']
        reference = 'after_pretrain' if arm in ('jepa_finetune', 'jepa_frozen') else 'initial'
        assert fingerprints['selected']['target_encoder'] == fingerprints[reference]['target_encoder']
        assert all(not p.requires_grad and p.grad is None for p in model.model.target_encoder.parameters())
    model = copy.deepcopy(fitted['jepa_finetune'])  # never mutate the shared fixture
    grid = windows['test'].targets.grid
    before = model.predict(windows['test'].context, grid).quantiles
    with torch.no_grad():
        for parameter in model.model.target_encoder.parameters():
            parameter.add_(torch.randn_like(parameter))
    assert np.array_equal(before, model.predict(windows['test'].context, grid).quantiles)


# ------------------------------------------------------ reuse, determinism, holdouts


def test_pretraining_artifact_reuse_equals_recomputation(tmp_path):
    module = controlled()
    windows = fixture()
    config = module.ControlledConfig(tiny(), schedule('jepa_finetune'))
    artifact = module.pretrain_controlled(windows['train'].training_slice, config)
    artifact.save(tmp_path / 'ssl.pt')
    loaded = module.PretrainingArtifact.load(tmp_path / 'ssl.pt')
    assert loaded.fingerprint == artifact.fingerprint
    fresh = fit_arm('jepa_finetune', windows)
    reused = fit_arm('jepa_finetune', windows, pretraining=loaded)
    frozen = module.fit_controlled(windows['train'].training_slice, windows['validation'],
                                   module.ControlledConfig(tiny(), schedule('jepa_frozen')), pretraining=loaded)
    a, b = fresh.model.state_dict(), reused.model.state_dict()
    assert all(torch.equal(a[k], b[k]) for k in a)
    assert fresh.record['history'] == reused.record['history'] or all(
        {k: v for k, v in x.items() if k != 'wall_seconds'} == {k: v for k, v in y.items() if k != 'wall_seconds'}
        for x, y in zip(fresh.record['history'], reused.record['history']))
    assert reused.record['pretraining']['reused'] is True and fresh.record['pretraining']['reused'] is False
    assert frozen.record['pretraining']['artifact_fingerprint'] == artifact.fingerprint
    wrong = [module.ControlledConfig(tiny(seed=6), schedule('jepa_finetune')),
             module.ControlledConfig(tiny(width=32, heads=2), schedule('jepa_finetune')),
             module.ControlledConfig(tiny(), replace(schedule('jepa_finetune'), pretrain_epochs=1)),
             module.ControlledConfig(tiny(max_train_windows=50), schedule('jepa_finetune'))]
    for cfg in wrong:
        with pytest.raises(ValueError, match='Pretraining artifact identity'):
            module.fit_controlled(windows['train'].training_slice, windows['validation'], cfg, pretraining=loaded)
    with pytest.raises(ValueError, match='does not use'):
        fit_arm('supervised', windows, pretraining=loaded)
    (tmp_path / 'ssl.pt').write_bytes((tmp_path / 'ssl.pt').read_bytes()[:-20] + b'0' * 20)
    with pytest.raises(ValueError):
        module.PretrainingArtifact.load(tmp_path / 'ssl.pt')


def test_seed_determinism_and_sensitivity():
    one, two = fit_arm('supervised_extra_updates'), fit_arm('supervised_extra_updates')
    a, b = one.model.state_dict(), two.model.state_dict()
    assert all(torch.equal(a[k], b[k]) for k in a)
    other = fit_arm('supervised_extra_updates', config=tiny(seed=6))
    assert other.record['pairing']['initial_state'] != one.record['pairing']['initial_state']


def test_held_out_values_cannot_change_any_arm():
    windows = fixture(heldout_multiplier=1., test_multiplier=1e3)
    base = fixture()
    for arm in ('random_frozen', 'supervised_extra_updates'):
        a, b = fit_arm(arm, base).model.state_dict(), fit_arm(arm, windows).model.state_dict()
        assert all(torch.equal(a[k], b[k]) for k in a)


# ---------------------------------------------------------------- checkpointing


def test_checkpoint_round_trip_and_tamper_detection(arms, tmp_path):
    module = controlled()
    fitted, windows = arms
    grid = windows['test'].targets.grid
    for arm, model in fitted.items():
        path = tmp_path / f'{arm}.pt'
        model.save(path)
        with pytest.raises(FileExistsError):
            model.save(path)
        loaded = module.load_forecaster(path)
        assert loaded.model_id == model.model_id == f'v2_{arm}'
        assert loaded.record == model.record
        assert np.array_equal(loaded.predict(windows['test'].context, grid).quantiles,
                              model.predict(windows['test'].context, grid).quantiles)
    payload = torch.load(tmp_path / 'supervised.pt', weights_only=True)
    payload['record_json'] = payload['record_json'].replace('"supervised"', '"jepa_finetune"', 1)
    torch.save(payload, tmp_path / 'tampered.pt')
    with pytest.raises(ValueError):
        module.load_forecaster(tmp_path / 'tampered.pt')


def test_prediction_rejects_other_spec_and_returns_ordered_native_quantiles(arms):
    fitted, windows = arms
    model = fitted['random_frozen']
    prediction = model.predict(windows['test'].context, windows['test'].targets.grid)
    assert prediction.quantiles.shape == (len(windows['test'].context.origin_ids), 5, 2, 5)
    assert (np.diff(prediction.quantiles, axis=-1) >= 0).all() and (prediction.quantiles > 0).all()
    assert prediction.model_id == 'v2_random_frozen'
    with pytest.raises(ValueError):
        model.predict(windows['test'].targets.grid, windows['test'].context)


# ------------------------------------------------------- review regression tests


def test_forged_pretraining_artifact_with_other_seed_weights_is_rejected():
    module = controlled()
    windows = fixture()
    config5 = module.ControlledConfig(tiny(seed=5), schedule('jepa_frozen'))
    config6 = module.ControlledConfig(tiny(seed=6), schedule('jepa_frozen'))
    five = module.pretrain_controlled(windows['train'].training_slice, config5)
    six = module.pretrain_controlled(windows['train'].training_slice, config6)
    record = dict(five.record, state_fingerprint=six.record['state_fingerprint'])
    forged = module.PretrainingArtifact(six.state, record)
    with pytest.raises(ValueError, match='Pretraining artifact identity'):
        module.fit_controlled(windows['train'].training_slice, windows['validation'], config5, pretraining=forged)


def test_checkpoint_cannot_carry_another_arms_weights(arms, tmp_path):
    module = controlled()
    from solar_flare_jepa.training.core import _cpu_state, _weights_fingerprint
    fitted, _ = arms
    fitted['jepa_finetune'].save(tmp_path / 'j.pt')
    payload = torch.load(tmp_path / 'j.pt', weights_only=True)
    payload['model_state'] = _cpu_state(fitted['supervised'].model.state_dict())
    payload['weights_fingerprint'] = _weights_fingerprint(payload['model_state'])
    torch.save(payload, tmp_path / 'swapped.pt')
    with pytest.raises(ValueError, match='selected weights'):
        module.load_forecaster(tmp_path / 'swapped.pt')


def test_paired_cohort_check_accepts_matched_arms_and_rejects_budget_mismatch(arms):
    module = controlled()
    fitted, windows = arms
    records = [model.record for model in fitted.values()]
    with pytest.raises(ValueError, match='SSL artifact'):  # fixture arms each ran their own SSL
        module.check_paired_cohort(records)
    without_frozen = [r for r in records if r['arm'] != 'jepa_frozen']
    summary = module.check_paired_cohort(without_frozen)
    assert summary['seeds'] == [5] and summary['records'] == 4
    longer = module.fit_controlled(windows['train'].training_slice, windows['validation'], module.ControlledConfig(
        tiny(), replace(schedule('supervised_extra_updates'), warmup_epochs=3)))
    mixed = [r for r in without_frozen if r['arm'] != 'supervised_extra_updates'] + [longer.record]
    with pytest.raises(ValueError, match='replay the JEPA SSL'):
        module.check_paired_cohort(mixed)
    other = fit_arm('supervised', windows, config=tiny(width=32, heads=2))
    with pytest.raises(ValueError, match='architectures differ'):
        module.check_paired_cohort(without_frozen + [dict(other.record, seed=7)])


def test_paired_cohort_accepts_frozen_arm_sharing_the_ssl_artifact():
    module = controlled()
    windows = fixture()
    artifact = module.pretrain_controlled(windows['train'].training_slice,
                                          module.ControlledConfig(tiny(), schedule('jepa_finetune')))
    records = [fit_arm(arm, windows, pretraining=artifact).record for arm in ('jepa_finetune', 'jepa_frozen')]
    records += [fit_arm(arm, windows).record for arm in ('supervised', 'supervised_extra_updates', 'random_frozen')]
    assert module.check_paired_cohort(records)['arms'] == sorted(module.ARMS)
