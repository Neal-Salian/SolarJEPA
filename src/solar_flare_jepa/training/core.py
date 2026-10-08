"""Bounded optional PyTorch smoke training; this model is never SolarJEPA."""
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import random

import numpy as np

from solar_flare_jepa.forecasting.contracts import (
    ForecastContext, ForecastPrediction, ForecastSpec, ForecastTargets, FutureGrid,
    _canonical_fields, canonical_json, fingerprint_payload, validate_alignment,
)
from solar_flare_jepa.forecasting.windows import WindowedPartition
from .normalization import Normalization, training_snapshot

MODEL_ID = 'TRAINING_INFRASTRUCTURE_SMOKE_TEST'
IDENTITY_KEYS = {'source', 'dataset', 'spec', 'split', 'training', 'normalization', 'training_config'}


def _torch():
    try:
        import torch
    except ImportError as error:
        raise RuntimeError('Optional training dependency missing; install solar-flare-jepa[training]') from error
    return torch


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 17
    epochs: int = 2
    batch_size: int = 16
    max_train_batches: int = 4
    max_validation_batches: int = 2
    max_eval_origins: int = 32
    learning_rate: float = .001
    gradient_clip: float = 1.

    def __post_init__(self):
        limits = {'seed': (0, 2**32 - 1), 'epochs': (1, 20), 'batch_size': (1, 256),
                  'max_train_batches': (1, 64), 'max_validation_batches': (1, 64),
                  'max_eval_origins': (1, 2048)}
        for name, (lower, upper) in limits.items():
            value = getattr(self, name)
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError(f'{name} must be a bounded integer in [{lower}, {upper}]')
        for name, upper in (('learning_rate', 1.), ('gradient_clip', 1000.)):
            value = getattr(self, name)
            if type(value) not in (float, int) or not np.isfinite(value) or not 0 < value <= upper:
                raise ValueError(f'{name} must be finite and positive, at most {upper}')
            object.__setattr__(self, name, float(value))

    def as_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        return fingerprint_payload(self.as_dict())


def resolve_device(value='cpu'):
    torch = _torch()
    if value not in ('cpu', 'mps'):
        raise ValueError('Supported training devices are cpu and explicitly requested mps')
    if value == 'mps' and not (torch.backends.mps.is_built() and torch.backends.mps.is_available()):
        raise ValueError('MPS was requested but this runtime has no available MPS capability')
    return torch.device(value)


def _context_grid(context, grid):
    if not isinstance(context, ForecastContext) or not isinstance(grid, FutureGrid):
        raise ValueError('Prediction requires ForecastContext and FutureGrid')
    arguments = _canonical_fields(context, ForecastContext)
    arguments['spec'] = ForecastSpec(**_canonical_fields(context.spec, ForecastSpec))
    context = ForecastContext(**arguments)
    arguments = _canonical_fields(grid, FutureGrid)
    arguments['spec'] = ForecastSpec(**_canonical_fields(grid.spec, ForecastSpec))
    grid = FutureGrid(**arguments)
    validate_alignment(context, grid)
    return context, grid


def window_snapshot(window):
    if not isinstance(window, WindowedPartition):
        raise ValueError('Expected a WindowedPartition')
    context, grid = _context_grid(window.context, window.targets.grid)
    targets = ForecastTargets(window.targets.values, window.targets.mask, grid)
    return WindowedPartition(context, targets, None, canonical_json(window.as_dict()))


@dataclass(frozen=True)
class TensorBatch:
    features: object
    feature_mask: object
    targets: object
    target_mask: object
    origin_ids: tuple[str, ...]


def tensor_batch(window, normalization, indices, *, device='cpu'):
    torch = _torch()
    window = window_snapshot(window)
    if normalization.spec.fingerprint != window.context.spec.fingerprint:
        raise ValueError('Tensor batch normalization/spec identity differs')
    raw = list(indices)
    if (not raw or any(type(x) is not int for x in raw) or len(set(raw)) != len(raw)
            or min(raw) < 0 or max(raw) >= len(window.context.origin_ids)):
        raise ValueError('Batch indices must be explicit unique valid origins')
    features = normalization.normalize(window.context.values[raw], window.context.mask[raw], 'feature')
    targets = normalization.normalize(window.targets.values[raw], window.targets.mask[raw], 'target')
    device = resolve_device(str(device))
    features = torch.tensor(features, dtype=torch.float32, device=device)
    targets = torch.tensor(targets, dtype=torch.float32, device=device)
    if not torch.isfinite(features).all() or not torch.isfinite(targets).all():
        raise ValueError('Nonfinite tensor conversion')
    return TensorBatch(features, torch.tensor(window.context.mask[raw].copy(), dtype=torch.bool, device=device),
        targets, torch.tensor(window.targets.mask[raw].copy(), dtype=torch.bool, device=device),
        tuple(window.context.origin_ids[i] for i in raw))


def masked_mse(prediction, targets, mask):
    torch = _torch()
    if prediction.shape != targets.shape or mask.shape != targets.shape or mask.dtype != torch.bool:
        raise ValueError('Masked loss prediction/target/mask shape differs')
    if not torch.isfinite(prediction).all() or not torch.isfinite(targets).all():
        raise ValueError('Nonfinite loss inputs')
    if not bool(mask.any()):
        raise ValueError('No valid supervision cells in bounded batch')
    loss = (prediction[mask] - targets[mask]).square().mean()
    if not bool(torch.isfinite(loss)):
        raise ValueError('Nonfinite training loss')
    return loss


def build_smoke_model(spec):
    """Values and explicit mask are separate inputs; output is [B,H,K]."""
    torch = _torch()
    inputs = spec.context_steps * len(spec.feature_names) * 2
    outputs = spec.horizon_steps * len(spec.target_names)
    if inputs * outputs + outputs > 2_000_000:
        raise ValueError('Smoke model exceeds bounded parameter budget')

    class MaskedLinear(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(inputs, outputs)

        def forward(self, values, mask):
            if values.shape != mask.shape or values.shape[1:] != (spec.context_steps, len(spec.feature_names)):
                raise ValueError('Model input shape differs from forecast spec')
            joined = torch.cat((values.flatten(1), mask.to(values.dtype).flatten(1)), dim=1)
            return self.linear(joined).reshape(len(values), spec.horizon_steps, len(spec.target_names))

    return MaskedLinear()


def _cpu_state(value):
    torch = _torch()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: _cpu_state(part) for key, part in value.items()}
    if isinstance(value, list):
        return [_cpu_state(part) for part in value]
    if isinstance(value, tuple):
        return tuple(_cpu_state(part) for part in value)
    return deepcopy(value)


def _finite_state(state):
    torch = _torch()
    if isinstance(state, torch.Tensor):
        if not bool(torch.isfinite(state).all()):
            raise ValueError('Nonfinite checkpoint/model/optimizer weights')
    elif isinstance(state, dict):
        for value in state.values():
            _finite_state(value)
    elif isinstance(state, (list, tuple)):
        for value in state:
            _finite_state(value)
    elif type(state) is float and not np.isfinite(state):
        raise ValueError('Nonfinite optimizer state')


def _weights_fingerprint(state):
    _finite_state(state)
    items = []
    for name, tensor in sorted(state.items()):
        array = tensor.detach().cpu().numpy()
        items.append(dict(name=name, shape=list(array.shape), dtype=str(array.dtype),
                          sha256=hashlib.sha256(array.tobytes()).hexdigest()))
    return fingerprint_payload(items)


def _identities(value):
    if not isinstance(value, dict) or set(value) != IDENTITY_KEYS or any(type(x) is not str or not x for x in value.values()):
        raise ValueError('Checkpoint requires complete source/data/spec/split/training/normalization/config identities')
    return dict(value)


def _selection(window, maximum):
    count = min(len(window.context.origin_ids), maximum)
    if not count:
        raise ValueError('No eligible origins in bounded partition')
    return dict(policy='FIRST_CHRONOLOGICAL_ORIGINS_FIXED_BEFORE_TRAINING', eligible_count=len(window.context.origin_ids),
                selected_count=count, omitted_count=len(window.context.origin_ids) - count,
                origin_ids=list(window.context.origin_ids[:count]),
                valid_target_cells=int(window.targets.mask[:count].sum()),
                total_target_cells=int(window.targets.mask[:count].size))


class TrainedSmoke:
    def __init__(self, model, normalization, config, identities, record, optimizer_state, *, device='cpu'):
        self._device = resolve_device(device)
        self._model = model.to(self._device)
        self._model.eval()
        self.normalization = normalization
        self.config = config
        self.identities = _identities(identities)
        self._record = deepcopy(record)
        self.optimizer_state = _cpu_state(optimizer_state)

    @property
    def record(self):
        return deepcopy(self._record)

    def predict(self, context, future_grid):
        torch = _torch()
        context, future_grid = _context_grid(context, future_grid)
        if (context.spec.fingerprint != self.identities['spec']
                or context.dataset_fingerprint != self.identities['dataset']):
            raise ValueError('Prediction dataset/spec identity differs from checkpoint identity')
        output = []
        self._model.eval()
        with torch.inference_mode():
            for start in range(0, len(context.origin_ids), self.config.batch_size):
                stop = min(start + self.config.batch_size, len(context.origin_ids))
                values = self.normalization.normalize(context.values[start:stop], context.mask[start:stop], 'feature')
                features = torch.tensor(values, dtype=torch.float32, device=self._device)
                mask = torch.tensor(context.mask[start:stop].copy(), dtype=torch.bool, device=self._device)
                if not bool(torch.isfinite(features).all()):
                    raise ValueError('Nonfinite prediction tensor')
                predicted = self._model(features, mask)
                if predicted.shape != (stop - start, context.spec.horizon_steps, len(context.spec.target_names)) or not bool(torch.isfinite(predicted).all()):
                    raise ValueError('Nonfinite or malformed model output')
                output.append(predicted.cpu().numpy().astype(float))
        shape = (0, context.spec.horizon_steps, len(context.spec.target_names))
        values = self.normalization.inverse_targets(np.concatenate(output) if output else np.empty(shape))
        return ForecastPrediction(values, future_grid, MODEL_ID,
            point_interpretation='inverse_transformed_point' if context.spec.transform == 'log10' else 'native_point')

    def save_checkpoint(self, path):
        torch = _torch()
        path = Path(path)
        # Never replace an existing artifact, including dangling links.
        from solar_flare_jepa.experiments.provenance import _source_path
        _source_path(path.parent)
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
        state = _cpu_state(self._model.state_dict())
        _finite_state(self.optimizer_state)
        payload = dict(schema_version=1, model_id=MODEL_ID, model_kind='masked_linear',
            identities=dict(self.identities), spec=self.normalization.spec.as_dict(),
            normalization=self.normalization.as_dict(), training_config=self.config.as_dict(),
            training_record=self.record, model_state=state, model_weights_fingerprint=_weights_fingerprint(state),
            optimizer_kind='Adam', optimizer_state=_cpu_state(self.optimizer_state),
            seed=self.config.seed, torch_version=str(torch.__version__))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            torch.save(payload, stream)


def fit_smoke(training, validation, *, config=None, source_identity, split_identity, device='cpu'):
    """Fit fixed chronological batches; monitor validation only, never test."""
    torch = _torch()
    training = training_snapshot(training)
    validation = window_snapshot(validation)
    config = TrainingConfig() if config is None else TrainingConfig(**config.as_dict())
    device = resolve_device(device)
    if validation.as_dict().get('partition', {}).get('name') != 'validation':
        raise ValueError('Checkpoint monitoring requires the validation partition')
    if (validation.context.dataset_fingerprint != training.context.dataset_fingerprint
            or validation.context.spec.fingerprint != training.spec.fingerprint):
        raise ValueError('Validation training dataset/spec identity differs')
    if (validation.context.starts_ns < training.partition_end_ns).any():
        raise ValueError('Validation context overlaps raw training partition')
    normalization = Normalization.fit(training)
    identities = _identities(dict(source=source_identity, dataset=training.context.dataset_fingerprint,
        spec=training.spec.fingerprint, split=split_identity, training=training.fingerprint,
        normalization=normalization.fingerprint, training_config=config.fingerprint))
    train = WindowedPartition(training.context, training.targets, training, '{}')
    coverage = dict(train=_selection(train, config.batch_size * config.max_train_batches),
                    validation=_selection(validation, config.batch_size * config.max_validation_batches))
    # Fixed initialization and chronological iteration consume no held-out RNG.
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = build_smoke_model(training.spec).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    initial = _weights_fingerprint(model.state_dict())
    history, steps, best_loss, best_epoch = [], 0, float('inf'), None
    best_state = best_optimizer = None
    for epoch in range(1, config.epochs + 1):
        losses = {}
        for name, window in (('train', train), ('validation', validation)):
            is_train = name == 'train'
            model.train(is_train)
            total, cells = 0., 0
            for start in range(0, coverage[name]['selected_count'], config.batch_size):
                indices = list(range(start, min(start + config.batch_size, coverage[name]['selected_count'])))
                batch = tensor_batch(window, normalization, indices, device=str(device))
                with torch.set_grad_enabled(is_train):
                    if is_train:
                        optimizer.zero_grad(set_to_none=True)
                    output = model(batch.features, batch.feature_mask)
                    loss = masked_mse(output, batch.targets, batch.target_mask)
                    if is_train:
                        loss.backward()
                        for parameter in model.parameters():
                            if parameter.grad is None or not bool(torch.isfinite(parameter.grad).all()):
                                raise ValueError('Nonfinite or missing training gradients')
                        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip, error_if_nonfinite=True)
                        if not bool(torch.isfinite(norm)):
                            raise ValueError('Nonfinite gradient norm')
                        optimizer.step()
                        _finite_state(model.state_dict())
                        _finite_state(optimizer.state_dict())
                        steps += 1
                count = int(batch.target_mask.sum().item())
                total += float(loss.detach().cpu()) * count
                cells += count
            losses[name] = total / cells
            if not np.isfinite(losses[name]):
                raise ValueError('Nonfinite aggregate epoch loss')
        history.append(dict(epoch=epoch, training_loss=losses['train'], validation_loss=losses['validation']))
        if losses['validation'] < best_loss:
            best_loss, best_epoch = losses['validation'], epoch
            best_state, best_optimizer = _cpu_state(model.state_dict()), _cpu_state(optimizer.state_dict())
    final_fingerprint = _weights_fingerprint(model.state_dict())
    model.load_state_dict(best_state, strict=True)
    record = dict(model_id=MODEL_ID, model_kind='masked_linear', scientific_status='TRAINING_INFRASTRUCTURE_SMOKE_TEST',
        phase_e='BLOCKED_FOR_PHASE_E', identities=dict(identities), training_config=config.as_dict(),
        device=str(device), torch_version=str(torch.__version__), optimizer='Adam',
        deterministic_algorithms=True, torch_threads=1, iteration='fixed_chronological_no_shuffle',
        tensor_dtype='float32', normalization_dtype='float64', masked_fill='normalized_zero_for_tensor_consumption_only',
        optimizer_steps=steps, history=history, coverage=coverage,
        selection=dict(partition='validation', metric='masked_normalized_mse', epoch=best_epoch,
                       loss=best_loss, tie_policy='earliest_epoch'),
        initial_weights_fingerprint=initial, final_training_weights_fingerprint=final_fingerprint,
        selected_weights_fingerprint=_weights_fingerprint(best_state))
    canonical_json(record)
    return TrainedSmoke(model, normalization, config, identities, record, best_optimizer, device=str(device))


def _validate_training_record(record, config, torch_version):
    """Reject scientific and monitoring claims inconsistent with this smoke run."""
    constants = dict(model_id=MODEL_ID, model_kind='masked_linear',
        scientific_status=MODEL_ID, phase_e='BLOCKED_FOR_PHASE_E', optimizer='Adam',
        deterministic_algorithms=True, torch_threads=1, iteration='fixed_chronological_no_shuffle',
        tensor_dtype='float32', normalization_dtype='float64',
        masked_fill='normalized_zero_for_tensor_consumption_only', torch_version=torch_version)
    if not isinstance(record, dict) or any(record.get(k) != v for k,v in constants.items()):
        raise ValueError('Checkpoint training record status/policy contradicts smoke infrastructure')
    history = record.get('history')
    if not isinstance(history, list) or len(history) != config.epochs:
        raise ValueError('Checkpoint training history does not match epoch configuration')
    for epoch, entry in enumerate(history, 1):
        if (not isinstance(entry, dict) or set(entry) != {'epoch', 'training_loss', 'validation_loss'}
                or type(entry['epoch']) is not int or entry['epoch'] != epoch
                or any(type(entry[k]) not in (int, float) or not np.isfinite(entry[k]) or entry[k] < 0
                       for k in ('training_loss', 'validation_loss'))):
            raise ValueError('Checkpoint training history has invalid monitoring values')
    best = min(history, key=lambda item: item['validation_loss'])
    expected_selection = dict(partition='validation', metric='masked_normalized_mse',
        epoch=best['epoch'], loss=best['validation_loss'], tie_policy='earliest_epoch')
    if record.get('selection') != expected_selection:
        raise ValueError('Checkpoint selection contradicts validation monitoring history')
    coverage = record.get('coverage')
    if not isinstance(coverage, dict) or set(coverage) != {'train', 'validation'}:
        raise ValueError('Checkpoint monitoring coverage must describe train and validation')
    for name, limit in [('train', config.max_train_batches), ('validation', config.max_validation_batches)]:
        item = coverage[name]
        if not isinstance(item, dict):
            raise ValueError('Invalid checkpoint coverage record')
        counts = [item.get(k) for k in ('eligible_count', 'selected_count', 'omitted_count',
                                       'valid_target_cells', 'total_target_cells')]
        if (any(type(x) is not int or x < 0 for x in counts)
                or not 0 < counts[1] <= min(counts[0], config.batch_size*limit)
                or counts[2] != counts[0]-counts[1] or not 0 < counts[3] <= counts[4]
                or item.get('policy') != 'FIRST_CHRONOLOGICAL_ORIGINS_FIXED_BEFORE_TRAINING'
                or not isinstance(item.get('origin_ids'), list)
                or len(item['origin_ids']) != counts[1] or len(set(item['origin_ids'])) != counts[1]):
            raise ValueError('Checkpoint coverage record contradicts bounded monitoring')
    steps = ((coverage['train']['selected_count']+config.batch_size-1)//config.batch_size)*config.epochs
    if type(record.get('optimizer_steps')) is not int or record['optimizer_steps'] != steps:
        raise ValueError('Checkpoint optimizer steps contradict bounded training history')


def load_checkpoint(path, *, expected_identities, device='cpu'):
    torch = _torch()
    expected = _identities(expected_identities)
    from solar_flare_jepa.experiments.provenance import _source_path
    path = _source_path(path)
    try:
        payload = torch.load(path, map_location='cpu', weights_only=True)
    except Exception as error:
        raise ValueError('Checkpoint could not be loaded with safe weights-only deserialization') from error
    required = {'schema_version', 'model_id', 'model_kind', 'identities', 'spec', 'normalization',
                'training_config', 'training_record', 'model_state', 'model_weights_fingerprint',
                'optimizer_kind', 'optimizer_state', 'seed', 'torch_version'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError('Malformed checkpoint payload')
    if type(payload['schema_version']) is not int or payload['schema_version'] != 1 or payload['model_id'] != MODEL_ID or payload['model_kind'] != 'masked_linear' or payload['optimizer_kind'] != 'Adam':
        raise ValueError('Unsupported checkpoint version/model/optimizer')
    identities = _identities(payload['identities'])
    if identities != expected:
        raise ValueError('Checkpoint identities do not match required provenance')
    normalization = Normalization.from_dict(payload['normalization'])
    config = TrainingConfig(**payload['training_config'])
    spec = ForecastSpec(**payload['spec'])
    record = payload['training_record']
    canonical_json(record)
    _validate_training_record(record, config, payload['torch_version'])
    if (spec.fingerprint != identities['spec'] or normalization.spec.fingerprint != spec.fingerprint
            or normalization.fingerprint != identities['normalization']
            or config.fingerprint != identities['training_config'] or payload['seed'] != config.seed
            or record.get('identities') != identities or record.get('training_config') != config.as_dict()):
        raise ValueError('Checkpoint internal provenance identity differs')
    _finite_state(payload['model_state'])
    _finite_state(payload['optimizer_state'])
    weight_identity = _weights_fingerprint(payload['model_state'])
    if weight_identity != payload['model_weights_fingerprint'] or weight_identity != record.get('selected_weights_fingerprint'):
        raise ValueError('Checkpoint weight identity differs')
    model = build_smoke_model(spec)
    try:
        model.load_state_dict(payload['model_state'], strict=True)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
        optimizer.load_state_dict(payload['optimizer_state'])
    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        raise ValueError('Incompatible checkpoint model/optimizer state') from error
    return TrainedSmoke(model, normalization, config, identities, record, payload['optimizer_state'], device=device)
