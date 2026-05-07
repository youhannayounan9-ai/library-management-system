import logging
import json
import redis.asyncio as redis
from app.config import settings  # 👈 FIXED: Use 'settings' instead of 'get_settings'

logger = logging.getLogger(__name__)

# Initialize async Redis client using the settings object
redis_client = redis.from_url(settings.REDIS_URL)

def book_key(book_id: int) -> str:
    return f"book:{book_id}"

async def get_cached_book(book_id: int):
    try:
        data = await redis_client.get(book_key(book_id))
        if data:
            logger.info(f"Cache HIT for book {book_id}")
            return json.loads(data)
    except Exception as e:
        logger.error(f"Redis GET error: {e}")
    return None

async def cache_set(book_id: int, data: dict):
    try:
        await redis_client.setex(
            book_key(book_id), 
            3600, # 1 hour TTL
            json.dumps(data)
        )
        logger.info(f"Cache SET for book {book_id}")
    except Exception as e:
        logger.error(f"Redis SET error: {e}")

async def cache_invalidate(book_id: int):
    try:
        await redis_client.delete(book_key(book_id))
        logger.info(f"Cache INVALIDATE for book {book_id}")
    except Exception as e:
        logger.error(f"Redis DELETE error: {e}")