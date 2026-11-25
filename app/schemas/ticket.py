from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

Category = Literal["billing", "technical", "manual_review"]


class TicketInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    ticket_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=3, max_length=10000)


class Classification(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1, max_length=500)


class TicketResult(TicketInput):
    category: Category | None
    confidence: float | None
    reason: str | None
    status: str
