from pydantic import BaseModel


class BaseResponse(BaseModel):
    ok: bool = True


class ErrorResponse(BaseModel):
    ok: bool = False
    reason: str
