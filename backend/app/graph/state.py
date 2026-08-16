"""LangGraph state definition."""

from typing import TypedDict


class GraphState(TypedDict, total=False):
    question: str
    company: str  # company id whose compartment we retrieve from
    chunks: list[str]
    sources: list[str]
    grade: str  # "relevant" | "insufficient"
    reformulated: str | None
    escalated: bool
    answer: str
    intent: str  # "faq" | "wants_human" | "tool_use"
    retries: int  # internal retry counter (capped at 1)
    tool_calls: list[dict]  # [{name, arguments}] for trace
    tool_result: str | None  # raw tool output fed to generation
