import uuid
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import GmailCache, User
from app.embeddings.service import EmbeddingService, search_gmail_semantic

router = APIRouter()

# Fixed user ID for testing/seeding
FIXED_TEST_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


class SeedAndSearchRequest(BaseModel):
    text: str


@router.post("/debug/seed-and-search")
async def seed_and_search(
    payload: SeedAndSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    # Use fixed user ID for all test data
    user_id = FIXED_TEST_USER_ID
    email_id = f"test-{uuid.uuid4()}@example.com"

    # Upsert user
    stmt = pg_insert(User).values(
        id=user_id,
        email=f"test-{user_id}@example.com",
    ).on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()

    # Embed text
    embeddings_svc = EmbeddingService()
    embedding = await embeddings_svc.embed(payload.text)

    # Insert row
    gmail_cache = GmailCache(
        user_id=user_id,
        email_id=email_id,
        subject=payload.text[:50],
        body_preview=payload.text,
        embedding=embedding,
        received_at=datetime.utcnow(),
    )

    db.add(gmail_cache)
    await db.commit()
    await db.refresh(gmail_cache)

    # Search immediately
    results = await search_gmail_semantic(
        db=db,
        user_id=user_id,
        query_embedding=embedding,
        limit=5,
    )

    return {
        "inserted_id": str(gmail_cache.id),
        "user_id": str(user_id),
        "results": [
            {
                "id": str(row.id),
                "email_id": row.email_id,
                "subject": row.subject,
            }
            for row in results
        ],
    }