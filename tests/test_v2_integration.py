"""End-to-end synthetic V2 run: controlled arms + TCN through the staged runner A→F."""
import importlib
import json

import numpy as np
import pytest

torch = pytest.importorskip('torch')

from test_jepa import fixture, tiny  # noqa: E402
from solar_flare_jepa.experiments import v2_runner as v2  # noqa: E402
from solar_flare_jepa.forecasting.contracts import canonical_json  # noqa: E402

LOSS = 'dex_pinball_equal_channel_v2'


def schedule(controlled, arm):
    return controlled.TrainingSchedule(
        arm=arm, pretrain_epochs=1 if arm in controlled.SSL_ARMS else 0,
        warmup_epochs=1 if arm == 'supervised_extra_updates' else 0, downstream_epochs=2,
        early_stopping_patience=None, train_loss=LOSS, selection_metric=LOSS)


def test_synthetic_paired_run_through_every_stage(tmp_path):
    controlled = importlib.import_module('solar_flare_jepa.training.controlled')
    comparators = importlib.import_module('solar_flare_jepa.training.comparators')
    development = fixture()
    train, validation = development['train'], development['validation']
    held_test_identity = fixture()['test'].split_fingerprint  # custodian's declaration only
    arms = ('jepa_finetune', 'supervised', 'supervised_extra_updates', 'tcn')
    plan = v2.RunConfig(
        experiment_id='v2-synthetic-integration', config=dict(loss=LOSS, epochs=2, arms=list(arms)),
        dataset_fingerprint=train.training_slice.context.dataset_fingerprint,
        split_identities=dict(train=train.split_fingerprint, validation=validation.split_fingerprint),
        test_identity=held_test_identity, jobs=tuple(v2.JobSpec(arm, seed) for arm in arms for seed in (5, 6)),
        approval_status=v2.APPROVED)  # synthetic test-only approval of a synthetic plan
    run = v2.StagedRun(tmp_path, 'integration', plan, allow_test_release=True)

    def fit(job, job_dir):
        if job['arm'] == 'tcn':
            model = comparators.fit_tcn(
                train.training_slice, validation,
                comparators.TcnConfig(width=8, kernel_size=3, dilations=(1, 2), dropout=0., seed=job['seed'],
                                      threads=1, batch_size=16, lr=1e-3, weight_decay=1e-4, gradient_clip=1.,
                                      quantiles=(0.05, 0.25, 0.5, 0.75, 0.95), max_train_windows=None),
                comparators.ComparatorSchedule(downstream_epochs=2, early_stopping_patience=None,
                                               train_loss=LOSS, selection_metric=LOSS))
        else:
            config = controlled.ControlledConfig(tiny(seed=job['seed']), schedule(controlled, job['arm']))
            model = controlled.fit_controlled(train.training_slice, validation, config)
        model.save(job_dir / 'model.pt')
        record = model.record
        return dict(model_id=record['model_id'], selection=record['selection'],
                    optimizer_steps=record['budget']['totals']['optimizer_steps'],
                    initial_state=record['pairing']['initial_state'],
                    downstream_order=record['pairing']['downstream_order'])

    run.validate()
    run.fit(fit)
    jobs = run.snapshot()['jobs']
    assert all(job['status'] == 'succeeded' for job in jobs.values())
    by_seed = {}
    for job in jobs.values():
        by_seed.setdefault(job['spec']['seed'] if 'spec' in job else job['seed'], []).append(job['record'])
    for records in by_seed.values():
        neural = [r for r in records if r['model_id'] != 'v2_tcn_quantile']
        assert len({r['initial_state'] for r in neural}) == 1
        assert len({r['downstream_order'] for r in records}) == 1
    with pytest.raises(v2.InvalidTransition):
        run.release_test(None, held_test_identity, None)
    run.select(lambda records: dict(selected_job_ids=sorted(r['job_id'] for r in records
                                                            if r['status'] == 'succeeded'),
                                    criterion='all succeeded jobs are reported; no cross-model test selection'))
    run.lock()

    test = fixture()['test']  # the custodian supplies the held-out partition only now

    def predict(job, locked_dir, output_dir):
        model = controlled.load_forecaster(locked_dir / 'model.pt')
        prediction = model.predict(test.context, test.targets.grid)
        with (output_dir / 'quantiles.npy').open('xb') as stream:
            np.save(stream, prediction.quantiles)
        return dict(model_id=prediction.model_id, origins=len(test.context.origin_ids))

    authorization = v2.TestReleaseAuthorization(
        approval_status=v2.APPROVED, config_fingerprint=run.plan.config_fingerprint,
        lock_fingerprint=run.lock_fingerprint, authorized_by='synthetic-custodian', reference='integration-test')
    run.release_test(authorization, test.split_fingerprint, predict)
    destination = run.publish(contents={'summary.json': dict(jobs=len(jobs))})
    assert run.stage == 'F_PUBLISHED'
    ledger = json.loads((destination / 'run_ledger.json').read_text())
    assert canonical_json(ledger)
    assert len(ledger['release']['jobs']) == len(jobs)
