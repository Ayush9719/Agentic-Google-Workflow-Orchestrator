"""Orchestration API endpoint.

Chains intent classification → planning → execution.
"""
import uuid
from pydantic import BaseModel
from fastapi import APIRouter
from celery.result import AsyncResult
from app.services.celery_app import celery_app
from app.services.tasks import run_orchestration

router = APIRouter()

# Fixed user ID for testing (matches debug.py)
FIXED_TEST_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


class OrchestrateRequest(BaseModel):
    query: str


class OrchestrateResponse(BaseModel):
    intent: dict
    execution_results: dict


@router.post("/query")
async def submit_query(payload: OrchestrateRequest):
    user_id = str(FIXED_TEST_USER_ID)
    task = run_orchestration.delay(user_id, payload.query)
    return {"task_id": task.id}

@router.get("/query/{task_id}")
async def get_query_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "completed", "result": result.result}
    elif result.state == "FAILURE":
        return {"status": "failed", "error": str(result.info)}
    else:
        return {"status": result.state}