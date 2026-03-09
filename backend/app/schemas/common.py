from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    timestamp: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody
