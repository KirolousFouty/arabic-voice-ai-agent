from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=3, max_length=100)


class ChatResponse(BaseModel):
    text: str
    requires_confirmation: bool = False
    tool_status: str | None = None
    metrics: dict[str, float] = {}


class ConfirmationRequest(BaseModel):
    session_id: str
    confirmed: bool
