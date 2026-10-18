import importlib.util
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.events import diagnostics
from test_event_frozen import bundle, fingerprint  # complete pinned synthetic fixture

MIN = 60_000_000_000


def test_onset_peak_and_forecast_maximum_are_distinct():
    # This catches treating the future class-defining peak as horizon truth.
    row = diagnostics.trajectory_error(
        [2e-6, 3e-6], [3e-6, 4e-6, 4e-6], [3e-6, 5e-6, 8e-6],
        issue_ns=120*MIN, start_ns=122*MIN, peak_ns=125*MIN,
        threshold_W_m2=1e-5)
    assert row['onset_lead_seconds'] == 120
    assert row['onset_to_peak_seconds'] == 180
    assert row['catalog_peak_in_horizon'] is False
    assert row['predicted_max_first_bin_start_ns'] == 121*MIN
    assert row['observed_max_W_m2'] == 8e-6
    assert row['predicted_to_observed_max_ratio'] == 0.5
    assert row['predicted_threshold_exceedance'] is False
    assert row['observed_threshold_exceedance'] is False


@pytest.mark.parametrize('bad', [[True, 1e-6], [0., 1e-6], [float('nan'), 1e-6]])
def test_trajectory_rejects_nonphysical_or_boolean_flux(bad):
    with pytest.raises(ValueError):
        diagnostics.trajectory_error(bad, [1e-6]*2, [1e-6]*2,
            issue_ns=120*MIN, start_ns=121*MIN, peak_ns=122*MIN,
            threshold_W_m2=1e-5)


def test_pinned_diagnostics_keep_fixed_event_truth_and_all_models(bundle):
    config, roots, _, _ = bundle
    result = diagnostics.diagnose_frozen(config, roots)
    assert result['rule_selection_performed'] is False
    assert result['claim'] == 'exposed_period_error_diagnostics_only'
    assert result['classes']['M']['eligible_events'] == 2
    model = result['classes']['M']['models']['persistence']
    assert model['legacy_counts'] == dict(alarms=2, events=2, hits=2, false_alarms=0, misses=0)
    assert len(model['events']) == 2
    assert {r['status'] for r in model['events']} == {'hit'}
    assert model['events'][0]['opportunities'][0]['onset_lead_seconds'] == 600
    assert model['matched_events'][0]['lead_seconds'] == 600
    assert model['false_alarms_per_exposed_day'] == 0
    assert model['warning_time_fraction'] == 0.5
    assert model['paired_persistence_comparison']['both_hit_event_ids'] == ['cat:e0', 'cat:e2']
    assert model['paired_persistence_comparison']['model_only_hit_event_ids'] == []
    assert model['threshold_sensitivity'][0]['factor'] == 0.5
    # Raising the decision threshold cannot silently raise the observed event class.
    last = model['threshold_sensitivity'][-1]
    assert last['factor'] == 2.0
    assert last['counts']['events'] == 2
    assert last['counts']['hits'] == 2  # inclusive threshold 2e-5
    assert len(model['lead_sensitivity']) == 5
    assert result['event_uncertainty']['status'] == 'NOT_ESTIMATED'


def test_changed_pinned_bytes_fail_before_diagnostics(bundle):
    config, roots, _, _ = bundle
    (roots['bundle']/'predictions.json').write_text('{}')
    with pytest.raises(ValueError, match='identity'):
        diagnostics.diagnose_frozen(config, roots)


def test_miss_and_flux_false_alarm_keep_their_actual_error_evidence(bundle):
    config, roots, docs, write = bundle
    values = docs['predictions']['persistence']['values']
    values[0] = np.full((30, 2), 1e-6).tolist()  # miss the first event
    values[1] = np.full((30, 2), 2e-5).tolist()  # actual below-threshold future
    docs['summary']['prediction_content_fingerprint'] = fingerprint(docs['predictions'])
    write('predictions', docs['predictions'])
    write('summary', docs['summary'])
    model = diagnostics.diagnose_frozen(config, roots)['classes']['M']['models']['persistence']
    assert model['legacy_counts'] == dict(alarms=2, events=2, hits=1, false_alarms=1, misses=1)
    assert model['events'][0]['status'] == 'miss'
    assert model['events'][0]['opportunities'][0]['predicted_max_W_m2'] == 1e-6
    assert model['false_alarms'][0]['observed_threshold_exceedance'] is False
    assert model['false_alarms'][0]['background_already_above_threshold'] is False
    assert model['false_alarms'][0]['known_catalog_evolution_ids'] == []


def test_diagnostic_cli_refuses_overwrite_and_emits_json(bundle, tmp_path, capsys):
    config, roots, _, _ = bundle
    import json
    config_path = tmp_path/'config.json'
    # CLI accepts the same two logical root names as the production config.
    for identity in config['resources'].values():
        identity['root'] = 'forecasts'
    config_path.write_text(json.dumps(config))
    path = Path(__file__).resolve().parents[1]/'scripts/diagnose_flare_events.py'
    spec = importlib.util.spec_from_file_location('diagnose_cli', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = path.parents[1]/'results'/('test-diagnostics-'+tmp_path.name+'.json')
    args = ['--config', str(config_path), '--forecast-root', str(roots['bundle']),
            '--label-root', str(roots['bundle']), '--output', str(output)]
    try:
        module.main(args)
        document = json.loads(output.read_text())
        assert document['classes']['M']['eligible_events'] == 2
        assert set(document['executed_source_sha256']) >= {'diagnostics.py', 'frozen.py'}
        before = output.read_bytes()
        with pytest.raises(SystemExit):
            module.main(args)
        assert output.read_bytes() == before
    finally:
        output.unlink(missing_ok=True)
