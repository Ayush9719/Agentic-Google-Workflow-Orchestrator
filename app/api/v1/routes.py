from fastapi import APIRouter

from app.api.v1 import health, debug, orchestrator

router = APIRouter()

# mount sub-routers
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(debug.router, prefix="/debug", tags=["debug"])
router.include_router(orchestrator.router, tags=["orchestrator"])
