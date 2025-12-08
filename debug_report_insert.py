from api.utils.database import supabase
from datetime import datetime

def test_insert_report():
    print("Attempting to insert dummy report...")
    data = {
        # Using a valid existing user ID would be best, but let's try a dummy first or look one up
        "employee_id": "00000000-0000-0000-0000-000000000000", # UUID format
        "date": datetime.utcnow().date().isoformat(),
        "tasks": "Debug Task",
        "ta_calls": 5,
        "ta_calls_to": "Test Client",
        "metrics": {"notes": "debug"},
        "created_at": datetime.utcnow().isoformat()
    }

    # Query a real user ID first to avoid foreign key violation
    try:
        users = supabase.table("users").select("id").limit(1).execute()
        if users.data:
            data["employee_id"] = users.data[0]["id"]
            print(f"Using employee_id: {data['employee_id']}")
    except Exception as e:
        print(f"User fetch failed: {e}")

    try:
        res = supabase.table("daily_reports").insert(data).execute()
        print("Insert Result:", res)
    except Exception as e:
        print(f"Insert Failed: {e}")

if __name__ == "__main__":
    test_insert_report()
