import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.user import User

async def check_admin_role():
    async with async_session() as session:
        email = "admin@library.com"
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"DEBUG: Found user {user.email}")
            print(f"DEBUG: Role in DB: {user.role}")
            print(f"DEBUG: Role type: {type(user.role)}")
            if hasattr(user.role, "value"):
                print(f"DEBUG: Role value: {user.role.value}")
        else:
            print(f"DEBUG: User {email} not found in database.")

if __name__ == "__main__":
    asyncio.run(check_admin_role())
