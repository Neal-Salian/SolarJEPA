"""Bounded complete integration with no test observations or test window objects."""
from dataclasses import replace
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from m4b_helpers import controlled_config, development_windows, fit_model, LOSS
from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord
from solar_flare_jepa.experiments.provenance import source_fingerprint, verify_artifacts, verify_source_identities
from solar_flare_jepa.experiments.v2_evaluation_adapters import (
    build_evaluation_record, calendar_bounds, descriptive_budget_table, replicate_deterministic_record,
    split_identity, subset_records)
from solar_flare_jepa.experiments.v2_descriptive import descriptive_comparison
from solar_flare_jepa.experiments.v2_runner import JobSpec, RunConfig, StagedRun, _json_copy
from solar_flare_jepa.forecasting.baselines import make_baseline
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.training import controlled

ROOT = Path(__file__).resolve().parents[1]
ARMS = (*controlled.ARMS, 'tcn', 'quantile_linear')
SEEDS = (5, 6)


def test_synthetic_two_fold_all_models_descriptive_publication_without_test_access(tmp_path, monkeypatch):
    safety = importlib.import_module('solar_flare_jepa.experiments.v2_evaluation_safety')
    # Instrument the actual construction/release boundaries. There is no test
    # dataset even in the fixture; a future accidental test path fails here.
    original = build_partition_windows
    constructed = []
    def development_only(dataset, spec, partition, *args, **kwargs):
        constructed.append(partition.name)
        assert partition.name in ('train', 'validation')
        return original(dataset, spec, partition, *args, **kwargs)
    monkeypatch.setattr('m4b_helpers.build_partition_windows', development_only)
    def forbidden(*args, **kwargs):
        pytest.fail('synthetic development attempted test release or bootstrap inference')
    monkeypatch.setattr(StagedRun, 'release_test', forbidden)
    monkeypatch.setattr('solar_flare_jepa.evaluation.comparison.paired_comparison', forbidden)
    monkeypatch.setattr('solar_flare_jepa.evaluation.probabilistic.block_bootstrap', forbidden)
    source = source_fingerprint(ROOT)

    def execute(root):
        cohorts, calendars, model_records, runs = {}, {}, {}, {}
        for index, fold in enumerate(('fold-1', 'fold-2')):
            w = development_windows(offset_ns=index * 2 * 86_400_000_000_000)
            training, validation = w['train'].training_slice, w['validation']
            declared_test = f'UNRELEASED_SYNTHETIC_ID_{fold}'
            identity = dict(experiment_id='m4b-synthetic', code_fingerprint=source['fingerprint'],
                data_provenance_fingerprint=training.context.dataset_fingerprint,
                split_fingerprint=split_identity(w['train'].split_fingerprint,
                    validation.split_fingerprint, declared_test, fold_id=fold),
                protocol_fingerprint='M4B_SYNTHETIC_DEVELOPMENT_V1')
            plan = RunConfig(experiment_id=identity['experiment_id'],
                config=dict(execution_mode='DEVELOPMENT_ONLY', evaluation_identity=identity,
                            synthetic_epochs=1, max_train_windows=24, arms=list(ARMS), seeds=list(SEEDS)),
                dataset_fingerprint=training.context.dataset_fingerprint,
                split_identities=dict(train=w['train'].split_fingerprint, validation=validation.split_fingerprint),
                test_identity=declared_test, jobs=[JobSpec(arm, s) for arm in ARMS for s in SEEDS])
            run = safety.DevelopmentRun(root, fold, plan, training=training, validation=validation,
                embargo_ns=0, provenance=dict(code_fingerprint=source['fingerprint'], source_files=source['files']))
            assert run.allow_test_release is False
            artifacts = {s: controlled.pretrain_controlled(training, controlled_config('jepa_finetune', s))
                         for s in SEEDS}
            def fit(job, directory):
                arm, seed = job['arm'], job['seed']
                model = fit_model(arm, seed, w, pretraining=artifacts[seed] if arm in controlled.SSL_ARMS else None)
                model.save(directory / 'selected.pt')
                loaded = controlled.load_forecaster(directory / 'selected.pt')
                record = build_evaluation_record(model, validation, identity)
                reloaded = build_evaluation_record(loaded, validation, identity)
                assert reloaded.to_json() == record.to_json()
                (directory / 'evaluation.json').write_text(record.to_json())
                return dict(model_record=model.record, evaluation_record=record.as_dict())
            run.validate().fit(fit)
            assert all(job['status'] == 'succeeded' for job in run.snapshot()['jobs'].values())
            run.select(lambda jobs: dict(selected_job_ids=[job['job_id'] for job in jobs],
                criterion='each model already selected only on its validation support'))
            run.lock()
            assert run.stage == 'D_LOCKED' and run.snapshot()['release'] is None
            entries = list(_json_copy(run.snapshot())['jobs'].values())
            model_records[fold] = [job['record']['model_record'] for job in entries]
            assert len(model_records[fold]) == len(ARMS) * len(SEEDS)
            safety.check_comparator_cohort(model_records[fold])
            for seed in SEEDS:
                controlled.check_paired_cohort([r for r in model_records[fold]
                    if r['seed'] == seed and r['model_kind'] == controlled.MODEL_KIND])
            by_arm = {arm: [EvaluationRecord.from_dict(job['record']['evaluation_record']) for job in entries
                if job['spec']['arm'] == arm] for arm in ARMS}
            for arm, records in by_arm.items():
                records.sort(key=lambda r: r.identity.seed)
                assert tuple(r.identity.seed for r in records) == SEEDS
                for record in records:
                    assert record.prediction.grid.origin_ids == validation.context.origin_ids
                    assert record.prediction.quantiles.shape[1:] == (5, 2, 5)
                    assert record.prediction.grid.spec.target_names == ('a', 'b')
            # Linear really is fitted per seed. Classical persistence is fitted
            # once and its reused seed labels explicitly attest replication.
            classical = make_baseline('persistence', {}).fit(training)
            reference = by_arm['supervised'][0].identity
            classical_record = EvaluationRecord(replace(reference, model_version='classical:persistence',
                config_fingerprint='fixed-persistence'), validation.targets,
                classical.predict(validation.context, validation.targets.grid))
            replicated, metadata = replicate_deterministic_record(classical_record, SEEDS,
                deterministic=True, source_execution_id=f'{fold}:fixed-persistence')
            assert metadata['independent_seed_runs'] is False
            np.testing.assert_array_equal(replicated[0].prediction.values, replicated[1].prediction.values)
            assert subset_records(by_arm['jepa_finetune'], (5,))[0].identity.seed == 5
            cohorts[fold], calendars[fold], runs[fold] = by_arm, calendar_bounds(validation), run
        report = descriptive_comparison({f: c['jepa_finetune'] for f, c in cohorts.items()},
            {f: c['supervised'] for f, c in cohorts.items()}, calendars=calendars)
        assert report['status'] == 'DESCRIPTIVE_ONLY' and report['inference_status'] == 'INFERENCE_UNAVAILABLE'
        assert report['difference_interval'] is None and report['p_value'] is None
        assert len(report['folds']) == 2 and report['seed_ids'] == list(SEEDS)
        assert report == descriptive_comparison({f: c['jepa_finetune'] for f, c in cohorts.items()},
            {f: c['supervised'] for f, c in cohorts.items()}, calendars=calendars)
        for alternative in ('jepa_frozen', 'random_frozen', 'tcn', 'quantile_linear', 'supervised_extra_updates'):
            secondary = descriptive_comparison(
                {f: subset_records(c['jepa_finetune'], (5,)) for f, c in cohorts.items()},
                {f: subset_records(c[alternative], (5,)) for f, c in cohorts.items()}, calendars=calendars)
            assert secondary['seed_ids'] == [5]
            assert secondary['inference_status'] == 'INFERENCE_UNAVAILABLE'
            assert secondary['difference_interval'] is None
        budget = descriptive_budget_table(model_records)
        assert budget['acceptance'] is None and len(budget['jobs']) == 28
        verify_source_identities(ROOT, source['files'])
        for fold, run in runs.items():
            destination = run.publish_development({'descriptive.json': report, 'budgets.json': budget})
            manifest = verify_artifacts(destination)
            assert manifest['files'] and run.stage == 'D_LOCKED'
            assert run.snapshot()['release'] is None
            before = (destination / 'descriptive.json').read_bytes()
            with pytest.raises(FileExistsError):
                run.publish_development({'descriptive.json': {'changed': True}})
            assert (destination / 'descriptive.json').read_bytes() == before
        return report, {fold: {arm: [r.fingerprint for r in records] for arm, records in cohort.items()}
                        for fold, cohort in cohorts.items()}

    first = execute(tmp_path / 'first')
    repeat = execute(tmp_path / 'repeat')
    assert first == repeat
    assert set(constructed) == {'train', 'validation'}
