import os
from supabase import create_client
import bcrypt
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

user_data = {
    "name": "John Doe",
    "email": "john@crm.com",
    "password": "password123",
    "role": "employee"
}

try:
    # Check if user exists
    existing = supabase.table("users").select("id").eq("email", user_data["email"]).execute()
    
    if existing.data:
        print(f"User {user_data['email']} already exists. Updating password...")
        supabase.table("users").update({
            "password_hash": hash_password(user_data["password"]),
            "role": user_data["role"]
        }).eq("email", user_data["email"]).execute()
        print("User updated.")
    else:
        # Create user
        print(f"Creating user {user_data['email']}...")
        result = supabase.table("users").insert({
            "name": user_data["name"],
            "email": user_data["email"],
            "password_hash": hash_password(user_data["password"]),
            "role": user_data["role"],
            "status": "active"
        }).execute()
        print("User created.")

except Exception as e:
    print(f"Error: {e}")
