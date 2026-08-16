"""Run the compiled agentic graph and return a ChatResponse with a trace."""

from app.companies import DEFAULT_COMPANY_ID
from app.graph.build_graph import get_graph
from app.models.schemas import ChatResponse


async def run_rag(question: str, company: str | None = None) -> ChatResponse:
    """Invoke the LangGraph flow for *question* and surface its trace."""
    company_id = company or DEFAULT_COMPANY_ID
    graph = get_graph()
    result = await graph.ainvoke({"question": question, "company": company_id})

    trace = {
        "intent": result.get("intent"),
        "retrieved_chunks": result.get("chunks", []),
        "grading": result.get("grade"),
        "reformulated_query": result.get("reformulated"),
        "escalated": result.get("escalated", False),
        "tool_calls": result.get("tool_calls", []),
        "tool_result": result.get("tool_result"),
    }

    return ChatResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        company=company_id,
        trace=trace,
    )
