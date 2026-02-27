"""Database seeding for demo/test data.

Run via:
    python -m asyncio -c "from app.db.seed import seed_demo_data; await seed_demo_data()"

Or call from FastAPI startup event.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import async_session
from app.db.models import User, GmailCache, GCalCache, GDriveCache
from app.embeddings.service import EmbeddingService

# Fixed demo user ID
DEMO_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


async def seed_demo_data() -> None:
    """Seed demo data if not already present.
    
    Idempotent: checks if data exists before inserting.
    """
    async with async_session() as db:
        # Check if users table has data
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()

        if user_count > 0:
            # Data already seeded
            return

        # Create demo user
        demo_user = User(
            id=DEMO_USER_ID,
            email="demo@example.com",
        )
        db.add(demo_user)
        await db.commit()

        # Embed texts for Gmail
        embeddings_svc = EmbeddingService()

        # Create demo Gmail emails (expanded for multi-service testing)
        gmail_subjects = [
            # Flight-related (for flight cancellation query)
            "Turkish Airlines Booking TK1234",
            "Singapore Airlines Flight TK5678 Confirmed",
            "Flight confirmation and seat assignment TK1234",
            
            # Budget/meeting-related (for Acme Corp query)
            "Budget discussion with Sarah - Q1 Planning",
            "Acme Corp meeting agenda - Product Launch",
            "Sarah: Budget Review - Conference Room A",
            
            # Calendar/document related
            "Acme Corp Contract Review - Document attached",
            "Out of Office Policy Update",
            "Weekly Newsletter: Tech Trends",
            
            # Additional for temporal reasoning tests
            "Tomorrow's Stand-up Agenda",
            "Next Week: Team Offsite Details",
        ]

        for i, subject in enumerate(gmail_subjects):
            embedding = await embeddings_svc.embed(subject)
            gmail = GmailCache(
                user_id=DEMO_USER_ID,
                email_id=f"gmail_msg_{i}",
                subject=subject,
                body_preview=subject,
                received_at=datetime.utcnow() - timedelta(days=max(0, i-5)),
                embedding=embedding,
            )
            db.add(gmail)

        # Create demo GCal events (expanded for multi-service testing)
        gcal_events = [
            {
                "title": "Istanbul → NYC Flight TK1234",
                "description": "Turkish Airlines flight",
                "start_time": datetime.utcnow() + timedelta(days=10),
            },
            {
                "title": "Acme Corp Meeting",
                "description": "Product launch planning with Acme",
                "start_time": datetime.utcnow() + timedelta(days=3),
            },
            {
                "title": "Sarah - Budget Review",
                "description": "Quarterly budget discussion",
                "start_time": datetime.utcnow() + timedelta(days=5),
            },
            {
                "title": "Out of Office - Vacation",
                "description": "Personal time off",
                "start_time": datetime.utcnow() + timedelta(days=15),
            },
        ]

        for i, event in enumerate(gcal_events):
            event_embedding = await embeddings_svc.embed(event["title"])
            gcal = GCalCache(
                user_id=DEMO_USER_ID,
                event_id=f"gcal_event_{i}",
                title=event["title"],
                description=event["description"],
                start_time=event["start_time"],
                embedding=event_embedding,
            )
            db.add(gcal)

        gdrive_files = [
            {
                "name": "Turkish Airlines Cancellation Policy",
                "content_preview": "Cancellation policy for Turkish Airlines bookings including refund rules."
            },
            {
                "name": "Acme Corp Product Launch Plan",
                "content_preview": "Detailed strategy document for Acme Corp product launch."
            },
            {
                "name": "Q1 Budget Spreadsheet",
                "content_preview": "Quarterly budget breakdown for Q1 planning."
            },
            {
                "name": "Company Out of Office Policy",
                "content_preview": "Official company policy for vacation and leave."
            },
        ]

        for i, file in enumerate(gdrive_files):
            gdfile = GDriveCache(
                user_id=DEMO_USER_ID,
                external_id=str(uuid.uuid4()),
                payload={
                    "name": file["name"],
                    "content_preview": file["content_preview"],
                },
                embedding=await embeddings_svc.embed(file["name"] + " " + file["content_preview"]),
            )
            db.add(gdfile)
        
        await db.commit()