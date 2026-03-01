from fastapi import APIRouter
from datetime import datetime

auth_router = APIRouter(prefix="/auth", tags=["auth"])
sync_router = APIRouter(prefix="/sync", tags=["sync"])

@auth_router.get("/google")
async def google_oauth():
    """Mock endpoint for Google Workspace OAuth flow."""
    return {
        "status": "mocked", 
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?mock=true"
    }

@sync_router.post("/trigger")
async def trigger_sync():
    """Mock endpoint to manually trigger background sync."""
    return {
        "status": "sync_triggered", 
        "message": "Background sync for Gmail, GCal, and Drive initiated."
    }

@sync_router.get("/status")
async def sync_status():
    """Mock endpoint to retrieve last sync timestamps per service."""
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "status": "success",
        "last_sync": {
            "gmail": now,
            "gcal": now,
            "gdrive": now
        }
    }