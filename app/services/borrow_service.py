import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.book import Book
from app.models.borrow import BorrowRecord
from app.redis_client import cache_invalidate, book_key
from app.config import get_settings
from datetime import datetime, timezone

logger = logging.getLogger("borrow")

settings = get_settings()

FINE_RATE_PER_DAY: float = 0.50  # USD
MAX_BORROW_DAYS: int = 14  # books are due back after 14 days


async def borrow_book(db: AsyncSession, user_id: int, book_id: int) -> None:
    """Borrow a book: enforce borrow limit, decrement copies, create record."""
    # Check active borrows against limit
    result = await db.execute(
        select(BorrowRecord).where(
            BorrowRecord.user_id == user_id,
            BorrowRecord.return_date.is_(None),
        )
    )
    active_borrows = result.scalars().all()
    if len(active_borrows) >= settings.MAX_BORROW_LIMIT:
        raise HTTPException(status_code=400, detail="Borrow limit reached")

    book = await db.get(Book, book_id)
    if not book or book.available_copies <= 0 or book.is_deleted:
        raise HTTPException(status_code=400, detail="Book unavailable")

    logger.info(f"CRUD:BOOK_BORROW | user_id={user_id} | book_id={book_id}")
    book.available_copies -= 1
    record = BorrowRecord(user_id=user_id, book_id=book_id)
    db.add(record)
    try:
        await db.commit()
        await cache_invalidate(book_key(book_id))
    except Exception as e:
        logger.error(f"DB/CACHE ERROR: {e}")
        raise


async def return_book(db: AsyncSession, user_id: int, record_id: int) -> dict:
    """Return a borrowed book: validate ownership, set return date, restore copy.

    Returns a dict with ``fine`` (float) indicating any late-return charge
    calculated as: days_overdue * FINE_RATE_PER_DAY ($0.50/day).
    """
    record = await db.get(BorrowRecord, record_id)
    if not record or record.user_id != user_id or record.return_date is not None:
        raise HTTPException(status_code=400, detail="Invalid return operation")

    now = datetime.now(timezone.utc)
    record.return_date = now

    # --- Late-fine calculation ---
    # borrow_date may be naive (stored as UTC) – normalise before subtracting.
    borrow_date = record.borrow_date
    if borrow_date.tzinfo is None:
        borrow_date = borrow_date.replace(tzinfo=timezone.utc)

    days_held = (now - borrow_date).days
    days_late = max(0, days_held - MAX_BORROW_DAYS)
    fine = round(days_late * FINE_RATE_PER_DAY, 2)
    record.fine = fine  # persist on the record

    logger.info(f"CRUD:BOOK_RETURN | user_id={user_id} | record_id={record_id} | fine_amount={record.fine}")
    record.return_date = now

    book = await db.get(Book, record.book_id)
    try:
        if book:
            book.available_copies += 1
            await cache_invalidate(book_key(book.id))
        await db.commit()
    except Exception as e:
        logger.error(f"DB/CACHE ERROR: {e}")
        raise

    return {"fine": fine, "days_late": days_late}
