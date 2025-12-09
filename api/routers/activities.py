"""
Activities Router
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime
import logging
import time

from ..models import ActivityLog
from ..dependencies import verify_token
from ..utils.database import supabase
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["activities"])  # prefix is /api because endpoints are /api/activity-log and /api/activity-feed

@router.post("/activity-log")
def log_activity(activity: ActivityLog, payload = Depends(verify_token)):
    """
    Log a new activity for a client
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    if activity.follow_up_required and not activity.follow_up_due_date:
        raise HTTPException(status_code=400, detail="follow_up_due_date is required when follow_up_required is true")
    
    data = {
        "client_id": activity.client_id,
        "employee_id": payload["sub"],
        "outcome": activity.outcome,
        "notes": activity.notes,
        "category": activity.category or "contact_attempt",
        "attachments": (activity.attachments or []) + ([{"type": "contact_meta", "method": activity.contact_method, "follow_up_required": activity.follow_up_required, "due_date": activity.follow_up_due_date}] if (activity.contact_method or activity.follow_up_required or activity.follow_up_due_date) else []),
        "quantity": activity.quantity or 1,
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = supabase.table("activity_logs").insert(data).execute()
    supabase.table("clients").update({
        "last_contact_date": datetime.utcnow().isoformat(),
        "status": "Good"
    }).eq("id", activity.client_id).execute()

    # Create follow-up notification
    try:
        if activity.follow_up_required and activity.follow_up_due_date:
            supabase.table("notifications").insert({
                "user_id": payload["sub"],
                "type": "follow_up",
                "title": "Follow-up required",
                "message": f"Contact follow-up for client {activity.client_id}",
                "metadata": {"client_id": activity.client_id, "due_date": activity.follow_up_due_date, "method": activity.contact_method},
                "created_at": datetime.utcnow().isoformat()
            }).execute()
    except Exception as e:
        logger.warning(f"follow-up notification insert failed: {e}")
    
    return {"message": "Activity logged", "id": result.data[0]["id"]}

@router.get("/activity-feed")
def activity_feed(
    payload = Depends(verify_token),
    category: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get activity feed with filtering
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        logger.info(f"ACTIVITY_FEED: Fetching for {payload['sub']} role={payload['role']}")
        q = supabase.table("activity_logs").select("*", count="exact")
        if category: q = q.eq("category", category)
        if employee_id: q = q.eq("employee_id", employee_id)
        elif payload["role"] == "employee":
            q = q.eq("employee_id", payload["sub"])
        if client_id: q = q.eq("client_id", client_id)
        if date_from: q = q.gte("created_at", date_from)
        if date_to: q = q.lte("created_at", date_to)
        if search:
            q = q.or_(f"notes.ilike.%{search}%,outcome.ilike.%{search}%")
        
        res = q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        total = res.count or 0
        
        data = res.data or []
        # Enrich with client name manually to ensure reliability
        if data:
            client_ids = list(set([item["client_id"] for item in data if item.get("client_id")]))
            if client_ids:
                try:
                    cres = supabase.table("clients").select("id, name").in_("id", client_ids).execute()
                    cmap = {c["id"]: c["name"] for c in cres.data}
                    for item in data:
                        item["client_name"] = cmap.get(item["client_id"], "Unknown Client")
                except Exception as e:
                    logger.warning(f"Failed to enrich activities with client names: {e}")
                    for item in data: item["client_name"] = "Unknown Client"
        
        logger.info(f"ACTIVITY_FEED: Found {total} activities")
        return {"data": data, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"ACTIVITY_FEED: ERROR {type(e).__name__}: {e}")
        return {"data": [], "total": 0, "limit": limit, "offset": offset}
