from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, File, UploadFile
from fastapi.responses import PlainTextResponse, HTMLResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
import logging
from datetime import datetime, timedelta, date
import jwt
import random
from supabase import create_client, Client
import bcrypt
import secrets
import time
import math
from collections import deque, defaultdict
from dotenv import load_dotenv
import psycopg2
import uuid
 

load_dotenv()
logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("crm")

app = FastAPI()

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()] if allowed_origins_env else (["*"] if os.getenv("APP_ENV", "development").lower() in ("development", "test") else [])
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

# Health endpoint inline
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Competence CRM API"}

@app.get("/")
def root():
    return FileResponse("login_page/code.html")



# Simple in-memory cache
CACHE = {"clients": {}}
CACHE_TTL_SECONDS = 0  # Disabled for real-time sync

@app.middleware("http")
async def perf_middleware(request, call_next):
    rid = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    dur = int((time.time() - start) * 1000)
    try:
        response.headers["X-Request-ID"] = rid
        response.headers["X-Response-Time-ms"] = str(dur)
    except Exception:
        pass
    logger.info(f"req_id={rid} method={request.method} path={request.url.path} status={getattr(response, 'status_code', 0)} duration_ms={dur}")
    return response

# Consistent error response helpers and handlers
def _error_response(status_code: int, code: str, message: str, details: dict | None = None):
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return JSONResponse(payload, status_code=status_code)

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    status = exc.status_code
    code_map = {404: "not_found", 401: "unauthorized", 403: "forbidden", 405: "method_not_allowed"}
    code = code_map.get(status, "http_error")
    detail = str(getattr(exc, "detail", "HTTP error"))
    return _error_response(status, code, detail, {"path": request.url.path})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    status = exc.status_code
    code_map = {404: "not_found", 401: "unauthorized", 403: "forbidden", 422: "validation_error", 503: "service_unavailable"}
    code = code_map.get(status, "http_error")
    detail = str(getattr(exc, "detail", "HTTP error"))
    return _error_response(status, code, detail, {"path": request.url.path})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(422, "validation_error", "Request validation failed", {"errors": exc.errors(), "path": request.url.path})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error at {request.url.path}: {exc}")
    return _error_response(500, "internal_error", "Internal server error", {"path": request.url.path})

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# JWT secret: require env in production, generate ephemeral in dev if missing
APP_ENV = os.getenv("APP_ENV", "development").lower()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    if APP_ENV not in ("development", "test"):
        raise RuntimeError("JWT_SECRET must be set in production")
    # Ephemeral dev secret (tokens invalidated on restart)
    JWT_SECRET = secrets.token_urlsafe(32)

USE_DEMO = str(os.getenv("USE_DEMO", "1")).lower() in ("1", "true", "yes")
# Initialize Supabase client (disabled if USE_DEMO)
try:
    supabase: Client = None if USE_DEMO else (create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None)
    if supabase:
        # Test connection
        supabase.table("users").select("id").limit(1).execute()
        logger.info("Supabase connected successfully")
    else:
        logger.info("Demo mode active (Supabase disabled or not configured)")
except Exception as e:
    logger.error(f"Supabase connection failed: {e}")
    supabase = None
DEMO_ACTIVITY_LOGS = []
DEMO_DAILY_REPORTS = []
DEMO_DAILY_REPORT_DRAFTS = {}
# Initialize demo clients with explicit assignments to John Doe (demo-employee-1)
DEMO_CLIENTS = [
    {
        "id": "demo-client-1", 
        "name": "ABC Corporation", 
        "member_id": "ABC001", 
        "city": "New York", 
        "products_posted": 5, 
        "expiry_date": "2024-12-31", 
        "contact_email": "contact@abc.com", 
        "email": "contact@abc.com", 
        "phone": "555-0101", 
        "assigned_employee_id": "demo-employee-1",
        "last_contact_date": (datetime.utcnow() - timedelta(days=4)).isoformat()
    },
    {
        "id": "demo-client-2", 
        "name": "XYZ Industries", 
        "member_id": "XYZ002", 
        "city": "Los Angeles", 
        "products_posted": 3, 
        "expiry_date": "2024-11-30", 
        "contact_email": "info@xyz.com", 
        "email": "info@xyz.com", 
        "phone": "555-0102", 
        "assigned_employee_id": "demo-employee-1",
        "last_contact_date": (datetime.utcnow() - timedelta(days=11)).isoformat()
    },
    {
        "id": "demo-client-3", 
        "name": "Global Services", 
        "member_id": "GLO003", 
        "city": "Chicago", 
        "products_posted": 8, 
        "expiry_date": "2025-01-15", 
        "contact_email": "hello@global.com", 
        "email": "hello@global.com", 
        "phone": "555-0103", 
        "assigned_employee_id": "demo-employee-1",
        "last_contact_date": (datetime.utcnow() - timedelta(days=21)).isoformat()
    }
]

# Demo users for development mode when Supabase is not configured
DEMO_USERS = {
    "john@crm.com": {
        "id": "demo-employee-1",
        "name": "John Doe",
        "email": "john@crm.com",
        "role": "employee",
        "password": "password123",
        "password_hash": "$2b$12$LyFo6ban81LS4BYWUu0f3ei8uaK.HQwsqh1rzcBLv8BJMzExnLzeK"  # password123
    },
    "manager@crm.com": {
        "id": "demo-manager-1",
        "name": "Jane Smith",
        "email": "manager@crm.com",
        "role": "manager",
        "password": "password123",
        "password_hash": "$2b$12$LyFo6ban81LS4BYWUu0f3ei8uaK.HQwsqh1rzcBLv8BJMzExnLzeK"  # password123
    }
}

# Demo data validation and logging
def _validate_demo_data():
    try:
        print(f"DEMO MODE: Validating demo data...")
        print(f"DEMO_USERS: {len(DEMO_USERS)} users")
        for email, user in DEMO_USERS.items():
            print(f"  - {email}: {user['name']} ({user['role']}) ID: {user['id']}")
        
        print(f"DEMO_CLIENTS: {len(DEMO_CLIENTS)} clients")
        for client in DEMO_CLIENTS:
            print(f"  - {client['name']}: assigned to {client.get('assigned_employee_id', 'UNASSIGNED')}")
        
        # Verify John Doe has clients assigned
        john_clients = [c for c in DEMO_CLIENTS if c.get('assigned_employee_id') == 'demo-employee-1']
        print(f"John Doe (demo-employee-1) has {len(john_clients)} clients assigned")
        
    except Exception as e:
        print(f"Demo data validation error: {e}")

if not supabase:
    print("Running in DEMO MODE - no Supabase connection")
    _validate_demo_data()

# Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ClientCreate(BaseModel):
    name: str
    member_id: Optional[str] = None
    city: Optional[str] = None
    products_posted: Optional[int] = 0
    expiry_date: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    


class ActivityLog(BaseModel):
    client_id: str
    outcome: str
    notes: Optional[str] = None
    category: Optional[str] = None
    attachments: Optional[List[dict]] = None
    quantity: Optional[int] = 1
    contact_method: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_due_date: Optional[str] = None
    


class DailyReport(BaseModel):
    ta_calls: Optional[int] = None
    ta_calls_to: Optional[str] = None
    renewal_calls: Optional[int] = None
    renewal_calls_to: Optional[str] = None
    service_calls: Optional[int] = None
    service_calls_to: Optional[str] = None
    zero_star_calls: Optional[int] = None
    one_star_calls: Optional[int] = None
    additional_info: Optional[str] = None
    


class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# Auth Helper
def create_token(user_id: str, role: str, expires_delta: timedelta = timedelta(days=7)) -> str:
    payload = {"sub": user_id, "role": role, "exp": datetime.utcnow() + expires_delta, "iat": datetime.utcnow()}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

DB_URL = os.getenv("DATABASE_URL")
PG_USER = os.getenv("user")
PG_PASSWORD = os.getenv("password")
PG_HOST = os.getenv("host")
PG_PORT = os.getenv("port")
PG_DBNAME = os.getenv("dbname")

def _pg_conn():
    if DB_URL:
        return psycopg2.connect(DB_URL)
    if PG_USER and PG_PASSWORD and PG_HOST and PG_PORT and PG_DBNAME:
        return psycopg2.connect(user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT, dbname=PG_DBNAME)
    raise Exception("database_config_missing")

try:
    c = None
    c = _pg_conn()
    cur = c.cursor()
    cur.execute("SELECT NOW();")
    _ = cur.fetchone()
    cur.close()
    c.close()
    logger.info("Postgres connected successfully")
except Exception as e:
    logger.warning(f"Postgres connection failed: {e}")

@app.get("/api/db/check")
def db_check(payload = Depends(verify_token)):
    try:
        c = _pg_conn()
        cur = c.cursor()
        cur.execute("SELECT NOW();")
        row = cur.fetchone()
        cur.close()
        c.close()
        return {"ok": True, "time": str(row[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Login rate limiting (simple in-memory, per-IP)
RATE_LIMIT_WINDOW_SEC = int(os.getenv("LOGIN_RATE_WINDOW", "60"))
RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("LOGIN_RATE_MAX", "10"))
_login_attempts: defaultdict[str, deque] = defaultdict(deque)
_failed_login_events: deque = deque()

def _check_login_rate_limit(ip: str):
    now = time.time()
    dq = _login_attempts[ip]
    # drop old attempts
    while dq and (now - dq[0]) > RATE_LIMIT_WINDOW_SEC:
        dq.popleft()
    if len(dq) >= RATE_LIMIT_MAX_ATTEMPTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SEC - (now - dq[0])))
        raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again in {retry_after}s")
    dq.append(now)

# Routes
@app.get("/")
def root():
    return {"status": "healthy", "service": "Competence CRM API"}

@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(ip)
    
    # Demo mode - use hardcoded users when Supabase is not configured
    if not supabase:
        logger.info(f"Demo mode login attempt for: {req.email}")
        demo_user = DEMO_USERS.get(req.email)
        
        if not demo_user:
            _failed_login_events.append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(req.password, demo_user["password_hash"]):
            _failed_login_events.append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        logger.info(f"Demo login successful: {demo_user['name']} ({demo_user['role']})")
        token = create_token(demo_user["id"], demo_user["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": demo_user["id"], "name": demo_user["name"], "email": demo_user["email"], "role": demo_user["role"]}
        }
    
    # Production mode - use Supabase
    try:
        result = supabase.table("users").select("*").eq("email", req.email).execute()
        logger.info(f"Login attempt for {req.email}: Found {len(result.data or [])} users")

        if not result.data:
            # Dev/test fallback to demo users even when Supabase is configured
            if APP_ENV in ("development", "test") and req.email in DEMO_USERS:
                demo_user = DEMO_USERS[req.email]
                if verify_password(req.password, demo_user["password_hash"]):
                    logger.info(f"Dev fallback login successful: {demo_user['name']} ({demo_user['role']})")
                    token = create_token(demo_user["id"], demo_user["role"]) 
                    return {
                        "access_token": token,
                        "token_type": "bearer",
                        "user": {"id": demo_user["id"], "name": demo_user["name"], "email": demo_user["email"], "role": demo_user["role"]}
                    }
            _failed_login_events.append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = result.data[0]
        ph = user.get("password_hash", "")
        
        if not ph.startswith(("$2a$", "$2b$", "$2y$")) or not verify_password(req.password, ph):
            _failed_login_events.append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        logger.info(f"Login successful: {user['name']} ({user['role']})")
        token = create_token(user["id"], user["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/refresh")
def refresh_token(payload = Depends(verify_token)):
    exp = payload.get("exp")
    if exp and (exp - time.time()) < 86400:
        return {"access_token": create_token(payload["sub"], payload["role"]), "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Token still valid")

@app.get("/api/auth/me")
def get_me(payload = Depends(verify_token)):
    # Demo mode - return hardcoded user data
    if not supabase:
        user_id = payload["sub"]
        # Find user by ID in demo users
        for demo_user in DEMO_USERS.values():
            if demo_user["id"] == user_id:
                return {"id": demo_user["id"], "name": demo_user["name"], "email": demo_user["email"], "role": demo_user["role"]}
        raise HTTPException(status_code=404, detail="User not found")
    
    # Production mode - use Supabase
    result = supabase.table("users").select("id,name,email,role").eq("id", payload["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@app.put("/api/profile")
def update_profile(profile: ProfileUpdate, payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    update_data = {}
    if profile.name:
        update_data["name"] = profile.name
    if profile.email:
        existing = supabase.table("users").select("id").eq("email", profile.email).neq("id", payload["sub"]).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = profile.email
    
    if update_data:
        supabase.table("users").update(update_data).eq("id", payload["sub"]).execute()
    return {"message": "Profile updated"}

@app.put("/api/profile/password")
def change_password(pwd: PasswordChange, payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    user = supabase.table("users").select("password_hash").eq("id", payload["sub"]).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(pwd.old_password, user.data[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password incorrect")
    
    new_hash = hash_password(pwd.new_password)
    supabase.table("users").update({"password_hash": new_hash}).eq("id", payload["sub"]).execute()
    return {"message": "Password changed"}

@app.get("/api/clients")
def list_clients(payload = Depends(verify_token), employee_id: Optional[str] = Query(None)):
    if not supabase:
        cache_key = f"{payload['role']}:{payload['sub']}:{employee_id or ''}"
        now = time.time()
        entry = CACHE["clients"].get(cache_key)
        if entry and now - entry["time"] < CACHE_TTL_SECONDS:
            return {"data": entry["data"], "total": len(entry["data"])}
        
        # Start with all demo clients
        base = DEMO_CLIENTS[:]
        
        # Filter based on role and parameters
        if payload["role"] == "employee":
            # Employee can only see their assigned clients
            base = [c for c in base if c.get("assigned_employee_id") == payload["sub"]]
            print(f"DEBUG: Employee {payload['sub']} requesting clients, found {len(base)} assigned clients")
            print(f"DEBUG: All clients: {[(c['name'], c.get('assigned_employee_id')) for c in DEMO_CLIENTS]}")
        elif employee_id:
            # Manager requesting specific employee's clients
            base = [c for c in base if c.get("assigned_employee_id") == employee_id]
            print(f"DEBUG: Manager requesting employee {employee_id} clients, found {len(base)} clients")
        else:
            # Manager requesting all clients
            print(f"DEBUG: Manager requesting all clients, found {len(base)} clients")
        
        def classify(c: dict):
            lcd = c.get("last_contact_date")
            days = 999
            if lcd:
                try:
                    if "Z" in lcd or "+" in lcd:
                        dt = datetime.fromisoformat(lcd.replace("Z", "+00:00"))
                        days = max(0, math.ceil((datetime.utcnow().replace(tzinfo=dt.tzinfo) - dt).total_seconds() / 86400))
                    else:
                        dt = datetime.fromisoformat(lcd)
                        days = max(0, math.ceil((datetime.utcnow() - dt).total_seconds() / 86400))
                except Exception as e:
                    logger.warning(f"Date parse error for {c.get('name')}: {lcd} - {e}")
                    days = 999
            status = "good" if days <= 7 else ("due_soon" if days <= 14 else "overdue")
            c2 = dict(c)
            c2["days_since_last_contact"] = days
            c2["status"] = status
            c2["is_overdue"] = (status == "overdue")
            return c2
        
        enriched = [classify(c) for c in base]
        CACHE["clients"][cache_key] = {"data": enriched, "time": now}
        print(f"DEBUG: Returning {len(enriched)} enriched clients for {payload['role']} {payload['sub']}")
        return {"data": enriched, "total": len(enriched)}
    
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
            lcd = c.get("last_contact_date")
            days = 999
            if lcd:
                try:
                    if isinstance(lcd, str):
                        dt = datetime.fromisoformat(lcd.replace("Z", "+00:00")) if "+" in lcd or "Z" in lcd else datetime.fromisoformat(lcd)
                        dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    else:
                        dt = lcd
                    now = datetime.utcnow()
                    diff_seconds = (now - dt).total_seconds()
                    days = max(0, int(diff_seconds / 86400))
                    logger.info(f"Client {c.get('name')}: lcd={lcd}, dt={dt}, now={now}, diff_sec={diff_seconds}, days={days}")
                except Exception as e:
                    logger.warning(f"Date parse error for {c.get('name')}: {lcd} - {e}")
                    days = 999
            status = "good" if days <= 7 else ("due_soon" if days <= 14 else "overdue")
            c2 = dict(c)
            c2["days_since_last_contact"] = days
            c2["status"] = status
            c2["is_overdue"] = (status == "overdue")
            return c2
        enriched = [classify(c) for c in items]
        return {"data": enriched, "total": len(enriched)}
    except Exception as e:
        print(f"Error loading clients: {e}")
        return {"data": [], "total": 0, "error": str(e)}

@app.post("/api/clients")
def create_client(client: ClientCreate, payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
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
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("clients").insert(data).execute()
        print(f"Client created: {result.data}")
        return {"message": "Client created", "data": result.data[0] if result.data else None}
    except Exception as e:
        print(f"Error creating client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clients/{client_id}/assign")
def assign_client(client_id: str, body: dict, payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
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

@app.post("/api/activity-log")
def log_activity(activity: ActivityLog, payload = Depends(verify_token)):
    if not supabase:
        data = {
            "id": f"demo-act-{int(time.time()*1000)}",
            "client_id": activity.client_id,
            "employee_id": payload["sub"],
            "outcome": activity.outcome,
            "notes": activity.notes,
            "category": activity.category or "contact_attempt",
            "attachments": (activity.attachments or []) + ([{"type": "contact_meta", "method": activity.contact_method, "follow_up_required": activity.follow_up_required, "due_date": activity.follow_up_due_date}] if (activity.contact_method or activity.follow_up_required or activity.follow_up_due_date) else []),
            "quantity": activity.quantity or 1,
            "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        }
        DEMO_ACTIVITY_LOGS.insert(0, data)
        for i, c in enumerate(DEMO_CLIENTS):
            if c.get("id") == activity.client_id:
                DEMO_CLIENTS[i] = {**c, "last_contact_date": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}
                break
        return {"message": "Activity logged", "id": data["id"]}
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
    supabase.table("clients").update({"last_contact_date": datetime.utcnow().isoformat()}).eq("id", activity.client_id).execute()

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

@app.get("/api/activity-feed")
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
    if not supabase:
        items = DEMO_ACTIVITY_LOGS[:]
        if category:
            items = [x for x in items if x.get("category") == category]
        if employee_id:
            items = [x for x in items if x.get("employee_id") == employee_id]
        elif payload["role"] == "employee":
            items = [x for x in items if x.get("employee_id") == payload["sub"]]
        if client_id:
            items = [x for x in items if x.get("client_id") == client_id]
        if date_from:
            items = [x for x in items if x.get("created_at") and x.get("created_at") >= date_from]
        if date_to:
            items = [x for x in items if x.get("created_at") and x.get("created_at") <= date_to]
        if search:
            s = search.lower()
            items = [x for x in items if (str(x.get("notes") or '').lower().find(s) >= 0) or (str(x.get("outcome") or '').lower().find(s) >= 0)]
        total = len(items)
        items = items[offset:offset+limit]
        return {"data": items, "total": total, "limit": limit, "offset": offset}

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
    
    return {"data": res.data or [], "total": total, "limit": limit, "offset": offset}

@app.post("/api/daily-report")
def submit_report(report: DailyReport, payload = Depends(verify_token)):
    if not supabase:
        data = {
            "id": f"demo-dmr-{int(time.time()*1000)}",
            "employee_id": payload["sub"],
            "date": datetime.utcnow().date().isoformat(),
            "tasks": "",
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
            "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        }
        DEMO_DAILY_REPORTS.insert(0, data)
        logger.info(f"Submitting daily report for {payload['sub']}")
        return {"message": "Report submitted", "id": data["id"]}
    
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
    try:
        result = supabase.table("daily_reports").insert(data).execute()
        logger.info(f"Daily report inserted successfully: {result.data}")
    except Exception as e:
        logger.error(f"daily_reports insert failed: {e}")
        # Fallback: record as an activity log to ensure visibility on dashboard
        try:
            supabase.table("activity_logs").insert({
                "client_id": None,
                "employee_id": payload["sub"],
                "category": "daily_report",
                "outcome": "submitted",
                "notes": data.get("additional_info", ""),
                "attachments": [],
                "quantity": (data.get("ta_calls") or 0) + (data.get("renewal_calls") or 0) + (data.get("service_calls") or 0),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            result = type("Res", (), {"data": [{"id": None}]})
        except Exception as e2:
            logger.error(f"activity_logs fallback failed: {e2}")
            raise HTTPException(status_code=500, detail="Report logging failed")
    
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



@app.get("/api/daily-reports")
def get_reports(payload = Depends(verify_token), employee_id: Optional[str] = Query(None)):
    def demo_reports():
        items = DEMO_DAILY_REPORTS[:]
        if payload["role"] == "employee":
            items = [x for x in items if x.get("employee_id") == payload["sub"]]
        elif employee_id:
            items = [x for x in items if x.get("employee_id") == employee_id]
        data = []
        for r in items:
            metrics = r.get("metrics", {})
            data.append({
                "id": r.get("id"),
                "employee_id": r.get("employee_id"),
                "employee_name": "Employee",
                "metrics": metrics,
                "date": r.get("date"),
                "submitted_at": r.get("created_at")
            })
        return {"data": data, "total": len(data)}
    if not supabase:
        return demo_reports()
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
        return demo_reports()

@app.post("/api/daily-report/draft")
def save_report_draft(report: DailyReport, payload = Depends(verify_token)):
    key = f"{payload['sub']}:{datetime.utcnow().date().isoformat()}"
    if not supabase:
        DEMO_DAILY_REPORT_DRAFTS[key] = {
            "employee_id": payload["sub"],
            "date": datetime.utcnow().date().isoformat(),
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
            "updated_at": datetime.utcnow().isoformat()
        }
        return {"message": "Draft saved"}
    raise HTTPException(status_code=503, detail="Database not configured")

@app.get("/api/daily-report/draft")
def get_report_draft(payload = Depends(verify_token)):
    key = f"{payload['sub']}:{datetime.utcnow().date().isoformat()}"
    if not supabase:
        draft = DEMO_DAILY_REPORT_DRAFTS.get(key)
        return {"data": draft}
    raise HTTPException(status_code=503, detail="Database not configured")

@app.get("/api/debug/employee-clients/{employee_id}")
def debug_employee_clients(employee_id: str, payload = Depends(verify_token)):
    if not supabase:
        assigned_clients = [c for c in DEMO_CLIENTS if c.get("assigned_employee_id") == employee_id]
        return {
            "employee_id": employee_id,
            "total_clients": len(DEMO_CLIENTS),
            "assigned_clients": len(assigned_clients),
            "clients": [{"id": c["id"], "name": c["name"], "assigned_to": c.get("assigned_employee_id")} for c in assigned_clients]
        }
    return {"message": "Production mode"}

@app.get("/api/employee/stats")
def employee_stats(payload = Depends(verify_token)):
    if payload["role"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access only")
    
    if not supabase:
        assigned_clients = [c for c in DEMO_CLIENTS if c.get("assigned_employee_id") == payload["sub"]]
        total = len(assigned_clients)
        logger.info(f"Employee stats for {payload['sub']}: {total} clients assigned")
        
        def parse_dt(s):
            try:
                if isinstance(s, str) and ("Z" in s or "+" in s):
                    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                    return dt.replace(tzinfo=None)
                return datetime.fromisoformat(s) if isinstance(s, str) else s
            except Exception:
                return None
        
        good_count = 0
        due_soon_count = 0
        overdue_count = 0
        
        for c in assigned_clients:
            lcd = c.get("last_contact_date")
            days = 999
            if lcd:
                dt = parse_dt(lcd)
                if dt:
                    days = max(0, math.ceil((datetime.utcnow() - dt).total_seconds() / 86400))
            
            if days <= 7:
                good_count += 1
            elif days <= 14:
                due_soon_count += 1
            else:
                overdue_count += 1
        
        result = {
            "total_clients": total,
            "good_clients": good_count,
            "due_soon_clients": due_soon_count,
            "overdue_clients": overdue_count
        }
        logger.info(f"Employee stats result: {result}")
        return result
    
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

@app.get("/api/manager/stats")
def manager_stats(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        try:
            total = len(DEMO_CLIENTS)
            cutoff = datetime.utcnow() - timedelta(days=14)
            logger.info(f"Manager stats: {total} total clients, cutoff date: {cutoff}")
            
            overdue_count = 0
            for c in DEMO_CLIENTS:
                lcd = c.get("last_contact_date")
                if not lcd:
                    overdue_count += 1
                    continue
                try:
                    if isinstance(lcd, str):
                        dt = datetime.fromisoformat(lcd.replace("Z", "+00:00")) if "Z" in lcd else datetime.fromisoformat(lcd)
                        dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    else:
                        dt = lcd
                    if dt < cutoff:
                        overdue_count += 1
                except Exception as e:
                    logger.warning(f"Date parse error in manager stats: {lcd} - {e}")
                    overdue_count += 1
            
            employees_count = len([u for u in DEMO_USERS.values() if u.get("role") == "employee"])
            efficiency = round((total - overdue_count) / total * 100) if total > 0 else 0
            
            result = {
                "employees": employees_count, 
                "clients": total, 
                "overdue": overdue_count, 
                "efficiency": efficiency
            }
            logger.info(f"Manager stats result: {result}")
            return result
        except Exception as e:
            logger.error(f"Manager stats error: {e}")
            return {"employees": 0, "clients": 0, "overdue": 0, "efficiency": 0}
    
    # Production mode - use Supabase
    try:
        employees = supabase.table("users").select("id", count="exact").eq("role", "employee").execute()
        clients_res = supabase.table("clients").select("id,last_contact_date").execute()
        data = clients_res.data or []
        cutoff = datetime.utcnow() - timedelta(days=14)
        def parse_dt(s):
            try:
                dt = datetime.fromisoformat(s.replace("Z", "+00:00")) if isinstance(s, str) and "Z" in s else (datetime.fromisoformat(s) if isinstance(s, str) else s)
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
            except Exception:
                return None
        overdue_count = 0
        for c in data:
            lcd = c.get("last_contact_date")
            if not lcd:
                overdue_count += 1
                continue
            dt = parse_dt(lcd)
            if not dt or dt < cutoff:
                overdue_count += 1
        total = len(data)
        efficiency = round((total - overdue_count) / total * 100) if total > 0 else 0
        return {"employees": employees.count or 0,"clients": total,"overdue": overdue_count,"efficiency": efficiency}
    except Exception as e:
        logger.error(f"Manager stats production error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/manager/employee-performance")
def employee_performance(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        try:
            employees = [u for u in DEMO_USERS.values() if u.get("role") == "employee"]
            logger.info(f"Employee performance: Found {len(employees)} employees")
            
            week_ago = datetime.utcnow() - timedelta(days=7)
            overdue_date = datetime.utcnow() - timedelta(days=14)
            
            # Calculate assignments and overdue clients
            assigned_map = {}
            overdue_map = {}
            for c in DEMO_CLIENTS:
                emp_id = c.get("assigned_employee_id")
                if not emp_id:
                    continue
                assigned_map[emp_id] = assigned_map.get(emp_id, 0) + 1
                lcd = c.get("last_contact_date")
                if not lcd:
                    overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1
                    continue
                try:
                    if isinstance(lcd, str):
                        dt = datetime.fromisoformat(lcd.replace("Z", "+00:00")) if "Z" in lcd else datetime.fromisoformat(lcd)
                        dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    else:
                        dt = lcd
                    if dt < overdue_date:
                        overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1
                except Exception as e:
                    logger.warning(f"Date parse error in employee performance: {lcd} - {e}")
                    overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1
            
            # Calculate activities
            activity_map = {}
            for a in DEMO_ACTIVITY_LOGS:
                try:
                    ts = a.get("created_at")
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if "Z" in ts else datetime.fromisoformat(ts)
                        dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    else:
                        dt = ts
                    if dt >= week_ago:
                        emp_id = a.get("employee_id")
                        if emp_id:
                            activity_map[emp_id] = activity_map.get(emp_id, 0) + 1
                except Exception:
                    continue
            
            # Build response data
            data = []
            for e in employees:
                assigned = assigned_map.get(e["id"], 0)
                overdue_count = overdue_map.get(e["id"], 0)
                efficiency = round((assigned - overdue_count) / assigned * 100) if assigned > 0 else 100
                
                emp_data = {
                    "id": e["id"],
                    "name": e.get("name", "Unknown"),
                    "email": e.get("email", ""),
                    "assigned_clients": assigned,
                    "overdue_clients": overdue_count,
                    "activities_this_week": activity_map.get(e["id"], 0),
                    "efficiency": efficiency
                }
                data.append(emp_data)
            
            logger.info(f"Employee performance result: {len(data)} employees with data")
            return {"data": data}
        except Exception as e:
            logger.error(f"Employee performance error: {e}")
            return {"data": []}
    
    # Production mode - use Supabase
    employees_res = supabase.table("users").select("id,name,email").eq("role", "employee").execute()
    employees = employees_res.data or []
    emp_ids = [e["id"] for e in employees]

    clients_res = supabase.table("clients").select("id,assigned_employee_id,last_contact_date").execute()
    clients = clients_res.data or []
    week_ago = (datetime.utcnow() - timedelta(days=7))
    overdue_date = (datetime.utcnow() - timedelta(days=14))
    activities_res = supabase.table("activity_logs").select("id,employee_id,created_at").gte("created_at", week_ago.isoformat()).execute()
    activities = activities_res.data or []

    assigned_map = {}
    overdue_map = {}
    for c in clients:
        emp_id = c.get("assigned_employee_id")
        if not emp_id:
            continue
        assigned_map[emp_id] = assigned_map.get(emp_id, 0) + 1
        lcd = c.get("last_contact_date")
        if not lcd:
            overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1
            continue
        try:
            if isinstance(lcd, str):
                lcd_dt = datetime.fromisoformat(lcd.replace("Z", "+00:00")) if "+" in lcd or "Z" in lcd else datetime.fromisoformat(lcd)
                lcd_dt = lcd_dt.replace(tzinfo=None) if lcd_dt.tzinfo else lcd_dt
            else:
                lcd_dt = lcd
            days_since = int((datetime.utcnow() - lcd_dt).total_seconds() / 86400)
            if days_since > 14:
                overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1
        except Exception as e:
            logger.warning(f"Date parse error in employee performance: {lcd} - {e}")
            overdue_map[emp_id] = overdue_map.get(emp_id, 0) + 1

    activity_map = {}
    for a in activities:
        emp_id = a.get("employee_id")
        if not emp_id:
            continue
        activity_map[emp_id] = activity_map.get(emp_id, 0) + 1

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



@app.get("/api/users")
def list_users(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        # Return demo users for manager dashboard
        demo_user_list = []
        for user in DEMO_USERS.values():
            demo_user_list.append({
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            })
        return {"data": demo_user_list, "total": len(demo_user_list)}
    
    try:
        result = supabase.table("users").select("id,name,email,role,status,created_at").execute()
        return {"data": result.data or [], "total": len(result.data or [])}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {"data": [], "total": 0, "error": str(e)}

@app.post("/api/employees")
def create_employee(emp: EmployeeCreate, payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
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
        print(f"Employee created: {result.data}")
        return {"message": "Employee created", "data": result.data[0] if result.data else None}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clients/{client_id}")
def delete_client(client_id: str, payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = supabase.table("clients").delete().eq("id", client_id).execute()
        print(f"Client deleted: {client_id}")
        return {"message": "Client deleted successfully"}
    except Exception as e:
        print(f"Error deleting client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manager/alerts")
def manager_alerts(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        employees = [{"id": u["id"], "name": u.get("name", "Employee")} for u in DEMO_USERS.values() if u.get("role") == "employee"]
        today = datetime.utcnow().date().isoformat()
        alerts = []
        for emp in employees:
            have_dmr = any((r.get("employee_id") == emp["id"] and r.get("date") == today) for r in DEMO_DAILY_REPORTS)
            if not have_dmr:
                have_dmr = any((a.get("employee_id") == emp["id"] and (a.get("category") == "daily_report") and str(a.get("created_at", "")).startswith(today)) for a in DEMO_ACTIVITY_LOGS)
            if not have_dmr:
                alerts.append({"type": "dmr_missing", "employee_id": emp["id"], "name": emp["name"], "date": today})
        return {"data": alerts}

@app.get("/api/manager/workload-distribution")
def workload_distribution(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        employees = [{"id": u["id"], "name": u.get("name", "Employee")} for u in DEMO_USERS.values() if u.get("role") == "employee"]
        assigned_map = {}
        for c in DEMO_CLIENTS:
            emp_id = c.get("assigned_employee_id")
            if emp_id:
                assigned_map[emp_id] = assigned_map.get(emp_id, 0) + 1
        today_prefix = datetime.utcnow().date().isoformat()
        postings_map = {}
        for a in DEMO_ACTIVITY_LOGS:
            if str(a.get("created_at", "")).startswith(today_prefix):
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
        return {"data": data}

@app.post("/api/manager/assign-round-robin")
def assign_round_robin(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not supabase:
        emps = [u for u in DEMO_USERS.values() if u.get("role") == "employee"]
        if not emps:
            return {"message": "No employees"}
        emp_ids = [e["id"] for e in emps]
        i = 0
        changes = []
        for idx, c in enumerate(DEMO_CLIENTS):
            if not c.get("assigned_employee_id"):
                assign_to = emp_ids[i % len(emp_ids)]
                DEMO_CLIENTS[idx] = {**c, "assigned_employee_id": assign_to}
                changes.append({"client_id": c["id"], "assigned_employee_id": assign_to})
                i += 1
        return {"message": "Round robin applied", "changes": changes}
    raise HTTPException(status_code=503, detail="Database not configured")

@app.get("/api/manager/report-flags")
def report_flags(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    def demo_flags():
        today = datetime.utcnow().date().isoformat()
        flags = []
        by_emp = {}
        for r in DEMO_DAILY_REPORTS:
            if r.get("date") != today:
                continue
            emp = r.get("employee_id")
            m = r.get("metrics", {})
            def names_from(s):
                if not s: return []
                return [x.strip().lower() for x in str(s).split(',') if x.strip()]
            all_names = names_from(m.get("ta_calls_to")) + names_from(m.get("renewal_calls_to")) + names_from(m.get("service_calls_to"))
            if not all_names: continue
            cnt = by_emp.get(emp) or {}
            for n in all_names:
                cnt[n] = cnt.get(n, 0) + 1
            by_emp[emp] = cnt
        for emp_id, cnt in by_emp.items():
            for name, c in cnt.items():
                if c > 1:
                    flags.append({"employee_id": emp_id, "name": name, "count": c, "date": today})
        return {"data": flags}
    if not supabase:
        return demo_flags()
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
    except Exception:
        return demo_flags()

@app.get("/api/export/clients")
def export_clients(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
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
        print(f"Error exporting clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/daily-reports")
def export_daily_reports(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
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
        print(f"Error exporting daily reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/activities")
def export_activities(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
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
        print(f"Error exporting activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: str, payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    if user_id == payload["sub"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = supabase.table("users").delete().eq("id", user_id).execute()
        print(f"User deleted: {user_id}")
        return {"message": "User deleted successfully"}
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clients/bulk-import-csv")
async def bulk_import_csv(file: UploadFile = File(...), payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
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

@app.post("/api/clients/bulk-create")
def bulk_create_clients(body: dict, payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
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
                    print(f"Inserted batch: {len(result.data)} clients")
                batch_data = []
        
        print(f"Total clients created: {len(clients)}")
        return {"message": f"Created {len(clients)} clients", "count": len(clients)}
    except Exception as e:
        print(f"Error bulk creating clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clients/bulk-assign")
def bulk_assign_clients(body: dict, payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
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

@app.post("/api/clients/assign-round-robin")
def assign_round_robin(body: dict, payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    client_ids: List[str] = body.get("client_ids", [])
    employees = supabase.table("users").select("id").eq("role", "employee").execute().data or []
    if not employees:
        raise HTTPException(status_code=400, detail="No employees available")

    if not client_ids:
        client_ids = [c["id"] for c in supabase.table("clients").select("id").is_('assigned_employee_id', None).execute().data or []]

    assigned_count = {}
    for i, cid in enumerate(client_ids):
        to_emp = employees[i % len(employees)]["id"]
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



@app.get("/api/reminders")
def get_reminders(payload = Depends(verify_token)):
    """Get reminders/notifications for the current user."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = supabase.table("reminders").select("*").eq("user_id", payload["sub"]).order("created_at", desc=True).limit(50).execute()
        return {"data": result.data or []}
    except Exception as e:
        print(f"Error loading reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reminders/{reminder_id}/mark-read")
def mark_reminder_read(reminder_id: str, payload = Depends(verify_token)):
    """Mark a reminder as read."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = supabase.table("reminders").update({"status": "read"}).eq("id", reminder_id).eq("user_id", payload["sub"]).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return {"message": "Reminder marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking reminder as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/stats")
def admin_stats(payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    if payload["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    today = datetime.utcnow().date().isoformat()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    seven_days_ago_ts = time.time() - 7 * 24 * 3600
    while _failed_login_events and _failed_login_events[0] < seven_days_ago_ts:
        _failed_login_events.popleft()
    failed_logins_week = len([ts for ts in _failed_login_events if ts >= seven_days_ago_ts])
    
    return {
        "users": supabase.table("users").select("id", count="exact").execute().count or 0,
        "clients": supabase.table("clients").select("id", count="exact").execute().count or 0,
        "activities": supabase.table("activity_logs").select("id", count="exact").execute().count or 0,
        "activities_today": supabase.table("activity_logs").select("id", count="exact").gte("created_at", today).execute().count or 0,
        "activities_week": supabase.table("activity_logs").select("id", count="exact").gte("created_at", week_ago).execute().count or 0,
        "failed_logins_week": failed_logins_week
    }





# Vercel handler
handler = app
@app.get("/api/follow-ups")
def get_follow_ups(payload = Depends(verify_token)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    logs = supabase.table("activity_logs").select("id,client_id,employee_id,category,outcome,attachments,created_at").eq("employee_id", payload["sub"]).order("created_at", desc=True).limit(500).execute().data or []
    items = []
    now = datetime.utcnow()
    for r in logs:
        atts = r.get("attachments") or []
        meta = next((a for a in atts if isinstance(a, dict) and a.get("type") == "contact_meta" and a.get("follow_up_required")), None)
        if not meta:
            continue
        due = meta.get("due_date")
        status = "pending"
        try:
            if due:
                due_dt = datetime.fromisoformat(due.replace("Z", "+00:00")) if "Z" in due else datetime.fromisoformat(due)
                status = "overdue" if due_dt < now else "upcoming"
        except Exception:
            status = "pending"
        items.append({
            "id": r.get("id"),
            "client_id": r.get("client_id"),
            "method": meta.get("method"),
            "due_date": due,
            "status": status,
            "created_at": r.get("created_at")
        })
    return {"data": items, "total": len(items)}


# HTML page routes
@app.get("/login_page/code.html")
def login_page():
    return FileResponse("login_page/code.html")

@app.get("/employee_dashboard_page/code.html")
def employee_dashboard():
    return FileResponse("employee_dashboard_page/code.html")

@app.get("/manager_dashboard_page/code.html")
def manager_dashboard():
    return FileResponse("manager_dashboard_page/code.html")

@app.get("/management_page/code.html")
def management_page():
    return FileResponse("management_page/code.html")

@app.get("/activity_logging_page/code.html")
def activity_logging():
    return FileResponse("activity_logging_page/code.html")

@app.get("/daily_work_report/code.html")
def daily_work_report():
    return FileResponse("daily_work_report/code.html")

@app.get("/reports_page/code.html")
def reports_page():
    return FileResponse("reports_page/code.html")

@app.get("/notifications_page/code.html")
def notifications_page():
    return FileResponse("notifications_page/code.html")


@app.get("/api/export/reports")
def export_reports(payload = Depends(verify_token)):
    if payload["role"] not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        res = supabase.table("daily_reports").select("*").order("date", desc=True).limit(1000).execute()
        rows = ["date,employee_id,ta_calls,ta_calls_to,renewal_calls,renewal_calls_to,service_calls,service_calls_to,zero_star_calls,one_star_calls,additional_info,submitted_at"]
        
        for r in res.data or []:
            m = r.get("metrics") or {}
            row = [
                str(r.get('date', '')),
                str(r.get('employee_id', '')),
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
        logger.error(f"Error exporting reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))
