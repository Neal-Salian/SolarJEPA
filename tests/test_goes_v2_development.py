"""Offline loader isolation tests; synthetic native-reader fixtures only."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (
    'data/manifests/goes_v1_202405.json',
    'data/manifests/goes_v1_202406.json',
    'data/manifests/goes_p2_july2024.json',
)
SPLITS = [
    dict(name='train', start_utc='2024-05-01T00:00:00Z', end_utc='2024-07-22T00:00:00Z'),
    dict(name='validation', start_utc='2024-07-22T00:00:00Z', end_utc='2024-08-01T00:00:00Z'),
]


def loader():
    name = 'solar_flare_jepa.data.goes_v2_development'
    assert importlib.util.find_spec(name) is not None, 'Dedicated development-only GOES loader missing'
    return importlib.import_module(name)


@pytest.fixture
def frozen_root(tmp_path):
    """Copy small tracked metadata only; no real scientific files are inspected."""
    for relative in MANIFESTS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        inventory = json.loads(target.read_text())
        config = tmp_path / inventory['config_path']
        config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / inventory['config_path'], config)
    return tmp_path.resolve()


@pytest.mark.parametrize('mode', ['test', 'confirmatory', 'training', 'DEVELOPMENT_ONLY', '', None])
def test_mode_rejected_before_any_source_access(tmp_path, mode):
    with pytest.raises(ValueError, match='development'):
        loader().load_development(tmp_path, mode=mode)


@pytest.mark.parametrize('selection', [
    (*MANIFESTS, 'data/manifests/goes_v1_202408.json'),
    ('data/manifests/goes_202501.json',),
    MANIFESTS[::-1],
    (MANIFESTS[0], MANIFESTS[0], MANIFESTS[2]),
    '../data/manifests/goes_v1_202405.json',
])
def test_unapproved_manifest_selection_rejected_before_source_access(tmp_path, selection):
    with pytest.raises(ValueError, match='manifest selection'):
        loader().load_development(tmp_path, manifests=selection)


@pytest.mark.parametrize('change', ['calendar', 'pseudo_test', 'test_role', 'reorder'])
def test_calendar_and_partition_roles_cannot_change_before_source_access(tmp_path, change):
    splits = copy.deepcopy(SPLITS)
    if change == 'calendar':
        splits[0]['end_utc'] = '2024-07-21T00:00:00Z'
    elif change == 'pseudo_test':
        splits.append(dict(name='test', start_utc='2024-07-31T00:00:00Z', end_utc='2024-08-01T00:00:00Z'))
    elif change == 'test_role':
        splits[1]['name'] = 'test'
    else:
        splits.reverse()
    with pytest.raises(ValueError, match='split'):
        loader().load_development(tmp_path, splits=splits)


@pytest.mark.parametrize(('field', 'value'), [
    ('context_steps', 60), ('transform', 'identity'),
    ('target_units', ['counts', 'W/m2']), ('eligibility_policy', 'masked'),
])
def test_forecast_mutations_rejected_before_source_access(tmp_path, field, value):
    forecast = json.loads((ROOT / 'configs/experiments/v1_goes_2024.json').read_text())['forecast']
    forecast[field] = value
    with pytest.raises(ValueError, match='forecast'):
        loader().load_development(tmp_path, forecast=forecast)


def test_later_manifest_tampering_blocks_before_first_raw_read(frozen_root, monkeypatch):
    from solar_flare_jepa.data import foundation
    def forbidden(*args, **kwargs):
        pytest.fail('Raw native files opened before all manifest guards passed')
    monkeypatch.setattr(foundation, '_pinned_frame', forbidden)
    path = frozen_root / MANIFESTS[1]
    content = json.loads(path.read_text())
    content['product'] = 'unapproved_product'
    path.write_text(json.dumps(content))
    with pytest.raises(ValueError, match='manifest.*identity'):
        loader().load_development(frozen_root)


def test_later_config_tampering_blocks_before_first_raw_read(frozen_root, monkeypatch):
    from solar_flare_jepa.data import foundation
    monkeypatch.setattr(foundation, '_pinned_frame', lambda *a, **k: pytest.fail('Native files opened'))
    path = frozen_root / 'configs/data/v1_goes_202406.json'
    content = json.loads(path.read_text())
    content['version'] = 'unexpected'
    path.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        loader().load_development(frozen_root)


def test_manifest_symlink_is_rejected(frozen_root, monkeypatch):
    from solar_flare_jepa.data import foundation
    monkeypatch.setattr(foundation, '_pinned_frame', lambda *a, **k: pytest.fail('Native files opened'))
    path = frozen_root / MANIFESTS[0]
    target = path.with_suffix('.copy')
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(ValueError, match='symlink|Symlink'):
        loader().load_development(frozen_root)


def test_loader_import_does_not_load_model_modules():
    result = subprocess.run([sys.executable, '-c',
        "import sys; from solar_flare_jepa.data import goes_v2_development; "
        "assert 'solar_flare_jepa.training.jepa' not in sys.modules; assert 'torch' not in sys.modules"],
        cwd=ROOT, capture_output=True, text=True, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT / 'src')})
    assert result.returncode == 0, result.stderr


def test_failed_native_product_identity_blocks_before_frame_read(frozen_root, monkeypatch):
    module = loader()
    from solar_flare_jepa.data import foundation, goes_acquisition, goes_development_validation
    def verified(manifest, root):
        return [root / row['path'] for row in json.loads(Path(manifest).read_text())['files']]
    monkeypatch.setattr(goes_acquisition, 'verify_history', verified)
    monkeypatch.setattr(goes_development_validation, 'native_identity',
        lambda path, row: dict(path=row['path'], passed=False, checks={'processing_level': False}, provenance={}))
    monkeypatch.setattr(foundation, '_pinned_frame', lambda *a, **k: pytest.fail('Native flux read before identity guard'))
    with pytest.raises(ValueError, match='native.*identity'):
        module.load_development(frozen_root)


def synthetic_reader(monkeypatch):
    """Replace the native boundary; keep real assembly, windows and normalization."""
    from solar_flare_jepa.data import foundation
    def read(relative, root):
        assert relative in MANIFESTS, 'A forbidden selection reached the native reader'
        inventory = json.loads((root / relative).read_text())
        interval = inventory['selected_interval']
        index = pd.date_range(interval['start'], interval['end_exclusive'], inclusive='left', freq='min', tz='UTC')
        # Training and validation intentionally have different levels so scaler
        # leakage is visible. Both channels have positive native values.
        validation = index >= pd.Timestamp('2024-07-22T00:00:00Z')
        flux = np.where(validation, 1e-3, 1e-6)
        frame = pd.DataFrame(dict(xrsa_flux=flux / 10, xrsb_flux=flux,
                                  xrsa_valid=True, xrsb_valid=True), index=index)
        frame['time_end'] = index + pd.Timedelta(minutes=1)
        frame['observed'] = True
        for channel, factor in (('xrsa', 10), ('xrsb', 1)):
            frame[channel + '_flux_raw'] = flux / factor
            frame[channel + '_flag'] = 0
            frame[channel + '_num'] = 60
        frame['electron_correction_flag'] = 0
        return root / relative, inventory, [], frame, dict(status='OFFLINE_SYNTHETIC_NATIVE_BOUNDARY')
    monkeypatch.setattr(foundation, '_pinned_frame', read)
    monkeypatch.setattr(loader(), '_native_identities', lambda root: [
        dict(path=row['path'], passed=True, checks={'offline': True}, provenance={})
        for relative in MANIFESTS for row in json.loads((root / relative).read_text())['files']])
    monkeypatch.setattr(loader(), '_verify_sources_at_completion', lambda root, dataset: None)
    # Any accidental eager tensor/model use fails before importing optional Torch.
    from solar_flare_jepa.training import core, jepa
    monkeypatch.setattr(core, '_torch', lambda: pytest.fail('Preprocessing imported Torch'))
    monkeypatch.setattr(jepa, '_torch', lambda: pytest.fail('Preprocessing imported Torch'))


def test_complete_synthetic_calendar_has_only_two_windows_and_train_only_scaler(frozen_root, monkeypatch):
    synthetic_reader(monkeypatch)
    module = loader()
    bundle = module.load_development(frozen_root)
    assert bundle.train.as_dict()['partition']['name'] == 'train'
    assert bundle.validation.as_dict()['partition']['name'] == 'validation'
    assert len(bundle.dataset.starts_ns) == 132480  # 92 calendar days
    assert len(bundle.train.retained_origins) == 3932
    assert len(bundle.validation.retained_origins) == 476
    assert bundle.normalization.feature_mean == pytest.approx((-7., -6.))
    assert bundle.normalization.target_mean == pytest.approx((-7., -6.))
    assert bundle.normalization.feature_counts == (118080, 118080)
    evidence = bundle.evidence
    assert evidence['train_windows']['eligible'] == 117931
    assert evidence['train_windows']['used'] == 20000
    assert evidence['model_fit_executed'] is False
    assert evidence['test_partition_constructed'] is False
    assert evidence['test_windows_built'] is False
    assert evidence['native_identity_passed'] == 92
    assert evidence['quality_summary']['observed_bins'] == 132480
    assert evidence['quality_summary']['missing_bins'] == 0
    assert evidence['shapes']['validation_context'] == [476, 120, 2]
    assert evidence['training_fingerprint'] == bundle.training.fingerprint
    assert evidence['normalization_fingerprint'] == bundle.normalization.fingerprint
    assert max(bundle.training.raw_ends_ns) == pd.Timestamp('2024-07-22T00:00:00Z').value
    assert min(bundle.validation.context.starts_ns[:, 0]) >= max(bundle.training.raw_ends_ns)
    evidence['model_fit_executed'] = True
    assert bundle.evidence['model_fit_executed'] is False  # detached provenance


def test_measured_fingerprints_are_deterministic_and_expected_ids_are_checked(frozen_root, monkeypatch):
    synthetic_reader(monkeypatch)
    module = loader()
    first = module.load_development(frozen_root)
    repeat = module.load_development(frozen_root,
        dataset_fingerprint=first.dataset.fingerprint,
        split_fingerprint=first.evidence['split_fingerprint'],
        split_fingerprints=first.evidence['split_fingerprints'])
    assert repeat.evidence == first.evidence
    with pytest.raises(ValueError, match='dataset.*fingerprint'):
        module.load_development(frozen_root, dataset_fingerprint='0' * 64)
    with pytest.raises(ValueError, match='split.*fingerprint'):
        module.load_development(frozen_root, split_fingerprint='0' * 64)


def test_assembly_source_hashes_must_equal_pins_at_completion(frozen_root):
    from types import SimpleNamespace
    dataset = SimpleNamespace(metadata_json=json.dumps({'sources': []}))
    with pytest.raises(ValueError, match='source.*identit'):
        loader()._verify_sources_at_completion(frozen_root, dataset)


def test_raw_bytes_are_reverified_after_preparation(frozen_root, monkeypatch):
    from types import SimpleNamespace
    from solar_flare_jepa.data import goes_acquisition
    sources = [dict(path=row['path'], bytes=row['bytes'], sha256=row['sha256'])
               for relative in MANIFESTS for row in json.loads((frozen_root / relative).read_text())['files']]
    dataset = SimpleNamespace(metadata_json=json.dumps({'sources': sources}))
    def changed(*args):
        raise ValueError('changed raw bytes detected at completion')
    monkeypatch.setattr(goes_acquisition, 'verify_history', changed)
    with pytest.raises(ValueError, match='changed raw bytes'):
        loader()._verify_sources_at_completion(frozen_root, dataset)
