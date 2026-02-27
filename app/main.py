from fastapi import FastAPI

from app.api.v1.routes import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.db import models
from app.db.seed import seed_demo_data


def create_app() -> FastAPI:
    """Application factory. Keeps top-level script small and testable."""
    setup_logging()

    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def _startup():
        # place for startup tasks: warm LLM, DB migrations, etc.
        await init_db()
        await seed_demo_data()

    @app.on_event("shutdown")
    async def _shutdown():
        # place for graceful shutdown tasks
        pass

    return app


app = create_app()
