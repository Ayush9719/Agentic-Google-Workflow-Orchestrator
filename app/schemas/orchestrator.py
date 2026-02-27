from pydantic import BaseModel
from typing import List, Any


class PlanRequest(BaseModel):
    input_text: str


class PlanResponse(BaseModel):
    plan: List[Any]
