from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.book import Book
from app.schemas.book import BookCreate, BookResponse
from app.dependencies import get_current_user, require_admin
from app.redis_client import get_cached_book, cache_set, cache_invalidate, book_key
from app.models.user import User

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=list[BookResponse])
async def get_books(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all non-deleted books with pagination."""
    result = await db.execute(
        select(Book).where(Book.is_deleted == False).offset(skip).limit(limit)  # noqa: E712
    )
    return result.scalars().all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    async def fetch():
        book = await db.get(Book, book_id)
        if not book or book.is_deleted:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    return await get_cached_book(book_id, fetch)


from sqlalchemy.exc import IntegrityError

@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    new_book = Book(**book.model_dump())
    db.add(new_book)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    await db.refresh(new_book)
    await cache_set(book_key(new_book.id), new_book)
    return new_book


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    db_book = await db.get(Book, book_id)
    if not db_book or db_book.is_deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.model_dump().items():
        setattr(db_book, key, value)
    await db.commit()
    await cache_invalidate(book_key(book_id))
    return db_book


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Soft-delete a book (sets is_deleted=True; row is preserved for audit)."""
    db_book = await db.get(Book, book_id)
    if not db_book or db_book.is_deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    db_book.is_deleted = True
    await db.commit()
    await cache_invalidate(book_key(book_id))

