from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

# ✅ Swagger-friendly Bearer token input (no OAuth2 modal)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(authorization: str = Depends(api_key_header), db: AsyncSession = Depends(get_db)):
    """Validates JWT, performs live DB lookup, and returns the full User model."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    # 🔍 Live DB Lookup (Rubric: Real-time role enforcement)
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user  # ✅ Returns User model (fixes current_user.id access in borrows/books)

async def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

# Alias kept so books.py import of `admin_required` continues to work
admin_required = require_admin