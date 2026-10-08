"""CPU numerical modeling of recorded arrays, with no instrument-time contract.

The caller supplies train-only scalar standardization and already separated
sample windows. No physical units, UTC, completed-bin availability, calibrated
measurement, event labels, or SolarJEPA architecture are asserted here.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from solar_flare_jepa.training.core import build_smoke_model, masked_mse


SCIENTIFIC_LABEL = 'EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED'
MODEL_KIND = 'numerical_sample_masked_linear_v1'
DEFAULT_CONFIG = dict(seed=17, epochs=8, batch_size=128, learning_rate=.001, gradient_clip=1.)


def _torch():
    try:
        import torch
    except ImportError as error:
        raise RuntimeError('Numerical training requires the optional PyTorch training dependency') from error
    return torch


def _config(value):
    if not isinstance(value, dict) or set(value) != set(DEFAULT_CONFIG):
        raise ValueError('Explicit seed, epochs, batch_size, learning_rate and gradient_clip are required')
    result = dict(value)
    for name, lower, upper in [('seed', 0, 2**32 - 1), ('epochs', 1, 20), ('batch_size', 1, 256)]:
        if type(result[name]) is not int or not lower <= result[name] <= upper:
            raise ValueError(f'{name} is outside the bounded numerical training configuration')
    for name, upper in [('learning_rate', 1.), ('gradient_clip', 1000.)]:
        if type(result[name]) not in (int, float) or not np.isfinite(result[name]) or not 0 < result[name] <= upper:
            raise ValueError(f'{name} requires a finite positive bounded number')
        result[name] = float(result[name])
    return result


def _normalization(mean, scale):
    for value in (mean, scale):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)) or not np.isfinite(value):
            raise ValueError('Numerical normalization requires finite scalar statistics')
    if scale <= 0:
        raise ValueError('Numerical normalization scale must be positive')
    return dict(mean=float(mean), scale=float(scale))


def _identities(value):
    if (not isinstance(value, dict) or not value
            or any(type(k) is not str or not k.strip() or type(v) is not str or not v.strip()
                   for k, v in value.items())):
        raise ValueError('Complete supplied provenance identities require nonempty string keys and values')
    return dict(value)


def _arrays(values, mask, *, steps=None, allow_empty=False):
    raw, mask = np.asarray(values), np.asarray(mask)
    if (raw.dtype.kind not in 'fiu' or raw.ndim != 3 or raw.shape[-1] != 1
            or raw.shape[1] < 1 or (not allow_empty and raw.shape[0] < 1)
            or steps is not None and raw.shape[1] != steps
            or mask.dtype.kind != 'b' or raw.shape != mask.shape):
        raise ValueError('Numerical values and boolean masks require matching [origins, samples, 1] shapes')
    values = np.array(raw, dtype=np.float64, copy=True)
    mask = np.array(mask, dtype=bool, copy=True)
    if np.isinf(values).any() or not np.isfinite(values[mask]).all():
        raise ValueError('Valid numerical observations must be finite; false-mask NaNs remain missing')
    if not mask.any(axis=(1, 2)).all():
        raise ValueError('Every numerical origin requires observed support')
    return values, mask


def _normalized(values, mask, normalization):
    result = np.zeros(values.shape, dtype=np.float64)
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            result[mask] = (values[mask] - normalization['mean']) / normalization['scale']
    except FloatingPointError as error:
        raise ValueError('Nonfinite numerical standardization') from error
    torch = _torch()
    tensor = torch.tensor(result, dtype=torch.float32, device='cpu')
    if not bool(torch.isfinite(tensor).all()):
        raise ValueError('Nonfinite float32 numerical tensor')
    return tensor, torch.tensor(mask, dtype=torch.bool, device='cpu')


def _finite_state(value):
    torch = _torch()
    if isinstance(value, torch.Tensor):
        if not bool(torch.isfinite(value).all()):
            raise ValueError('Nonfinite model or optimizer state')
    elif isinstance(value, dict):
        for part in value.values():
            _finite_state(part)
    elif isinstance(value, (list, tuple)):
        for part in value:
            _finite_state(part)
    elif type(value) is float and not np.isfinite(value):
        raise ValueError('Nonfinite optimizer scalar')


def _state_content(value):
    torch = _torch()
    if isinstance(value, torch.Tensor):
        array = value.detach().cpu().numpy()
        return dict(dtype=str(array.dtype), shape=list(array.shape), sha256=hashlib.sha256(array.tobytes()).hexdigest())
    if isinstance(value, dict):
        return [[type(key).__name__, key, _state_content(part)]
                for key, part in sorted(value.items(), key=lambda item: (type(item[0]).__name__, str(item[0])))]
    if isinstance(value, (list, tuple)):
        return [_state_content(part) for part in value]
    return value


def _state_fingerprint(value):
    _finite_state(value)
    return fingerprint_payload(_state_content(value))


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


def _model(context_steps, horizon_steps):
    if any(type(value) is not int or value < 1 for value in (context_steps, horizon_steps)):
        raise ValueError('Context and horizon require positive sample lengths')
    # Reuse only the numerical module factory. This shape object is deliberately
    # not a ForecastSpec and supplies no fictional seconds or UTC intervals.
    return build_smoke_model(SimpleNamespace(context_steps=context_steps, horizon_steps=horizon_steps,
                            feature_names=('recorded_COUNTS',), target_names=('recorded_COUNTS',)))


class NeuralModel:
    def __init__(self, model, record, optimizer_state):
        self._model = model.cpu().eval()
        self._record = deepcopy(record)
        self._optimizer_state = _cpu_state(optimizer_state)

    @property
    def history(self):
        return deepcopy(self._record['history'])

    @property
    def selected_epoch(self):
        return self._record['selected_epoch']

    @property
    def parameter_count(self):
        return sum(parameter.numel() for parameter in self._model.parameters())

    def predict(self, values, mask):
        torch = _torch()
        values, mask = _arrays(values, mask, steps=self._record['context_steps'], allow_empty=True)
        output = []
        self._model.eval()
        with torch.inference_mode():
            for start in range(0, len(values), self._record['config']['batch_size']):
                stop = min(start + self._record['config']['batch_size'], len(values))
                features, feature_mask = _normalized(values[start:stop], mask[start:stop], self._record['normalization'])
                prediction = self._model(features, feature_mask)
                if prediction.shape != (stop - start, self._record['horizon_steps'], 1) or not bool(torch.isfinite(prediction).all()):
                    raise ValueError('Nonfinite or malformed numerical model prediction')
                output.append(prediction.cpu().numpy().astype(np.float64))
        result = np.concatenate(output) if output else np.empty((0, self._record['horizon_steps'], 1))
        try:
            with np.errstate(over='raise', invalid='raise'):
                result = result * self._record['normalization']['scale'] + self._record['normalization']['mean']
        except FloatingPointError as error:
            raise ValueError('Nonfinite inverse numerical standardization') from error
        if not np.isfinite(result).all():
            raise ValueError('Nonfinite numerical prediction')
        return result

    def save_checkpoint(self, path):
        torch = _torch()
        path = Path(path).absolute()
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
        if any(parent.is_symlink() for parent in path.parents):
            raise ValueError('Checkpoint parent must not redirect through symlinks')
        state = _cpu_state(self._model.state_dict())
        _finite_state(self._optimizer_state)
        record = deepcopy(self._record)
        record['weights_fingerprint'] = _state_fingerprint(state)
        record['optimizer_fingerprint'] = _state_fingerprint(self._optimizer_state)
        payload = dict(**record, metadata_fingerprint=fingerprint_payload(record),
                       model_state=state, optimizer_state=_cpu_state(self._optimizer_state))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            torch.save(payload, stream)


def fit_neural(train_x, train_y, train_x_mask, train_y_mask,
               val_x, val_y, val_x_mask, val_y_mask, *, mean, scale, identities, config):
    """Fit all supplied train origins; select only by all validation target cells.

    Shapes are numerical samples, not elapsed durations. Standardization must
    have been fitted by the caller on unique raw training rows only.
    """
    torch = _torch()
    settings, normalization, identities = _config(config), _normalization(mean, scale), _identities(identities)
    tx, txm = _arrays(train_x, train_x_mask)
    ty, tym = _arrays(train_y, train_y_mask)
    vx, vxm = _arrays(val_x, val_x_mask, steps=tx.shape[1])
    vy, vym = _arrays(val_y, val_y_mask, steps=ty.shape[1])
    if len(tx) != len(ty) or len(vx) != len(vy):
        raise ValueError('Numerical feature and target origin counts differ')
    train_features, train_features_mask = _normalized(tx, txm, normalization)
    train_targets, train_targets_mask = _normalized(ty, tym, normalization)
    val_features, val_features_mask = _normalized(vx, vxm, normalization)
    val_targets, val_targets_mask = _normalized(vy, vym, normalization)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(settings['seed'])
    generator = np.random.default_rng(settings['seed'])
    model = _model(int(tx.shape[1]), int(ty.shape[1]))
    initial_identity = _state_fingerprint(model.state_dict())
    optimizer = torch.optim.Adam(model.parameters(), lr=settings['learning_rate'])
    history, best_loss, best_epoch, best_state, best_optimizer = [], float('inf'), None, None, None
    for epoch in range(1, settings['epochs'] + 1):
        model.train()
        total, cells, steps = 0., 0, 0
        order = generator.permutation(len(tx))
        for start in range(0, len(tx), settings['batch_size']):
            indices = order[start:start + settings['batch_size']].tolist()
            optimizer.zero_grad(set_to_none=True)
            output = model(train_features[indices], train_features_mask[indices])
            loss = masked_mse(output, train_targets[indices], train_targets_mask[indices])
            loss.backward()
            for parameter in model.parameters():
                if parameter.grad is None or not bool(torch.isfinite(parameter.grad).all()):
                    raise ValueError('Nonfinite or missing numerical training gradients')
            torch.nn.utils.clip_grad_norm_(model.parameters(), settings['gradient_clip'], error_if_nonfinite=True)
            optimizer.step()
            _finite_state(model.state_dict())
            _finite_state(optimizer.state_dict())
            count = int(train_targets_mask[indices].sum().item())
            total += float(loss.detach()) * count
            cells += count
            steps += 1
        training_loss = total / cells
        model.eval()
        total, cells = 0., 0
        with torch.inference_mode():
            for start in range(0, len(vx), settings['batch_size']):
                stop = min(start + settings['batch_size'], len(vx))
                output = model(val_features[start:stop], val_features_mask[start:stop])
                loss = masked_mse(output, val_targets[start:stop], val_targets_mask[start:stop])
                count = int(val_targets_mask[start:stop].sum().item())
                total += float(loss) * count
                cells += count
        validation_loss = total / cells
        if not np.isfinite([training_loss, validation_loss]).all():
            raise ValueError('Nonfinite numerical epoch loss')
        history.append(dict(epoch=epoch, training_loss=training_loss, validation_loss=validation_loss,
            train_origins=len(tx), validation_origins=len(vx), optimizer_steps=steps,
            training_target_cells=int(tym.sum()), validation_target_cells=int(vym.sum())))
        if validation_loss < best_loss:
            best_loss, best_epoch = validation_loss, epoch
            best_state, best_optimizer = _cpu_state(model.state_dict()), _cpu_state(optimizer.state_dict())
    model.load_state_dict(best_state, strict=True)
    record = dict(schema_version=1, model_kind=MODEL_KIND, scientific_label=SCIENTIFIC_LABEL,
        context_steps=int(tx.shape[1]), horizon_steps=int(ty.shape[1]), normalization=normalization,
        normalization_fingerprint=fingerprint_payload(normalization), config=settings,
        config_fingerprint=fingerprint_payload(settings), identities=identities, history=history,
        selected_epoch=best_epoch, selection='minimum_validation_masked_normalized_mse_earliest_tie',
        train_iteration='seeded_numpy_generator_permutation_all_origins_each_epoch',
        device='cpu', deterministic_algorithms=True, torch_threads=1,
        versions=dict(torch=str(torch.__version__), numpy=np.__version__),
        initial_weights_fingerprint=initial_identity, weights_fingerprint=_state_fingerprint(best_state),
        optimizer_fingerprint=_state_fingerprint(best_optimizer))
    canonical_json(record)
    return NeuralModel(model, record, best_optimizer)


def load_checkpoint(path, *, expected_identities):
    """Load tensors and primitive records safely on CPU, with explicit identities."""
    torch = _torch()
    expected = _identities(expected_identities)
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Checkpoint must be an existing regular file')
    try:
        payload = torch.load(path, map_location='cpu', weights_only=True)
    except Exception as error:
        raise ValueError('Checkpoint cannot be loaded with weights-only deserialization') from error
    required = {'schema_version', 'model_kind', 'scientific_label', 'context_steps', 'horizon_steps',
        'normalization', 'normalization_fingerprint', 'config', 'config_fingerprint', 'identities',
        'history', 'selected_epoch', 'selection', 'train_iteration', 'device', 'deterministic_algorithms',
        'torch_threads', 'versions', 'initial_weights_fingerprint', 'weights_fingerprint',
        'optimizer_fingerprint', 'metadata_fingerprint', 'model_state', 'optimizer_state'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError('Malformed numerical checkpoint')
    constants = dict(schema_version=1, model_kind=MODEL_KIND, scientific_label=SCIENTIFIC_LABEL,
        selection='minimum_validation_masked_normalized_mse_earliest_tie',
        train_iteration='seeded_numpy_generator_permutation_all_origins_each_epoch',
        device='cpu', deterministic_algorithms=True, torch_threads=1)
    if any(type(payload[key]) is not type(value) or payload[key] != value for key, value in constants.items()):
        raise ValueError('Checkpoint version, model, scientific label or numerical training policy differs')
    if _identities(payload['identities']) != expected:
        raise ValueError('Checkpoint provenance identities differ')
    settings = _config(payload['config'])
    normal = payload['normalization']
    if not isinstance(normal, dict) or set(normal) != {'mean', 'scale'}:
        raise ValueError('Malformed checkpoint normalization')
    normal = _normalization(normal['mean'], normal['scale'])
    if (payload['config_fingerprint'] != fingerprint_payload(settings)
            or payload['normalization_fingerprint'] != fingerprint_payload(normal)):
        raise ValueError('Checkpoint normalization or configuration digest differs')
    record = {key: payload[key] for key in required - {'metadata_fingerprint', 'model_state', 'optimizer_state'}}
    if payload['metadata_fingerprint'] != fingerprint_payload(record):
        raise ValueError('Checkpoint metadata digest differs')
    history = payload['history']
    if not isinstance(history, list) or len(history) != settings['epochs']:
        raise ValueError('Checkpoint history does not match configured epochs')
    for epoch, entry in enumerate(history, 1):
        if (not isinstance(entry, dict) or set(entry) != {'epoch', 'training_loss', 'validation_loss',
                'train_origins', 'validation_origins', 'optimizer_steps', 'training_target_cells', 'validation_target_cells'}
                or type(entry['epoch']) is not int or entry['epoch'] != epoch
                or any(type(entry[key]) not in (int, float) or not np.isfinite(entry[key]) or entry[key] < 0
                       for key in ('training_loss', 'validation_loss'))
                or any(type(entry[key]) is not int or entry[key] < 1 for key in (
                    'train_origins', 'validation_origins', 'optimizer_steps', 'training_target_cells', 'validation_target_cells'))
                or entry['optimizer_steps'] != (entry['train_origins'] + settings['batch_size'] - 1) // settings['batch_size']):
            raise ValueError('Invalid numerical checkpoint training history')
    best = min(history, key=lambda entry: entry['validation_loss'])
    if type(payload['selected_epoch']) is not int or payload['selected_epoch'] != best['epoch']:
        raise ValueError('Checkpoint selection differs from validation monitoring')
    if (not isinstance(payload['versions'], dict) or set(payload['versions']) != {'torch', 'numpy'}
            or any(type(value) is not str or not value for value in payload['versions'].values())):
        raise ValueError('Checkpoint requires recorded numerical library versions')
    if (_state_fingerprint(payload['model_state']) != payload['weights_fingerprint']
            or _state_fingerprint(payload['optimizer_state']) != payload['optimizer_fingerprint']):
        raise ValueError('Checkpoint model or optimizer state digest differs')
    model = _model(payload['context_steps'], payload['horizon_steps'])
    try:
        model.load_state_dict(payload['model_state'], strict=True)
        optimizer = torch.optim.Adam(model.parameters(), lr=settings['learning_rate'])
        optimizer.load_state_dict(payload['optimizer_state'])
    except (ValueError, RuntimeError, KeyError, TypeError) as error:
        raise ValueError('Incompatible checkpoint model or optimizer state') from error
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    return NeuralModel(model, record, payload['optimizer_state'])
