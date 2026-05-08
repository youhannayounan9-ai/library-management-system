import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.borrow import Borrow
from app.models.book import Book
from app.config import settings  # 👈 FIXED: Use 'settings' instead of 'get_settings'

from app.redis_client import cache_invalidate, invalidate_books_list, invalidate_history

logger = logging.getLogger(__name__)

async def borrow_book(db: AsyncSession, user_id: int, book_id: int) -> Borrow:
    # Verify book exists and has copies
    book_result = await db.execute(select(Book).where(Book.id == book_id, Book.is_deleted == False))
    book = book_result.scalar_one_or_none()
    
    if not book:
        logger.warning(f"BORROW_FAILED: Book {book_id} not found")
        raise ValueError(f"Book with ID {book_id} not found or has been removed")
        
    if book.available_copies <= 0:
        logger.warning(f"BORROW_FAILED: No copies available for book '{book.title}'")
        raise ValueError(f"Sorry, all copies of '{book.title}' are currently borrowed")

    # Create borrow record
    borrow = Borrow(
        user_id=user_id,
        book_id=book_id,
        borrow_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=settings.DUE_DAYS),
        is_returned=False
    )
    db.add(borrow)
    book.available_copies -= 1
    
    # Invalidate Caches
    await cache_invalidate(book_id)
    await invalidate_books_list()
    await invalidate_history(user_id)
    
    logger.info(f"BORROW_SUCCESS: User {user_id} borrowed '{book.title}' (Borrow ID: {borrow.id})")
    return borrow

async def return_book(db: AsyncSession, borrow_id: int) -> Borrow:
    borrow_result = await db.execute(select(Borrow).where(Borrow.id == borrow_id))
    borrow = borrow_result.scalar_one_or_none()
    
    if not borrow:
        logger.warning(f"RETURN_FAILED: Borrow record {borrow_id} not found")
        raise ValueError("Invalid borrow record ID")
        
    if borrow.is_returned:
        logger.warning(f"RETURN_FAILED: Book already returned for borrow {borrow_id}")
        raise ValueError("This book has already been marked as returned")

    borrow.is_returned = True
    borrow.return_date = datetime.now(timezone.utc)

    # Calculate fine if overdue
    if borrow.return_date > borrow.due_date:
        days_overdue = (borrow.return_date - borrow.due_date).days
        borrow.fine_amount = days_overdue * settings.FINE_PER_DAY
        logger.warning(f"OVERDUE_RETURN: Borrow {borrow_id} is {days_overdue} days late. Fine: ${borrow.fine_amount:.2f}")

    # Restore book copy
    book_result = await db.execute(select(Book).where(Book.id == borrow.book_id))
    book = book_result.scalar_one_or_none()
    if book:
        book.available_copies += 1
        await cache_invalidate(book.id)
        await invalidate_books_list()
        logger.info(f"RETURN_SUCCESS: User returned '{book.title}' (Borrow ID: {borrow_id})")
    
    await invalidate_history(borrow.user_id)
    return borrow