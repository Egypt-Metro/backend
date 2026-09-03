#!/bin/sh
# Container entrypoint: apply DB migrations, refresh static files, then serve.
set -e

echo "==> Running database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

# Single worker so the in-memory Channels layer works without Redis.
# Set REDIS_URL and raise --workers to scale to multiple processes.
echo "==> Starting uvicorn on :${PORT:-8000}"
exec uvicorn metro.asgi:application \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --proxy-headers \
    --forwarded-allow-ips="*"
