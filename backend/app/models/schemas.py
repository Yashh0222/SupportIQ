"""Pydantic request/response schemas."""

from pydantic import BaseModel, Field

from app.companies import DEFAULT_COMPANY_ID


class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    company: str = DEFAULT_COMPANY_ID


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    company: str = DEFAULT_COMPANY_ID
    trace: dict = {}  # {retrieved_chunks, grading, reformulated_query, escalated}


class CreateCompanyRequest(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$", description="lowercase letters, digits, hyphens")
    display_name: str = Field(min_length=1)
    description: str = ""


class AllowedOriginRequest(BaseModel):
    origin: str = Field(min_length=1)
