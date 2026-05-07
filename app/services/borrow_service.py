import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.borrow import Borrow
from app.models.book import Book
from app.config import settings  # 👈 FIXED: Use 'settings' instead of 'get_settings'

logger = logging.getLogger(__name__)

async def borrow_book(db: AsyncSession, user_id: int, book_id: int) -> Borrow:
    # Verify book exists and has copies
    book_result = await db.execute(select(Book).where(Book.id == book_id, Book.is_deleted == False))
    book = book_result.scalar_one_or_none()
    if not book:
        raise ValueError("Book not found or unavailable")
    if book.available_copies <= 0:
        raise ValueError("No available copies")

    # Create borrow record
    borrow = Borrow(
        user_id=user_id,
        book_id=book_id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=settings.DUE_DAYS),
        is_returned=False
    )
    db.add(borrow)
    book.available_copies -= 1
    logger.info(f"User {user_id} borrowed book '{book.title}' (ID: {book_id})")
    return borrow

async def return_book(db: AsyncSession, borrow_id: int) -> Borrow:
    borrow_result = await db.execute(select(Borrow).where(Borrow.id == borrow_id))
    borrow = borrow_result.scalar_one_or_none()
    if not borrow:
        raise ValueError("Borrow record not found")
    if borrow.is_returned:
        raise ValueError("Book already returned")

    borrow.is_returned = True
    borrow.return_date = datetime.utcnow()

    # Calculate fine if overdue
    if borrow.return_date > borrow.due_date:
        days_overdue = (borrow.return_date - borrow.due_date).days
        borrow.fine_amount = days_overdue * settings.FINE_PER_DAY
        logger.warning(f"Late return! Borrow {borrow_id} is {days_overdue} days overdue. Fine: ${borrow.fine_amount:.2f}")

    # Restore book copy
    book_result = await db.execute(select(Book).where(Book.id == borrow.book_id))
    book = book_result.scalar_one_or_none()
    if book:
        book.available_copies += 1

    logger.info(f"User returned book '{book.title}' (ID: {book_id})")
    return borrow