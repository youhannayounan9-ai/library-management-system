from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.book import BookCreate, BookResponse
from app.models.book import Book
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.redis_client import (
    get_cached_book, 
    cache_set, 
    cache_invalidate, 
    get_cached_books, 
    cache_books_list, 
    invalidate_books_list
)

router = APIRouter()

# ====================== LIST BOOKS (Cache-Aside) ======================
@router.get("/", response_model=list[BookResponse])
async def list_books(
    skip: int = Query(0, ge=0), 
    limit: int = Query(10, ge=1, le=100), 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Try cache first
    cached = await get_cached_books(skip, limit)
    if cached:
        return cached

    # 2. On miss, query DB
    query = select(Book).where(Book.is_deleted == False).offset(skip).limit(limit)
    result = await db.execute(query)
    books = result.scalars().all()

    # 3. Cache the result for next time
    books_data = [BookResponse.model_validate(b, from_attributes=True).model_dump() for b in books]
    await cache_books_list(skip, limit, books_data)
    
    return books

# ====================== CREATE ======================
@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    book: BookCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(require_admin)
):
    exists = await db.execute(select(Book).where(Book.isbn == book.isbn))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")

    new_book = Book(**book.model_dump())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)

    # Invalidate list cache
    await invalidate_books_list()
    return new_book

# ====================== GET SINGLE (Cache-Aside) ======================
@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    # 1. Try cache first
    cached = await get_cached_book(book_id)
    if cached:
        return cached

    # 2. On miss, query DB
    result = await db.execute(select(Book).where(Book.id == book_id, Book.is_deleted == False))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 3. Cache the result
    book_data = BookResponse.model_validate(book, from_attributes=True).model_dump()
    await cache_set(book_id, book_data)
    return book

# ====================== UPDATE ======================
@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int, 
    book: BookCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(require_admin)
):
    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalar_one_or_none()
    if not db_book or db_book.is_deleted:
        raise HTTPException(status_code=404, detail="Book not found")

    for k, v in book.model_dump().items():
        setattr(db_book, k, v)

    await db.commit()
    await db.refresh(db_book)

    # Invalidate caches
    await cache_invalidate(book_id)
    await invalidate_books_list()

    return db_book

# ====================== DELETE ======================
@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(require_admin)
):
    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalar_one_or_none()
    if not db_book or db_book.is_deleted:
        raise HTTPException(status_code=404, detail="Book not found")

    db_book.is_deleted = True
    await db.commit()

    # Invalidate caches
    await cache_invalidate(book_id)
    await invalidate_books_list()