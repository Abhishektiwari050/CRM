import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def reset_password():
    email = "manager@crm.com"
    new_password = "admin123"
    
    print(f"Resetting password for {email}...")
    
    # Check if user exists
    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        print(f"User {email} not found!")
        # Create maybe?
        sys.exit(1)
        
    user_id = res.data[0]["id"]
    new_hash = hash_password(new_password)
    
    try:
        supabase.table("users").update({"password_hash": new_hash}).eq("id", user_id).execute()
        print("Password updated successfully.")
    except Exception as e:
        print(f"Error updating password: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_password()
