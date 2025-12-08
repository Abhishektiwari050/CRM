"""
Dependencies for FastAPI routes
"""
from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from .utils.security import decode_token

# ============================================================================
# Authentication Dependency
# ============================================================================

async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify JWT token from Authorization header
    Returns payload with user_id and role
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = decode_token(token)
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

# ============================================================================
# Role-Based Authorization
# ============================================================================

def require_role(*allowed_roles: str):
    """Decorator to require specific roles"""
    async def role_checker(payload: dict = Depends(verify_token)) -> dict:
        user_role = payload.get("role", "")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user_role} not authorized for this action"
            )
        return payload
    return role_checker

# Manager or admin only
require_manager = require_role("manager", "admin")

# Admin only
require_admin = require_role("admin")
