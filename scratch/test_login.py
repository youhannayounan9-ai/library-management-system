import asyncio
import json
from jose import jwt
from app.services.auth_service import authenticate_user, create_access_token
from app.database import async_session
from app.config import settings

async def test_admin_login():
    async with async_session() as db:
        email = "admin@library.com"
        password = "admin123"
        
        user = await authenticate_user(db, email, password)
        if not user:
            print(f"FAILED: Could not authenticate {email}")
            return
            
        print(f"DEBUG: Authenticated user {user.email}, role: {user.role}")
        
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        token = create_access_token(data={"sub": user.email}, role=user_role)
        
        print(f"DEBUG: Generated token: {token}")
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        print(f"DEBUG: Token payload: {json.dumps(payload, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_admin_login())
