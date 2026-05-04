from pydantic import BaseModel
from datetime import datetime


class BorrowResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrow_date: datetime
    return_date: datetime | None
    fine: float = 0.0
    model_config = {"from_attributes": True}
