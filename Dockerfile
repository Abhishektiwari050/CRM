# Production Dockerfile - Multi-stage build
FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 crm && \
    chown -R crm:crm /app

# Copy dependencies from builder
COPY --from=builder --chown=crm:crm /root/.local /home/crm/.local

# Copy application
COPY --chown=crm:crm api/ ./api/
COPY --chown=crm:crm static/ ./static/
COPY --chown=crm:crm .env.production .env

# Update PATH
ENV PATH=/home/crm/.local/bin:$PATH

# Switch to non-root user
USER crm

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/api/health')"

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
