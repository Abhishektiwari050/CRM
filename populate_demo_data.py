import os
from supabase import create_client
from datetime import datetime, timedelta
import random
import bcrypt

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Create 5 employees
employees = []
for i in range(1, 6):
    emp = {
        "name": f"Employee {i}",
        "email": f"emp{i}@crm.com",
        "password_hash": hash_password("password123"),
        "role": "employee",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    result = supabase.table("users").insert(emp).execute()
    if result.data:
        employees.append(result.data[0])
        print(f"Created: {emp['name']}")

# Create 20 clients
cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"]
for i in range(1, 21):
    client = {
        "name": f"Client {i}",
        "member_id": f"MEM{str(i).zfill(3)}",
        "city": cities[i % len(cities)],
        "products_posted": random.randint(10, 100),
        "expiry_date": (datetime.utcnow() + timedelta(days=random.randint(30, 365))).date().isoformat(),
        "contact_email": f"client{i}@example.com",
        "contact_phone": f"+91-{random.randint(7000000000, 9999999999)}",
        "assigned_employee_id": employees[i % len(employees)]["id"] if employees else None,
        "last_contact_date": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("clients").insert(client).execute()
    print(f"Created: {client['name']}")

print("\n✅ Demo data populated successfully!")
print(f"- {len(employees)} employees created")
print(f"- 20 clients created and assigned")
