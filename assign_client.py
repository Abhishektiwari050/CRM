import os
from supabase import create_client
from dotenv import load_dotenv
import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get John's ID
user = supabase.table("users").select("id").eq("email", "john@crm.com").execute()
if not user.data:
    print("John not found")
    exit(1)
john_id = user.data[0]["id"]

# Create a client assigned to John
client_data = {
    "name": "Test Client for John",
    "assigned_employee_id": john_id,
    "status": "active",
    "expiry_date": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
    "created_at": datetime.datetime.utcnow().isoformat()
}

result = supabase.table("clients").insert(client_data).execute()
print(f"Client created: {result.data}")
