"""Synthetic guard/report bridge: no native reads, model builds, fits or predictions."""
from copy import deepcopy
import json
from types import SimpleNamespace

import numpy as np

from test_v2_pilot_reporting import fixture as reporting_fixture
from solar_flare_jepa.data import goes_v2_development
from solar_flare_jepa.evaluation.records import EvaluationIdentity, EvaluationRecord
from solar_flare_jepa.experiments import v2_pilot, v2_pilot_protocol
from solar_flare_jepa.experiments.v2_interfaces import evaluation_identity_fields
from solar_flare_jepa.experiments.v2_pilot_reporting import build_report, validate_report
from solar_flare_jepa.forecasting.contracts import (
    ForecastPrediction, ForecastSpec, TimeSeriesDataset, fingerprint_payload,
)
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import build_partition_windows
from solar_flare_jepa.training.controlled import _validation_identity, _window_record
from solar_flare_jepa.training.jepa import training_windows
from solar_flare_jepa.training.normalization import Normalization


def test_synthetic_records_pass_real_fitting_guards_locks_and_strict_report_publication(tmp_path, monkeypatch):
    """Import declared fixture records through the actual 14+4 guarded pipeline.

    The training hook only copies clearly synthetic bytes and returns handcrafted
    records. No loader, trainer, predictor or checkpoint deserializer executes.
    Actual temporal/support/config/cohort guards and report validation stay on.
    """
    design, payloads, accounting = reporting_fixture()
    spec = ForecastSpec(**design['data']['forecast'])
    minute_ns = 60 * 10**9

    def utc_ns(value):
        return int(np.datetime64(value.rstrip('Z'), 'ns').astype(np.int64))

    starts = np.concatenate([
        utc_ns('2024-05-01') + np.arange(300) * minute_ns,
        utc_ns('2024-07-22') + np.arange(300) * minute_ns,
        [utc_ns('2024-08-01') - minute_ns],
    ])
    values = 10. ** np.column_stack((
        -6 + .2 * np.sin(np.arange(len(starts)) / 10),
        -5 + .2 * np.cos(np.arange(len(starts)) / 10),
    ))
    mask = np.ones_like(values, bool)
    dataset = TimeSeriesDataset('synthetic-guard-bridge', 'synthetic_fixture', starts,
        starts + minute_ns, values, mask, values, mask, tuple(spec.feature_names),
        tuple(spec.target_names), tuple(spec.feature_units), tuple(spec.target_units), 60,
        availability_policy='bin_end_earliest')
    partitions = {name: build_partition_windows(dataset, spec,
        TemporalPartition(name, utc_ns(bounds[0]), utc_ns(bounds[1])))
        for name, bounds in design['data']['splits_utc_half_open'].items()}
    training, validation = partitions['train'].training_slice, partitions['validation']
    normalization = Normalization.fit(training)
    lazy = training_windows(training, normalization, stride=1)
    window_record = _window_record(lazy, lazy.subsample(20000), 20000)
    split_ids = {name: window.split_fingerprint for name, window in partitions.items()}
    evidence = dict(dataset_fingerprint=dataset.fingerprint, forecast_fingerprint=spec.fingerprint,
        split_fingerprint=fingerprint_payload(split_ids), split_fingerprints=split_ids,
        training_fingerprint=training.fingerprint, normalization_fingerprint=normalization.fingerprint,
        train_windows=window_record)
    bundle = SimpleNamespace(dataset=dataset, training=training, validation=validation,
        normalization=normalization, evidence=evidence)
    data_identity = dict(evidence,
        validation_content_fingerprint=_validation_identity(validation)['content_fingerprint'])
    context = dict(approval=dict(data_root='SYNTHETIC_IN_MEMORY_ONLY', data_identity=data_identity),
        runtime=deepcopy(accounting['runtime']), binding_fingerprint='synthetic-binding', design=design)
    declarations = v2_pilot_protocol.evaluation_identity(context, bundle)
    for job in design['jobs']:
        if job['development_run'] is None:
            continue
        payload = payloads[job['job_id']]
        record = payload['model_record']
        record.update(spec_fingerprint=spec.fingerprint, normalization_fingerprint=normalization.fingerprint,
            training_fingerprint=training.fingerprint, training_dataset_fingerprint=dataset.fingerprint,
            train_windows=window_record, validation=_validation_identity(validation))
        targets = validation.targets
        quantiles = np.repeat(targets.values[..., None], 5, axis=-1) * np.array([.5, .8, 1., 1.2, 1.5])
        prediction = ForecastPrediction(quantiles[..., 2], targets.grid, record['model_id'],
            tuple(design['training']['quantiles']), quantiles)
        identity = EvaluationIdentity(**evaluation_identity_fields(record, **declarations))
        payload['evaluation_record'] = EvaluationRecord(identity, targets, prediction).as_dict()
    monkeypatch.setattr(goes_v2_development, 'load_development', lambda *args, **kwargs: bundle)
    paths = {}
    synthetic_checkpoint = b'SYNTHETIC_FIXTURE_NO_MODEL_OR_TRAINED_WEIGHTS'
    for job_id, payload in payloads.items():
        path = tmp_path / 'synthetic-workers' / job_id
        path.mkdir(parents=True)
        paths[job_id] = path
        (path / 'selected.pt').write_bytes(synthetic_checkpoint)
        (path / 'result.json').write_text(json.dumps(payload))
        (path / 'binding.json').write_text('{"synthetic_fixture":true}')
    runs = v2_pilot._guarded_runs(context, tmp_path / 'staging', payloads, paths)
    accounting['development_locks'] = {cohort: run.snapshot()['lock']['fingerprint']
                                       for cohort, run in runs.items()}
    report = build_report(design, payloads, accounting=accounting)
    validate_report(report)
    assert len(report['comparisons']) == 10
    assert len(report['models']) == 18
    assert report['inference_reason'] == 'NO_VALIDATED_REPLACEMENT'
    assert {cohort: (run.stage, len(run.plan.jobs)) for cohort, run in runs.items()} == {
        'primary': ('D_LOCKED', 14), 'alternate_loss': ('D_LOCKED', 4)}
    for run in runs.values():
        snapshot = run.snapshot()
        assert [(hook['stage'], hook['result']['passed']) for hook in snapshot['hooks']] == [
            ('B_FITTED', True), ('C_SELECTED', True), ('D_LOCKED', True)]
        publication = run.publish_development({'pilot_report.json': report})
        saved = json.loads((publication / 'pilot_report.json').read_text())
        assert validate_report(saved) == report
        status = json.loads((publication / 'development_status.json').read_text())
        assert status['test_released'] is False
        assert status['m3_verdict'] == 'NO_VALIDATED_REPLACEMENT'
        assert all((paths[job_id] / 'selected.pt').read_bytes() == synthetic_checkpoint
                   for job_id in paths)
