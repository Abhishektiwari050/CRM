"""
Users & Employees Router
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional, List
from datetime import datetime
import logging
import math

from ..models import EmployeeCreate
from ..dependencies import verify_token, require_manager, require_admin
from ..utils.database import supabase
from ..utils import hash_password
from ..config import settings

logger = logging.getLogger(__name__)
# Again, prefix is generic /api because of legacy route naming
router = APIRouter(prefix="/api", tags=["users"])

@router.get("/users")
def list_users(payload = Depends(require_manager)):
    """
    List all users (employees and managers)
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        logger.info(f"LIST_USERS: Fetching for {payload['sub']}")
        result = supabase.table("users").select("id,name,email,role,status,created_at").execute()
        users = result.data or []
        logger.info(f"LIST_USERS: Found {len(users)} users")
        return {"data": users, "total": len(users)}
    except Exception as e:
        logger.error(f"LIST_USERS: ERROR {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/employees")
def create_employee(emp: EmployeeCreate, payload = Depends(require_manager)):
    """
    Create a new employee
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        existing = supabase.table("users").select("id").eq("email", emp.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        data = {
            "name": emp.name,
            "email": emp.email,
            "password_hash": hash_password(emp.password),
            "role": "employee",
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("users").insert(data).execute()
        logger.info(f"Employee created: {result.data}")
        return {"message": "Employee created", "data": result.data[0] if result.data else None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/users/{user_id}")
def delete_user(user_id: str, payload = Depends(require_manager)):
    """
    Delete a user
    """
    if user_id == payload["sub"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = supabase.table("users").delete().eq("id", user_id).execute()
        logger.info(f"User deleted: {user_id}")
        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee/stats")
def employee_stats(payload = Depends(verify_token)):
    """
    Get stats for the currently logged in employee
    """
    if payload["role"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access only")
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    # Production mode - use Supabase
    result = supabase.table("clients").select("*").eq("assigned_employee_id", payload["sub"]).execute()
    clients = result.data or []
    total = len(clients)
    
    def parse_dt(s):
        try:
            if isinstance(s, str):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00")) if "+" in s or "Z" in s else datetime.fromisoformat(s)
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
            return s
        except Exception:
            return None
    
    good_count = 0
    due_soon_count = 0
    overdue_count = 0
    
    for c in clients:
        lcd = c.get("last_contact_date")
        days = 999
        if lcd:
            dt = parse_dt(lcd)
            if dt:
                days = max(0, int((datetime.utcnow() - dt).total_seconds() / 86400))
        
        if days <= 7:
            good_count += 1
        elif days <= 14:
            due_soon_count += 1
        else:
            overdue_count += 1
    
    return {
        "total_clients": total,
        "good_clients": good_count,
        "due_soon_clients": due_soon_count,
        "overdue_clients": overdue_count
    }

@router.get("/debug/employee-clients/{employee_id}")
def debug_employee_clients(employee_id: str, payload = Depends(verify_token)):
    """
    Debug endpoint to check clients assigned to an employee
    """
    if not supabase:
         raise HTTPException(status_code=503, detail="Database not configured")
         
    result = supabase.table("clients").select("id,name").eq("assigned_employee_id", employee_id).execute()
    clients = result.data or []
    return {
        "employee_id": employee_id,
        "total_clients": len(clients),
        "clients": clients
    }

@router.get("/notifications")
def get_notifications(payload = Depends(verify_token)):
    """
    Get user notifications
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        # Fetch notifications for this user or 'all'
        # Assuming table 'notifications' has 'user_id' column
        user_id = payload["sub"]
        
        # Simple query for now
        res = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(50).execute()
        return {"data": res.data or []}
    except Exception as e:
        logger.error(f"Error loading notifications: {e}")
        return {"data": []}
