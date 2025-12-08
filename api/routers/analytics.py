"""
Analytics & Exports Router
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from ..dependencies import verify_token, require_manager
from ..utils.database import supabase
from ..config import settings

logger = logging.getLogger(__name__)
# Keep prefix as /api to match old routes
router = APIRouter(prefix="/api", tags=["analytics"])

@router.get("/manager/stats")
def manager_stats(payload = Depends(require_manager)):
    """
    Get dashboard top-level stats
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        employees = supabase.table("users").select("id", count="exact").eq("role", "employee").execute()
        emp_count = employees.count or 0
        
        clients_res = supabase.table("clients").select("id,expiry_date,last_contact_date").execute()
        data = clients_res.data or []
        total = len(data)
        
        now = datetime.utcnow()
        overdue_count = 0
        for c in data:
            # New Logic: Overdue if last_contact_date is > 30 days ago or None
            last_contact = c.get("last_contact_date")
            is_overdue = True # Default to overdue (Never contacted)
            
            if last_contact:
                try:
                    dt = datetime.fromisoformat(last_contact.replace("Z", "+00:00")) if "+" in last_contact or "Z" in last_contact else datetime.fromisoformat(last_contact)
                    dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    diff_days = (now - dt).days
                    if diff_days <= 30:
                        is_overdue = False # Contacted recently (Good or Due Soon is considered "Not Overdue" for efficiency calc?)
                        # Actually efficiency usually penalizes overdue. 
                        # If status is "Due Soon" (15-30 days), is that "Overdue"?
                        # Usually Overdue means > 30.
                        # So if diff <= 30, it is NOT overdue.
                except:
                    pass
            
            if is_overdue:
                overdue_count += 1
        
        efficiency = round((total - overdue_count) / total * 100) if total > 0 else 0
        return {"employees": emp_count, "clients": total, "overdue": overdue_count, "efficiency": efficiency}
    except Exception as e:
        logger.error(f"Error loading stats: {e}")
        return {"employees": 0, "clients": 0, "overdue": 0, "efficiency": 0}

@router.get("/manager/employee-performance")
def employee_performance(payload = Depends(require_manager)):
    """
    Get detailed employee performance table
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        employees_res = supabase.table("users").select("id,name,email").eq("role", "employee").execute()
        employees = employees_res.data or []
        
        clients_res = supabase.table("clients").select("id,assigned_employee_id,expiry_date").execute()
        clients = clients_res.data or []
        
        week_ago = (datetime.utcnow() - timedelta(days=7))
        activities_res = supabase.table("activity_logs").select("id,employee_id").gte("created_at", week_ago.isoformat()).execute()
        activities = activities_res.data or []
        
        assigned_map = {}
        overdue_map = {}
        now = datetime.utcnow()
        
        for c in clients:
            emp_id = c.get("assigned_employee_id")
            if not emp_id: continue
            assigned_map[emp_id] = assigned_map.get(emp_id, 0) + 1
            
            expiry = c.get("expiry_date")
            if expiry:
                try:
                    if isinstance(expiry, str):
                        dt = datetime.fromisoformat(expiry.replace("Z", "+00:00")) if "+" in expiry or "Z" in expiry else datetime.fromisoformat(expiry)
                        dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    else: dt = expiry
                    if dt < now: overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1
                except: pass
        
        activity_map = {}
        for a in activities:
            emp_id = a.get("employee_id")
            if emp_id: activity_map[emp_id] = activity_map.get(emp_id, 0) + 1
            
        data = []
        for e in employees:
            assigned = assigned_map.get(e["id"], 0)
            overdue_count = overdue_map.get(e["id"], 0)
            efficiency = round((assigned - overdue_count) / assigned * 100) if assigned > 0 else 100
            data.append({
                "id": e["id"],
                "name": e.get("name", "Unknown"),
                "email": e.get("email", ""),
                "assigned_clients": assigned,
                "overdue_clients": overdue_count,
                "activities_this_week": activity_map.get(e["id"], 0),
                "efficiency": efficiency
            })
        return {"data": data}
    except Exception as e:
        logger.error(f"Error loading performance: {e}")
        return {"data": []}

@router.get("/manager/alerts")
def manager_alerts(payload = Depends(require_manager)):
    """
    Get system alerts
    """
    if not supabase:
        return {"data": []}
    
    alerts = []
    try:
        # Check for highly overdue clients
        clients = supabase.table("clients").select("expiry_date").execute()
        overdue = 0
        now = datetime.utcnow()
        for c in clients.data or []:
            expiry = c.get("expiry_date")
            if expiry:
                try:
                    dt = datetime.fromisoformat(expiry.replace("Z", "+00:00")).replace(tzinfo=None)
                    if (now - dt).days > 30:
                        overdue += 1
                except:
                    pass
        
        if overdue > 0:
            alerts.append({
                "type": "critical" if overdue > 10 else "warning",
                "title": f"{overdue} Long-Overdue Clients",
                "message": "Clients overdue by more than 30 days require immediate attention."
            })
            
        # Check for low activity (example)
    except Exception as e:
        logger.error(f"Error generating alerts: {e}")
        
    return {"data": alerts}

@router.get("/manager/workload-distribution")
def workload_distribution(payload = Depends(require_manager)):
    """
    Get workload distribution (clients and activity) per employee
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        logger.info(f"WORKLOAD: Fetching for {payload['sub']}")
        employees_res = supabase.table("users").select("id,name").eq("role", "employee").execute()
        employees = employees_res.data or []
        logger.info(f"WORKLOAD: Found {len(employees)} employees")
        
        clients_res = supabase.table("clients").select("id,assigned_employee_id").execute()
        clients = clients_res.data or []
        logger.info(f"WORKLOAD: Found {len(clients)} clients")
        
        assigned_map = {}
        for c in clients:
            emp_id = c.get("assigned_employee_id")
            if emp_id:
                assigned_map[emp_id] = assigned_map.get(emp_id, 0) + 1
        
        today = datetime.utcnow().date().isoformat()
        activities_res = supabase.table("activity_logs").select("id,employee_id,created_at").gte("created_at", today).execute()
        activities = activities_res.data or []
        logger.info(f"WORKLOAD: Found {len(activities)} activities today")
        
        postings_map = {}
        for a in activities:
            emp_id = a.get("employee_id")
            if emp_id:
                postings_map[emp_id] = postings_map.get(emp_id, 0) + 1
        
        data = []
        for e in employees:
            data.append({
                "employee_id": e["id"],
                "name": e["name"],
                "assigned_clients": assigned_map.get(e["id"], 0),
                "postings_today": postings_map.get(e["id"], 0)
            })
        
        logger.info(f"WORKLOAD: Returning {len(data)} employees")
        return {"data": data}
    except Exception as e:
        logger.error(f"WORKLOAD: ERROR {type(e).__name__}: {e}")
        return {"data": []}

@router.get("/export/clients")
def export_clients(payload = Depends(require_manager)):
    """
    Export all clients to CSV
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        res = supabase.table("clients").select("*").execute()
        rows = ["id,name,member_id,city,products_posted,expiry_date,contact_email,contact_phone,assigned_employee_id,status,last_contact_date,created_at"]
        
        for c in res.data or []:
            row = [
                str(c.get('id', '')),
                str(c.get('name', '')).replace(',', ';'),
                str(c.get('member_id', '')),
                str(c.get('city', '')),
                str(c.get('products_posted', '')),
                str(c.get('expiry_date', '')),
                str(c.get('contact_email', '')),
                str(c.get('contact_phone', '')),
                str(c.get('assigned_employee_id', '')),
                str(c.get('status', '')),
                str(c.get('last_contact_date', '')),
                str(c.get('created_at', ''))
            ]
            rows.append(','.join(row))
        
        return PlainTextResponse(content="\n".join(rows), media_type="text/csv")
    except Exception as e:
        logger.error(f"Error exporting clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/daily-reports")
def export_daily_reports(payload = Depends(require_manager)):
    """
    Export daily reports to CSV
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        res = supabase.table("daily_reports").select("*").order("date", desc=True).limit(1000).execute()
        rows = ["id,employee_id,date,ta_calls,ta_calls_to,renewal_calls,renewal_calls_to,service_calls,service_calls_to,zero_star_calls,one_star_calls,additional_info,submitted_at"]
        
        for r in res.data or []:
            m = r.get("metrics") or {}
            row = [
                str(r.get('id', '')),
                str(r.get('employee_id', '')),
                str(r.get('date', '')),
                str(m.get('ta_calls', '')),
                str(m.get('ta_calls_to', '')).replace(',', ';'),
                str(m.get('renewal_calls', '')),
                str(m.get('renewal_calls_to', '')).replace(',', ';'),
                str(m.get('service_calls', '')),
                str(m.get('service_calls_to', '')).replace(',', ';'),
                str(m.get('zero_star_calls', '')),
                str(m.get('one_star_calls', '')),
                str(m.get('additional_info', '')).replace(',', ';'),
                str(r.get('created_at', ''))
            ]
            rows.append(','.join(row))
        
        return PlainTextResponse(content="\n".join(rows), media_type="text/csv")
    except Exception as e:
        logger.error(f"Error exporting daily reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/activities")
def export_activities(payload = Depends(require_manager)):
    """
    Export activity logs to CSV
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        res = supabase.table("activity_logs").select("*").order("created_at", desc=True).limit(1000).execute()
        rows = ["id,client_id,employee_id,category,outcome,notes,quantity,method,follow_up_due,created_at"]
        
        for r in res.data or []:
            method = ""
            follow_due = ""
            try:
                atts = r.get('attachments') or []
                meta = next((a for a in atts if isinstance(a, dict) and a.get('type') == 'contact_meta'), None)
                if meta:
                    method = str(meta.get('method') or '')
                    follow_due = str(meta.get('due_date') or '')
            except Exception:
                pass
            row = [
                str(r.get('id', '')),
                str(r.get('client_id', '')),
                str(r.get('employee_id', '')),
                str(r.get('category', '')),
                str(r.get('outcome', '')),
                str(r.get('notes', '')).replace(',', ';'),
                str(r.get('quantity', '')),
                method.replace(',', ';'),
                follow_due,
                str(r.get('created_at', ''))
            ]
            rows.append(','.join(row))
        
        return PlainTextResponse(content="\n".join(rows), media_type="text/csv")
    except Exception as e:
        logger.error(f"Error exporting activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
