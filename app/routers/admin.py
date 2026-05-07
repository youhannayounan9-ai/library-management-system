from fastapi import APIRouter, Depends
from app.dependencies import require_admin

router = APIRouter()

@router.get("/stats")
async def stats(current_user = Depends(require_admin)):
    return {"message": "Admin dashboard stats", "user_id": current_user.id, "role": current_user.role}