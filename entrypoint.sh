#!/bin/bash
set -e

echo "Running database migrations..."
uv run python manage.py migrate --noinput

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

echo "Starting server..."
exec uv run gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
