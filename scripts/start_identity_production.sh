#!/usr/bin/env bash
set -eu

exec gunicorn \
  --chdir mock-identity-server \
  app.wsgi:application \
  --bind "0.0.0.0:${PORT:-8001}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --timeout 60
