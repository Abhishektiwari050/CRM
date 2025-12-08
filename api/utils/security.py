"""
Security utilities: password hashing, JWT tokens
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from ..config import settings

# ============================================================================
# Password Hashing
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# ============================================================================
# JWT Token Management
# ============================================================================

def create_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT token for a user"""
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "user_id": user_id, # Keep for backward compatibility during transition
        "role": role,
        "exp": expire
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

def decode_token(token: str) -> Dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
