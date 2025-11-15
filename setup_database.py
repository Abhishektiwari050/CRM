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

print("Setting up database...")

# Read and execute schema
with open("supabase/migrations/000_initial_schema.sql", "r") as f:
    schema_sql = f.read()

print("\n1. Creating tables...")
print("   Please run the SQL in Supabase SQL Editor:")
print("   https://supabase.com/dashboard/project/YOUR_PROJECT/sql")
print("\n" + "="*60)
print(schema_sql)
print("="*60 + "\n")

# Create initial users
print("2. Creating initial users...")

users_to_create = [
    {
        "name": "Admin User",
        "email": "admin@crm.com",
        "password": "admin123",
        "role": "admin"
    },
    {
        "name": "Manager User",
        "email": "manager@crm.com",
        "password": "password123",
        "role": "manager"
    },
    {
        "name": "John Doe",
        "email": "john@crm.com",
        "password": "password123",
        "role": "employee"
    }
]

for user_data in users_to_create:
    try:
        # Check if user exists
        existing = supabase.table("users").select("id").eq("email", user_data["email"]).execute()
        
        if existing.data:
            print(f"   [OK] User {user_data['email']} already exists")
        else:
            # Create user
            result = supabase.table("users").insert({
                "name": user_data["name"],
                "email": user_data["email"],
                "password_hash": hash_password(user_data["password"]),
                "role": user_data["role"],
                "status": "active"
            }).execute()
            
            if result.data:
                print(f"   [OK] Created {user_data['role']}: {user_data['email']} / {user_data['password']}")
            else:
                print(f"   [ERROR] Failed to create {user_data['email']}")
    except Exception as e:
        print(f"   [ERROR] Error creating {user_data['email']}: {e}")

print("\n" + "="*60)
print("Setup complete!")
print("="*60)
print("\nLogin credentials:")
print("  Admin:    admin@crm.com / admin123")
print("  Manager:  manager@crm.com / password123")
print("  Employee: john@crm.com / password123")
print("\nStart the application with: START.bat")
