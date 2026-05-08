import logging
import enum
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings

# Setup structured logging
logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed one."""
    try:
        logger.debug("[AUTH] Verifying password against hash...")
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"[AUTH ERROR] Password verification failed: {e}")
        return False

def create_access_token(data: dict):
    """Generates a robust JWT access token with error handling and role safety."""
    try:
        to_encode = data.copy()
        
        # Use timezone-aware UTC for expiration
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        # Safely convert RoleEnum or other objects to string for the JWT payload
        if "role" in to_encode:
            role = to_encode["role"]
            if hasattr(role, "value"):
                role_val = role.value
                logger.debug(f"[JWT] Converting RoleEnum to string: {role_val}")
                to_encode["role"] = role_val
            else:
                to_encode["role"] = str(role)
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.info(f"✅ [JWT SUCCESS] Token created for '{to_encode.get('sub')}' with role '{to_encode.get('role')}'")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"❌ [JWT ERROR] Creation failed: {e}", exc_info=True)
        raise

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticates a user and returns the User object or False."""
    from app.models.user import User
    from sqlalchemy import select
    
    logger.info(f"[AUTH] Attempting login for user: {email}")
    
    try:
        # Query user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            logger.warning(f"❌ [AUTH FAILED] User '{email}' not found in database")
            return False
            
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"❌ [AUTH FAILED] Incorrect password for '{email}'")
            return False
            
        logger.info(f"✅ [AUTH SUCCESS] User '{email}' authenticated (Role: {user.role})")
        return user
        
    except Exception as e:
        logger.error(f"❌ [AUTH CRASH] Unexpected error in authenticate_user: {e}", exc_info=True)
        return False