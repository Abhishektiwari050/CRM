"""
Client-related Pydantic models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class ClientCreate(BaseModel):
    name: str
    member_id: Optional[str] = None
    city: Optional[str] = None
    products_posted: Optional[int] = 0
    expiry_date: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    member_id: Optional[str] = None
    city: Optional[str] = None
    products_posted: Optional[int] = None
    expiry_date: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    assigned_employee_id: Optional[str] = None

class ClientAssignment(BaseModel):
    employee_id: str

class Client(BaseModel):
    id: str
    name: str
    member_id: Optional[str] = None
    city: Optional[str] = None
    products_posted: int = 0
    expiry_date: Optional[date] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    assigned_employee_id: Optional[str] = None
    status: str = "new"
    last_contact_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Computed fields
    days_since_last_contact: Optional[int] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True
