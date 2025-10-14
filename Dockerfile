# Build stage - install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (cached unless pyproject.toml or uv.lock changes)
RUN uv sync --frozen --no-dev

# Runtime stage - minimal image
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
# Optimize Python startup
ENV PYTHONOPTIMIZE=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Copy and set entrypoint permissions
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Pre-collect static files during build (not at runtime)
RUN python manage.py collectstatic --noinput --clear

# Pre-compile Python files for faster startup
RUN python -m compileall -q .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE $PORT

CMD ["./entrypoint.sh"]
