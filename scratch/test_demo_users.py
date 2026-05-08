import requests

BASE_URL = "http://localhost:8000"

def test_login(email, password):
    print(f"Testing login for {email}...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {resp.status_code} - {resp.text}")
        return None

if __name__ == "__main__":
    admin_token = test_login("admin@library.com", "admin123")
    member_token = test_login("member@library.com", "member123")
