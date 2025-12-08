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
COPY --chown=crm:crm assets/ ./assets/
COPY --chown=crm:crm login_page/ ./login_page/
COPY --chown=crm:crm manager_dashboard_page/ ./manager_dashboard_page/
COPY --chown=crm:crm employee_dashboard_page/ ./employee_dashboard_page/
COPY --chown=crm:crm management_page/ ./management_page/
COPY --chown=crm:crm notifications_page/ ./notifications_page/
COPY --chown=crm:crm reports_page/ ./reports_page/
COPY --chown=crm:crm daily_work_report/ ./daily_work_report/
COPY --chown=crm:crm activity_logging_page/ ./activity_logging_page/
COPY --chown=crm:crm server.py .
COPY --chown=crm:crm index.html .
COPY --chown=crm:crm start.sh .

COPY --chown=crm:crm .env.production .env

# Update PATH
ENV PATH=/home/crm/.local/bin:$PATH

# Switch to non-root user
USER crm

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3000/api/health')"

# Run application via start script
CMD ["./start.sh"]
