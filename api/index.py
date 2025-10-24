"""
Vercel Serverless Entry Point for CRM API
This is a simplified API wrapper that works in Vercel's serverless environment
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import logging

# Import backend modules
from app.database.connection import get_db, init_db
from app.models.models import User, Client, ActivityLog, UserRole
from app.middleware.auth import AuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# Create FastAPI app
app = FastAPI(
    title="Competence CRM API",
    version="1.0.0",
    description="CRM API for Vercel Serverless Deployment",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
auth_service = AuthService()


# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ClientResponse(BaseModel):
    id: str
    company_name: str
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: Optional[str]
    assigned_to_id: Optional[str]
    created_at: datetime
    updated_at: datetime


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, auth_service.secret_key, algorithms=[auth_service.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# Health check endpoint
@app.get("/")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Competence CRM API",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Authentication endpoint
@app.post("/api/auth/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    try:
        user = db.query(User).filter(User.email == login_data.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not auth_service.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )

        # Create access token
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


# Get current user info
@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
    }


# List clients
@app.get("/api/clients")
def list_clients(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List clients with optional filtering"""
    try:
        query = db.query(Client)

        # Filter based on user role
        if current_user.role == UserRole.EMPLOYEE:
            query = query.filter(Client.assigned_to_id == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            # Managers see their team's clients
            team_member_ids = (
                db.query(User.id).filter(User.manager_id == current_user.id).all()
            )
            team_ids = [str(current_user.id)] + [str(uid[0]) for uid in team_member_ids]
            query = query.filter(Client.assigned_to_id.in_(team_ids))

        # Apply filters
        if status:
            query = query.filter(Client.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Client.company_name.ilike(search_term))
                | (Client.contact_name.ilike(search_term))
                | (Client.email.ilike(search_term))
            )

        # Get results
        total = query.count()
        clients = query.offset(skip).limit(limit).all()

        return {
            "total": total,
            "clients": [
                {
                    "id": str(client.id),
                    "company_name": client.company_name,
                    "contact_name": client.contact_name,
                    "email": client.email,
                    "phone": client.phone,
                    "status": client.status,
                    "assigned_to_id": str(client.assigned_to_id)
                    if client.assigned_to_id
                    else None,
                    "created_at": client.created_at.isoformat(),
                    "updated_at": client.updated_at.isoformat(),
                }
                for client in clients
            ],
        }
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clients",
        )


# Get single client
@app.get("/api/clients/{client_id}")
def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get client by ID"""
    try:
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Check permissions
        if current_user.role == UserRole.EMPLOYEE:
            if str(client.assigned_to_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")

        return {
            "id": str(client.id),
            "company_name": client.company_name,
            "contact_name": client.contact_name,
            "email": client.email,
            "phone": client.phone,
            "status": client.status,
            "assigned_to_id": str(client.assigned_to_id)
            if client.assigned_to_id
            else None,
            "created_at": client.created_at.isoformat(),
            "updated_at": client.updated_at.isoformat(),
            "notes": client.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve client",
        )


# List activity logs
@app.get("/api/activities")
def list_activities(
    skip: int = 0,
    limit: int = 50,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List activity logs"""
    try:
        query = db.query(ActivityLog)

        # Filter by user role
        if current_user.role == UserRole.EMPLOYEE:
            query = query.filter(ActivityLog.user_id == current_user.id)

        # Filter by client if specified
        if client_id:
            query = query.filter(ActivityLog.client_id == client_id)

        # Order by most recent
        query = query.order_by(ActivityLog.created_at.desc())

        total = query.count()
        activities = query.offset(skip).limit(limit).all()

        return {
            "total": total,
            "activities": [
                {
                    "id": str(activity.id),
                    "client_id": str(activity.client_id),
                    "user_id": str(activity.user_id),
                    "activity_type": activity.activity_type,
                    "description": activity.description,
                    "created_at": activity.created_at.isoformat(),
                    "updated_at": activity.updated_at.isoformat(),
                }
                for activity in activities
            ],
        }
    except Exception as e:
        logger.error(f"Error listing activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activities",
        )


# List users (admin/manager only)
@app.get("/api/users")
def list_users(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List users (admin/manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        query = db.query(User)

        if current_user.role == UserRole.MANAGER:
            # Managers only see their team
            query = query.filter(
                (User.manager_id == current_user.id) | (User.id == current_user.id)
            )

        users = query.all()

        return {
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "is_active": user.is_active,
                }
                for user in users
            ]
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "detail": "Internal server error",
        "error": str(exc) if app.debug else "An error occurred",
    }


# For local testing
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
