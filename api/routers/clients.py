"""
Clients Router
"""
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile
from typing import Optional, List
from datetime import datetime, timedelta
import math
import logging
import random

from ..models import ClientCreate
from ..dependencies import verify_token, require_manager
from ..utils.database import supabase
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/clients", tags=["clients"])

@router.get("")
def list_clients(payload = Depends(verify_token), employee_id: Optional[str] = Query(None)):
    """
    List clients with status calculation
    """
    # Production mode - use Supabase
    try:
        query = supabase.table("clients").select("*")
        if payload["role"] == "employee":
            query = query.eq("assigned_employee_id", payload["sub"])    
        elif employee_id:
            query = query.eq("assigned_employee_id", employee_id)
        
        result = query.execute()
        items = result.data or []
        
        def classify(c: dict):
            # Calculate days since last contact
            last_contact = c.get("last_contact_date")
            days_since = 9999
            if last_contact:
                try:
                    # Parse last_contact_date
                    lc_dt = datetime.fromisoformat(last_contact.replace("Z", "+00:00")) if "+" in last_contact or "Z" in last_contact else datetime.fromisoformat(last_contact)
                    lc_dt = lc_dt.replace(tzinfo=None) if lc_dt.tzinfo else lc_dt
                    now = datetime.utcnow()
                    diff = (now - lc_dt).total_seconds()
                    days_since = math.floor(diff / 86400)
                except Exception:
                    pass

            # Recency Logic (User Defined)
            # Good: < 7 days
            # Due Soon: 7-14 days
            # Overdue: > 15 days (Treating as >= 15 for safety/continuity, ensuring no gap at 15)
            
            status = "overdue"
            if days_since < 7:
                status = "good" 
            elif days_since <= 14:
                status = "due_soon"
            # Else (>= 15) -> Overdue

            # Still calculate expiry days for display/sorting if needed, but NOT for status
            expiry = c.get("expiry_date")
            days_until_expiry = 9999
            if expiry:
                try:
                    if isinstance(expiry, str):
                        dt = datetime.fromisoformat(expiry.replace("Z", "+00:00")) if "+" in expiry or "Z" in expiry else datetime.fromisoformat(expiry)
                        dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    else:
                        dt = expiry
                    now = datetime.utcnow()
                    days_until_expiry = math.ceil((dt - now).total_seconds() / 86400)
                except:
                    pass

            c2 = dict(c)
            c2["days_since_contact"] = days_since
            c2["days_until_expiry"] = days_until_expiry
            c2["status"] = status
            c2["is_overdue"] = (status == "overdue")
            return c2

        enriched = [classify(c) for c in items]
        # Sort by days_until_expiry ascending (Overdue negative numbers first, then small positive, then large positive)
        enriched.sort(key=lambda x: x["days_until_expiry"])
        
        return {"data": enriched, "total": len(enriched)}
    except Exception as e:
        logger.error(f"Error loading clients: {e}")
        return {"data": [], "total": 0, "error": str(e)}

@router.get("/{client_id}")
def get_client(client_id: str, payload = Depends(verify_token)):
    """
    Get single client details
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        res = supabase.table("clients").select("*").eq("id", client_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = res.data[0]
        
        
        # Security check: If employee, ensure assigned
        role = payload.get("role", "")
        if role in ["manager", "admin"]:
            pass
        elif client.get("assigned_employee_id") != payload["sub"]:
             raise HTTPException(status_code=403, detail="Not authorized to view this client")
        
        # Classify status (reuse logic if possible, or just duplicate for now to be safe)
        last_contact = client.get("last_contact_date")
        days_since = 9999
        if last_contact:
            try:
                lc_dt = datetime.fromisoformat(last_contact.replace("Z", "+00:00")) if "+" in last_contact or "Z" in last_contact else datetime.fromisoformat(last_contact)
                lc_dt = lc_dt.replace(tzinfo=None) if lc_dt.tzinfo else lc_dt
                diff = (datetime.utcnow() - lc_dt).total_seconds()
                days_since = math.floor(diff / 86400)
            except: pass
            
        status = "overdue"
        if days_since < 7: status = "good"
        elif days_since <= 14: status = "due_soon"
        
        client["status"] = status
        client["days_since_contact"] = days_since
        
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def create_client(client: ClientCreate, payload = Depends(verify_token)):
    """
    Create a new client
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Auto-assign if creator is an employee
        assigned_id = None
        role = payload.get("role", "")
        if role == "employee":
            assigned_id = payload["sub"]

        data = {
            "name": client.name,
            "member_id": client.member_id or None,
            "city": client.city or None,
            "products_posted": client.products_posted or 0,
            "expiry_date": client.expiry_date if client.expiry_date else None,
            "contact_email": client.email or None,
            "contact_phone": client.phone or None,
            "status": "new",
            "last_contact_date": None,
            "assigned_employee_id": assigned_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("clients").insert(data).execute()
        
        # Log assignment history if auto-assigned
        if assigned_id and result.data:
             try:
                client_id = result.data[0]["id"]
                supabase.table("client_assignment_history").insert({
                    "client_id": client_id,
                    "assigned_to_employee_id": assigned_id,
                    "changed_by_user_id": payload["sub"],
                    "reason": "self_created",
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
             except Exception as h_err:
                 logger.warning(f"History insert failed for self-created client: {h_err}")

        logger.info(f"Client created: {result.data}")
        return {"message": "Client created", "data": result.data[0] if result.data else None}
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/assign")
def assign_client(client_id: str, body: dict, payload = Depends(require_manager)):
    """
    Assign client to an employee
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    employee_id = body.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    
    supabase.table("clients").update({"assigned_employee_id": employee_id}).eq("id", client_id).execute()
    try:
        supabase.table("client_assignment_history").insert({
            "client_id": client_id,
            "assigned_to_employee_id": employee_id,
            "changed_by_user_id": payload["sub"],
            "reason": "manual_assign",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.warning(f"assignment_history insert failed (client {client_id} -> {employee_id}): {e}")
    return {"message": "Client assigned"}

@router.delete("/{client_id}")
def delete_client(client_id: str, payload = Depends(require_manager)):
    """
    Delete a client
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = supabase.table("clients").delete().eq("id", client_id).execute()
        logger.info(f"Client deleted: {client_id}")
        return {"message": "Client deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{client_id}")
def update_client(client_id: str, client: dict, payload = Depends(verify_token)):
    """
    Update client details
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Check if client exists
        res = supabase.table("clients").select("*").eq("id", client_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        current_client = res.data[0]
        role = payload.get("role", "")
        
        # Access Control
        if role == "employee":
            # Allow employees to update if assigned to them
            if current_client.get("assigned_employee_id") != payload["sub"]:
                 raise HTTPException(status_code=403, detail="Not authorized to update this client")
        elif role not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        allowed_fields = ["name", "member_id", "city", "products_posted", "expiry_date", "contact_email", "contact_phone", "status", "last_contact_date", "assigned_employee_id"]
        
        # Restrict employees from changing assignment
        if role == "employee" and "assigned_employee_id" in client:
            del client["assigned_employee_id"]

        data = {k: v for k, v in client.items() if k in allowed_fields}
        
        # Sanitize data types
        if "expiry_date" in data and data["expiry_date"] == "":
            data["expiry_date"] = None
        if "assigned_employee_id" in data and data["assigned_employee_id"] == "":
             data["assigned_employee_id"] = None
        
        if not data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
            
        result = supabase.table("clients").update(data).eq("id", client_id).execute()
        
        if not result.data:
            logger.error(f"Update returned no data for client {client_id}. Data: {data}")
            raise HTTPException(status_code=500, detail="Update failed at database level")

        logger.info(f"Client updated: {client_id}")
        return {"message": "Client updated", "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/bulk-create")
def bulk_create_clients(body: dict, payload = Depends(require_manager)):
    """
    Bulk create dummy clients for testing
    """
    count = body.get("count", 0)
    if count < 1 or count > 500:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 500")
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        clients = []
        batch_data = []
        cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"]
        
        for i in range(1, count + 1):
            data = {
                "name": f"Client {i}",
                "member_id": f"MEM{str(i).zfill(5)}",
                "city": cities[i % len(cities)],
                "products_posted": random.randint(50, 500),
                "expiry_date": (datetime.utcnow() + timedelta(days=random.randint(30, 365))).date().isoformat(),
                "contact_email": f"client{i}@example.com",
                "contact_phone": f"+91-{random.randint(7000000000, 9999999999)}",
                "status": "new",
                "last_contact_date": None,
                "created_at": datetime.utcnow().isoformat()
            }
            batch_data.append(data)
            
            # Insert in batches of 50
            if len(batch_data) >= 50 or i == count:
                result = supabase.table("clients").insert(batch_data).execute()
                if result.data:
                    clients.extend(result.data)
                    logger.info(f"Inserted batch: {len(result.data)} clients")
                batch_data = []
        
        logger.info(f"Total clients created: {len(clients)}")
        return {"message": f"Created {len(clients)} clients", "count": len(clients)}
    except Exception as e:
        logger.error(f"Error bulk creating clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-import-csv")
async def bulk_import_csv(file: UploadFile = File(...), payload = Depends(require_manager)):
    """
    Import clients from CSV file
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        import csv
        import io
        content = await file.read()
        text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        
        clients = []
        for row in reader:
            data = {
                "name": row.get("name", "").strip(),
                "member_id": row.get("member_id", "").strip() or None,
                "city": row.get("city", "").strip() or None,
                "products_posted": int(row.get("products_posted", 0) or 0),
                "expiry_date": row.get("expiry_date", "").strip() or None,
                "contact_email": row.get("email", "").strip() or None,
                "contact_phone": row.get("phone", "").strip() or None,
                "status": "new",
                "last_contact_date": None,
                "created_at": datetime.utcnow().isoformat()
            }
            if data["name"]:
                clients.append(data)
        
        if not clients:
            raise HTTPException(status_code=400, detail="No valid clients found in CSV")
        
        # Insert in batches
        batch_size = 50
        inserted = []
        for i in range(0, len(clients), batch_size):
            batch = clients[i:i+batch_size]
            result = supabase.table("clients").insert(batch).execute()
            if result.data:
                inserted.extend(result.data)
        
        return {"message": f"Imported {len(inserted)} clients", "count": len(inserted)}
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-assign")
def bulk_assign_clients(body: dict, payload = Depends(require_manager)):
    """
    Bulk assign clients to an employee
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    client_ids = body.get("client_ids", [])
    employee_id = body.get("employee_id")
    if not client_ids or not employee_id:
        raise HTTPException(status_code=400, detail="client_ids and employee_id required")
    
    for cid in client_ids:
        supabase.table("clients").update({"assigned_employee_id": employee_id}).eq("id", cid).execute()
        try:
            supabase.table("client_assignment_history").insert({
                "client_id": cid,
                "assigned_to_employee_id": employee_id,
                "changed_by_user_id": payload["sub"],
                "reason": "bulk_assign",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"assignment_history insert failed (bulk {cid} -> {employee_id}): {e}")
    
    return {"message": f"Assigned {len(client_ids)} clients", "count": len(client_ids)}

@router.post("/assign-round-robin")
def assign_round_robin(body: dict, payload = Depends(require_manager)):
    """
    Assign clients in round-robin fashion
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")

    client_ids: List[str] = body.get("client_ids", [])
    employees = supabase.table("users").select("id").eq("role", "employee").execute().data or []
    if not employees:
        raise HTTPException(status_code=400, detail="No employees available")

    if not client_ids:
        # If no explicit list, take all unassigned
        client_ids = [c["id"] for c in supabase.table("clients").select("id").is_('assigned_employee_id', "null").execute().data or []]

    assigned_count = {}
    for i, cid in enumerate(client_ids):
        to_emp = employees[i % len(employees)]["id"]
        # Fetch current assignment for history
        from_emp = (supabase.table("clients").select("assigned_employee_id").eq("id", cid).execute().data or [{}])[0].get("assigned_employee_id")
        
        supabase.table("clients").update({"assigned_employee_id": to_emp, "updated_at": datetime.utcnow().isoformat()}).eq("id", cid).execute()
        try:
            supabase.table("client_assignment_history").insert({
                "client_id": cid,
                "assigned_from_employee_id": from_emp,
                "assigned_to_employee_id": to_emp,
                "changed_by_user_id": payload["sub"],
                "reason": body.get("reason", "round_robin"),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"assignment_history insert failed (rr {cid} {from_emp}->{to_emp}): {e}")
        assigned_count[to_emp] = assigned_count.get(to_emp, 0) + 1
    
    return {"message": "Assigned", "summary": assigned_count}
