from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, RoleEnum

# Standard Bearer scheme
auth_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Decodes the token and returns a dictionary containing email and role."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return {"email": email, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

def admin_required(current_user: dict = Depends(get_current_user)):
    """Ensures the current user has the admin role (case-insensitive)."""
    # Force lowercase comparison to be safe
    if current_user.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    return current_user