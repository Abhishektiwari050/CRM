"""
Routers package for modularized API endpoints
"""
from .auth import router as auth_router
from .clients import router as clients_router
from .activities import router as activities_router
from .reports import router as reports_router
from .users import router as users_router
from .analytics import router as analytics_router

# Export all routers
__all__ = [
    "auth_router",
    "clients_router",
    "activities_router",
    "reports_router",
    "users_router",
    "analytics_router",
]
