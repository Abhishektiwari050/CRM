from api.utils.database import supabase

def test_query():
    print("Querying daily_reports...")
    try:
        res = supabase.table("daily_reports").select("*").limit(5).execute()
        print(f"Got {len(res.data)} rows")
        print(res.data)
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    test_query()
