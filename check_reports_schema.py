from api.utils.database import supabase

def check_reports_schema():
    try:
        res = supabase.table("daily_reports").select("*").limit(1).execute()
        if res.data:
            print("Columns:", list(res.data[0].keys()))
        else:
            # If empty, try to get structure from error or just insert a dummy to fail
            print("Table empty.")
            # Try a dry run insert with minimal data
            try:
                supabase.table("daily_reports").insert({"employee_id": "dummy"}).execute()
            except Exception as e:
                print(f"Insert error (might reveal schema): {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_reports_schema()
