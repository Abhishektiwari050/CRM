# Stage 1: Build React Frontend
FROM node:20-slim as frontend-builder
WORKDIR /app
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim

WORKDIR /app

# Install System Dependencies (if needed for psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 crm && chown -R crm:crm /app
USER crm

# Copy Backend Code
COPY --chown=crm:crm api/ ./api/
COPY --chown=crm:crm assets/ ./assets/
COPY --chown=crm:crm static/ ./static/
COPY --chown=crm:crm employee_dashboard_page/ ./employee_dashboard_page/
COPY --chown=crm:crm daily_work_report/ ./daily_work_report/
COPY --chown=crm:crm activity_logging_page/ ./activity_logging_page/
COPY --chown=crm:crm notifications_page/ ./notifications_page/
COPY --chown=crm:crm .env.production .env

# Copy Built Frontend
COPY --from=frontend-builder --chown=crm:crm /app/frontend/dist ./frontend/dist

# Expose Port
EXPOSE 8001

# Start Command
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "api.main:app", "--bind", "0.0.0.0:8001"]
