#!/bin/bash
set -e

# Only run migrations if RUN_MIGRATIONS env var is set (for deployment time only)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Skipping migrations (RUN_MIGRATIONS not set)"
fi

echo "Starting server..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --worker-class gthread --threads 4
