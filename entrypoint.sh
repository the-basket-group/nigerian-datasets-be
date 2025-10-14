#!/bin/bash
set -e

# Check if migrations are needed (only on first deployment or when migrations change)
if python manage.py migrate --check > /dev/null 2>&1; then
    echo "✓ Database is up to date, skipping migrations"
else
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

echo "Starting server..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 8 \
    --timeout 120 \
    --worker-class gthread \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 50
