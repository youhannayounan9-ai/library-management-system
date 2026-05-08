import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.user import User

async def list_users():
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"- {u.email} (Role: {u.role})")

if __name__ == "__main__":
    asyncio.run(list_users())
