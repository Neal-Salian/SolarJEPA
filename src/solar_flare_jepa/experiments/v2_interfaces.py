"""Model-side adapters for the proposed V2 cross-contributor interfaces.

No new schema is defined for forecasts or evaluation: forecasts are P1
``ForecastPrediction`` objects, and evaluation identities use the field names of
``evaluation.records.EvaluationIdentity`` on the independent-validation branch
(``origin/feat/v2-m0-m1-validation-foundation``, inspected at ``fd7203b``). That
class is integrated in M4B. This module continues to return plain mappings for
backward compatibility; the development adapter constructs canonical records.
Adoption of the mapping for an approved experiment remains a separate decision.

Fields the model owner cannot know (code, data provenance, split and protocol
identities, experiment id) are caller declarations and are never invented here.
"""
from solar_flare_jepa.forecasting.contracts import _string

INTERFACE_VERSION = 'solarjepa-v2-model-interface-1'
EVALUATION_IDENTITY_FIELDS = (
    'experiment_id', 'model_version', 'seed', 'code_fingerprint', 'config_fingerprint',
    'data_provenance_fingerprint', 'split_fingerprint', 'training_fingerprint', 'normalization_fingerprint',
    'protocol_fingerprint', 'selection_partition', 'schema_version')
_RECORD_KEYS = ('model_kind', 'model_id', 'recipe_fingerprint', 'seed', 'training_fingerprint',
                'normalization_fingerprint', 'selection')


def evaluation_identity_fields(record, *, experiment_id, code_fingerprint, data_provenance_fingerprint,
                               split_fingerprint, protocol_fingerprint):
    """Map a V2 model record to ``EvaluationIdentity`` keyword arguments.

    ``config_fingerprint`` is the seed-free recipe fingerprint so one paired
    cohort shares one configuration identity; ``model_version`` names the model
    kind, model id and recipe. Selection must have used the validation partition.
    """
    if not isinstance(record, dict) or any(key not in record for key in _RECORD_KEYS):
        raise ValueError('A complete V2 model record is required')
    if record['selection'].get('partition') != 'validation':
        raise ValueError('V2 evaluation identities require validation-only selection')
    seed = record['seed']
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('Model record seed must be a uint32 integer')
    declared = dict(experiment_id=experiment_id, code_fingerprint=code_fingerprint,
                    data_provenance_fingerprint=data_provenance_fingerprint,
                    split_fingerprint=split_fingerprint, protocol_fingerprint=protocol_fingerprint)
    for name, value in declared.items():
        if not _string(value, name).strip():
            raise ValueError(f'{name} cannot be whitespace')
    return dict(declared, seed=seed,
                model_version=f"{record['model_kind']}:{record['model_id']}:{record['recipe_fingerprint']}",
                config_fingerprint=record['recipe_fingerprint'],
                training_fingerprint=record['training_fingerprint'],
                normalization_fingerprint=record['normalization_fingerprint'],
                selection_partition='validation', schema_version=1)


def training_budget_summary(record):
    """Flat, versioned training-budget metadata for statistical/compute analysis."""
    budget = record.get('budget') if isinstance(record, dict) else None
    if not isinstance(budget, dict) or not isinstance(budget.get('phases'), list) or 'totals' not in budget:
        raise ValueError('Model record has no V2 budget')
    phases = [{key: phase.get(key) for key in ('phase', 'epochs_planned', 'epochs_executed', 'optimizer_steps',
                                               'examples_seen', 'wall_seconds')} for phase in budget['phases']]
    return dict(interface_version=INTERFACE_VERSION, model_id=record['model_id'], seed=record['seed'],
                recipe_fingerprint=record['recipe_fingerprint'], phases=phases, totals=budget['totals'],
                train_windows=record.get('train_windows'), wall_seconds=record.get('wall_seconds'),
                process_peak_rss_bytes=record.get('environment', {}).get('process_peak_rss_bytes'),
                notes='step counts are not FLOP counts; RSS is a process high-water mark')
