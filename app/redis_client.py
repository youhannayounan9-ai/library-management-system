import logging
import redis.asyncio as redis
import json
from typing import Callable, Awaitable, Any
from fastapi.encoders import jsonable_encoder
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-decoded value from Redis, or None if missing/unavailable."""
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except redis.RedisError as exc:
        logger.warning("Redis cache_get failed for key '%s': %s", key, exc)
        return None


async def cache_set(key: str, value: Any, expire: int = 300) -> None:
    """Serialise *value* with jsonable_encoder and store it in Redis."""
    try:
        safe_data = jsonable_encoder(value)
        await redis_client.setex(key, expire, json.dumps(safe_data))
    except redis.RedisError as exc:
        logger.warning("Redis cache_set failed for key '%s': %s", key, exc)


async def cache_invalidate(key: str) -> None:
    """Delete a key from Redis."""
    try:
        await redis_client.delete(key)
    except redis.RedisError as exc:
        logger.warning("Redis cache_invalidate failed for key '%s': %s", key, exc)


def book_key(book_id: int) -> str:
    return f"book:{book_id}"


async def get_cached_book(book_id: int, fetch: Callable[[], Awaitable[Any]]) -> Any:
    """Cache-Aside pattern: return cached book or call *fetch*, cache, and return.

    If Redis is unavailable at any point the function falls back to the database
    fetch transparently so the API remains operational.
    """
    key = book_key(book_id)
    # Step 1 – try the cache
    cached = await cache_get(key)  # already handles RedisError internally
    if cached is not None:
        return cached
    # Step 2 – cache miss: hit the database
    book = await fetch()
    # Step 3 – populate the cache (best-effort; errors are swallowed)
    await cache_set(key, book)  # already handles RedisError internally
    return book


async def ping_redis() -> bool:
    """Return True if Redis is reachable, False otherwise."""
    try:
        return await redis_client.ping()
    except redis.RedisError:
        return False
