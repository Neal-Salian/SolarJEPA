"""Model-side interface adapters: EvaluationIdentity field mapping and budget summaries."""
import importlib

import pytest

torch = pytest.importorskip('torch')

from test_jepa import fixture, tiny  # noqa: E402
from solar_flare_jepa.experiments import v2_interfaces as interfaces  # noqa: E402

DECLARED = dict(experiment_id='v2-dev', code_fingerprint='c' * 64, data_provenance_fingerprint='d' * 64,
                split_fingerprint='s' * 64, protocol_fingerprint='p' * 64)


def fitted(seed):
    controlled = importlib.import_module('solar_flare_jepa.training.controlled')
    windows = fixture()
    loss = 'dex_pinball_equal_channel_v2'
    schedule = controlled.TrainingSchedule(arm='supervised', pretrain_epochs=0, warmup_epochs=0,
                                           downstream_epochs=2, early_stopping_patience=None,
                                           train_loss=loss, selection_metric=loss)
    return controlled.fit_controlled(windows['train'].training_slice, windows['validation'],
                                     controlled.ControlledConfig(tiny(seed=seed), schedule))


def test_identity_fields_match_the_independent_evaluation_schema_and_pair_seeds():
    one, two = fitted(3).record, fitted(4).record
    a, b = (interfaces.evaluation_identity_fields(r, **DECLARED) for r in (one, two))
    assert tuple(sorted(a)) == tuple(sorted(interfaces.EVALUATION_IDENTITY_FIELDS))
    assert a['seed'] == 3 and b['seed'] == 4 and a['selection_partition'] == 'validation'
    assert a['config_fingerprint'] == b['config_fingerprint'] == one['recipe_fingerprint']
    assert a['model_version'] == b['model_version'] and a['training_fingerprint'] == b['training_fingerprint']


def test_identity_fields_refuse_missing_declarations_or_non_validation_selection():
    record = fitted(3).record
    for name in DECLARED:
        with pytest.raises(ValueError):
            interfaces.evaluation_identity_fields(record, **dict(DECLARED, **{name: '  '}))
    record['selection']['partition'] = 'test'
    with pytest.raises(ValueError, match='validation-only'):
        interfaces.evaluation_identity_fields(record, **DECLARED)
    with pytest.raises(ValueError):
        interfaces.evaluation_identity_fields({'seed': 1}, **DECLARED)


def test_budget_summary_is_flat_and_versioned():
    summary = interfaces.training_budget_summary(fitted(3).record)
    assert summary['interface_version'] == interfaces.INTERFACE_VERSION
    assert [p['phase'] for p in summary['phases']] == ['downstream']
    assert summary['totals']['optimizer_steps'] == summary['phases'][0]['optimizer_steps'] > 0
    with pytest.raises(ValueError):
        interfaces.training_budget_summary({'model_id': 'x'})
