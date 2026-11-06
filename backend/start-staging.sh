#!/bin/sh
set -eu

cd /app
python manage.py collectstatic --noinput
python manage.py migrate --noinput
exec gunicorn EatHub.wsgi:application --bind "0.0.0.0:${PORT}" --workers 1 --threads 4 --timeout 120
