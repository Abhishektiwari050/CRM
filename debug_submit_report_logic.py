from api.utils.database import supabase
from datetime import datetime
from api.models import DailyReport
import json

def test_submit_logic():
    # Mock payload like the router receives
    payload = {"sub": "00000000-0000-0000-0000-000000000000"}
    
    # Needs a valid user ID technically, let's fetch one
    try:
        u = supabase.table("users").select("id").limit(1).execute()
        if u.data:
            payload["sub"] = u.data[0]["id"]
            print(f"Using user: {payload['sub']}")
    except:
        pass

    # Mock Report Object
    report = DailyReport(
        ta_calls=10,
        ta_calls_to="Logic Test",
        renewal_calls=5,
        additional_info="Testing script"
    )

    data = {
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
        "created_at": datetime.utcnow().isoformat()
    }
    
    print("Data to insert:", json.dumps(data, indent=2, default=str))

    try:
        result = supabase.table("daily_reports").insert(data).execute()
        print("Insert Success:", result)
    except Exception as e:
        print("Insert Failed:", e)

if __name__ == "__main__":
    test_submit_logic()
