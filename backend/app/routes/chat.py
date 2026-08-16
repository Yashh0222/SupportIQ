"""Chat endpoint backed by the LangGraph agentic flow."""

from fastapi import APIRouter

from app.graph.run import run_rag
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    return await run_rag(req.message, req.company)
