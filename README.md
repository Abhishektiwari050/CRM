# Competence CRM

System overview, key architectural decisions, implementation highlights, performance improvements, setup and deployment instructions, and known limitations.

## System Overview
Competence CRM supports three roles: `admin`, `manager`, `employee`. Managers create and assign clients to employees. Employees log client contacts and submit daily work reports. Dashboards show status groups: `overdue` (>14d), `due_soon` (8–14d), `good` (≤7d).

## Key Architectural Decisions
- Modular FastAPI application with standardized error handling and JWT auth.
- In-memory demo mode when Supabase is not configured.
- Performance middleware with request IDs and response time headers.
- Backend-derived status classification and unified calculation rules.
- Event-based UI refresh via `localStorage` for real-time sync.

## Implementation Highlights
- `/api/clients` returns enriched fields: `days_since_last_contact`, `status`, `is_overdue`.
- `/api/activity-log` updates client `last_contact_date`.
- Manager analytics: stats, performance, alerts, workload distribution.
- DWR autosave with server-side drafts and manager archive.
- Round-robin auto-assignment endpoint for unassigned clients.

## Performance Improvements
- Response-time instrumentation headers: `X-Request-ID`, `X-Response-Time-ms`.
- Client list caching with short TTL.
- Reduced blocking UI by rendering from cache and refreshing asynchronously.

## Setup and Deployment
1. `pip install -r api/requirements.txt`
2. Start backend: `python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001`
3. Start UI proxy: `python server.py` (serves UI and proxies `/api/*`)
4. Configure Supabase via environment variables to use production mode.

## Known Limitations
- Demo mode uses in-memory data; restart resets state.
- Round-robin assignment is demo-only; production requires DB writes.

## CI and Tests
- GitHub Actions run unit tests, coverage, and Bandit security scan.

