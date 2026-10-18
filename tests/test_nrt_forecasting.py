"""The NRT boundary rejects live inputs and replays only pinned science inputs."""
from importlib import import_module, util
import builtins
import io
import json
from pathlib import Path
import shutil
import socket

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ISSUE = '2024-08-01T02:00:00Z'
EXECUTED = '2026-10-18T00:00:00Z'


def service():
    assert util.find_spec('solar_flare_jepa.forecasting.nrt') is not None, 'NRT inference boundary missing'
    return import_module('solar_flare_jepa.forecasting.nrt')


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError('Replay attempted network access')
    monkeypatch.setattr(socket.socket, 'connect', reject)
    monkeypatch.setattr(socket, 'getaddrinfo', reject)


@pytest.fixture(scope='module')
def artifacts():
    historical = import_module('solar_flare_jepa.dashboard.prediction')
    registry = historical.load_prediction_registry(ROOT)
    needed = ('jepa_checkpoint', 'supervised_checkpoint', 'replay_archive', 'replay_summary')
    manifest = json.loads((ROOT / registry['artifacts']['august_manifest']['path']).read_text())
    paths = [ROOT / registry['artifacts'][key]['path'] for key in needed]
    paths.extend(ROOT / row['path'] for row in manifest['files'])
    if any(not path.is_file() for path in paths):
        pytest.skip('Pinned local GOES-16 science observations/checkpoints/archive are required for real replay')
    historical.verify_artifacts(ROOT, registry, needed)
    return historical, registry, manifest


@pytest.mark.parametrize('options', [{}, {'allow_unvalidated': True}, {'context': object(), 'checkpoint': 'supplied.pt'}])
def test_live_snapshot_never_imports_or_loads_model_even_with_override(options, monkeypatch):
    nrt = service()
    original = builtins.__import__
    def no_model(name, *args, **kwargs):
        if name.startswith(('torch', 'solar_flare_jepa.training', 'solar_flare_jepa.dashboard.prediction')):
            raise AssertionError('Live snapshot reached model or historical inference code')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', no_model)
    with pytest.raises(nrt.NrtForecastUnavailable, match='scientific contract unavailable'):
        nrt.forecast_snapshot(object(), **options)


def test_saved_replay_matches_independent_archived_context_predictions_and_timing(artifacts):
    historical, registry, _ = artifacts
    report = service().replay_v1(ROOT, ISSUE, executed_utc=EXECUTED, include_supervised=True)
    assert report['status'] == 'PASS'
    assert report['mode'] == 'historical_science_replay'
    assert report['operationally_validated'] is False
    assert report['timing'] == {
        'observation_start_utc': '2024-08-01T00:00:00+00:00',
        'observation_end_utc': '2024-08-01T02:00:00+00:00',
        'publication_utc': None,
        'forecast_origin_utc': '2024-08-01T02:00:00+00:00',
        'horizon_minutes': 30,
        'forecast_end_utc': '2024-08-01T02:30:00+00:00',
        'execution_utc': '2026-10-18T00:00:00+00:00',
    }
    assert report['context']['feature_names'] == ['xrsa_flux', 'xrsb_flux']
    assert report['context']['feature_units'] == ['W/m2', 'W/m2']
    assert report['future_grid']['starts_utc'][0] == '2024-08-01T02:00:00+00:00'
    assert report['future_grid']['ends_utc'][-1] == '2024-08-01T02:30:00+00:00'
    with np.load(ROOT / registry['artifacts']['replay_archive']['path'], allow_pickle=False) as archive:
        indices = np.flatnonzero(archive['issue_times_ns'] == pd.Timestamp(ISSUE).value)
        assert indices.tolist() == [0]
        np.testing.assert_array_equal(report['context']['values'], archive['context'][0])
        np.testing.assert_array_equal(report['context']['mask'], archive['context_mask'][0])
        predictions = {row['model_id']: row for row in report['predictions']}
        assert set(predictions) == {'jepa_finetune', 'supervised_transformer'}
        for model_id, archived_id in [('jepa_finetune', 'jepa_finetune_seed17'),
                                      ('supervised_transformer', 'supervised_seed17')]:
            model_index = np.flatnonzero(archive['model_ids'] == archived_id).item()
            output = predictions[model_id]
            assert output['quantile_levels'] == [.05, .25, .5, .75, .95]
            assert output['point_interpretation'] == 'inverse_transformed_point'
            np.testing.assert_allclose(output['values'], archive['point_' + str(model_index)][0], rtol=1e-6, atol=1e-15)
            np.testing.assert_allclose(output['quantiles'], archive['quantiles_' + str(model_index)][0], rtol=1e-6, atol=1e-15)
    keys = historical.SOURCE_KEYS + ('jepa_checkpoint', 'supervised_checkpoint')
    assert report['provenance'] == {
        'experiment_id': registry['experiment_id'], 'executed_commit': registry['executed_commit'],
        'seed': 17, 'normalization_fingerprint': registry['normalization_fingerprint'],
        'spec_fingerprint': registry['spec_fingerprint'], 'dataset_fingerprint': registry['dataset_fingerprint'],
        'artifacts': {key: registry['artifacts'][key] for key in keys},
    }
    json.dumps(report, allow_nan=False)


def test_replay_never_reads_saved_predictions_and_ignores_future_actuals(artifacts, monkeypatch):
    historical, registry, _ = artifacts
    observations = historical.load_august_observations(ROOT, registry)
    original = service().replay_v1(ROOT, ISSUE, executed_utc=EXECUTED)
    observations.loc[observations.index >= pd.Timestamp(ISSUE), ['xrsa_flux', 'xrsb_flux']] = np.nan
    monkeypatch.setattr(historical, 'load_august_observations', lambda *args: observations)
    def guard(open_file):
        def checked(path, *args, **kwargs):
            if isinstance(path, (str, bytes, Path)):
                assert not any(x in str(path) for x in ('test_predictions.npz', 'summary.json', 'supervised_seed17.pt'))
            return open_file(path, *args, **kwargs)
        return checked
    monkeypatch.setattr(builtins, 'open', guard(builtins.open))
    monkeypatch.setattr(io, 'open', guard(io.open))
    changed = service().replay_v1(ROOT, ISSUE, executed_utc=EXECUTED)
    assert len(changed['predictions']) == 1
    assert original['predictions'] == changed['predictions']
    assert original['context'] == changed['context']
    assert changed['quality']['future']['xrsa'] == {'valid': 0, 'masked': 30, 'missing': 0}


def test_replay_preserves_real_incomplete_context_rejection(artifacts):
    with pytest.raises(ValueError, match='120 context bins'):
        service().replay_v1(ROOT, '2024-08-04T09:15Z', executed_utc=EXECUTED)


def isolated_replay_root(tmp_path, artifacts):
    historical, registry, manifest = artifacts
    paths = [historical.REGISTRY_PATH]
    paths.extend(registry['artifacts'][key]['path'] for key in historical.SOURCE_KEYS + ('jepa_checkpoint',))
    paths.extend(row['path'] for row in manifest['files'])
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    return tmp_path


@pytest.mark.parametrize('defect', ['missing_checkpoint', 'corrupt_checkpoint', 'corrupt_code', 'corrupt_native', 'spoof_registry'])
def test_replay_refuses_missing_or_changed_pinned_artifact_identity(tmp_path, artifacts, defect):
    historical, registry, manifest = artifacts
    root = isolated_replay_root(tmp_path, artifacts)
    if defect in ('missing_checkpoint', 'corrupt_checkpoint'):
        path = root / registry['artifacts']['jepa_checkpoint']['path']
        if defect == 'missing_checkpoint':
            path.unlink()
        else:
            path.write_bytes(b'changed checkpoint')
    elif defect == 'corrupt_code':
        (root / registry['artifacts']['goes_adapter']['path']).write_text('changed source')
    elif defect == 'corrupt_native':
        (root / manifest['files'][0]['path']).write_bytes(b'arbitrary supplied science data')
    else:
        path = root / historical.REGISTRY_PATH
        content = json.loads(path.read_text())
        content['dataset_fingerprint'] = 'caller asserted identity'
        path.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        service().replay_v1(root, ISSUE, executed_utc=EXECUTED)


@pytest.mark.parametrize('executed', ['2026-10-18T00:00:00', '2026-10-18T00:00+01:00', 'NaT', '2024-08-01T01:59Z'])
def test_replay_refuses_unknown_non_utc_or_pre_origin_execution_time(executed):
    with pytest.raises(ValueError, match='execution'):
        service().replay_v1(ROOT, ISSUE, executed_utc=executed)


def test_replay_has_no_supplied_context_or_file_path_override():
    with pytest.raises(TypeError):
        service().replay_v1(ROOT, ISSUE, context=object())
    with pytest.raises(TypeError):
        service().replay_v1(ROOT, ISSUE, science_file='arbitrary.nc')
