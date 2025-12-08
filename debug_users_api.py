import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8001"

def debug_users_endpoint():
    try:
        # 1. Login as Manager
        print("Logging in as manager...")
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "manager@crm.com", "password": "admin123"})
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        print("Login successful.")
        import base64
        payload = json.loads(base64.b64decode(token.split('.')[1] + "==").decode('utf-8'))
        print("Token Payload:", json.dumps(payload, indent=2))

        # 2. Call /api/users
        print("Calling /api/users ...")
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        with open("last_response.json", "w") as f:
            f.write(r.text)
        print("Response saved to last_response.json")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_users_endpoint()
