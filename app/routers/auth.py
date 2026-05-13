import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserLogin, Token
from app.services.auth_service import create_access_token, hash_password, authenticate_user
from app.models.user import User
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new user."""
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    user_role = new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role)
    token = create_access_token(data={"sub": new_user.email}, role=user_role)
    return {"access_token": token, "token_type": "bearer", "message": "Registered successfully"}


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates a user and returns a JWT."""
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(data={"sub": user.email}, role=user_role)
    return Token(access_token=token, token_type="bearer")