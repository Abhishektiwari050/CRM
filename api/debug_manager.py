from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
import logging

router = APIRouter()
logger = logging.getLogger("crm")

def verify_token(authorization: str = None):
    # Import from dependencies
    from api.dependencies import verify_token as main_verify
    return main_verify(authorization)

@router.get("/api/debug/manager-full")
def debug_manager_full(payload = Depends(verify_token)):
    from api.utils.database import supabase
    
    if not supabase:
        return {"error": "Supabase not configured"}
    
    try:
        # Test 1: Count employees
        emp_res = supabase.table("users").select("id,name,email,role").eq("role", "employee").execute()
        employees = emp_res.data or []
        
        # Test 2: Count clients
        client_res = supabase.table("clients").select("id,name,assigned_employee_id,last_contact_date").execute()
        clients = client_res.data or []
        
        # Test 3: Count activities
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        act_res = supabase.table("activity_logs").select("id,employee_id,created_at").gte("created_at", week_ago).execute()
        activities = act_res.data or []
        
        # Test 4: Count daily reports
        today = datetime.utcnow().date().isoformat()
        report_res = supabase.table("daily_reports").select("id,employee_id,date").eq("date", today).execute()
        reports = report_res.data or []
        
        return {
            "manager_id": payload["sub"],
            "manager_role": payload["role"],
            "employees": {
                "count": len(employees),
                "sample": employees[:3] if employees else []
            },
            "clients": {
                "count": len(clients),
                "sample": clients[:3] if clients else []
            },
            "activities": {
                "count": len(activities),
                "sample": activities[:3] if activities else []
            },
            "reports": {
                "count": len(reports),
                "sample": reports[:3] if reports else []
            }
        }
    except Exception as e:
        logger.error(f"Debug manager full error: {e}")
        return {"error": str(e), "type": type(e).__name__}
