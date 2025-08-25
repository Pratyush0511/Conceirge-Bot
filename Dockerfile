# Multi-stage build for production-ready Flask application
# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Add metadata
LABEL maintainer="AI Customer Service Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="ai-customer-service" \
      org.label-schema.description="Multi-Channel AI Customer Service System" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0"

# Install build dependencies and system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    libhdf5-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies with binary wheels
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install --no-cache-dir --prefer-binary --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    dumb-init \
    libopenblas-dev \
    liblapack-dev \
    libgfortran5 \
    python3-numpy \
    python3-scipy \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -g 1001 appgroup \
    && useradd -u 1001 -g appgroup -m appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/instance /app/uploads/documents /app/logs \
    && chown -R appuser:appgroup /app

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    FLASK_DEBUG=False \
    PORT=5000

# Expose port
EXPOSE 5000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Switch to non-root user
USER appuser

# Use dumb-init to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Default command
CMD ["python", "start.py"]

# Alternative commands for different deployment scenarios:
# For Gunicorn (recommended for production):
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "run:app"]
# For development:
# CMD ["python", "run.py"]
# For Celery worker:
# CMD ["celery", "-A", "celery_worker.celery", "worker", "--loglevel=info"]