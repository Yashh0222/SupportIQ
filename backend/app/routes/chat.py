"""Chat endpoint backed by the LangGraph agentic flow."""

import logging

from fastapi import APIRouter, HTTPException

from app.graph.run import run_rag
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        return await run_rag(req.message, req.company)
    except Exception as exc:
        logger.exception("Chat failed for company=%s", req.company)
        raise HTTPException(status_code=500, detail=f"Assistant error: {exc}") from exc
