from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "orchestrator",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Explicit task discovery
celery_app.autodiscover_tasks(["app.services"])