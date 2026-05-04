import logging
import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.config import get_settings

logger = logging.getLogger("auth")

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    result = bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    logger.info(f"Auth Event: Password verification {'SUCCESS' if result else 'FAILED'}")
    return result


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    logger.info(f"Auth Event: JWT generated for user: {data.get('sub')}")
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
