# syntax=docker/dockerfile:1
# Production image for the Metro backend (Django + Channels, served over ASGI).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=metro.settings

# libmagic1 -> python-magic (file type detection); curl -> container healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

# Koyeb/Render/Fly inject $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

# X-Forwarded-Proto header so the check isn't 301'd by SECURE_SSL_REDIRECT in prod.
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -fsS -H "X-Forwarded-Proto: https" "http://localhost:${PORT}/health/" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
