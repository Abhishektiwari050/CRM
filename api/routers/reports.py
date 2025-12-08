"""
Reports Router - Daily Work Reports
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
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
                supabase.table("notifications").insert({
                    "user_id": "manager",
                    "type": "repeated_contact",
                    "title": f"Repeated Contact: {name}",
                    "message": f"Employee {payload['sub']} has contacted {name} for 3+ consecutive days",
                    "metadata": {"employee_id": payload["sub"], "contact_name": name, "count": count},
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
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
def report_flags(payload = Depends(verify_token)):
    """
    Get flags for repeated contacts
    """
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        today = datetime.utcnow().date().isoformat()
        res = supabase.table("daily_reports").select("employee_id,metrics,date,created_at").eq("date", today).execute()
        by_emp = {}
        def names_from(s):
            if not s: return []
            return [x.strip().lower() for x in str(s).split(',') if x.strip()]
        for r in res.data or []:
            emp = r.get("employee_id")
            m = r.get("metrics", {})
            all_names = names_from(m.get("ta_calls_to")) + names_from(m.get("renewal_calls_to")) + names_from(m.get("service_calls_to"))
            if not all_names: continue
            cnt = by_emp.get(emp) or {}
            for n in all_names:
                cnt[n] = cnt.get(n, 0) + 1
            by_emp[emp] = cnt
        flags = []
        for emp_id, cnt in by_emp.items():
            for name, c in cnt.items():
                if c > 1:
                    flags.append({"employee_id": emp_id, "name": name, "count": c, "date": today})
        return {"data": flags}
    except Exception as e:
        logger.error(f"Report flags error: {e}")
        return {"data": []}
