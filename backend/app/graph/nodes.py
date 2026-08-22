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
    "If the context doesn't contain the answer, say you don't know. "
    "Answer in short, plain conversational text: no markdown, no asterisks, "
    "no bold, no headers. Use simple dashes or numbered lines when listing steps."
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
    "Classify the user's message into exactly one label:\n"
    "- 'wants_human': the user is requesting to talk with a human person now, "
    "or filing a complaint that clearly requires a person.\n"
    "- 'tool_use': the user wants an action on a specific order or ticket "
    "(check its status, track a specific order or shipment, open a ticket).\n"
    "- 'faq': anything else, including questions ABOUT policies or processes, "
    "such as when escalation to humans happens, how tracking works, or how "
    "tickets are handled.\n"
    "\n"
    "Examples:\n"
    "Message: I want to speak to a human -> wants_human\n"
    "Message: connect me with your support agent -> wants_human\n"
    "Message: this is unacceptable, I demand a refund from a person -> wants_human\n"
    "Message: where is my order 12345 -> tool_use\n"
    "Message: check the status of order 9876 -> tool_use\n"
    "Message: I want to file a support ticket -> tool_use\n"
    "Message: what are all the reasons you hand off to a human -> faq\n"
    "Message: when do you escalate to a human -> faq\n"
    "Message: how does order tracking work -> faq\n"
    "Message: how do we book listing -> faq\n"
    "\n"
    "Return only the label, nothing else."
)

EXTRACT_TOOL_PROMPT = (
    "You read a customer support message and decide what should happen next. "
    "Reply with ONLY a JSON object, nothing else: "
    "{{\"action\": \"order_lookup\", \"order_id\": \"<digits>\"}} when the customer "
    "refers to a specific order or shipment; "
    "{{\"action\": \"new_ticket\", \"issue\": \"<short text>\"}} when they want to "
    "report an issue or complaint."
)

_HUMAN_REQUEST_PHRASES = (
    "speak to a human",
    "talk to a human",
    "speak with a human",
    "talk with a human",
    "real person",
    "human agent",
    "human representative",
    "talk to someone",
    "speak to someone",
    "connect me",
    "transfer me",
    "file a complaint",
)

_TOOL_REQUEST_PHRASES = (
    "where is my order",
    "track my order",
    "track order",
    "track shipment",
    "track my shipment",
    "status of my order",
    "order status for order",
    "open a ticket",
    "create a ticket",
    "file a ticket",
)


async def route_node(state: GraphState) -> dict:
    question = state["question"].lower()
    if any(p in question for p in _HUMAN_REQUEST_PHRASES):
        return {"intent": "wants_human"}
    if any(p in question for p in _TOOL_REQUEST_PHRASES):
        return {"intent": "tool_use"}
    label = (
        await (_route_prompt | _llm).ainvoke({"question": state["question"]})
    ).content.strip().lower()
    if "human" in label:
        return {"intent": "wants_human"}
    if "tool" in label:
        return {"intent": "tool_use"}
    return {"intent": "faq"}


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

    if "order_lookup" in name or "check_order" in name or "order_status" in name or name == "status":
        return "check_order_status", arguments
    if "new_ticket" in name or "ticket" in name or name == "create_ticket":
        return "create_ticket", arguments

    if any(k in question.lower() for k in ("order", "track", "shipment")):
        return "check_order_status", arguments
    return "create_ticket", arguments


async def tool_node(state: GraphState) -> dict:
    response = await (_extract_tool_prompt | _llm).ainvoke(
        {"question": state["question"]}
    )
    parsed = _parse_tool_json(response.content)
    raw_args = parsed.get("arguments") or {k: v for k, v in parsed.items() if k != "action"}
    name, arguments = _resolve_tool(
        parsed.get("tool") or parsed.get("action"),
        raw_args,
        state["question"],
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
