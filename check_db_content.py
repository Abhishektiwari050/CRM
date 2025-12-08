import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def print_table_summary(table_name, cols="*"):
    with open("db_summary.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- {table_name} ---\n")
        try:
            res = supabase.table(table_name).select(cols, count="exact").execute()
            count = res.count if res.count is not None else len(res.data)
            f.write(f"Total count: {count}\n")
            if res.data:
                f.write("First 3 records:\n")
                for item in res.data[:3]:
                    f.write(json.dumps(item, indent=2, default=str) + "\n")
            else:
                f.write("No records found.\n")
        except Exception as e:
            f.write(f"Error querying {table_name}: {e}\n")

# Clear file first
with open("db_summary.txt", "w", encoding="utf-8") as f:
    f.write("Checking Supabase Database Content...\n")

print("Checking Supabase Database Content...")
print_table_summary("users", "id, name, email, role, status")
print_table_summary("clients", "id, name, city, status, assigned_employee_id")
print_table_summary("daily_reports", "id, employee_id, date, metrics")
print_table_summary("activity_logs", "id, employee_id, client_id, category, outcome")
