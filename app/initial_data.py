import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import hash_password
from app.database import async_session

logger = logging.getLogger(__name__)

DEMO_USERS = [
    {"email": "admin@library.com", "password": "admin123", "role": "admin"},
    {"email": "member@library.com", "password": "member123", "role": "member"},
]

async def seed_demo_users():
    """Idempotently creates demo users on startup."""
    async with async_session() as session:
        for user_data in DEMO_USERS:
            result = await session.execute(select(User).where(User.email == user_data["email"]))
            existing = result.scalar_one_or_none()

            if not existing:
                new_user = User(
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    role=user_data["role"]
                )
                session.add(new_user)
                await session.commit()
                logger.info(f"✅ User ready: {user_data['email']} / {user_data['password']} (Role: {user_data['role']})")
            else:
                logger.info(f"✅ User ready: {user_data['email']} (Already exists)")