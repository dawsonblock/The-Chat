from fastapi import APIRouter

from api.public.auth import router as auth_router
from api.public.artifacts import router as artifacts_router
from api.public.conversations import router as conversations_router
from api.public.files import router as files_router
from api.public.runs import router as runs_router
from api.public.tools import router as tools_router
from api.public.workflows import router as workflows_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(conversations_router)
router.include_router(files_router)
router.include_router(artifacts_router)
router.include_router(runs_router)
router.include_router(tools_router)
router.include_router(workflows_router)
