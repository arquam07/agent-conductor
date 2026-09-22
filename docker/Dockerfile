# Multi-stage build. One image serves both API and worker (different commands).
# Stage 1: build deps into a venv with uv. Stage 2: slim runtime, non-root.

FROM python:3.12-slim AS builder

# uv: fast, reproducible installs from the lockfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy only dependency manifests first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install deps into a project-local venv, no dev deps, frozen to the lock
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: runtime
FROM python:3.12-slim

# Non-root user
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Bring the built venv over from the builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# App code
COPY app ./app

USER appuser

# Default command runs the API; compose/K8s override for the worker.
# 0.0.0.0 so the container is reachable; port 8000.
CMD ["python", "-m", "app.api.main", "--host", "0.0.0.0", "--port", "8000"]