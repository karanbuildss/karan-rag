#!/usr/bin/env bash
set -eu

python backend/manage.py migrate --noinput
python backend/manage.py seed_demo_data
python backend/manage.py import_reviewed_budget_facts
python backend/manage.py detect_anomalies

exec gunicorn \
  --chdir backend \
  config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120
