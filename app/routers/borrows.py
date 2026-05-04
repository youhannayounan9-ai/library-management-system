from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.dependencies import get_current_user
from app.services.borrow_service import borrow_book, return_book
from app.models.user import User
from app.models.borrow import BorrowRecord
from app.schemas.borrow import BorrowResponse

router = APIRouter(prefix="/borrows", tags=["Borrows"])


@router.post("/{book_id}", status_code=201)
async def borrow(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await borrow_book(db, current_user.id, book_id)
    return {"message": "Book borrowed successfully"}


@router.post("/return/{record_id}", status_code=200)
async def return_book_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await return_book(db, current_user.id, record_id)
    message = "Book returned successfully"
    if result["fine"] > 0:
        message = (
            f"Book returned successfully. Late fine: ${result['fine']:.2f} "
            f"({result['days_late']} day(s) overdue)."
        )
    return {"message": message, "fine": result["fine"], "days_late": result["days_late"]}


@router.get("/my-history", response_model=list[BorrowResponse])
async def get_my_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BorrowRecord).where(BorrowRecord.user_id == current_user.id)
    )
    return result.scalars().all()

