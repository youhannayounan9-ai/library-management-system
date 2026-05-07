from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserLogin, Token
from app.services.auth_service import create_access_token, hash_password, verify_password
from app.models.user import User
from app.database import get_db

router = APIRouter()

@router.post("/register", status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")
        
    new_user = User(email=user.email, hashed_password=hash_password(user.password), role=user.role or "member")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # ✅ FIXED: Return token so tests pass
    token = create_access_token(data={"sub": new_user.email, "role": new_user.role})
    return {"access_token": token, "token_type": "bearer", "message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    return Token(access_token=token, token_type="bearer")