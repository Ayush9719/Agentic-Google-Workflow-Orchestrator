from datetime import datetime
from typing import Any
from uuid import UUID
import random
import redis
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
# from openai import AsyncOpenAI
from sqlalchemy import text

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.REDIS_URL)

    async def embed(self, text: str) -> list[float]:
        # Deterministic fake embedding based on hash
        cache_key = f"embedding:{hash(text)}"
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        random.seed(hash(text))
        embedding = [random.random() for _ in range(1536)]
        self.redis.setex(cache_key, 3600, json.dumps(embedding))
        return embedding

def _to_pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(x) for x in embedding) + "]"


async def search_gmail_semantic(
    db: AsyncSession,
    user_id: UUID,
    query_embedding: list[float],
    limit: int = 5,
    received_after: datetime | None = None,
):
    vector_literal = _to_pgvector_literal(query_embedding)

    base_query = """
        SELECT id, email_id, subject, body_preview, received_at
        FROM gmail_cache
        WHERE user_id = :user_id
    """

    params = {
        "user_id": user_id,
        "query_embedding": vector_literal,
        "limit": limit,
    }

    if received_after:
        base_query += " AND received_at > :received_after"
        params["received_after"] = received_after

    base_query += """
        ORDER BY embedding <-> CAST(:query_embedding AS vector)
        LIMIT :limit
    """

    result = await db.execute(text(base_query), params)
    return result.fetchall()