from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from app.database import Base
from datetime import datetime

class Borrow(Base):
    __tablename__ = "borrows"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    
    # Dates
    borrow_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)
    
    # Status & Fines
    is_returned = Column(Boolean, default=False)
    fine_amount = Column(Float, default=0.0)

    # Optional relationships (uncomment if needed, but keeping simple to avoid circular imports)
    # user = relationship("User", back_populates="borrows")
    # book = relationship("Book", back_populates="borrows")