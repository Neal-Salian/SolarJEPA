"""External configurations cannot request fitting or silently change label tasks."""
from pathlib import Path
from copy import deepcopy
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]


def validate(config):
    from solar_flare_jepa.data.external_validation import validate_external_config
    return validate_external_config(config)


def fixture():
    forecast=json.loads((ROOT/'configs/experiments/p2_goes_july2024.json').read_text())['forecast']
    return dict(schema_version=1,evaluation_id='external-fixed-fixture',
        goes_manifest='data/manifests/goes_external_january2025.json',
        catalog_manifest='data/manifests/flare_catalog_2025.json',forecast=forecast,
        catalog_interval=['2025-01-01T00:00:00Z','2026-01-01T00:00:00Z'],
        minimum_classes=['C1.0','M1.0','X1.0'],
        policy='external_evaluation_only_no_fitting_or_tuning')


def test_external_config_reuses_frozen_forecast_contract_with_distinct_sources():
    value=fixture()
    assert validate(value)==value
    assert validate(value) is not value


@pytest.mark.parametrize('change',[
    {'schema_version':True},{'policy':'tune_on_external'},{'minimum_classes':['M1.3']},
    {'minimum_classes':['M1.0','M1.0']},{'catalog_interval':['2025-01-01','2026-01-01']},
    {'catalog_interval':['2026-01-01T00:00:00Z','2025-01-01T00:00:00Z']},
    {'goes_manifest':'../raw.json'},{'catalog_manifest':'/tmp/catalog.json'},
    {'fit_statistics':True}
])
def test_config_fails_closed_on_unapproved_policy_or_ambiguous_source(change):
    value=fixture();value.update(change)
    with pytest.raises(ValueError):validate(value)


def test_external_retrospective_archive_cannot_assert_operational_availability():
    value=fixture();value['forecast']['availability_mode']='operational'
    with pytest.raises(ValueError):validate(value)


def test_malformed_nested_class_list_is_a_controlled_validation_error():
    value=fixture();value['minimum_classes']=[{'M1.0':True}]
    with pytest.raises(ValueError):validate(value)
