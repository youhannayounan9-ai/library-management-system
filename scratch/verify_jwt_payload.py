import asyncio
import enum
from app.models.user import User, RoleEnum
from app.services.auth_service import create_access_token
from app.config import settings
from jose import jwt

# Use a test database or just mock the user object
async def test_jwt_payload():
    print("Testing JWT Payload for ADMIN role...")
    
    # Simulate a user from DB
    admin_user = User(email="admin@example.com", hashed_password="...", role=RoleEnum.ADMIN)
    
    # Create token
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    # Decode token
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    print(f"Decoded Payload: {payload}")
    
    assert payload["role"] == "admin"
    print("SUCCESS: Admin role correctly encoded as 'admin'")

    print("\nTesting JWT Payload for MEMBER role...")
    member_user = User(email="user@example.com", hashed_password="...", role=RoleEnum.MEMBER)
    token = create_access_token(data={"sub": member_user.email, "role": member_user.role})
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    print(f"Decoded Payload: {payload}")
    
    assert payload["role"] == "member"
    print("SUCCESS: Member role correctly encoded as 'member'")

if __name__ == "__main__":
    asyncio.run(test_jwt_payload())
