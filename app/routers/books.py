from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.book import BookCreate, BookResponse
from app.models.book import Book
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.redis_client import get_cached_book, cache_set, cache_invalidate
from sqlalchemy import select

router = APIRouter()

@router.get("/", response_model=list[BookResponse])
async def list_books(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    query = select(Book).where(Book.is_deleted == False).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(book: BookCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    exists = await db.execute(select(Book).where(Book.isbn == book.isbn))
    if exists.first():
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    new_book = Book(**book.model_dump())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    await cache_invalidate(new_book.id)
    return new_book

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    cached = await get_cached_book(book_id)
    if cached: return cached
    result = await db.execute(select(Book).where(Book.id == book_id, Book.is_deleted == False))
    book = result.scalar_one_or_none()
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    await cache_set(book_id, BookResponse.model_validate(book, from_attributes=True).model_dump())
    return book

@router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, book: BookCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalar_one_or_none()
    if not db_book or db_book.is_deleted: raise HTTPException(status_code=404, detail="Book not found")
    for k, v in book.model_dump().items(): setattr(db_book, k, v)
    await db.commit()
    await db.refresh(db_book)
    await cache_invalidate(book_id)
    return db_book

@router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalar_one_or_none()
    if not db_book or db_book.is_deleted: raise HTTPException(status_code=404, detail="Book not found")
    db_book.is_deleted = True
    await db.commit()
    await cache_invalidate(book_id)