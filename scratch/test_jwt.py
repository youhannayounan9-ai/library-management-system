import requests
import jose.jwt
import json

BASE_URL = "http://localhost:8000"

def test_login(email, password):
    print(f"\nLogging in as {email}...")
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("Login SUCCESS")
        
        # In a real scenario we'd use the secret key, but for a quick check we can just unverified decode
        # or use a known secret if we have it. 
        # Since I'm on the same system, I can try to get the secret from config.
        # But for simplicity, let's just use the unverified decode to see the payload.
        header, payload, signature = token.split('.')
        # Pad payload
        payload += '=' * (4 - len(payload) % 4)
        import base64
        decoded_payload = base64.b64decode(payload).decode('utf-8')
        print(f"Token Payload: {decoded_payload}")
        return json.loads(decoded_payload)
    else:
        print(f"Login FAILED: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    # Test Admin
    test_login("admin@example.com", "admin123")
    
    # Test Member
    test_login("user@example.com", "user123")
