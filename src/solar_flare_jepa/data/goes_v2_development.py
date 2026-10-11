"""Frozen May–July 2024 development inputs; no test loader or model fitting.

This route preserves V1's training/validation calendar and native GOES policies
while giving the smaller dataset its own observed identity. The three historical
manifests remain immutable. A different selection/calendar requires a versioned
implementation and authorization; caller strings cannot broaden this route.
"""
from dataclasses import dataclass
import json

import pandas as pd

from solar_flare_jepa.experiments.config import read_finite_json, utc_ns
from solar_flare_jepa.experiments.provenance import _source_path
from solar_flare_jepa.forecasting.contracts import (
    ForecastSpec, TimeSeriesDataset, canonical_json, fingerprint_payload, logical_array,
)
from solar_flare_jepa.forecasting.splitting import TemporalPartition
from solar_flare_jepa.forecasting.windows import WindowedPartition, build_partition_windows
from solar_flare_jepa.training.normalization import Normalization

from . import foundation
from .download import sha256_file
from .goes_acquisition import _config, _ledger, _path


MANIFEST_PINS = (
    ('data/manifests/goes_v1_202405.json',
     '9828b714ecb4545af2711f2760d110b9d0dd963a67e1f3d1d1f711af0aeb2240'),
    ('data/manifests/goes_v1_202406.json',
     '91e45449c61918c52786c4d4f45d4d9311ef313bbc8baace314a40bf135ecc79'),
    ('data/manifests/goes_p2_july2024.json',
     '581a3c4b8cfba6b9b21ed1fdb0b2277e728e9bf329a8da1ddcc0bd49c3cc4b3d'),
)
_SPLITS = (
    ('train', '2024-05-01T00:00:00Z', '2024-07-22T00:00:00Z'),
    ('validation', '2024-07-22T00:00:00Z', '2024-08-01T00:00:00Z'),
)


def forecast_definition():
    """Detached canonical V1 forecast geometry and native channel semantics."""
    return ForecastSpec(cadence_seconds=60, context_steps=120, horizon_steps=30,
        stride_steps=30, feature_names=('xrsa_flux', 'xrsb_flux'),
        target_names=('xrsa_flux', 'xrsb_flux'), feature_units=('W/m2', 'W/m2'),
        target_units=('W/m2', 'W/m2'), availability_mode='retrospective_bin_end',
        eligibility_policy='complete', transform='log10', feature_reference=(1., 1.),
        target_reference=(1., 1.), target_minimum=(0., 0.)).as_dict()


def split_definitions():
    """Only the two authorized historical half-open UTC partitions."""
    return [dict(name=name, start_utc=start, end_utc=end) for name, start, end in _SPLITS]


@dataclass(frozen=True)
class DevelopmentBundle:
    dataset: TimeSeriesDataset
    train: WindowedPartition
    validation: WindowedPartition
    normalization: Normalization
    _evidence_json: str

    @property
    def training(self):
        return self.train.training_slice

    @property
    def evidence(self):
        """Detached, deterministic metadata; no wall-clock or model outcomes."""
        return json.loads(self._evidence_json)


def _definitions(mode, manifests, forecast, splits, max_train_windows):
    if mode != 'development':
        raise ValueError('GOES loader permits development mode only')
    expected = tuple(path for path, _ in MANIFEST_PINS)
    if manifests is not None and (not isinstance(manifests, (tuple, list)) or tuple(manifests) != expected):
        raise ValueError('Development manifest selection must be the frozen ordered May–July inputs')
    spec = ForecastSpec(**forecast_definition())
    if forecast is not None:
        try:
            supplied = ForecastSpec(**forecast)
        except (TypeError, ValueError) as error:
            raise ValueError('Development forecast definition differs from frozen V1 semantics') from error
        if supplied.fingerprint != spec.fingerprint:
            raise ValueError('Development forecast definition differs from frozen V1 semantics')
    if splits is not None:
        try:
            if not isinstance(splits, (list, tuple)) or len(splits) != 2:
                raise ValueError('Exactly train and validation splits required')
            supplied = []
            for item in splits:
                if not isinstance(item, dict) or set(item) != {'name', 'start_utc', 'end_utc'}:
                    raise ValueError('Unexpected split definition')
                supplied.append((item['name'], utc_ns(item['start_utc']), utc_ns(item['end_utc'])))
            expected_splits = [(name, utc_ns(start), utc_ns(end)) for name, start, end in _SPLITS]
            if supplied != expected_splits:
                raise ValueError('Changed split bounds or roles')
        except (TypeError, ValueError) as error:
            raise ValueError('Development splits must preserve the two frozen V1 calendar bounds') from error
    if type(max_train_windows) is not int or max_train_windows != 20000:
        raise ValueError('Development training-window cap must remain 20000')
    return spec


def _metadata(root):
    """Validate every metadata pin before the first scientific file is opened."""
    identities = []
    for relative, digest in MANIFEST_PINS:
        manifest = _path(relative, root)
        if sha256_file(manifest) != digest:
            raise ValueError(f'Development manifest identity differs: {relative}')
        inventory = read_finite_json(manifest)
        spec, config_relative, config_digest, output = _config(inventory['config_path'], root)
        _ledger(inventory, spec, config_relative, config_digest)
        if output != manifest or inventory['complete'] is not True:
            raise ValueError('Development manifest/config completion identity differs')
        identities.append(dict(path=relative, sha256=digest,
            config_path=config_relative, config_sha256=config_digest,
            files=inventory['selected_file_count'], bytes=inventory['total_bytes']))
    return identities


def _native_identities(root):
    """Check every verified file's native product metadata before decoding flux."""
    from .goes_acquisition import verify_history
    from .goes_development_validation import native_identity
    identities = []
    for relative, _ in MANIFEST_PINS:
        inventory = read_finite_json(root / relative)
        paths = verify_history(root / relative, root)
        for path, row in zip(paths, inventory['files'], strict=True):
            identity = native_identity(path, row)
            if identity['passed'] is not True:
                failed = sorted(name for name, passed in identity['checks'].items() if not passed)
                raise ValueError(f"Development native product identity differs: {row['path']}: {failed}")
            identities.append(identity)
    return identities


def _verify_sources_at_completion(root, dataset):
    """Refuse stale attribution if source/metadata bytes changed while preparing."""
    from .goes_acquisition import verify_history
    _metadata(root)
    expected = [dict(path=row['path'], bytes=row['bytes'], sha256=row['sha256'])
                for relative, _ in MANIFEST_PINS
                for row in read_finite_json(_path(relative, root))['files']]
    if json.loads(dataset.metadata_json).get('sources') != expected:
        raise ValueError('Assembled source identities differ from the pinned manifests')
    for relative, _ in MANIFEST_PINS:
        verify_history(_path(relative, root), root)


def load_development(root, *, mode='development', manifests=None, forecast=None, splits=None,
                     dataset_fingerprint=None, split_fingerprint=None, split_fingerprints=None,
                     max_train_windows=20000):
    """Verify only frozen local development sources and prepare fitting artifacts.

    All caller definitions and all three manifest/config identities are checked
    before native reads. This function neither acquires data nor constructs test
    objects. Expected dataset/split fingerprints, when supplied, are compared to
    actual content after validation; no expected identity is silently invented.

    Normalization fits scalar statistics on unique raw training bins only.
    Stride-1 eligibility uses lazy ``TrainWindows`` normalized row arrays plus
    start indices, avoiding expanded context/future tensors. No Torch call,
    optimizer, predictor, training loop or staged-run constructor is used.
    """
    spec = _definitions(mode, manifests, forecast, splits, max_train_windows)
    root = _source_path(root)
    sources = _metadata(root)
    native_identities = _native_identities(root)
    selections = [foundation._pinned_frame(relative, root) for relative, _ in MANIFEST_PINS]
    dataset = foundation._goes_dataset(selections, root, 'goes_historical_multi')
    from .goes_development_validation import quality_summary
    quality = quality_summary(pd.concat(selection[3] for selection in selections))
    partitions = [TemporalPartition(name, utc_ns(start), utc_ns(end)) for name, start, end in _SPLITS]
    train, validation = [build_partition_windows(dataset, spec, partition) for partition in partitions]
    training = train.training_slice
    normalization = Normalization.fit(training)
    # No model-module import before all metadata/bytes/native checks succeed.
    # This function uses row arrays and starts only; it never calls _torch().
    from solar_flare_jepa.training.jepa import training_windows
    lazy = training_windows(training, normalization, stride=1)
    selected = lazy.subsample(max_train_windows)
    split_ids = dict(train=train.split_fingerprint, validation=validation.split_fingerprint)
    split_id = fingerprint_payload(split_ids)
    if dataset_fingerprint is not None and dataset_fingerprint != dataset.fingerprint:
        raise ValueError('Observed development dataset fingerprint differs from expected identity')
    if split_fingerprint is not None and split_fingerprint != split_id:
        raise ValueError('Observed development split fingerprint differs from expected identity')
    if split_fingerprints is not None and split_fingerprints != split_ids:
        raise ValueError('Observed development split fingerprints differ from expected identities')
    evidence = dict(schema_version=1, status='VALIDATED_DEVELOPMENT_INPUTS',
        execution_mode='DEVELOPMENT_ONLY', source_selection='GOES16_MAY_JULY_2024_FROZEN_V1',
        manifest_identities=sources, native_file_count=sum(item['files'] for item in sources),
        native_identity_passed=sum(identity['passed'] for identity in native_identities),
        native_identities=native_identities, quality_summary=quality,
        native_coverage=dict(
            observed_start_utc=min(selection[4].get('observed_start_utc', selection[3].index[0].isoformat())
                                   for selection in selections),
            observed_end_utc=max(selection[4].get('observed_end_utc', selection[3].time_end.iloc[-1].isoformat())
                                 for selection in selections),
            grid_rows=len(dataset.starts_ns), duplicate_timestamps=0,
            missing_bins=quality['missing_bins']),
        native_bytes=sum(item['bytes'] for item in sources), dataset_fingerprint=dataset.fingerprint,
        forecast_fingerprint=spec.fingerprint, split_fingerprint=split_id, split_fingerprints=split_ids,
        training_fingerprint=training.fingerprint, normalization_fingerprint=normalization.fingerprint,
        partitions={window.as_dict()['partition']['name']: dict(
            **window.as_dict()['partition'], retained_origins=len(window.retained_origins),
            excluded_origins=len(window.excluded_origins), split_fingerprint=window.split_fingerprint)
            for window in (train, validation)},
        train_windows=dict(eligible=len(lazy), used=len(selected), stride=1, cap=max_train_windows,
            policy='complete_consecutive_raw_training_rows',
            subsample='evenly_spaced_chronological' if len(selected) < len(lazy) else 'none',
            fingerprint=fingerprint_payload(dict(starts=logical_array(selected.starts),
                issue_times_ns=logical_array(selected.issue_times_ns)))),
        shapes=dict(train_context=list(train.context.values.shape), train_targets=list(train.targets.values.shape),
            validation_context=list(validation.context.values.shape),
            validation_targets=list(validation.targets.values.shape), raw_training_rows=len(training.raw_starts_ns)),
        normalization=normalization.as_dict(), model_fit_executed=False, test_partition_constructed=False,
        test_windows_built=False,
        actual_operational_delivery='UNKNOWN', scientific_scope='EXPOSED_DEVELOPMENT_ONLY')
    _verify_sources_at_completion(root, dataset)
    return DevelopmentBundle(dataset, train, validation, normalization, canonical_json(evidence))
