"""Read simple local KEY=value settings without evaluation or interpolation."""
import re
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def load_environment(path, environment):
    path = Path(path)
    if not path.exists():
        return False
    pending = {}
    for number, original in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = original.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise ImproperlyConfigured(f'Invalid .env syntax on line {number}. Expected KEY=value.')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ImproperlyConfigured(f'Unclosed .env quote on line {number}.')
            value = value[1:-1]
        pending[key] = value
    for key, value in pending.items():
        environment.setdefault(key, value)
    return True
