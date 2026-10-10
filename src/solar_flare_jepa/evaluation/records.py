"""Canonical independent-evaluation records and declared fitting checks.

No data is acquired or discovered here. Identities describe caller declarations;
they cannot authenticate unseen training history or dishonest feature lineage.
"""
from dataclasses import asdict, dataclass, fields
import json

import numpy as np

from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
    TrainingSlice, _canonical_fields, _category, _string, _time_scalar,
    canonical_json, fingerprint_payload, logical_array, validate_alignment,
)
from solar_flare_jepa.training.normalization import Normalization
from .trajectory import _forecast_snapshot, _grid_snapshot, prediction_snapshot


def _exact_keys(record, keys, label):
    if type(record) is not dict or set(record) != set(keys):
        raise ValueError(f'Malformed {label} schema')


def _version(value):
    if type(value) is not int or value != 1:
        raise ValueError('Unsupported evaluation schema version')


def _numeric_json_cells(value, *, allow_null=False):
    """Reject coercible strings/booleans before NumPy float conversion."""
    if type(value) is not list:
        raise ValueError('Serialized numerical arrays require JSON lists')
    raw = np.asarray(value, dtype=object)
    if any(type(cell) not in (int, float) and not (allow_null and cell is None)
           for cell in raw.flat):
        raise ValueError('Serialized numerical cells must be JSON numbers, excluding booleans')
    return raw


def _empty_array(value, shape, dtype):
    if type(value) is not list or value:
        raise ValueError('Empty-origin serialized arrays must be empty JSON lists')
    return np.empty(shape, dtype=dtype)


def _identity_snapshot(value):
    if not isinstance(value, EvaluationIdentity):
        raise ValueError('Evaluation requires an explicit EvaluationIdentity')
    return EvaluationIdentity(**_canonical_fields(value, EvaluationIdentity))


def _targets_snapshot(value):
    if not isinstance(value, ForecastTargets):
        raise ValueError('Evaluation requires explicit ForecastTargets')
    value = _forecast_snapshot(value, ForecastTargets)
    # Unscored payload is not scientific support and must not leak into records.
    return ForecastTargets(np.where(value.mask, value.values, np.nan), value.mask, value.grid)


def _context_snapshot(value):
    if not isinstance(value, ForecastContext) or not isinstance(value.spec, ForecastSpec):
        raise ValueError('Evaluation requires an explicit ForecastContext and spec')
    declarations = _canonical_fields(value, ForecastContext)
    declarations['spec'] = ForecastSpec(**_canonical_fields(value.spec, ForecastSpec))
    return ForecastContext(**declarations)


def _grid_content(grid):
    return dict(spec=grid.spec.as_dict(), dataset_fingerprint=grid.dataset_fingerprint,
        origin_ids=list(grid.origin_ids), issue_times_ns=logical_array(grid.issue_times_ns),
        starts_ns=logical_array(grid.starts_ns), ends_ns=logical_array(grid.ends_ns))


def _support_content(targets):
    return dict(schema_version=1, grid=_grid_content(targets.grid),
        values=logical_array(targets.values), mask=logical_array(targets.mask))


def support_fingerprint(targets):
    """Identity of canonical observed targets/masks and their exact future grid.

    Unscored values are canonical NaNs/nulls; changing predictions or unscored
    payload does not change support. No target value is read from a file.
    """
    return fingerprint_payload(_support_content(_targets_snapshot(targets)))


@dataclass(frozen=True)
class EvaluationIdentity:
    experiment_id: str
    model_version: str
    seed: int
    code_fingerprint: str
    config_fingerprint: str
    data_provenance_fingerprint: str
    split_fingerprint: str
    training_fingerprint: str
    normalization_fingerprint: str
    protocol_fingerprint: str
    selection_partition: str = 'validation'
    schema_version: int = 1

    def __post_init__(self):
        _version(self.schema_version)
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError('Evaluation seed must be a nonnegative uint32 integer')
        for field in fields(EvaluationIdentity):
            if field.name not in ('schema_version', 'seed', 'selection_partition'):
                value = _string(getattr(self, field.name), field.name)
                if not value.strip():
                    raise ValueError('Evaluation identities cannot be whitespace')
                object.__setattr__(self, field.name, value)
        object.__setattr__(self, 'selection_partition',
                           _category(self.selection_partition, ('validation',), 'selection partition'))

    def as_dict(self):
        return asdict(_identity_snapshot(self))

    @classmethod
    def from_dict(cls, record):
        _exact_keys(record, (field.name for field in fields(EvaluationIdentity)), 'evaluation identity')
        canonical_json(record)
        return cls(**record)

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())


@dataclass(frozen=True, eq=False)
class EvaluationRecord:
    identity: EvaluationIdentity
    targets: ForecastTargets
    prediction: ForecastPrediction

    def __post_init__(self):
        object.__setattr__(self, 'identity', _identity_snapshot(self.identity))
        object.__setattr__(self, 'targets', _targets_snapshot(self.targets))
        object.__setattr__(self, 'prediction', prediction_snapshot(self.prediction))
        validate_alignment(self.targets.grid, self.prediction.grid)

    @property
    def support_fingerprint(self):
        return support_fingerprint(self.targets)

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())

    def as_dict(self):
        # Revalidate at every publication boundary, including deserialized copies.
        snapshot = EvaluationRecord(self.identity, self.targets, self.prediction)
        prediction, targets = snapshot.prediction, snapshot.targets
        return dict(schema_version=1, identity=snapshot.identity.as_dict(),
            grid=_grid_content(targets.grid),
            targets=dict(values=logical_array(targets.values), mask=logical_array(targets.mask)),
            prediction=dict(values=logical_array(prediction.values), model_id=prediction.model_id,
                point_interpretation=prediction.point_interpretation,
                quantile_levels=list(prediction.quantile_levels),
                quantiles=None if prediction.quantiles is None else logical_array(prediction.quantiles)),
            support_fingerprint=fingerprint_payload(_support_content(targets)))

    def to_json(self):
        return canonical_json(self.as_dict())

    @classmethod
    def from_dict(cls, record):
        _exact_keys(record, ('schema_version', 'identity', 'grid', 'targets',
                             'prediction', 'support_fingerprint'), 'evaluation record')
        _version(record['schema_version'])
        try:
            # Detach genuine finite JSON before validating nested declarations.
            record = json.loads(canonical_json(record))
            identity = EvaluationIdentity.from_dict(record['identity'])
            grid = record['grid']
            _exact_keys(grid, ('spec', 'dataset_fingerprint', 'origin_ids', 'issue_times_ns',
                               'starts_ns', 'ends_ns'), 'future grid')
            _exact_keys(grid['spec'], (field.name for field in fields(ForecastSpec)), 'forecast spec')
            spec = ForecastSpec(**grid['spec'])
            empty = grid['origin_ids'] == []
            if empty:
                grid = dict(grid,
                    starts_ns=_empty_array(grid['starts_ns'], (0, spec.horizon_steps), np.int64),
                    ends_ns=_empty_array(grid['ends_ns'], (0, spec.horizon_steps), np.int64),
                    issue_times_ns=_empty_array(grid['issue_times_ns'], (0,), np.int64))
            grid = FutureGrid(**dict(grid, spec=spec))
            targets = record['targets']
            _exact_keys(targets, ('values', 'mask'), 'targets')
            mask = np.asarray(targets['mask'])
            raw = _numeric_json_cells(targets['values'], allow_null=True)
            shape = (0, spec.horizon_steps, len(spec.target_names))
            if empty:
                mask = _empty_array(targets['mask'], shape, bool)
                raw = _empty_array(targets['values'], shape, object)
            if mask.dtype.kind != 'b' or raw.shape != mask.shape:
                raise ValueError('Serialized targets require boolean masks of matching shape')
            null = np.equal(raw, None)
            if not np.array_equal(null, ~mask):
                raise ValueError('Serialized observations must be null exactly on masked cells')
            targets = ForecastTargets(np.asarray(raw, dtype=float), mask, grid)
            prediction = record['prediction']
            _exact_keys(prediction, ('values', 'model_id', 'point_interpretation',
                                    'quantile_levels', 'quantiles'), 'prediction')
            _numeric_json_cells(prediction['values'])
            _numeric_json_cells(prediction['quantile_levels'])
            if prediction['quantiles'] is not None:
                _numeric_json_cells(prediction['quantiles'])
            if empty:
                prediction['values'] = _empty_array(prediction['values'], shape, float)
                if prediction['quantiles'] is not None:
                    prediction['quantiles'] = _empty_array(prediction['quantiles'],
                        shape + (len(prediction['quantile_levels']),), float)
            result = cls(identity, targets, ForecastPrediction(**prediction, grid=grid))
            if record['support_fingerprint'] != result.support_fingerprint:
                raise ValueError('Evaluation support identity differs from actual content')
            return result
        except (TypeError, AttributeError, OverflowError) as error:
            raise ValueError('Malformed evaluation record content') from error

    @classmethod
    def from_json(cls, content):
        def pairs(entries):
            result = {}
            for key, value in entries:
                if key in result:
                    raise ValueError('Duplicate evaluation JSON key')
                result[key] = value
            return result
        def nonfinite(value):
            raise ValueError('Nonfinite evaluation JSON literal')
        if type(content) is not str:
            raise ValueError('Evaluation JSON must be explicit text')
        try:
            return cls.from_dict(json.loads(content, object_pairs_hook=pairs, parse_constant=nonfinite))
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError('Malformed evaluation JSON') from error


def validate_fitting_artifacts(training, normalization, evaluation_context, evaluation_targets,
                               *, identity=None, embargo_ns=0):
    """Check declared support and recomputed train-only normalizer consistency.

    Full evaluation context/lookback and target/maturity envelopes must occur
    after raw training support plus an optional explicit minimum embargo. This
    validates supplied artifacts, not authentication of prior data access. Equal
    external statistics and dishonest feature lineage cannot be inferred here.
    """
    embargo_ns = _time_scalar(embargo_ns)
    if embargo_ns < 0:
        raise ValueError('Temporal embargo must be nonnegative')
    if not isinstance(training, TrainingSlice) or not isinstance(normalization, Normalization):
        raise ValueError('Fitting checks require TrainingSlice and Normalization')
    training = TrainingSlice(**_canonical_fields(training, TrainingSlice))
    normalization = Normalization(**_canonical_fields(normalization, Normalization))
    expected = Normalization.fit(training)
    if normalization.as_dict() != expected.as_dict():
        raise ValueError('Supplied normalization differs from unique raw training statistics/identity')
    context = _context_snapshot(evaluation_context)
    targets = _targets_snapshot(evaluation_targets)
    validate_alignment(context, targets.grid)
    if (context.spec.fingerprint != training.spec.fingerprint
            or context.dataset_fingerprint != training.context.dataset_fingerprint):
        raise ValueError('Evaluation and training spec/dataset identities differ')
    if not len(context.origin_ids):
        raise ValueError('Evaluation support is empty')
    earliest = min(int(row[0]) - context.spec.feature_lookback_steps * context.spec.cadence_ns
                   for row in context.starts_ns)
    if earliest < training.partition_end_ns:
        raise ValueError('Evaluation support overlaps raw training support')
    if earliest - training.partition_end_ns < embargo_ns:
        raise ValueError('Evaluation support gap is smaller than declared embargo')
    latest = max(int(row[-1]) + context.spec.label_maturity_steps * context.spec.cadence_ns
                 for row in targets.grid.ends_ns)
    _time_scalar(earliest)
    _time_scalar(latest)
    if identity is not None:
        identity = _identity_snapshot(identity)
        if (identity.training_fingerprint != training.fingerprint
                or identity.normalization_fingerprint != expected.fingerprint):
            raise ValueError('Declared fitting identities differ from actual fitting artifacts')
    return dict(schema_version=1, status='VALIDATED_DECLARED_FITTING_ARTIFACTS',
        training_fingerprint=training.fingerprint, normalization_fingerprint=expected.fingerprint,
        raw_support_fingerprint=expected.raw_support_fingerprint,
        support_fingerprint=fingerprint_payload(_support_content(targets)),
        evaluation_support_start_ns=earliest, evaluation_support_end_ns=latest,
        training_partition_end_ns=training.partition_end_ns, embargo_ns=embargo_ns,
        limits='Declared support/statistics consistency; no authentication of training history or feature lineage')
