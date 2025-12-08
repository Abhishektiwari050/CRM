"""
Pydantic models for the CRM API
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ============================================================================
# Authentication Models
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# ============================================================================
# User Models
# ============================================================================

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "employee"

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    role: str
    status: str = "active"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
