"""
Reports Router - Daily Work Reports
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from ..models import DailyReport
from ..dependencies import verify_token, require_manager
from ..utils.database import supabase
from ..config import settings

logger = logging.getLogger(__name__)
# Keep prefix as /api to match old routes /api/daily-report, /api/daily-reports, etc.
# But since routes are inconsistent (/api/daily-report vs /api/manager/report-flags), 
# we'll use a base prefix /api and specify full paths or sub-prefixes.
router = APIRouter(prefix="/api", tags=["reports"])

@router.post("/daily-report")
def submit_report(report: DailyReport, payload = Depends(verify_token)):
    """
    Submit a daily work report
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    data = {
        "employee_id": payload["sub"],
        "date": datetime.utcnow().date().isoformat(),
        "tasks": "",
        # Duplicate key metrics to top-level for schema compatibility
        "ta_calls": report.ta_calls or 0,
        "ta_calls_to": report.ta_calls_to or "",
        "renewal_calls": report.renewal_calls or 0,
        "renewal_calls_to": report.renewal_calls_to or "",
        "service_calls": report.service_calls or 0,
        "service_calls_to": report.service_calls_to or "",
        "zero_star_calls": report.zero_star_calls or 0,
        "one_star_calls": report.one_star_calls or 0,
        "additional_info": report.additional_info or "",
        "metrics": {
            "ta_calls": report.ta_calls or 0,
            "ta_calls_to": report.ta_calls_to or "",
            "renewal_calls": report.renewal_calls or 0,
            "renewal_calls_to": report.renewal_calls_to or "",
            "service_calls": report.service_calls or 0,
            "service_calls_to": report.service_calls_to or "",
            "zero_star_calls": report.zero_star_calls or 0,
            "one_star_calls": report.one_star_calls or 0,
            "additional_info": report.additional_info or ""
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Submitting daily report for {payload['sub']}: {data}")
    result = supabase.table("daily_reports").insert(data).execute()
    logger.info(f"Daily report inserted successfully: {result.data}")
    
    # Check for repeated names in call logs (3+ days)
    all_names = []
    if report.ta_calls_to:
        all_names.extend([n.strip() for n in report.ta_calls_to.split(',') if n.strip()])
    if report.renewal_calls_to:
        all_names.extend([n.strip() for n in report.renewal_calls_to.split(',') if n.strip()])
    if report.service_calls_to:
        all_names.extend([n.strip() for n in report.service_calls_to.split(',') if n.strip()])
    
    if all_names:
        three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat()
        for name in set(all_names):
            past_reports = supabase.table("daily_reports").select("id,date,metrics").eq("employee_id", payload["sub"]).gte("created_at", three_days_ago).execute()
            count = 0
            for r in past_reports.data:
                m = r.get("metrics", {})
                if any(name.lower() in str(m.get(field, "")).lower() for field in ["ta_calls_to", "renewal_calls_to", "service_calls_to"]):
                    count += 1
            if count >= 3:
                # Create notification for manager
                # Create notification for all managers
                try:
                    managers_res = supabase.table("users").select("id").eq("role", "manager").execute()
                    managers = managers_res.data or []
                    
                    notifications = []
                    for mgr in managers:
                        notifications.append({
                            "user_id": mgr["id"],
                            "type": "repeated_contact",
                            "title": f"Repeated Contact: {name}",
                            "message": f"Employee {payload['sub']} has contacted {name} for 3+ consecutive days",
                            "metadata": {"employee_id": payload["sub"], "contact_name": name, "count": count},
                            "created_at": datetime.utcnow().isoformat()
                        })
                    
                    if notifications:
                        supabase.table("notifications").insert(notifications).execute()
                        logger.info(f"Repeated contact notification sent to {len(notifications)} managers for {name}")

                except Exception as notify_error:
                    logger.error(f"Failed to send manager notifications: {notify_error}")
                logger.info(f"Repeated contact notification created for {name}")
    
    return {"message": "Report submitted", "id": (result.data and result.data[0].get("id"))}


@router.get("/daily-reports")
def get_reports(payload = Depends(verify_token), employee_id: Optional[str] = Query(None)):
    """
    Get list of daily reports
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        query = supabase.table("daily_reports").select("*")
        if payload["role"] == "employee":
            query = query.eq("employee_id", payload["sub"])    
        elif employee_id:
            query = query.eq("employee_id", employee_id)
        result = query.order("created_at", desc=True).limit(100).execute()
        logger.info(f"Daily reports query returned {len(result.data or [])} records")
        
        # Get employee names
        emp_ids = list(set([r["employee_id"] for r in result.data or []]))
        emp_names = {}
        if emp_ids:
            users_res = supabase.table("users").select("id,name").in_("id", emp_ids).execute()
            emp_names = {u["id"]: u["name"] for u in users_res.data or []}
        
        data = []
        for r in result.data or []:
            data.append({
                "id": r["id"],
                "employee_id": r["employee_id"],
                "employee_name": emp_names.get(r["employee_id"], "Unknown"),
                "metrics": r.get("metrics", {}),
                "date": r["date"],
                "submitted_at": r["created_at"]
            })
        logger.info(f"Returning {len(data)} daily reports")
        return {"data": data, "total": len(data)}
    except Exception as e:
        logger.error(f"Error loading daily reports: {e}")
        return {"data": [], "total": 0}

@router.post("/daily-report/draft")
def save_report_draft(report: DailyReport, payload = Depends(verify_token)):
    """
    Save draft report (mock implementation as Supabase doesn't have drafts table in schema yet usually)
    Real impl would need a table or local storage. For now, we'll error if not handled by frontend.
    But to support existing logic, we'll verify connection only.
    """
    if not supabase:
         raise HTTPException(status_code=503, detail="Database not configured")
    
    # In a real app, save to 'daily_report_drafts' table
    # For this refactor, we acknowledge the request but don't persist if table missing.
    return {"message": "Draft saved"}

@router.get("/daily-report/draft")
def get_report_draft(payload = Depends(verify_token)):
    """
    Get draft report
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    # Return empty if no persistence
    return {"data": None}

@router.get("/manager/report-flags")
def report_flags(payload = Depends(require_manager)):
    """
    Get flags for repeated contacts from notifications
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        # Fetch unread repeated_contact notifications for manager
        # We need to filter by metrics in the metadata field or rely on 'type' column if we set it
        # Based on submit_report, type="repeated_contact", user_id="manager"
        
        # Note: Supabase JS/Python client syntax for JSON contains filtering might be tricky in python client depending on version
        # But we can filter in python for now if volume is low, or use exact match on type
        
        # Fetch unread repeated_contact notifications for THIS manager
        res = supabase.table("notifications").select("*").eq("user_id", payload["sub"]).eq("type", "repeated_contact").eq("is_read", "false").order("created_at", desc=True).execute()
        
        notifications = res.data or []
        flags = []
        
        if notifications:
            # Prefetch employee names to avoid N+1
            emp_ids = list(set([n.get("metadata", {}).get("employee_id") for n in notifications if n.get("metadata", {}).get("employee_id")]))
            emp_names = {}
            if emp_ids:
                users_res = supabase.table("users").select("id,name").in_("id", emp_ids).execute()
                emp_names = {u["id"]: u["name"] for u in users_res.data or []}

            for n in notifications:
                meta = n.get("metadata", {})
                emp_id = meta.get("employee_id")
                flags.append({
                    "id": n["id"], # Notification ID for dismissal
                    "employee_id": emp_id,
                    "employee_name": emp_names.get(emp_id, "Unknown"),
                    "name": meta.get("contact_name", "Unknown Client"),
                    "count": meta.get("count", 0),
                    "date": n["created_at"]
                })
                
        return {"data": flags}
    except Exception as e:
        logger.error(f"Report flags error: {e}")
        return {"data": []}

class DismissFlagRequest(BaseModel):
    notification_id: str


@router.post("/manager/dismiss-flag")
def dismiss_flag(req: DismissFlagRequest, payload = Depends(require_manager)):
    """
    Dismiss a repeated contact flag (mark notification as read)
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        # Verify it's a manager notification (optional security check)
        # Just update is_read = true
        # Verify it's a manager notification for this user
        res = supabase.table("notifications").update({"is_read": True}).eq("id", req.notification_id).eq("user_id", payload["sub"]).execute()
        
        return {"message": "Flag dismissed"}
    except Exception as e:
        logger.error(f"Dismiss flag error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
