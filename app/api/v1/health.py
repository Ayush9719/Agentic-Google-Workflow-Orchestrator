from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Service health")
async def health() -> dict:
    return {"status": "ok"}
