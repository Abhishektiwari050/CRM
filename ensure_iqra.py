import os
from supabase import create_client
import bcrypt
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

email = "iqra@crm.com"
password = "Iqra@1"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Check if user exists
existing = supabase.table("users").select("*").eq("email", email).execute()

if existing.data:
    print(f"User {email} exists.")
    # Update password to ensure it matches
    supabase.table("users").update({
        "password_hash": hash_password(password),
        "role": "employee" # Ensure role is employee
    }).eq("email", email).execute()
    print("Password and role updated.")
else:
    print(f"Creating user {email}...")
    supabase.table("users").insert({
        "name": "Iqra User",
        "email": email,
        "password_hash": hash_password(password),
        "role": "employee",
        "status": "active"
    }).execute()
    print("User created.")
