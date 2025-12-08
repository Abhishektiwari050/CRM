from api.utils.database import supabase
import json

def check_schema():
    try:
        # Try to select one row with * to see all columns
        res = supabase.table("daily_reports").select("*").limit(1).execute()
        if res.data:
            cols = list(res.data[0].keys())
            print("Columns found:")
            for c in cols:
                print(f"- {c}")
        else:
            print("Table empty, checking error...")
            print(res)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
