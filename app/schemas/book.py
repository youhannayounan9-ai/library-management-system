from pydantic import BaseModel


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    available_copies: int = 1


class BookResponse(BookCreate):
    id: int
    is_deleted: bool = False
    model_config = {"from_attributes": True}
