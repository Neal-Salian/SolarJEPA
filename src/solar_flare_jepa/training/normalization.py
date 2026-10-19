"""Masked, dimensioned transforms fitted on unique raw training support only."""
from dataclasses import dataclass

import numpy as np

from solar_flare_jepa.forecasting.contracts import (
    ForecastSpec, TrainingSlice, _canonical_fields, canonical_json,
    fingerprint_payload, logical_array,
)


def training_snapshot(training):
    if not isinstance(training, TrainingSlice):
        raise ValueError('Training requires an explicit TrainingSlice')
    return TrainingSlice(**_canonical_fields(training, TrainingSlice))


def _finite(value, label):
    if not np.isfinite(value).all():
        raise ValueError(f'Nonfinite {label}')
    return value


def _transformed(values, mask, spec, kind):
    values, mask = np.asarray(values, float), np.asarray(mask)
    count = len(getattr(spec, f'{kind}_names'))
    if mask.dtype.kind != 'b' or values.shape != mask.shape or values.shape[-1] != count:
        raise ValueError('Normalization values/masks/channel shape differs')
    refs = getattr(spec, f'{kind}_reference')
    result = np.zeros_like(values)
    for channel in range(count):
        selected = values[..., channel][mask[..., channel]]
        _finite(selected, 'valid normalization inputs')
        if spec.transform == 'log10':
            if (selected <= 0).any():
                raise ValueError('Log transform requires positive valid observations')
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                selected = np.log10(selected / refs[channel])
        result[..., channel][mask[..., channel]] = _finite(selected, 'dimensioned transform')
    return result


@dataclass(frozen=True)
class Normalization:
    spec: ForecastSpec
    feature_mean: tuple[float, ...]
    feature_scale: tuple[float, ...]
    target_mean: tuple[float, ...]
    target_scale: tuple[float, ...]
    feature_counts: tuple[int, ...]
    target_counts: tuple[int, ...]
    raw_support_fingerprint: str

    def __post_init__(self):
        if not isinstance(self.spec, ForecastSpec):
            raise ValueError('Normalization requires an explicit forecast spec')
        object.__setattr__(self, 'spec', ForecastSpec(**_canonical_fields(self.spec, ForecastSpec)))
        for kind in ('feature', 'target'):
            size = len(getattr(self.spec, f'{kind}_names'))
            for part in ('mean', 'scale', 'counts'):
                name = f'{kind}_{part}'
                raw = getattr(self, name)
                if not isinstance(raw, (list, tuple)) or len(raw) != size:
                    raise ValueError('Normalization channel dimensions differ')
                if part == 'counts':
                    if any(type(x) is not int or x < 1 for x in raw):
                        raise ValueError('Normalization requires valid raw observations for every channel')
                    values = tuple(raw)
                else:
                    if any(type(x) not in (int, float) for x in raw):
                        raise ValueError('Normalization statistics require finite numbers')
                    values = tuple(float(x) for x in raw)
                    _finite(values, 'normalization statistics')
                    if part == 'scale' and min(values) <= 0:
                        raise ValueError('Normalization scales must be positive')
                object.__setattr__(self, name, values)
        if type(self.raw_support_fingerprint) is not str or not self.raw_support_fingerprint:
            raise ValueError('Normalization requires a raw support identity')

    @classmethod
    def fit(cls, training):
        training = training_snapshot(training)
        spec = training.spec
        statistics = {}
        for kind in ('feature', 'target'):
            values = getattr(training, f'raw_{kind}s')
            mask = getattr(training, f'raw_{kind}_mask')
            transformed = _transformed(values, mask, spec, kind)
            means, scales, counts = [], [], []
            for channel in range(values.shape[1]):
                selected = transformed[:, channel][mask[:, channel]]
                if not len(selected):
                    raise ValueError('No valid raw training observations for a normalization channel')
                with np.errstate(over='ignore', invalid='ignore'):
                    mean, scale = float(selected.mean()), float(selected.std(ddof=0))
                _finite([mean, scale], 'training normalization statistics')
                means.append(mean)
                scales.append(scale if scale > 0 else 1.)
                counts.append(len(selected))
            statistics.update({f'{kind}_mean': tuple(means), f'{kind}_scale': tuple(scales),
                               f'{kind}_counts': tuple(counts)})
        # Deliberately exclude derived windows and the full-dataset fingerprint:
        # neither window multiplicity nor held-out data define fitting support.
        raw_identity = fingerprint_payload(dict(spec=spec.fingerprint,
            **{name: logical_array(getattr(training, name)) for name in (
                'raw_starts_ns', 'raw_ends_ns', 'raw_features', 'raw_feature_mask',
                'raw_targets', 'raw_target_mask')}))
        return cls(spec=spec, raw_support_fingerprint=raw_identity, **statistics)

    def normalize(self, values, mask, kind):
        if kind not in ('feature', 'target'):
            raise ValueError('Unsupported normalization kind')
        transformed = _transformed(values, mask, self.spec, kind)
        mean, scale = np.asarray(getattr(self, f'{kind}_mean')), np.asarray(getattr(self, f'{kind}_scale'))
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            result = np.where(mask, (transformed - mean) / scale, 0.)
        return _finite(result, 'normalized tensor inputs')

    def inverse_targets(self, values):
        with np.errstate(over='ignore', invalid='ignore'):
            transformed = np.asarray(values, float) * np.asarray(self.target_scale) + np.asarray(self.target_mean)
        return self.spec.inverse_targets(_finite(transformed, 'denormalized predictions'))

    def as_dict(self):
        return dict(schema_version=1, fitting_scope='UNIQUE_RAW_TRAINING_PARTITION',
            spec=self.spec.as_dict(), spec_fingerprint=self.spec.fingerprint,
            raw_support_fingerprint=self.raw_support_fingerprint,
            **{name: list(getattr(self, name)) for name in (
                'feature_mean', 'feature_scale', 'target_mean', 'target_scale',
                'feature_counts', 'target_counts')})

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())

    @classmethod
    def from_dict(cls, record):
        required = {'schema_version', 'fitting_scope', 'spec', 'spec_fingerprint', 'raw_support_fingerprint',
                    'feature_mean', 'feature_scale', 'target_mean', 'target_scale', 'feature_counts', 'target_counts'}
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError('Malformed normalization record')
        canonical_json(record)
        if type(record['schema_version']) is not int or record['schema_version'] != 1 or record['fitting_scope'] != 'UNIQUE_RAW_TRAINING_PARTITION':
            raise ValueError('Unsupported normalization scope/version')
        spec = ForecastSpec(**record['spec'])
        if record['spec_fingerprint'] != spec.fingerprint:
            raise ValueError('Normalization spec identity differs')
        return cls(spec=spec, **{key: record[key] for key in required - {
            'schema_version', 'fitting_scope', 'spec', 'spec_fingerprint'}})
