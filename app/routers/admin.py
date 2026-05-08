import logging
from fastapi import APIRouter, Depends
from app.dependencies import require_admin
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
async def stats(current_user: User = Depends(require_admin)):
    logger.info(f"ADMIN_ACCESS: User {current_user.id} accessed admin stats")
    return {
        "message": "Library System Statistics",
        "admin_user": current_user.email,
        "status": "Healthy",
        "version": "1.0.0"
    }