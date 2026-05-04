from sqlalchemy import ForeignKey, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    borrow_date: Mapped[datetime] = mapped_column(server_default=func.now())
    return_date: Mapped[datetime | None] = mapped_column(nullable=True)
    fine: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")

    user = relationship("User", backref="borrows")
    book = relationship("Book", backref="borrows")
