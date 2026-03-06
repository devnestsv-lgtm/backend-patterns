# ===============================
# PRODUCTION DEPLOYMENT DOCKERFILE
# ===============================
# This image is optimized for deployment:
# - Multi-stage build reduces final image size.
# - Runs as non-root user.
# - Uses gunicorn + uvicorn workers for production serving.

# ===============================
# BUILDER STAGE
# ===============================
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt /build/requirements.txt

# Install dependencies into a dedicated prefix so we can copy them cleanly.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r /build/requirements.txt && \
    pip install --no-cache-dir --prefix=/install gunicorn==23.0.0

# ===============================
# RUNTIME STAGE
# ===============================
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for container hardening.
RUN useradd -u 10001 -m appuser

WORKDIR /app

# Copy python dependencies from builder layer.
COPY --from=builder /install /usr/local

# Copy only runtime-required project files.
COPY app /app/app
COPY scripts /app/scripts
COPY requirements.txt /app/requirements.txt

# Environment defaults for production.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

# Drop root privileges.
USER appuser

# Production application server command.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "app.main:app"]
