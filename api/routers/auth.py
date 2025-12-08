"""
Authentication routes: login, refresh, profile management
"""
from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import Optional
import time
import logging
from collections import defaultdict, deque

from ..models import LoginRequest, ProfileUpdate, PasswordChange, TokenResponse
from ..dependencies import verify_token
from ..utils import hash_password, verify_password, create_token
from ..utils.database import supabase
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Login rate limiting (simple in-memory, per-IP)
_login_attempts: defaultdict[str, deque] = defaultdict(deque)
_failed_login_events: deque = deque()

def _check_login_rate_limit(ip: str):
    """Check if IP has exceeded login rate limit"""
    now = time.time()
    dq = _login_attempts[ip]
    # Drop old attempts
    while dq and (now - dq[0]) > settings.LOGIN_RATE_WINDOW:
        dq.popleft()
    if len(dq) >= settings.LOGIN_RATE_MAX:
        retry_after = max(1, int(settings.LOGIN_RATE_WINDOW - (now - dq[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after}s"
        )
    dq.append(now)

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request):
    """
    Authenticate user and return JWT token
    """
    ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(ip)
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured"
        )
    
    try:
        result = supabase.table("users").select("*").eq("email", req.email).execute()
        logger.info(f"Login attempt for {req.email}: Found {len(result.data or [])} users")

        if not result.data:
            _failed_login_events.append(time.time())
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user = result.data[0]
        ph = user.get("password_hash", "")
        
        if not ph.startswith(("$2a$", "$2b$", "$2y$")) or not verify_password(req.password, ph):
            _failed_login_events.append(time.time())
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        logger.info(f"Login successful: {user['name']} ({user['role']})")
        token = create_token(user["id"], user["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh")
def refresh_token(payload = Depends(verify_token)):
    """
    Refresh JWT token if expiring soon
    """
    exp = payload.get("exp")
    if exp and (exp - time.time()) < 86400:  # Less than 24h remaining
        user_id = payload.get("sub") or payload.get("user_id")
        role = payload.get("role")
        return {
            "access_token": create_token(user_id, role),
            "token_type": "bearer"
        }
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token still valid"
    )

@router.get("/me")
def get_me(payload = Depends(verify_token)):
    """
    Get current user information
    """
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured"
        )
    
    user_id = payload.get("sub") or payload.get("user_id")
    result = supabase.table("users").select("id,name,email,role").eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return result.data[0]

@router.put("/profile")
def update_profile(profile: ProfileUpdate, payload = Depends(verify_token)):
    """
    Update user profile (name, email)
    """
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured"
        )
    
    update_data = {}
    user_id = payload.get("sub") or payload.get("user_id")
    
    if profile.name:
        update_data["name"] = profile.name
    
    if profile.email:
        # Check if email already in use
        existing = supabase.table("users").select("id").eq("email", profile.email).neq("id", user_id).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        update_data["email"] = profile.email
    
    if update_data:
        supabase.table("users").update(update_data).eq("id", user_id).execute()
    
    return {"message": "Profile updated"}

@router.put("/password")
def change_password(pwd: PasswordChange, payload = Depends(verify_token)):
    """
    Change user password
    """
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured"
        )
    
    user_id = payload.get("sub") or payload.get("user_id")
    user = supabase.table("users").select("password_hash").eq("id", user_id).execute()
    
    if not user.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not verify_password(pwd.old_password, user.data[0]["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password incorrect"
        )
    
    new_hash = hash_password(pwd.new_password)
    supabase.table("users").update({"password_hash": new_hash}).eq("id", user_id).execute()
    
    return {"message": "Password changed"}
