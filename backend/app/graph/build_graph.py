"""LangGraph wiring for the agentic RAG flow."""

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    escalate_node,
    generate_node,
    grade_node,
    reformulate_node,
    retrieve_node,
    route_node,
    tool_node,
)
from app.graph.state import GraphState


def _after_route(state: GraphState) -> str:
    intent = state.get("intent")
    if intent == "wants_human":
        return "escalate_node"
    if intent == "tool_use":
        return "tool_node"
    return "retrieve_node"


def _after_grade(state: GraphState) -> str:
    if state.get("grade") == "relevant":
        return "generate_node"
    if state.get("retries", 0) < 1:
        return "reformulate_node"
    return "escalate_node"


def build_graph():
    """Build and compile the agentic RAG StateGraph."""
    workflow = StateGraph(GraphState)

    workflow.add_node("route_node", route_node)
    workflow.add_node("retrieve_node", retrieve_node)
    workflow.add_node("grade_node", grade_node)
    workflow.add_node("reformulate_node", reformulate_node)
    workflow.add_node("generate_node", generate_node)
    workflow.add_node("escalate_node", escalate_node)
    workflow.add_node("tool_node", tool_node)

    workflow.set_entry_point("route_node")
    workflow.add_conditional_edges("route_node", _after_route)
    workflow.add_edge("retrieve_node", "grade_node")
    workflow.add_conditional_edges("grade_node", _after_grade)
    workflow.add_edge("reformulate_node", "retrieve_node")
    workflow.add_edge("tool_node", "generate_node")
    workflow.add_edge("generate_node", END)
    workflow.add_edge("escalate_node", END)

    return workflow.compile()


@lru_cache(maxsize=1)
def get_graph():
    """Return a cached compiled graph."""
    return build_graph()
