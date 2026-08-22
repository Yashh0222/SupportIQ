"""Graph nodes: routing, retrieval, grading, reformulation, generation, escalation."""

import json
import re
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.companies import DEFAULT_COMPANY_ID, get_company
from app.graph.state import GraphState
from app.ingestion.embedder import get_embedding_model
from app.mcp_tools.client import call_tool
from app.rag.vectorstore import load_vectorstore

MODEL_NAME = "openai/gpt-oss-20b"
TOP_K = 5

GENERATION_PROMPT = (
    "You are the customer support assistant for {company}, {company_description}. "
    "Answer only using the provided context, which is the documentation for {company}. "
    "Never use knowledge about other companies. "
    "If the context doesn't contain the answer, say you don't know."
)

GRADER_PROMPT = (
    "You are a grader deciding whether the provided context is sufficient to "
    "answer the user's question. Return exactly 'yes' if the context answers it "
    "or 'no' if it does not. Nothing else."
)

REFORMULATE_PROMPT = (
    "Rewrite the user's question into a clearer, more specific search query that "
    "will match internal documentation. Return only the rewritten question, "
    "nothing else."
)

ROUTE_PROMPT = (
    "Classify the user's intent into exactly one of:\n"
    "- 'wants_human': asking to speak with a human, representative, or agent, "
    "or filing a complaint that clearly requires a person.\n"
    "- 'tool_use': asking about a specific order's status, tracking, shipment, "
    "or wanting to file a support ticket.\n"
    "- 'faq': a general question that documentation should answer.\n"
    "Return only the label, nothing else."
)

EXTRACT_TOOL_PROMPT = (
    "You are a function-calling assistant. Given the user's request, pick exactly "
    "one tool and return a JSON object with the keys 'tool' and 'arguments' "
    "where 'arguments' is a JSON object with the exact keys below:\n"
    "- check_order_status: 'arguments' has the key 'order_id' (digits only). Use "
    "it when the user asks about a specific order's status or tracking.\n"
    "- create_ticket: 'arguments' has the key 'issue' (a short text). Use it when "
    "the user wants to file an issue or complaint.\n"
    "Return ONLY the JSON object, no markdown, no extra text."
)

HUMAN_INTENT_KEYWORDS = (
    "human",
    "agent",
    "representative",
    "real person",
    "talk to someone",
    "speak to someone",
    "escalate",
    "complaint",
)

TOOL_USE_KEYWORDS = (
    "track",
    "tracking",
    "order status",
    "where is my order",
    "status of order",
    "ticket",
    "shipment",
)

_generation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", GENERATION_PROMPT),
        ("system", "Context:\n{context}"),
        ("human", "{question}"),
    ]
)
_grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", GRADER_PROMPT),
        ("system", "Context:\n{context}"),
        ("human", "Question: {question}"),
    ]
)
_reformulate_prompt = ChatPromptTemplate.from_messages(
    [("system", REFORMULATE_PROMPT), ("human", "Question: {question}")]
)
_route_prompt = ChatPromptTemplate.from_messages(
    [("system", ROUTE_PROMPT), ("human", "Question: {question}")]
)
_extract_tool_prompt = ChatPromptTemplate.from_messages(
    [("system", EXTRACT_TOOL_PROMPT), ("human", "Request: {question}")]
)

_llm = ChatGroq(model=MODEL_NAME)


def _filename(source: str) -> str:
    return Path(source).name


async def route_node(state: GraphState) -> dict:
    question = state["question"].lower()
    if any(k in question for k in TOOL_USE_KEYWORDS):
        return {"intent": "tool_use"}
    if any(k in question for k in HUMAN_INTENT_KEYWORDS):
        return {"intent": "wants_human"}
    label = (
        await (_route_prompt | _llm).ainvoke({"question": state["question"]})
    ).content.strip().lower()
    if "human" in label:
        return {"intent": "wants_human"}
    if "tool" in label:
        return {"intent": "tool_use"}
    return {"intent": "faq"}


async def retrieve_node(state: GraphState) -> dict:
    query = state.get("reformulated") or state["question"]
    company_id = state.get("company") or DEFAULT_COMPANY_ID
    vectorstore = load_vectorstore(get_embedding_model(), company_id)
    docs = await vectorstore.asimilarity_search(query, k=TOP_K)
    return {
        "chunks": [doc.page_content for doc in docs],
        "sources": list(
            dict.fromkeys(_filename(doc.metadata.get("source", "unknown")) for doc in docs)
        ),
    }


async def grade_node(state: GraphState) -> dict:
    question = state["question"]
    context = "\n\n".join(state.get("chunks", []))
    response = await (_grader_prompt | _llm).ainvoke(
        {"context": context, "question": question}
    )
    grade = "relevant" if response.content.strip().lower().startswith("yes") else "insufficient"
    return {"grade": grade}


async def reformulate_node(state: GraphState) -> dict:
    response = await (_reformulate_prompt | _llm).ainvoke(
        {"question": state["question"]}
    )
    return {
        "reformulated": response.content.strip(),
        "retries": state.get("retries", 0) + 1,
    }


def _parse_tool_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in: {text[:200]}")
    return json.loads(match.group(0))


def _normalize_arguments(name: str, arguments) -> dict:
    if isinstance(arguments, dict):
        return arguments
    value = arguments[0] if isinstance(arguments, list) and arguments else str(arguments)
    key = "order_id" if name == "check_order_status" else "issue"
    return {key: str(value)}


def _resolve_tool(name: str, arguments: dict, question: str) -> tuple[str, dict]:
    """Map a possibly-hallucinated extraction to a known MCP tool."""
    name = str(name or "").lower()

    for known in ("check_order_status", "create_ticket"):
        if known in arguments and isinstance(arguments[known], dict):
            return known, arguments[known]

    if "order_id" in arguments:
        return "check_order_status", arguments
    if "issue" in arguments:
        return "create_ticket", arguments

    if "check_order" in name or "order_status" in name or name == "status":
        return "check_order_status", arguments
    if "ticket" in name or name == "create_ticket":
        return "create_ticket", arguments

    if any(k in question.lower() for k in ("order", "track", "shipment")):
        return "check_order_status", arguments
    return "create_ticket", arguments


async def tool_node(state: GraphState) -> dict:
    response = await (_extract_tool_prompt | _llm).ainvoke(
        {"question": state["question"]}
    )
    parsed = _parse_tool_json(response.content)
    name, arguments = _resolve_tool(
        parsed.get("tool"), parsed.get("arguments") or {}, state["question"]
    )
    arguments = _normalize_arguments(name, arguments)

    tool_result = await call_tool(name, arguments)
    return {
        "tool_calls": [{"name": name, "arguments": arguments}],
        "tool_result": tool_result,
    }


async def generate_node(state: GraphState) -> dict:
    question = state["question"]
    context_parts = []
    if state.get("chunks"):
        context_parts.append("Documentation context:\n" + "\n\n".join(state["chunks"]))
    if state.get("tool_result"):
        context_parts.append("Tool result:\n" + state["tool_result"])
    context = "\n\n".join(context_parts)

    company = get_company(state.get("company") or DEFAULT_COMPANY_ID)
    response = await (_generation_prompt | _llm).ainvoke(
        {
            "context": context,
            "question": question,
            "company": company.display_name,
            "company_description": company.description,
        }
    )
    return {"answer": response.content}


async def escalate_node(state: GraphState) -> dict:
    return {
        "escalated": True,
        "answer": (
            "I'm sorry, I couldn't find a confident answer in our documentation. "
            "Let me connect you with a human support agent who can help you further."
        ),
    }
