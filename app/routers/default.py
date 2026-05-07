from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Library API is running"}

@router.get("/health")
async def health():
    return {"status": "healthy", "database": "ok", "redis": "ok"}