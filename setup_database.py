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

"""
NOTE: Demo users have been removed from automatic setup.

To create users, you have two options:

Option 1: Manual creation via Supabase Dashboard
- Go to your Supabase project dashboard
- Navigate to Table Editor > users
- Insert records manually

Option 2: Use this script to create a single admin user
- Run: python setup_database.py --create-admin
"""

# Uncomment below to create demo users (NOT RECOMMENDED FOR PRODUCTION)
# users_to_create = [
#     {
#         "name": "Admin User",
#         "email": "admin@crm.com",
#         "password": "admin123",
#         "role": "admin"
#     },
#     {
#         "name": "Manager User",
#         "email": "manager@crm.com",
#         "password": "password123",
#         "role": "manager"
#     },
#     {
#         "name": "John Doe",
#         "email": "john@crm.com",
#         "password": "password123",
#         "role": "employee"
#     }
# ]

import argparse
import sys

parser = argparse.ArgumentParser(description='Setup CRM database')
parser.add_argument('--create-admin', action='store_true', help='Create a single admin user')
args = parser.parse_args()

users_to_create = []

if args.create_admin:
    admin_email = input("Admin email [admin@company.com]: ") or "admin@company.com"
    admin_password = input("Admin password [ChangeMe123!]: ") or "ChangeMe123!"
    admin_name = input("Admin name [System Administrator]: ") or "System Administrator"
    
    users_to_create = [{
        "name": admin_name,
        "email": admin_email,
        "password": admin_password,
        "role": "admin"
    }]

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

if args.create_admin and users_to_create:
    print("\nAdmin user created:")
    print(f"  Email:    {users_to_create[0]['email']}")
    print(f"  Password: {users_to_create[0]['password']}")
    print("\n⚠️  IMPORTANT: Change the password after first login!")
else:
    print("\nNo users were created.")
    print("To create an admin user, run:")
    print("  python setup_database.py --create-admin")
    print("\nOr create users manually via Supabase Dashboard:")
    print("  https://supabase.com/dashboard")

print("\nStart the application with: START.bat")
