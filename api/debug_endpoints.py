# Debug endpoints to test manager data fetching
# Add these to index.py to diagnose the issue

@app.get("/api/debug/manager-data")
def debug_manager_data(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        return {
            "mode": "demo",
            "employees": len([u for u in DEMO_USERS.values() if u.get("role") == "employee"]),
            "clients": len(DEMO_CLIENTS),
            "activities": len(DEMO_ACTIVITY_LOGS)
        }
    
    try:
        employees = supabase.table("users").select("id,name,email,role").eq("role", "employee").execute()
        clients = supabase.table("clients").select("id,name").execute()
        activities = supabase.table("activity_logs").select("id").execute()
        
        return {
            "mode": "production",
            "employees_count": len(employees.data or []),
            "employees": [{"id": e["id"], "name": e.get("name")} for e in (employees.data or [])],
            "clients_count": len(clients.data or []),
            "activities_count": len(activities.data or []),
            "manager_id": payload["sub"]
        }
    except Exception as e:
        logger.error(f"DEBUG_ERROR: {e}")
        return {"error": str(e), "type": type(e).__name__}
