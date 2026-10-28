#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements-render.txt
python manage.py collectstatic --noinput
# The persistent disk is unavailable during build. Migrate at runtime instead.
