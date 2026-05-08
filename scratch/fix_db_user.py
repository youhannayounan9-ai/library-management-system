import asyncio
import asyncpg
import os

async def main():
    # Use the DB URL from the environment or hardcode for this fix
    db_url = "postgresql://postgres:postgres@localhost:5432/library"
    password_hash = "$2b$12$LBIuFCt10.tCyhtmljLayuxpr/UqH/fPMkegsjBV55XOvTubi6KmW" # "password"
    
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute(
            "UPDATE users SET hashed_password = $1 WHERE email = 'prof_test@lib.com'",
            password_hash
        )
        print("Successfully updated prof_test@lib.com password hash.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
