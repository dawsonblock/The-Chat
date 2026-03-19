from fastapi import APIRouter

from api.internal.intake import router as intake_router

router = APIRouter()
router.include_router(intake_router)
