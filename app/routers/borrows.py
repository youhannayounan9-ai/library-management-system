from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.borrow import BorrowResponse
from app.models.borrow import Borrow
from app.database import get_db
from app.dependencies import get_current_user
from app.services.borrow_service import borrow_book, return_book
from sqlalchemy import select
from app.redis_client import get_cached_history, cache_history

router = APIRouter()

@router.post("/{book_id}", response_model=BorrowResponse)
async def borrow(book_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        borrow_record = await borrow_book(db, current_user.id, book_id)
        await db.commit()
        await db.refresh(borrow_record)
        return borrow_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/return/{borrow_id}", response_model=BorrowResponse)
async def ret(borrow_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        borrow_record = await return_book(db, borrow_id)
        await db.commit()
        await db.refresh(borrow_record)
        return borrow_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my-history")
async def history(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    # Try Cache
    cached = await get_cached_history(current_user.id)
    if cached:
        return cached

    query = select(Borrow).where(Borrow.user_id == current_user.id)
    result = await db.execute(query)
    borrows = result.scalars().all()
    
    # Cache result
    history_data = [BorrowResponse.model_validate(b, from_attributes=True).model_dump() for b in borrows]
    await cache_history(current_user.id, history_data)
    
    return borrows