"""Published forecasts and scores must consume the same canonical prediction."""
from copy import deepcopy
from dataclasses import replace
import importlib
import json

import numpy as np
import pytest

from solar_flare_jepa.forecasting.contracts import ForecastPrediction
from solar_flare_jepa.experiments.provenance import verify_artifacts
from test_experiment_provenance import config

MODELS = [
    ('persistence', {}), ('training_mean', {}),
    ('trailing_mean', {'lookback_steps': 3}), ('drift', {'lookback_steps': 3}),
    ('ar1', {}), ('direct_ridge', {'lag_steps': 3, 'alpha': 1.}),
]


class UntrustedList(np.ndarray):
    def tolist(self):
        return np.zeros(self.shape).tolist()


def run_fixture(tmp_path, monkeypatch, name, parameters, change):
    module = importlib.import_module('solar_flare_jepa.experiments.runner')
    cfg = config()
    cfg['baselines'] = [dict(name=name, parameters=parameters)]
    cfg['seeds'] = [17]
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(cfg))
    provenance = dict(git_commit='bounded-fixture', git_branch='bounded-fixture',
                      source=dict(fingerprint='bounded-source', files=[]))
    monkeypatch.setattr(module, 'code_provenance', lambda root: deepcopy(provenance))
    monkeypatch.setattr(module, 'verify_source_identities', lambda root, files: None)
    make = module.make_baseline

    def changed_model(model_name, model_parameters):
        model = make(model_name, model_parameters)
        if model_name == name:
            predict = model.predict

            def changed_prediction(context, grid):
                return change(predict(context, grid))

            model.predict = changed_prediction
        return model

    monkeypatch.setattr(module, 'make_baseline', changed_model)
    output = module.run_experiment(path, tmp_path)
    verify_artifacts(output)
    return {filename: json.loads((output / f'{filename}.json').read_text())
            for filename in ('result', 'predictions', 'metrics', 'failures')}


@pytest.mark.parametrize('name,parameters', MODELS)
def test_all_baselines_publish_values_used_by_metric_logic(tmp_path, monkeypatch, name, parameters):
    def owner(prediction):
        prediction = deepcopy(prediction)
        object.__setattr__(prediction, 'values', np.array(prediction.values).view(UntrustedList))
        return prediction

    artifacts = run_fixture(tmp_path, monkeypatch, name, parameters, owner)
    assert artifacts['result']['status'] == 'complete'
    assert artifacts['failures'] == []
    for prediction in artifacts['predictions']:
        if prediction['model'] != name:
            continue
        score = next(record['metrics'] for record in artifacts['metrics']
                     if record['model'] == name and record['partition'] == prediction['partition'])
        values = np.array(prediction['values'])
        targets = np.array(prediction['targets'])
        mask = np.array(prediction['target_mask'])
        assert np.any(values != 0.)
        for k, target in enumerate(prediction['target_names']):
            mae = float(np.abs(values[:, :, k] - targets[:, :, k])[mask[:, :, k]].mean())
            assert score['by_target'][target]['mae']['value'] == pytest.approx(mae)


@pytest.mark.parametrize('malformed', [
    'none', 'array', 'missing-fields', 'shape', 'grid',
    'misaligned-grid', 'dataset', 'origins', 'units', 'model-id',
])
def test_malformed_model_output_becomes_explicit_failure_before_publication(
        tmp_path, monkeypatch, malformed):
    def damage(prediction):
        if malformed == 'none':
            return None
        if malformed == 'array':
            return np.array(prediction.values)
        if malformed == 'missing-fields':
            return ForecastPrediction.__new__(ForecastPrediction)
        if malformed == 'misaligned-grid':
            grid = prediction.grid
            offset = grid.spec.cadence_ns
            return replace(prediction, grid=replace(grid, starts_ns=grid.starts_ns + offset,
                ends_ns=grid.ends_ns + offset, issue_times_ns=grid.issue_times_ns + offset))
        if malformed == 'dataset':
            return replace(prediction, grid=replace(prediction.grid, dataset_fingerprint='other-dataset'))
        if malformed == 'origins':
            return replace(prediction, grid=replace(prediction.grid,
                origin_ids=tuple('other:' + value for value in prediction.grid.origin_ids)))
        if malformed == 'units':
            spec = replace(prediction.grid.spec, target_units=('other-unit', 'other-unit'))
            return replace(prediction, grid=replace(prediction.grid, spec=spec))
        if malformed == 'model-id':
            return replace(prediction, model_id='other-model')
        prediction = deepcopy(prediction)
        if malformed == 'shape':
            prediction.values.resize((1, 1, 2), refcheck=False)
        else:
            prediction.grid.starts_ns[0, 0] += 1
        return prediction

    artifacts = run_fixture(tmp_path, monkeypatch, 'training_mean', {}, damage)
    assert artifacts['result']['status'] == 'failed'
    assert artifacts['result']['successful_model_partition_scores'] == 0
    assert artifacts['result']['attempted_model_partition_scores'] == 3
    assert len(artifacts['failures']) == 3
    for failure in artifacts['failures']:
        assert failure['stage'] == 'predict'
        assert failure['error_type'] == 'ValueError'
        assert failure['attempted_origin_ids']
        assert failure['common_target_valid_count'] > 0
    for record in artifacts['predictions']:
        if record['model'] == 'training_mean':
            assert record['status'] == 'failed'
            assert record['values'] is None
    assert all(record['status'] == 'failed' and record['metrics'] is None
               for record in artifacts['metrics'])


def test_supplied_quantiles_are_published_with_the_scored_levels(tmp_path, monkeypatch):
    def supplied(prediction):
        return replace(prediction, quantile_levels=(.25, .75),
                       quantiles=np.stack((prediction.values - .5, prediction.values + .5), axis=-1))

    artifacts = run_fixture(tmp_path, monkeypatch, 'training_mean', {}, supplied)
    assert artifacts['result']['status'] == 'complete'
    for prediction in artifacts['predictions']:
        if prediction['model'] != 'training_mean':
            continue
        quantiles = np.array(prediction['quantiles'])
        observed = np.array(prediction['targets'])
        mask = np.array(prediction['target_mask'])
        assert quantiles.shape == observed.shape + (2,)
        score = next(record['metrics'] for record in artifacts['metrics']
                     if record['model'] == 'training_mean' and record['partition'] == prediction['partition'])
        residual = observed[..., None] - quantiles
        levels = np.array(prediction['quantile_levels'])
        losses = np.maximum(levels * residual, (levels - 1) * residual)
        for k, target in enumerate(prediction['target_names']):
            for q in range(2):
                oracle = losses[:, :, k, q][mask[:, :, k]].mean()
                assert score['by_target'][target]['pinball'][q]['value'] == pytest.approx(oracle)
