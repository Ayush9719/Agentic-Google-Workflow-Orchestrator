"""Async SQLAlchemy session and FastAPI dependency helper.

This file uses SQLAlchemy's asyncio API. Ensure `settings.DATABASE_URL`
is an async URL, e.g.:

    postgresql+asyncpg://user:pass@host:5432/dbname

Keep this module minimal and importable from application code and tests.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings


# Create the async engine. `future=True` keeps compatibility with SQLAlchemy 2.0
# style SQL and recommended usage in 1.4+.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)


# async_session is an async_sessionmaker producing AsyncSession instances.
# expire_on_commit=False is convenient for web backends to avoid lazy-loading
# after commit; adjust if you prefer stricter session lifecycle.
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Declarative base for models. Put models in `app/db/models.py` and import Base.
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session.

    Usage in endpoints:

        async def endpoint(db: AsyncSession = Depends(get_db)):
            await db.execute(...)
    """
    async with async_session() as session:
        yield session


async def init_db() -> None:
    """Create database tables for all models defined on Base.

    Call this during application startup or from a small management script.
    Uses run_sync to execute synchronous metadata.create_all on the sync
    engine bound to the async connection.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

