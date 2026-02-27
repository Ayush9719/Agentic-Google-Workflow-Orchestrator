"""Google Calendar service agent.

Handles Google Calendar-specific steps in orchestration.
"""
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.db.session import async_session
from app.db.models import GCalCache


class GCalAgent(BaseAgent):
    """Agent for Google Calendar service operations."""

    async def handle(self, step_id: str, context: dict) -> dict:
        """Handle a Calendar step.

        Args:
            step_id: Step identifier
            context: Execution context

        Returns:
            Result dict
        """
        if step_id == "find_calendar_event":
            return await self._find_calendar_event(context)
        else:
            return {"status": "unsupported_step", "step_id": step_id}

    async def _find_calendar_event(self, context: dict) -> dict:
        """Find calendar event by keyword search.
        
        Searches for events matching airline or booking reference.
        """
        user_id = context.get("user_id")
        intent = context.get("intent", {})
        entities = intent.get("entities", {})
        airline = entities.get("airline", "")
        booking_reference = context.get("booking_reference")

        # Determine search keywords
        search_terms = []
        if airline:
            search_terms.append(airline)
        if booking_reference:
            search_terms.append(booking_reference)

        if not search_terms:
            return {
                "status": "not_found",
                "step": "find_calendar_event",
                "message": "No search terms available",
            }

        # Search in database
        async with async_session() as db:
            # Try keyword search for each term
            for term in search_terms:
                event = await self._keyword_search(
                    db=db,
                    user_id=user_id,
                    keyword=term,
                )
                if event:
                    # Add event date to context
                    context["event_date"] = str(event.start_time) if event.start_time else None

                    return {
                        "status": "found",
                        "step": "find_calendar_event",
                        "event_id": str(event.id),
                        "title": event.title,
                        "start_time": str(event.start_time) if event.start_time else None,
                    }

        return {
            "status": "not_found",
            "step": "find_calendar_event",
            "message": f"No calendar event found for {' or '.join(search_terms)}",
        }

    async def _keyword_search(
        self, db: AsyncSession, user_id, keyword: str
    ) -> GCalCache | None:
        """Search by keyword in event title."""
        stmt = select(GCalCache).where(
            and_(
                GCalCache.user_id == user_id,
                GCalCache.title.ilike(f"%{keyword}%"),
            )
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()
