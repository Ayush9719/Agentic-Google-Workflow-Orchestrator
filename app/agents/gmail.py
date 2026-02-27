"""Gmail service agent.

Handles Gmail-specific steps in orchestration.
"""
from typing import Any
import re

from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.db.session import async_session
from app.db.models import GmailCache
from app.embeddings.service import EmbeddingService


class GmailAgent(BaseAgent):
    """Agent for Gmail service operations."""

    async def handle(self, step_id: str, context: dict) -> dict:
        """Handle a Gmail step.

        Args:
            step_id: Step identifier
            context: Execution context with intent, entities, etc.

        Returns:
            Result dict
        """
        if step_id == "search_gmail_for_booking":
            return await self._search_gmail_for_booking(context)
        elif step_id == "draft_cancellation_email":
            return await self._draft_cancellation_email(context)
        else:
            return {"status": "unsupported_step", "step_id": step_id}

    async def _search_gmail_for_booking(self, context: dict) -> dict:
        """Search Gmail for booking confirmation email using hybrid search.
        
        Strategy:
        1. Filter by keyword (airline name in subject)
        2. Rank keyword matches by vector similarity
        3. Fallback to pure vector similarity if no keyword matches
        """
        intent = context.get("intent", {})
        entities = intent.get("entities", {})
        airline = entities.get("airline", "Unknown")
        user_id = context.get("user_id")

        # Generate embedding for query
        embeddings_svc = EmbeddingService()
        query = f"{airline} booking confirmation"
        query_embedding = await embeddings_svc.embed(query)

        # Search in database with hybrid strategy
        async with async_session() as db:
            # Step 1: Try keyword filter
            keyword_results = await self._keyword_search(
                db=db,
                user_id=user_id,
                airline=airline,
            )

            if keyword_results:
                # Rank keyword matches by vector similarity
                best_match = await self._rank_by_vector(
                    db=db,
                    email_ids=[row.id for row in keyword_results],
                    query_embedding=query_embedding,
                )
                if best_match:
                    # Extract booking reference from subject
                    booking_ref = self._extract_booking_reference(best_match.subject)
                    context["booking_reference"] = booking_ref

                    return {
                        "status": "found",
                        "step": "search_gmail_for_booking",
                        "email_id": str(best_match.id),
                        "subject": best_match.subject,
                        "body": best_match.body_preview,
                        "booking_reference": booking_ref,
                        "method": "hybrid",
                    }

            # Step 2: Fallback to pure vector similarity
            vector_results = await self._vector_search(
                db=db,
                user_id=user_id,
                query_embedding=query_embedding,
                limit=1,
            )

            if vector_results:
                row = vector_results[0]
                # Extract booking reference from subject
                booking_ref = self._extract_booking_reference(row.subject)
                context["booking_reference"] = booking_ref

                return {
                    "status": "found",
                    "step": "search_gmail_for_booking",
                    "email_id": str(row.id),
                    "subject": row.subject,
                    "body": row.body_preview,
                    "booking_reference": booking_ref,
                    "method": "vector_only",
                }

            return {
                "status": "not_found",
                "step": "search_gmail_for_booking",
                "message": f"No booking email found for {airline}",
            }

    async def _keyword_search(
        self, db: AsyncSession, user_id, airline: str
    ) -> list:
        """Search by keyword (airline name in subject)."""
        stmt = select(GmailCache).where(
            and_(
                GmailCache.user_id == user_id,
                GmailCache.subject.ilike(f"%{airline}%"),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def _rank_by_vector(
        self, db: AsyncSession, email_ids: list, query_embedding: list
    ):
        """Rank emails by vector similarity and return top 1."""
        if not email_ids:
            return None

        stmt = select(GmailCache).where(
            GmailCache.id.in_(email_ids)
        ).order_by(
            GmailCache.embedding.op("<->")(query_embedding)
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def _vector_search(
        self, db: AsyncSession, user_id, query_embedding: list, limit: int = 1
    ) -> list:
        """Pure vector similarity search."""
        stmt = select(GmailCache).where(
            GmailCache.user_id == user_id
        ).order_by(
            GmailCache.embedding.op("<->")(query_embedding)
        ).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def _draft_cancellation_email(self, context: dict) -> dict:
        """Draft a cancellation email."""
        intent = context.get("intent", {})
        entities = intent.get("entities", {})
        airline = entities.get("airline", "Unknown")
        booking_ref = context.get("booking_reference")
        event_date = context.get("event_date")

        # Build body with or without event date
        if event_date:
            # Format event_date to YYYY-MM-DD if it's a datetime object
            if hasattr(event_date, "strftime"):
                date_str = event_date.strftime("%Y-%m-%d")
            else:
                date_str = str(event_date).split()[0]  # Extract date part
            
            if booking_ref:
                body = (
                    f"Please cancel my {airline} booking {booking_ref} "
                    f"scheduled on {date_str}.\n"
                    "Kindly confirm the cancellation."
                )
            else:
                body = (
                    f"Please cancel my {airline} booking scheduled on {date_str}.\n"
                    "Kindly confirm the cancellation."
                )
        else:
            # Fallback: no event date
            if booking_ref:
                body = (
                    f"Please cancel my {airline} booking {booking_ref}.\n"
                    "Kindly confirm the cancellation."
                )
            else:
                body = (
                    f"Please cancel my {airline} booking.\n"
                    "Kindly confirm the cancellation."
                )

        return {
            "status": "drafted",
            "step": "draft_cancellation_email",
            "to": "support@airline.com",
            "subject": f"Cancellation Request - {airline}",
            "body": body,
        }

    def _extract_booking_reference(self, text: str) -> str | None:
        """Extract booking reference from text.
        
        Pattern: 2 uppercase letters followed by 4 digits (e.g., TK1234).
        """
        match = re.search(r"[A-Z]{2}\d{4}", text)
        return match.group(0) if match else None
