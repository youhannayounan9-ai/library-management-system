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
    try:
        existing = await db.execute(select(User).where(User.email == user.email))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
            
        new_user = User(
            email=user.email, 
            hashed_password=hash_password(user.password), 
            role=user.role
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        token = create_access_token(data={"sub": new_user.email, "role": new_user.role})
        return {"access_token": token, "token_type": "bearer", "message": "Registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REGISTER CRASH] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during registration")

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates a user and returns a JWT."""
    try:
        user = await authenticate_user(db, user_credentials.email, user_credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token = create_access_token(data={"sub": user.email, "role": user.role})
        return Token(access_token=token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LOGIN CRASH] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="A server error occurred during login. Check logs.")

@router.get("/debug/login-check/{email}")
async def debug_login(email: str, db: AsyncSession = Depends(get_db)):
    """A temporary debug endpoint to verify user existence and hash status."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        return {"status": "error", "message": f"User {email} not found in DB"}
        
    return {
        "status": "success",
        "email": user.email,
        "role": user.role,
        "has_hash": len(user.hashed_password) > 0,
        "hash_prefix": user.hashed_password[:10] if user.hashed_password else "NONE"
    }