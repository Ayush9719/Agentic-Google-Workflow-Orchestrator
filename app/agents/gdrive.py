"""Google Drive service agent.

Handles Drive-specific steps in orchestration.
"""
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.db.models import GDriveCache
from app.embeddings.service import EmbeddingService


class DriveAgent(BaseAgent):
    """Agent for Google Drive service operations."""

    def __init__(self, db: AsyncSession, user_id: str, embeddings_svc: EmbeddingService):
        self.db = db
        self.user_id = user_id
        self.embeddings_svc = embeddings_svc

    async def handle(self, step_id: str, context: dict) -> dict:
        """Handle a Drive step.

        Args:
            step_id: Step identifier
            context: Execution context with intent, entities, etc.

        Returns:
            Result dict
        """
        if step_id == "search_drive_files":
            return await self._search_drive_files(context)
        else:
            return {"status": "unsupported_step", "step_id": step_id}

    async def _search_drive_files(self, context: dict) -> dict:
        intent = context.get("intent", {})
        entities = intent.get("entities", {})

        # Use extracted entity or fallback
        query_text = entities.get("company") or entities.get("query") or "document"

        # Generate embedding
        query_embedding = await self.embeddings_svc.embed(query_text)

        query_sql = """
            SELECT id, external_id, payload
            FROM gdrive_cache
            WHERE user_id = :user_id
            AND (payload->>'name') ILIKE :keyword
            ORDER BY embedding <-> (:query_embedding)::vector
            LIMIT 1
        """

        result = await self.db.execute(
            text(query_sql),
            {
                "user_id": self.user_id,
                "keyword": f"%{query_text}%",
                "query_embedding": query_embedding,
            },
        )

        row = result.first()

        if row:
            return {
                "status": "found",
                "step": "search_drive_files",
                "file_id": str(row.id),
                "name": row.payload.get("name"),
                "content_preview": row.payload.get("content_preview"),
                "method": "hybrid",
            }

        return {
            "status": "not_found",
            "step": "search_drive_files",
        }