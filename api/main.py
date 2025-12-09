"""
Main FastAPI application with modular routers

This is a refactored version of the original index.py file.
The original 1877-line file has been split into:
- models/ - Pydantic models
- routers/ - API endpoint modules  
- utils/ - Security and database utilities
- config.py - Configuration management
- dependencies.py - Shared dependencies

NOTE: This is a TRANSITION file. To complete the migration:
1. Uncomment router imports as they are completed
2. Remove corresponding routes from index.py
3. Test each router independently
4. When all routers are done, rename this to main.py and update START.bat
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
import logging
import time
import uuid

from .config import settings
from .routers import auth_router  # ✅ Complete
from .routers import clients_router
from .routers import activities_router
from .routers import reports_router
from .routers import users_router
from .routers import analytics_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
)
logger = logging.getLogger("crm")

# Validate configuration
try:
    settings.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Add request ID and response time headers"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    try:
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = str(duration_ms)
    except Exception:
        pass
    
    logger.info(
        f"req_id={request_id} method={request.method} "
        f"path={request.url.path} status={getattr(response, 'status_code', 0)} "
        f"duration_ms={duration_ms}"
    )
    
    return response

# ============================================================================
# Error Handlers
# ============================================================================

def _error_response(status_code: int, code: str, message: str, details: dict | None = None):
    """Standard error response format"""
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return JSONResponse(payload, status_code=status_code)

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        404: "not_found",
        401: "unauthorized",
        403: "forbidden",
        405: "method_not_allowed"
    }
    code = code_map.get(exc.status_code, "http_error")
    return _error_response(exc.status_code, code, str(exc.detail), {"path": request.url.path})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        422, "validation_error", "Request validation failed",
        {"errors": exc.errors(), "path": request.url.path}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error at {request.url.path}: {exc}", exc_info=True)
    return _error_response(
        500, "internal_error", f"Internal server error: {str(exc)}",
        {"path": request.url.path}
    )

# ============================================================================
# Register Routers
# ============================================================================

# ✅ Authentication router (complete)
app.include_router(auth_router)

# Registered routers
app.include_router(clients_router)
app.include_router(activities_router)
app.include_router(reports_router)
app.include_router(users_router)
app.include_router(analytics_router)

# ============================================================================
# Root & Health Endpoints
# ============================================================================

# ============================================================================
# Static Files & Frontend Serving
# ============================================================================

import os
from starlette.responses import FileResponse

# 1. Mount Legacy Directories
legacy_dirs = [
    "assets", "static", "employee_dashboard_page", 
    "daily_work_report", "activity_logging_page", 
    "notifications_page"
]

for dir_name in legacy_dirs:
    if os.path.exists(dir_name):
        app.mount(f"/{dir_name}", StaticFiles(directory=dir_name, html=True), name=dir_name)

# 2. Mount React Assets
if os.path.exists("frontend/dist/react-assets"):
    app.mount("/react-assets", StaticFiles(directory="frontend/dist/react-assets"), name="react-assets")

# 3. Serve React App (SPA)
@app.get("/")
async def read_root():
    return FileResponse("frontend/dist/index.html")

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Catch-all for React Router (must be last)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # If path starts with api/, return 404 (handled by routers if matched, but here if not)
    if full_path.startswith("api/"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    # Check if file exists in frontend/dist (e.g. favicon.ico)
    possible_file = os.path.join("frontend/dist", full_path)
    if os.path.exists(possible_file) and os.path.isfile(possible_file):
        return FileResponse(possible_file)

    # Otherwise serve index.html for SPA routing
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    
    return JSONResponse({"error": "Frontend not found (Run build)"}, status_code=404)

# ============================================================================
# Startup / Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Demo mode: {settings.USE_DEMO}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"{settings.APP_NAME} shutting down...")
