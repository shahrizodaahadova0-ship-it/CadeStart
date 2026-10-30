#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements-render-free.txt
python manage.py collectstatic --noinput
