"""Adversarial evidence catalog with explicit observable-metadata limits."""
import pytest

from solar_flare_jepa.evaluation.stress.contracts import contract_probes


def test_all_adversarial_and_boundary_probes_match_declared_outcomes():
    results = contract_probes()
    assert len(results) >= 35
    assert all(row['matched_expected'] for row in results)
    names = {r['case'] for r in results}
    assert {'overlapping_partitions', 'embargo_one_ns_short', 'target_crossing_boundary',
            'future_fitted_normalization', 'duplicate_origins', 'out_of_order_timestamps',
            'dataset_identity', 'wrong_horizon', 'invalid_support_metadata',
            'normalization_provenance', 'incorrect_fitting_range', 'prediction_target_identity',
            'exact_embargo_boundary', 'exact_target_boundary', 'common_missing_run',
            'secret_future_feature', 'standalone_failed_fit_label'} <= names
    assert {r['classification'] for r in results} >= {'DETECTED LEAKAGE', 'DETECTED CONTRACT VIOLATION',
                                                    'UNDETECTABLE FROM AVAILABLE METADATA', 'VALID BOUNDARY'}


def test_probe_catalog_is_deterministic_and_limits_do_not_claim_rejection():
    a, b = contract_probes(), contract_probes()
    assert a == b
    limits = [r for r in a if r['classification'] == 'UNDETECTABLE FROM AVAILABLE METADATA']
    assert len(limits) >= 4
    assert all(r['observed'] == 'accepted' for r in limits)
