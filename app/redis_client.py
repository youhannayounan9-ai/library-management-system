import logging
import json
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize async Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# ====================== SINGLE BOOK CACHING ======================

def book_key(book_id: int) -> str:
    return f"book:{book_id}"

async def get_cached_book(book_id: int):
    try:
        data = await redis_client.get(book_key(book_id))
        if data:
            logger.info(f"CACHE_HIT: Book {book_id}")
            return json.loads(data)
    except Exception as e:
        logger.error(f"REDIS_ERROR: GET book {book_id}: {e}")
    return None

async def cache_set(book_id: int, data: dict):
    try:
        await redis_client.setex(book_key(book_id), 3600, json.dumps(data))
        logger.info(f"CACHE_SET: Book {book_id}")
    except Exception as e:
        logger.error(f"REDIS_ERROR: SET book {book_id}: {e}")

async def cache_invalidate(book_id: int):
    try:
        await redis_client.delete(book_key(book_id))
        logger.info(f"CACHE_INVALIDATE: Book {book_id}")
    except Exception as e:
        logger.error(f"REDIS_ERROR: DELETE book {book_id}: {e}")

# ====================== BOOKS LIST CACHING ======================

def books_list_key(skip: int, limit: int) -> str:
    return f"books:list:skip={skip}:limit={limit}"

async def get_cached_books(skip: int, limit: int):
    try:
        data = await redis_client.get(books_list_key(skip, limit))
        if data:
            logger.info(f"CACHE_HIT: Books list (skip={skip}, limit={limit})")
            return json.loads(data)
        logger.info(f"CACHE_MISS: Books list (skip={skip}, limit={limit})")
    except Exception as e:
        logger.error(f"REDIS_ERROR: GET books list: {e}")
    return None

async def cache_books_list(skip: int, limit: int, data: list):
    try:
        await redis_client.setex(books_list_key(skip, limit), 3600, json.dumps(data))
        logger.info(f"CACHE_SET: Books list (skip={skip}, limit={limit})")
    except Exception as e:
        logger.error(f"REDIS_ERROR: SET books list: {e}")

async def invalidate_books_list():
    try:
        # Clear all variations of the list cache (skip/limit variations)
        keys = await redis_client.keys("books:list:*")
        if keys:
            await redis_client.delete(*keys)
            logger.info(f"CACHE_INVALIDATE: Cleared {len(keys)} books list keys")
    except Exception as e:
        logger.error(f"REDIS_ERROR: Invalidate books list: {e}")

# ====================== USER HISTORY CACHING ======================

def history_key(user_id: int) -> str:
    return f"user:{user_id}:history"

async def get_cached_history(user_id: int):
    try:
        data = await redis_client.get(history_key(user_id))
        if data:
            logger.info(f"CACHE_HIT: History for user {user_id}")
            return json.loads(data)
    except Exception as e:
        logger.error(f"REDIS_ERROR: GET history for user {user_id}: {e}")
    return None

async def cache_history(user_id: int, data: list):
    try:
        await redis_client.setex(history_key(user_id), 600, json.dumps(data))
        logger.info(f"CACHE_SET: History for user {user_id}")
    except Exception as e:
        logger.error(f"REDIS_ERROR: SET history for user {user_id}: {e}")

async def invalidate_history(user_id: int):
    try:
        await redis_client.delete(history_key(user_id))
        logger.info(f"CACHE_INVALIDATE: History for user {user_id}")
    except Exception as e:
        logger.error(f"REDIS_ERROR: DELETE history for user {user_id}: {e}")