#!/bin/bash
# Exit on error
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
exec gunicorn evoting.wsgi:application --bind 0.0.0.0:8000