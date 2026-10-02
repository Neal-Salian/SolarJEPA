"""Normal installed entry points must work without pytest's src injection."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def clean_environment():
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def test_normal_installed_import_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, '-B', '-c', 'import solar_flare_jepa'],
        cwd=tmp_path, env=clean_environment(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('script', [
    'download_data.py', 'inspect_data.py', 'preprocess.py', 'eda.py', 'register_aditya.py',
    'validate_solexs.py',
])
def test_existing_cli_help_without_pythonpath(tmp_path, script):
    result = subprocess.run(
        [sys.executable, '-B', str(ROOT / 'scripts' / script), '--help'],
        cwd=tmp_path, env=clean_environment(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'usage:' in result.stdout
