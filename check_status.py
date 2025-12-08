from api.utils.database import supabase

def check_status():
    try:
        res = supabase.table("users").select("status").limit(1).execute()
        print("Status column query result:", res)
    except Exception as e:
        print(f"Status column failed: {e}")

if __name__ == "__main__":
    check_status()
