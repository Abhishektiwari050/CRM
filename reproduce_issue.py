import requests
import json

API_URL = "http://localhost:8001"
EMAIL = "iqra@crm.com"
PASSWORD = "Iqra@1"

def test_api():
    print(f"Testing API at {API_URL}...")
    
    # 1. Login
    try:
        resp = requests.post(f"{API_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return
        
        data = resp.json()
        token = data.get("access_token")
    except Exception as e:
        print(f"Login error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get User Profile
    try:
        resp = requests.get(f"{API_URL}/api/auth/me", headers=headers)
        user = resp.json()
        print(f"User Role: {user.get('role')}")
    except Exception as e:
        print(f"Profile error: {e}")

    # 3. Get Clients
    try:
        resp = requests.get(f"{API_URL}/api/clients", headers=headers)
        print(f"Clients Response Type: {type(resp.json())}")
        print(f"Clients Response Keys: {resp.json().keys() if isinstance(resp.json(), dict) else 'Not a dict'}")
        print(f"Clients Response Preview: {str(resp.json())[:100]}")
    except Exception as e:
        print(f"Clients error: {e}")

if __name__ == "__main__":
    test_api()
