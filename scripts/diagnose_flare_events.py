"""Describe exposed frozen forecast errors, without training or rule selection."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

from solar_flare_jepa.events.diagnostics import diagnose_frozen
from solar_flare_jepa.events.frozen import read_json


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=root/'configs/events/january2025_frozen.json')
    parser.add_argument('--forecast-root', type=Path, required=True)
    parser.add_argument('--label-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not output.is_relative_to((root/'results').resolve()):
        parser.error('Output must be inside this worktree results/')
    if output.exists():
        parser.error('Refusing to overwrite output')
    result = diagnose_frozen(read_json(args.config), dict(
        forecasts=args.forecast_root, preparation=args.label_root))
    result['config_sha256'] = hashlib.sha256(args.config.read_bytes()).hexdigest()
    import solar_flare_jepa.events as package
    directory = Path(package.__file__).parent
    result['executed_source_sha256'] = {name: hashlib.sha256((directory/name).read_bytes()).hexdigest()
        for name in ('diagnostics.py', 'frozen.py', 'labels.py', 'matching.py', 'scoring.py')}
    result['runtime'] = dict(python=platform.python_version(), numpy=__import__('numpy').__version__)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(output), claim=result['claim'], origins=result['origin_count'])))


if __name__ == '__main__':
    main()
